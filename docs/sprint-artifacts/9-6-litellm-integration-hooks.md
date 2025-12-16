# Story 9.6: LiteLLM Integration Hooks

Status: done

## Story

As a **system administrator**,
I want **all LLM calls (embeddings, completions) automatically traced via LiteLLM callbacks with model, tokens, and cost metrics**,
so that **I can monitor LLM usage across the entire application without manual instrumentation of each call site**.

## Acceptance Criteria

1. LiteLLM callback handler implements success_callback and failure_callback hooks
2. Embedding calls automatically create LLM spans with model, input_tokens, dimensions, duration_ms
3. Chat completion calls automatically create LLM spans with model, prompt_tokens, completion_tokens, duration_ms
4. Streaming completions aggregate token counts and create span after stream completes
5. Cost tracking extracts cost_usd from LiteLLM response when available
6. Failed LLM calls log error type and message without exposing prompt content
7. Callback handler uses fire-and-forget pattern - never blocks LLM responses
8. TraceContext passed via LiteLLM metadata for correlation with parent traces
9. Unit tests verify callback creates correct spans for embeddings and completions
10. Integration test demonstrates automatic LLM call tracing through callback

## Tasks / Subtasks

- [ ] Task 1: Create LiteLLM callback handler class (AC: #1, #7)
  - [ ] Subtask 1.1: Create `ObservabilityCallback` class implementing litellm.Callback
  - [ ] Subtask 1.2: Implement `async_log_success_event()` for successful calls
  - [ ] Subtask 1.3: Implement `async_log_failure_event()` for failed calls
  - [ ] Subtask 1.4: Wrap all observability calls in try/except (fire-and-forget)

- [ ] Task 2: Implement embedding call tracing (AC: #2)
  - [ ] Subtask 2.1: Detect embedding calls via call_type or model name
  - [ ] Subtask 2.2: Extract model from response
  - [ ] Subtask 2.3: Extract input_tokens from usage
  - [ ] Subtask 2.4: Extract dimensions from embedding vector length
  - [ ] Subtask 2.5: Calculate duration_ms from start_time and end_time
  - [ ] Subtask 2.6: Log via obs.log_llm_call() with name="embedding"

- [ ] Task 3: Implement chat completion tracing (AC: #3)
  - [ ] Subtask 3.1: Detect completion calls via call_type
  - [ ] Subtask 3.2: Extract model from response
  - [ ] Subtask 3.3: Extract prompt_tokens, completion_tokens from usage
  - [ ] Subtask 3.4: Calculate duration_ms from timing
  - [ ] Subtask 3.5: Log via obs.log_llm_call() with name="chat_completion"

- [ ] Task 4: Implement streaming completion handling (AC: #4)
  - [ ] Subtask 4.1: Detect streaming response via response type or call metadata
  - [ ] Subtask 4.2: Track stream start time in callback state
  - [ ] Subtask 4.3: Aggregate tokens from stream_response_object
  - [ ] Subtask 4.4: Create span after stream completes with aggregated metrics

- [ ] Task 5: Implement cost tracking (AC: #5)
  - [ ] Subtask 5.1: Extract response_cost from LiteLLM response when available
  - [ ] Subtask 5.2: Convert to Decimal for precision
  - [ ] Subtask 5.3: Include cost_usd in span metadata
  - [ ] Subtask 5.4: Handle missing cost gracefully (set to None)

- [ ] Task 6: Implement error tracing (AC: #6)
  - [ ] Subtask 6.1: In failure callback, extract exception type and message
  - [ ] Subtask 6.2: Never include prompt content in error logs
  - [ ] Subtask 6.3: Log via obs.log_llm_call() with status="failed"
  - [ ] Subtask 6.4: Include error_message (sanitized) in span

- [ ] Task 7: Implement trace context propagation (AC: #8)
  - [ ] Subtask 7.1: Accept trace_id in LiteLLM call metadata
  - [ ] Subtask 7.2: Extract trace_id from litellm_params["metadata"]
  - [ ] Subtask 7.3: Use extracted trace_id for log_llm_call correlation
  - [ ] Subtask 7.4: Generate new trace_id if not provided (standalone calls)

- [ ] Task 8: Register callback handler with LiteLLM (AC: #1)
  - [ ] Subtask 8.1: Create singleton callback instance
  - [ ] Subtask 8.2: Register via litellm.callbacks.append() in application startup
  - [ ] Subtask 8.3: Add initialization in main.py lifespan handler
  - [ ] Subtask 8.4: Document callback registration in litellm_client.py

- [ ] Task 9: Update existing LiteLLM calls to pass trace context (AC: #8)
  - [ ] Subtask 9.1: Modify LiteLLMEmbeddingClient.get_embeddings() to accept trace_ctx
  - [ ] Subtask 9.2: Modify chat_completion() to accept trace_ctx
  - [ ] Subtask 9.3: Pass metadata={"trace_id": ctx.trace_id} in LiteLLM calls
  - [ ] Subtask 9.4: Update callers (document_tasks, conversation_service) to pass context

- [ ] Task 10: Write unit tests (AC: #9)
  - [ ] Subtask 10.1: Test callback creates span for embedding call
  - [ ] Subtask 10.2: Test callback creates span for completion call
  - [ ] Subtask 10.3: Test streaming completion aggregates tokens correctly
  - [ ] Subtask 10.4: Test cost extraction when available
  - [ ] Subtask 10.5: Test failure callback logs error correctly
  - [ ] Subtask 10.6: Test trace context propagation via metadata

- [ ] Task 11: Write integration tests (AC: #10)
  - [ ] Subtask 11.1: Test embedding call through LiteLLM creates trace span
  - [ ] Subtask 11.2: Test completion call through LiteLLM creates trace span
  - [ ] Subtask 11.3: Verify span records in database have correct metrics
  - [ ] Subtask 11.4: Test parent trace correlation via metadata

## Dev Notes

### Architecture Patterns

- **Callback Hook Pattern**: LiteLLM calls callbacks after each API call
- **Fire-and-Forget**: Callback exceptions never propagate to caller
- **Metadata Propagation**: Use litellm_params["metadata"] for context passing
- **Singleton Registration**: One callback instance registered at app startup

### Key Technical Decisions

- **Call Type Detection**: Use response.call_type to distinguish embedding vs completion
- **Token Aggregation**: For streaming, track token delta and sum at end
- **Cost Source**: LiteLLM calculates cost from model pricing tables
- **No Prompt Logging**: Prompts may contain sensitive data - never log

### LiteLLM Callback Interface

```python
class ObservabilityCallback(litellm.Callback):
    async def async_log_success_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Called after successful LLM API call."""
        ...

    async def async_log_failure_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Called after failed LLM API call."""
        ...
```

### Source Tree Changes

```
backend/
├── app/
│   ├── integrations/
│   │   ├── litellm_client.py      # Modified: Add trace context support
│   │   └── litellm_callback.py    # New: ObservabilityCallback implementation
│   └── main.py                    # Modified: Register callback at startup
└── tests/
    ├── unit/
    │   └── test_litellm_callback.py    # New: Unit tests
    └── integration/
        └── test_litellm_trace_flow.py  # New: Integration tests
```

### Callback Response Structure

```python
# Embedding response
response_obj = {
    "data": [{"embedding": [...], "index": 0}],
    "model": "text-embedding-3-small",
    "usage": {"prompt_tokens": 100, "total_tokens": 100},
}

# Completion response
response_obj = {
    "choices": [{"message": {"content": "..."}}],
    "model": "gpt-4",
    "usage": {"prompt_tokens": 500, "completion_tokens": 200, "total_tokens": 700},
    "response_cost": 0.025,  # Optional, when cost tracking enabled
}
```

### Usage Example

```python
# In litellm_callback.py
import litellm
from app.services.observability_service import (
    ObservabilityService,
    TraceContext,
    generate_trace_id,
)

class ObservabilityCallback(litellm.Callback):
    def __init__(self):
        self.obs = ObservabilityService.get_instance()

    async def async_log_success_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        try:
            # Extract trace context from metadata
            metadata = kwargs.get("litellm_params", {}).get("metadata", {})
            trace_id = metadata.get("trace_id") or generate_trace_id()

            # Calculate duration
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Detect call type
            call_type = getattr(response_obj, "call_type", "completion")

            if call_type == "embedding":
                await self._log_embedding(trace_id, response_obj, duration_ms)
            else:
                await self._log_completion(trace_id, response_obj, duration_ms)

        except Exception as e:
            # Fire-and-forget - log but don't propagate
            logger.warning("callback_error", error=str(e))

    async def _log_embedding(self, trace_id, response, duration_ms):
        model = getattr(response, "model", "unknown")
        usage = getattr(response, "usage", None)
        input_tokens = usage.prompt_tokens if usage else None

        # Create minimal TraceContext for logging
        ctx = TraceContext(trace_id=trace_id)

        await self.obs.log_llm_call(
            ctx=ctx,
            name="embedding",
            model=model,
            input_tokens=input_tokens,
            duration_ms=duration_ms,
        )

    async def _log_completion(self, trace_id, response, duration_ms):
        model = getattr(response, "model", "unknown")
        usage = getattr(response, "usage", None)
        cost = getattr(response, "response_cost", None)

        ctx = TraceContext(trace_id=trace_id)

        await self.obs.log_llm_call(
            ctx=ctx,
            name="chat_completion",
            model=model,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
            duration_ms=duration_ms,
            metadata={"cost_usd": str(cost)} if cost else None,
        )


# Registration in main.py lifespan
async def lifespan(app: FastAPI):
    # Startup
    from app.integrations.litellm_callback import observability_callback
    litellm.callbacks.append(observability_callback)

    yield

    # Shutdown
    ...
```

### Testing Standards

- Mock LiteLLM response objects for unit tests
- Use real LiteLLM with mock LLM server for integration tests
- Verify database records have correct metrics
- Test both sync and async callback paths

### Configuration Dependencies

No new configuration needed - callbacks are always registered when observability is enabled.

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#LiteLLM Integration]
- [Source: docs/sprint-artifacts/9-3-trace-context-and-core-service.md]
- [Source: backend/app/integrations/litellm_client.py - existing client]
- [LiteLLM Callback Documentation](https://docs.litellm.ai/docs/observability/custom_callback)

## Dev Agent Record

### Context Reference

- [9-6-litellm-integration-hooks.context.xml](9-6-litellm-integration-hooks.context.xml)

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

### Completion Notes List

- 2025-12-15: All 10 ACs implemented and verified. 18 unit tests + 12 integration tests passing. ObservabilityCallback registered via litellm.callbacks, trace context propagation via metadata, fire-and-forget error handling. Code review APPROVED. See: docs/sprint-artifacts/code-review-stories-9-4-9-5-9-6.md

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Story drafted | Claude (SM Agent) |
| 2025-12-15 | Story context XML created and validated | Claude (SM Agent) |
| 2025-12-15 | Status: ready-for-dev | Claude (SM Agent) |
| 2025-12-15 | Status: done - Code review APPROVED, 83 tests passing | Claude (Dev Agent) |
