"""Admin API routes.

Provides:
- GET /api/v1/admin/users - List all users with pagination (admin only)
- POST /api/v1/admin/users - Create new user (admin only)
- PATCH /api/v1/admin/users/{user_id} - Update user status (admin only)
"""

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
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserManager, current_superuser, get_user_manager
from app.core.database import get_async_session
from app.core.redis import get_client_ip
from app.models.audit import AuditEvent
from app.models.outbox import Outbox
from app.models.user import User
from app.schemas.admin import AdminStats
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.user import AdminUserUpdate, UserCreate, UserRead
from app.services.admin_stats_service import AdminStatsService
from app.workers.outbox_tasks import MAX_OUTBOX_ATTEMPTS


class OutboxStats(BaseModel):
    """Outbox queue statistics response."""

    pending_events: int
    failed_events: int
    processed_last_hour: int
    processed_last_24h: int
    queue_depth: int
    average_processing_time_ms: float | None


class AuditEventResponse(BaseModel):
    """Single audit event response."""

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

    events: list[AuditEventResponse]
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
    _admin: User = Depends(current_superuser),
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

    Returns:
        AdminStats: Comprehensive system statistics.
    """
    try:
        service = AdminStatsService(session)
        return await service.get_dashboard_stats()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise


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
    _admin: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session),
) -> PaginatedResponse[UserRead]:
    """List all users with pagination (admin only).

    Args:
        skip: Number of records to skip (default 0).
        limit: Number of records to return (default 20, max 100).
        admin: Current authenticated superuser.
        session: Database session.

    Returns:
        PaginatedResponse[UserRead]: Paginated list of users.
    """
    # Get total count
    count_result = await session.execute(select(func.count(User.id)))
    total = count_result.scalar() or 0

    # Get paginated results
    result = await session.execute(
        select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
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
    admin: User = Depends(current_superuser),
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
    admin: User = Depends(current_superuser),
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
    _admin: User = Depends(current_superuser),
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
    _admin: User = Depends(current_superuser),
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
            AuditEvent.action.in_([
                "generation.request",
                "generation.complete",
                "generation.failed",
                "generation.feedback",
                "document.export",
            ])
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
            AuditEvent.action.in_([
                "generation.request",
                "generation.complete",
                "generation.failed",
                "generation.feedback",
                "document.export",
            ])
        )
        if start_date:
            count_query = count_query.where(AuditEvent.timestamp >= start_date)
        if end_date:
            count_query = count_query.where(AuditEvent.timestamp <= end_date)
        if user_id:
            count_query = count_query.where(AuditEvent.user_id == user_id)
        if kb_id:
            count_query = count_query.where(AuditEvent.details["kb_id"].astext == str(kb_id))
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
                AuditEventResponse(
                    id=event.id,
                    timestamp=event.timestamp,
                    user_id=event.user_id,
                    user_email=user_emails.get(event.user_id) if event.user_id else None,
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
            AuditEvent.action.in_([
                "generation.request",
                "generation.complete",
                "generation.failed",
            ])
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
