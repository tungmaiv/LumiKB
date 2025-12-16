"""Observability Admin API endpoints.

Story 9-7: Observability Admin API

Provides REST endpoints for querying observability data including traces,
chat history, document processing events, and aggregated statistics.
All endpoints require admin authentication.
"""

import re
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_administrator
from app.core.database import get_async_session
from app.models.user import User
from app.schemas.observability import (
    ChatHistoryResponse,
    ChatSessionsResponse,
    DocumentTimelineResponse,
    ObservabilityStatsResponse,
    TraceDetailResponse,
    TraceListResponse,
)
from app.services.observability_query_service import ObservabilityQueryService

router = APIRouter(prefix="/observability", tags=["observability"])

# W3C Trace ID pattern: 32 hex characters
TRACE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def validate_trace_id(trace_id: str) -> str:
    """Validate W3C trace ID format (32 hex characters)."""
    if not TRACE_ID_PATTERN.match(trace_id.lower()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trace_id format. Expected 32 hexadecimal characters.",
        )
    return trace_id.lower()


@router.get("/traces", response_model=TraceListResponse)
async def list_traces(
    operation_type: str | None = Query(
        default=None,
        description="Filter by operation type (e.g., chat_completion, document_processing)",
    ),
    trace_status: str | None = Query(
        default=None,
        alias="status",
        description="Filter by status: in_progress, completed, failed",
    ),
    user_id: UUID | None = Query(default=None, description="Filter by user ID"),
    kb_id: UUID | None = Query(default=None, description="Filter by knowledge base ID"),
    start_date: datetime | None = Query(
        default=None, description="Filter traces after this date"
    ),
    end_date: datetime | None = Query(
        default=None, description="Filter traces before this date"
    ),
    search: str | None = Query(
        default=None,
        description="Search in trace ID, document ID, or trace name (case-insensitive)",
    ),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=20, ge=1, le=100, description="Maximum records to return (max 100)"
    ),
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> TraceListResponse:
    """List traces with filters and pagination.

    Returns a paginated list of traces matching the specified filters.
    Traces are ordered by start time (newest first).

    **Requires admin authentication.**
    """
    service = ObservabilityQueryService(session)
    result = await service.list_traces(
        operation_type=operation_type,
        status=trace_status,
        user_id=user_id,
        kb_id=kb_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
        skip=skip,
        limit=limit,
    )
    return result


@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
async def get_trace(
    trace_id: str,
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> TraceDetailResponse:
    """Get trace detail with all child spans.

    Returns the trace with all associated spans ordered by start time.

    **Requires admin authentication.**
    """
    validated_trace_id = validate_trace_id(trace_id)
    service = ObservabilityQueryService(session)
    result = await service.get_trace_with_spans(validated_trace_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace not found: {trace_id}",
        )

    return result


@router.get("/chat-history", response_model=ChatHistoryResponse)
async def get_chat_history(
    user_id: UUID | None = Query(default=None, description="Filter by user ID"),
    kb_id: UUID | None = Query(default=None, description="Filter by knowledge base ID"),
    session_id: str | None = Query(
        default=None, description="Filter by conversation session ID"
    ),
    search_query: str | None = Query(
        default=None, description="Search within message content (case-insensitive)"
    ),
    start_date: datetime | None = Query(
        default=None, description="Filter messages after this date"
    ),
    end_date: datetime | None = Query(
        default=None, description="Filter messages before this date"
    ),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=50, ge=1, le=500, description="Maximum records to return (max 500)"
    ),
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> ChatHistoryResponse:
    """Query persistent chat history with filters.

    Returns a paginated list of chat messages matching the specified filters.
    Messages are ordered by creation time (newest first).

    **Requires admin authentication.**
    """
    service = ObservabilityQueryService(session)
    result = await service.list_chat_messages(
        user_id=user_id,
        kb_id=kb_id,
        session_id=session_id,
        search_query=search_query,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return result


@router.get("/chat-sessions", response_model=ChatSessionsResponse)
async def list_chat_sessions(
    user_id: UUID | None = Query(default=None, description="Filter by user ID"),
    kb_id: UUID | None = Query(default=None, description="Filter by knowledge base ID"),
    search_query: str | None = Query(
        default=None, description="Search within message content (case-insensitive)"
    ),
    start_date: datetime | None = Query(
        default=None, description="Filter sessions with messages after this date"
    ),
    end_date: datetime | None = Query(
        default=None, description="Filter sessions with messages before this date"
    ),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=20, ge=1, le=100, description="Maximum records to return (max 100)"
    ),
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> ChatSessionsResponse:
    """List chat sessions grouped by conversation.

    Returns a paginated list of chat sessions (conversations) with aggregated
    data including user name, KB name, message count, and timestamps.
    Sessions are ordered by last message time (newest first).

    **Requires admin authentication.**
    """
    service = ObservabilityQueryService(session)
    result = await service.list_chat_sessions(
        user_id=user_id,
        kb_id=kb_id,
        search_query=search_query,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return result


@router.get(
    "/documents/{document_id}/timeline", response_model=DocumentTimelineResponse
)
async def get_document_timeline(
    document_id: UUID,
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> DocumentTimelineResponse:
    """Get document processing events timeline.

    Returns all processing events for a specific document ordered by timestamp.

    **Requires admin authentication.**
    """
    service = ObservabilityQueryService(session)
    result = await service.get_document_timeline(document_id)

    if result is None or len(result.events) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No processing events found for document: {document_id}",
        )

    return result


@router.get("/stats", response_model=ObservabilityStatsResponse)
async def get_stats(
    time_period: str = Query(
        default="day",
        pattern="^(hour|day|week|month)$",
        description="Aggregation period: hour, day, week, month",
    ),
    kb_id: UUID | None = Query(default=None, description="Filter by knowledge base ID"),
    user_id: UUID | None = Query(default=None, description="Filter by user ID"),
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> ObservabilityStatsResponse:
    """Get aggregated observability statistics.

    Returns aggregated metrics for LLM usage, document processing, and chat activity
    for the specified time period.

    **Requires admin authentication.**
    """
    service = ObservabilityQueryService(session)
    result = await service.get_aggregated_stats(
        time_period=time_period,
        kb_id=kb_id,
        user_id=user_id,
    )
    return result
