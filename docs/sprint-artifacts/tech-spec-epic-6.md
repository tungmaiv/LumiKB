# Epic Technical Specification: Document Lifecycle Management

Date: 2025-12-07
Author: Tung Vu
Epic ID: epic-6
Status: Draft

---

## Overview

Epic 6 introduces comprehensive document lifecycle management capabilities to LumiKB, enabling users to manage documents through their complete lifecycle including archive, restore, purge, clear failed, duplicate detection, and replace operations.

Key capabilities:
1. **Archive & Restore**: Soft-delete completed documents to remove from active search while keeping them recoverable
2. **Purge**: Permanent deletion of archived documents with full storage cleanup (PostgreSQL, Qdrant, MinIO)
3. **Clear Failed**: Remove partial artifacts from failed document processing attempts
4. **Duplicate Detection**: Prevent duplicate document names within a KB with intelligent handling
5. **Replace**: Update existing documents with new versions while preserving document identity

## Objectives and Scope

### In Scope

**Archive Management (FR59-63)**
- Archive completed documents to remove from active search
- Dedicated archive management page with pagination, search, filtering
- Restore archived documents back to active status
- Name collision detection on restore

**Purge Operations (FR64-66)**
- Single document purge (permanent deletion)
- Bulk purge for multiple archived documents
- Complete multi-layer storage cleanup (PostgreSQL, Qdrant, MinIO, Redis/Celery)

**Failed Document Handling (FR67-68)**
- Clear failed documents manually
- Remove all partial artifacts from failed processing

**Duplicate Detection & Replace (FR69-74)**
- Case-insensitive duplicate name detection on upload
- Detection scope: completed, processing, pending, and archived documents
- Auto-clear failed documents on same-name re-upload
- Replace existing document with confirmation workflow

**Audit Trail (FR77)**
- All lifecycle operations create audit log entries
- Actions: document_archived, document_restored, document_purged, document_cleared, document_replaced, document_auto_cleared

### Out of Scope

- Automated retention policies (future enhancement)
- Version history / document versioning (future enhancement)
- Soft-delete for non-archived documents
- Trash/recycle bin concept (archive serves this purpose)
- Bulk archive operations beyond single KB scope

## System Architecture Alignment

Epic 6 builds on the established architecture with enhancements to existing services:

**Backend Services (FastAPI)**
- Extends DocumentService with lifecycle operations
- New endpoints on `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/` path
- Reuses existing permission checking patterns from KB service

**Storage Layer Operations**
- PostgreSQL: Status field updates, soft-delete (archive), hard-delete (purge/clear)
- Qdrant: Payload updates for soft-filter (archive), vector deletion (purge/clear)
- MinIO: Object deletion for permanent removal
- Redis/Celery: Task revocation and metadata cleanup

**Frontend (Next.js 15 App Router)**
- New `/app/(protected)/archive/page.tsx` route for archive management
- Extended DocumentActionsMenu component for lifecycle actions
- New DuplicateDocumentModal for upload conflict handling

**Document State Machine**
```
pending ─┬─> processing ─┬─> completed ─> archived ─> [purged/deleted]
         │               │
         │               └─> failed ─> [cleared/deleted]
         │
         └─> failed ─> [cleared/deleted]

Note: Cancel Processing allows users to interrupt pending/processing
      documents, moving them to failed status for retry or deletion.
```

**State Transitions:**
| From | To | Operation | Trigger |
|------|-----|-----------|---------|
| completed | archived | Archive | User action |
| archived | completed | Restore | User action |
| archived | [deleted] | Purge | User action |
| failed | [deleted] | Clear | User action / Auto-clear |
| pending | failed | Cancel | User action |
| processing | failed | Cancel | User action |
| any (except processing) | pending | Replace | User action |

## Detailed Design

### Services and Modules

| Service/Module | Responsibilities | Inputs | Outputs | Owner |
|----------------|------------------|--------|---------|-------|
| **DocumentLifecycleService** | Archive, restore, purge, clear operations | Document ID, operation type | Operation result, audit entry | Stories 6.1-6.4 |
| **DuplicateDetectionService** | Check for duplicate names, auto-clear failed | KB ID, document name | Duplicate status, existing doc info | Story 6.5 |
| **DocumentReplaceService** | Replace document with new version | Document ID, new file | Updated document, processing task | Story 6.6 |
| **QdrantLifecycleOperations** | Payload updates, vector deletion | Collection, document ID, operation | Success/failure | Stories 6.1-6.4 |
| **ArchiveManagementPage** | Archive listing UI with actions | Filters, pagination | Archived documents table | Story 6.7 |
| **useArchive** | React Query hook for archive operations | API calls | Archive list, mutations | Story 6.7 |
| **DocumentActionsMenu (Extended)** | Archive/Clear actions in document list | Document status, permissions | Action menu items | Story 6.8 |
| **DuplicateDocumentModal** | Handle duplicate upload conflicts | Conflict info | User decision (cancel/replace) | Story 6.9 |

### Database Schema Changes

**Document Model Extensions**
```sql
-- Add archived_at timestamp to documents table
ALTER TABLE documents ADD COLUMN archived_at TIMESTAMP NULL;

-- Index for efficient archive queries
CREATE INDEX idx_documents_archived_at ON documents(archived_at) WHERE archived_at IS NOT NULL;

-- Composite index for duplicate detection (case-insensitive)
CREATE INDEX idx_documents_kb_name_lower ON documents(knowledge_base_id, LOWER(name));
```

**Status Enum Extension**
```python
class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"  # New status
```

### API Contracts

**Archive Document**
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
```

**Restore Document**
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
Response 409: { "detail": "Cannot restore: a document with this name already exists" }
```

**Purge Document (Single)**
```
DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge
Authorization: Bearer {token}

Response 200: { "message": "Document permanently deleted" }
Response 400: { "detail": "Only archived documents can be purged" }
```

**Bulk Purge**
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

**Clear Failed Document**
```
DELETE /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear
Authorization: Bearer {token}

Response 200: { "message": "Failed document cleared" }
Response 400: { "detail": "Only failed documents can be cleared" }
```

**Cancel Document Processing**
```
POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/cancel
Authorization: Bearer {token}

Response 200: { "message": "Document processing cancelled" }
Response 400: { "detail": "Only PROCESSING or PENDING documents can be cancelled" }
Response 403: { "detail": "Permission denied" }
Response 404: { "detail": "Document not found" }
```

Note: Cancel moves the document to FAILED status with `last_error = "Processing cancelled by user"`.
The document can then be retried or deleted. This is useful for:
- Stuck documents that aren't progressing
- Documents uploaded by mistake during processing
- Freeing up processing queue for more important documents

**Replace Document**
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
```

**List Archived Documents**
```
GET /api/v1/documents/archived?kb_id={kb_id}&search={search}&page={page}&limit={limit}
Authorization: Bearer {token}

Response 200:
{
  "items": [
    {
      "id": "uuid",
      "name": "document.pdf",
      "kb_id": "uuid",
      "kb_name": "My KB",
      "status": "archived",
      "archived_at": "2025-12-07T10:00:00Z",
      "completed_at": "2025-12-01T08:00:00Z",
      "file_size": 1024000
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

**Upload with Duplicate Detection Response**
```
POST /api/v1/knowledge-bases/{kb_id}/documents
Content-Type: multipart/form-data

Response 409 (Duplicate):
{
  "error": "duplicate_document",
  "existing_document_id": "uuid",
  "existing_status": "completed",  // or "archived"
  "message": "A document with this name already exists"
}

Response 201 (Auto-cleared failed):
{
  "id": "uuid",
  "name": "document.pdf",
  "status": "pending",
  "auto_cleared_document_id": "uuid",
  "message": "Previous failed upload was automatically cleared"
}
```

### Qdrant Operations

**Archive (Soft-Filter)**
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

**Restore**
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

**Purge/Clear (Hard Delete)**
```python
# Delete vectors permanently
await qdrant_client.delete(
    collection_name=f"kb_{kb_id}",
    points_selector=FilterSelector(
        filter=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=str(doc_id)))]
        )
    )
)
```

**Search Filter (Exclude Archived)**
```python
# Add to search filter to exclude archived documents
filter_conditions.append(
    FieldCondition(
        key="status",
        match=MatchValue(value="completed")  # Only search completed docs
    )
)
```

### MinIO Operations

```python
# Delete document file
await minio_client.remove_object(
    bucket_name=settings.MINIO_BUCKET,
    object_name=f"{kb_id}/{doc_id}/{filename}"
)
```

### Celery Task Management

```python
# Revoke pending tasks for document
from celery.result import AsyncResult

def revoke_document_tasks(task_id: str):
    if task_id:
        app.control.revoke(task_id, terminate=True)
        # Clean up Redis task metadata
        result = AsyncResult(task_id, app=app)
        result.forget()
```

### Permission Model

All lifecycle operations require:
- **KB Owner**: Full access to lifecycle operations for their KBs
- **Admin (is_admin=True)**: Full access to lifecycle operations for all KBs
- **Regular User**: No lifecycle operation access (can only upload/view)

Permission check pattern:
```python
async def check_lifecycle_permission(
    user: User,
    kb: KnowledgeBase
) -> bool:
    if user.is_admin:
        return True
    if kb.owner_id == user.id:
        return True
    return False
```

## Non-Functional Requirements

### Performance

| Operation | Target | Notes |
|-----------|--------|-------|
| Archive (single) | < 500ms | PostgreSQL update + Qdrant payload update |
| Restore (single) | < 500ms | PostgreSQL update + Qdrant payload update |
| Purge (single) | < 3s | PostgreSQL delete + Qdrant vectors delete + MinIO object delete |
| Bulk Purge (up to 100) | < 30s | Parallel execution with connection pooling |
| Clear Failed | < 2s | Graceful handling of missing artifacts |
| Replace | < 1s (initial) | Returns immediately, processing async |
| Duplicate Detection | < 200ms | Indexed case-insensitive query |
| Archive List (paginated) | < 500ms | Indexed query with pagination |

### Reliability

| Requirement | Implementation |
|-------------|----------------|
| **Atomic State Transitions** | Use database transactions for status updates; Qdrant/MinIO operations wrapped in try-catch |
| **Partial Failure Handling** | Purge: If MinIO fails after Qdrant delete, log error and continue; document removed from search |
| **Rollback on Critical Failure** | Archive/Restore: Rollback PostgreSQL if Qdrant payload update fails |
| **Graceful Degradation** | Clear Failed: Skip missing artifacts (file already deleted, vectors not created) |
| **Idempotency** | All operations check current state before executing; repeated calls return same result |
| **Consistency Verification** | Reconciliation job detects orphaned vectors (doc deleted but vectors remain) |

### Security

| Requirement | Implementation |
|-------------|----------------|
| **Authorization** | All lifecycle endpoints require KB owner OR admin role |
| **Permission Check Location** | Service layer (not just API decorator) for reusability |
| **Audit Trail** | Fire-and-forget audit logging for all operations |
| **Input Validation** | Document IDs validated as UUID; bulk purge limited to 100 documents |
| **Rate Limiting** | Bulk purge: 10 requests/minute per user |

### Observability

| Metric | Type | Labels |
|--------|------|--------|
| `lumikb_documents_archived_total` | Counter | `kb_id`, `user_id` |
| `lumikb_documents_restored_total` | Counter | `kb_id`, `user_id` |
| `lumikb_documents_purged_total` | Counter | `kb_id`, `user_id`, `bulk` |
| `lumikb_documents_cleared_total` | Counter | `kb_id`, `user_id`, `auto` |
| `lumikb_documents_replaced_total` | Counter | `kb_id`, `user_id` |
| `lumikb_lifecycle_operation_duration_seconds` | Histogram | `operation`, `status` |
| `lumikb_lifecycle_errors_total` | Counter | `operation`, `error_type` |

**Alerting Thresholds:**
- Purge operation > 10s: Warning
- Lifecycle error rate > 5% over 5 minutes: Alert
- Orphaned documents detected (reconciliation): Alert

**Logging:**
- All operations logged with `structlog` at INFO level
- Include: `operation`, `document_id`, `kb_id`, `user_id`, `duration_ms`, `status`
- Errors logged at ERROR level with full stack trace

## Story Dependencies

```
Story 6.1 (Archive Backend)
    │
    ├─> Story 6.2 (Restore Backend)
    │
    ├─> Story 6.3 (Purge Backend)
    │
    └─> Story 6.7 (Archive Management UI)
         │
         └─> Story 6.8 (Document List Actions UI)

Story 6.4 (Clear Failed Backend)
    │
    └─> Story 6.5 (Duplicate Detection)
         │
         └─> Story 6.6 (Replace Backend)
              │
              └─> Story 6.9 (Duplicate Upload UI)
```

**Recommended Implementation Order:**
1. Story 6.1: Archive Document Backend (3 pts)
2. Story 6.4: Clear Failed Document Backend (3 pts)
3. Story 6.2: Restore Document Backend (3 pts)
4. Story 6.3: Purge Document Backend (5 pts)
5. Story 6.5: Duplicate Detection & Auto-Clear Backend (5 pts)
6. Story 6.6: Replace Document Backend (5 pts)
7. Story 6.7: Archive Management UI (5 pts)
8. Story 6.8: Document List Archive/Clear Actions UI (3 pts)
9. Story 6.9: Duplicate Upload & Replace UI (3 pts)

**Total Story Points:** 35

## Testing Strategy

### Unit Tests
- DocumentLifecycleService state transitions
- Permission checks for each operation
- Duplicate detection logic (case-insensitive)
- Auto-clear trigger conditions

### Integration Tests
- Archive → Search exclusion verification
- Restore → Name collision detection
- Purge → Multi-layer cleanup verification
- Replace → Atomic operation testing
- Duplicate detection → Response format validation

### E2E Tests
- Archive page navigation and listing
- Restore with collision error handling
- Purge confirmation flow (two-step)
- Upload duplicate → Replace workflow
- Auto-clear notification display

## Audit Log Events

| Action | Payload | Actor |
|--------|---------|-------|
| `document_archived` | `{doc_id, kb_id, doc_name}` | User who archived |
| `document_restored` | `{doc_id, kb_id, doc_name}` | User who restored |
| `document_purged` | `{doc_id, kb_id, doc_name}` | User who purged |
| `document_cleared` | `{doc_id, kb_id, doc_name, reason}` | User who cleared |
| `document_auto_cleared` | `{doc_id, kb_id, doc_name, reason: "duplicate_upload"}` | System (triggered by uploader) |
| `document_replaced` | `{doc_id, kb_id, old_name, new_name}` | User who replaced |

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss from accidental purge | High | Two-step confirmation, admin-only access |
| Orphaned vectors in Qdrant | Medium | Transactional operations, cleanup verification |
| Race condition on replace | Medium | Database locks, status checks |
| Name collision edge cases | Low | Case-insensitive comparison, KB-scoped checks |

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._
