"""Unit tests for DraftService.

Tests business logic, status transitions, and citation validation.
No database or HTTP - pure service layer testing.

Coverage Target: 85%+
Test Count: 12
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.draft import DraftStatus
from app.services.draft_service import DraftService
from tests.factories import create_draft, create_draft_with_citations, create_citation


class TestDraftServiceCreation:
    """Test draft creation logic."""

    @pytest.mark.asyncio
    async def test_create_draft_sets_default_status(self):
        """[P1] Draft creation should set status to 'streaming' by default."""
        # GIVEN: DraftService with mocked repository
        mock_repo = AsyncMock()
        service = DraftService(draft_repository=mock_repo)

        draft_data = create_draft()
        draft_data.pop("status")  # Remove status to test default

        # WHEN: Creating draft without explicit status
        await service.create_draft(draft_data)

        # THEN: Repository called with status='streaming'
        mock_repo.create.assert_called_once()
        call_args = mock_repo.create.call_args[0][0]
        assert call_args["status"] == DraftStatus.STREAMING

    @pytest.mark.asyncio
    async def test_create_draft_calculates_word_count(self):
        """[P2] Draft creation should auto-calculate word count if not provided."""
        # GIVEN: DraftService
        mock_repo = AsyncMock()
        service = DraftService(draft_repository=mock_repo)

        content = "The quick brown fox jumps over the lazy dog"
        draft_data = create_draft(content=content)
        draft_data.pop("word_count")  # Remove to test auto-calculation

        # WHEN: Creating draft without word_count
        await service.create_draft(draft_data)

        # THEN: Word count calculated (9 words)
        call_args = mock_repo.create.call_args[0][0]
        assert call_args["word_count"] == 9

    @pytest.mark.asyncio
    async def test_create_draft_preserves_explicit_word_count(self):
        """[P2] Draft creation should use explicit word_count if provided."""
        # GIVEN: DraftService
        mock_repo = AsyncMock()
        service = DraftService(draft_repository=mock_repo)

        draft_data = create_draft(word_count=500)

        # WHEN: Creating draft with explicit word_count
        await service.create_draft(draft_data)

        # THEN: Explicit word_count preserved
        call_args = mock_repo.create.call_args[0][0]
        assert call_args["word_count"] == 500


class TestDraftStatusTransitions:
    """Test draft status state machine transitions."""

    @pytest.mark.asyncio
    async def test_transition_streaming_to_complete(self):
        """[P0] Draft status can transition from 'streaming' to 'complete'."""
        # GIVEN: Draft with status='streaming'
        mock_repo = AsyncMock()
        service = DraftService(draft_repository=mock_repo)

        draft = create_draft(status=DraftStatus.STREAMING)
        mock_repo.get_by_id.return_value = draft

        # WHEN: Updating status to 'complete'
        await service.update_draft(draft["id"], {"status": DraftStatus.COMPLETE})

        # THEN: Update succeeds
        mock_repo.update.assert_called_once()
        call_args = mock_repo.update.call_args[0]
        assert call_args[1]["status"] == DraftStatus.COMPLETE

    @pytest.mark.asyncio
    async def test_transition_complete_to_editing(self):
        """[P0] Draft status can transition from 'complete' to 'editing'."""
        # GIVEN: Draft with status='complete'
        mock_repo = AsyncMock()
        service = DraftService(draft_repository=mock_repo)

        draft = create_draft(status=DraftStatus.COMPLETE)
        mock_repo.get_by_id.return_value = draft

        # WHEN: Updating content (triggers editing status)
        await service.update_draft(
            draft["id"],
            {"content": "Updated content", "status": DraftStatus.EDITING}
        )

        # THEN: Status transitions to 'editing'
        call_args = mock_repo.update.call_args[0]
        assert call_args[1]["status"] == DraftStatus.EDITING

    @pytest.mark.asyncio
    async def test_transition_editing_to_exported(self):
        """[P1] Draft status can transition from 'editing' to 'exported'."""
        # GIVEN: Draft with status='editing'
        mock_repo = AsyncMock()
        service = DraftService(draft_repository=mock_repo)

        draft = create_draft(status=DraftStatus.EDITING)
        mock_repo.get_by_id.return_value = draft

        # WHEN: Marking as exported
        await service.update_draft(draft["id"], {"status": DraftStatus.EXPORTED})

        # THEN: Status transitions to 'exported'
        call_args = mock_repo.update.call_args[0]
        assert call_args[1]["status"] == DraftStatus.EXPORTED


class TestCitationMarkerValidation:
    """Test citation marker validation logic."""

    @pytest.mark.asyncio
    async def test_validate_citation_markers_match(self):
        """[P0] Validation succeeds when citation markers match citation data."""
        # GIVEN: Draft with 2 citations and matching markers
        draft_data = create_draft_with_citations(citation_count=2)

        # WHEN: Validating citations
        service = DraftService(draft_repository=AsyncMock())
        result = service._validate_citation_markers(
            draft_data["content"],
            draft_data["citations"]
        )

        # THEN: Validation passes
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_detects_orphaned_citations(self):
        """[P1] Validation detects citations without markers in content."""
        # GIVEN: Draft with citation but no marker in content
        content = "OAuth 2.0 is secure"  # No [1] marker
        citations = [create_citation(number=1)]

        # WHEN: Validating citations
        service = DraftService(draft_repository=AsyncMock())
        result = service._validate_citation_markers(content, citations)

        # THEN: Validation fails (orphaned citation)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_detects_missing_citation_data(self):
        """[P1] Validation detects markers without citation data."""
        # GIVEN: Draft with marker but no citation data
        content = "OAuth 2.0 [1] is secure"
        citations = []  # No citation for [1]

        # WHEN: Validating citations
        service = DraftService(draft_repository=AsyncMock())
        result = service._validate_citation_markers(content, citations)

        # THEN: Validation fails (missing citation data)
        assert result is False


class TestDraftRetrieval:
    """Test draft retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_drafts_by_kb_filters_correctly(self):
        """[P1] Service retrieves only drafts for specified knowledge base."""
        # GIVEN: DraftService with mock repository
        mock_repo = AsyncMock()
        service = DraftService(draft_repository=mock_repo)

        kb_id = str(uuid4())
        mock_repo.get_by_kb.return_value = [
            create_draft(kb_id=kb_id),
            create_draft(kb_id=kb_id),
        ]

        # WHEN: Getting drafts for KB
        result = await service.get_drafts_by_kb(kb_id)

        # THEN: Repository called with KB ID filter
        mock_repo.get_by_kb.assert_called_once_with(kb_id)
        assert len(result) == 2
        assert all(draft["kb_id"] == kb_id for draft in result)

    @pytest.mark.asyncio
    async def test_get_draft_by_id_returns_single_draft(self):
        """[P1] Service retrieves draft by ID correctly."""
        # GIVEN: DraftService
        mock_repo = AsyncMock()
        service = DraftService(draft_repository=mock_repo)

        draft_id = str(uuid4())
        expected_draft = create_draft(id=draft_id)
        mock_repo.get_by_id.return_value = expected_draft

        # WHEN: Getting draft by ID
        result = await service.get_draft(draft_id)

        # THEN: Correct draft returned
        mock_repo.get_by_id.assert_called_once_with(draft_id)
        assert result["id"] == draft_id


class TestDraftDeletion:
    """Test draft deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_draft_calls_repository(self):
        """[P2] Draft deletion delegates to repository correctly."""
        # GIVEN: DraftService
        mock_repo = AsyncMock()
        service = DraftService(draft_repository=mock_repo)

        draft_id = str(uuid4())

        # WHEN: Deleting draft
        await service.delete_draft(draft_id)

        # THEN: Repository delete called
        mock_repo.delete.assert_called_once_with(draft_id)
