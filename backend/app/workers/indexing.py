"""Qdrant vector indexing for document embeddings.

Handles upserting document embeddings to Qdrant with idempotent
point IDs and orphan chunk cleanup for re-uploads.
"""

from uuid import UUID

import structlog
from qdrant_client.http import models

from app.integrations.qdrant_client import qdrant_service
from app.workers.embedding import ChunkEmbedding

logger = structlog.get_logger(__name__)


class IndexingError(Exception):
    """Error during vector indexing."""


async def index_document(
    doc_id: str,
    kb_id: UUID,
    embeddings: list[ChunkEmbedding],
    max_retries: int = 3,
    vector_size: int | None = None,
) -> int:
    """Index document embeddings to Qdrant.

    Uses deterministic point IDs ({doc_id}_{chunk_index}) for idempotent
    retry behavior.

    Args:
        doc_id: Document UUID as string.
        kb_id: Knowledge Base UUID.
        embeddings: List of ChunkEmbedding objects to index.
        max_retries: Maximum retry attempts for Qdrant operations.
        vector_size: Optional vector dimensions for collection creation.
                    If not provided, defaults to 768 for backward compatibility.

    Returns:
        Number of points indexed.

    Raises:
        IndexingError: If indexing fails after all retries.
    """
    if not embeddings:
        logger.warning("indexing_empty_embeddings", document_id=doc_id)
        return 0

    logger.info(
        "indexing_started",
        document_id=doc_id,
        kb_id=str(kb_id),
        embedding_count=len(embeddings),
    )

    # Convert embeddings to Qdrant points
    points = _create_points(embeddings)

    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            # Ensure collection exists with correct vector dimensions
            if not await qdrant_service.collection_exists(kb_id):
                # Use consolidated create_collection with optional vector_size
                # Defaults to 768 if vector_size is None (backward compatibility)
                await qdrant_service.create_collection(
                    kb_id=kb_id,
                    vector_size=vector_size,
                )

            # Upsert points
            count = await qdrant_service.upsert_points(kb_id, points)

            logger.info(
                "indexing_completed",
                document_id=doc_id,
                kb_id=str(kb_id),
                indexed_count=count,
            )

            return count

        except Exception as e:
            last_error = e
            logger.warning(
                "indexing_retry",
                document_id=doc_id,
                kb_id=str(kb_id),
                attempt=attempt + 1,
                max_retries=max_retries,
                error=str(e),
            )

            if attempt < max_retries - 1:
                continue

    # All retries exhausted
    logger.error(
        "indexing_failed",
        document_id=doc_id,
        kb_id=str(kb_id),
        error=str(last_error),
    )
    raise IndexingError(
        f"Failed to index document after {max_retries} retries: {last_error}"
    )


def _create_points(embeddings: list[ChunkEmbedding]) -> list[models.PointStruct]:
    """Create Qdrant PointStruct objects from embeddings.

    Args:
        embeddings: List of ChunkEmbedding objects.

    Returns:
        List of PointStruct ready for upsert.
    """
    points = []

    for emb in embeddings:
        point = models.PointStruct(
            id=emb.point_id,  # Deterministic: {doc_id}_{chunk_index}
            vector=emb.embedding,
            payload=emb.chunk.to_payload(),
        )
        points.append(point)

    return points


async def cleanup_orphan_chunks(
    doc_id: str,
    kb_id: UUID,
    max_chunk_index: int,
) -> int:
    """Clean up orphan chunks from a document re-upload.

    After a re-upload, the document may have fewer chunks than before.
    This function deletes any vectors with chunk_index > max_chunk_index.

    Args:
        doc_id: Document UUID as string.
        kb_id: Knowledge Base UUID.
        max_chunk_index: Maximum valid chunk index (0-indexed).

    Returns:
        Number of orphan chunks deleted.
    """
    logger.info(
        "orphan_cleanup_started",
        document_id=doc_id,
        kb_id=str(kb_id),
        max_chunk_index=max_chunk_index,
    )

    try:
        # Build filter for orphan chunks
        # Points with document_id matching AND chunk_index > max_chunk_index
        filter_conditions = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=doc_id),
                ),
                models.FieldCondition(
                    key="chunk_index",
                    range=models.Range(gt=max_chunk_index),
                ),
            ]
        )

        deleted_count = await qdrant_service.delete_points_by_filter(
            kb_id=kb_id,
            filter_conditions=filter_conditions,
        )

        logger.info(
            "orphan_cleanup_completed",
            document_id=doc_id,
            kb_id=str(kb_id),
            deleted_count=deleted_count,
        )

        return deleted_count

    except Exception as e:
        logger.error(
            "orphan_cleanup_failed",
            document_id=doc_id,
            kb_id=str(kb_id),
            error=str(e),
        )
        # Don't raise - orphan cleanup is best-effort
        return 0


async def delete_document_vectors(
    doc_id: str,
    kb_id: UUID,
) -> int:
    """Delete all vectors for a document.

    Used when a document is deleted.

    Args:
        doc_id: Document UUID as string.
        kb_id: Knowledge Base UUID.

    Returns:
        Number of vectors deleted.
    """
    logger.info(
        "document_vectors_deletion_started",
        document_id=doc_id,
        kb_id=str(kb_id),
    )

    try:
        # Build filter for all chunks of this document
        filter_conditions = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=doc_id),
                ),
            ]
        )

        deleted_count = await qdrant_service.delete_points_by_filter(
            kb_id=kb_id,
            filter_conditions=filter_conditions,
        )

        logger.info(
            "document_vectors_deleted",
            document_id=doc_id,
            kb_id=str(kb_id),
            deleted_count=deleted_count,
        )

        return deleted_count

    except Exception as e:
        logger.error(
            "document_vectors_deletion_failed",
            document_id=doc_id,
            kb_id=str(kb_id),
            error=str(e),
        )
        raise IndexingError(f"Failed to delete document vectors: {e}") from e


async def get_document_chunk_count(
    doc_id: str,
    kb_id: UUID,
) -> int:
    """Get the number of chunks indexed for a document.

    Args:
        doc_id: Document UUID as string.
        kb_id: Knowledge Base UUID.

    Returns:
        Number of chunks in Qdrant.
    """
    try:
        # Build filter for document chunks
        filter_conditions = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=doc_id),
                ),
            ]
        )

        count_result = qdrant_service.client.count(
            collection_name=f"kb_{kb_id}",
            count_filter=filter_conditions,
        )

        return count_result.count

    except Exception as e:
        logger.warning(
            "chunk_count_failed",
            document_id=doc_id,
            kb_id=str(kb_id),
            error=str(e),
        )
        return 0
