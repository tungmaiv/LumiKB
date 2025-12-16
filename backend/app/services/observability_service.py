"""Observability service for fire-and-forget telemetry data collection.

This module provides:
- TraceContext: Container for distributed trace context with W3C-compliant IDs
- ObservabilityProvider: Abstract interface for observability providers
- PostgreSQLProvider: Always-on PostgreSQL/TimescaleDB storage provider
- ObservabilityService: Central facade with provider fan-out and fail-safe error handling

Story 9-2: PostgreSQL Provider Implementation
Story 9-3: TraceContext and Core Service
"""

import secrets
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import celery_session_factory
from app.models.observability import (
    DocumentEvent,
    ObsChatMessage,
    Span,
    Trace,
)

logger = structlog.get_logger()


# Text truncation limits
MAX_ERROR_MESSAGE_LENGTH = 1000
MAX_PREVIEW_LENGTH = 500


def truncate_text(text: str | None, max_length: int) -> str | None:
    """Truncate text to max length, handling None gracefully.

    Args:
        text: Text to truncate (may be None)
        max_length: Maximum allowed length

    Returns:
        Truncated text or None if input was None
    """
    if text is None:
        return None
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def generate_trace_id() -> str:
    """Generate W3C-compliant trace ID (32 hex characters).

    Returns:
        32-character hexadecimal string
    """
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate W3C-compliant span ID (16 hex characters).

    Returns:
        16-character hexadecimal string
    """
    return secrets.token_hex(8)


@dataclass
class TraceContext:
    """Container for distributed trace context with W3C-compliant IDs.

    Holds all context needed to correlate traces, spans, and events across
    the system. Supports nested span creation via child_context().

    Attributes:
        trace_id: W3C trace-id (32 hex chars) - identifies the entire trace
        span_id: W3C span-id (16 hex chars) - identifies current span
        parent_span_id: Optional parent span ID for nested spans
        user_id: Optional user who initiated the trace
        session_id: Optional chat session ID
        kb_id: Optional knowledge base context
        db_trace_id: Database UUID set after trace is persisted
        timestamp: Trace start timestamp for composite key lookups
    """

    trace_id: str
    span_id: str = field(default_factory=generate_span_id)
    parent_span_id: str | None = None
    user_id: UUID | None = None
    session_id: str | None = None
    kb_id: UUID | None = None
    db_trace_id: UUID | None = None
    timestamp: datetime | None = None

    def child_context(self, parent_span_id: str) -> "TraceContext":
        """Create a child context for nested span creation.

        Preserves trace_id and user context while creating a new span_id
        and linking to the parent span.

        Args:
            parent_span_id: The span ID to set as parent

        Returns:
            New TraceContext with same trace_id, new span_id, linked parent
        """
        return TraceContext(
            trace_id=self.trace_id,
            span_id=generate_span_id(),
            parent_span_id=parent_span_id,
            user_id=self.user_id,
            session_id=self.session_id,
            kb_id=self.kb_id,
            db_trace_id=self.db_trace_id,
            timestamp=self.timestamp,
        )


class ObservabilityProvider(ABC):
    """Abstract base class for observability providers.

    Defines the interface for all observability providers. Providers implement
    fire-and-forget methods that never block or propagate exceptions.

    Properties:
        name: Provider identifier (e.g., "postgresql", "langfuse")
        enabled: Whether the provider is active
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name identifier."""
        ...

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Return whether the provider is enabled."""
        ...

    @abstractmethod
    async def start_trace(
        self,
        trace_id: str,
        name: str,
        timestamp: datetime,
        user_id: UUID | None = None,
        kb_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Start a new trace.

        Args:
            trace_id: W3C trace-id (32 hex chars)
            name: Human-readable trace name
            timestamp: Trace start timestamp (for composite key consistency)
            user_id: Optional user who initiated the trace
            kb_id: Optional knowledge base context
            metadata: Additional context as JSONB
        """
        ...

    @abstractmethod
    async def end_trace(
        self,
        trace_id: str,
        timestamp: datetime,
        status: str,
        duration_ms: int,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """End a trace with status and duration.

        Args:
            trace_id: W3C trace-id to update
            timestamp: Original trace start timestamp (for composite key)
            status: Final status (completed, failed)
            duration_ms: Total trace duration in milliseconds
            error_message: Error details if failed
            metadata: Additional context to merge
        """
        ...

    @abstractmethod
    async def start_span(
        self,
        span_id: str,
        trace_id: str,
        name: str,
        span_type: str,
        parent_span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Start a new span within a trace.

        Args:
            span_id: W3C span-id (16 hex chars)
            trace_id: Parent trace identifier
            name: Human-readable span name
            span_type: Operation type (llm, retrieval, generation, embedding)
            parent_span_id: Optional parent span for nesting
            metadata: Additional context as JSONB
        """
        ...

    @abstractmethod
    async def end_span(
        self,
        span_id: str,
        timestamp: datetime,
        status: str,
        duration_ms: int,
        error_message: str | None = None,
        **metrics: Any,
    ) -> None:
        """End a span with status and type-specific metrics.

        Args:
            span_id: Span ID to update
            timestamp: Original span start timestamp (for composite key)
            status: Final status (completed, failed)
            duration_ms: Span duration in milliseconds
            error_message: Error details if failed
            **metrics: Type-specific metrics (input_tokens, output_tokens, model, etc.)
        """
        ...

    @abstractmethod
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
        """Log an LLM call as a span with LLM-specific metrics.

        Args:
            trace_id: Parent trace identifier
            name: LLM call name (e.g., "chat_completion", "embedding")
            model: Model identifier (e.g., "gpt-4", "text-embedding-3-small")
            input_tokens: Token count for input
            output_tokens: Token count for output
            duration_ms: Call duration in milliseconds
            status: Call status (completed, failed)
            error_message: Error details if failed
            parent_span_id: Optional parent span for nesting
            metadata: Additional context as JSONB

        Returns:
            Generated span_id for reference
        """
        ...

    @abstractmethod
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
        """Log a chat message for observability tracking.

        Args:
            trace_id: Associated trace for correlation
            role: Message role (user, assistant, system)
            content: Message content
            user_id: User who sent/received the message
            kb_id: Knowledge base context
            conversation_id: Conversation grouping
            input_tokens: Tokens in input (for assistant messages)
            output_tokens: Tokens in output (for assistant messages)
            model: Model used for generation
            latency_ms: Response latency
            feedback_type: User feedback (thumbs_up, thumbs_down)
            feedback_comment: Additional feedback text
            metadata: Additional context as JSONB
        """
        ...

    @abstractmethod
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
        """Log a document processing event.

        Args:
            trace_id: Associated trace for correlation
            document_id: Document being processed
            kb_id: Knowledge base context
            event_type: Event type (upload, parse, chunk, embed, index, delete)
            status: Event status (started, completed, failed)
            duration_ms: Event duration in milliseconds
            chunk_count: Number of chunks (for chunking events)
            token_count: Token count (for embedding events)
            error_message: Error details if failed
            metadata: Additional context as JSONB
        """
        ...


class PostgreSQLProvider(ObservabilityProvider):
    """PostgreSQL-based observability provider using TimescaleDB.

    Always-on provider that stores all traces, spans, and events to the database.
    Uses fire-and-forget pattern - never blocks or propagates exceptions.

    Uses dedicated session factory to avoid blocking request sessions.
    """

    def __init__(self) -> None:
        """Initialize the PostgreSQL provider.

        Always enabled - no config toggle.
        """
        self._enabled = True

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "postgresql"

    @property
    def enabled(self) -> bool:
        """Return whether the provider is enabled (always True)."""
        return self._enabled

    def _get_session(self) -> AsyncSession:
        """Get a dedicated database session context manager.

        Uses celery_session_factory with NullPool to avoid event loop issues
        when called from Celery workers via run_async(). The NullPool creates
        fresh connections each time, avoiding the "Future attached to different loop"
        error that occurs with pooled connections.

        Returns:
            AsyncSession context manager for database operations
        """
        return celery_session_factory()

    async def start_trace(
        self,
        trace_id: str,
        name: str,
        timestamp: datetime,
        user_id: UUID | None = None,
        kb_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Start a new trace. Fire-and-forget - exceptions logged, not propagated."""
        try:
            async with self._get_session() as session:
                trace = Trace(
                    trace_id=trace_id,
                    timestamp=timestamp,
                    name=name,
                    user_id=user_id,
                    kb_id=kb_id,
                    status="in_progress",
                    attributes=metadata,
                )
                session.add(trace)
                await session.commit()
                logger.debug(
                    "postgresql_trace_started",
                    trace_id=trace_id,
                    name=name,
                )
        except Exception as e:
            logger.warning(
                "postgresql_start_trace_failed",
                trace_id=trace_id,
                error=str(e),
            )

    async def end_trace(
        self,
        trace_id: str,
        timestamp: datetime,
        status: str,
        duration_ms: int,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """End a trace with status and duration. Fire-and-forget."""
        try:
            async with self._get_session() as session:
                values: dict[str, Any] = {
                    "status": status,
                    "duration_ms": duration_ms,
                }
                if error_message:
                    # Truncate error message
                    values["attributes"] = {
                        **(metadata or {}),
                        "error_message": truncate_text(
                            error_message, MAX_ERROR_MESSAGE_LENGTH
                        ),
                    }
                elif metadata:
                    values["attributes"] = metadata

                # First try exact timestamp match
                stmt = (
                    update(Trace)
                    .where(Trace.trace_id == trace_id, Trace.timestamp == timestamp)
                    .values(**values)
                )
                result = await session.execute(stmt)

                # If no rows updated, try matching by trace_id only
                # (timestamp precision mismatch between Python and PostgreSQL)
                if result.rowcount == 0:
                    logger.warning(
                        "postgresql_end_trace_timestamp_mismatch",
                        trace_id=trace_id,
                        timestamp=timestamp.isoformat(),
                    )
                    # Fallback: update by trace_id only (safe since trace_id is unique)
                    fallback_stmt = (
                        update(Trace).where(Trace.trace_id == trace_id).values(**values)
                    )
                    fallback_result = await session.execute(fallback_stmt)
                    if fallback_result.rowcount == 0:
                        logger.warning(
                            "postgresql_end_trace_no_rows_updated",
                            trace_id=trace_id,
                        )

                await session.commit()
                logger.debug(
                    "postgresql_trace_ended",
                    trace_id=trace_id,
                    status=status,
                    duration_ms=duration_ms,
                )
        except Exception as e:
            logger.warning(
                "postgresql_end_trace_failed",
                trace_id=trace_id,
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
        """Start a new span within a trace. Fire-and-forget."""
        try:
            async with self._get_session() as session:
                span = Span(
                    span_id=span_id,
                    trace_id=trace_id,
                    parent_span_id=parent_span_id,
                    name=name,
                    span_type=span_type,
                    status="in_progress",
                    attributes=metadata,
                )
                session.add(span)
                await session.commit()
                logger.debug(
                    "postgresql_span_started",
                    span_id=span_id,
                    trace_id=trace_id,
                    name=name,
                    span_type=span_type,
                )
        except Exception as e:
            logger.warning(
                "postgresql_start_span_failed",
                span_id=span_id,
                trace_id=trace_id,
                error=str(e),
            )

    async def end_span(
        self,
        span_id: str,
        timestamp: datetime,
        status: str,
        duration_ms: int,
        error_message: str | None = None,
        **metrics: Any,
    ) -> None:
        """End a span with status and type-specific metrics. Fire-and-forget."""
        try:
            async with self._get_session() as session:
                values: dict[str, Any] = {
                    "status": status,
                    "duration_ms": duration_ms,
                }

                # Add error message if present
                if error_message:
                    values["error_message"] = truncate_text(
                        error_message, MAX_ERROR_MESSAGE_LENGTH
                    )

                # Add type-specific metrics via kwargs
                valid_span_fields = {
                    "input_tokens",
                    "output_tokens",
                    "model",
                }
                for key, value in metrics.items():
                    if key in valid_span_fields and value is not None:
                        values[key] = value

                # First try exact timestamp match
                stmt = (
                    update(Span)
                    .where(Span.span_id == span_id, Span.timestamp == timestamp)
                    .values(**values)
                )
                result = await session.execute(stmt)

                # If no rows updated, try matching by span_id only
                # (timestamp precision mismatch between Python and PostgreSQL)
                if result.rowcount == 0:
                    logger.warning(
                        "postgresql_end_span_timestamp_mismatch",
                        span_id=span_id,
                        timestamp=timestamp.isoformat(),
                    )
                    # Fallback: update by span_id only (safe since span_id is unique)
                    fallback_stmt = (
                        update(Span).where(Span.span_id == span_id).values(**values)
                    )
                    fallback_result = await session.execute(fallback_stmt)
                    if fallback_result.rowcount == 0:
                        logger.warning(
                            "postgresql_end_span_no_rows_updated",
                            span_id=span_id,
                        )

                await session.commit()
                logger.debug(
                    "postgresql_span_ended",
                    span_id=span_id,
                    status=status,
                    duration_ms=duration_ms,
                )
        except Exception as e:
            logger.warning(
                "postgresql_end_span_failed",
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
        """Log an LLM call as a span with LLM-specific metrics. Fire-and-forget."""
        span_id = generate_span_id()
        try:
            async with self._get_session() as session:
                span = Span(
                    span_id=span_id,
                    trace_id=trace_id,
                    parent_span_id=parent_span_id,
                    name=name,
                    span_type="llm",
                    status=status,
                    duration_ms=duration_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=model,
                    error_message=truncate_text(error_message, MAX_ERROR_MESSAGE_LENGTH)
                    if error_message
                    else None,
                    attributes=metadata,
                )
                session.add(span)
                await session.commit()
                logger.debug(
                    "postgresql_llm_call_logged",
                    span_id=span_id,
                    trace_id=trace_id,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
        except Exception as e:
            logger.warning(
                "postgresql_log_llm_call_failed",
                trace_id=trace_id,
                model=model,
                error=str(e),
            )
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
        """Log a chat message for observability tracking. Fire-and-forget."""
        try:
            async with self._get_session() as session:
                chat_message = ObsChatMessage(
                    trace_id=trace_id,
                    user_id=user_id,
                    kb_id=kb_id,
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=model,
                    latency_ms=latency_ms,
                    feedback_type=feedback_type,
                    feedback_comment=feedback_comment,
                    attributes=metadata,
                )
                session.add(chat_message)
                await session.commit()
                logger.debug(
                    "postgresql_chat_message_logged",
                    trace_id=trace_id,
                    role=role,
                    conversation_id=str(conversation_id) if conversation_id else None,
                )
        except Exception as e:
            logger.warning(
                "postgresql_log_chat_message_failed",
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
        """Log a document processing event. Fire-and-forget."""
        try:
            async with self._get_session() as session:
                doc_event = DocumentEvent(
                    trace_id=trace_id,
                    document_id=document_id,
                    kb_id=kb_id,
                    event_type=event_type,
                    status=status,
                    duration_ms=duration_ms,
                    chunk_count=chunk_count,
                    token_count=token_count,
                    error_message=truncate_text(error_message, MAX_ERROR_MESSAGE_LENGTH)
                    if error_message
                    else None,
                    attributes=metadata,
                )
                session.add(doc_event)
                await session.commit()
                logger.debug(
                    "postgresql_document_event_logged",
                    trace_id=trace_id,
                    document_id=str(document_id),
                    event_type=event_type,
                    status=status,
                )
        except Exception as e:
            logger.warning(
                "postgresql_log_document_event_failed",
                trace_id=trace_id,
                document_id=str(document_id),
                event_type=event_type,
                error=str(e),
            )


# Singleton instance for use across the application
postgresql_provider = PostgreSQLProvider()


def get_postgresql_provider() -> PostgreSQLProvider:
    """Dependency injection for PostgreSQLProvider.

    Returns:
        PostgreSQLProvider singleton instance
    """
    return postgresql_provider


class ObservabilityService:
    """Central observability service with provider registry and fan-out.

    Singleton service that coordinates all observability operations across
    multiple providers. Implements fire-and-forget pattern where provider
    errors are logged but never propagated to callers.

    Usage:
        obs = ObservabilityService.get_instance()
        ctx = await obs.start_trace(name="chat.conversation", user_id=user.id)
        async with obs.span(ctx, "retrieval", "retrieval") as span_id:
            # operation
        await obs.end_trace(ctx, status="success")
    """

    _instance: "ObservabilityService | None" = None

    def __init__(self, providers: list[ObservabilityProvider]) -> None:
        """Initialize with a list of observability providers.

        Args:
            providers: List of providers to fan out to (only enabled ones used)
        """
        # Filter to only enabled providers
        self.providers = [p for p in providers if p.enabled]
        logger.info(
            "observability_service_initialized",
            providers=[p.name for p in self.providers],
        )

    @classmethod
    def get_instance(cls) -> "ObservabilityService":
        """Get or create the singleton instance.

        Lazily initializes the service with PostgreSQL provider (always)
        and LangFuse provider (if configured).

        Returns:
            The singleton ObservabilityService instance
        """
        if cls._instance is None:
            # PostgreSQL provider is always registered first
            providers: list[ObservabilityProvider] = [
                PostgreSQLProvider(),
            ]

            # Story 9-11: Add LangFuseProvider if configured
            from app.services.langfuse_provider import get_langfuse_provider

            langfuse_provider = get_langfuse_provider()
            if langfuse_provider.enabled:
                providers.append(langfuse_provider)

            cls._instance = cls(providers)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing only)."""
        cls._instance = None

    async def start_trace(
        self,
        name: str,
        user_id: UUID | None = None,
        session_id: str | None = None,
        kb_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceContext:
        """Start a new trace and fan out to all enabled providers.

        Creates a TraceContext with generated trace_id and span_id,
        then notifies all providers. Provider failures are logged but
        never propagated.

        Args:
            name: Human-readable trace name (e.g., "chat.conversation")
            user_id: Optional user who initiated the trace
            session_id: Optional chat session ID
            kb_id: Optional knowledge base context
            metadata: Additional context as JSONB

        Returns:
            TraceContext with generated IDs for use in spans
        """
        trace_id = generate_trace_id()
        timestamp = datetime.utcnow()

        ctx = TraceContext(
            trace_id=trace_id,
            span_id=generate_span_id(),
            user_id=user_id,
            session_id=session_id,
            kb_id=kb_id,
            timestamp=timestamp,
        )

        # Fan out to all providers
        for provider in self.providers:
            try:
                await provider.start_trace(
                    trace_id=trace_id,
                    name=name,
                    timestamp=timestamp,
                    user_id=user_id,
                    kb_id=kb_id,
                    metadata=metadata,
                )
            except Exception as e:
                logger.warning(
                    "provider_start_trace_failed",
                    provider=provider.name,
                    trace_id=trace_id,
                    error=str(e),
                )

        return ctx

    async def end_trace(
        self,
        ctx: TraceContext,
        status: str,
        duration_ms: int | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """End a trace and fan out to all enabled providers.

        Calculates duration if not provided using ctx.timestamp.
        Provider failures are logged but never propagated.

        Args:
            ctx: TraceContext from start_trace
            status: Final status (completed, failed)
            duration_ms: Total trace duration (auto-calculated if None)
            error_message: Error details if failed
            metadata: Additional context to merge
        """
        if ctx.timestamp is None:
            logger.warning(
                "end_trace_missing_timestamp",
                trace_id=ctx.trace_id,
            )
            return

        # Calculate duration if not provided
        if duration_ms is None:
            duration_ms = int(
                (datetime.utcnow() - ctx.timestamp).total_seconds() * 1000
            )

        # Fan out to all providers
        for provider in self.providers:
            try:
                await provider.end_trace(
                    trace_id=ctx.trace_id,
                    timestamp=ctx.timestamp,
                    status=status,
                    duration_ms=duration_ms,
                    error_message=error_message,
                    metadata=metadata,
                )
            except Exception as e:
                logger.warning(
                    "provider_end_trace_failed",
                    provider=provider.name,
                    trace_id=ctx.trace_id,
                    error=str(e),
                )

    @asynccontextmanager
    async def span(
        self,
        ctx: TraceContext,
        name: str,
        span_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Async context manager for automatic span timing and error capture.

        Creates a span in all providers, tracks timing using monotonic clock,
        captures any exceptions, and ensures span is ended with proper status.

        Args:
            ctx: TraceContext for the parent trace
            name: Human-readable span name
            span_type: Operation type (llm, retrieval, generation, embedding)
            metadata: Additional context as JSONB

        Yields:
            The span_id (from PostgreSQL provider, or generated fallback)

        Example:
            async with obs.span(ctx, "retrieval", "retrieval") as span_id:
                results = await search_service.search(query)
        """
        span_id = generate_span_id()
        span_timestamp = datetime.utcnow()
        start_time = time.monotonic()
        error_info: tuple[str | None, str | None] = (None, None)

        # Start span in all providers
        for provider in self.providers:
            try:
                await provider.start_span(
                    span_id=span_id,
                    trace_id=ctx.trace_id,
                    name=name,
                    span_type=span_type,
                    parent_span_id=ctx.parent_span_id,
                    metadata=metadata,
                )
            except Exception as e:
                logger.warning(
                    "provider_start_span_failed",
                    provider=provider.name,
                    span_id=span_id,
                    trace_id=ctx.trace_id,
                    error=str(e),
                )

        try:
            yield span_id
        except Exception as e:
            # Capture error info but re-raise
            error_info = (type(e).__name__, str(e))
            raise
        finally:
            # Calculate duration using monotonic clock
            duration_ms = int((time.monotonic() - start_time) * 1000)
            status = "failed" if error_info[0] else "completed"
            error_message = (
                f"{error_info[0]}: {error_info[1]}" if error_info[0] else None
            )

            # End span in all providers
            for provider in self.providers:
                try:
                    await provider.end_span(
                        span_id=span_id,
                        timestamp=span_timestamp,
                        status=status,
                        duration_ms=duration_ms,
                        error_message=error_message,
                    )
                except Exception as e:
                    logger.warning(
                        "provider_end_span_failed",
                        provider=provider.name,
                        span_id=span_id,
                        error=str(e),
                    )

    async def log_llm_call(
        self,
        ctx: TraceContext,
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
        """Log an LLM call and fan out to all providers.

        Args:
            ctx: TraceContext for correlation
            name: LLM call name (e.g., "chat_completion", "embedding")
            model: Model identifier (e.g., "gpt-4", "text-embedding-3-small")
            input_tokens: Token count for input
            output_tokens: Token count for output
            duration_ms: Call duration in milliseconds
            status: Call status (completed, failed)
            error_message: Error details if failed
            parent_span_id: Optional parent span for nesting
            metadata: Additional context as JSONB

        Returns:
            Generated span_id for reference
        """
        span_id = generate_span_id()

        for provider in self.providers:
            try:
                await provider.log_llm_call(
                    trace_id=ctx.trace_id,
                    name=name,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=duration_ms,
                    status=status,
                    error_message=error_message,
                    parent_span_id=parent_span_id or ctx.parent_span_id,
                    metadata=metadata,
                )
            except Exception as e:
                logger.warning(
                    "provider_log_llm_call_failed",
                    provider=provider.name,
                    trace_id=ctx.trace_id,
                    model=model,
                    error=str(e),
                )

        return span_id

    async def log_chat_message(
        self,
        ctx: TraceContext,
        role: str,
        content: str,
        conversation_id: UUID | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        model: str | None = None,
        latency_ms: int | None = None,
        feedback_type: str | None = None,
        feedback_comment: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log a chat message and fan out to all providers.

        Args:
            ctx: TraceContext for correlation (provides user_id, kb_id)
            role: Message role (user, assistant, system)
            content: Message content
            conversation_id: Conversation grouping
            input_tokens: Tokens in input (for assistant messages)
            output_tokens: Tokens in output (for assistant messages)
            model: Model used for generation
            latency_ms: Response latency
            feedback_type: User feedback (thumbs_up, thumbs_down)
            feedback_comment: Additional feedback text
            metadata: Additional context as JSONB
        """
        for provider in self.providers:
            try:
                await provider.log_chat_message(
                    trace_id=ctx.trace_id,
                    role=role,
                    content=content,
                    user_id=ctx.user_id,
                    kb_id=ctx.kb_id,
                    conversation_id=conversation_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=model,
                    latency_ms=latency_ms,
                    feedback_type=feedback_type,
                    feedback_comment=feedback_comment,
                    metadata=metadata,
                )
            except Exception as e:
                logger.warning(
                    "provider_log_chat_message_failed",
                    provider=provider.name,
                    trace_id=ctx.trace_id,
                    role=role,
                    error=str(e),
                )

    async def log_document_event(
        self,
        ctx: TraceContext,
        document_id: UUID,
        event_type: str,
        status: str,
        duration_ms: int | None = None,
        chunk_count: int | None = None,
        token_count: int | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log a document processing event and fan out to all providers.

        Args:
            ctx: TraceContext for correlation (provides kb_id)
            document_id: Document being processed
            event_type: Event type (upload, parse, chunk, embed, index, delete)
            status: Event status (started, completed, failed)
            duration_ms: Event duration in milliseconds
            chunk_count: Number of chunks (for chunking events)
            token_count: Token count (for embedding events)
            error_message: Error details if failed
            metadata: Additional context as JSONB
        """
        if ctx.kb_id is None:
            logger.warning(
                "log_document_event_missing_kb_id",
                trace_id=ctx.trace_id,
                document_id=str(document_id),
            )
            return

        for provider in self.providers:
            try:
                await provider.log_document_event(
                    trace_id=ctx.trace_id,
                    document_id=document_id,
                    kb_id=ctx.kb_id,
                    event_type=event_type,
                    status=status,
                    duration_ms=duration_ms,
                    chunk_count=chunk_count,
                    token_count=token_count,
                    error_message=error_message,
                    metadata=metadata,
                )
            except Exception as e:
                logger.warning(
                    "provider_log_document_event_failed",
                    provider=provider.name,
                    trace_id=ctx.trace_id,
                    document_id=str(document_id),
                    error=str(e),
                )

    async def log_processing_span(
        self,
        ctx: TraceContext,
        name: str,
        span_type: str,
        status: str,
        duration_ms: int,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Log a completed processing span (for synchronous processing contexts).

        This creates a span with both start and end in one call, useful for
        synchronous document processing where we can't use async context managers.

        Args:
            ctx: TraceContext for correlation
            name: Human-readable span name (e.g., "upload", "parse", "chunk")
            span_type: Operation type (e.g., "processing", "embedding", "indexing")
            status: Final status (completed, failed)
            duration_ms: Span duration in milliseconds
            error_message: Error details if failed
            metadata: Additional context as JSONB

        Returns:
            Generated span_id for reference
        """
        span_id = generate_span_id()
        timestamp = datetime.utcnow()

        for provider in self.providers:
            try:
                # Create the span with completed status
                await provider.start_span(
                    span_id=span_id,
                    trace_id=ctx.trace_id,
                    name=name,
                    span_type=span_type,
                    parent_span_id=ctx.parent_span_id,
                    metadata=metadata,
                )
                # Immediately end it with the final status
                await provider.end_span(
                    span_id=span_id,
                    timestamp=timestamp,
                    status=status,
                    duration_ms=duration_ms,
                    error_message=error_message,
                )
            except Exception as e:
                logger.warning(
                    "provider_log_processing_span_failed",
                    provider=provider.name,
                    trace_id=ctx.trace_id,
                    span_id=span_id,
                    error=str(e),
                )

        return span_id


# Singleton accessor
def get_observability_service() -> ObservabilityService:
    """Get the singleton ObservabilityService instance.

    Returns:
        The singleton ObservabilityService instance
    """
    return ObservabilityService.get_instance()
