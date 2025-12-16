"""Chat conversation API endpoints."""

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.core.logging import get_logger
from app.core.redis import RedisClient
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.audit_service import AuditService, get_audit_service
from app.services.conversation_service import ConversationService, NoDocumentsError
from app.services.kb_service import get_kb_permission_service
from app.services.observability_service import ObservabilityService
from app.services.search_service import SearchService, get_search_service

logger = get_logger()

router = APIRouter(prefix="/chat", tags=["chat"])


def get_conversation_service(
    search_service: SearchService = Depends(get_search_service),
    session: AsyncSession = Depends(get_async_session),
) -> ConversationService:
    """Dependency injection for ConversationService.

    Args:
        search_service: Search service dependency
        session: Database session for KB model lookup (Story 7-10)

    Returns:
        ConversationService instance
    """
    return ConversationService(search_service, session=session)


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    request_body: ChatRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    conversation_service: ConversationService = Depends(get_conversation_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> ChatResponse:
    """Send a chat message and receive response with citations.

    Multi-turn RAG conversation with conversation history management.
    Supports contextual follow-up questions.

    Args:
        request_body: Chat request with kb_id, message, optional conversation_id
        current_user: Authenticated user
        session: Database session
        conversation_service: Conversation service dependency
        audit_service: Audit service for logging
        permission_service: Permission service for access checks

    Returns:
        ChatResponse with answer, citations, confidence, conversation_id

    Raises:
        HTTPException: 404 if KB not found/unauthorized, 400 if no documents, 503 if service fails

    Example request:
        POST /api/v1/chat
        {
            "kb_id": "550e8400-e29b-41d4-a716-446655440000",
            "message": "How did we handle authentication?",
            "conversation_id": "conv-abc123"  // optional
        }

    Example response:
        {
            "answer": "Our authentication approach uses OAuth 2.0 [1] with PKCE...",
            "citations": [...],
            "confidence": 0.87,
            "conversation_id": "conv-abc123"
        }
    """
    start_time = time.time()
    success = True
    error_message = None
    result = {}

    # Generate conversation_id if not provided (needed for observability logging)
    conversation_id = request_body.conversation_id or f"conv-{uuid.uuid4()}"

    # Start observability trace
    obs = ObservabilityService.get_instance()
    trace_ctx = await obs.start_trace(
        name="chat.conversation",
        user_id=current_user.id,
        kb_id=uuid.UUID(request_body.kb_id),
        metadata={
            "conversation_id": conversation_id,
            "message_length": len(request_body.message),
        },
    )

    try:
        # Permission check - raises 404 if no access
        permission_service = get_kb_permission_service(session)
        has_permission = await permission_service.check_permission(
            user_id=str(current_user.id),
            kb_id=str(request_body.kb_id),
            permission_level="READ",
        )
        if not has_permission:
            raise HTTPException(status_code=404, detail="Knowledge Base not found")

        # Generate session_id from user (using user_id as session scope)
        session_id = str(current_user.id)

        # Log user message (privacy: message length only)
        await obs.log_chat_message(
            ctx=trace_ctx,
            role="user",
            content="",  # Privacy: don't log actual content
            conversation_id=uuid.UUID(conversation_id.replace("conv-", ""))
            if conversation_id.startswith("conv-")
            else uuid.UUID(conversation_id),
        )

        # Send message with trace context for internal spans
        result = await conversation_service.send_message(
            session_id=session_id,
            kb_id=request_body.kb_id,
            user_id=str(current_user.id),
            message=request_body.message,
            conversation_id=conversation_id,
            trace_ctx=trace_ctx,
        )

        response = ChatResponse(**result)

        # Log assistant message with same conversation_id parsing
        response_time_ms = int((time.time() - start_time) * 1000)
        result_conv_id = result.get("conversation_id", conversation_id)
        await obs.log_chat_message(
            ctx=trace_ctx,
            role="assistant",
            content="",  # Privacy: don't log actual content
            conversation_id=uuid.UUID(result_conv_id.replace("conv-", ""))
            if result_conv_id.startswith("conv-")
            else uuid.UUID(result_conv_id),
            latency_ms=response_time_ms,
        )

        logger.info(
            "chat_message_success",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            conversation_id=result.get("conversation_id"),
            citation_count=len(result.get("citations", [])),
            confidence=result.get("confidence", 0.0),
        )

        # End trace successfully
        await obs.end_trace(trace_ctx, status="completed")
        return response

    except HTTPException as e:
        # End trace with failed status for 404/etc
        await obs.end_trace(
            trace_ctx,
            status="failed",
            error_message=f"HTTPException: {e.status_code}",
        )
        raise

    except NoDocumentsError as e:
        success = False
        error_message = str(e)
        logger.warning(
            "chat_no_documents",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            error=error_message,
        )
        await obs.end_trace(
            trace_ctx,
            status="failed",
            error_message="NoDocumentsError",
        )
        raise HTTPException(status_code=400, detail=e.message) from e

    except Exception as e:
        success = False
        error_message = str(e)
        logger.error(
            "chat_message_failed",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            error=error_message,
            exc_info=True,
        )
        await obs.end_trace(
            trace_ctx,
            status="failed",
            error_message=type(e).__name__,
        )
        raise HTTPException(
            status_code=503, detail="Chat service temporarily unavailable"
        ) from e

    finally:
        # Async audit logging (non-blocking)
        response_time_ms = int((time.time() - start_time) * 1000)

        try:
            await audit_service.log_event(
                action="chat.message",
                resource_type="conversation",
                user_id=current_user.id,
                resource_id=result.get("conversation_id", "unknown"),
                details={
                    "kb_id": str(request_body.kb_id),
                    "message_length": len(request_body.message),
                    "response_length": len(result.get("answer", "")),
                    "citation_count": len(result.get("citations", [])),
                    "confidence": result.get("confidence", 0.0),
                    "response_time_ms": response_time_ms,
                    "success": success,
                    "error": error_message,
                },
            )
        except Exception as audit_error:
            # Never fail request due to audit logging
            logger.error(
                "audit_logging_failed",
                error=str(audit_error),
                user_id=str(current_user.id),
            )


@router.post("/new")
async def new_conversation(
    kb_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Start a new conversation for a knowledge base.

    Clears any existing conversation history and generates a fresh conversation ID.

    Args:
        kb_id: Knowledge Base ID
        current_user: Authenticated user
        session: Database session

    Returns:
        Dict with conversation_id and kb_id

    Raises:
        HTTPException: 404 if KB not found/unauthorized

    Example response:
        {
            "conversation_id": "conv-550e8400-e29b-41d4-a716-446655440000",
            "kb_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    """
    try:
        # Permission check
        permission_service = get_kb_permission_service(session)
        await permission_service.check_permission(
            user_id=str(current_user.id),
            kb_id=str(kb_id),
            permission_level="READ",
        )

        # Generate new conversation ID
        conversation_id = f"conv-{uuid.uuid4()}"

        # Clear any existing conversation
        redis_client = await RedisClient.get_client()
        session_id = str(current_user.id)
        key = f"conversation:{session_id}:{kb_id}"
        await redis_client.delete(key)

        logger.info(
            "conversation_started",
            user_id=str(current_user.id),
            kb_id=kb_id,
            conversation_id=conversation_id,
        )

        return {
            "conversation_id": conversation_id,
            "kb_id": kb_id,
        }

    except Exception as e:
        logger.error(
            "new_conversation_failed",
            user_id=str(current_user.id),
            kb_id=kb_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=503, detail="Failed to start new conversation"
        ) from e


@router.delete("/clear")
async def clear_conversation(
    kb_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str | bool]:
    """Clear conversation history with 30-second undo capability.

    Moves conversation to backup key with 30s TTL for undo.

    Args:
        kb_id: Knowledge Base ID
        current_user: Authenticated user
        session: Database session

    Returns:
        Dict with message and undo_available flag

    Raises:
        HTTPException: 404 if KB not found/unauthorized

    Example response:
        {
            "message": "Conversation cleared",
            "undo_available": true
        }
    """
    try:
        # Permission check
        permission_service = get_kb_permission_service(session)
        await permission_service.check_permission(
            user_id=str(current_user.id),
            kb_id=str(kb_id),
            permission_level="READ",
        )

        redis_client = await RedisClient.get_client()
        session_id = str(current_user.id)
        key = f"conversation:{session_id}:{kb_id}"
        backup_key = f"{key}:backup"

        # Check if conversation exists
        exists = await redis_client.exists(key)
        if exists:
            # Get current conversation data
            conversation_data = await redis_client.get(key)

            # Store in backup with 30s TTL
            await redis_client.setex(backup_key, 30, conversation_data)

            # Delete original
            await redis_client.delete(key)

            logger.info(
                "conversation_cleared",
                user_id=str(current_user.id),
                kb_id=kb_id,
                backup_available=True,
            )

            return {
                "message": "Conversation cleared",
                "undo_available": True,
            }

        logger.info(
            "conversation_clear_no_history",
            user_id=str(current_user.id),
            kb_id=kb_id,
        )

        return {
            "message": "No conversation to clear",
            "undo_available": False,
        }

    except Exception as e:
        logger.error(
            "clear_conversation_failed",
            user_id=str(current_user.id),
            kb_id=kb_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=503, detail="Failed to clear conversation"
        ) from e


@router.post("/undo-clear")
async def undo_clear_conversation(
    kb_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str | bool]:
    """Restore cleared conversation from backup (30-second window).

    Args:
        kb_id: Knowledge Base ID
        current_user: Authenticated user
        session: Database session

    Returns:
        Dict with message and success status

    Raises:
        HTTPException: 404 if KB not found/unauthorized, 410 if backup expired

    Example response:
        {
            "message": "Conversation restored",
            "success": true
        }
    """
    try:
        # Permission check
        permission_service = get_kb_permission_service(session)
        await permission_service.check_permission(
            user_id=str(current_user.id),
            kb_id=str(kb_id),
            permission_level="READ",
        )

        redis_client = await RedisClient.get_client()
        session_id = str(current_user.id)
        key = f"conversation:{session_id}:{kb_id}"
        backup_key = f"{key}:backup"

        # Check if backup exists
        backup_exists = await redis_client.exists(backup_key)
        if not backup_exists:
            raise HTTPException(
                status_code=410, detail="Undo window expired (30 seconds)"
            )

        # Restore from backup
        conversation_data = await redis_client.get(backup_key)
        await redis_client.setex(key, 86400, conversation_data)  # 24h TTL

        # Delete backup
        await redis_client.delete(backup_key)

        logger.info(
            "conversation_restored",
            user_id=str(current_user.id),
            kb_id=kb_id,
        )

        return {
            "message": "Conversation restored",
            "success": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "undo_clear_failed",
            user_id=str(current_user.id),
            kb_id=kb_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=503, detail="Failed to restore conversation"
        ) from e


@router.get("/history")
async def get_conversation_history(
    kb_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> dict[str, list | int]:
    """Retrieve conversation history for a knowledge base.

    Args:
        kb_id: Knowledge Base ID
        current_user: Authenticated user
        session: Database session
        conversation_service: Conversation service dependency

    Returns:
        Dict with messages array

    Raises:
        HTTPException: 404 if KB not found/unauthorized

    Example response:
        {
            "messages": [
                {
                    "role": "user",
                    "content": "How did we handle auth?",
                    "timestamp": "2025-11-27T10:30:00Z"
                },
                {
                    "role": "assistant",
                    "content": "Our auth uses OAuth 2.0 [1]...",
                    "citations": [...],
                    "confidence": 0.87,
                    "timestamp": "2025-11-27T10:30:02Z"
                }
            ],
            "message_count": 2
        }
    """
    try:
        # Permission check
        permission_service = get_kb_permission_service(session)
        await permission_service.check_permission(
            user_id=str(current_user.id),
            kb_id=str(kb_id),
            permission_level="READ",
        )

        # Get history
        session_id = str(current_user.id)
        history = await conversation_service.get_history(session_id, kb_id)

        logger.info(
            "conversation_history_retrieved",
            user_id=str(current_user.id),
            kb_id=kb_id,
            message_count=len(history),
        )

        return {
            "messages": history,
            "message_count": len(history),
        }

    except Exception as e:
        logger.error(
            "get_history_failed",
            user_id=str(current_user.id),
            kb_id=kb_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=503, detail="Failed to retrieve conversation history"
        ) from e
