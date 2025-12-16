# ATDD Checklist: Story 9-4 Document Processing Instrumentation

**Story**: 9-4 Document Processing Instrumentation
**Status**: Pre-Implementation (ATDD Phase)
**Generated**: 2025-12-15

## Overview

This ATDD checklist defines acceptance tests for document processing observability instrumentation. Tests verify that parse/chunk/embed/index operations are traced with proper spans, metrics, and document events.

## Test Environment Requirements

### Required Fixtures
- `test_engine` - PostgreSQL with observability schema (from integration/conftest.py)
- `db_session` - Async session with rollback (from integration/conftest.py)
- `mock_embedding_client` - Mock embedding responses (from integration/conftest.py)
- `observability_factory` - Factories for trace/span/document_event assertions

### Required Test Data Factories
```python
from tests.factories import (
    create_trace,
    create_span,
    create_document_event,
    generate_trace_id,
    generate_span_id,
    create_document,
    create_knowledge_base,
)
```

---

## Acceptance Criteria Tests

### AC-1: Document Processing Trace Starts

**Test ID**: `test_process_document_creates_trace`

| Field | Value |
|-------|-------|
| **Description** | Document processing trace starts when `process_document` Celery task begins |
| **Given** | A document ready for processing in a knowledge base |
| **When** | The `process_document` Celery task is triggered |
| **Then** | A trace record is created with name="document.processing", kb_id, user_id |
| **Assertions** | - Trace exists in `obs_traces` table<br>- `trace.name == "document.processing"`<br>- `trace.kb_id == document.kb_id`<br>- `trace.user_id == document.created_by`<br>- `trace.status == "in_progress"` initially |

**Test File**: `backend/tests/integration/test_document_trace_flow.py`

---

### AC-2: Child Spans for Each Processing Step

**Test ID**: `test_processing_steps_create_child_spans`

| Field | Value |
|-------|-------|
| **Description** | Each processing step (upload/parse/chunk/embed/index) creates a child span |
| **Given** | A document trace has been started |
| **When** | Document processing completes all steps |
| **Then** | Five child spans exist with correct names and parent relationships |
| **Assertions** | - Span with `name="upload"` exists<br>- Span with `name="parse"` exists<br>- Span with `name="chunk"` exists<br>- Span with `name="embed"` exists<br>- Span with `name="index"` exists<br>- All spans have `trace_id` matching parent trace |

**Test File**: `backend/tests/integration/test_document_trace_flow.py`

---

### AC-3: Parse Span Records File Metrics

**Test ID**: `test_parse_span_records_file_metrics`

| Field | Value |
|-------|-------|
| **Description** | Parse span records: file_type, file_size_bytes, extracted_chars, page_count, section_count, duration_ms |
| **Given** | A PDF document being processed |
| **When** | The parse step completes |
| **Then** | Parse span contains all required metrics in attributes |
| **Assertions** | - `span.name == "parse"`<br>- `span.attributes["file_type"]` present<br>- `span.attributes["file_size_bytes"] > 0`<br>- `span.attributes["extracted_chars"] > 0`<br>- `span.duration_ms > 0`<br>- `span.status == "completed"` |

**Test File**: `backend/tests/unit/test_document_observability.py`

---

### AC-4: Chunk Span Records Chunking Metrics

**Test ID**: `test_chunk_span_records_chunking_metrics`

| Field | Value |
|-------|-------|
| **Description** | Chunk span records: chunk_count, chunk_size_config, chunk_overlap_config, total_tokens, duration_ms |
| **Given** | Parsed document content |
| **When** | The chunking step completes |
| **Then** | Chunk span contains chunking configuration and results |
| **Assertions** | - `span.name == "chunk"`<br>- `span.attributes["chunk_count"] > 0`<br>- `span.attributes["chunk_size_config"]` matches KB config<br>- `span.attributes["chunk_overlap_config"]` present<br>- `span.duration_ms > 0` |

**Test File**: `backend/tests/unit/test_document_observability.py`

---

### AC-5: Embed Span Records Embedding Metrics

**Test ID**: `test_embed_span_records_embedding_metrics`

| Field | Value |
|-------|-------|
| **Description** | Embed span records: embedding_model, dimensions, batch_count, total_tokens_used, duration_ms |
| **Given** | Document chunks ready for embedding |
| **When** | The embedding step completes |
| **Then** | Embed span contains model and token metrics |
| **Assertions** | - `span.name == "embed"`<br>- `span.attributes["embedding_model"]` present<br>- `span.attributes["dimensions"] == 1536` (or configured)<br>- `span.attributes["batch_count"] > 0`<br>- `span.attributes["total_tokens_used"] > 0`<br>- `span.duration_ms > 0` |

**Test File**: `backend/tests/unit/test_document_observability.py`

---

### AC-6: Index Span Records Vector Metrics

**Test ID**: `test_index_span_records_vector_metrics`

| Field | Value |
|-------|-------|
| **Description** | Index span records: qdrant_collection, vectors_indexed, duration_ms |
| **Given** | Embeddings ready for indexing |
| **When** | The indexing step completes |
| **Then** | Index span contains collection and vector count |
| **Assertions** | - `span.name == "index"`<br>- `span.attributes["qdrant_collection"]` matches `kb-{kb_id}`<br>- `span.attributes["vectors_indexed"] > 0`<br>- `span.duration_ms > 0` |

**Test File**: `backend/tests/unit/test_document_observability.py`

---

### AC-7: Error Spans Capture Failure Details

**Test ID**: `test_error_spans_capture_sanitized_errors`

| Field | Value |
|-------|-------|
| **Description** | Error spans capture step name, error type, and error message without stack traces |
| **Given** | Document processing with simulated parse failure |
| **When** | The parse step fails with an exception |
| **Then** | Error span captures error info without stack trace |
| **Assertions** | - `span.status == "failed"`<br>- `span.error_message` contains error type<br>- `span.error_message` does NOT contain "Traceback"<br>- `span.error_message` does NOT contain file paths<br>- Error message truncated to reasonable length |

**Test File**: `backend/tests/unit/test_document_observability.py`

---

### AC-8: Document Events Logged for Each Step

**Test ID**: `test_document_events_logged_per_step`

| Field | Value |
|-------|-------|
| **Description** | Document events logged via `log_document_event()` for each step transition |
| **Given** | Document processing completes |
| **When** | All steps finish |
| **Then** | Document events exist for each step |
| **Assertions** | - Event with `event_type="upload"` exists<br>- Event with `event_type="parse"` exists<br>- Event with `event_type="chunk"` exists with `chunk_count`<br>- Event with `event_type="embed"` exists with `token_count`<br>- Event with `event_type="index"` exists<br>- All events have matching `trace_id` and `document_id` |

**Test File**: `backend/tests/integration/test_document_trace_flow.py`

---

### AC-9: Failed Pipeline Ends Trace with Failed Status

**Test ID**: `test_pipeline_failure_ends_trace_failed`

| Field | Value |
|-------|-------|
| **Description** | Processing pipeline failures properly end the trace with status="failed" |
| **Given** | Document processing where embed step will fail |
| **When** | The embed step throws an exception |
| **Then** | Trace ends with failed status |
| **Assertions** | - `trace.status == "failed"`<br>- `trace.duration_ms > 0`<br>- Failed span has `status="failed"`<br>- Document event with `status="failed"` exists |

**Test File**: `backend/tests/integration/test_document_trace_flow.py`

---

### AC-10: Unit Tests for Span Creation

**Test ID**: `test_unit_span_creation_per_step`

| Field | Value |
|-------|-------|
| **Description** | Unit tests verify span creation for each processing step |
| **Test Cases** | - `test_upload_step_creates_span_with_correct_type`<br>- `test_parse_step_creates_span_with_file_metrics`<br>- `test_chunk_step_creates_span_with_chunk_metrics`<br>- `test_embed_step_creates_span_with_token_metrics`<br>- `test_index_step_creates_span_with_vector_metrics`<br>- `test_error_ends_span_with_failed_status` |
| **Approach** | Mock `ObservabilityService.get_instance()` and verify method calls |

**Test File**: `backend/tests/unit/test_document_observability.py`

---

### AC-11: Integration Test End-to-End Trace

**Test ID**: `test_e2e_document_processing_trace`

| Field | Value |
|-------|-------|
| **Description** | Integration test demonstrates end-to-end document processing trace with all steps |
| **Given** | Test document uploaded to KB via API |
| **When** | Document processing completes (simulated Celery task) |
| **Then** | Full trace with all spans and events in database |
| **Assertions** | - Trace in `obs_traces` with `status="completed"`<br>- 5 spans in `obs_spans` linked to trace<br>- 5 document events in `obs_document_events`<br>- Span timing cascade: upload < parse < chunk < embed < index<br>- All spans have non-zero `duration_ms` |

**Test File**: `backend/tests/integration/test_document_trace_flow.py`

---

## Unit Test Specifications

### File: `backend/tests/unit/test_document_observability.py`

```python
"""Unit tests for document processing observability instrumentation.

Tests verify span creation for each processing step using mocked
ObservabilityService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from tests.factories import (
    create_document,
    create_knowledge_base,
    generate_trace_id,
)


class TestDocumentTraceInitialization:
    """Tests for trace initialization in document processing."""

    @pytest.mark.asyncio
    async def test_process_document_starts_trace(self):
        """Trace starts with document.processing name and correct metadata."""
        pass  # Implementation per story

    @pytest.mark.asyncio
    async def test_trace_includes_document_kb_user_ids(self):
        """Trace metadata includes document_id, kb_id, user_id."""
        pass


class TestUploadSpan:
    """Tests for upload/download step span."""

    @pytest.mark.asyncio
    async def test_upload_span_created_with_document_type(self):
        """Upload span has name='upload' and span_type='document'."""
        pass

    @pytest.mark.asyncio
    async def test_upload_span_records_file_size(self):
        """Upload span attributes include file_size_bytes."""
        pass


class TestParseSpan:
    """Tests for parse step span."""

    @pytest.mark.asyncio
    async def test_parse_span_records_file_type(self):
        """Parse span records mime_type in attributes."""
        pass

    @pytest.mark.asyncio
    async def test_parse_span_records_extracted_chars(self):
        """Parse span records character count after extraction."""
        pass


class TestChunkSpan:
    """Tests for chunk step span."""

    @pytest.mark.asyncio
    async def test_chunk_span_records_count_and_config(self):
        """Chunk span includes chunk_count, chunk_size, overlap."""
        pass


class TestEmbedSpan:
    """Tests for embed step span."""

    @pytest.mark.asyncio
    async def test_embed_span_records_model_and_tokens(self):
        """Embed span includes embedding_model, dimensions, tokens_used."""
        pass


class TestIndexSpan:
    """Tests for index step span."""

    @pytest.mark.asyncio
    async def test_index_span_records_collection_and_vectors(self):
        """Index span includes qdrant_collection, vectors_indexed."""
        pass


class TestErrorHandling:
    """Tests for error capture in spans."""

    @pytest.mark.asyncio
    async def test_error_span_captures_exception_type(self):
        """Failed span includes error type in error_message."""
        pass

    @pytest.mark.asyncio
    async def test_error_span_excludes_stack_trace(self):
        """Error message does not include stack trace."""
        pass

    @pytest.mark.asyncio
    async def test_error_truncates_long_messages(self):
        """Long error messages are truncated."""
        pass


class TestDocumentEvents:
    """Tests for document event logging."""

    @pytest.mark.asyncio
    async def test_log_document_event_called_per_step(self):
        """log_document_event called for each processing step."""
        pass

    @pytest.mark.asyncio
    async def test_document_event_includes_chunk_count(self):
        """Chunk event includes chunk_count metric."""
        pass

    @pytest.mark.asyncio
    async def test_document_event_includes_token_count(self):
        """Embed event includes token_count metric."""
        pass
```

---

## Integration Test Specifications

### File: `backend/tests/integration/test_document_trace_flow.py`

```python
"""Integration tests for document processing trace flow.

Tests verify end-to-end trace creation with real PostgreSQL provider.
Uses testcontainers for isolated database environment.
"""
import pytest
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import Trace, Span, DocumentEvent
from tests.factories import (
    create_document,
    create_knowledge_base,
    create_user,
)


@pytest.fixture
async def test_kb_with_document(db_session: AsyncSession):
    """Create KB with document ready for processing."""
    # Setup code per project patterns
    pass


class TestEndToEndDocumentTrace:
    """Integration tests for complete document processing trace."""

    @pytest.mark.asyncio
    async def test_full_processing_creates_trace(
        self,
        db_session: AsyncSession,
        test_kb_with_document,
    ):
        """Full document processing creates trace with all spans."""
        pass

    @pytest.mark.asyncio
    async def test_all_five_spans_created(
        self,
        db_session: AsyncSession,
        test_kb_with_document,
    ):
        """All five processing steps create spans linked to trace."""
        pass

    @pytest.mark.asyncio
    async def test_document_events_recorded(
        self,
        db_session: AsyncSession,
        test_kb_with_document,
    ):
        """Document events exist for each processing step."""
        pass

    @pytest.mark.asyncio
    async def test_successful_processing_ends_completed(
        self,
        db_session: AsyncSession,
        test_kb_with_document,
    ):
        """Successful processing ends trace with status='completed'."""
        pass

    @pytest.mark.asyncio
    async def test_failed_processing_ends_failed(
        self,
        db_session: AsyncSession,
        test_kb_with_document,
    ):
        """Failed processing ends trace with status='failed'."""
        pass

    @pytest.mark.asyncio
    async def test_span_timing_cascade(
        self,
        db_session: AsyncSession,
        test_kb_with_document,
    ):
        """Span timestamps follow expected processing order."""
        pass


class TestTraceMetrics:
    """Tests for trace metric accuracy."""

    @pytest.mark.asyncio
    async def test_chunk_count_matches_actual(
        self,
        db_session: AsyncSession,
        test_kb_with_document,
    ):
        """Recorded chunk_count matches actual chunks created."""
        pass

    @pytest.mark.asyncio
    async def test_duration_ms_reasonable(
        self,
        db_session: AsyncSession,
        test_kb_with_document,
    ):
        """All duration_ms values are positive and reasonable."""
        pass
```

---

## Test Data Factory Requirements

### New Factory Functions Needed

```python
# In observability_factory.py - extend if needed

def create_document_processing_trace(
    document_id: UUID | None = None,
    kb_id: UUID | None = None,
    user_id: UUID | None = None,
    status: str = "completed",
    **kwargs,
) -> dict[str, Any]:
    """Create trace data for document processing scenario."""
    return create_trace(
        name="document.processing",
        kb_id=kb_id,
        user_id=user_id,
        status=status,
        attributes={
            "document_id": str(document_id) if document_id else str(uuid4()),
            **(kwargs.get("attributes", {})),
        },
        **{k: v for k, v in kwargs.items() if k != "attributes"},
    )


def create_processing_step_span(
    step_name: str,
    trace_id: str,
    duration_ms: int = 100,
    **kwargs,
) -> dict[str, Any]:
    """Create span for a document processing step."""
    return create_span(
        name=step_name,
        span_type="document",
        trace_id=trace_id,
        duration_ms=duration_ms,
        **kwargs,
    )
```

---

## Verification Checklist

Before implementation begins, verify:

- [ ] `obs_traces` table exists with required columns
- [ ] `obs_spans` table exists with required columns
- [ ] `obs_document_events` table exists with required columns
- [ ] `ObservabilityService.get_instance()` singleton pattern works
- [ ] `obs.span()` context manager available
- [ ] `obs.log_document_event()` method available
- [ ] Test database has observability schema migrated
- [ ] Celery task can use async observability calls via `run_async()`

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Initial ATDD checklist created | TEA Agent |
