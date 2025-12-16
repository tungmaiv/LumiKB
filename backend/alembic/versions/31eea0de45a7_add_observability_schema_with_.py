"""add_observability_schema_with_timescaledb

Revision ID: 31eea0de45a7
Revises: 3c33e68b67e1
Create Date: 2025-12-15 09:10:30.864026

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "31eea0de45a7"
down_revision: Union[str, Sequence[str], None] = "3c33e68b67e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create observability schema with optional TimescaleDB hypertables.

    This migration:
    1. Attempts to enable TimescaleDB extension (optional)
    2. Creates observability schema
    3. Creates traces, spans, chat_messages, document_events tables
    4. Converts tables to hypertables if TimescaleDB is available
    5. Creates metrics_aggregates and provider_sync_status tables
    6. Creates all required indexes for efficient querying
    """
    # 1. Check if TimescaleDB is available by querying pg_available_extensions
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb' LIMIT 1"
        )
    )
    timescaledb_available = result.fetchone() is not None

    # Try to enable TimescaleDB if available
    if timescaledb_available:
        try:
            conn.execute(
                sa.text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
            )
        except Exception:
            timescaledb_available = False

    # 2. Create observability schema
    op.execute("CREATE SCHEMA IF NOT EXISTS observability")

    # 3. Create traces table (hypertable with 1-day chunks)
    op.create_table(
        "traces",
        sa.Column(
            "trace_id",
            sa.String(32),
            nullable=False,
            comment="W3C trace-id (32 hex chars)",
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="in_progress",
        ),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "synced_to_langfuse",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.PrimaryKeyConstraint("trace_id", "timestamp"),
        schema="observability",
    )

    # Convert traces to hypertable if TimescaleDB is available
    if timescaledb_available:
        op.execute(
            """
            SELECT create_hypertable(
                'observability.traces',
                'timestamp',
                chunk_time_interval => INTERVAL '1 day',
                if_not_exists => TRUE
            )
            """
        )

    # 4. Create spans table (hypertable with 1-day chunks)
    op.create_table(
        "spans",
        sa.Column(
            "span_id",
            sa.String(16),
            nullable=False,
            comment="W3C span-id (16 hex chars)",
        ),
        sa.Column("trace_id", sa.String(32), nullable=False),
        sa.Column(
            "parent_span_id",
            sa.String(16),
            nullable=True,
            comment="Parent span-id for nested spans",
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "span_type",
            sa.String(50),
            nullable=False,
            comment="llm, retrieval, generation, embedding, etc.",
        ),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="in_progress",
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("span_id", "timestamp"),
        schema="observability",
    )

    # Convert spans to hypertable if TimescaleDB is available
    if timescaledb_available:
        op.execute(
            """
            SELECT create_hypertable(
                'observability.spans',
                'timestamp',
                chunk_time_interval => INTERVAL '1 day',
                if_not_exists => TRUE
            )
            """
        )

    # 5. Create chat_messages table (hypertable with 7-day chunks)
    op.create_table(
        "chat_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("trace_id", sa.String(32), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            comment="user, assistant, system",
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column(
            "feedback_type",
            sa.String(20),
            nullable=True,
            comment="thumbs_up, thumbs_down, null",
        ),
        sa.Column("feedback_comment", sa.Text, nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", "timestamp"),
        schema="observability",
    )

    # Convert chat_messages to hypertable if TimescaleDB is available
    if timescaledb_available:
        op.execute(
            """
            SELECT create_hypertable(
                'observability.chat_messages',
                'timestamp',
                chunk_time_interval => INTERVAL '7 days',
                if_not_exists => TRUE
            )
            """
        )

    # 6. Create document_events table (hypertable with 1-day chunks)
    op.create_table(
        "document_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("trace_id", sa.String(32), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kb_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "event_type",
            sa.String(50),
            nullable=False,
            comment="upload, parse, chunk, embed, index, delete, etc.",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            comment="started, completed, failed",
        ),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("chunk_count", sa.Integer, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", "timestamp"),
        schema="observability",
    )

    # Convert document_events to hypertable if TimescaleDB is available
    if timescaledb_available:
        op.execute(
            """
            SELECT create_hypertable(
                'observability.document_events',
                'timestamp',
                chunk_time_interval => INTERVAL '1 day',
                if_not_exists => TRUE
            )
            """
        )

    # 7. Create metrics_aggregates table (hypertable with 7-day chunks)
    op.create_table(
        "metrics_aggregates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "bucket",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Time bucket start (hourly/daily)",
        ),
        sa.Column(
            "metric_type",
            sa.String(50),
            nullable=False,
            comment="chat_latency, embedding_throughput, etc.",
        ),
        sa.Column(
            "dimensions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="kb_id, model, user_id groupings",
        ),
        sa.Column("count", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("sum_value", sa.Float, nullable=True),
        sa.Column("min_value", sa.Float, nullable=True),
        sa.Column("max_value", sa.Float, nullable=True),
        sa.Column("avg_value", sa.Float, nullable=True),
        sa.Column("p50_value", sa.Float, nullable=True),
        sa.Column("p95_value", sa.Float, nullable=True),
        sa.Column("p99_value", sa.Float, nullable=True),
        sa.PrimaryKeyConstraint("id", "bucket"),
        schema="observability",
    )

    # Convert metrics_aggregates to hypertable if TimescaleDB is available
    if timescaledb_available:
        op.execute(
            """
            SELECT create_hypertable(
                'observability.metrics_aggregates',
                'bucket',
                chunk_time_interval => INTERVAL '7 days',
                if_not_exists => TRUE
            )
            """
        )

    # 8. Create provider_sync_status table (regular table, not hypertable)
    op.create_table(
        "provider_sync_status",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("provider_name", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column(
            "last_synced_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "sync_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            comment="pending, synced, failed",
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider_name",
            "entity_type",
            "entity_id",
            name="uq_provider_entity",
        ),
        schema="observability",
    )

    # 9. Create indexes for efficient querying

    # Traces indexes
    op.create_index(
        "idx_traces_user_id",
        "traces",
        ["user_id"],
        schema="observability",
    )
    op.create_index(
        "idx_traces_kb_id",
        "traces",
        ["kb_id"],
        schema="observability",
    )
    op.create_index(
        "idx_traces_status",
        "traces",
        ["status"],
        schema="observability",
    )
    op.create_index(
        "idx_traces_synced",
        "traces",
        ["synced_to_langfuse"],
        schema="observability",
        postgresql_where=sa.text("synced_to_langfuse = false"),
    )

    # Spans indexes
    op.create_index(
        "idx_spans_trace_id",
        "spans",
        ["trace_id"],
        schema="observability",
    )
    op.create_index(
        "idx_spans_type",
        "spans",
        ["span_type"],
        schema="observability",
    )
    op.create_index(
        "idx_spans_model",
        "spans",
        ["model"],
        schema="observability",
    )

    # Chat messages indexes
    op.create_index(
        "idx_chat_trace_id",
        "chat_messages",
        ["trace_id"],
        schema="observability",
    )
    op.create_index(
        "idx_chat_user_id",
        "chat_messages",
        ["user_id"],
        schema="observability",
    )
    op.create_index(
        "idx_chat_kb_id",
        "chat_messages",
        ["kb_id"],
        schema="observability",
    )
    op.create_index(
        "idx_chat_conversation_id",
        "chat_messages",
        ["conversation_id"],
        schema="observability",
    )
    op.create_index(
        "idx_chat_feedback",
        "chat_messages",
        ["feedback_type"],
        schema="observability",
        postgresql_where=sa.text("feedback_type IS NOT NULL"),
    )

    # Document events indexes
    op.create_index(
        "idx_doc_events_trace_id",
        "document_events",
        ["trace_id"],
        schema="observability",
    )
    op.create_index(
        "idx_doc_events_document_id",
        "document_events",
        ["document_id"],
        schema="observability",
    )
    op.create_index(
        "idx_doc_events_kb_id",
        "document_events",
        ["kb_id"],
        schema="observability",
    )
    op.create_index(
        "idx_doc_events_type",
        "document_events",
        ["event_type"],
        schema="observability",
    )

    # Metrics aggregates indexes
    op.create_index(
        "idx_metrics_type",
        "metrics_aggregates",
        ["metric_type"],
        schema="observability",
    )
    op.create_index(
        "idx_metrics_dimensions",
        "metrics_aggregates",
        ["dimensions"],
        schema="observability",
        postgresql_using="gin",
    )

    # Provider sync status indexes
    op.create_index(
        "idx_sync_provider",
        "provider_sync_status",
        ["provider_name"],
        schema="observability",
    )
    op.create_index(
        "idx_sync_status",
        "provider_sync_status",
        ["sync_status"],
        schema="observability",
    )
    op.create_index(
        "idx_sync_pending",
        "provider_sync_status",
        ["sync_status", "retry_count"],
        schema="observability",
        postgresql_where=sa.text("sync_status = 'pending' OR sync_status = 'failed'"),
    )


def downgrade() -> None:
    """Drop observability schema and all tables."""
    # Drop indexes (indexes are automatically dropped with tables, but being explicit)

    # Drop provider_sync_status indexes
    op.drop_index(
        "idx_sync_pending",
        table_name="provider_sync_status",
        schema="observability",
    )
    op.drop_index(
        "idx_sync_status",
        table_name="provider_sync_status",
        schema="observability",
    )
    op.drop_index(
        "idx_sync_provider",
        table_name="provider_sync_status",
        schema="observability",
    )

    # Drop metrics_aggregates indexes
    op.drop_index(
        "idx_metrics_dimensions",
        table_name="metrics_aggregates",
        schema="observability",
    )
    op.drop_index(
        "idx_metrics_type",
        table_name="metrics_aggregates",
        schema="observability",
    )

    # Drop document_events indexes
    op.drop_index(
        "idx_doc_events_type",
        table_name="document_events",
        schema="observability",
    )
    op.drop_index(
        "idx_doc_events_kb_id",
        table_name="document_events",
        schema="observability",
    )
    op.drop_index(
        "idx_doc_events_document_id",
        table_name="document_events",
        schema="observability",
    )
    op.drop_index(
        "idx_doc_events_trace_id",
        table_name="document_events",
        schema="observability",
    )

    # Drop chat_messages indexes
    op.drop_index(
        "idx_chat_feedback",
        table_name="chat_messages",
        schema="observability",
    )
    op.drop_index(
        "idx_chat_conversation_id",
        table_name="chat_messages",
        schema="observability",
    )
    op.drop_index(
        "idx_chat_kb_id",
        table_name="chat_messages",
        schema="observability",
    )
    op.drop_index(
        "idx_chat_user_id",
        table_name="chat_messages",
        schema="observability",
    )
    op.drop_index(
        "idx_chat_trace_id",
        table_name="chat_messages",
        schema="observability",
    )

    # Drop spans indexes
    op.drop_index(
        "idx_spans_model",
        table_name="spans",
        schema="observability",
    )
    op.drop_index(
        "idx_spans_type",
        table_name="spans",
        schema="observability",
    )
    op.drop_index(
        "idx_spans_trace_id",
        table_name="spans",
        schema="observability",
    )

    # Drop traces indexes
    op.drop_index(
        "idx_traces_synced",
        table_name="traces",
        schema="observability",
    )
    op.drop_index(
        "idx_traces_status",
        table_name="traces",
        schema="observability",
    )
    op.drop_index(
        "idx_traces_kb_id",
        table_name="traces",
        schema="observability",
    )
    op.drop_index(
        "idx_traces_user_id",
        table_name="traces",
        schema="observability",
    )

    # Drop tables (hypertables are dropped like regular tables)
    op.drop_table("provider_sync_status", schema="observability")
    op.drop_table("metrics_aggregates", schema="observability")
    op.drop_table("document_events", schema="observability")
    op.drop_table("chat_messages", schema="observability")
    op.drop_table("spans", schema="observability")
    op.drop_table("traces", schema="observability")

    # Drop observability schema
    op.execute("DROP SCHEMA IF EXISTS observability CASCADE")

    # Note: We don't drop the TimescaleDB extension as it may be used by other schemas
