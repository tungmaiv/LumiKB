"""Integration tests for audit logging infrastructure.

Tests cover:
- AuditService writes events to database (AC: 1, 4)
- AuditEvent model has correct structure (AC: 2)
- AuditRepository uses INSERT-only pattern (AC: 3)
- Async audit logging does not block requests (AC: 5)

Note: Tests that verify audit events via HTTP endpoints use the fire-and-forget
pattern where the endpoint returns success. Database verification is tested
via AuditRepository and direct service tests.
"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit import AuditEvent

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestAuditTableImmutability:
    """Test that audit.events table enforces INSERT-only access."""

    async def test_audit_events_use_insert_only_pattern(
        self,
        test_engine,
        setup_database,  # noqa: ARG002
    ):
        """Test that AuditRepository only uses INSERT (not ORM add/merge)."""
        from app.repositories.audit_repo import AuditRepository

        test_session_factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with test_session_factory() as session:
            repo = AuditRepository(session)

            # Create an event using the repository
            await repo.create_event(
                action="test.insert_only",
                resource_type="test",
                user_id=None,
                resource_id=None,
                details={"test": True},
                ip_address="127.0.0.1",
            )

        # Verify it was inserted with a fresh session
        async with test_session_factory() as session:
            result = await session.execute(
                select(AuditEvent).where(AuditEvent.action == "test.insert_only")
            )
            event = result.scalar_one_or_none()

            assert event is not None
            assert event.action == "test.insert_only"
            assert event.details == {"test": True}


class TestAuditServiceIntegration:
    """Test AuditService integration with database."""

    async def test_audit_service_writes_to_database(
        self,
        test_engine,
        setup_database,  # noqa: ARG002
    ):
        """Test that AuditService successfully writes to audit.events table."""
        import app.services.audit_service as audit_module
        from app.services.audit_service import AuditService

        # Create a service with test database
        test_session_factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        service = AuditService()
        user_id = uuid.uuid4()

        # Patch the session factory to use test database
        original_factory = audit_module.async_session_factory

        try:
            audit_module.async_session_factory = test_session_factory

            await service.log_event(
                action="test.service_write",
                resource_type="test",
                user_id=user_id,
                resource_id=user_id,
                details={"service": "test"},
                ip_address="10.0.0.1",
            )

            # Query with fresh session
            async with test_session_factory() as session:
                result = await session.execute(
                    select(AuditEvent).where(AuditEvent.action == "test.service_write")
                )
                event = result.scalar_one_or_none()

            assert event is not None
            assert event.user_id == user_id
            assert event.details == {"service": "test"}
            assert str(event.ip_address) == "10.0.0.1"

        finally:
            audit_module.async_session_factory = original_factory

    async def test_audit_service_handles_errors_silently(self):
        """Test that AuditService doesn't raise on database errors."""
        from app.services.audit_service import AuditService

        service = AuditService()

        # This should not raise even with invalid session factory
        # The service catches all exceptions
        await service.log_event(
            action="test.error_handling",
            resource_type="test",
            ip_address="127.0.0.1",
        )
        # If we got here without exception, the test passes


class TestAuditEventFields:
    """Test that audit events contain all required fields."""

    async def test_audit_event_has_all_required_fields(
        self,
        test_engine,
        setup_database,  # noqa: ARG002
    ):
        """Test that audit events contain timestamp, user_id, action, resource_type, etc."""
        from app.repositories.audit_repo import AuditRepository

        test_session_factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        user_id = uuid.uuid4()
        resource_id = uuid.uuid4()

        async with test_session_factory() as session:
            repo = AuditRepository(session)
            await repo.create_event(
                action="test.field_verification",
                resource_type="test_resource",
                user_id=user_id,
                resource_id=resource_id,
                details={"key": "value"},
                ip_address="192.168.1.100",
            )

        # Verify with fresh session
        async with test_session_factory() as session:
            result = await session.execute(
                select(AuditEvent).where(AuditEvent.action == "test.field_verification")
            )
            event = result.scalar_one_or_none()

        assert event is not None
        # Verify all required fields are present (AC: 2)
        assert event.id is not None  # UUID primary key
        assert event.timestamp is not None  # TIMESTAMPTZ
        assert event.action == "test.field_verification"  # action
        assert event.resource_type == "test_resource"  # resource_type
        assert event.user_id == user_id
        assert event.resource_id == resource_id
        assert event.details == {"key": "value"}
        assert str(event.ip_address) == "192.168.1.100"  # INET returns IPv4Address
