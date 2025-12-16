# Story 9-14: Data Retention & Cleanup

Status: ready-for-dev

## Story

As an **Admin/DevOps engineer**,
I want observability data to be automatically cleaned up based on configurable retention policies,
so that database storage is managed efficiently and compliance requirements are met.

## Acceptance Criteria

1. **AC1:** Configuration: `OBSERVABILITY_RETENTION_DAYS` (default 90)
2. **AC2:** Celery beat task runs daily at 3am
3. **AC3:** Drops TimescaleDB chunks older than retention period
4. **AC4:** Uses `drop_chunks()` for efficient deletion
5. **AC5:** Logs chunk drop operations for audit
6. **AC6:** Metrics aggregates retained longer (365 days)
7. **AC7:** Provider sync status cleaned after 7 days
8. **AC8:** Admin API endpoint to trigger manual cleanup
9. **AC9:** Dry-run mode to preview deletions
10. **AC10:** Unit tests for retention logic

## Tasks / Subtasks

- [ ] Task 1: Add configuration settings (AC: 1, 6)
  - [ ] Add `OBSERVABILITY_RETENTION_DAYS` to config.py (default 90)
  - [ ] Add `OBSERVABILITY_METRICS_RETENTION_DAYS` (default 365)
  - [ ] Add `OBSERVABILITY_SYNC_STATUS_RETENTION_DAYS` (default 7)
  - [ ] Document settings in environment template

- [ ] Task 2: Create Celery beat schedule (AC: 2)
  - [ ] Add cleanup task to `backend/app/workers/celery_app.py`
  - [ ] Configure daily schedule at 3 AM
  - [ ] Add task to Celery worker imports

- [ ] Task 3: Implement TimescaleDB chunk cleanup (AC: 3, 4)
  - [ ] Create `backend/app/workers/retention_tasks.py`
  - [ ] Implement `cleanup_observability_data` task
  - [ ] Use TimescaleDB `drop_chunks()` function
  - [ ] Apply to: traces, spans, chat_messages, document_events

- [ ] Task 4: Implement metrics aggregates cleanup (AC: 6)
  - [ ] Apply longer retention (365 days) to metrics_aggregates
  - [ ] Use `drop_chunks()` for metrics_aggregates hypertable
  - [ ] Separate from main observability retention

- [ ] Task 5: Implement provider sync status cleanup (AC: 7)
  - [ ] Delete provider_sync_status records older than 7 days
  - [ ] Use standard DELETE for non-hypertable
  - [ ] Only delete synced/failed records (not pending)

- [ ] Task 6: Implement audit logging (AC: 5)
  - [ ] Log start and end of cleanup operation
  - [ ] Log each hypertable cleanup with chunk count
  - [ ] Log total storage reclaimed (if available)
  - [ ] Use structlog for consistent formatting

- [ ] Task 7: Implement dry-run mode (AC: 9)
  - [ ] Add `dry_run` parameter to cleanup task
  - [ ] Use `show_chunks()` to preview what would be dropped
  - [ ] Log preview without actual deletion
  - [ ] Return summary of what would be deleted

- [ ] Task 8: Create admin API endpoint (AC: 8)
  - [ ] Add `POST /api/v1/admin/observability/cleanup` endpoint
  - [ ] Accept `dry_run` query parameter
  - [ ] Require admin authentication
  - [ ] Return cleanup summary/preview

- [ ] Task 9: Create retention service (AC: 3, 4)
  - [ ] Create `backend/app/services/retention_service.py`
  - [ ] Implement `get_chunks_to_drop()` method
  - [ ] Implement `drop_chunks()` wrapper method
  - [ ] Handle TimescaleDB extension availability check

- [ ] Task 10: Write tests (AC: 10)
  - [ ] Unit tests for retention logic
  - [ ] Test dry-run mode
  - [ ] Test different retention periods
  - [ ] Mock TimescaleDB functions for unit tests
  - [ ] Integration test with actual chunk operations

## Dev Notes

### Learnings from Previous Story

**Story 9-10 (Document Timeline UI)** established key patterns:
- **Status Visualization:** pending/in-progress/completed/failed states - applicable to retention job status
- **Error Display:** Error message presentation pattern - reuse for cleanup failure reporting
- **Source:** [stories/9-10-document-timeline-ui.md#Step-Specific Metrics]

**Story 9-13 (Metrics Aggregation Worker)** established:
- **Celery Beat Scheduling:** Hourly task pattern - retention uses similar daily pattern at 3 AM
- **Idempotent Operations:** Safe to re-run pattern - cleanup is naturally idempotent (dropping already-dropped chunks is no-op)

### Dependencies

- **Story 9-1 (Observability Schema):** TimescaleDB hypertables must exist for `drop_chunks()` to operate on
- **Story 9-13 (Metrics Aggregation):** Aggregates should be preserved longer than raw data - retention policy alignment required

### Architecture Patterns

- **Celery Beat Pattern:** Scheduled cleanup execution
- **TimescaleDB Chunk Management:** Efficient time-based data deletion
- **Dry-Run Pattern:** Preview before destructive operations
- **Audit Trail:** All cleanup operations logged

### TimescaleDB Chunk Operations

```sql
-- View chunks for a hypertable
SELECT * FROM timescaledb_information.chunks
WHERE hypertable_name = 'traces'
ORDER BY range_start DESC;

-- Drop chunks older than retention period
SELECT drop_chunks(
    'observability.traces',
    older_than => NOW() - INTERVAL '90 days'
);

-- Drop chunks with dry-run (show what would be dropped)
SELECT show_chunks(
    'observability.traces',
    older_than => NOW() - INTERVAL '90 days'
);
```

### Cleanup Task Implementation

```python
# backend/app/workers/retention_tasks.py

from celery import shared_task
from sqlalchemy import text
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

HYPERTABLES = [
    ('observability.traces', settings.observability_retention_days),
    ('observability.spans', settings.observability_retention_days),
    ('observability.chat_messages', settings.observability_retention_days),
    ('observability.document_events', settings.observability_retention_days),
    ('observability.metrics_aggregates', settings.observability_metrics_retention_days),
]

@shared_task
def cleanup_observability_data(dry_run: bool = False):
    """Clean up observability data based on retention policies."""
    logger.info("retention_cleanup_started", dry_run=dry_run)

    results = {}
    for table, retention_days in HYPERTABLES:
        if dry_run:
            chunks = show_chunks_to_drop(table, retention_days)
            results[table] = {"chunks_to_drop": len(chunks), "dry_run": True}
        else:
            dropped = drop_old_chunks(table, retention_days)
            results[table] = {"chunks_dropped": dropped, "dry_run": False}

    # Clean provider_sync_status (non-hypertable)
    sync_deleted = cleanup_sync_status(dry_run)
    results['provider_sync_status'] = sync_deleted

    logger.info("retention_cleanup_completed", results=results)
    return results
```

### Celery Beat Schedule

```python
# backend/app/workers/celery_app.py
app.conf.beat_schedule = {
    # ... existing tasks ...
    'cleanup-observability-data-daily': {
        'task': 'app.workers.retention_tasks.cleanup_observability_data',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
        'args': (False,),  # dry_run=False
    },
}
```

### Admin API Endpoint

```python
# backend/app/api/v1/admin.py

@router.post("/observability/cleanup", response_model=CleanupResponse)
async def trigger_cleanup(
    dry_run: bool = Query(False, description="Preview without deleting"),
    current_user: User = Depends(require_admin),
):
    """Manually trigger observability data cleanup."""
    result = cleanup_observability_data.delay(dry_run=dry_run)
    return CleanupResponse(
        task_id=result.id,
        status="queued",
        dry_run=dry_run,
    )
```

### Configuration

```env
# Data retention settings
OBSERVABILITY_RETENTION_DAYS=90           # Traces, spans, chat, events
OBSERVABILITY_METRICS_RETENTION_DAYS=365  # Aggregated metrics
OBSERVABILITY_SYNC_STATUS_RETENTION_DAYS=7  # Provider sync status
```

### Source Tree Components

- `backend/app/workers/retention_tasks.py` - Cleanup Celery task
- `backend/app/services/retention_service.py` - Retention business logic
- `backend/app/workers/celery_app.py` - Beat schedule configuration
- `backend/app/api/v1/admin.py` - Manual cleanup endpoint
- `backend/app/core/config.py` - Configuration settings
- `backend/tests/unit/test_retention_service.py` - Unit tests
- `backend/tests/integration/test_retention_cleanup.py` - Integration tests

### TimescaleDB Extension Check

```python
async def check_timescaledb_available(session: AsyncSession) -> bool:
    """Check if TimescaleDB extension is available."""
    result = await session.execute(
        text("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'")
    )
    return result.scalar() is not None
```

### Testing Standards

- Mock TimescaleDB functions for unit tests
- Use test database with TimescaleDB for integration tests
- Test dry-run mode produces no side effects
- Verify audit logs are created

### Security Considerations

- Admin-only access for manual cleanup
- Audit logging of all cleanup operations
- Dry-run by default for API endpoint
- No user-facing data deletion API

### Project Structure Notes

- Follows existing Celery task patterns
- Uses existing admin API patterns
- Configuration follows settings.py conventions

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#Phase 4: Advanced Features - Story 9-14 Data Retention & Cleanup]
- [Source: docs/epics/epic-9-observability.md#Phase 4: Advanced Features (18 points)]
- [Source: docs/epics/epic-9-observability.md#Configuration] - Retention config examples
- [Source: docs/architecture.md#monitoring] - Architecture monitoring stack documentation
- [Source: docs/testing-guideline.md] - Testing standards for scheduled tasks
- [Source: backend/app/workers/celery_app.py] - Existing beat schedule pattern
- TimescaleDB: https://docs.timescale.com/api/latest/data-retention/drop_chunks/

## Dev Agent Record

### Context Reference

- [9-14-data-retention-and-cleanup.context.xml](./9-14-data-retention-and-cleanup.context.xml)

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

### File List
