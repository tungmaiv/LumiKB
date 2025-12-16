# Story 7-27: Queue Monitoring Enhancement with Operator Access

**Story ID:** 7-27
**Epic:** Epic 7 - Infrastructure & DevOps
**Priority:** Medium
**Estimated Effort:** 3 days (24 hours)
**Type:** Enhancement

---

## User Story

As an operator or administrator, I want enhanced queue monitoring with per-step timing, error visibility, bulk retry capabilities, and filtering so that I can diagnose processing failures quickly, understand bottlenecks, and recover failed documents efficiently.

---

## Acceptance Criteria

### Change 1: Per-Step Time Tracking in UI

**AC-7.27.1: Expandable task row**
**Given** I am viewing the TaskListModal
**When** I click a task row
**Then** it expands to show a step breakdown table

**AC-7.27.2: Step breakdown table**
**Given** I expand a task row
**Then** I see columns: Step, Status, Started, Completed, Duration
**And** each processing step (parse, chunk, embed, index) is displayed

**AC-7.27.3: Live elapsed time**
**Given** a step is in_progress
**Then** the Duration column shows live elapsed time counter

### Change 2: Step Status Visibility with Error Display

**AC-7.27.4: Color-coded status badges**
**Given** I view the step breakdown table
**Then** step statuses are displayed with color-coded badges:
- done = green badge
- in_progress = blue badge with spinner
- pending = gray badge
- error = red badge with error icon

**AC-7.27.5: Error tooltip**
**Given** a step has status "error"
**When** I hover over the red error badge
**Then** a tooltip shows the full error message from step_errors

### Change 3: Bulk Queue Restart for Failed Tasks

**AC-7.27.6: Retry All Failed button**
**Given** failed tasks exist in the queue
**When** I view TaskListModal
**Then** "Retry All Failed" button is visible in the header

**AC-7.27.7: Selective retry checkboxes**
**Given** I view tasks in TaskListModal
**Then** each task row has a checkbox for selection
**And** I can select multiple tasks for bulk retry

**AC-7.27.8: Bulk retry confirmation**
**Given** I select tasks and click retry
**When** confirmation dialog appears
**Then** it shows count: "Retry X failed documents?"

**AC-7.27.9: Retry success feedback**
**Given** I confirm bulk retry
**When** retry completes
**Then** success toast shows "X documents queued for retry"
**And** failed retries are shown in error list

**AC-7.27.10: Bulk retry API**
**Given** I call POST /api/v1/admin/queue/retry-failed
**When** request body contains document_ids or retry_all_failed=true
**Then** documents are queued for reprocessing
**And** response shows queued count, failed count, and error details

### Change 4: Failed Task Filter

**AC-7.27.11: Filter tabs**
**Given** I view TaskListModal
**Then** I see filter tabs: All, Active, Pending, Failed

**AC-7.27.12: Failed count badge**
**Given** failed tasks exist
**Then** Failed tab shows count badge: "Failed (N)"

**AC-7.27.13: Filter updates task list**
**Given** I select a filter tab
**When** filter is applied
**Then** task list updates immediately to show matching tasks

**AC-7.27.14: Filter persistence**
**Given** I select a filter
**Then** filter state persists during modal session

**AC-7.27.15: Document status filter API**
**Given** I call GET /api/v1/admin/queue/{queue_name}/tasks?document_status=FAILED
**Then** only documents with FAILED status are returned

### Change 5: Operator Role Access

**AC-7.27.16: Operator permission check**
**Given** a user is in a group with permission_level >= 2
**When** they access queue monitoring endpoints
**Then** access is granted (200 OK)

**AC-7.27.17: Regular user denied**
**Given** a user has only permission_level = 1
**When** they access queue monitoring endpoints
**Then** access is denied (403 Forbidden)

**AC-7.27.18: Admin access preserved**
**Given** a user has is_superuser=True
**When** they access queue monitoring endpoints
**Then** access is granted regardless of group membership

**AC-7.27.19: Sidebar visibility**
**Given** a user has permission_level >= 2
**When** they view the application sidebar
**Then** "Queue Status" link is visible under Operations

---

## Tasks

| # | Task | Estimate | Dependencies |
|---|------|----------|--------------|
| 1 | Extend TaskInfo schema with processing_steps, current_step, step_errors | 1h | - |
| 2 | Update queue_monitor_service to fetch processing_steps from documents | 2h | Task 1 |
| 3 | Create StepBreakdown expandable component in TaskListModal | 3h | Task 2 |
| 4 | Add StepStatusBadge component with error tooltips | 2h | Task 3 |
| 5 | Create POST /api/v1/admin/queue/retry-failed endpoint | 2h | - |
| 6 | Add BulkRetryRequest/Response schemas | 0.5h | Task 5 |
| 7 | Add bulk retry UI (checkboxes, button, confirmation dialog) | 3h | Task 5, 6 |
| 8 | Add document_status query param to queue tasks endpoint | 1h | - |
| 9 | Add filter tabs component to TaskListModal | 2h | Task 8 |
| 10 | Create get_current_operator_or_admin dependency in auth.py | 2h | - |
| 11 | Add get_user_max_permission_level helper to permission_service | 0.5h | Task 10 |
| 12 | Update queue endpoints to use operator_or_admin dependency | 1h | Task 10, 11 |
| 13 | Update sidebar to show Queue Status for operators | 1h | Task 12 |
| 14 | Write backend unit tests | 2h | All backend tasks |
| 15 | Write frontend unit tests | 2h | All frontend tasks |
| 16 | Integration testing | 2h | All tasks |

**Total Estimate:** 24 hours (~3 days)

---

## Dev Notes

### Existing Assets to Leverage

| Component | Location | Reuse Level |
|-----------|----------|-------------|
| ProcessingStep enum | `backend/app/models/document.py:29-47` | 100% |
| processing_steps JSONB | `backend/app/models/document.py:133-147` | 100% |
| QueueMonitorService | `backend/app/services/queue_monitor_service.py` | 90% extend |
| Queue Status API | `backend/app/api/v1/admin.py` | 80% extend |
| QueueStatusCard | `frontend/src/components/admin/queue-status-card.tsx` | 100% |
| TaskListModal | `frontend/src/components/admin/task-list-modal.tsx` | 70% extend |
| Document retry API | `backend/app/api/v1/documents.py:574` | 100% |
| Group RBAC (permission_level) | `backend/app/models/group.py:68-74` | 100% |

### Backend Changes

**Files to Modify:**
- `backend/app/schemas/admin.py` - Extend TaskInfo, add BulkRetryRequest/Response
- `backend/app/services/queue_monitor_service.py` - Add processing_steps, bulk_retry, status filter
- `backend/app/api/v1/admin.py` - New bulk retry endpoint, update dependencies
- `backend/app/core/auth.py` - Add `get_current_operator_or_admin()` dependency
- `backend/app/services/permission_service.py` - Add `get_user_max_permission_level()` helper

**New Endpoint:**
```python
POST /api/v1/admin/queue/retry-failed
Request:
{
  "document_ids": ["uuid1", "uuid2", ...],  # Selective retry
  # OR
  "retry_all_failed": true,  # Retry all FAILED documents
  "kb_id": "optional-uuid"   # Scope to specific KB (optional)
}

Response:
{
  "queued": 15,
  "failed": 2,
  "errors": [{"document_id": "uuid", "error": "reason"}]
}
```

### Frontend Changes

**Files to Modify:**
- `frontend/src/components/admin/task-list-modal.tsx` - Expandable rows, checkboxes, tabs
- `frontend/src/components/layout/kb-sidebar.tsx` - Conditional Queue Status link

**New Components:**
- `StepBreakdown` - Expandable step breakdown table
- `StepStatusBadge` - Color-coded status badge with tooltip
- `BulkRetryDialog` - Confirmation dialog for bulk retry

### Permission Model

```
permission_level:
  1 = User (read-only)
  2 = Operator (queue monitoring, document retry)
  3 = Administrator (full access)

Access check: user_max_level >= 2
```

---

## Testing Strategy

### Backend Unit Tests
- [ ] TaskInfo schema includes processing_steps, current_step, step_errors
- [ ] bulk_retry_failed() queues correct documents
- [ ] bulk_retry_failed() respects kb_id filter
- [ ] bulk_retry_failed() returns accurate success/failure counts
- [ ] get_current_operator_or_admin() grants access for level >= 2
- [ ] get_current_operator_or_admin() denies access for level 1
- [ ] document_status filter returns correct documents

### Frontend Unit Tests
- [ ] StepBreakdown renders step table correctly
- [ ] StepBreakdown shows live elapsed time for in_progress steps
- [ ] StepStatusBadge shows correct colors for each status
- [ ] StepStatusBadge shows error tooltip on hover
- [ ] BulkRetryDialog shows document count
- [ ] Filter tabs update task list correctly
- [ ] Checkboxes enable bulk selection

### Integration Tests
- [ ] Bulk retry endpoint creates outbox events
- [ ] Status filter returns correct documents
- [ ] Operator can access queue endpoints (200)
- [ ] Regular user cannot access queue endpoints (403)

### E2E Tests (Deferred)
- [ ] Operator can view queue status
- [ ] Operator can retry failed documents
- [ ] Regular user receives 403 redirect

---

## Definition of Done

- [ ] All acceptance criteria verified
- [ ] Backend unit tests passing (pytest)
- [ ] Frontend unit tests passing (vitest)
- [ ] Integration tests passing
- [ ] No TypeScript errors (npm run type-check)
- [ ] No linting errors (ruff check, eslint)
- [ ] Code reviewed and approved
- [ ] Documentation updated (if applicable)
- [ ] Story marked DONE in sprint-status.yaml

---

## References

- Sprint Change Proposal: [sprint-change-proposal-queue-monitoring-enhancement.md](./sprint-change-proposal-queue-monitoring-enhancement.md)
- Story 5-4: [5-4-processing-queue-status.md](./5-4-processing-queue-status.md)
- Processing Step Model: `backend/app/models/document.py:29-47`
