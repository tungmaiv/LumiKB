# Epic 9: Hybrid Observability Platform - Technical Specification

**Version:** 1.0
**Date:** 2025-12-14
**Author:** Architecture Team (Winston, Bob, Murat)
**Status:** Draft - Pending Review

---

## Executive Summary

This technical specification defines the architecture, design, and implementation plan for a **Hybrid Observability Platform** in LumiKB. The platform provides comprehensive visibility into document processing pipelines, chat/RAG operations, and LLM interactions through:

1. **Internal PostgreSQL Storage** - Always-on, self-contained observability with TimescaleDB optimization
2. **Optional LangFuse Provider** - External integration for advanced LLM analytics when needed
3. **Provider Registry Pattern** - Extensible architecture supporting future providers (LangSmith, Phoenix, etc.)

---

## 1. Scope

### 1.1 In Scope

| Area | Description |
|------|-------------|
| **Distributed Tracing** | W3C Trace Context propagation across all LumiKB services |
| **Document Processing Observability** | Step-by-step event tracking for upload, parse, chunk, embed, index |
| **Chat/RAG Observability** | Conversation history persistence, retrieval tracking, response timing |
| **LLM Call Tracking** | Token usage, latency, cost tracking for all LLM invocations |
| **Admin Observability API** | REST endpoints for querying traces, chat history, document timelines |
| **Admin Observability UI** | Trace viewer, chat browser, document timeline, dashboard widgets |
| **PostgreSQL Provider** | Always-on internal storage with TimescaleDB time-series optimization |
| **LangFuse Provider** | Optional external integration for advanced LLM analytics |
| **Metrics Aggregation** | Pre-computed hourly/daily metrics for dashboard performance |
| **Data Retention** | Configurable retention policies with automatic cleanup |

### 1.2 Out of Scope

| Area | Rationale |
|------|-----------|
| **APM Tool Replacement** | Not replacing Datadog/New Relic - focused on LLM & document observability only |
| **Infrastructure Monitoring** | CPU/memory/disk metrics handled by existing Prometheus stack |
| **Log Aggregation** | Not a centralized logging solution - existing structlog + ELK integration remains |
| **Real-time Alerting** | Alerting rules remain in Prometheus/Grafana - observability provides data source |
| **User-facing Analytics** | This is admin-only; end-user analytics would be a separate epic |
| **Cross-tenant Observability** | Single-tenant design - multi-tenant isolation not addressed |
| **OpenTelemetry Collector** | Direct provider writes, not OTEL collector deployment |
| **Custom Dashboarding Tools** | Uses existing admin dashboard framework, not Grafana/Kibana |

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LumiKB Application                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Chat API   │  │ Document    │  │  Search     │  │ Generation  │        │
│  │             │  │ Processing  │  │  Service    │  │  Service    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│         └────────────────┴────────────────┴────────────────┘               │
│                                   │                                         │
│                    ┌──────────────▼──────────────┐                         │
│                    │    ObservabilityService     │                         │
│                    │  ┌───────────────────────┐  │                         │
│                    │  │    TraceContext       │  │                         │
│                    │  │  (OpenTelemetry)      │  │                         │
│                    │  └───────────────────────┘  │                         │
│                    │  ┌───────────────────────┐  │                         │
│                    │  │   Provider Registry   │  │                         │
│                    │  └───────────────────────┘  │                         │
│                    └──────────────┬──────────────┘                         │
│                                   │                                         │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│  PostgreSQL       │   │  LangFuse         │   │  Future           │
│  Provider         │   │  Provider         │   │  Providers        │
│  (Always Active)  │   │  (Optional)       │   │  (LangSmith, etc) │
└─────────┬─────────┘   └─────────┬─────────┘   └───────────────────┘
          │                       │
          ▼                       ▼
┌───────────────────┐   ┌───────────────────┐
│  PostgreSQL       │   │  LangFuse Cloud   │
│  + TimescaleDB    │   │  or Self-Hosted   │
│  (observability   │   │                   │
│   schema)         │   │                   │
└───────────────────┘   └───────────────────┘
          │
          ▼
┌───────────────────┐
│  Admin Dashboard  │
│  (React/Next.js)  │
└───────────────────┘
```

### 2.2 Design Principles

1. **Fire-and-Forget**: Observability never blocks application flow
2. **Fail-Safe**: Provider failures are logged but don't impact operations
3. **Schema Separation**: Dedicated `observability` schema like existing `audit` schema
4. **Dual Write**: Internal storage always active; external providers optional
5. **OpenTelemetry Native**: W3C Trace Context for distributed tracing
6. **Token-First**: Token/cost tracking in core schema, not optional metadata

### 2.3 Integration with Existing Systems

| Existing System | Integration Approach |
|-----------------|---------------------|
| AuditService | Coexist - Audit for compliance, Observability for operations |
| SearchAuditService | Migrate to ObservabilityService for unified tracing |
| Document processing_steps | Enhance with trace context, migrate to unified events |
| Celery tasks | Instrument with trace propagation |
| LiteLLM client | Add callback hooks for LLM call tracking |
| Redis sessions | Add session_id to trace context |

---

## 3. Non-Functional Requirements

### 3.1 Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Trace/Span Write Latency** | < 5ms p99 | Fire-and-forget must not impact request latency |
| **Dashboard Query Latency** | < 500ms p95 | Admin experience for trace list/detail views |
| **Concurrent Traces** | 1,000+ active traces | Peak load during batch document processing |
| **Write Throughput** | 10,000 events/minute | Support high-volume document processing |
| **Storage Efficiency** | < 1KB per span average | TimescaleDB compression after 7 days |

### 3.2 Reliability & Availability

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| **Observability Failure Isolation** | 100% | Provider failures never impact business operations |
| **Data Durability** | 99.9% | PostgreSQL with WAL, no async buffering |
| **Provider Recovery** | Automatic | Retry queue for failed external provider writes |
| **Graceful Degradation** | Required | LangFuse unavailable → PostgreSQL-only mode |

### 3.3 Security & Compliance

| Aspect | Requirement | Implementation |
|--------|-------------|----------------|
| **Access Control** | Admin-only | All observability endpoints require `require_admin` |
| **Data Classification** | Internal/Confidential | Chat content may contain user PII |
| **PII in Chat Messages** | Retention-aware | See Section 3.4 for handling policy |
| **Encryption at Rest** | Database-level | PostgreSQL TDE or volume encryption |
| **Encryption in Transit** | TLS 1.3 | All API endpoints over HTTPS |
| **Audit Trail** | Immutable | Observability data append-only (no deletes except retention) |

### 3.4 PII Handling Policy

The `chat_messages.content` field stores raw user input which may contain personally identifiable information (PII). The following policies apply:

| Policy | Implementation |
|--------|----------------|
| **Retention Period** | Configurable via `OBSERVABILITY_RETENTION_DAYS` (default: 90 days) |
| **Automatic Deletion** | TimescaleDB `drop_chunks()` removes data older than retention period |
| **No Manual Deletion** | Individual message deletion not supported (audit integrity) |
| **Content Masking** | Optional `input_preview`/`output_preview` fields truncated to 500 chars |
| **GDPR Right to Erasure** | Covered by retention policy; no individual record deletion API |
| **Access Logging** | All chat history queries logged via existing AuditService |
| **Export Restrictions** | Chat export requires admin + explicit user consent workflow |

**Future Enhancement:** Consider field-level encryption for `chat_messages.content` using application-managed keys (Story 9-15 candidate).

### 3.5 Scalability Projections

| Metric | Baseline (Month 1) | Growth (Month 6) | Design Capacity |
|--------|-------------------|------------------|-----------------|
| **Traces/Day** | 1,000 | 10,000 | 100,000 |
| **Spans/Day** | 5,000 | 50,000 | 500,000 |
| **Chat Messages/Day** | 500 | 5,000 | 50,000 |
| **Storage Growth/Month** | 500 MB | 5 GB | 50 GB |
| **Query Performance** | < 100ms | < 200ms | < 500ms |

**Mitigation:** TimescaleDB compression (7-day policy) reduces storage by ~80%. Continuous aggregates for dashboard metrics.

---

## 4. Data Model

### 4.1 PostgreSQL Schema (observability)

```sql
-- Enable TimescaleDB extension for time-series optimization
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create observability schema
CREATE SCHEMA IF NOT EXISTS observability;

-- ═══════════════════════════════════════════════════════════════════════════
-- TRACES TABLE - Root spans for distributed operations
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE observability.traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- W3C Trace Context
    trace_id VARCHAR(32) NOT NULL,           -- 16-byte hex string

    -- Operation context
    name VARCHAR(100) NOT NULL,               -- "chat.conversation", "document.process"
    operation_type VARCHAR(50) NOT NULL,      -- "chat", "document", "search", "generation"

    -- User/session context
    user_id UUID,
    session_id VARCHAR(100),                  -- Chat session or request correlation
    kb_id UUID,

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_ms INTEGER,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',  -- in_progress, success, error
    error_type VARCHAR(100),
    error_message TEXT,

    -- Aggregated metrics (updated on trace completion)
    total_tokens INTEGER DEFAULT 0,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Indexes
    CONSTRAINT traces_status_check CHECK (status IN ('in_progress', 'success', 'error'))
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('observability.traces', 'started_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX idx_traces_trace_id ON observability.traces(trace_id);
CREATE INDEX idx_traces_user ON observability.traces(user_id, started_at DESC);
CREATE INDEX idx_traces_session ON observability.traces(session_id, started_at DESC);
CREATE INDEX idx_traces_operation ON observability.traces(operation_type, started_at DESC);
CREATE INDEX idx_traces_status ON observability.traces(status, started_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- SPANS TABLE - Child operations within a trace
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE observability.spans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Trace hierarchy
    trace_id VARCHAR(32) NOT NULL,
    parent_span_id UUID,                      -- NULL for root spans
    span_id VARCHAR(16) NOT NULL,             -- 8-byte hex string

    -- Operation details
    name VARCHAR(100) NOT NULL,               -- "llm.completion", "embedding.generate"
    span_type VARCHAR(50) NOT NULL,           -- "llm", "embedding", "retrieval", "parse", etc.

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_ms INTEGER,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    error_type VARCHAR(100),
    error_message TEXT,

    -- Type-specific fields (denormalized for query performance)
    -- LLM spans
    model VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    temperature DECIMAL(3, 2),

    -- Embedding spans
    embedding_model VARCHAR(100),
    vector_count INTEGER,
    vector_dimensions INTEGER,

    -- Retrieval spans
    query_text TEXT,
    result_count INTEGER,
    top_score DECIMAL(5, 4),

    -- Parsing spans
    file_type VARCHAR(50),
    file_size_bytes BIGINT,
    page_count INTEGER,

    -- Chunking spans
    chunk_count INTEGER,
    chunk_strategy VARCHAR(50),

    -- Flexible metadata
    input_preview TEXT,                       -- First 500 chars of input
    output_preview TEXT,                      -- First 500 chars of output
    metadata JSONB DEFAULT '{}'
);

SELECT create_hypertable('observability.spans', 'started_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX idx_spans_trace ON observability.spans(trace_id, started_at);
CREATE INDEX idx_spans_parent ON observability.spans(parent_span_id);
CREATE INDEX idx_spans_type ON observability.spans(span_type, started_at DESC);
CREATE INDEX idx_spans_model ON observability.spans(model, started_at DESC) WHERE model IS NOT NULL;

-- ═══════════════════════════════════════════════════════════════════════════
-- CHAT_MESSAGES TABLE - Persistent chat history (replacing Redis-only)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE observability.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Trace correlation
    trace_id VARCHAR(32),
    span_id UUID,

    -- Conversation context
    session_id VARCHAR(100) NOT NULL,
    user_id UUID NOT NULL,
    kb_id UUID NOT NULL,

    -- Message content
    role VARCHAR(20) NOT NULL,                -- "user", "assistant", "system"
    content TEXT NOT NULL,

    -- Turn metadata
    turn_number INTEGER NOT NULL,

    -- For assistant messages: retrieval details
    sources JSONB,                            -- [{doc_id, doc_name, chunk_id, score, excerpt}]
    citations JSONB,                          -- [{marker: "[1]", doc_id, page, section}]

    -- Token usage (for assistant messages)
    prompt_tokens INTEGER,
    completion_tokens INTEGER,

    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    response_time_ms INTEGER                  -- Time from user message to response complete
);

SELECT create_hypertable('observability.chat_messages', 'created_at',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE INDEX idx_chat_session ON observability.chat_messages(session_id, turn_number);
CREATE INDEX idx_chat_user ON observability.chat_messages(user_id, created_at DESC);
CREATE INDEX idx_chat_kb ON observability.chat_messages(kb_id, created_at DESC);
CREATE INDEX idx_chat_trace ON observability.chat_messages(trace_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- DOCUMENT_EVENTS TABLE - Detailed processing step events
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE observability.document_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Trace correlation
    trace_id VARCHAR(32) NOT NULL,
    span_id UUID,

    -- Document context
    document_id UUID NOT NULL,
    kb_id UUID NOT NULL,

    -- Event details
    event_type VARCHAR(50) NOT NULL,          -- upload, parse, chunk, embed, index, complete
    status VARCHAR(20) NOT NULL,              -- started, completed, failed, skipped

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,

    -- Step-specific metrics
    -- Parse step
    extracted_pages INTEGER,
    extracted_chars INTEGER,
    tables_found INTEGER,
    images_found INTEGER,

    -- Chunk step
    chunks_created INTEGER,
    avg_chunk_size INTEGER,

    -- Embed step
    vectors_generated INTEGER,
    embedding_model VARCHAR(100),

    -- Index step
    vectors_upserted INTEGER,
    collection_name VARCHAR(100),

    -- Error details
    error_type VARCHAR(100),
    error_message TEXT,
    retryable BOOLEAN,
    retry_count INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

SELECT create_hypertable('observability.document_events', 'started_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX idx_doc_events_document ON observability.document_events(document_id, started_at);
CREATE INDEX idx_doc_events_trace ON observability.document_events(trace_id);
CREATE INDEX idx_doc_events_type ON observability.document_events(event_type, started_at DESC);
CREATE INDEX idx_doc_events_status ON observability.document_events(status, started_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- METRICS_AGGREGATES TABLE - Pre-computed metrics for dashboards
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE observability.metrics_aggregates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Aggregation window
    bucket_time TIMESTAMPTZ NOT NULL,         -- Truncated to hour
    granularity VARCHAR(10) NOT NULL,         -- "hour", "day", "week"

    -- Dimension
    metric_name VARCHAR(100) NOT NULL,
    dimension_type VARCHAR(50),               -- "kb", "user", "model", "operation"
    dimension_value VARCHAR(100),

    -- Metrics
    count INTEGER DEFAULT 0,
    sum_value DECIMAL(15, 4) DEFAULT 0,
    min_value DECIMAL(15, 4),
    max_value DECIMAL(15, 4),
    avg_value DECIMAL(15, 4),
    p50_value DECIMAL(15, 4),
    p95_value DECIMAL(15, 4),
    p99_value DECIMAL(15, 4),

    -- Composite unique key
    UNIQUE (bucket_time, granularity, metric_name, dimension_type, dimension_value)
);

SELECT create_hypertable('observability.metrics_aggregates', 'bucket_time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE INDEX idx_metrics_name ON observability.metrics_aggregates(metric_name, bucket_time DESC);
CREATE INDEX idx_metrics_dimension ON observability.metrics_aggregates(dimension_type, dimension_value, bucket_time DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- PROVIDER_SYNC_STATUS TABLE - Track external provider sync state
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE observability.provider_sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    provider_name VARCHAR(50) NOT NULL,       -- "langfuse", "langsmith"
    trace_id VARCHAR(32) NOT NULL,

    -- Sync status
    synced_at TIMESTAMPTZ,
    sync_status VARCHAR(20) NOT NULL,         -- "pending", "synced", "failed"
    external_id VARCHAR(100),                 -- Provider's trace ID

    -- Error tracking
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider_name, trace_id)
);

CREATE INDEX idx_sync_pending ON observability.provider_sync_status(sync_status, created_at)
    WHERE sync_status = 'pending';
```

### 2.2 SQLAlchemy Models

```python
# backend/app/models/observability.py

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Trace(UUIDPrimaryKeyMixin, Base):
    """Root span for distributed operations."""

    __tablename__ = "traces"
    __table_args__ = (
        Index("idx_traces_trace_id", "trace_id"),
        Index("idx_traces_user", "user_id", "started_at"),
        Index("idx_traces_session", "session_id", "started_at"),
        Index("idx_traces_operation", "operation_type", "started_at"),
        {"schema": "observability"},
    )

    trace_id: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)

    user_id: Mapped[UUID | None] = mapped_column(nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    kb_id: Mapped[UUID | None] = mapped_column(nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    error_type: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)

    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)

    metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class Span(UUIDPrimaryKeyMixin, Base):
    """Child operations within a trace."""

    __tablename__ = "spans"
    __table_args__ = (
        Index("idx_spans_trace", "trace_id", "started_at"),
        Index("idx_spans_parent", "parent_span_id"),
        Index("idx_spans_type", "span_type", "started_at"),
        {"schema": "observability"},
    )

    trace_id: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_span_id: Mapped[UUID | None] = mapped_column(nullable=True)
    span_id: Mapped[str] = mapped_column(String(16), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    span_type: Mapped[str] = mapped_column(String(50), nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    error_type: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)

    # LLM fields
    model: Mapped[str | None] = mapped_column(String(100))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))

    # Embedding fields
    embedding_model: Mapped[str | None] = mapped_column(String(100))
    vector_count: Mapped[int | None] = mapped_column(Integer)
    vector_dimensions: Mapped[int | None] = mapped_column(Integer)

    # Retrieval fields
    query_text: Mapped[str | None] = mapped_column(Text)
    result_count: Mapped[int | None] = mapped_column(Integer)
    top_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    # Parse fields
    file_type: Mapped[str | None] = mapped_column(String(50))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    page_count: Mapped[int | None] = mapped_column(Integer)

    # Chunk fields
    chunk_count: Mapped[int | None] = mapped_column(Integer)
    chunk_strategy: Mapped[str | None] = mapped_column(String(50))

    input_preview: Mapped[str | None] = mapped_column(Text)
    output_preview: Mapped[str | None] = mapped_column(Text)
    metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ChatMessage(UUIDPrimaryKeyMixin, Base):
    """Persistent chat history."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_chat_session", "session_id", "turn_number"),
        Index("idx_chat_user", "user_id", "created_at"),
        Index("idx_chat_kb", "kb_id", "created_at"),
        {"schema": "observability"},
    )

    trace_id: Mapped[str | None] = mapped_column(String(32))
    span_id: Mapped[UUID | None] = mapped_column(nullable=True)

    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[UUID] = mapped_column(nullable=False)
    kb_id: Mapped[UUID] = mapped_column(nullable=False)

    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)

    sources: Mapped[list[dict] | None] = mapped_column(JSONB)
    citations: Mapped[list[dict] | None] = mapped_column(JSONB)

    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    response_time_ms: Mapped[int | None] = mapped_column(Integer)


class DocumentEvent(UUIDPrimaryKeyMixin, Base):
    """Detailed document processing events."""

    __tablename__ = "document_events"
    __table_args__ = (
        Index("idx_doc_events_document", "document_id", "started_at"),
        Index("idx_doc_events_trace", "trace_id"),
        Index("idx_doc_events_type", "event_type", "started_at"),
        {"schema": "observability"},
    )

    trace_id: Mapped[str] = mapped_column(String(32), nullable=False)
    span_id: Mapped[UUID | None] = mapped_column(nullable=True)

    document_id: Mapped[UUID] = mapped_column(nullable=False)
    kb_id: Mapped[UUID] = mapped_column(nullable=False)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    # Parse metrics
    extracted_pages: Mapped[int | None] = mapped_column(Integer)
    extracted_chars: Mapped[int | None] = mapped_column(Integer)
    tables_found: Mapped[int | None] = mapped_column(Integer)
    images_found: Mapped[int | None] = mapped_column(Integer)

    # Chunk metrics
    chunks_created: Mapped[int | None] = mapped_column(Integer)
    avg_chunk_size: Mapped[int | None] = mapped_column(Integer)

    # Embed metrics
    vectors_generated: Mapped[int | None] = mapped_column(Integer)
    embedding_model: Mapped[str | None] = mapped_column(String(100))

    # Index metrics
    vectors_upserted: Mapped[int | None] = mapped_column(Integer)
    collection_name: Mapped[str | None] = mapped_column(String(100))

    # Error tracking
    error_type: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    retryable: Mapped[bool | None] = mapped_column(Boolean)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ProviderSyncStatus(UUIDPrimaryKeyMixin, Base):
    """Track external provider sync state."""

    __tablename__ = "provider_sync_status"
    __table_args__ = (
        Index("idx_sync_pending", "sync_status", "created_at"),
        {"schema": "observability"},
    )

    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(32), nullable=False)

    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(100))

    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

---

## 5. Service Architecture

### 5.1 ObservabilityService Interface

```python
# backend/app/services/observability_service.py

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any, AsyncIterator
from uuid import UUID, uuid4
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.observability import (
    ChatMessage,
    DocumentEvent,
    Span,
    Trace,
)


def generate_trace_id() -> str:
    """Generate W3C-compliant 16-byte trace ID as hex string."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate W3C-compliant 8-byte span ID as hex string."""
    return secrets.token_hex(8)


class TraceContext:
    """Container for distributed trace context."""

    def __init__(
        self,
        trace_id: str,
        span_id: str | None = None,
        parent_span_id: UUID | None = None,
        user_id: UUID | None = None,
        session_id: str | None = None,
        kb_id: UUID | None = None,
    ):
        self.trace_id = trace_id
        self.span_id = span_id or generate_span_id()
        self.parent_span_id = parent_span_id
        self.user_id = user_id
        self.session_id = session_id
        self.kb_id = kb_id
        self.db_trace_id: UUID | None = None  # Set when trace is persisted

    def child_context(self, span_id: UUID) -> "TraceContext":
        """Create child context for nested spans."""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=generate_span_id(),
            parent_span_id=span_id,
            user_id=self.user_id,
            session_id=self.session_id,
            kb_id=self.kb_id,
        )


class ObservabilityProvider(ABC):
    """Abstract base class for observability providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Whether this provider is currently enabled."""
        pass

    @abstractmethod
    async def start_trace(
        self,
        ctx: TraceContext,
        name: str,
        operation_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Start a new trace."""
        pass

    @abstractmethod
    async def end_trace(
        self,
        ctx: TraceContext,
        status: str,
        error_type: str | None = None,
        error_message: str | None = None,
        total_tokens: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_cost_usd: Decimal = Decimal("0"),
    ) -> None:
        """End a trace."""
        pass

    @abstractmethod
    async def start_span(
        self,
        ctx: TraceContext,
        name: str,
        span_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """Start a span within a trace. Returns span database ID."""
        pass

    @abstractmethod
    async def end_span(
        self,
        span_id: UUID,
        status: str,
        duration_ms: int,
        error_type: str | None = None,
        error_message: str | None = None,
        **metrics: Any,
    ) -> None:
        """End a span with metrics."""
        pass

    @abstractmethod
    async def log_llm_call(
        self,
        ctx: TraceContext,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        cost_usd: Decimal,
        temperature: float | None = None,
        input_preview: str | None = None,
        output_preview: str | None = None,
    ) -> None:
        """Log an LLM API call."""
        pass

    @abstractmethod
    async def log_chat_message(
        self,
        ctx: TraceContext,
        role: str,
        content: str,
        turn_number: int,
        sources: list[dict] | None = None,
        citations: list[dict] | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        response_time_ms: int | None = None,
    ) -> None:
        """Log a chat message."""
        pass

    @abstractmethod
    async def log_document_event(
        self,
        ctx: TraceContext,
        document_id: UUID,
        event_type: str,
        status: str,
        duration_ms: int | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        **metrics: Any,
    ) -> None:
        """Log a document processing event."""
        pass


class PostgreSQLProvider(ObservabilityProvider):
    """Always-on internal PostgreSQL provider."""

    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._enabled = True  # Always enabled

    @property
    def name(self) -> str:
        return "postgresql"

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def _get_session(self) -> AsyncSession:
        """Get a new database session."""
        return self._session_factory()

    async def start_trace(
        self,
        ctx: TraceContext,
        name: str,
        operation_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        async with self._get_session() as session:
            trace = Trace(
                trace_id=ctx.trace_id,
                name=name,
                operation_type=operation_type,
                user_id=ctx.user_id,
                session_id=ctx.session_id,
                kb_id=ctx.kb_id,
                metadata=metadata or {},
            )
            session.add(trace)
            await session.commit()
            ctx.db_trace_id = trace.id

    async def end_trace(
        self,
        ctx: TraceContext,
        status: str,
        error_type: str | None = None,
        error_message: str | None = None,
        total_tokens: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_cost_usd: Decimal = Decimal("0"),
    ) -> None:
        async with self._get_session() as session:
            from sqlalchemy import update

            ended_at = datetime.utcnow()
            stmt = (
                update(Trace)
                .where(Trace.trace_id == ctx.trace_id)
                .values(
                    ended_at=ended_at,
                    status=status,
                    error_type=error_type,
                    error_message=error_message[:1000] if error_message else None,
                    total_tokens=total_tokens,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_cost_usd=total_cost_usd,
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def start_span(
        self,
        ctx: TraceContext,
        name: str,
        span_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        async with self._get_session() as session:
            span = Span(
                trace_id=ctx.trace_id,
                parent_span_id=ctx.parent_span_id,
                span_id=ctx.span_id,
                name=name,
                span_type=span_type,
                metadata=metadata or {},
            )
            session.add(span)
            await session.commit()
            return span.id

    async def end_span(
        self,
        span_id: UUID,
        status: str,
        duration_ms: int,
        error_type: str | None = None,
        error_message: str | None = None,
        **metrics: Any,
    ) -> None:
        async with self._get_session() as session:
            from sqlalchemy import update

            values = {
                "ended_at": datetime.utcnow(),
                "status": status,
                "duration_ms": duration_ms,
                "error_type": error_type,
                "error_message": error_message[:1000] if error_message else None,
            }
            # Add type-specific metrics
            for key, value in metrics.items():
                if hasattr(Span, key):
                    values[key] = value

            stmt = update(Span).where(Span.id == span_id).values(**values)
            await session.execute(stmt)
            await session.commit()

    async def log_llm_call(
        self,
        ctx: TraceContext,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        cost_usd: Decimal,
        temperature: float | None = None,
        input_preview: str | None = None,
        output_preview: str | None = None,
    ) -> None:
        async with self._get_session() as session:
            span = Span(
                trace_id=ctx.trace_id,
                parent_span_id=ctx.parent_span_id,
                span_id=generate_span_id(),
                name=f"llm.{model}",
                span_type="llm",
                status="success",
                duration_ms=latency_ms,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd,
                temperature=Decimal(str(temperature)) if temperature else None,
                input_preview=input_preview[:500] if input_preview else None,
                output_preview=output_preview[:500] if output_preview else None,
                ended_at=datetime.utcnow(),
            )
            session.add(span)
            await session.commit()

    async def log_chat_message(
        self,
        ctx: TraceContext,
        role: str,
        content: str,
        turn_number: int,
        sources: list[dict] | None = None,
        citations: list[dict] | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        response_time_ms: int | None = None,
    ) -> None:
        if not ctx.user_id or not ctx.kb_id or not ctx.session_id:
            return  # Cannot log without required context

        async with self._get_session() as session:
            message = ChatMessage(
                trace_id=ctx.trace_id,
                session_id=ctx.session_id,
                user_id=ctx.user_id,
                kb_id=ctx.kb_id,
                role=role,
                content=content,
                turn_number=turn_number,
                sources=sources,
                citations=citations,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time_ms=response_time_ms,
            )
            session.add(message)
            await session.commit()

    async def log_document_event(
        self,
        ctx: TraceContext,
        document_id: UUID,
        event_type: str,
        status: str,
        duration_ms: int | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        **metrics: Any,
    ) -> None:
        async with self._get_session() as session:
            event = DocumentEvent(
                trace_id=ctx.trace_id,
                document_id=document_id,
                kb_id=ctx.kb_id,
                event_type=event_type,
                status=status,
                duration_ms=duration_ms,
                error_type=error_type,
                error_message=error_message[:1000] if error_message else None,
            )
            # Set type-specific metrics
            for key, value in metrics.items():
                if hasattr(DocumentEvent, key):
                    setattr(event, key, value)

            if status in ("completed", "failed", "skipped"):
                event.completed_at = datetime.utcnow()

            session.add(event)
            await session.commit()


class LangFuseProvider(ObservabilityProvider):
    """Optional LangFuse integration provider."""

    def __init__(self):
        self._client = None
        self._enabled = bool(settings.langfuse_public_key and settings.langfuse_secret_key)

        if self._enabled:
            from langfuse import Langfuse
            self._client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host or "https://cloud.langfuse.com",
            )

    @property
    def name(self) -> str:
        return "langfuse"

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def start_trace(
        self,
        ctx: TraceContext,
        name: str,
        operation_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self._client:
            return

        try:
            self._client.trace(
                id=ctx.trace_id,
                name=name,
                user_id=str(ctx.user_id) if ctx.user_id else None,
                session_id=ctx.session_id,
                metadata={
                    "operation_type": operation_type,
                    "kb_id": str(ctx.kb_id) if ctx.kb_id else None,
                    **(metadata or {}),
                },
            )
        except Exception as e:
            # Fire-and-forget - log but don't propagate
            import structlog
            logger = structlog.get_logger(__name__)
            logger.warning("langfuse_trace_failed", error=str(e))

    async def end_trace(
        self,
        ctx: TraceContext,
        status: str,
        error_type: str | None = None,
        error_message: str | None = None,
        total_tokens: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_cost_usd: Decimal = Decimal("0"),
    ) -> None:
        if not self._client:
            return

        try:
            # LangFuse traces are auto-ended, but we can update metadata
            trace = self._client.trace(id=ctx.trace_id)
            trace.update(
                metadata={
                    "status": status,
                    "error_type": error_type,
                    "total_tokens": total_tokens,
                    "total_cost_usd": float(total_cost_usd),
                },
            )
            self._client.flush()
        except Exception as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.warning("langfuse_end_trace_failed", error=str(e))

    async def start_span(
        self,
        ctx: TraceContext,
        name: str,
        span_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        if not self._client:
            return uuid4()  # Return dummy ID

        try:
            trace = self._client.trace(id=ctx.trace_id)
            span = trace.span(
                name=name,
                metadata={"span_type": span_type, **(metadata or {})},
            )
            return UUID(span.id)
        except Exception as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.warning("langfuse_start_span_failed", error=str(e))
            return uuid4()

    async def end_span(
        self,
        span_id: UUID,
        status: str,
        duration_ms: int,
        error_type: str | None = None,
        error_message: str | None = None,
        **metrics: Any,
    ) -> None:
        # LangFuse spans auto-end; metrics logged via generation
        pass

    async def log_llm_call(
        self,
        ctx: TraceContext,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        cost_usd: Decimal,
        temperature: float | None = None,
        input_preview: str | None = None,
        output_preview: str | None = None,
    ) -> None:
        if not self._client:
            return

        try:
            trace = self._client.trace(id=ctx.trace_id)
            trace.generation(
                name=f"llm.{model}",
                model=model,
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
                model_parameters={"temperature": temperature} if temperature else None,
                input=input_preview,
                output=output_preview,
                metadata={
                    "latency_ms": latency_ms,
                    "cost_usd": float(cost_usd),
                },
            )
        except Exception as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.warning("langfuse_log_llm_failed", error=str(e))

    async def log_chat_message(
        self,
        ctx: TraceContext,
        role: str,
        content: str,
        turn_number: int,
        sources: list[dict] | None = None,
        citations: list[dict] | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        response_time_ms: int | None = None,
    ) -> None:
        # LangFuse handles chat via generation events
        pass

    async def log_document_event(
        self,
        ctx: TraceContext,
        document_id: UUID,
        event_type: str,
        status: str,
        duration_ms: int | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        **metrics: Any,
    ) -> None:
        if not self._client:
            return

        try:
            trace = self._client.trace(id=ctx.trace_id)
            trace.event(
                name=f"document.{event_type}",
                metadata={
                    "document_id": str(document_id),
                    "status": status,
                    "duration_ms": duration_ms,
                    "error_type": error_type,
                    **{k: v for k, v in metrics.items() if v is not None},
                },
            )
        except Exception as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.warning("langfuse_log_doc_event_failed", error=str(e))


class ObservabilityService:
    """
    Central observability service with provider registry.

    Usage:
        obs = ObservabilityService.get_instance()

        # Start trace
        ctx = await obs.start_trace(
            name="chat.conversation",
            operation_type="chat",
            user_id=current_user.id,
            session_id=session_id,
            kb_id=kb_id,
        )

        # Use context manager for spans
        async with obs.span(ctx, "retrieval", "retrieval") as span_id:
            results = await search_service.search(query)
            await obs.update_span(span_id, result_count=len(results))

        # Log LLM call
        await obs.log_llm_call(
            ctx=ctx,
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
            latency_ms=1500,
            cost_usd=Decimal("0.045"),
        )

        # End trace
        await obs.end_trace(ctx, status="success")
    """

    _instance: "ObservabilityService | None" = None

    def __init__(self, providers: list[ObservabilityProvider]):
        self.providers = [p for p in providers if p.enabled]

    @classmethod
    def get_instance(cls) -> "ObservabilityService":
        """Get singleton instance."""
        if cls._instance is None:
            from app.core.database import async_session_factory

            providers = [
                PostgreSQLProvider(async_session_factory),
                LangFuseProvider(),
            ]
            cls._instance = cls(providers)
        return cls._instance

    async def start_trace(
        self,
        name: str,
        operation_type: str,
        user_id: UUID | None = None,
        session_id: str | None = None,
        kb_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceContext:
        """Start a new distributed trace."""
        ctx = TraceContext(
            trace_id=generate_trace_id(),
            user_id=user_id,
            session_id=session_id,
            kb_id=kb_id,
        )

        for provider in self.providers:
            try:
                await provider.start_trace(ctx, name, operation_type, metadata)
            except Exception as e:
                import structlog
                logger = structlog.get_logger(__name__)
                logger.warning(
                    "provider_start_trace_failed",
                    provider=provider.name,
                    error=str(e),
                )

        return ctx

    async def end_trace(
        self,
        ctx: TraceContext,
        status: str,
        error_type: str | None = None,
        error_message: str | None = None,
        total_tokens: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_cost_usd: Decimal = Decimal("0"),
    ) -> None:
        """End a distributed trace."""
        for provider in self.providers:
            try:
                await provider.end_trace(
                    ctx,
                    status,
                    error_type,
                    error_message,
                    total_tokens,
                    prompt_tokens,
                    completion_tokens,
                    total_cost_usd,
                )
            except Exception as e:
                import structlog
                logger = structlog.get_logger(__name__)
                logger.warning(
                    "provider_end_trace_failed",
                    provider=provider.name,
                    error=str(e),
                )

    @asynccontextmanager
    async def span(
        self,
        ctx: TraceContext,
        name: str,
        span_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[UUID]:
        """Context manager for spans with automatic timing."""
        import time

        span_ids: dict[str, UUID] = {}
        start_time = time.monotonic()
        error_info: tuple[str | None, str | None] = (None, None)

        # Start span in all providers
        for provider in self.providers:
            try:
                span_id = await provider.start_span(ctx, name, span_type, metadata)
                span_ids[provider.name] = span_id
            except Exception as e:
                import structlog
                logger = structlog.get_logger(__name__)
                logger.warning(
                    "provider_start_span_failed",
                    provider=provider.name,
                    error=str(e),
                )

        # Return the PostgreSQL span ID (primary)
        primary_span_id = span_ids.get("postgresql", uuid4())

        try:
            yield primary_span_id
        except Exception as e:
            error_info = (type(e).__name__, str(e))
            raise
        finally:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            status = "error" if error_info[0] else "success"

            # End span in all providers
            for provider in self.providers:
                if provider.name in span_ids:
                    try:
                        await provider.end_span(
                            span_ids[provider.name],
                            status,
                            duration_ms,
                            error_info[0],
                            error_info[1],
                        )
                    except Exception as e:
                        import structlog
                        logger = structlog.get_logger(__name__)
                        logger.warning(
                            "provider_end_span_failed",
                            provider=provider.name,
                            error=str(e),
                        )

    async def log_llm_call(
        self,
        ctx: TraceContext,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        cost_usd: Decimal,
        temperature: float | None = None,
        input_preview: str | None = None,
        output_preview: str | None = None,
    ) -> None:
        """Log an LLM API call."""
        for provider in self.providers:
            try:
                await provider.log_llm_call(
                    ctx,
                    model,
                    prompt_tokens,
                    completion_tokens,
                    latency_ms,
                    cost_usd,
                    temperature,
                    input_preview,
                    output_preview,
                )
            except Exception as e:
                import structlog
                logger = structlog.get_logger(__name__)
                logger.warning(
                    "provider_log_llm_failed",
                    provider=provider.name,
                    error=str(e),
                )

    async def log_chat_message(
        self,
        ctx: TraceContext,
        role: str,
        content: str,
        turn_number: int,
        sources: list[dict] | None = None,
        citations: list[dict] | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        response_time_ms: int | None = None,
    ) -> None:
        """Log a chat message."""
        for provider in self.providers:
            try:
                await provider.log_chat_message(
                    ctx,
                    role,
                    content,
                    turn_number,
                    sources,
                    citations,
                    prompt_tokens,
                    completion_tokens,
                    response_time_ms,
                )
            except Exception as e:
                import structlog
                logger = structlog.get_logger(__name__)
                logger.warning(
                    "provider_log_chat_failed",
                    provider=provider.name,
                    error=str(e),
                )

    async def log_document_event(
        self,
        ctx: TraceContext,
        document_id: UUID,
        event_type: str,
        status: str,
        duration_ms: int | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        **metrics: Any,
    ) -> None:
        """Log a document processing event."""
        for provider in self.providers:
            try:
                await provider.log_document_event(
                    ctx,
                    document_id,
                    event_type,
                    status,
                    duration_ms,
                    error_type,
                    error_message,
                    **metrics,
                )
            except Exception as e:
                import structlog
                logger = structlog.get_logger(__name__)
                logger.warning(
                    "provider_log_doc_event_failed",
                    provider=provider.name,
                    error=str(e),
                )
```

### 5.2 Configuration Updates

```python
# backend/app/core/config.py - Add these settings

class Settings(BaseSettings):
    # ... existing settings ...

    # Observability - Internal (always enabled)
    observability_enabled: bool = True
    observability_retention_days: int = 90
    observability_metrics_aggregation_enabled: bool = True

    # Observability - LangFuse (optional)
    langfuse_enabled: bool = False
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None  # Default: https://cloud.langfuse.com

    # TimescaleDB
    timescaledb_enabled: bool = True
```

---

## 6. API Endpoints

### 6.1 Observability Admin API

```python
# backend/app/api/v1/observability.py

from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin
from app.core.database import get_session
from app.models.observability import (
    ChatMessage,
    DocumentEvent,
    Span,
    Trace,
)
from app.models.user import User
from app.schemas.observability import (
    ChatHistoryResponse,
    DocumentTimelineResponse,
    ObservabilityStatsResponse,
    SpanListResponse,
    TraceDetailResponse,
    TraceListResponse,
)

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/traces", response_model=TraceListResponse)
async def list_traces(
    operation_type: str | None = None,
    status: str | None = None,
    user_id: UUID | None = None,
    kb_id: UUID | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """List traces with filtering and pagination."""
    query = select(Trace).order_by(Trace.started_at.desc())

    if operation_type:
        query = query.where(Trace.operation_type == operation_type)
    if status:
        query = query.where(Trace.status == status)
    if user_id:
        query = query.where(Trace.user_id == user_id)
    if kb_id:
        query = query.where(Trace.kb_id == kb_id)
    if from_date:
        query = query.where(Trace.started_at >= from_date)
    if to_date:
        query = query.where(Trace.started_at <= to_date)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)

    # Paginate
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    traces = result.scalars().all()

    return TraceListResponse(
        traces=traces,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
async def get_trace(
    trace_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Get trace details with all spans."""
    # Get trace
    trace_query = select(Trace).where(Trace.trace_id == trace_id)
    trace = await session.scalar(trace_query)

    if not trace:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trace not found")

    # Get all spans
    spans_query = (
        select(Span)
        .where(Span.trace_id == trace_id)
        .order_by(Span.started_at)
    )
    result = await session.execute(spans_query)
    spans = result.scalars().all()

    # Get document events if applicable
    doc_events_query = (
        select(DocumentEvent)
        .where(DocumentEvent.trace_id == trace_id)
        .order_by(DocumentEvent.started_at)
    )
    result = await session.execute(doc_events_query)
    doc_events = result.scalars().all()

    # Get chat messages if applicable
    chat_query = (
        select(ChatMessage)
        .where(ChatMessage.trace_id == trace_id)
        .order_by(ChatMessage.turn_number)
    )
    result = await session.execute(chat_query)
    chat_messages = result.scalars().all()

    return TraceDetailResponse(
        trace=trace,
        spans=spans,
        document_events=doc_events,
        chat_messages=chat_messages,
    )


@router.get("/chat-history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str | None = None,
    user_id: UUID | None = None,
    kb_id: UUID | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Query persistent chat history."""
    query = select(ChatMessage).order_by(ChatMessage.created_at.desc())

    if session_id:
        query = query.where(ChatMessage.session_id == session_id)
    if user_id:
        query = query.where(ChatMessage.user_id == user_id)
    if kb_id:
        query = query.where(ChatMessage.kb_id == kb_id)
    if from_date:
        query = query.where(ChatMessage.created_at >= from_date)
    if to_date:
        query = query.where(ChatMessage.created_at <= to_date)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    messages = result.scalars().all()

    return ChatHistoryResponse(
        messages=messages,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/documents/{document_id}/timeline", response_model=DocumentTimelineResponse)
async def get_document_timeline(
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Get processing timeline for a document."""
    query = (
        select(DocumentEvent)
        .where(DocumentEvent.document_id == document_id)
        .order_by(DocumentEvent.started_at)
    )
    result = await session.execute(query)
    events = result.scalars().all()

    return DocumentTimelineResponse(
        document_id=document_id,
        events=events,
    )


@router.get("/stats", response_model=ObservabilityStatsResponse)
async def get_observability_stats(
    period: Literal["hour", "day", "week", "month"] = "day",
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Get aggregated observability statistics."""
    to_date = to_date or datetime.utcnow()

    if period == "hour":
        from_date = from_date or to_date - timedelta(hours=24)
    elif period == "day":
        from_date = from_date or to_date - timedelta(days=7)
    elif period == "week":
        from_date = from_date or to_date - timedelta(weeks=4)
    else:  # month
        from_date = from_date or to_date - timedelta(days=90)

    # Trace stats
    trace_stats_query = select(
        Trace.operation_type,
        Trace.status,
        func.count().label("count"),
        func.avg(Trace.duration_ms).label("avg_duration_ms"),
        func.sum(Trace.total_tokens).label("total_tokens"),
        func.sum(Trace.total_cost_usd).label("total_cost"),
    ).where(
        Trace.started_at.between(from_date, to_date)
    ).group_by(
        Trace.operation_type,
        Trace.status,
    )

    result = await session.execute(trace_stats_query)
    trace_stats = result.mappings().all()

    # LLM model usage
    llm_stats_query = select(
        Span.model,
        func.count().label("call_count"),
        func.sum(Span.prompt_tokens).label("prompt_tokens"),
        func.sum(Span.completion_tokens).label("completion_tokens"),
        func.sum(Span.cost_usd).label("total_cost"),
        func.avg(Span.duration_ms).label("avg_latency_ms"),
    ).where(
        Span.span_type == "llm",
        Span.started_at.between(from_date, to_date),
        Span.model.isnot(None),
    ).group_by(
        Span.model,
    )

    result = await session.execute(llm_stats_query)
    llm_stats = result.mappings().all()

    # Document processing stats
    doc_stats_query = select(
        DocumentEvent.event_type,
        DocumentEvent.status,
        func.count().label("count"),
        func.avg(DocumentEvent.duration_ms).label("avg_duration_ms"),
    ).where(
        DocumentEvent.started_at.between(from_date, to_date)
    ).group_by(
        DocumentEvent.event_type,
        DocumentEvent.status,
    )

    result = await session.execute(doc_stats_query)
    doc_stats = result.mappings().all()

    return ObservabilityStatsResponse(
        period=period,
        from_date=from_date,
        to_date=to_date,
        trace_stats=trace_stats,
        llm_stats=llm_stats,
        document_stats=doc_stats,
    )
```

---

## 7. Implementation Plan

### 7.1 Epic 9 Stories Overview

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| 9-1 | Observability Schema & Models | 5 | P0 |
| 9-2 | PostgreSQL Provider Implementation | 5 | P0 |
| 9-3 | TraceContext & Core Service | 5 | P0 |
| 9-4 | Document Processing Instrumentation | 5 | P0 |
| 9-5 | Chat/RAG Flow Instrumentation | 5 | P0 |
| 9-6 | LiteLLM Integration Hooks | 3 | P0 |
| 9-7 | LangFuse Provider Implementation | 5 | P1 |
| 9-8 | Observability Admin API | 5 | P0 |
| 9-9 | Trace Viewer UI Component | 5 | P1 |
| 9-10 | Chat History Viewer UI | 5 | P1 |
| 9-11 | Document Timeline UI | 3 | P1 |
| 9-12 | Observability Dashboard Widgets | 5 | P1 |
| 9-13 | Metrics Aggregation Worker | 3 | P2 |
| 9-14 | Data Retention & Cleanup | 3 | P2 |
| **Total** | | **62** | |

### 5.2 Detailed Story Specifications

#### Story 9-1: Observability Schema & Models

**Description:** Create PostgreSQL schema with TimescaleDB hypertables for observability data storage.

**Acceptance Criteria:**
- [ ] AC1: Alembic migration creates `observability` schema
- [ ] AC2: `traces` hypertable with 1-day chunks created
- [ ] AC3: `spans` hypertable with 1-day chunks created
- [ ] AC4: `chat_messages` hypertable with 7-day chunks created
- [ ] AC5: `document_events` hypertable with 1-day chunks created
- [ ] AC6: `metrics_aggregates` hypertable with 7-day chunks created
- [ ] AC7: `provider_sync_status` table created
- [ ] AC8: All indexes defined per schema design
- [ ] AC9: SQLAlchemy models map correctly to tables
- [ ] AC10: Unit tests verify model CRUD operations

**Technical Notes:**
- Enable TimescaleDB extension in migration
- Use `select create_hypertable()` for time-series optimization
- Set chunk intervals based on expected data volume

---

#### Story 9-2: PostgreSQL Provider Implementation

**Description:** Implement the PostgreSQLProvider class for internal observability storage.

**Acceptance Criteria:**
- [ ] AC1: `PostgreSQLProvider` implements `ObservabilityProvider` interface
- [ ] AC2: `start_trace()` creates Trace record with all context fields
- [ ] AC3: `end_trace()` updates Trace with duration, status, tokens, cost
- [ ] AC4: `start_span()` creates Span record, returns database ID
- [ ] AC5: `end_span()` updates Span with duration and type-specific metrics
- [ ] AC6: `log_llm_call()` creates Span with LLM-specific fields
- [ ] AC7: `log_chat_message()` creates ChatMessage record
- [ ] AC8: `log_document_event()` creates DocumentEvent record
- [ ] AC9: All methods are fire-and-forget (catch and log exceptions)
- [ ] AC10: Integration tests verify data persistence

**Technical Notes:**
- Use dedicated session factory to avoid blocking request sessions
- Truncate long text fields to schema limits (1000 chars for errors)

---

#### Story 9-3: TraceContext & Core Service

**Description:** Implement TraceContext for distributed tracing and ObservabilityService as the central facade.

**Acceptance Criteria:**
- [ ] AC1: `TraceContext` holds W3C-compliant trace_id (32 hex) and span_id (16 hex)
- [ ] AC2: `TraceContext.child_context()` creates nested context for child spans
- [ ] AC3: `ObservabilityService` singleton pattern via `get_instance()`
- [ ] AC4: Service registers PostgreSQL provider (always) and LangFuse (if configured)
- [ ] AC5: `start_trace()` fans out to all enabled providers
- [ ] AC6: `end_trace()` fans out to all enabled providers
- [ ] AC7: `span()` context manager handles timing and error capture
- [ ] AC8: All provider failures are logged but don't propagate
- [ ] AC9: Unit tests verify trace context hierarchy
- [ ] AC10: Integration test with PostgreSQL provider end-to-end

---

#### Story 9-4: Document Processing Instrumentation

**Description:** Instrument document processing pipeline with observability.

**Acceptance Criteria:**
- [ ] AC1: `process_document` task starts trace with `operation_type="document"`
- [ ] AC2: Each processing step (upload, parse, chunk, embed, index) logged as DocumentEvent
- [ ] AC3: Parse step includes: extracted_pages, extracted_chars, tables_found
- [ ] AC4: Chunk step includes: chunks_created, avg_chunk_size, chunk_strategy
- [ ] AC5: Embed step includes: vectors_generated, embedding_model
- [ ] AC6: Index step includes: vectors_upserted, collection_name
- [ ] AC7: Errors captured with error_type, error_message, retryable flag
- [ ] AC8: Trace ends with final status (success/error) and aggregated metrics
- [ ] AC9: Existing `processing_steps` JSONB continues to work (backward compatibility)
- [ ] AC10: E2E test: upload document, verify full trace in observability schema

---

#### Story 9-5: Chat/RAG Flow Instrumentation

**Description:** Instrument conversation service with observability for chat history persistence.

**Acceptance Criteria:**
- [ ] AC1: `send_message` starts trace with `operation_type="chat"`
- [ ] AC2: User message logged via `log_chat_message()` with role="user"
- [ ] AC3: Retrieval step logged as Span with query_text, result_count, top_score
- [ ] AC4: LLM call logged with model, tokens, latency, cost
- [ ] AC5: Assistant message logged with role="assistant", sources, citations
- [ ] AC6: Streaming response tokens aggregated for final token count
- [ ] AC7: Turn number tracked per session for conversation ordering
- [ ] AC8: Session ID links multi-turn conversations
- [ ] AC9: Chat history persisted to PostgreSQL (parallel to Redis cache)
- [ ] AC10: Integration test: send 3 messages, verify all in chat_messages table

---

#### Story 9-6: LiteLLM Integration Hooks

**Description:** Add observability callbacks to LiteLLM client for LLM call tracking.

**Acceptance Criteria:**
- [ ] AC1: `LiteLLMEmbeddingClient.get_embeddings()` logs embedding span
- [ ] AC2: `chat_completion()` logs LLM span with model, tokens, latency
- [ ] AC3: Token usage extracted from LiteLLM response metadata
- [ ] AC4: Cost calculation based on model pricing (configurable)
- [ ] AC5: Streaming responses aggregate tokens for final count
- [ ] AC6: Retry attempts tracked in span metadata
- [ ] AC7: Rate limit errors captured with error_type
- [ ] AC8: TraceContext passed through client methods
- [ ] AC9: Fire-and-forget pattern - LLM calls not blocked by observability
- [ ] AC10: Unit tests with mocked LiteLLM verify event logging

---

#### Story 9-7: LangFuse Provider Implementation

**Description:** Implement optional LangFuse provider for external observability.

**Acceptance Criteria:**
- [ ] AC1: `LangFuseProvider` implements `ObservabilityProvider` interface
- [ ] AC2: Provider disabled if `langfuse_public_key` not configured
- [ ] AC3: `start_trace()` creates LangFuse trace with user_id, session_id
- [ ] AC4: `log_llm_call()` creates LangFuse generation with usage metrics
- [ ] AC5: Document events logged as LangFuse events with metadata
- [ ] AC6: Provider sync status tracked in `provider_sync_status` table
- [ ] AC7: All LangFuse calls are async and non-blocking
- [ ] AC8: SDK errors caught and logged (fire-and-forget)
- [ ] AC9: Flush called on trace end to ensure data sent
- [ ] AC10: Integration test with LangFuse mock server

**Configuration:**
```env
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com  # or self-hosted URL
```

---

#### Story 9-8: Observability Admin API

**Description:** Create REST API endpoints for querying observability data.

**Acceptance Criteria:**
- [x] AC1: `GET /api/v1/observability/traces` - list traces with filters (operation_type, status, user_id, kb_id, date range, search)
- [x] AC2: `GET /api/v1/observability/traces/{trace_id}` - trace detail with spans
- [ ] AC3: `GET /api/v1/observability/chat-history` - query chat messages
- [ ] AC4: `GET /api/v1/observability/documents/{id}/timeline` - document events
- [ ] AC5: `GET /api/v1/observability/stats` - aggregated statistics
- [x] AC6: All endpoints require admin authentication
- [x] AC7: Pagination with skip/limit (max 100 traces, 500 messages)
- [x] AC8: Date range filtering on all list endpoints
- [x] AC9: OpenAPI schemas documented (TraceListResponse includes document_id, name)
- [ ] AC10: Integration tests for all endpoints

---

#### Story 9-9: Trace Viewer UI Component

**Description:** Build React component for viewing trace details.

**Acceptance Criteria:**
- [x] AC1: Trace list view with operation type, document ID, status, duration, span count, time
- [x] AC2: Filtering by operation type, status, date range, and search (trace ID/name)
- [x] AC3: Click trace to view detail panel
- [ ] AC4: Trace detail shows timeline of spans (waterfall view)
- [ ] AC5: Span details show type-specific metrics
- [ ] AC6: Error spans highlighted in red with error message
- [ ] AC7: LLM spans show model, tokens, cost
- [ ] AC8: Responsive design for admin dashboard integration
- [ ] AC9: Loading states and error handling
- [ ] AC10: Unit tests for component rendering

---

#### Story 9-10: Chat History Viewer UI

**Description:** Build React component for browsing persistent chat history.

**Acceptance Criteria:**
- [ ] AC1: Session list with user, KB, message count, last active
- [ ] AC2: Click session to view conversation thread
- [ ] AC3: User and assistant messages rendered differently
- [ ] AC4: Citations displayed with source links
- [ ] AC5: Token usage and response time shown per message
- [ ] AC6: Search within chat history by content
- [ ] AC7: Filter by user, KB, date range
- [ ] AC8: Export conversation as JSON/CSV
- [ ] AC9: Pagination for long histories
- [ ] AC10: Unit tests for component rendering

---

#### Story 9-11: Document Timeline UI

**Description:** Build React component showing document processing timeline.

**Acceptance Criteria:**
- [ ] AC1: Access via document detail modal "View Processing" button
- [ ] AC2: Timeline visualization of processing steps
- [ ] AC3: Each step shows status icon (pending/in-progress/done/error)
- [ ] AC4: Step duration displayed in human-readable format
- [ ] AC5: Click step to see detailed metrics (chunks, vectors, etc.)
- [ ] AC6: Error steps show error type and message
- [ ] AC7: Retry count visible for failed steps
- [ ] AC8: Total processing time summarized at top
- [ ] AC9: Responsive design
- [ ] AC10: Unit tests for timeline rendering

---

#### Story 9-12: Observability Dashboard Widgets

**Description:** Add observability widgets to admin dashboard.

**Acceptance Criteria:**
- [ ] AC1: "LLM Usage" widget: total tokens, cost, by model
- [ ] AC2: "Processing Pipeline" widget: documents processed, avg time, error rate
- [ ] AC3: "Chat Activity" widget: messages today, active sessions, avg response time
- [ ] AC4: "System Health" widget: trace success rate, p95 latency
- [ ] AC5: Time period selector (hour/day/week/month)
- [ ] AC6: Auto-refresh every 30 seconds (configurable)
- [ ] AC7: Sparkline charts for trends
- [ ] AC8: Click widget to navigate to detailed view
- [ ] AC9: Widgets load independently (parallel fetching)
- [ ] AC10: Unit tests for widget components

---

#### Story 9-13: Metrics Aggregation Worker

**Description:** Implement Celery worker for pre-computing observability metrics.

**Acceptance Criteria:**
- [ ] AC1: Celery beat task runs hourly
- [ ] AC2: Aggregates trace metrics into `metrics_aggregates` table
- [ ] AC3: Computes count, sum, min, max, avg per metric
- [ ] AC4: Calculates p50, p95, p99 percentiles for latencies
- [ ] AC5: Dimensions: by operation_type, by model, by kb, by user
- [ ] AC6: Handles hour, day, week granularities
- [ ] AC7: Idempotent: re-running for same bucket updates metrics
- [ ] AC8: Backfill capability for missed periods
- [ ] AC9: Prometheus metrics for aggregation job health
- [ ] AC10: Unit tests for aggregation logic

---

#### Story 9-14: Data Retention & Cleanup

**Description:** Implement configurable data retention and cleanup.

**Acceptance Criteria:**
- [ ] AC1: Configuration: `OBSERVABILITY_RETENTION_DAYS` (default 90)
- [ ] AC2: Celery beat task runs daily at 3am
- [ ] AC3: Drops TimescaleDB chunks older than retention period
- [ ] AC4: Uses `drop_chunks()` for efficient deletion
- [ ] AC5: Logs chunk drop operations for audit
- [ ] AC6: Metrics aggregates retained longer (365 days)
- [ ] AC7: Provider sync status cleaned after 7 days
- [ ] AC8: Admin API endpoint to trigger manual cleanup
- [ ] AC9: Dry-run mode to preview deletions
- [ ] AC10: Unit tests for retention logic

---

## 8. Phased Implementation

### Phase 1: Core Infrastructure (Week 1-2)
- Story 9-1: Observability Schema & Models
- Story 9-2: PostgreSQL Provider Implementation
- Story 9-3: TraceContext & Core Service

**Milestone:** Internal observability storage operational

### Phase 2: Pipeline Instrumentation (Week 2-3)
- Story 9-4: Document Processing Instrumentation
- Story 9-5: Chat/RAG Flow Instrumentation
- Story 9-6: LiteLLM Integration Hooks

**Milestone:** All operations traced and persisted

### Phase 3: API & UI (Week 3-4)
- Story 9-8: Observability Admin API
- Story 9-9: Trace Viewer UI Component
- Story 9-10: Chat History Viewer UI
- Story 9-11: Document Timeline UI

**Milestone:** Admin can query and view observability data

### Phase 4: Advanced Features (Week 4-5)
- Story 9-7: LangFuse Provider Implementation
- Story 9-12: Observability Dashboard Widgets
- Story 9-13: Metrics Aggregation Worker
- Story 9-14: Data Retention & Cleanup

**Milestone:** Full hybrid observability platform operational

---

## 9. Configuration Reference

### 9.1 Environment Variables

```env
# Observability - Internal (always enabled)
OBSERVABILITY_ENABLED=true
OBSERVABILITY_RETENTION_DAYS=90
OBSERVABILITY_METRICS_AGGREGATION_ENABLED=true

# Observability - LangFuse (optional)
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

# TimescaleDB (for hypertables)
TIMESCALEDB_ENABLED=true
```

### 9.2 Dependency Versions

| Dependency | Minimum Version | Notes |
|------------|-----------------|-------|
| **PostgreSQL** | >= 14.0 | Required for TimescaleDB 2.x compatibility |
| **TimescaleDB** | >= 2.10.0 | Time-series optimization, `create_hypertable()`, `drop_chunks()` |
| **LangFuse SDK** | >= 2.0.0 | Python SDK for LangFuse provider integration |
| **SQLAlchemy** | >= 2.0.0 | Already in use - async support required |
| **asyncpg** | >= 0.27.0 | Already in use - async PostgreSQL driver |

#### pyproject.toml Additions

```toml
[project.dependencies]
# Existing dependencies - no changes
sqlalchemy = ">=2.0.0"
asyncpg = ">=0.27.0"

# New dependencies for Epic 9
langfuse = { version = ">=2.0.0", optional = true }
timescale-vector = ">=0.0.1"  # Optional - for vector extensions

[project.optional-dependencies]
langfuse = ["langfuse>=2.0.0"]
```

#### TimescaleDB Extension Installation

```sql
-- Added via Alembic migration (Story 9-1)
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

### 9.3 Docker Compose Addition

```yaml
# infrastructure/docker/docker-compose.yml - No changes needed
# PostgreSQL already deployed; TimescaleDB extension added via migration
```

---

## 10. Migration Path

### 10.1 From Current State

1. **Audit coexistence:** Existing `AuditService` and `audit.events` table remain untouched
2. **SearchAuditService migration:** Gradually migrate to ObservabilityService
3. **Document processing_steps:** Continue using JSONB field; observability adds parallel detailed events
4. **Redis chat history:** Kept as cache; PostgreSQL becomes source of truth

### 10.2 Backward Compatibility

- All existing APIs continue to work
- No breaking changes to document or chat flows
- Observability adds telemetry without modifying behavior

---

## 11. Risks, Assumptions & Open Questions

### 11.1 Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Performance impact from logging** | Medium | Medium | Fire-and-forget async pattern - never blocks request path |
| **Storage growth** | Medium | Low | TimescaleDB compression + configurable retention policies |
| **LangFuse SDK compatibility** | Low | Medium | Use OTEL bridge as fallback; thorough integration testing |
| **Migration complexity** | Low | Medium | Coexist with existing audit; gradual migration path defined |
| **TimescaleDB extension unavailable** | Low | High | Fallback to standard PostgreSQL tables (slower queries) |

### 11.2 Assumptions

| Assumption | Validation |
|------------|------------|
| PostgreSQL version supports TimescaleDB | Check during Story 9-1 migration; PostgreSQL >= 14 required |
| TimescaleDB extension available in all environments | Verify dev, staging, prod PostgreSQL deployments |
| LangFuse cloud latency acceptable | Test with fire-and-forget; <100ms network overhead expected |
| Admin users access observability <10 QPS | Dashboard queries sized for low concurrency |
| Chat history doesn't contain sensitive PII beyond compliance scope | Implement PII handling policy (Section 3.4) |

### 11.3 Open Questions

| Question | Owner | Target Resolution |
|----------|-------|-------------------|
| Should we expose trace IDs in API responses for debugging? | Architecture | Story 9-3 |
| Do we need per-KB observability enablement toggles? | PM | Story 9-7 |
| What's the data retention requirement for GDPR compliance? | Legal/Compliance | Before Story 9-14 |
| Should LangFuse be default-enabled if configured? | DevOps | Configuration decision |

---

## 12. Appendix

### A. Event Taxonomy

| Category | Event Type | Fields |
|----------|-----------|--------|
| **Document** | document.upload.started | file_type, size_bytes, kb_id |
| | document.parse.started | - |
| | document.parse.completed | pages, chars, tables, images |
| | document.parse.failed | error_type, error_message, retryable |
| | document.chunk.completed | chunks_created, avg_size, strategy |
| | document.embed.completed | vectors, model, dimensions |
| | document.index.completed | vectors_upserted, collection |
| **Chat** | chat.message.received | kb_id, session_id |
| | chat.retrieval.completed | query_text, result_count, top_score |
| | chat.llm.completed | model, tokens, latency, cost |
| | chat.response.sent | response_time_ms |
| **Search** | search.query.received | query_text, kb_ids, search_type |
| | search.embedding.completed | model, latency_ms |
| | search.qdrant.completed | result_count, latency_ms |

### B. Cost Calculation

LLM costs calculated based on model pricing:

```python
MODEL_PRICING = {
    "gpt-4": {"prompt": 0.03, "completion": 0.06},  # per 1K tokens
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
    "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
    "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
    # Local models (Ollama) - no cost
    "ollama/*": {"prompt": 0, "completion": 0},
}
```

### C. TimescaleDB Chunk Management

```sql
-- View chunk information
SELECT * FROM timescaledb_information.chunks
WHERE hypertable_name = 'traces';

-- Manual chunk drop (for testing)
SELECT drop_chunks('observability.traces', older_than => INTERVAL '90 days');

-- Compression policy (future optimization)
ALTER TABLE observability.traces SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'operation_type'
);

SELECT add_compression_policy('observability.traces', INTERVAL '7 days');
```

---

## Document Approval

| Role | Name | Status | Date |
|------|------|--------|------|
| Architect | Winston | Pending | |
| Tech Lead | Murat | Pending | |
| Product Manager | John | Pending | |
| Scrum Master | Bob | Pending | |

---

*This technical specification defines the complete architecture for Epic 9: Hybrid Observability Platform. Implementation should follow the phased approach to minimize risk and enable incremental value delivery.*
