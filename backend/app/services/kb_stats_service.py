"""KB statistics service for admin view."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis_client
from app.integrations.minio_client import MinIOService
from app.integrations.qdrant_client import QdrantService
from app.models.audit import AuditEvent
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.schemas.kb_stats import KBDetailedStats, TopDocument

logger = structlog.get_logger()

CACHE_TTL = 600  # 10 minutes


class KBStatsService:
    """Service for aggregating KB-specific statistics.

    Aggregates metrics from PostgreSQL, MinIO, and Qdrant.
    Uses Redis caching with 10-minute TTL to reduce load.
    Falls back gracefully if external services unavailable.
    """

    def __init__(
        self,
        session: AsyncSession,
        minio_service: MinIOService,
        qdrant_service: QdrantService,
    ) -> None:
        """Initialize service with dependencies.

        Args:
            session: SQLAlchemy async session.
            minio_service: MinIO client for storage queries.
            qdrant_service: Qdrant client for vector queries.
        """
        self.session = session
        self.minio_service = minio_service
        self.qdrant_service = qdrant_service

    async def get_kb_stats(self, kb_id: UUID) -> KBDetailedStats:
        """Get detailed KB statistics with Redis caching.

        Args:
            kb_id: Knowledge Base UUID.

        Returns:
            KBDetailedStats: Comprehensive KB statistics.

        Raises:
            ValueError: If KB not found.
        """
        cache_key = f"kb:stats:{kb_id}"

        try:
            redis = await get_redis_client()

            # Try cache first
            cached = await redis.get(cache_key)
            if cached:
                logger.info("kb_stats_cache_hit", kb_id=str(kb_id))
                return KBDetailedStats.model_validate_json(cached)
        except Exception as e:
            logger.warning("redis_unavailable", error=str(e))
            # Continue with aggregation if Redis fails

        # Cache miss - aggregate from multiple sources
        logger.info("kb_stats_cache_miss", kb_id=str(kb_id))
        stats = await self._aggregate_kb_stats(kb_id)

        # Store in cache (best effort)
        try:
            redis = await get_redis_client()
            await redis.setex(cache_key, CACHE_TTL, stats.model_dump_json())
        except Exception as e:
            logger.warning("redis_cache_set_failed", error=str(e))

        return stats

    async def _aggregate_kb_stats(self, kb_id: UUID) -> KBDetailedStats:
        """Aggregate KB statistics from multiple sources.

        Args:
            kb_id: Knowledge Base UUID.

        Returns:
            KBDetailedStats: Aggregated statistics.

        Raises:
            ValueError: If KB not found.
        """
        # Verify KB exists and get name
        kb = await self.session.scalar(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        if not kb:
            raise ValueError(f"Knowledge base not found: {kb_id}")

        # Document count (PostgreSQL)
        document_count = (
            await self.session.scalar(
                select(func.count(Document.id)).where(Document.kb_id == kb_id)
            )
            or 0
        )

        # Storage bytes (MinIO) - graceful degradation
        storage_bytes = await self._get_storage_bytes(kb_id)

        # Vector metrics (Qdrant) - graceful degradation
        total_chunks, total_embeddings = await self._get_vector_metrics(kb_id)

        # Usage metrics (audit.events) - last 30 days
        searches_30d, generations_30d, unique_users_30d = await self._get_usage_metrics(
            kb_id
        )

        # Top documents (audit.events) - last 30 days
        top_documents = await self._get_top_documents(kb_id)

        return KBDetailedStats(
            kb_id=kb_id,
            kb_name=kb.name,
            document_count=document_count,
            storage_bytes=storage_bytes,
            total_chunks=total_chunks,
            total_embeddings=total_embeddings,
            searches_30d=searches_30d,
            generations_30d=generations_30d,
            unique_users_30d=unique_users_30d,
            top_documents=top_documents,
            last_updated=datetime.now(UTC),
        )

    async def _get_storage_bytes(self, kb_id: UUID) -> int:
        """Get total storage bytes from MinIO.

        Args:
            kb_id: Knowledge Base UUID.

        Returns:
            Total storage bytes, or 0 if MinIO unavailable.
        """
        try:
            # Query all documents to get file sizes
            result = await self.session.execute(
                select(Document.file_path, Document.file_size_bytes).where(
                    Document.kb_id == kb_id
                )
            )
            documents = result.all()

            if not documents:
                return 0

            # Sum file sizes from database (more reliable than querying MinIO)
            total_bytes = sum(doc.file_size_bytes or 0 for doc in documents)
            return total_bytes

        except Exception as e:
            logger.warning(
                "storage_query_failed",
                kb_id=str(kb_id),
                error=str(e),
            )
            return 0  # Graceful degradation

    async def _get_vector_metrics(self, kb_id: UUID) -> tuple[int, int]:
        """Get vector metrics from Qdrant.

        Args:
            kb_id: Knowledge Base UUID.

        Returns:
            Tuple of (total_chunks, total_embeddings).
            Returns (0, 0) if Qdrant unavailable.
        """
        try:
            collection_info = await self.qdrant_service.get_collection_info(kb_id)
            if collection_info:
                # points_count = chunks, vectors_count = embeddings
                points = collection_info.get("points_count", 0)
                vectors = collection_info.get("vectors_count", 0)
                return (points, vectors)
            return (0, 0)
        except Exception as e:
            logger.warning(
                "qdrant_query_failed",
                kb_id=str(kb_id),
                error=str(e),
            )
            return (0, 0)  # Graceful degradation

    async def _get_usage_metrics(self, kb_id: UUID) -> tuple[int, int, int]:
        """Get usage metrics from audit.events.

        Args:
            kb_id: Knowledge Base UUID.

        Returns:
            Tuple of (searches_30d, generations_30d, unique_users_30d).
        """
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        # Search count
        searches_30d = (
            await self.session.scalar(
                select(func.count(AuditEvent.id)).where(
                    AuditEvent.timestamp >= thirty_days_ago,
                    AuditEvent.action == "search",
                    AuditEvent.details["kb_id"].astext == str(kb_id),
                )
            )
            or 0
        )

        # Generation count
        generations_30d = (
            await self.session.scalar(
                select(func.count(AuditEvent.id)).where(
                    AuditEvent.timestamp >= thirty_days_ago,
                    AuditEvent.action.in_(
                        ["generation.request", "generation.complete"]
                    ),
                    AuditEvent.details["kb_id"].astext == str(kb_id),
                )
            )
            or 0
        )

        # Unique users count
        unique_users_30d = (
            await self.session.scalar(
                select(func.count(func.distinct(AuditEvent.user_id))).where(
                    AuditEvent.timestamp >= thirty_days_ago,
                    AuditEvent.details["kb_id"].astext == str(kb_id),
                    AuditEvent.user_id.is_not(None),
                )
            )
            or 0
        )

        return (searches_30d, generations_30d, unique_users_30d)

    async def _get_top_documents(self, kb_id: UUID) -> list[TopDocument]:
        """Get top 5 most accessed documents from audit.events.

        Args:
            kb_id: Knowledge Base UUID.

        Returns:
            List of top 5 documents with access counts.
        """
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        # Query audit.events for document access counts
        result = await self.session.execute(
            select(
                AuditEvent.resource_id,
                func.count(AuditEvent.id).label("access_count"),
            )
            .where(
                AuditEvent.timestamp >= thirty_days_ago,
                AuditEvent.resource_type == "document",
                AuditEvent.details["kb_id"].astext == str(kb_id),
                AuditEvent.resource_id.is_not(None),
            )
            .group_by(AuditEvent.resource_id)
            .order_by(func.count(AuditEvent.id).desc())
            .limit(5)
        )
        top_docs_raw = result.all()

        # Enrich with document metadata
        top_documents = []
        for doc_id_str, access_count in top_docs_raw:
            try:
                doc_id = UUID(doc_id_str)
                doc = await self.session.scalar(
                    select(Document).where(Document.id == doc_id)
                )
                if doc:
                    top_documents.append(
                        TopDocument(
                            id=doc.id,
                            filename=doc.original_filename,
                            access_count=access_count,
                        )
                    )
            except (ValueError, Exception) as e:
                logger.warning(
                    "top_document_metadata_fetch_failed",
                    doc_id=doc_id_str,
                    error=str(e),
                )
                continue

        return top_documents
