"""Document processing Celery task.

Handles full document processing pipeline:
1. Download from MinIO
2. Parse based on MIME type
3. Chunk into semantic pieces
4. Generate embeddings via LiteLLM
5. Index in Qdrant

Status transitions: PENDING → PROCESSING → READY | FAILED

Story 9-4: Instrumented with observability traces and spans for each processing step.
"""

import asyncio
import hashlib
import os
import shutil
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import structlog
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import select, update

from app.core.config import settings
from app.core.database import celery_session_factory
from app.integrations.minio_client import minio_service
from app.models.document import Document, DocumentStatus, ProcessingStep, StepStatus
from app.models.outbox import Outbox
from app.services.observability_service import (
    ObservabilityService,
    TraceContext,
)
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


class DocumentProcessingError(Exception):
    """Error during document processing."""

    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


async def _get_document(doc_id: str) -> Document | None:
    """Fetch document from database."""
    async with celery_session_factory() as session:
        result = await session.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()


# Default fallback if no model configured in registry
_FALLBACK_EMBEDDING_DIMENSIONS = 768


async def _get_default_embedding_dimensions() -> int:
    """Get embedding dimensions from the system default embedding model.

    Queries the model registry to find the default embedding model and
    returns its configured dimensions. Falls back to 768 if no default
    model is configured.

    Returns:
        int: The dimensions for the default embedding model.
    """
    from app.models.llm_model import LLMModel, ModelStatus, ModelType

    async with celery_session_factory() as session:
        result = await session.execute(
            select(LLMModel)
            .where(LLMModel.type == ModelType.EMBEDDING.value)
            .where(LLMModel.is_default == True)  # noqa: E712
            .where(LLMModel.status == ModelStatus.ACTIVE.value)
        )
        default_model = result.scalar_one_or_none()

        if default_model and default_model.config:
            dimensions = default_model.config.get(
                "dimensions", _FALLBACK_EMBEDDING_DIMENSIONS
            )
            logger.debug(
                "default_embedding_dimensions_loaded",
                model_id=default_model.model_id,
                dimensions=dimensions,
            )
            return dimensions

        logger.warning(
            "no_default_embedding_model_configured",
            fallback_dimensions=_FALLBACK_EMBEDDING_DIMENSIONS,
        )
        return _FALLBACK_EMBEDDING_DIMENSIONS


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
    async with celery_session_factory() as session:
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


async def _update_step_status(
    doc_id: str,
    step: ProcessingStep,
    step_status: StepStatus,
    error: str | None = None,
) -> None:
    """Update processing step status for a document.

    Story 5-23: Tracks step-level progress for document processing.

    Args:
        doc_id: Document UUID as string.
        step: The processing step (upload, parse, chunk, embed, index, complete).
        step_status: The status of the step (pending, in_progress, done, error, skipped).
        error: Optional error message for failed steps.
    """
    async with celery_session_factory() as session:
        # Get current document
        result = await session.execute(select(Document).where(Document.id == doc_id))
        document = result.scalar_one_or_none()

        if not document:
            logger.warning("document_not_found_for_step_update", document_id=doc_id)
            return

        # Get or initialize processing_steps and step_errors
        processing_steps = (
            dict(document.processing_steps) if document.processing_steps else {}
        )
        step_errors = dict(document.step_errors) if document.step_errors else {}

        now = datetime.now(UTC)
        step_key = step.value

        # Initialize step data if not exists
        if step_key not in processing_steps:
            processing_steps[step_key] = {}

        step_data = processing_steps[step_key]

        # Update step data based on status
        if step_status == StepStatus.IN_PROGRESS:
            step_data["status"] = step_status.value
            step_data["started_at"] = now.isoformat()
        elif step_status in (StepStatus.DONE, StepStatus.ERROR, StepStatus.SKIPPED):
            step_data["status"] = step_status.value
            step_data["completed_at"] = now.isoformat()
            # Calculate duration if started_at exists
            if "started_at" in step_data:
                started = datetime.fromisoformat(step_data["started_at"])
                duration_ms = int((now - started).total_seconds() * 1000)
                step_data["duration_ms"] = duration_ms
        else:
            step_data["status"] = step_status.value

        processing_steps[step_key] = step_data

        # Update step_errors: add error if provided, clear if step succeeded
        if error:
            step_errors[step_key] = error[:1000]  # Truncate long errors
        elif step_status == StepStatus.DONE and step_key in step_errors:
            # Clear previous error when step succeeds (e.g., on retry)
            del step_errors[step_key]

        # Build update values
        values = {
            "current_step": step.value,
            "processing_steps": processing_steps,
            "step_errors": step_errors,
        }

        await session.execute(
            update(Document).where(Document.id == doc_id).values(**values)
        )
        await session.commit()

        logger.debug(
            "step_status_updated",
            document_id=doc_id,
            step=step.value,
            status=step_status.value,
            has_error=error is not None,
        )


async def _mark_step_complete(doc_id: str, step: ProcessingStep) -> None:
    """Mark a processing step as complete."""
    await _update_step_status(doc_id, step, StepStatus.DONE)


async def _mark_step_error(doc_id: str, step: ProcessingStep, error: str) -> None:
    """Mark a processing step as failed with error."""
    await _update_step_status(doc_id, step, StepStatus.ERROR, error)


async def _mark_step_in_progress(doc_id: str, step: ProcessingStep) -> None:
    """Mark a processing step as in progress."""
    await _update_step_status(doc_id, step, StepStatus.IN_PROGRESS)


async def _mark_outbox_processed(aggregate_id: str) -> None:
    """Mark outbox event as processed for this document."""
    async with celery_session_factory() as session:
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


async def _get_kb_parser_backend(kb_id: UUID) -> str:
    """Fetch KB's parser backend configuration for document processing.

    Story 7-32 (AC-7.32.5): Get KB-specific parser backend setting.

    Args:
        kb_id: Knowledge Base UUID.

    Returns:
        Parser backend string ('unstructured', 'docling', 'auto') from KB settings
        or 'unstructured' as default.
    """
    from app.models.knowledge_base import KnowledgeBase
    from app.schemas.kb_settings import DocumentParserBackend, KBSettings

    async with celery_session_factory() as session:
        result = await session.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()

        if not kb or not kb.settings:
            logger.debug(
                "kb_no_parser_config",
                kb_id=str(kb_id),
                using_default="unstructured",
            )
            return DocumentParserBackend.UNSTRUCTURED.value

        try:
            kb_settings = KBSettings.model_validate(kb.settings)
            parser_backend = kb_settings.processing.parser_backend.value

            logger.info(
                "kb_parser_backend_loaded",
                kb_id=str(kb_id),
                parser_backend=parser_backend,
            )
            return parser_backend
        except Exception as e:
            logger.warning(
                "kb_parser_config_parse_error",
                kb_id=str(kb_id),
                error=str(e),
            )
            return DocumentParserBackend.UNSTRUCTURED.value


async def _get_kb_chunking_config(kb_id: UUID) -> tuple[int, int]:
    """Fetch KB's chunking configuration for document processing.

    Story 7-17 (AC-7.17.4): Get KB-specific chunking settings.

    Args:
        kb_id: Knowledge Base UUID.

    Returns:
        Tuple of (chunk_size, chunk_overlap) from KB settings or system defaults.
    """
    from app.models.knowledge_base import KnowledgeBase
    from app.schemas.kb_settings import KBSettings

    async with celery_session_factory() as session:
        result = await session.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()

        if not kb or not kb.settings:
            logger.debug(
                "kb_no_chunking_config",
                kb_id=str(kb_id),
                using_defaults=True,
            )
            # Return system defaults
            return settings.chunk_size, settings.chunk_overlap

        try:
            # Parse KB settings and extract chunking config
            kb_settings = KBSettings.model_validate(kb.settings)
            chunk_size = kb_settings.chunking.chunk_size
            chunk_overlap = kb_settings.chunking.chunk_overlap

            logger.info(
                "kb_chunking_config_loaded",
                kb_id=str(kb_id),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            return chunk_size, chunk_overlap
        except Exception as e:
            logger.warning(
                "kb_chunking_config_parse_error",
                kb_id=str(kb_id),
                error=str(e),
            )
            return settings.chunk_size, settings.chunk_overlap


async def _get_kb_embedding_config(kb_id: UUID):
    """Fetch KB's embedding model configuration for document processing.

    Story 7-10 (AC-7.10.8): Get KB-specific embedding model settings.

    Args:
        kb_id: Knowledge Base UUID.

    Returns:
        EmbeddingConfig if KB has configured embedding model, None otherwise.
    """
    from sqlalchemy.orm import joinedload

    from app.models.knowledge_base import KnowledgeBase
    from app.workers.embedding import DEFAULT_EMBEDDING_DIMENSIONS, EmbeddingConfig

    async with celery_session_factory() as session:
        result = await session.execute(
            select(KnowledgeBase)
            .options(joinedload(KnowledgeBase.embedding_model))
            .where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()

        if not kb or not kb.embedding_model:
            logger.debug(
                "kb_no_embedding_model_configured",
                kb_id=str(kb_id),
            )
            return None

        # Extract model configuration
        model = kb.embedding_model
        dimensions = (
            model.config.get("dimensions", DEFAULT_EMBEDDING_DIMENSIONS)
            if model.config
            else DEFAULT_EMBEDDING_DIMENSIONS
        )
        api_endpoint = model.api_endpoint

        logger.info(
            "kb_embedding_config_loaded",
            kb_id=str(kb_id),
            model_id=model.model_id,
            dimensions=dimensions,
            provider=model.provider,
            has_custom_endpoint=api_endpoint is not None,
        )

        return EmbeddingConfig(
            model_id=model.model_id,
            dimensions=dimensions,
            api_endpoint=api_endpoint,
            provider=model.provider,
        )


async def _chunk_embed_index(
    doc_id: str,
    kb_id: UUID,
    document_name: str,
    is_replacement: bool = False,
    trace_ctx: TraceContext | None = None,
) -> int:
    """Chunk, embed, and index document content.

    Loads parsed content from MinIO, chunks it, generates embeddings,
    and indexes in Qdrant. Tracks step-level progress (Story 5-23).

    Story 7-10 (AC-7.10.8-9): Uses KB-configured embedding model if set.
    Falls back to system default if KB has no embedding model configured.

    Story 9-4: Instrumented with observability spans for chunk, embed, index steps.

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
        trace_ctx: Optional TraceContext for observability instrumentation.

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

    # Story 7-10 (AC-7.10.8): Fetch KB embedding configuration
    embedding_config = await _get_kb_embedding_config(kb_id)

    # Story 7-17 (AC-7.17.4): Fetch KB chunking configuration
    chunk_size, chunk_overlap = await _get_kb_chunking_config(kb_id)

    logger.info(
        "chunk_embed_index_started",
        document_id=doc_id,
        kb_id=str(kb_id),
        is_replacement=is_replacement,
        embedding_model=embedding_config.model_id if embedding_config else "default",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # 1. Load parsed content from MinIO
    parsed_content = await load_parsed_content(kb_id, UUID(doc_id))
    if not parsed_content:
        await _mark_step_error(
            doc_id, ProcessingStep.CHUNK, "Parsed content not found in MinIO"
        )
        raise DocumentProcessingError(
            "Parsed content not found in MinIO",
            retryable=True,
        )

    # 2. Chunk the document (Story 5-23: track CHUNK step)
    # Story 7-17 (AC-7.17.4): Use KB-configured chunking parameters
    # Story 9-4 (AC4): Chunk span with chunk_count, chunk_size_config, chunk_overlap_config, duration_ms
    await _mark_step_in_progress(doc_id, ProcessingStep.CHUNK)
    chunk_start_time = time.monotonic()
    chunk_error: str | None = None
    total_tokens = 0
    try:
        chunks = chunk_document(
            parsed_content=parsed_content,
            document_id=doc_id,
            document_name=document_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        # Estimate total tokens (roughly 4 chars per token)
        total_tokens = sum(len(chunk.text) // 4 for chunk in chunks) if chunks else 0
    except ChunkingError as e:
        chunk_error = str(e)
        await _mark_step_error(doc_id, ProcessingStep.CHUNK, chunk_error)
        # Log document event for failed chunk step (Story 9-4 AC8)
        if trace_ctx:
            obs = ObservabilityService.get_instance()
            chunk_duration_ms = int((time.monotonic() - chunk_start_time) * 1000)
            await obs.log_document_event(
                ctx=trace_ctx,
                document_id=UUID(doc_id),
                event_type="chunk",
                status="failed",
                duration_ms=chunk_duration_ms,
                error_message=chunk_error,
                metadata={
                    "chunk_size_config": chunk_size,
                    "chunk_overlap_config": chunk_overlap,
                },
            )
            # Create span for trace detail view
            await obs.log_processing_span(
                ctx=trace_ctx,
                name="chunk",
                span_type="processing",
                status="failed",
                duration_ms=chunk_duration_ms,
                error_message=chunk_error,
                metadata={
                    "chunk_size_config": chunk_size,
                    "chunk_overlap_config": chunk_overlap,
                },
            )
        raise DocumentProcessingError(f"Chunking failed: {e}", retryable=True) from e

    chunk_duration_ms = int((time.monotonic() - chunk_start_time) * 1000)

    if not chunks:
        logger.warning("no_chunks_created", document_id=doc_id)
        # Log document event for chunk step with 0 chunks (Story 9-4 AC8)
        if trace_ctx:
            obs = ObservabilityService.get_instance()
            await obs.log_document_event(
                ctx=trace_ctx,
                document_id=UUID(doc_id),
                event_type="chunk",
                status="completed",
                duration_ms=chunk_duration_ms,
                chunk_count=0,
                metadata={
                    "chunk_size_config": chunk_size,
                    "chunk_overlap_config": chunk_overlap,
                },
            )
        # For replacement with no chunks, still delete old vectors
        if is_replacement:
            await delete_document_vectors(doc_id, kb_id)
        await _mark_step_complete(doc_id, ProcessingStep.CHUNK)
        return 0

    await _mark_step_complete(doc_id, ProcessingStep.CHUNK)

    # Log document event for successful chunk step (Story 9-4 AC4, AC8)
    if trace_ctx:
        obs = ObservabilityService.get_instance()
        await obs.log_document_event(
            ctx=trace_ctx,
            document_id=UUID(doc_id),
            event_type="chunk",
            status="completed",
            duration_ms=chunk_duration_ms,
            chunk_count=len(chunks),
            token_count=total_tokens,
            metadata={
                "chunk_size_config": chunk_size,
                "chunk_overlap_config": chunk_overlap,
            },
        )
        # Create span for trace detail view
        await obs.log_processing_span(
            ctx=trace_ctx,
            name="chunk",
            span_type="processing",
            status="completed",
            duration_ms=chunk_duration_ms,
            metadata={
                "chunk_count": len(chunks),
                "token_count": total_tokens,
                "chunk_size_config": chunk_size,
                "chunk_overlap_config": chunk_overlap,
            },
        )

    # 3. Generate embeddings (Story 5-23: track EMBED step)
    # Story 7-10 (AC-7.10.8-9): Use KB-configured embedding model
    # Story 9-4 (AC5): Embed span with embedding_model, dimensions, batch_count, total_tokens_used, duration_ms
    await _mark_step_in_progress(doc_id, ProcessingStep.EMBED)
    embed_start_time = time.monotonic()

    # Reset LiteLLM logging worker to prevent event loop binding issues in Celery
    # See: https://github.com/BerriAI/litellm/issues/6921
    from app.integrations.litellm_client import reset_litellm_logging_worker

    reset_litellm_logging_worker()

    try:
        # AC-7.10.8: Pass KB-specific embedding config to use configured model
        embeddings = await generate_embeddings(chunks, embedding_config)
    except EmbeddingGenerationError as e:
        embed_error = str(e)
        await _mark_step_error(doc_id, ProcessingStep.EMBED, embed_error)
        # Log document event for failed embed step (Story 9-4 AC8)
        if trace_ctx:
            obs = ObservabilityService.get_instance()
            embed_duration_ms = int((time.monotonic() - embed_start_time) * 1000)
            await obs.log_document_event(
                ctx=trace_ctx,
                document_id=UUID(doc_id),
                event_type="embed",
                status="failed",
                duration_ms=embed_duration_ms,
                error_message=embed_error,
                metadata={
                    "embedding_model": embedding_config.model_id
                    if embedding_config
                    else "default",
                    "chunk_count": len(chunks),
                },
            )
            # Create span for trace detail view
            await obs.log_processing_span(
                ctx=trace_ctx,
                name="embed",
                span_type="processing",
                status="failed",
                duration_ms=embed_duration_ms,
                error_message=embed_error,
                metadata={
                    "embedding_model": embedding_config.model_id
                    if embedding_config
                    else "default",
                    "chunk_count": len(chunks),
                },
            )
        # Check if rate limit error (non-retryable after max retries)
        if "rate limit exceeded" in str(e).lower():
            raise DocumentProcessingError(str(e), retryable=False) from e
        raise DocumentProcessingError(f"Embedding failed: {e}", retryable=True) from e

    embed_duration_ms = int((time.monotonic() - embed_start_time) * 1000)
    await _mark_step_complete(doc_id, ProcessingStep.EMBED)

    # Log document event for successful embed step (Story 9-4 AC5, AC8)
    # Get default embedding dimensions once (used for logging and indexing)
    default_dimensions = (
        await _get_default_embedding_dimensions() if not embedding_config else None
    )
    embedding_dimensions = (
        embedding_config.dimensions if embedding_config else default_dimensions
    )

    if trace_ctx:
        obs = ObservabilityService.get_instance()
        # Calculate batch count (assuming default batch size of 100)
        batch_count = (len(chunks) + 99) // 100
        await obs.log_document_event(
            ctx=trace_ctx,
            document_id=UUID(doc_id),
            event_type="embed",
            status="completed",
            duration_ms=embed_duration_ms,
            chunk_count=len(chunks),
            token_count=total_tokens,  # Reuse from chunk step
            metadata={
                "embedding_model": embedding_config.model_id
                if embedding_config
                else "default",
                "dimensions": embedding_dimensions,
                "batch_count": batch_count,
            },
        )
        # Create span for trace detail view
        await obs.log_processing_span(
            ctx=trace_ctx,
            name="embed",
            span_type="processing",
            status="completed",
            duration_ms=embed_duration_ms,
            metadata={
                "embedding_model": embedding_config.model_id
                if embedding_config
                else "default",
                "dimensions": embedding_dimensions,
                "batch_count": batch_count,
                "chunk_count": len(chunks),
            },
        )

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

    # 5. Index in Qdrant (Story 5-23: track INDEX step)
    # Story 9-4 (AC6): Index span with qdrant_collection, vectors_indexed, duration_ms
    # Reset Qdrant async client before indexing to prevent "Event loop is closed" errors
    # The client may hold gRPC channels bound to a previous event loop from the embed step
    from app.integrations.qdrant_client import qdrant_service

    qdrant_service.reset_async_client()

    await _mark_step_in_progress(doc_id, ProcessingStep.INDEX)
    index_start_time = time.monotonic()
    # Get vector dimensions from embedding config for collection creation
    # Reuse default_dimensions computed earlier (or compute if needed)
    vector_size = (
        embedding_config.dimensions
        if embedding_config
        else (
            default_dimensions
            if default_dimensions is not None
            else await _get_default_embedding_dimensions()
        )
    )
    try:
        chunk_count = await index_document(
            doc_id=doc_id,
            kb_id=kb_id,
            embeddings=embeddings,
            vector_size=vector_size,
        )
    except IndexingError as e:
        index_error = str(e)
        await _mark_step_error(doc_id, ProcessingStep.INDEX, index_error)
        # Log document event for failed index step (Story 9-4 AC8)
        if trace_ctx:
            obs = ObservabilityService.get_instance()
            index_duration_ms = int((time.monotonic() - index_start_time) * 1000)
            await obs.log_document_event(
                ctx=trace_ctx,
                document_id=UUID(doc_id),
                event_type="index",
                status="failed",
                duration_ms=index_duration_ms,
                error_message=index_error,
                metadata={
                    "qdrant_collection": f"kb_{kb_id}",
                },
            )
            # Create span for trace detail view
            await obs.log_processing_span(
                ctx=trace_ctx,
                name="index",
                span_type="processing",
                status="failed",
                duration_ms=index_duration_ms,
                error_message=index_error,
                metadata={
                    "qdrant_collection": f"kb_{kb_id}",
                },
            )
        raise DocumentProcessingError(f"Indexing failed: {e}", retryable=False) from e

    index_duration_ms = int((time.monotonic() - index_start_time) * 1000)

    # 6. Clean up orphan chunks from previous versions (non-replacement scenario)
    # For replacements, we already deleted all old vectors, so skip this
    if not is_replacement:
        max_chunk_index = len(chunks) - 1
        await cleanup_orphan_chunks(doc_id, kb_id, max_chunk_index)

    await _mark_step_complete(doc_id, ProcessingStep.INDEX)

    # Log document event for successful index step (Story 9-4 AC6, AC8)
    if trace_ctx:
        obs = ObservabilityService.get_instance()
        await obs.log_document_event(
            ctx=trace_ctx,
            document_id=UUID(doc_id),
            event_type="index",
            status="completed",
            duration_ms=index_duration_ms,
            chunk_count=chunk_count,
            metadata={
                "qdrant_collection": f"kb_{kb_id}",
                "vectors_indexed": chunk_count,
            },
        )
        # Create span for trace detail view
        await obs.log_processing_span(
            ctx=trace_ctx,
            name="index",
            span_type="processing",
            status="completed",
            duration_ms=index_duration_ms,
            metadata={
                "qdrant_collection": f"kb_{kb_id}",
                "vectors_indexed": chunk_count,
            },
        )

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
    soft_time_limit=1200,  # 20 minutes soft limit (for large PDFs)
    time_limit=1500,  # 25 minutes hard limit
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

    Story 9-4: Instrumented with observability trace and spans for each step.

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
    trace_ctx: TraceContext | None = None
    file_size_bytes = 0

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

        # Story 9-4 (AC1): Start observability trace when process_document begins
        obs = ObservabilityService.get_instance()
        trace_start_time = time.monotonic()
        trace_ctx = run_async(
            obs.start_trace(
                name="document_processing",
                user_id=document.uploaded_by,
                kb_id=kb_id,
                metadata={
                    "document_id": doc_id,
                    "task_id": task_id,
                    "retry": self.request.retries,
                    "is_replacement": is_replacement,
                    "mime_type": mime_type,
                    "filename": document.original_filename,
                },
            )
        )

        if not file_path:
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error="Document has no file path",
                )
            )
            # End trace with failure (Story 9-4 AC9)
            if trace_ctx:
                run_async(
                    obs.end_trace(
                        ctx=trace_ctx,
                        status="failed",
                        error_message="Document has no file path",
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
            # End trace with failure (Story 9-4 AC9)
            if trace_ctx:
                run_async(
                    obs.end_trace(
                        ctx=trace_ctx,
                        status="failed",
                        error_message=f"Invalid file path format: {file_path}",
                    )
                )
            return {"status": "error", "reason": "Invalid file path"}

        object_path = path_parts[1]

        # 2. Update status to PROCESSING and mark UPLOAD step in progress (Story 5-23)
        run_async(
            _update_document_status(
                doc_id,
                DocumentStatus.PROCESSING,
                processing_started=True,
            )
        )
        run_async(_mark_step_in_progress(doc_id, ProcessingStep.UPLOAD))

        # 3. Download file from MinIO
        # Story 9-4 (AC2): Upload span with file_size_bytes, duration_ms
        logger.info(
            "downloading_document",
            document_id=doc_id,
            kb_id=str(kb_id),
            object_path=object_path,
        )

        upload_start_time = time.monotonic()
        try:
            file_data = run_async(minio_service.download_file(kb_id, object_path))
            file_size_bytes = len(file_data)
        except Exception as e:
            upload_error = str(e)
            run_async(_mark_step_error(doc_id, ProcessingStep.UPLOAD, upload_error))
            # Log document event for failed upload step (Story 9-4 AC8)
            if trace_ctx:
                upload_duration_ms = int((time.monotonic() - upload_start_time) * 1000)
                run_async(
                    obs.log_document_event(
                        ctx=trace_ctx,
                        document_id=UUID(doc_id),
                        event_type="upload",
                        status="failed",
                        duration_ms=upload_duration_ms,
                        error_message=upload_error,
                    )
                )
            raise DocumentProcessingError(
                f"Failed to download file: {e}",
                retryable=True,
            ) from e

        # 4. Validate checksum
        if not _validate_checksum(file_data, checksum):
            run_async(
                _mark_step_error(doc_id, ProcessingStep.UPLOAD, "Checksum mismatch")
            )
            # Log document event for failed upload step (Story 9-4 AC8)
            if trace_ctx:
                upload_duration_ms = int((time.monotonic() - upload_start_time) * 1000)
                run_async(
                    obs.log_document_event(
                        ctx=trace_ctx,
                        document_id=UUID(doc_id),
                        event_type="upload",
                        status="failed",
                        duration_ms=upload_duration_ms,
                        error_message="Checksum mismatch - file may be corrupted",
                        metadata={"file_size_bytes": file_size_bytes},
                    )
                )
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

        upload_duration_ms = int((time.monotonic() - upload_start_time) * 1000)

        logger.info(
            "document_downloaded",
            document_id=doc_id,
            local_path=local_path,
            file_size=file_size_bytes,
        )

        # Mark UPLOAD step complete (Story 5-23)
        run_async(_mark_step_complete(doc_id, ProcessingStep.UPLOAD))

        # Log document event and span for successful upload step (Story 9-4 AC2, AC8)
        if trace_ctx:
            run_async(
                obs.log_document_event(
                    ctx=trace_ctx,
                    document_id=UUID(doc_id),
                    event_type="upload",
                    status="completed",
                    duration_ms=upload_duration_ms,
                    metadata={"file_size_bytes": file_size_bytes},
                )
            )
            # Create span for trace detail view
            run_async(
                obs.log_processing_span(
                    ctx=trace_ctx,
                    name="upload",
                    span_type="processing",
                    status="completed",
                    duration_ms=upload_duration_ms,
                    metadata={"file_size_bytes": file_size_bytes},
                )
            )

        run_async(_mark_step_in_progress(doc_id, ProcessingStep.PARSE))

        # 6. Parse document based on MIME type
        # Story 7-32 (AC-7.32.5): Fetch KB parser backend configuration
        # Story 9-4 (AC3): Parse span with file_type, file_size_bytes, extracted_chars, page_count, section_count, duration_ms
        parser_backend = run_async(_get_kb_parser_backend(kb_id))
        parse_start_time = time.monotonic()

        def _log_parse_failure(error_msg: str, parser_used: str = "unknown") -> None:
            """Helper to log parse failure document event."""
            if trace_ctx:
                parse_duration_ms = int((time.monotonic() - parse_start_time) * 1000)
                run_async(
                    obs.log_document_event(
                        ctx=trace_ctx,
                        document_id=UUID(doc_id),
                        event_type="parse",
                        status="failed",
                        duration_ms=parse_duration_ms,
                        error_message=error_msg,
                        metadata={
                            "file_type": mime_type,
                            "file_size_bytes": file_size_bytes,
                            "parser_backend": parser_used,
                        },
                    )
                )
                # End trace with failure (Story 9-4 AC9)
                run_async(
                    obs.end_trace(
                        ctx=trace_ctx,
                        status="failed",
                        error_message=error_msg,
                    )
                )

        try:
            # Story 7-32 (AC-7.32.5): Pass KB parser backend to parse_document
            parsed_content = parse_document(local_path, mime_type, parser_backend)
        except PasswordProtectedError:
            parse_error = "Password-protected PDF cannot be processed"
            run_async(
                _mark_step_error(doc_id, ProcessingStep.PARSE, "Password-protected PDF")
            )
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error=parse_error,
                    retry_count=settings.max_parsing_retries,  # Mark max retries to stop
                )
            )
            run_async(_mark_outbox_processed(doc_id))
            _log_parse_failure(parse_error)
            return {
                "status": "failed",
                "reason": "password_protected",
                "document_id": doc_id,
            }
        except ScannedDocumentError:
            parse_error = "Document appears to be scanned (OCR required - MVP 2)"
            run_async(
                _mark_step_error(
                    doc_id, ProcessingStep.PARSE, "Scanned document (OCR required)"
                )
            )
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error=parse_error,
                    retry_count=settings.max_parsing_retries,
                )
            )
            run_async(_mark_outbox_processed(doc_id))
            _log_parse_failure(parse_error)
            return {
                "status": "failed",
                "reason": "scanned_document",
                "document_id": doc_id,
            }
        except InsufficientContentError as e:
            parse_error = str(e)
            run_async(_mark_step_error(doc_id, ProcessingStep.PARSE, parse_error))
            run_async(
                _update_document_status(
                    doc_id,
                    DocumentStatus.FAILED,
                    error=parse_error,
                    retry_count=settings.max_parsing_retries,
                )
            )
            run_async(_mark_outbox_processed(doc_id))
            _log_parse_failure(parse_error)
            return {
                "status": "failed",
                "reason": "insufficient_content",
                "document_id": doc_id,
                "extracted_chars": 0,
            }
        except ParsingError as e:
            parse_error = str(e)
            run_async(_mark_step_error(doc_id, ProcessingStep.PARSE, parse_error))
            # Log document event for failed parse step (Story 9-4 AC8)
            if trace_ctx:
                parse_duration_ms = int((time.monotonic() - parse_start_time) * 1000)
                run_async(
                    obs.log_document_event(
                        ctx=trace_ctx,
                        document_id=UUID(doc_id),
                        event_type="parse",
                        status="failed",
                        duration_ms=parse_duration_ms,
                        error_message=parse_error,
                        metadata={
                            "file_type": mime_type,
                            "file_size_bytes": file_size_bytes,
                        },
                    )
                )
                # Create span for trace detail view
                run_async(
                    obs.log_processing_span(
                        ctx=trace_ctx,
                        name="parse",
                        span_type="processing",
                        status="failed",
                        duration_ms=parse_duration_ms,
                        error_message=parse_error,
                        metadata={
                            "file_type": mime_type,
                            "file_size_bytes": file_size_bytes,
                        },
                    )
                )
            raise DocumentProcessingError(parse_error, retryable=True) from e

        parse_duration_ms = int((time.monotonic() - parse_start_time) * 1000)

        # 7. Store parsed content temporarily
        run_async(
            store_parsed_content(
                kb_id=kb_id,
                document_id=UUID(doc_id),
                parsed=parsed_content,
            )
        )

        # Mark PARSE step complete (Story 5-23)
        run_async(_mark_step_complete(doc_id, ProcessingStep.PARSE))

        # Log document event and span for successful parse step (Story 9-4 AC3, AC8)
        # Story 7-32: Include parser_backend in metadata
        effective_parser = parsed_content.metadata.get("parser_backend", "unstructured")
        if trace_ctx:
            run_async(
                obs.log_document_event(
                    ctx=trace_ctx,
                    document_id=UUID(doc_id),
                    event_type="parse",
                    status="completed",
                    duration_ms=parse_duration_ms,
                    metadata={
                        "file_type": mime_type,
                        "file_size_bytes": file_size_bytes,
                        "extracted_chars": parsed_content.extracted_chars,
                        "page_count": parsed_content.page_count,
                        "section_count": parsed_content.section_count,
                        "parser_backend": effective_parser,
                    },
                )
            )
            # Create span for trace detail view
            run_async(
                obs.log_processing_span(
                    ctx=trace_ctx,
                    name="parse",
                    span_type="processing",
                    status="completed",
                    duration_ms=parse_duration_ms,
                    metadata={
                        "file_type": mime_type,
                        "extracted_chars": parsed_content.extracted_chars,
                        "page_count": parsed_content.page_count,
                        "parser_backend": effective_parser,
                    },
                )
            )

        logger.info(
            "document_parsing_completed",
            document_id=doc_id,
            extracted_chars=parsed_content.extracted_chars,
            page_count=parsed_content.page_count,
            section_count=parsed_content.section_count,
            parser_backend=effective_parser,
        )

        # 8. Chunk, embed, and index the document
        # For replacement flow, performs atomic vector switch (delete old, upsert new)
        # Note: CHUNK, EMBED, INDEX steps are tracked inside _chunk_embed_index
        chunk_count = run_async(
            _chunk_embed_index(
                doc_id=doc_id,
                kb_id=kb_id,
                document_name=filename,
                is_replacement=is_replacement,
                trace_ctx=trace_ctx,  # Story 9-4: Pass trace context for span instrumentation
            )
        )

        # 9. Mark processing COMPLETE step and update document status (Story 5-23)
        run_async(_mark_step_complete(doc_id, ProcessingStep.COMPLETE))
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

        # Story 9-4 AC9: End trace with status="completed" on success
        if trace_ctx:
            total_duration_ms = int((time.monotonic() - trace_start_time) * 1000)
            run_async(
                obs.end_trace(
                    trace_ctx,
                    status="completed",
                    metadata={
                        "document_id": doc_id,
                        "extracted_chars": parsed_content.extracted_chars,
                        "page_count": parsed_content.page_count,
                        "section_count": parsed_content.section_count,
                        "chunk_count": chunk_count,
                        "total_duration_ms": total_duration_ms,
                    },
                )
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
                # Story 9-4 AC9: End trace with status="failed" on max retries
                if trace_ctx:
                    run_async(
                        obs.end_trace(
                            trace_ctx,
                            status="failed",
                            metadata={
                                "document_id": doc_id,
                                "error_type": "max_retries_exhausted",
                                "error_message": str(e)[:500],
                            },
                        )
                    )
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
            # Story 9-4 AC9: End trace with status="failed" on non-retryable error
            if trace_ctx:
                run_async(
                    obs.end_trace(
                        trace_ctx,
                        status="failed",
                        metadata={
                            "document_id": doc_id,
                            "error_type": "non_retryable_error",
                            "error_message": str(e)[:500],
                        },
                    )
                )
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
            # Story 9-4 AC9: End trace with status="failed" on unexpected error
            if trace_ctx:
                run_async(
                    obs.end_trace(
                        trace_ctx,
                        status="failed",
                        metadata={
                            "document_id": doc_id,
                            "error_type": "unexpected_error",
                            "error_message": str(e)[:500],
                        },
                    )
                )
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
    async with celery_session_factory() as session:
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
