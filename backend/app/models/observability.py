"""Observability models for time-series telemetry data.

This module defines SQLAlchemy models for the observability schema,
which uses TimescaleDB hypertables for efficient time-series storage.

Models:
    - Trace: Distributed trace records (W3C trace context)
    - Span: Individual operations within traces
    - ObsChatMessage: Chat interaction logs
    - DocumentEvent: Document processing events
    - MetricsAggregate: Pre-aggregated metrics
    - ProviderSyncStatus: External provider sync tracking
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class Trace(Base):
    """Distributed trace record following W3C trace context specification.

    A trace represents a single request/operation flow through the system,
    containing multiple spans. Stored in TimescaleDB hypertable with 1-day chunks.

    Attributes:
        trace_id: W3C trace-id (32 hex characters)
        timestamp: When the trace started (hypertable partitioning key)
        name: Human-readable trace name (e.g., "chat_completion", "document_processing")
        user_id: Optional user who initiated the trace
        kb_id: Optional knowledge base context
        status: Current status (in_progress, completed, failed)
        duration_ms: Total trace duration in milliseconds
        metadata: Additional context as JSONB
        synced_to_langfuse: Whether synced to external LangFuse provider
    """

    __tablename__ = "traces"
    __table_args__ = {"schema": "observability"}

    trace_id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        comment="W3C trace-id (32 hex chars)",
    )
    timestamp: Mapped[datetime] = mapped_column(
        primary_key=True,
        server_default=func.now(),
    )
    name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    kb_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="in_progress",
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",  # Column name in DB is 'metadata'
        JSONB,
        nullable=True,
    )
    synced_to_langfuse: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
    )


class Span(Base):
    """Individual operation span within a trace.

    Spans represent discrete operations (LLM calls, retrieval, embedding, etc.)
    and can be nested via parent_span_id. Stored in TimescaleDB hypertable
    with 1-day chunks.

    Attributes:
        span_id: W3C span-id (16 hex characters)
        trace_id: Parent trace identifier
        parent_span_id: Optional parent span for nesting
        timestamp: When the span started (hypertable partitioning key)
        name: Human-readable span name
        span_type: Operation type (llm, retrieval, generation, embedding, etc.)
        duration_ms: Span duration in milliseconds
        input_tokens: Token count for input (LLM spans)
        output_tokens: Token count for output (LLM spans)
        model: Model identifier for LLM spans
        status: Current status (in_progress, completed, failed)
        error_message: Error details if failed
        metadata: Additional context as JSONB
    """

    __tablename__ = "spans"
    __table_args__ = {"schema": "observability"}

    span_id: Mapped[str] = mapped_column(
        String(16),
        primary_key=True,
        comment="W3C span-id (16 hex chars)",
    )
    trace_id: Mapped[str] = mapped_column(String(32))
    parent_span_id: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="Parent span-id for nested spans",
    )
    timestamp: Mapped[datetime] = mapped_column(
        primary_key=True,
        server_default=func.now(),
    )
    name: Mapped[str] = mapped_column(String(255))
    span_type: Mapped[str] = mapped_column(
        String(50),
        comment="llm, retrieval, generation, embedding, etc.",
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="in_progress",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",  # Column name in DB is 'metadata'
        JSONB,
        nullable=True,
    )


class ObsChatMessage(Base):
    """Chat message log for observability tracking.

    Records all chat interactions with optional feedback data.
    Named ObsChatMessage to avoid conflicts with any existing ChatMessage model.
    Stored in TimescaleDB hypertable with 7-day chunks.

    Attributes:
        id: Unique message identifier
        trace_id: Associated trace for correlation
        timestamp: When the message was sent (hypertable partitioning key)
        user_id: User who sent/received the message
        kb_id: Knowledge base context
        conversation_id: Conversation grouping
        role: Message role (user, assistant, system)
        content: Message content
        input_tokens: Tokens in input (for assistant messages)
        output_tokens: Tokens in output (for assistant messages)
        model: Model used for generation
        latency_ms: Response latency
        feedback_type: User feedback (thumbs_up, thumbs_down)
        feedback_comment: Additional feedback text
        metadata: Additional context as JSONB
    """

    __tablename__ = "chat_messages"
    __table_args__ = {"schema": "observability"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    trace_id: Mapped[str] = mapped_column(String(32))
    timestamp: Mapped[datetime] = mapped_column(
        primary_key=True,
        server_default=func.now(),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    kb_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        comment="user, assistant, system",
    )
    content: Mapped[str] = mapped_column(Text)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="thumbs_up, thumbs_down, null",
    )
    feedback_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",  # Column name in DB is 'metadata'
        JSONB,
        nullable=True,
    )


class DocumentEvent(Base):
    """Document processing event for observability tracking.

    Records document lifecycle events (upload, parse, chunk, embed, index, delete).
    Stored in TimescaleDB hypertable with 1-day chunks.

    Attributes:
        id: Unique event identifier
        trace_id: Associated trace for correlation
        timestamp: When the event occurred (hypertable partitioning key)
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

    __tablename__ = "document_events"
    __table_args__ = {"schema": "observability"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    trace_id: Mapped[str] = mapped_column(String(32))
    timestamp: Mapped[datetime] = mapped_column(
        primary_key=True,
        server_default=func.now(),
    )
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    kb_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(
        String(50),
        comment="upload, parse, chunk, embed, index, delete, etc.",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        comment="started, completed, failed",
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",  # Column name in DB is 'metadata'
        JSONB,
        nullable=True,
    )


class MetricsAggregate(Base):
    """Pre-aggregated metrics for efficient dashboard queries.

    Stores hourly/daily aggregated metrics with statistical summaries.
    Stored in TimescaleDB hypertable with 7-day chunks.

    Attributes:
        id: Unique aggregate identifier
        bucket: Time bucket start (hourly/daily)
        metric_type: Metric name (chat_latency, embedding_throughput, etc.)
        dimensions: Grouping dimensions (kb_id, model, user_id)
        count: Number of observations
        sum_value: Sum of values
        min_value: Minimum value
        max_value: Maximum value
        avg_value: Average value
        p50_value: 50th percentile
        p95_value: 95th percentile
        p99_value: 99th percentile
    """

    __tablename__ = "metrics_aggregates"
    __table_args__ = {"schema": "observability"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    bucket: Mapped[datetime] = mapped_column(
        primary_key=True,
        comment="Time bucket start (hourly/daily)",
    )
    metric_type: Mapped[str] = mapped_column(
        String(50),
        comment="chat_latency, embedding_throughput, etc.",
    )
    dimensions: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="kb_id, model, user_id groupings",
    )
    count: Mapped[int] = mapped_column(BigInteger, server_default="0")
    sum_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    p50_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    p95_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    p99_value: Mapped[float | None] = mapped_column(Float, nullable=True)


class ProviderSyncStatus(Base):
    """Tracks synchronization status with external observability providers.

    Used to track which traces/spans have been synced to LangFuse
    and manage retry logic for failed syncs.

    Attributes:
        id: Unique record identifier
        provider_name: External provider (langfuse)
        entity_type: Type of entity (trace, span, chat_message)
        entity_id: ID of the entity being synced
        last_synced_at: Last successful sync timestamp
        sync_status: Current status (pending, synced, failed)
        error_message: Error details if failed
        retry_count: Number of retry attempts
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "provider_sync_status"
    __table_args__ = {"schema": "observability"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    provider_name: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(100))
    last_synced_at: Mapped[datetime | None] = mapped_column(nullable=True)
    sync_status: Mapped[str] = mapped_column(
        String(20),
        server_default="pending",
        comment="pending, synced, failed",
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
