"""Unit tests for Metrics Aggregation Service.

Story 9-13: Metrics Aggregation Worker
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.metrics_aggregation_service import (
    ALL_METRICS,
    CHAT_METRICS,
    DOCUMENT_METRICS,
    SPAN_METRICS,
    TRACE_METRICS,
    MetricsAggregationService,
)


class TestBucketBoundaries:
    """Test bucket boundary calculations."""

    def test_hour_boundaries(self):
        """Test hourly bucket boundary calculation."""
        service = MetricsAggregationService(MagicMock())

        # Reference time: 2024-01-15 14:35:22
        ref_time = datetime(2024, 1, 15, 14, 35, 22)
        start, end = service._get_bucket_boundaries("hour", ref_time)

        assert start == datetime(2024, 1, 15, 13, 0, 0)  # Previous complete hour
        assert end == datetime(2024, 1, 15, 14, 0, 0)

    def test_day_boundaries(self):
        """Test daily bucket boundary calculation."""
        service = MetricsAggregationService(MagicMock())

        ref_time = datetime(2024, 1, 15, 14, 35, 22)
        start, end = service._get_bucket_boundaries("day", ref_time)

        assert start == datetime(2024, 1, 14, 0, 0, 0)  # Previous complete day
        assert end == datetime(2024, 1, 15, 0, 0, 0)

    def test_week_boundaries(self):
        """Test weekly bucket boundary calculation."""
        service = MetricsAggregationService(MagicMock())

        # Wednesday Jan 17, 2024
        ref_time = datetime(2024, 1, 17, 14, 35, 22)
        start, end = service._get_bucket_boundaries("week", ref_time)

        # Week ends on Monday Jan 15 (start of this week)
        # Week starts on Monday Jan 8
        assert start == datetime(2024, 1, 8, 0, 0, 0)
        assert end == datetime(2024, 1, 15, 0, 0, 0)

    def test_invalid_granularity_raises_error(self):
        """Test that invalid granularity raises ValueError."""
        service = MetricsAggregationService(MagicMock())

        with pytest.raises(ValueError, match="Unknown granularity"):
            service._get_bucket_boundaries("invalid")  # type: ignore

    def test_hour_boundaries_at_midnight(self):
        """Test hourly boundaries when reference is at midnight."""
        service = MetricsAggregationService(MagicMock())

        ref_time = datetime(2024, 1, 15, 0, 15, 0)
        start, end = service._get_bucket_boundaries("hour", ref_time)

        assert start == datetime(2024, 1, 14, 23, 0, 0)  # Previous day's last hour
        assert end == datetime(2024, 1, 15, 0, 0, 0)


class TestMetricConfigurations:
    """Test metric configuration definitions."""

    def test_trace_metrics_defined(self):
        """Test trace metrics are properly defined."""
        assert len(TRACE_METRICS) >= 2

        # Check trace.count
        count_metric = next(
            m for m in TRACE_METRICS if m["metric_type"] == "trace.count"
        )
        assert count_metric["source_table"] == "observability.traces"
        assert count_metric["value_column"] is None  # Count only
        assert count_metric["dimension_type"] == "operation_type"

        # Check trace.duration_ms
        duration_metric = next(
            m for m in TRACE_METRICS if m["metric_type"] == "trace.duration_ms"
        )
        assert duration_metric["value_column"] == "duration_ms"

    def test_span_metrics_defined(self):
        """Test span/LLM metrics are properly defined."""
        assert len(SPAN_METRICS) >= 4

        # Check LLM metrics have proper filters
        for metric in SPAN_METRICS:
            assert "filter" in metric
            assert "span_type = 'llm'" in metric["filter"]
            assert metric["dimension_type"] == "model"

    def test_document_metrics_defined(self):
        """Test document event metrics are properly defined."""
        assert len(DOCUMENT_METRICS) >= 2

        for metric in DOCUMENT_METRICS:
            assert metric["source_table"] == "observability.document_events"
            assert metric["dimension_type"] == "event_type"

    def test_chat_metrics_defined(self):
        """Test chat metrics are properly defined."""
        assert len(CHAT_METRICS) >= 2

        for metric in CHAT_METRICS:
            assert metric["source_table"] == "observability.chat_messages"
            assert metric["dimension_type"] == "kb_id"

    def test_all_metrics_combined(self):
        """Test ALL_METRICS contains all metric types."""
        expected_count = (
            len(TRACE_METRICS)
            + len(SPAN_METRICS)
            + len(DOCUMENT_METRICS)
            + len(CHAT_METRICS)
        )
        assert len(ALL_METRICS) == expected_count


class TestAggregateMetric:
    """Test single metric aggregation."""

    @pytest.mark.asyncio
    async def test_aggregate_metric_executes_queries(self):
        """Test that aggregate_metric executes delete and insert queries."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = MetricsAggregationService(mock_session)

        metric_config = {
            "metric_type": "trace.count",
            "source_table": "observability.traces",
            "value_column": None,
            "dimension_column": "name",
            "dimension_type": "operation_type",
        }

        start_time = datetime(2024, 1, 15, 13, 0, 0)
        end_time = datetime(2024, 1, 15, 14, 0, 0)

        rows = await service.aggregate_metric(
            metric_config, "hour", start_time, end_time
        )

        # Should execute delete then insert
        assert mock_session.execute.call_count == 2
        assert rows == 5

    @pytest.mark.asyncio
    async def test_aggregate_metric_with_filter(self):
        """Test aggregation with extra filter condition."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = MetricsAggregationService(mock_session)

        metric_config = {
            "metric_type": "llm.call_count",
            "source_table": "observability.spans",
            "value_column": None,
            "dimension_column": "model",
            "dimension_type": "model",
            "filter": "span_type = 'llm'",
        }

        rows = await service.aggregate_metric(
            metric_config,
            "hour",
            datetime(2024, 1, 15, 13, 0, 0),
            datetime(2024, 1, 15, 14, 0, 0),
        )

        assert rows == 3

        # Verify the insert query includes the filter
        insert_call = mock_session.execute.call_args_list[1]
        query = str(insert_call[0][0])
        assert "span_type = 'llm'" in query


class TestAggregateAllMetrics:
    """Test aggregating all metrics."""

    @pytest.mark.asyncio
    async def test_aggregate_all_metrics_processes_all(self):
        """Test that all metrics are processed."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        service = MetricsAggregationService(mock_session)

        start_time = datetime(2024, 1, 15, 13, 0, 0)
        end_time = datetime(2024, 1, 15, 14, 0, 0)

        results = await service.aggregate_all_metrics("hour", start_time, end_time)

        # Should have results for all metrics
        assert len(results) == len(ALL_METRICS)

        # All should have been processed
        for _metric_type, rows in results.items():
            assert rows == 1  # Our mock returns 1 row

        # Session should be committed
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_aggregate_all_metrics_handles_errors(self):
        """Test that errors in one metric don't stop others."""
        mock_session = AsyncMock()

        call_count = [0]

        async def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 3:  # Third call fails (second metric's insert)
                raise Exception("Database error")
            result = MagicMock()
            result.rowcount = 1
            return result

        mock_session.execute = AsyncMock(side_effect=execute_side_effect)
        mock_session.commit = AsyncMock()

        service = MetricsAggregationService(mock_session)

        results = await service.aggregate_all_metrics(
            "hour",
            datetime(2024, 1, 15, 13, 0, 0),
            datetime(2024, 1, 15, 14, 0, 0),
        )

        # Should have results for all metrics, with -1 for the failed one
        assert len(results) == len(ALL_METRICS)

        # At least one should have failed
        failed_count = sum(1 for v in results.values() if v == -1)
        assert failed_count >= 1

    @pytest.mark.asyncio
    async def test_aggregate_all_metrics_uses_default_boundaries(self):
        """Test that default boundaries are used when times not provided."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        service = MetricsAggregationService(mock_session)

        with patch.object(service, "_get_bucket_boundaries") as mock_boundaries:
            mock_boundaries.return_value = (
                datetime(2024, 1, 15, 13, 0, 0),
                datetime(2024, 1, 15, 14, 0, 0),
            )

            await service.aggregate_all_metrics("hour")

            mock_boundaries.assert_called_once_with("hour")


class TestBackfill:
    """Test backfill functionality."""

    @pytest.mark.asyncio
    async def test_backfill_processes_each_bucket(self):
        """Test backfill processes each time bucket."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        service = MetricsAggregationService(mock_session)

        start_date = datetime(2024, 1, 15, 0, 0, 0)
        end_date = datetime(2024, 1, 15, 3, 0, 0)  # 3 hours

        result = await service.backfill("hour", start_date, end_date)

        assert result["granularity"] == "hour"
        assert result["buckets_processed"] == 3  # 3 hour buckets
        assert result["total_rows"] > 0
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_backfill_with_progress_callback(self):
        """Test backfill calls progress callback."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        service = MetricsAggregationService(mock_session)

        progress_calls = []

        def progress_callback(bucket, count, rows):
            progress_calls.append((bucket, count, rows))

        start_date = datetime(2024, 1, 15, 0, 0, 0)
        end_date = datetime(2024, 1, 15, 2, 0, 0)  # 2 hours

        await service.backfill("hour", start_date, end_date, progress_callback)

        assert len(progress_calls) == 2

    @pytest.mark.asyncio
    async def test_backfill_daily_granularity(self):
        """Test backfill with daily granularity."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        service = MetricsAggregationService(mock_session)

        start_date = datetime(2024, 1, 10, 0, 0, 0)
        end_date = datetime(2024, 1, 15, 0, 0, 0)  # 5 days

        result = await service.backfill("day", start_date, end_date)

        assert result["buckets_processed"] == 5

    @pytest.mark.asyncio
    async def test_backfill_records_bucket_errors(self):
        """Test backfill records errors when entire bucket fails."""
        mock_session = AsyncMock()

        bucket_count = [0]

        async def execute_side_effect(*args, **kwargs):
            bucket_count[0] += 1
            # Make all calls in second bucket fail (queries 21-40 for bucket 2)
            # Each bucket does 2 queries per metric (delete + insert) = 20 queries total
            if 21 <= bucket_count[0] <= 40:
                raise Exception("Database error")
            result = MagicMock()
            result.rowcount = 1
            return result

        mock_session.execute = AsyncMock(side_effect=execute_side_effect)
        mock_session.commit = AsyncMock()

        service = MetricsAggregationService(mock_session)

        start_date = datetime(2024, 1, 15, 0, 0, 0)
        end_date = datetime(2024, 1, 15, 3, 0, 0)  # 3 hours

        result = await service.backfill("hour", start_date, end_date)

        # All 3 buckets should be processed
        assert result["buckets_processed"] == 3

        # Total rows should be less than ideal due to errors
        # Bucket 1: 10 rows, Bucket 2: has errors, Bucket 3: 10 rows
        assert result["total_rows"] >= 10  # At least one bucket worked


class TestQueryGeneration:
    """Test SQL query generation for aggregations."""

    @pytest.mark.asyncio
    async def test_value_metric_includes_aggregations(self):
        """Test that value metrics include statistical aggregations."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = MetricsAggregationService(mock_session)

        metric_config = {
            "metric_type": "trace.duration_ms",
            "source_table": "observability.traces",
            "value_column": "duration_ms",
            "dimension_column": "name",
            "dimension_type": "operation_type",
        }

        await service.aggregate_metric(
            metric_config,
            "hour",
            datetime(2024, 1, 15, 13, 0, 0),
            datetime(2024, 1, 15, 14, 0, 0),
        )

        # Check insert query includes percentile functions
        insert_call = mock_session.execute.call_args_list[1]
        query = str(insert_call[0][0])
        assert "PERCENTILE_CONT(0.50)" in query
        assert "PERCENTILE_CONT(0.95)" in query
        assert "PERCENTILE_CONT(0.99)" in query

    @pytest.mark.asyncio
    async def test_count_only_metric_has_null_aggregations(self):
        """Test that count-only metrics have NULL value columns."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = MetricsAggregationService(mock_session)

        metric_config = {
            "metric_type": "trace.count",
            "source_table": "observability.traces",
            "value_column": None,
            "dimension_column": "name",
            "dimension_type": "operation_type",
        }

        await service.aggregate_metric(
            metric_config,
            "hour",
            datetime(2024, 1, 15, 13, 0, 0),
            datetime(2024, 1, 15, 14, 0, 0),
        )

        # Check insert query has NULL for count-only metrics
        insert_call = mock_session.execute.call_args_list[1]
        query = str(insert_call[0][0])
        assert "NULL::DOUBLE PRECISION AS sum_value" in query
        assert "PERCENTILE_CONT" not in query
