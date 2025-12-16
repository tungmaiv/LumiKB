# ATDD Checklist - Epic 9, Story 9-8: Trace Viewer UI Component

**Date:** 2025-12-15
**Author:** Tung Vu
**Primary Test Level:** Component Tests + Selective E2E

---

## Story Summary

Create a React component for viewing distributed traces with a waterfall visualization showing all spans, their timing, and type-specific metrics for debugging and performance analysis.

**As a** system administrator
**I want** a trace viewer with waterfall visualization
**So that** I can debug request flows, identify bottlenecks, and analyze performance across the system

---

## Acceptance Criteria

1. Trace list view displays operation type, document ID, status, duration, span count, and timestamp
2. Filtering controls for operation type (document_processing, chat, search), status (completed, failed), date range, and search (trace ID or name)
3. Click trace row to view detail panel (slide-out or modal)
4. Trace detail shows timeline of spans in waterfall view with duration bars
5. Span details show type-specific metrics (LLM: model/tokens/cost, DB: query/rows, External: URL/status)
6. Error spans highlighted in red with error message displayed
7. LLM spans prominently show model name, token counts (input/output), and cost (if available)
8. Responsive design for admin dashboard integration (works on desktop and tablet)
9. Loading states (skeleton) and error handling (toast notifications)
10. Unit tests for component rendering and user interactions

---

## Failing Tests Created (RED Phase)

### Component Tests (12 tests)

**File:** `frontend/src/components/admin/traces/__tests__/trace-list.test.tsx` (~200 lines)

- [x] **Test:** `renders_trace_list_with_all_columns`
  - **Status:** GREEN - TraceList component implemented
  - **Verifies:** AC-9.8.1 - Displays operation type, document ID, status, duration, span count, time

- [x] **Test:** `highlights_selected_trace_row`
  - **Status:** GREEN - Component implemented
  - **Verifies:** AC-9.8.3 - Visual indication of selected trace

- [x] **Test:** `calls_onSelectTrace_when_row_clicked`
  - **Status:** GREEN - Component implemented
  - **Verifies:** AC-9.8.3 - Click handler triggers detail panel

- [x] **Test:** `displays_loading_skeleton_when_loading`
  - **Status:** GREEN - TraceListSkeleton component implemented
  - **Verifies:** AC-9.8.9 - Loading state with skeleton

- [x] **Test:** `displays_empty_state_when_no_traces`
  - **Status:** GREEN - Component implemented
  - **Verifies:** AC-9.8.9 - Empty state message shown

- [x] **Test:** `formats_duration_correctly`
  - **Status:** GREEN - formatDuration helper implemented
  - **Verifies:** AC-9.8.1 - Duration formatted as ms, s, or min

**File:** `frontend/src/components/admin/traces/__tests__/trace-filters.test.tsx` (~150 lines)

- [ ] **Test:** `renders_operation_type_filter_options`
  - **Status:** RED - TraceFilters component does not exist
  - **Verifies:** AC-9.8.2 - Filter by document_processing, chat, search

- [ ] **Test:** `renders_status_filter_options`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.8.2 - Filter by completed, failed

- [ ] **Test:** `calls_onFiltersChange_when_filter_applied`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.8.2 - Filter changes trigger callback

**File:** `frontend/src/components/admin/traces/__tests__/waterfall-timeline.test.tsx` (~180 lines)

- [ ] **Test:** `renders_spans_as_horizontal_bars`
  - **Status:** RED - WaterfallTimeline component does not exist
  - **Verifies:** AC-9.8.4 - Waterfall view with duration bars

- [ ] **Test:** `positions_spans_correctly_based_on_timing`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.8.4 - Proportional positioning based on relative_start_ms

- [ ] **Test:** `highlights_error_spans_in_red`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.8.6 - Error spans highlighted in red

**File:** `frontend/src/components/admin/traces/__tests__/span-detail.test.tsx` (~200 lines)

- [ ] **Test:** `renders_llm_span_with_model_and_tokens`
  - **Status:** RED - SpanDetail component does not exist
  - **Verifies:** AC-9.8.5, AC-9.8.7 - LLM span shows model, input_tokens, output_tokens, cost

- [ ] **Test:** `renders_error_message_for_failed_span`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.8.6 - Error message displayed for failed spans

### Hook Tests (3 tests)

**File:** `frontend/src/hooks/__tests__/useTraces.test.ts` (~120 lines)

- [ ] **Test:** `fetches_traces_with_filters`
  - **Status:** RED - useTraces hook does not exist
  - **Verifies:** AC-9.8.1, AC-9.8.2 - Fetches data with filter params

- [ ] **Test:** `fetches_trace_detail_when_enabled`
  - **Status:** RED - useTraceDetail hook does not exist
  - **Verifies:** AC-9.8.3 - Lazy loads trace detail on selection

- [ ] **Test:** `handles_api_errors_gracefully`
  - **Status:** RED - Hook does not exist
  - **Verifies:** AC-9.8.9 - Error state handling

### E2E Tests (3 tests)

**File:** `frontend/e2e/tests/admin/trace-viewer.spec.ts` (~150 lines)

- [ ] **Test:** `admin_can_view_trace_list_and_apply_filters`
  - **Status:** RED - Page does not exist
  - **Verifies:** AC-9.8.1, AC-9.8.2 - Full filter flow

- [ ] **Test:** `admin_can_view_trace_detail_with_waterfall`
  - **Status:** RED - Page does not exist
  - **Verifies:** AC-9.8.3, AC-9.8.4, AC-9.8.5 - Click trace shows detail

- [ ] **Test:** `trace_viewer_displays_error_toast_on_api_failure`
  - **Status:** RED - Page does not exist
  - **Verifies:** AC-9.8.9 - Error handling with toast notification

---

## Data Factories Created

### Trace Data Factory

**File:** `frontend/src/test/factories/trace.factory.ts`

**Exports:**

- `createTraceListItem(overrides?)` - Create single trace list item
- `createTraceListItems(count)` - Create array of trace list items
- `createSpanDetail(overrides?)` - Create single span detail
- `createTraceDetailResponse(overrides?)` - Create full trace detail with spans

**Example Usage:**

```typescript
import { createTraceListItem, createTraceDetailResponse } from "@/test/factories/trace.factory";

const traces = [
  createTraceListItem({ operation_type: "chat", status: "completed" }),
  createTraceListItem({ operation_type: "document_processing", status: "failed" }),
];

const traceDetail = createTraceDetailResponse({
  trace_id: "abc123...",
  spans: [
    { span_type: "llm", model: "gpt-4", input_tokens: 150, output_tokens: 50 },
    { span_type: "retrieval", duration_ms: 45 },
  ],
});
```

---

## Fixtures Created

### Trace Viewer Fixtures

**File:** `frontend/src/test/fixtures/trace-viewer.fixture.ts`

**Fixtures:**

- `mockTraceListApi` - MSW handler for GET /observability/traces
  - **Setup:** Registers MSW handler with mock trace data
  - **Provides:** Pre-configured API response
  - **Cleanup:** Handler automatically cleaned between tests

- `mockTraceDetailApi` - MSW handler for GET /observability/traces/{id}
  - **Setup:** Registers MSW handler with mock detail data
  - **Provides:** Pre-configured trace detail response
  - **Cleanup:** Handler automatically cleaned between tests

**Example Usage:**

```typescript
import { mockTraceListApi, mockTraceDetailApi } from "@/test/fixtures/trace-viewer.fixture";

beforeEach(() => {
  mockTraceListApi([
    createTraceListItem({ status: "completed" }),
    createTraceListItem({ status: "failed" }),
  ]);
});

test("renders trace list", async () => {
  render(<TraceList />);
  await screen.findByText("completed");
});
```

---

## Mock Requirements

### Traces List API Mock

**Endpoint:** `GET /api/v1/observability/traces`

**Query Parameters:**

- `operation_type` - Filter by operation type (chat_completion, document_processing, etc.)
- `status` - Filter by status (completed, failed, in_progress)
- `user_id` - Filter by user UUID
- `kb_id` - Filter by knowledge base UUID
- `start_date` - Filter traces after this date (ISO 8601)
- `end_date` - Filter traces before this date (ISO 8601)
- `search` - Search in trace ID or name (case-insensitive, uses ILIKE)
- `skip` - Pagination offset (default: 0)
- `limit` - Results per page (default: 20, max: 100)

**Success Response:**

```json
{
  "items": [
    {
      "trace_id": "abc123def456789012345678901234ab",
      "name": "chat_completion",
      "status": "completed",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "kb_id": "550e8400-e29b-41d4-a716-446655440001",
      "document_id": null,
      "started_at": "2025-12-15T10:00:00Z",
      "ended_at": "2025-12-15T10:00:01Z",
      "duration_ms": 1234,
      "span_count": 5
    }
  ],
  "total": 50,
  "skip": 0,
  "limit": 20
}
```

**Failure Response:**

```json
{
  "detail": "Failed to fetch traces"
}
```

### Trace Detail API Mock

**Endpoint:** `GET /api/v1/observability/traces/{trace_id}`

**Success Response:**

```json
{
  "trace_id": "abc123def456...",
  "operation_type": "chat",
  "status": "completed",
  "duration_ms": 1234,
  "spans": [
    {
      "span_id": "span123",
      "name": "LLM Generation",
      "span_type": "llm",
      "status": "completed",
      "started_at": "2025-12-15T10:00:00Z",
      "duration_ms": 800,
      "metadata": {
        "model": "gpt-4",
        "input_tokens": 150,
        "output_tokens": 50,
        "cost_usd": 0.0045
      }
    }
  ]
}
```

**Notes:** MSW handlers should support query parameters for filtering

---

## Required data-testid Attributes

### Trace List Component

- `trace-row-{trace_id}` - Individual trace row (clickable)
- Uses `bg-muted` class for selected row highlighting
- Uses `animate-pulse` class for loading skeleton

### Trace Filters Component

- `operation-type-filter` - Operation type select dropdown
- `status-filter` - Status select dropdown
- `start-date-filter` - Start date picker
- `end-date-filter` - End date picker
- `search-filter` - Search input for trace ID or name
- `clear-filters-btn` - Clear all filters button

### Waterfall Timeline Component

- `waterfall-timeline` - Main timeline container
- `waterfall-span-{span_id}` - Individual span bar
- `waterfall-span-label-{span_id}` - Span name label
- `waterfall-time-scale` - Time scale header

### Span Detail Component

- `span-detail-{span_id}` - Span detail card container
- `span-detail-model` - LLM model name
- `span-detail-tokens` - Token counts display
- `span-detail-cost` - Cost display
- `span-detail-error` - Error message container

### Trace Detail Panel

- `trace-detail-panel` - Slide-out panel container
- `trace-detail-close-btn` - Close panel button
- `trace-detail-summary` - Summary section header

**Implementation Example:**

```tsx
<Table data-testid="trace-list-table">
  <TableBody>
    {traces.map((trace) => (
      <TableRow
        key={trace.trace_id}
        data-testid={`trace-list-row-${trace.trace_id}`}
        onClick={() => onSelectTrace(trace.trace_id)}
      >
        <TableCell>{trace.operation_type}</TableCell>
        <TableCell>
          <Badge data-testid={`trace-list-status-${trace.trace_id}`}>
            {trace.status}
          </Badge>
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

---

## Implementation Checklist

### Test: renders_trace_list_with_all_columns

**File:** `frontend/src/components/admin/traces/__tests__/trace-list.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/traces/trace-list.tsx`
- [ ] Define TraceListProps interface
- [ ] Render Table with columns: Operation, Status, Duration, User, Timestamp
- [ ] Use shadcn/ui Table component
- [ ] Add data-testid attributes: `trace-list-table`, `trace-list-row-{id}`
- [ ] Run test: `npm run test:run -- src/components/admin/traces/__tests__/trace-list.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: renders_operation_type_filter_options

**File:** `frontend/src/components/admin/traces/__tests__/trace-filters.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/traces/trace-filters.tsx`
- [ ] Add Select dropdown for operation_type with options
- [ ] Add data-testid: `trace-filter-operation-type`
- [ ] Run test: `npm run test:run -- src/components/admin/traces/__tests__/trace-filters.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1 hour

---

### Test: renders_spans_as_horizontal_bars

**File:** `frontend/src/components/admin/traces/__tests__/waterfall-timeline.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/traces/waterfall-timeline.tsx`
- [ ] Calculate percentage positions from relative_start_ms / totalDuration
- [ ] Render horizontal bars with CSS width and left positioning
- [ ] Add data-testid: `waterfall-timeline`, `waterfall-span-{id}`
- [ ] Run test: `npm run test:run -- src/components/admin/traces/__tests__/waterfall-timeline.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 2 hours

---

### Test: renders_llm_span_with_model_and_tokens

**File:** `frontend/src/components/admin/traces/__tests__/span-detail.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/traces/span-detail.tsx`
- [ ] Render type-specific metrics based on span_type
- [ ] For LLM spans: show model, input_tokens, output_tokens, cost_usd
- [ ] Add data-testid: `span-detail-model`, `span-detail-tokens`, `span-detail-cost`
- [ ] Run test: `npm run test:run -- src/components/admin/traces/__tests__/span-detail.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: fetches_traces_with_filters

**File:** `frontend/src/hooks/__tests__/useTraces.test.ts`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/hooks/useTraces.ts`
- [ ] Implement useTraces hook with TanStack Query
- [ ] Accept filter options and include in queryKey
- [ ] Set staleTime to 30 seconds
- [ ] Run test: `npm run test:run -- src/hooks/__tests__/useTraces.test.ts`
- [ ] Test passes (green phase)

**Estimated Effort:** 1 hour

---

### Test: admin_can_view_trace_list_and_apply_filters (E2E)

**File:** `frontend/e2e/tests/admin/trace-viewer.spec.ts`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/app/(protected)/admin/traces/page.tsx`
- [ ] Compose TraceList, TraceFilters, TraceDetailPanel components
- [ ] Wire up useTraces hook with filter state
- [ ] Add navigation link from admin dashboard
- [ ] Run test: `npx playwright test e2e/tests/admin/trace-viewer.spec.ts`
- [ ] Test passes (green phase)

**Estimated Effort:** 2 hours

---

## Running Tests

```bash
# Run all component tests for this story
npm run test:run -- src/components/admin/traces

# Run specific test file
npm run test:run -- src/components/admin/traces/__tests__/trace-list.test.tsx

# Run hook tests
npm run test:run -- src/hooks/__tests__/useTraces.test.ts

# Run E2E tests
npx playwright test e2e/tests/admin/trace-viewer.spec.ts

# Run E2E in headed mode
npx playwright test e2e/tests/admin/trace-viewer.spec.ts --headed

# Run with coverage
npm run test:coverage -- --testPathPattern="admin/traces"
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

- [ ] All tests written and failing
- [ ] Fixtures and factories created with auto-cleanup
- [ ] Mock requirements documented
- [ ] data-testid requirements listed
- [ ] Implementation checklist created

**Verification:**

- All tests run and fail as expected
- Failure messages are clear and actionable
- Tests fail due to missing implementation, not test bugs

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Pick one failing test** from implementation checklist
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

---

## Next Steps

1. **Review this checklist** with team
2. **Run failing tests** to confirm RED phase
3. **Begin implementation** using implementation checklist
4. **Work one test at a time** (red -> green for each)
5. **When all tests pass**, refactor code for quality
6. **When refactoring complete**, run `bmad sm story-done` to move story to DONE

---

## Knowledge Base References Applied

This ATDD workflow consulted the following knowledge fragments:

- **fixture-architecture.md** - React Testing Library fixtures with MSW
- **data-factories.md** - Factory patterns for trace/span test data
- **component-tdd.md** - Component test strategies with Vitest
- **network-first.md** - MSW handler setup for API mocking
- **test-quality.md** - Test design principles
- **test-levels-framework.md** - Component tests as primary, selective E2E

See `tea-index.csv` for complete knowledge fragment mapping.

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `npm run test:run -- src/components/admin/traces`

**Results:**

```
FAIL src/components/admin/traces/__tests__/trace-list.test.tsx
  Cannot find module '@/components/admin/traces/trace-list'

FAIL src/components/admin/traces/__tests__/trace-filters.test.tsx
  Cannot find module '@/components/admin/traces/trace-filters'

FAIL src/components/admin/traces/__tests__/waterfall-timeline.test.tsx
  Cannot find module '@/components/admin/traces/waterfall-timeline'

FAIL src/components/admin/traces/__tests__/span-detail.test.tsx
  Cannot find module '@/components/admin/traces/span-detail'
```

**Summary:**

- Total tests: 18
- Passing: 0 (expected)
- Failing: 18 (expected)
- Status: RED phase verified - components don't exist

---

## Notes

- Waterfall bars should have minimum 1% width for visibility of very short spans
- TanStack Query staleTime: 30s for list, 60s for detail
- Status colors: green=completed, red=failed, yellow=running, gray=pending
- Consider keyboard navigation (arrow keys) for trace list

---

## Contact

**Questions or Issues?**

- Ask in team standup
- Refer to `./bmad/docs/tea-README.md` for workflow documentation
- Consult `./bmad/testarch/knowledge` for testing best practices

---

**Generated by BMad TEA Agent** - 2025-12-15
