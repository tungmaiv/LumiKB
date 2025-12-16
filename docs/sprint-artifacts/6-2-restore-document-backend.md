# Story 6-2: Restore Document Backend

## Story Information
- **Epic:** 6 - Document Lifecycle Management
- **Story ID:** 6-2
- **Story Points:** 3
- **Priority:** HIGH
- **Status:** ready-for-dev

## User Story
**As a** KB owner or admin
**I want** to restore archived documents back to active status
**So that** they appear in search results again and are fully accessible

## Context
Document restoration reverses the archive operation, making documents searchable again. This story implements the backend API including name collision detection to prevent restoring a document when another document with the same name already exists in active state.

## Acceptance Criteria

### AC-6.2.1: Restore endpoint exists
**Given** I am authenticated as KB owner or admin
**And** a document is archived
**When** I call POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore
**Then** I receive 200 OK
**And** the document status changes from "archived" to "completed"
**And** archived_at is set to null
**And** an audit log entry is created with action "document_restored"

### AC-6.2.2: Only archived documents can be restored
**Given** a document has status other than "archived"
**When** I attempt to restore it
**Then** I receive 400 Bad Request with message "Only archived documents can be restored"

### AC-6.2.3: Name collision detection
**Given** I attempt to restore an archived document
**And** a document with the same name already exists in the KB (status: completed, pending, or processing)
**When** I call the restore endpoint
**Then** I receive 409 Conflict with message "Cannot restore: a document with this name already exists"

### AC-6.2.4: Qdrant vectors marked as completed
**Given** I restore a document
**When** the operation completes
**Then** all Qdrant vectors for this document have payload status: "completed"

### AC-6.2.5: Permission check enforced
**Given** I am not KB owner or admin
**When** I attempt to restore a document
**Then** I receive 403 Forbidden

### AC-6.2.6: Restored documents appear in search
**Given** a document is restored
**When** I perform semantic search on the KB
**Then** the restored document's chunks appear in results (if relevant)

## Technical Notes

### API Contract
```
POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore
Authorization: Bearer {token}

Response 200:
{
  "id": "uuid",
  "name": "document.pdf",
  "status": "completed",
  "archived_at": null
}

Response 400: { "detail": "Only archived documents can be restored" }
Response 403: { "detail": "Permission denied" }
Response 409: { "detail": "Cannot restore: a document with this name already exists" }
```

### Name Collision Check
```python
# Check for existing document with same name (case-insensitive)
existing = await db.execute(
    select(Document).where(
        Document.knowledge_base_id == kb_id,
        func.lower(Document.name) == func.lower(document.name),
        Document.id != document.id,
        Document.status.in_([DocumentStatus.COMPLETED, DocumentStatus.PENDING, DocumentStatus.PROCESSING])
    )
)
if existing.scalar_one_or_none():
    raise HTTPException(status_code=409, detail="Cannot restore: a document with this name already exists")
```

### Qdrant Operations
```python
# Update payload to mark as completed
await qdrant_client.set_payload(
    collection_name=f"kb_{kb_id}",
    payload={"status": "completed"},
    points=Filter(
        must=[FieldCondition(key="doc_id", match=MatchValue(value=str(doc_id)))]
    )
)
```

## Dependencies
- Story 6-1: Archive Document Backend (provides archived status)

## Test Cases

### Unit Tests
1. restore_document succeeds for archived document
2. restore_document raises error for non-archived document
3. restore_document detects name collision (case-insensitive)
4. restore_document updates Qdrant payload
5. restore_document creates audit log entry
6. restore_document clears archived_at timestamp

### Integration Tests
1. POST /restore returns 200 for KB owner
2. POST /restore returns 200 for admin user
3. POST /restore returns 403 for non-owner/non-admin
4. POST /restore returns 400 for non-archived document
5. POST /restore returns 409 for name collision
6. Restored document appears in semantic search

## Definition of Done
- [ ] DocumentService.restore_document() method implemented
- [ ] POST /restore endpoint implemented
- [ ] Name collision detection implemented (case-insensitive)
- [ ] Qdrant payload update implemented
- [ ] Permission checks enforced
- [ ] Audit logging integrated
- [ ] Unit tests passing (6+)
- [ ] Integration tests passing (6+)
- [ ] Code review approved
