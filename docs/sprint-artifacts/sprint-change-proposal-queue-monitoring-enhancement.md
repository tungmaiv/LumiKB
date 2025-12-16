# Sprint Change Proposal: Queue Monitoring Enhancement

**Proposal ID:** SCP-2025-12-10-001
**Date:** 2025-12-10
**Requestor:** Tung Vu
**Scrum Master:** Bob (SM Agent)
**Status:** APPROVED FOR IMPLEMENTATION

---

## Executive Summary

Enhance the existing queue monitoring system at `/operations/queue` to provide operators and administrators with detailed processing workflow visibility, per-step timing metrics, error tracking, and bulk retry capabilities for failed documents.

**Impact Level:** MEDIUM
**Estimated Effort:** 2-3 days
**Risk Level:** LOW (extends existing implementation)

---

## Business Justification

### Problem Statement
Operators and administrators need visibility into document processing workflows to:
1. Diagnose processing failures quickly
2. Understand bottlenecks (which step is slow?)
3. Recover failed documents in bulk (not one-by-one)
4. Monitor queue health without requiring admin privileges

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

---

## Approved Changes

### Change 1: Per-Step Time Tracking in UI

**Description:** Display processing step breakdown with individual timing for each step (parse, chunk, embed, index).

**Backend Changes:**
- Extend `GET /api/v1/admin/queue/{queue_name}/tasks` response to include `processing_steps` from Document model
- Add `processing_steps`, `current_step`, `step_errors` to TaskInfo schema

**Frontend Changes:**
- Add expandable row in TaskListModal showing step breakdown table:
  | Step | Status | Started | Completed | Duration |
  |------|--------|---------|-----------|----------|
  | parse | done | 14:30:01 | 14:30:05 | 4s |
  | chunk | done | 14:30:05 | 14:30:08 | 3s |
  | embed | in_progress | 14:30:08 | - | 12s... |

**Files to Modify:**
- `backend/app/schemas/admin.py` - Extend TaskInfo schema
- `backend/app/services/queue_monitor_service.py` - Include processing_steps in task query
- `frontend/src/components/admin/task-list-modal.tsx` - Add expandable row component

**Acceptance Criteria:**
- [ ] AC-Q1.1: Clicking a task row expands to show step breakdown
- [ ] AC-Q1.2: Each step shows status, started_at, completed_at, duration
- [ ] AC-Q1.3: In-progress steps show elapsed time with live counter

---

### Change 2: Step Status Visibility with Error Display

**Description:** Color-coded step status badges with error message tooltips for failed steps.

**Frontend Changes:**
- Add status badges to step breakdown table:
  - 🟢 `done` = green badge
  - 🔵 `in_progress` = blue with spinner
  - 🟡 `pending` = gray badge
  - 🔴 `error` = red badge with tooltip showing error message
- Error tooltip sourced from `step_errors` JSONB field

**Files to Modify:**
- `frontend/src/components/admin/task-list-modal.tsx` - Add StepStatusBadge component
- `frontend/src/components/ui/tooltip.tsx` - Reuse existing tooltip (if available)

**Acceptance Criteria:**
- [ ] AC-Q2.1: Step status displayed with color-coded badges
- [ ] AC-Q2.2: Failed steps show red badge with error icon
- [ ] AC-Q2.3: Hovering error badge shows full error message in tooltip

---

### Change 3: Bulk Queue Restart for Failed Tasks

**Description:** Allow operators to retry multiple failed documents at once.

**Backend Changes:**
- New endpoint: `POST /api/v1/admin/queue/retry-failed`
  ```python
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
- Reuse existing `document_service.retry()` method internally

**Frontend Changes:**
- Add "Retry All Failed" button to TaskListModal header
- Add checkboxes to task rows for selective retry
- Add confirmation dialog: "Retry X failed documents?"
- Show success/failure toast after bulk retry

**Files to Modify:**
- `backend/app/api/v1/admin.py` - New bulk retry endpoint
- `backend/app/services/queue_monitor_service.py` - Add `bulk_retry_failed()` method
- `backend/app/schemas/admin.py` - Add BulkRetryRequest/Response schemas
- `frontend/src/components/admin/task-list-modal.tsx` - Add checkboxes, retry button

**Acceptance Criteria:**
- [ ] AC-Q3.1: "Retry All Failed" button visible when failed tasks exist
- [ ] AC-Q3.2: Checkboxes allow selective document retry
- [ ] AC-Q3.3: Confirmation dialog shows count before retry
- [ ] AC-Q3.4: Success toast shows "X documents queued for retry"
- [ ] AC-Q3.5: Failed retries shown in error list

---

### Change 4: Failed Task Filter

**Description:** Add filter tabs to easily view only failed tasks.

**Backend Changes:**
- Extend `GET /api/v1/admin/queue/{queue_name}/tasks`:
  - Add query param: `?document_status=FAILED`
  - Filter documents by status enum (PENDING, PROCESSING, READY, FAILED)

**Frontend Changes:**
- Add filter tabs in TaskListModal: `All | Active | Pending | Failed`
- Show count badge on Failed tab: `Failed (12)`
- Remember last selected filter in session

**Files to Modify:**
- `backend/app/api/v1/admin.py` - Add document_status query param
- `backend/app/services/queue_monitor_service.py` - Add status filter to query
- `frontend/src/components/admin/task-list-modal.tsx` - Add Tabs component

**Acceptance Criteria:**
- [ ] AC-Q4.1: Filter tabs displayed: All, Active, Pending, Failed
- [ ] AC-Q4.2: Failed tab shows count badge with failed document count
- [ ] AC-Q4.3: Selecting filter updates task list immediately
- [ ] AC-Q4.4: Filter state persists during modal session

---

### Change 5: Operator Role Access

**Description:** Allow users with Operator role (permission_level >= 2) to access queue monitoring.

**Backend Changes:**
- New dependency in `backend/app/core/auth.py`:
  ```python
  async def get_current_operator_or_admin(
      current_user: User = Depends(current_active_user),
      db: AsyncSession = Depends(get_db),
  ) -> User:
      """Require user with operator (level 2) or admin (level 3) permissions."""
      # Check is_superuser first (backward compat)
      if current_user.is_superuser:
          return current_user

      # Check group permission_level >= 2
      user_max_level = await get_user_max_permission_level(db, current_user.id)
      if user_max_level >= 2:
          return current_user

      raise HTTPException(status_code=403, detail="Operator access required")
  ```

- Update queue endpoints to use new dependency:
  - `GET /api/v1/admin/queue/status`
  - `GET /api/v1/admin/queue/{queue_name}/tasks`
  - `POST /api/v1/admin/queue/retry-failed`

**Frontend Changes:**
- Show "Queue Status" link in sidebar for operators (permission_level >= 2)
- Route remains at `/operations/queue`

**Files to Modify:**
- `backend/app/core/auth.py` - Add `get_current_operator_or_admin()` dependency
- `backend/app/services/permission_service.py` - Add `get_user_max_permission_level()` helper
- `backend/app/api/v1/admin.py` - Update queue endpoints
- `frontend/src/components/layout/kb-sidebar.tsx` - Conditional sidebar link

**Acceptance Criteria:**
- [ ] AC-Q5.1: Users in groups with permission_level >= 2 can access queue endpoints
- [ ] AC-Q5.2: Regular users (permission_level = 1) receive 403 Forbidden
- [ ] AC-Q5.3: Admins (is_superuser=True) retain full access
- [ ] AC-Q5.4: Queue Status link visible to operators in sidebar

---

## Implementation Plan

### Task Breakdown

| # | Task | Estimate | Dependencies |
|---|------|----------|--------------|
| 1 | Extend TaskInfo schema with processing_steps | 1h | - |
| 2 | Update queue_monitor_service to fetch processing_steps | 2h | Task 1 |
| 3 | Create StepBreakdown expandable component | 3h | Task 2 |
| 4 | Add StepStatusBadge with error tooltips | 2h | Task 3 |
| 5 | Create bulk retry endpoint | 2h | - |
| 6 | Add bulk retry UI (checkboxes, button, dialog) | 3h | Task 5 |
| 7 | Add document_status filter to API | 1h | - |
| 8 | Add filter tabs to TaskListModal | 2h | Task 7 |
| 9 | Create get_current_operator_or_admin dependency | 2h | - |
| 10 | Update queue endpoints with new dependency | 1h | Task 9 |
| 11 | Update sidebar for operator access | 1h | Task 10 |
| 12 | Write unit tests (backend) | 2h | All backend |
| 13 | Write unit tests (frontend) | 2h | All frontend |
| 14 | Integration testing | 2h | All tasks |

**Total Estimate:** 24 hours (~3 days)

### Suggested Story Structure

This change can be implemented as a single story or split into 2 stories:

**Option A: Single Story (Recommended)**
- Story: "Queue Monitoring Enhancement with Operator Access"
- All 5 changes in one story
- Pros: Single review cycle, cohesive feature
- Cons: Larger PR

**Option B: Two Stories**
- Story A: "Queue Step Visibility" (Changes 1, 2, 4)
- Story B: "Bulk Retry and Operator Access" (Changes 3, 5)
- Pros: Smaller PRs, can ship incrementally
- Cons: Two review cycles

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Permission check performance | Low | Medium | Cache user permission_level in session |
| Bulk retry overwhelms queue | Low | Medium | Add rate limit (max 100 per request) |
| Step timing data missing | Medium | Low | Graceful fallback to "N/A" if not tracked |
| UI complexity in modal | Low | Low | Use existing shadcn/ui components |

---

## Testing Requirements

### Backend Tests
- [ ] Unit: TaskInfo schema includes processing_steps
- [ ] Unit: bulk_retry_failed() queues correct documents
- [ ] Unit: get_current_operator_or_admin() permission checks
- [ ] Integration: Bulk retry endpoint creates outbox events
- [ ] Integration: Status filter returns correct documents

### Frontend Tests
- [ ] Unit: StepBreakdown renders step table correctly
- [ ] Unit: StepStatusBadge shows correct colors
- [ ] Unit: Bulk retry dialog shows confirmation
- [ ] Unit: Filter tabs update task list

### E2E Tests (Deferred to E2E infrastructure story)
- [ ] Operator can view queue status
- [ ] Operator can retry failed documents
- [ ] Regular user receives 403

---

## Approvals

| Role | Name | Status | Date |
|------|------|--------|------|
| Requestor | Tung Vu | ✅ Approved | 2025-12-10 |
| Scrum Master | Bob (SM Agent) | ✅ Approved | 2025-12-10 |
| Architect | - | Pending | - |
| Dev Lead | - | Pending | - |

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-10 | Bob (SM) | Initial proposal created via correct-course workflow |

---

## Next Steps

1. **Route to Dev Agent** for implementation
2. **Create story file** with acceptance criteria
3. **Update sprint-status.yaml** with new story

**Recommended:** Run `*create-story` workflow to generate implementation story from this proposal.
