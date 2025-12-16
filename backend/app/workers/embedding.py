"""Embedding generation for document chunks.

Orchestrates embedding generation using LiteLLM client with
batching, retry logic, and oversized chunk handling.

Story 7-10: Supports KB-specific embedding models with configurable
dimensions. Falls back to system defaults when KB model not configured.
"""

from dataclasses import dataclass
from typing import NamedTuple
from uuid import UUID, uuid5

import structlog

# UUID namespace for generating deterministic point IDs
# Using DNS namespace as a base for our document chunk IDs
POINT_ID_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

from app.integrations.litellm_client import (
    LiteLLMEmbeddingClient,
    RateLimitExceededError,
    TokenLimitExceededError,
    embedding_client,
)
from app.workers.chunking import DocumentChunk

logger = structlog.get_logger(__name__)

# Default embedding dimensions for system default model (Gemini text-embedding-004)
DEFAULT_EMBEDDING_DIMENSIONS = 768


class EmbeddingConfig(NamedTuple):
    """Configuration for KB-specific embedding model (Story 7-10).

    Attributes:
        model_id: LiteLLM model identifier (e.g., "openai/text-embedding-3-small").
        dimensions: Vector dimensions for this model.
        api_endpoint: Optional custom API endpoint URL.
        provider: Model provider (ollama, openai, lmstudio, etc.) for routing.
    """

    model_id: str | None = None
    dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
    api_endpoint: str | None = None
    provider: str | None = None


# Legacy alias for backward compatibility
EMBEDDING_DIMENSIONS = DEFAULT_EMBEDDING_DIMENSIONS


@dataclass
class ChunkEmbedding:
    """A chunk with its embedding vector.

    Attributes:
        chunk: The DocumentChunk that was embedded.
        embedding: The embedding vector (768 dimensions for Gemini text-embedding-004).
    """

    chunk: DocumentChunk
    embedding: list[float]

    @property
    def point_id(self) -> str:
        """Generate deterministic UUID point ID for Qdrant.

        Uses UUID5 to create a deterministic UUID from document_id and chunk_index.
        This ensures idempotent upserts while being valid for Qdrant's gRPC API.

        Format: UUID5(namespace, "{document_id}_{chunk_index}")
        """
        name = f"{self.chunk.document_id}_{self.chunk.chunk_index}"
        return str(uuid5(POINT_ID_NAMESPACE, name))


class EmbeddingGenerationError(Exception):
    """Error during embedding generation."""


async def generate_embeddings(
    chunks: list[DocumentChunk],
    embedding_config: EmbeddingConfig | None = None,
) -> list[ChunkEmbedding]:
    """Generate embeddings for a list of document chunks.

    Story 7-10: Supports KB-specific embedding models. If embedding_config
    is provided, uses the configured model and validates dimensions against
    the expected value. Falls back to system default if not configured.

    Handles:
    - Batched API calls for efficiency
    - Exponential backoff on rate limits
    - Oversized chunk splitting for token limit errors

    Args:
        chunks: List of DocumentChunk objects to embed.
        embedding_config: Optional KB-specific embedding configuration (Story 7-10).
            If None, uses system default model.

    Returns:
        List of ChunkEmbedding objects with vectors.

    Raises:
        EmbeddingGenerationError: If embedding generation fails.
    """
    if not chunks:
        return []

    # Story 7-10: Determine expected dimensions from config or use default
    if embedding_config:
        expected_dimensions = embedding_config.dimensions
    else:
        expected_dimensions = DEFAULT_EMBEDDING_DIMENSIONS

    logger.info(
        "embedding_generation_started",
        chunk_count=len(chunks),
        document_id=chunks[0].document_id if chunks else None,
        model_id=embedding_config.model_id if embedding_config else "default",
        expected_dimensions=expected_dimensions,
    )

    try:
        # Extract texts for embedding
        texts = [chunk.text for chunk in chunks]

        # Generate embeddings with retry handling
        # Story 7-10: Pass embedding config for KB-specific model
        embeddings = await _generate_with_retry(texts, chunks, embedding_config)

        # Combine chunks with embeddings
        results = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            # Validate embedding dimensions against expected (AC-7.10.9)
            if len(embedding) != expected_dimensions:
                logger.warning(
                    "unexpected_embedding_dimensions",
                    expected=expected_dimensions,
                    actual=len(embedding),
                    chunk_index=chunk.chunk_index,
                    model_id=embedding_config.model_id
                    if embedding_config
                    else "default",
                )

            results.append(ChunkEmbedding(chunk=chunk, embedding=embedding))

        # Get token count from appropriate client
        tokens_used = embedding_client.total_tokens_used

        logger.info(
            "embedding_generation_completed",
            chunk_count=len(results),
            document_id=chunks[0].document_id if chunks else None,
            tokens_used=tokens_used,
            model_id=embedding_config.model_id if embedding_config else "default",
        )

        return results

    except RateLimitExceededError as e:
        logger.error(
            "embedding_rate_limit_exhausted",
            document_id=chunks[0].document_id if chunks else None,
            model_id=embedding_config.model_id if embedding_config else "default",
            error=str(e),
        )
        raise EmbeddingGenerationError(str(e)) from e

    except Exception as e:
        logger.error(
            "embedding_generation_failed",
            document_id=chunks[0].document_id if chunks else None,
            model_id=embedding_config.model_id if embedding_config else "default",
            error=str(e),
        )
        raise EmbeddingGenerationError(f"Failed to generate embeddings: {e}") from e


async def _generate_with_retry(
    texts: list[str],
    chunks: list[DocumentChunk],
    embedding_config: EmbeddingConfig | None = None,
) -> list[list[float]]:
    """Generate embeddings with token limit error handling.

    If a chunk exceeds token limits, it's split further and re-embedded.

    Story 7-10: Uses KB-specific embedding model if configured.

    Args:
        texts: Texts to embed.
        chunks: Corresponding chunks (for re-chunking metadata).
        embedding_config: Optional KB-specific embedding configuration.

    Returns:
        List of embedding vectors.
    """
    try:
        # Story 7-10: Use KB-specific model if configured (AC-7.10.8)
        if embedding_config and embedding_config.model_id:
            # Create a temporary client with KB-specific model, endpoint, and provider
            # Provider-based routing enables proper handling of local providers (Ollama, LM Studio)
            client = LiteLLMEmbeddingClient(
                model=embedding_config.model_id,
                api_base=embedding_config.api_endpoint,
                provider=embedding_config.provider,
            )
            return await client.get_embeddings(texts)
        else:
            # Use system default
            return await embedding_client.get_embeddings(texts)

    except TokenLimitExceededError as e:
        # Handle oversized chunk by splitting
        logger.warning(
            "token_limit_handling",
            chunk_index=e.chunk_index,
            error=str(e),
        )

        # Re-chunk the oversized text
        return await _handle_oversized_chunks(
            texts, chunks, e.chunk_index, embedding_config
        )


async def _handle_oversized_chunks(
    texts: list[str],
    chunks: list[DocumentChunk],
    problem_index: int,
    embedding_config: EmbeddingConfig | None = None,
) -> list[list[float]]:
    """Handle token limit errors by splitting oversized chunks.

    Splits the problematic chunk into smaller pieces, embeds them,
    and averages the embeddings.

    Story 7-10: Uses KB-specific embedding model if configured.

    Args:
        texts: Original texts.
        chunks: Original chunks.
        problem_index: Index of the chunk that exceeded limits.
        embedding_config: Optional KB-specific embedding configuration.

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

    # Story 7-10: Create client based on config
    # Provider-based routing enables proper handling of local providers (Ollama, LM Studio)
    if embedding_config and embedding_config.model_id:
        client = LiteLLMEmbeddingClient(
            model=embedding_config.model_id,
            api_base=embedding_config.api_endpoint,
            provider=embedding_config.provider,
        )
        expected_dimensions = embedding_config.dimensions
    else:
        client = embedding_client
        expected_dimensions = DEFAULT_EMBEDDING_DIMENSIONS

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

            # Embed sub-chunks using appropriate client
            sub_embeddings = await client.get_embeddings(sub_texts)

            # Average the embeddings
            if sub_embeddings:
                avg_embedding = [
                    sum(e[j] for e in sub_embeddings) / len(sub_embeddings)
                    for j in range(len(sub_embeddings[0]))
                ]
                results.append(avg_embedding)
            else:
                # Fallback: zero embedding (should not happen)
                results.append([0.0] * expected_dimensions)
        else:
            # Embed normally using appropriate client
            embeddings = await client.get_embeddings([text])
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
