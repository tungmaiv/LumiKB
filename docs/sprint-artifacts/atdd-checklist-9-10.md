# ATDD Checklist - Epic 9, Story 9-10: Document Timeline UI

**Date:** 2025-12-15
**Author:** Tung Vu
**Primary Test Level:** Component Tests + Selective E2E

---

## Story Summary

Create a React component showing the document processing timeline with step-by-step visualization of upload, parse, chunk, embed, and index stages for troubleshooting document ingestion issues.

**As a** system administrator
**I want** a document processing timeline visualization
**So that** I can quickly identify which processing step failed or took longer than expected

---

## Acceptance Criteria

1. Access via "View Processing" button in document detail modal
2. Timeline visualization shows all processing steps in vertical layout
3. Each step shows status icon (pending=gray, in-progress=blue spinner, completed=green check, failed=red X)
4. Step duration displayed in human-readable format (e.g., "2.3s", "45ms")
5. Click step to see detailed metrics (chunks created, vectors generated, etc.)
6. Error steps show error type and full error message
7. Retry count visible for failed steps that were retried
8. Total processing time summarized at top of timeline
9. Responsive design for modal display
10. Unit tests for timeline rendering and interactions

---

## Failing Tests Created (RED Phase)

### Component Tests (13 tests)

**File:** `frontend/src/components/admin/documents/__tests__/processing-timeline.test.tsx` (~180 lines)

- [ ] **Test:** `renders_all_processing_steps`
  - **Status:** RED - ProcessingTimeline component does not exist
  - **Verifies:** AC-9.10.2 - Shows upload, parse, chunk, embed, index steps

- [ ] **Test:** `displays_total_processing_time`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.10.8 - Summary at top of timeline

- [ ] **Test:** `displays_loading_skeleton_when_loading`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.10.9 - Loading state

- [ ] **Test:** `displays_error_state_when_fetch_fails`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.10.9 - Error handling

**File:** `frontend/src/components/admin/documents/__tests__/timeline-step.test.tsx` (~200 lines)

- [ ] **Test:** `renders_step_name_and_duration`
  - **Status:** RED - TimelineStep component does not exist
  - **Verifies:** AC-9.10.4 - Duration in human-readable format

- [ ] **Test:** `expands_to_show_metrics_on_click`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.10.5 - Click to see detailed metrics

- [ ] **Test:** `displays_retry_count_badge_when_retried`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.10.7 - Retry count visible

**File:** `frontend/src/components/admin/documents/__tests__/status-icon.test.tsx` (~100 lines)

- [ ] **Test:** `renders_green_check_for_completed`
  - **Status:** RED - StatusIcon component does not exist
  - **Verifies:** AC-9.10.3 - Green check icon

- [ ] **Test:** `renders_red_x_for_failed`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.10.3 - Red X icon

- [ ] **Test:** `renders_spinning_loader_for_in_progress`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.10.3 - Blue spinner with animation

- [ ] **Test:** `renders_gray_circle_for_pending`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.10.3 - Gray circle icon

**File:** `frontend/src/components/admin/documents/__tests__/step-detail.test.tsx` (~180 lines)

- [ ] **Test:** `renders_error_message_for_failed_step`
  - **Status:** RED - StepDetail component does not exist
  - **Verifies:** AC-9.10.6 - Error type and message displayed

- [ ] **Test:** `renders_type_specific_metrics_for_each_step`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.10.5 - chunks, vectors, pages, etc.

### Hook Tests (2 tests)

**File:** `frontend/src/hooks/__tests__/useDocumentTimeline.test.ts` (~120 lines)

- [ ] **Test:** `fetches_timeline_for_document`
  - **Status:** RED - useDocumentTimeline hook does not exist
  - **Verifies:** AC-9.10.2 - Fetches timeline data

- [ ] **Test:** `polls_while_processing_in_progress`
  - **Status:** RED - Hook does not exist
  - **Verifies:** AC-9.10.3 - 2s polling interval

### E2E Tests (2 tests)

**File:** `frontend/e2e/tests/admin/document-timeline.spec.ts` (~120 lines)

- [ ] **Test:** `admin_can_view_document_processing_timeline`
  - **Status:** RED - Timeline not integrated into document modal
  - **Verifies:** AC-9.10.1, AC-9.10.2 - Access via "View Processing" button

- [ ] **Test:** `timeline_shows_error_details_for_failed_step`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.10.6 - Error display in timeline

---

## Data Factories Created

### Document Timeline Factory

**File:** `frontend/src/test/factories/document-timeline.factory.ts`

**Exports:**

- `createDocumentEvent(overrides?)` - Create single document event
- `createDocumentEvents(count)` - Create array of events
- `createDocumentTimeline(options?)` - Create full processing timeline
- `createStepMetrics(stepName)` - Create type-specific metrics

**Example Usage:**

```typescript
import {
  createDocumentTimeline,
  createDocumentEvent,
  createStepMetrics,
} from "@/test/factories/document-timeline.factory";

// Create complete timeline
const timeline = createDocumentTimeline({
  status: "completed",
  includeMetrics: true,
});

// Create specific events
const failedEvent = createDocumentEvent({
  step_name: "parse",
  status: "failed",
  error_message: "PDF parsing failed: corrupted file",
  retry_count: 2,
});

// Create step-specific metrics
const parseMetrics = createStepMetrics("parse");
// { pages_extracted: 15, text_length: 12500, parser_used: "pdfplumber" }

const chunkMetrics = createStepMetrics("chunk");
// { chunks_created: 42, avg_chunk_size: 512 }

const embedMetrics = createStepMetrics("embed");
// { vectors_generated: 42, embedding_model: "text-embedding-3-small" }
```

---

## Fixtures Created

### Document Timeline Fixtures

**File:** `frontend/src/test/fixtures/document-timeline.fixture.ts`

**Fixtures:**

- `mockDocumentTimelineApi` - MSW handler for GET /observability/documents/{id}/timeline
  - **Setup:** Registers MSW handler with mock timeline data
  - **Provides:** Pre-configured API response
  - **Cleanup:** Handler automatically cleaned between tests

- `mockPollingTimeline` - MSW handler that changes response over time
  - **Setup:** Returns in-progress timeline, then completed on next call
  - **Provides:** Simulates polling behavior
  - **Cleanup:** Resets call counter between tests

**Example Usage:**

```typescript
import { mockDocumentTimelineApi, mockPollingTimeline } from "@/test/fixtures/document-timeline.fixture";

beforeEach(() => {
  mockDocumentTimelineApi(createDocumentTimeline({ status: "completed" }));
});

test("renders completed timeline", async () => {
  render(<ProcessingTimeline documentId="doc-123" />);
  await screen.findByTestId("status-icon-completed");
});

// For polling tests
test("polls until complete", async () => {
  const { getCallCount } = mockPollingTimeline();

  render(<ProcessingTimeline documentId="doc-123" />);

  // Initially shows in-progress
  await screen.findByTestId("status-icon-in-progress");

  // After polling, shows completed
  await waitFor(() => {
    expect(screen.getByTestId("status-icon-completed")).toBeInTheDocument();
  }, { timeout: 5000 });

  expect(getCallCount()).toBeGreaterThanOrEqual(2);
});
```

---

## Mock Requirements

### Document Timeline API Mock

**Endpoint:** `GET /api/v1/observability/documents/{document_id}/timeline`

**Success Response (Completed):**

```json
{
  "document_id": "doc-uuid",
  "total_duration_ms": 4500,
  "events": [
    {
      "id": "event-1",
      "trace_id": "trace-abc123",
      "step_name": "upload",
      "status": "completed",
      "started_at": "2025-12-15T10:00:00Z",
      "ended_at": "2025-12-15T10:00:00.500Z",
      "duration_ms": 500,
      "retry_count": 0,
      "metrics": {
        "file_size": 1048576,
        "mime_type": "application/pdf"
      },
      "error_message": null
    },
    {
      "id": "event-2",
      "trace_id": "trace-abc123",
      "step_name": "parse",
      "status": "completed",
      "started_at": "2025-12-15T10:00:00.500Z",
      "ended_at": "2025-12-15T10:00:02Z",
      "duration_ms": 1500,
      "retry_count": 0,
      "metrics": {
        "pages_extracted": 15,
        "text_length": 12500,
        "parser_used": "pdfplumber"
      },
      "error_message": null
    },
    {
      "id": "event-3",
      "trace_id": "trace-abc123",
      "step_name": "chunk",
      "status": "completed",
      "started_at": "2025-12-15T10:00:02Z",
      "ended_at": "2025-12-15T10:00:02.300Z",
      "duration_ms": 300,
      "retry_count": 0,
      "metrics": {
        "chunks_created": 42,
        "avg_chunk_size": 512
      },
      "error_message": null
    },
    {
      "id": "event-4",
      "trace_id": "trace-abc123",
      "step_name": "embed",
      "status": "completed",
      "started_at": "2025-12-15T10:00:02.300Z",
      "ended_at": "2025-12-15T10:00:04Z",
      "duration_ms": 1700,
      "retry_count": 0,
      "metrics": {
        "vectors_generated": 42,
        "embedding_model": "text-embedding-3-small"
      },
      "error_message": null
    },
    {
      "id": "event-5",
      "trace_id": "trace-abc123",
      "step_name": "index",
      "status": "completed",
      "started_at": "2025-12-15T10:00:04Z",
      "ended_at": "2025-12-15T10:00:04.500Z",
      "duration_ms": 500,
      "retry_count": 0,
      "metrics": {
        "points_indexed": 42,
        "collection_name": "kb_doc-kb-uuid"
      },
      "error_message": null
    }
  ]
}
```

**Failed Step Response:**

```json
{
  "document_id": "doc-uuid",
  "total_duration_ms": 2500,
  "events": [
    {
      "id": "event-1",
      "step_name": "upload",
      "status": "completed",
      "duration_ms": 500,
      "metrics": { "file_size": 1048576, "mime_type": "application/pdf" }
    },
    {
      "id": "event-2",
      "step_name": "parse",
      "status": "failed",
      "duration_ms": 2000,
      "retry_count": 3,
      "metrics": null,
      "error_message": "PDF parsing failed: Document is password protected"
    }
  ]
}
```

**Notes:**
- Polling: refetchInterval of 2 seconds when last event status is "started" or "in_progress"
- Stop polling when all events are "completed" or any event is "failed"

---

## Required data-testid Attributes

### Processing Timeline Component

- `processing-timeline` - Main timeline container
- `processing-timeline-loading` - Loading skeleton
- `processing-timeline-error` - Error state container
- `processing-timeline-total-duration` - Total time display

### Timeline Step Component

- `timeline-step-{step_name}` - Step container (upload, parse, chunk, embed, index)
- `timeline-step-name-{step_name}` - Step name label
- `timeline-step-duration-{step_name}` - Duration display
- `timeline-step-retry-{step_name}` - Retry count badge
- `timeline-step-expand-{step_name}` - Expand/collapse chevron

### Status Icon Component

- `status-icon-{step_name}` - Status icon container
- `status-icon-completed` - Green check (generic selector)
- `status-icon-failed` - Red X (generic selector)
- `status-icon-in-progress` - Blue spinner (generic selector)
- `status-icon-pending` - Gray circle (generic selector)

### Step Detail Component

- `step-detail-{step_name}` - Expanded detail container
- `step-detail-error-{step_name}` - Error message box
- `step-detail-metric-{metric_name}` - Individual metric display

**Implementation Example:**

```tsx
<div data-testid="processing-timeline" className="space-y-4">
  <div className="flex justify-between border-b pb-2">
    <h3>Processing Timeline</h3>
    <span data-testid="processing-timeline-total-duration">
      Total: {formatDuration(total_duration_ms)}
    </span>
  </div>

  <div className="relative pl-6">
    {events.map((event) => (
      <div
        key={event.id}
        data-testid={`timeline-step-${event.step_name}`}
        className="relative mb-4"
      >
        <div className="absolute -left-6">
          <StatusIcon
            status={event.status}
            data-testid={`status-icon-${event.step_name}`}
          />
        </div>

        <div className="rounded-lg border p-3">
          <div className="flex justify-between">
            <span data-testid={`timeline-step-name-${event.step_name}`}>
              {event.step_name}
            </span>
            <span data-testid={`timeline-step-duration-${event.step_name}`}>
              {formatDuration(event.duration_ms)}
            </span>
          </div>

          {event.retry_count > 0 && (
            <Badge data-testid={`timeline-step-retry-${event.step_name}`}>
              Retry {event.retry_count}
            </Badge>
          )}
        </div>
      </div>
    ))}
  </div>
</div>
```

---

## Implementation Checklist

### Test: renders_all_processing_steps

**File:** `frontend/src/components/admin/documents/__tests__/processing-timeline.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/documents/processing-timeline.tsx`
- [ ] Define ProcessingTimelineProps interface with documentId
- [ ] Use useDocumentTimeline hook (stub initially)
- [ ] Render vertical timeline with connector line
- [ ] Map events to TimelineStep components
- [ ] Add data-testid: `processing-timeline`
- [ ] Run test: `npm run test:run -- src/components/admin/documents/__tests__/processing-timeline.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: displays_total_processing_time

**File:** `frontend/src/components/admin/documents/__tests__/processing-timeline.test.tsx`

**Tasks to make this test pass:**

- [ ] Add summary header with total_duration_ms
- [ ] Use formatDuration utility function
- [ ] Add data-testid: `processing-timeline-total-duration`
- [ ] Run test: `npm run test:run -- src/components/admin/documents/__tests__/processing-timeline.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: renders_step_name_and_duration

**File:** `frontend/src/components/admin/documents/__tests__/timeline-step.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/documents/timeline-step.tsx`
- [ ] Render step_name (capitalized) and duration
- [ ] Format duration with formatDuration utility
- [ ] Add data-testid: `timeline-step-{name}`, `timeline-step-duration-{name}`
- [ ] Run test: `npm run test:run -- src/components/admin/documents/__tests__/timeline-step.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1 hour

---

### Test: expands_to_show_metrics_on_click

**File:** `frontend/src/components/admin/documents/__tests__/timeline-step.test.tsx`

**Tasks to make this test pass:**

- [ ] Add useState for isExpanded
- [ ] Toggle isExpanded on click
- [ ] Conditionally render StepDetail when expanded
- [ ] Add ChevronRight/ChevronDown icon
- [ ] Run test: `npm run test:run -- src/components/admin/documents/__tests__/timeline-step.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1 hour

---

### Test: renders_green_check_for_completed

**File:** `frontend/src/components/admin/documents/__tests__/status-icon.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/documents/status-icon.tsx`
- [ ] Import CheckCircle from lucide-react
- [ ] Return CheckCircle with green color for status="completed"
- [ ] Add data-testid: `status-icon-completed`
- [ ] Run test: `npm run test:run -- src/components/admin/documents/__tests__/status-icon.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: renders_spinning_loader_for_in_progress

**File:** `frontend/src/components/admin/documents/__tests__/status-icon.test.tsx`

**Tasks to make this test pass:**

- [ ] Import Loader2 from lucide-react
- [ ] Return Loader2 with animate-spin class for status="in_progress" or "started"
- [ ] Add data-testid: `status-icon-in-progress`
- [ ] Run test: `npm run test:run -- src/components/admin/documents/__tests__/status-icon.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: renders_error_message_for_failed_step

**File:** `frontend/src/components/admin/documents/__tests__/step-detail.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/documents/step-detail.tsx`
- [ ] Conditionally render error box when status="failed" and error_message exists
- [ ] Style with red-tinted background
- [ ] Add data-testid: `step-detail-error-{step_name}`
- [ ] Run test: `npm run test:run -- src/components/admin/documents/__tests__/step-detail.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1 hour

---

### Test: renders_type_specific_metrics_for_each_step

**File:** `frontend/src/components/admin/documents/__tests__/step-detail.test.tsx`

**Tasks to make this test pass:**

- [ ] Render different metrics based on step_name
- [ ] upload: file_size, mime_type
- [ ] parse: pages_extracted, text_length, parser_used
- [ ] chunk: chunks_created, avg_chunk_size
- [ ] embed: vectors_generated, embedding_model
- [ ] index: points_indexed, collection_name
- [ ] Run test: `npm run test:run -- src/components/admin/documents/__tests__/step-detail.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: polls_while_processing_in_progress

**File:** `frontend/src/hooks/__tests__/useDocumentTimeline.test.ts`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/hooks/useDocumentTimeline.ts`
- [ ] Use TanStack Query useQuery
- [ ] Implement refetchInterval that returns 2000 when processing, false when done
- [ ] Check last event status to determine if still processing
- [ ] Run test: `npm run test:run -- src/hooks/__tests__/useDocumentTimeline.test.ts`
- [ ] Test passes (green phase)

**Estimated Effort:** 1 hour

---

### Test: admin_can_view_document_processing_timeline (E2E)

**File:** `frontend/e2e/tests/admin/document-timeline.spec.ts`

**Tasks to make this test pass:**

- [ ] Add "View Processing" button to document-detail-modal.tsx
- [ ] Wire button to open ProcessingTimeline modal/panel
- [ ] Pass documentId to ProcessingTimeline component
- [ ] Run test: `npx playwright test e2e/tests/admin/document-timeline.spec.ts`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

## Running Tests

```bash
# Run all component tests for this story
npm run test:run -- src/components/admin/documents

# Run specific test file
npm run test:run -- src/components/admin/documents/__tests__/processing-timeline.test.tsx

# Run hook tests
npm run test:run -- src/hooks/__tests__/useDocumentTimeline.test.ts

# Run E2E tests
npx playwright test e2e/tests/admin/document-timeline.spec.ts

# Run E2E in headed mode
npx playwright test e2e/tests/admin/document-timeline.spec.ts --headed

# Run with coverage
npm run test:coverage -- --testPathPattern="admin/documents"
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

- [ ] All tests written and failing
- [ ] Fixtures and factories created
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

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

1. **Verify all tests pass**
2. **Review code for quality**
3. **Extract duplications**
4. **Ensure tests still pass** after each refactor

---

## Next Steps

1. **Review this checklist** with team
2. **Run failing tests** to confirm RED phase
3. **Begin implementation** using checklist
4. **Work one test at a time**
5. **When all tests pass**, refactor for quality
6. **When complete**, run `bmad sm story-done`

---

## Knowledge Base References Applied

- **fixture-architecture.md** - React Testing Library fixtures
- **data-factories.md** - Factory patterns for timeline data
- **component-tdd.md** - Component test strategies
- **network-first.md** - MSW handler setup for polling
- **test-quality.md** - Test design principles

See `tea-index.csv` for complete knowledge fragment mapping.

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `npm run test:run -- src/components/admin/documents`

**Results:**

```
FAIL src/components/admin/documents/__tests__/processing-timeline.test.tsx
  Cannot find module '@/components/admin/documents/processing-timeline'

FAIL src/components/admin/documents/__tests__/timeline-step.test.tsx
  Cannot find module '@/components/admin/documents/timeline-step'

FAIL src/components/admin/documents/__tests__/status-icon.test.tsx
  Cannot find module '@/components/admin/documents/status-icon'

FAIL src/components/admin/documents/__tests__/step-detail.test.tsx
  Cannot find module '@/components/admin/documents/step-detail'
```

**Summary:**

- Total tests: 17
- Passing: 0 (expected)
- Failing: 17 (expected)
- Status: RED phase verified

---

## Notes

- Polling interval: 2 seconds while processing, stops when complete/failed
- Status icon for in-progress should use animate-spin
- Add formatDuration and formatBytes to utils.ts if not present
- Error messages displayed in red-tinted box
- Consider auto-scroll to latest event when new events arrive
- Add aria-labels to status icons for accessibility

---

**Generated by BMad TEA Agent** - 2025-12-15
