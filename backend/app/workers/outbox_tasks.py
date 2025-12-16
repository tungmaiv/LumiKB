"""Outbox processor task for reliable event processing."""

import asyncio
from datetime import UTC, datetime

import structlog
from sqlalchemy import select, update

from app.core.database import celery_session_factory
from app.models.outbox import Outbox
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)

# Maximum attempts before giving up on an event
MAX_OUTBOX_ATTEMPTS = 5


def run_async(coro):
    """Run async coroutine in sync context for Celery tasks.

    Reuses an existing event loop if available, otherwise creates one.
    This prevents "Future attached to different loop" errors that occur
    when asyncio.run() creates and closes loops for each call.

    For production Celery workers, this is the normal execution path.
    For tests, run_async is typically mocked or patched.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        # If we're already in an async context (shouldn't happen in Celery workers)
        # Create a new event loop in a new thread
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        # Get or create an event loop for this thread
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


async def _poll_outbox_events(limit: int = 100) -> list[dict]:
    """Poll outbox for unprocessed events with row-level locking.

    Args:
        limit: Maximum number of events to fetch.

    Returns:
        List of event dictionaries with id, event_type, aggregate_id, payload.
    """
    async with celery_session_factory() as session:
        # Query for unprocessed events with row-level locking
        # skip_locked=True prevents worker contention
        result = await session.execute(
            select(Outbox)
            .where(Outbox.processed_at.is_(None))
            .where(Outbox.attempts < MAX_OUTBOX_ATTEMPTS)
            .order_by(Outbox.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        events = result.scalars().all()

        # Convert to dictionaries before session closes
        return [
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "aggregate_id": str(event.aggregate_id),
                "aggregate_type": event.aggregate_type,
                "payload": event.payload,
                "attempts": event.attempts,
            }
            for event in events
        ]


async def _mark_event_processed(event_id: str) -> None:
    """Mark an outbox event as processed."""
    async with celery_session_factory() as session:
        await session.execute(
            update(Outbox)
            .where(Outbox.id == event_id)
            .values(processed_at=datetime.now(UTC))
        )
        await session.commit()


async def _increment_event_attempts(
    event_id: str,
    error_message: str,
    event_type: str | None = None,
    aggregate_id: str | None = None,
) -> int:
    """Increment attempt count and record error for failed event.

    Args:
        event_id: The outbox event UUID string.
        error_message: The error message to record.
        event_type: Optional event type for alert logging.
        aggregate_id: Optional aggregate ID for alert logging.

    Returns:
        The new attempt count after incrementing.
    """
    async with celery_session_factory() as session:
        # Increment and get new value
        result = await session.execute(
            update(Outbox)
            .where(Outbox.id == event_id)
            .values(
                attempts=Outbox.attempts + 1,
                last_error=error_message[:1000],  # Truncate long errors
            )
            .returning(Outbox.attempts)
        )
        new_attempts = result.scalar() or 0
        await session.commit()

        # Check if max attempts reached - log admin alert (AC: 2)
        if new_attempts >= MAX_OUTBOX_ATTEMPTS:
            logger.error(
                "outbox_event_max_retries_reached",
                alert="ADMIN_INTERVENTION_REQUIRED",
                severity="CRITICAL",
                event_id=event_id,
                event_type=event_type,
                aggregate_id=aggregate_id,
                last_error=error_message[:500],  # Shorter for alert
                attempts=new_attempts,
            )

        return new_attempts


async def dispatch_event_async(event: dict) -> None:
    """Async dispatch event to appropriate handler based on event_type.

    This is the preferred method when calling from an async context to avoid
    nested event loops.

    Args:
        event: Event dictionary with event_type, aggregate_id, payload.
    """
    event_type = event["event_type"]

    if event_type == "document.process":
        # Import here to avoid circular imports
        from app.workers.document_tasks import process_document

        document_id = event["payload"].get("document_id")
        if document_id:
            # Dispatch to document processing task
            process_document.delay(document_id)
            logger.info(
                "dispatched_document_processing",
                document_id=document_id,
                event_id=event["id"],
            )
        else:
            logger.error(
                "missing_document_id_in_payload",
                event_id=event["id"],
                payload=event["payload"],
            )

    elif event_type == "document.delete":
        # Import here to avoid circular imports
        from app.workers.document_tasks import delete_document_cleanup

        document_id = event["payload"].get("document_id")
        kb_id = event["payload"].get("kb_id")
        file_path = event["payload"].get("file_path")

        if document_id and kb_id:
            # Dispatch to document cleanup task
            delete_document_cleanup.delay(
                doc_id=document_id,
                kb_id=kb_id,
                file_path=file_path,
            )
            logger.info(
                "dispatched_document_cleanup",
                document_id=document_id,
                kb_id=kb_id,
                event_id=event["id"],
            )
        else:
            logger.error(
                "missing_document_or_kb_id_in_payload",
                event_id=event["id"],
                payload=event["payload"],
            )

    elif event_type == "kb.delete":
        # Handle knowledge base deletion - soft-delete docs, delete vectors and files
        kb_id = event["payload"].get("kb_id")

        if kb_id:
            # Await KB delete cleanup directly in async context
            await _handle_kb_delete(kb_id, event["id"])
        else:
            logger.error(
                "missing_kb_id_in_kb_delete_payload",
                event_id=event["id"],
                payload=event["payload"],
            )

    elif event_type == "kb.archive":
        # Handle KB archive - update Qdrant payloads with is_archived: true (Story 7-24)
        kb_id = event["payload"].get("kb_id")
        collection_name = event["payload"].get("collection_name")
        is_archived = event["payload"].get("is_archived", True)

        if kb_id and collection_name:
            await _handle_kb_archive(kb_id, collection_name, is_archived, event["id"])
        else:
            logger.error(
                "missing_kb_id_or_collection_in_kb_archive_payload",
                event_id=event["id"],
                payload=event["payload"],
            )

    elif event_type == "kb.restore":
        # Handle KB restore - update Qdrant payloads with is_archived: false (Story 7-25)
        kb_id = event["payload"].get("kb_id")
        collection_name = event["payload"].get("collection_name")
        is_archived = event["payload"].get("is_archived", False)

        if kb_id and collection_name:
            await _handle_kb_archive(kb_id, collection_name, is_archived, event["id"])
        else:
            logger.error(
                "missing_kb_id_or_collection_in_kb_restore_payload",
                event_id=event["id"],
                payload=event["payload"],
            )

    elif event_type == "document.reprocess":
        # Handle document reprocessing (from reconciliation or replacement)
        document_id = event["payload"].get("document_id")
        reason = event["payload"].get("reason", "manual")
        is_replacement = event["payload"].get("is_replacement", False)

        if document_id:
            # Await document reprocess directly in async context
            await _handle_document_reprocess(
                document_id, reason, event["id"], is_replacement=is_replacement
            )
        else:
            logger.error(
                "missing_document_id_in_reprocess_payload",
                event_id=event["id"],
                payload=event["payload"],
            )

    else:
        logger.warning(
            "unknown_event_type",
            event_type=event_type,
            event_id=event["id"],
        )


def dispatch_event(event: dict) -> None:
    """Sync dispatch event to appropriate handler based on event_type.

    NOTE: This sync version is kept for backward compatibility but should
    be avoided when calling from an async context. Use dispatch_event_async instead.

    Args:
        event: Event dictionary with event_type, aggregate_id, payload.
    """
    run_async(dispatch_event_async(event))


@celery_app.task(name="app.workers.outbox_tasks.process_outbox_events")
def process_outbox_events() -> dict:
    """Periodic task to poll and process outbox events.

    Runs every 10 seconds (configured in celery_app.py beat_schedule).

    Returns:
        Dict with processed and failed counts.
    """
    logger.debug("outbox_poll_started")

    # Run all async operations in a single event loop to avoid
    # "Future attached to a different loop" errors
    return run_async(_process_outbox_events_async())


async def _process_outbox_events_async() -> dict:
    """Async implementation of outbox event processing.

    Consolidates all async operations into a single event loop context
    to prevent asyncio event loop mismatch errors.
    """
    try:
        events = await _poll_outbox_events(limit=100)
    except Exception as e:
        logger.error("outbox_poll_failed", error=str(e))
        return {"processed": 0, "failed": 0, "error": str(e)}

    processed_count = 0
    failed_count = 0

    for event in events:
        try:
            # Use async dispatch to avoid nested event loops
            await dispatch_event_async(event)
            # Mark as processed after successful dispatch
            await _mark_event_processed(event["id"])
            processed_count += 1
            logger.info(
                "outbox_event_processed",
                event_id=event["id"],
                event_type=event["event_type"],
            )
        except Exception as e:
            # Increment attempts and record error (includes admin alert on max retries)
            await _increment_event_attempts(
                event["id"],
                str(e),
                event_type=event["event_type"],
                aggregate_id=event["aggregate_id"],
            )
            failed_count += 1
            logger.error(
                "outbox_event_failed",
                event_id=event["id"],
                event_type=event["event_type"],
                error=str(e),
                attempts=event["attempts"] + 1,
            )

    if processed_count > 0 or failed_count > 0:
        logger.info(
            "outbox_poll_completed",
            processed=processed_count,
            failed=failed_count,
        )

    return {"processed": processed_count, "failed": failed_count}


async def _handle_kb_archive(
    kb_id: str, collection_name: str, is_archived: bool, event_id: str
) -> None:
    """Handle kb.archive or kb.restore event - update Qdrant payloads with is_archived flag.

    Story 7-24 (archive) and Story 7-25 (restore):
    - Updates all point payloads in the KB's Qdrant collection with is_archived: true/false
    - Uses set_payload to bulk update all points in the collection

    Args:
        kb_id: The knowledge base UUID string.
        collection_name: The Qdrant collection name.
        is_archived: True for archive, False for restore.
        event_id: The outbox event ID for logging.
    """
    from qdrant_client.http import models as qdrant_models

    from app.integrations.qdrant_client import qdrant_service

    try:
        # Check if collection exists
        from uuid import UUID

        kb_uuid = UUID(kb_id)
        if not await qdrant_service.collection_exists(kb_uuid):
            logger.warning(
                "kb_archive_collection_not_found",
                kb_id=kb_id,
                collection_name=collection_name,
                event_id=event_id,
            )
            return

        # Get point count before update for logging
        count_result = await qdrant_service.count(
            collection_name=collection_name,
            exact=True,
        )
        point_count = count_result.count

        if point_count == 0:
            logger.info(
                "kb_archive_no_points_to_update",
                kb_id=kb_id,
                collection_name=collection_name,
                is_archived=is_archived,
                event_id=event_id,
            )
            return

        # Update all points in the collection with is_archived flag
        # Using an empty filter matches all points
        await qdrant_service.set_payload(
            collection_name=collection_name,
            payload={"is_archived": is_archived},
            points=qdrant_models.Filter(must=[]),  # Empty filter matches all points
            wait=True,
        )

        logger.info(
            "kb_archive_qdrant_updated",
            kb_id=kb_id,
            collection_name=collection_name,
            is_archived=is_archived,
            points_updated=point_count,
            event_id=event_id,
        )

    except Exception as e:
        logger.error(
            "kb_archive_qdrant_update_failed",
            kb_id=kb_id,
            collection_name=collection_name,
            is_archived=is_archived,
            event_id=event_id,
            error=str(e),
        )
        raise


async def _handle_kb_delete(kb_id: str, event_id: str) -> None:
    """Handle kb.delete event - soft-delete docs, delete vectors and files.

    Args:
        kb_id: The knowledge base UUID string.
        event_id: The outbox event ID for logging.
    """
    from uuid import UUID

    from sqlalchemy import func

    from app.integrations.minio_client import minio_service
    from app.integrations.qdrant_client import qdrant_service
    from app.models.document import Document, DocumentStatus

    kb_uuid = UUID(kb_id)

    async with celery_session_factory() as session:
        # 1. Soft-delete all documents in the KB
        await session.execute(
            update(Document)
            .where(Document.kb_id == kb_uuid)
            .where(Document.deleted_at.is_(None))
            .values(
                status=DocumentStatus.ARCHIVED,
                deleted_at=datetime.now(UTC),
            )
        )
        await session.commit()

        # Get document count from the result
        doc_count_result = await session.execute(
            select(func.count(Document.id)).where(Document.kb_id == kb_uuid)
        )
        document_count = doc_count_result.scalar() or 0

    # 2. Delete Qdrant collection
    vector_collection_deleted = False
    try:
        vector_collection_deleted = await qdrant_service.delete_collection(kb_uuid)
    except Exception as e:
        logger.warning(
            "kb_delete_qdrant_cleanup_failed",
            kb_id=kb_id,
            event_id=event_id,
            error=str(e),
        )

    # 3. Delete all MinIO files for this KB
    files_deleted = 0
    try:
        bucket_deleted = await minio_service.delete_bucket(kb_uuid)
        if bucket_deleted:
            files_deleted = -1  # Indicates bucket was deleted (unknown file count)
    except Exception as e:
        logger.warning(
            "kb_delete_minio_cleanup_failed",
            kb_id=kb_id,
            event_id=event_id,
            error=str(e),
        )

    logger.info(
        "kb_delete_completed",
        kb_id=kb_id,
        event_id=event_id,
        document_count=document_count,
        vector_collection_deleted=vector_collection_deleted,
        files_deleted=files_deleted,
    )


async def _handle_document_reprocess(
    document_id: str,
    reason: str,
    event_id: str,
    is_replacement: bool = False,
) -> None:
    """Handle document.reprocess event - reset status and trigger processing.

    Args:
        document_id: The document UUID string.
        reason: Reason for reprocessing (e.g., "reconciliation", "manual", "replacement").
        event_id: The outbox event ID for logging.
        is_replacement: If True, perform atomic vector switch during reprocessing.
    """
    from uuid import UUID

    from app.models.document import Document, DocumentStatus
    from app.workers.document_tasks import process_document

    doc_uuid = UUID(document_id)

    async with celery_session_factory() as session:
        # Reset document status to PENDING
        await session.execute(
            update(Document)
            .where(Document.id == doc_uuid)
            .values(
                status=DocumentStatus.PENDING,
                last_error=None,
                retry_count=0,
                processing_started_at=None,
                processing_completed_at=None,
            )
        )
        await session.commit()

    # Dispatch to document processing task with replacement flag
    process_document.delay(document_id, is_replacement=is_replacement)

    logger.info(
        "document_reprocess_dispatched",
        document_id=document_id,
        reason=reason,
        event_id=event_id,
        is_replacement=is_replacement,
    )


# =============================================================================
# Reconciliation Job (AC: 3, 4)
# =============================================================================


@celery_app.task(name="app.workers.outbox_tasks.reconcile_data_consistency")
def reconcile_data_consistency() -> dict:
    """Hourly reconciliation job to detect data inconsistencies.

    Scans for:
    - Documents in READY status without vectors in Qdrant
    - Documents in PROCESSING status for > 30 minutes (stale)
    - Orphaned vectors/files (logged only, no auto-cleanup)

    Returns:
        Dict with anomaly counts and correction actions taken.
    """
    logger.info("reconciliation_started")

    try:
        result = run_async(_run_reconciliation())
        return result
    except Exception as e:
        logger.error("reconciliation_failed", error=str(e))
        return {"error": str(e)}


async def _run_reconciliation() -> dict:
    """Execute reconciliation checks and create correction events."""

    from app.integrations.minio_client import minio_service
    from app.integrations.qdrant_client import qdrant_service
    from app.models.document import Document, DocumentStatus

    anomalies: list[dict] = []
    corrections_created = 0

    async with celery_session_factory() as session:
        # 1. Detect READY docs without vectors
        ready_without_vectors = await _detect_ready_docs_without_vectors(
            session, qdrant_service
        )
        for doc in ready_without_vectors:
            anomalies.append(
                {
                    "type": "ready_without_vectors",
                    "document_id": str(doc["id"]),
                    "kb_id": str(doc["kb_id"]),
                    "detected_at": datetime.now(UTC).isoformat(),
                }
            )
            # Create correction event
            await _create_reprocess_event(
                session, doc["id"], doc["kb_id"], "reconciliation_ready_without_vectors"
            )
            corrections_created += 1

        # 2. Detect stale PROCESSING docs (> 30 min)
        stale_processing = await _detect_stale_processing(session)
        for doc in stale_processing:
            anomalies.append(
                {
                    "type": "stale_processing",
                    "document_id": str(doc["id"]),
                    "kb_id": str(doc["kb_id"]),
                    "processing_started_at": doc["processing_started_at"].isoformat()
                    if doc["processing_started_at"]
                    else None,
                    "detected_at": datetime.now(UTC).isoformat(),
                }
            )
            # Reset to PENDING and create reprocess event
            await session.execute(
                update(Document)
                .where(Document.id == doc["id"])
                .values(status=DocumentStatus.PENDING)
            )
            await _create_reprocess_event(
                session, doc["id"], doc["kb_id"], "reconciliation_stale_processing"
            )
            corrections_created += 1

        await session.commit()

        # 3. Detect orphan vectors (log only in MVP)
        orphan_vectors = await _detect_orphan_vectors(session, qdrant_service)
        for orphan in orphan_vectors:
            anomalies.append(
                {
                    "type": "orphan_vector",
                    "kb_id": str(orphan["kb_id"]),
                    "document_id": str(orphan["document_id"]),
                    "detected_at": datetime.now(UTC).isoformat(),
                }
            )
            logger.warning(
                "reconciliation_orphan_vector_detected",
                kb_id=str(orphan["kb_id"]),
                document_id=str(orphan["document_id"]),
            )

        # 4. Detect orphan files (log only in MVP)
        orphan_files = await _detect_orphan_files(session, minio_service)
        for orphan in orphan_files:
            anomalies.append(
                {
                    "type": "orphan_file",
                    "kb_id": str(orphan["kb_id"]),
                    "file_path": orphan["file_path"],
                    "detected_at": datetime.now(UTC).isoformat(),
                }
            )
            logger.warning(
                "reconciliation_orphan_file_detected",
                kb_id=str(orphan["kb_id"]),
                file_path=orphan["file_path"],
            )

    # Log all anomalies with full details
    for anomaly in anomalies:
        logger.info(
            "reconciliation_anomaly_detected",
            anomaly_type=anomaly["type"],
            **{k: v for k, v in anomaly.items() if k != "type"},
        )

    # Alert if anomaly count > 5
    if len(anomalies) > 5:
        logger.error(
            "reconciliation_high_anomaly_count",
            alert="ADMIN_ATTENTION_RECOMMENDED",
            severity="WARNING",
            anomaly_count=len(anomalies),
            corrections_created=corrections_created,
        )

    logger.info(
        "reconciliation_completed",
        total_anomalies=len(anomalies),
        corrections_created=corrections_created,
        ready_without_vectors=len(ready_without_vectors),
        stale_processing=len(stale_processing),
        orphan_vectors=len(orphan_vectors),
        orphan_files=len(orphan_files),
    )

    return {
        "total_anomalies": len(anomalies),
        "corrections_created": corrections_created,
        "ready_without_vectors": len(ready_without_vectors),
        "stale_processing": len(stale_processing),
        "orphan_vectors": len(orphan_vectors),
        "orphan_files": len(orphan_files),
    }


async def _detect_ready_docs_without_vectors(session, qdrant_service) -> list[dict]:
    """Find READY documents that have no vectors in Qdrant."""
    from app.models.document import Document, DocumentStatus

    # Get all READY docs
    result = await session.execute(
        select(Document.id, Document.kb_id)
        .where(Document.status == DocumentStatus.READY)
        .where(Document.deleted_at.is_(None))
    )
    ready_docs = result.all()

    missing_vectors = []
    for doc_id, kb_id in ready_docs:
        try:
            # Check if collection exists and has points for this doc
            if not await qdrant_service.collection_exists(kb_id):
                missing_vectors.append({"id": doc_id, "kb_id": kb_id})
                continue

            # Check if document has any points in the collection
            from qdrant_client.http import models as qdrant_models

            count_result = qdrant_service.client.count(
                collection_name=f"kb_{kb_id}",
                count_filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="document_id",
                            match=qdrant_models.MatchValue(value=str(doc_id)),
                        )
                    ]
                ),
            )

            if count_result.count == 0:
                missing_vectors.append({"id": doc_id, "kb_id": kb_id})

        except Exception as e:
            logger.warning(
                "reconciliation_vector_check_failed",
                document_id=str(doc_id),
                kb_id=str(kb_id),
                error=str(e),
            )
            # Assume missing on error
            missing_vectors.append({"id": doc_id, "kb_id": kb_id})

    return missing_vectors


async def _detect_stale_processing(session) -> list[dict]:
    """Find documents stuck in PROCESSING status for > 10 minutes.

    Tech Debt Fix P2: Reduced threshold from 30 to 10 minutes for faster recovery.
    """
    from datetime import timedelta

    from app.models.document import Document, DocumentStatus

    # Tech Debt Fix P2: Reduced from 30 to 10 minutes
    stale_threshold = datetime.now(UTC) - timedelta(minutes=10)

    result = await session.execute(
        select(Document.id, Document.kb_id, Document.processing_started_at)
        .where(Document.status == DocumentStatus.PROCESSING)
        .where(Document.deleted_at.is_(None))
        .where(Document.processing_started_at < stale_threshold)
    )
    stale_docs = result.all()

    return [
        {
            "id": doc_id,
            "kb_id": kb_id,
            "processing_started_at": processing_started_at,
        }
        for doc_id, kb_id, processing_started_at in stale_docs
    ]


async def _detect_orphan_vectors(session, qdrant_service) -> list[dict]:
    """Find vectors in Qdrant without corresponding documents in PostgreSQL."""
    from app.models.document import Document
    from app.models.knowledge_base import KnowledgeBase

    orphans = []

    # Get all active KBs
    kb_result = await session.execute(
        select(KnowledgeBase.id).where(KnowledgeBase.status == "active")
    )
    kb_ids = [kb_id for (kb_id,) in kb_result.all()]

    for kb_id in kb_ids:
        try:
            if not await qdrant_service.collection_exists(kb_id):
                continue

            # Get unique document_ids from Qdrant
            points, _ = qdrant_service.client.scroll(
                collection_name=f"kb_{kb_id}",
                limit=10000,
                with_payload=["document_id"],
            )

            qdrant_doc_ids = {
                p.payload.get("document_id")
                for p in points
                if p.payload and p.payload.get("document_id")
            }

            # Check each against PostgreSQL
            for doc_id_str in qdrant_doc_ids:
                try:
                    from uuid import UUID

                    doc_uuid = UUID(doc_id_str)
                    doc_result = await session.execute(
                        select(Document.id)
                        .where(Document.id == doc_uuid)
                        .where(Document.deleted_at.is_(None))
                    )
                    if doc_result.scalar_one_or_none() is None:
                        orphans.append(
                            {
                                "kb_id": kb_id,
                                "document_id": doc_id_str,
                            }
                        )
                except (ValueError, TypeError):
                    # Invalid UUID format
                    orphans.append(
                        {
                            "kb_id": kb_id,
                            "document_id": doc_id_str,
                        }
                    )

        except Exception as e:
            logger.warning(
                "reconciliation_orphan_vector_scan_failed",
                kb_id=str(kb_id),
                error=str(e),
            )

    return orphans


async def _detect_orphan_files(session, minio_service) -> list[dict]:
    """Find files in MinIO without corresponding documents in PostgreSQL."""
    from app.models.document import Document
    from app.models.knowledge_base import KnowledgeBase

    orphans = []

    # Get all active KBs
    kb_result = await session.execute(
        select(KnowledgeBase.id).where(KnowledgeBase.status == "active")
    )
    kb_ids = [kb_id for (kb_id,) in kb_result.all()]

    for kb_id in kb_ids:
        try:
            # List all objects in KB bucket
            object_keys = await minio_service.list_objects(kb_id)

            # Extract document IDs from file paths
            # Format: {doc_id}/{filename} or {doc_id}/parsed/{filename}
            doc_ids_in_minio = set()
            for key in object_keys:
                parts = key.split("/")
                if parts:
                    doc_ids_in_minio.add(parts[0])

            # Check each against PostgreSQL
            for doc_id_str in doc_ids_in_minio:
                try:
                    from uuid import UUID

                    doc_uuid = UUID(doc_id_str)
                    doc_result = await session.execute(
                        select(Document.id)
                        .where(Document.id == doc_uuid)
                        .where(Document.kb_id == kb_id)
                        .where(Document.deleted_at.is_(None))
                    )
                    if doc_result.scalar_one_or_none() is None:
                        # Find the actual file paths for this orphan
                        for key in object_keys:
                            if key.startswith(f"{doc_id_str}/"):
                                orphans.append(
                                    {
                                        "kb_id": kb_id,
                                        "file_path": key,
                                    }
                                )
                except (ValueError, TypeError):
                    # Invalid UUID format in path
                    continue

        except Exception as e:
            logger.warning(
                "reconciliation_orphan_file_scan_failed",
                kb_id=str(kb_id),
                error=str(e),
            )

    return orphans


async def _create_reprocess_event(session, document_id, kb_id, reason: str) -> None:
    """Create a document.reprocess outbox event."""
    from uuid import uuid4

    event = Outbox(
        id=uuid4(),
        event_type="document.reprocess",
        aggregate_type="document",
        aggregate_id=document_id,
        payload={
            "document_id": str(document_id),
            "kb_id": str(kb_id),
            "reason": reason,
        },
    )
    session.add(event)


# =============================================================================
# Cleanup Job (AC: 6)
# =============================================================================


@celery_app.task(name="app.workers.outbox_tasks.cleanup_processed_outbox_events")
def cleanup_processed_outbox_events() -> dict:
    """Daily cleanup job for old outbox events.

    Deletes:
    - Processed events older than 7 days
    - Failed events (attempts >= 5) older than 30 days

    Returns:
        Dict with deletion counts.
    """
    logger.info("outbox_cleanup_started")

    try:
        result = run_async(_run_cleanup())
        return result
    except Exception as e:
        logger.error("outbox_cleanup_failed", error=str(e))
        return {"error": str(e)}


async def _run_cleanup() -> dict:
    """Execute cleanup of old outbox events."""
    from datetime import timedelta

    from sqlalchemy import delete, func

    async with celery_session_factory() as session:
        # Delete processed events older than 7 days
        processed_threshold = datetime.now(UTC) - timedelta(days=7)
        processed_result = await session.execute(
            delete(Outbox)
            .where(Outbox.processed_at.isnot(None))
            .where(Outbox.processed_at < processed_threshold)
            .returning(func.count())
        )
        processed_deleted = processed_result.scalar() or 0

        # Delete failed events older than 30 days
        failed_threshold = datetime.now(UTC) - timedelta(days=30)
        failed_result = await session.execute(
            delete(Outbox)
            .where(Outbox.attempts >= MAX_OUTBOX_ATTEMPTS)
            .where(Outbox.created_at < failed_threshold)
            .returning(func.count())
        )
        failed_deleted = failed_result.scalar() or 0

        await session.commit()

    logger.info(
        "outbox_cleanup_completed",
        processed_deleted=processed_deleted,
        failed_deleted=failed_deleted,
    )

    return {
        "processed_deleted": processed_deleted,
        "failed_deleted": failed_deleted,
    }
