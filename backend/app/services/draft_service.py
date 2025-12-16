"""Draft service for draft CRUD operations."""

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.draft import Draft, DraftStatus

logger = structlog.get_logger(__name__)


class DraftService:
    """Service for draft operations.

    Handles business logic for creating, retrieving, updating, and deleting drafts.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize DraftService with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self.session = session

    async def create_draft(
        self,
        kb_id: UUID,
        user_id: UUID,
        title: str,
        template_type: str | None = None,
        content: str = "",
        citations: list[dict] | None = None,
        status: DraftStatus = DraftStatus.STREAMING,
        word_count: int = 0,
    ) -> Draft:
        """Create a new draft.

        Args:
            kb_id: Knowledge Base UUID
            user_id: User UUID
            title: Draft title
            template_type: Template used (rfp_response, checklist, etc.)
            content: Draft content (markdown with [n] markers)
            citations: List of citation dicts
            status: Initial status (default: streaming)
            word_count: Word count (default: 0)

        Returns:
            Created Draft record
        """
        draft = Draft(
            kb_id=kb_id,
            user_id=user_id,
            title=title,
            template_type=template_type,
            content=content,
            citations=citations or [],
            status=status,
            word_count=word_count,
        )

        self.session.add(draft)
        await self.session.commit()
        await self.session.refresh(draft)

        logger.info(
            "draft_created",
            draft_id=str(draft.id),
            kb_id=str(kb_id),
            user_id=str(user_id),
            status=status.value,
        )

        return draft

    async def get_draft(self, draft_id: UUID) -> Draft | None:
        """Get a single draft by ID.

        Args:
            draft_id: Draft UUID

        Returns:
            Draft record or None if not found
        """
        result = await self.session.execute(select(Draft).where(Draft.id == draft_id))
        return result.scalars().first()

    async def list_drafts(
        self,
        kb_id: UUID,
        status: DraftStatus | None = None,
    ) -> list[Draft]:
        """List all drafts for a Knowledge Base.

        Args:
            kb_id: Knowledge Base UUID
            status: Optional status filter

        Returns:
            List of Draft records
        """
        query = select(Draft).where(Draft.kb_id == kb_id)

        if status:
            query = query.where(Draft.status == status)

        query = query.order_by(Draft.updated_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_draft(
        self,
        draft_id: UUID,
        content: str,
        citations: list[dict],
        status: DraftStatus,
        word_count: int,
    ) -> Draft:
        """Update draft content, citations, and status.

        Used for auto-save, manual save, and status transitions.

        Args:
            draft_id: Draft UUID
            content: Updated content
            citations: Updated citations list
            status: New status
            word_count: Updated word count

        Returns:
            Updated Draft record

        Raises:
            ValueError: If draft not found
        """
        draft = await self.get_draft(draft_id)

        if not draft:
            raise ValueError(f"Draft {draft_id} not found")

        # Update fields
        draft.content = content
        draft.citations = citations
        draft.status = status
        draft.word_count = word_count

        await self.session.commit()
        await self.session.refresh(draft)

        logger.info(
            "draft_updated",
            draft_id=str(draft_id),
            status=status.value,
            word_count=word_count,
            citations_count=len(citations),
        )

        return draft

    async def delete_draft(self, draft_id: UUID) -> None:
        """Delete a draft.

        Args:
            draft_id: Draft UUID

        Raises:
            ValueError: If draft not found
        """
        draft = await self.get_draft(draft_id)

        if not draft:
            raise ValueError(f"Draft {draft_id} not found")

        await self.session.delete(draft)
        await self.session.commit()

        logger.info(
            "draft_deleted",
            draft_id=str(draft_id),
            kb_id=str(draft.kb_id),
        )

    async def transition_status(
        self,
        draft_id: UUID,
        new_status: DraftStatus,
    ) -> Draft:
        """Transition draft to a new status.

        Valid transitions:
        - streaming → partial (on cancel)
        - streaming → complete (on finish)
        - complete → editing (on first edit)
        - editing → editing (on save)
        - editing → exported (on export)

        Args:
            draft_id: Draft UUID
            new_status: New status

        Returns:
            Updated Draft record

        Raises:
            ValueError: If draft not found or invalid transition
        """
        draft = await self.get_draft(draft_id)

        if not draft:
            raise ValueError(f"Draft {draft_id} not found")

        # Validate transition
        current = draft.status
        valid_transitions = {
            DraftStatus.STREAMING: {DraftStatus.PARTIAL, DraftStatus.COMPLETE},
            DraftStatus.PARTIAL: set(),  # Terminal state
            DraftStatus.COMPLETE: {DraftStatus.EDITING},
            DraftStatus.EDITING: {DraftStatus.EDITING, DraftStatus.EXPORTED},
            DraftStatus.EXPORTED: set(),  # Terminal state
        }

        if new_status not in valid_transitions.get(current, set()):
            raise ValueError(
                f"Invalid transition from {current.value} to {new_status.value}"
            )

        draft.status = new_status
        await self.session.commit()
        await self.session.refresh(draft)

        logger.info(
            "draft_status_transition",
            draft_id=str(draft_id),
            from_status=current.value,
            to_status=new_status.value,
        )

        return draft
