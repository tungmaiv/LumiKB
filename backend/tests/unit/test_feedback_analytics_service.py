"""Tests for FeedbackAnalyticsService - Story 7-23."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.feedback_analytics_service import FeedbackAnalyticsService


class TestFeedbackAnalyticsService:
    """Test cases for FeedbackAnalyticsService."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = MagicMock(spec=AsyncSession)
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance with mocked session."""
        return FeedbackAnalyticsService(mock_session)

    @pytest.mark.asyncio
    async def test_get_feedback_by_type_returns_aggregated_data(
        self, service, mock_session
    ):
        """Test get_feedback_by_type returns aggregated feedback counts (AC-7.23.2)."""
        # Arrange - mock query results
        mock_rows = [
            MagicMock(feedback_type="not_relevant", count=10),
            MagicMock(feedback_type="inaccurate", count=5),
            MagicMock(feedback_type="incomplete", count=3),
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        # Act
        result = await service.get_feedback_by_type()

        # Assert
        assert len(result) == 3
        assert result[0] == {"type": "not_relevant", "count": 10}
        assert result[1] == {"type": "inaccurate", "count": 5}
        assert result[2] == {"type": "incomplete", "count": 3}

    @pytest.mark.asyncio
    async def test_get_feedback_by_type_handles_null_type(self, service, mock_session):
        """Test get_feedback_by_type handles null feedback types."""
        # Arrange
        mock_rows = [
            MagicMock(feedback_type=None, count=2),
            MagicMock(feedback_type="not_relevant", count=5),
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        # Act
        result = await service.get_feedback_by_type()

        # Assert
        assert result[0] == {"type": "unknown", "count": 2}

    @pytest.mark.asyncio
    async def test_get_feedback_trend_returns_daily_counts(self, service, mock_session):
        """Test get_feedback_trend returns daily feedback counts (AC-7.23.3)."""
        # Arrange
        today = datetime.now(UTC).date()
        yesterday = today - timedelta(days=1)
        mock_rows = [
            MagicMock(date=yesterday, count=3),
            MagicMock(date=today, count=5),
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        # Act
        result = await service.get_feedback_trend(days=30)

        # Assert - should include all days in range with zeros for missing days
        assert len(result) == 31  # 30 days + today
        # Check that the trend data includes the mocked dates with their counts
        date_counts = {item["date"]: item["count"] for item in result}
        assert date_counts.get(str(yesterday)) == 3
        assert date_counts.get(str(today)) == 5

    @pytest.mark.asyncio
    async def test_get_feedback_trend_fills_missing_days_with_zero(
        self, service, mock_session
    ):
        """Test get_feedback_trend fills in missing days with zero counts."""
        # Arrange - only one day has data
        today = datetime.now(UTC).date()
        mock_rows = [MagicMock(date=today, count=5)]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        # Act
        result = await service.get_feedback_trend(days=7)

        # Assert - should have 8 days (7 + today)
        assert len(result) == 8
        # Only today should have count > 0
        non_zero_days = [item for item in result if item["count"] > 0]
        assert len(non_zero_days) == 1
        assert non_zero_days[0]["count"] == 5

    @pytest.mark.asyncio
    async def test_get_recent_feedback_returns_formatted_items(
        self, service, mock_session
    ):
        """Test get_recent_feedback returns properly formatted items (AC-7.23.4)."""
        # Arrange
        user_id = uuid4()
        draft_id = uuid4()
        event_id = uuid4()
        timestamp = datetime.now(UTC)

        mock_rows = [
            MagicMock(
                id=event_id,
                timestamp=timestamp,
                user_id=user_id,
                draft_id=draft_id,
                user_email="test@example.com",
                details={
                    "feedback_type": "not_relevant",
                    "feedback_comments": "This was not helpful",
                    "related_request_id": "req-123",
                },
            )
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        # Act
        result = await service.get_recent_feedback(limit=20)

        # Assert
        assert len(result) == 1
        item = result[0]
        assert item["id"] == str(event_id)
        assert item["user_id"] == str(user_id)
        assert item["user_email"] == "test@example.com"
        assert item["draft_id"] == str(draft_id)
        assert item["feedback_type"] == "not_relevant"
        assert item["feedback_comments"] == "This was not helpful"
        assert item["related_request_id"] == "req-123"

    @pytest.mark.asyncio
    async def test_get_recent_feedback_handles_missing_details(
        self, service, mock_session
    ):
        """Test get_recent_feedback handles items with missing details."""
        # Arrange
        mock_rows = [
            MagicMock(
                id=uuid4(),
                timestamp=datetime.now(UTC),
                user_id=None,
                draft_id=None,
                user_email=None,
                details=None,
            )
        ]
        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        # Act
        result = await service.get_recent_feedback(limit=20)

        # Assert
        assert len(result) == 1
        item = result[0]
        assert item["user_id"] is None
        assert item["user_email"] is None
        assert item["draft_id"] is None
        assert item["feedback_type"] is None
        assert item["feedback_comments"] is None

    @pytest.mark.asyncio
    async def test_get_total_feedback_count_returns_integer(
        self, service, mock_session
    ):
        """Test get_total_feedback_count returns total count."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        mock_session.execute.return_value = mock_result

        # Act
        result = await service.get_total_feedback_count()

        # Assert
        assert result == 42

    @pytest.mark.asyncio
    async def test_get_total_feedback_count_returns_zero_for_null(
        self, service, mock_session
    ):
        """Test get_total_feedback_count returns 0 when result is null."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await service.get_total_feedback_count()

        # Assert
        assert result == 0

    @pytest.mark.asyncio
    async def test_get_analytics_aggregates_all_data(self, service, mock_session):
        """Test get_analytics returns comprehensive analytics (AC-7.23.6)."""
        # Arrange - we need to mock multiple execute calls
        by_type_result = MagicMock()
        by_type_result.all.return_value = [
            MagicMock(feedback_type="not_relevant", count=10)
        ]

        trend_result = MagicMock()
        trend_result.all.return_value = [
            MagicMock(date=datetime.now(UTC).date(), count=5)
        ]

        recent_result = MagicMock()
        recent_result.all.return_value = []

        count_result = MagicMock()
        count_result.scalar.return_value = 10

        # Configure mock to return different results for each call
        mock_session.execute.side_effect = [
            by_type_result,
            trend_result,
            recent_result,
            count_result,
        ]

        # Act
        result = await service.get_analytics()

        # Assert - check structure
        assert "by_type" in result
        assert "by_day" in result
        assert "recent" in result
        assert "total_count" in result
        assert result["total_count"] == 10
        assert len(result["by_type"]) == 1
        assert result["by_type"][0]["type"] == "not_relevant"
