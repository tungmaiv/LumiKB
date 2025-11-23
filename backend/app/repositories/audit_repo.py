"""Audit event repository for database access."""

from typing import Any
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent


class AuditRepository:
    """Repository for audit event database operations.

    Uses INSERT-only pattern for immutable audit logging.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self._session = session

    async def create_event(
        self,
        action: str,
        resource_type: str,
        user_id: UUID | None = None,
        resource_id: UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Create a new audit event.

        Args:
            action: The audit action name (e.g., "user.registered").
            resource_type: The type of resource (e.g., "user").
            user_id: The user's UUID (optional for anonymous actions).
            resource_id: The resource UUID (optional).
            details: Additional JSON details (optional).
            ip_address: The client's IP address (optional).
        """
        stmt = insert(AuditEvent).values(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        await self._session.execute(stmt)
        await self._session.commit()
