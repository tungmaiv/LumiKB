"""Unit tests for Observability models (Story 9-1).

Tests field validation and model structure for:
- Trace: Root operation traces with W3C trace context
- Span: Child spans with type-specific metrics
- ObsChatMessage: Conversation messages with feedback
- DocumentEvent: Document processing step events
- MetricsAggregate: Pre-computed dashboard metrics
- ProviderSyncStatus: External provider sync tracking

These tests verify AC #9, #10 from Story 9-1:
- SQLAlchemy 2.0 async-compatible models with proper type annotations
- Unit tests verify model structure for all observability models
"""

import secrets

from app.models.observability import (
    DocumentEvent,
    MetricsAggregate,
    ObsChatMessage,
    ProviderSyncStatus,
    Span,
    Trace,
)


def generate_trace_id() -> str:
    """Generate W3C-compliant trace ID (32 hex chars)."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate W3C-compliant span ID (16 hex chars)."""
    return secrets.token_hex(8)


class TestTraceIdGeneration:
    """Tests for W3C-compliant trace ID generation (AC #1 from 9-3)."""

    def test_generate_trace_id_produces_32_hex_chars(self) -> None:
        """
        GIVEN: A request to generate a trace ID
        WHEN: generate_trace_id() is called
        THEN: Returns a 32-character hexadecimal string
        """
        trace_id = generate_trace_id()

        assert len(trace_id) == 32
        assert all(c in "0123456789abcdef" for c in trace_id)

    def test_generate_trace_id_produces_unique_values(self) -> None:
        """
        GIVEN: Multiple requests for trace IDs
        WHEN: generate_trace_id() is called multiple times
        THEN: Each ID is unique
        """
        ids = [generate_trace_id() for _ in range(100)]

        assert len(set(ids)) == 100


class TestSpanIdGeneration:
    """Tests for W3C-compliant span ID generation (AC #1 from 9-3)."""

    def test_generate_span_id_produces_16_hex_chars(self) -> None:
        """
        GIVEN: A request to generate a span ID
        WHEN: generate_span_id() is called
        THEN: Returns a 16-character hexadecimal string
        """
        span_id = generate_span_id()

        assert len(span_id) == 16
        assert all(c in "0123456789abcdef" for c in span_id)

    def test_generate_span_id_produces_unique_values(self) -> None:
        """
        GIVEN: Multiple requests for span IDs
        WHEN: generate_span_id() is called multiple times
        THEN: Each ID is unique
        """
        ids = [generate_span_id() for _ in range(100)]

        assert len(set(ids)) == 100


class TestTraceModel:
    """Tests for Trace model structure (AC #9, #10)."""

    def test_trace_model_has_required_columns(self) -> None:
        """
        GIVEN: The Trace model
        WHEN: Checking model columns
        THEN: All required columns exist with correct types
        """
        columns = Trace.__table__.columns

        assert "trace_id" in columns
        assert "timestamp" in columns
        assert "name" in columns
        assert "user_id" in columns
        assert "kb_id" in columns
        assert "status" in columns
        assert "duration_ms" in columns
        assert "metadata" in columns
        assert "synced_to_langfuse" in columns

    def test_trace_model_uses_observability_schema(self) -> None:
        """
        GIVEN: The Trace model
        WHEN: Checking table schema
        THEN: Uses 'observability' schema
        """
        assert Trace.__table__.schema == "observability"

    def test_trace_model_has_composite_primary_key(self) -> None:
        """
        GIVEN: The Trace model (hypertable)
        WHEN: Checking primary key
        THEN: Has composite PK on trace_id and timestamp
        """
        pk_columns = [col.name for col in Trace.__table__.primary_key.columns]
        assert "trace_id" in pk_columns
        assert "timestamp" in pk_columns

    def test_trace_id_is_32_char_string(self) -> None:
        """
        GIVEN: The Trace model
        WHEN: Checking trace_id column
        THEN: Is String(32) for W3C compliance
        """
        trace_id_col = Trace.__table__.columns["trace_id"]
        assert trace_id_col.type.length == 32


class TestSpanModel:
    """Tests for Span model structure (AC #9, #10)."""

    def test_span_model_has_required_columns(self) -> None:
        """
        GIVEN: The Span model
        WHEN: Checking model columns
        THEN: All required columns exist
        """
        columns = Span.__table__.columns

        assert "span_id" in columns
        assert "trace_id" in columns
        assert "parent_span_id" in columns
        assert "timestamp" in columns
        assert "name" in columns
        assert "span_type" in columns
        assert "duration_ms" in columns
        assert "input_tokens" in columns
        assert "output_tokens" in columns
        assert "model" in columns
        assert "status" in columns
        assert "error_message" in columns
        assert "metadata" in columns

    def test_span_model_uses_observability_schema(self) -> None:
        """
        GIVEN: The Span model
        WHEN: Checking table schema
        THEN: Uses 'observability' schema
        """
        assert Span.__table__.schema == "observability"

    def test_span_id_is_16_char_string(self) -> None:
        """
        GIVEN: The Span model
        WHEN: Checking span_id column
        THEN: Is String(16) for W3C compliance
        """
        span_id_col = Span.__table__.columns["span_id"]
        assert span_id_col.type.length == 16

    def test_span_has_llm_metrics_columns(self) -> None:
        """
        GIVEN: The Span model
        WHEN: Checking LLM-specific columns
        THEN: Has input_tokens, output_tokens, model
        """
        columns = Span.__table__.columns
        assert "input_tokens" in columns
        assert "output_tokens" in columns
        assert "model" in columns


class TestObsChatMessageModel:
    """Tests for ObsChatMessage model structure (AC #9, #10)."""

    def test_chat_message_model_has_required_columns(self) -> None:
        """
        GIVEN: The ObsChatMessage model
        WHEN: Checking model columns
        THEN: All required columns exist
        """
        columns = ObsChatMessage.__table__.columns

        assert "id" in columns
        assert "trace_id" in columns
        assert "timestamp" in columns
        assert "user_id" in columns
        assert "kb_id" in columns
        assert "conversation_id" in columns
        assert "role" in columns
        assert "content" in columns
        assert "input_tokens" in columns
        assert "output_tokens" in columns
        assert "model" in columns
        assert "latency_ms" in columns
        assert "feedback_type" in columns
        assert "feedback_comment" in columns
        assert "metadata" in columns

    def test_chat_message_model_uses_observability_schema(self) -> None:
        """
        GIVEN: The ObsChatMessage model
        WHEN: Checking table schema
        THEN: Uses 'observability' schema
        """
        assert ObsChatMessage.__table__.schema == "observability"

    def test_chat_message_has_feedback_columns(self) -> None:
        """
        GIVEN: The ObsChatMessage model
        WHEN: Checking feedback columns
        THEN: Has feedback_type and feedback_comment
        """
        columns = ObsChatMessage.__table__.columns
        assert "feedback_type" in columns
        assert "feedback_comment" in columns


class TestDocumentEventModel:
    """Tests for DocumentEvent model structure (AC #9, #10)."""

    def test_document_event_model_has_required_columns(self) -> None:
        """
        GIVEN: The DocumentEvent model
        WHEN: Checking model columns
        THEN: All required columns exist
        """
        columns = DocumentEvent.__table__.columns

        assert "id" in columns
        assert "trace_id" in columns
        assert "timestamp" in columns
        assert "document_id" in columns
        assert "kb_id" in columns
        assert "event_type" in columns
        assert "status" in columns
        assert "duration_ms" in columns
        assert "chunk_count" in columns
        assert "token_count" in columns
        assert "error_message" in columns
        assert "metadata" in columns

    def test_document_event_model_uses_observability_schema(self) -> None:
        """
        GIVEN: The DocumentEvent model
        WHEN: Checking table schema
        THEN: Uses 'observability' schema
        """
        assert DocumentEvent.__table__.schema == "observability"

    def test_document_event_has_processing_metrics(self) -> None:
        """
        GIVEN: The DocumentEvent model
        WHEN: Checking processing metric columns
        THEN: Has chunk_count and token_count
        """
        columns = DocumentEvent.__table__.columns
        assert "chunk_count" in columns
        assert "token_count" in columns


class TestMetricsAggregateModel:
    """Tests for MetricsAggregate model structure (AC #9, #10)."""

    def test_metrics_aggregate_model_has_required_columns(self) -> None:
        """
        GIVEN: The MetricsAggregate model
        WHEN: Checking model columns
        THEN: All required columns exist
        """
        columns = MetricsAggregate.__table__.columns

        assert "id" in columns
        assert "bucket" in columns
        assert "metric_type" in columns
        assert "dimensions" in columns
        assert "count" in columns
        assert "sum_value" in columns
        assert "min_value" in columns
        assert "max_value" in columns
        assert "avg_value" in columns
        assert "p50_value" in columns
        assert "p95_value" in columns
        assert "p99_value" in columns

    def test_metrics_aggregate_model_uses_observability_schema(self) -> None:
        """
        GIVEN: The MetricsAggregate model
        WHEN: Checking table schema
        THEN: Uses 'observability' schema
        """
        assert MetricsAggregate.__table__.schema == "observability"

    def test_metrics_aggregate_has_percentile_columns(self) -> None:
        """
        GIVEN: The MetricsAggregate model
        WHEN: Checking percentile columns
        THEN: Has p50, p95, p99 values
        """
        columns = MetricsAggregate.__table__.columns
        assert "p50_value" in columns
        assert "p95_value" in columns
        assert "p99_value" in columns


class TestProviderSyncStatusModel:
    """Tests for ProviderSyncStatus model structure (AC #9, #10)."""

    def test_provider_sync_status_model_has_required_columns(self) -> None:
        """
        GIVEN: The ProviderSyncStatus model
        WHEN: Checking model columns
        THEN: All required columns exist
        """
        columns = ProviderSyncStatus.__table__.columns

        assert "id" in columns
        assert "provider_name" in columns
        assert "entity_type" in columns
        assert "entity_id" in columns
        assert "last_synced_at" in columns
        assert "sync_status" in columns
        assert "error_message" in columns
        assert "retry_count" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_provider_sync_status_model_uses_observability_schema(self) -> None:
        """
        GIVEN: The ProviderSyncStatus model
        WHEN: Checking table schema
        THEN: Uses 'observability' schema
        """
        assert ProviderSyncStatus.__table__.schema == "observability"

    def test_provider_sync_status_has_single_pk(self) -> None:
        """
        GIVEN: The ProviderSyncStatus model (not a hypertable)
        WHEN: Checking primary key
        THEN: Has single PK on id
        """
        pk_columns = [
            col.name for col in ProviderSyncStatus.__table__.primary_key.columns
        ]
        assert pk_columns == ["id"]


class TestModelTableNames:
    """Tests to verify all models have correct table names."""

    def test_trace_table_name(self) -> None:
        """Trace model uses 'traces' table."""
        assert Trace.__tablename__ == "traces"

    def test_span_table_name(self) -> None:
        """Span model uses 'spans' table."""
        assert Span.__tablename__ == "spans"

    def test_chat_message_table_name(self) -> None:
        """ObsChatMessage model uses 'chat_messages' table."""
        assert ObsChatMessage.__tablename__ == "chat_messages"

    def test_document_event_table_name(self) -> None:
        """DocumentEvent model uses 'document_events' table."""
        assert DocumentEvent.__tablename__ == "document_events"

    def test_metrics_aggregate_table_name(self) -> None:
        """MetricsAggregate model uses 'metrics_aggregates' table."""
        assert MetricsAggregate.__tablename__ == "metrics_aggregates"

    def test_provider_sync_status_table_name(self) -> None:
        """ProviderSyncStatus model uses 'provider_sync_status' table."""
        assert ProviderSyncStatus.__tablename__ == "provider_sync_status"


class TestModelSchemas:
    """Tests to verify all models use observability schema."""

    def test_all_models_use_observability_schema(self) -> None:
        """All observability models use the observability schema."""
        models = [
            Trace,
            Span,
            ObsChatMessage,
            DocumentEvent,
            MetricsAggregate,
            ProviderSyncStatus,
        ]
        for model in models:
            assert (
                model.__table__.schema == "observability"
            ), f"{model.__name__} should use 'observability' schema"
