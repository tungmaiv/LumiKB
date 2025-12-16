# Epic 6: Document Lifecycle Management

**Goal:** Provide comprehensive document lifecycle management including archive, restore, purge, clear failed, duplicate detection, and replace capabilities.

**User Value:** Users can manage document lifecycle states - archiving completed documents to declutter active views, restoring archived documents when needed, permanently purging documents, clearing failed documents, detecting duplicate uploads, and replacing existing documents with updated versions.

**FRs Covered:** FR59-FR77

**Technical Foundation:**
- Document state machine: pending → processing → completed → archived / failed
- Multi-layer storage operations: PostgreSQL, Qdrant, MinIO, Redis/Celery
- Qdrant soft-filtering via status payload for archived documents
- Transactional operations for replace flow (delete + upload)
- Case-insensitive duplicate name detection within KB scope

---

## Story 6.1: Archive Document Backend

**Description:** As a KB owner or admin, I want to archive completed documents so they are removed from active search results while remaining recoverable.

**Story Points:** 3

**Acceptance Criteria:**

**AC-6.1.1: Archive endpoint exists**
**Given** I am authenticated as KB owner or admin
**When** I call `POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive`
**Then** I receive 200 OK
**And** the document status changes from "completed" to "archived"
**And** an audit log entry is created with action "document_archived"

**AC-6.1.2: Only completed documents can be archived**
**Given** a document has status "pending", "processing", or "failed"
**When** I attempt to archive it
**Then** I receive 400 Bad Request with message "Only completed documents can be archived"

**AC-6.1.3: Already archived document returns 400**
**Given** a document is already archived
**When** I attempt to archive it again
**Then** I receive 400 Bad Request with message "Document is already archived"

**AC-6.1.4: Qdrant vectors marked as archived**
**Given** I archive a document
**When** the operation completes
**Then** all Qdrant vectors for this document have payload `status: "archived"`
**And** vectors are not deleted (soft-filter approach)

**AC-6.1.5: Permission check enforced**
**Given** I am not KB owner or admin
**When** I attempt to archive a document
**Then** I receive 403 Forbidden

**AC-6.1.6: Archived documents excluded from search**
**Given** a document is archived
**When** I perform semantic search on the KB
**Then** the archived document's chunks do not appear in results

**Prerequisites:**
- Existing document model with status field
- Qdrant client with payload update capability

**Technical Notes:**
- Add `archived_at` timestamp field to document model
- Qdrant update operation: `qdrant_client.set_payload(collection, {status: "archived"}, filter)`
- Search filter: `must_not: [{key: "status", match: {value: "archived"}}]`

---

## Story 6.2: Restore Document Backend

**Description:** As a KB owner or admin, I want to restore archived documents back to active status so they reappear in search results.

**Story Points:** 3

**Acceptance Criteria:**

**AC-6.2.1: Restore endpoint exists**
**Given** I am authenticated as KB owner or admin
**When** I call `POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore`
**Then** I receive 200 OK
**And** the document status changes from "archived" to "completed"
**And** an audit log entry is created with action "document_restored"

**AC-6.2.2: Only archived documents can be restored**
**Given** a document has status other than "archived"
**When** I attempt to restore it
**Then** I receive 400 Bad Request with message "Only archived documents can be restored"

**AC-6.2.3: Name collision blocks restore**
**Given** an archived document named "report.pdf"
**And** an active document with the same name exists in the KB
**When** I attempt to restore the archived document
**Then** I receive 409 Conflict with message "Cannot restore: a document with this name already exists"

**AC-6.2.4: Qdrant vectors restored to active**
**Given** I restore a document
**When** the operation completes
**Then** all Qdrant vectors for this document have payload `status: "completed"`
**And** vectors appear in search results

**AC-6.2.5: Permission check enforced**
**Given** I am not KB owner or admin
**When** I attempt to restore a document
**Then** I receive 403 Forbidden

**AC-6.2.6: archived_at timestamp cleared**
**Given** I restore a document
**When** the operation completes
**Then** the `archived_at` field is set to null

**Prerequisites:**
- Story 6-1: Archive Document Backend

**Technical Notes:**
- Case-insensitive name collision check: `SELECT COUNT(*) FROM documents WHERE kb_id=? AND LOWER(name)=LOWER(?) AND status != 'archived' AND id != ?`
- Qdrant payload update to remove archived status

---

## Story 6.3: Purge Document Backend

**Description:** As a KB owner or admin, I want to permanently delete archived documents including all storage artifacts so I can free up storage and comply with data retention policies.

**Story Points:** 5

**Acceptance Criteria:**

**AC-6.3.1: Single purge endpoint exists**
**Given** I am authenticated as KB owner or admin
**When** I call `DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge`
**Then** I receive 200 OK
**And** the document is permanently deleted
**And** an audit log entry is created with action "document_purged"

**AC-6.3.2: Bulk purge endpoint exists**
**Given** I am authenticated as KB owner or admin
**When** I call `POST /api/v1/knowledge-bases/{kb_id}/documents/bulk-purge` with `{"document_ids": [...]}`
**Then** I receive 200 OK with count of purged documents
**And** all specified archived documents are permanently deleted
**And** audit log entries are created for each purged document

**AC-6.3.3: Only archived documents can be purged**
**Given** a document has status other than "archived"
**When** I attempt to purge it
**Then** I receive 400 Bad Request with message "Only archived documents can be purged"

**AC-6.3.4: All storage layers cleaned**
**Given** I purge a document
**When** the operation completes
**Then** the document row is deleted from PostgreSQL
**And** all vectors are deleted from Qdrant collection
**And** the file is deleted from MinIO bucket
**And** any pending Celery tasks are revoked

**AC-6.3.5: Permission check enforced**
**Given** I am not KB owner or admin
**When** I attempt to purge a document
**Then** I receive 403 Forbidden

**AC-6.3.6: Bulk purge skips non-archived with partial success**
**Given** a bulk purge request contains both archived and non-archived document IDs
**When** I execute the bulk purge
**Then** only archived documents are purged
**And** response includes `{"purged": 3, "skipped": 2, "skipped_ids": [...]}`

**Prerequisites:**
- Story 6-1: Archive Document Backend

**Technical Notes:**
- Qdrant delete: `qdrant_client.delete(collection, filter={doc_id: doc_id})`
- MinIO delete: `minio_client.remove_object(bucket, object_name)`
- Celery task revocation: `app.control.revoke(task_id, terminate=True)`
- Use database transaction for atomicity

---

## Story 6.4: Clear Failed Document Backend

**Description:** As a KB owner or admin, I want to clear failed documents so I can remove partial artifacts and retry document uploads cleanly.

**Story Points:** 3

**Acceptance Criteria:**

**AC-6.4.1: Clear failed endpoint exists**
**Given** I am authenticated as KB owner or admin
**When** I call `DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear`
**Then** I receive 200 OK
**And** the failed document and all artifacts are removed
**And** an audit log entry is created with action "document_cleared"

**AC-6.4.2: Only failed documents can be cleared**
**Given** a document has status other than "failed"
**When** I attempt to clear it
**Then** I receive 400 Bad Request with message "Only failed documents can be cleared"

**AC-6.4.3: All partial artifacts cleaned**
**Given** I clear a failed document
**When** the operation completes
**Then** the document row is deleted from PostgreSQL
**And** any partial vectors are deleted from Qdrant
**And** the file is deleted from MinIO (if exists)
**And** any pending/failed Celery tasks are revoked
**And** Redis keys related to the task are cleared

**AC-6.4.4: Permission check enforced**
**Given** I am not KB owner or admin
**When** I attempt to clear a failed document
**Then** I receive 403 Forbidden

**AC-6.4.5: Already processing document cannot be cleared**
**Given** a document has status "processing"
**When** I attempt to clear it
**Then** I receive 400 Bad Request with message "Cannot clear document while processing is in progress"

**Prerequisites:**
- Existing document model with status tracking
- Celery task management capability

**Technical Notes:**
- Query for task_id from document metadata or Celery result backend
- Handle case where some artifacts don't exist (no-op, not error)
- Clear Redis keys: `redis_client.delete(f"celery-task-meta-{task_id}")`

---

## Story 6.5: Duplicate Detection & Auto-Clear Backend

**Description:** As a user uploading documents, I want the system to detect duplicate document names and auto-clear failed documents with the same name so I can re-upload without manual cleanup.

**Story Points:** 5

**Acceptance Criteria:**

**AC-6.5.1: Upload detects duplicate active document**
**Given** I upload a document named "report.pdf" (case-insensitive)
**And** a document with the same name exists with status "completed" or "processing" or "pending"
**When** the upload is processed
**Then** I receive 409 Conflict with response:
```json
{
  "error": "duplicate_document",
  "existing_document_id": "uuid",
  "existing_status": "completed",
  "message": "A document with this name already exists"
}
```

**AC-6.5.2: Upload detects duplicate archived document**
**Given** I upload a document named "report.pdf"
**And** an archived document with the same name exists
**When** the upload is processed
**Then** I receive 409 Conflict with response indicating archived duplicate:
```json
{
  "error": "duplicate_document",
  "existing_document_id": "uuid",
  "existing_status": "archived",
  "message": "An archived document with this name exists"
}
```

**AC-6.5.3: Upload auto-clears failed document**
**Given** I upload a document named "report.pdf"
**And** a failed document with the same name exists
**When** the upload is processed
**Then** the failed document is auto-cleared (artifacts removed)
**And** the new upload proceeds normally
**And** I receive notification in response: `{"auto_cleared_document_id": "uuid", "message": "Previous failed upload was automatically cleared"}`

**AC-6.5.4: Case-insensitive matching**
**Given** a document named "Report.PDF" exists
**When** I upload "report.pdf" or "REPORT.pdf"
**Then** duplicate detection triggers

**AC-6.5.5: Duplicate check scoped to KB**
**Given** a document "report.pdf" exists in KB-A
**When** I upload "report.pdf" to KB-B
**Then** no duplicate is detected
**And** upload proceeds normally

**Prerequisites:**
- Existing document upload endpoint
- Story 6-4: Clear Failed Document Backend (for auto-clear logic)

**Technical Notes:**
- Check query: `SELECT id, status FROM documents WHERE kb_id=? AND LOWER(name)=LOWER(?) LIMIT 1`
- Auto-clear uses same logic as Story 6-4 but triggered automatically
- Audit log: "document_auto_cleared" with reason "duplicate_upload"

---

## Story 6.6: Replace Document Backend

**Description:** As a KB owner or admin, I want to replace an existing document with a new version so I can update content without changing the document's identity in the system.

**Story Points:** 5

**Acceptance Criteria:**

**AC-6.6.1: Replace endpoint exists**
**Given** I am authenticated as KB owner or admin
**And** a document exists (any status except "processing")
**When** I call `POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace` with new file
**Then** I receive 200 OK with new document details
**And** an audit log entry is created with action "document_replaced"

**AC-6.6.2: Replace performs atomic delete-then-upload**
**Given** I replace a document
**When** the operation executes
**Then** the old document's vectors are deleted from Qdrant
**And** the old file is deleted from MinIO
**And** the new file is uploaded to MinIO
**And** document metadata is updated (file_size, content_type, updated_at)
**And** document status is set to "pending" for reprocessing

**AC-6.6.3: Replace preserves document ID and metadata**
**Given** I replace a document
**When** the operation completes
**Then** the document ID remains the same
**And** the document name is updated to new file name
**And** created_at timestamp is preserved
**And** tags and other metadata are preserved

**AC-6.6.4: Cannot replace while processing**
**Given** a document has status "processing"
**When** I attempt to replace it
**Then** I receive 400 Bad Request with message "Cannot replace document while processing is in progress"

**AC-6.6.5: Permission check enforced**
**Given** I am not KB owner or admin
**When** I attempt to replace a document
**Then** I receive 403 Forbidden

**AC-6.6.6: Replace triggers reprocessing**
**Given** I replace a document
**When** the operation completes
**Then** a new Celery task is queued for document processing
**And** the document status shows "pending"

**AC-6.6.7: Replace from upload flow with confirmation**
**Given** duplicate detection returns 409 for an active document
**When** user confirms replacement via `POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace`
**Then** the existing document is replaced with the new upload

**Prerequisites:**
- Story 6-5: Duplicate Detection Backend
- Existing document upload and processing pipeline

**Technical Notes:**
- Two-phase operation: 1) validate & stage new file, 2) delete old + activate new
- Use database transaction to ensure atomicity
- Preserve document UUID for any external references

---

## Story 6.7: Archive Management UI

**Description:** As a user, I want a dedicated archive page to browse, search, filter, restore, and purge archived documents.

**Story Points:** 5

**Acceptance Criteria:**

**AC-6.7.1: Archive page accessible from navigation**
**Given** I am on any page
**When** I click the "Archive" link in navigation (or KB context menu)
**Then** I see the archive management page
**And** URL is `/archive` or `/knowledge-bases/{kb_id}/archive`

**AC-6.7.2: Archive page lists archived documents**
**Given** I am on the archive page
**Then** I see a table of archived documents with columns:
- Document name
- KB name
- Archived date
- Original completion date
- File size
- Actions (Restore, Purge)

**AC-6.7.3: Pagination consistent with document list**
**Given** there are more than 20 archived documents
**Then** I see pagination controls
**And** default page size is 20
**And** I can change page size (10, 20, 50, 100)

**AC-6.7.4: Search archived documents**
**Given** I am on the archive page
**When** I type in the search box
**Then** results filter by document name (case-insensitive)
**And** search is debounced (300ms)

**AC-6.7.5: Filter by KB**
**Given** I am on the archive page
**When** I select a KB from the filter dropdown
**Then** only archived documents from that KB are shown

**AC-6.7.6: Filter by date range**
**Given** I am on the archive page
**When** I select archived date range
**Then** only documents archived within that range are shown

**AC-6.7.7: Restore action with confirmation**
**Given** I click "Restore" on an archived document
**Then** I see a confirmation dialog: "Restore 'filename.pdf' to active documents?"
**When** I confirm
**Then** the document is restored
**And** success toast appears
**And** document disappears from archive list

**AC-6.7.8: Purge action with two-step confirmation**
**Given** I click "Purge" on an archived document
**Then** I see a warning dialog: "Permanently delete 'filename.pdf'? This cannot be undone."
**When** I confirm
**Then** I see a second confirmation: "Type 'DELETE' to confirm permanent deletion"
**When** I type "DELETE" and confirm
**Then** the document is purged
**And** success toast appears

**AC-6.7.9: Bulk purge with selection**
**Given** I select multiple archived documents via checkboxes
**When** I click "Purge Selected"
**Then** I see bulk purge confirmation with count
**And** two-step confirmation applies

**AC-6.7.10: Restore collision shows error**
**Given** I attempt to restore a document
**And** name collision exists
**When** the API returns 409
**Then** I see error toast: "Cannot restore: a document with this name already exists"

**Prerequisites:**
- Story 6-1, 6-2, 6-3: Backend APIs

**Technical Notes:**
- Use same DataTable component as document list
- API: `GET /api/v1/documents/archived?kb_id=&search=&page=&limit=`
- Loading skeleton during fetch
- Error boundary for failed operations

---

## Story 6.8: Document List Archive/Clear Actions UI

**Description:** As a KB owner or admin, I want archive and clear actions in the document list so I can manage document lifecycle without leaving the KB view.

**Story Points:** 3

**Acceptance Criteria:**

**AC-6.8.1: Archive action in document row menu**
**Given** I am viewing documents in a KB
**And** I am KB owner or admin
**And** a document has status "completed"
**When** I click the document row actions menu (⋮)
**Then** I see "Archive" option

**AC-6.8.2: Archive action with confirmation**
**Given** I click "Archive" on a completed document
**Then** I see confirmation: "Archive 'filename.pdf'? It will be removed from search results."
**When** I confirm
**Then** the document status changes to "archived"
**And** success toast appears
**And** document row shows "Archived" badge or is removed from list

**AC-6.8.3: Clear action for failed documents**
**Given** a document has status "failed"
**When** I click the document row actions menu
**Then** I see "Clear" option (not "Archive")

**AC-6.8.4: Clear action with confirmation**
**Given** I click "Clear" on a failed document
**Then** I see confirmation: "Clear failed document 'filename.pdf'? All partial data will be removed."
**When** I confirm
**Then** the document is cleared
**And** success toast appears
**And** document row is removed from list

**AC-6.8.5: Actions hidden for non-owners**
**Given** I am not KB owner or admin
**Then** "Archive" and "Clear" actions are not visible in menu

**AC-6.8.6: Action disabled during processing**
**Given** a document has status "processing"
**Then** no lifecycle actions are available
**And** tooltip explains "Cannot modify while processing"

**AC-6.8.7: Bulk archive selection**
**Given** I select multiple completed documents
**Then** "Archive Selected" button appears in toolbar
**When** I click it
**Then** confirmation shows count of documents to archive

**Prerequisites:**
- Story 6-1, 6-4: Backend APIs
- Existing document list component

**Technical Notes:**
- Extend existing DocumentActionsMenu component
- Check permissions via useKBPermissions hook
- Optimistic UI update with rollback on error

---

## Story 6.9: Duplicate Upload & Replace UI

**Description:** As a user, I want clear feedback when uploading duplicate documents and the ability to replace existing documents through the UI.

**Story Points:** 3

**Acceptance Criteria:**

**AC-6.9.1: Duplicate detection modal appears**
**Given** I upload a document
**And** the API returns 409 duplicate_document
**Then** I see a modal with:
- Document name
- Existing document status (completed/archived)
- Options: "Cancel" / "Replace Existing"

**AC-6.9.2: Replace option for active documents**
**Given** duplicate modal shows for a "completed" document
**When** I click "Replace Existing"
**Then** I see two-step confirmation: "This will delete the existing document and upload the new version. Continue?"
**When** I confirm
**Then** replace API is called
**And** progress indicator shows
**And** success message on completion

**AC-6.9.3: Archived duplicate shows restore suggestion**
**Given** duplicate modal shows for an "archived" document
**Then** I see message: "An archived document with this name exists"
**And** options: "Cancel" / "Restore Existing" / "Replace Archived"

**AC-6.9.4: Auto-clear notification for failed**
**Given** I upload a document
**And** the API auto-cleared a failed document
**Then** I see info toast: "Previous failed upload 'filename.pdf' was automatically cleared"
**And** upload proceeds normally

**AC-6.9.5: Cancel returns to normal state**
**Given** I see duplicate modal
**When** I click "Cancel"
**Then** modal closes
**And** no changes are made
**And** I can retry with a different file

**AC-6.9.6: Replace progress and error handling**
**Given** replace is in progress
**Then** I see progress indicator (spinner)
**And** upload button is disabled
**Given** replace fails
**Then** I see error toast with message
**And** original document is unchanged

**AC-6.9.7: Name collision on restore shows clear message**
**Given** I choose "Restore Existing" for archived duplicate
**And** restore fails due to name collision
**Then** I see error: "Cannot restore: rename the archived document first or delete the conflicting active document"

**Prerequisites:**
- Story 6-5, 6-6: Backend APIs
- Existing document upload component

**Technical Notes:**
- Intercept 409 response in upload mutation
- DuplicateDocumentModal component with state machine
- Use same upload progress component for replace operation

---

## Summary

Epic 6 establishes the document lifecycle management system for LumiKB:

| Story | Points | Key Deliverable |
|-------|--------|-----------------|
| 6.1 | 3 | Archive document backend |
| 6.2 | 3 | Restore document backend |
| 6.3 | 5 | Purge document backend |
| 6.4 | 3 | Clear failed document backend |
| 6.5 | 5 | Duplicate detection & auto-clear backend |
| 6.6 | 5 | Replace document backend |
| 6.7 | 5 | Archive management UI |
| 6.8 | 3 | Document list archive/clear actions UI |
| 6.9 | 3 | Duplicate upload & replace UI |

**Total Stories:** 9
**Total Story Points:** 35

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._
