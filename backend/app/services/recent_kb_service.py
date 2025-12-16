"""Recent KB service for retrieving user's recently accessed knowledge bases.

Provides efficient queries for recent KB access with 100ms SLA target.
Uses indexed query on kb_access_log table.
"""

from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.kb_access_log import KBAccessLog
from app.models.knowledge_base import KnowledgeBase
from app.schemas.recent_kb import RecentKB

logger = structlog.get_logger()

# Default limit for recent KBs
DEFAULT_RECENT_KB_LIMIT = 5


class RecentKBService:
    """Service for retrieving user's recently accessed knowledge bases.

    Uses the kb_access_log table to track access patterns.
    Optimized for 100ms SLA with indexed queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def get_recent_kbs(
        self, user_id: UUID, limit: int = DEFAULT_RECENT_KB_LIMIT
    ) -> list[RecentKB]:
        """Get user's recently accessed knowledge bases.

        Query uses indexed columns (user_id, kb_id, accessed_at DESC)
        for optimal performance. Target SLA: 100ms.

        Args:
            user_id: The user's UUID.
            limit: Maximum number of recent KBs to return (default 5).

        Returns:
            List of RecentKB objects sorted by last_accessed DESC.
        """
        # Subquery to get most recent access per KB for this user
        recent_access_subquery = (
            select(
                KBAccessLog.kb_id,
                func.max(KBAccessLog.accessed_at).label("last_accessed"),
            )
            .where(KBAccessLog.user_id == user_id)
            .group_by(KBAccessLog.kb_id)
            .subquery()
        )

        # Subquery to get document count per KB
        doc_count_subquery = (
            select(
                Document.kb_id,
                func.count(Document.id).label("doc_count"),
            )
            .group_by(Document.kb_id)
            .subquery()
        )

        # Main query: join with KBs and get document counts
        query = (
            select(
                KnowledgeBase.id,
                KnowledgeBase.name,
                KnowledgeBase.description,
                recent_access_subquery.c.last_accessed,
                func.coalesce(doc_count_subquery.c.doc_count, 0).label(
                    "document_count"
                ),
            )
            .join(
                recent_access_subquery,
                KnowledgeBase.id == recent_access_subquery.c.kb_id,
            )
            .outerjoin(
                doc_count_subquery,
                KnowledgeBase.id == doc_count_subquery.c.kb_id,
            )
            .where(KnowledgeBase.status == "active")
            .order_by(recent_access_subquery.c.last_accessed.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        rows = result.all()

        recent_kbs = []
        for row in rows:
            recent_kbs.append(
                RecentKB(
                    kb_id=row.id,
                    kb_name=row.name,
                    description=row.description or "",
                    last_accessed=row.last_accessed,
                    document_count=row.document_count,
                )
            )

        logger.info(
            "recent_kbs_retrieved",
            user_id=str(user_id),
            count=len(recent_kbs),
        )

        return recent_kbs
