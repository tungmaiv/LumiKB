"""Chunk service for document chunk retrieval from Qdrant.

Story 5-25: Document Chunk Viewer Backend
Story 7-7: AsyncQdrantClient Migration (AC-7.7.2)
Story 7-17: KB-aware embedding model for chunk search
"""

from uuid import UUID

import structlog
from qdrant_client.http import models as qdrant_models
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.litellm_client import LiteLLMEmbeddingClient, embedding_client
from app.integrations.qdrant_client import qdrant_service
from app.schemas.document import DocumentChunkResponse, DocumentChunksResponse
from app.services.kb_config_resolver import KBConfigResolver

logger = structlog.get_logger(__name__)

# Default pagination limit
DEFAULT_CHUNK_LIMIT = 50
MAX_CHUNK_LIMIT = 100


class ChunkServiceError(Exception):
    """Error during chunk retrieval."""

    def __init__(self, message: str, code: str = "CHUNK_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ChunkService:
    """Service for retrieving document chunks from Qdrant.

    AC-5.25.1: Returns chunks with chunk_id, chunk_index, text, char_start,
               char_end, page_number, section_header
    AC-5.25.2: Cursor-based pagination using chunk_index
    AC-5.25.3: Search with query embedding and score
    Story 7-17: Uses KB's configured embedding model for chunk search
    """

    def __init__(
        self,
        kb_id: UUID,
        session: AsyncSession | None = None,
        redis: Redis | None = None,
    ):
        """Initialize ChunkService for a specific knowledge base.

        Args:
            kb_id: Knowledge base UUID (determines Qdrant collection).
            session: Database session for KB config resolution (optional).
            redis: Redis client for config caching (optional).
        """
        self.kb_id = kb_id
        self.collection_name = f"kb_{kb_id}"
        # KB config resolver for embedding model resolution (Story 7-17)
        self._kb_config_resolver: KBConfigResolver | None = None
        if session and redis:
            self._kb_config_resolver = KBConfigResolver(session, redis)

    async def get_chunks(
        self,
        document_id: UUID,
        cursor: int = 0,
        limit: int = DEFAULT_CHUNK_LIMIT,
        search_query: str | None = None,
    ) -> DocumentChunksResponse:
        """Get paginated chunks for a document.

        Args:
            document_id: Document UUID to get chunks for.
            cursor: Starting chunk_index for pagination (0-indexed).
            limit: Maximum chunks to return (default 50, max 100).
            search_query: Optional search query to filter and rank chunks.

        Returns:
            DocumentChunksResponse with chunks, total, has_more, next_cursor.

        Raises:
            ChunkServiceError: If Qdrant query fails.
        """
        # Validate and clamp limit
        limit = min(max(1, limit), MAX_CHUNK_LIMIT)

        try:
            # Build filter for document_id
            doc_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="document_id",
                        match=qdrant_models.MatchValue(value=str(document_id)),
                    )
                ]
            )

            if search_query:
                # AC-5.25.3: Search with embedding
                return await self._search_chunks(
                    search_query=search_query,
                    doc_filter=doc_filter,
                    cursor=cursor,
                    limit=limit,
                )
            else:
                # Standard pagination by chunk_index
                return await self._scroll_chunks(
                    doc_filter=doc_filter,
                    cursor=cursor,
                    limit=limit,
                )

        except Exception as e:
            logger.error(
                "chunk_retrieval_failed",
                document_id=str(document_id),
                kb_id=str(self.kb_id),
                error=str(e),
            )
            raise ChunkServiceError(
                message=f"Failed to retrieve chunks: {e}",
                code="QDRANT_ERROR",
            ) from e

    async def _scroll_chunks(
        self,
        doc_filter: qdrant_models.Filter,
        cursor: int,
        limit: int,
    ) -> DocumentChunksResponse:
        """Scroll through chunks ordered by chunk_index.

        Uses Qdrant scroll API with filter for cursor-based pagination.

        Args:
            doc_filter: Qdrant filter for document.
            cursor: Starting chunk_index.
            limit: Max chunks to return.

        Returns:
            DocumentChunksResponse with paginated chunks.
        """
        # First, get total count
        total = await self._get_chunk_count(doc_filter)

        if total == 0:
            return DocumentChunksResponse(
                chunks=[],
                total=0,
                has_more=False,
                next_cursor=None,
            )

        # Add cursor filter if not starting from beginning
        scroll_filter = doc_filter
        if cursor > 0:
            scroll_filter = qdrant_models.Filter(
                must=[
                    *doc_filter.must,
                    qdrant_models.FieldCondition(
                        key="chunk_index",
                        range=qdrant_models.Range(gte=cursor),
                    ),
                ]
            )

        # Scroll with ordering by chunk_index
        # Note: Qdrant scroll doesn't support ordering, so we fetch more and sort
        # Story 7-7: Use native async scroll method (AC-7.7.2)
        points, _ = await qdrant_service.scroll(
            collection_name=self.collection_name,
            scroll_filter=scroll_filter,
            limit=limit + 1,  # Fetch one extra to check has_more
            with_payload=True,
            with_vectors=False,
        )

        # Sort by chunk_index
        points.sort(key=lambda p: p.payload.get("chunk_index", 0))

        # Take only limit items
        has_more = len(points) > limit
        points = points[:limit]

        # Convert to response schema
        chunks = [self._point_to_chunk(p) for p in points]

        # Determine next cursor
        next_cursor = None
        if has_more and chunks:
            next_cursor = chunks[-1].chunk_index + 1

        return DocumentChunksResponse(
            chunks=chunks,
            total=total,
            has_more=has_more,
            next_cursor=next_cursor,
        )

    async def _search_chunks(
        self,
        search_query: str,
        doc_filter: qdrant_models.Filter,
        cursor: int,
        limit: int,
    ) -> DocumentChunksResponse:
        """Search chunks with query embedding.

        Uses Qdrant search API with document filter and embedding similarity.
        Story 7-17: Uses KB's configured embedding model for query embedding.

        Args:
            search_query: Text query to search for.
            doc_filter: Qdrant filter for document.
            cursor: Offset for pagination.
            limit: Max chunks to return.

        Returns:
            DocumentChunksResponse with scored chunks.
        """
        # Get total count first
        total = await self._get_chunk_count(doc_filter)

        if total == 0:
            return DocumentChunksResponse(
                chunks=[],
                total=0,
                has_more=False,
                next_cursor=None,
            )

        # Resolve KB embedding model (Story 7-17)
        # This ensures query embedding dimensions match indexed vectors
        embedding_model_config = None
        if self._kb_config_resolver:
            try:
                embedding_model_config = (
                    await self._kb_config_resolver.get_kb_embedding_model(self.kb_id)
                )
            except Exception as e:
                logger.warning(
                    "kb_embedding_model_resolution_failed",
                    kb_id=str(self.kb_id),
                    error=str(e),
                )

        # Generate query embedding with KB-specific model
        if embedding_model_config:
            # Use KB's embedding model
            client = LiteLLMEmbeddingClient(
                model=embedding_model_config.model_id,
                provider=embedding_model_config.provider,
                api_base=embedding_model_config.api_endpoint,
            )
            logger.debug(
                "chunk_search_using_kb_embedding_model",
                kb_id=str(self.kb_id),
                model_id=embedding_model_config.model_id,
                provider=embedding_model_config.provider,
            )
            embeddings = await client.get_embeddings([search_query])
        else:
            # Fall back to system default embedding client
            logger.debug(
                "chunk_search_using_default_embedding_model",
                kb_id=str(self.kb_id),
            )
            embeddings = await embedding_client.get_embeddings([search_query])

        query_vector = embeddings[0]

        # Search with embedding
        # Story 7-7: Use native async search method (AC-7.7.2)
        search_result = await qdrant_service.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=doc_filter,
            limit=limit + 1,  # Fetch one extra to check has_more
            offset=cursor,
            with_payload=True,
            with_vectors=False,
        )

        # Check has_more
        has_more = len(search_result) > limit
        search_result = search_result[:limit]

        # Convert to response schema with scores
        chunks = [self._scored_point_to_chunk(p) for p in search_result]

        # Determine next cursor (offset-based for search)
        next_cursor = None
        if has_more:
            next_cursor = cursor + limit

        return DocumentChunksResponse(
            chunks=chunks,
            total=total,
            has_more=has_more,
            next_cursor=next_cursor,
        )

    async def _get_chunk_count(self, doc_filter: qdrant_models.Filter) -> int:
        """Get total chunk count for filter.

        Args:
            doc_filter: Qdrant filter.

        Returns:
            Total count of matching points.
        """
        # Story 7-7: Use native async count method (AC-7.7.2)
        count_result = await qdrant_service.count(
            collection_name=self.collection_name,
            count_filter=doc_filter,
            exact=True,
        )
        return count_result.count

    def _point_to_chunk(self, point: qdrant_models.Record) -> DocumentChunkResponse:
        """Convert Qdrant point to chunk response.

        Args:
            point: Qdrant Record with payload.

        Returns:
            DocumentChunkResponse schema.
        """
        payload = point.payload or {}
        return DocumentChunkResponse(
            chunk_id=str(point.id),
            chunk_index=payload.get("chunk_index", 0),
            text=payload.get("chunk_text", ""),
            char_start=payload.get("char_start", 0),
            char_end=payload.get("char_end", 0),
            page_number=payload.get("page_number"),
            section_header=payload.get("section_header"),
            score=None,
        )

    def _scored_point_to_chunk(
        self, point: qdrant_models.ScoredPoint
    ) -> DocumentChunkResponse:
        """Convert Qdrant scored point to chunk response.

        Args:
            point: Qdrant ScoredPoint with payload and score.

        Returns:
            DocumentChunkResponse schema with score.
        """
        payload = point.payload or {}
        return DocumentChunkResponse(
            chunk_id=str(point.id),
            chunk_index=payload.get("chunk_index", 0),
            text=payload.get("chunk_text", ""),
            char_start=payload.get("char_start", 0),
            char_end=payload.get("char_end", 0),
            page_number=payload.get("page_number"),
            section_header=payload.get("section_header"),
            score=point.score,
        )

    async def get_chunk_by_index(
        self,
        document_id: UUID,
        chunk_index: int,
    ) -> DocumentChunkResponse | None:
        """Get a single chunk by document ID and chunk index.

        Args:
            document_id: Document UUID.
            chunk_index: Chunk index to retrieve.

        Returns:
            DocumentChunkResponse or None if not found.
        """
        try:
            scroll_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="document_id",
                        match=qdrant_models.MatchValue(value=str(document_id)),
                    ),
                    qdrant_models.FieldCondition(
                        key="chunk_index",
                        match=qdrant_models.MatchValue(value=chunk_index),
                    ),
                ]
            )

            # Story 7-7: Use native async scroll method (AC-7.7.2)
            points, _ = await qdrant_service.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=1,
                with_payload=True,
                with_vectors=False,
            )
            if not points:
                return None

            return self._point_to_chunk(points[0])

        except Exception as e:
            logger.error(
                "chunk_by_index_failed",
                document_id=str(document_id),
                chunk_index=chunk_index,
                error=str(e),
            )
            return None
