# ATDD Checklist: Story 9-5 Chat RAG Flow Instrumentation

**Story**: 9-5 Chat RAG Flow Instrumentation
**Status**: Pre-Implementation (ATDD Phase)
**Generated**: 2025-12-15

## Overview

This ATDD checklist defines acceptance tests for chat RAG flow observability instrumentation. Tests verify that retrieval, context assembly, LLM synthesis, and citation mapping are traced with proper spans and metrics.

## Test Environment Requirements

### Required Fixtures
- `test_engine` - PostgreSQL with observability schema
- `db_session` - Async session with rollback
- `api_client` - Authenticated HTTP client
- `kb_with_indexed_chunks` - KB with searchable documents
- `mock_embedding_client` - Mock embedding for query vectorization

### Required Test Data Factories
```python
from tests.factories import (
    create_trace,
    create_span,
    create_llm_span,
    create_obs_chat_message,
    create_conversation,
    create_chat_message,
    generate_trace_id,
)
```

---

## Acceptance Criteria Tests

### AC-1: Chat Conversation Trace Starts on Request

**Test ID**: `test_chat_endpoint_creates_trace`

| Field | Value |
|-------|-------|
| **Description** | Chat conversation trace starts when `/api/v1/chat/` endpoint receives a request |
| **Given** | Authenticated user with access to a KB |
| **When** | POST `/api/v1/chat/` with valid message |
| **Then** | Trace created with name="chat.conversation" |
| **Assertions** | - Trace exists in `obs_traces` table<br>- `trace.name == "chat.conversation"`<br>- `trace.user_id == current_user.id`<br>- `trace.kb_id == request.kb_id`<br>- `trace.attributes["conversation_id"]` present |

**Test File**: `backend/tests/integration/test_chat_trace_flow.py`

---

### AC-2: Retrieval Span Tracks Search Metrics

**Test ID**: `test_retrieval_span_records_search_metrics`

| Field | Value |
|-------|-------|
| **Description** | Retrieval span tracks: query embedding time, Qdrant search latency, documents_retrieved, confidence_scores |
| **Given** | Chat request to KB with indexed documents |
| **When** | Retrieval step completes |
| **Then** | Retrieval span contains search metrics |
| **Assertions** | - `span.name == "retrieval"`<br>- `span.span_type == "retrieval"`<br>- `span.attributes["query_embedding_ms"] > 0`<br>- `span.attributes["qdrant_search_ms"] > 0`<br>- `span.attributes["documents_retrieved"] >= 0`<br>- `span.attributes["max_confidence"]` present<br>- `span.duration_ms > 0` |

**Test File**: `backend/tests/integration/test_chat_trace_flow.py`

---

### AC-3: Context Assembly Span Tracks Token Metrics

**Test ID**: `test_context_assembly_span_records_metrics`

| Field | Value |
|-------|-------|
| **Description** | Context assembly span tracks: chunks_selected, context_tokens, truncation_applied |
| **Given** | Retrieved chunks ready for context building |
| **When** | Context assembly completes |
| **Then** | Context span contains selection metrics |
| **Assertions** | - `span.name == "context_assembly"`<br>- `span.attributes["chunks_selected"] >= 0`<br>- `span.attributes["context_tokens"] > 0`<br>- `span.attributes["truncation_applied"]` is boolean<br>- `span.duration_ms > 0` |

**Test File**: `backend/tests/unit/test_chat_observability.py`

---

### AC-4: LLM Synthesis Span Tracks Model Metrics

**Test ID**: `test_synthesis_span_records_llm_metrics`

| Field | Value |
|-------|-------|
| **Description** | LLM synthesis span tracks: model, prompt_tokens, completion_tokens, latency_ms |
| **Given** | Context prepared for LLM call |
| **When** | LLM synthesis completes |
| **Then** | Synthesis span contains token metrics |
| **Assertions** | - `span.name == "synthesis"`<br>- `span.span_type == "llm"`<br>- `span.model` present<br>- `span.input_tokens > 0` (prompt_tokens)<br>- `span.output_tokens > 0` (completion_tokens)<br>- `span.duration_ms > 0` |

**Test File**: `backend/tests/integration/test_chat_trace_flow.py`

---

### AC-5: Citation Mapping Span Tracks Citation Metrics

**Test ID**: `test_citation_span_records_citation_metrics`

| Field | Value |
|-------|-------|
| **Description** | Citation mapping span tracks: citations_generated, citation_confidence_scores |
| **Given** | LLM response ready for citation extraction |
| **When** | Citation mapping completes |
| **Then** | Citation span contains mapping metrics |
| **Assertions** | - `span.name == "citation_mapping"`<br>- `span.attributes["citations_generated"] >= 0`<br>- `span.attributes["citation_confidence_scores"]` is array<br>- `span.duration_ms >= 0` |

**Test File**: `backend/tests/unit/test_chat_observability.py`

---

### AC-6: Overall Trace Captures Request Metadata

**Test ID**: `test_trace_captures_request_metadata`

| Field | Value |
|-------|-------|
| **Description** | Overall trace captures: user_id, kb_id, conversation_id, total_latency_ms |
| **Given** | Complete chat request/response cycle |
| **When** | Trace ends |
| **Then** | Trace has all request metadata |
| **Assertions** | - `trace.user_id == authenticated_user.id`<br>- `trace.kb_id == request.kb_id`<br>- `trace.attributes["conversation_id"]` present<br>- `trace.duration_ms > 0` (total_latency)<br>- `trace.status == "completed"` |

**Test File**: `backend/tests/integration/test_chat_trace_flow.py`

---

### AC-7: Chat Messages Logged for Both Roles

**Test ID**: `test_chat_messages_logged_user_and_assistant`

| Field | Value |
|-------|-------|
| **Description** | Chat messages logged via `log_chat_message()` for both user and assistant messages |
| **Given** | Complete chat request/response |
| **When** | Response returned to client |
| **Then** | Both user and assistant messages in obs_chat_messages |
| **Assertions** | - User message: `role="user"`, content matches input<br>- Assistant message: `role="assistant"`, content matches response<br>- Both have same `trace_id`<br>- Both have same `conversation_id`<br>- Assistant message has `latency_ms > 0` |

**Test File**: `backend/tests/integration/test_chat_trace_flow.py`

---

### AC-8: Error Traces Sanitize Sensitive Content

**Test ID**: `test_error_traces_exclude_query_content`

| Field | Value |
|-------|-------|
| **Description** | Error traces capture step name and error type without exposing sensitive query content |
| **Given** | Chat request that will fail during synthesis |
| **When** | LLM call throws exception |
| **Then** | Error trace excludes query/message content |
| **Assertions** | - `trace.status == "failed"`<br>- Error message contains exception type<br>- Error message does NOT contain user query<br>- Error message does NOT contain "prompt" content<br>- Span error_message is sanitized |

**Test File**: `backend/tests/unit/test_chat_observability.py`

---

### AC-9: Streaming Responses Maintain Trace Continuity

**Test ID**: `test_streaming_maintains_trace_continuity`

| Field | Value |
|-------|-------|
| **Description** | Streaming responses maintain trace continuity across SSE chunks |
| **Given** | Chat request with streaming=true |
| **When** | SSE streaming completes |
| **Then** | Single trace covers entire streaming response |
| **Assertions** | - One trace record for entire stream<br>- Trace starts before first chunk<br>- Trace ends after final chunk<br>- LLM span has aggregated token counts<br>- `trace.status == "completed"` after stream ends |

**Test File**: `backend/tests/integration/test_chat_trace_flow.py`

---

### AC-10: Unit Tests for RAG Step Spans

**Test ID**: `test_unit_rag_step_spans`

| Field | Value |
|-------|-------|
| **Description** | Unit tests verify span creation for each RAG pipeline step |
| **Test Cases** | - `test_retrieval_step_creates_span`<br>- `test_context_assembly_creates_span`<br>- `test_synthesis_creates_llm_span`<br>- `test_citation_mapping_creates_span`<br>- `test_error_ends_span_failed` |
| **Approach** | Mock `ObservabilityService` and verify method calls with correct parameters |

**Test File**: `backend/tests/unit/test_chat_observability.py`

---

### AC-11: Integration Test End-to-End Chat Trace

**Test ID**: `test_e2e_chat_trace_with_retrieval_synthesis`

| Field | Value |
|-------|-------|
| **Description** | Integration test demonstrates end-to-end chat trace with retrieval and synthesis |
| **Given** | KB with indexed documents, authenticated user |
| **When** | Complete chat request via API |
| **Then** | Full trace with RAG spans in database |
| **Assertions** | - Trace in `obs_traces` with `status="completed"`<br>- Retrieval span with search metrics<br>- Context assembly span with token count<br>- Synthesis span with LLM metrics<br>- Citation span with citation count<br>- User and assistant messages in `obs_chat_messages` |

**Test File**: `backend/tests/integration/test_chat_trace_flow.py`

---

## Unit Test Specifications

### File: `backend/tests/unit/test_chat_observability.py`

```python
"""Unit tests for chat RAG flow observability instrumentation.

Tests verify span creation for each RAG step using mocked ObservabilityService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from tests.factories import (
    create_conversation,
    create_chat_message,
    generate_trace_id,
)


class TestChatTraceInitialization:
    """Tests for trace initialization in chat endpoint."""

    @pytest.mark.asyncio
    async def test_chat_endpoint_starts_trace(self):
        """Trace starts with chat.conversation name."""
        pass

    @pytest.mark.asyncio
    async def test_trace_includes_user_kb_conversation_ids(self):
        """Trace metadata includes user_id, kb_id, conversation_id."""
        pass


class TestRetrievalSpan:
    """Tests for retrieval step span."""

    @pytest.mark.asyncio
    async def test_retrieval_span_created_with_correct_type(self):
        """Retrieval span has span_type='retrieval'."""
        pass

    @pytest.mark.asyncio
    async def test_retrieval_span_records_timing_breakdown(self):
        """Retrieval span includes query_embedding_ms and qdrant_search_ms."""
        pass

    @pytest.mark.asyncio
    async def test_retrieval_span_records_document_count(self):
        """Retrieval span records documents_retrieved count."""
        pass


class TestContextAssemblySpan:
    """Tests for context assembly span."""

    @pytest.mark.asyncio
    async def test_context_span_records_chunks_selected(self):
        """Context span includes chunks_selected count."""
        pass

    @pytest.mark.asyncio
    async def test_context_span_records_token_estimate(self):
        """Context span includes context_tokens estimate."""
        pass

    @pytest.mark.asyncio
    async def test_context_span_records_truncation(self):
        """Context span records if truncation was applied."""
        pass


class TestSynthesisSpan:
    """Tests for LLM synthesis span."""

    @pytest.mark.asyncio
    async def test_synthesis_span_uses_log_llm_call(self):
        """Synthesis logs via obs.log_llm_call() with correct params."""
        pass

    @pytest.mark.asyncio
    async def test_synthesis_span_includes_model(self):
        """Synthesis span includes model name."""
        pass

    @pytest.mark.asyncio
    async def test_synthesis_span_includes_token_counts(self):
        """Synthesis span includes prompt_tokens and completion_tokens."""
        pass


class TestCitationMappingSpan:
    """Tests for citation mapping span."""

    @pytest.mark.asyncio
    async def test_citation_span_records_count(self):
        """Citation span includes citations_generated count."""
        pass


class TestChatMessageLogging:
    """Tests for chat message logging."""

    @pytest.mark.asyncio
    async def test_user_message_logged(self):
        """User message logged with role='user'."""
        pass

    @pytest.mark.asyncio
    async def test_assistant_message_logged_with_metrics(self):
        """Assistant message logged with latency_ms, model, tokens."""
        pass

    @pytest.mark.asyncio
    async def test_messages_share_conversation_id(self):
        """Both messages have same conversation_id."""
        pass


class TestErrorHandling:
    """Tests for error handling in chat traces."""

    @pytest.mark.asyncio
    async def test_error_trace_excludes_query(self):
        """Error message does not contain user query text."""
        pass

    @pytest.mark.asyncio
    async def test_error_trace_includes_exception_type(self):
        """Error message includes exception class name."""
        pass


class TestStreamingTraces:
    """Tests for streaming response traces."""

    @pytest.mark.asyncio
    async def test_streaming_creates_single_trace(self):
        """Streaming response creates one trace, not per-chunk."""
        pass

    @pytest.mark.asyncio
    async def test_streaming_aggregates_tokens(self):
        """Token counts aggregated after stream completes."""
        pass
```

---

## Integration Test Specifications

### File: `backend/tests/integration/test_chat_trace_flow.py`

```python
"""Integration tests for chat RAG flow trace.

Tests verify end-to-end trace creation with real PostgreSQL provider.
Uses kb_with_indexed_chunks fixture for realistic RAG testing.
"""
import pytest
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import Trace, Span, ObsChatMessage
from tests.factories import create_user, create_chat_message


@pytest.fixture
async def chat_test_user(db_session: AsyncSession):
    """Create authenticated test user."""
    pass


class TestEndToEndChatTrace:
    """Integration tests for complete chat RAG trace."""

    @pytest.mark.asyncio
    async def test_chat_request_creates_trace(
        self,
        api_client,
        kb_with_indexed_chunks,
        chat_test_user,
    ):
        """Chat API request creates trace in database."""
        pass

    @pytest.mark.asyncio
    async def test_all_rag_spans_created(
        self,
        api_client,
        kb_with_indexed_chunks,
        db_session: AsyncSession,
    ):
        """All RAG steps create spans: retrieval, context, synthesis, citation."""
        pass

    @pytest.mark.asyncio
    async def test_chat_messages_recorded(
        self,
        api_client,
        kb_with_indexed_chunks,
        db_session: AsyncSession,
    ):
        """User and assistant messages recorded in obs_chat_messages."""
        pass

    @pytest.mark.asyncio
    async def test_successful_chat_ends_completed(
        self,
        api_client,
        kb_with_indexed_chunks,
        db_session: AsyncSession,
    ):
        """Successful chat ends trace with status='completed'."""
        pass

    @pytest.mark.asyncio
    async def test_failed_chat_ends_failed(
        self,
        api_client,
        kb_with_indexed_chunks,
        db_session: AsyncSession,
    ):
        """Failed chat ends trace with status='failed'."""
        pass


class TestStreamingChatTrace:
    """Tests for streaming chat response traces."""

    @pytest.mark.asyncio
    async def test_streaming_chat_creates_trace(
        self,
        api_client,
        kb_with_indexed_chunks,
        db_session: AsyncSession,
    ):
        """Streaming chat creates single trace covering entire stream."""
        pass

    @pytest.mark.asyncio
    async def test_streaming_llm_span_has_aggregated_tokens(
        self,
        api_client,
        kb_with_indexed_chunks,
        db_session: AsyncSession,
    ):
        """LLM span after streaming has total token counts."""
        pass


class TestTraceCorrelation:
    """Tests for trace correlation across services."""

    @pytest.mark.asyncio
    async def test_all_spans_share_trace_id(
        self,
        api_client,
        kb_with_indexed_chunks,
        db_session: AsyncSession,
    ):
        """All spans from single request share same trace_id."""
        pass

    @pytest.mark.asyncio
    async def test_conversation_id_correlates_messages(
        self,
        api_client,
        kb_with_indexed_chunks,
        db_session: AsyncSession,
    ):
        """Conversation ID links user and assistant messages."""
        pass
```

---

## Test Data Factory Requirements

### New/Extended Factory Functions

```python
# In observability_factory.py - extend existing factories

def create_chat_trace(
    user_id: UUID | None = None,
    kb_id: UUID | None = None,
    conversation_id: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Create trace data for chat conversation scenario."""
    return create_trace(
        name="chat.conversation",
        user_id=user_id,
        kb_id=kb_id,
        attributes={
            "conversation_id": conversation_id or str(uuid4()),
            **(kwargs.get("attributes", {})),
        },
        **{k: v for k, v in kwargs.items() if k != "attributes"},
    )


def create_retrieval_span(
    trace_id: str,
    documents_retrieved: int = 5,
    query_embedding_ms: int = 50,
    qdrant_search_ms: int = 100,
    **kwargs,
) -> dict[str, Any]:
    """Create retrieval span with search metrics."""
    return create_span(
        name="retrieval",
        span_type="retrieval",
        trace_id=trace_id,
        attributes={
            "documents_retrieved": documents_retrieved,
            "query_embedding_ms": query_embedding_ms,
            "qdrant_search_ms": qdrant_search_ms,
            "max_confidence": 0.95,
            "min_confidence": 0.75,
            **(kwargs.get("attributes", {})),
        },
        **{k: v for k, v in kwargs.items() if k != "attributes"},
    )


def create_synthesis_span(
    trace_id: str,
    model: str = "gpt-4",
    prompt_tokens: int = 500,
    completion_tokens: int = 200,
    **kwargs,
) -> dict[str, Any]:
    """Create synthesis span with LLM metrics."""
    return create_llm_span(
        name="synthesis",
        trace_id=trace_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        **kwargs,
    )
```

---

## Verification Checklist

Before implementation begins, verify:

- [ ] `obs_chat_messages` table exists with required columns
- [ ] `conversation_service.py` accepts optional `trace_ctx` parameter
- [ ] `search_service.py` accepts optional `trace_ctx` parameter
- [ ] Chat endpoint can access `ObservabilityService.get_instance()`
- [ ] SSE streaming endpoint can propagate trace context
- [ ] `obs.log_chat_message()` method handles all required fields
- [ ] Test KB fixture has indexed documents for retrieval testing
- [ ] Mock LLM returns realistic token counts for testing

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Initial ATDD checklist created | TEA Agent |
