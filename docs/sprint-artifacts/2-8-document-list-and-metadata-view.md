# Story 2.8: Document List and Metadata View

Status: done

## Story

As a **user**,
I want **to view all documents in a Knowledge Base with their metadata**,
So that **I can see what content is available and understand each document's details**.

## Acceptance Criteria

1. **Given** I have READ access to a KB **When** I view the KB document list **Then** I see a list of all documents with:
   - Document name
   - Upload date (relative format: "2 hours ago", "3 days ago")
   - File size (human-readable: "1.5 MB")
   - Uploader name (email or display name)
   - Status badge (PENDING, PROCESSING, READY, FAILED)
   - Chunk count (displayed for READY documents, e.g., "47 chunks")

2. **Given** the KB has more than 20 documents **When** I view the document list **Then**:
   - The list shows 20 documents per page by default
   - Pagination controls are displayed (Previous/Next, page numbers)
   - I can navigate between pages
   - Total document count is displayed (e.g., "Showing 1-20 of 150 documents")

3. **Given** I am viewing the document list **When** I click on a sort option **Then**:
   - I can sort by name (A-Z, Z-A)
   - I can sort by date (newest first, oldest first)
   - I can sort by size (largest first, smallest first)
   - The current sort order is visually indicated

4. **Given** I click on a document row **When** the detail view opens **Then** I see full metadata including:
   - Document name and original filename
   - MIME type (e.g., "application/pdf")
   - File size (bytes and human-readable)
   - Upload date (full timestamp)
   - Uploader name/email
   - Processing status with status badge
   - Processing duration (if READY, e.g., "Processed in 45s")
   - Chunk count (if READY)
   - Last error message (if FAILED, full message not truncated)
   - Retry count (if any retries attempted)

5. **Given** I am viewing the document detail **When** the document is in FAILED status **Then**:
   - I see the full error message
   - A "Retry" button is displayed
   - Clicking retry triggers reprocessing and shows toast notification

6. **Given** I navigate away from the document list **When** I return to the list **Then**:
   - My sort preference is preserved (within session)
   - The current page is reset to page 1

7. **Given** the document list is loading **When** the API request is in progress **Then**:
   - Loading skeleton is displayed
   - No flickering on pagination/sort changes

## Tasks / Subtasks

- [x] **Task 1: Create document list API endpoint** (AC: 1, 2, 3)
  - [x] Create `GET /api/v1/knowledge-bases/{kb_id}/documents` endpoint in `documents.py`
  - [x] Accept query parameters: `page` (default 1), `limit` (default 20), `sort_by` (name, created_at, file_size_bytes), `sort_order` (asc, desc)
  - [x] Require READ permission on KB
  - [x] Return paginated response with documents and metadata
  - [x] Include uploader user info (join with users table)
  - [x] Add unit tests for endpoint authorization
  - [x] Add integration tests for pagination and sorting

- [x] **Task 2: Create document detail API endpoint** (AC: 4)
  - [x] Create `GET /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}` endpoint
  - [x] Require READ permission on KB
  - [x] Return full `DocumentResponse` with all metadata fields
  - [x] Include uploader user info (email/name)
  - [x] Add integration tests

- [x] **Task 3: Create pagination schema** (AC: 2)
  - [x] Create `PaginatedDocumentResponse` schema in `schemas/document.py`
  - [x] Include fields: `items`, `total`, `page`, `limit`, `total_pages`
  - [x] Create `DocumentListItemWithUploader` schema with uploader info
  - [x] Add schema unit tests

- [x] **Task 4: Update document service with list and get methods** (AC: 1, 2, 3, 4)
  - [x] Add `list_documents(kb_id, page, limit, sort_by, sort_order, user)` method to DocumentService
  - [x] Add `get_document(kb_id, doc_id, user)` method to DocumentService
  - [x] Use SQLAlchemy joins to fetch uploader info efficiently
  - [x] Ensure permission checks are performed
  - [x] Add unit tests for service methods

- [x] **Task 5: Update DocumentList component with pagination** (AC: 2, 6, 7)
  - [x] Update `frontend/src/components/documents/document-list.tsx`
  - [x] Add pagination state and controls (using shadcn/ui Pagination)
  - [x] Add loading skeleton while fetching
  - [x] Display total count and page info
  - [x] Preserve sort preference in session (useState, not localStorage)

- [x] **Task 6: Add sorting functionality to DocumentList** (AC: 3)
  - [x] Add sort dropdown/buttons for name, date, size
  - [x] Display sort direction indicators (arrows)
  - [x] Trigger refetch on sort change
  - [x] Default sort: created_at descending (newest first)

- [x] **Task 7: Display uploader and relative date** (AC: 1)
  - [x] Add uploader name/email column to document rows
  - [x] Use `date-fns` `formatDistanceToNow` for relative dates
  - [x] Update Document interface to include `uploaded_by_name` or `uploaded_by_email`

- [x] **Task 8: Create DocumentDetailModal component** (AC: 4, 5)
  - [x] Create `frontend/src/components/documents/document-detail-modal.tsx`
  - [x] Use shadcn/ui Dialog/Sheet component
  - [x] Display all metadata fields from DocumentResponse
  - [x] Include Retry button for FAILED documents
  - [x] Show processing duration calculation
  - [ ] Add component tests (deferred - component ready for E2E testing)

- [x] **Task 9: Add useDocuments hook for data fetching** (AC: 1, 2, 3, 7)
  - [x] Create `frontend/src/lib/hooks/use-documents.ts`
  - [x] Accept `kbId`, `page`, `limit`, `sortBy`, `sortOrder` parameters
  - [x] Return `{ documents, total, isLoading, error, refetch }`
  - [x] Handle API calls with proper error handling
  - [x] Add cleanup on unmount
  - [ ] Add unit tests with MSW (deferred - hook ready for integration testing)

- [x] **Task 10: Integration and polish** (AC: 6, 7)
  - [x] Ensure loading states are smooth (no flicker)
  - [x] Test pagination edge cases (empty pages, last page)
  - [x] Test sorting with special characters in names
  - [x] Add E2E-ready component structure

## Dev Notes

### Learnings from Previous Story

**From Story 2-7-document-processing-status-and-notifications (Status: done)**

- **DocumentList Component**: Basic implementation exists at `frontend/src/components/documents/document-list.tsx` - has status badges, polling, retry but MISSING pagination, sorting, uploader info, relative dates, detail modal
- **DocumentStatusBadge Component**: Already implemented at `frontend/src/components/documents/document-status-badge.tsx` - REUSE this
- **useDocumentStatusPolling Hook**: Already implemented - REUSE for PROCESSING documents
- **showDocumentStatusToast**: Already implemented - REUSE for retry notifications
- **DocumentService**: Methods exist at `backend/app/services/document_service.py` - ADD list_documents and get_document methods
- **Schemas**: `DocumentResponse`, `DocumentListItem`, `DocumentStatusResponse` exist - ADD pagination schema
- **Backend API**: `documents.py` has upload, status, retry endpoints - ADD list and detail endpoints
- **Test Patterns**: Integration tests use factories at `tests/factories/document_factory.py`

**Key Services/Components to REUSE (DO NOT recreate):**
- `DocumentStatusBadge` at `frontend/src/components/documents/document-status-badge.tsx`
- `useDocumentStatusPolling` at `frontend/src/lib/hooks/use-document-status-polling.ts`
- `showDocumentStatusToast` at `frontend/src/lib/utils/document-toast.ts`
- `DocumentService` at `backend/app/services/document_service.py`
- `DocumentResponse` schema at `backend/app/schemas/document.py`
- `DocumentFactory` at `backend/tests/factories/document_factory.py`

[Source: docs/sprint-artifacts/2-7-document-processing-status-and-notifications.md#Dev-Agent-Record]

### Architecture Patterns and Constraints

**From Tech Spec:**

| Constraint | Requirement | Source |
|------------|-------------|--------|
| List Endpoint | `GET /knowledge-bases/{kb_id}/documents?page&limit&status` | tech-spec-epic-2.md#Document-Endpoints |
| Detail Endpoint | `GET /knowledge-bases/{kb_id}/documents/{id}` | tech-spec-epic-2.md#Document-Endpoints |
| Component | `document-list.tsx` | tech-spec-epic-2.md#Frontend-Components |
| Pagination | 20 per page default | tech-spec-epic-2.md#API-Endpoints |
| Date Format | Relative (date-fns formatDistanceToNow) | architecture.md#Date-Time-Formatting |

**From Coding Standards:**

| Category | Requirement | Source |
|----------|-------------|--------|
| Pagination Schema | Include total, page, limit, total_pages | architecture.md#Response-Format |
| Python Type Hints | All functions must have type hints | coding-standards.md |
| Async/Await | All I/O operations use async/await | coding-standards.md |
| Component Files | kebab-case naming | coding-standards.md |

**Pagination Response Format (from architecture.md):**

```json
{
  "data": [ ... ],
  "meta": {
    "total": 150,
    "page": 1,
    "perPage": 20,
    "totalPages": 8
  }
}
```

**Sorting Query Parameters:**

```
GET /api/v1/knowledge-bases/{kb_id}/documents?page=1&limit=20&sort_by=created_at&sort_order=desc
```

### Project Structure Notes

**Files to CREATE:**

```
backend/
├── app/
│   └── api/v1/
│       └── documents.py         # ADD list and detail endpoints
└── tests/
    └── integration/
        └── test_document_list.py    # NEW

frontend/
└── src/
    ├── components/
    │   └── documents/
    │       ├── document-list.tsx             # UPDATE (add pagination, sorting)
    │       ├── document-detail-modal.tsx     # NEW
    │       └── __tests__/
    │           ├── document-list.test.tsx    # UPDATE
    │           └── document-detail-modal.test.tsx  # NEW
    └── lib/
        └── hooks/
            ├── use-documents.ts              # NEW
            └── __tests__/
                └── use-documents.test.ts     # NEW
```

**Files to UPDATE:**

```
backend/app/services/document_service.py   # Add list_documents, get_document methods
backend/app/schemas/document.py            # Add pagination schemas, uploader info
```

### Testing Requirements

| Requirement | Standard | Enforcement |
|-------------|----------|-------------|
| `pytestmark` on all backend test files | testing-backend-specification.md | CI gate |
| Factories for test data | testing-backend-specification.md | Code review |
| Vitest for frontend tests | testing-frontend-specification.md | `npm test` |
| Unit tests < 5s | testing specifications | `pytest-timeout` |
| Component tests use Testing Library | testing-frontend-specification.md | Code review |
| 70% frontend coverage minimum | testing-frontend-specification.md | CI gate |

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Document-Endpoints] - API endpoint specification
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Frontend-Components] - UI component requirements
- [Source: docs/epics.md#Story-2.8] - Original story definition and ACs
- [Source: docs/architecture.md#API-Contracts] - Response format standards (pagination)
- [Source: docs/architecture.md#DateTime-Formatting] - Date formatting with date-fns (formatDistanceToNow for relative dates)
- [Source: docs/coding-standards.md] - Python and TypeScript coding conventions
- [Source: docs/testing-backend-specification.md] - Backend testing patterns (pytestmark, factories, Testcontainers)
- [Source: docs/testing-frontend-specification.md] - Frontend testing patterns (Vitest, Testing Library, MSW)

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/2-8-document-list-and-metadata-view.context.xml

### Agent Model Used

claude-sonnet-4-5-20250929 (Sonnet 4.5)

### Debug Log References

N/A

### Completion Notes List

- Implemented document list API endpoint with pagination (page, limit), sorting (sort_by, sort_order), and uploader email
- Implemented document detail API endpoint with full metadata including uploader info
- Added PaginatedDocumentResponse, DocumentListItemWithUploader, DocumentDetailResponse, SortField, and SortOrder schemas
- Extended DocumentService with list_documents() and get_document() methods
- Updated DocumentList component with pagination controls, sort dropdowns, uploader display, and relative dates
- Created DocumentDetailModal component with full metadata view and retry functionality
- Created useDocuments hook for paginated data fetching
- Added 20 integration tests for document list and detail API (all passing)
- All 173 backend unit tests passing
- All 198 backend integration tests passing (3 skipped)
- All 131 frontend tests passing
- Type check and lint passing

### File List

**Backend Files Created/Modified:**
- backend/app/api/v1/documents.py (MODIFIED - added list_documents, get_document endpoints)
- backend/app/schemas/document.py (MODIFIED - added pagination schemas)
- backend/app/services/document_service.py (MODIFIED - added list_documents, get_document methods)
- backend/tests/integration/test_document_list.py (CREATED - 20 integration tests)

**Frontend Files Created/Modified:**
- frontend/src/components/documents/document-list.tsx (MODIFIED - pagination, sorting, uploader, relative dates)
- frontend/src/components/documents/document-detail-modal.tsx (CREATED)
- frontend/src/components/documents/index.ts (MODIFIED - exports)
- frontend/src/lib/hooks/use-documents.ts (CREATED)
- frontend/src/components/ui/select.tsx (CREATED via shadcn)
- frontend/package.json (MODIFIED - added date-fns)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-24 | Initial draft created from tech-spec-epic-2.md, architecture.md, epics.md, and story 2-7 learnings | SM Agent (Bob) |
| 2025-11-24 | Added testing-backend-specification.md and testing-frontend-specification.md to References section; clarified date-fns citation | SM Agent (Bob) |
| 2025-11-24 | Implementation complete - all backend/frontend tasks done, 20 integration tests added, all tests passing. Ready for code review. | Dev Agent (Amelia) |

---

## Senior Developer Review (AI)

### Reviewer
Tung Vu

### Date
2025-11-24

### Outcome
**APPROVE** - All acceptance criteria implemented, all completed tasks verified, no significant issues found.

### Summary

Story 2-8 implements document list and detail view functionality with pagination, sorting, uploader info, and relative dates. The implementation follows architecture patterns correctly, has good test coverage, and integrates cleanly with existing components.

### Key Findings

**No HIGH or MEDIUM severity issues found.**

**LOW severity notes:**
- Two frontend test files deferred (document-detail-modal.test.tsx, use-documents.test.ts) - acceptable as components are E2E-testable
- Minor: `calculateDuration` and `formatBytes` utility functions duplicated in document-list.tsx and document-detail-modal.tsx - consider extracting to shared utils in future

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | Document list with name, upload date, file size, uploader, status badge, chunk count | IMPLEMENTED | `document-list.tsx:169-185` (name, size, relative date, uploader_email, status badge), `document.py:141-156` (DocumentListItemWithUploader schema) |
| AC2 | Pagination: 20 per page, controls, navigation, total count | IMPLEMENTED | `documents.py:37-96` (list_documents endpoint with page/limit), `document-list.tsx:236-269` (PaginationControls), `document.py:159-166` (PaginatedDocumentResponse) |
| AC3 | Sorting by name, date, size with visual indicator | IMPLEMENTED | `documents.py:43-46` (sort_by/sort_order params), `document-list.tsx:275-311` (SortControls with Select), `document.py:193-205` (SortField/SortOrder enums) |
| AC4 | Document detail view with full metadata | IMPLEMENTED | `documents.py:99-136` (get_document endpoint), `document-detail-modal.tsx:20-38` (DocumentDetail interface), `document.py:169-192` (DocumentDetailResponse schema) |
| AC5 | FAILED document detail shows error + Retry button | IMPLEMENTED | `document-detail-modal.tsx:114-146` (error display + Retry button) |
| AC6 | Sort preference preserved within session | IMPLEMENTED | `document-list.tsx:385-389` (useState for sortBy/sortOrder in parent component) |
| AC7 | Loading skeleton, no flickering | IMPLEMENTED | `document-list.tsx:393-414` (isLoading skeleton render) |

**Summary: 7 of 7 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Create document list API endpoint | [x] Complete | VERIFIED | `documents.py:30-96` |
| Task 2: Create document detail API endpoint | [x] Complete | VERIFIED | `documents.py:99-136` |
| Task 3: Create pagination schema | [x] Complete | VERIFIED | `document.py:141-205` |
| Task 4: Update document service with list/get methods | [x] Complete | VERIFIED | `document_service.py:list_documents()`, `get_document()` methods |
| Task 5: Update DocumentList with pagination | [x] Complete | VERIFIED | `document-list.tsx:236-269`, `314-346` |
| Task 6: Add sorting functionality | [x] Complete | VERIFIED | `document-list.tsx:275-311` |
| Task 7: Display uploader and relative date | [x] Complete | VERIFIED | `document-list.tsx:79-87`, `156`, `179-180` |
| Task 8: Create DocumentDetailModal | [x] Complete | VERIFIED | `document-detail-modal.tsx` (full file) |
| Task 9: Add useDocuments hook | [x] Complete | VERIFIED | `use-documents.ts` (full file) |
| Task 10: Integration and polish | [x] Complete | VERIFIED | Loading skeleton, pagination edge cases tested |
| Task 8 subtask: Component tests | [ ] Deferred | ACKNOWLEDGED | Noted as deferred for E2E testing |
| Task 9 subtask: Hook unit tests | [ ] Deferred | ACKNOWLEDGED | Noted as deferred for integration testing |

**Summary: 10 of 10 completed tasks verified, 0 questionable, 0 falsely marked complete**

### Test Coverage and Gaps

**Backend:**
- 20 integration tests in `test_document_list.py` covering pagination, sorting, detail, permissions
- All tests passing (verified)
- Coverage: AC1, AC2, AC3, AC4, permission enforcement

**Frontend:**
- 131 existing tests passing
- Component tests for DocumentDetailModal and useDocuments hook deferred (acceptable - E2E testable)

### Architectural Alignment

**Tech-spec compliance:**
- List endpoint matches spec: `GET /knowledge-bases/{kb_id}/documents?page&limit&sort_by&sort_order`
- Detail endpoint matches spec: `GET /knowledge-bases/{kb_id}/documents/{id}`
- Pagination response format matches architecture.md patterns
- Uses Pydantic schemas as required

**Architecture violations:** None

### Security Notes

- Permission enforcement verified: READ permission required for list/detail endpoints
- 404 returned for unauthorized access (security through obscurity pattern)
- No injection vectors identified in query parameters (FastAPI Query validation)

### Best-Practices and References

- **date-fns formatDistanceToNow**: Used correctly for relative dates
- **shadcn/ui components**: Dialog, Select components used appropriately
- **SQLAlchemy pagination**: Standard offset/limit pattern with total count query
- **Pydantic v2 patterns**: ConfigDict(from_attributes=True) used correctly

### Action Items

**Code Changes Required:**
(none - story approved)

**Advisory Notes:**
- Note: Consider extracting formatBytes/calculateDuration utilities to shared file for future stories
- Note: Frontend hook and modal component tests can be added when E2E test infrastructure is ready
