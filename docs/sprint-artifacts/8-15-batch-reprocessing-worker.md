# Story 8-15: Batch Re-processing Worker

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-15
**Priority:** MEDIUM
**Estimated Effort:** 3 story points
**Status:** BACKLOG

---

## Overview

Implement a dedicated Celery worker for batch re-processing operations including entity re-extraction and document reprocessing. This handles large-scale operations efficiently without impacting normal document processing.

---

## Acceptance Criteria

### AC1: Dedicated Worker Queue
**Given** re-extraction jobs are created
**When** tasks are queued
**Then** they use a dedicated "reprocessing" queue
**And** normal document processing continues unaffected
**And** queue priority can be configured

### AC2: Rate Limiting
**Given** many documents need re-extraction
**When** tasks are processed
**Then** LLM calls are rate-limited to avoid overload
**And** configurable rate limits (default: 10 calls/second)
**And** rate limit violations trigger backoff

### AC3: Progress Reporting
**Given** a batch job is running
**When** status is queried
**Then** real-time progress is available:
  - Documents completed/failed/remaining
  - Estimated time remaining
  - Current processing rate
  - Recent errors (last 10)

### AC4: Resource Management
**Given** re-processing may run for hours
**When** resources are constrained
**Then**:
  - Memory usage is bounded
  - Connections are pooled and reused
  - Temporary files are cleaned up
  - Idle workers don't consume resources

### AC5: Failure Recovery
**Given** a worker crashes mid-job
**When** the worker restarts
**Then**:
  - In-progress documents are re-queued
  - Completed work is preserved
  - Job continues from where it stopped
  - No duplicate processing

### AC6: Job Scheduling
**Given** admins may want scheduled re-processing
**When** Celery Beat is configured
**Then** optional scheduled re-extraction is supported
**And** cron-style scheduling is available
**And** schedule can be updated at runtime

---

## Technical Notes

### Celery Worker Configuration

```python
# backend/app/workers/celery_app.py

# Define dedicated queue for reprocessing
app.conf.task_queues = (
    Queue('default', routing_key='default'),
    Queue('document_processing', routing_key='documents.#'),
    Queue('reprocessing', routing_key='reprocess.#'),  # NEW
)

app.conf.task_routes = {
    'app.workers.document_tasks.*': {'queue': 'document_processing'},
    'app.workers.extraction_tasks.reextract_*': {'queue': 'reprocessing'},  # NEW
    'app.workers.batch_tasks.*': {'queue': 'reprocessing'},  # NEW
}

# Rate limiting for LLM calls
app.conf.task_annotations = {
    'app.workers.extraction_tasks.reextract_document': {
        'rate_limit': '10/s'  # Max 10 extractions per second
    }
}
```

### Docker Compose Addition

```yaml
# infrastructure/docker/docker-compose.yml

celery-reprocessing:
  build:
    context: ../../backend
    dockerfile: Dockerfile
  container_name: lumikb-celery-reprocessing
  command: celery -A app.workers.celery_app worker -Q reprocessing -c 2 --loglevel=info
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - DATABASE_URL=postgresql+asyncpg://...
    - NEO4J_URI=bolt://neo4j:7687
    - LITELLM_API_BASE=http://litellm:4000
  depends_on:
    - redis
    - postgres
    - neo4j
    - litellm
  volumes:
    - ../../backend:/app
  networks:
    - lumikb-network
  deploy:
    resources:
      limits:
        memory: 2G  # Bounded memory
```

### Batch Task Implementation

```python
# backend/app/workers/batch_tasks.py
from celery import shared_task, group, chord
from celery.exceptions import SoftTimeLimitExceeded

@shared_task(
    bind=True,
    soft_time_limit=300,  # 5 min per document max
    time_limit=360,
    acks_late=True,  # For failure recovery
    reject_on_worker_lost=True
)
def reextract_document_batch(self, batch: List[str], job_id: str, domain_id: str, cleanup_mode: str):
    """Process a batch of documents for re-extraction."""
    results = []

    for doc_id in batch:
        try:
            # Check for cancellation
            if is_job_cancelled(job_id):
                return {"status": "cancelled", "processed": len(results)}

            result = process_single_document(doc_id, domain_id, cleanup_mode)
            results.append({"doc_id": doc_id, "status": "success", **result})

            # Update progress
            update_job_progress(job_id, completed=1)

        except SoftTimeLimitExceeded:
            # Requeue remaining documents
            remaining = batch[batch.index(doc_id):]
            reextract_document_batch.delay(remaining, job_id, domain_id, cleanup_mode)
            break

        except Exception as e:
            results.append({"doc_id": doc_id, "status": "failed", "error": str(e)})
            update_job_progress(job_id, failed=1, error=str(e))

    return {"status": "completed", "results": results}


def process_single_document(doc_id: str, domain_id: str, cleanup_mode: str) -> Dict:
    """Process a single document for re-extraction."""
    from app.services.entity_extraction_service import EntityExtractionService
    from app.services.graph_storage_service import GraphStorageService

    # Cleanup based on mode
    if cleanup_mode == "replace":
        clear_document_entities(doc_id)

    # Get chunks
    chunks = get_document_chunks(doc_id)

    # Extract entities
    extraction_service = EntityExtractionService()
    storage_service = GraphStorageService()

    entity_count = 0
    relationship_count = 0

    for chunk in chunks:
        result = extraction_service.extract_from_chunk(chunk, domain_id)
        storage_service.store_entities(result.entities)
        storage_service.store_relationships(result.relationships)

        entity_count += len(result.entities)
        relationship_count += len(result.relationships)

    # Update document schema version
    update_document_extraction_version(doc_id, domain_id)

    return {
        "entities": entity_count,
        "relationships": relationship_count
    }
```

### Progress Tracking with Redis

```python
# backend/app/services/job_progress_service.py
import redis
from typing import Optional

class JobProgressService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "reprocessing:job:"

    def update_progress(
        self,
        job_id: str,
        completed: int = 0,
        failed: int = 0,
        error: Optional[str] = None
    ):
        """Update job progress atomically."""
        key = f"{self.prefix}{job_id}"

        pipe = self.redis.pipeline()
        if completed:
            pipe.hincrby(key, "completed", completed)
        if failed:
            pipe.hincrby(key, "failed", failed)
        if error:
            pipe.lpush(f"{key}:errors", error)
            pipe.ltrim(f"{key}:errors", 0, 9)  # Keep last 10 errors
        pipe.hset(key, "last_update", datetime.utcnow().isoformat())
        pipe.execute()

    def get_progress(self, job_id: str) -> JobProgress:
        """Get current job progress."""
        key = f"{self.prefix}{job_id}"

        data = self.redis.hgetall(key)
        errors = self.redis.lrange(f"{key}:errors", 0, 9)

        total = int(data.get(b"total", 0))
        completed = int(data.get(b"completed", 0))
        failed = int(data.get(b"failed", 0))
        started_at = data.get(b"started_at")

        # Calculate ETA
        if started_at and completed > 0:
            elapsed = (datetime.utcnow() - datetime.fromisoformat(started_at.decode())).total_seconds()
            rate = completed / elapsed
            remaining = total - completed - failed
            eta_seconds = remaining / rate if rate > 0 else None
        else:
            eta_seconds = None

        return JobProgress(
            job_id=job_id,
            total=total,
            completed=completed,
            failed=failed,
            pending=total - completed - failed,
            rate=rate if completed > 0 else 0,
            eta_seconds=eta_seconds,
            recent_errors=[e.decode() for e in errors]
        )

    def initialize_job(self, job_id: str, total_documents: int):
        """Initialize job progress tracking."""
        key = f"{self.prefix}{job_id}"
        self.redis.hset(key, mapping={
            "total": total_documents,
            "completed": 0,
            "failed": 0,
            "started_at": datetime.utcnow().isoformat()
        })
        # Set expiry (7 days)
        self.redis.expire(key, 7 * 24 * 60 * 60)
```

### Scheduled Re-extraction (Optional)

```python
# backend/app/workers/celery_app.py

# Celery Beat schedule for optional scheduled re-extraction
app.conf.beat_schedule = {
    # ... existing schedules ...

    # Optional: Run schema drift check daily
    'check-schema-drift': {
        'task': 'app.workers.batch_tasks.check_all_kbs_schema_drift',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'options': {'queue': 'reprocessing'}
    },
}

@shared_task
def check_all_kbs_schema_drift():
    """Check all KBs for schema drift and notify admins."""
    from app.services.schema_drift_service import SchemaDriftService

    service = SchemaDriftService()
    kbs_with_drift = service.check_all_kbs()

    for kb in kbs_with_drift:
        if kb.outdated_count > 10:  # Threshold
            notify_admin_schema_drift(kb)
```

---

## Definition of Done

- [ ] Dedicated Celery queue for reprocessing
- [ ] Worker container in Docker Compose
- [ ] Rate limiting configured
- [ ] Batch task with proper error handling
- [ ] Redis-based progress tracking
- [ ] ETA calculation
- [ ] Error aggregation (last 10)
- [ ] Memory bounds on worker
- [ ] Failure recovery (acks_late, reject_on_worker_lost)
- [ ] Optional scheduled drift check
- [ ] Unit tests for batch processing
- [ ] Integration tests for progress tracking
- [ ] Documentation for scaling workers

---

**Created:** 2025-12-08
**Epic:** 8 - GraphRAG Integration
**Dependencies:** Story 8-14 (Schema Evolution), Story 8-9 (Document Processing Integration)
**Next Story:** None (Final story in Epic 8)
