"""Qdrant vector database integration for Knowledge Base collections.

Story 7-7: AsyncQdrantClient Migration
- AC-7.7.1: AsyncQdrantClient replaces synchronous QdrantClient
- Native async operations without asyncio.to_thread
"""

import atexit
from typing import Any
from uuid import UUID

import structlog
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Vector configuration - last-resort fallback only
# In normal operation, embedding dimensions come from:
# 1. KB's configured embedding model (KnowledgeBase.embedding_model.config["dimensions"])
# 2. System default embedding model (from model registry with is_default=True)
# This constant is only used if no model is configured at all
VECTOR_SIZE = 768
DISTANCE_METRIC = models.Distance.COSINE

# Connection configuration to prevent "too many open files" errors
# NOTE: qdrant-client 1.16+ requires grpc_options as a dict, not list of tuples
GRPC_OPTIONS: dict[str, int] = {
    # Limit concurrent streams per connection
    "grpc.max_concurrent_streams": 100,
    # Enable keepalive to detect dead connections
    "grpc.keepalive_time_ms": 30000,
    "grpc.keepalive_timeout_ms": 10000,
    "grpc.keepalive_permit_without_calls": 1,
    # HTTP/2 flow control
    "grpc.http2.max_pings_without_data": 0,
    "grpc.http2.min_time_between_pings_ms": 10000,
}


class QdrantService:
    """Service for managing Qdrant collections.

    Each Knowledge Base has its own collection named `kb_{uuid}`.
    This ensures zero-trust isolation between KBs.

    Connection Management:
    - Uses lazy initialization with singleton pattern
    - Includes gRPC options for connection limits and keepalive
    - Provides close() method for explicit cleanup
    - Registers atexit handler for graceful shutdown

    Story 7-7: AsyncQdrantClient Migration
    - Uses AsyncQdrantClient for native async operations
    - No asyncio.to_thread wrappers needed
    """

    def __init__(self) -> None:
        """Initialize Qdrant client with settings."""
        self._async_client: AsyncQdrantClient | None = None
        self._sync_client: QdrantClient | None = None  # Kept for backward compat
        self._closed: bool = False

    @property
    def async_client(self) -> AsyncQdrantClient:
        """Lazy initialization of async Qdrant client.

        Returns:
            AsyncQdrantClient: The async Qdrant client instance.

        Raises:
            RuntimeError: If service has been closed.
        """
        if self._closed:
            raise RuntimeError("QdrantService has been closed")

        if self._async_client is None:
            self._async_client = AsyncQdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                grpc_port=settings.qdrant_grpc_port,
                prefer_grpc=True,
                grpc_options=GRPC_OPTIONS,
            )
            logger.info(
                "async_qdrant_client_initialized",
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                grpc_port=settings.qdrant_grpc_port,
            )
        return self._async_client

    @property
    def client(self) -> QdrantClient:
        """Lazy initialization of sync Qdrant client (backward compatibility).

        NOTE: Deprecated - use async_client instead for new code.

        Returns:
            QdrantClient: The sync Qdrant client instance.

        Raises:
            RuntimeError: If service has been closed.
        """
        if self._closed:
            raise RuntimeError("QdrantService has been closed")

        if self._sync_client is None:
            self._sync_client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                grpc_port=settings.qdrant_grpc_port,
                prefer_grpc=True,
                grpc_options=GRPC_OPTIONS,
            )
            logger.info(
                "sync_qdrant_client_initialized",
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                grpc_port=settings.qdrant_grpc_port,
            )
        return self._sync_client

    async def close_async(self) -> None:
        """Close the async Qdrant client and release connections.

        Should be called during application shutdown to prevent
        resource leaks and "too many open files" errors.
        """
        if self._async_client is not None and not self._closed:
            try:
                await self._async_client.close()
                logger.info("async_qdrant_client_closed")
            except Exception as e:
                # Log but don't raise - shutdown should be best-effort
                logger.warning("async_qdrant_client_close_error", error=str(e))
            finally:
                self._async_client = None

    def close(self, grpc_grace: float | None = None) -> None:
        """Close the sync Qdrant client and release connections.

        Should be called during application shutdown to prevent
        resource leaks and "too many open files" errors.

        Args:
            grpc_grace: Grace period in seconds for gRPC channel shutdown.
                       None means immediate shutdown.
        """
        if self._sync_client is not None:
            try:
                self._sync_client.close(grpc_grace=grpc_grace)
                logger.info("sync_qdrant_client_closed")
            except Exception as e:
                # Log but don't raise - shutdown should be best-effort
                logger.warning("sync_qdrant_client_close_error", error=str(e))
            finally:
                self._sync_client = None

        # Also close async client if present
        if self._async_client is not None:
            try:
                # Can't await here in sync context, just set to None
                # The async client will be cleaned up by the event loop
                self._async_client = None
                logger.info("async_qdrant_client_cleared")
            except Exception as e:
                logger.warning("async_qdrant_client_clear_error", error=str(e))

        self._closed = True

    def reset(self) -> None:
        """Reset the service for reuse (e.g., in tests).

        Closes existing connection and allows new connections.
        """
        self.close()
        self._closed = False

    def reset_async_client(self) -> None:
        """Reset the async client for use in a new event loop.

        Call this when initializing a new event loop (e.g., in Celery worker tasks)
        to prevent "Event loop is closed" errors.

        The AsyncQdrantClient's gRPC channels get bound to the event loop that was
        active when the client was created. In Celery workers using asyncio.run(),
        each task runs in a new event loop, but the singleton client still holds
        references to gRPC channels from the previous (now closed) event loop.

        This method discards the old client so a new one will be created with
        the current event loop.
        """
        if self._async_client is not None:
            try:
                # Don't await close - we're in sync context and the old loop is closed
                # Just discard the reference so a new client is created
                self._async_client = None
                logger.debug("async_qdrant_client_reset_for_new_event_loop")
            except Exception as e:
                logger.debug("async_qdrant_client_reset_skipped", reason=str(e))
                self._async_client = None

    async def ensure_connection(self) -> bool:
        """Verify Qdrant connection is healthy, reset if stale.

        This method should be called before operations that might fail due to
        stale gRPC connections (e.g., after Docker restarts).

        Returns:
            True if connection is healthy (possibly after reset).

        Raises:
            ConnectionError: If unable to establish connection after reset.
        """
        try:
            # Quick health check - get collections (lightweight operation)
            await self.async_client.get_collections()
            return True
        except Exception as e:
            logger.warning(
                "qdrant_connection_unhealthy",
                error=str(e),
                action="resetting_client",
            )
            # Reset and retry once
            self._async_client = None
            try:
                await self.async_client.get_collections()
                logger.info("qdrant_connection_restored_after_reset")
                return True
            except Exception as retry_error:
                logger.error(
                    "qdrant_connection_failed_after_reset",
                    error=str(retry_error),
                )
                raise ConnectionError(
                    f"Unable to connect to Qdrant: {retry_error}"
                ) from retry_error

    def _collection_name(self, kb_id: UUID) -> str:
        """Generate collection name for a KB.

        Args:
            kb_id: The Knowledge Base UUID.

        Returns:
            Collection name in format `kb_{uuid}`.
        """
        return f"kb_{kb_id}"

    async def create_collection(
        self,
        kb_id: UUID,
        vector_size: int | None = None,
        distance_metric: str = "cosine",
    ) -> None:
        """Create a Qdrant collection for a Knowledge Base.

        Creates a collection with configurable vector dimensions and distance metric.
        If vector_size is not provided, defaults to VECTOR_SIZE (768) for backward
        compatibility.

        Args:
            kb_id: The Knowledge Base UUID.
            vector_size: Vector dimensions. Defaults to 768 if not provided.
            distance_metric: Distance metric (cosine, euclidean, dot).
                           Defaults to "cosine".

        Raises:
            ValueError: If distance_metric is invalid.
            Exception: If collection creation fails.
        """
        collection_name = self._collection_name(kb_id)

        # Use default vector size if not provided
        actual_vector_size = vector_size if vector_size is not None else VECTOR_SIZE

        # Map string distance metric to Qdrant enum
        distance_map = {
            "cosine": models.Distance.COSINE,
            "euclidean": models.Distance.EUCLID,
            "dot": models.Distance.DOT,
        }

        distance = distance_map.get(distance_metric.lower())
        if distance is None:
            raise ValueError(
                f"Invalid distance_metric: {distance_metric}. "
                f"Must be one of: {list(distance_map.keys())}"
            )

        try:
            # Check if collection already exists
            if await self.collection_exists(kb_id):
                logger.warning(
                    "qdrant_collection_exists",
                    collection_name=collection_name,
                    kb_id=str(kb_id),
                )
                return

            # Create collection with vector configuration using async client
            await self.async_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=actual_vector_size,
                    distance=distance,
                ),
            )

            logger.info(
                "qdrant_collection_created",
                collection_name=collection_name,
                kb_id=str(kb_id),
                vector_size=actual_vector_size,
                distance=distance_metric,
            )

        except Exception as e:
            logger.error(
                "qdrant_collection_create_failed",
                collection_name=collection_name,
                kb_id=str(kb_id),
                vector_size=actual_vector_size,
                distance=distance_metric,
                error=str(e),
            )
            raise

    # Alias for backward compatibility - will be removed in future version
    async def create_collection_for_kb(
        self,
        kb_id: UUID,
        vector_size: int,
        distance_metric: str = "cosine",
    ) -> None:
        """Deprecated: Use create_collection(kb_id, vector_size, distance_metric) instead."""
        await self.create_collection(kb_id, vector_size, distance_metric)

    async def delete_collection(self, kb_id: UUID) -> bool:
        """Delete a Qdrant collection for a Knowledge Base.

        Args:
            kb_id: The Knowledge Base UUID.

        Returns:
            True if deleted successfully, False if collection didn't exist.
        """
        collection_name = self._collection_name(kb_id)

        try:
            # Check if collection exists before deleting
            if not await self.collection_exists(kb_id):
                logger.warning(
                    "qdrant_collection_not_found",
                    collection_name=collection_name,
                    kb_id=str(kb_id),
                )
                return False

            await self.async_client.delete_collection(collection_name=collection_name)

            logger.info(
                "qdrant_collection_deleted",
                collection_name=collection_name,
                kb_id=str(kb_id),
            )
            return True

        except Exception as e:
            logger.error(
                "qdrant_collection_delete_failed",
                collection_name=collection_name,
                kb_id=str(kb_id),
                error=str(e),
            )
            raise

    async def collection_exists(self, kb_id: UUID) -> bool:
        """Check if a collection exists for a Knowledge Base.

        Args:
            kb_id: The Knowledge Base UUID.

        Returns:
            True if collection exists, False otherwise.
        """
        collection_name = self._collection_name(kb_id)

        try:
            await self.async_client.get_collection(collection_name=collection_name)
            return True
        except UnexpectedResponse as e:
            if e.status_code == 404:
                return False
            raise
        except Exception:
            # For other errors, assume collection doesn't exist
            return False

    async def upsert_points(
        self,
        kb_id: UUID,
        points: list[models.PointStruct],
    ) -> int:
        """Upsert vectors to a Knowledge Base collection.

        Uses deterministic point IDs for idempotent retries.

        Args:
            kb_id: The Knowledge Base UUID.
            points: List of PointStruct with id, vector, and payload.

        Returns:
            Number of points upserted.

        Raises:
            Exception: If upsert fails.
        """
        collection_name = self._collection_name(kb_id)

        try:
            await self.async_client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True,  # Wait for operation to complete
            )

            logger.info(
                "qdrant_points_upserted",
                collection_name=collection_name,
                kb_id=str(kb_id),
                point_count=len(points),
            )

            return len(points)

        except Exception as e:
            logger.error(
                "qdrant_upsert_failed",
                collection_name=collection_name,
                kb_id=str(kb_id),
                point_count=len(points),
                error=str(e),
            )
            raise

    async def delete_points_by_filter(
        self,
        kb_id: UUID,
        filter_conditions: models.Filter,
    ) -> int:
        """Delete points from a collection matching a filter.

        Used for cleaning up orphan chunks during document re-upload.

        Args:
            kb_id: The Knowledge Base UUID.
            filter_conditions: Qdrant filter for points to delete.

        Returns:
            Number of points deleted (estimated).

        Raises:
            Exception: If deletion fails.
        """
        collection_name = self._collection_name(kb_id)

        try:
            # Get count before deletion for logging
            count_result = await self.async_client.count(
                collection_name=collection_name,
                count_filter=filter_conditions,
            )
            delete_count = count_result.count

            if delete_count == 0:
                logger.debug(
                    "qdrant_no_points_to_delete",
                    collection_name=collection_name,
                    kb_id=str(kb_id),
                )
                return 0

            await self.async_client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(filter=filter_conditions),
                wait=True,
            )

            logger.info(
                "qdrant_points_deleted",
                collection_name=collection_name,
                kb_id=str(kb_id),
                deleted_count=delete_count,
            )

            return delete_count

        except Exception as e:
            logger.error(
                "qdrant_delete_failed",
                collection_name=collection_name,
                kb_id=str(kb_id),
                error=str(e),
            )
            raise

    async def get_collection_info(self, kb_id: UUID) -> dict[str, Any] | None:
        """Get collection information and statistics.

        Args:
            kb_id: The Knowledge Base UUID.

        Returns:
            Dict with collection info, or None if not found.
        """
        collection_name = self._collection_name(kb_id)

        try:
            info = await self.async_client.get_collection(
                collection_name=collection_name
            )

            # Extract vector config from collection info
            vector_size = VECTOR_SIZE  # Default fallback
            distance = DISTANCE_METRIC.value  # Default fallback

            if info.config and info.config.params:
                vectors_config = info.config.params.vectors
                if isinstance(vectors_config, models.VectorParams):
                    vector_size = vectors_config.size
                    if vectors_config.distance:
                        distance = vectors_config.distance.value

            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value if info.status else None,
                "vector_size": vector_size,
                "distance": distance,
            }
        except UnexpectedResponse as e:
            if e.status_code == 404:
                return None
            raise
        except Exception:
            return None

    async def health_check(self) -> bool:
        """Check if Qdrant is healthy and accessible.

        Returns:
            True if Qdrant is healthy, False otherwise.
        """
        try:
            # Try to list collections as a health check
            await self.async_client.get_collections()
            return True
        except Exception as e:
            logger.warning("qdrant_health_check_failed", error=str(e))
            return False

    # Native async methods for ChunkService and SearchService (Story 7-7)

    async def scroll(
        self,
        collection_name: str,
        scroll_filter: models.Filter | None = None,
        limit: int = 10,
        with_payload: bool = True,
        with_vectors: bool = False,
        offset: str | int | None = None,
    ) -> tuple[list[models.Record], str | int | None]:
        """Native async scroll through collection points.

        Args:
            collection_name: Name of the collection.
            scroll_filter: Optional filter conditions.
            limit: Maximum points to return.
            with_payload: Include payload in response.
            with_vectors: Include vectors in response.
            offset: Offset for pagination.

        Returns:
            Tuple of (points, next_offset).
        """
        return await self.async_client.scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=limit,
            with_payload=with_payload,
            with_vectors=with_vectors,
            offset=offset,
        )

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        query_filter: models.Filter | None = None,
        limit: int = 10,
        offset: int = 0,
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> list[models.ScoredPoint]:
        """Native async vector search.

        Uses query_points API (qdrant-client 1.16+) and converts response
        to ScoredPoint list for backward compatibility.

        Args:
            collection_name: Name of the collection.
            query_vector: Query embedding vector.
            query_filter: Optional filter conditions.
            limit: Maximum results to return.
            offset: Offset for pagination (applied by skipping results).
            with_payload: Include payload in response.
            with_vectors: Include vectors in response.

        Returns:
            List of ScoredPoint results.
        """
        # qdrant-client 1.16+ uses query_points instead of search
        # Fetch extra results to handle offset (query_points doesn't support offset)
        fetch_limit = limit + offset if offset > 0 else limit

        response = await self.async_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=fetch_limit,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )

        # Apply offset by skipping results
        points = response.points[offset:] if offset > 0 else response.points

        # Convert QueryResponse points to ScoredPoint for backward compatibility
        return [
            models.ScoredPoint(
                id=point.id,
                version=getattr(point, "version", 0),
                score=point.score or 0.0,
                payload=point.payload,
                vector=point.vector,
            )
            for point in points[:limit]
        ]

    async def count(
        self,
        collection_name: str,
        count_filter: models.Filter | None = None,
        exact: bool = True,
    ) -> models.CountResult:
        """Native async count points.

        Args:
            collection_name: Name of the collection.
            count_filter: Optional filter conditions.
            exact: If True, count exactly (slower but accurate).

        Returns:
            CountResult with count.
        """
        return await self.async_client.count(
            collection_name=collection_name,
            count_filter=count_filter,
            exact=exact,
        )

    async def query_points(
        self,
        collection_name: str,
        query: list[float],
        query_filter: models.Filter | None = None,
        limit: int = 10,
        with_payload: bool = True,
        score_threshold: float | None = None,
    ) -> models.QueryResponse:
        """Native async query points (qdrant-client 1.16+ API).

        Args:
            collection_name: Name of the collection.
            query: Query embedding vector.
            query_filter: Optional filter conditions.
            limit: Maximum results to return.
            with_payload: Include payload in response.
            score_threshold: Minimum similarity score threshold for results.

        Returns:
            QueryResponse with points.
        """
        return await self.async_client.query_points(
            collection_name=collection_name,
            query=query,
            query_filter=query_filter,
            limit=limit,
            with_payload=with_payload,
            score_threshold=score_threshold,
        )

    async def retrieve(
        self,
        collection_name: str,
        ids: list[str | int],
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> list[models.Record]:
        """Native async retrieve points by IDs.

        Args:
            collection_name: Name of the collection.
            ids: List of point IDs to retrieve.
            with_payload: Include payload in response.
            with_vectors: Include vectors in response.

        Returns:
            List of Record objects.
        """
        return await self.async_client.retrieve(
            collection_name=collection_name,
            ids=ids,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )

    async def set_payload(
        self,
        collection_name: str,
        payload: dict[str, Any],
        points: list[str | int] | models.Filter,
        wait: bool = True,
    ) -> None:
        """Native async set payload on points.

        Args:
            collection_name: Name of the collection.
            payload: Payload to set.
            points: Point IDs or filter to select points.
            wait: Wait for operation to complete.
        """
        await self.async_client.set_payload(
            collection_name=collection_name,
            payload=payload,
            points=points,
            wait=wait,
        )


# Singleton instance for use across the application
qdrant_service = QdrantService()


def _cleanup_qdrant() -> None:
    """Atexit handler to cleanup Qdrant connections on process exit."""
    qdrant_service.close(grpc_grace=1.0)


# Register cleanup handler for graceful shutdown
atexit.register(_cleanup_qdrant)
