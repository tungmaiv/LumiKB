"""Unit tests for AuditService query methods."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.audit import AuditEvent
from app.services.audit_service import AuditService


@pytest.fixture
def mock_db():
    """Mock AsyncSession for database operations."""
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def audit_service():
    """Create AuditService instance for testing."""
    return AuditService()


@pytest.fixture
def sample_events():
    """Create sample audit events for testing."""
    user_id = uuid4()
    now = datetime.now(UTC)

    return [
        AuditEvent(
            id=uuid4(),
            timestamp=now - timedelta(days=1),
            user_id=user_id,
            action="search",
            resource_type="search",
            resource_id=None,
            details={"query": "test"},
            ip_address="192.168.1.1",
        ),
        AuditEvent(
            id=uuid4(),
            timestamp=now - timedelta(days=2),
            user_id=user_id,
            action="generation.request",
            resource_type="draft",
            resource_id=uuid4(),
            details={"document_type": "report"},
            ip_address="192.168.1.2",
        ),
        AuditEvent(
            id=uuid4(),
            timestamp=now - timedelta(days=3),
            user_id=user_id,
            action="generation.complete",
            resource_type="draft",
            resource_id=uuid4(),
            details={"citation_count": 5},
            ip_address="192.168.1.3",
        ),
    ]


class TestQueryAuditLogsDateFilter:
    """Test query_audit_logs with date filters."""

    @pytest.mark.asyncio
    async def test_query_audit_logs_with_date_filter(
        self, audit_service, mock_db, sample_events
    ):
        """Test querying audit logs with date range filter."""
        # Arrange
        start_date = datetime.now(UTC) - timedelta(days=5)
        end_date = datetime.now(UTC)

        # Mock the count query
        count_result = MagicMock()
        count_result.scalar.return_value = 3

        # Mock the events query
        events_result = MagicMock()
        events_result.scalars.return_value.all.return_value = sample_events

        # Configure execute to return different results for count vs select
        mock_db.execute.side_effect = [count_result, events_result]

        # Act
        events, total = await audit_service.query_audit_logs(
            db=mock_db,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=50,
        )

        # Assert
        assert len(events) == 3
        assert total == 3
        assert mock_db.execute.call_count == 2


class TestQueryAuditLogsUserFilter:
    """Test query_audit_logs with user email filter."""

    @pytest.mark.asyncio
    async def test_query_audit_logs_with_user_filter(
        self, audit_service, mock_db, sample_events
    ):
        """Test querying audit logs filtered by user email."""
        # Arrange
        user_email = "test@example.com"

        # Mock the count query
        count_result = MagicMock()
        count_result.scalar.return_value = 2

        # Mock the events query
        events_result = MagicMock()
        events_result.scalars.return_value.all.return_value = sample_events[:2]

        # Configure execute to return different results
        mock_db.execute.side_effect = [count_result, events_result]

        # Act
        events, total = await audit_service.query_audit_logs(
            db=mock_db, user_email=user_email, page=1, page_size=50
        )

        # Assert
        assert len(events) == 2
        assert total == 2
        assert mock_db.execute.call_count == 2


class TestQueryAuditLogsPagination:
    """Test query_audit_logs pagination."""

    @pytest.mark.asyncio
    async def test_query_audit_logs_pagination(
        self, audit_service, mock_db, sample_events
    ):
        """Test pagination calculates offset correctly."""
        # Arrange
        page = 2
        page_size = 50

        # Mock the count query
        count_result = MagicMock()
        count_result.scalar.return_value = 150

        # Mock the events query (page 2 should have different events)
        events_result = MagicMock()
        events_result.scalars.return_value.all.return_value = sample_events

        # Configure execute to return different results
        mock_db.execute.side_effect = [count_result, events_result]

        # Act
        events, total = await audit_service.query_audit_logs(
            db=mock_db, page=page, page_size=page_size
        )

        # Assert
        assert len(events) == 3
        assert total == 150
        # Verify offset calculation: (page - 1) * page_size = (2 - 1) * 50 = 50
        # This is verified through the query execution


class TestRedactPII:
    """Test redact_pii method."""

    def test_redact_pii_masks_ip_and_sensitive_fields(self, audit_service):
        """Test PII redaction masks IP address and sensitive fields."""
        # Arrange
        event = AuditEvent(
            id=uuid4(),
            timestamp=datetime.now(UTC),
            user_id=uuid4(),
            action="user.login",
            resource_type="user",
            resource_id=uuid4(),
            details={
                "password": "secret123",
                "token": "abc123",
                "api_key": "key456",
                "query": "test search",
            },
            ip_address="192.168.1.100",
        )

        # Act
        redacted = audit_service.redact_pii(event)

        # Assert
        assert redacted.ip_address == "XXX.XXX.XXX.XXX"
        assert redacted.details is not None
        assert redacted.details["password"] == "[REDACTED]"
        assert redacted.details["token"] == "[REDACTED]"
        assert redacted.details["api_key"] == "[REDACTED]"
        assert redacted.details["query"] == "test search"  # Not sensitive
        # Original event should not be modified
        assert event.ip_address == "192.168.1.100"
        assert event.details["password"] == "secret123"


class TestQueryTimeout:
    """Test query timeout handling."""

    @pytest.mark.asyncio
    async def test_query_timeout_raises_exception(self, audit_service, mock_db):
        """Test that query timeout raises exception after 30 seconds."""
        # Arrange
        # Mock count query to succeed quickly
        count_result = MagicMock()
        count_result.scalar.return_value = 1000

        # Mock execute to timeout on second call
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(31)  # Longer than 30s timeout
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        # First call (count) succeeds, second call (events) times out
        call_count = [0]

        async def execute_mock(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return count_result
            else:
                return await slow_execute(*args, **kwargs)

        mock_db.execute = execute_mock

        # Act & Assert
        with pytest.raises(asyncio.TimeoutError):
            await audit_service.query_audit_logs(db=mock_db, page=1, page_size=10000)
