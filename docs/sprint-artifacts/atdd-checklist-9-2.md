# ATDD Checklist: Story 9-2 - PostgreSQL Provider Implementation

**Story ID:** 9-2
**Title:** PostgreSQL Provider Implementation
**Generated:** 2025-12-14
**Agent:** TEA (Master Test Architect)

---

## Test Summary

| Test Level | Test Count | Status |
|------------|------------|--------|
| Unit | 0 | N/A |
| Integration | 32 | 🔴 Failing (Not Implemented) |
| E2E | 0 | N/A |

---

## Acceptance Criteria Coverage

| AC# | Description | Test Type | Test Class | Status |
|-----|-------------|-----------|------------|--------|
| 1 | Implements ObservabilityProvider interface | Integration | TestPostgreSQLProviderInterface | 🔴 |
| 2 | start_trace creates Trace with context fields | Integration | TestStartTrace | 🔴 |
| 3 | end_trace updates duration, status, metrics | Integration | TestEndTrace | 🔴 |
| 4 | start_span creates Span, returns UUID | Integration | TestStartSpan | 🔴 |
| 5 | end_span updates with type-specific metrics | Integration | TestEndSpan | 🔴 |
| 6 | log_llm_call creates Span with LLM fields | Integration | TestLogLLMCall | 🔴 |
| 7 | log_chat_message creates ChatMessage record | Integration | TestLogChatMessage | 🔴 |
| 8 | log_document_event creates DocumentEvent | Integration | TestLogDocumentEvent | 🔴 |
| 9 | Fire-and-forget: exceptions logged, not propagated | Integration | TestFireAndForget | 🔴 |
| 10 | Integration tests verify all methods | Integration | All classes | 🔴 |

---

## Test Files Created

### Integration Tests
- **File:** `backend/tests/integration/test_observability_provider.py`
- **Classes:**
  - `TestPostgreSQLProviderInterface` - Interface compliance (3 tests)
  - `TestStartTrace` - start_trace behavior (3 tests)
  - `TestEndTrace` - end_trace behavior (3 tests)
  - `TestStartSpan` - start_span behavior (2 tests)
  - `TestEndSpan` - end_span behavior (3 tests)
  - `TestLogLLMCall` - log_llm_call behavior (2 tests)
  - `TestLogChatMessage` - log_chat_message behavior (2 tests)
  - `TestLogDocumentEvent` - log_document_event behavior (7 tests)
  - `TestFireAndForget` - Exception handling (4 tests)
  - `TestConcurrentWrites` - Concurrent access (2 tests)
  - `TestTextTruncation` - Text truncation utilities (2 tests)

---

## Implementation Checklist

### Task 1: Create ObservabilityProvider Abstract Base
- [ ] Define abstract interface with all methods
- [ ] Add `name` abstract property
- [ ] Add `enabled` abstract property
- [ ] Document method signatures with type hints

### Task 2: Implement PostgreSQLProvider
- [ ] Initialize with session factory (always enabled)
- [ ] Implement `_get_session()` for dedicated sessions
- [ ] Implement `start_trace()` - create Trace with context
- [ ] Implement `end_trace()` - update duration/metrics
- [ ] Implement `start_span()` - create Span, return UUID
- [ ] Implement `end_span()` - update with **kwargs metrics
- [ ] Implement `log_llm_call()` - create LLM Span
- [ ] Implement `log_chat_message()` - create ChatMessage
- [ ] Implement `log_document_event()` - create DocumentEvent
- [ ] Wrap all operations in try/except with structlog warning

### Task 3: Text Truncation Utilities
- [ ] Truncate error_message to 1000 chars
- [ ] Truncate input_preview/output_preview to 500 chars
- [ ] Handle None values gracefully

### Task 4: Pass Integration Tests
- [ ] All `TestPostgreSQLProviderInterface` tests pass
- [ ] All `TestStartTrace` tests pass
- [ ] All `TestEndTrace` tests pass
- [ ] All `TestStartSpan` tests pass
- [ ] All `TestEndSpan` tests pass
- [ ] All `TestLogLLMCall` tests pass
- [ ] All `TestLogChatMessage` tests pass
- [ ] All `TestLogDocumentEvent` tests pass
- [ ] All `TestFireAndForget` tests pass
- [ ] All `TestConcurrentWrites` tests pass
- [ ] All `TestTextTruncation` tests pass

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `backend/app/services/observability_service.py` | Create | Provider implementation |
| `backend/app/services/__init__.py` | Modify | Register service |

---

## Run Tests

```bash
# Run integration tests (should fail until implemented)
cd backend
.venv/bin/pytest tests/integration/test_observability_provider.py -v

# Run specific test class
.venv/bin/pytest tests/integration/test_observability_provider.py::TestStartTrace -v

# Run with database container
DOCKER_HOST=unix:///home/tungmv/.docker/desktop/docker.sock \
TESTCONTAINERS_RYUK_DISABLED=true \
.venv/bin/pytest tests/integration/test_observability_provider.py -v
```

---

## Key Implementation Patterns

### Fire-and-Forget Pattern
```python
async def start_trace(self, ctx, name, operation_type, metadata=None):
    try:
        async with self._get_session() as session:
            trace = Trace(...)
            session.add(trace)
            await session.commit()
            ctx.db_trace_id = trace.id
    except Exception as e:
        logger.warning("postgresql_start_trace_failed", error=str(e))
```

### Type-Specific Metrics via kwargs
```python
async def end_span(self, span_id, status, duration_ms, **metrics):
    values = {"status": status, "duration_ms": duration_ms}
    for key, value in metrics.items():
        if hasattr(Span, key):
            values[key] = value
    # Update span with values
```

---

## Definition of Done

- [ ] All integration tests pass
- [ ] Fire-and-forget verified (no exceptions propagate)
- [ ] Concurrent writes work correctly
- [ ] Text truncation works correctly
- [ ] Code review completed
- [ ] No ruff/type errors

---

## Notes

- PostgreSQLProvider is ALWAYS enabled (no config toggle)
- Uses dedicated session factory for isolation
- All timestamps in UTC
- Duration calculated from started_at to now
- Provider errors logged via structlog, never propagated
