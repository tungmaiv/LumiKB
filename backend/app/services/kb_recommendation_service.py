"""KB Recommendation service for personalized KB suggestions.

Implements smart scoring algorithm with:
- Recent access count (40% weight) - last 30 days
- Search relevance (35% weight) - KB search frequency ratio
- Shared access (25% weight) - global popularity

Uses Redis caching with 1-hour TTL for performance.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis_client
from app.models.kb_access_log import AccessType, KBAccessLog
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission
from app.models.user import User
from app.schemas.kb_recommendation import KBRecommendation

logger = structlog.get_logger()

# Cache configuration
CACHE_KEY_PREFIX = "kb_recommendations:user:"
CACHE_TTL = 3600  # 1 hour

# Scoring weights (must sum to 1.0)
WEIGHT_RECENT_ACCESS = 0.40
WEIGHT_SEARCH_RELEVANCE = 0.35
WEIGHT_SHARED_ACCESS = 0.25

# Cold start detection threshold
COLD_START_DAYS = 7
MIN_SEARCHES_FOR_PERSONALIZATION = 1


class KBRecommendationService:
    """Service for generating personalized KB recommendations.

    Uses weighted scoring algorithm combining user activity patterns
    and global popularity. Falls back to popular public KBs for
    new users (cold start).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_recommendations(
        self, user_id: UUID, limit: int = 5
    ) -> list[KBRecommendation]:
        """Get personalized KB recommendations for a user.

        Checks Redis cache first, falls back to calculation on cache miss.

        Args:
            user_id: The user's UUID.
            limit: Maximum number of recommendations (default 5).

        Returns:
            List of KBRecommendation objects sorted by score (highest first).
        """
        cache_key = f"{CACHE_KEY_PREFIX}{user_id}"

        # Try cache first
        try:
            redis = await get_redis_client()
            cached = await redis.get(cache_key)
            if cached:
                logger.info("kb_recommendations_cache_hit", user_id=str(user_id))
                import json

                data = json.loads(cached)
                return [KBRecommendation(**r) for r in data]
        except Exception as e:
            logger.warning("redis_unavailable", error=str(e))
            # Continue with DB calculation if Redis fails

        # Cache miss - calculate recommendations
        logger.info("kb_recommendations_cache_miss", user_id=str(user_id))

        # Check if cold start
        is_cold_start = await self._is_cold_start_user(user_id)

        if is_cold_start:
            recommendations = await self._get_cold_start_recommendations(limit)
        else:
            recommendations = await self._calculate_personalized_recommendations(
                user_id, limit
            )

        # Store in cache (best effort)
        try:
            redis = await get_redis_client()
            import json

            cache_data = json.dumps(
                [r.model_dump(mode="json") for r in recommendations]
            )
            await redis.setex(cache_key, CACHE_TTL, cache_data)
        except Exception as e:
            logger.warning("redis_cache_set_failed", error=str(e))

        return recommendations

    async def _is_cold_start_user(self, user_id: UUID) -> bool:
        """Check if user qualifies for cold start (no meaningful history).

        Cold start criteria:
        - Account created < 7 days ago AND
        - Has 0 search accesses

        Args:
            user_id: The user's UUID.

        Returns:
            True if user should receive cold start recommendations.
        """
        # Get user creation date
        user = await self.session.get(User, user_id)
        if not user:
            return True

        # Check if user is new (< 7 days)
        days_since_creation = (datetime.now(UTC) - user.created_at).days
        if days_since_creation >= COLD_START_DAYS:
            return False

        # Check if user has any search history
        search_count = await self.session.scalar(
            select(func.count(KBAccessLog.id)).where(
                KBAccessLog.user_id == user_id,
                KBAccessLog.access_type == AccessType.SEARCH,
            )
        )

        return (search_count or 0) < MIN_SEARCHES_FOR_PERSONALIZATION

    async def _get_cold_start_recommendations(
        self, limit: int
    ) -> list[KBRecommendation]:
        """Get popular public KBs for cold start users.

        Falls back to most accessed public KBs when user has no history.

        Args:
            limit: Maximum number of recommendations.

        Returns:
            List of KBRecommendation objects with is_cold_start=True.
        """
        # Get public KBs sorted by global access count
        # First, get access counts per KB
        access_counts_subquery = (
            select(KBAccessLog.kb_id, func.count(KBAccessLog.id).label("access_count"))
            .group_by(KBAccessLog.kb_id)
            .subquery()
        )

        # Join with KBs and filter for active status
        query = (
            select(
                KnowledgeBase,
                func.coalesce(access_counts_subquery.c.access_count, 0).label(
                    "access_count"
                ),
            )
            .outerjoin(
                access_counts_subquery,
                KnowledgeBase.id == access_counts_subquery.c.kb_id,
            )
            .where(KnowledgeBase.status == "active")
            .order_by(
                func.coalesce(access_counts_subquery.c.access_count, 0).desc(),
                KnowledgeBase.created_at.desc(),
            )
            .limit(limit)
        )

        result = await self.session.execute(query)
        rows = result.all()

        recommendations = []
        for row in rows:
            kb = row[0]
            access_count = row[1]

            # Calculate a simple popularity score (0-100)
            # Just normalize based on access count
            score = min(100.0, float(access_count) * 10) if access_count > 0 else 50.0

            recommendations.append(
                KBRecommendation(
                    kb_id=kb.id,
                    kb_name=kb.name,
                    description=kb.description or "",
                    score=round(score, 1),
                    reason="Popular knowledge base",
                    last_accessed=None,
                    is_cold_start=True,
                )
            )

        return recommendations

    async def _calculate_personalized_recommendations(
        self, user_id: UUID, limit: int
    ) -> list[KBRecommendation]:
        """Calculate personalized recommendations using scoring algorithm.

        Algorithm:
        - recent_access (40%): User's KB access count in last 30 days
        - search_relevance (35%): Ratio of user's searches in this KB vs total
        - shared_access (25%): Global KB popularity

        Uses batch queries to avoid N+1 pattern.

        Args:
            user_id: The user's UUID.
            limit: Maximum number of recommendations.

        Returns:
            List of KBRecommendation objects sorted by score.
        """
        # Get KBs user has access to (owner OR has permission)
        accessible_kbs = await self._get_accessible_kbs(user_id)

        if not accessible_kbs:
            return []

        kb_ids = [kb.id for kb in accessible_kbs]

        # Batch load all scoring data in parallel queries to avoid N+1
        (
            recent_access_data,
            search_relevance_data,
            shared_access_data,
            last_access_data,
        ) = await self._batch_load_scoring_data(user_id, kb_ids)

        # Calculate scores for each KB using pre-loaded data
        scored_kbs: list[tuple[KnowledgeBase, float, str, datetime | None]] = []

        for kb in accessible_kbs:
            recent_score = self._compute_recent_score(kb.id, recent_access_data)
            search_score = self._compute_search_score(kb.id, search_relevance_data)
            shared_score = self._compute_shared_score(kb.id, shared_access_data)
            last_accessed = last_access_data.get(kb.id)

            # Calculate weighted score
            raw_score = (
                recent_score * WEIGHT_RECENT_ACCESS
                + search_score * WEIGHT_SEARCH_RELEVANCE
                + shared_score * WEIGHT_SHARED_ACCESS
            )

            # Normalize to 0-100
            normalized_score = min(100.0, max(0.0, raw_score * 100))

            # Generate reason based on dominant factor
            reason = self._generate_reason(recent_score, search_score, shared_score)

            scored_kbs.append((kb, normalized_score, reason, last_accessed))

        # Sort by score descending and take top N
        scored_kbs.sort(key=lambda x: x[1], reverse=True)
        top_kbs = scored_kbs[:limit]

        return [
            KBRecommendation(
                kb_id=kb.id,
                kb_name=kb.name,
                description=kb.description or "",
                score=round(score, 1),
                reason=reason,
                last_accessed=last_accessed,
                is_cold_start=False,
            )
            for kb, score, reason, last_accessed in top_kbs
        ]

    async def _batch_load_scoring_data(
        self, user_id: UUID, kb_ids: list[UUID]
    ) -> tuple[dict, dict, dict, dict[UUID, datetime | None]]:
        """Batch load all scoring data in optimized queries.

        Eliminates N+1 query pattern by loading all data upfront.

        Args:
            user_id: The user's UUID.
            kb_ids: List of KB UUIDs to load data for.

        Returns:
            Tuple of (recent_access_data, search_relevance_data, shared_access_data, last_access_data)
        """
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        # Query 1: Recent access counts per KB (user's 30-day access)
        recent_query = (
            select(
                KBAccessLog.kb_id,
                func.count(KBAccessLog.id).label("access_count"),
            )
            .where(
                KBAccessLog.user_id == user_id,
                KBAccessLog.kb_id.in_(kb_ids),
                KBAccessLog.accessed_at >= thirty_days_ago,
            )
            .group_by(KBAccessLog.kb_id)
        )
        recent_result = await self.session.execute(recent_query)
        recent_counts = {row.kb_id: row.access_count for row in recent_result.all()}

        # Get max recent access for normalization
        max_recent = max(recent_counts.values()) if recent_counts else 0

        recent_access_data = {
            "counts": recent_counts,
            "max": max_recent,
        }

        # Query 2: Search counts per KB (user's search history)
        search_query = (
            select(
                KBAccessLog.kb_id,
                func.count(KBAccessLog.id).label("search_count"),
            )
            .where(
                KBAccessLog.user_id == user_id,
                KBAccessLog.kb_id.in_(kb_ids),
                KBAccessLog.access_type == AccessType.SEARCH,
            )
            .group_by(KBAccessLog.kb_id)
        )
        search_result = await self.session.execute(search_query)
        search_counts = {row.kb_id: row.search_count for row in search_result.all()}

        # Get total search count for normalization
        total_searches = sum(search_counts.values())

        search_relevance_data = {
            "counts": search_counts,
            "total": total_searches,
        }

        # Query 3: Global access counts per KB (shared access/popularity)
        shared_query = (
            select(
                KBAccessLog.kb_id,
                func.count(KBAccessLog.id).label("access_count"),
            )
            .where(KBAccessLog.kb_id.in_(kb_ids))
            .group_by(KBAccessLog.kb_id)
        )
        shared_result = await self.session.execute(shared_query)
        shared_counts = {row.kb_id: row.access_count for row in shared_result.all()}

        # Get max global access for normalization
        max_shared = max(shared_counts.values()) if shared_counts else 0

        shared_access_data = {
            "counts": shared_counts,
            "max": max_shared,
        }

        # Query 4: Last access time per KB
        last_access_query = (
            select(
                KBAccessLog.kb_id,
                func.max(KBAccessLog.accessed_at).label("last_access"),
            )
            .where(
                KBAccessLog.user_id == user_id,
                KBAccessLog.kb_id.in_(kb_ids),
            )
            .group_by(KBAccessLog.kb_id)
        )
        last_access_result = await self.session.execute(last_access_query)
        last_access_data: dict[UUID, datetime | None] = {
            row.kb_id: row.last_access for row in last_access_result.all()
        }

        return (
            recent_access_data,
            search_relevance_data,
            shared_access_data,
            last_access_data,
        )

    def _compute_recent_score(self, kb_id: UUID, recent_data: dict) -> float:
        """Compute recent access score from batch-loaded data.

        Args:
            kb_id: The KB's UUID.
            recent_data: Pre-loaded recent access data.

        Returns:
            Score between 0.0 and 1.0.
        """
        counts = recent_data["counts"]
        max_count = recent_data["max"]

        if not max_count:
            return 0.0

        kb_count = counts.get(kb_id, 0)
        return float(kb_count) / float(max_count) if kb_count else 0.0

    def _compute_search_score(self, kb_id: UUID, search_data: dict) -> float:
        """Compute search relevance score from batch-loaded data.

        Args:
            kb_id: The KB's UUID.
            search_data: Pre-loaded search relevance data.

        Returns:
            Score between 0.0 and 1.0.
        """
        counts = search_data["counts"]
        total = search_data["total"]

        if not total:
            return 0.0

        kb_count = counts.get(kb_id, 0)
        return float(kb_count) / float(total) if kb_count else 0.0

    def _compute_shared_score(self, kb_id: UUID, shared_data: dict) -> float:
        """Compute shared access score from batch-loaded data.

        Args:
            kb_id: The KB's UUID.
            shared_data: Pre-loaded shared access data.

        Returns:
            Score between 0.0 and 1.0.
        """
        counts = shared_data["counts"]
        max_count = shared_data["max"]

        if not max_count:
            return 0.0

        kb_count = counts.get(kb_id, 0)
        return float(kb_count) / float(max_count) if kb_count else 0.0

    async def _get_accessible_kbs(self, user_id: UUID) -> list[KnowledgeBase]:
        """Get all KBs a user can access (owner or has permission).

        Args:
            user_id: The user's UUID.

        Returns:
            List of accessible KnowledgeBase objects.
        """
        query = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.status == "active",
                or_(
                    KnowledgeBase.owner_id == user_id,
                    KnowledgeBase.id.in_(
                        select(KBPermission.kb_id).where(
                            KBPermission.user_id == user_id
                        )
                    ),
                ),
            )
            .distinct()
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_recent_access_score(self, user_id: UUID, kb_id: UUID) -> float:
        """Calculate recent access score (30-day window).

        Score is normalized by dividing user's KB access count by their max
        access count across all KBs.

        Args:
            user_id: The user's UUID.
            kb_id: The KB's UUID.

        Returns:
            Score between 0.0 and 1.0.
        """
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

        # Get user's access count for this KB in last 30 days
        kb_access_count = await self.session.scalar(
            select(func.count(KBAccessLog.id)).where(
                KBAccessLog.user_id == user_id,
                KBAccessLog.kb_id == kb_id,
                KBAccessLog.accessed_at >= thirty_days_ago,
            )
        )

        if not kb_access_count:
            return 0.0

        # Get user's max access count for any KB in last 30 days
        max_access_count = await self.session.scalar(
            select(func.count(KBAccessLog.id))
            .where(
                KBAccessLog.user_id == user_id,
                KBAccessLog.accessed_at >= thirty_days_ago,
            )
            .group_by(KBAccessLog.kb_id)
            .order_by(func.count(KBAccessLog.id).desc())
            .limit(1)
        )

        if not max_access_count:
            return 0.0

        return float(kb_access_count) / float(max_access_count)

    async def _get_search_relevance_score(self, user_id: UUID, kb_id: UUID) -> float:
        """Calculate search relevance score.

        Score is ratio of user's searches in this KB vs total searches.

        Args:
            user_id: The user's UUID.
            kb_id: The KB's UUID.

        Returns:
            Score between 0.0 and 1.0.
        """
        # Get user's search count for this KB
        kb_search_count = await self.session.scalar(
            select(func.count(KBAccessLog.id)).where(
                KBAccessLog.user_id == user_id,
                KBAccessLog.kb_id == kb_id,
                KBAccessLog.access_type == AccessType.SEARCH,
            )
        )

        if not kb_search_count:
            return 0.0

        # Get user's total search count
        total_search_count = await self.session.scalar(
            select(func.count(KBAccessLog.id)).where(
                KBAccessLog.user_id == user_id,
                KBAccessLog.access_type == AccessType.SEARCH,
            )
        )

        if not total_search_count:
            return 0.0

        return float(kb_search_count) / float(total_search_count)

    async def _get_shared_access_score(self, kb_id: UUID) -> float:
        """Calculate shared access score (global popularity).

        Score is KB's total access count normalized by max access count
        across all KBs.

        Args:
            kb_id: The KB's UUID.

        Returns:
            Score between 0.0 and 1.0.
        """
        # Get this KB's total access count
        kb_access_count = await self.session.scalar(
            select(func.count(KBAccessLog.id)).where(KBAccessLog.kb_id == kb_id)
        )

        if not kb_access_count:
            return 0.0

        # Get max access count across all KBs
        max_access_count = await self.session.scalar(
            select(func.count(KBAccessLog.id))
            .group_by(KBAccessLog.kb_id)
            .order_by(func.count(KBAccessLog.id).desc())
            .limit(1)
        )

        if not max_access_count:
            return 0.0

        return float(kb_access_count) / float(max_access_count)

    async def _get_last_access_time(
        self, user_id: UUID, kb_id: UUID
    ) -> datetime | None:
        """Get user's last access time for a KB.

        Args:
            user_id: The user's UUID.
            kb_id: The KB's UUID.

        Returns:
            Last access datetime or None if never accessed.
        """
        result = await self.session.scalar(
            select(func.max(KBAccessLog.accessed_at)).where(
                KBAccessLog.user_id == user_id,
                KBAccessLog.kb_id == kb_id,
            )
        )
        return result

    def _generate_reason(
        self, recent_score: float, search_score: float, shared_score: float
    ) -> str:
        """Generate human-readable reason based on dominant scoring factor.

        Args:
            recent_score: Recent access score (0-1).
            search_score: Search relevance score (0-1).
            shared_score: Shared access score (0-1).

        Returns:
            Human-readable reason string.
        """
        weighted = [
            (recent_score * WEIGHT_RECENT_ACCESS, "Frequently accessed recently"),
            (search_score * WEIGHT_SEARCH_RELEVANCE, "Matches your search patterns"),
            (shared_score * WEIGHT_SHARED_ACCESS, "Popular among users"),
        ]

        # Get top contributor
        weighted.sort(key=lambda x: x[0], reverse=True)
        _, reason = weighted[0]

        return reason

    async def invalidate_user_recommendations(self, user_id: UUID) -> None:
        """Invalidate cached recommendations for a user.

        Call this when user activity should trigger recalculation
        (new KB created, search performed).

        Args:
            user_id: The user's UUID.
        """
        cache_key = f"{CACHE_KEY_PREFIX}{user_id}"

        try:
            redis = await get_redis_client()
            await redis.delete(cache_key)
            logger.info("kb_recommendations_cache_invalidated", user_id=str(user_id))
        except Exception as e:
            logger.warning(
                "redis_cache_invalidation_failed",
                user_id=str(user_id),
                error=str(e),
            )

    async def log_kb_access(
        self, user_id: UUID, kb_id: UUID, access_type: AccessType
    ) -> None:
        """Log a KB access event for recommendation algorithm.

        Fire-and-forget pattern - does not raise exceptions.
        Also invalidates user's recommendation cache.

        Args:
            user_id: The user's UUID.
            kb_id: The KB's UUID.
            access_type: Type of access (search, view, edit).
        """
        try:
            access_log = KBAccessLog(
                user_id=user_id,
                kb_id=kb_id,
                access_type=access_type,
            )
            self.session.add(access_log)
            await self.session.commit()

            # Invalidate cache after new access
            await self.invalidate_user_recommendations(user_id)
        except Exception as e:
            logger.warning(
                "kb_access_log_failed",
                user_id=str(user_id),
                kb_id=str(kb_id),
                access_type=access_type.value,
                error=str(e),
            )
