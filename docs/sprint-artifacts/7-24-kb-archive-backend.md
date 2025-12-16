# Story 7-24: KB Archive Backend

| Field | Value |
|-------|-------|
| **Story ID** | 7-24 |
| **Epic** | Epic 7 - Infrastructure & DevOps |
| **Priority** | HIGH |
| **Effort** | 5 story points |
| **Added** | 2025-12-10 (Correct-Course: KB Delete/Archive Feature) |
| **Status** | TODO |
| **Context** | [7-24-kb-archive-backend.context.xml](7-24-kb-archive-backend.context.xml) |

## User Story

**As an** administrator
**I want** to archive a Knowledge Base and all its documents
**So that** content is preserved but hidden from normal operations

## Background

This story implements the KB Archive functionality as part of the KB lifecycle management feature. It introduces distinct **Archive** and **Delete** operations for Knowledge Bases:

- **Archive KB**: Cascades to all documents, marking them archived and filtering from search results. KB can be restored.
- **Delete KB**: Only permitted for empty Knowledge Bases (0 documents). Performs hard delete.

The archive pattern reuses Epic 6's document archive cascade pattern, ensuring consistency and reliability through the transactional outbox.

## Acceptance Criteria

### AC-7.24.1: Archive endpoint
- **Given** I have ADMIN permission on a KB
- **When** I call POST /api/v1/knowledge-bases/{id}/archive
- **Then** the KB status is set to ARCHIVED
- **And** KB.archived_at is set to current timestamp

### AC-7.24.2: Cascade to documents
- **Given** a KB is being archived
- **When** the archive operation executes
- **Then** all documents in KB have archived_at set to current timestamp
- **And** an outbox event is created for Qdrant payload updates

### AC-7.24.3: Qdrant payload updates
- **Given** a KB archive outbox event is processed
- **When** the outbox worker runs
- **Then** all Qdrant points for KB documents have payload updated to is_archived: true
- **And** archived points are excluded from search queries

### AC-7.24.4: Archived KB hidden from listings
- **Given** a KB is archived
- **When** I call GET /api/v1/knowledge-bases
- **Then** the archived KB does not appear in default listing
- **And** it appears when include_archived=true query param is set

### AC-7.24.5: Upload blocked on archived KB
- **Given** a KB is archived
- **When** I try to upload documents to it
- **Then** I receive 400 Bad Request
- **And** error message states: "Cannot upload to archived KB"

### AC-7.24.6: Audit logging
- **Given** a KB is archived
- **When** the operation completes
- **Then** the action is logged to audit.events with event_type=kb.archived

## Tasks

### Task 1: Database Migration
- [ ] 1.1 Create Alembic migration to add `archived_at TIMESTAMP WITH TIME ZONE` column to `knowledge_bases` table
- [ ] 1.2 Add partial index: `CREATE INDEX idx_kb_archived ON knowledge_bases(archived_at) WHERE archived_at IS NOT NULL`
- [ ] 1.3 Test migration up/down

### Task 2: KB Model Updates
- [ ] 2.1 Add `archived_at: datetime | None` field to `KnowledgeBase` model
- [ ] 2.2 Update `KBStatus` enum if needed (or use archived_at as archive indicator)
- [ ] 2.3 Add `is_archived` property to model

### Task 3: Archive Endpoint Implementation
- [ ] 3.1 Create `POST /api/v1/knowledge-bases/{id}/archive` endpoint
- [ ] 3.2 Require ADMIN permission check
- [ ] 3.3 Set KB.archived_at to current timestamp
- [ ] 3.4 Cascade: UPDATE documents SET archived_at = now() WHERE kb_id = {id}
- [ ] 3.5 Create outbox event: KB_ARCHIVE with kb_id

### Task 4: Outbox Worker - KB Archive Handler
- [ ] 4.1 Add KB_ARCHIVE event handler to outbox worker
- [ ] 4.2 Fetch all document IDs for KB
- [ ] 4.3 Batch update Qdrant payloads (100 points per batch)
- [ ] 4.4 Set `is_archived: true` on all KB points
- [ ] 4.5 Handle errors with retry logic

### Task 5: KB List Filtering
- [ ] 5.1 Modify `GET /api/v1/knowledge-bases` to exclude archived by default
- [ ] 5.2 Add `include_archived` query parameter
- [ ] 5.3 Update KB list response to include archived_at field

### Task 6: Upload Protection
- [ ] 6.1 Add check in document upload endpoint
- [ ] 6.2 Return 400 if KB.archived_at is not null
- [ ] 6.3 Clear error message: "Cannot upload to archived KB"

### Task 7: Audit Logging
- [ ] 7.1 Log kb.archived event on successful archive
- [ ] 7.2 Include metadata: kb_id, kb_name, document_count, user_id

### Task 8: Testing
- [ ] 8.1 Unit tests for KB archive service
- [ ] 8.2 Integration tests for archive endpoint
- [ ] 8.3 Test cascade to documents
- [ ] 8.4 Test Qdrant payload updates
- [ ] 8.5 Test KB list filtering

## Dev Notes

### Database Schema Change

```sql
-- Migration
ALTER TABLE knowledge_bases
ADD COLUMN archived_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- Partial index for archived KBs
CREATE INDEX idx_kb_archived ON knowledge_bases(archived_at) WHERE archived_at IS NOT NULL;
```

### Archive Flow Sequence

```
KB Archive Flow:
1. Set KB.archived_at = now()
2. UPDATE documents SET archived_at = now() WHERE kb_id = {id}
3. Create outbox event: KB_ARCHIVE with kb_id
4. Outbox worker: Batch update Qdrant payloads (is_archived: true)
5. Log to audit.events
```

### Key Files to Modify

**Backend:**
- `backend/alembic/versions/xxxx_add_kb_archived_at.py` - Migration
- `backend/app/models/knowledge_base.py` - Add archived_at field
- `backend/app/api/v1/knowledge_bases.py` - Archive endpoint
- `backend/app/services/kb_service.py` - Archive service method
- `backend/app/workers/outbox_tasks.py` - KB_ARCHIVE handler
- `backend/app/schemas/knowledge_base.py` - Update response schema

**Tests:**
- `backend/tests/unit/test_kb_service.py` - Archive unit tests
- `backend/tests/integration/test_kb_archive_api.py` - Integration tests

### Implementation Pattern (from Epic 6 Document Archive)

```python
# In kb_service.py
async def archive_kb(self, kb_id: UUID, user_id: UUID) -> KnowledgeBase:
    async with self.db.begin():
        # 1. Update KB
        kb = await self.get_kb_by_id(kb_id)
        kb.archived_at = datetime.utcnow()

        # 2. Cascade to documents
        await self.db.execute(
            update(Document)
            .where(Document.kb_id == kb_id)
            .values(archived_at=datetime.utcnow())
        )

        # 3. Create outbox event
        await self.create_outbox_event(
            event_type="KB_ARCHIVE",
            payload={"kb_id": str(kb_id)}
        )

        # 4. Audit log
        await self.audit_service.log(
            event_type="kb.archived",
            user_id=user_id,
            resource_id=kb_id,
            metadata={"document_count": kb.document_count}
        )

        return kb
```

### Qdrant Batch Update Pattern

```python
# In outbox_tasks.py
async def handle_kb_archive(payload: dict):
    kb_id = payload["kb_id"]

    # Get all document IDs
    doc_ids = await get_kb_document_ids(kb_id)

    # Batch update in chunks of 100
    for batch in chunks(doc_ids, 100):
        await qdrant_client.set_payload(
            collection_name=f"kb_{kb_id}",
            payload={"is_archived": True},
            points=batch
        )
```

### Dependencies
- Story 2.1 (KB CRUD Backend) - Base KB operations
- Story 6.1 (Archive Document Backend) - Pattern reference
- Story 2.11 (Outbox Processing) - Event processing infrastructure

## Testing Strategy

### Unit Tests
- Mock database session and Qdrant client
- Test archive service method
- Test cascade logic
- Test permission checks
- Test archived KB upload protection

### Integration Tests
- Create KB with documents
- Archive KB via API
- Verify KB and documents have archived_at set
- Verify Qdrant payloads updated
- Verify KB hidden from default listing
- Verify upload blocked

### Test Fixtures
```python
@pytest.fixture
def kb_with_documents(db_session):
    kb = KnowledgeBase(name="Test KB")
    docs = [Document(kb_id=kb.id, name=f"doc_{i}") for i in range(5)]
    db_session.add_all([kb, *docs])
    return kb
```

## Definition of Done
- [ ] All ACs implemented and passing
- [ ] Database migration created and tested
- [ ] Unit tests ≥80% coverage
- [ ] Integration tests passing
- [ ] No ruff lint errors
- [ ] Code reviewed
- [ ] Documentation updated

## References
- [Sprint Change Proposal](sprint-change-proposal-kb-archive-delete-2025-12-10.md)
- [Epic 2 - KB & Document Management](../epics/epic-2-kb-documents.md)
- [Epic 6 - Document Archive Pattern](../epics/epic-6-document-lifecycle.md)
