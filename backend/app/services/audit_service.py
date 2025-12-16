"""Audit logging service for fire-and-forget event logging."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.audit import AuditEvent
from app.models.user import User
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

    async def log_search(
        self,
        user_id: str,
        query: str,
        kb_ids: list[str],
        result_count: int,
        latency_ms: int,
        search_type: str = "semantic",
        status: str = "success",
        error_message: str | None = None,
        error_type: str | None = None,
        effective_config: dict[str, Any] | None = None,
    ) -> None:
        """Log a search query event with PII sanitization.

        Story 7-17 (AC-7.17.6): Now includes effective_config for audit trail.

        Args:
            user_id: User ID who performed the search
            query: Search query text (will be PII sanitized)
            kb_ids: List of KB IDs searched
            result_count: Number of results returned
            latency_ms: Response latency in milliseconds
            search_type: Type of search ("semantic", "cross_kb", "quick", "similar")
            status: "success" or "failed" (default: "success")
            error_message: Error message if status="failed"
            error_type: Error category if status="failed"
                - "validation_error": Invalid request parameters
                - "kb_not_found": Knowledge base does not exist
                - "access_denied": User lacks permission
                - "internal_error": Unexpected server error
            effective_config: Resolved configuration used for this search (Story 7-17)
        """
        # Sanitize PII from query text (Story 5.14, AC2)
        sanitized_query = self._sanitize_pii(query)

        # Build metadata
        details: dict[str, Any] = {
            "query": sanitized_query[:500],  # Truncate for storage
            "kb_ids": kb_ids,
            "result_count": result_count,
            "latency_ms": latency_ms,
            "search_type": search_type,
            "status": status,
        }

        # Add error fields if failed (AC4)
        if error_message:
            details["error_message"] = error_message[:500]
        if error_type:
            details["error_type"] = error_type

        # Story 7-17 (AC-7.17.6): Include effective config in audit log
        if effective_config:
            details["effective_config"] = effective_config

        # Use first KB ID as resource_id if available
        resource_id = UUID(kb_ids[0]) if kb_ids else None

        await self.log_event(
            action="search",
            resource_type="knowledge_base",
            user_id=UUID(user_id),
            resource_id=resource_id,
            details=details,
        )

    async def log_generation_request(
        self,
        user_id: UUID,
        kb_id: UUID,
        document_type: str,
        context: str,
        selected_source_count: int = 0,
        request_id: str | None = None,
        template_id: str | None = None,
    ) -> None:
        """Log generation request attempt.

        Args:
            user_id: User ID who initiated generation
            kb_id: Knowledge base ID
            document_type: Type of document being generated
            context: Generation context (truncated to 500 chars)
            selected_source_count: Number of sources selected
            request_id: Request ID for linking events
            template_id: Template ID if template used
        """
        import uuid

        await self.log_event(
            action="generation.request",
            resource_type="draft",
            user_id=user_id,
            details={
                "request_id": request_id or str(uuid.uuid4()),
                "kb_id": str(kb_id),
                "document_type": document_type,
                "context": context[:500],  # Truncate to 500 chars
                "selected_source_count": selected_source_count,
                "template_id": template_id or document_type,
            },
        )

    async def log_generation_complete(
        self,
        user_id: UUID,
        request_id: str,
        kb_id: UUID,
        document_type: str,
        citation_count: int,
        source_document_ids: list[str],
        generation_time_ms: int,
        output_word_count: int,
        confidence_score: float,
    ) -> None:
        """Log successful generation completion.

        Args:
            user_id: User ID who initiated generation
            request_id: Request ID for linking events
            kb_id: Knowledge base ID
            document_type: Type of document generated
            citation_count: Number of citations in output
            source_document_ids: List of source document IDs
            generation_time_ms: Time from request to completion
            output_word_count: Word count of generated content
            confidence_score: Final confidence score (0.0-1.0)
        """
        await self.log_event(
            action="generation.complete",
            resource_type="draft",
            user_id=user_id,
            details={
                "request_id": request_id,
                "kb_id": str(kb_id),
                "document_type": document_type,
                "citation_count": citation_count,
                "source_document_ids": source_document_ids,
                "generation_time_ms": generation_time_ms,
                "output_word_count": output_word_count,
                "confidence_score": confidence_score,
                "success": True,
            },
        )

    async def log_generation_failed(
        self,
        user_id: UUID,
        request_id: str,
        kb_id: UUID,
        document_type: str,
        error_message: str,
        error_type: str,
        generation_time_ms: int,
        failure_stage: str,
    ) -> None:
        """Log failed generation attempt.

        Args:
            user_id: User ID who initiated generation
            request_id: Request ID for linking events
            kb_id: Knowledge base ID
            document_type: Type of document attempted
            error_message: Exception message (sanitized, truncated)
            error_type: Exception class name
            generation_time_ms: Time until failure
            failure_stage: "retrieval" | "context_build" | "llm_generation" | "citation_extraction"
        """
        await self.log_event(
            action="generation.failed",
            resource_type="draft",
            user_id=user_id,
            details={
                "request_id": request_id,
                "kb_id": str(kb_id),
                "document_type": document_type,
                "error_message": error_message[:500],  # Sanitized, truncated
                "error_type": error_type,
                "generation_time_ms": generation_time_ms,
                "failure_stage": failure_stage,
                "success": False,
            },
        )

    async def log_feedback(
        self,
        user_id: UUID,
        draft_id: UUID,
        feedback_type: str,
        feedback_comments: str | None = None,
        related_request_id: str | None = None,
    ) -> None:
        """Log user feedback on generated draft.

        Args:
            user_id: User ID who submitted feedback
            draft_id: Draft identifier
            feedback_type: Type of feedback
            feedback_comments: Optional text feedback (truncated to 1000 chars)
            related_request_id: Request ID linking back to generation
        """
        await self.log_event(
            action="generation.feedback",
            resource_type="draft",
            user_id=user_id,
            resource_id=draft_id,
            details={
                "feedback_type": feedback_type,
                "feedback_comments": feedback_comments[:1000]
                if feedback_comments
                else None,
                "related_request_id": related_request_id,
            },
        )

    async def log_export(
        self,
        user_id: UUID,
        draft_id: UUID | None,
        export_format: str,
        citation_count: int,
        file_size_bytes: int,
        related_request_id: str | None = None,
    ) -> None:
        """Log document export.

        Args:
            user_id: User ID who exported document
            draft_id: Draft identifier (if available)
            export_format: Export format (docx, pdf, markdown)
            citation_count: Number of citations in exported document
            file_size_bytes: Size of generated file
            related_request_id: Request ID linking back to generation
        """
        await self.log_event(
            action="document.export",
            resource_type="document",
            user_id=user_id,
            resource_id=draft_id,
            details={
                "export_format": export_format,
                "citation_count": citation_count,
                "file_size_bytes": file_size_bytes,
                "related_request_id": related_request_id,
            },
        )

    async def log_export_failed(
        self,
        user_id: UUID,
        draft_id: UUID | None,
        export_format: str,
        error_message: str,
        kb_id: UUID | None = None,
    ) -> None:
        """Log failed document export (AC-7.19.3).

        Args:
            user_id: User ID who attempted export
            draft_id: Draft identifier (if available)
            export_format: Requested export format (docx, pdf, markdown)
            error_message: Error message describing the failure
            kb_id: Knowledge base ID (if available)
        """
        await self.log_event(
            action="document.export_failed",
            resource_type="document",
            user_id=user_id,
            resource_id=draft_id,
            details={
                "export_format": export_format,
                "error": error_message[:500],  # Truncate long errors
                "kb_id": str(kb_id) if kb_id else None,
            },
        )

    def _build_filtered_query(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_email: str | None = None,
        event_type: str | None = None,
        resource_type: str | None = None,
    ):
        """Build base filtered query (DRY - reused by query_audit_logs, get_events_stream, count_events).

        Args:
            start_date: Filter events >= start_date
            end_date: Filter events <= end_date
            user_email: Filter by user email (case-insensitive partial match)
            event_type: Filter by event type (exact match)
            resource_type: Filter by resource type (exact match)

        Returns:
            SQLAlchemy select query with filters applied
        """
        query = select(AuditEvent)

        if start_date:
            query = query.where(AuditEvent.timestamp >= start_date)
        if end_date:
            query = query.where(AuditEvent.timestamp <= end_date)
        if user_email:
            # Join with users table to filter by email
            query = query.join(User, AuditEvent.user_id == User.id).where(
                User.email.ilike(f"%{user_email}%")
            )
        if event_type:
            query = query.where(AuditEvent.action == event_type)
        if resource_type:
            query = query.where(AuditEvent.resource_type == resource_type)

        return query

    async def query_audit_logs(
        self,
        db: AsyncSession,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_email: str | None = None,
        event_type: str | None = None,
        resource_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditEvent], int]:
        """Query audit logs with filters and pagination.

        Args:
            db: Async SQLAlchemy session
            start_date: Filter events >= start_date (ISO 8601)
            end_date: Filter events <= end_date (ISO 8601)
            user_email: Filter by user email (case-insensitive partial match)
            event_type: Filter by event type (exact match)
            resource_type: Filter by resource type (exact match)
            page: Page number (1-indexed)
            page_size: Results per page (default 50, max enforced by caller)

        Returns:
            Tuple of (events, total_count)
        """
        # Build query with filters (REUSE _build_filtered_query)
        query = self._build_filtered_query(
            start_date=start_date,
            end_date=end_date,
            user_email=user_email,
            event_type=event_type,
            resource_type=resource_type,
        )

        # Sort by timestamp DESC (newest first)
        query = query.order_by(AuditEvent.timestamp.desc())

        # Get total count (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.limit(page_size).offset(offset)

        # Execute query with timeout (30s)
        try:
            result = await asyncio.wait_for(db.execute(query), timeout=30.0)
            events = list(result.scalars().all())
        except TimeoutError:
            logger.error(
                "audit_query_timeout",
                filters={
                    "start_date": start_date,
                    "end_date": end_date,
                    "user_email": user_email,
                    "event_type": event_type,
                    "resource_type": resource_type,
                },
            )
            raise

        return events, total_count

    async def get_events_stream(
        self,
        db: AsyncSession,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_email: str | None = None,
        event_type: str | None = None,
        resource_type: str | None = None,
        batch_size: int = 1000,
    ) -> AsyncGenerator[list[AuditEvent], None]:
        """Stream audit events in batches for export.

        Uses SQLAlchemy yield_per() for server-side cursor pagination to avoid
        loading all records into memory.

        Args:
            db: Async SQLAlchemy session
            start_date: Filter events >= start_date
            end_date: Filter events <= end_date
            user_email: Filter by user email (case-insensitive partial match)
            event_type: Filter by event type (exact match)
            resource_type: Filter by resource type (exact match)
            batch_size: Number of records to fetch per batch (default 1000)

        Yields:
            List[AuditEvent]: Batches of audit events
        """
        # REUSE _build_filtered_query (DRY principle)
        query = self._build_filtered_query(
            start_date=start_date,
            end_date=end_date,
            user_email=user_email,
            event_type=event_type,
            resource_type=resource_type,
        )

        # Sort by timestamp DESC (newest first)
        query = query.order_by(AuditEvent.timestamp.desc())

        # Execute query with streaming (yield_per for server-side cursor)
        try:
            result = await asyncio.wait_for(
                db.stream(query.execution_options(yield_per=batch_size)), timeout=30.0
            )

            batch = []
            async for (event,) in result:
                batch.append(event)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            # Yield remaining events
            if batch:
                yield batch
        except TimeoutError:
            logger.error(
                "audit_export_stream_timeout",
                filters={
                    "start_date": start_date,
                    "end_date": end_date,
                    "user_email": user_email,
                    "event_type": event_type,
                    "resource_type": resource_type,
                },
            )
            raise

    async def count_events(
        self,
        db: AsyncSession,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_email: str | None = None,
        event_type: str | None = None,
        resource_type: str | None = None,
    ) -> int:
        """Count total events matching filters (for audit log metadata).

        Args:
            db: Async SQLAlchemy session
            start_date: Filter events >= start_date
            end_date: Filter events <= end_date
            user_email: Filter by user email (case-insensitive partial match)
            event_type: Filter by event type (exact match)
            resource_type: Filter by resource type (exact match)

        Returns:
            int: Total count of matching events
        """
        # REUSE _build_filtered_query (DRY principle)
        query = self._build_filtered_query(
            start_date=start_date,
            end_date=end_date,
            user_email=user_email,
            event_type=event_type,
            resource_type=resource_type,
        )

        # Wrap in count query
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        return result.scalar() or 0

    def _sanitize_pii(self, text: str) -> str:
        """Sanitize PII patterns from text (Story 5.14, AC2).

        Replaces common PII patterns with placeholders:
        - Email addresses → [EMAIL]
        - Phone numbers → [PHONE]
        - SSN patterns → [SSN]
        - Credit card patterns → [CC]

        Args:
            text: Input text that may contain PII

        Returns:
            Text with PII patterns replaced by placeholders
        """
        import re

        if not text:
            return text

        patterns = {
            "email": (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
            "phone": (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]"),
            "ssn": (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
            "credit_card": (
                r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
                "[CC]",
            ),
        }

        result = text
        for pattern, replacement in patterns.values():
            result = re.sub(pattern, replacement, result)
        return result

    def redact_pii(self, event: AuditEvent) -> AuditEvent:
        """Redact PII fields from audit event.

        Redacts:
        - IP address → "XXX.XXX.XXX.XXX"
        - Email addresses in details → "***@***.***"
        - Sensitive keys in details (passwords, tokens, api_keys)

        Args:
            event: Original audit event

        Returns:
            New AuditEvent instance with redacted PII
        """
        # Create a shallow copy of the event
        redacted_event = AuditEvent(
            id=event.id,
            timestamp=event.timestamp,
            user_id=event.user_id,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            details=event.details.copy() if event.details else None,
            ip_address="XXX.XXX.XXX.XXX" if event.ip_address else None,
        )

        # Redact sensitive fields in details JSON
        if redacted_event.details:
            sensitive_keys = [
                "password",
                "token",
                "api_key",
                "secret",
                "authorization",
            ]
            for key in sensitive_keys:
                if key in redacted_event.details:
                    redacted_event.details[key] = "[REDACTED]"

        return redacted_event


# Singleton instance for use across the application
audit_service = AuditService()


def get_audit_service() -> AuditService:
    """Dependency injection for AuditService.

    Returns:
        AuditService singleton instance
    """
    return audit_service
