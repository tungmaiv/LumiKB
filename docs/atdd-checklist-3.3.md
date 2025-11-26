# ATDD Checklist: Story 3.3 - SSE Streaming for Real-Time Search

**Date:** 2025-11-25
**Story ID:** 3.3
**Status:** RED Phase (Tests Failing - Implementation Pending)

---

## Story Summary

**Epic**: 3 - Semantic Search & Citations
**Story**: 3.3 - SSE Streaming for Real-Time Search

**Description:**
Implement Server-Sent Events (SSE) streaming for real-time search results. Users see incremental answer text and citations as they arrive, improving perceived performance and engagement.

**Risk Level:** MEDIUM
- **R-005**: SSE stream disconnects (Score: 4 - MONITOR) - Network issues, client disconnects

---

## Acceptance Criteria Breakdown

| AC ID | Requirement | Test Level | Test File | Status |
|-------|------------|------------|-----------|--------|
| AC-3.3.1 | SSE endpoint with text/event-stream | Integration | `test_sse_streaming.py::test_search_with_sse_accept_header_returns_event_stream` | ❌ RED |
| AC-3.3.2 | Event ordering (token → citation → done) | Integration | `test_sse_streaming.py::test_sse_events_streamed_in_correct_order` | ❌ RED |
| AC-3.3.2 | Token events (incremental text) | Integration | `test_sse_streaming.py::test_sse_token_events_contain_incremental_text` | ❌ RED |
| AC-3.3.2 | Citation events (metadata) | Integration | `test_sse_streaming.py::test_sse_citation_events_contain_metadata` | ❌ RED |
| AC-3.3.3 | Reconnection logic (DEFERRED) | Integration | `test_sse_streaming.py::test_sse_reconnection_resumes_from_last_event` | ⏸️ SKIP |
| AC-3.3.4 | Graceful degradation (non-streaming) | Integration | `test_sse_streaming.py::test_search_without_sse_header_returns_non_streaming` | ❌ RED |

**Total Tests**: 6 tests (5 active + 1 deferred)

**Note**: Reconnection logic (AC-3.3.3) is deferred - requires session state management. Basic streaming is sufficient for MVP.

---

## Test Files Created

### Integration Tests

**File**: `backend/tests/integration/test_sse_streaming.py`

**Tests (6 integration tests):**
1. ✅ `test_search_with_sse_accept_header_returns_event_stream` - SSE protocol compliance
2. ✅ `test_sse_events_streamed_in_correct_order` - Event ordering validation
3. ✅ `test_sse_token_events_contain_incremental_text` - Token streaming
4. ✅ `test_sse_citation_events_contain_metadata` - Citation streaming
5. ⏸️ `test_sse_reconnection_resumes_from_last_event` - DEFERRED (reconnection logic)
6. ✅ `test_search_without_sse_header_returns_non_streaming` - Graceful degradation

---

## Supporting Infrastructure

### SSE Protocol Primer

**SSE Format:**
```
event: token
data: {"text": "OAuth"}

event: token
data: {"text": " 2.0"}

event: citation
data: {"number": 1, "document_name": "OAuth Guide.pdf", "excerpt": "..."}

event: done
data: {"confidence_score": 85}
```

**Key Points:**
- `event:` line declares event type
- `data:` line contains JSON payload
- Blank line separates events
- `Content-Type: text/event-stream`
- Connection stays open until `done` event

---

## Implementation Checklist

### RED Phase (Complete ✅)

- [x] All 5 active tests written and failing (1 deferred)
- [x] SSE protocol documented
- [x] Fixtures created

### GREEN Phase (DEV Team - Implementation Tasks)

#### Task 1: Create SSE Streaming Utility

- [ ] Create `backend/app/utils/sse.py`
- [ ] Implement SSE event formatter:
  ```python
  def format_sse_event(event_type: str, data: dict) -> str:
      """Format SSE event with type and data."""
      import json
      return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
  ```
- [ ] Implement async generator for streaming:
  ```python
  async def stream_events(events):
      """Async generator for SSE events."""
      for event in events:
          yield format_sse_event(event["type"], event["data"])
  ```
- [ ] Run test: Basic SSE formatting (manual validation)
- [ ] ✅ Utility created

#### Task 2: Update Search Endpoint for SSE

- [ ] In `backend/app/api/v1/search.py`, detect SSE request:
  ```python
  @router.post("/search")
  async def search(
      request: Request,
      query: SearchQuery,
      ...
  ):
      accept_header = request.headers.get("accept", "")
      is_sse = "text/event-stream" in accept_header

      if is_sse:
          return StreamingResponse(
              stream_search_results(query, user),
              media_type="text/event-stream"
          )
      else:
          # Non-streaming response (existing logic)
          return search_non_streaming(query, user)
  ```
- [ ] Run test: `test_search_with_sse_accept_header_returns_event_stream`
- [ ] ✅ Test passes (SSE endpoint created)

#### Task 3: Stream Token Events (Incremental Text)

- [ ] Create async generator `stream_search_results()`:
  ```python
  async def stream_search_results(query, user):
      # 1. Perform semantic search (get chunks)
      chunks = await search_service.search(query.query, query.kb_ids, user.id)

      # 2. Stream LLM synthesis with token callbacks
      async for token in synthesis_service.synthesize_streaming(chunks, query.query):
          yield format_sse_event("token", {"text": token})

      # 3. Stream citations (after answer complete)
      for citation in citations:
          yield format_sse_event("citation", citation.dict())

      # 4. Stream done event
      yield format_sse_event("done", {"confidence_score": confidence})
  ```
- [ ] Modify `SynthesisService.synthesize_streaming()` to yield tokens:
  ```python
  async def synthesize_streaming(self, chunks, query):
      # Use LiteLLM streaming API
      response = await litellm.acompletion(
          model="gpt-4",
          messages=[...],
          stream=True  # Enable streaming
      )

      async for chunk in response:
          token = chunk.choices[0].delta.content
          if token:
              yield token
  ```
- [ ] Run test: `test_sse_token_events_contain_incremental_text`
- [ ] ✅ Test passes (token streaming works)

#### Task 4: Stream Citation Events

- [ ] After LLM completes, extract citations from full answer
- [ ] Stream each citation as separate event:
  ```python
  # After all tokens streamed
  full_answer = "".join(tokens)
  clean_text, citations = citation_service.extract_citations(full_answer, chunks)

  for citation in citations:
      yield format_sse_event("citation", citation.dict())
  ```
- [ ] Run test: `test_sse_citation_events_contain_metadata`
- [ ] ✅ Test passes (citation streaming works)

#### Task 5: Validate Event Ordering

- [ ] Ensure events stream in order: token → citation → done
- [ ] Add logging to track event sequence
- [ ] Run test: `test_sse_events_streamed_in_correct_order`
- [ ] ✅ Test passes (ordering correct)

#### Task 6: Implement Graceful Degradation

- [ ] In search endpoint, handle non-SSE requests:
  ```python
  if not is_sse:
      # Non-streaming: wait for full answer
      result = await synthesis_service.synthesize(chunks, query.query)
      return {
          "answer": result.answer,
          "citations": result.citations,
          "confidence_score": result.confidence,
          "results": chunks
      }
  ```
- [ ] Run test: `test_search_without_sse_header_returns_non_streaming`
- [ ] ✅ Test passes (fallback works)

#### Task 7: Error Handling and Cleanup

- [ ] Handle client disconnect gracefully (catch `asyncio.CancelledError`)
- [ ] Log SSE streaming errors
- [ ] Add timeout for long-running streams (max 60s)
- [ ] Run all tests to verify robustness
- [ ] ✅ All tests pass (GREEN phase)

---

## RED-GREEN-REFACTOR Workflow

### RED Phase (Complete ✅)

- ✅ All 5 active tests written and failing
- ✅ Tests define SSE protocol expectations
- ✅ Failures due to missing streaming implementation

### GREEN Phase (DEV Team - Current)

**Suggested order**:
1. Task 1 (SSE utility) - Foundation
2. Task 2 (Endpoint detection) - Protocol
3. Task 3 (Token streaming) - Core UX
4. Task 4 (Citation streaming) - Metadata
5. Task 5 (Event ordering) - Validation
6. Task 6 (Graceful degradation) - Fallback
7. Task 7 (Error handling) - Robustness

### REFACTOR Phase (After all tests green)

1. Extract SSE streaming to reusable middleware
2. Add connection pool monitoring (concurrent streams)
3. Optimize token buffering (reduce network overhead)
4. Add telemetry: track stream duration, disconnect rate
5. Code review with senior dev
6. Commit: "feat: implement SSE streaming for search (Story 3.3)"

---

## Running Tests

### Run All SSE Tests

```bash
cd backend
pytest tests/integration/test_sse_streaming.py -v

# Expected: 5 tests FAIL, 1 SKIP (RED phase)
```

### Run Specific Test

```bash
# Test SSE protocol compliance
pytest tests/integration/test_sse_streaming.py::test_search_with_sse_accept_header_returns_event_stream -vv

# Test event ordering
pytest tests/integration/test_sse_streaming.py::test_sse_events_streamed_in_correct_order -vv
```

### Run After Implementation

```bash
# Run full Story 3.3 test suite
pytest tests/integration/test_sse_streaming.py -v

# Expected: 5 tests PASS, 1 SKIP (GREEN phase)
```

---

## SSE Implementation Notes

### LiteLLM Streaming API

```python
import litellm

async def synthesize_streaming(chunks, query):
    """Stream LLM response token by token."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response = await litellm.acompletion(
        model="gpt-4",
        messages=messages,
        stream=True  # Enable streaming
    )

    async for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

### FastAPI StreamingResponse

```python
from fastapi.responses import StreamingResponse

@router.post("/search")
async def search(...):
    if is_sse:
        return StreamingResponse(
            stream_search_results(...),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
```

---

## Deferred Features (Post-MVP)

### Reconnection Logic (AC-3.3.3)

**Why deferred:**
- Requires server-side session state management
- Adds complexity (event ID tracking, 60s retention)
- Not critical for MVP (most streams complete in <5s)

**Future implementation:**
- Store last N events in Redis (keyed by session_id)
- Accept `Last-Event-ID` header on reconnect
- Resend events after last_event_id
- Expire session state after 60s

**Placeholder test**: `test_sse_reconnection_resumes_from_last_event` (skipped)

---

## Known Issues / TODOs

### Client Disconnect Handling

**Issue**: Client closes connection mid-stream

**Solution**:
```python
async def stream_search_results(...):
    try:
        async for token in synthesis_service.synthesize_streaming(...):
            yield format_sse_event("token", {"text": token})
    except asyncio.CancelledError:
        # Client disconnected - cleanup gracefully
        logger.info("Client disconnected during streaming")
        raise
```

### Concurrent Stream Limits

**Issue**: Too many concurrent SSE connections

**Solution**:
- Limit concurrent streams per user (e.g., max 3)
- Return 429 Too Many Requests if limit exceeded
- Monitor connection pool health

---

## Next Steps for DEV Team

### Immediate Actions

1. **Review SSE protocol** (see SSE Protocol Primer above)
2. **Review LiteLLM streaming docs**: https://docs.litellm.ai/docs/completion/stream
3. **Run failing tests** to confirm RED phase
4. **Start GREEN phase** with Task 1 (SSE utility)

### Definition of Done

- [ ] All 5 active tests pass (1 skipped - reconnection deferred)
- [ ] SSE protocol compliance validated
- [ ] Graceful degradation works (non-streaming fallback)
- [ ] Error handling robust (client disconnect, timeout)
- [ ] Code reviewed by senior dev
- [ ] Merged to main branch

---

## Knowledge Base References Applied

**Frameworks:**
- `test-levels-framework.md` - Integration test level
- `test-quality.md` - Event ordering validation

**Risk Management:**
- `test-design-epic-3.md` - R-005 risk assessment (SSE reliability)

---

## Output Summary

### ATDD Complete - Tests in RED Phase ✅

**Story**: 3.3 - SSE Streaming for Real-Time Search
**Primary Test Level**: Integration

**Failing Tests Created**:
- Integration tests: 5 tests (1 deferred) in `backend/tests/integration/test_sse_streaming.py`

**Supporting Infrastructure**:
- SSE utility functions (to be implemented)
- LiteLLM streaming integration
- FastAPI StreamingResponse

**Implementation Checklist**:
- Total tasks: 7 tasks
- Estimated effort: 8-12 hours

**Risk Mitigation**:
- R-005 (Score 4): SSE stream reliability (graceful degradation, error handling)

**Deferred**:
- Reconnection logic (AC-3.3.3) - Post-MVP

**Next Steps for DEV Team**:
1. Review SSE protocol and LiteLLM streaming docs
2. Run failing tests: `pytest tests/integration/test_sse_streaming.py -v`
3. Implement Task 1 (SSE utility)
4. Follow RED → GREEN → REFACTOR cycle

**Output File**: `docs/atdd-checklist-3.3.md`

---

**Generated by**: Murat (TEA Agent - Test Architect Module)
**Workflow**: `.bmad/bmm/workflows/testarch/atdd`
**Date**: 2025-11-25
