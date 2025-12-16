"""Admin statistics service for dashboard metrics."""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis_client
from app.models.audit import AuditEvent
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.admin import (
    ActivityStats,
    AdminStats,
    DocumentStats,
    KnowledgeBaseStats,
    PeriodStats,
    StorageStats,
    TrendData,
    UserStats,
)

logger = structlog.get_logger()

CACHE_KEY = "admin:stats:dashboard"
CACHE_TTL = 300  # 5 minutes


class AdminStatsService:
    """Service for aggregating admin dashboard statistics.

    Uses Redis caching with 5-minute TTL to reduce database load.
    Falls back to direct DB queries if Redis unavailable.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_dashboard_stats(self) -> AdminStats:
        """Get admin dashboard statistics with Redis caching.

        Returns:
            AdminStats: Comprehensive system statistics.
        """
        try:
            redis = await get_redis_client()

            # Try cache first
            cached = await redis.get(CACHE_KEY)
            if cached:
                logger.info("admin_stats_cache_hit")
                return AdminStats.model_validate_json(cached)
        except Exception as e:
            logger.warning("redis_unavailable", error=str(e))
            # Continue with DB aggregation if Redis fails

        # Cache miss - aggregate from DB
        logger.info("admin_stats_cache_miss")
        stats = await self._aggregate_stats()

        # Store in cache (best effort)
        try:
            redis = await get_redis_client()
            await redis.setex(CACHE_KEY, CACHE_TTL, stats.model_dump_json())
        except Exception as e:
            logger.warning("redis_cache_set_failed", error=str(e))

        return stats

    async def _aggregate_stats(self) -> AdminStats:
        """Aggregate statistics from database.

        Returns:
            AdminStats: Aggregated system statistics.
        """
        # User stats
        total_users = await self.session.scalar(select(func.count(User.id))) or 0

        # Calculate active users (created in last 30 days as proxy for last_active)
        # TODO: Add last_active column to User model in future migration
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
        active_users = (
            await self.session.scalar(
                select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
            )
            or 0
        )
        inactive_users = total_users - active_users

        # Knowledge base stats
        total_kbs = await self.session.scalar(select(func.count(KnowledgeBase.id))) or 0
        kb_status_counts = await self._count_by_status(
            KnowledgeBase, KnowledgeBase.status
        )

        # Document stats
        total_docs = await self.session.scalar(select(func.count(Document.id))) or 0
        doc_status_counts = await self._count_by_status(Document, Document.status)

        # Storage stats
        total_bytes_result = await self.session.scalar(
            select(func.sum(Document.file_size_bytes))
        )
        total_bytes = int(total_bytes_result) if total_bytes_result else 0
        avg_doc_size = int(total_bytes / total_docs) if total_docs > 0 else 0

        # Activity stats
        searches_24h = await self._count_audit_events("search.query", hours=24)
        searches_7d = await self._count_audit_events("search.query", days=7)
        searches_30d = await self._count_audit_events("search.query", days=30)

        generations_24h = await self._count_audit_events("generation.request", hours=24)
        generations_7d = await self._count_audit_events("generation.request", days=7)
        generations_30d = await self._count_audit_events("generation.request", days=30)

        # Trend data (sparklines)
        search_trends = await self._get_daily_counts("search.query", days=30)
        generation_trends = await self._get_daily_counts("generation.request", days=30)

        return AdminStats(
            users=UserStats(
                total=total_users,
                active=active_users,
                inactive=inactive_users,
            ),
            knowledge_bases=KnowledgeBaseStats(
                total=total_kbs,
                by_status=kb_status_counts,
            ),
            documents=DocumentStats(
                total=total_docs,
                by_status=doc_status_counts,
            ),
            storage=StorageStats(
                total_bytes=total_bytes,
                avg_doc_size_bytes=avg_doc_size,
            ),
            activity=ActivityStats(
                searches=PeriodStats(
                    last_24h=searches_24h,
                    last_7d=searches_7d,
                    last_30d=searches_30d,
                ),
                generations=PeriodStats(
                    last_24h=generations_24h,
                    last_7d=generations_7d,
                    last_30d=generations_30d,
                ),
            ),
            trends=TrendData(
                searches=search_trends,
                generations=generation_trends,
            ),
        )

    async def _count_by_status(
        self, _model: type, status_column: any
    ) -> dict[str, int]:
        """Count records grouped by status.

        Args:
            _model: SQLAlchemy model class (unused, kept for interface compatibility).
            status_column: Status column to group by.

        Returns:
            Dict mapping status values to counts.
        """
        result = await self.session.execute(
            select(status_column, func.count()).group_by(status_column)
        )
        counts = {}
        for status, count in result.all():
            # Handle enum values by using .value attribute if available
            key = status.value if hasattr(status, "value") else str(status)
            counts[key] = count
        return counts

    async def _count_audit_events(
        self, action: str, hours: int | None = None, days: int | None = None
    ) -> int:
        """Count audit events for given action within time period.

        Args:
            action: Audit action to count (e.g., "search.query").
            hours: Count events in last N hours.
            days: Count events in last N days.

        Returns:
            Count of matching audit events.
        """
        query = select(func.count(AuditEvent.id)).where(AuditEvent.action == action)

        if hours:
            since = datetime.now(UTC) - timedelta(hours=hours)
        elif days:
            since = datetime.now(UTC) - timedelta(days=days)
        else:
            # No time filter
            count = await self.session.scalar(query)
            return int(count) if count else 0

        query = query.where(AuditEvent.timestamp >= since)
        count = await self.session.scalar(query)
        return int(count) if count else 0

    async def _get_daily_counts(self, action: str, days: int) -> list[int]:
        """Get daily counts for sparkline visualization.

        Args:
            action: Audit action to count.
            days: Number of days to retrieve.

        Returns:
            List of daily counts (oldest to newest).
        """
        since = datetime.now(UTC) - timedelta(days=days)

        # Query daily counts using date truncation
        # Create a labeled column for the truncated day
        day_column = func.date_trunc("day", AuditEvent.timestamp).label("day")

        query = (
            select(
                day_column,
                func.count(AuditEvent.id).label("count"),
            )
            .where(AuditEvent.action == action)
            .where(AuditEvent.timestamp >= since)
            .group_by(day_column)
            .order_by(day_column)
        )

        result = await self.session.execute(query)
        rows = result.all()

        # Build dict of date -> count
        count_map = {}
        for row in rows:
            # row is a tuple (day, count) or Row object depending on SQLAlchemy version
            if hasattr(row, "day"):
                day_value = row.day
                count_value = row.count
            else:
                # Fallback for tuple-style results
                day_value, count_value = row

            # Extract date from datetime
            date_key = day_value.date() if hasattr(day_value, "date") else day_value

            count_map[date_key] = count_value

        # Fill in missing days with 0
        daily_counts = []
        for i in range(days):
            day = (datetime.now(UTC) - timedelta(days=days - i - 1)).date()
            daily_counts.append(count_map.get(day, 0))

        return daily_counts
