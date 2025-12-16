# Story 9.5: Chat RAG Flow Instrumentation

Status: done

## Story

As a **system administrator**,
I want **chat conversations traced showing retrieval latency, context tokens, LLM response time, and citation mapping**,
so that **I can monitor RAG pipeline performance and optimize retrieval-to-response latency**.

## Acceptance Criteria

1. Chat conversation trace starts when `/api/v1/chat/` endpoint receives a request
2. Retrieval span tracks: query embedding time, Qdrant search latency, documents_retrieved, confidence_scores
3. Context assembly span tracks: chunks_selected, context_tokens, truncation_applied
4. LLM synthesis span tracks: model, prompt_tokens, completion_tokens, latency_ms
5. Citation mapping span tracks: citations_generated, citation_confidence_scores
6. Overall trace captures: user_id, kb_id, conversation_id, total_latency_ms
7. Chat messages logged via `log_chat_message()` for both user and assistant messages
8. Error traces capture step name and error type without exposing sensitive query content
9. Streaming responses maintain trace continuity across SSE chunks
10. Unit tests verify span creation for each RAG pipeline step
11. Integration test demonstrates end-to-end chat trace with retrieval and synthesis

## Tasks / Subtasks

- [ ] Task 1: Instrument chat endpoint with trace initialization (AC: #1, #6)
  - [ ] Subtask 1.1: Import ObservabilityService in chat.py
  - [ ] Subtask 1.2: Start trace at beginning of `send_chat_message()` endpoint
  - [ ] Subtask 1.3: Pass TraceContext through service calls
  - [ ] Subtask 1.4: Record user_id, kb_id, conversation_id in trace metadata
  - [ ] Subtask 1.5: End trace in finally block with appropriate status

- [ ] Task 2: Instrument ConversationService.send_message (AC: #2, #3, #4, #5)
  - [ ] Subtask 2.1: Accept TraceContext parameter in send_message()
  - [ ] Subtask 2.2: Create spans for each RAG pipeline stage
  - [ ] Subtask 2.3: Pass context to SearchService for retrieval instrumentation
  - [ ] Subtask 2.4: Track context assembly metrics

- [ ] Task 3: Instrument retrieval step (AC: #2)
  - [ ] Subtask 3.1: Start "retrieval" span before search_service.search()
  - [ ] Subtask 3.2: Track query_embedding_ms (time to embed query)
  - [ ] Subtask 3.3: Track qdrant_search_ms (time to search vectors)
  - [ ] Subtask 3.4: Record documents_retrieved, max_confidence, min_confidence
  - [ ] Subtask 3.5: End span with total duration_ms

- [ ] Task 4: Instrument context assembly step (AC: #3)
  - [ ] Subtask 4.1: Start "context_assembly" span before building prompt
  - [ ] Subtask 4.2: Track chunks_selected after relevance filtering
  - [ ] Subtask 4.3: Track context_tokens (estimated from chunks)
  - [ ] Subtask 4.4: Record truncation_applied if context was truncated
  - [ ] Subtask 4.5: End span with duration_ms

- [ ] Task 5: Instrument LLM synthesis step (AC: #4)
  - [ ] Subtask 5.1: Start "synthesis" span before LLM call
  - [ ] Subtask 5.2: Record model name in span metadata
  - [ ] Subtask 5.3: After response, record prompt_tokens, completion_tokens
  - [ ] Subtask 5.4: Calculate latency_ms for LLM call
  - [ ] Subtask 5.5: Log LLM call via obs.log_llm_call() with all metrics
  - [ ] Subtask 5.6: End span with duration_ms

- [ ] Task 6: Instrument citation mapping step (AC: #5)
  - [ ] Subtask 6.1: Start "citation_mapping" span before citation extraction
  - [ ] Subtask 6.2: Track citations_generated count
  - [ ] Subtask 6.3: Track citation_confidence_scores array
  - [ ] Subtask 6.4: End span with duration_ms

- [ ] Task 7: Log chat messages (AC: #7)
  - [ ] Subtask 7.1: Log user message via obs.log_chat_message() with role="user"
  - [ ] Subtask 7.2: Log assistant message with role="assistant", token counts, model
  - [ ] Subtask 7.3: Include conversation_id for message grouping
  - [ ] Subtask 7.4: Record latency_ms for assistant messages

- [ ] Task 8: Implement error tracing (AC: #8)
  - [ ] Subtask 8.1: Wrap each step in try/except with span error handling
  - [ ] Subtask 8.2: On error, end span with status="failed", sanitized error_message
  - [ ] Subtask 8.3: Never log query content or user messages in error traces
  - [ ] Subtask 8.4: End overall trace with status="failed" on any step failure

- [ ] Task 9: Handle streaming responses (AC: #9)
  - [ ] Subtask 9.1: Modify chat_stream.py to accept and propagate TraceContext
  - [ ] Subtask 9.2: Start trace before streaming begins
  - [ ] Subtask 9.3: Log LLM call after streaming completes with aggregated tokens
  - [ ] Subtask 9.4: End trace after final SSE chunk sent

- [ ] Task 10: Write unit tests (AC: #10)
  - [ ] Subtask 10.1: Test chat endpoint creates trace with correct metadata
  - [ ] Subtask 10.2: Test each RAG step creates span with correct name and type
  - [ ] Subtask 10.3: Test error handling ends span with failed status
  - [ ] Subtask 10.4: Test chat messages logged for user and assistant
  - [ ] Subtask 10.5: Mock ObservabilityService to verify method calls

- [ ] Task 11: Write integration tests (AC: #11)
  - [ ] Subtask 11.1: Test full chat request with mock KB and documents
  - [ ] Subtask 11.2: Verify trace record in obs_traces table
  - [ ] Subtask 11.3: Verify span records for retrieval, context, synthesis, citation steps
  - [ ] Subtask 11.4: Verify obs_chat_messages records for user and assistant
  - [ ] Subtask 11.5: Test error scenario captures failure correctly

## Dev Notes

### Architecture Patterns

- **Request-Scoped Trace**: One trace per chat request, ends when response sent
- **Span Hierarchy**: trace → retrieval → context_assembly → synthesis → citation_mapping
- **Fire-and-Forget**: Observability calls never block chat response
- **Full Content Logging**: User and assistant message content logged for Chat History viewer (error traces only contain error type, not content)

### Key Technical Decisions

- **Context Propagation**: Pass TraceContext through all service layers
- **Token Estimation**: Use tiktoken or character-based estimation for context_tokens
- **Streaming Traces**: Aggregate token counts after stream completes
- **Citation Scores**: Extract confidence from search result scores

### Source Tree Changes

```
backend/
├── app/api/v1/
│   ├── chat.py              # Modified: Add trace instrumentation
│   └── chat_stream.py       # Modified: Add streaming trace support
├── app/services/
│   ├── conversation_service.py    # Modified: Accept TraceContext, create spans
│   └── search_service.py          # Modified: Accept TraceContext for retrieval span
└── tests/
    ├── unit/
    │   └── test_chat_observability.py    # New: Unit tests
    └── integration/
        └── test_chat_trace_flow.py       # New: Integration tests
```

### Service Method Signature Changes

```python
# conversation_service.py
async def send_message(
    self,
    session_id: str,
    kb_id: UUID,
    user_id: str,
    message: str,
    conversation_id: str | None = None,
    trace_ctx: TraceContext | None = None,  # NEW
) -> dict[str, Any]:

# search_service.py
async def search(
    self,
    kb_id: UUID,
    query: str,
    top_k: int = 5,
    trace_ctx: TraceContext | None = None,  # NEW
) -> list[SearchResult]:
```

### Usage Example

```python
# In chat.py send_chat_message endpoint
from app.services.observability_service import ObservabilityService

@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    request_body: ChatRequest,
    current_user: User = Depends(current_active_user),
    ...
) -> ChatResponse:
    obs = ObservabilityService.get_instance()

    # Start trace
    ctx = await obs.start_trace(
        name="chat.conversation",
        user_id=current_user.id,
        kb_id=request_body.kb_id,
        metadata={"conversation_id": request_body.conversation_id},
    )

    try:
        # Log user message
        await obs.log_chat_message(
            ctx=ctx,
            role="user",
            content=request_body.message,
            conversation_id=result.get("conversation_id"),
        )

        # Call conversation service with trace context
        result = await conversation_service.send_message(
            session_id=session_id,
            kb_id=request_body.kb_id,
            user_id=str(current_user.id),
            message=request_body.message,
            conversation_id=request_body.conversation_id,
            trace_ctx=ctx,  # Pass context
        )

        # Log assistant message
        await obs.log_chat_message(
            ctx=ctx,
            role="assistant",
            content=result["answer"],
            conversation_id=result["conversation_id"],
            latency_ms=response_time_ms,
        )

        # End trace successfully
        await obs.end_trace(ctx, status="completed")

        return ChatResponse(**result)

    except Exception as e:
        await obs.end_trace(ctx, status="failed", error_message=type(e).__name__)
        raise
```

### Testing Standards

- Mock `ObservabilityService.get_instance()` for unit tests
- Use real PostgreSQLProvider for integration tests
- Test with mock search results to verify retrieval metrics
- Verify chat_messages table records both roles

### Configuration Dependencies

No new configuration needed - uses existing observability_enabled setting.

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#Chat RAG Flow]
- [Source: docs/sprint-artifacts/9-3-trace-context-and-core-service.md]
- [Source: backend/app/api/v1/chat.py - existing endpoint structure]
- [Source: backend/app/services/conversation_service.py - RAG pipeline]

## Dev Agent Record

### Context Reference

- [9-5-chat-rag-flow-instrumentation.context.xml](9-5-chat-rag-flow-instrumentation.context.xml)

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

### Completion Notes List

- 2025-12-15: All 11 ACs implemented and verified. 12 unit tests + 9 integration tests passing. Privacy-first design (user content logged as empty string), streaming trace continuity maintained. Code review APPROVED. See: docs/sprint-artifacts/code-review-stories-9-4-9-5-9-6.md
- 2025-12-16: Updated to full content logging - user and assistant message content now logged for Chat History viewer functionality. Error traces still only contain error type (not content) for security.

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Story drafted | Claude (SM Agent) |
| 2025-12-15 | Story context XML created and validated | Claude (SM Agent) |
| 2025-12-15 | Status: ready-for-dev | Claude (SM Agent) |
| 2025-12-15 | Status: done - Code review APPROVED, 83 tests passing | Claude (Dev Agent) |
| 2025-12-16 | Updated: Full content logging enabled for Chat History viewer | Claude (Dev Agent) |
