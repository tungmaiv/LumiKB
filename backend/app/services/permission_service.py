"""Permission service for RBAC permission level checks.

Story 7.11: Navigation Restructure with RBAC Default Groups
- AC-7.11.11: Cumulative permission checks (higher levels inherit lower)
- AC-7.11.19: Last admin safety check
- AC-7.11.20: MAX permission_level across all groups
"""

from collections.abc import Callable
from enum import IntEnum
from functools import wraps
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.group import Group, UserGroup

if TYPE_CHECKING:
    from app.models.user import User

logger = structlog.get_logger(__name__)


class PermissionLevel(IntEnum):
    """System permission levels (cumulative hierarchy).

    Higher levels inherit all lower-level permissions.
    - USER (1): Basic access - search, view, generate
    - OPERATOR (2): + upload/delete documents, create KBs, Operations menu
    - ADMINISTRATOR (3): + delete KBs, manage users/groups, Admin menu
    """

    USER = 1
    OPERATOR = 2
    ADMINISTRATOR = 3


# System group names (must match migration seed)
SYSTEM_GROUP_USERS = "Users"
SYSTEM_GROUP_OPERATORS = "Operators"
SYSTEM_GROUP_ADMINISTRATORS = "Administrators"


class PermissionService:
    """Service for permission level checks and safety guards.

    Provides methods to:
    - Get user's effective permission level (MAX across groups)
    - Check if user has required permission level
    - Validate last administrator safety constraints
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize PermissionService with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self.session = session

    async def get_user_permission_level(self, user: "User") -> int:
        """Get user's effective permission level (MAX across all groups).

        AC-7.11.20: Uses MAX aggregation for users in multiple groups.

        Args:
            user: The user to check.

        Returns:
            Maximum permission_level from user's groups, or 1 (USER) if no groups.
        """
        # Query MAX permission_level from user's active groups
        result = await self.session.execute(
            select(func.max(Group.permission_level))
            .select_from(UserGroup)
            .join(Group, UserGroup.group_id == Group.id)
            .where(
                UserGroup.user_id == user.id,
                Group.is_active.is_(True),
            )
        )
        max_level = result.scalar()

        # Fallback: if user is superuser but not in Administrators group
        # (backwards compatibility during migration)
        if max_level is None and getattr(user, "is_superuser", False):
            logger.info(
                "superuser_fallback",
                user_id=str(user.id),
                message="User is superuser but not in any group, using ADMINISTRATOR level",
            )
            return PermissionLevel.ADMINISTRATOR

        return max_level or PermissionLevel.USER

    async def check_permission(
        self,
        user: "User",
        required_level: PermissionLevel,
    ) -> bool:
        """Check if user has at least the required permission level.

        AC-7.11.11: Cumulative check - higher levels inherit lower permissions.

        Args:
            user: The user to check.
            required_level: Minimum required permission level.

        Returns:
            True if user's level >= required_level.
        """
        user_level = await self.get_user_permission_level(user)
        return user_level >= required_level

    async def get_administrators_group_id(self) -> UUID | None:
        """Get the ID of the Administrators system group.

        Returns:
            UUID of Administrators group, or None if not found.
        """
        result = await self.session.execute(
            select(Group.id).where(
                Group.name == SYSTEM_GROUP_ADMINISTRATORS,
                Group.is_system.is_(True),
                Group.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def count_administrators(self) -> int:
        """Count users in the Administrators group.

        Returns:
            Number of users in Administrators group.
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(UserGroup)
            .join(Group, UserGroup.group_id == Group.id)
            .where(
                Group.name == SYSTEM_GROUP_ADMINISTRATORS,
                Group.is_system.is_(True),
                Group.is_active.is_(True),
            )
        )
        return result.scalar() or 0

    async def is_last_administrator(self, user_id: UUID) -> bool:
        """Check if user is the last administrator in the system.

        AC-7.11.19: Safety check to prevent accidental lockout.

        Args:
            user_id: The user ID to check.

        Returns:
            True if user is in Administrators group AND is the only member.
        """
        admin_group_id = await self.get_administrators_group_id()
        if not admin_group_id:
            return False

        # Check if user is in Administrators group
        result = await self.session.execute(
            select(UserGroup).where(
                UserGroup.user_id == user_id,
                UserGroup.group_id == admin_group_id,
            )
        )
        if not result.scalar_one_or_none():
            return False

        # Check if they're the only member
        admin_count = await self.count_administrators()
        return admin_count == 1

    async def can_remove_from_administrators(
        self,
        user_id: UUID,
        group_id: UUID,
    ) -> tuple[bool, str | None]:
        """Check if user can be removed from Administrators group.

        AC-7.11.19: Prevents removing the last administrator.

        Args:
            user_id: The user ID being removed.
            group_id: The group ID being removed from.

        Returns:
            Tuple of (can_remove, error_message).
        """
        admin_group_id = await self.get_administrators_group_id()

        # Not the Administrators group - allow removal
        if admin_group_id is None or group_id != admin_group_id:
            return True, None

        # Check if this is the last admin
        if await self.is_last_administrator(user_id):
            return False, "Cannot remove the last administrator"

        return True, None


async def get_permission_service(
    session: AsyncSession = Depends(get_async_session),
) -> PermissionService:
    """FastAPI dependency for PermissionService.

    Args:
        session: Async SQLAlchemy session.

    Returns:
        PermissionService instance.
    """
    return PermissionService(session)


def require_permission(
    required_level: PermissionLevel,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator factory for permission-gated endpoints.

    Usage:
        @router.post("/upload")
        @require_permission(PermissionLevel.OPERATOR)
        async def upload_document(...):
            ...

    Args:
        required_level: Minimum required permission level.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get current_user from kwargs (must be injected by FastAPI)
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Get session from kwargs
            session = kwargs.get("session")
            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available",
                )

            # Check permission
            service = PermissionService(session)
            has_permission = await service.check_permission(
                current_user, required_level
            )

            if not has_permission:
                logger.warning(
                    "permission_denied",
                    user_id=str(current_user.id),
                    required_level=required_level.name,
                    endpoint=func.__name__,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {required_level.name} permission",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
