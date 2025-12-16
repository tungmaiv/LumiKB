"""FastAPI-Users authentication configuration.

This module configures:
- UserManager with custom behavior for registration/login hooks
- JWT authentication strategy with dynamic timeout from DB config
- Cookie transport (httpOnly, Secure, SameSite=Lax)
- FastAPIUsers instance
"""

import time
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_factory, get_async_session
from app.core.users import get_user_db
from app.models.config import SystemConfig
from app.models.group import Group, UserGroup
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User

if TYPE_CHECKING:
    from fastapi_users.db import SQLAlchemyUserDatabase
    from sqlalchemy.ext.asyncio import AsyncSession

# Cache for session timeout (sync access for get_jwt_strategy)
_jwt_timeout_cache: dict[str, int | float] = {
    "value": settings.jwt_expiry_minutes * 60,  # Default fallback
    "expires_at": 0,
}

# Demo KB name constant - must match seed-data.py
DEMO_KB_NAME = "Sample Knowledge Base"

# Default group for new user registration (Story 7.11 AC-7.11.10)
DEFAULT_USER_GROUP_NAME = "Users"

logger = structlog.get_logger(__name__)


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    """Custom user manager with hooks for audit logging.

    Extends FastAPI-Users BaseUserManager to add:
    - Custom validation logic
    - Audit logging hooks (on_after_register, on_after_login, etc.)
    """

    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    async def on_after_register(
        self,
        user: User,
        request: Request | None = None,  # noqa: ARG002
    ) -> None:
        """Called after successful user registration.

        - Assigns user to the default "Users" group (AC-7.11.10)
        - Grants READ permission on the demo KB (Sample Knowledge Base)

        Args:
            user: The newly registered user.
            request: The FastAPI request object.
        """
        await self._assign_default_group(user)
        await self._grant_demo_kb_access(user)

    async def _assign_default_group(self, user: User) -> None:
        """Assign user to the default Users group (AC-7.11.10).

        Args:
            user: The newly registered user.
        """
        async with async_session_factory() as session:
            # Find Users group
            result = await session.execute(
                select(Group).where(
                    Group.name == DEFAULT_USER_GROUP_NAME,
                    Group.is_active.is_(True),
                )
            )
            users_group = result.scalar_one_or_none()

            if not users_group:
                logger.warning(
                    "default_users_group_not_found",
                    group_name=DEFAULT_USER_GROUP_NAME,
                    user_id=str(user.id),
                )
                return

            # Check if membership already exists
            result = await session.execute(
                select(UserGroup).where(
                    UserGroup.user_id == user.id,
                    UserGroup.group_id == users_group.id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.debug(
                    "default_group_membership_exists",
                    user_id=str(user.id),
                    group_id=str(users_group.id),
                )
                return

            # Create membership
            membership = UserGroup(
                user_id=user.id,
                group_id=users_group.id,
            )
            session.add(membership)
            await session.commit()

            logger.info(
                "user_assigned_to_default_group",
                user_id=str(user.id),
                group_id=str(users_group.id),
                group_name=DEFAULT_USER_GROUP_NAME,
            )

    async def _grant_demo_kb_access(self, user: User) -> None:
        """Grant READ permission on demo KB to user.

        Args:
            user: The user to grant permission to.
        """
        async with async_session_factory() as session:
            # Find demo KB
            result = await session.execute(
                select(KnowledgeBase).where(KnowledgeBase.name == DEMO_KB_NAME)
            )
            demo_kb = result.scalar_one_or_none()

            if not demo_kb:
                logger.info(
                    "demo_kb_not_found",
                    kb_name=DEMO_KB_NAME,
                    user_id=str(user.id),
                )
                return

            # Check if permission already exists
            result = await session.execute(
                select(KBPermission).where(
                    KBPermission.user_id == user.id,
                    KBPermission.kb_id == demo_kb.id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.debug(
                    "demo_kb_permission_exists",
                    user_id=str(user.id),
                    kb_id=str(demo_kb.id),
                )
                return

            # Grant READ permission
            permission = KBPermission(
                user_id=user.id,
                kb_id=demo_kb.id,
                permission_level=PermissionLevel.READ,
            )
            session.add(permission)
            await session.commit()

            logger.info(
                "demo_kb_access_granted",
                user_id=str(user.id),
                kb_id=str(demo_kb.id),
                permission_level="READ",
            )

    async def on_after_login(
        self,
        user: User,
        request: Request | None = None,
        response: None = None,
    ) -> None:
        """Called after successful login.

        Args:
            user: The authenticated user.
            request: The FastAPI request object.
            response: The response object (for cookie setting).
        """
        # Session storage and audit logging will be added in Task 5 (auth routes)
        pass

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Request | None = None,
    ) -> None:
        """Called after password reset request.

        Args:
            user: The user requesting password reset.
            token: The reset token.
            request: The FastAPI request object.
        """
        # Password reset functionality for future stories
        pass


async def get_user_manager(
    user_db: "SQLAlchemyUserDatabase[User, UUID]" = Depends(get_user_db),
) -> UserManager:
    """FastAPI dependency for UserManager.

    Args:
        user_db: The user database adapter.

    Yields:
        UserManager: The user manager instance.
    """
    yield UserManager(user_db)


def get_session_timeout_sync() -> int:
    """Get session timeout in seconds (sync version with caching).

    Uses a cached value that gets refreshed by async code.
    Falls back to env config if cache is empty.

    Returns:
        Session timeout in seconds.
    """
    now = time.time()
    if _jwt_timeout_cache["expires_at"] > now:
        return int(_jwt_timeout_cache["value"])
    # Return cached value even if expired (will be refreshed async)
    # This ensures we always have a value
    cached = _jwt_timeout_cache["value"]
    return int(cached) if cached else settings.jwt_expiry_minutes * 60


async def refresh_session_timeout_cache() -> int:
    """Refresh the session timeout cache from database.

    Called during app startup and periodically to keep cache fresh.
    Also called when session_timeout_minutes config is updated.

    Returns:
        Session timeout in seconds.
    """
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(SystemConfig.value).where(
                    SystemConfig.key == "session_timeout_minutes"
                )
            )
            db_value = result.scalar_one_or_none()

            # Use DB value if set, otherwise default (720 minutes = 12 hours)
            timeout_seconds = int(db_value) * 60 if db_value is not None else 720 * 60

            # Update cache with 60 second TTL
            _jwt_timeout_cache["value"] = timeout_seconds
            _jwt_timeout_cache["expires_at"] = time.time() + 60

            logger.info(
                "session_timeout_cache_refreshed",
                timeout_minutes=timeout_seconds // 60,
                timeout_seconds=timeout_seconds,
            )

            return timeout_seconds
    except Exception as e:
        logger.warning(
            "session_timeout_cache_refresh_failed",
            error=str(e),
            fallback_minutes=settings.jwt_expiry_minutes,
        )
        # Fallback to env config if DB query fails
        return settings.jwt_expiry_minutes * 60


def get_jwt_strategy() -> JWTStrategy[User, UUID]:
    """Create JWT strategy with dynamic timeout from DB config.

    The timeout is fetched from the session_timeout_minutes setting
    in SystemConfig, with caching to avoid DB queries on every request.

    Returns:
        JWTStrategy: JWT authentication strategy.
    """
    lifetime_seconds = get_session_timeout_sync()
    return JWTStrategy(
        secret=settings.secret_key,
        lifetime_seconds=lifetime_seconds,
        algorithm=settings.jwt_algorithm,
    )


# Cookie transport configuration: httpOnly + Secure + SameSite=Lax
# Note: cookie_max_age is set to a long value (30 days) since the actual
# session expiry is controlled by the JWT lifetime. The JWT expiry is
# dynamic based on session_timeout_minutes in DB config.
COOKIE_MAX_AGE_SECONDS = 30 * 24 * 60 * 60  # 30 days (JWT expiry is the real limit)

cookie_transport = CookieTransport(
    cookie_name="lumikb_auth",
    cookie_max_age=COOKIE_MAX_AGE_SECONDS,
    cookie_httponly=True,
    cookie_secure=not settings.debug,  # Secure in production, not in debug
    cookie_samesite="lax",
)

# Authentication backend combining cookie transport with JWT strategy
auth_backend = AuthenticationBackend(
    name="jwt-cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPIUsers instance - the main entry point for auth functionality
fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)

# Dependency for getting the current authenticated user
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


# Permission-level dependencies (Story 7.11)
async def get_current_operator(
    user: User = Depends(current_active_user),
    session: "AsyncSession" = Depends(get_async_session),
) -> User:
    """Dependency that requires OPERATOR (level 2+) permission.

    AC-7.11.13: Operators can upload/delete documents, create KBs.

    Args:
        user: Current authenticated user.
        session: Database session.

    Returns:
        User if they have OPERATOR or higher permission.

    Raises:
        HTTPException: 403 if user doesn't have required permission.
    """
    from app.services.permission_service import PermissionLevel, PermissionService

    service = PermissionService(session)
    has_permission = await service.check_permission(user, PermissionLevel.OPERATOR)

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires Operator permission",
        )

    return user


async def get_current_administrator(
    user: User = Depends(current_active_user),
    session: "AsyncSession" = Depends(get_async_session),
) -> User:
    """Dependency that requires ADMINISTRATOR (level 3) permission.

    AC-7.11.15: Administrators have full access including KB deletion.

    Args:
        user: Current authenticated user.
        session: Database session.

    Returns:
        User if they have ADMINISTRATOR permission.

    Raises:
        HTTPException: 403 if user doesn't have required permission.
    """
    from app.services.permission_service import PermissionLevel, PermissionService

    service = PermissionService(session)
    has_permission = await service.check_permission(user, PermissionLevel.ADMINISTRATOR)

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires Administrator permission",
        )

    return user


# Alias dependencies for clarity
current_operator = get_current_operator
current_administrator = get_current_administrator


async def get_current_operator_or_admin(
    user: User = Depends(current_active_user),
    session: "AsyncSession" = Depends(get_async_session),
) -> User:
    """Dependency that requires OPERATOR+ permission or superuser status.

    Story 7-27: AC-7.27.16-18 - Queue monitoring access for operators/admins.

    Access granted if:
    - User is superuser (is_superuser=True) - AC-7.27.18
    - User has permission_level >= 2 (OPERATOR or ADMINISTRATOR) - AC-7.27.16

    Args:
        user: Current authenticated user.
        session: Database session.

    Returns:
        User if they have operator+ permission or are superuser.

    Raises:
        HTTPException: 403 if user doesn't have required permission.
    """
    # Superusers always have access (AC-7.27.18)
    if user.is_superuser:
        return user

    from app.services.permission_service import PermissionLevel, PermissionService

    service = PermissionService(session)
    has_permission = await service.check_permission(user, PermissionLevel.OPERATOR)

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires Operator permission or higher",
        )

    return user


# Alias for queue monitoring endpoints
current_operator_or_admin = get_current_operator_or_admin


# Import AsyncSession for type hint
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402
