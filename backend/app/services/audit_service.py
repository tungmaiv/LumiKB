"""Audit logging service for fire-and-forget event logging."""

from typing import Any
from uuid import UUID

import structlog

from app.core.database import async_session_factory
from app.repositories.audit_repo import AuditRepository

logger = structlog.get_logger()


class AuditService:
    """Service for asynchronous audit logging.

    Uses fire-and-forget pattern to not block request processing.
    Creates its own database session for each log operation.
    """

    async def log_event(
        self,
        action: str,
        resource_type: str,
        user_id: UUID | None = None,
        resource_id: UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Log an audit event asynchronously.

        This method is designed to be called from background tasks
        and should never raise exceptions to the caller.

        Args:
            action: The audit action name (e.g., "user.registered").
            resource_type: The type of resource (e.g., "user").
            user_id: The user's UUID (optional for anonymous actions).
            resource_id: The resource UUID (optional).
            details: Additional JSON details (optional).
            ip_address: The client's IP address (optional).
        """
        try:
            # Create a dedicated session for audit logging
            async with async_session_factory() as session:
                repo = AuditRepository(session)
                await repo.create_event(
                    action=action,
                    resource_type=resource_type,
                    user_id=user_id,
                    resource_id=resource_id,
                    details=details,
                    ip_address=ip_address,
                )
                logger.info(
                    "audit_event_logged",
                    action=action,
                    resource_type=resource_type,
                    user_id=str(user_id) if user_id else None,
                )
        except Exception as e:
            # Log the error but don't propagate it
            logger.error(
                "audit_event_failed",
                action=action,
                error=str(e),
            )


# Singleton instance for use across the application
audit_service = AuditService()
