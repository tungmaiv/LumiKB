# Epic 2: Knowledge Base & Document Management

**Goal:** Enable users to create Knowledge Bases and upload documents that are processed, chunked, and indexed for semantic search.

**User Value:** "I can create my own Knowledge Base, upload my documents, and see them processed and ready for search."

**FRs Covered:** FR9-14, FR15-23, FR23a-c, FR53

**Technical Foundation:**
- MinIO for document storage
- Celery workers for async processing
- unstructured for document parsing
- LangChain for chunking
- Qdrant for vector storage
- Outbox pattern for consistency

---

## Story 2.1: Knowledge Base CRUD Backend

As an **administrator**,
I want **to create and manage Knowledge Bases**,
So that **I can organize documents into logical collections**.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I call POST /api/v1/knowledge-bases with name and description
**Then** a new Knowledge Base is created
**And** a corresponding Qdrant collection is created (kb_{id})
**And** I am assigned ADMIN permission on the KB
**And** the action is logged to audit.events

**Given** a KB exists
**When** I call GET /api/v1/knowledge-bases/{id}
**Then** I receive KB details including document count and status

**Given** I have ADMIN permission on a KB
**When** I call PATCH /api/v1/knowledge-bases/{id}
**Then** the KB name/description is updated

**Given** I have ADMIN permission on a KB
**When** I call DELETE /api/v1/knowledge-bases/{id}
**Then** the KB status is set to ARCHIVED
**And** it no longer appears in normal listings
**And** the Qdrant collection is deleted

**Prerequisites:** Story 1.2, Story 1.7

**Technical Notes:**
- Soft delete (ARCHIVED status) for audit trail
- Collection naming: `kb_{uuid}`
- Reference: FR9, FR10, FR11, FR14

---

## Story 2.2: Knowledge Base Permissions Backend

As an **administrator**,
I want **to assign users to Knowledge Bases with specific permissions**,
So that **I can control who can read, write, or manage each KB**.

**Acceptance Criteria:**

**Given** I have ADMIN permission on a KB
**When** I call POST /api/v1/knowledge-bases/{id}/permissions
**Then** the specified user is granted the specified permission level
**And** the action is logged to audit.events

**Given** a user has READ permission on a KB
**When** they try to upload a document
**Then** they receive 403 Forbidden

**Given** a user has WRITE permission on a KB
**When** they try to delete the KB
**Then** they receive 403 Forbidden

**Given** a user has no permission on a KB
**When** they try to access it
**Then** they receive 404 Not Found (not 403, to avoid leaking existence)

**And** permission levels are: READ, WRITE, ADMIN
**And** ADMIN includes WRITE includes READ

**Prerequisites:** Story 2.1

**Technical Notes:**
- Permission check middleware on all KB endpoints
- Use 404 for unauthorized access (security through obscurity)
- Reference: FR6, FR7

---

## Story 2.3: Knowledge Base List and Selection Frontend

As a **user**,
I want **to see and switch between Knowledge Bases I have access to**,
So that **I can work with different document collections**.

**Acceptance Criteria:**

**Given** I am logged in
**When** I view the sidebar
**Then** I see a list of Knowledge Bases I have access to
**And** each shows name, document count, and my permission level icon

**Given** multiple KBs exist
**When** I click on a different KB
**Then** it becomes the active KB
**And** the center panel updates to show that KB's context

**Given** I have ADMIN permission
**When** I click "Create Knowledge Base"
**Then** a modal appears with name and description fields
**And** I can create a new KB

**And** the sidebar shows my permission level for each KB:
- 👁 READ
- ✏️ WRITE
- ⚙️ ADMIN

**Prerequisites:** Story 2.1, Story 1.9

**Technical Notes:**
- Use KBSelectorItem component from UX spec
- Store active KB in Zustand
- Reference: FR12, FR12a, FR13

---

## Story 2.4: Document Upload API and Storage

As a **user with WRITE permission**,
I want **to upload documents to a Knowledge Base**,
So that **they can be processed and made searchable**.

**Acceptance Criteria:**

**Given** I have WRITE permission on a KB
**When** I call POST /api/v1/knowledge-bases/{id}/documents with a file
**Then** the file is uploaded to MinIO (bucket: kb-{id})
**And** a document record is created with status PENDING
**And** an outbox event is created for processing
**And** I receive 202 Accepted with document ID

**And** supported formats are: PDF, DOCX, MD (FR16)
**And** maximum file size is 50MB
**And** the upload is logged to audit.events (FR53)

**Given** I upload an unsupported file type
**When** validation runs
**Then** I receive 400 Bad Request with clear error message

**Prerequisites:** Story 2.2, Story 1.3 (MinIO)

**Technical Notes:**
- Use MinIO Python client
- Chunked upload for large files
- File stored as: `{kb_id}/{doc_id}/{original_filename}`
- Reference: FR15, FR16, FR53

---

## Story 2.5: Document Processing Worker - Parsing

As a **system**,
I want **to parse uploaded documents and extract text**,
So that **content can be chunked and embedded**.

**Acceptance Criteria:**

**Given** a document is in PENDING status
**When** the Celery worker picks up the processing event
**Then** the document status is updated to PROCESSING
**And** the file is downloaded from MinIO
**And** text is extracted using unstructured library

**Given** a PDF document
**When** parsing completes
**Then** text content and page numbers are extracted

**Given** a DOCX document
**When** parsing completes
**Then** text content and section headers are extracted

**Given** a Markdown document
**When** parsing completes
**Then** text content and heading structure are extracted

**Given** parsing fails
**When** max retries (3) are exhausted
**Then** document status is set to FAILED
**And** last_error contains the failure reason

**Prerequisites:** Story 2.4

**Technical Notes:**
- Use unstructured library with appropriate loaders
- Extract metadata: page_number, section_header where available
- Store parsed content temporarily for chunking step
- Reference: FR17

---

## Story 2.6: Document Processing Worker - Chunking and Embedding

As a **system**,
I want **to chunk parsed documents and generate embeddings**,
So that **content can be searched semantically**.

**Acceptance Criteria:**

**Given** a document has been parsed successfully
**When** the chunking step runs
**Then** text is split into semantic chunks (target: 500 tokens, overlap: 50)
**And** each chunk retains metadata (document_id, page, section, char_start, char_end)

**Given** chunks are created
**When** the embedding step runs
**Then** embeddings are generated via LiteLLM
**And** vectors are stored in Qdrant collection (kb_{kb_id})

**And** each Qdrant point includes payload:
- document_id
- document_name
- page_number (if available)
- section_header (if available)
- chunk_text
- char_start, char_end

**Given** all steps complete successfully
**When** the worker finishes
**Then** document status is set to READY
**And** chunk_count is updated on the document record

**Prerequisites:** Story 2.5

**Technical Notes:**
- Use LangChain RecursiveCharacterTextSplitter
- Embedding model configured via LiteLLM (default: text-embedding-ada-002)
- Rich metadata is CRITICAL for citation system
- Reference: FR17, FR43, FR44

---

## Story 2.7: Document Processing Status and Notifications

As a **user**,
I want **to see the status of my uploaded documents**,
So that **I know when they're ready for search**.

**Acceptance Criteria:**

**Given** I uploaded a document
**When** I view the KB document list
**Then** I see the document with its current status:
- PENDING: "Queued for processing"
- PROCESSING: "Processing..." with spinner
- READY: "Ready" with green checkmark
- FAILED: "Failed" with error icon and retry option

**Given** a document finishes processing
**When** status changes to READY or FAILED
**Then** a toast notification appears (if user is on the page)

**Given** a document is READY
**When** I view it in the list
**Then** I see chunk count (e.g., "47 chunks indexed")

**Prerequisites:** Story 2.6, Story 2.3

**Technical Notes:**
- Poll for status updates every 5 seconds while PROCESSING
- Use toast component from shadcn/ui
- Reference: FR18, FR19

---

## Story 2.8: Document List and Metadata View

As a **user**,
I want **to view all documents in a Knowledge Base**,
So that **I can see what content is available**.

**Acceptance Criteria:**

**Given** I have access to a KB
**When** I view the KB detail page
**Then** I see a list of all documents with:
- Document name
- Upload date (relative: "2 hours ago")
- File size
- Uploader name
- Status badge
- Chunk count (if READY)

**And** the list is paginated (20 per page)
**And** I can sort by name, date, or size

**Given** I click on a document
**When** the detail view opens
**Then** I see full metadata including:
- Original filename
- MIME type
- Processing duration
- Last error (if FAILED)

**Prerequisites:** Story 2.7

**Technical Notes:**
- Use date-fns formatDistanceToNow for relative dates
- Reference: FR20, FR21

---

## Story 2.9: Document Upload Frontend

As a **user with WRITE permission**,
I want **to upload documents via drag-and-drop or file picker**,
So that **I can easily add content to a Knowledge Base**.

**Acceptance Criteria:**

**Given** I have WRITE permission on the active KB
**When** I drag a file onto the upload zone
**Then** the zone highlights to indicate drop target
**And** releasing the file starts the upload

**Given** I click the upload zone
**When** the file picker opens
**Then** I can select one or more files
**And** only supported formats are selectable

**Given** upload is in progress
**When** I view the upload zone
**Then** I see a progress bar for each file
**And** I can cancel pending uploads

**Given** upload completes
**When** the response returns
**Then** the document appears in the list with PENDING status
**And** I see a success toast

**Prerequisites:** Story 2.4, Story 2.8

**Technical Notes:**
- Use react-dropzone for drag-and-drop
- Chunked upload for files > 5MB
- Reference: FR15, FR18

---

## Story 2.10: Document Deletion

As a **user with WRITE permission**,
I want **to delete documents from a Knowledge Base**,
So that **I can remove outdated or incorrect content**.

**Acceptance Criteria:**

**Given** I have WRITE permission on a KB
**When** I click delete on a document
**Then** a confirmation dialog appears

**Given** I confirm deletion
**When** the delete request completes
**Then** the document status is set to ARCHIVED
**And** an outbox event is created for cleanup
**And** the action is logged to audit.events

**Given** a document is deleted
**When** the cleanup worker runs
**Then** vectors are removed from Qdrant
**And** file is removed from MinIO
**And** document no longer appears in listings or search results

**Prerequisites:** Story 2.6, Story 2.8

**Technical Notes:**
- Soft delete first (status = ARCHIVED), then async cleanup
- Outbox ensures cleanup completes even if initial request fails
- Reference: FR22, FR23

---

## Story 2.11: Outbox Processing and Reconciliation

As a **system**,
I want **reliable cross-service operations via the outbox pattern**,
So that **document state remains consistent across PostgreSQL, MinIO, and Qdrant**.

**Acceptance Criteria:**

**Given** events exist in the outbox table
**When** the outbox worker runs (every 10 seconds)
**Then** unprocessed events are picked up and executed
**And** processed_at is set on successful completion
**And** attempts is incremented on failure

**Given** an event fails repeatedly
**When** attempts reaches 5
**Then** the event is marked as failed
**And** an alert is logged

**Given** the reconciliation job runs (hourly)
**When** it detects inconsistencies:
- Documents in READY status without vectors
- Vectors without corresponding document records
- Files in MinIO without document records
**Then** it logs the inconsistency and creates correction events

**Prerequisites:** Story 2.6

**Technical Notes:**
- Use Celery Beat for scheduled jobs
- Reconciliation is defensive - logs and alerts, doesn't auto-fix
- Reference: [architecture.md](../architecture.md) Transactional Outbox section

---

## Story 2.12: Document Re-upload and Version Awareness

As a **user with WRITE permission**,
I want **to re-upload an updated version of a document**,
So that **the Knowledge Base stays current**.

**Acceptance Criteria:**

**Given** a document exists in the KB
**When** I upload a file with the same name
**Then** I am prompted: "Replace existing document?"

**Given** I confirm replacement
**When** the upload completes
**Then** the old vectors are removed from Qdrant
**And** the new file replaces the old in MinIO
**And** the document is reprocessed
**And** updated_at timestamp is set

**Given** the replacement is in progress
**When** someone searches
**Then** search uses the old vectors until new processing completes
**And** then atomically switches to new vectors

**Prerequisites:** Story 2.9, Story 2.6

**Technical Notes:**
- Atomic switch: process new vectors, then delete old in single operation
- Consider using versioned point IDs in Qdrant
- Reference: FR23a, FR23b, FR23c

---

## Summary

Epic 2 establishes the document management infrastructure for LumiKB:

| Story | Points | Key Deliverable |
|-------|--------|-----------------|
| 2.1 | - | Knowledge Base CRUD backend |
| 2.2 | - | KB permissions backend |
| 2.3 | - | KB list and selection frontend |
| 2.4 | - | Document upload API and storage |
| 2.5 | - | Document parsing worker |
| 2.6 | - | Chunking and embedding worker |
| 2.7 | - | Processing status and notifications |
| 2.8 | - | Document list and metadata view |
| 2.9 | - | Document upload frontend |
| 2.10 | - | Document deletion |
| 2.11 | - | Outbox processing and reconciliation |
| 2.12 | - | Document re-upload and versioning |

**Total Stories:** 12

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._
