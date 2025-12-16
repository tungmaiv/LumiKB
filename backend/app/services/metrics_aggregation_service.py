"""Metrics Aggregation Service.

Story 9-13: Metrics Aggregation Worker

This service handles pre-aggregation of observability metrics into the
metrics_aggregates table for efficient dashboard queries.

Features:
- Statistical computations (count, sum, min, max, avg, percentiles)
- Multi-dimensional aggregation (operation_type, model, kb_id, user_id)
- Multiple granularities (hour, day, week)
- Idempotent UPSERT operations
- Backfill capability for missed periods
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Type definitions
GranularityType = Literal["hour", "day", "week"]
DimensionType = Literal[
    "operation_type", "model", "kb_id", "user_id", "event_type", "global"
]

# Metrics definitions
TRACE_METRICS = [
    {
        "metric_type": "trace.count",
        "source_table": "observability.traces",
        "value_column": None,  # Count only
        "dimension_column": "name",
        "dimension_type": "operation_type",
    },
    {
        "metric_type": "trace.duration_ms",
        "source_table": "observability.traces",
        "value_column": "duration_ms",
        "dimension_column": "name",
        "dimension_type": "operation_type",
    },
]

SPAN_METRICS = [
    {
        "metric_type": "llm.call_count",
        "source_table": "observability.spans",
        "value_column": None,  # Count only
        "dimension_column": "model",
        "dimension_type": "model",
        "filter": "span_type = 'llm'",
    },
    {
        "metric_type": "llm.latency_ms",
        "source_table": "observability.spans",
        "value_column": "duration_ms",
        "dimension_column": "model",
        "dimension_type": "model",
        "filter": "span_type = 'llm'",
    },
    {
        "metric_type": "llm.input_tokens",
        "source_table": "observability.spans",
        "value_column": "input_tokens",
        "dimension_column": "model",
        "dimension_type": "model",
        "filter": "span_type = 'llm'",
    },
    {
        "metric_type": "llm.output_tokens",
        "source_table": "observability.spans",
        "value_column": "output_tokens",
        "dimension_column": "model",
        "dimension_type": "model",
        "filter": "span_type = 'llm'",
    },
]

DOCUMENT_METRICS = [
    {
        "metric_type": "document.count",
        "source_table": "observability.document_events",
        "value_column": None,  # Count only
        "dimension_column": "event_type",
        "dimension_type": "event_type",
        "filter": "status = 'completed'",
    },
    {
        "metric_type": "document.duration_ms",
        "source_table": "observability.document_events",
        "value_column": "duration_ms",
        "dimension_column": "event_type",
        "dimension_type": "event_type",
        "filter": "status = 'completed'",
    },
]

CHAT_METRICS = [
    {
        "metric_type": "chat.message_count",
        "source_table": "observability.chat_messages",
        "value_column": None,  # Count only
        "dimension_column": "kb_id",
        "dimension_type": "kb_id",
        "filter": "role = 'assistant'",
    },
    {
        "metric_type": "chat.latency_ms",
        "source_table": "observability.chat_messages",
        "value_column": "latency_ms",
        "dimension_column": "kb_id",
        "dimension_type": "kb_id",
        "filter": "role = 'assistant'",
    },
]

ALL_METRICS = TRACE_METRICS + SPAN_METRICS + DOCUMENT_METRICS + CHAT_METRICS


class MetricsAggregationService:
    """Service for aggregating observability metrics."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    def _get_bucket_boundaries(
        self,
        granularity: GranularityType,
        reference_time: datetime | None = None,
    ) -> tuple[datetime, datetime]:
        """Calculate time bucket boundaries for aggregation.

        Args:
            granularity: Aggregation granularity (hour, day, week)
            reference_time: Reference point for bucket calculation

        Returns:
            Tuple of (start_time, end_time) for the bucket
        """
        now = reference_time or datetime.utcnow()

        if granularity == "hour":
            # Previous complete hour
            end_time = now.replace(minute=0, second=0, microsecond=0)
            start_time = end_time - timedelta(hours=1)
        elif granularity == "day":
            # Previous complete day
            end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_time = end_time - timedelta(days=1)
        elif granularity == "week":
            # Previous complete week (Monday to Sunday)
            days_since_monday = now.weekday()
            end_time = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=days_since_monday)
            start_time = end_time - timedelta(weeks=1)
        else:
            raise ValueError(f"Unknown granularity: {granularity}")

        return start_time, end_time

    async def aggregate_metric(
        self,
        metric_config: dict[str, Any],
        granularity: GranularityType,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """Aggregate a single metric for a time period.

        Args:
            metric_config: Metric configuration
            granularity: Aggregation granularity
            start_time: Period start time
            end_time: Period end time

        Returns:
            Number of rows affected
        """
        metric_type = metric_config["metric_type"]
        dimension_type = metric_config["dimension_type"]

        # Use simpler insert approach to avoid conflict issues
        source_table = metric_config["source_table"]
        value_column = metric_config.get("value_column")
        dimension_column = metric_config["dimension_column"]
        extra_filter = metric_config.get("filter", "TRUE")

        # Determine time column
        time_column = "timestamp"

        # Build dimension expression
        if dimension_type == "kb_id":
            dimension_expr = f"COALESCE({dimension_column}::TEXT, 'global')"
        else:
            dimension_expr = f"COALESCE({dimension_column}::TEXT, 'unknown')"

        # First delete existing aggregates for this bucket/metric/granularity
        delete_query = text("""
            DELETE FROM observability.metrics_aggregates
            WHERE bucket = :bucket_time
              AND metric_type = :metric_type
              AND dimensions->>'granularity' = :granularity
        """)

        await self.session.execute(
            delete_query,
            {
                "bucket_time": start_time,
                "metric_type": metric_type,
                "granularity": granularity,
            },
        )

        # Build value expressions
        if value_column:
            value_expressions = f"""
                SUM({value_column})::DOUBLE PRECISION AS sum_value,
                MIN({value_column})::DOUBLE PRECISION AS min_value,
                MAX({value_column})::DOUBLE PRECISION AS max_value,
                AVG({value_column})::DOUBLE PRECISION AS avg_value,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {value_column})::DOUBLE PRECISION AS p50_value,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {value_column})::DOUBLE PRECISION AS p95_value,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY {value_column})::DOUBLE PRECISION AS p99_value
            """
        else:
            value_expressions = """
                NULL::DOUBLE PRECISION AS sum_value,
                NULL::DOUBLE PRECISION AS min_value,
                NULL::DOUBLE PRECISION AS max_value,
                NULL::DOUBLE PRECISION AS avg_value,
                NULL::DOUBLE PRECISION AS p50_value,
                NULL::DOUBLE PRECISION AS p95_value,
                NULL::DOUBLE PRECISION AS p99_value
            """

        # Then insert new aggregates
        insert_query = text(f"""
            INSERT INTO observability.metrics_aggregates (
                bucket, metric_type, dimensions, count, sum_value,
                min_value, max_value, avg_value, p50_value, p95_value, p99_value
            )
            SELECT
                :bucket_time AS bucket,
                :metric_type AS metric_type,
                jsonb_build_object(
                    'granularity', :granularity,
                    'dimension_type', :dimension_type,
                    'dimension_value', {dimension_expr}
                ) AS dimensions,
                COUNT(*)::BIGINT AS count,
                {value_expressions}
            FROM {source_table}
            WHERE {time_column} >= :start_time
              AND {time_column} < :end_time
              AND {extra_filter}
            GROUP BY {dimension_expr}
        """)

        result = await self.session.execute(
            insert_query,
            {
                "bucket_time": start_time,
                "metric_type": metric_type,
                "granularity": granularity,
                "dimension_type": dimension_type,
                "start_time": start_time,
                "end_time": end_time,
            },
        )

        return result.rowcount

    async def aggregate_all_metrics(
        self,
        granularity: GranularityType,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, int]:
        """Aggregate all metrics for a time period.

        Args:
            granularity: Aggregation granularity
            start_time: Period start time (defaults to previous period)
            end_time: Period end time (defaults to previous period)

        Returns:
            Dict mapping metric_type to rows affected
        """
        if start_time is None or end_time is None:
            start_time, end_time = self._get_bucket_boundaries(granularity)

        logger.info(
            f"Starting metrics aggregation: granularity={granularity}, "
            f"start={start_time}, end={end_time}"
        )

        results: dict[str, int] = {}
        total_rows = 0

        for metric_config in ALL_METRICS:
            metric_type = metric_config["metric_type"]
            try:
                rows = await self.aggregate_metric(
                    metric_config, granularity, start_time, end_time
                )
                results[metric_type] = rows
                total_rows += rows
                logger.debug(f"Aggregated {metric_type}: {rows} rows")
            except Exception as e:
                logger.error(f"Error aggregating {metric_type}: {e}")
                results[metric_type] = -1

        await self.session.commit()

        logger.info(
            f"Completed aggregation: {total_rows} total rows across {len(ALL_METRICS)} metrics"
        )
        return results

    async def backfill(
        self,
        granularity: GranularityType,
        start_date: datetime,
        end_date: datetime,
        progress_callback: Any | None = None,
    ) -> dict[str, Any]:
        """Backfill aggregations for a date range.

        Args:
            granularity: Aggregation granularity
            start_date: Start of backfill range
            end_date: End of backfill range
            progress_callback: Optional callback for progress updates

        Returns:
            Summary of backfill results
        """
        logger.info(f"Starting backfill: {granularity} from {start_date} to {end_date}")

        # Calculate bucket size
        if granularity == "hour":
            delta = timedelta(hours=1)
        elif granularity == "day":
            delta = timedelta(days=1)
        elif granularity == "week":
            delta = timedelta(weeks=1)
        else:
            raise ValueError(f"Unknown granularity: {granularity}")

        # Process each bucket
        current = start_date
        buckets_processed = 0
        total_rows = 0
        errors: list[str] = []

        while current < end_date:
            bucket_end = current + delta
            try:
                results = await self.aggregate_all_metrics(
                    granularity, current, bucket_end
                )
                rows = sum(v for v in results.values() if v > 0)
                total_rows += rows
                buckets_processed += 1

                if progress_callback:
                    progress_callback(current, buckets_processed, total_rows)

                logger.debug(f"Backfilled bucket {current}: {rows} rows")
            except Exception as e:
                logger.error(f"Error backfilling bucket {current}: {e}")
                errors.append(f"{current}: {e!s}")

            current = bucket_end

        return {
            "granularity": granularity,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "buckets_processed": buckets_processed,
            "total_rows": total_rows,
            "errors": errors,
        }


async def get_metrics_aggregation_service(
    session: AsyncSession,
) -> MetricsAggregationService:
    """Factory function for MetricsAggregationService.

    Args:
        session: Async SQLAlchemy session

    Returns:
        Configured MetricsAggregationService instance
    """
    return MetricsAggregationService(session)
