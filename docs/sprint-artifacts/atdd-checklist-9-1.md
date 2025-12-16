# ATDD Checklist: Story 9-1 - Observability Schema & Models

**Story ID:** 9-1
**Title:** Observability Schema & Models
**Generated:** 2025-12-14
**Agent:** TEA (Master Test Architect)

---

## Test Summary

| Test Level | Test Count | Status |
|------------|------------|--------|
| Unit | 25 | 🔴 Failing (Not Implemented) |
| Integration | 6 (via migration) | 🔴 Failing (Not Implemented) |
| E2E | 0 | N/A |

---

## Acceptance Criteria Coverage

| AC# | Description | Test Type | Test File | Status |
|-----|-------------|-----------|-----------|--------|
| 1 | TimescaleDB extension enabled | Integration | Migration verify | 🔴 |
| 2 | `traces` hypertable with 1-day chunks | Integration | Migration verify | 🔴 |
| 3 | `spans` hypertable with 1-day chunks | Integration | Migration verify | 🔴 |
| 4 | `chat_messages` hypertable with 7-day chunks | Integration | Migration verify | 🔴 |
| 5 | `document_events` hypertable with 1-day chunks | Integration | Migration verify | 🔴 |
| 6 | `metrics_aggregates` hypertable with 7-day chunks | Integration | Migration verify | 🔴 |
| 7 | `provider_sync_status` table created | Integration | Migration verify | 🔴 |
| 8 | All indexes defined per schema design | Integration | Migration verify | 🔴 |
| 9 | SQLAlchemy 2.0 async-compatible models | Unit | test_observability_models.py | 🔴 |
| 10 | Unit tests verify model CRUD | Unit | test_observability_models.py | 🔴 |

---

## Test Files Created

### Unit Tests
- **File:** `backend/tests/unit/test_observability_models.py`
- **Classes:**
  - `TestTraceIdGeneration` - W3C trace ID validation
  - `TestSpanIdGeneration` - W3C span ID validation
  - `TestTraceModel` - Trace model CRUD
  - `TestSpanModel` - Span model with type-specific fields
  - `TestChatMessageModel` - ChatMessage with sources/citations
  - `TestDocumentEventModel` - DocumentEvent for processing steps
  - `TestMetricsAggregateModel` - MetricsAggregate with percentiles
  - `TestProviderSyncStatusModel` - ProviderSyncStatus tracking

### Data Factories
- **File:** `backend/tests/factories/observability_factory.py`
- **Factories:**
  - `generate_trace_id()` - W3C-compliant 32-hex trace ID
  - `generate_span_id()` - W3C-compliant 16-hex span ID
  - `create_trace()` - Full trace test data
  - `create_completed_trace()` - Completed trace with timing
  - `create_failed_trace()` - Error trace with details
  - `create_span()` - Span with type-specific fields
  - `create_llm_span()` - LLM span convenience factory
  - `create_retrieval_span()` - Retrieval span convenience factory
  - `create_chat_message()` - Chat message test data (renamed to `create_obs_chat_message` in exports)
  - `create_document_event()` - Document event test data
  - `create_metrics_aggregate()` - Metrics aggregate test data
  - `create_provider_sync_status()` - Provider sync status test data

---

## Implementation Checklist

### Task 1: Create Alembic Migration
- [ ] Enable TimescaleDB extension
- [ ] Create `observability` schema
- [ ] Create `traces` table with W3C trace context fields
- [ ] Convert `traces` to hypertable (1-day chunks)
- [ ] Create `spans` table with type-specific fields
- [ ] Convert `spans` to hypertable (1-day chunks)
- [ ] Create `chat_messages` table with JSONB fields
- [ ] Convert `chat_messages` to hypertable (7-day chunks)
- [ ] Create `document_events` table with step metrics
- [ ] Convert `document_events` to hypertable (1-day chunks)
- [ ] Create `metrics_aggregates` table with percentiles
- [ ] Convert `metrics_aggregates` to hypertable (7-day chunks)
- [ ] Create `provider_sync_status` table
- [ ] Add all required indexes

### Task 2: Create SQLAlchemy Models
- [ ] Create `Trace` model with UUIDPrimaryKeyMixin
- [ ] Create `Span` model with nullable type fields
- [ ] Create `ChatMessage` model with JSONB sources/citations
- [ ] Create `DocumentEvent` model with step metrics
- [ ] Create `MetricsAggregate` model with p50/p95/p99
- [ ] Create `ProviderSyncStatus` model
- [ ] Register models in `app/models/__init__.py`

### Task 3: Pass Unit Tests
- [ ] All `TestTraceModel` tests pass
- [ ] All `TestSpanModel` tests pass
- [ ] All `TestChatMessageModel` tests pass
- [ ] All `TestDocumentEventModel` tests pass
- [ ] All `TestMetricsAggregateModel` tests pass
- [ ] All `TestProviderSyncStatusModel` tests pass

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `backend/alembic/versions/xxx_add_observability_schema.py` | Create | Migration for observability schema |
| `backend/app/models/observability.py` | Create | SQLAlchemy models |
| `backend/app/models/__init__.py` | Modify | Register observability models |

---

## Run Tests

```bash
# Run unit tests (should fail until implemented)
cd backend
.venv/bin/pytest tests/unit/test_observability_models.py -v

# Run specific test class
.venv/bin/pytest tests/unit/test_observability_models.py::TestTraceModel -v

# Run with verbose output
.venv/bin/pytest tests/unit/test_observability_models.py -v --tb=short
```

---

## Definition of Done

- [ ] All unit tests pass
- [ ] Migration creates all tables correctly
- [ ] Hypertables verified via `\d+ observability.traces`
- [ ] Indexes verified via `\di observability.*`
- [ ] Code review completed
- [ ] No ruff/type errors

---

## Notes

- Models use `observability` schema prefix
- TimescaleDB extension must be available in PostgreSQL
- W3C trace context: trace_id=32 hex, span_id=16 hex
- JSONB fields for flexible metadata storage
- Decimal precision: cost_usd uses Numeric(10, 6)
