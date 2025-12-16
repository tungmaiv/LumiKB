# Technical Debt: Document Upload & Processing Defects

**Created:** 2025-12-05
**Updated:** 2025-12-06 (All defects fixed)
**Priority:** CRITICAL
**Status:** ✅ RESOLVED
**Reporter:** Tung Vu (via SM)

---

## Migration Notice

> **RESOLVED:** All defects in this document were fixed on 2025-12-06.
> This file is kept for historical reference only.
>
> **See consolidated tracker:** **[epic-7-tech-debt.md](./epic-7-tech-debt.md)**
>
> **Resolution Summary:**
> - P0: PostgreSQL Connection Pool Exhaustion - FIXED
> - P1: Duplicate Documents on Single Upload - FIXED
> - P2: Documents Stuck in Processing - FIXED

---

## Executive Summary

**THREE critical defects** identified in the document upload and processing pipeline:
1. **Duplicate documents** appear when uploading a single file
2. **Documents stuck in "Processing"** status for 22+ hours
3. **PostgreSQL connection pool exhaustion** (NEWLY DISCOVERED - BLOCKING)

All defects impact user experience and data integrity. **Defect 3 is the immediate blocker** - the entire processing pipeline is non-functional due to database connection exhaustion.

---

## ✅ Resolution Summary (2025-12-06)

All three defects have been fixed:

### P0 - PostgreSQL Connection Pool Exhaustion (FIXED)
**Files Modified:**
- `infrastructure/docker/docker-compose.yml` - PostgreSQL max_connections=200 (already applied)
- `backend/app/core/database.py` - Added connection pool config (pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=1800, pool_pre_ping=True)
- `backend/app/core/database.py` - Created separate `celery_engine` with NullPool and `celery_session_factory` for workers
- `backend/app/workers/outbox_tasks.py` - Switched to use `celery_session_factory`
- `backend/app/workers/document_tasks.py` - Switched to use `celery_session_factory`

### P1 - Duplicate Documents on Single Upload (FIXED)
**Files Modified:**
- `backend/app/services/document_service.py` - Added duplicate filename check before upload
- `backend/app/services/document_service.py` - Reordered operations: MinIO upload BEFORE database record creation

### P2 - Documents Stuck in Processing Status (FIXED)
**Files Modified:**
- `backend/app/workers/celery_app.py` - Reduced reconciliation interval from 3600s to 300s (5 minutes)
- `backend/app/workers/outbox_tasks.py` - Reduced stale threshold from 30 to 10 minutes
- `backend/app/integrations/minio_client.py` - Added timeout configuration (connect=30s, read=60s, retries=3)

---

## CRITICAL: Defect 3 - PostgreSQL Connection Pool Exhaustion (BLOCKER)

### Symptoms (Live Investigation 2025-12-05)
- PostgreSQL rejecting ALL new connections: `FATAL: sorry, too many clients already`
- Outbox polling fails continuously every 10 seconds
- **Reconciliation job has NEVER run** (no logs found)
- Documents stuck for **22 hours** because processing pipeline is completely blocked

### Evidence from Live Logs

**Celery Worker Logs (continuous failures):**
```
[2025-12-05 12:16:45] outbox_poll_failed error='sorry, too many clients already'
[2025-12-05 12:16:55] outbox_poll_failed error='sorry, too many clients already'
[2025-12-05 12:17:05] outbox_poll_failed error='sorry, too many clients already'
```

**PostgreSQL Logs (saturated):**
```
2025-12-05 12:17:26 FATAL: sorry, too many clients already
2025-12-05 12:17:35 FATAL: sorry, too many clients already
2025-12-05 12:17:46 LOG: unexpected EOF on client connection with an open transaction
```

**Celery Beat Logs:**
- `process-outbox-events` runs every 10 seconds (configured correctly)
- `reconcile-data-consistency` - **NO LOGS FOUND** (never executed due to connection exhaustion)

### Root Cause Analysis

**Location:** [backend/app/core/database.py](../backend/app/core/database.py) + [backend/app/workers/outbox_tasks.py](../backend/app/workers/outbox_tasks.py)

**Problem:**
1. Each outbox poll creates a new async database session
2. Sessions are not being properly closed/released
3. Pool exhaustion prevents ANY database operations
4. Reconciliation job never runs because it can't get a connection

**Additional Issue - Event Loop Errors:**
```
RuntimeError: Event loop is closed
Task got Future attached to a different loop
```
This indicates async context issues in Celery workers with SQLAlchemy async sessions.

### Required Fixes

#### Fix 3.1: Increase PostgreSQL max_connections
**File:** `infrastructure/docker/docker-compose.yml`

```yaml
postgres:
  image: postgres:16
  command:
    - "postgres"
    - "-c"
    - "max_connections=200"  # Increase from default 100
  environment:
    ...
```

#### Fix 3.2: Configure SQLAlchemy Connection Pool
**File:** `backend/app/core/database.py`

```python
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=10,           # Base connections
    max_overflow=20,        # Extra connections when needed
    pool_timeout=30,        # Wait 30s for connection
    pool_recycle=1800,      # Recycle connections after 30 min
    pool_pre_ping=True,     # Verify connection is alive
)
```

#### Fix 3.3: Fix Async Session Management in Celery
**File:** `backend/app/workers/outbox_tasks.py`

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_worker_session():
    """Properly scoped async session for Celery workers."""
    # Create new event loop for each task if needed
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()  # CRITICAL: Explicit close
```

#### Fix 3.4: Add Connection Health Check
**File:** `backend/app/workers/outbox_tasks.py`

```python
async def _poll_outbox_events() -> dict:
    """Poll with connection health check."""
    try:
        async with get_worker_session() as session:
            # Test connection first
            await session.execute(text("SELECT 1"))

            # Then poll for events
            ...
    except Exception as e:
        if "too many clients" in str(e):
            logger.error("connection_pool_exhausted",
                        action="backing_off")
            await asyncio.sleep(30)  # Back off on pool exhaustion
        raise
```

### Immediate Action Required

**Before any other fix, the connection pool must be fixed.** Current state:
- Documents uploaded in last 22 hours are ALL stuck
- No processing is happening
- Reconciliation never runs
- System is effectively broken

---

## Defect 1: Duplicate Documents on Single Upload

### Symptoms
- User uploads 1 file, sees 2+ copies in KB listing
- Duplicates have same filename, same upload time, same uploader

### Root Cause Analysis

**Location:** [backend/app/services/document_service.py:71-192](../backend/app/services/document_service.py#L71-L192)

**Problem Flow:**
```
1. Document record created in DB (PENDING)
2. session.flush() called → Document now has ID in DB
3. File uploaded to MinIO (EXTERNAL I/O - can fail here)
4. Outbox event created
5. Transaction commits on request exit
```

**Race Condition:**
- If MinIO upload fails after flush but before commit
- Retry creates NEW document (no duplicate check)
- No unique constraint prevents this

**Code Evidence:**
```python
# Line 126-127: Document created and flushed
document = Document(...)
self.session.add(document)
await self.session.flush()  # Document now in DB

# Line 129-152: File upload (can fail)
full_path = await minio_service.upload_file(...)

# If exception here, document exists but may be orphaned
# User retries → new document created
```

### Required Fixes

#### Fix 1.1: Add Database Unique Constraint
**File:** New Alembic migration

```python
# Create partial unique index (exclude soft-deleted)
op.create_index(
    'ix_documents_kb_filename_unique',
    'documents',
    ['kb_id', 'original_filename'],
    unique=True,
    postgresql_where=text('deleted_at IS NULL')
)
```

#### Fix 1.2: Add Duplicate Check in Upload Service
**File:** `backend/app/services/document_service.py`

```python
async def upload(self, kb_id: UUID, file: UploadFile, user_id: UUID) -> Document:
    # ADD: Check for existing document with same filename
    existing = await self.session.execute(
        select(Document).where(
            Document.kb_id == kb_id,
            Document.original_filename == file.filename,
            Document.deleted_at.is_(None)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Document '{file.filename}' already exists in this KB"
        )

    # Continue with existing upload logic...
```

#### Fix 1.3: Reorder Operations (Create After Upload)
**File:** `backend/app/services/document_service.py`

```python
async def upload(self, kb_id: UUID, file: UploadFile, user_id: UUID) -> Document:
    # 1. Validate file first
    content = await file.read()
    await self._validate_file(file, len(content))

    # 2. Upload to MinIO BEFORE creating DB record
    temp_path = f"temp/{kb_id}/{uuid4()}/{file.filename}"
    full_path = await minio_service.upload_file(
        content, temp_path, file.content_type
    )

    # 3. Only create Document if upload succeeded
    document = Document(
        kb_id=kb_id,
        file_path=full_path,  # Already have path
        ...
    )
    self.session.add(document)

    # 4. Create outbox event in same transaction
    outbox_event = Outbox(...)
    self.session.add(outbox_event)

    await self.session.commit()  # Explicit commit
    return document
```

---

## Defect 2: Documents Stuck in "Processing" for Hours

### Symptoms
- Documents show "Processing..." status for 2+ hours
- Documents never transition to READY or FAILED
- Users cannot search or use the documents

### Root Cause Analysis

**Location 1:** [backend/app/workers/document_tasks.py:257-270](../backend/app/workers/document_tasks.py#L257-L270)

```python
@celery_app.task(
    soft_time_limit=540,   # 9 minutes (SIGTERM)
    time_limit=600,        # 10 minutes (SIGKILL)
    acks_late=True,
    reject_on_worker_lost=True,
)
```

**Location 2:** [backend/app/workers/outbox_tasks.py:406-555](../backend/app/workers/outbox_tasks.py#L406-L555)

**Problem:**
- Worker crash/timeout leaves document in PROCESSING
- Reconciliation job runs every **3600 seconds (1 hour)**
- Stale threshold is **30 minutes**
- **Worst case recovery time: 90 minutes**

**Missing Safeguards:**
- No individual timeouts on network calls (MinIO, Qdrant, LiteLLM)
- No heartbeat mechanism during processing
- Reconciliation frequency too low

### Required Fixes

#### Fix 2.1: Reduce Reconciliation Interval
**File:** `backend/app/workers/outbox_tasks.py`

```python
# Change from 3600 to 300 seconds (5 minutes)
@celery_app.task(name="app.workers.outbox_tasks.reconciliation_job")
def reconciliation_job():
    """Run every 5 minutes instead of 1 hour."""
    ...

# In celery beat schedule:
"reconciliation-job": {
    "task": "app.workers.outbox_tasks.reconciliation_job",
    "schedule": 300,  # 5 minutes instead of 3600
}
```

#### Fix 2.2: Reduce Stale Threshold
**File:** `backend/app/workers/outbox_tasks.py`

```python
async def _detect_stale_processing(session) -> list[dict]:
    # Change from 30 minutes to 10 minutes
    stale_threshold = datetime.now(UTC) - timedelta(minutes=10)
    ...
```

#### Fix 2.3: Add Network Call Timeouts
**File:** `backend/app/workers/document_tasks.py`

```python
import asyncio

async def _chunk_embed_index(...):
    # Add timeout to embedding call
    try:
        embeddings = await asyncio.wait_for(
            litellm_service.get_embeddings(chunks),
            timeout=120  # 2 minute timeout per batch
        )
    except asyncio.TimeoutError:
        raise ProcessingError("Embedding service timeout")

    # Add timeout to Qdrant upsert
    try:
        await asyncio.wait_for(
            qdrant_service.upsert_vectors(vectors),
            timeout=60  # 1 minute timeout
        )
    except asyncio.TimeoutError:
        raise ProcessingError("Vector DB timeout")
```

#### Fix 2.4: Add Processing Heartbeat
**File:** `backend/app/workers/document_tasks.py`

```python
async def process_document(self, document_id: str):
    """Process with periodic heartbeat updates."""

    async def update_heartbeat():
        await session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(processing_heartbeat=datetime.now(UTC))
        )
        await session.commit()

    # Update heartbeat every 30 seconds during processing
    heartbeat_task = asyncio.create_task(
        periodic_heartbeat(update_heartbeat, interval=30)
    )

    try:
        # ... processing logic ...
    finally:
        heartbeat_task.cancel()
```

**Update stale detection to use heartbeat:**
```python
async def _detect_stale_processing(session) -> list[dict]:
    # Document is stale if heartbeat > 2 minutes old
    stale_threshold = datetime.now(UTC) - timedelta(minutes=2)

    result = await session.execute(
        select(Document)
        .where(Document.status == DocumentStatus.PROCESSING)
        .where(
            or_(
                Document.processing_heartbeat < stale_threshold,
                Document.processing_heartbeat.is_(None)
            )
        )
    )
```

---

## Database Migration Required

```python
"""Add document processing tracking columns

Revision ID: xxx
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add heartbeat column for stale detection
    op.add_column(
        'documents',
        sa.Column('processing_heartbeat', sa.DateTime(timezone=True), nullable=True)
    )

    # Add partial unique index to prevent duplicates
    op.create_index(
        'ix_documents_kb_filename_unique',
        'documents',
        ['kb_id', 'original_filename'],
        unique=True,
        postgresql_where=sa.text('deleted_at IS NULL')
    )

def downgrade():
    op.drop_index('ix_documents_kb_filename_unique')
    op.drop_column('documents', 'processing_heartbeat')
```

---

## Testing Requirements

### Unit Tests
1. Test duplicate upload returns 409 Conflict
2. Test document status transitions correctly
3. Test heartbeat updates during processing
4. Test stale detection with various thresholds

### Integration Tests
1. Upload same file twice → second should fail
2. Kill worker during processing → document should recover
3. Simulate network timeout → document should fail gracefully
4. Verify reconciliation job requeues stale documents

### Manual Verification
1. Upload document → verify single entry in DB
2. Kill celery worker mid-processing → verify recovery within 15 minutes
3. Check no orphaned documents after various failure scenarios

---

## Acceptance Criteria

### Defect 3 (P0) Fixed When:
- [x] PostgreSQL max_connections increased to 200
- [x] SQLAlchemy engine configured with proper connection pooling (pool_size=10, max_overflow=20)
- [x] Celery workers use NullPool to avoid event loop issues
- [x] Separate `celery_session_factory` for worker processes

### Defect 1 (P1) Fixed When:
- [x] Uploading same file twice returns 409 error
- [x] Duplicate check added before document creation
- [x] MinIO upload happens BEFORE database record creation (operation reordering)

### Defect 2 (P2) Fixed When:
- [x] Stuck documents recover within 15 minutes (not 90)
- [x] Reconciliation runs every 5 minutes (reduced from 3600s to 300s)
- [x] Stale threshold reduced from 30 to 10 minutes
- [x] MinIO client configured with timeouts (connect=30s, read=60s)
- [x] Network timeouts properly configured

---

## Files to Modify

### Priority 1: Fix Connection Pool (BLOCKER)
| File | Changes |
|------|---------|
| `infrastructure/docker/docker-compose.yml` | Increase PostgreSQL max_connections to 200 |
| `backend/app/core/database.py` | Configure SQLAlchemy pool (size, overflow, timeout, recycle, pre_ping) |
| `backend/app/workers/outbox_tasks.py` | Fix async session management, add connection health checks |

### Priority 2: Fix Duplicates
| File | Changes |
|------|---------|
| `backend/app/services/document_service.py` | Add duplicate check, reorder operations |
| `backend/alembic/versions/xxx_*.py` | Add partial unique index on (kb_id, filename) |

### Priority 3: Fix Stuck Processing
| File | Changes |
|------|---------|
| `backend/app/workers/document_tasks.py` | Add heartbeat, network timeouts |
| `backend/app/workers/celery_app.py` | Reduce reconciliation interval (3600 → 300) |
| `backend/app/workers/outbox_tasks.py` | Reduce stale threshold (30 → 10 min) |
| `backend/app/models/document.py` | Add processing_heartbeat column |
| `backend/alembic/versions/xxx_*.py` | Add heartbeat column |

---

## Estimated Complexity & Priority Order

| Priority | Defect | Complexity | Reason |
|----------|--------|------------|--------|
| **P0** | Connection Pool Exhaustion | Medium | BLOCKER - nothing works without this |
| **P1** | Duplicate Documents | Medium | Data integrity issue |
| **P2** | Stuck Processing | Medium-High | UX issue, mitigated once P0 is fixed |

---

## Immediate Workaround (Before Fix)

To unblock the system temporarily:

```bash
# 1. Restart all containers to clear leaked connections
docker compose -f infrastructure/docker/docker-compose.yml restart

# 2. Verify connections cleared
docker exec lumikb-postgres psql -U lumikb_dev -d lumikb_dev \
  -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Watch for connection exhaustion
docker logs -f lumikb-postgres 2>&1 | grep -E "FATAL|too many"
```

**Note:** This is temporary. The leak will recur within hours without the proper fix.

---

## Related Documentation

- [Document Processing Flow](../architecture.md#document-processing)
- [Celery Worker Configuration](../../backend/app/workers/celery_app.py)
- [Outbox Pattern Implementation](../../backend/app/workers/outbox_tasks.py)
- [PostgreSQL Connection Management](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [SQLAlchemy Async Session Best Practices](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
