"""Unit tests for DraftService.

Tests business logic, status transitions, and draft operations.
Uses AsyncSession mock - no database calls.

Coverage Target: 85%+
Test Count: 12
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.draft import Draft, DraftStatus
from app.services.draft_service import DraftService


# Fixtures
@pytest.fixture
def mock_session():
    """Create mock AsyncSession with query chain."""
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def sample_draft():
    """Create a sample Draft model instance."""
    return Draft(
        id=uuid4(),
        kb_id=uuid4(),
        user_id=uuid4(),
        title="Test Draft",
        content="Test content with citation [1]",
        citations=[{"number": 1, "source": "doc.pdf"}],
        status=DraftStatus.STREAMING,
        word_count=5,
    )


class TestDraftServiceCreation:
    """Test draft creation logic."""

    @pytest.mark.asyncio
    async def test_create_draft_sets_default_status(self, mock_session):
        """[P1] Draft creation should set status to 'streaming' by default."""
        service = DraftService(session=mock_session)

        # Capture added draft via side_effect
        added_draft = None

        def capture_add(draft):
            nonlocal added_draft
            added_draft = draft

        mock_session.add.side_effect = capture_add

        await service.create_draft(
            kb_id=uuid4(),
            user_id=uuid4(),
            title="Test Draft",
        )

        assert added_draft is not None
        assert added_draft.status == DraftStatus.STREAMING
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_draft_with_content(self, mock_session):
        """[P2] Draft creation stores provided content."""
        service = DraftService(session=mock_session)

        added_draft = None

        def capture_add(draft):
            nonlocal added_draft
            added_draft = draft

        mock_session.add.side_effect = capture_add

        content = "The quick brown fox"
        await service.create_draft(
            kb_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            content=content,
        )

        assert added_draft.content == content

    @pytest.mark.asyncio
    async def test_create_draft_with_word_count(self, mock_session):
        """[P2] Draft creation stores explicit word_count."""
        service = DraftService(session=mock_session)

        added_draft = None

        def capture_add(draft):
            nonlocal added_draft
            added_draft = draft

        mock_session.add.side_effect = capture_add

        await service.create_draft(
            kb_id=uuid4(),
            user_id=uuid4(),
            title="Test",
            word_count=500,
        )

        assert added_draft.word_count == 500


class TestDraftStatusTransitions:
    """Test draft status state machine transitions."""

    @pytest.mark.asyncio
    async def test_transition_streaming_to_complete(self, mock_session, sample_draft):
        """[P0] Draft status can transition from 'streaming' to 'complete'."""
        sample_draft.status = DraftStatus.STREAMING

        result = MagicMock()
        result.scalars.return_value.first.return_value = sample_draft
        mock_session.execute = AsyncMock(return_value=result)

        service = DraftService(session=mock_session)
        updated = await service.transition_status(sample_draft.id, DraftStatus.COMPLETE)

        assert updated.status == DraftStatus.COMPLETE
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_transition_complete_to_editing(self, mock_session, sample_draft):
        """[P0] Draft status can transition from 'complete' to 'editing'."""
        sample_draft.status = DraftStatus.COMPLETE

        result = MagicMock()
        result.scalars.return_value.first.return_value = sample_draft
        mock_session.execute = AsyncMock(return_value=result)

        service = DraftService(session=mock_session)
        updated = await service.transition_status(sample_draft.id, DraftStatus.EDITING)

        assert updated.status == DraftStatus.EDITING

    @pytest.mark.asyncio
    async def test_transition_editing_to_exported(self, mock_session, sample_draft):
        """[P1] Draft status can transition from 'editing' to 'exported'."""
        sample_draft.status = DraftStatus.EDITING

        result = MagicMock()
        result.scalars.return_value.first.return_value = sample_draft
        mock_session.execute = AsyncMock(return_value=result)

        service = DraftService(session=mock_session)
        updated = await service.transition_status(sample_draft.id, DraftStatus.EXPORTED)

        assert updated.status == DraftStatus.EXPORTED

    @pytest.mark.asyncio
    async def test_invalid_transition_raises_error(self, mock_session, sample_draft):
        """[P0] Invalid status transition raises ValueError."""
        sample_draft.status = DraftStatus.EXPORTED  # Terminal state

        result = MagicMock()
        result.scalars.return_value.first.return_value = sample_draft
        mock_session.execute = AsyncMock(return_value=result)

        service = DraftService(session=mock_session)

        with pytest.raises(ValueError, match="Invalid transition"):
            await service.transition_status(sample_draft.id, DraftStatus.STREAMING)


class TestDraftRetrieval:
    """Test draft retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_draft_returns_draft(self, mock_session, sample_draft):
        """[P1] Service retrieves draft by ID correctly."""
        result = MagicMock()
        result.scalars.return_value.first.return_value = sample_draft
        mock_session.execute = AsyncMock(return_value=result)

        service = DraftService(session=mock_session)
        draft = await service.get_draft(sample_draft.id)

        assert draft == sample_draft
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_draft_returns_none_if_not_found(self, mock_session):
        """[P1] Service returns None if draft not found."""
        result = MagicMock()
        result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=result)

        service = DraftService(session=mock_session)
        draft = await service.get_draft(uuid4())

        assert draft is None

    @pytest.mark.asyncio
    async def test_list_drafts_by_kb(self, mock_session, sample_draft):
        """[P1] Service lists drafts filtered by KB."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_draft]
        mock_session.execute = AsyncMock(return_value=result)

        service = DraftService(session=mock_session)
        drafts = await service.list_drafts(sample_draft.kb_id)

        assert len(drafts) == 1
        assert drafts[0] == sample_draft


class TestDraftDeletion:
    """Test draft deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_draft_removes_draft(self, mock_session, sample_draft):
        """[P2] Draft deletion removes from database."""
        result = MagicMock()
        result.scalars.return_value.first.return_value = sample_draft
        mock_session.execute = AsyncMock(return_value=result)

        service = DraftService(session=mock_session)
        await service.delete_draft(sample_draft.id)

        mock_session.delete.assert_called_once_with(sample_draft)
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_delete_draft_raises_if_not_found(self, mock_session):
        """[P2] Deletion raises ValueError if draft not found."""
        result = MagicMock()
        result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=result)

        service = DraftService(session=mock_session)

        with pytest.raises(ValueError, match="not found"):
            await service.delete_draft(uuid4())
