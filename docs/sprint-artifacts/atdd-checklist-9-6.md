# ATDD Checklist: Story 9-6 LiteLLM Integration Hooks

**Story**: 9-6 LiteLLM Integration Hooks
**Status**: Pre-Implementation (ATDD Phase)
**Generated**: 2025-12-15

## Overview

This ATDD checklist defines acceptance tests for LiteLLM callback integration that automatically traces all LLM calls. Tests verify that embeddings, completions, and streaming responses are captured via LiteLLM callbacks without manual instrumentation.

## Test Environment Requirements

### Required Fixtures
- `test_engine` - PostgreSQL with observability schema
- `db_session` - Async session with rollback
- `mock_litellm_response` - Mock LiteLLM response objects
- `observability_callback` - Registered callback instance

### Required Test Data Factories
```python
from tests.factories import (
    create_trace,
    create_llm_span,
    generate_trace_id,
    generate_span_id,
)
```

### LiteLLM Mock Response Fixtures
```python
@pytest.fixture
def mock_embedding_response():
    """Mock LiteLLM embedding response."""
    return {
        "data": [{"embedding": [0.1] * 1536, "index": 0}],
        "model": "text-embedding-3-small",
        "usage": {"prompt_tokens": 100, "total_tokens": 100},
    }

@pytest.fixture
def mock_completion_response():
    """Mock LiteLLM completion response."""
    return {
        "choices": [{"message": {"content": "Test response"}}],
        "model": "gpt-4",
        "usage": {"prompt_tokens": 500, "completion_tokens": 200, "total_tokens": 700},
        "response_cost": 0.025,
    }
```

---

## Acceptance Criteria Tests

### AC-1: Callback Handler Implements LiteLLM Interface

**Test ID**: `test_callback_implements_litellm_interface`

| Field | Value |
|-------|-------|
| **Description** | LiteLLM callback handler implements success_callback and failure_callback hooks |
| **Given** | ObservabilityCallback class |
| **When** | Inspecting class methods |
| **Then** | Required callback methods exist |
| **Assertions** | - `async_log_success_event()` method exists<br>- `async_log_failure_event()` method exists<br>- Methods accept kwargs, response_obj, start_time, end_time<br>- Class inherits from or implements litellm.Callback |

**Test File**: `backend/tests/unit/test_litellm_callback.py`

---

### AC-2: Embedding Calls Create LLM Spans

**Test ID**: `test_embedding_call_creates_span`

| Field | Value |
|-------|-------|
| **Description** | Embedding calls automatically create LLM spans with model, input_tokens, dimensions, duration_ms |
| **Given** | Mock embedding response from LiteLLM |
| **When** | `async_log_success_event()` called with embedding response |
| **Then** | LLM span created with embedding metrics |
| **Assertions** | - Span created via `obs.log_llm_call()`<br>- `span.name == "embedding"`<br>- `span.model == "text-embedding-3-small"`<br>- `span.input_tokens == 100`<br>- `span.attributes["dimensions"] == 1536`<br>- `span.duration_ms > 0` |

**Test File**: `backend/tests/unit/test_litellm_callback.py`

---

### AC-3: Chat Completion Calls Create LLM Spans

**Test ID**: `test_completion_call_creates_span`

| Field | Value |
|-------|-------|
| **Description** | Chat completion calls automatically create LLM spans with model, prompt_tokens, completion_tokens, duration_ms |
| **Given** | Mock completion response from LiteLLM |
| **When** | `async_log_success_event()` called with completion response |
| **Then** | LLM span created with completion metrics |
| **Assertions** | - Span created via `obs.log_llm_call()`<br>- `span.name == "chat_completion"`<br>- `span.model == "gpt-4"`<br>- `span.input_tokens == 500`<br>- `span.output_tokens == 200`<br>- `span.duration_ms > 0` |

**Test File**: `backend/tests/unit/test_litellm_callback.py`

---

### AC-4: Streaming Completions Aggregate Tokens

**Test ID**: `test_streaming_completion_aggregates_tokens`

| Field | Value |
|-------|-------|
| **Description** | Streaming completions aggregate token counts and create span after stream completes |
| **Given** | Streaming completion response with aggregated usage |
| **When** | `async_log_success_event()` called after stream completes |
| **Then** | Single span created with total tokens |
| **Assertions** | - One span per streaming request (not per chunk)<br>- Token counts reflect final aggregated values<br>- `span.attributes["streaming"] == True`<br>- Duration covers entire stream |

**Test File**: `backend/tests/unit/test_litellm_callback.py`

---

### AC-5: Cost Tracking Extracts cost_usd

**Test ID**: `test_cost_tracking_from_response`

| Field | Value |
|-------|-------|
| **Description** | Cost tracking extracts cost_usd from LiteLLM response when available |
| **Given** | Completion response with `response_cost` field |
| **When** | Callback processes response |
| **Then** | Cost recorded in span metadata |
| **Assertions** | - `span.attributes["cost_usd"] == "0.025"`<br>- Cost stored as string (Decimal precision)<br>- Missing cost handled gracefully (None) |

**Test File**: `backend/tests/unit/test_litellm_callback.py`

---

### AC-6: Failed Calls Log Error Without Prompt

**Test ID**: `test_failure_callback_sanitizes_error`

| Field | Value |
|-------|-------|
| **Description** | Failed LLM calls log error type and message without exposing prompt content |
| **Given** | Failed LLM call with exception |
| **When** | `async_log_failure_event()` called |
| **Then** | Error span created without prompt exposure |
| **Assertions** | - Span with `status="failed"` created<br>- `error_message` contains exception type<br>- `error_message` does NOT contain "prompt"<br>- `error_message` does NOT contain message content<br>- Original exception type preserved |

**Test File**: `backend/tests/unit/test_litellm_callback.py`

---

### AC-7: Fire-and-Forget Pattern Never Blocks

**Test ID**: `test_callback_never_blocks_response`

| Field | Value |
|-------|-------|
| **Description** | Callback handler uses fire-and-forget pattern - never blocks LLM responses |
| **Given** | Callback with simulated slow observability operation |
| **When** | Callback method raises exception |
| **Then** | Exception is caught, logged, not propagated |
| **Assertions** | - No exception propagates from callback<br>- Warning logged when callback fails<br>- LLM response unaffected by callback errors<br>- Callback wrapped in try/except |

**Test File**: `backend/tests/unit/test_litellm_callback.py`

---

### AC-8: Trace Context Propagation via Metadata

**Test ID**: `test_trace_context_from_metadata`

| Field | Value |
|-------|-------|
| **Description** | TraceContext passed via LiteLLM metadata for correlation with parent traces |
| **Given** | LiteLLM call with `metadata={"trace_id": "abc123..."}` |
| **When** | Callback processes response |
| **Then** | Span linked to parent trace |
| **Assertions** | - Span uses `trace_id` from metadata<br>- Extracted from `kwargs["litellm_params"]["metadata"]`<br>- Missing trace_id generates new one<br>- Standalone calls work without metadata |

**Test File**: `backend/tests/unit/test_litellm_callback.py`

---

### AC-9: Unit Tests for Callback Spans

**Test ID**: `test_unit_callback_span_creation`

| Field | Value |
|-------|-------|
| **Description** | Unit tests verify callback creates correct spans for embeddings and completions |
| **Test Cases** | - `test_embedding_response_creates_embedding_span`<br>- `test_completion_response_creates_completion_span`<br>- `test_streaming_response_aggregates_tokens`<br>- `test_cost_extraction_when_available`<br>- `test_failure_callback_logs_error`<br>- `test_trace_context_propagation` |
| **Approach** | Mock ObservabilityService, call callback directly with mock responses |

**Test File**: `backend/tests/unit/test_litellm_callback.py`

---

### AC-10: Integration Test Automatic LLM Tracing

**Test ID**: `test_integration_automatic_llm_tracing`

| Field | Value |
|-------|-------|
| **Description** | Integration test demonstrates automatic LLM call tracing through callback |
| **Given** | Callback registered with LiteLLM, real database |
| **When** | LLM call made via LiteLLM client |
| **Then** | Span appears in database without manual instrumentation |
| **Assertions** | - Span in `obs_spans` table<br>- `span.span_type == "llm"`<br>- Token counts match response<br>- Model name recorded<br>- Duration reasonable |

**Test File**: `backend/tests/integration/test_litellm_trace_flow.py`

---

## Unit Test Specifications

### File: `backend/tests/unit/test_litellm_callback.py`

```python
"""Unit tests for LiteLLM observability callback.

Tests verify callback creates correct spans for embeddings and completions
using mocked ObservabilityService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from tests.factories import generate_trace_id


@pytest.fixture
def mock_embedding_response():
    """Mock LiteLLM embedding response object."""
    response = MagicMock()
    response.call_type = "embedding"
    response.model = "text-embedding-3-small"
    response.usage = MagicMock(prompt_tokens=100, total_tokens=100)
    response.data = [MagicMock(embedding=[0.1] * 1536)]
    return response


@pytest.fixture
def mock_completion_response():
    """Mock LiteLLM completion response object."""
    response = MagicMock()
    response.call_type = "completion"
    response.model = "gpt-4"
    response.usage = MagicMock(
        prompt_tokens=500,
        completion_tokens=200,
        total_tokens=700,
    )
    response.response_cost = 0.025
    return response


@pytest.fixture
def mock_kwargs_with_trace():
    """Mock kwargs with trace context in metadata."""
    trace_id = generate_trace_id()
    return {
        "litellm_params": {
            "metadata": {"trace_id": trace_id},
        },
    }


class TestCallbackInterface:
    """Tests for callback class structure."""

    def test_callback_has_success_method(self):
        """Callback has async_log_success_event method."""
        pass

    def test_callback_has_failure_method(self):
        """Callback has async_log_failure_event method."""
        pass


class TestEmbeddingSpan:
    """Tests for embedding call span creation."""

    @pytest.mark.asyncio
    async def test_embedding_creates_span_with_name(
        self,
        mock_embedding_response,
        mock_kwargs_with_trace,
    ):
        """Embedding call creates span with name='embedding'."""
        pass

    @pytest.mark.asyncio
    async def test_embedding_extracts_model(
        self,
        mock_embedding_response,
        mock_kwargs_with_trace,
    ):
        """Embedding span includes correct model name."""
        pass

    @pytest.mark.asyncio
    async def test_embedding_extracts_input_tokens(
        self,
        mock_embedding_response,
        mock_kwargs_with_trace,
    ):
        """Embedding span includes input_tokens from usage."""
        pass

    @pytest.mark.asyncio
    async def test_embedding_extracts_dimensions(
        self,
        mock_embedding_response,
        mock_kwargs_with_trace,
    ):
        """Embedding span includes dimensions from vector length."""
        pass

    @pytest.mark.asyncio
    async def test_embedding_calculates_duration(
        self,
        mock_embedding_response,
        mock_kwargs_with_trace,
    ):
        """Embedding span calculates duration_ms from timestamps."""
        pass


class TestCompletionSpan:
    """Tests for completion call span creation."""

    @pytest.mark.asyncio
    async def test_completion_creates_span_with_name(
        self,
        mock_completion_response,
        mock_kwargs_with_trace,
    ):
        """Completion call creates span with name='chat_completion'."""
        pass

    @pytest.mark.asyncio
    async def test_completion_extracts_token_counts(
        self,
        mock_completion_response,
        mock_kwargs_with_trace,
    ):
        """Completion span includes prompt_tokens and completion_tokens."""
        pass


class TestStreamingCompletion:
    """Tests for streaming completion handling."""

    @pytest.mark.asyncio
    async def test_streaming_aggregates_final_tokens(self):
        """Streaming response uses final aggregated token counts."""
        pass

    @pytest.mark.asyncio
    async def test_streaming_single_span_per_request(self):
        """One span created for entire streaming request."""
        pass


class TestCostTracking:
    """Tests for cost extraction."""

    @pytest.mark.asyncio
    async def test_cost_extracted_when_present(
        self,
        mock_completion_response,
        mock_kwargs_with_trace,
    ):
        """Cost extracted from response_cost field."""
        pass

    @pytest.mark.asyncio
    async def test_cost_none_when_missing(self):
        """Missing cost handled gracefully as None."""
        pass

    @pytest.mark.asyncio
    async def test_cost_stored_as_string(
        self,
        mock_completion_response,
        mock_kwargs_with_trace,
    ):
        """Cost stored as string for Decimal precision."""
        pass


class TestFailureCallback:
    """Tests for failure callback."""

    @pytest.mark.asyncio
    async def test_failure_creates_failed_span(self):
        """Failure callback creates span with status='failed'."""
        pass

    @pytest.mark.asyncio
    async def test_failure_excludes_prompt_content(self):
        """Error message does not contain prompt or message content."""
        pass

    @pytest.mark.asyncio
    async def test_failure_includes_exception_type(self):
        """Error message includes exception class name."""
        pass


class TestFireAndForget:
    """Tests for fire-and-forget pattern."""

    @pytest.mark.asyncio
    async def test_observability_error_not_propagated(self):
        """Errors in observability calls are caught, not propagated."""
        pass

    @pytest.mark.asyncio
    async def test_warning_logged_on_callback_error(self):
        """Warning logged when callback fails."""
        pass


class TestTraceContextPropagation:
    """Tests for trace context extraction from metadata."""

    @pytest.mark.asyncio
    async def test_trace_id_extracted_from_metadata(
        self,
        mock_completion_response,
        mock_kwargs_with_trace,
    ):
        """Trace ID extracted from litellm_params.metadata."""
        pass

    @pytest.mark.asyncio
    async def test_new_trace_id_when_missing(
        self,
        mock_completion_response,
    ):
        """New trace ID generated when not in metadata."""
        pass

    @pytest.mark.asyncio
    async def test_standalone_calls_work(
        self,
        mock_completion_response,
    ):
        """Calls without metadata still create spans."""
        pass
```

---

## Integration Test Specifications

### File: `backend/tests/integration/test_litellm_trace_flow.py`

```python
"""Integration tests for LiteLLM callback trace flow.

Tests verify automatic LLM tracing through registered callback
with real PostgreSQL provider.
"""
import pytest
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import Span
from tests.factories import generate_trace_id


@pytest.fixture
async def registered_callback():
    """Ensure callback is registered with LiteLLM."""
    # Registration happens in app startup
    # This fixture may verify registration
    pass


class TestAutomaticLLMTracing:
    """Integration tests for automatic LLM call tracing."""

    @pytest.mark.asyncio
    async def test_embedding_call_traced_automatically(
        self,
        db_session: AsyncSession,
        registered_callback,
    ):
        """Embedding call via LiteLLM creates span in database."""
        pass

    @pytest.mark.asyncio
    async def test_completion_call_traced_automatically(
        self,
        db_session: AsyncSession,
        registered_callback,
    ):
        """Completion call via LiteLLM creates span in database."""
        pass

    @pytest.mark.asyncio
    async def test_span_has_correct_metrics(
        self,
        db_session: AsyncSession,
        registered_callback,
    ):
        """Traced span has correct token counts and model."""
        pass


class TestTraceCorrelation:
    """Tests for trace correlation via metadata."""

    @pytest.mark.asyncio
    async def test_span_linked_to_parent_trace(
        self,
        db_session: AsyncSession,
        registered_callback,
    ):
        """LLM span linked to parent trace via metadata."""
        pass

    @pytest.mark.asyncio
    async def test_multiple_calls_share_trace(
        self,
        db_session: AsyncSession,
        registered_callback,
    ):
        """Multiple LLM calls with same trace_id linked together."""
        pass


class TestCallbackRegistration:
    """Tests for callback registration lifecycle."""

    @pytest.mark.asyncio
    async def test_callback_registered_at_startup(self):
        """Callback registered in litellm.callbacks at app startup."""
        pass

    @pytest.mark.asyncio
    async def test_singleton_callback_instance(self):
        """Only one callback instance registered."""
        pass
```

---

## Test Data Factory Requirements

### New Factory Functions

```python
# In a new file or extend observability_factory.py

def create_litellm_embedding_response(
    model: str = "text-embedding-3-small",
    input_tokens: int = 100,
    dimensions: int = 1536,
) -> MagicMock:
    """Create mock LiteLLM embedding response."""
    response = MagicMock()
    response.call_type = "embedding"
    response.model = model
    response.usage = MagicMock(prompt_tokens=input_tokens, total_tokens=input_tokens)
    response.data = [MagicMock(embedding=[0.1] * dimensions)]
    return response


def create_litellm_completion_response(
    model: str = "gpt-4",
    prompt_tokens: int = 500,
    completion_tokens: int = 200,
    cost: float | None = 0.025,
) -> MagicMock:
    """Create mock LiteLLM completion response."""
    response = MagicMock()
    response.call_type = "completion"
    response.model = model
    response.usage = MagicMock(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    response.response_cost = cost
    return response


def create_litellm_kwargs(
    trace_id: str | None = None,
    **extra_metadata,
) -> dict:
    """Create mock LiteLLM kwargs with optional trace context."""
    metadata = {}
    if trace_id:
        metadata["trace_id"] = trace_id
    metadata.update(extra_metadata)

    return {
        "litellm_params": {
            "metadata": metadata,
        } if metadata else {},
    }
```

---

## Verification Checklist

Before implementation begins, verify:

- [ ] LiteLLM installed and importable
- [ ] `litellm.Callback` base class available
- [ ] `litellm.callbacks` list accessible for registration
- [ ] `ObservabilityService.get_instance()` works in callback context
- [ ] `obs.log_llm_call()` accepts all required parameters
- [ ] App startup lifespan can register callback
- [ ] Test fixtures can mock LiteLLM response objects
- [ ] `generate_trace_id()` available from factories

---

## Implementation Notes for Dev Agent

### Callback Registration Pattern

```python
# In app/main.py lifespan handler
from app.integrations.litellm_callback import observability_callback

async def lifespan(app: FastAPI):
    # Startup
    import litellm
    litellm.callbacks.append(observability_callback)
    yield
    # Shutdown
```

### Fire-and-Forget Pattern

```python
async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
    try:
        # All observability logic here
        await self._log_embedding(...) or self._log_completion(...)
    except Exception as e:
        # Never propagate - log and continue
        logger.warning("callback_error", error=str(e))
```

### Trace Context Extraction

```python
def _extract_trace_id(self, kwargs: dict) -> str:
    metadata = kwargs.get("litellm_params", {}).get("metadata", {})
    return metadata.get("trace_id") or generate_trace_id()
```

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Initial ATDD checklist created | TEA Agent |
