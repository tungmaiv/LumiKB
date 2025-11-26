"""Embedding generation for document chunks.

Orchestrates embedding generation using LiteLLM client with
batching, retry logic, and oversized chunk handling.
"""

from dataclasses import dataclass

import structlog

from app.integrations.litellm_client import (
    RateLimitExceededError,
    TokenLimitExceededError,
    embedding_client,
)
from app.workers.chunking import DocumentChunk

logger = structlog.get_logger(__name__)

# Expected embedding dimensions for ada-002
EMBEDDING_DIMENSIONS = 1536


@dataclass
class ChunkEmbedding:
    """A chunk with its embedding vector.

    Attributes:
        chunk: The DocumentChunk that was embedded.
        embedding: The embedding vector (1536 dimensions).
    """

    chunk: DocumentChunk
    embedding: list[float]

    @property
    def point_id(self) -> str:
        """Generate deterministic point ID for Qdrant.

        Format: {document_id}_{chunk_index}
        """
        return f"{self.chunk.document_id}_{self.chunk.chunk_index}"


class EmbeddingGenerationError(Exception):
    """Error during embedding generation."""


async def generate_embeddings(
    chunks: list[DocumentChunk],
) -> list[ChunkEmbedding]:
    """Generate embeddings for a list of document chunks.

    Handles:
    - Batched API calls for efficiency
    - Exponential backoff on rate limits
    - Oversized chunk splitting for token limit errors

    Args:
        chunks: List of DocumentChunk objects to embed.

    Returns:
        List of ChunkEmbedding objects with vectors.

    Raises:
        EmbeddingGenerationError: If embedding generation fails.
    """
    if not chunks:
        return []

    logger.info(
        "embedding_generation_started",
        chunk_count=len(chunks),
        document_id=chunks[0].document_id if chunks else None,
    )

    try:
        # Extract texts for embedding
        texts = [chunk.text for chunk in chunks]

        # Generate embeddings with retry handling
        embeddings = await _generate_with_retry(texts, chunks)

        # Combine chunks with embeddings
        results = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            # Validate embedding dimensions
            if len(embedding) != EMBEDDING_DIMENSIONS:
                logger.warning(
                    "unexpected_embedding_dimensions",
                    expected=EMBEDDING_DIMENSIONS,
                    actual=len(embedding),
                    chunk_index=chunk.chunk_index,
                )

            results.append(ChunkEmbedding(chunk=chunk, embedding=embedding))

        logger.info(
            "embedding_generation_completed",
            chunk_count=len(results),
            document_id=chunks[0].document_id if chunks else None,
            tokens_used=embedding_client.total_tokens_used,
        )

        return results

    except RateLimitExceededError as e:
        logger.error(
            "embedding_rate_limit_exhausted",
            document_id=chunks[0].document_id if chunks else None,
            error=str(e),
        )
        raise EmbeddingGenerationError(str(e)) from e

    except Exception as e:
        logger.error(
            "embedding_generation_failed",
            document_id=chunks[0].document_id if chunks else None,
            error=str(e),
        )
        raise EmbeddingGenerationError(f"Failed to generate embeddings: {e}") from e


async def _generate_with_retry(
    texts: list[str],
    chunks: list[DocumentChunk],
) -> list[list[float]]:
    """Generate embeddings with token limit error handling.

    If a chunk exceeds token limits, it's split further and re-embedded.

    Args:
        texts: Texts to embed.
        chunks: Corresponding chunks (for re-chunking metadata).

    Returns:
        List of embedding vectors.
    """
    try:
        return await embedding_client.get_embeddings(texts)

    except TokenLimitExceededError as e:
        # Handle oversized chunk by splitting
        logger.warning(
            "token_limit_handling",
            chunk_index=e.chunk_index,
            error=str(e),
        )

        # Re-chunk the oversized text
        return await _handle_oversized_chunks(texts, chunks, e.chunk_index)


async def _handle_oversized_chunks(
    texts: list[str],
    chunks: list[DocumentChunk],
    problem_index: int,
) -> list[list[float]]:
    """Handle token limit errors by splitting oversized chunks.

    Splits the problematic chunk into smaller pieces, embeds them,
    and averages the embeddings.

    Args:
        texts: Original texts.
        chunks: Original chunks.
        problem_index: Index of the chunk that exceeded limits.

    Returns:
        List of embedding vectors.
    """
    from app.core.config import settings
    from app.workers.chunking import (
        _count_tokens,
        _get_token_encoder,
        _split_oversized_chunk,
    )

    encoder = _get_token_encoder()
    results: list[list[float]] = []

    for i, (text, _chunk) in enumerate(zip(texts, chunks, strict=True)):
        if i == problem_index:
            # Split this chunk and average embeddings
            sub_texts = _split_oversized_chunk(text, settings.chunk_size, encoder)

            logger.info(
                "splitting_oversized_chunk",
                chunk_index=i,
                original_tokens=_count_tokens(text, encoder),
                sub_chunk_count=len(sub_texts),
            )

            # Embed sub-chunks
            sub_embeddings = await embedding_client.get_embeddings(sub_texts)

            # Average the embeddings
            if sub_embeddings:
                avg_embedding = [
                    sum(e[j] for e in sub_embeddings) / len(sub_embeddings)
                    for j in range(len(sub_embeddings[0]))
                ]
                results.append(avg_embedding)
            else:
                # Fallback: zero embedding (should not happen)
                results.append([0.0] * EMBEDDING_DIMENSIONS)
        else:
            # Embed normally
            embeddings = await embedding_client.get_embeddings([text])
            results.append(embeddings[0])

    return results


async def embed_document_chunks(
    parsed_content: "ParsedContent",  # noqa: F821
    document_id: str,
    document_name: str,
) -> list[ChunkEmbedding]:
    """Convenience function to chunk and embed a document in one call.

    Args:
        parsed_content: ParsedContent from document parsing.
        document_id: Document UUID as string.
        document_name: Original filename.

    Returns:
        List of ChunkEmbedding objects ready for indexing.
    """
    from app.workers.chunking import chunk_document

    # Chunk the document
    chunks = chunk_document(
        parsed_content=parsed_content,
        document_id=document_id,
        document_name=document_name,
    )

    if not chunks:
        return []

    # Generate embeddings
    return await generate_embeddings(chunks)
