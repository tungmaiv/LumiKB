# ATDD Checklist - Epic 9, Story 13: Metrics Aggregation Worker

**Date:** 2025-12-15
**Author:** Tung Vu
**Primary Test Level:** API/Unit (Backend Python - Celery)

---

## Story Summary

Implement a Celery beat scheduled task that aggregates observability metrics into pre-computed buckets for fast dashboard queries. Supports multiple granularities and dimensions with idempotent upserts.

**As an** Admin user
**I want** observability metrics to be pre-aggregated on a schedule
**So that** dashboard queries are fast and don't impact database performance during high load

---

## Acceptance Criteria

1. **AC1:** Celery beat task runs hourly
2. **AC2:** Aggregates trace metrics into `metrics_aggregates` table
3. **AC3:** Computes count, sum, min, max, avg per metric
4. **AC4:** Calculates p50, p95, p99 percentiles for latencies
5. **AC5:** Dimensions: by operation_type, by model, by kb, by user
6. **AC6:** Handles hour, day, week granularities
7. **AC7:** Idempotent: re-running for same bucket updates metrics
8. **AC8:** Backfill capability for missed periods
9. **AC9:** Prometheus metrics for aggregation job health
10. **AC10:** Unit tests for aggregation logic

---

## Failing Tests Created (RED Phase)

### Unit Tests (14 tests)

**File:** `backend/tests/unit/test_metrics_aggregation.py`

- [ ] **Test:** `test_aggregate_task_registered_in_celery`
  - **Status:** RED - Task not registered
  - **Verifies:** AC1 - Task exists in Celery app

- [ ] **Test:** `test_aggregate_writes_to_metrics_aggregates_table`
  - **Status:** RED - Aggregation logic not implemented
  - **Verifies:** AC2 - Data written to correct table

- [ ] **Test:** `test_computes_count_for_traces`
  - **Status:** RED - Count computation not implemented
  - **Verifies:** AC3 - Count aggregation works

- [ ] **Test:** `test_computes_sum_min_max_avg`
  - **Status:** RED - Statistical functions not implemented
  - **Verifies:** AC3 - Sum, min, max, avg computed

- [ ] **Test:** `test_computes_percentiles_p50_p95_p99`
  - **Status:** RED - Percentile calculation not implemented
  - **Verifies:** AC4 - Percentiles calculated correctly

- [ ] **Test:** `test_aggregates_by_operation_type_dimension`
  - **Status:** RED - Dimension grouping not implemented
  - **Verifies:** AC5 - operation_type dimension works

- [ ] **Test:** `test_aggregates_by_model_dimension`
  - **Status:** RED - Model dimension not implemented
  - **Verifies:** AC5 - model dimension for LLM spans

- [ ] **Test:** `test_aggregates_by_kb_dimension`
  - **Status:** RED - KB dimension not implemented
  - **Verifies:** AC5 - kb_id dimension works

- [ ] **Test:** `test_supports_hour_granularity`
  - **Status:** RED - Granularity handling not implemented
  - **Verifies:** AC6 - Hourly buckets created

- [ ] **Test:** `test_supports_day_granularity`
  - **Status:** RED - Granularity handling not implemented
  - **Verifies:** AC6 - Daily buckets created

- [ ] **Test:** `test_supports_week_granularity`
  - **Status:** RED - Granularity handling not implemented
  - **Verifies:** AC6 - Weekly buckets created

- [ ] **Test:** `test_idempotent_upsert_updates_existing`
  - **Status:** RED - Upsert logic not implemented
  - **Verifies:** AC7 - Re-running updates, not duplicates

- [ ] **Test:** `test_backfill_processes_date_range`
  - **Status:** RED - Backfill not implemented
  - **Verifies:** AC8 - Backfill for missed periods

- [ ] **Test:** `test_empty_data_produces_no_aggregates`
  - **Status:** RED - Edge case handling not implemented
  - **Verifies:** AC10 - Empty data handled gracefully

### Integration Tests (4 tests)

**File:** `backend/tests/integration/test_metrics_aggregation_integration.py`

- [ ] **Test:** `test_hourly_aggregation_full_flow`
  - **Status:** RED - Full flow not implemented
  - **Verifies:** AC1-3 - End-to-end aggregation works

- [ ] **Test:** `test_aggregation_with_real_trace_data`
  - **Status:** RED - Integration not complete
  - **Verifies:** AC2-4 - Works with actual trace data

- [ ] **Test:** `test_beat_schedule_configured_correctly`
  - **Status:** RED - Beat schedule not configured
  - **Verifies:** AC1 - Celery beat schedule correct

- [ ] **Test:** `test_prometheus_metrics_exported`
  - **Status:** RED - Prometheus metrics not implemented
  - **Verifies:** AC9 - Job health metrics exported

---

## Data Factories Created

### Metrics Test Data Factories

**File:** `backend/tests/factories/observability_factory.py`

**Existing Exports (already available):**

- `create_trace(overrides?)` - Create trace with metrics
- `create_completed_trace(overrides?)` - Create completed trace
- `create_span(overrides?)` - Create span with metrics
- `create_llm_span(overrides?)` - Create LLM-type span
- `create_metrics_aggregate(overrides?)` - Create aggregate record

**New Factory Functions to Add:**

```python
def create_traces_for_aggregation(
    *,
    count: int = 10,
    operation_type: str | None = None,
    time_range_hours: int = 1,
    user_id: UUID | None = None,
    kb_id: UUID | None = None,
) -> list[dict[str, Any]]:
    """Create multiple traces suitable for aggregation testing.

    Args:
        count: Number of traces to create
        operation_type: Fixed operation type (random if None)
        time_range_hours: Spread traces across this many hours
        user_id: Fixed user ID (random if None)
        kb_id: Fixed KB ID (random if None)

    Returns:
        List of trace dictionaries
    """
    base_time = datetime.utcnow() - timedelta(hours=time_range_hours)
    traces = []
    for i in range(count):
        offset = timedelta(minutes=i * (time_range_hours * 60 // count))
        traces.append(create_completed_trace(
            operation_type=operation_type or fake.random_element(["chat", "search", "generation"]),
            started_at=base_time + offset,
            user_id=user_id or uuid4(),
            kb_id=kb_id or uuid4(),
            duration_ms=fake.random_int(min=100, max=5000),
            total_tokens=fake.random_int(min=100, max=2000),
        ))
    return traces


def create_llm_spans_for_aggregation(
    *,
    count: int = 10,
    model: str | None = None,
    trace_id: str | None = None,
) -> list[dict[str, Any]]:
    """Create multiple LLM spans for model-dimension aggregation testing."""
    spans = []
    for _ in range(count):
        spans.append(create_llm_span(
            trace_id=trace_id or generate_trace_id(),
            model=model or fake.random_element(["gpt-4", "gpt-3.5-turbo", "claude-3"]),
            duration_ms=fake.random_int(min=100, max=3000),
        ))
    return spans
```

**Example Usage:**

```python
from tests.factories import (
    create_traces_for_aggregation,
    create_llm_spans_for_aggregation,
    create_metrics_aggregate,
)

# Create traces for hour-long aggregation test
traces = create_traces_for_aggregation(
    count=50,
    operation_type="chat",
    time_range_hours=1,
)

# Create LLM spans for model breakdown
spans = create_llm_spans_for_aggregation(
    count=20,
    model="gpt-4",
)

# Verify existing aggregate
expected = create_metrics_aggregate(
    granularity="hour",
    metric_type="trace.duration_ms",
    dimension_type="operation_type",
    dimension_value="chat",
)
```

---

## Fixtures Created

### Aggregation Test Fixtures

**File:** `backend/tests/fixtures/aggregation_fixtures.py`

**Fixtures:**

- `populated_traces_table` - Table with trace data for aggregation
  - **Setup:** Insert 100 traces across 24 hours
  - **Provides:** Database session with data
  - **Cleanup:** Truncate traces table

- `aggregation_service` - Metrics aggregation service instance
  - **Setup:** Create service with test database
  - **Provides:** `MetricsAggregationService` instance
  - **Cleanup:** None (stateless)

- `mock_celery_task` - Mock Celery task context
  - **Setup:** Patch Celery task decorators
  - **Provides:** Mock task for testing
  - **Cleanup:** Restore original decorators

**Example Usage:**

```python
import pytest
from tests.fixtures.aggregation_fixtures import populated_traces_table

@pytest.fixture
async def populated_traces_table(test_db_session):
    """Populate traces table with test data."""
    from tests.factories import create_traces_for_aggregation
    from app.models.observability import Trace

    traces = create_traces_for_aggregation(count=100, time_range_hours=24)
    for trace_data in traces:
        trace = Trace(**trace_data)
        test_db_session.add(trace)
    await test_db_session.commit()
    yield test_db_session
    # Cleanup handled by test transaction rollback


async def test_hourly_aggregation_full_flow(populated_traces_table):
    from app.workers.metrics_aggregation_tasks import aggregate_observability_metrics

    result = await aggregate_observability_metrics("hour")
    assert result["metrics_created"] > 0
```

---

## Mock Requirements

### Celery Task Mock

**Target:** `@shared_task` decorator and task execution

**Mock Setup:**

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_celery_task(mocker):
    """Mock Celery task for unit testing."""
    mock_app = MagicMock()
    mocker.patch("celery.shared_task", return_value=lambda f: f)
    mocker.patch("app.workers.celery_app.app", mock_app)
    return mock_app
```

### Prometheus Metrics Mock

**Target:** Prometheus client metrics

**Mock Setup:**

```python
@pytest.fixture
def mock_prometheus_metrics(mocker):
    """Mock Prometheus metrics for testing."""
    mock_histogram = mocker.MagicMock()
    mock_counter = mocker.MagicMock()
    mock_gauge = mocker.MagicMock()

    mocker.patch("prometheus_client.Histogram", return_value=mock_histogram)
    mocker.patch("prometheus_client.Counter", return_value=mock_counter)
    mocker.patch("prometheus_client.Gauge", return_value=mock_gauge)

    return {
        "histogram": mock_histogram,
        "counter": mock_counter,
        "gauge": mock_gauge,
    }
```

### Database Time Mock

**Target:** `datetime.utcnow()` for deterministic bucket times

**Mock Setup:**

```python
from freezegun import freeze_time

@freeze_time("2025-12-15 10:30:00")
async def test_hour_bucket_truncation():
    """Test that bucket_time is truncated to hour."""
    result = await aggregate_observability_metrics("hour")
    assert result["bucket_time"] == datetime(2025, 12, 15, 10, 0, 0)
```

---

## Implementation Checklist

### Test: `test_aggregate_task_registered_in_celery`

**File:** `backend/tests/unit/test_metrics_aggregation.py`

**Tasks to make this test pass:**

- [ ] Create `backend/app/workers/metrics_aggregation_tasks.py`
- [ ] Import `shared_task` from Celery
- [ ] Define `aggregate_observability_metrics` task function
- [ ] Add `@shared_task` decorator
- [ ] Import task in `celery_app.py` for autodiscovery
- [ ] Run test: `pytest backend/tests/unit/test_metrics_aggregation.py::test_aggregate_task_registered_in_celery -v`
- [ ] Test passes (green phase)

---

### Test: `test_computes_count_for_traces`

**File:** `backend/tests/unit/test_metrics_aggregation.py`

**Tasks to make this test pass:**

- [ ] Create `backend/app/services/metrics_aggregation_service.py`
- [ ] Implement `aggregate_traces()` method
- [ ] Use SQL `COUNT(*)` for trace count
- [ ] Group by `date_trunc('hour', started_at)`
- [ ] Return count in result dictionary
- [ ] Run test: `pytest backend/tests/unit/test_metrics_aggregation.py::test_computes_count_for_traces -v`
- [ ] Test passes (green phase)

---

### Test: `test_computes_percentiles_p50_p95_p99`

**File:** `backend/tests/unit/test_metrics_aggregation.py`

**Tasks to make this test pass:**

- [ ] Use SQL `PERCENTILE_CONT(0.50)` for p50
- [ ] Use SQL `PERCENTILE_CONT(0.95)` for p95
- [ ] Use SQL `PERCENTILE_CONT(0.99)` for p99
- [ ] Use `WITHIN GROUP (ORDER BY duration_ms)` clause
- [ ] Store in `p50_value`, `p95_value`, `p99_value` columns
- [ ] Run test: `pytest backend/tests/unit/test_metrics_aggregation.py::test_computes_percentiles_p50_p95_p99 -v`
- [ ] Test passes (green phase)

---

### Test: `test_aggregates_by_operation_type_dimension`

**File:** `backend/tests/unit/test_metrics_aggregation.py`

**Tasks to make this test pass:**

- [ ] Add `dimension_type` parameter to aggregation
- [ ] Add `GROUP BY operation_type` when dimension is "operation_type"
- [ ] Store dimension value in `dimension_value` column
- [ ] Create separate aggregate row per dimension value
- [ ] Run test: `pytest backend/tests/unit/test_metrics_aggregation.py::test_aggregates_by_operation_type_dimension -v`
- [ ] Test passes (green phase)

---

### Test: `test_idempotent_upsert_updates_existing`

**File:** `backend/tests/unit/test_metrics_aggregation.py`

**Tasks to make this test pass:**

- [ ] Use `INSERT ... ON CONFLICT DO UPDATE` SQL pattern
- [ ] Define unique constraint on (bucket_time, granularity, metric_name, dimension_type, dimension_value)
- [ ] Update all metric columns on conflict
- [ ] Verify running twice produces same result
- [ ] Run test: `pytest backend/tests/unit/test_metrics_aggregation.py::test_idempotent_upsert_updates_existing -v`
- [ ] Test passes (green phase)

---

### Test: `test_backfill_processes_date_range`

**File:** `backend/tests/unit/test_metrics_aggregation.py`

**Tasks to make this test pass:**

- [ ] Add `start_time` and `end_time` parameters to task
- [ ] Implement `backfill_metrics()` function
- [ ] Iterate through each bucket in range
- [ ] Call aggregation for each bucket
- [ ] Return summary of buckets processed
- [ ] Run test: `pytest backend/tests/unit/test_metrics_aggregation.py::test_backfill_processes_date_range -v`
- [ ] Test passes (green phase)

---

### Test: `test_beat_schedule_configured_correctly`

**File:** `backend/tests/integration/test_metrics_aggregation_integration.py`

**Tasks to make this test pass:**

- [ ] Add hourly task to `celery_app.conf.beat_schedule`
- [ ] Configure `crontab(minute=5)` for hourly run
- [ ] Add daily task for day granularity at 1 AM
- [ ] Verify schedule configuration in tests
- [ ] Run test: `pytest backend/tests/integration/test_metrics_aggregation_integration.py::test_beat_schedule_configured_correctly -v`
- [ ] Test passes (green phase)

---

### Test: `test_prometheus_metrics_exported`

**File:** `backend/tests/integration/test_metrics_aggregation_integration.py`

**Tasks to make this test pass:**

- [ ] Import prometheus_client in task module
- [ ] Create `observability_aggregation_duration_seconds` Histogram
- [ ] Create `observability_aggregation_records_processed` Counter
- [ ] Create `observability_aggregation_last_success` Gauge
- [ ] Instrument task with metrics
- [ ] Run test: `pytest backend/tests/integration/test_metrics_aggregation_integration.py::test_prometheus_metrics_exported -v`
- [ ] Test passes (green phase)

---

## Running Tests

```bash
# Run all unit tests for metrics aggregation
pytest backend/tests/unit/test_metrics_aggregation.py -v

# Run integration tests
pytest backend/tests/integration/test_metrics_aggregation_integration.py -v

# Run with coverage
pytest backend/tests/unit/test_metrics_aggregation.py --cov=app/services/metrics_aggregation_service --cov=app/workers/metrics_aggregation_tasks --cov-report=term-missing

# Run specific test
pytest backend/tests/unit/test_metrics_aggregation.py::test_computes_percentiles_p50_p95_p99 -v

# Run with verbose SQL logging
pytest backend/tests/integration/test_metrics_aggregation_integration.py -v --log-cli-level=DEBUG

# Test Celery task registration
pytest backend/tests/unit/test_metrics_aggregation.py::test_aggregate_task_registered_in_celery -v
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

1. Create task file and register with Celery (AC1)
2. Implement basic count aggregation (AC3)
3. Add sum, min, max, avg computations (AC3)
4. Add percentile calculations (AC4)
5. Implement dimension grouping (AC5)
6. Add granularity support (AC6)
7. Implement idempotent upsert (AC7)
8. Add backfill capability (AC8)
9. Add Prometheus metrics (AC9)
10. Configure beat schedule

---

## Knowledge Base References Applied

- **data-factories.md** - Factory patterns for test data
- **test-quality.md** - Idempotent test design
- **ci-burn-in.md** - Celery task testing patterns

---

## Notes

- Use `freezegun` for deterministic datetime in tests
- Percentile functions require PostgreSQL (use test database)
- Celery beat requires Redis broker for scheduling
- Consider using `pytest-celery` for task testing
- Prometheus metrics follow existing convention in codebase

---

**Generated by BMad TEA Agent** - 2025-12-15
