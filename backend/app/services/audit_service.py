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

    async def log_search(
        self,
        user_id: str,
        query: str,
        kb_ids: list[str],
        result_count: int,
        latency_ms: int,
    ) -> None:
        """Log a search query event.

        Args:
            user_id: User ID who performed the search
            query: Search query text
            kb_ids: List of KB IDs searched
            result_count: Number of results returned
            latency_ms: Response latency in milliseconds
        """
        await self.log_event(
            action="search",
            resource_type="search",
            user_id=UUID(user_id),
            details={
                "query": query[:500],  # Truncate for storage
                "kb_ids": kb_ids,
                "result_count": result_count,
                "latency_ms": latency_ms,
            },
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


# Singleton instance for use across the application
audit_service = AuditService()


def get_audit_service() -> AuditService:
    """Dependency injection for AuditService.

    Returns:
        AuditService singleton instance
    """
    return audit_service
