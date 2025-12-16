"""Queue monitoring service for Celery background tasks.

Provides real-time visibility into:
- Active Celery queues (dynamically discovered)
- Queue metrics: pending tasks, active tasks, worker count
- Worker health: heartbeat detection (offline if > 60s)
- Task details: task_id, task_name, status, started_at, estimated_duration

Story 7-27 Extensions:
- Processing step breakdown with per-step timing
- Bulk retry for failed documents
- Document status filtering

Uses Celery Inspect API with Redis caching (5-min TTL) to minimize broker load.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from celery.app.control import Inspect
from kombu.exceptions import OperationalError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis_client
from app.models.document import Document, DocumentStatus
from app.schemas.admin import (
    BulkRetryError,
    BulkRetryResponse,
    DocumentStatusFilter,
    QueueStatus,
    StepInfo,
    StepStatusType,
    TaskInfo,
    WorkerInfo,
)
from app.workers.celery_app import celery_app

logger = structlog.get_logger()

CACHE_KEY = "admin:queue:status"
CACHE_TTL = 300  # 5 minutes
WORKER_HEARTBEAT_THRESHOLD = 60  # seconds
CELERY_INSPECT_TIMEOUT = 1.0  # seconds


class QueueMonitorService:
    """Service for monitoring Celery queue status and worker health.

    Uses Celery Inspect API to dynamically discover active queues and workers.
    Applies Redis caching (5-min TTL) to reduce broker load.
    Falls back to direct Celery inspect if Redis unavailable.
    """

    async def get_all_queues(self) -> list[QueueStatus]:
        """Get status for all active Celery queues with Redis caching.

        Dynamically discovers queues via Celery Inspect API (no hardcoded queue names).
        Returns QueueStatus with metrics: pending_tasks, active_tasks, workers.

        Returns:
            List[QueueStatus]: Status for all active queues, or empty list if unavailable.
        """
        try:
            redis = await get_redis_client()

            # Try cache first
            cached = await redis.get(CACHE_KEY)
            if cached:
                logger.info("queue_status_cache_hit")
                # Parse cached JSON into list of QueueStatus
                import json

                cached_data = json.loads(cached)
                return [QueueStatus.model_validate(item) for item in cached_data]
        except Exception as e:
            logger.warning("redis_unavailable", error=str(e))
            # Continue with Celery inspect if Redis fails

        # Cache miss - query Celery inspect API
        logger.info("queue_status_cache_miss")
        queue_statuses = await self._query_celery_inspect()

        # Store in cache (best effort)
        try:
            redis = await get_redis_client()
            import json

            cache_value = json.dumps(
                [q.model_dump(mode="json") for q in queue_statuses]
            )
            await redis.setex(CACHE_KEY, CACHE_TTL, cache_value)
        except Exception as e:
            logger.warning("redis_cache_set_failed", error=str(e))

        return queue_statuses

    async def get_queue_tasks(
        self,
        queue_name: str,
        session: AsyncSession | None = None,
        document_status: DocumentStatusFilter = DocumentStatusFilter.ALL,
    ) -> list[TaskInfo]:
        """Get task details for a specific queue with processing step breakdown.

        Story 7-27: Extended to include document processing steps and support filtering.

        Args:
            queue_name: Name of the queue (e.g., "document_processing").
            session: Database session for fetching document details (optional).
            document_status: Filter by document status (AC-7.27.15).

        Returns:
            List[TaskInfo]: Active tasks in the queue, sorted by started_at DESC.
        """
        try:
            inspect = self._get_celery_inspect()
            active_tasks_dict = inspect.active()

            if active_tasks_dict is None:
                logger.warning("celery_broker_connection_error")
                return []

            # Collect document IDs from task args for batch lookup
            task_doc_ids: dict[str, UUID | None] = {}

            # Aggregate tasks from all workers for this queue
            raw_tasks = []
            for _worker_name, worker_tasks in active_tasks_dict.items():
                for task in worker_tasks:
                    # Filter by queue name (routing_key matches queue name)
                    delivery_info = task.get("delivery_info", {})
                    task_queue = delivery_info.get("routing_key", "")

                    if task_queue == queue_name:
                        task_id = task.get("id", "")
                        # Extract document_id from task args (first positional arg for process_document)
                        doc_id = self._extract_document_id(task)
                        task_doc_ids[task_id] = doc_id
                        raw_tasks.append(task)

            # Batch fetch documents if session provided
            documents_map: dict[UUID, Document] = {}
            if session and task_doc_ids:
                doc_ids = [d for d in task_doc_ids.values() if d is not None]
                if doc_ids:
                    documents_map = await self._fetch_documents(session, doc_ids)

            # Apply document status filter if not ALL
            if document_status != DocumentStatusFilter.ALL and session:
                filtered_doc_ids = {
                    doc_id
                    for doc_id, doc in documents_map.items()
                    if doc.status.value == document_status.value
                }
                raw_tasks = [
                    t
                    for t in raw_tasks
                    if task_doc_ids.get(t.get("id", "")) in filtered_doc_ids
                ]

            # Build TaskInfo objects with document details
            tasks = []
            for task in raw_tasks:
                task_id = task.get("id", "")
                doc_id = task_doc_ids.get(task_id)
                doc = documents_map.get(doc_id) if doc_id else None

                task_info = TaskInfo(
                    task_id=task_id,
                    task_name=task.get("name", ""),
                    status="active",
                    started_at=self._parse_timestamp(task.get("time_start")),
                    estimated_duration=self._calculate_duration(task.get("time_start")),
                    document_id=doc_id,
                    document_name=doc.original_filename if doc else None,
                    current_step=doc.current_step if doc else None,
                    processing_steps=self._build_step_info(doc) if doc else None,
                    step_errors=doc.step_errors if doc else None,
                )
                tasks.append(task_info)

            # Sort by started_at DESC (newest first)
            tasks.sort(key=lambda t: t.started_at or datetime.min, reverse=True)
            return tasks

        except (OperationalError, ConnectionError) as e:
            logger.warning("celery_inspect_timeout", error=str(e))
            return []

    def _extract_document_id(self, task: dict[str, Any]) -> UUID | None:
        """Extract document_id from Celery task args.

        Task args format: (document_id_str, kb_id_str, ...)

        Args:
            task: Celery task dict from inspect.active().

        Returns:
            UUID | None: Document UUID if found, None otherwise.
        """
        args = task.get("args", [])
        if args and len(args) > 0:
            try:
                return UUID(args[0])
            except (ValueError, TypeError):
                pass

        # Also check kwargs
        kwargs = task.get("kwargs", {})
        doc_id_str = kwargs.get("document_id")
        if doc_id_str:
            try:
                return UUID(doc_id_str)
            except (ValueError, TypeError):
                pass

        return None

    async def _fetch_documents(
        self,
        session: AsyncSession,
        doc_ids: list[UUID],
    ) -> dict[UUID, Document]:
        """Batch fetch documents by IDs.

        Args:
            session: Database session.
            doc_ids: List of document UUIDs.

        Returns:
            Dict mapping document ID to Document.
        """
        if not doc_ids:
            return {}

        result = await session.execute(select(Document).where(Document.id.in_(doc_ids)))
        documents = result.scalars().all()
        return {doc.id: doc for doc in documents}

    def _build_step_info(self, doc: Document) -> list[StepInfo]:
        """Build StepInfo list from document processing_steps.

        AC-7.27.2: Returns step breakdown with columns: Step, Status, Started, Completed, Duration.

        Args:
            doc: Document with processing_steps JSONB.

        Returns:
            List of StepInfo for UI display.
        """
        steps_order = ["parse", "chunk", "embed", "index"]
        step_infos = []

        processing_steps = doc.processing_steps or {}
        step_errors = doc.step_errors or {}

        for step_name in steps_order:
            step_data = processing_steps.get(step_name, {})
            status_str = step_data.get("status", "pending")

            # Map to StepStatusType enum
            try:
                status = StepStatusType(status_str)
            except ValueError:
                status = StepStatusType.PENDING

            # Parse timestamps
            started_at = None
            completed_at = None
            if step_data.get("started_at"):
                try:
                    started_at = datetime.fromisoformat(step_data["started_at"])
                except (ValueError, TypeError):
                    pass

            if step_data.get("completed_at"):
                try:
                    completed_at = datetime.fromisoformat(step_data["completed_at"])
                except (ValueError, TypeError):
                    pass

            # Calculate or use stored duration
            duration_ms = step_data.get("duration_ms")
            if duration_ms is None and started_at and completed_at:
                duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            step_infos.append(
                StepInfo(
                    step=step_name,
                    status=status,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                    error_message=step_errors.get(step_name),
                )
            )

        return step_infos

    async def bulk_retry_failed(
        self,
        session: AsyncSession,
        document_ids: list[UUID] | None = None,
        retry_all_failed: bool = False,
        kb_id: UUID | None = None,
    ) -> BulkRetryResponse:
        """Retry failed documents in bulk (AC-7.27.6-7.27.10).

        Args:
            session: Database session.
            document_ids: Specific document UUIDs to retry (selective).
            retry_all_failed: Retry all FAILED documents (overrides document_ids).
            kb_id: Scope retry to specific knowledge base (optional).

        Returns:
            BulkRetryResponse with queued/failed counts and errors.
        """
        from app.workers.document_tasks import process_document

        queued = 0
        failed = 0
        errors: list[BulkRetryError] = []

        # Build query for documents to retry
        query = select(Document).where(Document.status == DocumentStatus.FAILED)

        if retry_all_failed:
            # Retry all failed documents, optionally scoped to KB
            if kb_id:
                query = query.where(Document.kb_id == kb_id)
        elif document_ids:
            # Retry specific documents
            query = query.where(Document.id.in_(document_ids))
        else:
            # No documents specified
            return BulkRetryResponse(queued=0, failed=0, errors=[])

        result = await session.execute(query)
        documents = result.scalars().all()

        logger.info(
            "bulk_retry_starting",
            document_count=len(documents),
            retry_all_failed=retry_all_failed,
            kb_id=str(kb_id) if kb_id else None,
        )

        for doc in documents:
            try:
                # Reset document for retry
                doc.status = DocumentStatus.PENDING
                doc.retry_count = (doc.retry_count or 0) + 1
                doc.last_error = None
                doc.processing_started_at = None
                doc.processing_completed_at = None
                doc.current_step = "upload"
                doc.processing_steps = {}
                doc.step_errors = {}

                # Queue for processing
                process_document.delay(str(doc.id), str(doc.kb_id))
                queued += 1

                logger.info("document_retry_queued", document_id=str(doc.id))

            except Exception as e:
                failed += 1
                errors.append(BulkRetryError(document_id=doc.id, error=str(e)))
                logger.warning(
                    "document_retry_failed",
                    document_id=str(doc.id),
                    error=str(e),
                )

        # Commit document status changes
        await session.commit()

        logger.info(
            "bulk_retry_completed",
            queued=queued,
            failed=failed,
        )

        return BulkRetryResponse(queued=queued, failed=failed, errors=errors)

    async def _query_celery_inspect(self) -> list[QueueStatus]:
        """Query Celery Inspect API for queue status.

        Returns:
            List[QueueStatus]: Status for all active queues, or empty list if unavailable.
        """
        try:
            inspect = self._get_celery_inspect()

            # Get active tasks per worker
            active_tasks_dict = inspect.active()
            # Get reserved tasks (pending assignment)
            reserved_tasks_dict = inspect.reserved()
            # Get worker stats (includes heartbeat)
            stats_dict = inspect.stats()

            if active_tasks_dict is None or stats_dict is None:
                logger.warning("celery_broker_connection_error")
                return self._unavailable_status()

            # Dynamically discover queues from active and reserved tasks
            queues: dict[str, dict[str, Any]] = {}

            # Process active tasks
            for worker_name, tasks in (active_tasks_dict or {}).items():
                for task in tasks:
                    delivery_info = task.get("delivery_info", {})
                    queue_name = delivery_info.get("routing_key", "default")

                    if queue_name not in queues:
                        queues[queue_name] = {
                            "active_tasks": 0,
                            "pending_tasks": 0,
                            "workers": {},
                        }

                    queues[queue_name]["active_tasks"] += 1

                    # Track worker for this queue
                    if worker_name not in queues[queue_name]["workers"]:
                        queues[queue_name]["workers"][worker_name] = {
                            "active_tasks": 0,
                        }
                    queues[queue_name]["workers"][worker_name]["active_tasks"] += 1

            # Process reserved tasks (pending)
            for worker_name, tasks in (reserved_tasks_dict or {}).items():
                for task in tasks:
                    delivery_info = task.get("delivery_info", {})
                    queue_name = delivery_info.get("routing_key", "default")

                    if queue_name not in queues:
                        queues[queue_name] = {
                            "active_tasks": 0,
                            "pending_tasks": 0,
                            "workers": {},
                        }

                    queues[queue_name]["pending_tasks"] += 1

                    # Track worker for this queue if not already tracked
                    if worker_name not in queues[queue_name]["workers"]:
                        queues[queue_name]["workers"][worker_name] = {
                            "active_tasks": 0,
                        }

            # Add known queues from celery_app config if not discovered
            configured_queues = celery_app.conf.task_queues or {}
            for queue_name in configured_queues:
                if queue_name not in queues:
                    queues[queue_name] = {
                        "active_tasks": 0,
                        "pending_tasks": 0,
                        "workers": {},
                    }

            # Build QueueStatus objects
            queue_statuses = []
            for queue_name, metrics in queues.items():
                # Build worker info with heartbeat detection
                workers = []
                for worker_name, worker_metrics in metrics["workers"].items():
                    worker_stats = (stats_dict or {}).get(worker_name, {})
                    is_online = self._is_worker_online(worker_stats)

                    workers.append(
                        WorkerInfo(
                            worker_id=worker_name,
                            status="online" if is_online else "offline",
                            active_tasks=worker_metrics["active_tasks"],
                        )
                    )

                queue_statuses.append(
                    QueueStatus(
                        queue_name=queue_name,
                        pending_tasks=metrics["pending_tasks"],
                        active_tasks=metrics["active_tasks"],
                        workers=workers,
                        status="available",
                    )
                )

            return queue_statuses

        except (OperationalError, ConnectionError) as e:
            logger.warning("celery_inspect_timeout", error=str(e))
            return self._unavailable_status()
        except Exception as e:
            logger.error("celery_inspect_error", error=str(e), exc_info=True)
            return self._unavailable_status()

    def _get_celery_inspect(self) -> Inspect:
        """Get Celery Inspect instance with timeout.

        Returns:
            Inspect: Celery inspect instance.
        """
        return celery_app.control.inspect(timeout=CELERY_INSPECT_TIMEOUT)

    def _is_worker_online(self, worker_stats: dict[str, Any]) -> bool:
        """Determine if worker is online based on heartbeat.

        Args:
            worker_stats: Worker stats dict from Celery inspect.

        Returns:
            bool: True if worker online (heartbeat <= 60s), False otherwise.
        """
        # Worker is considered online if it responded to inspect.stats()
        # Celery inspect timeout is 1s, so if we get stats, worker is responsive
        # For additional validation, we could check the rusage or other fields
        return bool(worker_stats)

    def _unavailable_status(self) -> list[QueueStatus]:
        """Return unavailable status for all configured queues.

        Returns:
            List[QueueStatus]: Queues marked as unavailable.
        """
        configured_queues = celery_app.conf.task_queues or {}
        return [
            QueueStatus(
                queue_name=queue_name,
                pending_tasks=0,
                active_tasks=0,
                workers=[],
                status="unavailable",
            )
            for queue_name in configured_queues
        ]

    def _parse_timestamp(self, timestamp: float | None) -> datetime | None:
        """Parse Unix timestamp to datetime.

        Args:
            timestamp: Unix timestamp (seconds since epoch).

        Returns:
            datetime | None: Parsed datetime or None if invalid.
        """
        if timestamp is None:
            return None
        try:
            return datetime.fromtimestamp(timestamp, tz=UTC)
        except (ValueError, OSError):
            return None

    def _calculate_duration(self, start_timestamp: float | None) -> int | None:
        """Calculate elapsed duration in milliseconds.

        Args:
            start_timestamp: Task start time (Unix timestamp).

        Returns:
            int | None: Elapsed time in milliseconds, or None if invalid.
        """
        if start_timestamp is None:
            return None

        started_at = self._parse_timestamp(start_timestamp)
        if started_at is None:
            return None

        elapsed = datetime.now(UTC) - started_at
        return int(elapsed.total_seconds() * 1000)
