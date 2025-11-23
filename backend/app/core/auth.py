"""FastAPI-Users authentication configuration.

This module configures:
- UserManager with custom behavior for registration/login hooks
- JWT authentication strategy
- Cookie transport (httpOnly, Secure, SameSite=Lax)
- FastAPIUsers instance
"""

from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.users import get_user_db
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User

if TYPE_CHECKING:
    from fastapi_users.db import SQLAlchemyUserDatabase

# Demo KB name constant - must match seed-data.py
DEMO_KB_NAME = "Sample Knowledge Base"

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

        Grants READ permission on the demo KB (Sample Knowledge Base)
        to newly registered users so they can explore immediately.

        Args:
            user: The newly registered user.
            request: The FastAPI request object.
        """
        await self._grant_demo_kb_access(user)

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


def get_jwt_strategy() -> JWTStrategy[User, UUID]:
    """Create JWT strategy with configured settings.

    Returns:
        JWTStrategy: JWT authentication strategy.
    """
    return JWTStrategy(
        secret=settings.secret_key,
        lifetime_seconds=settings.jwt_expiry_minutes * 60,
        algorithm=settings.jwt_algorithm,
    )


# Cookie transport configuration: httpOnly + Secure + SameSite=Lax
cookie_transport = CookieTransport(
    cookie_name="lumikb_auth",
    cookie_max_age=settings.jwt_expiry_minutes * 60,
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
