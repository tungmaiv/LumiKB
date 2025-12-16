"""Test data factories for observability models (Epic 9).

Provides parallel-safe, unique test data for:
- Trace: Root operation traces
- Span: Child spans within traces
- ChatMessage: Conversation messages
- DocumentEvent: Document processing events
- MetricsAggregate: Pre-computed metrics
- ProviderSyncStatus: External provider sync state

Usage:
    from tests.factories import create_trace, create_span

    # Default trace
    trace = create_trace()

    # Trace with specific user
    trace = create_trace(user_id=user.id)

    # Span with LLM metrics
    span = create_span(
        trace_id=trace.trace_id,
        span_type="llm",
        model="gpt-4",
        prompt_tokens=100,
    )
"""

import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from faker import Faker

fake = Faker()


def generate_trace_id() -> str:
    """Generate W3C-compliant trace ID (32 hex chars)."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate W3C-compliant span ID (16 hex chars)."""
    return secrets.token_hex(8)


def create_trace(
    *,
    id: UUID | None = None,
    trace_id: str | None = None,
    name: str | None = None,
    operation_type: str | None = None,
    user_id: UUID | None = None,
    session_id: str | None = None,
    kb_id: UUID | None = None,
    status: str = "running",
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    duration_ms: int | None = None,
    total_tokens: int | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_cost_usd: Decimal | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create trace test data.

    Args:
        id: Database UUID (auto-generated if None)
        trace_id: W3C trace ID (32 hex, auto-generated if None)
        name: Operation name (e.g., "chat.conversation")
        operation_type: Type of operation (chat, search, generation, document)
        user_id: Associated user UUID
        session_id: Session identifier
        kb_id: Knowledge base UUID
        status: Trace status (running, success, error)
        started_at: Trace start time
        ended_at: Trace end time
        duration_ms: Total duration in milliseconds
        total_tokens: Aggregated token count
        prompt_tokens: Prompt tokens used
        completion_tokens: Completion tokens generated
        total_cost_usd: Total LLM cost
        error_type: Error classification
        error_message: Error details
        metadata: Additional context

    Returns:
        Dictionary of trace fields
    """
    return {
        "id": id or uuid4(),
        "trace_id": trace_id or generate_trace_id(),
        "name": name or fake.sentence(nb_words=3),
        "operation_type": operation_type
        or fake.random_element(["chat", "search", "generation", "document"]),
        "user_id": user_id or uuid4(),
        "session_id": session_id or str(uuid4()),
        "kb_id": kb_id,
        "status": status,
        "started_at": started_at or datetime.utcnow(),
        "ended_at": ended_at,
        "duration_ms": duration_ms,
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_cost_usd": total_cost_usd,
        "error_type": error_type,
        "error_message": error_message,
        "metadata": metadata or {},
    }


def create_span(
    *,
    id: UUID | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    parent_span_id: str | None = None,
    name: str | None = None,
    span_type: str | None = None,
    status: str = "running",
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    duration_ms: int | None = None,
    # LLM-specific fields
    model: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    cost_usd: Decimal | None = None,
    temperature: float | None = None,
    input_preview: str | None = None,
    output_preview: str | None = None,
    # Embedding-specific fields
    embedding_model: str | None = None,
    embedding_tokens: int | None = None,
    embedding_dimensions: int | None = None,
    # Retrieval-specific fields
    query: str | None = None,
    results_count: int | None = None,
    top_score: float | None = None,
    # Parse-specific fields
    file_type: str | None = None,
    file_size_bytes: int | None = None,
    pages_count: int | None = None,
    # Chunk-specific fields
    chunks_count: int | None = None,
    avg_chunk_size: int | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create span test data.

    Args:
        id: Database UUID
        trace_id: Parent trace ID (32 hex)
        span_id: This span's ID (16 hex)
        parent_span_id: Parent span ID for nesting
        name: Span name
        span_type: Type (llm, embedding, retrieval, parse, chunk, index)
        status: Span status
        started_at: Span start time
        ended_at: Span end time
        duration_ms: Duration in milliseconds
        model: LLM model name
        prompt_tokens: LLM prompt tokens
        completion_tokens: LLM completion tokens
        cost_usd: LLM cost
        temperature: LLM temperature
        input_preview: Truncated input
        output_preview: Truncated output
        embedding_model: Embedding model name
        embedding_tokens: Tokens for embedding
        embedding_dimensions: Vector dimensions
        query: Search query
        results_count: Number of results
        top_score: Best similarity score
        file_type: Document type
        file_size_bytes: File size
        pages_count: Number of pages
        chunks_count: Number of chunks
        avg_chunk_size: Average chunk size
        error_type: Error classification
        error_message: Error details
        metadata: Additional context

    Returns:
        Dictionary of span fields
    """
    return {
        "id": id or uuid4(),
        "trace_id": trace_id or generate_trace_id(),
        "span_id": span_id or generate_span_id(),
        "parent_span_id": parent_span_id,
        "name": name or fake.sentence(nb_words=2),
        "span_type": span_type
        or fake.random_element(
            ["llm", "embedding", "retrieval", "parse", "chunk", "index"]
        ),
        "status": status,
        "started_at": started_at or datetime.utcnow(),
        "ended_at": ended_at,
        "duration_ms": duration_ms,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost_usd,
        "temperature": temperature,
        "input_preview": input_preview,
        "output_preview": output_preview,
        "embedding_model": embedding_model,
        "embedding_tokens": embedding_tokens,
        "embedding_dimensions": embedding_dimensions,
        "query": query,
        "results_count": results_count,
        "top_score": top_score,
        "file_type": file_type,
        "file_size_bytes": file_size_bytes,
        "pages_count": pages_count,
        "chunks_count": chunks_count,
        "avg_chunk_size": avg_chunk_size,
        "error_type": error_type,
        "error_message": error_message,
        "metadata": metadata or {},
    }


def create_chat_message(
    *,
    id: UUID | None = None,
    trace_id: str | None = None,
    user_id: UUID | None = None,
    session_id: str | None = None,
    kb_id: UUID | None = None,
    role: str | None = None,
    content: str | None = None,
    turn_number: int | None = None,
    sources: list[dict[str, Any]] | None = None,
    citations: list[dict[str, Any]] | None = None,
    tokens: int | None = None,
    latency_ms: int | None = None,
    model: str | None = None,
    created_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create chat message test data.

    Args:
        id: Database UUID
        trace_id: Associated trace ID
        user_id: User UUID
        session_id: Session identifier
        kb_id: Knowledge base UUID
        role: Message role (user, assistant, system)
        content: Message content
        turn_number: Conversation turn number
        sources: Retrieved document sources
        citations: Inline citations
        tokens: Token count
        latency_ms: Response latency
        model: Model used
        created_at: Message timestamp
        metadata: Additional context

    Returns:
        Dictionary of chat message fields
    """
    return {
        "id": id or uuid4(),
        "trace_id": trace_id or generate_trace_id(),
        "user_id": user_id or uuid4(),
        "session_id": session_id or str(uuid4()),
        "kb_id": kb_id,
        "role": role or fake.random_element(["user", "assistant"]),
        "content": content or fake.paragraph(),
        "turn_number": turn_number or fake.random_int(min=1, max=20),
        "sources": sources,
        "citations": citations,
        "tokens": tokens or fake.random_int(min=10, max=500),
        "latency_ms": latency_ms,
        "model": model,
        "created_at": created_at or datetime.utcnow(),
        "metadata": metadata or {},
    }


def create_document_event(
    *,
    id: UUID | None = None,
    trace_id: str | None = None,
    document_id: UUID | None = None,
    kb_id: UUID | None = None,
    event_type: str | None = None,
    status: str = "running",
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    duration_ms: int | None = None,
    # Step-specific metrics
    file_size_bytes: int | None = None,
    pages_count: int | None = None,
    chunks_count: int | None = None,
    tokens_count: int | None = None,
    vectors_count: int | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create document event test data.

    Args:
        id: Database UUID
        trace_id: Associated trace ID
        document_id: Document UUID
        kb_id: Knowledge base UUID
        event_type: Event type (upload, parse, chunk, embed, index)
        status: Event status
        started_at: Event start time
        ended_at: Event end time
        duration_ms: Duration in milliseconds
        file_size_bytes: File size
        pages_count: Number of pages parsed
        chunks_count: Number of chunks created
        tokens_count: Tokens processed
        vectors_count: Vectors indexed
        error_type: Error classification
        error_message: Error details
        metadata: Additional context

    Returns:
        Dictionary of document event fields
    """
    return {
        "id": id or uuid4(),
        "trace_id": trace_id or generate_trace_id(),
        "document_id": document_id or uuid4(),
        "kb_id": kb_id or uuid4(),
        "event_type": event_type
        or fake.random_element(["upload", "parse", "chunk", "embed", "index"]),
        "status": status,
        "started_at": started_at or datetime.utcnow(),
        "ended_at": ended_at,
        "duration_ms": duration_ms,
        "file_size_bytes": file_size_bytes,
        "pages_count": pages_count,
        "chunks_count": chunks_count,
        "tokens_count": tokens_count,
        "vectors_count": vectors_count,
        "error_type": error_type,
        "error_message": error_message,
        "metadata": metadata or {},
    }


def create_metrics_aggregate(
    *,
    id: UUID | None = None,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    granularity: str | None = None,
    metric_type: str | None = None,
    dimension_type: str | None = None,
    dimension_value: str | None = None,
    count: int | None = None,
    sum_value: float | None = None,
    avg_value: float | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    p50_value: float | None = None,
    p95_value: float | None = None,
    p99_value: float | None = None,
) -> dict[str, Any]:
    """Create metrics aggregate test data.

    Args:
        id: Database UUID
        period_start: Aggregation period start
        period_end: Aggregation period end
        granularity: Time granularity (hour, day, week)
        metric_type: Metric being aggregated (latency, tokens, cost)
        dimension_type: Dimension for grouping (user, kb, model)
        dimension_value: Dimension value
        count: Number of samples
        sum_value: Sum of values
        avg_value: Average value
        min_value: Minimum value
        max_value: Maximum value
        p50_value: 50th percentile
        p95_value: 95th percentile
        p99_value: 99th percentile

    Returns:
        Dictionary of metrics aggregate fields
    """
    now = datetime.utcnow()
    return {
        "id": id or uuid4(),
        "period_start": period_start or now.replace(minute=0, second=0, microsecond=0),
        "period_end": period_end
        or (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)),
        "granularity": granularity or "hour",
        "metric_type": metric_type
        or fake.random_element(["latency_ms", "tokens", "cost_usd"]),
        "dimension_type": dimension_type
        or fake.random_element(["user", "kb", "model", "operation"]),
        "dimension_value": dimension_value or str(uuid4()),
        "count": count or fake.random_int(min=1, max=1000),
        "sum_value": sum_value,
        "avg_value": avg_value,
        "min_value": min_value,
        "max_value": max_value,
        "p50_value": p50_value,
        "p95_value": p95_value,
        "p99_value": p99_value,
    }


def create_provider_sync_status(
    *,
    id: UUID | None = None,
    provider_name: str | None = None,
    last_synced_at: datetime | None = None,
    last_synced_trace_id: str | None = None,
    sync_status: str = "idle",
    error_count: int = 0,
    last_error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create provider sync status test data.

    Args:
        id: Database UUID
        provider_name: External provider name (langfuse)
        last_synced_at: Last successful sync time
        last_synced_trace_id: Last synced trace ID
        sync_status: Sync status (idle, syncing, error)
        error_count: Consecutive error count
        last_error: Last error message
        metadata: Additional context

    Returns:
        Dictionary of provider sync status fields
    """
    return {
        "id": id or uuid4(),
        "provider_name": provider_name or "langfuse",
        "last_synced_at": last_synced_at,
        "last_synced_trace_id": last_synced_trace_id,
        "sync_status": sync_status,
        "error_count": error_count,
        "last_error": last_error,
        "metadata": metadata or {},
    }


# Convenience functions for common test scenarios


def create_completed_trace(**overrides: Any) -> dict[str, Any]:
    """Create a completed trace with timing."""
    started = datetime.utcnow() - timedelta(seconds=5)
    ended = datetime.utcnow()
    defaults = {
        "status": "success",
        "started_at": started,
        "ended_at": ended,
        "duration_ms": int((ended - started).total_seconds() * 1000),
    }
    defaults.update(overrides)
    return create_trace(**defaults)


def create_failed_trace(
    error_type: str = "ValueError", error_message: str = "Test error", **overrides: Any
) -> dict[str, Any]:
    """Create a failed trace with error details."""
    defaults = {
        "status": "error",
        "error_type": error_type,
        "error_message": error_message,
    }
    defaults.update(overrides)
    return create_completed_trace(**defaults)


def create_llm_span(
    *,
    model: str = "gpt-4",
    prompt_tokens: int = 100,
    completion_tokens: int = 50,
    cost_usd: Decimal | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Create an LLM-type span with typical metrics."""
    defaults = {
        "span_type": "llm",
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost_usd or Decimal("0.0045"),
        "temperature": 0.7,
    }
    defaults.update(overrides)
    return create_span(**defaults)


def create_retrieval_span(
    *,
    query: str | None = None,
    results_count: int = 5,
    top_score: float = 0.95,
    **overrides: Any,
) -> dict[str, Any]:
    """Create a retrieval-type span with search metrics."""
    defaults = {
        "span_type": "retrieval",
        "query": query or fake.sentence(),
        "results_count": results_count,
        "top_score": top_score,
    }
    defaults.update(overrides)
    return create_span(**defaults)
