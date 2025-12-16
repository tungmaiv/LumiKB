"""Streaming document generation API endpoints for real-time draft generation."""

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
from app.schemas.generation import GenerationRequest
from app.services.audit_service import AuditService, get_audit_service
from app.services.generation_service import GenerationService, InsufficientSourcesError
from app.services.kb_service import get_kb_permission_service

logger = get_logger()

router = APIRouter(prefix="/generate", tags=["generation"])


def get_generation_service() -> GenerationService:
    """Dependency injection for GenerationService."""
    return GenerationService()


async def generate_sse_events(
    generation_service: GenerationService,
    session: AsyncSession,
    request: GenerationRequest,
    user_id: str,
    audit_service: AuditService,
    request_id: str,
    start_time: float,
) -> AsyncGenerator[str, None]:
    """Generate real-time SSE events from generation service stream.

    Args:
        generation_service: Generation service instance
        session: Database session
        request: GenerationRequest with mode, chunks, additional_prompt
        user_id: User ID for audit logging
        audit_service: Audit service for logging
        request_id: Request ID for audit linking
        start_time: Request start time for metrics

    Yields:
        SSE-formatted event strings

    Event types:
        - status: {"type": "status", "content": "Preparing sources..."}
        - token: {"type": "token", "content": "word"}
        - citation: {"type": "citation", "number": 1, "data": {...}}
        - done: {"type": "done", "generation_id": "...", "confidence": 0.85}
        - error: {"type": "error", "message": "..."}
    """
    # Track metrics for audit logging
    citation_count = 0
    source_doc_ids: set[str] = set()
    output_word_count = 0
    confidence_score = 0.0

    try:
        async for event in generation_service.generate_document_stream(
            session=session,
            request=request,
            user_id=user_id,
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
            kb_id=uuid.UUID(str(request.kb_id)),
            document_type=request.mode,
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
            kb_id=uuid.UUID(str(request.kb_id)),
            document_type=request.mode,
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
    if "Search" in exc_name or "Document" in exc_name or "InsufficientSources" in exc_name:
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
async def generate_document_stream(
    request_body: GenerationRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    generation_service: GenerationService = Depends(get_generation_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Generate document and stream response word-by-word.

    Streams draft generation progress using Server-Sent Events (SSE).

    Args:
        request_body: GenerationRequest with kb_id, mode, chunks, additional_prompt
        current_user: Authenticated user
        session: Database session
        generation_service: Generation service dependency
        audit_service: Audit service for logging

    Returns:
        StreamingResponse with SSE events

    Raises:
        HTTPException: 404 if KB not found/unauthorized, 400 if invalid request

    Event types:
        - status: {"type": "status", "content": "Preparing sources..."}
        - token: {"type": "token", "content": "word"}
        - citation: {"type": "citation", "number": 1, "data": {...}}
        - done: {"type": "done", "generation_id": "...", "confidence": 0.85}
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
            kb_id=uuid.UUID(str(request_body.kb_id)),
            document_type=request_body.mode,
            context=request_body.additional_prompt or "",
            selected_source_count=len(request_body.selected_chunk_ids),
            request_id=request_id,
            template_id=request_body.mode,
        )

        logger.info(
            "generate_stream_started",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            mode=request_body.mode,
            chunk_count=len(request_body.selected_chunk_ids),
            request_id=request_id,
        )

        # Return real-time streaming response
        return StreamingResponse(
            generate_sse_events(
                generation_service=generation_service,
                session=session,
                request=request_body,
                user_id=str(current_user.id),
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

    except InsufficientSourcesError as e:
        logger.warning(
            "generate_stream_insufficient_sources",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=e.message) from e

    except ValueError as e:
        # Invalid generation mode or other validation errors
        logger.warning(
            "generate_stream_invalid_request",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.error(
            "generate_stream_failed",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=503,
            detail="Generation streaming service temporarily unavailable",
        ) from e
