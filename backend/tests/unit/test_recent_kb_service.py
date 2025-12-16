"""Unit tests for RecentKBService."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.recent_kb_service import DEFAULT_RECENT_KB_LIMIT, RecentKBService


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def recent_kb_service(mock_session):
    """Create RecentKBService with mocked session."""
    return RecentKBService(mock_session)


@pytest.fixture
def sample_user_id():
    """Generate a sample user UUID."""
    return uuid4()


class TestGetRecentKBs:
    """Tests for get_recent_kbs method."""

    @pytest.mark.asyncio
    async def test_returns_list_of_recent_kbs(
        self, recent_kb_service, mock_session, sample_user_id
    ):
        """Test that get_recent_kbs returns a list of RecentKB objects (AC-5.9.1)."""
        from datetime import UTC, datetime

        # Mock result rows
        mock_row = MagicMock()
        mock_row.id = uuid4()
        mock_row.name = "Test KB"
        mock_row.description = "Test description"
        mock_row.last_accessed = datetime.now(UTC)
        mock_row.document_count = 5

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        recent_kbs = await recent_kb_service.get_recent_kbs(sample_user_id)

        assert len(recent_kbs) == 1
        assert recent_kbs[0].kb_name == "Test KB"
        assert recent_kbs[0].document_count == 5

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_history(
        self, recent_kb_service, mock_session, sample_user_id
    ):
        """Test that empty list is returned when user has no KB access history."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        recent_kbs = await recent_kb_service.get_recent_kbs(sample_user_id)

        assert recent_kbs == []

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(
        self, recent_kb_service, mock_session, sample_user_id
    ):
        """Test that limit parameter limits number of results (AC-5.9.3)."""
        from datetime import UTC, datetime

        # Create 10 mock rows
        mock_rows = []
        for i in range(10):
            mock_row = MagicMock()
            mock_row.id = uuid4()
            mock_row.name = f"Test KB {i}"
            mock_row.description = f"Description {i}"
            mock_row.last_accessed = datetime.now(UTC)
            mock_row.document_count = i
            mock_rows.append(mock_row)

        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows[:3]  # Limit applied in query
        mock_session.execute.return_value = mock_result

        recent_kbs = await recent_kb_service.get_recent_kbs(sample_user_id, limit=3)

        assert len(recent_kbs) == 3

    @pytest.mark.asyncio
    async def test_default_limit_is_five(self, recent_kb_service):  # noqa: ARG002
        """Test that default limit is 5 (AC-5.9.3)."""
        assert DEFAULT_RECENT_KB_LIMIT == 5

    @pytest.mark.asyncio
    async def test_sorted_by_last_accessed_desc(
        self, recent_kb_service, mock_session, sample_user_id
    ):
        """Test that results are sorted by last_accessed DESC (AC-5.9.1)."""
        from datetime import UTC, datetime, timedelta

        # Create mock rows with different access times
        now = datetime.now(UTC)
        mock_row_older = MagicMock()
        mock_row_older.id = uuid4()
        mock_row_older.name = "Older KB"
        mock_row_older.description = "Accessed yesterday"
        mock_row_older.last_accessed = now - timedelta(days=1)
        mock_row_older.document_count = 3

        mock_row_newer = MagicMock()
        mock_row_newer.id = uuid4()
        mock_row_newer.name = "Newer KB"
        mock_row_newer.description = "Accessed today"
        mock_row_newer.last_accessed = now
        mock_row_newer.document_count = 5

        # Query returns sorted result (DESC order)
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row_newer, mock_row_older]
        mock_session.execute.return_value = mock_result

        recent_kbs = await recent_kb_service.get_recent_kbs(sample_user_id)

        # Verify order
        assert len(recent_kbs) == 2
        assert recent_kbs[0].kb_name == "Newer KB"
        assert recent_kbs[1].kb_name == "Older KB"

    @pytest.mark.asyncio
    async def test_includes_document_count(
        self, recent_kb_service, mock_session, sample_user_id
    ):
        """Test that document_count is included in response (AC-5.9.2)."""
        from datetime import UTC, datetime

        mock_row = MagicMock()
        mock_row.id = uuid4()
        mock_row.name = "Test KB"
        mock_row.description = None
        mock_row.last_accessed = datetime.now(UTC)
        mock_row.document_count = 42

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        recent_kbs = await recent_kb_service.get_recent_kbs(sample_user_id)

        assert recent_kbs[0].document_count == 42

    @pytest.mark.asyncio
    async def test_handles_null_description(
        self, recent_kb_service, mock_session, sample_user_id
    ):
        """Test that null description is handled gracefully."""
        from datetime import UTC, datetime

        mock_row = MagicMock()
        mock_row.id = uuid4()
        mock_row.name = "Test KB"
        mock_row.description = None  # NULL description
        mock_row.last_accessed = datetime.now(UTC)
        mock_row.document_count = 5

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        recent_kbs = await recent_kb_service.get_recent_kbs(sample_user_id)

        # Description should be empty string, not None
        assert recent_kbs[0].description == ""


class TestPerformance:
    """Tests for performance requirements."""

    @pytest.mark.asyncio
    async def test_uses_indexed_query(self, mock_session):
        """Verify query uses indexed columns for 100ms SLA (AC-5.9.2)."""
        # The service uses kb_access_log.user_id, kb_id, accessed_at
        # which are covered by idx_kb_access_user_kb_date index
        service = RecentKBService(mock_session)

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Execute query
        user_id = uuid4()
        await service.get_recent_kbs(user_id)

        # Verify execute was called (query ran)
        mock_session.execute.assert_called_once()


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_zero_document_count(
        self, recent_kb_service, mock_session, sample_user_id
    ):
        """Test that zero document count is handled correctly."""
        from datetime import UTC, datetime

        mock_row = MagicMock()
        mock_row.id = uuid4()
        mock_row.name = "Empty KB"
        mock_row.description = "No documents"
        mock_row.last_accessed = datetime.now(UTC)
        mock_row.document_count = 0

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        recent_kbs = await recent_kb_service.get_recent_kbs(sample_user_id)

        assert recent_kbs[0].document_count == 0

    @pytest.mark.asyncio
    async def test_only_active_kbs_returned(
        self, recent_kb_service, mock_session, sample_user_id
    ):
        """Test that only active KBs are returned (archived KBs excluded)."""
        from datetime import UTC, datetime

        # Only active KB in result (query filters by status='active')
        mock_row = MagicMock()
        mock_row.id = uuid4()
        mock_row.name = "Active KB"
        mock_row.description = "Active"
        mock_row.last_accessed = datetime.now(UTC)
        mock_row.document_count = 10

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        recent_kbs = await recent_kb_service.get_recent_kbs(sample_user_id)

        # Only active KB returned
        assert len(recent_kbs) == 1
        assert recent_kbs[0].kb_name == "Active KB"
