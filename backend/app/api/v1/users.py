"""Users API routes.

Provides:
- GET /api/v1/users/me - Get current user profile (protected)
- PATCH /api/v1/users/me - Update current user profile (protected)
- PUT /api/v1/users/me/onboarding - Mark onboarding as completed (protected)
- GET /api/v1/users/me/kb-recommendations - Get personalized KB recommendations (protected)
- GET /api/v1/users/me/recent-kbs - Get recently accessed KBs (protected)
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserManager, current_active_user, get_user_manager
from app.core.database import get_async_session
from app.core.redis import get_client_ip
from app.models.user import User
from app.schemas.kb_recommendation import KBRecommendation
from app.schemas.recent_kb import RecentKB
from app.schemas.user import UserRead, UserUpdate
from app.services.kb_recommendation_service import KBRecommendationService
from app.services.permission_service import PermissionService
from app.services.recent_kb_service import RecentKBService

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
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get the current authenticated user's profile with permission level.

    Story 7.11: Returns computed permission_level from user's groups.

    Args:
        user: Current authenticated user (from JWT cookie).
        session: Database session.

    Returns:
        UserRead: The user's profile data with permission_level.
    """
    # Compute permission level from groups (AC-7.11.20)
    permission_service = PermissionService(session)
    permission_level = await permission_service.get_user_permission_level(user)

    # Return user data with computed permission_level
    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "onboarding_completed": user.onboarding_completed,
        "last_active": user.last_active,
        "permission_level": permission_level,
    }


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


@router.put(
    "/me/onboarding",
    response_model=UserRead,
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def mark_onboarding_complete(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Mark the onboarding wizard as completed for the current user.

    This endpoint is idempotent - can be called multiple times safely.

    Args:
        user: Current authenticated user (from JWT cookie).
        session: Database session.

    Returns:
        UserRead: The updated user profile with onboarding_completed=True.
    """
    # Mark onboarding as complete (idempotent - safe to call multiple times)
    user.onboarding_completed = True
    await session.commit()
    await session.refresh(user)

    return user


@router.get(
    "/me/kb-recommendations",
    response_model=list[KBRecommendation],
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def get_kb_recommendations(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[KBRecommendation]:
    """Get personalized KB recommendations for the current user.

    Returns up to 5 KB recommendations based on:
    - Recent access patterns (40% weight)
    - Search relevance (35% weight)
    - Global popularity (25% weight)

    New users (< 7 days, no searches) receive cold start recommendations
    based on popular public KBs.

    Results are cached in Redis for 1 hour per user.

    Args:
        user: Current authenticated user (from JWT cookie).
        session: Database session.

    Returns:
        List of KBRecommendation objects (max 5), sorted by score.
    """
    service = KBRecommendationService(session)
    return await service.get_recommendations(user.id, limit=5)


@router.get(
    "/me/recent-kbs",
    response_model=list[RecentKB],
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def get_recent_kbs(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[RecentKB]:
    """Get the current user's recently accessed knowledge bases.

    Returns up to 5 recently accessed KBs sorted by last access time (most
    recent first). Uses indexed queries on kb_access_log table for 100ms SLA.

    Returns empty list if user has no KB access history.

    Args:
        user: Current authenticated user (from JWT cookie).
        session: Database session.

    Returns:
        List of RecentKB objects (max 5), sorted by last_accessed DESC.
    """
    service = RecentKBService(session)
    return await service.get_recent_kbs(user.id, limit=5)


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
