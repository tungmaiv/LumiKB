# ATDD Checklist - Epic 9, Story 9-7: Observability Admin API

**Date:** 2025-12-15
**Author:** Tung Vu
**Primary Test Level:** API/Integration Tests

---

## Story Summary

Expose REST API endpoints for querying observability data including traces, chat history, document processing events, and aggregated statistics for admin dashboard use.

**As a** system administrator
**I want** REST API endpoints for querying observability data
**So that** I can access observability information programmatically for debugging, monitoring, and building admin dashboard views

---

## Acceptance Criteria

1. GET /api/v1/observability/traces - list traces with filters (operation_type, status, user_id, date range)
2. GET /api/v1/observability/traces/{trace_id} - trace detail with all child spans
3. GET /api/v1/observability/chat-history - query chat messages with filters (user_id, kb_id, session_id, date range)
4. GET /api/v1/observability/documents/{document_id}/timeline - document processing events for a specific document
5. GET /api/v1/observability/stats - aggregated statistics (token usage, costs, processing metrics)
6. All endpoints require admin authentication (require_admin dependency)
7. Pagination with skip/limit (max 100 traces per page, max 500 messages per page)
8. Date range filtering on all list endpoints (start_date, end_date query parameters)
9. OpenAPI schemas documented with examples and descriptions
10. Integration tests for all endpoints with positive and negative test cases

---

## Failing Tests Created (RED Phase)

### API/Integration Tests (18 tests)

**File:** `backend/tests/integration/test_observability_api.py` (~450 lines)

#### Traces Endpoint Tests

- [ ] **Test:** `test_list_traces_returns_paginated_results`
  - **Status:** RED - No /api/v1/observability/traces endpoint exists
  - **Verifies:** AC-9.7.1, AC-9.7.7 - GET /traces returns TraceListResponse with items, total, skip, limit

- [ ] **Test:** `test_list_traces_filters_by_operation_type`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.1 - Filter by operation_type (document_processing, chat, search)

- [ ] **Test:** `test_list_traces_filters_by_status`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.1 - Filter by status (pending, running, completed, failed)

- [ ] **Test:** `test_list_traces_filters_by_date_range`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.8 - Filter by start_date and end_date query params

- [ ] **Test:** `test_list_traces_enforces_max_limit`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.7 - max 100 traces per page (limit > 100 capped)

- [ ] **Test:** `test_get_trace_detail_returns_spans`
  - **Status:** RED - No /traces/{trace_id} endpoint exists
  - **Verifies:** AC-9.7.2 - Returns TraceDetailResponse with spans array

- [ ] **Test:** `test_get_trace_detail_returns_404_for_unknown_trace`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.2 - Returns 404 Not Found for non-existent trace_id

#### Chat History Endpoint Tests

- [ ] **Test:** `test_list_chat_history_returns_messages`
  - **Status:** RED - No /chat-history endpoint exists
  - **Verifies:** AC-9.7.3 - Returns ChatHistoryResponse with messages

- [ ] **Test:** `test_list_chat_history_filters_by_user_id`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.3 - Filter by user_id query param

- [ ] **Test:** `test_list_chat_history_filters_by_kb_id`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.3 - Filter by kb_id query param

- [ ] **Test:** `test_list_chat_history_search_by_content`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.3 - Full-text search via search_query param

- [ ] **Test:** `test_list_chat_history_enforces_max_limit`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.7 - max 500 messages per page

#### Document Timeline Endpoint Tests

- [ ] **Test:** `test_get_document_timeline_returns_events`
  - **Status:** RED - No /documents/{document_id}/timeline endpoint exists
  - **Verifies:** AC-9.7.4 - Returns DocumentTimelineResponse with events

- [ ] **Test:** `test_get_document_timeline_returns_404_for_unknown_document`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.4 - Returns 404 for non-existent document

#### Stats Endpoint Tests

- [ ] **Test:** `test_get_stats_returns_aggregated_metrics`
  - **Status:** RED - No /stats endpoint exists
  - **Verifies:** AC-9.7.5 - Returns ObservabilityStatsResponse

- [ ] **Test:** `test_get_stats_filters_by_time_period`
  - **Status:** RED - No endpoint exists
  - **Verifies:** AC-9.7.5 - time_period param (hour, day, week, month)

#### Auth Tests

- [ ] **Test:** `test_endpoints_require_admin_auth`
  - **Status:** RED - No endpoints exist
  - **Verifies:** AC-9.7.6 - All endpoints return 403 for non-admin users

- [ ] **Test:** `test_endpoints_return_401_for_unauthenticated`
  - **Status:** RED - No endpoints exist
  - **Verifies:** AC-9.7.6 - All endpoints return 401 without auth

---

## Data Factories Created

### Trace Factory

**File:** `backend/tests/factories/observability_factory.py`

**Exports:**

- `create_trace(overrides?)` - Create single trace with optional overrides
- `create_traces(count)` - Create array of traces
- `create_span(trace_id, overrides?)` - Create span linked to trace
- `create_spans(trace_id, count)` - Create multiple spans for a trace

**Example Usage:**

```python
from tests.factories.observability_factory import create_trace, create_span

trace = create_trace(operation_type="chat", status="completed")
spans = [
    create_span(trace.trace_id, span_type="llm", model="gpt-4"),
    create_span(trace.trace_id, span_type="retrieval"),
]
```

### Chat Message Factory

**File:** `backend/tests/factories/observability_factory.py`

**Exports:**

- `create_obs_chat_message(overrides?)` - Create single chat message
- `create_obs_chat_messages(count)` - Create array of chat messages
- `create_chat_session(user_id, kb_id, message_count)` - Create session with messages

**Example Usage:**

```python
from tests.factories.observability_factory import create_chat_session

session = create_chat_session(
    user_id=admin_user.id,
    kb_id=knowledge_base.id,
    message_count=5
)
```

### Document Event Factory

**File:** `backend/tests/factories/observability_factory.py`

**Exports:**

- `create_document_event(document_id, overrides?)` - Create single document event
- `create_document_timeline(document_id)` - Create full processing timeline

**Example Usage:**

```python
from tests.factories.observability_factory import create_document_timeline

timeline = create_document_timeline(document_id=doc.id)
# Creates: upload, parse, chunk, embed, index events
```

---

## Fixtures Created

### Observability Test Fixtures

**File:** `backend/tests/integration/conftest.py` (additions)

**Fixtures:**

- `admin_user` - Admin user for authenticated requests
  - **Setup:** Creates user with is_superuser=True
  - **Provides:** User model instance
  - **Cleanup:** Rolled back via transaction

- `regular_user` - Non-admin user for 403 tests
  - **Setup:** Creates user with is_superuser=False
  - **Provides:** User model instance
  - **Cleanup:** Rolled back via transaction

- `sample_traces` - Pre-populated traces with spans
  - **Setup:** Creates 5 traces with various statuses and 2-5 spans each
  - **Provides:** List of Trace models
  - **Cleanup:** Rolled back via transaction

- `sample_chat_messages` - Pre-populated chat messages
  - **Setup:** Creates 20 messages across 3 sessions
  - **Provides:** List of ObsChatMessage models
  - **Cleanup:** Rolled back via transaction

- `sample_document_events` - Pre-populated document timeline
  - **Setup:** Creates full processing timeline for test document
  - **Provides:** List of DocumentEvent models
  - **Cleanup:** Rolled back via transaction

**Example Usage:**

```python
@pytest.mark.asyncio
async def test_list_traces_returns_paginated_results(
    client: AsyncClient,
    admin_auth_headers: dict,
    sample_traces: list[Trace],
):
    response = await client.get(
        "/api/v1/observability/traces",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) == len(sample_traces)
```

---

## Mock Requirements

### No External Mocks Required

This story tests database queries through the ObservabilityService. All data is seeded in the test database using fixtures. No external services need mocking.

**Notes:**
- Tests use the same async PostgreSQL test database with observability schema
- TimescaleDB hypertables work in test environment
- Fixtures seed data before each test and rollback after

---

## Required data-testid Attributes

Not applicable for API tests. UI tests are covered in Stories 9-8, 9-9, and 9-10.

---

## Implementation Checklist

### Test: test_list_traces_returns_paginated_results

**File:** `backend/tests/integration/test_observability_api.py`

**Tasks to make this test pass:**

- [ ] Create `backend/app/api/v1/observability.py` router file
- [ ] Add router to main app with prefix `/api/v1/observability`
- [ ] Define GET `/traces` endpoint with query parameters
- [ ] Create `TraceListResponse` schema in `backend/app/schemas/observability.py`
- [ ] Implement `ObservabilityService.list_traces()` method
- [ ] Apply `require_admin` dependency to endpoint
- [ ] Run test: `pytest backend/tests/integration/test_observability_api.py::test_list_traces_returns_paginated_results -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 2 hours

---

### Test: test_list_traces_filters_by_operation_type

**File:** `backend/tests/integration/test_observability_api.py`

**Tasks to make this test pass:**

- [ ] Add `operation_type` query parameter to `/traces` endpoint
- [ ] Add filter to `list_traces()` SQLAlchemy query
- [ ] Run test: `pytest backend/tests/integration/test_observability_api.py::test_list_traces_filters_by_operation_type -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: test_list_traces_filters_by_date_range

**File:** `backend/tests/integration/test_observability_api.py`

**Tasks to make this test pass:**

- [ ] Add `start_date` and `end_date` query parameters
- [ ] Add date range filter to `list_traces()` query
- [ ] Run test: `pytest backend/tests/integration/test_observability_api.py::test_list_traces_filters_by_date_range -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: test_get_trace_detail_returns_spans

**File:** `backend/tests/integration/test_observability_api.py`

**Tasks to make this test pass:**

- [ ] Define GET `/traces/{trace_id}` endpoint
- [ ] Create `TraceDetailResponse` schema with spans array
- [ ] Implement `ObservabilityService.get_trace_with_spans()` method
- [ ] Return spans ordered by start_time
- [ ] Run test: `pytest backend/tests/integration/test_observability_api.py::test_get_trace_detail_returns_spans -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: test_get_trace_detail_returns_404_for_unknown_trace

**File:** `backend/tests/integration/test_observability_api.py`

**Tasks to make this test pass:**

- [ ] Add 404 handling when trace not found
- [ ] Validate trace_id format (32-hex W3C trace ID)
- [ ] Run test: `pytest backend/tests/integration/test_observability_api.py::test_get_trace_detail_returns_404_for_unknown_trace -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: test_list_chat_history_returns_messages

**File:** `backend/tests/integration/test_observability_api.py`

**Tasks to make this test pass:**

- [ ] Define GET `/chat-history` endpoint
- [ ] Create `ChatHistoryResponse` schema
- [ ] Implement `ObservabilityService.list_chat_messages()` method
- [ ] Run test: `pytest backend/tests/integration/test_observability_api.py::test_list_chat_history_returns_messages -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: test_list_chat_history_search_by_content

**File:** `backend/tests/integration/test_observability_api.py`

**Tasks to make this test pass:**

- [ ] Add `search_query` parameter to `/chat-history` endpoint
- [ ] Implement ILIKE search in `list_chat_messages()` query
- [ ] Run test: `pytest backend/tests/integration/test_observability_api.py::test_list_chat_history_search_by_content -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: test_get_document_timeline_returns_events

**File:** `backend/tests/integration/test_observability_api.py`

**Tasks to make this test pass:**

- [ ] Define GET `/documents/{document_id}/timeline` endpoint
- [ ] Create `DocumentTimelineResponse` schema
- [ ] Implement `ObservabilityService.get_document_timeline()` method
- [ ] Return events ordered by timestamp
- [ ] Run test: `pytest backend/tests/integration/test_observability_api.py::test_get_document_timeline_returns_events -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: test_get_stats_returns_aggregated_metrics

**File:** `backend/tests/integration/test_observability_api.py`

**Tasks to make this test pass:**

- [ ] Define GET `/stats` endpoint
- [ ] Create `ObservabilityStatsResponse` schema
- [ ] Implement `ObservabilityService.get_aggregated_stats()` method
- [ ] Query from metrics_aggregates table
- [ ] Run test: `pytest backend/tests/integration/test_observability_api.py::test_get_stats_returns_aggregated_metrics -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: test_endpoints_require_admin_auth

**File:** `backend/tests/integration/test_observability_api.py`

**Tasks to make this test pass:**

- [ ] Apply `require_admin` dependency to all endpoints
- [ ] Verify non-admin user receives 403 Forbidden
- [ ] Run test: `pytest backend/tests/integration/test_observability_api.py::test_endpoints_require_admin_auth -v`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.5 hours

---

## Running Tests

```bash
# Run all failing tests for this story
pytest backend/tests/integration/test_observability_api.py -v

# Run specific test file
pytest backend/tests/integration/test_observability_api.py -v

# Run with coverage
pytest backend/tests/integration/test_observability_api.py --cov=app/api/v1/observability --cov-report=term-missing

# Run specific test
pytest backend/tests/integration/test_observability_api.py::test_list_traces_returns_paginated_results -v

# Debug specific test
pytest backend/tests/integration/test_observability_api.py::test_list_traces_returns_paginated_results -v -s --pdb
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

- [ ] All tests written and failing
- [ ] Fixtures and factories created with auto-cleanup
- [ ] Mock requirements documented
- [ ] Implementation checklist created

**Verification:**

- All tests run and fail as expected
- Failure messages are clear and actionable
- Tests fail due to missing implementation, not test bugs

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Pick one failing test** from implementation checklist (start with `test_list_traces_returns_paginated_results`)
2. **Read the test** to understand expected behavior
3. **Implement minimal code** to make that specific test pass
4. **Run the test** to verify it now passes (green)
5. **Check off the task** in implementation checklist
6. **Move to next test** and repeat

**Key Principles:**

- One test at a time (don't try to fix all at once)
- Minimal implementation (don't over-engineer)
- Run tests frequently (immediate feedback)
- Use implementation checklist as roadmap

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

**DEV Agent Responsibilities:**

1. **Verify all tests pass** (green phase complete)
2. **Review code for quality** (readability, maintainability, performance)
3. **Extract duplications** (DRY principle)
4. **Optimize performance** (if needed)
5. **Ensure tests still pass** after each refactor
6. **Update documentation** (if API contracts change)

---

## Next Steps

1. **Review this checklist** with team in standup or planning
2. **Run failing tests** to confirm RED phase: `pytest backend/tests/integration/test_observability_api.py -v`
3. **Begin implementation** using implementation checklist as guide
4. **Work one test at a time** (red -> green for each)
5. **Share progress** in daily standup
6. **When all tests pass**, refactor code for quality
7. **When refactoring complete**, run `bmad sm story-done` to move story to DONE

---

## Knowledge Base References Applied

This ATDD workflow consulted the following knowledge fragments:

- **fixture-architecture.md** - Test fixture patterns with setup/teardown and auto-cleanup
- **data-factories.md** - Factory patterns using faker for random test data generation
- **network-first.md** - N/A for backend API tests
- **test-quality.md** - Test design principles (Given-When-Then, isolation, determinism)
- **test-levels-framework.md** - API/Integration tests selected as primary level

See `tea-index.csv` for complete knowledge fragment mapping.

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `pytest backend/tests/integration/test_observability_api.py -v`

**Results:**

```
FAILED test_list_traces_returns_paginated_results - 404 Client Error: Not Found
FAILED test_list_traces_filters_by_operation_type - 404 Client Error: Not Found
FAILED test_list_traces_filters_by_status - 404 Client Error: Not Found
FAILED test_list_traces_filters_by_date_range - 404 Client Error: Not Found
FAILED test_list_traces_enforces_max_limit - 404 Client Error: Not Found
FAILED test_get_trace_detail_returns_spans - 404 Client Error: Not Found
FAILED test_get_trace_detail_returns_404_for_unknown_trace - 404 Client Error: Not Found
FAILED test_list_chat_history_returns_messages - 404 Client Error: Not Found
FAILED test_list_chat_history_filters_by_user_id - 404 Client Error: Not Found
FAILED test_list_chat_history_filters_by_kb_id - 404 Client Error: Not Found
FAILED test_list_chat_history_search_by_content - 404 Client Error: Not Found
FAILED test_list_chat_history_enforces_max_limit - 404 Client Error: Not Found
FAILED test_get_document_timeline_returns_events - 404 Client Error: Not Found
FAILED test_get_document_timeline_returns_404_for_unknown_document - 404 Client Error: Not Found
FAILED test_get_stats_returns_aggregated_metrics - 404 Client Error: Not Found
FAILED test_get_stats_filters_by_time_period - 404 Client Error: Not Found
FAILED test_endpoints_require_admin_auth - 404 Client Error: Not Found
FAILED test_endpoints_return_401_for_unauthenticated - 404 Client Error: Not Found
```

**Summary:**

- Total tests: 18
- Passing: 0 (expected)
- Failing: 18 (expected)
- Status: RED phase verified - all tests fail because endpoints don't exist

---

## Notes

- TimescaleDB hypertables require time-based filtering for optimal query performance
- Composite primary keys (trace_id + timestamp) require both fields for updates
- W3C Trace ID is 32-hex string format
- Chat history search uses ILIKE for MVP; consider tsvector for scale
- Stats endpoint reads from pre-computed metrics_aggregates table

---

## Contact

**Questions or Issues?**

- Ask in team standup
- Refer to `./bmad/docs/tea-README.md` for workflow documentation
- Consult `./bmad/testarch/knowledge` for testing best practices

---

**Generated by BMad TEA Agent** - 2025-12-15
