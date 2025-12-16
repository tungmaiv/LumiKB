"""Streaming chat conversation API endpoints for real-time responses."""

import json
import time
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.core.logging import get_logger
from app.core.redis import get_redis_client
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.audit_service import AuditService, get_audit_service
from app.services.conversation_service import ConversationService, NoDocumentsError
from app.services.kb_service import get_kb_permission_service
from app.services.observability_service import ObservabilityService, TraceContext
from app.services.search_service import SearchService, get_search_service

logger = get_logger()

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_conversation_service(
    search_service: SearchService = Depends(get_search_service),
    session: AsyncSession = Depends(get_async_session),
    redis_client: Redis = Depends(get_redis_client),
) -> ConversationService:
    """Dependency injection for ConversationService.

    Args:
        search_service: Search service dependency
        session: Database session for KB model lookup (Story 7-10)
        redis_client: Redis client for KB config caching (Story 7-17)
    """
    return ConversationService(
        search_service, session=session, redis_client=redis_client
    )


async def generate_sse_events(
    conversation_service: ConversationService,
    session_id: str,
    kb_id: str,
    user_id: str,
    message: str,
    conversation_id: str | None,
    audit_service: AuditService,
    request_id: str,
    start_time: float,
    trace_ctx: TraceContext | None = None,
) -> AsyncGenerator[str, None]:
    """Generate real-time SSE events from conversation service stream.

    Args:
        conversation_service: Conversation service instance
        session_id: User session ID
        kb_id: Knowledge Base ID
        user_id: User ID
        message: User message
        conversation_id: Existing conversation ID (optional)
        audit_service: Audit service for logging
        request_id: Request ID for audit linking
        start_time: Request start time for metrics
        trace_ctx: Observability trace context (optional)

    Yields:
        SSE-formatted event strings
    """
    # Track metrics for audit logging and observability
    citation_count = 0
    source_doc_ids: set[str] = set()
    output_word_count = 0
    confidence_score = 0.0
    chunks_retrieved = 0
    response_text_length = 0
    response_text_buffer: list[str] = []  # Accumulate response text for chat history
    debug_info_data: dict | None = (
        None  # Capture debug info for chat history persistence
    )
    obs = ObservabilityService.get_instance()
    final_conversation_id: str | None = None

    try:
        async for event in conversation_service.send_message_stream(
            session_id=session_id,
            kb_id=kb_id,
            user_id=user_id,
            message=message,
            conversation_id=conversation_id,
            trace_ctx=trace_ctx,
        ):
            # Track metrics from events
            if event.get("type") == "citation":
                citation_count += 1
                citation_data = event.get("data", {})
                if "document_id" in citation_data:
                    source_doc_ids.add(str(citation_data["document_id"]))
            elif event.get("type") == "token":
                content = event.get("content", "")
                output_word_count += len(content.split())
                response_text_length += len(content)
                response_text_buffer.append(content)  # Accumulate for chat history
            elif event.get("type") == "retrieval_complete":
                chunks_retrieved = event.get("chunks_retrieved", 0)
            elif event.get("type") == "debug":
                # Capture debug info for persistence in chat history
                debug_info_data = event.get("data")
            elif event.get("type") == "done":
                confidence_score = event.get("confidence", 0.0)
                final_conversation_id = event.get("conversation_id")
                # Capture final metrics from done event
                if "chunks_retrieved" in event:
                    chunks_retrieved = event.get("chunks_retrieved", chunks_retrieved)
                if "response_length" in event:
                    response_text_length = event.get(
                        "response_length", response_text_length
                    )

            # Format event as SSE
            yield f"data: {json.dumps(event)}\n\n"

        # Log successful completion
        generation_time_ms = int((time.time() - start_time) * 1000)
        await audit_service.log_generation_complete(
            user_id=uuid.UUID(user_id),
            request_id=request_id,
            kb_id=uuid.UUID(kb_id),
            document_type="chat",
            citation_count=citation_count,
            source_document_ids=list(source_doc_ids),
            generation_time_ms=generation_time_ms,
            output_word_count=output_word_count,
            confidence_score=confidence_score,
        )

        # Log assistant message and end trace on success
        if trace_ctx:
            # Parse conversation_id: final_conversation_id is from response (conv-xxx format)
            # Fall back to the original conversation_id passed to the function
            final_conv_id = final_conversation_id or conversation_id
            conv_uuid = None
            if final_conv_id:
                conv_uuid = (
                    uuid.UUID(final_conv_id.replace("conv-", ""))
                    if final_conv_id.startswith("conv-")
                    else uuid.UUID(final_conv_id)
                )
            # Join accumulated response text for chat history logging
            full_response_text = "".join(response_text_buffer)
            # Build metadata including debug info if available
            message_metadata: dict = {
                "chunks_retrieved": chunks_retrieved,
                "citations_count": citation_count,
                "response_length": response_text_length,
                "confidence_score": confidence_score,
                "source_documents": len(source_doc_ids),
            }
            # Include debug_info if KB has debug mode enabled
            if debug_info_data:
                message_metadata["debug_info"] = debug_info_data

            await obs.log_chat_message(
                ctx=trace_ctx,
                role="assistant",
                content=full_response_text,  # Log actual content for chat history
                conversation_id=conv_uuid,
                latency_ms=generation_time_ms,
                metadata=message_metadata,
            )
            await obs.end_trace(trace_ctx, status="completed")

    except Exception as e:
        # Log failure
        generation_time_ms = int((time.time() - start_time) * 1000)
        await audit_service.log_generation_failed(
            user_id=uuid.UUID(user_id),
            request_id=request_id,
            kb_id=uuid.UUID(kb_id),
            document_type="chat",
            error_message=str(e),
            error_type=type(e).__name__,
            generation_time_ms=generation_time_ms,
            failure_stage=_determine_failure_stage(e),
        )

        # End trace with failed status
        if trace_ctx:
            await obs.end_trace(
                trace_ctx,
                status="failed",
                error_message=type(e).__name__,  # Only error type, not message
            )

        # Yield error event
        error_event = {
            "type": "error",
            "message": str(e),
        }
        yield f"data: {json.dumps(error_event)}\n\n"


def _determine_failure_stage(exception: Exception) -> str:
    """Determine which stage of generation failed.

    Args:
        exception: The exception that occurred

    Returns:
        Failure stage identifier
    """
    exc_name = type(exception).__name__
    if "Search" in exc_name or "Document" in exc_name:
        return "retrieval"
    elif "Context" in exc_name:
        return "context_build"
    elif "LLM" in exc_name or "Litellm" in exc_name:
        return "llm_generation"
    elif "Citation" in exc_name:
        return "citation_extraction"
    else:
        return "unknown"


@router.post("/stream")
async def send_chat_message_stream(
    request_body: ChatRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    conversation_service: ConversationService = Depends(get_conversation_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Send a chat message and receive streaming response.

    Streams response word-by-word using Server-Sent Events (SSE).

    Args:
        request_body: Chat request with kb_id, message, optional conversation_id
        current_user: Authenticated user
        session: Database session
        conversation_service: Conversation service dependency
        audit_service: Audit service for logging

    Returns:
        StreamingResponse with SSE events

    Raises:
        HTTPException: 404 if KB not found/unauthorized, 400 if no documents

    Event types:
        - status: {"type": "status", "content": "Searching..."}
        - token: {"type": "token", "content": "word"}
        - citation: {"type": "citation", "data": {...}}
        - done: {"type": "done", "confidence": 0.87, "conversation_id": "..."}
        - error: {"type": "error", "message": "..."}
    """
    # Generate request ID and start timer for audit logging
    request_id = str(uuid.uuid4())
    start_time = time.time()

    # Generate conversation_id if not provided (needed for observability logging)
    conversation_id = request_body.conversation_id or f"conv-{uuid.uuid4()}"

    # Start observability trace
    obs = ObservabilityService.get_instance()
    trace_ctx = await obs.start_trace(
        name="chat.conversation.stream",
        user_id=current_user.id,
        kb_id=uuid.UUID(request_body.kb_id),
        metadata={
            "conversation_id": conversation_id,
            "message_length": len(request_body.message),
            "streaming": True,
        },
    )

    try:
        # Permission check
        permission_service = get_kb_permission_service(session)
        has_permission = await permission_service.check_permission(
            user_id=str(current_user.id),
            kb_id=str(request_body.kb_id),
            permission_level="READ",
        )
        if not has_permission:
            await obs.end_trace(
                trace_ctx, status="failed", error_message="Unauthorized"
            )
            raise HTTPException(status_code=404, detail="Knowledge Base not found")

        # Log generation request
        await audit_service.log_generation_request(
            user_id=current_user.id,
            kb_id=uuid.UUID(request_body.kb_id),
            document_type="chat",
            context=request_body.message,
            selected_source_count=0,
            request_id=request_id,
        )

        # Generate session_id from user
        session_id = str(current_user.id)

        # Log user message for chat history
        # Parse conversation_id: strip "conv-" prefix if present to get UUID
        conv_uuid = (
            uuid.UUID(conversation_id.replace("conv-", ""))
            if conversation_id.startswith("conv-")
            else uuid.UUID(conversation_id)
        )
        await obs.log_chat_message(
            ctx=trace_ctx,
            role="user",
            content=request_body.message,  # Log actual content for chat history
            conversation_id=conv_uuid,
        )

        logger.info(
            "chat_stream_started",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            request_id=request_id,
        )

        # Return real-time streaming response with trace context
        return StreamingResponse(
            generate_sse_events(
                conversation_service=conversation_service,
                session_id=session_id,
                kb_id=request_body.kb_id,
                user_id=str(current_user.id),
                message=request_body.message,
                conversation_id=conversation_id,
                audit_service=audit_service,
                request_id=request_id,
                start_time=start_time,
                trace_ctx=trace_ctx,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    except NoDocumentsError as e:
        logger.warning(
            "chat_stream_no_documents",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            error=str(e),
        )
        await obs.end_trace(
            trace_ctx, status="failed", error_message="NoDocumentsError"
        )
        raise HTTPException(status_code=400, detail=e.message) from e

    except HTTPException:
        # Already handled above (permission check)
        raise

    except Exception as e:
        logger.error(
            "chat_stream_failed",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            error=str(e),
            exc_info=True,
        )
        await obs.end_trace(trace_ctx, status="failed", error_message=type(e).__name__)
        raise HTTPException(
            status_code=503, detail="Chat streaming service temporarily unavailable"
        ) from e
