"""Search audit service with PII sanitization for audit logging.

This service extends the base AuditService with:
1. PII sanitization for query text (email, phone, SSN, CC)
2. Search-specific metadata (search_type, status, error details)
3. Fire-and-forget async pattern for non-blocking audit logging

Story: 5.14 - Search Audit Logging
"""

import re
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from app.services.audit_service import AuditService

logger = structlog.get_logger(__name__)


class PIISanitizer:
    """Sanitize PII patterns from search queries.

    Supports:
    - Email addresses → [EMAIL]
    - Phone numbers → [PHONE]
    - SSN patterns → [SSN]
    - Credit card patterns → [CC]
    """

    PATTERNS = {
        "email": (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
        "phone": (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]"),
        "ssn": (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
        "credit_card": (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[CC]"),
    }

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Sanitize all PII patterns from text.

        Args:
            text: Input text that may contain PII

        Returns:
            Text with PII patterns replaced by placeholders
        """
        if not text:
            return text

        result = text
        for pattern, replacement in cls.PATTERNS.values():
            result = re.sub(pattern, replacement, result)
        return result


class SearchAuditService:
    """Service for logging search operations to audit trail.

    Uses fire-and-forget pattern to avoid blocking search responses.
    Sanitizes PII in query text before storing.
    """

    def __init__(self, audit_service: "AuditService"):
        """Initialize search audit service.

        Args:
            audit_service: Base audit service for logging events
        """
        self.audit_service = audit_service

    async def log_search(
        self,
        user_id: UUID,
        query_text: str,
        kb_ids: list[UUID | str],
        result_count: int,
        duration_ms: int,
        search_type: str,
        status: str = "success",
        error_message: str | None = None,
        error_type: str | None = None,
    ) -> None:
        """Log a search operation to audit trail (fire-and-forget).

        This method is designed to be called from background tasks or
        directly without awaiting in performance-critical paths.
        All exceptions are caught and logged, never raised.

        Args:
            user_id: UUID of the user who performed the search
            query_text: Search query text (will be PII sanitized)
            kb_ids: List of KB IDs searched
            result_count: Number of results returned
            duration_ms: Search response time in milliseconds
            search_type: Type of search ("semantic", "cross_kb", "quick", "similar")
            status: "success" or "failed" (default: "success")
            error_message: Error message if status="failed"
            error_type: Error category if status="failed"
                - "validation_error": Invalid request parameters
                - "kb_not_found": Knowledge base does not exist
                - "access_denied": User lacks permission
                - "internal_error": Unexpected server error
        """
        try:
            # Sanitize PII from query text (AC2)
            sanitized_query = PIISanitizer.sanitize(query_text)

            # Convert kb_ids to strings
            kb_id_strings = [str(kb_id) for kb_id in kb_ids]

            # Build metadata (AC2)
            metadata: dict[str, str | int | list[str] | None] = {
                "query_text": sanitized_query[:500],  # Truncate for storage
                "kb_ids": kb_id_strings,
                "result_count": result_count,
                "duration_ms": duration_ms,
                "search_type": search_type,
                "status": status,
            }

            # Add error fields if failed (AC4)
            if error_message:
                metadata["error_message"] = error_message[:500]
            if error_type:
                metadata["error_type"] = error_type

            # Use existing audit service log_event method (AC1, AC3)
            # resource_id is first KB ID if available
            resource_id = UUID(kb_id_strings[0]) if kb_id_strings else None

            await self.audit_service.log_event(
                action="search",
                resource_type="knowledge_base",
                user_id=user_id,
                resource_id=resource_id,
                details=metadata,
            )

            logger.debug(
                "search_audit_logged",
                user_id=str(user_id),
                search_type=search_type,
                result_count=result_count,
                duration_ms=duration_ms,
                status=status,
            )

        except Exception as e:
            # Fire-and-forget: log error but don't raise (AC3)
            logger.error(
                "search_audit_failed",
                error=str(e),
                user_id=str(user_id),
                search_type=search_type,
            )
