"""Health check endpoints for Celery workers and queues."""

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/workers")
async def worker_health_check() -> dict[str, Any]:
    """Check Celery worker availability and queue status.

    Returns:
        Worker status including:
        - available: bool indicating if workers are responding
        - worker_count: number of active workers
        - queues: queue depth for each queue
        - checked_at: timestamp of the check
    """
    try:
        from app.workers.celery_app import celery_app

        # Ping workers with short timeout
        inspect = celery_app.control.inspect(timeout=2.0)

        # Get active workers
        ping_response = inspect.ping()
        active_workers = ping_response if ping_response else {}
        worker_count = len(active_workers)

        # Get queue lengths
        queue_stats = {}
        try:
            # Get stats from workers
            stats = inspect.stats()
            if stats:
                for _worker_name, worker_stats in stats.items():
                    for queue in worker_stats.get("queues", []):
                        queue_name = queue.get("name", "unknown")
                        if queue_name not in queue_stats:
                            queue_stats[queue_name] = {"workers": 0}
                        queue_stats[queue_name]["workers"] += 1
        except Exception as e:
            logger.warning("failed_to_get_queue_stats", error=str(e))

        # Get active task count
        active_tasks = {}
        try:
            active = inspect.active()
            if active:
                for worker_name, tasks in active.items():
                    active_tasks[worker_name] = len(tasks) if tasks else 0
        except Exception as e:
            logger.warning("failed_to_get_active_tasks", error=str(e))

        return {
            "available": worker_count > 0,
            "worker_count": worker_count,
            "workers": list(active_workers.keys()) if active_workers else [],
            "queues": queue_stats,
            "active_tasks": active_tasks,
            "checked_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error("worker_health_check_failed", error=str(e))
        return {
            "available": False,
            "worker_count": 0,
            "workers": [],
            "queues": {},
            "active_tasks": {},
            "error": str(e),
            "checked_at": datetime.now(UTC).isoformat(),
        }


@router.get("/queues")
async def queue_status() -> dict[str, Any]:
    """Get queue depth and pending task count.

    Returns:
        Queue status for each configured queue.
    """
    try:
        from app.workers.celery_app import celery_app

        # Get reserved (pending) tasks per queue
        inspect = celery_app.control.inspect(timeout=2.0)

        reserved = {}
        scheduled = {}

        try:
            res = inspect.reserved()
            if res:
                for worker_name, tasks in res.items():
                    reserved[worker_name] = len(tasks) if tasks else 0
        except Exception:
            pass

        try:
            sched = inspect.scheduled()
            if sched:
                for worker_name, tasks in sched.items():
                    scheduled[worker_name] = len(tasks) if tasks else 0
        except Exception:
            pass

        return {
            "reserved": reserved,
            "scheduled": scheduled,
            "checked_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error("queue_status_check_failed", error=str(e))
        return {
            "reserved": {},
            "scheduled": {},
            "error": str(e),
            "checked_at": datetime.now(UTC).isoformat(),
        }
