"""Streaming chat conversation API endpoints for real-time responses."""

import json
import time
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.audit_service import AuditService, get_audit_service
from app.services.conversation_service import ConversationService, NoDocumentsError
from app.services.kb_service import get_kb_permission_service
from app.services.search_service import SearchService, get_search_service

logger = get_logger()

router = APIRouter(prefix="/chat", tags=["chat"])


def get_conversation_service(
    search_service: SearchService = Depends(get_search_service),
) -> ConversationService:
    """Dependency injection for ConversationService."""
    return ConversationService(search_service)


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

    Yields:
        SSE-formatted event strings
    """
    # Track metrics for audit logging
    citation_count = 0
    source_doc_ids: set[str] = set()
    output_word_count = 0
    confidence_score = 0.0

    try:
        async for event in conversation_service.send_message_stream(
            session_id=session_id,
            kb_id=kb_id,
            user_id=user_id,
            message=message,
            conversation_id=conversation_id,
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
            elif event.get("type") == "done":
                confidence_score = event.get("confidence", 0.0)

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

    try:
        # Permission check
        permission_service = get_kb_permission_service(session)
        await permission_service.check_permission(
            user_id=str(current_user.id),
            kb_id=str(request_body.kb_id),
            permission_level="READ",
        )

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

        logger.info(
            "chat_stream_started",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            request_id=request_id,
        )

        # Return real-time streaming response
        return StreamingResponse(
            generate_sse_events(
                conversation_service=conversation_service,
                session_id=session_id,
                kb_id=request_body.kb_id,
                user_id=str(current_user.id),
                message=request_body.message,
                conversation_id=request_body.conversation_id,
                audit_service=audit_service,
                request_id=request_id,
                start_time=start_time,
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
        raise HTTPException(status_code=400, detail=e.message) from e

    except Exception as e:
        logger.error(
            "chat_stream_failed",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=503, detail="Chat streaming service temporarily unavailable"
        ) from e
