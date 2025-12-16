"""Celery tasks for metrics aggregation.

Story 9-13: Metrics Aggregation Worker

Scheduled tasks for pre-aggregating observability metrics into the
metrics_aggregates table for efficient dashboard queries.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta

from celery import shared_task

from app.core.database import get_async_session_context
from app.services.metrics_aggregation_service import MetricsAggregationService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.workers.metrics_aggregation_tasks.aggregate_observability_metrics",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def aggregate_observability_metrics(
    self,  # noqa: ARG001 - required by bind=True for retry capability
    granularity: str = "hour",
    start_time_iso: str | None = None,
    end_time_iso: str | None = None,
) -> dict:
    """Aggregate observability metrics for a time period.

    This task is scheduled to run:
    - Hourly: 5 minutes past every hour
    - Daily: 1 AM UTC

    Args:
        granularity: Aggregation granularity ('hour', 'day', 'week')
        start_time_iso: Optional ISO format start time
        end_time_iso: Optional ISO format end time

    Returns:
        Dict with aggregation results
    """
    task_start = time.time()
    logger.info(f"Starting metrics aggregation task: granularity={granularity}")

    # Parse times if provided
    start_time = datetime.fromisoformat(start_time_iso) if start_time_iso else None
    end_time = datetime.fromisoformat(end_time_iso) if end_time_iso else None

    # Run async aggregation
    try:
        result = asyncio.get_event_loop().run_until_complete(
            _run_aggregation(granularity, start_time, end_time)
        )
    except RuntimeError:
        # No event loop running - create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _run_aggregation(granularity, start_time, end_time)
            )
        finally:
            loop.close()

    duration = time.time() - task_start

    logger.info(
        f"Completed metrics aggregation: duration={duration:.2f}s, "
        f"metrics_aggregated={len(result)}"
    )

    return {
        "status": "success",
        "granularity": granularity,
        "duration_seconds": duration,
        "metrics": result,
    }


async def _run_aggregation(
    granularity: str,
    start_time: datetime | None,
    end_time: datetime | None,
) -> dict[str, int]:
    """Run the aggregation using async context.

    Args:
        granularity: Aggregation granularity
        start_time: Optional start time
        end_time: Optional end time

    Returns:
        Dict mapping metric_type to rows affected
    """
    async with get_async_session_context() as session:
        service = MetricsAggregationService(session)
        return await service.aggregate_all_metrics(
            granularity,  # type: ignore
            start_time,
            end_time,
        )


@shared_task(
    bind=True,
    name="app.workers.metrics_aggregation_tasks.backfill_metrics",
    time_limit=3600,  # 1 hour max for backfill
    soft_time_limit=3300,  # 55 minutes soft limit
)
def backfill_metrics(
    self,
    granularity: str,
    start_date_iso: str,
    end_date_iso: str,
) -> dict:
    """Backfill metrics aggregations for a date range.

    Use this for:
    - Initial data population
    - Recovery from missed aggregation periods
    - Re-aggregating after schema changes

    Args:
        granularity: Aggregation granularity ('hour', 'day', 'week')
        start_date_iso: ISO format start date
        end_date_iso: ISO format end date

    Returns:
        Dict with backfill results
    """
    task_start = time.time()
    start_date = datetime.fromisoformat(start_date_iso)
    end_date = datetime.fromisoformat(end_date_iso)

    logger.info(
        f"Starting backfill task: granularity={granularity}, "
        f"start={start_date}, end={end_date}"
    )

    def progress_callback(bucket: datetime, count: int, rows: int) -> None:
        """Update task state with progress."""
        self.update_state(
            state="PROGRESS",
            meta={
                "current_bucket": bucket.isoformat(),
                "buckets_processed": count,
                "total_rows": rows,
            },
        )

    # Run async backfill
    try:
        result = asyncio.get_event_loop().run_until_complete(
            _run_backfill(granularity, start_date, end_date, progress_callback)
        )
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _run_backfill(granularity, start_date, end_date, progress_callback)
            )
        finally:
            loop.close()

    duration = time.time() - task_start
    result["duration_seconds"] = duration

    logger.info(
        f"Completed backfill: duration={duration:.2f}s, "
        f"buckets={result['buckets_processed']}, rows={result['total_rows']}"
    )

    return result


async def _run_backfill(
    granularity: str,
    start_date: datetime,
    end_date: datetime,
    progress_callback,
) -> dict:
    """Run the backfill using async context.

    Args:
        granularity: Aggregation granularity
        start_date: Start of backfill range
        end_date: End of backfill range
        progress_callback: Callback for progress updates

    Returns:
        Backfill results summary
    """
    async with get_async_session_context() as session:
        service = MetricsAggregationService(session)
        return await service.backfill(
            granularity,  # type: ignore
            start_date,
            end_date,
            progress_callback,
        )


@shared_task(
    name="app.workers.metrics_aggregation_tasks.rollup_daily_to_weekly",
)
def rollup_daily_to_weekly() -> dict:
    """Roll up daily aggregates to weekly granularity.

    Runs weekly on Mondays to create week-level aggregates
    from daily data.

    Returns:
        Dict with rollup results
    """
    task_start = time.time()
    logger.info("Starting weekly rollup task")

    # Calculate previous week boundaries
    now = datetime.utcnow()
    days_since_monday = now.weekday()
    week_end = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=days_since_monday
    )
    week_start = week_end - timedelta(weeks=1)

    # Run aggregation for the week
    try:
        result = asyncio.get_event_loop().run_until_complete(
            _run_aggregation("week", week_start, week_end)
        )
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _run_aggregation("week", week_start, week_end)
            )
        finally:
            loop.close()

    duration = time.time() - task_start

    logger.info(f"Completed weekly rollup: duration={duration:.2f}s")

    return {
        "status": "success",
        "granularity": "week",
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "duration_seconds": duration,
        "metrics": result,
    }
