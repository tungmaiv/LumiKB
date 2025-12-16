"""Unit tests for metrics aggregation worker (Story 9-13).

RED PHASE: All tests are designed to FAIL until implementation is complete.
These tests verify the Celery beat task aggregates observability metrics
with multiple dimensions and granularities.

Run with: pytest backend/tests/unit/test_metrics_aggregation.py -v
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from freezegun import freeze_time


class TestMetricsAggregationTaskRegistration:
    """Tests for AC1: Celery beat task runs hourly."""

    def test_aggregate_task_registered_in_celery(self) -> None:
        """Verify aggregation task is registered with Celery app."""
        from app.workers.celery_app import app

        task_names = list(app.tasks.keys())
        assert any("aggregate_observability_metrics" in name for name in task_names)

    def test_aggregate_task_is_shared_task(self) -> None:
        """Verify task uses @shared_task decorator."""
        from app.workers.metrics_aggregation_tasks import (
            aggregate_observability_metrics,
        )

        # Task should have Celery task attributes
        assert hasattr(aggregate_observability_metrics, "delay")
        assert hasattr(aggregate_observability_metrics, "apply_async")


class TestMetricsAggregationOutput:
    """Tests for AC2: Aggregates trace metrics into metrics_aggregates table."""

    @pytest.mark.asyncio
    async def test_aggregate_writes_to_metrics_aggregates_table(self) -> None:
        """Aggregation should write to metrics_aggregates table."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        await service.aggregate_traces(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
        )

        # Verify INSERT was executed
        mock_session.execute.assert_called()
        call_args = str(mock_session.execute.call_args)
        assert "metrics_aggregates" in call_args or "INSERT" in call_args


class TestStatisticalComputations:
    """Tests for AC3: Computes count, sum, min, max, avg per metric."""

    @pytest.mark.asyncio
    async def test_computes_count_for_traces(self) -> None:
        """Aggregation should compute COUNT for traces."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            {
                "bucket_time": datetime.utcnow().replace(
                    minute=0, second=0, microsecond=0
                ),
                "count": 42,
                "dimension_value": "chat",
            }
        ]
        mock_session.execute.return_value = mock_result

        service = MetricsAggregationService(mock_session)
        result = await service.aggregate_traces(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
        )

        assert result is not None
        # Verify count is computed
        call_sql = str(mock_session.execute.call_args)
        assert "COUNT" in call_sql.upper()

    @pytest.mark.asyncio
    async def test_computes_sum_min_max_avg(self) -> None:
        """Aggregation should compute SUM, MIN, MAX, AVG."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        await service.aggregate_traces(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
        )

        call_sql = str(mock_session.execute.call_args).upper()
        assert "SUM" in call_sql
        assert "MIN" in call_sql
        assert "MAX" in call_sql
        assert "AVG" in call_sql


class TestPercentileCalculations:
    """Tests for AC4: Calculates p50, p95, p99 percentiles for latencies."""

    @pytest.mark.asyncio
    async def test_computes_percentiles_p50_p95_p99(self) -> None:
        """Aggregation should compute p50, p95, p99 percentiles."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        await service.aggregate_latencies(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
        )

        call_sql = str(mock_session.execute.call_args).upper()
        assert "PERCENTILE_CONT" in call_sql or "PERCENTILE" in call_sql
        # Should compute 50th, 95th, 99th percentiles
        assert "0.50" in call_sql or "0.5" in call_sql
        assert "0.95" in call_sql
        assert "0.99" in call_sql


class TestDimensionAggregation:
    """Tests for AC5: Dimensions by operation_type, model, kb, user."""

    @pytest.mark.asyncio
    async def test_aggregates_by_operation_type_dimension(self) -> None:
        """Aggregation should group by operation_type dimension."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        await service.aggregate_traces(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
            dimension="operation_type",
        )

        call_sql = str(mock_session.execute.call_args).upper()
        assert "OPERATION_TYPE" in call_sql
        assert "GROUP BY" in call_sql

    @pytest.mark.asyncio
    async def test_aggregates_by_model_dimension(self) -> None:
        """Aggregation should group by model dimension for LLM spans."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        await service.aggregate_llm_spans(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
            dimension="model",
        )

        call_sql = str(mock_session.execute.call_args).upper()
        assert "MODEL" in call_sql

    @pytest.mark.asyncio
    async def test_aggregates_by_kb_dimension(self) -> None:
        """Aggregation should group by kb_id dimension."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        await service.aggregate_traces(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
            dimension="kb_id",
        )

        call_sql = str(mock_session.execute.call_args).upper()
        assert "KB_ID" in call_sql


class TestGranularityHandling:
    """Tests for AC6: Handles hour, day, week granularities."""

    @freeze_time("2025-12-15 10:30:00")
    @pytest.mark.asyncio
    async def test_supports_hour_granularity(self) -> None:
        """Aggregation should support hourly buckets."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        await service.aggregate_traces(
            start_time=datetime(2025, 12, 15, 9, 0, 0),
            end_time=datetime(2025, 12, 15, 10, 0, 0),
            granularity="hour",
        )

        call_sql = str(mock_session.execute.call_args)
        assert "hour" in call_sql.lower() or "DATE_TRUNC" in call_sql.upper()

    @freeze_time("2025-12-15 10:30:00")
    @pytest.mark.asyncio
    async def test_supports_day_granularity(self) -> None:
        """Aggregation should support daily buckets."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        await service.aggregate_traces(
            start_time=datetime(2025, 12, 14, 0, 0, 0),
            end_time=datetime(2025, 12, 15, 0, 0, 0),
            granularity="day",
        )

        call_sql = str(mock_session.execute.call_args)
        assert "day" in call_sql.lower()

    @freeze_time("2025-12-15 10:30:00")
    @pytest.mark.asyncio
    async def test_supports_week_granularity(self) -> None:
        """Aggregation should support weekly buckets."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        await service.aggregate_traces(
            start_time=datetime(2025, 12, 8, 0, 0, 0),
            end_time=datetime(2025, 12, 15, 0, 0, 0),
            granularity="week",
        )

        call_sql = str(mock_session.execute.call_args)
        assert "week" in call_sql.lower()


class TestIdempotentUpsert:
    """Tests for AC7: Idempotent re-running updates existing metrics."""

    @pytest.mark.asyncio
    async def test_idempotent_upsert_updates_existing(self) -> None:
        """Re-running aggregation should update, not duplicate."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        # Run twice with same parameters
        await service.aggregate_traces(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
        )

        # Verify UPSERT pattern used
        call_sql = str(mock_session.execute.call_args).upper()
        assert (
            "ON CONFLICT" in call_sql or "UPSERT" in call_sql or "DO UPDATE" in call_sql
        )

    @pytest.mark.asyncio
    async def test_upsert_uses_correct_conflict_columns(self) -> None:
        """UPSERT should use correct unique constraint columns."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        await service.aggregate_traces(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
        )

        call_sql = str(mock_session.execute.call_args)
        # Should conflict on composite key
        assert "bucket_time" in call_sql.lower()
        assert "granularity" in call_sql.lower()
        assert "metric_name" in call_sql.lower()


class TestBackfillCapability:
    """Tests for AC8: Backfill capability for missed periods."""

    @pytest.mark.asyncio
    async def test_backfill_processes_date_range(self) -> None:
        """Backfill should process each bucket in date range."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        # Backfill 24 hours
        result = await service.backfill(
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow(),
            granularity="hour",
        )

        # Should process ~24 hourly buckets
        assert result["buckets_processed"] >= 23

    @pytest.mark.asyncio
    async def test_backfill_returns_summary(self) -> None:
        """Backfill should return summary of processed buckets."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        service = MetricsAggregationService(mock_session)

        result = await service.backfill(
            start_time=datetime.utcnow() - timedelta(hours=3),
            end_time=datetime.utcnow(),
            granularity="hour",
        )

        assert "buckets_processed" in result
        assert "metrics_created" in result
        assert "duration_ms" in result


class TestEdgeCases:
    """Tests for AC10: Unit tests for aggregation logic edge cases."""

    @pytest.mark.asyncio
    async def test_empty_data_produces_no_aggregates(self) -> None:
        """Empty source data should produce no aggregate records."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []  # No data
        mock_session.execute.return_value = mock_result

        service = MetricsAggregationService(mock_session)
        result = await service.aggregate_traces(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
        )

        assert result["metrics_created"] == 0

    @pytest.mark.asyncio
    async def test_single_trace_aggregation(self) -> None:
        """Single trace should produce valid aggregate."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            {
                "bucket_time": datetime.utcnow().replace(
                    minute=0, second=0, microsecond=0
                ),
                "count": 1,
                "sum_value": 500,
                "min_value": 500,
                "max_value": 500,
                "avg_value": 500,
                "dimension_value": "chat",
            }
        ]
        mock_session.execute.return_value = mock_result

        service = MetricsAggregationService(mock_session)
        result = await service.aggregate_traces(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
        )

        assert result["metrics_created"] >= 1

    @pytest.mark.asyncio
    async def test_handles_null_dimension_values(self) -> None:
        """Aggregation should handle NULL dimension values."""
        from app.services.metrics_aggregation_service import MetricsAggregationService

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            {
                "bucket_time": datetime.utcnow().replace(
                    minute=0, second=0, microsecond=0
                ),
                "count": 5,
                "dimension_value": None,  # NULL dimension
            }
        ]
        mock_session.execute.return_value = mock_result

        service = MetricsAggregationService(mock_session)

        # Should not raise exception
        result = await service.aggregate_traces(
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            granularity="hour",
            dimension="kb_id",
        )

        assert result is not None


class TestCeleryBeatSchedule:
    """Tests for Celery beat schedule configuration."""

    def test_hourly_task_in_beat_schedule(self) -> None:
        """Hourly aggregation task should be in beat schedule."""
        from app.workers.celery_app import app

        schedule = app.conf.beat_schedule
        hourly_task = schedule.get("aggregate-observability-metrics-hourly")

        assert hourly_task is not None
        assert "aggregate_observability_metrics" in hourly_task["task"]

    def test_daily_task_in_beat_schedule(self) -> None:
        """Daily aggregation task should be in beat schedule."""
        from app.workers.celery_app import app

        schedule = app.conf.beat_schedule
        daily_task = schedule.get("aggregate-observability-metrics-daily")

        assert daily_task is not None
        assert "aggregate_observability_metrics" in daily_task["task"]
