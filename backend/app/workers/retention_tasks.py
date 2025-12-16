"""Celery tasks for observability data retention cleanup.

Story 9-14: Data Retention and Cleanup

Scheduled tasks for cleaning up old observability data based on
configurable retention policies using TimescaleDB chunk management.
"""

import asyncio
import logging
import time
from typing import Any

from celery import shared_task

from app.core.database import get_async_session_context
from app.services.retention_service import RetentionService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.workers.retention_tasks.cleanup_observability_data",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def cleanup_observability_data(
    self,  # noqa: ARG001 - required by bind=True for retry capability
    dry_run: bool = False,
) -> dict[str, Any]:
    """Clean up observability data based on retention policies.

    This task is scheduled to run daily at 3 AM UTC. It drops
    TimescaleDB chunks older than the retention period for efficient
    storage management.

    Args:
        dry_run: If True, preview what would be deleted without actual deletion

    Returns:
        Dict with cleanup results for each table
    """
    task_start = time.time()
    logger.info(f"Starting observability data cleanup: dry_run={dry_run}")

    # Run async cleanup
    try:
        result = asyncio.get_event_loop().run_until_complete(_run_cleanup(dry_run))
    except RuntimeError:
        # No event loop running - create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_run_cleanup(dry_run))
        finally:
            loop.close()

    duration = time.time() - task_start

    # Log summary
    tables_cleaned = len(result.get("results", {}))
    errors_count = len(result.get("errors", []))

    logger.info(
        f"Completed observability data cleanup: duration={duration:.2f}s, "
        f"tables_cleaned={tables_cleaned}, errors={errors_count}, "
        f"timescaledb_used={result.get('timescaledb_used', False)}"
    )

    return {
        "status": "success" if errors_count == 0 else "partial",
        "dry_run": dry_run,
        "duration_seconds": duration,
        **result,
    }


async def _run_cleanup(dry_run: bool) -> dict[str, Any]:
    """Run the cleanup using async context.

    Args:
        dry_run: If True, preview without actual deletion

    Returns:
        Cleanup results from RetentionService
    """
    async with get_async_session_context() as session:
        service = RetentionService(session)
        return await service.cleanup_all(dry_run)


@shared_task(
    name="app.workers.retention_tasks.cleanup_table",
)
def cleanup_table(
    table_name: str,
    retention_days: int,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Clean up a specific table (admin use only).

    Args:
        table_name: Fully qualified table name (schema.table)
        retention_days: Days of data to retain
        dry_run: If True, preview without deletion

    Returns:
        Dict with cleanup results
    """
    task_start = time.time()
    logger.info(
        f"Starting table cleanup: table={table_name}, "
        f"retention_days={retention_days}, dry_run={dry_run}"
    )

    try:
        result = asyncio.get_event_loop().run_until_complete(
            _run_table_cleanup(table_name, retention_days, dry_run)
        )
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _run_table_cleanup(table_name, retention_days, dry_run)
            )
        finally:
            loop.close()

    duration = time.time() - task_start
    result["duration_seconds"] = duration

    logger.info(f"Completed table cleanup: {result}")

    return result


async def _run_table_cleanup(
    table_name: str,
    retention_days: int,  # noqa: ARG001 - reserved for future custom retention override
    dry_run: bool,
) -> dict[str, Any]:
    """Run single table cleanup using async context.

    Args:
        table_name: Fully qualified table name
        retention_days: Days of data to retain (reserved for future use)
        dry_run: If True, preview without deletion

    Returns:
        Cleanup results
    """
    async with get_async_session_context() as session:
        service = RetentionService(session)
        use_timescaledb = await service.check_timescaledb_available()

        # Determine retention setting name for this table
        # Note: Currently uses config settings, retention_days param reserved for future use
        retention_setting = "observability_retention_days"
        if "metrics_aggregates" in table_name:
            retention_setting = "observability_metrics_retention_days"
        elif "provider_sync_status" in table_name:
            retention_setting = "observability_sync_status_retention_days"

        result = await service.cleanup_hypertable(
            table_name,
            retention_setting,
            use_timescaledb,
            dry_run,
        )

        if not dry_run:
            await session.commit()

        return {
            "table": table_name,
            "timescaledb_used": use_timescaledb,
            **result,
        }
