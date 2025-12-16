"""LangFuse observability provider for external LLM tracing.

Story 9-11: LangFuse Provider Implementation

Implements the ObservabilityProvider interface for LangFuse integration.
Uses fire-and-forget pattern - never blocks or propagates exceptions.

The provider is disabled if:
- langfuse_enabled is False
- langfuse_public_key is not configured
- langfuse SDK is not installed (optional dependency)
"""

import asyncio
import concurrent.futures
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.observability import ProviderSyncStatus
from app.services.observability_service import ObservabilityProvider, generate_span_id

logger = structlog.get_logger()

# Try to import langfuse - it's an optional dependency
try:
    from langfuse import Langfuse

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    if TYPE_CHECKING:
        from langfuse import Langfuse


class LangFuseProvider(ObservabilityProvider):
    """LangFuse-based observability provider for external LLM tracing.

    Implements fire-and-forget pattern where all LangFuse SDK calls are
    wrapped in try/except. Exceptions are logged but never propagated.

    The provider tracks sync status in provider_sync_status table and
    flushes on trace end to ensure data is sent to LangFuse.

    Configuration:
        - LUMIKB_LANGFUSE_ENABLED: Enable/disable the provider
        - LUMIKB_LANGFUSE_PUBLIC_KEY: LangFuse public key (required)
        - LUMIKB_LANGFUSE_SECRET_KEY: LangFuse secret key (required)
        - LUMIKB_LANGFUSE_HOST: LangFuse host (default: cloud.langfuse.com)
    """

    def __init__(self) -> None:
        """Initialize the LangFuse provider.

        Provider is disabled if:
        - SDK not available
        - Not enabled in settings
        - Public key not configured
        """
        self._client: Langfuse | None = None
        self._enabled = False
        self._traces: dict[str, Any] = {}  # Cache active traces by trace_id

        # Check if langfuse SDK is available
        if not LANGFUSE_AVAILABLE:
            logger.info(
                "langfuse_provider_disabled",
                reason="langfuse SDK not installed",
            )
            return

        # Check if enabled in settings
        if not settings.langfuse_enabled:
            logger.info(
                "langfuse_provider_disabled",
                reason="langfuse_enabled is False",
            )
            return

        # Check if credentials are configured
        if not settings.langfuse_public_key:
            logger.info(
                "langfuse_provider_disabled",
                reason="langfuse_public_key not configured",
            )
            return

        if not settings.langfuse_secret_key:
            logger.info(
                "langfuse_provider_disabled",
                reason="langfuse_secret_key not configured",
            )
            return

        # Initialize the LangFuse client
        try:
            self._client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
            self._enabled = True
            logger.info(
                "langfuse_provider_initialized",
                host=settings.langfuse_host,
            )
        except Exception as e:
            logger.warning(
                "langfuse_provider_init_failed",
                error=str(e),
            )

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "langfuse"

    @property
    def enabled(self) -> bool:
        """Return whether the provider is enabled."""
        return self._enabled

    async def _track_sync_status(
        self,
        entity_type: str,
        entity_id: str,
        status: str = "synced",
        error_message: str | None = None,
    ) -> None:
        """Track sync status in provider_sync_status table.

        Fire-and-forget - exceptions are logged but not propagated.

        Args:
            entity_type: Type of entity (trace, span, chat_message, document_event)
            entity_id: ID of the entity
            status: Sync status (pending, synced, failed)
            error_message: Error details if failed
        """
        try:
            async with async_session_factory() as session:
                sync_record = ProviderSyncStatus(
                    provider_name="langfuse",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    sync_status=status,
                    error_message=error_message,
                    retry_count=1 if status == "failed" else 0,
                    last_synced_at=datetime.utcnow() if status == "synced" else None,
                )
                session.add(sync_record)
                await session.commit()
        except Exception as e:
            logger.warning(
                "langfuse_sync_status_tracking_failed",
                entity_type=entity_type,
                entity_id=entity_id,
                error=str(e),
            )

    async def start_trace(
        self,
        trace_id: str,
        name: str,
        timestamp: datetime,
        user_id: UUID | None = None,
        kb_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Start a new trace in LangFuse. Fire-and-forget."""
        if not self._enabled or not self._client:
            return

        try:
            # Create LangFuse trace
            trace = self._client.trace(
                id=trace_id,
                name=name,
                user_id=str(user_id) if user_id else None,
                metadata={
                    "kb_id": str(kb_id) if kb_id else None,
                    "timestamp": timestamp.isoformat(),
                    **(metadata or {}),
                },
            )
            # Cache the trace for later use
            self._traces[trace_id] = trace

            logger.debug(
                "langfuse_trace_started",
                trace_id=trace_id,
                name=name,
            )

            # Track sync status
            await self._track_sync_status("trace", trace_id, "synced")

        except Exception as e:
            logger.warning(
                "langfuse_start_trace_failed",
                trace_id=trace_id,
                error=str(e),
            )
            await self._track_sync_status("trace", trace_id, "failed", str(e))

    async def end_trace(
        self,
        trace_id: str,
        timestamp: datetime,
        status: str,
        duration_ms: int,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """End a trace in LangFuse. Fire-and-forget.

        Calls flush() with timeout to ensure data is sent to LangFuse
        without blocking indefinitely on network issues.
        """
        if not self._enabled or not self._client:
            return

        try:
            # Get cached trace or create a new reference
            trace = self._traces.pop(trace_id, None)
            if trace is None:
                # Trace might have been started in a different instance
                trace = self._client.trace(id=trace_id)

            # Update trace with final status
            trace.update(
                metadata={
                    "status": status,
                    "duration_ms": duration_ms,
                    "error_message": error_message,
                    **(metadata or {}),
                },
            )

            # Flush to ensure data is sent to LangFuse with timeout
            await self._flush_with_timeout()

            logger.debug(
                "langfuse_trace_ended",
                trace_id=trace_id,
                status=status,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.warning(
                "langfuse_end_trace_failed",
                trace_id=trace_id,
                error=str(e),
            )

    async def _flush_with_timeout(self) -> None:
        """Flush LangFuse client with configurable timeout.

        Uses ThreadPoolExecutor to run blocking flush() in a separate thread
        with timeout protection to prevent indefinite blocking on network issues.
        """
        if not self._client:
            return

        timeout = settings.langfuse_flush_timeout_seconds

        try:
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                await asyncio.wait_for(
                    loop.run_in_executor(executor, self._client.flush),
                    timeout=timeout,
                )
        except TimeoutError:
            logger.warning(
                "langfuse_flush_timeout",
                timeout_seconds=timeout,
            )
        except Exception as e:
            logger.warning(
                "langfuse_flush_failed",
                error=str(e),
            )

    async def start_span(
        self,
        span_id: str,
        trace_id: str,
        name: str,
        span_type: str,
        parent_span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Start a new span in LangFuse. Fire-and-forget."""
        if not self._enabled or not self._client:
            return

        try:
            # Get the parent trace
            trace = self._traces.get(trace_id)
            if trace is None:
                trace = self._client.trace(id=trace_id)
                self._traces[trace_id] = trace

            # Create span within trace
            trace.span(
                id=span_id,
                name=name,
                metadata={
                    "span_type": span_type,
                    "parent_span_id": parent_span_id,
                    **(metadata or {}),
                },
            )

            logger.debug(
                "langfuse_span_started",
                span_id=span_id,
                trace_id=trace_id,
                name=name,
            )

            await self._track_sync_status("span", span_id, "synced")

        except Exception as e:
            logger.warning(
                "langfuse_start_span_failed",
                span_id=span_id,
                trace_id=trace_id,
                error=str(e),
            )
            await self._track_sync_status("span", span_id, "failed", str(e))

    async def end_span(
        self,
        span_id: str,
        timestamp: datetime,
        status: str,
        duration_ms: int,
        error_message: str | None = None,
        **metrics: Any,
    ) -> None:
        """End a span in LangFuse. Fire-and-forget.

        Note: LangFuse SDK handles span completion automatically based on
        context. This method primarily logs the completion for debugging.
        """
        if not self._enabled or not self._client:
            return

        try:
            # LangFuse spans are typically completed via context manager
            # We log the completion for debugging purposes
            logger.debug(
                "langfuse_span_ended",
                span_id=span_id,
                status=status,
                duration_ms=duration_ms,
                metrics=metrics,
            )

        except Exception as e:
            logger.warning(
                "langfuse_end_span_failed",
                span_id=span_id,
                error=str(e),
            )

    async def log_llm_call(
        self,
        trace_id: str,
        name: str,
        model: str,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        duration_ms: int | None = None,
        status: str = "completed",
        error_message: str | None = None,
        parent_span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Log an LLM call as a LangFuse generation. Fire-and-forget."""
        span_id = generate_span_id()

        if not self._enabled or not self._client:
            return span_id

        try:
            # Get the parent trace
            trace = self._traces.get(trace_id)
            if trace is None:
                trace = self._client.trace(id=trace_id)
                self._traces[trace_id] = trace

            # Calculate total tokens
            total_tokens = None
            if input_tokens is not None and output_tokens is not None:
                total_tokens = input_tokens + output_tokens

            # Create generation (LangFuse's term for LLM calls)
            trace.generation(
                id=span_id,
                name=f"llm.{model}" if not name.startswith("llm.") else name,
                model=model,
                usage={
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": total_tokens,
                }
                if input_tokens is not None or output_tokens is not None
                else None,
                metadata={
                    "latency_ms": duration_ms,
                    "status": status,
                    "error_message": error_message,
                    "parent_span_id": parent_span_id,
                    **(metadata or {}),
                },
            )

            logger.debug(
                "langfuse_llm_call_logged",
                span_id=span_id,
                trace_id=trace_id,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            await self._track_sync_status("generation", span_id, "synced")

        except Exception as e:
            logger.warning(
                "langfuse_log_llm_call_failed",
                trace_id=trace_id,
                model=model,
                error=str(e),
            )
            await self._track_sync_status("generation", span_id, "failed", str(e))

        return span_id

    async def log_chat_message(
        self,
        trace_id: str,
        role: str,
        content: str,
        user_id: UUID | None = None,
        kb_id: UUID | None = None,
        conversation_id: UUID | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        model: str | None = None,
        latency_ms: int | None = None,
        feedback_type: str | None = None,
        feedback_comment: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log a chat message as a LangFuse event. Fire-and-forget."""
        if not self._enabled or not self._client:
            return

        try:
            # Get the parent trace
            trace = self._traces.get(trace_id)
            if trace is None:
                trace = self._client.trace(id=trace_id)
                self._traces[trace_id] = trace

            # Create event for chat message
            event_id = generate_span_id()
            trace.event(
                id=event_id,
                name=f"chat.{role}",
                metadata={
                    "role": role,
                    "content_preview": content[:200] if content else None,
                    "user_id": str(user_id) if user_id else None,
                    "kb_id": str(kb_id) if kb_id else None,
                    "conversation_id": str(conversation_id)
                    if conversation_id
                    else None,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "model": model,
                    "latency_ms": latency_ms,
                    "feedback_type": feedback_type,
                    "feedback_comment": feedback_comment,
                    **(metadata or {}),
                },
            )

            logger.debug(
                "langfuse_chat_message_logged",
                trace_id=trace_id,
                role=role,
                conversation_id=str(conversation_id) if conversation_id else None,
            )

            await self._track_sync_status("chat_message", event_id, "synced")

        except Exception as e:
            logger.warning(
                "langfuse_log_chat_message_failed",
                trace_id=trace_id,
                role=role,
                error=str(e),
            )

    async def log_document_event(
        self,
        trace_id: str,
        document_id: UUID,
        kb_id: UUID,
        event_type: str,
        status: str,
        duration_ms: int | None = None,
        chunk_count: int | None = None,
        token_count: int | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log a document processing event in LangFuse. Fire-and-forget."""
        if not self._enabled or not self._client:
            return

        try:
            # Get the parent trace
            trace = self._traces.get(trace_id)
            if trace is None:
                trace = self._client.trace(id=trace_id)
                self._traces[trace_id] = trace

            # Create event for document processing
            event_id = generate_span_id()
            trace.event(
                id=event_id,
                name=f"document.{event_type}",
                metadata={
                    "document_id": str(document_id),
                    "kb_id": str(kb_id),
                    "event_type": event_type,
                    "status": status,
                    "duration_ms": duration_ms,
                    "chunk_count": chunk_count,
                    "token_count": token_count,
                    "error_message": error_message,
                    **(metadata or {}),
                },
            )

            logger.debug(
                "langfuse_document_event_logged",
                trace_id=trace_id,
                document_id=str(document_id),
                event_type=event_type,
                status=status,
            )

            await self._track_sync_status("document_event", event_id, "synced")

        except Exception as e:
            logger.warning(
                "langfuse_log_document_event_failed",
                trace_id=trace_id,
                document_id=str(document_id),
                event_type=event_type,
                error=str(e),
            )


# Singleton instance (created lazily if configured)
_langfuse_provider: LangFuseProvider | None = None


def get_langfuse_provider() -> LangFuseProvider:
    """Get the singleton LangFuseProvider instance.

    Returns:
        LangFuseProvider instance (may be disabled if not configured)
    """
    global _langfuse_provider
    if _langfuse_provider is None:
        _langfuse_provider = LangFuseProvider()
    return _langfuse_provider
