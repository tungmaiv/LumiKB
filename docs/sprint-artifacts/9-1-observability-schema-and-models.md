# Story 9.1: Observability Schema & Models

Status: ready-for-dev

## Story

As an **administrator**,
I want **a dedicated observability database schema with optimized time-series storage**,
so that **I can persistently store and efficiently query traces, spans, chat history, and document processing events**.

## Acceptance Criteria

1. Alembic migration creates `observability` schema with TimescaleDB extension enabled
2. `traces` hypertable created with 1-day chunk intervals for root span storage
3. `spans` hypertable created with 1-day chunk intervals for child operation storage
4. `chat_messages` hypertable created with 7-day chunk intervals for conversation persistence
5. `document_events` hypertable created with 1-day chunk intervals for processing step events
6. `metrics_aggregates` hypertable created with 7-day chunk intervals for pre-computed dashboard metrics
7. `provider_sync_status` table created for tracking external provider sync state
8. All indexes defined per schema design (trace_id, user_id, session_id, operation_type, etc.)
9. SQLAlchemy 2.0 async-compatible models map correctly to all tables with proper type annotations
10. Unit tests verify model CRUD operations (create, read, update) for all observability models

## Tasks / Subtasks

- [ ] Task 1: Create Alembic migration for observability schema (AC: #1, #2, #3, #4, #5, #6, #7, #8)
  - [ ] Subtask 1.1: Enable TimescaleDB extension in migration
  - [ ] Subtask 1.2: Create `observability` schema
  - [ ] Subtask 1.3: Create `traces` table with W3C trace context fields and token/cost aggregates
  - [ ] Subtask 1.4: Convert `traces` to hypertable with 1-day chunks
  - [ ] Subtask 1.5: Create `spans` table with type-specific fields (LLM, embedding, retrieval, parse, chunk)
  - [ ] Subtask 1.6: Convert `spans` to hypertable with 1-day chunks
  - [ ] Subtask 1.7: Create `chat_messages` table with conversation context and citation fields
  - [ ] Subtask 1.8: Convert `chat_messages` to hypertable with 7-day chunks
  - [ ] Subtask 1.9: Create `document_events` table with step-specific metrics
  - [ ] Subtask 1.10: Convert `document_events` to hypertable with 1-day chunks
  - [ ] Subtask 1.11: Create `metrics_aggregates` table with dimension-based aggregations
  - [ ] Subtask 1.12: Convert `metrics_aggregates` to hypertable with 7-day chunks
  - [ ] Subtask 1.13: Create `provider_sync_status` table for external provider tracking
  - [ ] Subtask 1.14: Add all required indexes per schema design

- [ ] Task 2: Create SQLAlchemy models (AC: #9)
  - [ ] Subtask 2.1: Create `Trace` model with UUIDPrimaryKeyMixin and proper schema setting
  - [ ] Subtask 2.2: Create `Span` model with type-specific nullable fields
  - [ ] Subtask 2.3: Create `ChatMessage` model with JSONB sources/citations fields
  - [ ] Subtask 2.4: Create `DocumentEvent` model with step-specific metrics
  - [ ] Subtask 2.5: Create `MetricsAggregate` model with percentile fields (p50, p95, p99)
  - [ ] Subtask 2.6: Create `ProviderSyncStatus` model
  - [ ] Subtask 2.7: Register models in `app/models/__init__.py`

- [ ] Task 3: Write unit tests (AC: #10)
  - [ ] Subtask 3.1: Test Trace model CRUD operations
  - [ ] Subtask 3.2: Test Span model with various span_type values
  - [ ] Subtask 3.3: Test ChatMessage model with sources and citations
  - [ ] Subtask 3.4: Test DocumentEvent model for all event_type values
  - [ ] Subtask 3.5: Test MetricsAggregate unique constraint behavior
  - [ ] Subtask 3.6: Test ProviderSyncStatus sync_status transitions

## Dev Notes

### Architecture Patterns

- **Schema Separation**: Dedicated `observability` schema like existing `audit` schema for clear domain boundaries
- **TimescaleDB Hypertables**: Time-series optimization for efficient range queries and automatic data retention
- **Fire-and-Forget Design**: Schema supports async writes that never block application flow
- **Denormalized Fields**: Span type-specific fields (LLM, embedding, etc.) are denormalized for query performance

### Key Technical Decisions

- **W3C Trace Context**: `trace_id` is 32-hex (16 bytes), `span_id` is 16-hex (8 bytes) per OpenTelemetry spec
- **Chunk Intervals**: 1-day for high-volume tables (traces, spans, doc_events), 7-day for lower-volume (chat, metrics)
- **JSONB Fields**: Used for flexible metadata, sources, and citations storage
- **Decimal Precision**: `cost_usd` uses `Numeric(10, 6)` for accurate cost tracking

### Source Tree Components

```
backend/
├── alembic/versions/
│   └── xxx_add_observability_schema.py  # New migration
├── app/models/
│   ├── __init__.py                       # Register new models
│   └── observability.py                  # New: All observability models
└── tests/unit/
    └── test_observability_models.py      # New: Model CRUD tests
```

### Testing Standards

- Use factory pattern for test data generation
- Use async test fixtures with `pytest-asyncio`
- Test with actual database transactions (rollback after each test)
- Verify index creation via SQLAlchemy introspection

### Project Structure Notes

- Models follow existing patterns from `app/models/document.py` and `app/models/user.py`
- Use `UUIDPrimaryKeyMixin` and `TimestampMixin` from `app/models/base.py`
- Alembic migration should be auto-generated then manually enhanced for hypertable creation

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#4.1 PostgreSQL Schema]
- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#2.2 SQLAlchemy Models]
- [Source: docs/epics/epic-9-observability.md#Phase 1: Core Infrastructure]

## Dev Agent Record

### Context Reference

- [9-1-observability-schema-and-models.context.xml](9-1-observability-schema-and-models.context.xml)

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-14 | Story drafted | Claude (SM Agent) |
