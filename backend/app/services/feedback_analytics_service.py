"""Feedback Analytics Service - Story 7-23.

Provides analytics aggregation for generation feedback data stored in audit events.
Feedback is stored via audit_service.log_feedback() with action="generation.feedback".
"""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.models.user import User

logger = structlog.get_logger()


class FeedbackAnalyticsService:
    """Service for aggregating and analyzing generation feedback data.

    Queries audit.events table where action='generation.feedback' to provide:
    - Feedback distribution by type (AC-7.23.2)
    - Feedback trend over time (AC-7.23.3)
    - Recent feedback items with user context (AC-7.23.4)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_feedback_by_type(self) -> list[dict]:
        """Get feedback count grouped by feedback_type (AC-7.23.2).

        Queries audit events with action='generation.feedback' and aggregates
        by the feedback_type field in the JSONB details column.

        Returns:
            List of dicts with 'type' and 'count' keys.
            Example: [{"type": "not_relevant", "count": 42}, ...]
        """
        # Query aggregation by feedback_type from JSONB details
        query = (
            select(
                AuditEvent.details["feedback_type"].astext.label("feedback_type"),
                func.count(AuditEvent.id).label("count"),
            )
            .where(AuditEvent.action == "generation.feedback")
            .group_by(AuditEvent.details["feedback_type"].astext)
            .order_by(func.count(AuditEvent.id).desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {"type": row.feedback_type or "unknown", "count": row.count} for row in rows
        ]

    async def get_feedback_trend(self, days: int = 30) -> list[dict]:
        """Get daily feedback counts for the last N days (AC-7.23.3).

        Args:
            days: Number of days to include (default 30)

        Returns:
            List of dicts with 'date' (ISO string) and 'count' keys.
            Includes all days in range, even those with 0 feedback.
            Example: [{"date": "2025-12-01", "count": 5}, ...]
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        # Query daily counts
        query = (
            select(
                func.date(AuditEvent.timestamp).label("date"),
                func.count(AuditEvent.id).label("count"),
            )
            .where(AuditEvent.action == "generation.feedback")
            .where(AuditEvent.timestamp >= cutoff_date)
            .group_by(func.date(AuditEvent.timestamp))
            .order_by(func.date(AuditEvent.timestamp))
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Build a map of date -> count
        date_counts = {str(row.date): row.count for row in rows}

        # Fill in all days in range (including zeros)
        trend_data = []
        current_date = cutoff_date.date()
        end_date = datetime.now(UTC).date()

        while current_date <= end_date:
            date_str = str(current_date)
            trend_data.append(
                {
                    "date": date_str,
                    "count": date_counts.get(date_str, 0),
                }
            )
            current_date += timedelta(days=1)

        return trend_data

    async def get_recent_feedback(self, limit: int = 20) -> list[dict]:
        """Get most recent feedback items with user context (AC-7.23.4).

        Joins with users table to include email for display.

        Args:
            limit: Maximum items to return (default 20)

        Returns:
            List of feedback items with:
            - id: Event UUID
            - timestamp: ISO datetime string
            - user_id: User UUID (if available)
            - user_email: User email (joined)
            - draft_id: Resource ID (draft UUID)
            - feedback_type: Type of feedback
            - feedback_comments: User comments (truncated)
        """
        # Query recent feedback events with user join
        query = (
            select(
                AuditEvent.id,
                AuditEvent.timestamp,
                AuditEvent.user_id,
                AuditEvent.resource_id.label("draft_id"),
                AuditEvent.details,
                User.email.label("user_email"),
            )
            .outerjoin(User, AuditEvent.user_id == User.id)
            .where(AuditEvent.action == "generation.feedback")
            .order_by(AuditEvent.timestamp.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        items = []
        for row in rows:
            details = row.details or {}
            items.append(
                {
                    "id": str(row.id),
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "user_id": str(row.user_id) if row.user_id else None,
                    "user_email": row.user_email,
                    "draft_id": str(row.draft_id) if row.draft_id else None,
                    "feedback_type": details.get("feedback_type"),
                    "feedback_comments": details.get("feedback_comments"),
                    "related_request_id": details.get("related_request_id"),
                }
            )

        return items

    async def get_total_feedback_count(self) -> int:
        """Get total count of all feedback events.

        Returns:
            Total number of feedback events in the system.
        """
        query = select(func.count(AuditEvent.id)).where(
            AuditEvent.action == "generation.feedback"
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_analytics(self) -> dict:
        """Get comprehensive feedback analytics (AC-7.23.6).

        Aggregates all feedback analytics into a single response:
        - by_type: Distribution by feedback type
        - by_day: 30-day trend data
        - recent: 20 most recent items
        - total_count: Total feedback count

        Returns:
            Dict matching FeedbackAnalyticsResponse schema.
        """
        # Execute all queries concurrently would be better, but for simplicity
        # we run them sequentially here
        by_type = await self.get_feedback_by_type()
        by_day = await self.get_feedback_trend(days=30)
        recent = await self.get_recent_feedback(limit=20)
        total_count = await self.get_total_feedback_count()

        return {
            "by_type": by_type,
            "by_day": by_day,
            "recent": recent,
            "total_count": total_count,
        }
