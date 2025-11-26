# Story 2.9: Document Upload Frontend

Status: done

## Story

As a **user with WRITE permission**,
I want **to upload documents via drag-and-drop or file picker**,
So that **I can easily add content to a Knowledge Base**.

## Acceptance Criteria

1. **Given** I have WRITE permission on the active KB **When** I drag a file onto the upload zone **Then**:
   - The zone highlights to indicate drop target (visual feedback)
   - Releasing the file starts the upload
   - Only supported formats (PDF, DOCX, MD) are accepted

2. **Given** I click the upload zone **When** the file picker opens **Then**:
   - I can select one or more files (multi-file upload)
   - Only supported formats are selectable (file filter)
   - Selected files are queued for upload

3. **Given** upload is in progress **When** I view the upload zone **Then**:
   - I see a progress bar for each file
   - File name and size are displayed
   - I can cancel pending uploads (not in-progress ones)
   - Progress shows percentage uploaded

4. **Given** upload completes successfully **When** the response returns **Then**:
   - The document appears in the list with PENDING status
   - A success toast notification appears
   - The upload zone resets for next upload

5. **Given** upload fails **When** an error occurs **Then**:
   - An error toast shows the failure reason
   - The failed file shows error state in the queue
   - User can retry the failed upload

6. **Given** I upload a file >50MB **When** validation runs **Then**:
   - Upload is blocked client-side before sending
   - Clear error message shows "Maximum file size is 50MB"

7. **Given** I try to upload an unsupported file type **When** validation runs **Then**:
   - Upload is blocked client-side
   - Clear error message shows "Supported formats: PDF, DOCX, MD"

8. **Given** I only have READ permission on the KB **When** I view the document list **Then**:
   - The upload zone is hidden or disabled
   - No upload functionality is accessible

## Tasks / Subtasks

- [x] **Task 1: Install and configure react-dropzone** (AC: 1, 2)
  - [x] Add react-dropzone dependency to frontend package.json
  - [x] Configure accepted MIME types: application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, text/markdown
  - [x] Configure maxSize: 50MB (52428800 bytes)
  - [x] Add unit test for dropzone configuration

- [x] **Task 2: Create UploadDropzone component** (AC: 1, 2, 6, 7)
  - [x] Create `frontend/src/components/documents/upload-dropzone.tsx`
  - [x] Implement drag-and-drop visual feedback (isDragActive state)
  - [x] Implement click-to-open file picker
  - [x] Add file type validation with clear error messages
  - [x] Add file size validation (50MB max)
  - [x] Integrate with existing DocumentList component
  - [x] Add component tests

- [x] **Task 3: Create UploadProgress component** (AC: 3, 4, 5)
  - [x] Create `frontend/src/components/documents/upload-progress.tsx`
  - [x] Display file name, size, and upload percentage
  - [x] Add progress bar (use shadcn/ui Progress component)
  - [x] Add cancel button for pending files
  - [x] Show success/error states per file
  - [x] Add component tests

- [x] **Task 4: Create useFileUpload hook** (AC: 3, 4, 5)
  - [x] Create `frontend/src/lib/hooks/use-file-upload.ts`
  - [x] Manage upload queue state (pending, uploading, completed, failed)
  - [x] Track upload progress per file using XMLHttpRequest or fetch with ReadableStream
  - [x] Handle API calls to POST /api/v1/knowledge-bases/{kb_id}/documents
  - [x] Implement retry logic for failed uploads
  - [x] Add abort controller for cancellation
  - [x] Add unit tests for hook

- [x] **Task 5: Integrate upload with permission checks** (AC: 8)
  - [x] Check user's permission level on current KB (from useKnowledgeBase or similar)
  - [x] Conditionally render UploadDropzone based on WRITE/ADMIN permission
  - [x] Show disabled state or hide entirely for READ-only users
  - [x] Add test for permission-based rendering

- [x] **Task 6: Add toast notifications** (AC: 4, 5)
  - [x] Use existing toast infrastructure (shadcn/ui toast or similar)
  - [x] Add success toast on upload completion: "Document uploaded successfully"
  - [x] Add error toast on upload failure with error message
  - [x] Add info toast when document starts processing: "Processing started..."

- [x] **Task 7: Integrate with DocumentList** (AC: 4)
  - [x] Update DocumentList to include UploadDropzone at the top
  - [x] Trigger document list refetch after successful upload
  - [x] Ensure newly uploaded document appears with PENDING status
  - [x] Polling should pick up status changes (reuse useDocumentStatusPolling)

- [x] **Task 8: Add E2E-ready styling and polish** (AC: 1, 2, 3)
  - [x] Style upload zone following UX spec (dashed border, icon, helper text)
  - [x] Add smooth animations for drag state transitions
  - [x] Ensure responsive design (works on tablet/mobile)
  - [x] Add loading skeleton while KB permission is being fetched

## Dev Notes

### Learnings from Previous Story

**From Story 2-8-document-list-and-metadata-view (Status: done)**

- **DocumentList Component**: Full implementation at `frontend/src/components/documents/document-list.tsx` - has pagination, sorting, status badges, detail modal. ADD upload dropzone at the top.
- **DocumentStatusBadge Component**: Already implemented at `frontend/src/components/documents/document-status-badge.tsx` - REUSE for newly uploaded PENDING documents
- **useDocumentStatusPolling Hook**: Already implemented at `frontend/src/lib/hooks/use-document-status-polling.ts` - REUSE to poll PENDING/PROCESSING documents
- **showDocumentStatusToast**: Already implemented at `frontend/src/lib/utils/document-toast.ts` - REUSE for upload notifications
- **useDocuments Hook**: Already implemented at `frontend/src/lib/hooks/use-documents.ts` - REUSE for refetching document list
- **DocumentService Backend**: Methods exist at `backend/app/services/document_service.py` - upload endpoint already implemented in Story 2-4
- **date-fns**: Already installed - REUSE for relative date display

**Key Services/Components to REUSE (DO NOT recreate):**
- `DocumentStatusBadge` at `frontend/src/components/documents/document-status-badge.tsx`
- `useDocumentStatusPolling` at `frontend/src/lib/hooks/use-document-status-polling.ts`
- `showDocumentStatusToast` at `frontend/src/lib/utils/document-toast.ts`
- `useDocuments` at `frontend/src/lib/hooks/use-documents.ts`
- Toast infrastructure from shadcn/ui

[Source: docs/sprint-artifacts/2-8-document-list-and-metadata-view.md#Dev-Agent-Record]

### Architecture Patterns and Constraints

**From Tech Spec:**

| Constraint | Requirement | Source |
|------------|-------------|--------|
| Upload Endpoint | `POST /api/v1/knowledge-bases/{kb_id}/documents` (multipart/form-data) | tech-spec-epic-2.md#Document-Endpoints |
| File Formats | PDF, DOCX, MD only | tech-spec-epic-2.md#API-Endpoints |
| Max File Size | 50MB | tech-spec-epic-2.md#Edge-Case-Handling |
| Response | 202 Accepted with DocumentResponse | tech-spec-epic-2.md#API-Endpoints |
| Permission | WRITE permission required | tech-spec-epic-2.md#KB-Permissions |
| Component | `upload-dropzone.tsx`, `upload-progress.tsx` | tech-spec-epic-2.md#Frontend-Components |

**From Coding Standards:**

| Category | Requirement | Source |
|----------|-------------|--------|
| TypeScript | Strict mode enabled | coding-standards.md |
| Component Files | kebab-case naming | coding-standards.md |
| Hooks | Prefix with `use` | coding-standards.md |
| State Management | Zustand for global, useState for local | architecture.md |
| Testing Library | Vitest + Testing Library | testing-frontend-specification.md |

**Upload Flow (from architecture.md):**

```
User drops file
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: Validate type/size → Create FormData → POST API  │
│           Track progress → Show status → Refetch list      │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
API returns 202 with document_id, status=PENDING
```

**MIME Types for Validation:**

```typescript
const ACCEPTED_MIME_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/markdown': ['.md'],
  'text/x-markdown': ['.md'],
};
```

### Project Structure Notes

**Files to CREATE:**

```
frontend/
└── src/
    ├── components/
    │   └── documents/
    │       ├── upload-dropzone.tsx          # NEW
    │       ├── upload-progress.tsx          # NEW
    │       └── __tests__/
    │           ├── upload-dropzone.test.tsx # NEW
    │           └── upload-progress.test.tsx # NEW
    └── lib/
        └── hooks/
            ├── use-file-upload.ts           # NEW
            └── __tests__/
                └── use-file-upload.test.ts  # NEW
```

**Files to UPDATE:**

```
frontend/src/components/documents/document-list.tsx  # Add UploadDropzone integration
frontend/src/components/documents/index.ts           # Export new components
frontend/package.json                                 # Add react-dropzone
```

### Testing Requirements

| Requirement | Standard | Enforcement |
|-------------|----------|-------------|
| Vitest for frontend tests | testing-frontend-specification.md | `npm test` |
| Component tests use Testing Library | testing-frontend-specification.md | Code review |
| `userEvent` over `fireEvent` | testing-frontend-specification.md | Code review |
| Accessible queries (role, label, text) | testing-frontend-specification.md | Code review |
| 70% frontend coverage minimum | testing-frontend-specification.md | CI gate |
| Mock file uploads in tests | testing-frontend-specification.md | MSW |

**Test Scenarios to Cover:**

1. Drop valid file → upload starts
2. Drop invalid file type → shows error
3. Drop file > 50MB → shows size error
4. Multi-file upload → all files queued
5. Cancel pending upload → removed from queue
6. Upload success → toast + refetch
7. Upload failure → error toast + retry option
8. READ-only user → upload zone hidden/disabled

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Document-Endpoints] - Upload API specification
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Frontend-Components] - UI component requirements
- [Source: docs/epics.md#Story-2.9] - Original story definition and ACs
- [Source: docs/architecture.md#Project-Structure] - Frontend component structure
- [Source: docs/coding-standards.md] - TypeScript coding conventions
- [Source: docs/testing-frontend-specification.md] - Frontend testing patterns (Vitest, Testing Library)
- [Source: docs/ux-design-specification.md#Upload-Components] - Upload zone visual patterns (dashed border, icons, helper text)
- [Source: docs/sprint-artifacts/2-8-document-list-and-metadata-view.md] - Previous story implementation details

## Dev Agent Record

### Context Reference

- [2-9-document-upload-frontend.context.xml](docs/sprint-artifacts/2-9-document-upload-frontend.context.xml)

### Agent Model Used

claude-sonnet-4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

- Installed react-dropzone v14.2.0 via npm
- Added shadcn/ui Progress component for upload progress visualization
- Created useFileUpload hook with XMLHttpRequest for progress tracking
- Extended showDocumentStatusToast with upload-specific statuses
- Created DocumentsPanel to integrate upload with document list
- Updated dashboard page to show DocumentsPanel when KB is active
- All 167 frontend tests passing, build successful

### Completion Notes List

- UploadDropzone: Fully functional drag-drop upload with visual feedback, validation
- UploadProgress: Shows file name, size, percentage, cancel/retry buttons
- useFileUpload: Manages upload queue, progress tracking, abort/retry
- Permission-based rendering: Upload zone hidden for READ users
- Toast notifications: Success/error/started notifications via sonner
- Integration: DocumentsPanel combines upload zone + document list
- Dashboard: Shows documents when KB selected, getting started otherwise

### File List

**Created:**
- frontend/src/components/documents/upload-dropzone.tsx
- frontend/src/components/documents/upload-progress.tsx
- frontend/src/components/documents/documents-panel.tsx
- frontend/src/components/documents/__tests__/upload-dropzone.test.tsx
- frontend/src/components/documents/__tests__/upload-progress.test.tsx
- frontend/src/lib/hooks/use-file-upload.ts
- frontend/src/lib/hooks/__tests__/use-file-upload.test.ts
- frontend/src/components/ui/progress.tsx (shadcn)

**Modified:**
- frontend/package.json (added react-dropzone)
- frontend/src/components/documents/index.ts (exports)
- frontend/src/lib/utils/document-toast.ts (upload toast types)
- frontend/src/app/(protected)/dashboard/page.tsx (DocumentsPanel integration)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-24 | Initial draft created from tech-spec-epic-2.md, architecture.md, epics.md, and story 2-8 learnings | SM Agent (Bob) |
| 2025-11-24 | Added ux-design-specification.md reference for upload zone visual patterns | SM Agent (Bob) |
| 2025-11-24 | Generated story context XML, marked ready-for-dev | SM Agent (Bob) |
| 2025-11-24 | Implemented all tasks, 167 tests passing, ready for review | Dev Agent (Amelia) |
| 2025-11-24 | Senior Developer Review notes appended, APPROVED | Dev Agent (Amelia) |

---

## Senior Developer Review (AI)

**Reviewer:** Tung Vu
**Date:** 2025-11-24
**Outcome:** ✅ **APPROVE**

### Summary

All 8 acceptance criteria fully implemented with evidence. All 8 tasks verified complete. 36 new tests added (167 total passing). No HIGH or MEDIUM severity findings. Code follows architectural patterns and coding standards.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| 1 | Drag-drop with visual feedback | ✅ IMPLEMENTED | upload-dropzone.tsx:111-148 - isDragActive state |
| 2 | Click file picker, multi-file | ✅ IMPLEMENTED | upload-dropzone.tsx:118,150 - multiple: true |
| 3 | Progress bar, file info, cancel | ✅ IMPLEMENTED | upload-progress.tsx:54-94 - Progress + Cancel |
| 4 | Success: PENDING + toast + reset | ✅ IMPLEMENTED | documents-panel.tsx:82-85, document-toast.ts:51-56 |
| 5 | Error: toast + state + retry | ✅ IMPLEMENTED | upload-progress.tsx:96-106, use-file-upload.ts:196-206 |
| 6 | >50MB blocked client-side | ✅ IMPLEMENTED | upload-dropzone.tsx:12,83-86 - MAX_FILE_SIZE |
| 7 | Unsupported type blocked | ✅ IMPLEMENTED | upload-dropzone.tsx:15-20,87-89 - ACCEPTED_MIME_TYPES |
| 8 | READ permission hides zone | ✅ IMPLEMENTED | upload-dropzone.tsx:65,122-125 - canUpload check |

**Summary: 8 of 8 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Status | Evidence |
|------|--------|----------|
| Task 1: Install react-dropzone | ✅ Verified | package.json:44 |
| Task 2: UploadDropzone component | ✅ Verified | upload-dropzone.tsx (205 lines) |
| Task 3: UploadProgress component | ✅ Verified | upload-progress.tsx (163 lines) |
| Task 4: useFileUpload hook | ✅ Verified | use-file-upload.ts (299 lines) |
| Task 5: Permission checks | ✅ Verified | upload-dropzone.tsx:65 |
| Task 6: Toast notifications | ✅ Verified | document-toast.ts:51-71 |
| Task 7: DocumentList integration | ✅ Verified | documents-panel.tsx |
| Task 8: E2E-ready styling | ✅ Verified | upload-dropzone.tsx:135-148 |

**Summary: 8 of 8 completed tasks verified**

### Test Coverage

- UploadDropzone: 13 tests ✅
- UploadProgress: 11 tests ✅
- useFileUpload: 12 tests ✅
- **Total: 36 new tests, 167 total passing**

### Architectural Alignment

- ✅ kebab-case file naming
- ✅ Hook prefixed with `use`
- ✅ Correct API endpoint POST /api/v1/knowledge-bases/{kb_id}/documents
- ✅ 202 response handling
- ✅ Reuses existing components (showDocumentStatusToast, useDocuments)

### Security Notes

- ✅ Client-side file validation (type + size)
- ✅ Server-side validation handled (400/413)
- ✅ withCredentials for auth cookies
- ✅ Permission check before render

### Action Items

**Advisory Notes:**
- Note: Consider adding E2E tests for full upload flow when Playwright integration is ready
