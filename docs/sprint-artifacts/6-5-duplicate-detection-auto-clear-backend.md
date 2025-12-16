# Story 6-5: Duplicate Detection & Auto-Clear Backend

## Story Information
- **Epic:** 6 - Document Lifecycle Management
- **Story ID:** 6-5
- **Story Points:** 5
- **Priority:** HIGH
- **Status:** ready-for-dev

## User Story
**As a** KB user
**I want** the system to detect duplicate document uploads
**So that** I can decide whether to replace existing documents and failed uploads are automatically cleaned up

## Context
When uploading a document with a name that already exists in the KB, the system should detect the conflict and return appropriate information. If the existing document is failed, it should be automatically cleared. If the existing document is completed or archived, return 409 with details for user decision.

## Acceptance Criteria

### AC-6.5.1: Case-insensitive duplicate detection
**Given** I upload a document named "Report.pdf"
**And** a document named "report.pdf" already exists in the KB
**When** the upload is processed
**Then** duplicate detection triggers (case-insensitive match)

### AC-6.5.2: 409 response for completed/archived duplicates
**Given** I upload a document with a duplicate name
**And** the existing document has status "completed" or "archived"
**When** the upload is processed
**Then** I receive 409 Conflict with:
  - existing_document_id
  - existing_status ("completed" or "archived")
  - message explaining the conflict

### AC-6.5.3: Auto-clear failed duplicates
**Given** I upload a document with a duplicate name
**And** the existing document has status "failed"
**When** the upload is processed
**Then** the failed document is automatically cleared
**And** the new upload proceeds
**And** the response includes auto_cleared_document_id
**And** an audit log entry is created with action "document_auto_cleared"

### AC-6.5.4: Pending/processing duplicates blocked
**Given** I upload a document with a duplicate name
**And** the existing document has status "pending" or "processing"
**When** the upload is processed
**Then** I receive 409 Conflict with message "A document with this name is currently being processed"

### AC-6.5.5: Different KB allows same name
**Given** I upload a document named "Report.pdf" to KB-A
**And** a document named "Report.pdf" exists in KB-B
**When** the upload is processed
**Then** no duplicate is detected (different KB scope)
**And** the upload proceeds normally

## Technical Notes

### Database Index for Duplicate Detection
```sql
-- Composite index for efficient case-insensitive duplicate detection
CREATE INDEX idx_documents_kb_name_lower ON documents(knowledge_base_id, LOWER(name));
```

### API Response Contracts

**409 Conflict (Completed/Archived Duplicate)**
```json
{
  "error": "duplicate_document",
  "existing_document_id": "uuid",
  "existing_status": "completed",
  "message": "A document with this name already exists"
}
```

**409 Conflict (Processing Duplicate)**
```json
{
  "error": "duplicate_document",
  "existing_document_id": "uuid",
  "existing_status": "processing",
  "message": "A document with this name is currently being processed"
}
```

**201 Created (Auto-Cleared Failed)**
```json
{
  "id": "new-uuid",
  "name": "document.pdf",
  "status": "pending",
  "auto_cleared_document_id": "old-uuid",
  "message": "Previous failed upload was automatically cleared"
}
```

### Duplicate Detection Logic
```python
async def check_duplicate_on_upload(kb_id: UUID, filename: str) -> Optional[Document]:
    """Check for existing document with same name (case-insensitive)"""
    result = await db.execute(
        select(Document).where(
            Document.knowledge_base_id == kb_id,
            func.lower(Document.name) == func.lower(filename)
        )
    )
    return result.scalar_one_or_none()

async def handle_duplicate(existing: Document, new_file: UploadFile, kb_id: UUID):
    """Handle duplicate document based on existing status"""

    if existing.status == DocumentStatus.FAILED:
        # Auto-clear and proceed
        await clear_failed_document(existing.id, kb_id)
        audit_service.log_event(
            action="document_auto_cleared",
            resource_type="document",
            resource_id=str(existing.id),
            details={"reason": "duplicate_upload", "new_upload_name": new_file.filename}
        )
        return {"auto_cleared": True, "cleared_id": existing.id}

    elif existing.status in [DocumentStatus.PENDING, DocumentStatus.PROCESSING]:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "duplicate_document",
                "existing_document_id": str(existing.id),
                "existing_status": existing.status.value,
                "message": "A document with this name is currently being processed"
            }
        )

    else:  # COMPLETED or ARCHIVED
        raise HTTPException(
            status_code=409,
            detail={
                "error": "duplicate_document",
                "existing_document_id": str(existing.id),
                "existing_status": existing.status.value,
                "message": "A document with this name already exists"
            }
        )
```

## Dependencies
- Story 6-4: Clear Failed Document Backend (provides clear_failed_document function)

## Test Cases

### Unit Tests
1. Duplicate detection is case-insensitive
2. Completed duplicate returns 409 with correct details
3. Archived duplicate returns 409 with correct details
4. Processing duplicate returns 409 with processing message
5. Pending duplicate returns 409 with processing message
6. Failed duplicate triggers auto-clear
7. Auto-clear creates audit log entry
8. Different KB same name allowed

### Integration Tests
1. Upload duplicate to completed document returns 409
2. Upload duplicate to archived document returns 409
3. Upload duplicate to processing document returns 409
4. Upload duplicate to failed document succeeds with auto-clear
5. Response includes auto_cleared_document_id
6. Different KB allows same filename

## Definition of Done
- [ ] Database index created for case-insensitive duplicate detection
- [ ] Duplicate detection integrated into upload endpoint
- [ ] 409 response format implemented with existing document details
- [ ] Auto-clear for failed duplicates implemented
- [ ] Audit logging for auto-clear implemented
- [ ] Unit tests passing (8+)
- [ ] Integration tests passing (6+)
- [ ] Code review approved
