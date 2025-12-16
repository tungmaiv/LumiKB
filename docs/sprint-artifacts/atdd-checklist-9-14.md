# ATDD Checklist - Epic 9, Story 14: Data Retention & Cleanup

**Date:** 2025-12-15
**Author:** Tung Vu
**Primary Test Level:** API/Unit (Backend Python - Celery/TimescaleDB)

---

## Story Summary

Implement automated data retention and cleanup for observability data using TimescaleDB's efficient chunk management. Supports configurable retention periods, dry-run mode, and manual cleanup via admin API.

**As an** Admin/DevOps engineer
**I want** observability data to be automatically cleaned up based on configurable retention policies
**So that** database storage is managed efficiently and compliance requirements are met

---

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

---

## Failing Tests Created (RED Phase)

### Unit Tests (14 tests)

**File:** `backend/tests/unit/test_retention_service.py`

- [ ] **Test:** `test_retention_days_default_value`
  - **Status:** RED - Config setting not defined
  - **Verifies:** AC1 - Default 90 days configured

- [ ] **Test:** `test_retention_days_configurable_via_env`
  - **Status:** RED - Config setting not defined
  - **Verifies:** AC1 - Environment variable override works

- [ ] **Test:** `test_cleanup_task_registered_in_celery`
  - **Status:** RED - Task not registered
  - **Verifies:** AC2 - Task exists in Celery app

- [ ] **Test:** `test_cleanup_uses_drop_chunks_function`
  - **Status:** RED - Cleanup logic not implemented
  - **Verifies:** AC3, AC4 - Uses TimescaleDB drop_chunks

- [ ] **Test:** `test_cleanup_drops_chunks_older_than_retention`
  - **Status:** RED - Cleanup logic not implemented
  - **Verifies:** AC3 - Correct age threshold applied

- [ ] **Test:** `test_cleanup_logs_operations_for_audit`
  - **Status:** RED - Audit logging not implemented
  - **Verifies:** AC5 - Operations logged with structlog

- [ ] **Test:** `test_metrics_aggregates_longer_retention`
  - **Status:** RED - Different retention not implemented
  - **Verifies:** AC6 - 365 days for metrics_aggregates

- [ ] **Test:** `test_provider_sync_status_7_day_retention`
  - **Status:** RED - Sync status cleanup not implemented
  - **Verifies:** AC7 - 7 days for provider_sync_status

- [ ] **Test:** `test_dry_run_mode_no_deletions`
  - **Status:** RED - Dry-run mode not implemented
  - **Verifies:** AC9 - Dry-run shows but doesn't delete

- [ ] **Test:** `test_dry_run_returns_preview_summary`
  - **Status:** RED - Preview logic not implemented
  - **Verifies:** AC9 - Returns what would be deleted

- [ ] **Test:** `test_show_chunks_called_in_dry_run`
  - **Status:** RED - show_chunks not used
  - **Verifies:** AC9 - Uses TimescaleDB show_chunks

- [ ] **Test:** `test_cleanup_handles_no_chunks_gracefully`
  - **Status:** RED - Edge case not handled
  - **Verifies:** AC10 - Empty result handled

- [ ] **Test:** `test_cleanup_handles_timescaledb_not_installed`
  - **Status:** RED - Extension check not implemented
  - **Verifies:** AC10 - Graceful degradation

- [ ] **Test:** `test_all_hypertables_cleaned`
  - **Status:** RED - Multi-table cleanup not implemented
  - **Verifies:** AC3 - All observability tables cleaned

### Integration Tests (4 tests)

**File:** `backend/tests/integration/test_retention_cleanup.py`

- [ ] **Test:** `test_cleanup_full_flow_with_timescaledb`
  - **Status:** RED - Full flow not implemented
  - **Verifies:** AC3, AC4 - End-to-end cleanup works

- [ ] **Test:** `test_beat_schedule_at_3am_daily`
  - **Status:** RED - Beat schedule not configured
  - **Verifies:** AC2 - Scheduled for 3 AM daily

- [ ] **Test:** `test_admin_cleanup_endpoint`
  - **Status:** RED - API endpoint not implemented
  - **Verifies:** AC8 - Manual trigger works

- [ ] **Test:** `test_admin_cleanup_requires_admin_role`
  - **Status:** RED - Authorization not implemented
  - **Verifies:** AC8 - Admin-only access

---

## Data Factories Created

### Retention Test Data Factories

**File:** `backend/tests/factories/observability_factory.py`

**Existing Exports (already available):**

- `create_trace(overrides?)` - Create trace record
- `create_span(overrides?)` - Create span record
- `create_metrics_aggregate(overrides?)` - Create aggregate record
- `create_provider_sync_status(overrides?)` - Create sync status

**New Factory Functions to Add:**

```python
def create_old_traces(
    *,
    count: int = 10,
    days_old: int = 100,
) -> list[dict[str, Any]]:
    """Create traces older than retention period.

    Args:
        count: Number of traces to create
        days_old: How many days in the past

    Returns:
        List of trace dictionaries with old timestamps
    """
    old_time = datetime.utcnow() - timedelta(days=days_old)
    return [
        create_completed_trace(
            started_at=old_time - timedelta(hours=i),
            ended_at=old_time - timedelta(hours=i) + timedelta(seconds=5),
        )
        for i in range(count)
    ]


def create_recent_traces(
    *,
    count: int = 10,
    days_old: int = 30,
) -> list[dict[str, Any]]:
    """Create traces within retention period.

    Args:
        count: Number of traces to create
        days_old: How many days in the past (within retention)

    Returns:
        List of trace dictionaries with recent timestamps
    """
    recent_time = datetime.utcnow() - timedelta(days=days_old)
    return [
        create_completed_trace(
            started_at=recent_time + timedelta(hours=i),
            ended_at=recent_time + timedelta(hours=i) + timedelta(seconds=5),
        )
        for i in range(count)
    ]


def create_old_sync_status(
    *,
    days_old: int = 10,
    provider_name: str = "langfuse",
    sync_status: str = "synced",
) -> dict[str, Any]:
    """Create provider sync status older than 7 days."""
    return create_provider_sync_status(
        provider_name=provider_name,
        sync_status=sync_status,
        last_synced_at=datetime.utcnow() - timedelta(days=days_old),
    )
```

**Example Usage:**

```python
from tests.factories import (
    create_old_traces,
    create_recent_traces,
    create_old_sync_status,
)

# Create traces that should be deleted (older than 90 days)
old_traces = create_old_traces(count=50, days_old=100)

# Create traces that should be kept (within 90 days)
recent_traces = create_recent_traces(count=50, days_old=30)

# Create sync status older than 7 days
old_sync = create_old_sync_status(days_old=10)
```

---

## Fixtures Created

### Retention Test Fixtures

**File:** `backend/tests/fixtures/retention_fixtures.py`

**Fixtures:**

- `populated_old_data` - Tables with old and recent data
  - **Setup:** Insert old traces (100+ days) and recent traces (30 days)
  - **Provides:** Database session with mixed-age data
  - **Cleanup:** Truncate all observability tables

- `retention_service` - Retention service instance
  - **Setup:** Create service with test database
  - **Provides:** `RetentionService` instance
  - **Cleanup:** None (stateless)

- `mock_timescaledb` - Mock TimescaleDB functions
  - **Setup:** Patch drop_chunks and show_chunks
  - **Provides:** Mock functions for unit tests
  - **Cleanup:** Restore original functions

**Example Usage:**

```python
import pytest
from tests.fixtures.retention_fixtures import populated_old_data

@pytest.fixture
async def populated_old_data(test_db_session):
    """Populate tables with data of various ages."""
    from tests.factories import create_old_traces, create_recent_traces
    from app.models.observability import Trace

    # Insert old data (should be deleted)
    old_traces = create_old_traces(count=20, days_old=100)
    for trace_data in old_traces:
        test_db_session.add(Trace(**trace_data))

    # Insert recent data (should be kept)
    recent_traces = create_recent_traces(count=20, days_old=30)
    for trace_data in recent_traces:
        test_db_session.add(Trace(**trace_data))

    await test_db_session.commit()
    yield test_db_session


async def test_cleanup_drops_old_keeps_recent(populated_old_data):
    from app.services.retention_service import RetentionService

    service = RetentionService(populated_old_data)
    result = await service.cleanup(dry_run=False)

    # Verify old data deleted, recent kept
    remaining = await populated_old_data.execute(
        text("SELECT COUNT(*) FROM observability.traces")
    )
    assert remaining.scalar() == 20  # Only recent traces remain
```

---

## Mock Requirements

### TimescaleDB Functions Mock

**Target:** TimescaleDB `drop_chunks()` and `show_chunks()` functions

**Mock Setup:**

```python
@pytest.fixture
def mock_timescaledb(mocker):
    """Mock TimescaleDB functions for unit tests."""
    mock_drop = mocker.MagicMock(return_value=5)  # 5 chunks dropped
    mock_show = mocker.MagicMock(return_value=[
        {"chunk_name": "chunk_1", "range_start": "2025-09-01"},
        {"chunk_name": "chunk_2", "range_start": "2025-09-15"},
    ])

    async def mock_execute(query, params=None):
        if "drop_chunks" in str(query):
            return mock_drop()
        if "show_chunks" in str(query):
            return mock_show()
        return mocker.MagicMock()

    mocker.patch.object(
        AsyncSession,
        "execute",
        side_effect=mock_execute
    )

    return {"drop_chunks": mock_drop, "show_chunks": mock_show}
```

### Structlog Mock

**Target:** Audit logging calls

**Mock Setup:**

```python
@pytest.fixture
def mock_structlog(mocker):
    """Mock structlog for audit log verification."""
    mock_logger = mocker.MagicMock()
    mocker.patch("structlog.get_logger", return_value=mock_logger)
    return mock_logger


async def test_cleanup_logs_operations_for_audit(mock_structlog, retention_service):
    await retention_service.cleanup(dry_run=False)

    # Verify audit logs were created
    mock_structlog.info.assert_any_call(
        "retention_cleanup_started",
        dry_run=False,
    )
    mock_structlog.info.assert_any_call(
        "chunks_dropped",
        table=mocker.ANY,
        count=mocker.ANY,
    )
```

---

## Required Configuration

### Config Settings

**File:** `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Observability Retention Settings
    observability_retention_days: int = Field(
        default=90,
        env="OBSERVABILITY_RETENTION_DAYS",
        description="Days to retain raw observability data (traces, spans, events)"
    )
    observability_metrics_retention_days: int = Field(
        default=365,
        env="OBSERVABILITY_METRICS_RETENTION_DAYS",
        description="Days to retain aggregated metrics"
    )
    observability_sync_status_retention_days: int = Field(
        default=7,
        env="OBSERVABILITY_SYNC_STATUS_RETENTION_DAYS",
        description="Days to retain provider sync status records"
    )
```

---

## Implementation Checklist

### Test: `test_retention_days_default_value`

**File:** `backend/tests/unit/test_retention_service.py`

**Tasks to make this test pass:**

- [ ] Add `observability_retention_days` to `Settings` class in config.py
- [ ] Set default value to 90
- [ ] Add type annotation `int`
- [ ] Add `env="OBSERVABILITY_RETENTION_DAYS"` parameter
- [ ] Run test: `pytest backend/tests/unit/test_retention_service.py::test_retention_days_default_value -v`
- [ ] Test passes (green phase)

---

### Test: `test_cleanup_task_registered_in_celery`

**File:** `backend/tests/unit/test_retention_service.py`

**Tasks to make this test pass:**

- [ ] Create `backend/app/workers/retention_tasks.py`
- [ ] Import `shared_task` from Celery
- [ ] Define `cleanup_observability_data` task function
- [ ] Add `@shared_task` decorator
- [ ] Import task in `celery_app.py` for autodiscovery
- [ ] Run test: `pytest backend/tests/unit/test_retention_service.py::test_cleanup_task_registered_in_celery -v`
- [ ] Test passes (green phase)

---

### Test: `test_cleanup_uses_drop_chunks_function`

**File:** `backend/tests/unit/test_retention_service.py`

**Tasks to make this test pass:**

- [ ] Create `backend/app/services/retention_service.py`
- [ ] Implement `drop_old_chunks()` method
- [ ] Use SQL: `SELECT drop_chunks('table', older_than => ...)`
- [ ] Pass retention days as interval
- [ ] Run test: `pytest backend/tests/unit/test_retention_service.py::test_cleanup_uses_drop_chunks_function -v`
- [ ] Test passes (green phase)

---

### Test: `test_dry_run_mode_no_deletions`

**File:** `backend/tests/unit/test_retention_service.py`

**Tasks to make this test pass:**

- [ ] Add `dry_run: bool = False` parameter to cleanup method
- [ ] When `dry_run=True`, use `show_chunks()` instead of `drop_chunks()`
- [ ] Return preview data without modifying database
- [ ] Log "DRY RUN" in audit messages
- [ ] Run test: `pytest backend/tests/unit/test_retention_service.py::test_dry_run_mode_no_deletions -v`
- [ ] Test passes (green phase)

---

### Test: `test_metrics_aggregates_longer_retention`

**File:** `backend/tests/unit/test_retention_service.py`

**Tasks to make this test pass:**

- [ ] Add `observability_metrics_retention_days` config (default 365)
- [ ] Use different retention for `metrics_aggregates` table
- [ ] Define HYPERTABLES list with per-table retention
- [ ] Run test: `pytest backend/tests/unit/test_retention_service.py::test_metrics_aggregates_longer_retention -v`
- [ ] Test passes (green phase)

---

### Test: `test_provider_sync_status_7_day_retention`

**File:** `backend/tests/unit/test_retention_service.py`

**Tasks to make this test pass:**

- [ ] Add `observability_sync_status_retention_days` config (default 7)
- [ ] Use standard DELETE (not drop_chunks) for non-hypertable
- [ ] Only delete synced/failed records, not pending
- [ ] Run test: `pytest backend/tests/unit/test_retention_service.py::test_provider_sync_status_7_day_retention -v`
- [ ] Test passes (green phase)

---

### Test: `test_admin_cleanup_endpoint`

**File:** `backend/tests/integration/test_retention_cleanup.py`

**Tasks to make this test pass:**

- [ ] Add route in `backend/app/api/v1/admin.py`
- [ ] Create `POST /api/v1/admin/observability/cleanup` endpoint
- [ ] Accept `dry_run` query parameter (default True for safety)
- [ ] Return cleanup summary as JSON response
- [ ] Require admin authentication
- [ ] Run test: `pytest backend/tests/integration/test_retention_cleanup.py::test_admin_cleanup_endpoint -v`
- [ ] Test passes (green phase)

---

### Test: `test_beat_schedule_at_3am_daily`

**File:** `backend/tests/integration/test_retention_cleanup.py`

**Tasks to make this test pass:**

- [ ] Add task to `celery_app.conf.beat_schedule`
- [ ] Configure `crontab(hour=3, minute=0)`
- [ ] Set task name to `'cleanup-observability-data-daily'`
- [ ] Set `args=(False,)` for production (dry_run=False)
- [ ] Run test: `pytest backend/tests/integration/test_retention_cleanup.py::test_beat_schedule_at_3am_daily -v`
- [ ] Test passes (green phase)

---

## Running Tests

```bash
# Run all unit tests for retention
pytest backend/tests/unit/test_retention_service.py -v

# Run integration tests
pytest backend/tests/integration/test_retention_cleanup.py -v

# Run with coverage
pytest backend/tests/unit/test_retention_service.py --cov=app/services/retention_service --cov=app/workers/retention_tasks --cov-report=term-missing

# Run specific test
pytest backend/tests/unit/test_retention_service.py::test_dry_run_mode_no_deletions -v

# Run with verbose SQL logging
pytest backend/tests/integration/test_retention_cleanup.py -v --log-cli-level=DEBUG

# Test TimescaleDB integration (requires TimescaleDB extension)
pytest backend/tests/integration/test_retention_cleanup.py::test_cleanup_full_flow_with_timescaledb -v
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

-  All tests written and failing
-  Fixtures and factories documented
-  Mock requirements documented
-  Implementation checklist created

---

### GREEN Phase (DEV Team - Next Steps)

**Recommended Implementation Order:**

1. Add configuration settings (AC1, AC6, AC7)
2. Create Celery task file (AC2)
3. Implement basic drop_chunks wrapper (AC3, AC4)
4. Add audit logging (AC5)
5. Implement per-table retention logic (AC6)
6. Implement provider_sync_status cleanup (AC7)
7. Create admin API endpoint (AC8)
8. Add dry-run mode (AC9)
9. Configure beat schedule (AC2)
10. Handle edge cases and errors (AC10)

---

## Knowledge Base References Applied

- **data-factories.md** - Factory patterns for test data
- **test-quality.md** - Idempotent test design
- **ci-burn-in.md** - Celery task testing patterns
- **error-handling.md** - Graceful degradation patterns

---

## Notes

- TimescaleDB extension must be installed for integration tests
- `drop_chunks()` is efficient but irreversible - dry-run recommended first
- Admin endpoint defaults to dry_run=True for safety
- Provider sync status uses DELETE (not hypertable)
- Consider adding Prometheus metrics for cleanup job monitoring
- Audit logs should include storage reclaimed (if available from TimescaleDB)

---

## Security Considerations

- Admin-only access for manual cleanup endpoint
- All cleanup operations logged for audit trail
- Dry-run by default for API to prevent accidents
- No user-facing data deletion API exposed

---

**Generated by BMad TEA Agent** - 2025-12-15
