# Story 9-11: LangFuse Provider Implementation

Status: ready-for-dev

## Story

As an **Admin/DevOps engineer**,
I want to integrate LangFuse as an optional external observability provider,
so that I can leverage advanced LLM analytics and visualization capabilities when needed.

## Acceptance Criteria

1. **AC1:** `LangFuseProvider` implements `ObservabilityProvider` interface
2. **AC2:** Provider disabled if `langfuse_public_key` not configured
3. **AC3:** `start_trace()` creates LangFuse trace with user_id, session_id
4. **AC4:** `log_llm_call()` creates LangFuse generation with usage metrics
5. **AC5:** Document events logged as LangFuse events with metadata
6. **AC6:** Provider sync status tracked in `provider_sync_status` table
7. **AC7:** All LangFuse calls are async and non-blocking
8. **AC8:** SDK errors caught and logged (fire-and-forget)
9. **AC9:** Flush called on trace end to ensure data sent
10. **AC10:** Integration test with LangFuse mock server

## Tasks / Subtasks

- [ ] Task 1: Implement LangFuseProvider class (AC: 1, 2)
  - [ ] Create `backend/app/services/langfuse_provider.py`
  - [ ] Implement `ObservabilityProvider` interface methods
  - [ ] Add configuration check for enabling/disabling provider
  - [ ] Initialize LangFuse SDK client when credentials available

- [ ] Task 2: Implement trace operations (AC: 3, 9)
  - [ ] Implement `start_trace()` with LangFuse trace creation
  - [ ] Pass user_id, session_id, kb_id to trace metadata
  - [ ] Implement `end_trace()` with metadata update
  - [ ] Call `flush()` on trace completion

- [ ] Task 3: Implement LLM call logging (AC: 4)
  - [ ] Implement `log_llm_call()` with LangFuse generation
  - [ ] Include model, usage metrics (prompt/completion tokens)
  - [ ] Include latency_ms and cost_usd in metadata
  - [ ] Include temperature in model_parameters

- [ ] Task 4: Implement span operations (AC: 5)
  - [ ] Implement `start_span()` with LangFuse span creation
  - [ ] Implement `end_span()` with span completion
  - [ ] Implement `log_document_event()` as LangFuse event
  - [ ] Implement `log_chat_message()` mapping

- [ ] Task 5: Implement sync status tracking (AC: 6)
  - [ ] Create/update `provider_sync_status` records
  - [ ] Track sync_status (pending/synced/failed)
  - [ ] Store external_id from LangFuse response
  - [ ] Track retry_count for failures

- [ ] Task 6: Implement fire-and-forget pattern (AC: 7, 8)
  - [ ] Wrap all LangFuse calls in try/except
  - [ ] Use structlog for error logging
  - [ ] Ensure no exceptions propagate to caller
  - [ ] Verify non-blocking behavior

- [ ] Task 7: Add configuration settings
  - [ ] Add `LANGFUSE_ENABLED` to config.py
  - [ ] Add `LANGFUSE_PUBLIC_KEY` to config.py
  - [ ] Add `LANGFUSE_SECRET_KEY` to config.py
  - [ ] Add `LANGFUSE_HOST` to config.py (default: cloud)

- [ ] Task 8: Write tests (AC: 10)
  - [ ] Unit tests for LangFuseProvider methods
  - [ ] Mock LangFuse SDK for unit tests
  - [ ] Integration test with mock LangFuse server
  - [ ] Test disabled provider behavior
  - [ ] Test error handling scenarios

## Dev Notes

### Learnings from Previous Story

**Story 9-10 (Document Timeline UI)** established key patterns:
- **Polling Pattern:** 2-second auto-refresh while processing - applicable to LangFuse sync status monitoring
- **Status Icon Patterns:** Consistent status visualization (pending/in-progress/completed/failed) - reuse for provider sync status
- **Component Composition:** Timeline composed of step components - similar pattern for provider status dashboard
- **Source:** [stories/9-10-document-timeline-ui.md#Dev Notes]

### Dependencies

- **Story 9-2 (PostgreSQL Provider):** `ObservabilityProvider` interface must exist - LangFuseProvider implements same interface
- **Story 9-3 (TraceContext & Core Service):** `ObservabilityService` provider registry must be implemented for LangFuseProvider registration

### Architecture Patterns

- **Fire-and-Forget Pattern:** All LangFuse operations must be non-blocking and fail silently
- **Provider Registry Pattern:** LangFuseProvider is registered alongside PostgreSQLProvider
- **Configuration-Based Enablement:** Provider only activates when credentials configured
- **Dual Write:** Data goes to both PostgreSQL (always) and LangFuse (optional)

### Implementation Details

```python
# LangFuse SDK initialization
from langfuse import Langfuse

client = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host or "https://cloud.langfuse.com",
)

# Trace creation
trace = client.trace(
    id=ctx.trace_id,
    name=name,
    user_id=str(ctx.user_id) if ctx.user_id else None,
    session_id=ctx.session_id,
    metadata={"operation_type": operation_type, "kb_id": str(ctx.kb_id)},
)

# LLM generation logging
trace.generation(
    name=f"llm.{model}",
    model=model,
    usage={
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    },
    model_parameters={"temperature": temperature} if temperature else None,
    metadata={"latency_ms": latency_ms, "cost_usd": float(cost_usd)},
)
```

### Configuration Example

```env
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com  # or self-hosted URL
```

### Dependencies

- `langfuse>=2.0.0` - LangFuse Python SDK (optional dependency)

### Source Tree Components

- `backend/app/services/langfuse_provider.py` - New provider implementation
- `backend/app/services/observability_service.py` - Register provider
- `backend/app/core/config.py` - Add configuration settings
- `backend/app/models/observability.py` - ProviderSyncStatus model (existing)
- `backend/tests/unit/test_langfuse_provider.py` - Unit tests
- `backend/tests/integration/test_langfuse_integration.py` - Integration tests

### Testing Standards

- Mock LangFuse SDK using `unittest.mock` or `pytest-mock`
- Verify fire-and-forget: exceptions don't propagate
- Test disabled state: no SDK calls when not configured
- Integration test: verify sync status tracking

### Project Structure Notes

- Follows existing provider pattern from PostgreSQLProvider
- Configuration follows existing settings pattern in config.py
- Optional dependency pattern matches existing extras in pyproject.toml

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#Phase 4: Advanced Features - Story 9-11 LangFuse Provider Implementation]
- [Source: docs/epics/epic-9-observability.md#Phase 4: Advanced Features (18 points)]
- [Source: docs/architecture.md#monitoring] - Architecture monitoring stack documentation
- [Source: docs/testing-guideline.md] - Testing standards for mocking external SDKs
- LangFuse SDK: https://langfuse.com/docs/sdk/python

## Dev Agent Record

### Context Reference

- [9-11-langfuse-provider-implementation.context.xml](./9-11-langfuse-provider-implementation.context.xml)

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

### File List
