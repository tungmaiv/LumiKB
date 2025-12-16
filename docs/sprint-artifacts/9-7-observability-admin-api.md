# Story 9.7: Observability Admin API

Status: ready-for-dev

## Story

As a **system administrator**,
I want **REST API endpoints for querying observability data including traces, chat history, document processing events, and aggregated statistics**,
so that **I can access observability information programmatically for debugging, monitoring, and building admin dashboard views**.

## Acceptance Criteria

1. `GET /api/v1/observability/traces` - list traces with filters (operation_type, status, user_id, kb_id, date range, search)
2. `GET /api/v1/observability/traces/{trace_id}` - trace detail with all child spans
3. `GET /api/v1/observability/chat-history` - query chat messages with filters (user_id, kb_id, session_id, date range)
4. `GET /api/v1/observability/documents/{document_id}/timeline` - document processing events for a specific document
5. `GET /api/v1/observability/stats` - aggregated statistics (token usage, costs, processing metrics)
6. All endpoints require admin authentication (`require_admin` dependency)
7. Pagination with skip/limit (max 100 traces per page, max 500 messages per page)
8. Date range filtering on all list endpoints (start_date, end_date query parameters)
9. OpenAPI schemas documented with examples and descriptions
10. Integration tests for all endpoints with positive and negative test cases

## Tasks / Subtasks

- [ ] Task 1: Create observability API router (AC: #1, #6)
  - [ ] Subtask 1.1: Create `backend/app/api/v1/observability.py` router file
  - [ ] Subtask 1.2: Add router to main app with prefix `/api/v1/observability`
  - [ ] Subtask 1.3: Apply `require_admin` dependency to all endpoints
  - [ ] Subtask 1.4: Import and use ObservabilityService for data access

- [ ] Task 2: Create Pydantic schemas for observability API (AC: #9)
  - [ ] Subtask 2.1: Create `backend/app/schemas/observability.py`
  - [ ] Subtask 2.2: Define `TraceListResponse` with pagination metadata
  - [ ] Subtask 2.3: Define `TraceDetailResponse` with spans array
  - [ ] Subtask 2.4: Define `SpanResponse` with type-specific metrics
  - [ ] Subtask 2.5: Define `ChatHistoryResponse` with session grouping
  - [ ] Subtask 2.6: Define `ChatMessageResponse` with citations and metrics
  - [ ] Subtask 2.7: Define `DocumentTimelineResponse` with events array
  - [ ] Subtask 2.8: Define `DocumentEventResponse` with step details
  - [ ] Subtask 2.9: Define `ObservabilityStatsResponse` with aggregated metrics
  - [ ] Subtask 2.10: Add OpenAPI examples to all schemas

- [x] Task 3: Implement traces list endpoint (AC: #1, #7, #8)
  - [x] Subtask 3.1: Define `GET /traces` endpoint with query parameters
  - [x] Subtask 3.2: Accept filters: operation_type, status, user_id, kb_id, start_date, end_date
  - [x] Subtask 3.3: Accept pagination: skip (default 0), limit (default 20, max 100)
  - [x] Subtask 3.4: Call ObservabilityQueryService.list_traces() with filters
  - [x] Subtask 3.5: Return TraceListResponse with total count and items
  - [x] Subtask 3.6: Add search parameter for trace ID or name (case-insensitive ILIKE)

- [ ] Task 4: Implement trace detail endpoint (AC: #2)
  - [ ] Subtask 4.1: Define `GET /traces/{trace_id}` endpoint
  - [ ] Subtask 4.2: Validate trace_id format (32-hex W3C trace ID)
  - [ ] Subtask 4.3: Call ObservabilityService.get_trace_with_spans()
  - [ ] Subtask 4.4: Return 404 if trace not found
  - [ ] Subtask 4.5: Return TraceDetailResponse with spans ordered by start_time

- [ ] Task 5: Implement chat history endpoint (AC: #3, #7, #8)
  - [ ] Subtask 5.1: Define `GET /chat-history` endpoint with query parameters
  - [ ] Subtask 5.2: Accept filters: user_id, kb_id, session_id, search_query, start_date, end_date
  - [ ] Subtask 5.3: Accept pagination: skip (default 0), limit (default 50, max 500)
  - [ ] Subtask 5.4: Call ObservabilityService.list_chat_messages() with filters
  - [ ] Subtask 5.5: Return ChatHistoryResponse with messages and session info

- [ ] Task 6: Implement document timeline endpoint (AC: #4)
  - [ ] Subtask 6.1: Define `GET /documents/{document_id}/timeline` endpoint
  - [ ] Subtask 6.2: Validate document_id is valid UUID
  - [ ] Subtask 6.3: Call ObservabilityService.get_document_timeline()
  - [ ] Subtask 6.4: Return 404 if no events found for document
  - [ ] Subtask 6.5: Return DocumentTimelineResponse with events ordered by timestamp

- [ ] Task 7: Implement stats endpoint (AC: #5)
  - [ ] Subtask 7.1: Define `GET /stats` endpoint with query parameters
  - [ ] Subtask 7.2: Accept time_period: hour, day, week, month (default: day)
  - [ ] Subtask 7.3: Accept optional filters: kb_id, user_id
  - [ ] Subtask 7.4: Call ObservabilityService.get_aggregated_stats()
  - [ ] Subtask 7.5: Return ObservabilityStatsResponse with metrics breakdown

- [ ] Task 8: Add ObservabilityService query methods
  - [ ] Subtask 8.1: Implement list_traces() with SQLAlchemy query
  - [ ] Subtask 8.2: Implement get_trace_with_spans() joining traces and spans
  - [ ] Subtask 8.3: Implement list_chat_messages() with full-text search support
  - [ ] Subtask 8.4: Implement get_document_timeline() filtering by document_id
  - [ ] Subtask 8.5: Implement get_aggregated_stats() using metrics_aggregates table

- [ ] Task 9: Write integration tests (AC: #10)
  - [ ] Subtask 9.1: Test traces list with various filters
  - [ ] Subtask 9.2: Test trace detail returns spans correctly
  - [ ] Subtask 9.3: Test chat history pagination and search
  - [ ] Subtask 9.4: Test document timeline for known document
  - [ ] Subtask 9.5: Test stats aggregation by time period
  - [ ] Subtask 9.6: Test 403 for non-admin users
  - [ ] Subtask 9.7: Test 404 for non-existent resources
  - [ ] Subtask 9.8: Test pagination limits enforced

## Dev Notes

### Architecture Patterns

- **Repository Pattern**: ObservabilityService encapsulates all database queries
- **Admin-Only Access**: All endpoints use `require_admin` dependency
- **Fire-and-Forget Writes, Sync Reads**: Writes are async fire-and-forget, reads are sync for consistency
- **Pagination Pattern**: Use skip/limit with max limits to prevent large queries

### Key Technical Decisions

- **W3C Trace ID Format**: trace_id is 32-hex string, validated via regex
- **Date Range Filtering**: Always filter by created_at using TimescaleDB time_bucket efficiency
- **Full-Text Search**: Chat history search uses PostgreSQL `ILIKE` for simplicity (no tsvector needed for MVP)
- **Stats Pre-Computation**: Stats endpoint reads from pre-computed `metrics_aggregates` table

### API Endpoint Specifications

```python
# backend/app/api/v1/observability.py

from fastapi import APIRouter, Depends, Query, HTTPException
from app.core.auth import require_admin
from app.services.observability_service import ObservabilityService
from app.schemas.observability import (
    TraceListResponse,
    TraceDetailResponse,
    ChatHistoryResponse,
    DocumentTimelineResponse,
    ObservabilityStatsResponse,
)

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/traces", response_model=TraceListResponse)
async def list_traces(
    operation_type: str | None = Query(
        default=None,
        description="Filter by operation type (e.g., chat_completion, document_processing)",
    ),
    trace_status: str | None = Query(
        default=None,
        alias="status",
        description="Filter by status: in_progress, completed, failed",
    ),
    user_id: UUID | None = Query(default=None, description="Filter by user ID"),
    kb_id: UUID | None = Query(default=None, description="Filter by knowledge base ID"),
    start_date: datetime | None = Query(default=None, description="Filter traces after this date"),
    end_date: datetime | None = Query(default=None, description="Filter traces before this date"),
    search: str | None = Query(
        default=None,
        description="Search in trace ID or trace name (case-insensitive)",
    ),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return (max 100)"),
    _admin: User = Depends(get_current_administrator),
    session: AsyncSession = Depends(get_async_session),
) -> TraceListResponse:
    """List traces with filters and pagination.

    Returns a paginated list of traces matching the specified filters.
    Traces are ordered by start time (newest first).

    **Requires admin authentication.**
    """
    ...


@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
async def get_trace(
    trace_id: str,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Get trace detail with all child spans."""
    ...


@router.get("/chat-history", response_model=ChatHistoryResponse)
async def get_chat_history(
    user_id: str | None = None,
    kb_id: str | None = None,
    session_id: str | None = None,
    search_query: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Query persistent chat history with filters."""
    ...


@router.get("/documents/{document_id}/timeline", response_model=DocumentTimelineResponse)
async def get_document_timeline(
    document_id: str,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Get document processing events timeline."""
    ...


@router.get("/stats", response_model=ObservabilityStatsResponse)
async def get_stats(
    time_period: str = Query(default="day", regex="^(hour|day|week|month)$"),
    kb_id: str | None = None,
    user_id: str | None = None,
    admin=Depends(require_admin),
    db=Depends(get_db),
):
    """Get aggregated observability statistics."""
    ...
```

### Schema Definitions

```python
# backend/app/schemas/observability.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class TraceListItem(BaseModel):
    trace_id: str = Field(..., description="W3C Trace ID (32-hex)")
    name: str = Field(..., description="Trace name/operation type")
    status: str = Field(..., description="Status: in_progress, completed, failed")
    user_id: Optional[UUID] = Field(None, description="User who initiated the operation")
    kb_id: Optional[UUID] = Field(None, description="Knowledge base context")
    document_id: Optional[UUID] = Field(None, description="Associated document ID (from metadata)")
    started_at: datetime
    ended_at: Optional[datetime]
    duration_ms: Optional[int]
    span_count: int = Field(..., description="Number of child spans")


class TraceListResponse(BaseModel):
    items: list[TraceListItem]
    total: int
    skip: int
    limit: int


class SpanDetail(BaseModel):
    span_id: str = Field(..., description="W3C Span ID (16-hex)")
    parent_span_id: Optional[str]
    name: str
    span_type: str = Field(..., description="Type: llm, db, external, internal")
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_ms: Optional[int]
    metadata: Optional[dict] = Field(None, description="Type-specific metrics")


class TraceDetailResponse(BaseModel):
    trace_id: str
    operation_type: str
    status: str
    user_id: Optional[UUID]
    kb_id: Optional[UUID]
    document_id: Optional[UUID]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_ms: Optional[int]
    spans: list[SpanDetail] = Field(..., description="Child spans ordered by start time")


class ChatMessageItem(BaseModel):
    id: UUID
    trace_id: str
    session_id: str
    role: str = Field(..., description="user or assistant")
    content: str
    user_id: UUID
    kb_id: UUID
    created_at: datetime
    token_count: Optional[int]
    response_time_ms: Optional[int]
    citations: Optional[list[dict]]


class ChatHistoryResponse(BaseModel):
    items: list[ChatMessageItem]
    total: int
    skip: int
    limit: int


class DocumentEventItem(BaseModel):
    id: UUID
    trace_id: str
    step_name: str = Field(..., description="Step: upload, parse, chunk, embed, index")
    status: str = Field(..., description="Status: started, completed, failed")
    started_at: datetime
    ended_at: Optional[datetime]
    duration_ms: Optional[int]
    metrics: Optional[dict] = Field(None, description="Step-specific metrics")
    error_message: Optional[str]


class DocumentTimelineResponse(BaseModel):
    document_id: UUID
    events: list[DocumentEventItem]
    total_duration_ms: Optional[int]


class ObservabilityStatsResponse(BaseModel):
    time_period: str
    llm_usage: dict = Field(..., description="Token counts and costs by model")
    processing_metrics: dict = Field(..., description="Document processing stats")
    chat_metrics: dict = Field(..., description="Chat activity stats")
    error_rate: float = Field(..., description="Percentage of failed traces")
```

### Source Tree Changes

```
backend/
├── app/
│   ├── api/v1/
│   │   └── observability.py         # New: API router
│   ├── schemas/
│   │   └── observability.py         # New: Pydantic schemas
│   └── services/
│       └── observability_service.py # Modified: Add query methods
└── tests/
    └── integration/
        └── test_observability_api.py  # New: Integration tests
```

### Testing Standards

- All endpoints tested with admin and non-admin users
- Pagination edge cases: skip=0, limit=max, empty results
- Date range filtering with various ranges
- Search query with partial matches
- 404 responses for non-existent resources

### Configuration Dependencies

No new configuration needed - uses existing database and admin auth.

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#6.1 API Endpoints]
- [Source: docs/epics/epic-9-observability.md]
- [Source: backend/app/api/v1/admin.py - existing admin endpoints pattern]
- [Source: backend/app/core/auth.py - require_admin dependency]

## Dev Agent Record

### Context Reference

- [9-7-observability-admin-api.context.xml](9-7-observability-admin-api.context.xml)

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Story drafted | Claude (SM Agent) |
