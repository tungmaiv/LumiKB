# Story 6-3: Purge Document Backend

## Story Information
- **Epic:** 6 - Document Lifecycle Management
- **Story ID:** 6-3
- **Story Points:** 5
- **Priority:** HIGH
- **Status:** ready-for-dev

## User Story
**As a** KB owner or admin
**I want** to permanently delete archived documents
**So that** I can free up storage space and remove documents that are no longer needed

## Context
Purging permanently deletes archived documents from all storage layers (PostgreSQL, Qdrant, MinIO). This is an irreversible operation that requires archived status first. Bulk purge allows efficient cleanup of multiple archived documents.

## Acceptance Criteria

### AC-6.3.1: Purge endpoint exists
**Given** I am authenticated as KB owner or admin
**And** a document is archived
**When** I call DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge
**Then** I receive 200 OK with message "Document permanently deleted"
**And** an audit log entry is created with action "document_purged"

### AC-6.3.2: Only archived documents can be purged
**Given** a document has status other than "archived"
**When** I attempt to purge it
**Then** I receive 400 Bad Request with message "Only archived documents can be purged"

### AC-6.3.3: Multi-layer storage cleanup
**Given** I purge a document
**When** the operation completes
**Then** the document record is deleted from PostgreSQL
**And** all vectors for this document are deleted from Qdrant
**And** the document file is deleted from MinIO

### AC-6.3.4: Permission check enforced
**Given** I am not KB owner or admin
**When** I attempt to purge a document
**Then** I receive 403 Forbidden

### AC-6.3.5: Bulk purge endpoint
**Given** I am authenticated as KB owner or admin
**When** I call POST /api/v1/knowledge-bases/{kb_id}/documents/bulk-purge with array of document IDs
**Then** I receive 200 OK with count of purged and skipped documents
**And** only archived documents are purged
**And** non-archived documents are skipped with their IDs returned

### AC-6.3.6: Graceful handling of missing storage artifacts
**Given** I purge a document
**And** some storage artifacts are already missing (e.g., MinIO file deleted manually)
**When** the operation executes
**Then** the operation still completes successfully
**And** existing artifacts are cleaned up

## Technical Notes

### API Contracts
```
DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge
Authorization: Bearer {token}

Response 200: { "message": "Document permanently deleted" }
Response 400: { "detail": "Only archived documents can be purged" }
Response 403: { "detail": "Permission denied" }
Response 404: { "detail": "Document not found" }
```

```
POST /api/v1/knowledge-bases/{kb_id}/documents/bulk-purge
Authorization: Bearer {token}
Content-Type: application/json

{
  "document_ids": ["uuid1", "uuid2", "uuid3"]
}

Response 200:
{
  "purged": 2,
  "skipped": 1,
  "skipped_ids": ["uuid3"],
  "message": "2 documents purged, 1 skipped (not archived)"
}
```

### Multi-Layer Cleanup Order
```python
async def purge_document(doc_id: UUID, kb_id: UUID):
    # 1. Delete from Qdrant (vectors)
    try:
        await qdrant_client.delete(
            collection_name=f"kb_{kb_id}",
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=str(doc_id)))]
                )
            )
        )
    except Exception as e:
        logger.warning(f"Qdrant cleanup failed (may be already deleted): {e}")

    # 2. Delete from MinIO (file)
    try:
        await minio_client.remove_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=f"{kb_id}/{doc_id}/{document.name}"
        )
    except Exception as e:
        logger.warning(f"MinIO cleanup failed (may be already deleted): {e}")

    # 3. Delete from PostgreSQL (record)
    await db.delete(document)
    await db.commit()

    # 4. Create audit log
    await audit_service.log_event(
        action="document_purged",
        resource_type="document",
        resource_id=str(doc_id),
        details={"kb_id": str(kb_id), "doc_name": document.name}
    )
```

### Qdrant Delete Operation
```python
await qdrant_client.delete(
    collection_name=f"kb_{kb_id}",
    points_selector=FilterSelector(
        filter=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=str(doc_id)))]
        )
    )
)
```

## Dependencies
- Story 6-1: Archive Document Backend (provides archived status requirement)

## Test Cases

### Unit Tests
1. purge_document succeeds for archived document
2. purge_document raises error for non-archived document
3. purge_document deletes from all storage layers
4. purge_document handles missing Qdrant vectors gracefully
5. purge_document handles missing MinIO file gracefully
6. purge_document creates audit log entry
7. bulk_purge processes multiple documents
8. bulk_purge skips non-archived documents

### Integration Tests
1. DELETE /purge returns 200 for KB owner
2. DELETE /purge returns 200 for admin user
3. DELETE /purge returns 403 for non-owner/non-admin
4. DELETE /purge returns 400 for non-archived document
5. POST /bulk-purge returns correct counts
6. Purged document not found in any storage layer

## Definition of Done
- [ ] DocumentService.purge_document() method implemented
- [ ] DELETE /purge endpoint implemented
- [ ] POST /bulk-purge endpoint implemented
- [ ] Qdrant vector deletion implemented
- [ ] MinIO file deletion implemented
- [ ] PostgreSQL record deletion implemented
- [ ] Graceful error handling for missing artifacts
- [ ] Permission checks enforced
- [ ] Audit logging integrated
- [ ] Unit tests passing (8+)
- [ ] Integration tests passing (6+)
- [ ] Code review approved
