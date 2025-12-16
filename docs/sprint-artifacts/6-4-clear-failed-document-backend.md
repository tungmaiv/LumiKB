# Story 6-4: Clear Failed Document Backend

## Story Information
- **Epic:** 6 - Document Lifecycle Management
- **Story ID:** 6-4
- **Story Points:** 3
- **Priority:** HIGH
- **Status:** ready-for-dev

## User Story
**As a** KB owner or admin
**I want** to clear failed documents from the system
**So that** I can remove partial artifacts from failed processing attempts and retry uploads

## Context
When document processing fails, partial artifacts may remain in storage (MinIO file, partial Qdrant vectors, PostgreSQL record). This story provides a clean way to remove these artifacts, allowing users to retry the upload without conflicts.

## Acceptance Criteria

### AC-6.4.1: Clear endpoint exists
**Given** I am authenticated as KB owner or admin
**And** a document has status "failed"
**When** I call DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear
**Then** I receive 200 OK with message "Failed document cleared"
**And** an audit log entry is created with action "document_cleared"

### AC-6.4.2: Only failed documents can be cleared
**Given** a document has status other than "failed"
**When** I attempt to clear it
**Then** I receive 400 Bad Request with message "Only failed documents can be cleared"

### AC-6.4.3: All partial artifacts removed
**Given** I clear a failed document
**When** the operation completes
**Then** the document record is deleted from PostgreSQL
**And** any partial vectors are deleted from Qdrant
**And** the uploaded file is deleted from MinIO
**And** any pending Celery tasks are revoked

### AC-6.4.4: Permission check enforced
**Given** I am not KB owner or admin
**When** I attempt to clear a document
**Then** I receive 403 Forbidden

### AC-6.4.5: Graceful handling of missing artifacts
**Given** I clear a failed document
**And** some artifacts were never created (e.g., processing failed before embedding)
**When** the operation executes
**Then** the operation still completes successfully
**And** existing artifacts are cleaned up

## Technical Notes

### API Contract
```
DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear
Authorization: Bearer {token}

Response 200: { "message": "Failed document cleared" }
Response 400: { "detail": "Only failed documents can be cleared" }
Response 403: { "detail": "Permission denied" }
Response 404: { "detail": "Document not found" }
```

### Cleanup Implementation
```python
async def clear_failed_document(doc_id: UUID, kb_id: UUID):
    document = await get_document(doc_id)

    if document.status != DocumentStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed documents can be cleared")

    # 1. Revoke pending Celery tasks
    if document.task_id:
        try:
            app.control.revoke(document.task_id, terminate=True)
            result = AsyncResult(document.task_id, app=app)
            result.forget()
        except Exception as e:
            logger.warning(f"Task revocation failed: {e}")

    # 2. Delete partial vectors from Qdrant (may not exist)
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
        logger.warning(f"Qdrant cleanup failed (may not exist): {e}")

    # 3. Delete file from MinIO (may not exist)
    try:
        await minio_client.remove_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=f"{kb_id}/{doc_id}/{document.name}"
        )
    except Exception as e:
        logger.warning(f"MinIO cleanup failed (may not exist): {e}")

    # 4. Delete PostgreSQL record
    await db.delete(document)
    await db.commit()

    # 5. Audit log
    await audit_service.log_event(
        action="document_cleared",
        resource_type="document",
        resource_id=str(doc_id),
        details={"kb_id": str(kb_id), "doc_name": document.name, "reason": "manual_clear"}
    )
```

### Celery Task Revocation
```python
from celery.result import AsyncResult

def revoke_document_tasks(task_id: str):
    if task_id:
        app.control.revoke(task_id, terminate=True)
        result = AsyncResult(task_id, app=app)
        result.forget()
```

## Dependencies
- Epic 2: Document Management (completed) - provides document processing infrastructure

## Test Cases

### Unit Tests
1. clear_document succeeds for failed document
2. clear_document raises error for non-failed document
3. clear_document handles missing Qdrant vectors gracefully
4. clear_document handles missing MinIO file gracefully
5. clear_document revokes Celery tasks
6. clear_document creates audit log entry

### Integration Tests
1. DELETE /clear returns 200 for KB owner
2. DELETE /clear returns 200 for admin user
3. DELETE /clear returns 403 for non-owner/non-admin
4. DELETE /clear returns 400 for non-failed document
5. Cleared document not found after operation

## Definition of Done
- [ ] DocumentService.clear_failed_document() method implemented
- [ ] DELETE /clear endpoint implemented
- [ ] Qdrant partial vector deletion implemented
- [ ] MinIO file deletion implemented
- [ ] Celery task revocation implemented
- [ ] PostgreSQL record deletion implemented
- [ ] Graceful error handling for missing artifacts
- [ ] Permission checks enforced
- [ ] Audit logging integrated
- [ ] Unit tests passing (6+)
- [ ] Integration tests passing (5+)
- [ ] Code review approved
