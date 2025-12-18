"""Chat conversation API endpoints."""

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user
from app.core.database import get_async_session
from app.core.logging import get_logger
from app.core.redis import RedisClient
from app.models.user import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    UserChatSessionMessagesResponse,
    UserChatSessionsResponse,
)
from app.services.audit_service import AuditService, get_audit_service
from app.services.conversation_service import (
    ConversationService,
    NoDocumentsError,
    NoMatchingDocumentsError,
)
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

    except NoMatchingDocumentsError as e:
        success = False
        error_message = str(e)
        logger.warning(
            "chat_no_matching_documents",
            user_id=str(current_user.id),
            kb_id=request_body.kb_id,
            query=e.query[:100] if e.query else "",
            error=error_message,
        )
        await obs.end_trace(
            trace_ctx,
            status="failed",
            error_message="NoMatchingDocumentsError",
        )
        raise HTTPException(status_code=422, detail=e.message) from e

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


# =============================================================================
# User Session History Endpoints (Story 8-0: Chat Session Persistence)
# =============================================================================


@router.get("/sessions", response_model=UserChatSessionsResponse)
async def list_user_sessions(
    kb_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """List user's chat sessions for a knowledge base.

    Returns the user's past chat sessions (grouped by conversation_id)
    for the specified KB, limited by the KB's max_chat_sessions setting.

    Args:
        kb_id: Knowledge Base ID
        current_user: Authenticated user
        session: Database session

    Returns:
        UserChatSessionsResponse with sessions, total count, and max limit

    Raises:
        HTTPException: 404 if KB not found/unauthorized

    Example response:
        {
            "sessions": [
                {
                    "conversation_id": "conv-abc123",
                    "kb_id": "kb-uuid",
                    "message_count": 8,
                    "first_message_preview": "How does OAuth 2.0 work?",
                    "last_message_at": "2025-12-18T10:30:00Z",
                    "first_message_at": "2025-12-18T10:00:00Z"
                }
            ],
            "total": 1,
            "max_sessions": 10
        }
    """
    from app.models.knowledge_base import KnowledgeBase
    from app.schemas.kb_settings import KBSettings
    from app.services.observability_query_service import ObservabilityQueryService

    try:
        # Permission check
        permission_service = get_kb_permission_service(session)
        has_permission = await permission_service.check_permission(
            user_id=str(current_user.id),
            kb_id=str(kb_id),
            permission_level="READ",
        )
        logger.info(
            "sessions_permission_check",
            user_id=str(current_user.id),
            kb_id=kb_id,
            has_permission=has_permission,
        )
        if not has_permission:
            raise HTTPException(status_code=404, detail="Knowledge Base not found")

        # Get KB settings for max_chat_sessions
        kb_result = await session.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == uuid.UUID(kb_id))
        )
        kb = kb_result.scalar_one_or_none()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge Base not found")

        # Parse KB settings to get max_chat_sessions
        kb_settings = KBSettings.model_validate(kb.settings or {})
        max_sessions = kb_settings.max_chat_sessions

        # Query user's sessions using observability service
        obs_service = ObservabilityQueryService(session)
        sessions_response = await obs_service.list_chat_sessions(
            user_id=current_user.id,
            kb_id=uuid.UUID(kb_id),
            limit=max_sessions,
        )

        # Transform to user-friendly format with first message preview
        user_sessions = []
        for item in sessions_response.items:
            # Get first user message for preview
            first_message_preview = await _get_first_user_message(
                session, item.session_id, current_user.id
            )

            user_sessions.append(
                {
                    "conversation_id": item.session_id,
                    "kb_id": str(item.kb_id) if item.kb_id else kb_id,
                    "message_count": item.message_count,
                    "first_message_preview": first_message_preview[:200]
                    if first_message_preview
                    else "",
                    "last_message_at": item.last_message_at.isoformat()
                    if item.last_message_at
                    else "",
                    "first_message_at": item.first_message_at.isoformat()
                    if item.first_message_at
                    else "",
                }
            )

        logger.info(
            "user_sessions_listed",
            user_id=str(current_user.id),
            kb_id=kb_id,
            session_count=len(user_sessions),
            max_sessions=max_sessions,
        )

        return {
            "sessions": user_sessions,
            "total": sessions_response.total,
            "max_sessions": max_sessions,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "list_user_sessions_failed",
            user_id=str(current_user.id),
            kb_id=kb_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=503, detail="Failed to list chat sessions"
        ) from e


@router.get(
    "/sessions/{conversation_id}/messages",
    response_model=UserChatSessionMessagesResponse,
)
async def get_session_messages(
    conversation_id: str,
    kb_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get messages for a specific chat session.

    Returns all messages in chronological order for the specified
    conversation_id. User must own the session.

    Args:
        conversation_id: Conversation ID (e.g., "conv-abc123")
        kb_id: Knowledge Base ID
        current_user: Authenticated user
        session: Database session

    Returns:
        UserChatSessionMessagesResponse with messages

    Raises:
        HTTPException: 404 if session not found or not owned by user

    Example response:
        {
            "conversation_id": "conv-abc123",
            "kb_id": "kb-uuid",
            "messages": [
                {
                    "role": "user",
                    "content": "How does OAuth 2.0 work?",
                    "timestamp": "2025-12-18T10:00:00Z",
                    "citations": [],
                    "confidence": null
                },
                {
                    "role": "assistant",
                    "content": "OAuth 2.0 is an authorization framework [1]...",
                    "timestamp": "2025-12-18T10:00:05Z",
                    "citations": [...],
                    "confidence": 0.87
                }
            ],
            "message_count": 2
        }
    """
    from app.models.observability import ObsChatMessage

    try:
        # Permission check for KB
        permission_service = get_kb_permission_service(session)
        has_permission = await permission_service.check_permission(
            user_id=str(current_user.id),
            kb_id=str(kb_id),
            permission_level="READ",
        )
        if not has_permission:
            raise HTTPException(status_code=404, detail="Knowledge Base not found")

        # Parse conversation_id to UUID
        try:
            conv_uuid = uuid.UUID(conversation_id.replace("conv-", ""))
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid conversation_id format"
            ) from None

        # Query messages for this conversation, ensuring user owns it
        query = (
            select(ObsChatMessage)
            .where(ObsChatMessage.conversation_id == conv_uuid)
            .where(ObsChatMessage.user_id == current_user.id)
            .where(ObsChatMessage.kb_id == uuid.UUID(kb_id))
            .order_by(ObsChatMessage.timestamp.asc())
        )
        result = await session.execute(query)
        messages = result.scalars().all()

        if not messages:
            raise HTTPException(
                status_code=404, detail="Session not found or not owned by user"
            )

        # Transform to response format
        message_items = []
        for msg in messages:
            citations = []
            if msg.attributes and "citations" in msg.attributes:
                citations = msg.attributes["citations"]

            confidence = None
            if msg.role == "assistant" and msg.attributes:
                confidence = msg.attributes.get("confidence")

            message_items.append(
                {
                    "role": msg.role,
                    "content": msg.content or "",
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else "",
                    "citations": citations,
                    "confidence": confidence,
                }
            )

        logger.info(
            "session_messages_retrieved",
            user_id=str(current_user.id),
            conversation_id=conversation_id,
            kb_id=kb_id,
            message_count=len(message_items),
        )

        return {
            "conversation_id": conversation_id,
            "kb_id": kb_id,
            "messages": message_items,
            "message_count": len(message_items),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_session_messages_failed",
            user_id=str(current_user.id),
            conversation_id=conversation_id,
            kb_id=kb_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=503, detail="Failed to retrieve session messages"
        ) from e


async def _get_first_user_message(
    session: AsyncSession,
    conversation_id: str,
    user_id: uuid.UUID,
) -> str:
    """Get the first user message content for a conversation.

    Args:
        session: Database session
        conversation_id: Conversation ID string
        user_id: User ID

    Returns:
        First user message content or empty string
    """
    from app.models.observability import ObsChatMessage

    try:
        conv_uuid = uuid.UUID(conversation_id.replace("conv-", ""))
    except ValueError:
        return ""

    query = (
        select(ObsChatMessage.content)
        .where(ObsChatMessage.conversation_id == conv_uuid)
        .where(ObsChatMessage.user_id == user_id)
        .where(ObsChatMessage.role == "user")
        .order_by(ObsChatMessage.timestamp.asc())
        .limit(1)
    )
    result = await session.execute(query)
    content = result.scalar_one_or_none()
    return content or ""
