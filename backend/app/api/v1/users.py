"""Users API routes.

Provides:
- GET /api/v1/users/me - Get current user profile (protected)
- PATCH /api/v1/users/me - Update current user profile (protected)
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserManager, current_active_user, get_user_manager
from app.core.database import get_async_session
from app.core.redis import get_client_ip
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserRead,
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def get_current_user(
    user: User = Depends(current_active_user),
) -> User:
    """Get the current authenticated user's profile.

    Args:
        user: Current authenticated user (from JWT cookie).

    Returns:
        UserRead: The user's profile data.
    """
    return user


@router.patch(
    "/me",
    response_model=UserRead,
    responses={
        400: {"description": "Email already exists"},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    },
)
async def update_current_user(
    request: Request,
    background_tasks: BackgroundTasks,
    user_update: UserUpdate,
    user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Update the current authenticated user's profile.

    Args:
        request: FastAPI request object.
        background_tasks: Background task manager for async audit logging.
        user_update: Update data (email, etc.).
        user: Current authenticated user (from JWT cookie).
        user_manager: FastAPI-Users user manager.
        session: Database session.

    Returns:
        UserRead: The updated user profile.

    Raises:
        HTTPException: 400 if email already exists.
    """
    # Check for email uniqueness if email is being updated
    if user_update.email is not None and user_update.email != user.email:
        existing_user = await session.execute(
            select(User).where(User.email == user_update.email)
        )
        if existing_user.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="REGISTER_USER_ALREADY_EXISTS",
            )

    # Use FastAPI-Users to update the user
    updated_user = await user_manager.update(
        user_update, user, safe=True, request=request
    )

    # Fire-and-forget audit logging
    ip_address = get_client_ip(request)
    background_tasks.add_task(
        _log_audit_event,
        "user.profile_updated",
        updated_user.id,
        ip_address,
        {
            "updated_fields": [
                k
                for k, v in user_update.model_dump(exclude_unset=True).items()
                if v is not None
            ]
        },
    )

    return updated_user


async def _log_audit_event(
    action: str,
    user_id: UUID,
    ip_address: str,
    details: dict | None = None,
) -> None:
    """Fire-and-forget audit logging.

    Args:
        action: The audit action name.
        user_id: The user's UUID.
        ip_address: The client's IP address.
        details: Additional details to log.
    """
    try:
        from app.services.audit_service import audit_service

        await audit_service.log_event(
            action=action,
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            details=details,
            ip_address=ip_address,
        )
    except Exception:
        # Audit logging should never fail the request
        pass
