"""Document processing Celery task.

Handles full document processing pipeline:
1. Download from MinIO
2. Parse based on MIME type
3. Chunk into semantic pieces
4. Generate embeddings via LiteLLM
5. Index in Qdrant

Status transitions: PENDING → PROCESSING → READY | FAILED
"""

import asyncio
import hashlib
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import structlog
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import select, update

from app.core.config import settings
from app.core.database import async_session_factory
from app.integrations.minio_client import minio_service
from app.models.document import Document, DocumentStatus
from app.models.outbox import Outbox
from app.workers.celery_app import celery_app
from app.workers.parsed_content_storage import (
    delete_parsed_content,
    load_parsed_content,
    store_parsed_content,
)
from app.workers.parsing import (
    InsufficientContentError,
    ParsingError,
    PasswordProtectedError,
    ScannedDocumentError,
    parse_document,
)

logger = structlog.get_logger(__name__)


def run_async(coro):
    """Run async coroutine in sync context for Celery tasks.

    Always runs in a fresh event loop. For production Celery workers,
    this is the normal execution path. For tests, run_async is typically
    mocked or patched to avoid actual async execution.
    """
    return asyncio.run(coro)


class DocumentProcessingError(Exception):
    """Error during document processing."""

    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


async def _get_document(doc_id: str) -> Document | None:
    """Fetch document from database."""
    async with async_session_factory() as session:
        result = await session.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()


async def _update_document_status(
    doc_id: str,
    status: DocumentStatus,
    error: str | None = None,
    processing_started: bool = False,
    processing_completed: bool = False,
    retry_count: int | None = None,
    chunk_count: int | None = None,
) -> None:
    """Update document status and related fields."""
    async with async_session_factory() as session:
        values = {"status": status}

        if error is not None:
            values["last_error"] = error[:1000]  # Truncate long errors

        if processing_started:
            values["processing_started_at"] = datetime.now(UTC)

        if processing_completed:
            values["processing_completed_at"] = datetime.now(UTC)

        if retry_count is not None:
            values["retry_count"] = retry_count

        if chunk_count is not None:
            values["chunk_count"] = chunk_count

        await session.execute(
            update(Document).where(Document.id == doc_id).values(**values)
        )
        await session.commit()


async def _mark_outbox_processed(aggregate_id: str) -> None:
    """Mark outbox event as processed for this document."""
    async with async_session_factory() as session:
        await session.execute(
            update(Outbox)
            .where(Outbox.aggregate_id == aggregate_id)
            .where(Outbox.event_type == "document.process")
            .values(processed_at=datetime.now(UTC))
        )
        await session.commit()


def _validate_checksum(file_data: bytes, expected_checksum: str) -> bool:
    """Validate file checksum matches expected value."""
    actual = hashlib.sha256(file_data).hexdigest()
    return actual == expected_checksum


def _cleanup_temp_dir(temp_dir: str) -> None:
    """Clean up temporary directory."""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.debug("temp_dir_cleaned", temp_dir=temp_dir)
    except Exception as e:
        logger.warning("temp_dir_cleanup_failed", temp_dir=temp_dir, error=str(e))


async def _chunk_embed_index(
    doc_id: str,
    kb_id: UUID,
    document_name: str,
    is_replacement: bool = False,
) -> int:
    """Chunk, embed, and index document content.

    Loads parsed content from MinIO, chunks it, generates embeddings,
    and indexes in Qdrant.

    For replacement flow (is_replacement=True), performs atomic vector switch:
    - Generates new embeddings first
    - THEN deletes old vectors
    - THEN upserts new vectors
    This ensures old vectors remain searchable until new ones are ready (AC3, AC4).

    Args:
        doc_id: Document UUID as string.
        kb_id: Knowledge Base UUID.
        document_name: Original filename.
        is_replacement: If True, perform atomic switch (delete old before upsert new).

    Returns:
        Number of chunks indexed.

    Raises:
        DocumentProcessingError: If chunking, embedding, or indexing fails.
    """
    from app.workers.chunking import ChunkingError, chunk_document
    from app.workers.embedding import EmbeddingGenerationError, generate_embeddings
    from app.workers.indexing import (
        IndexingError,
        cleanup_orphan_chunks,
        delete_document_vectors,
        index_document,
    )

    logger.info(
        "chunk_embed_index_started",
        document_id=doc_id,
        kb_id=str(kb_id),
        is_replacement=is_replacement,
    )

    # 1. Load parsed content from MinIO
    parsed_content = await load_parsed_content(kb_id, UUID(doc_id))
    if not parsed_content:
        raise DocumentProcessingError(
            "Parsed content not found in MinIO",
            retryable=True,
        )

    # 2. Chunk the document
    try:
        chunks = chunk_document(
            parsed_content=parsed_content,
            document_id=doc_id,
            document_name=document_name,
        )
    except ChunkingError as e:
        raise DocumentProcessingError(f"Chunking failed: {e}", retryable=True) from e

    if not chunks:
        logger.warning("no_chunks_created", document_id=doc_id)
        # For replacement with no chunks, still delete old vectors
        if is_replacement:
            await delete_document_vectors(doc_id, kb_id)
        return 0

    # 3. Generate embeddings
    try:
        embeddings = await generate_embeddings(chunks)
    except EmbeddingGenerationError as e:
        # Check if rate limit error (non-retryable after max retries)
        if "rate limit exceeded" in str(e).lower():
            raise DocumentProcessingError(str(e), retryable=False) from e
        raise DocumentProcessingError(f"Embedding failed: {e}", retryable=True) from e

    # 4. For replacement: DELETE old vectors BEFORE upserting new ones (atomic switch)
    # This is the critical point - old vectors available until we have new ones ready
    if is_replacement:
        logger.info(
            "replacement_deleting_old_vectors",
            document_id=doc_id,
            kb_id=str(kb_id),
        )
        deleted_count = await delete_document_vectors(doc_id, kb_id)
        logger.info(
            "replacement_old_vectors_deleted",
            document_id=doc_id,
            kb_id=str(kb_id),
            deleted_count=deleted_count,
        )

    # 5. Index in Qdrant (upsert new vectors)
    try:
        chunk_count = await index_document(
            doc_id=doc_id,
            kb_id=kb_id,
            embeddings=embeddings,
        )
    except IndexingError as e:
        raise DocumentProcessingError(f"Indexing failed: {e}", retryable=False) from e

    # 6. Clean up orphan chunks from previous versions (non-replacement scenario)
    # For replacements, we already deleted all old vectors, so skip this
    if not is_replacement:
        max_chunk_index = len(chunks) - 1
        await cleanup_orphan_chunks(doc_id, kb_id, max_chunk_index)

    logger.info(
        "chunk_embed_index_completed",
        document_id=doc_id,
        kb_id=str(kb_id),
        chunk_count=chunk_count,
        is_replacement=is_replacement,
    )

    return chunk_count


@celery_app.task(
    bind=True,
    name="app.workers.document_tasks.process_document",
    max_retries=settings.max_parsing_retries,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=300,
    soft_time_limit=540,  # 9 minutes soft limit
    time_limit=600,  # 10 minutes hard limit
    acks_late=True,
    reject_on_worker_lost=True,
    queue="document_processing",
)
def process_document(self, doc_id: str, is_replacement: bool = False) -> dict:
    """Process a document: download, parse, validate, store for chunking.

    This task handles the parsing phase of document processing:
    1. Update status to PROCESSING
    2. Download file from MinIO
    3. Validate checksum
    4. Parse based on MIME type
    5. Validate extracted content (>= 100 chars)
    6. Store parsed content for chunking (Story 2.6)

    For replacement flow (is_replacement=True), performs atomic vector switch:
    - Old vectors remain searchable until new ones are ready
    - After successful embedding, deletes old vectors then upserts new

    Args:
        doc_id: Document UUID as string.
        is_replacement: If True, perform atomic vector switch for document replacement.

    Returns:
        Dict with processing result.
    """
    task_id = self.request.id or "unknown"
    temp_dir = None

    logger.info(
        "document_processing_started",
        document_id=doc_id,
        task_id=task_id,
        retry=self.request.retries,
        is_replacement=is_replacement,
    )

    try:
        # 1. Get document from database
        document = run_async(_get_document(doc_id))
        if not document:
            logger.error("document_not_found", document_id=doc_id)
            return {"status": "error", "reason": "Document not found"}

        kb_id = document.kb_id
        file_path = document.file_path
        checksum = document.checksum
        mime_type = document.mime_type

        if not file_path:
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error="Document has no file path",
                )
            )
            return {"status": "error", "reason": "No file path"}

        # Extract object path from file_path (format: kb-{uuid}/{object_path})
        # file_path is stored as "kb-{kb_id}/{doc_id}/{filename}"
        path_parts = file_path.split("/", 1)
        if len(path_parts) != 2:
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error=f"Invalid file path format: {file_path}",
                )
            )
            return {"status": "error", "reason": "Invalid file path"}

        object_path = path_parts[1]

        # 2. Update status to PROCESSING
        run_async(
            _update_document_status(
                doc_id,
                DocumentStatus.PROCESSING,
                processing_started=True,
            )
        )

        # 3. Download file from MinIO
        logger.info(
            "downloading_document",
            document_id=doc_id,
            kb_id=str(kb_id),
            object_path=object_path,
        )

        try:
            file_data = run_async(minio_service.download_file(kb_id, object_path))
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to download file: {e}",
                retryable=True,
            ) from e

        # 4. Validate checksum
        if not _validate_checksum(file_data, checksum):
            raise DocumentProcessingError(
                "Checksum mismatch - file may be corrupted",
                retryable=False,
            )

        # 5. Save to temp directory for parsing
        temp_dir = tempfile.mkdtemp(prefix=f"lumikb-{task_id}-")
        filename = Path(object_path).name
        local_path = os.path.join(temp_dir, filename)

        with open(local_path, "wb") as f:
            f.write(file_data)

        logger.info(
            "document_downloaded",
            document_id=doc_id,
            local_path=local_path,
            file_size=len(file_data),
        )

        # 6. Parse document based on MIME type
        try:
            parsed_content = parse_document(local_path, mime_type)
        except PasswordProtectedError:
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error="Password-protected PDF cannot be processed",
                    retry_count=settings.max_parsing_retries,  # Mark max retries to stop
                )
            )
            run_async(_mark_outbox_processed(doc_id))
            return {
                "status": "failed",
                "reason": "password_protected",
                "document_id": doc_id,
            }
        except ScannedDocumentError:
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error="Document appears to be scanned (OCR required - MVP 2)",
                    retry_count=settings.max_parsing_retries,
                )
            )
            run_async(_mark_outbox_processed(doc_id))
            return {
                "status": "failed",
                "reason": "scanned_document",
                "document_id": doc_id,
            }
        except InsufficientContentError as e:
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error=str(e),
                    retry_count=settings.max_parsing_retries,
                )
            )
            run_async(_mark_outbox_processed(doc_id))
            return {
                "status": "failed",
                "reason": "insufficient_content",
                "document_id": doc_id,
                "extracted_chars": 0,
            }
        except ParsingError as e:
            raise DocumentProcessingError(str(e), retryable=True) from e

        # 7. Store parsed content temporarily
        run_async(
            store_parsed_content(
                kb_id=kb_id,
                document_id=UUID(doc_id),
                parsed=parsed_content,
            )
        )

        logger.info(
            "document_parsing_completed",
            document_id=doc_id,
            extracted_chars=parsed_content.extracted_chars,
            page_count=parsed_content.page_count,
            section_count=parsed_content.section_count,
        )

        # 8. Chunk, embed, and index the document
        # For replacement flow, performs atomic vector switch (delete old, upsert new)
        chunk_count = run_async(
            _chunk_embed_index(
                doc_id=doc_id,
                kb_id=kb_id,
                document_name=filename,
                is_replacement=is_replacement,
            )
        )

        # 9. Update document status to READY
        run_async(
            _update_document_status(
                doc_id,
                DocumentStatus.READY,
                processing_completed=True,
                chunk_count=chunk_count,
            )
        )

        # 10. Clean up parsed content from MinIO
        run_async(delete_parsed_content(kb_id, UUID(doc_id)))

        # Mark outbox as processed
        run_async(_mark_outbox_processed(doc_id))

        logger.info(
            "document_processing_completed",
            document_id=doc_id,
            chunk_count=chunk_count,
            status="READY",
        )

        return {
            "status": "success",
            "document_id": doc_id,
            "extracted_chars": parsed_content.extracted_chars,
            "page_count": parsed_content.page_count,
            "section_count": parsed_content.section_count,
            "chunk_count": chunk_count,
        }

    except DocumentProcessingError as e:
        logger.warning(
            "document_processing_error",
            document_id=doc_id,
            error=str(e),
            retryable=e.retryable,
            retry=self.request.retries,
        )

        if e.retryable:
            try:
                # Update retry count
                run_async(
                    _update_document_status(
                        doc_id,
                        DocumentStatus.PROCESSING,
                        retry_count=self.request.retries + 1,
                    )
                )
                raise self.retry(exc=e)
            except MaxRetriesExceededError:
                # Max retries exhausted
                run_async(
                    _update_document_status(
                        doc_id,
                        DocumentStatus.FAILED,
                        error=str(e),
                        retry_count=settings.max_parsing_retries,
                    )
                )
                run_async(_mark_outbox_processed(doc_id))
                return {
                    "status": "failed",
                    "reason": "max_retries_exhausted",
                    "document_id": doc_id,
                    "error": str(e),
                }
        else:
            # Non-retryable error
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error=str(e),
                    retry_count=settings.max_parsing_retries,
                )
            )
            run_async(_mark_outbox_processed(doc_id))
            return {
                "status": "failed",
                "reason": "non_retryable_error",
                "document_id": doc_id,
                "error": str(e),
            }

    except Exception as e:
        logger.exception(
            "document_processing_unexpected_error",
            document_id=doc_id,
            error=str(e),
        )

        try:
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.PROCESSING,
                    retry_count=self.request.retries + 1,
                )
            )
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error=f"Unexpected error: {str(e)[:500]}",
                    retry_count=settings.max_parsing_retries,
                )
            )
            run_async(_mark_outbox_processed(doc_id))
            return {
                "status": "failed",
                "reason": "unexpected_error",
                "document_id": doc_id,
                "error": str(e),
            }

    finally:
        # 8. Clean up temporary files
        if temp_dir:
            _cleanup_temp_dir(temp_dir)


async def _mark_outbox_delete_processed(aggregate_id: str) -> None:
    """Mark outbox delete event as processed for this document."""
    async with async_session_factory() as session:
        await session.execute(
            update(Outbox)
            .where(Outbox.aggregate_id == aggregate_id)
            .where(Outbox.event_type == "document.delete")
            .values(processed_at=datetime.now(UTC))
        )
        await session.commit()


async def _delete_document_vectors(doc_id: str, kb_id: str) -> int:
    """Delete all vectors for a document from Qdrant.

    Args:
        doc_id: Document UUID as string.
        kb_id: Knowledge Base UUID as string.

    Returns:
        Number of vectors deleted.
    """
    from qdrant_client.http import models

    from app.integrations.qdrant_client import qdrant_service

    kb_uuid = UUID(kb_id)

    # Check if collection exists
    if not await qdrant_service.collection_exists(kb_uuid):
        logger.warning(
            "qdrant_collection_not_found_for_delete",
            document_id=doc_id,
            kb_id=kb_id,
        )
        return 0

    # Create filter for document_id in payload
    filter_conditions = models.Filter(
        must=[
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=doc_id),
            )
        ]
    )

    deleted_count = await qdrant_service.delete_points_by_filter(
        kb_id=kb_uuid,
        filter_conditions=filter_conditions,
    )

    logger.info(
        "document_vectors_deleted",
        document_id=doc_id,
        kb_id=kb_id,
        deleted_count=deleted_count,
    )

    return deleted_count


async def _delete_document_files(kb_id: str, file_path: str | None) -> bool:
    """Delete document files from MinIO.

    Args:
        kb_id: Knowledge Base UUID as string.
        file_path: Full file path in format "kb-{kb_id}/{doc_id}/{filename}".

    Returns:
        True if deletion succeeded, False otherwise.
    """
    if not file_path:
        logger.warning(
            "no_file_path_for_delete",
            kb_id=kb_id,
        )
        return True  # Nothing to delete

    try:
        # Extract object path from file_path (format: kb-{kb_id}/{object_path})
        path_parts = file_path.split("/", 1)
        if len(path_parts) != 2:
            logger.warning(
                "invalid_file_path_format",
                file_path=file_path,
                kb_id=kb_id,
            )
            return True  # Can't parse, assume nothing to delete

        object_path = path_parts[1]
        kb_uuid = UUID(kb_id)

        # Delete the file
        await minio_service.delete_file(kb_uuid, object_path)

        logger.info(
            "document_file_deleted",
            kb_id=kb_id,
            object_path=object_path,
        )
        return True

    except Exception as e:
        logger.error(
            "document_file_delete_failed",
            kb_id=kb_id,
            file_path=file_path,
            error=str(e),
        )
        raise


@celery_app.task(
    bind=True,
    name="app.workers.document_tasks.delete_document_cleanup",
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=300,
    soft_time_limit=120,
    time_limit=180,
    acks_late=True,
    reject_on_worker_lost=True,
    queue="document_processing",
)
def delete_document_cleanup(
    self,
    doc_id: str,
    kb_id: str,
    file_path: str | None = None,
) -> dict:
    """Clean up vectors and files for a deleted document.

    This task handles the cleanup phase after a document is soft-deleted:
    1. Delete all vectors from Qdrant for this document
    2. Delete the file from MinIO
    3. Delete any parsed content from MinIO
    4. Mark outbox event as processed

    Args:
        doc_id: Document UUID as string.
        kb_id: Knowledge Base UUID as string.
        file_path: Optional file path in MinIO.

    Returns:
        Dict with cleanup result.
    """
    task_id = self.request.id or "unknown"

    logger.info(
        "document_cleanup_started",
        document_id=doc_id,
        kb_id=kb_id,
        task_id=task_id,
        retry=self.request.retries,
    )

    try:
        # 1. Delete vectors from Qdrant
        deleted_vectors = run_async(_delete_document_vectors(doc_id, kb_id))

        # 2. Delete files from MinIO
        run_async(_delete_document_files(kb_id, file_path))

        # 3. Delete any parsed content (may not exist)
        try:
            run_async(delete_parsed_content(UUID(kb_id), UUID(doc_id)))
        except Exception as e:
            # Non-fatal - parsed content may not exist
            logger.debug(
                "parsed_content_delete_skipped",
                document_id=doc_id,
                error=str(e),
            )

        # 4. Mark outbox event as processed
        run_async(_mark_outbox_delete_processed(doc_id))

        logger.info(
            "document_cleanup_completed",
            document_id=doc_id,
            kb_id=kb_id,
            deleted_vectors=deleted_vectors,
        )

        return {
            "status": "success",
            "document_id": doc_id,
            "kb_id": kb_id,
            "deleted_vectors": deleted_vectors,
        }

    except Exception as e:
        logger.error(
            "document_cleanup_failed",
            document_id=doc_id,
            kb_id=kb_id,
            error=str(e),
            retry=self.request.retries,
        )

        try:
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            # Log admin alert for manual intervention
            logger.error(
                "document_cleanup_max_retries_exhausted",
                document_id=doc_id,
                kb_id=kb_id,
                error=str(e),
                alert="ADMIN_INTERVENTION_REQUIRED",
            )
            return {
                "status": "failed",
                "document_id": doc_id,
                "kb_id": kb_id,
                "error": str(e),
                "admin_alert": True,
            }
