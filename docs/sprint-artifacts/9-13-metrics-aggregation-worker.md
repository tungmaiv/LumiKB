# Story 9-13: Metrics Aggregation Worker

Status: ready-for-dev

## Story

As an **Admin user**,
I want observability metrics to be pre-aggregated on a schedule,
so that dashboard queries are fast and don't impact database performance during high load.

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

## Tasks / Subtasks

- [ ] Task 1: Create Celery beat schedule (AC: 1)
  - [ ] Add aggregation task to `backend/app/workers/celery_app.py`
  - [ ] Configure hourly schedule in beat schedule
  - [ ] Add task to Celery worker imports

- [ ] Task 2: Implement base aggregation task (AC: 2)
  - [ ] Create `backend/app/workers/metrics_aggregation_tasks.py`
  - [ ] Implement `aggregate_observability_metrics` task
  - [ ] Accept time range parameters for flexibility
  - [ ] Default to previous hour when no params

- [ ] Task 3: Implement statistical computations (AC: 3, 4)
  - [ ] Compute count for each metric
  - [ ] Compute sum, min, max, avg values
  - [ ] Implement percentile calculations (p50, p95, p99)
  - [ ] Use SQL window functions or Python computation

- [ ] Task 4: Implement dimension aggregation (AC: 5)
  - [ ] Aggregate by operation_type dimension
  - [ ] Aggregate by model dimension (for LLM spans)
  - [ ] Aggregate by kb_id dimension
  - [ ] Aggregate by user_id dimension
  - [ ] Support NULL dimension for global aggregates

- [ ] Task 5: Implement granularity handling (AC: 6)
  - [ ] Support "hour" granularity (primary)
  - [ ] Support "day" granularity (roll-up)
  - [ ] Support "week" granularity (roll-up)
  - [ ] Truncate bucket_time appropriately

- [ ] Task 6: Implement idempotency (AC: 7)
  - [ ] Use UPSERT (ON CONFLICT UPDATE) for metrics_aggregates
  - [ ] Match on (bucket_time, granularity, metric_name, dimension_type, dimension_value)
  - [ ] Re-running task updates existing records

- [ ] Task 7: Implement backfill capability (AC: 8)
  - [ ] Add `backfill_metrics` management command or endpoint
  - [ ] Accept start_date and end_date parameters
  - [ ] Process each hour/day in the range
  - [ ] Show progress during backfill

- [ ] Task 8: Add Prometheus metrics (AC: 9)
  - [ ] Export `observability_aggregation_duration_seconds` histogram
  - [ ] Export `observability_aggregation_records_processed` counter
  - [ ] Export `observability_aggregation_last_success` gauge
  - [ ] Export `observability_aggregation_errors_total` counter

- [ ] Task 9: Define metrics to aggregate
  - [ ] `trace.count` - trace count by operation type
  - [ ] `trace.duration_ms` - trace duration stats
  - [ ] `trace.tokens` - token usage stats
  - [ ] `trace.cost_usd` - cost stats
  - [ ] `llm.latency_ms` - LLM call latency
  - [ ] `document.processing_time_ms` - document processing time
  - [ ] `chat.response_time_ms` - chat response time

- [ ] Task 10: Write tests (AC: 10)
  - [ ] Unit tests for aggregation logic
  - [ ] Test percentile calculations
  - [ ] Test dimension grouping
  - [ ] Test idempotency (run twice, verify same result)
  - [ ] Test backfill functionality
  - [ ] Integration test with real data

## Dev Notes

### Learnings from Previous Story

**Story 9-10 (Document Timeline UI)** established key patterns:
- **Step-Specific Metrics:** Different metrics per step type (parse: pages, chunk: count, embed: vectors) - similar pattern for metrics by dimension
- **Duration Formatting:** Human-readable duration utilities - reuse for aggregation display
- **Source:** [stories/9-10-document-timeline-ui.md#Step-Specific Metrics]

**Story 9-6 (LiteLLM Integration Hooks)** established:
- **Fire-and-Forget Telemetry:** Async non-blocking pattern - same pattern for aggregation to avoid blocking beat scheduler
- **Token Counting:** prompt_tokens, completion_tokens tracking - source data for metrics aggregation

### Dependencies

- **Story 9-1 (Observability Schema):** `metrics_aggregates` hypertable must exist in TimescaleDB schema
- **Story 9-2 (PostgreSQL Provider):** Raw trace/span data must be persisted for aggregation queries
- **Story 9-4, 9-5, 9-6 (Instrumentation):** Source data (traces, spans, document_events, chat_messages) must be populated

### Architecture Patterns

- **Celery Beat Pattern:** Scheduled task execution
- **Idempotent Aggregation:** Safe to re-run without duplicate data
- **Multi-Dimensional:** Single aggregation run produces multiple dimension slices
- **Roll-Up Pattern:** Hour → Day → Week granularity roll-ups

### Metrics to Aggregate

| Metric Name | Source Table | Aggregations | Dimensions |
|-------------|--------------|--------------|------------|
| `trace.count` | traces | count | operation_type |
| `trace.duration_ms` | traces | avg, p50, p95, p99 | operation_type |
| `trace.tokens` | traces | sum, avg | operation_type |
| `trace.cost_usd` | traces | sum | operation_type |
| `llm.call_count` | spans (type=llm) | count | model |
| `llm.latency_ms` | spans (type=llm) | avg, p50, p95, p99 | model |
| `llm.tokens` | spans (type=llm) | sum | model |
| `document.count` | document_events | count | event_type |
| `document.duration_ms` | document_events | avg, p50, p95 | event_type |
| `chat.messages` | chat_messages | count | kb_id |
| `chat.response_time_ms` | chat_messages | avg, p95 | kb_id |

### SQL Aggregation Example

```sql
-- Hourly trace metrics aggregation
INSERT INTO observability.metrics_aggregates (
    bucket_time, granularity, metric_name, dimension_type, dimension_value,
    count, sum_value, min_value, max_value, avg_value, p50_value, p95_value, p99_value
)
SELECT
    date_trunc('hour', started_at) AS bucket_time,
    'hour' AS granularity,
    'trace.duration_ms' AS metric_name,
    'operation_type' AS dimension_type,
    operation_type AS dimension_value,
    COUNT(*) AS count,
    SUM(duration_ms) AS sum_value,
    MIN(duration_ms) AS min_value,
    MAX(duration_ms) AS max_value,
    AVG(duration_ms) AS avg_value,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) AS p50_value,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_value,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) AS p99_value
FROM observability.traces
WHERE started_at >= %(start_time)s AND started_at < %(end_time)s
  AND status = 'success'
GROUP BY date_trunc('hour', started_at), operation_type
ON CONFLICT (bucket_time, granularity, metric_name, dimension_type, dimension_value)
DO UPDATE SET
    count = EXCLUDED.count,
    sum_value = EXCLUDED.sum_value,
    min_value = EXCLUDED.min_value,
    max_value = EXCLUDED.max_value,
    avg_value = EXCLUDED.avg_value,
    p50_value = EXCLUDED.p50_value,
    p95_value = EXCLUDED.p95_value,
    p99_value = EXCLUDED.p99_value;
```

### Celery Beat Schedule

```python
# backend/app/workers/celery_app.py
app.conf.beat_schedule = {
    # ... existing tasks ...
    'aggregate-observability-metrics-hourly': {
        'task': 'app.workers.metrics_aggregation_tasks.aggregate_observability_metrics',
        'schedule': crontab(minute=5),  # 5 minutes past every hour
        'args': ('hour',),
    },
    'aggregate-observability-metrics-daily': {
        'task': 'app.workers.metrics_aggregation_tasks.aggregate_observability_metrics',
        'schedule': crontab(hour=1, minute=0),  # 1 AM daily
        'args': ('day',),
    },
}
```

### Source Tree Components

- `backend/app/workers/metrics_aggregation_tasks.py` - Aggregation task
- `backend/app/workers/celery_app.py` - Beat schedule configuration
- `backend/app/services/metrics_aggregation_service.py` - Business logic
- `backend/tests/unit/test_metrics_aggregation.py` - Unit tests
- `backend/tests/integration/test_metrics_aggregation_integration.py` - Integration tests

### Testing Standards

- Mock datetime for deterministic bucket times
- Use factory patterns for test data creation
- Test boundary conditions (empty data, single record)
- Verify idempotency with duplicate runs

### Project Structure Notes

- Follows existing Celery task patterns
- Uses existing database session patterns
- Prometheus metrics follow existing convention

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#Phase 4: Advanced Features - Story 9-13 Metrics Aggregation Worker]
- [Source: docs/epics/epic-9-observability.md#Phase 4: Advanced Features (18 points)]
- [Source: docs/architecture.md#monitoring] - Architecture monitoring stack documentation
- [Source: docs/testing-guideline.md] - Testing standards for Celery tasks
- [Source: backend/app/workers/celery_app.py] - Existing beat schedule pattern
- [Source: backend/app/workers/outbox_tasks.py] - Existing scheduled task pattern

## Dev Agent Record

### Context Reference

- [9-13-metrics-aggregation-worker.context.xml](./9-13-metrics-aggregation-worker.context.xml)

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

### File List
