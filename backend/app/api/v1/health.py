"""Health check endpoints for orchestration probes and Celery workers.

Story 7.4: Production Deployment Configuration
- /health: Liveness probe - basic check that service is running
- /ready: Readiness probe - checks DB, Redis, Qdrant connectivity
- /workers: Celery worker availability check
- /queues: Queue depth and pending task count
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Response, status

from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

# Timeout for dependency health checks (AC-7.4.4: 5s max)
HEALTH_CHECK_TIMEOUT = 5.0


@router.get("")
@router.get("/")
async def liveness_check() -> dict[str, Any]:
    """Liveness probe endpoint for orchestrator health checks.

    Returns 200 if the service is running. This is a simple check
    that does not verify dependencies - use /ready for that.

    Returns:
        Basic health status with version info.
    """
    return {
        "status": "healthy",
        "service": "lumikb-api",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/ready")
async def readiness_check(response: Response) -> dict[str, Any]:
    """Readiness probe endpoint checking all critical dependencies.

    Checks connectivity to:
    - PostgreSQL database
    - Redis cache
    - Qdrant vector database

    Each check has a 5-second timeout. If any dependency is unavailable,
    returns 503 Service Unavailable.

    Returns:
        Detailed status of each dependency with overall ready status.
    """
    checks: dict[str, dict[str, Any]] = {}
    all_healthy = True

    # Check PostgreSQL
    db_status = await _check_database()
    checks["database"] = db_status
    if not db_status["healthy"]:
        all_healthy = False

    # Check Redis
    redis_status = await _check_redis()
    checks["redis"] = redis_status
    if not redis_status["healthy"]:
        all_healthy = False

    # Check Qdrant
    qdrant_status = await _check_qdrant()
    checks["qdrant"] = qdrant_status
    if not qdrant_status["healthy"]:
        all_healthy = False

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def _check_database() -> dict[str, Any]:
    """Check PostgreSQL database connectivity with timeout."""
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=1,
            max_overflow=0,
        )

        async def check() -> bool:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            return True

        await asyncio.wait_for(check(), timeout=HEALTH_CHECK_TIMEOUT)
        return {"healthy": True, "latency_ms": None}

    except TimeoutError:
        logger.warning("database_health_check_timeout")
        return {"healthy": False, "error": "timeout"}
    except Exception as e:
        logger.warning("database_health_check_failed", error=str(e))
        return {"healthy": False, "error": str(e)}


async def _check_redis() -> dict[str, Any]:
    """Check Redis connectivity with timeout."""
    try:
        import redis.asyncio as redis

        client = redis.from_url(settings.redis_url, decode_responses=True)

        async def check() -> bool:
            pong = await client.ping()
            await client.aclose()
            return pong

        result = await asyncio.wait_for(check(), timeout=HEALTH_CHECK_TIMEOUT)
        return {"healthy": result, "latency_ms": None}

    except TimeoutError:
        logger.warning("redis_health_check_timeout")
        return {"healthy": False, "error": "timeout"}
    except Exception as e:
        logger.warning("redis_health_check_failed", error=str(e))
        return {"healthy": False, "error": str(e)}


async def _check_qdrant() -> dict[str, Any]:
    """Check Qdrant vector database connectivity with timeout."""
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            timeout=HEALTH_CHECK_TIMEOUT,
        )

        async def check() -> bool:
            # Use collections list as a health indicator
            # This is a lightweight operation that verifies connectivity
            import asyncio

            loop = asyncio.get_event_loop()
            # QdrantClient.get_collections is synchronous, run in executor
            await loop.run_in_executor(None, client.get_collections)
            client.close()
            return True

        await asyncio.wait_for(check(), timeout=HEALTH_CHECK_TIMEOUT)
        return {"healthy": True, "latency_ms": None}

    except TimeoutError:
        logger.warning("qdrant_health_check_timeout")
        return {"healthy": False, "error": "timeout"}
    except Exception as e:
        logger.warning("qdrant_health_check_failed", error=str(e))
        return {"healthy": False, "error": str(e)}


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
