"""Qdrant vector database integration for Knowledge Base collections."""

import atexit
from typing import Any
from uuid import UUID

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Vector configuration per tech-spec
VECTOR_SIZE = 1536  # OpenAI ada-002 dimensions
DISTANCE_METRIC = models.Distance.COSINE

# Connection configuration to prevent "too many open files" errors
GRPC_OPTIONS = [
    # Limit concurrent streams per connection
    ("grpc.max_concurrent_streams", 100),
    # Enable keepalive to detect dead connections
    ("grpc.keepalive_time_ms", 30000),
    ("grpc.keepalive_timeout_ms", 10000),
    ("grpc.keepalive_permit_without_calls", 1),
    # HTTP/2 flow control
    ("grpc.http2.max_pings_without_data", 0),
    ("grpc.http2.min_time_between_pings_ms", 10000),
]


class QdrantService:
    """Service for managing Qdrant collections.

    Each Knowledge Base has its own collection named `kb_{uuid}`.
    This ensures zero-trust isolation between KBs.

    Connection Management:
    - Uses lazy initialization with singleton pattern
    - Includes gRPC options for connection limits and keepalive
    - Provides close() method for explicit cleanup
    - Registers atexit handler for graceful shutdown
    """

    def __init__(self) -> None:
        """Initialize Qdrant client with settings."""
        self._client: QdrantClient | None = None
        self._closed: bool = False

    @property
    def client(self) -> QdrantClient:
        """Lazy initialization of Qdrant client with connection management.

        Returns:
            QdrantClient: The Qdrant client instance.

        Raises:
            RuntimeError: If service has been closed.
        """
        if self._closed:
            raise RuntimeError("QdrantService has been closed")

        if self._client is None:
            self._client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                grpc_port=settings.qdrant_grpc_port,
                prefer_grpc=True,
                grpc_options=GRPC_OPTIONS,
            )
            logger.info(
                "qdrant_client_initialized",
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                grpc_port=settings.qdrant_grpc_port,
            )
        return self._client

    def close(self, grpc_grace: float | None = None) -> None:
        """Close the Qdrant client and release connections.

        Should be called during application shutdown to prevent
        resource leaks and "too many open files" errors.

        Args:
            grpc_grace: Grace period in seconds for gRPC channel shutdown.
                       None means immediate shutdown.
        """
        if self._client is not None and not self._closed:
            try:
                self._client.close(grpc_grace=grpc_grace)
                logger.info("qdrant_client_closed")
            except Exception as e:
                # Log but don't raise - shutdown should be best-effort
                logger.warning("qdrant_client_close_error", error=str(e))
            finally:
                self._client = None
                self._closed = True

    def reset(self) -> None:
        """Reset the service for reuse (e.g., in tests).

        Closes existing connection and allows new connections.
        """
        self.close()
        self._closed = False

    def _collection_name(self, kb_id: UUID) -> str:
        """Generate collection name for a KB.

        Args:
            kb_id: The Knowledge Base UUID.

        Returns:
            Collection name in format `kb_{uuid}`.
        """
        return f"kb_{kb_id}"

    async def create_collection(self, kb_id: UUID) -> None:
        """Create a Qdrant collection for a Knowledge Base.

        Creates a collection with:
        - Vector size: 1536 (OpenAI ada-002)
        - Distance metric: Cosine similarity

        Args:
            kb_id: The Knowledge Base UUID.

        Raises:
            Exception: If collection creation fails.
        """
        collection_name = self._collection_name(kb_id)

        try:
            # Check if collection already exists
            if await self.collection_exists(kb_id):
                logger.warning(
                    "qdrant_collection_exists",
                    collection_name=collection_name,
                    kb_id=str(kb_id),
                )
                return

            # Create collection with vector configuration
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=DISTANCE_METRIC,
                ),
            )

            logger.info(
                "qdrant_collection_created",
                collection_name=collection_name,
                kb_id=str(kb_id),
                vector_size=VECTOR_SIZE,
                distance=DISTANCE_METRIC.value,
            )

        except Exception as e:
            logger.error(
                "qdrant_collection_create_failed",
                collection_name=collection_name,
                kb_id=str(kb_id),
                error=str(e),
            )
            raise

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

            self.client.delete_collection(collection_name=collection_name)

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
            self.client.get_collection(collection_name=collection_name)
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
            self.client.upsert(
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
            count_result = self.client.count(
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

            self.client.delete(
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
            info = self.client.get_collection(collection_name=collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value if info.status else None,
                "vector_size": VECTOR_SIZE,
                "distance": DISTANCE_METRIC.value,
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
            self.client.get_collections()
            return True
        except Exception as e:
            logger.warning("qdrant_health_check_failed", error=str(e))
            return False


# Singleton instance for use across the application
qdrant_service = QdrantService()


def _cleanup_qdrant() -> None:
    """Atexit handler to cleanup Qdrant connections on process exit."""
    qdrant_service.close(grpc_grace=1.0)


# Register cleanup handler for graceful shutdown
atexit.register(_cleanup_qdrant)
