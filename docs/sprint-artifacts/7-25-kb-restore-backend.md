# Story 7-25: KB Restore Backend

| Field | Value |
|-------|-------|
| **Story ID** | 7-25 |
| **Epic** | Epic 7 - Infrastructure & DevOps |
| **Priority** | HIGH |
| **Effort** | 3 story points |
| **Added** | 2025-12-10 (Correct-Course: KB Delete/Archive Feature) |
| **Status** | TODO |
| **Context** | [7-25-kb-restore-backend.context.xml](7-25-kb-restore-backend.context.xml) |

## User Story

**As an** administrator
**I want** to restore an archived Knowledge Base
**So that** it becomes active and searchable again

## Background

This story implements the KB Restore functionality, complementing Story 7.24 (KB Archive Backend). When a KB is restored:

1. The KB's archived_at is cleared
2. All documents in the KB have archived_at cleared
3. Qdrant payloads are updated to is_archived: false
4. The KB becomes searchable and accepts new uploads again

The restore operation mirrors the archive operation with inverse logic.

## Acceptance Criteria

### AC-7.25.1: Restore endpoint
- **Given** I have ADMIN permission on an archived KB
- **When** I call POST /api/v1/knowledge-bases/{id}/restore
- **Then** the KB status is set to ACTIVE
- **And** KB.archived_at is set to null

### AC-7.25.2: Cascade restore to documents
- **Given** a KB is being restored
- **When** the restore operation executes
- **Then** all documents in KB have archived_at set to null
- **And** an outbox event is created for Qdrant payload updates

### AC-7.25.3: Qdrant payload updates
- **Given** a KB restore outbox event is processed
- **When** the outbox worker runs
- **Then** all Qdrant points for KB documents have payload updated to is_archived: false
- **And** restored points are included in search queries

### AC-7.25.4: Restored KB visible in listings
- **Given** a KB is restored
- **When** I call GET /api/v1/knowledge-bases
- **Then** the KB appears in default listing
- **And** document upload is permitted again

### AC-7.25.5: Audit logging
- **Given** a KB is restored
- **When** the operation completes
- **Then** the action is logged to audit.events with event_type=kb.restored

## Tasks

### Task 1: Restore Endpoint Implementation
- [ ] 1.1 Create `POST /api/v1/knowledge-bases/{id}/restore` endpoint
- [ ] 1.2 Require ADMIN permission check
- [ ] 1.3 Verify KB is currently archived (archived_at is not null)
- [ ] 1.4 Set KB.archived_at to null
- [ ] 1.5 Cascade: UPDATE documents SET archived_at = null WHERE kb_id = {id}
- [ ] 1.6 Create outbox event: KB_RESTORE with kb_id

### Task 2: Outbox Worker - KB Restore Handler
- [ ] 2.1 Add KB_RESTORE event handler to outbox worker
- [ ] 2.2 Fetch all document IDs for KB
- [ ] 2.3 Batch update Qdrant payloads (100 points per batch)
- [ ] 2.4 Set `is_archived: false` on all KB points
- [ ] 2.5 Handle errors with retry logic

### Task 3: Validation
- [ ] 3.1 Return 400 if KB is not archived
- [ ] 3.2 Clear error message: "KB is not archived"

### Task 4: Audit Logging
- [ ] 4.1 Log kb.restored event on successful restore
- [ ] 4.2 Include metadata: kb_id, kb_name, document_count, user_id

### Task 5: Testing
- [ ] 5.1 Unit tests for KB restore service
- [ ] 5.2 Integration tests for restore endpoint
- [ ] 5.3 Test cascade to documents
- [ ] 5.4 Test Qdrant payload updates
- [ ] 5.5 Test restored KB in listings

## Dev Notes

### Restore Flow Sequence

```
KB Restore Flow:
1. Verify KB.archived_at is not null
2. Set KB.archived_at = null
3. UPDATE documents SET archived_at = null WHERE kb_id = {id}
4. Create outbox event: KB_RESTORE with kb_id
5. Outbox worker: Batch update Qdrant payloads (is_archived: false)
6. Log to audit.events
```

### Key Files to Modify

**Backend:**
- `backend/app/api/v1/knowledge_bases.py` - Restore endpoint
- `backend/app/services/kb_service.py` - Restore service method
- `backend/app/workers/outbox_tasks.py` - KB_RESTORE handler

**Tests:**
- `backend/tests/unit/test_kb_service.py` - Restore unit tests
- `backend/tests/integration/test_kb_restore_api.py` - Integration tests

### Implementation Pattern

```python
# In kb_service.py
async def restore_kb(self, kb_id: UUID, user_id: UUID) -> KnowledgeBase:
    async with self.db.begin():
        # 1. Get and validate KB
        kb = await self.get_kb_by_id(kb_id)
        if kb.archived_at is None:
            raise HTTPException(400, "KB is not archived")

        # 2. Clear archived_at
        kb.archived_at = None

        # 3. Cascade to documents
        await self.db.execute(
            update(Document)
            .where(Document.kb_id == kb_id)
            .values(archived_at=None)
        )

        # 4. Create outbox event
        await self.create_outbox_event(
            event_type="KB_RESTORE",
            payload={"kb_id": str(kb_id)}
        )

        # 5. Audit log
        await self.audit_service.log(
            event_type="kb.restored",
            user_id=user_id,
            resource_id=kb_id,
            metadata={"document_count": kb.document_count}
        )

        return kb
```

### Qdrant Restore Pattern

```python
# In outbox_tasks.py
async def handle_kb_restore(payload: dict):
    kb_id = payload["kb_id"]

    # Get all document IDs
    doc_ids = await get_kb_document_ids(kb_id)

    # Batch update in chunks of 100
    for batch in chunks(doc_ids, 100):
        await qdrant_client.set_payload(
            collection_name=f"kb_{kb_id}",
            payload={"is_archived": False},
            points=batch
        )
```

### API Endpoint

```python
@router.post("/{kb_id}/restore", response_model=KBResponse)
async def restore_kb(
    kb_id: UUID,
    current_user: User = Depends(get_current_user),
    kb_service: KBService = Depends(get_kb_service),
):
    """Restore an archived Knowledge Base."""
    # Check ADMIN permission
    await check_kb_permission(kb_id, current_user, PermissionLevel.ADMIN)

    kb = await kb_service.restore_kb(kb_id, current_user.id)
    return kb
```

### Dependencies
- Story 7.24 (KB Archive Backend) - Must be completed first

## Testing Strategy

### Unit Tests
- Mock database session and Qdrant client
- Test restore service method
- Test cascade logic
- Test permission checks
- Test validation (restoring non-archived KB)

### Integration Tests
- Create KB with documents
- Archive KB
- Restore KB via API
- Verify KB and documents have archived_at cleared
- Verify Qdrant payloads updated
- Verify KB visible in default listing
- Verify upload works again

### Test Cases

```python
class TestKBRestore:
    async def test_restore_archived_kb(self, client, archived_kb):
        """Test restoring an archived KB."""
        response = await client.post(f"/api/v1/knowledge-bases/{archived_kb.id}/restore")
        assert response.status_code == 200
        assert response.json()["archived_at"] is None

    async def test_restore_non_archived_kb_fails(self, client, active_kb):
        """Test restoring a non-archived KB returns 400."""
        response = await client.post(f"/api/v1/knowledge-bases/{active_kb.id}/restore")
        assert response.status_code == 400
        assert "not archived" in response.json()["detail"]

    async def test_restore_cascades_to_documents(self, client, archived_kb_with_docs):
        """Test that restore clears archived_at on all documents."""
        await client.post(f"/api/v1/knowledge-bases/{archived_kb_with_docs.id}/restore")

        docs = await get_kb_documents(archived_kb_with_docs.id)
        assert all(doc.archived_at is None for doc in docs)
```

## Definition of Done
- [ ] All ACs implemented and passing
- [ ] Unit tests ≥80% coverage
- [ ] Integration tests passing
- [ ] No ruff lint errors
- [ ] Code reviewed
- [ ] Documentation updated

## References
- [Sprint Change Proposal](sprint-change-proposal-kb-archive-delete-2025-12-10.md)
- [Story 7-24: KB Archive Backend](7-24-kb-archive-backend.md)
- [Epic 6 - Document Restore Pattern](../epics/epic-6-document-lifecycle.md)
