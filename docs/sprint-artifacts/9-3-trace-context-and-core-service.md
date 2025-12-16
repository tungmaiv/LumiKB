# Story 9.3: TraceContext & Core Service

Status: ready-for-dev

## Story

As a **developer**,
I want **a TraceContext class for distributed trace propagation and an ObservabilityService facade for unified observability operations**,
so that **I can instrument application code with consistent tracing that fans out to all registered providers**.

## Acceptance Criteria

1. `TraceContext` holds W3C-compliant trace_id (32 hex chars) and span_id (16 hex chars) with proper generation utilities
2. `TraceContext.child_context()` creates nested context for child spans with parent reference
3. `ObservabilityService` follows singleton pattern via `get_instance()` class method
4. Service automatically registers PostgreSQL provider (always) and LangFuse provider (if configured)
5. `start_trace()` creates TraceContext and fans out to all enabled providers
6. `end_trace()` fans out completion with status, error info, and aggregated metrics to all providers
7. `span()` async context manager handles automatic timing, error capture, and cleanup
8. All provider failures are logged via structlog but never propagate to callers (fail-safe)
9. Unit tests verify trace context hierarchy and ID generation
10. Integration test demonstrates end-to-end trace flow with PostgreSQL provider

## Tasks / Subtasks

- [ ] Task 1: Implement TraceContext class (AC: #1, #2)
  - [ ] Subtask 1.1: Create `generate_trace_id()` function (32 hex via secrets.token_hex(16))
  - [ ] Subtask 1.2: Create `generate_span_id()` function (16 hex via secrets.token_hex(8))
  - [ ] Subtask 1.3: Implement TraceContext with trace_id, span_id, parent_span_id, user_id, session_id, kb_id
  - [ ] Subtask 1.4: Add `db_trace_id` field for database ID tracking
  - [ ] Subtask 1.5: Implement `child_context()` method for nested span creation

- [ ] Task 2: Implement ObservabilityService core (AC: #3, #4, #5, #6, #8)
  - [ ] Subtask 2.1: Create singleton pattern with `_instance` class variable
  - [ ] Subtask 2.2: Implement `get_instance()` class method with lazy initialization
  - [ ] Subtask 2.3: Register PostgreSQLProvider in constructor
  - [ ] Subtask 2.4: Conditionally register LangFuseProvider based on configuration
  - [ ] Subtask 2.5: Implement `start_trace()` - create context, fan out to providers
  - [ ] Subtask 2.6: Implement `end_trace()` - fan out with metrics to all providers
  - [ ] Subtask 2.7: Wrap all provider calls in try/except with structlog warning

- [ ] Task 3: Implement span context manager (AC: #7, #8)
  - [ ] Subtask 3.1: Create `span()` async context manager method
  - [ ] Subtask 3.2: Start span in all providers, collect span IDs
  - [ ] Subtask 3.3: Track start time with `time.monotonic()`
  - [ ] Subtask 3.4: Capture exceptions for error status
  - [ ] Subtask 3.5: Calculate duration_ms on exit
  - [ ] Subtask 3.6: End span in all providers with status and duration
  - [ ] Subtask 3.7: Return PostgreSQL span_id as primary reference

- [ ] Task 4: Implement additional service methods (AC: #8)
  - [ ] Subtask 4.1: Implement `log_llm_call()` - fan out to all providers
  - [ ] Subtask 4.2: Implement `log_chat_message()` - fan out to all providers
  - [ ] Subtask 4.3: Implement `log_document_event()` - fan out to all providers

- [ ] Task 5: Write unit tests (AC: #9)
  - [ ] Subtask 5.1: Test trace_id generation produces 32 hex chars
  - [ ] Subtask 5.2: Test span_id generation produces 16 hex chars
  - [ ] Subtask 5.3: Test TraceContext initialization and field access
  - [ ] Subtask 5.4: Test child_context preserves trace_id, sets new span_id, links parent
  - [ ] Subtask 5.5: Test get_instance returns same instance on multiple calls

- [ ] Task 6: Write integration tests (AC: #10)
  - [ ] Subtask 6.1: Test complete trace flow: start_trace -> span -> end_trace
  - [ ] Subtask 6.2: Verify trace record in database after start_trace
  - [ ] Subtask 6.3: Verify span record with timing after span context manager
  - [ ] Subtask 6.4: Verify trace status and metrics after end_trace
  - [ ] Subtask 6.5: Test nested spans with parent references
  - [ ] Subtask 6.6: Test error capture in span context manager

## Dev Notes

### Architecture Patterns

- **Singleton Service**: ObservabilityService.get_instance() for global access
- **Provider Registry**: List of enabled providers for fan-out operations
- **Context Manager Pattern**: `async with obs.span()` for automatic resource management
- **Fail-Safe Design**: Provider errors never impact application flow

### Key Technical Decisions

- **W3C Trace Context Compliance**: 32-hex trace_id, 16-hex span_id per OpenTelemetry spec
- **Monotonic Timing**: Use `time.monotonic()` for accurate duration measurement
- **Primary Span ID**: Return PostgreSQL span ID from context manager for database references
- **Lazy Provider Init**: LangFuse provider only initialized if credentials configured

### Source Tree Components

```
backend/
├── app/services/
│   └── observability_service.py    # TraceContext, ObservabilityService, providers
├── tests/unit/
│   └── test_trace_context.py       # New: TraceContext unit tests
└── tests/integration/
    └── test_observability_flow.py  # New: End-to-end trace flow tests
```

### Usage Example

```python
# Start trace
obs = ObservabilityService.get_instance()
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
    # span automatically timed and closed

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
await obs.end_trace(ctx, status="success", total_tokens=1500)
```

### Testing Standards

- Mock providers for unit tests to verify fan-out behavior
- Use real PostgreSQLProvider for integration tests
- Test error scenarios by injecting exceptions
- Verify timing accuracy with controlled sleep intervals

### Project Structure Notes

- All observability code in single file for cohesion: `observability_service.py`
- TraceContext is a simple dataclass-like class (not actual dataclass for flexibility)
- Follow existing service patterns from `app/services/search_service.py`

### Configuration Dependencies

```python
# Required settings in app/core/config.py
observability_enabled: bool = True  # Always on
langfuse_enabled: bool = False
langfuse_public_key: str | None = None
langfuse_secret_key: str | None = None
langfuse_host: str | None = None
```

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#TraceContext lines 764-794]
- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#ObservabilityService lines 1331-1610]
- [Source: docs/epics/epic-9-observability.md#Key Features]

## Dev Agent Record

### Context Reference

- [9-3-trace-context-and-core-service.context.xml](9-3-trace-context-and-core-service.context.xml)

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-14 | Story drafted | Claude (SM Agent) |
