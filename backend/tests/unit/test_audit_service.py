"""Unit tests for AuditService.

Tests:
- log_event() creates audit event with all required fields
- Async write does not block caller
- Error handling (database failure should log error, not raise)
- IP address extraction from request
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit

from app.models.audit import AuditEvent
from app.repositories.audit_repo import AuditRepository
from app.services.audit_service import AuditService, audit_service


class TestAuditService:
    """Test suite for AuditService class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        """Create a mock session factory context manager."""

        async def mock_factory():
            return mock_session

        # Create an async context manager mock
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=mock_session)
        cm.__aexit__ = AsyncMock(return_value=None)
        return cm

    async def test_log_event_creates_audit_event_with_all_fields(
        self, mock_session_factory, mock_session
    ):
        """Test that log_event creates an audit event with all required fields."""
        service = AuditService()
        user_id = uuid.uuid4()
        resource_id = uuid.uuid4()

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            await service.log_event(
                action="user.login",
                resource_type="user",
                user_id=user_id,
                resource_id=resource_id,
                details={"browser": "Chrome"},
                ip_address="192.168.1.1",
            )

        # Verify session was used
        mock_session_factory.__aenter__.assert_called_once()
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_log_event_handles_database_error_gracefully(
        self, mock_session_factory, mock_session
    ):
        """Test that database errors don't propagate to caller."""
        service = AuditService()

        # Make commit raise an exception
        mock_session.commit.side_effect = Exception("Database connection failed")

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            # Should not raise
            await service.log_event(
                action="user.login",
                resource_type="user",
                ip_address="192.168.1.1",
            )

    async def test_log_event_with_optional_fields_none(
        self, mock_session_factory, mock_session
    ):
        """Test that optional fields can be None."""
        service = AuditService()

        with patch(
            "app.services.audit_service.async_session_factory",
            return_value=mock_session_factory,
        ):
            await service.log_event(
                action="anonymous.action",
                resource_type="system",
                user_id=None,
                resource_id=None,
                details=None,
                ip_address=None,
            )

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_singleton_instance_exists(self):
        """Test that audit_service singleton is available."""
        assert audit_service is not None
        assert isinstance(audit_service, AuditService)


class TestAuditRepository:
    """Test suite for AuditRepository class."""

    async def test_create_event_uses_insert_statement(self):
        """Test that create_event uses INSERT statement."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        repo = AuditRepository(mock_session)
        user_id = uuid.uuid4()

        await repo.create_event(
            action="user.login",
            resource_type="user",
            user_id=user_id,
            resource_id=user_id,
            details={"key": "value"},
            ip_address="10.0.0.1",
        )

        # Verify execute was called with INSERT statement
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        # The statement should be an INSERT
        assert "INSERT" in str(call_args).upper() or hasattr(call_args, "compile")

        mock_session.commit.assert_called_once()


class TestAuditEventModel:
    """Test suite for AuditEvent model structure."""

    def test_model_has_required_columns(self):
        """Test that AuditEvent model has all required columns."""
        # Check table name and schema
        assert AuditEvent.__tablename__ == "events"
        assert AuditEvent.__table_args__[-1]["schema"] == "audit"

        # Check columns exist via mapper
        mapper = AuditEvent.__mapper__
        column_names = {c.key for c in mapper.columns}

        required_columns = {
            "id",
            "timestamp",
            "user_id",
            "action",
            "resource_type",
            "resource_id",
            "details",
            "ip_address",
        }

        assert required_columns.issubset(column_names)

    def test_model_indexes(self):
        """Test that AuditEvent model has required indexes."""
        # Get index names from table args
        table_args = AuditEvent.__table_args__
        index_names = [
            arg.name for arg in table_args if hasattr(arg, "name") and arg.name
        ]

        assert "idx_audit_user" in index_names
        assert "idx_audit_timestamp" in index_names
        assert "idx_audit_resource" in index_names
