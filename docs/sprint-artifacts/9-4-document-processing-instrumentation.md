# Story 9.4: Document Processing Instrumentation

Status: done

## Story

As a **system administrator**,
I want **parse/chunk/embed/index operations traced with spans showing file type, chunk count, embedding dimensions, and timing**,
so that **I can monitor document processing performance and identify bottlenecks in the pipeline**.

## Acceptance Criteria

1. Document processing trace starts when `process_document` Celery task begins
2. Each processing step (upload/parse/chunk/embed/index) creates a child span with step-specific metrics
3. Parse span records: file_type, file_size_bytes, extracted_chars, page_count, section_count, duration_ms
4. Chunk span records: chunk_count, chunk_size_config, chunk_overlap_config, total_tokens, duration_ms
5. Embed span records: embedding_model, dimensions, batch_count, total_tokens_used, duration_ms
6. Index span records: qdrant_collection, vectors_indexed, duration_ms
7. Error spans capture step name, error type, and error message without stack traces
8. Document events logged via `log_document_event()` for each step transition
9. Processing pipeline failures properly end the trace with status="failed"
10. Unit tests verify span creation for each processing step
11. Integration test demonstrates end-to-end document processing trace with all steps

## Tasks / Subtasks

- [ ] Task 1: Create document trace initialization helper (AC: #1)
  - [ ] Subtask 1.1: Create `start_document_trace()` async function in document_tasks.py
  - [ ] Subtask 1.2: Generate TraceContext with document_id, kb_id, user_id (from document creator)
  - [ ] Subtask 1.3: Call `obs.start_trace()` with name="document.processing"
  - [ ] Subtask 1.4: Store trace_id in task metadata for correlation

- [ ] Task 2: Instrument upload/download step (AC: #2, #3)
  - [ ] Subtask 2.1: Start "upload" span before MinIO download
  - [ ] Subtask 2.2: Record file_size_bytes from downloaded content length
  - [ ] Subtask 2.3: Record duration_ms after checksum validation
  - [ ] Subtask 2.4: Log document event with event_type="upload", status="completed"

- [ ] Task 3: Instrument parse step (AC: #2, #3)
  - [ ] Subtask 3.1: Start "parse" span before `parse_document()` call
  - [ ] Subtask 3.2: Record mime_type, file_size_bytes in span metadata
  - [ ] Subtask 3.3: After parsing, record extracted_chars, page_count, section_count
  - [ ] Subtask 3.4: End span with duration_ms
  - [ ] Subtask 3.5: Log document event with event_type="parse", status="completed"

- [ ] Task 4: Instrument chunk step (AC: #2, #4)
  - [ ] Subtask 4.1: Start "chunk" span before `chunk_document()` call
  - [ ] Subtask 4.2: Record chunk_size and chunk_overlap from KB config
  - [ ] Subtask 4.3: After chunking, record chunk_count, total_chars
  - [ ] Subtask 4.4: End span with duration_ms
  - [ ] Subtask 4.5: Log document event with event_type="chunk", chunk_count

- [ ] Task 5: Instrument embed step (AC: #2, #5)
  - [ ] Subtask 5.1: Start "embed" span before `generate_embeddings()` call
  - [ ] Subtask 5.2: Record embedding_model, dimensions from config
  - [ ] Subtask 5.3: Track batch_count from embedding batches
  - [ ] Subtask 5.4: After embedding, record total_tokens_used from client
  - [ ] Subtask 5.5: End span with duration_ms
  - [ ] Subtask 5.6: Log document event with event_type="embed", token_count

- [ ] Task 6: Instrument index step (AC: #2, #6)
  - [ ] Subtask 6.1: Start "index" span before `index_document()` call
  - [ ] Subtask 6.2: Record collection_name (kb-{kb_id}), vectors_to_index
  - [ ] Subtask 6.3: After indexing, record actual vectors_indexed
  - [ ] Subtask 6.4: End span with duration_ms
  - [ ] Subtask 6.5: Log document event with event_type="index", status="completed"

- [ ] Task 7: Implement error tracing (AC: #7, #9)
  - [ ] Subtask 7.1: Wrap each step in try/except with span error handling
  - [ ] Subtask 7.2: On error, end span with status="failed", error_message
  - [ ] Subtask 7.3: Log document event with event_type=step, status="failed", error_message
  - [ ] Subtask 7.4: End overall trace with status="failed" on any step failure
  - [ ] Subtask 7.5: Ensure trace ends successfully with status="completed" on success

- [ ] Task 8: Handle async context in Celery worker (AC: #1, #8)
  - [ ] Subtask 8.1: Create sync wrapper functions for observability calls in Celery context
  - [ ] Subtask 8.2: Use `run_async()` pattern consistent with existing task code
  - [ ] Subtask 8.3: Ensure trace context is properly passed through pipeline

- [ ] Task 9: Write unit tests (AC: #10)
  - [ ] Subtask 9.1: Test trace initialization creates proper TraceContext
  - [ ] Subtask 9.2: Test each step creates span with correct name and type
  - [ ] Subtask 9.3: Test error handling ends span with failed status
  - [ ] Subtask 9.4: Mock ObservabilityService to verify method calls
  - [ ] Subtask 9.5: Test document events logged for each step

- [ ] Task 10: Write integration tests (AC: #11)
  - [ ] Subtask 10.1: Test full document processing with mock file
  - [ ] Subtask 10.2: Verify trace record in obs_traces table
  - [ ] Subtask 10.3: Verify span records for all 5 steps (upload, parse, chunk, embed, index)
  - [ ] Subtask 10.4: Verify document_events records for each step
  - [ ] Subtask 10.5: Test error scenario captures failure correctly

## Dev Notes

### Architecture Patterns

- **Celery Async Context**: Use `run_async()` wrapper for observability calls since Celery tasks are sync
- **Fire-and-Forget**: Observability calls should never block document processing
- **Context Propagation**: Pass TraceContext through all pipeline steps

### Key Technical Decisions

- **Span Hierarchy**: Root trace → step spans (upload → parse → chunk → embed → index)
- **Metrics Priority**: Focus on timing (duration_ms) and counts (chunks, tokens, vectors)
- **Error Isolation**: Step failures captured in span without stopping trace until final end
- **No Stack Traces**: Error messages only - stack traces too verbose for telemetry

### Source Tree Changes

```
backend/
├── app/workers/
│   └── document_tasks.py    # Modified: Add observability instrumentation
└── tests/
    ├── unit/
    │   └── test_document_observability.py    # New: Unit tests
    └── integration/
        └── test_document_trace_flow.py       # New: Integration tests
```

### Integration Points

- `ObservabilityService.get_instance()` - Singleton for all calls
- `obs.start_trace()` → `obs.span()` → `obs.log_document_event()` → `obs.end_trace()`
- Existing step tracking (`_mark_step_in_progress`, `_mark_step_complete`) retained for document.processing_steps

### Usage Example

```python
# In process_document Celery task
from app.services.observability_service import (
    ObservabilityService,
    TraceContext,
)

def process_document(self, doc_id: str, is_replacement: bool = False) -> dict:
    obs = ObservabilityService.get_instance()

    # Start trace
    ctx = run_async(obs.start_trace(
        name="document.processing",
        kb_id=document.kb_id,
        user_id=document.created_by,
        metadata={"document_id": doc_id, "is_replacement": is_replacement},
    ))

    try:
        # Upload/Download step
        async with obs.span(ctx, "upload", "document") as span_id:
            file_data = await minio_service.download_file(kb_id, object_path)
            # span auto-records duration

        await obs.log_document_event(
            ctx=ctx,
            document_id=UUID(doc_id),
            event_type="upload",
            status="completed",
            duration_ms=upload_duration,
        )

        # ... similar for parse, chunk, embed, index ...

        # End trace on success
        run_async(obs.end_trace(ctx, status="completed"))

    except Exception as e:
        run_async(obs.end_trace(ctx, status="failed", error_message=str(e)))
        raise
```

### Testing Standards

- Mock `ObservabilityService.get_instance()` for unit tests
- Use real PostgreSQLProvider for integration tests
- Verify span parent-child relationships
- Check timing accuracy with controlled operations

### Configuration Dependencies

No new configuration needed - uses existing observability_enabled setting.

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#Document Processing Flow]
- [Source: docs/sprint-artifacts/9-3-trace-context-and-core-service.md]
- [Source: backend/app/workers/document_tasks.py - existing task structure]

## Dev Agent Record

### Context Reference

- [9-4-document-processing-instrumentation.context.xml](9-4-document-processing-instrumentation.context.xml)

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

### Completion Notes List

- 2025-12-15: All 11 ACs implemented and verified. 15 unit tests + 8 integration tests passing. Fire-and-forget telemetry pattern, TraceContext propagation through all pipeline steps. Code review APPROVED. See: docs/sprint-artifacts/code-review-stories-9-4-9-5-9-6.md

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Story drafted | Claude (SM Agent) |
| 2025-12-15 | Story context XML created and validated | Claude (SM Agent) |
| 2025-12-15 | Status: ready-for-dev | Claude (SM Agent) |
| 2025-12-15 | Status: done - Code review APPROVED, 83 tests passing | Claude (Dev Agent) |
