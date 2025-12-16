# Story 9.2: PostgreSQL Provider Implementation

Status: ready-for-dev

## Story

As a **developer**,
I want **a PostgreSQL-based observability provider that stores all traces, spans, and events to the database**,
so that **the system has always-on internal observability storage that never blocks application flow**.

## Acceptance Criteria

1. `PostgreSQLProvider` class implements `ObservabilityProvider` abstract interface
2. `start_trace()` creates Trace record with all context fields (trace_id, user_id, session_id, kb_id, operation_type)
3. `end_trace()` updates Trace with duration_ms, status, error fields, and aggregated token/cost metrics
4. `start_span()` creates Span record with parent context and returns database UUID for reference
5. `end_span()` updates Span with duration_ms, status, and type-specific metrics (LLM, embedding, retrieval, etc.)
6. `log_llm_call()` creates Span with LLM-specific fields (model, tokens, cost, temperature, input/output preview)
7. `log_chat_message()` creates ChatMessage record with role, content, turn_number, sources, and citations
8. `log_document_event()` creates DocumentEvent record with event_type, status, and step-specific metrics
9. All methods are fire-and-forget: catch and log exceptions without propagating them to callers
10. Integration tests verify data persistence for all provider methods

## Tasks / Subtasks

- [ ] Task 1: Create ObservabilityProvider abstract base class (AC: #1)
  - [ ] Subtask 1.1: Define abstract interface with all required methods
  - [ ] Subtask 1.2: Add `name` and `enabled` abstract properties
  - [ ] Subtask 1.3: Document method signatures with type hints and docstrings

- [ ] Task 2: Implement PostgreSQLProvider class (AC: #2, #3, #4, #5, #6, #7, #8, #9)
  - [ ] Subtask 2.1: Initialize with session factory and enabled flag (always True)
  - [ ] Subtask 2.2: Implement `_get_session()` for dedicated session management
  - [ ] Subtask 2.3: Implement `start_trace()` - create Trace with context fields
  - [ ] Subtask 2.4: Implement `end_trace()` - update with duration calculation and metrics
  - [ ] Subtask 2.5: Implement `start_span()` - create Span, return database ID
  - [ ] Subtask 2.6: Implement `end_span()` - update with type-specific metrics via **kwargs
  - [ ] Subtask 2.7: Implement `log_llm_call()` - create Span with LLM fields, auto-generate span_id
  - [ ] Subtask 2.8: Implement `log_chat_message()` - create ChatMessage, validate required context
  - [ ] Subtask 2.9: Implement `log_document_event()` - create DocumentEvent with metrics
  - [ ] Subtask 2.10: Wrap all database operations in try/except with structlog warning

- [ ] Task 3: Add text truncation utilities (AC: #9)
  - [ ] Subtask 3.1: Truncate error_message to 1000 chars
  - [ ] Subtask 3.2: Truncate input_preview/output_preview to 500 chars
  - [ ] Subtask 3.3: Handle None values gracefully

- [ ] Task 4: Write integration tests (AC: #10)
  - [ ] Subtask 4.1: Test start_trace creates record with correct fields
  - [ ] Subtask 4.2: Test end_trace updates status and calculates duration
  - [ ] Subtask 4.3: Test start_span/end_span lifecycle
  - [ ] Subtask 4.4: Test log_llm_call persists all LLM metrics
  - [ ] Subtask 4.5: Test log_chat_message with and without sources/citations
  - [ ] Subtask 4.6: Test log_document_event for all event types (upload, parse, chunk, embed, index)
  - [ ] Subtask 4.7: Test fire-and-forget: verify exception logging without propagation
  - [ ] Subtask 4.8: Test concurrent writes don't block each other

## Dev Notes

### Architecture Patterns

- **Fire-and-Forget**: All database operations catch exceptions and log warnings via structlog
- **Dedicated Sessions**: Use separate session factory to avoid blocking request sessions
- **Atomic Writes**: Each method uses its own session context for isolation
- **Type-Specific Metrics**: Use `**kwargs` pattern to pass type-specific span metrics

### Key Technical Decisions

- **Always Enabled**: PostgreSQLProvider is always active (no config toggle)
- **Session Factory Pattern**: Accept session factory in constructor for testability
- **UTC Timestamps**: Use `datetime.utcnow()` for all timing calculations
- **Duration Calculation**: Calculate `duration_ms` on `end_trace/end_span` from started_at

### Source Tree Components

```
backend/
├── app/services/
│   ├── __init__.py                          # Register new service
│   └── observability_service.py             # New: Provider and service implementation
└── tests/integration/
    └── test_observability_provider.py       # New: Provider integration tests
```

### Implementation Notes

```python
# Session management pattern
async def start_trace(self, ctx, name, operation_type, metadata=None):
    try:
        async with self._get_session() as session:
            trace = Trace(...)
            session.add(trace)
            await session.commit()
            ctx.db_trace_id = trace.id
    except Exception as e:
        logger.warning("postgresql_start_trace_failed", error=str(e))

# Type-specific metrics via kwargs
async def end_span(self, span_id, status, duration_ms, **metrics):
    values = {"status": status, "duration_ms": duration_ms, ...}
    for key, value in metrics.items():
        if hasattr(Span, key):
            values[key] = value
```

### Testing Standards

- Use `conftest.py` fixtures for async session setup
- Test with actual PostgreSQL transactions (use testcontainers or test database)
- Verify data integrity by reading back written records
- Test exception handling by injecting database errors

### Project Structure Notes

- Provider class goes in `app/services/observability_service.py` alongside service
- Follow existing service patterns from `app/services/kb_service.py`
- Use structlog for all logging (existing pattern in codebase)

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#5.1 ObservabilityService Interface]
- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#PostgreSQLProvider lines 909-1127]
- [Source: docs/epics/epic-9-observability.md#Design Principles]

## Dev Agent Record

### Context Reference

- [9-2-postgresql-provider-implementation.context.xml](9-2-postgresql-provider-implementation.context.xml)

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-14 | Story drafted | Claude (SM Agent) |
