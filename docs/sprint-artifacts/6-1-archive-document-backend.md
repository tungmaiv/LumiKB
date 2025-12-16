# Story 6-1: Archive Document Backend

## Story Information
- **Epic:** 6 - Document Lifecycle Management
- **Story ID:** 6-1
- **Story Points:** 3
- **Priority:** HIGH
- **Status:** ready-for-dev

## User Story
**As a** KB owner or admin
**I want** to archive completed documents
**So that** they are removed from active search results while remaining recoverable

## Context
Document archiving is a soft-delete mechanism that removes documents from active search results without permanently deleting them. Archived documents can later be restored or permanently purged. This story implements the backend API and storage layer operations for archiving documents.

## Acceptance Criteria

### AC-6.1.1: Archive endpoint exists
**Given** I am authenticated as KB owner or admin
**When** I call POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive
**Then** I receive 200 OK
**And** the document status changes from "completed" to "archived"
**And** an audit log entry is created with action "document_archived"

### AC-6.1.2: Only completed documents can be archived
**Given** a document has status "pending", "processing", or "failed"
**When** I attempt to archive it
**Then** I receive 400 Bad Request with message "Only completed documents can be archived"

### AC-6.1.3: Already archived document returns 400
**Given** a document is already archived
**When** I attempt to archive it again
**Then** I receive 400 Bad Request with message "Document is already archived"

### AC-6.1.4: Qdrant vectors marked as archived
**Given** I archive a document
**When** the operation completes
**Then** all Qdrant vectors for this document have payload status: "archived"
**And** vectors are not deleted (soft-filter approach)

### AC-6.1.5: Permission check enforced
**Given** I am not KB owner or admin
**When** I attempt to archive a document
**Then** I receive 403 Forbidden

### AC-6.1.6: Archived documents excluded from search
**Given** a document is archived
**When** I perform semantic search on the KB
**Then** the archived document's chunks do not appear in results

## Technical Notes

### Database Changes
```sql
-- Add archived_at timestamp to documents table
ALTER TABLE documents ADD COLUMN archived_at TIMESTAMP NULL;

-- Index for efficient archive queries
CREATE INDEX idx_documents_archived_at ON documents(archived_at) WHERE archived_at IS NOT NULL;
```

### Status Enum Extension
```python
class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"  # New status
```

### API Contract
```
POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive
Authorization: Bearer {token}

Response 200:
{
  "id": "uuid",
  "name": "document.pdf",
  "status": "archived",
  "archived_at": "2025-12-07T10:00:00Z"
}

Response 400: { "detail": "Only completed documents can be archived" }
Response 403: { "detail": "Permission denied" }
Response 404: { "detail": "Document not found" }
```

### Qdrant Operations
```python
# Update payload to mark as archived (vectors NOT deleted)
await qdrant_client.set_payload(
    collection_name=f"kb_{kb_id}",
    payload={"status": "archived"},
    points=Filter(
        must=[FieldCondition(key="doc_id", match=MatchValue(value=str(doc_id)))]
    )
)
```

### Search Filter Update
```python
# Add to search filter to exclude archived documents
filter_conditions.append(
    FieldCondition(
        key="status",
        match=MatchValue(value="completed")  # Only search completed docs
    )
)
```

## Dependencies
- Epic 2: Document Management (completed)
- Epic 3: Search (completed)
- Epic 1: Audit logging infrastructure (completed)

## Test Cases

### Unit Tests
1. archive_document succeeds for completed document
2. archive_document raises error for non-completed document
3. archive_document raises error for already archived document
4. archive_document updates Qdrant payload
5. archive_document creates audit log entry

### Integration Tests
1. POST /archive returns 200 for KB owner
2. POST /archive returns 200 for admin user
3. POST /archive returns 403 for non-owner/non-admin
4. POST /archive returns 400 for non-completed document
5. POST /archive returns 400 for already archived document
6. Archived document excluded from semantic search

## Implementation Notes
1. Create Alembic migration for archived_at column and status enum update
2. Ensure Qdrant payload includes "status" field during document processing
3. Update search filter to only include status="completed" documents
4. Return clear error messages for state validation failures
5. Reuse existing KB permission checking patterns from kb_service

## Definition of Done
- [ ] Alembic migration created and tested
- [ ] DocumentService.archive_document() method implemented
- [ ] POST /archive endpoint implemented
- [ ] Qdrant payload update implemented
- [ ] Search filter updated to exclude archived
- [ ] Permission checks enforced
- [ ] Audit logging integrated
- [ ] Unit tests passing (5+)
- [ ] Integration tests passing (6+)
- [ ] Code review approved
