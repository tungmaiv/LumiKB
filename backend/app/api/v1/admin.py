"""Admin API routes.

Provides:
- GET /api/v1/admin/users - List all users with pagination (admin only)
- POST /api/v1/admin/users - Create new user (admin only)
- PATCH /api/v1/admin/users/{user_id} - Update user status (admin only)
"""

from datetime import UTC, datetime, timedelta
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
from app.models.outbox import Outbox
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.user import AdminUserUpdate, UserCreate, UserRead
from app.workers.outbox_tasks import MAX_OUTBOX_ATTEMPTS


class OutboxStats(BaseModel):
    """Outbox queue statistics response."""

    pending_events: int
    failed_events: int
    processed_last_hour: int
    processed_last_24h: int
    queue_depth: int
    average_processing_time_ms: float | None


router = APIRouter(prefix="/admin", tags=["admin"])


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
