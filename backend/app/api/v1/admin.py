"""Admin API routes.

Provides:
- GET /api/v1/admin/users - List all users with pagination (admin only)
- POST /api/v1/admin/users - Create new user (admin only)
- PATCH /api/v1/admin/users/{user_id} - Update user status (admin only)
- POST /api/v1/admin/audit/export - Export audit logs in CSV or JSON format (admin only)
"""

import csv
import io
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    UserManager,
    get_current_administrator,
    get_current_operator_or_admin,
    get_user_manager,
)
from app.core.database import get_async_session
from app.core.redis import get_client_ip
from app.integrations.minio_client import minio_service
from app.integrations.qdrant_client import qdrant_service
from app.models.audit import AuditEvent
from app.models.outbox import Outbox
from app.models.user import User
from app.schemas.admin import (
    AdminStats,
    AuditEventResponse,
    AuditExportRequest,
    AuditLogFilterRequest,
    BulkRetryRequest,
    BulkRetryResponse,
    CleanupError,
    CleanupResponse,
    ConfigSetting,
    ConfigUpdateRequest,
    ConfigUpdateResponse,
    DocumentStatusFilter,
    FeedbackAnalyticsResponse,
    LLMConfig,
    LLMConfigUpdateRequest,
    LLMConfigUpdateResponse,
    LLMHealthResponse,
    PaginatedAuditResponse,
    QueueStatus,
    RewriterModelResponse,
    RewriterModelUpdateRequest,
    TableCleanupResult,
    TaskInfo,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.kb_stats import KBDetailedStats
from app.schemas.user import AdminUserUpdate, UserCreate, UserRead
from app.services.admin_stats_service import AdminStatsService
from app.services.audit_service import get_audit_service
from app.services.config_service import ConfigService
from app.services.feedback_analytics_service import FeedbackAnalyticsService
from app.services.kb_stats_service import KBStatsService
from app.services.queue_monitor_service import QueueMonitorService
from app.services.retention_service import RetentionService
from app.workers.outbox_tasks import MAX_OUTBOX_ATTEMPTS


class OutboxStats(BaseModel):
    """Outbox queue statistics response."""

    pending_events: int
    failed_events: int
    processed_last_hour: int
    processed_last_24h: int
    queue_depth: int
    average_processing_time_ms: float | None


class AuditGenerationEventResponse(BaseModel):
    """Single audit generation event response (legacy, Story 4.10)."""

    id: UUID
    timestamp: datetime
    user_id: UUID | None
    user_email: str | None
    action: str
    kb_id: str | None
    document_type: str | None
    citation_count: int | None
    generation_time_ms: int | None
    success: bool | None
    error_message: str | None
    request_id: str | None


class AuditMetrics(BaseModel):
    """Aggregated audit metrics."""

    total_requests: int
    success_count: int
    failure_count: int
    avg_generation_time_ms: float | None
    total_citations: int


class AuditGenerationResponse(BaseModel):
    """Audit generation query response."""

    events: list[AuditGenerationEventResponse]
    pagination: PaginationMeta
    metrics: AuditMetrics


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/stats",
    response_model=AdminStats,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def get_admin_stats(
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> AdminStats:
    """Get system-wide statistics for admin dashboard.

    Returns comprehensive metrics including:
    - User counts (total, active, inactive)
    - Knowledge base counts by status
    - Document counts by processing status
    - Storage usage statistics
    - Search and generation activity (24h, 7d, 30d)
    - Trend data for sparkline visualization (last 30 days)

    Results cached in Redis for 5 minutes to reduce database load.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    **Performance:**
    - < 500ms with Redis cache hit
    - < 2s on cache miss (DB aggregation)

    **Known Limitations:**
    - Active users currently based on created_at (last 30 days) as proxy
      for last_active. This will be improved in a future migration to track
      actual user activity.

    Returns:
        AdminStats: Comprehensive system statistics.
    """
    service = AdminStatsService(session)
    return await service.get_dashboard_stats()


@router.get(
    "/users",
    response_model=PaginatedResponse[UserRead],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def list_users(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        default=20, ge=1, le=100, description="Number of records to return"
    ),
    is_active: bool | None = Query(
        default=None, description="Filter by active status (True/False/None for all)"
    ),
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[UserRead]:
    """List all users with pagination (admin only).

    Args:
        skip: Number of records to skip (default 0).
        limit: Number of records to return (default 20, max 100).
        is_active: Filter by active status (True=active only, False=inactive only, None=all).
        admin: Current authenticated superuser.
        session: Database session.

    Returns:
        PaginatedResponse[UserRead]: Paginated list of users.
    """
    # Build base query with optional is_active filter
    base_query = select(User)
    count_query = select(func.count(User.id))

    if is_active is not None:
        base_query = base_query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    # Get total count
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated results
    result = await session.execute(
        base_query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    users = result.scalars().all()

    # Calculate pagination meta
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    return PaginatedResponse[UserRead](
        data=[UserRead.model_validate(u) for u in users],
        meta=PaginationMeta(
            total=total,
            page=page,
            per_page=limit,
            total_pages=total_pages,
        ),
    )


@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid email format or password too short"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin"},
        409: {"description": "Email already exists"},
    },
)
async def create_user(
    request: Request,
    background_tasks: BackgroundTasks,
    user_data: UserCreate,
    admin: User = Depends(get_current_administrator),
    user_manager: UserManager = Depends(get_user_manager),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Create a new user (admin only).

    Args:
        request: FastAPI request object.
        background_tasks: Background task manager for async audit logging.
        user_data: User creation data (email, password).
        admin: Current authenticated superuser.
        user_manager: FastAPI-Users user manager.
        session: Database session.

    Returns:
        UserRead: The created user.

    Raises:
        HTTPException: 409 if email already exists.
    """
    # Check email uniqueness
    existing_user = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_user.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user via user_manager (handles password hashing)
    new_user = await user_manager.create(user_data, request=request)

    # Fire-and-forget audit logging
    ip_address = get_client_ip(request)
    background_tasks.add_task(
        _log_audit_event,
        "user.admin_created",
        admin.id,
        new_user.id,
        ip_address,
        {"email": new_user.email, "created_by_admin_id": str(admin.id)},
    )

    return new_user


@router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin"},
        404: {"description": "User not found"},
    },
)
async def update_user(
    user_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    user_update: AdminUserUpdate,
    admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Update user status (admin only).

    Args:
        user_id: Target user UUID.
        request: FastAPI request object.
        background_tasks: Background task manager for async audit logging.
        user_update: Update data (is_active).
        admin: Current authenticated superuser.
        session: Database session.

    Returns:
        UserRead: The updated user.

    Raises:
        HTTPException: 404 if user not found.
    """
    # Get target user
    result = await session.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Track changes for audit logging
    ip_address = get_client_ip(request)

    # Update is_active if provided
    if user_update.is_active is not None:
        old_value = target_user.is_active
        target_user.is_active = user_update.is_active
        await session.commit()
        await session.refresh(target_user)

        # Determine audit action based on change
        if user_update.is_active and not old_value:
            audit_action = "user.activated"
        elif not user_update.is_active and old_value:
            audit_action = "user.deactivated"
        else:
            audit_action = None

        if audit_action:
            background_tasks.add_task(
                _log_audit_event,
                audit_action,
                admin.id,
                target_user.id,
                ip_address,
                {
                    "target_user_email": target_user.email,
                    "is_active": target_user.is_active,
                    "changed_by_admin_id": str(admin.id),
                },
            )

    return target_user


async def _log_audit_event(
    action: str,
    admin_user_id: UUID,
    target_user_id: UUID,
    ip_address: str,
    details: dict | None = None,
) -> None:
    """Fire-and-forget audit logging.

    Args:
        action: The audit action name.
        admin_user_id: The admin user's UUID (who performed the action).
        target_user_id: The target user's UUID (who was affected).
        ip_address: The client's IP address.
        details: Additional details to log.
    """
    try:
        from app.services.audit_service import audit_service

        await audit_service.log_event(
            action=action,
            user_id=admin_user_id,
            resource_type="user",
            resource_id=target_user_id,
            details=details,
            ip_address=ip_address,
        )
    except Exception:
        # Audit logging should never fail the request
        pass


@router.get(
    "/outbox/stats",
    response_model=OutboxStats,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def get_outbox_stats(
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> OutboxStats:
    """Get outbox queue statistics (admin only).

    Args:
        admin: Current authenticated superuser.
        session: Database session.

    Returns:
        OutboxStats: Queue statistics including pending, failed, and processed counts.
    """
    now = datetime.now(UTC)
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(hours=24)

    # Pending events (unprocessed and not failed)
    pending_result = await session.execute(
        select(func.count(Outbox.id))
        .where(Outbox.processed_at.is_(None))
        .where(Outbox.attempts < MAX_OUTBOX_ATTEMPTS)
    )
    pending_events = pending_result.scalar() or 0

    # Failed events (max attempts reached)
    failed_result = await session.execute(
        select(func.count(Outbox.id)).where(Outbox.attempts >= MAX_OUTBOX_ATTEMPTS)
    )
    failed_events = failed_result.scalar() or 0

    # Processed in last hour
    processed_hour_result = await session.execute(
        select(func.count(Outbox.id)).where(Outbox.processed_at >= one_hour_ago)
    )
    processed_last_hour = processed_hour_result.scalar() or 0

    # Processed in last 24 hours
    processed_day_result = await session.execute(
        select(func.count(Outbox.id)).where(Outbox.processed_at >= one_day_ago)
    )
    processed_last_24h = processed_day_result.scalar() or 0

    # Queue depth (same as pending)
    queue_depth = pending_events

    # Average processing time for last 100 processed events
    # Calculate as (processed_at - created_at) in milliseconds
    avg_time_result = await session.execute(
        select(
            func.avg(
                func.extract("epoch", Outbox.processed_at)
                - func.extract("epoch", Outbox.created_at)
            )
            * 1000  # Convert seconds to milliseconds
        )
        .where(Outbox.processed_at.isnot(None))
        .order_by(Outbox.processed_at.desc())
        .limit(100)
    )
    avg_time_ms = avg_time_result.scalar()
    average_processing_time_ms = float(avg_time_ms) if avg_time_ms else None

    return OutboxStats(
        pending_events=pending_events,
        failed_events=failed_events,
        processed_last_hour=processed_last_hour,
        processed_last_24h=processed_last_24h,
        queue_depth=queue_depth,
        average_processing_time_ms=average_processing_time_ms,
    )


@router.get(
    "/audit/generation",
    response_model=AuditGenerationResponse,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def get_generation_audit_logs(
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
    start_date: datetime | None = Query(None, description="Filter by start date (UTC)"),
    end_date: datetime | None = Query(None, description="Filter by end date (UTC)"),
    user_id: UUID | None = Query(None, description="Filter by user ID"),
    kb_id: UUID | None = Query(None, description="Filter by knowledge base ID"),
    action_type: Literal[
        "generation.request",
        "generation.complete",
        "generation.failed",
        "generation.feedback",
        "document.export",
    ]
    | None = Query(None, description="Filter by action type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
) -> AuditGenerationResponse:
    """Query generation audit logs (admin only).

    Returns audit events with filters, pagination, and aggregated metrics.

    **Permissions:** Requires is_superuser=true (403 for non-admin).

    **Filters:**
    - start_date: Filter events after this timestamp (UTC)
    - end_date: Filter events before this timestamp (UTC)
    - user_id: Filter by user who performed the action
    - kb_id: Filter by knowledge base ID
    - action_type: Filter by specific action type

    **Pagination:**
    - page: Page number (default 1)
    - per_page: Items per page (default 50, max 100)

    **Response:**
    - events: List of audit events with user email joined
    - pagination: Page metadata with accurate total count
    - metrics: Aggregated metrics (total_requests, success_count, etc.)
    """
    try:
        # Build base query
        query = select(AuditEvent).where(
            AuditEvent.action.in_(
                [
                    "generation.request",
                    "generation.complete",
                    "generation.failed",
                    "generation.feedback",
                    "document.export",
                ]
            )
        )

        # Apply filters
        if start_date:
            query = query.where(AuditEvent.timestamp >= start_date)
        if end_date:
            query = query.where(AuditEvent.timestamp <= end_date)
        if user_id:
            query = query.where(AuditEvent.user_id == user_id)
        if kb_id:
            query = query.where(AuditEvent.details["kb_id"].astext == str(kb_id))
        if action_type:
            query = query.where(AuditEvent.action == action_type)

        # Get total count for pagination
        count_query = select(func.count(AuditEvent.id)).where(
            AuditEvent.action.in_(
                [
                    "generation.request",
                    "generation.complete",
                    "generation.failed",
                    "generation.feedback",
                    "document.export",
                ]
            )
        )
        if start_date:
            count_query = count_query.where(AuditEvent.timestamp >= start_date)
        if end_date:
            count_query = count_query.where(AuditEvent.timestamp <= end_date)
        if user_id:
            count_query = count_query.where(AuditEvent.user_id == user_id)
        if kb_id:
            count_query = count_query.where(
                AuditEvent.details["kb_id"].astext == str(kb_id)
            )
        if action_type:
            count_query = count_query.where(AuditEvent.action == action_type)

        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(AuditEvent.timestamp.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        # Execute query
        result = await session.execute(query)
        events = result.scalars().all()

        # Join user emails
        user_ids = {event.user_id for event in events if event.user_id}
        user_emails = {}
        if user_ids:
            users_result = await session.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_emails = dict(users_result.all())

        # Build response events
        event_responses = []
        for event in events:
            details = event.details or {}
            event_responses.append(
                AuditGenerationEventResponse(
                    id=event.id,
                    timestamp=event.timestamp,
                    user_id=event.user_id,
                    user_email=user_emails.get(event.user_id)
                    if event.user_id
                    else None,
                    action=event.action,
                    kb_id=details.get("kb_id"),
                    document_type=details.get("document_type"),
                    citation_count=details.get("citation_count"),
                    generation_time_ms=details.get("generation_time_ms"),
                    success=details.get("success"),
                    error_message=details.get("error_message"),
                    request_id=details.get("request_id"),
                )
            )

        # Calculate aggregated metrics
        metrics_query = select(AuditEvent).where(
            AuditEvent.action.in_(
                [
                    "generation.request",
                    "generation.complete",
                    "generation.failed",
                ]
            )
        )
        if start_date:
            metrics_query = metrics_query.where(AuditEvent.timestamp >= start_date)
        if end_date:
            metrics_query = metrics_query.where(AuditEvent.timestamp <= end_date)
        if user_id:
            metrics_query = metrics_query.where(AuditEvent.user_id == user_id)
        if kb_id:
            metrics_query = metrics_query.where(
                AuditEvent.details["kb_id"].astext == str(kb_id)
            )

        metrics_result = await session.execute(metrics_query)
        all_events = metrics_result.scalars().all()

        total_requests = sum(1 for e in all_events if e.action == "generation.request")
        success_count = sum(1 for e in all_events if e.action == "generation.complete")
        failure_count = sum(1 for e in all_events if e.action == "generation.failed")

        generation_times = [
            e.details.get("generation_time_ms")
            for e in all_events
            if e.details
            and e.details.get("generation_time_ms")
            and e.action in ["generation.complete", "generation.failed"]
        ]
        avg_generation_time_ms = (
            sum(generation_times) / len(generation_times) if generation_times else None
        )

        total_citations = sum(
            e.details.get("citation_count", 0)
            for e in all_events
            if e.details and e.action == "generation.complete"
        )

        # Calculate total_pages
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

        return AuditGenerationResponse(
            events=event_responses,
            pagination=PaginationMeta(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=total_pages,
            ),
            metrics=AuditMetrics(
                total_requests=total_requests,
                success_count=success_count,
                failure_count=failure_count,
                avg_generation_time_ms=avg_generation_time_ms,
                total_citations=total_citations,
            ),
        )

    except Exception as e:
        # Log the actual error for debugging
        import traceback

        print(f"Error in get_generation_audit_logs: {type(e).__name__}: {str(e)}")
        print(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audit logs: {type(e).__name__}: {str(e)}",
        ) from e


@router.post(
    "/audit/logs",
    response_model=PaginatedAuditResponse,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def query_audit_logs(
    filter_request: AuditLogFilterRequest,
    _current_user: User = Depends(get_current_administrator),
    db: AsyncSession = Depends(get_async_session),
) -> PaginatedAuditResponse:
    """Query audit logs with filtering and pagination.

    Requires admin role (is_superuser=True).

    Args:
        filter_request: Filter criteria and pagination settings
        current_user: Current authenticated superuser
        db: Database session

    Returns:
        PaginatedAuditResponse with events and pagination metadata

    Filters:
        - event_type: Filter by event type (exact match)
        - user_email: Filter by user email (case-insensitive partial match)
        - start_date: Filter events >= start_date (ISO 8601)
        - end_date: Filter events <= end_date (ISO 8601)
        - resource_type: Filter by resource type (exact match)
        - page: Page number (1-indexed, default 1)
        - page_size: Results per page (default 50, max 10000)

    Returns paginated audit events with PII redacted by default.
    """
    # Query audit logs with filters
    audit_service = get_audit_service()
    events, total_count = await audit_service.query_audit_logs(
        db=db,
        start_date=filter_request.start_date,
        end_date=filter_request.end_date,
        user_email=filter_request.user_email,
        event_type=filter_request.event_type.value
        if filter_request.event_type
        else None,
        resource_type=filter_request.resource_type.value
        if filter_request.resource_type
        else None,
        page=filter_request.page,
        page_size=filter_request.page_size,
    )

    # Redact PII (no export_pii permission check yet - always redact for now)
    # TODO: Add has_permission(current_user, "export_pii") check in future story
    redacted_events = [audit_service.redact_pii(event) for event in events]

    # Convert to response schema
    # Need to fetch user emails for events
    user_ids = [e.user_id for e in redacted_events if e.user_id]
    user_email_map = {}
    if user_ids:
        result = await db.execute(
            select(User.id, User.email).where(User.id.in_(user_ids))
        )
        user_email_map = {row[0]: row[1] for row in result.all()}

    event_responses = [
        AuditEventResponse(
            id=event.id,
            timestamp=event.timestamp,
            user_id=event.user_id,
            user_email=user_email_map.get(event.user_id) if event.user_id else None,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=str(event.resource_id) if event.resource_id else None,
            ip_address=event.ip_address,
            details=event.details,
        )
        for event in redacted_events
    ]

    # Calculate pagination metadata
    has_more = (filter_request.page * filter_request.page_size) < total_count

    return PaginatedAuditResponse(
        events=event_responses,
        total=total_count,
        page=filter_request.page,
        page_size=filter_request.page_size,
        has_more=has_more,
    )


async def export_csv_stream(
    audit_service,
    db: AsyncSession,
    filters: dict,
    include_pii: bool = False,
) -> AsyncGenerator[str, None]:
    """Stream audit events as CSV format.

    Args:
        audit_service: AuditService instance
        db: Database session
        filters: Filter dictionary (start_date, end_date, user_email, event_type, resource_type)
        include_pii: Whether to include PII (default False)

    Yields:
        str: CSV rows as newline-terminated strings
    """
    # CSV header (matches AuditEvent model field order - AC-5.3.4)
    csv_fields = [
        "id",
        "timestamp",
        "user_id",
        "user_email",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
        "details",
    ]

    # Yield CSV header row
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=csv_fields)
    writer.writeheader()
    yield buffer.getvalue()

    # Fetch user emails for all events (for efficient joining)
    user_email_map = {}

    # Stream events in batches
    async for batch in audit_service.get_events_stream(
        db=db,
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
        user_email=filters.get("user_email"),
        event_type=filters.get("event_type"),
        resource_type=filters.get("resource_type"),
        batch_size=1000,
    ):
        # Fetch user emails for this batch
        user_ids = [e.user_id for e in batch if e.user_id]
        if user_ids:
            result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_email_map.update(dict(result.all()))

        # Convert batch to CSV rows
        for event in batch:
            # Apply PII redaction if needed
            if not include_pii:
                event = audit_service.redact_pii(event)

            row = {
                "id": str(event.id),
                "timestamp": event.timestamp.isoformat(),
                "user_id": str(event.user_id) if event.user_id else "",
                "user_email": user_email_map.get(event.user_id, "")
                if event.user_id
                else "",
                "action": event.action or "",
                "resource_type": event.resource_type or "",
                "resource_id": str(event.resource_id) if event.resource_id else "",
                "ip_address": event.ip_address or "",
                "details": json.dumps(event.details) if event.details else "",
            }

            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=csv_fields)
            writer.writerow(row)
            yield buffer.getvalue()


async def export_json_stream(
    audit_service,
    db: AsyncSession,
    filters: dict,
    include_pii: bool = False,
) -> AsyncGenerator[str, None]:
    """Stream audit events as JSON array format.

    Args:
        audit_service: AuditService instance
        db: Database session
        filters: Filter dictionary (start_date, end_date, user_email, event_type, resource_type)
        include_pii: Whether to include PII (default False)

    Yields:
        str: JSON array chunks (opening bracket, objects with commas, closing bracket)
    """
    # Yield opening bracket
    yield "["

    # Fetch user emails for all events (for efficient joining)
    user_email_map = {}
    first_event = True

    # Stream events in batches
    async for batch in audit_service.get_events_stream(
        db=db,
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
        user_email=filters.get("user_email"),
        event_type=filters.get("event_type"),
        resource_type=filters.get("resource_type"),
        batch_size=1000,
    ):
        # Fetch user emails for this batch
        user_ids = [e.user_id for e in batch if e.user_id]
        if user_ids:
            result = await db.execute(
                select(User.id, User.email).where(User.id.in_(user_ids))
            )
            user_email_map.update(dict(result.all()))

        # Convert batch to JSON objects
        for event in batch:
            # Apply PII redaction if needed
            if not include_pii:
                event = audit_service.redact_pii(event)

            obj = {
                "id": str(event.id),
                "timestamp": event.timestamp.isoformat(),
                "user_id": str(event.user_id) if event.user_id else None,
                "user_email": user_email_map.get(event.user_id)
                if event.user_id
                else None,
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": str(event.resource_id) if event.resource_id else None,
                "ip_address": event.ip_address,
                "details": event.details,
            }

            # Add comma before subsequent events
            if not first_event:
                yield ","
            first_event = False

            # Yield JSON object
            yield json.dumps(obj)

    # Yield closing bracket
    yield "]"


@router.post(
    "/audit/export",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def export_audit_logs(
    export_request: AuditExportRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_administrator),
    db: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """Export audit logs in CSV or JSON format with streaming.

    Requires admin role (is_superuser=True).

    Args:
        export_request: Export format and filter criteria
        request: FastAPI request object (for audit logging)
        background_tasks: Background task manager for audit logging
        current_user: Current authenticated superuser
        db: Database session

    Returns:
        StreamingResponse with CSV or JSON content

    Filters:
        - format: Export format (csv or json)
        - filters.event_type: Filter by event type (exact match)
        - filters.user_email: Filter by user email (case-insensitive partial match)
        - filters.start_date: Filter events >= start_date (ISO 8601)
        - filters.end_date: Filter events <= end_date (ISO 8601)
        - filters.resource_type: Filter by resource type (exact match)

    Streams data incrementally to avoid loading full result set into memory (AC-5.3.3).
    Applies PII redaction by default (AC-5.3.5).
    Logs export operation to audit.events (AC-5.3.2).
    """
    audit_service = get_audit_service()

    # Count total events for audit logging
    total_events = await audit_service.count_events(
        db=db,
        start_date=export_request.filters.start_date,
        end_date=export_request.filters.end_date,
        user_email=export_request.filters.user_email,
        event_type=export_request.filters.event_type.value
        if export_request.filters.event_type
        else None,
        resource_type=export_request.filters.resource_type.value
        if export_request.filters.resource_type
        else None,
    )

    # Build filter dict for streaming functions
    filters = {
        "start_date": export_request.filters.start_date,
        "end_date": export_request.filters.end_date,
        "user_email": export_request.filters.user_email,
        "event_type": export_request.filters.event_type.value
        if export_request.filters.event_type
        else None,
        "resource_type": export_request.filters.resource_type.value
        if export_request.filters.resource_type
        else None,
    }

    # Determine PII inclusion (default False - privacy by default)
    # TODO: Add has_permission(current_user, "export_pii") check in future story
    include_pii = False

    # Generate filename with timestamp
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    filename = f"audit-log-export-{timestamp}.{export_request.format}"

    # Log export operation to audit.events (AC-5.3.2)
    ip_address = get_client_ip(request)
    background_tasks.add_task(
        audit_service.log_event,
        action="audit.export",
        resource_type="audit_log",
        user_id=current_user.id,
        ip_address=ip_address,
        details={
            "format": export_request.format,
            "record_count": total_events,
            "pii_redacted": not include_pii,
            "filters": {
                "start_date": export_request.filters.start_date.isoformat()
                if export_request.filters.start_date
                else None,
                "end_date": export_request.filters.end_date.isoformat()
                if export_request.filters.end_date
                else None,
                "user_email": export_request.filters.user_email,
                "event_type": export_request.filters.event_type.value
                if export_request.filters.event_type
                else None,
                "resource_type": export_request.filters.resource_type.value
                if export_request.filters.resource_type
                else None,
            },
        },
    )

    # Stream response based on format
    if export_request.format == "csv":
        return StreamingResponse(
            export_csv_stream(audit_service, db, filters, include_pii),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:  # json
        return StreamingResponse(
            export_json_stream(audit_service, db, filters, include_pii),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@router.get(
    "/queue/status",
    response_model=list[QueueStatus],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not operator/admin (permission_level < 2)"},
    },
)
async def get_queue_status(
    _operator: User = Depends(get_current_operator_or_admin),
) -> list[QueueStatus]:
    """Get status for all active Celery queues (operator/admin).

    Story 7-27: AC-7.27.16-18 - Queue monitoring accessible to operators.

    Returns real-time queue metrics via Celery Inspect API:
    - Dynamically discovers all active queues (currently: default, document_processing)
    - Pending tasks: Tasks waiting for worker assignment
    - Active tasks: Tasks currently being processed
    - Workers: Online/offline status based on heartbeat (offline if > 60s)

    Results cached in Redis for 5 minutes to reduce broker load.

    **Permissions:** Requires permission_level >= 2 (OPERATOR) or is_superuser=True.

    **Performance:**
    - < 100ms with Redis cache hit
    - < 2s on cache miss (Celery inspect API)

    **Graceful Degradation:**
    - If Celery broker unreachable, returns queue objects with status="unavailable"
    - No 500 error - always returns 200 OK with status indicator

    Returns:
        List[QueueStatus]: Status for all active queues.
    """
    service = QueueMonitorService()
    return await service.get_all_queues()


@router.get(
    "/queue/{queue_name}/tasks",
    response_model=list[TaskInfo],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not operator/admin (permission_level < 2)"},
    },
)
async def get_queue_tasks(
    queue_name: str,
    document_status: DocumentStatusFilter = Query(
        default=DocumentStatusFilter.ALL,
        description="Filter tasks by document status (AC-7.27.15)",
    ),
    _operator: User = Depends(get_current_operator_or_admin),
    session: AsyncSession = Depends(get_async_session),
) -> list[TaskInfo]:
    """Get task details for a specific queue with step breakdown (operator/admin).

    Story 7-27: AC-7.27.1-7.27.5, AC-7.27.15 - Enhanced task visibility with filtering.

    Returns active tasks for the specified queue with processing details:
    - task_id: Celery task UUID
    - task_name: Full task name (e.g., "app.workers.document_tasks.process_document")
    - status: Always "active" (Celery inspect API only shows active tasks)
    - started_at: Task start time (ISO 8601)
    - estimated_duration: Elapsed time in milliseconds
    - document_id: Associated document UUID (AC-7.27.1)
    - document_name: Original filename for display
    - current_step: Current processing step (parse, chunk, embed, index)
    - processing_steps: Step breakdown with timing (AC-7.27.2)
    - step_errors: Errors by step for tooltip display (AC-7.27.5)

    Tasks sorted by started_at DESC (newest first).

    **Permissions:** Requires permission_level >= 2 (OPERATOR) or is_superuser=True.

    **Performance:**
    - < 2s (Celery inspect API + DB query, not cached)

    **Graceful Degradation:**
    - If Celery broker unreachable, returns empty list (no 500 error)

    Args:
        queue_name: Queue name (e.g., "document_processing", "default").
        document_status: Filter by document status (all, PENDING, PROCESSING, READY, FAILED).

    Returns:
        List[TaskInfo]: Active tasks in the queue with processing step details.
    """
    service = QueueMonitorService()
    return await service.get_queue_tasks(
        queue_name=queue_name,
        session=session,
        document_status=document_status,
    )


@router.post(
    "/queue/retry-failed",
    response_model=BulkRetryResponse,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not operator/admin (permission_level < 2)"},
    },
)
async def bulk_retry_failed(
    request: BulkRetryRequest,
    _operator: User = Depends(get_current_operator_or_admin),
    session: AsyncSession = Depends(get_async_session),
) -> BulkRetryResponse:
    """Retry failed documents in bulk (operator/admin).

    Story 7-27: AC-7.27.6-7.27.10 - Bulk queue restart for failed tasks.

    Supports two modes:
    1. Selective retry: Provide specific document_ids to retry
    2. Retry all failed: Set retry_all_failed=true to retry all FAILED documents

    Optionally scope to a specific knowledge base using kb_id.

    **Request Examples:**

    Selective retry:
    ```json
    {
        "document_ids": ["uuid1", "uuid2", "uuid3"]
    }
    ```

    Retry all failed in a KB:
    ```json
    {
        "retry_all_failed": true,
        "kb_id": "kb-uuid"
    }
    ```

    Retry all failed system-wide:
    ```json
    {
        "retry_all_failed": true
    }
    ```

    **Response:**
    - queued: Number of documents successfully queued for retry
    - failed: Number of documents that failed to queue
    - errors: Array of error details for failed retries

    **Permissions:** Requires permission_level >= 2 (OPERATOR) or is_superuser=True.

    **Side Effects:**
    - Resets document status to PENDING
    - Increments retry_count
    - Clears processing_steps, step_errors, last_error
    - Queues document_tasks.process_document Celery task

    Args:
        request: Bulk retry request with document_ids or retry_all_failed flag.

    Returns:
        BulkRetryResponse: Queued/failed counts with error details.
    """
    service = QueueMonitorService()
    return await service.bulk_retry_failed(
        session=session,
        document_ids=request.document_ids,
        retry_all_failed=request.retry_all_failed,
        kb_id=request.kb_id,
    )


@router.get(
    "/config",
    response_model=dict[str, ConfigSetting],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def get_system_config(
    _current_user: User = Depends(get_current_administrator),
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, ConfigSetting]:
    """
    Get all system configuration settings (admin only).

    Returns all system settings grouped by category:
    - Security: session_timeout_minutes, login_rate_limit_per_hour
    - Processing: max_upload_file_size_mb, default_chunk_size_tokens, max_chunks_per_document
    - Rate Limits: search_rate_limit_per_hour, generation_rate_limit_per_hour, upload_rate_limit_per_hour

    Results cached in Redis for 5 minutes.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Returns:
        Dictionary mapping setting key → ConfigSetting object.
    """
    config_service = ConfigService(db)
    settings = await config_service.get_all_settings()
    return {setting.key: setting for setting in settings}


# =============================================================================
# Query Rewriter Model Configuration (Story 8-0)
# NOTE: These specific routes MUST be defined BEFORE /config/{key}
# to avoid FastAPI matching the wrong route.
# =============================================================================


@router.get(
    "/config/rewriter-model",
    response_model=RewriterModelResponse,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def get_rewriter_model(
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> RewriterModelResponse:
    """Get the configured query rewriter model (admin only).

    Story 8-0: History-Aware Query Rewriting

    Returns the currently configured query rewriter model ID.
    If null, the system uses the default generation model for query rewriting.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Returns:
        RewriterModelResponse with model_id (UUID or null).
    """
    config_service = ConfigService(session)
    model_id = await config_service.get_rewriter_model_id()
    return RewriterModelResponse(model_id=model_id)


@router.put(
    "/config/rewriter-model",
    response_model=RewriterModelResponse,
    responses={
        400: {"description": "Invalid model ID or model not found"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def update_rewriter_model(
    request: RewriterModelUpdateRequest,
    current_user: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> RewriterModelResponse:
    """Update the query rewriter model configuration (admin only).

    Story 8-0: History-Aware Query Rewriting

    Sets which LLM model to use for query rewriting. The model must be
    a registered generation model. Set to null to use the default
    generation model as fallback.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    **Validation:**
    - If model_id is provided, validates it exists and is a generation model
    - If model_id is null, clears the setting (uses default generation model)

    Args:
        request: RewriterModelUpdateRequest with model_id (UUID or null)

    Returns:
        RewriterModelResponse with the updated model_id.

    Raises:
        HTTPException 400: If model not found or not a generation model.
    """
    config_service = ConfigService(session)
    try:
        await config_service.set_rewriter_model_id(
            model_id=request.model_id,
            changed_by=current_user.email,
        )
        return RewriterModelResponse(model_id=request.model_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.put(
    "/config/{key}",
    response_model=ConfigUpdateResponse,
    responses={
        400: {"description": "Validation error (invalid value type or out of range)"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
        404: {"description": "Setting key not found"},
    },
)
async def update_config_setting(
    key: str,
    request: ConfigUpdateRequest,
    current_user: User = Depends(get_current_administrator),
    db: AsyncSession = Depends(get_async_session),
) -> ConfigUpdateResponse:
    """
    Update a single configuration setting (admin only).

    Validates value type and range before persisting.
    Logs change to audit.events table.
    Clears Redis cache.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Args:
        key: Setting key (e.g., "session_timeout_minutes")
        request: New value for the setting

    Returns:
        Updated setting and list of all settings requiring restart.

    Raises:
        400: If value is invalid (wrong type, out of range)
        404: If setting key does not exist
    """
    config_service = ConfigService(db)

    # Validate setting key exists
    if not await config_service.setting_exists(key):
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    # Update setting (includes validation)
    try:
        updated_setting = await config_service.update_setting(
            key=key,
            value=request.value,
            changed_by=current_user.email,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # If session_timeout_minutes was updated, refresh the JWT timeout cache
    if key == "session_timeout_minutes":
        from app.core.auth import refresh_session_timeout_cache

        await refresh_session_timeout_cache()

    # Get list of all settings requiring restart
    restart_required = await config_service.get_restart_required_settings()

    return ConfigUpdateResponse(
        setting=updated_setting,
        restart_required=restart_required,
    )


@router.get(
    "/config/restart-required",
    response_model=list[str],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def get_restart_required_settings(
    _current_user: User = Depends(get_current_administrator),
    db: AsyncSession = Depends(get_async_session),
) -> list[str]:
    """
    Get list of setting keys that have pending changes requiring service restart.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Returns:
        List of setting keys (e.g., ["default_chunk_size_tokens"])
    """
    config_service = ConfigService(db)
    return await config_service.get_restart_required_settings()


@router.get(
    "/knowledge-bases/{kb_id}/stats",
    response_model=KBDetailedStats,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
        404: {"description": "Knowledge base not found"},
    },
)
async def get_kb_stats(
    kb_id: UUID,
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> KBDetailedStats:
    """Get detailed Knowledge Base statistics for admin view.

    Aggregates metrics from PostgreSQL, MinIO, and Qdrant:
    - Document count (PostgreSQL)
    - Storage bytes (PostgreSQL file_size sum)
    - Vector metrics: total chunks and embeddings (Qdrant)
    - Usage metrics: searches, generations, unique users (audit.events last 30 days)
    - Top 5 most accessed documents (audit.events last 30 days)

    Results cached in Redis for 10 minutes to reduce cross-service load.
    Falls back gracefully if MinIO or Qdrant unavailable (returns 0 for those metrics).

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    **Performance:**
    - < 500ms with Redis cache hit
    - < 15s on cache miss (cross-service aggregation)
    - Query timeout: 15s

    Args:
        kb_id: Knowledge Base UUID.

    Returns:
        KBDetailedStats: Comprehensive KB statistics.

    Raises:
        HTTPException 404: If KB not found.
    """
    try:
        service = KBStatsService(session, minio_service, qdrant_service)
        return await service.get_kb_stats(kb_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# =============================================================================
# LLM Configuration Endpoints (Story 7-2)
# =============================================================================


@router.get(
    "/llm/config",
    response_model=LLMConfig,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def get_llm_config(
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> LLMConfig:
    """Get current LLM configuration (admin only).

    AC-7.2.1: Returns current LLM model settings including:
    - Embedding model: provider, model name, dimensions
    - Generation model: provider, model name, parameters
    - LiteLLM proxy base URL
    - Generation settings (temperature, max_tokens, top_p)

    Results cached in Redis for 30 seconds for hot-reload responsiveness.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    **Performance:**
    - < 50ms with Redis cache hit
    - < 500ms on cache miss (DB query)

    Returns:
        LLMConfig: Current LLM configuration.
    """
    config_service = ConfigService(session)
    return await config_service.get_llm_config()


@router.put(
    "/llm/config",
    response_model=LLMConfigUpdateResponse,
    responses={
        400: {"description": "Validation error (model not found or invalid type)"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def update_llm_config(
    request: LLMConfigUpdateRequest,
    current_user: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> LLMConfigUpdateResponse:
    """Update LLM configuration with hot-reload (admin only).

    AC-7.2.2: Model switching applies without service restart.
    AC-7.2.3: Embedding dimension mismatch triggers warning.

    Updates default embedding and/or generation models and parameters.
    Changes are applied immediately via Redis pub/sub hot-reload mechanism.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    **Hot-Reload:**
    - Config invalidated in Redis immediately
    - Pub/sub notification sent to `llm:config:updated` channel
    - Services subscribe and reload config without restart

    **Dimension Warning:**
    - If new embedding model has different dimensions than current
    - Lists affected knowledge bases with existing embeddings
    - Warns about potential search inconsistencies

    Args:
        request: Configuration update request with:
            - embedding_model_id: UUID of model to set as default embedding
            - generation_model_id: UUID of model to set as default generation
            - generation_settings: Temperature, max_tokens, top_p

    Returns:
        LLMConfigUpdateResponse with updated config and any warnings.

    Raises:
        HTTPException 400: If model not found or invalid model type.
    """
    config_service = ConfigService(session)
    try:
        return await config_service.update_llm_config(
            request=request,
            changed_by=current_user.email,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get(
    "/llm/health",
    response_model=LLMHealthResponse,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def get_llm_health(
    model_type: str | None = Query(
        None,
        description="Filter by model type ('embedding' or 'generation'). "
        "If omitted, tests all configured models.",
    ),
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> LLMHealthResponse:
    """Get health status for configured LLM models (admin only).

    AC-7.2.4: Health status shown for each configured model.

    Tests connectivity to configured embedding and generation models
    via LiteLLM proxy. Measures response latency and reports errors.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    **Health Check:**
    - Sends minimal test request to each model
    - Measures round-trip latency in milliseconds
    - Reports connection errors and timeouts

    Args:
        model_type: Optional filter ('embedding' or 'generation').
            If omitted, tests all configured models.

    Returns:
        LLMHealthResponse with:
        - embedding_health: Status for embedding model (if configured)
        - generation_health: Status for generation model (if configured)
        - overall_healthy: True if all tested models are healthy
    """
    config_service = ConfigService(session)
    return await config_service.test_model_health(model_type=model_type)


# =============================================================================
# Feedback Analytics Endpoints (Story 7-23)
# =============================================================================


@router.get(
    "/feedback/analytics",
    response_model=FeedbackAnalyticsResponse,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def get_feedback_analytics(
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> FeedbackAnalyticsResponse:
    """Get feedback analytics for admin dashboard (AC-7.23.6).

    Aggregates feedback data from audit.events table where action='generation.feedback'.

    Returns:
        - by_type: Distribution by feedback type (for pie chart - AC-7.23.2)
        - by_day: Daily counts for last 30 days (for line chart - AC-7.23.3)
        - recent: 20 most recent feedback items with user context (AC-7.23.4)
        - total_count: Total number of feedback submissions

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    **Performance:**
    - < 500ms (database aggregation queries)
    - No caching yet (can add if needed)

    Returns:
        FeedbackAnalyticsResponse: Comprehensive feedback analytics.
    """
    service = FeedbackAnalyticsService(session)
    analytics = await service.get_analytics()
    return FeedbackAnalyticsResponse(**analytics)


# =============================================================================
# Data Retention Cleanup Endpoints (Story 9-14)
# =============================================================================


@router.post(
    "/observability/cleanup",
    response_model=CleanupResponse,
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not admin (is_superuser=False)"},
    },
)
async def trigger_observability_cleanup(
    dry_run: bool = Query(
        False,
        description="Preview what would be deleted without actually deleting",
    ),
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> CleanupResponse:
    """Manually trigger observability data cleanup (Story 9-14).

    Cleans up old observability data based on configured retention policies:
    - Raw traces/spans/events: observability_retention_days (default 90)
    - Aggregated metrics: observability_metrics_retention_days (default 365)
    - Sync status records: observability_sync_status_retention_days (default 7)

    Uses TimescaleDB drop_chunks() for efficient hypertable cleanup when
    available, falling back to standard DELETE operations otherwise.

    **Permissions:** Requires is_superuser=True (403 for non-admin).

    Args:
        dry_run: If True, preview what would be deleted without actual deletion.

    Returns:
        CleanupResponse with:
        - status: 'success' or 'partial' if some tables had errors
        - dry_run: Whether this was a preview
        - timescaledb_used: Whether TimescaleDB was available
        - results: Dict of table name to cleanup result
        - errors: List of errors encountered
        - duration_ms: Total operation time
    """
    import time

    start_time = time.time()

    retention_service = RetentionService(session)
    cleanup_result = await retention_service.cleanup_all(dry_run=dry_run)

    duration_ms = (time.time() - start_time) * 1000

    # Convert results to proper schema format
    table_results: dict[str, TableCleanupResult] = {}
    for table_name, result in cleanup_result.get("results", {}).items():
        table_results[table_name] = TableCleanupResult(
            table=table_name,
            chunks_dropped=result.get("chunks_dropped"),
            chunks_to_drop=result.get("chunks_to_drop"),
            records_deleted=result.get("records_deleted"),
            records_to_delete=result.get("records_to_delete"),
            chunk_names=result.get("chunk_names"),
            dry_run=result.get("dry_run", dry_run),
            error=result.get("error"),
        )

    errors = [
        CleanupError(table=e["table"], error=e["error"])
        for e in cleanup_result.get("errors", [])
    ]

    return CleanupResponse(
        status="success" if len(errors) == 0 else "partial",
        dry_run=dry_run,
        timescaledb_used=cleanup_result.get("timescaledb_used", False),
        results=table_results,
        errors=errors,
        duration_ms=duration_ms,
        task_id=None,  # Synchronous execution, no task ID
    )
