# ATDD Checklist - Epic 6: Document Lifecycle Management

**Epic:** Epic 6 - Document Lifecycle Management
**Total Stories:** 9 (35 Story Points)
**Total Acceptance Criteria:** 60
**Generated:** 2025-12-07
**Status:** DRAFT - Ready for Implementation

---

## Overview

This ATDD checklist tracks all acceptance criteria for Epic 6: Document Lifecycle Management. Each criterion includes testable scenarios in Given/When/Then format with automation status tracking.

### Legend
- [ ] Not Started
- [~] In Progress
- [x] Completed
- [S] Skipped (with reason)

---

## Story 6-1: Archive Document Backend (5 SP)

### AC-6.1.1: Archive Endpoint
**Criterion:** POST `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive` sets `archived_at` timestamp and returns updated document.

| # | Scenario | Status |
|---|----------|--------|
| 1.1.1 | Given a completed document, When POST archive endpoint called, Then archived_at is set to current timestamp | [ ] |
| 1.1.2 | Given a completed document, When archived, Then response returns document with status "archived" | [ ] |
| 1.1.3 | Given archived document, When GET document, Then archived_at timestamp is included in response | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestArchiveEndpoint`

---

### AC-6.1.2: Status Validation
**Criterion:** Only documents with status "completed" can be archived; others return 400 Bad Request with reason.

| # | Scenario | Status |
|---|----------|--------|
| 1.2.1 | Given document with status "completed", When archive called, Then returns 200 OK | [ ] |
| 1.2.2 | Given document with status "pending", When archive called, Then returns 400 with "only completed documents can be archived" | [ ] |
| 1.2.3 | Given document with status "processing", When archive called, Then returns 400 | [ ] |
| 1.2.4 | Given document with status "failed", When archive called, Then returns 400 | [ ] |
| 1.2.5 | Given document already archived, When archive called again, Then returns 400 "document already archived" | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestArchiveStatusValidation`

---

### AC-6.1.3: Qdrant Vector Exclusion
**Criterion:** Archived documents have their Qdrant vectors marked with `archived: true` payload, excluding them from search results.

| # | Scenario | Status |
|---|----------|--------|
| 1.3.1 | Given document with vectors in Qdrant, When archived, Then vectors have archived:true payload | [ ] |
| 1.3.2 | Given archived document, When semantic search performed, Then document chunks not returned | [ ] |
| 1.3.3 | Given archived document, When similar search performed, Then document not in results | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestQdrantArchiveFlag`

---

### AC-6.1.4: Bulk Archive
**Criterion:** POST `/api/v1/knowledge-bases/{kb_id}/documents/bulk-archive` accepts array of document IDs and returns success/failure per document.

| # | Scenario | Status |
|---|----------|--------|
| 1.4.1 | Given 3 completed documents, When bulk archive called, Then all 3 archived successfully | [ ] |
| 1.4.2 | Given mix of completed and pending docs, When bulk archive, Then partial success with per-doc status | [ ] |
| 1.4.3 | Given empty array, When bulk archive, Then returns 400 | [ ] |
| 1.4.4 | Given 100+ documents, When bulk archive, Then handles within timeout | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestBulkArchive`

---

### AC-6.1.5: Permission Check
**Criterion:** Only KB owner or admin can archive documents; others receive 403 Forbidden.

| # | Scenario | Status |
|---|----------|--------|
| 1.5.1 | Given KB owner, When archive document, Then returns 200 | [ ] |
| 1.5.2 | Given admin user, When archive document, Then returns 200 | [ ] |
| 1.5.3 | Given viewer user, When archive document, Then returns 403 | [ ] |
| 1.5.4 | Given editor user (non-owner), When archive document, Then returns 403 | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestArchivePermissions`

---

### AC-6.1.6: Audit Logging
**Criterion:** Archive action creates audit log entry with document_id, user_id, and timestamp.

| # | Scenario | Status |
|---|----------|--------|
| 1.6.1 | Given successful archive, When audit log queried, Then contains DOCUMENT_ARCHIVED event | [ ] |
| 1.6.2 | Given archive event, When inspected, Then contains document_id, user_id, kb_id | [ ] |
| 1.6.3 | Given failed archive attempt (403), When audit queried, Then contains failed attempt log | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestArchiveAuditLog`

---

## Story 6-2: Restore Document Backend (5 SP)

### AC-6.2.1: Restore Endpoint
**Criterion:** POST `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore` clears `archived_at` and returns updated document.

| # | Scenario | Status |
|---|----------|--------|
| 2.1.1 | Given archived document, When POST restore called, Then archived_at becomes null | [ ] |
| 2.1.2 | Given archived document, When restored, Then status returns to "completed" | [ ] |
| 2.1.3 | Given non-archived document, When restore called, Then returns 400 "document not archived" | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestRestoreEndpoint`

---

### AC-6.2.2: Qdrant Vector Restoration
**Criterion:** Restored documents have their Qdrant vectors' `archived` payload set to `false`, re-enabling search.

| # | Scenario | Status |
|---|----------|--------|
| 2.2.1 | Given archived document with vectors, When restored, Then vectors have archived:false | [ ] |
| 2.2.2 | Given restored document, When semantic search performed, Then document chunks appear in results | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestQdrantRestoreFlag`

---

### AC-6.2.3: Name Collision Detection
**Criterion:** If restoring document would create duplicate filename in active documents, return 409 Conflict with existing document details.

| # | Scenario | Status |
|---|----------|--------|
| 2.3.1 | Given archived "report.pdf" and active "report.pdf" exists, When restore, Then returns 409 | [ ] |
| 2.3.2 | Given 409 response, Then body contains existing_document_id and suggestion | [ ] |
| 2.3.3 | Given no naming conflict, When restore, Then succeeds with 200 | [ ] |
| 2.3.4 | Given case-insensitive match (Report.PDF vs report.pdf), When restore, Then returns 409 | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestRestoreNameCollision`

---

### AC-6.2.4: Bulk Restore
**Criterion:** POST `/api/v1/knowledge-bases/{kb_id}/documents/bulk-restore` handles multiple documents with per-document status reporting.

| # | Scenario | Status |
|---|----------|--------|
| 2.4.1 | Given 3 archived documents, When bulk restore, Then all restored successfully | [ ] |
| 2.4.2 | Given 1 archived + 1 with name collision, When bulk restore, Then partial success reported | [ ] |
| 2.4.3 | Given bulk restore partial failure, Then response includes per-document error details | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestBulkRestore`

---

### AC-6.2.5: Permission Check
**Criterion:** Only KB owner or admin can restore documents; others receive 403 Forbidden.

| # | Scenario | Status |
|---|----------|--------|
| 2.5.1 | Given KB owner, When restore document, Then returns 200 | [ ] |
| 2.5.2 | Given viewer user, When restore document, Then returns 403 | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestRestorePermissions`

---

### AC-6.2.6: Search Reappearance
**Criterion:** After restore, document appears in search results within 5 seconds.

| # | Scenario | Status |
|---|----------|--------|
| 2.6.1 | Given restored document, When search immediately after, Then document in results | [ ] |
| 2.6.2 | Given restored document, When list documents, Then appears in active list | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestRestoreSearchReappearance`

---

## Story 6-3: Purge Document Backend (5 SP)

### AC-6.3.1: Purge Endpoint
**Criterion:** DELETE `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge` permanently deletes document record and returns 204 No Content.

| # | Scenario | Status |
|---|----------|--------|
| 3.1.1 | Given archived document, When purge called, Then returns 204 | [ ] |
| 3.1.2 | Given purged document, When GET document, Then returns 404 | [ ] |
| 3.1.3 | Given active (non-archived) document, When purge called, Then returns 400 "must archive first" | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestPurgeEndpoint`

---

### AC-6.3.2: Multi-Layer Cleanup
**Criterion:** Purge removes: PostgreSQL record, all Qdrant vectors, MinIO stored file.

| # | Scenario | Status |
|---|----------|--------|
| 3.2.1 | Given document with vectors, When purged, Then vectors deleted from Qdrant | [ ] |
| 3.2.2 | Given document with file in MinIO, When purged, Then file deleted from MinIO | [ ] |
| 3.2.3 | Given document record, When purged, Then PostgreSQL record deleted | [ ] |
| 3.2.4 | Given partial cleanup failure (Qdrant fails), Then transaction rolls back | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestPurgeMultiLayerCleanup`

---

### AC-6.3.3: Bulk Purge
**Criterion:** DELETE `/api/v1/knowledge-bases/{kb_id}/documents/bulk-purge` permanently deletes multiple documents with per-document status.

| # | Scenario | Status |
|---|----------|--------|
| 3.3.1 | Given 3 archived documents, When bulk purge, Then all permanently deleted | [ ] |
| 3.3.2 | Given mix of archived and active, When bulk purge, Then only archived purged | [ ] |
| 3.3.3 | Given bulk purge, Then response includes success count and failure details | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestBulkPurge`

---

### AC-6.3.4: Confirmation Required
**Criterion:** Purge requires `confirm=true` query parameter; omitting returns 400 with warning message.

| # | Scenario | Status |
|---|----------|--------|
| 3.4.1 | Given purge without confirm param, Then returns 400 "confirmation required" | [ ] |
| 3.4.2 | Given purge with confirm=false, Then returns 400 | [ ] |
| 3.4.3 | Given purge with confirm=true, Then proceeds with deletion | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestPurgeConfirmation`

---

### AC-6.3.5: Admin Only
**Criterion:** Only admin users can purge documents; KB owners receive 403 for purge operations.

| # | Scenario | Status |
|---|----------|--------|
| 3.5.1 | Given admin user, When purge document, Then returns 204 | [ ] |
| 3.5.2 | Given KB owner (non-admin), When purge document, Then returns 403 | [ ] |
| 3.5.3 | Given viewer user, When purge document, Then returns 403 | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestPurgeAdminOnly`

---

### AC-6.3.6: Audit Logging
**Criterion:** Purge action creates permanent audit log entry (retained even after document deletion).

| # | Scenario | Status |
|---|----------|--------|
| 3.6.1 | Given successful purge, When audit log queried, Then contains DOCUMENT_PURGED event | [ ] |
| 3.6.2 | Given purge audit entry, Then contains document metadata snapshot (name, size, etc.) | [ ] |
| 3.6.3 | Given purge audit entry, Then audit log retained after document gone | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestPurgeAuditLog`

---

## Story 6-4: Clear Failed Document Backend (3 SP)

### AC-6.4.1: Clear Endpoint
**Criterion:** DELETE `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear` removes failed documents and returns 204 No Content.

| # | Scenario | Status |
|---|----------|--------|
| 4.1.1 | Given failed document, When clear called, Then returns 204 | [ ] |
| 4.1.2 | Given cleared document, When GET document, Then returns 404 | [ ] |
| 4.1.3 | Given completed document, When clear called, Then returns 400 "only failed documents can be cleared" | [ ] |
| 4.1.4 | Given pending document, When clear called, Then returns 400 | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestClearEndpoint`

---

### AC-6.4.2: Artifact Cleanup
**Criterion:** Clear removes any partial artifacts: incomplete Qdrant vectors, partial MinIO uploads.

| # | Scenario | Status |
|---|----------|--------|
| 4.2.1 | Given failed doc with partial vectors, When cleared, Then vectors removed from Qdrant | [ ] |
| 4.2.2 | Given failed doc with partial MinIO upload, When cleared, Then file removed from MinIO | [ ] |
| 4.2.3 | Given failed doc with no artifacts, When cleared, Then only PostgreSQL record removed | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestClearArtifactCleanup`

---

### AC-6.4.3: Bulk Clear
**Criterion:** DELETE `/api/v1/knowledge-bases/{kb_id}/documents/bulk-clear` clears all failed documents in KB.

| # | Scenario | Status |
|---|----------|--------|
| 4.3.1 | Given 5 failed documents in KB, When bulk clear, Then all 5 removed | [ ] |
| 4.3.2 | Given mix of failed and completed, When bulk clear, Then only failed removed | [ ] |
| 4.3.3 | Given no failed documents, When bulk clear, Then returns 200 with count: 0 | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestBulkClear`

---

### AC-6.4.4: Task Revocation
**Criterion:** If failed document has pending Celery tasks, those tasks are revoked before cleanup.

| # | Scenario | Status |
|---|----------|--------|
| 4.4.1 | Given failed doc with pending retry task, When cleared, Then Celery task revoked | [ ] |
| 4.4.2 | Given failed doc with no pending tasks, When cleared, Then proceeds normally | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestClearTaskRevocation`

---

### AC-6.4.5: Permission Check
**Criterion:** KB owner or admin can clear failed documents.

| # | Scenario | Status |
|---|----------|--------|
| 4.5.1 | Given KB owner, When clear failed document, Then returns 204 | [ ] |
| 4.5.2 | Given admin user, When clear failed document, Then returns 204 | [ ] |
| 4.5.3 | Given viewer user, When clear failed document, Then returns 403 | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestClearPermissions`

---

## Story 6-5: Duplicate Detection & Auto-Clear Backend (5 SP)

### AC-6.5.1: Upload Duplicate Detection
**Criterion:** Document upload checks for existing document with same filename (case-insensitive) in KB.

| # | Scenario | Status |
|---|----------|--------|
| 5.1.1 | Given "report.pdf" exists, When upload "report.pdf", Then duplicate detected | [ ] |
| 5.1.2 | Given "report.pdf" exists, When upload "Report.PDF", Then duplicate detected (case-insensitive) | [ ] |
| 5.1.3 | Given "report.pdf" exists, When upload "report_v2.pdf", Then no duplicate (different name) | [ ] |
| 5.1.4 | Given archived "report.pdf", When upload "report.pdf", Then no duplicate (archived excluded) | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestDuplicateDetection`

---

### AC-6.5.2: 409 Conflict Response
**Criterion:** When duplicate detected, return 409 Conflict with existing document details and available actions.

| # | Scenario | Status |
|---|----------|--------|
| 5.2.1 | Given duplicate detected, Then response status is 409 | [ ] |
| 5.2.2 | Given 409 response, Then body contains existing_document_id | [ ] |
| 5.2.3 | Given 409 response, Then body contains existing_document_name | [ ] |
| 5.2.4 | Given 409 response, Then body contains available_actions: ["replace", "rename", "cancel"] | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestDuplicate409Response`

---

### AC-6.5.3: Auto-Clear Failed Duplicates
**Criterion:** If uploading duplicate of a failed document, automatically clear the failed document and proceed.

| # | Scenario | Status |
|---|----------|--------|
| 5.3.1 | Given failed "report.pdf", When upload "report.pdf", Then failed doc auto-cleared | [ ] |
| 5.3.2 | Given auto-cleared failed doc, Then new upload proceeds successfully | [ ] |
| 5.3.3 | Given auto-clear, Then audit log contains both CLEAR and UPLOAD events | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestAutoClearFailedDuplicates`

---

### AC-6.5.4: Hash-Based Detection (Optional)
**Criterion:** Optionally detect duplicates by file content hash (SHA-256) in addition to filename.

| # | Scenario | Status |
|---|----------|--------|
| 5.4.1 | Given file with same hash exists, When upload with hash_check=true, Then duplicate detected | [ ] |
| 5.4.2 | Given same filename but different hash, When upload, Then filename duplicate detected | [ ] |
| 5.4.3 | Given hash_check not specified, Then only filename checked (default) | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestHashBasedDetection`

---

### AC-6.5.5: Duplicate Check Response Time
**Criterion:** Duplicate check completes within 200ms for KBs with up to 10,000 documents.

| # | Scenario | Status |
|---|----------|--------|
| 5.5.1 | Given KB with 10,000 documents, When upload with duplicate check, Then response < 200ms | [ ] |
| 5.5.2 | Given KB with 100 documents, When duplicate check, Then response < 50ms | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestDuplicateCheckPerformance`

---

## Story 6-6: Replace Document Backend (5 SP)

### AC-6.6.1: Replace Endpoint
**Criterion:** POST `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace` accepts new file and returns updated document.

| # | Scenario | Status |
|---|----------|--------|
| 6.1.1 | Given completed document, When replace with new file, Then returns 200 with updated doc | [ ] |
| 6.1.2 | Given replace request, Then response contains new file metadata | [ ] |
| 6.1.3 | Given failed document, When replace called, Then returns 400 "cannot replace failed document" | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestReplaceEndpoint`

---

### AC-6.6.2: Atomic Delete-Upload
**Criterion:** Replace operation atomically: deletes old vectors/file, uploads new file, re-processes.

| # | Scenario | Status |
|---|----------|--------|
| 6.2.1 | Given replace initiated, Then old Qdrant vectors deleted | [ ] |
| 6.2.2 | Given replace initiated, Then old MinIO file deleted | [ ] |
| 6.2.3 | Given replace initiated, Then new file uploaded to MinIO | [ ] |
| 6.2.4 | Given replace initiated, Then processing task queued for new file | [ ] |
| 6.2.5 | Given replace fails mid-operation, Then rolls back to original state | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestReplaceAtomicOperation`

---

### AC-6.6.3: Document ID Preservation
**Criterion:** Replaced document keeps same document_id; citations referencing old content show "content updated" indicator.

| # | Scenario | Status |
|---|----------|--------|
| 6.3.1 | Given replace completed, Then document_id unchanged | [ ] |
| 6.3.2 | Given replace completed, Then created_at unchanged | [ ] |
| 6.3.3 | Given replace completed, Then updated_at reflects replacement time | [ ] |
| 6.3.4 | Given old citation after replace, When viewed, Then shows "content updated" | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestReplaceIdPreservation`

---

### AC-6.6.4: Processing Status
**Criterion:** After replace, document enters "processing" status until new content indexed.

| # | Scenario | Status |
|---|----------|--------|
| 6.4.1 | Given replace initiated, Then document status becomes "processing" | [ ] |
| 6.4.2 | Given processing complete, Then status returns to "completed" | [ ] |
| 6.4.3 | Given processing fails, Then status becomes "failed" with error details | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestReplaceProcessingStatus`

---

### AC-6.6.5: Version History (Optional)
**Criterion:** Optionally track replacement as new version with previous version accessible.

| # | Scenario | Status |
|---|----------|--------|
| 6.5.1 | Given replace with versioning enabled, Then version number increments | [ ] |
| 6.5.2 | Given versioned document, When GET versions, Then returns version history | [ ] |
| 6.5.3 | Given version history, Then each version has separate MinIO path | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestReplaceVersionHistory`

---

### AC-6.6.6: Permission Check
**Criterion:** KB owner or admin can replace documents.

| # | Scenario | Status |
|---|----------|--------|
| 6.6.1 | Given KB owner, When replace document, Then returns 200 | [ ] |
| 6.6.2 | Given admin user, When replace document, Then returns 200 | [ ] |
| 6.6.3 | Given editor user, When replace document, Then returns 403 | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestReplacePermissions`

---

### AC-6.6.7: Audit Logging
**Criterion:** Replace action creates audit log with old and new file metadata.

| # | Scenario | Status |
|---|----------|--------|
| 6.7.1 | Given successful replace, Then audit log contains DOCUMENT_REPLACED event | [ ] |
| 6.7.2 | Given replace audit entry, Then contains old_file_hash and new_file_hash | [ ] |
| 6.7.3 | Given replace audit entry, Then contains old_size and new_size | [ ] |

**Test File:** `backend/tests/integration/test_archive_api.py::TestReplaceAuditLog`

---

## Story 6-7: Archive Management UI (3 SP)

### AC-6.7.1: Archive Page Access
**Criterion:** Archive management accessible via KB settings or dedicated "Archive" tab in document list.

| # | Scenario | Status |
|---|----------|--------|
| 7.1.1 | Given document list page, When "Archive" tab clicked, Then archive view displayed | [ ] |
| 7.1.2 | Given KB settings, When "Manage Archive" clicked, Then archive view displayed | [ ] |
| 7.1.3 | Given archive view, Then shows only archived documents | [ ] |

**Test File:** `frontend/e2e/tests/archive/archive-management.spec.ts::ArchivePageAccess`

---

### AC-6.7.2: Archive Statistics
**Criterion:** Archive page shows: total archived count, storage used by archived docs, oldest/newest archive dates.

| # | Scenario | Status |
|---|----------|--------|
| 7.2.1 | Given archive page, Then displays total archived document count | [ ] |
| 7.2.2 | Given archive page, Then displays total storage used by archived docs | [ ] |
| 7.2.3 | Given archive page, Then displays date range (oldest to newest archived) | [ ] |

**Test File:** `frontend/e2e/tests/archive/archive-management.spec.ts::ArchiveStatistics`

---

### AC-6.7.3: Archived Document List
**Criterion:** List shows document name, original upload date, archived date, file size with sorting options.

| # | Scenario | Status |
|---|----------|--------|
| 7.3.1 | Given archived documents, Then list shows document name column | [ ] |
| 7.3.2 | Given archived documents, Then list shows upload date column | [ ] |
| 7.3.3 | Given archived documents, Then list shows archived date column | [ ] |
| 7.3.4 | Given archived documents, Then list shows file size column | [ ] |
| 7.3.5 | Given list headers, When clicked, Then sorts by that column | [ ] |

**Test File:** `frontend/e2e/tests/archive/archive-management.spec.ts::ArchivedDocumentList`

---

### AC-6.7.4: Restore Action
**Criterion:** Each archived document has "Restore" button that calls restore API and shows success/conflict feedback.

| # | Scenario | Status |
|---|----------|--------|
| 7.4.1 | Given archived document row, Then "Restore" button visible | [ ] |
| 7.4.2 | Given restore clicked, When successful, Then shows success toast | [ ] |
| 7.4.3 | Given restore clicked, When 409 conflict, Then shows conflict modal | [ ] |
| 7.4.4 | Given successful restore, Then document removed from archive list | [ ] |

**Test File:** `frontend/e2e/tests/archive/archive-management.spec.ts::RestoreAction`

---

### AC-6.7.5: Purge Action
**Criterion:** Each archived document has "Purge" button (admin only) with confirmation dialog warning of permanent deletion.

| # | Scenario | Status |
|---|----------|--------|
| 7.5.1 | Given admin user on archive page, Then "Purge" button visible | [ ] |
| 7.5.2 | Given non-admin user, Then "Purge" button hidden or disabled | [ ] |
| 7.5.3 | Given purge clicked, Then confirmation dialog appears | [ ] |
| 7.5.4 | Given confirmation dialog, Then warns "This action cannot be undone" | [ ] |
| 7.5.5 | Given purge confirmed, Then document permanently removed | [ ] |

**Test File:** `frontend/e2e/tests/archive/archive-management.spec.ts::PurgeAction`

---

### AC-6.7.6: Bulk Selection
**Criterion:** Checkbox selection allows bulk restore or purge of multiple archived documents.

| # | Scenario | Status |
|---|----------|--------|
| 7.6.1 | Given archive list, Then each row has checkbox | [ ] |
| 7.6.2 | Given multiple selected, Then "Bulk Restore" button appears | [ ] |
| 7.6.3 | Given multiple selected (admin), Then "Bulk Purge" button appears | [ ] |
| 7.6.4 | Given "Select All" checkbox, When clicked, Then all visible selected | [ ] |

**Test File:** `frontend/e2e/tests/archive/archive-management.spec.ts::BulkSelection`

---

### AC-6.7.7: Search & Filter
**Criterion:** Archive list supports search by document name and filter by archived date range.

| # | Scenario | Status |
|---|----------|--------|
| 7.7.1 | Given search input, When text entered, Then list filtered by name | [ ] |
| 7.7.2 | Given date range picker, When dates selected, Then list filtered by archived date | [ ] |
| 7.7.3 | Given filters applied, Then "Clear Filters" button visible | [ ] |

**Test File:** `frontend/e2e/tests/archive/archive-management.spec.ts::SearchAndFilter`

---

### AC-6.7.8: Empty State
**Criterion:** When no archived documents, show helpful empty state with explanation.

| # | Scenario | Status |
|---|----------|--------|
| 7.8.1 | Given no archived documents, Then empty state illustration shown | [ ] |
| 7.8.2 | Given empty state, Then explains what archiving is | [ ] |
| 7.8.3 | Given empty state, Then provides link to documentation | [ ] |

**Test File:** `frontend/e2e/tests/archive/archive-management.spec.ts::EmptyState`

---

### AC-6.7.9: Loading States
**Criterion:** Show skeleton loaders while fetching archived documents list.

| # | Scenario | Status |
|---|----------|--------|
| 7.9.1 | Given archive page loading, Then skeleton rows displayed | [ ] |
| 7.9.2 | Given archive page loaded, Then skeleton replaced with data | [ ] |
| 7.9.3 | Given action in progress (restore/purge), Then button shows loading spinner | [ ] |

**Test File:** `frontend/e2e/tests/archive/archive-management.spec.ts::LoadingStates`

---

### AC-6.7.10: Responsive Design
**Criterion:** Archive management UI works on tablet (768px) and desktop (1024px+) viewports.

| # | Scenario | Status |
|---|----------|--------|
| 7.10.1 | Given 768px viewport, Then archive UI fully functional | [ ] |
| 7.10.2 | Given 1024px viewport, Then archive UI displays optimally | [ ] |
| 7.10.3 | Given small viewport, Then horizontal scroll for wide table | [ ] |

**Test File:** `frontend/e2e/tests/archive/archive-management.spec.ts::ResponsiveDesign`

---

## Story 6-8: Document List Actions UI (2 SP)

### AC-6.8.1: Archive Action in Menu
**Criterion:** Document row dropdown menu includes "Archive" option for completed documents.

| # | Scenario | Status |
|---|----------|--------|
| 8.1.1 | Given completed document, When menu opened, Then "Archive" option visible | [ ] |
| 8.1.2 | Given pending document, When menu opened, Then "Archive" option disabled/hidden | [ ] |
| 8.1.3 | Given processing document, When menu opened, Then "Archive" option disabled/hidden | [ ] |

**Test File:** `frontend/e2e/tests/documents/document-actions.spec.ts::ArchiveActionInMenu`

---

### AC-6.8.2: Archive Confirmation
**Criterion:** Clicking "Archive" shows confirmation dialog before executing.

| # | Scenario | Status |
|---|----------|--------|
| 8.2.1 | Given "Archive" clicked, Then confirmation dialog appears | [ ] |
| 8.2.2 | Given dialog, Then shows document name being archived | [ ] |
| 8.2.3 | Given dialog, Then has "Cancel" and "Archive" buttons | [ ] |
| 8.2.4 | Given "Cancel" clicked, Then dialog closes, no action taken | [ ] |

**Test File:** `frontend/e2e/tests/documents/document-actions.spec.ts::ArchiveConfirmation`

---

### AC-6.8.3: Archive Feedback
**Criterion:** After successful archive, show toast notification and remove document from active list.

| # | Scenario | Status |
|---|----------|--------|
| 8.3.1 | Given archive confirmed, When successful, Then success toast shown | [ ] |
| 8.3.2 | Given successful archive, Then document removed from active list | [ ] |
| 8.3.3 | Given archive fails, Then error toast shown with reason | [ ] |

**Test File:** `frontend/e2e/tests/documents/document-actions.spec.ts::ArchiveFeedback`

---

### AC-6.8.4: Clear Failed Action
**Criterion:** Failed document row dropdown includes "Clear" option to remove failed document.

| # | Scenario | Status |
|---|----------|--------|
| 8.4.1 | Given failed document, When menu opened, Then "Clear" option visible | [ ] |
| 8.4.2 | Given completed document, When menu opened, Then "Clear" option hidden | [ ] |
| 8.4.3 | Given "Clear" clicked, Then confirmation dialog appears | [ ] |

**Test File:** `frontend/e2e/tests/documents/document-actions.spec.ts::ClearFailedAction`

---

### AC-6.8.5: Clear Feedback
**Criterion:** After clearing failed document, show toast and remove from list.

| # | Scenario | Status |
|---|----------|--------|
| 8.5.1 | Given clear confirmed, When successful, Then success toast shown | [ ] |
| 8.5.2 | Given successful clear, Then document removed from list | [ ] |
| 8.5.3 | Given clear fails, Then error toast shown | [ ] |

**Test File:** `frontend/e2e/tests/documents/document-actions.spec.ts::ClearFeedback`

---

### AC-6.8.6: Status Badge Updates
**Criterion:** Document status badges reflect current state (completed, processing, failed, archived).

| # | Scenario | Status |
|---|----------|--------|
| 8.6.1 | Given completed document, Then shows green "Completed" badge | [ ] |
| 8.6.2 | Given processing document, Then shows yellow "Processing" badge | [ ] |
| 8.6.3 | Given failed document, Then shows red "Failed" badge | [ ] |
| 8.6.4 | Given archived document (in archive view), Then shows gray "Archived" badge | [ ] |

**Test File:** `frontend/e2e/tests/documents/document-actions.spec.ts::StatusBadgeUpdates`

---

### AC-6.8.7: Bulk Archive Selection
**Criterion:** Multiple document selection enables "Archive Selected" bulk action.

| # | Scenario | Status |
|---|----------|--------|
| 8.7.1 | Given 2+ completed documents selected, Then "Archive Selected" button appears | [ ] |
| 8.7.2 | Given "Archive Selected" clicked, Then confirmation shows count | [ ] |
| 8.7.3 | Given bulk archive confirmed, Then all selected documents archived | [ ] |
| 8.7.4 | Given partial failure in bulk, Then shows which succeeded/failed | [ ] |

**Test File:** `frontend/e2e/tests/documents/document-actions.spec.ts::BulkArchiveSelection`

---

### AC-6.8.8: Keyboard Accessibility
**Criterion:** Archive and Clear actions accessible via keyboard (Enter to confirm, Escape to cancel).

| # | Scenario | Status |
|---|----------|--------|
| 8.8.1 | Given confirmation dialog, When Enter pressed, Then action executes | [ ] |
| 8.8.2 | Given confirmation dialog, When Escape pressed, Then dialog closes | [ ] |
| 8.8.3 | Given menu open, When arrow keys used, Then navigate options | [ ] |
| 8.8.4 | Given menu option focused, When Enter pressed, Then option selected | [ ] |

**Test File:** `frontend/e2e/tests/documents/document-actions.spec.ts::KeyboardAccessibility`

---

## Story 6-9: Duplicate Upload & Replace UI (2 SP)

### AC-6.9.1: Duplicate Detection Modal
**Criterion:** When upload detects duplicate (409), show modal with existing document info and action options.

| # | Scenario | Status |
|---|----------|--------|
| 9.1.1 | Given upload returns 409, Then duplicate modal appears | [ ] |
| 9.1.2 | Given modal, Then shows existing document name | [ ] |
| 9.1.3 | Given modal, Then shows existing document upload date | [ ] |
| 9.1.4 | Given modal, Then shows "Replace", "Keep Both", "Cancel" options | [ ] |

**Test File:** `frontend/e2e/tests/documents/duplicate-upload.spec.ts::DuplicateDetectionModal`

---

### AC-6.9.2: Replace Option
**Criterion:** "Replace" option triggers replace API and shows processing status.

| # | Scenario | Status |
|---|----------|--------|
| 9.2.1 | Given "Replace" selected, Then replace API called | [ ] |
| 9.2.2 | Given replace in progress, Then modal shows processing indicator | [ ] |
| 9.2.3 | Given replace successful, Then modal closes, success toast shown | [ ] |
| 9.2.4 | Given replace fails, Then error shown in modal | [ ] |

**Test File:** `frontend/e2e/tests/documents/duplicate-upload.spec.ts::ReplaceOption`

---

### AC-6.9.3: Keep Both Option
**Criterion:** "Keep Both" renames new file (appends counter) and proceeds with upload.

| # | Scenario | Status |
|---|----------|--------|
| 9.3.1 | Given "Keep Both" selected, Then file renamed (e.g., "report (1).pdf") | [ ] |
| 9.3.2 | Given renamed file, Then upload proceeds normally | [ ] |
| 9.3.3 | Given multiple duplicates, Then counter increments (report (2).pdf, etc.) | [ ] |

**Test File:** `frontend/e2e/tests/documents/duplicate-upload.spec.ts::KeepBothOption`

---

### AC-6.9.4: Cancel Option
**Criterion:** "Cancel" aborts upload and closes modal with no changes.

| # | Scenario | Status |
|---|----------|--------|
| 9.4.1 | Given "Cancel" clicked, Then modal closes | [ ] |
| 9.4.2 | Given cancel, Then no upload performed | [ ] |
| 9.4.3 | Given cancel, Then existing document unchanged | [ ] |

**Test File:** `frontend/e2e/tests/documents/duplicate-upload.spec.ts::CancelOption`

---

### AC-6.9.5: Auto-Clear Notification
**Criterion:** When duplicate of failed document triggers auto-clear, show notification explaining the automatic action.

| # | Scenario | Status |
|---|----------|--------|
| 9.5.1 | Given duplicate of failed doc, When uploaded, Then auto-clear notification shown | [ ] |
| 9.5.2 | Given notification, Then explains failed doc was auto-cleared | [ ] |
| 9.5.3 | Given auto-clear, Then upload proceeds automatically | [ ] |

**Test File:** `frontend/e2e/tests/documents/duplicate-upload.spec.ts::AutoClearNotification`

---

### AC-6.9.6: Replace from Document Actions
**Criterion:** Document menu includes "Replace" option that opens file picker for replacement.

| # | Scenario | Status |
|---|----------|--------|
| 9.6.1 | Given completed document menu, Then "Replace" option visible | [ ] |
| 9.6.2 | Given "Replace" clicked, Then file picker opens | [ ] |
| 9.6.3 | Given file selected, Then replace confirmation modal appears | [ ] |
| 9.6.4 | Given replace confirmed, Then document enters processing state | [ ] |

**Test File:** `frontend/e2e/tests/documents/duplicate-upload.spec.ts::ReplaceFromDocumentActions`

---

### AC-6.9.7: Replace Progress Indicator
**Criterion:** During document replacement, show progress indicator in document list.

| # | Scenario | Status |
|---|----------|--------|
| 9.7.1 | Given replace in progress, Then document row shows progress bar | [ ] |
| 9.7.2 | Given replace in progress, Then status shows "Replacing..." | [ ] |
| 9.7.3 | Given replace complete, Then progress bar removed, status updated | [ ] |
| 9.7.4 | Given replace fails, Then error indicator shown on row | [ ] |

**Test File:** `frontend/e2e/tests/documents/duplicate-upload.spec.ts::ReplaceProgressIndicator`

---

## Summary

### Coverage by Story

| Story | Description | ACs | Scenarios | Status |
|-------|-------------|-----|-----------|--------|
| 6-1 | Archive Document Backend | 6 | 20 | [ ] |
| 6-2 | Restore Document Backend | 6 | 14 | [ ] |
| 6-3 | Purge Document Backend | 6 | 16 | [ ] |
| 6-4 | Clear Failed Document Backend | 5 | 13 | [ ] |
| 6-5 | Duplicate Detection & Auto-Clear | 5 | 13 | [ ] |
| 6-6 | Replace Document Backend | 7 | 20 | [ ] |
| 6-7 | Archive Management UI | 10 | 27 | [ ] |
| 6-8 | Document List Actions UI | 8 | 21 | [ ] |
| 6-9 | Duplicate Upload & Replace UI | 7 | 18 | [ ] |
| **Total** | | **60** | **162** | |

### Risk Areas (from Test Design)

| Risk ID | Description | Priority | Mitigation Status |
|---------|-------------|----------|-------------------|
| R6.1 | Multi-layer cleanup failure (Qdrant/MinIO/Postgres) | HIGH (8) | [ ] |
| R6.2 | Race condition during concurrent archive/restore | HIGH (7) | [ ] |
| R6.3 | Orphaned vectors after failed purge | HIGH (8) | [ ] |
| R6.4 | Data loss from accidental purge | HIGH (9) | [ ] |
| R6.5 | Replace operation partial failure | HIGH (7) | [ ] |

### Test Execution Notes

1. **Backend Integration Tests**: Run with `pytest backend/tests/integration/test_archive_api.py -v`
2. **Frontend E2E Tests**: Run with `npx playwright test e2e/tests/archive/ e2e/tests/documents/`
3. **Performance Tests**: Duplicate check timing requires 10K document dataset

---

*Generated by TEA (Test Engineering Architect) Agent*
