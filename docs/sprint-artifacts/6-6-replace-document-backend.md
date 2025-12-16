# Story 6-6: Replace Document Backend

## Story Information
- **Epic:** 6 - Document Lifecycle Management
- **Story ID:** 6-6
- **Story Points:** 5
- **Priority:** HIGH
- **Status:** ready-for-dev

## User Story
**As a** KB owner or admin
**I want** to replace an existing document with a new version
**So that** I can update content without changing the document's identity

## Context
Document replacement allows updating an existing document with a new file while preserving the document ID. This is useful when the user intentionally wants to update a document they uploaded previously, triggered from the duplicate detection workflow.

## Acceptance Criteria

### AC-6.6.1: Replace endpoint exists
**Given** I am authenticated as KB owner or admin
**And** a document exists (any status except "processing")
**When** I call POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace with new file
**Then** I receive 200 OK with updated document details
**And** an audit log entry is created with action "document_replaced"

### AC-6.6.2: Replace performs atomic delete-then-upload
**Given** I replace a document
**When** the operation executes
**Then** the old document's vectors are deleted from Qdrant
**And** the old file is deleted from MinIO
**And** the new file is uploaded to MinIO
**And** document metadata is updated (file_size, content_type, updated_at)
**And** document status is set to "pending" for reprocessing

### AC-6.6.3: Replace preserves document ID and metadata
**Given** I replace a document
**When** the operation completes
**Then** the document ID remains the same
**And** the document name is updated to new file name
**And** created_at timestamp is preserved
**And** tags and other metadata are preserved

### AC-6.6.4: Cannot replace while processing
**Given** a document has status "processing"
**When** I attempt to replace it
**Then** I receive 400 Bad Request with message "Cannot replace document while processing is in progress"

### AC-6.6.5: Permission check enforced
**Given** I am not KB owner or admin
**When** I attempt to replace a document
**Then** I receive 403 Forbidden

### AC-6.6.6: Replace triggers reprocessing
**Given** I replace a document
**When** the operation completes
**Then** a new Celery task is queued for document processing
**And** the document status shows "pending"

### AC-6.6.7: Replace from upload flow with confirmation
**Given** duplicate detection returns 409 for an active document
**When** user confirms replacement via the replace endpoint
**Then** the existing document is replaced with the new upload

## Technical Notes

### API Contract
```
POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: <new_document_file>

Response 200:
{
  "id": "uuid",  // Same ID preserved
  "name": "new_document.pdf",
  "status": "pending",
  "message": "Document replaced and queued for processing"
}

Response 400: { "detail": "Cannot replace document while processing is in progress" }
Response 403: { "detail": "Permission denied" }
Response 404: { "detail": "Document not found" }
```

### Replace Operation Steps
```python
async def replace_document(doc_id: UUID, kb_id: UUID, file: UploadFile, user: User):
    document = await get_document(doc_id)

    # 1. Validate document exists and not processing
    if document.status == DocumentStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Cannot replace document while processing is in progress")

    # 2. Check permissions (KB owner or admin)
    await check_lifecycle_permission(user, kb_id)

    # 3. Delete old Qdrant vectors
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
        logger.warning(f"Qdrant cleanup failed: {e}")

    # 4. Delete old MinIO file
    try:
        await minio_client.remove_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=f"{kb_id}/{doc_id}/{document.name}"
        )
    except Exception as e:
        logger.warning(f"MinIO cleanup failed: {e}")

    # 5. Upload new file to MinIO
    file_content = await file.read()
    file_path = f"{kb_id}/{doc_id}/{file.filename}"
    await minio_client.put_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=file_path,
        data=io.BytesIO(file_content),
        length=len(file_content),
        content_type=file.content_type
    )

    # 6. Update document metadata
    old_name = document.name
    document.name = file.filename
    document.file_size = len(file_content)
    document.content_type = file.content_type
    document.status = DocumentStatus.PENDING
    document.archived_at = None  # Clear if was archived
    document.updated_at = datetime.utcnow()
    # Preserve: created_at, tags, other metadata

    await db.commit()

    # 7. Queue Celery task for processing
    task = process_document.delay(str(doc_id), str(kb_id))
    document.task_id = task.id
    await db.commit()

    # 8. Create audit log entry
    await audit_service.log_event(
        action="document_replaced",
        resource_type="document",
        resource_id=str(doc_id),
        details={
            "kb_id": str(kb_id),
            "old_name": old_name,
            "new_name": file.filename
        }
    )

    return document
```

## Dependencies
- Story 6-5: Duplicate Detection (provides duplicate detection that triggers replace flow)

## Test Cases

### Unit Tests
1. replace_document succeeds for completed document
2. replace_document succeeds for failed document
3. replace_document succeeds for archived document
4. replace_document raises error for processing document
5. replace_document preserves document ID
6. replace_document preserves created_at and tags
7. replace_document deletes old Qdrant vectors
8. replace_document deletes old MinIO file
9. replace_document uploads new file
10. replace_document queues new processing task
11. replace_document creates audit log entry

### Integration Tests
1. POST /replace returns 200 with updated document
2. POST /replace returns 400 for processing document
3. POST /replace returns 403 for non-owner
4. Replace preserves document ID
5. Replace deletes old Qdrant vectors
6. Replace queues new processing task
7. Replace creates audit log entry

## Definition of Done
- [ ] DocumentService.replace_document() method implemented
- [ ] POST /replace endpoint implemented (multipart/form-data)
- [ ] Old Qdrant vector deletion implemented
- [ ] Old MinIO file deletion implemented
- [ ] New file upload implemented
- [ ] Metadata update preserving ID and created_at
- [ ] Celery task queuing implemented
- [ ] Permission checks enforced
- [ ] Audit logging integrated
- [ ] Unit tests passing (11+)
- [ ] Integration tests passing (7+)
- [ ] Code review approved
