# ATDD Checklist: Story 9-3 - TraceContext & Core Service

**Story ID:** 9-3
**Title:** TraceContext & Core Service
**Generated:** 2025-12-14
**Agent:** TEA (Master Test Architect)

---

## Test Summary

| Test Level | Test Count | Status |
|------------|------------|--------|
| Unit | 27 | 🔴 Failing (Not Implemented) |
| Integration | 14 | 🔴 Failing (Not Implemented) |
| E2E | 0 | N/A |

---

## Acceptance Criteria Coverage

| AC# | Description | Test Type | Test Class | Status |
|-----|-------------|-----------|------------|--------|
| 1 | W3C trace_id (32 hex) and span_id (16 hex) | Unit | TestTraceIdGeneration, TestSpanIdGeneration | 🔴 |
| 2 | child_context() creates nested context | Unit | TestTraceContextChildContext | 🔴 |
| 3 | Singleton pattern via get_instance() | Unit | TestObservabilityServiceSingleton | 🔴 |
| 4 | Auto-registers PostgreSQL + LangFuse (if configured) | Unit | TestObservabilityServiceProviderRegistration | 🔴 |
| 5 | start_trace() fans out to all providers | Unit/Integration | TestObservabilityServiceStartTrace | 🔴 |
| 6 | end_trace() fans out with metrics | Unit | TestObservabilityServiceEndTrace | 🔴 |
| 7 | span() context manager with timing/error capture | Integration | TestSpanTimingAccuracy, TestSpanErrorCapture | 🔴 |
| 8 | Provider failures logged, never propagate | Unit | TestObservabilityServiceFailSafe | 🔴 |
| 9 | Unit tests verify context hierarchy and IDs | Unit | test_trace_context.py | 🔴 |
| 10 | Integration test demonstrates trace flow | Integration | TestCompleteTraceFlow | 🔴 |

---

## Test Files Created

### Unit Tests
- **File:** `backend/tests/unit/test_trace_context.py`
- **Classes:**
  - `TestTraceIdGeneration` - 32-hex trace ID validation (4 tests)
  - `TestSpanIdGeneration` - 16-hex span ID validation (3 tests)
  - `TestTraceContextInitialization` - TraceContext field access (3 tests)
  - `TestTraceContextChildContext` - Child context hierarchy (5 tests)
  - `TestObservabilityServiceSingleton` - Singleton pattern (3 tests)
  - `TestObservabilityServiceProviderRegistration` - Provider registration (3 tests)
  - `TestObservabilityServiceStartTrace` - start_trace fanout (2 tests)
  - `TestObservabilityServiceEndTrace` - end_trace fanout (2 tests)
  - `TestObservabilityServiceFailSafe` - Exception handling (3 tests)

### Integration Tests
- **File:** `backend/tests/integration/test_observability_flow.py`
- **Classes:**
  - `TestCompleteTraceFlow` - Full trace lifecycle (4 tests)
  - `TestNestedSpans` - Span hierarchy with parents (2 tests)
  - `TestSpanTimingAccuracy` - Accurate duration measurement (2 tests)
  - `TestSpanErrorCapture` - Exception capture in spans (3 tests)
  - `TestSpanReturnsPrimaryId` - PostgreSQL span ID return (1 test)
  - `TestDocumentProcessingFlow` - Document tracing (1 test)
  - `TestProviderFanout` - Provider fanout behavior (2 tests)

---

## Implementation Checklist

### Task 1: Implement TraceContext Class
- [ ] Create `generate_trace_id()` (32 hex via secrets.token_hex(16))
- [ ] Create `generate_span_id()` (16 hex via secrets.token_hex(8))
- [ ] Implement TraceContext with trace_id, span_id, parent_span_id
- [ ] Add user_id, session_id, kb_id fields
- [ ] Add db_trace_id field for database ID tracking
- [ ] Implement `child_context()` method

### Task 2: Implement ObservabilityService Core
- [ ] Create singleton with `_instance` class variable
- [ ] Implement `get_instance()` class method
- [ ] Register PostgreSQLProvider in constructor
- [ ] Conditionally register LangFuseProvider
- [ ] Implement `start_trace()` with provider fanout
- [ ] Implement `end_trace()` with metrics fanout
- [ ] Wrap provider calls in try/except with structlog

### Task 3: Implement span() Context Manager
- [ ] Create `span()` async context manager
- [ ] Start span in all providers, collect IDs
- [ ] Track start time with time.monotonic()
- [ ] Capture exceptions for error status
- [ ] Calculate duration_ms on exit
- [ ] End span in all providers
- [ ] Return PostgreSQL span_id as primary

### Task 4: Implement Additional Methods
- [ ] Implement `log_llm_call()` with fanout
- [ ] Implement `log_chat_message()` with fanout
- [ ] Implement `log_document_event()` with fanout

### Task 5: Pass Unit Tests
- [ ] All `TestTraceIdGeneration` tests pass
- [ ] All `TestSpanIdGeneration` tests pass
- [ ] All `TestTraceContextInitialization` tests pass
- [ ] All `TestTraceContextChildContext` tests pass
- [ ] All `TestObservabilityServiceSingleton` tests pass
- [ ] All `TestObservabilityServiceProviderRegistration` tests pass
- [ ] All `TestObservabilityServiceStartTrace` tests pass
- [ ] All `TestObservabilityServiceEndTrace` tests pass
- [ ] All `TestObservabilityServiceFailSafe` tests pass

### Task 6: Pass Integration Tests
- [ ] All `TestCompleteTraceFlow` tests pass
- [ ] All `TestNestedSpans` tests pass
- [ ] All `TestSpanTimingAccuracy` tests pass
- [ ] All `TestSpanErrorCapture` tests pass
- [ ] All `TestSpanReturnsPrimaryId` tests pass
- [ ] All `TestDocumentProcessingFlow` tests pass
- [ ] All `TestProviderFanout` tests pass

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `backend/app/services/observability_service.py` | Create/Modify | TraceContext + ObservabilityService |
| `backend/app/core/config.py` | Modify | Add LangFuse settings |

---

## Configuration Settings to Add

```python
# In app/core/config.py
class Settings(BaseSettings):
    # Observability
    observability_enabled: bool = True  # Always on

    # LangFuse (optional)
    langfuse_enabled: bool = False
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None
```

---

## Run Tests

```bash
# Run unit tests
cd backend
.venv/bin/pytest tests/unit/test_trace_context.py -v

# Run integration tests
DOCKER_HOST=unix:///home/tungmv/.docker/desktop/docker.sock \
TESTCONTAINERS_RYUK_DISABLED=true \
.venv/bin/pytest tests/integration/test_observability_flow.py -v

# Run all observability tests
.venv/bin/pytest tests/unit/test_trace_context.py tests/integration/test_observability_flow.py -v
```

---

## Usage Example

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

---

## Definition of Done

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Trace ID generation produces 32 hex chars
- [ ] Span ID generation produces 16 hex chars
- [ ] Child contexts link to parents correctly
- [ ] Singleton returns same instance
- [ ] Provider failures don't propagate
- [ ] Span timing is accurate (±50ms tolerance)
- [ ] Code review completed
- [ ] No ruff/type errors

---

## Notes

- W3C Trace Context compliance for future OpenTelemetry compatibility
- Use `time.monotonic()` for accurate duration measurement
- Return PostgreSQL span_id from context manager for DB references
- LangFuse provider only initialized if credentials configured
- All provider errors logged via structlog, never propagated
