"""Unit tests for KB archive/restore/hard_delete service methods (Stories 7-24, 7-25).

Tests focus on business logic validation that can be tested with mocked dependencies.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.knowledge_base import KnowledgeBase
from app.models.permission import PermissionLevel
from app.models.user import User

pytestmark = pytest.mark.unit


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> User:
    """Create a mock regular user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "user@example.com"
    user.is_superuser = False
    return user


@pytest.fixture
def mock_admin_user() -> User:
    """Create a mock admin user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "admin@example.com"
    user.is_superuser = True
    return user


@pytest.fixture
def mock_kb() -> KnowledgeBase:
    """Create a mock active KB."""
    kb = MagicMock(spec=KnowledgeBase)
    kb.id = uuid4()
    kb.name = "Test KB"
    kb.status = "active"
    kb.archived_at = None
    kb.owner_id = uuid4()
    kb.qdrant_collection_name = f"kb_{kb.id}"
    return kb


@pytest.fixture
def mock_archived_kb() -> KnowledgeBase:
    """Create a mock archived KB."""
    kb = MagicMock(spec=KnowledgeBase)
    kb.id = uuid4()
    kb.name = "Archived KB"
    kb.status = "archived"
    kb.archived_at = datetime.now(UTC)
    kb.owner_id = uuid4()
    kb.qdrant_collection_name = f"kb_{kb.id}"
    return kb


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock async session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


# =============================================================================
# Archive Method Tests (Story 7-24)
# =============================================================================


class TestKBServiceArchive:
    """Tests for KBService.archive() method."""

    @pytest.mark.asyncio
    async def test_archive_requires_admin_permission(
        self,
        mock_user: User,
        mock_session: AsyncMock,
    ) -> None:
        """Given non-admin user, When archive, Then raises PermissionError."""
        from app.services.kb_service import KBService

        service = KBService(mock_session)

        # Mock check_permission to return False (no ADMIN permission)
        service.check_permission = AsyncMock(return_value=False)

        kb_id = uuid4()

        with pytest.raises(PermissionError, match="ADMIN permission required"):
            await service.archive(kb_id, mock_user)

        # Verify permission check was called with ADMIN level
        service.check_permission.assert_called_once_with(
            kb_id, mock_user, PermissionLevel.ADMIN
        )

    @pytest.mark.asyncio
    async def test_archive_returns_false_for_nonexistent_kb(
        self,
        mock_admin_user: User,
        mock_session: AsyncMock,
    ) -> None:
        """Given non-existent KB, When archive, Then returns False."""
        from app.services.kb_service import KBService

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        # Mock execute to return None (KB not found)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        kb_id = uuid4()
        result = await service.archive(kb_id, mock_admin_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_archive_returns_false_for_already_archived(
        self,
        mock_admin_user: User,
        mock_archived_kb: KnowledgeBase,
        mock_session: AsyncMock,
    ) -> None:
        """Given already archived KB, When archive, Then returns False.

        Note: The query filters by status='active', so archived KBs won't be found.
        """
        from app.services.kb_service import KBService

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        # Mock execute to return None (KB not found because status != 'active')
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.archive(mock_archived_kb.id, mock_admin_user)

        assert result is False

    @pytest.mark.asyncio
    @patch("app.services.kb_service.audit_service")
    async def test_archive_sets_status_and_timestamp(
        self,
        mock_audit: MagicMock,
        mock_admin_user: User,
        mock_kb: KnowledgeBase,
        mock_session: AsyncMock,
    ) -> None:
        """Given active KB, When archive, Then sets status='archived' and archived_at."""
        from app.services.kb_service import KBService

        mock_audit.log_event = AsyncMock()

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        # First call returns KB, second returns doc count
        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = mock_kb

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5

        mock_session.execute.side_effect = [
            mock_kb_result,  # KB query
            MagicMock(),  # Document update query
            mock_count_result,  # Doc count query
        ]

        before = datetime.now(UTC)
        result = await service.archive(mock_kb.id, mock_admin_user)
        after = datetime.now(UTC)

        assert result is True
        assert mock_kb.status == "archived"
        assert mock_kb.archived_at is not None
        assert before <= mock_kb.archived_at <= after

    @pytest.mark.asyncio
    @patch("app.services.kb_service.audit_service")
    async def test_archive_creates_outbox_event(
        self,
        mock_audit: MagicMock,
        mock_admin_user: User,
        mock_kb: KnowledgeBase,
        mock_session: AsyncMock,
    ) -> None:
        """Given archive succeeds, Then creates kb.archive outbox event."""
        from app.models.outbox import Outbox
        from app.services.kb_service import KBService

        mock_audit.log_event = AsyncMock()

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = mock_kb

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 3

        mock_session.execute.side_effect = [
            mock_kb_result,
            MagicMock(),
            mock_count_result,
        ]

        await service.archive(mock_kb.id, mock_admin_user)

        # Verify outbox event was added
        add_calls = mock_session.add.call_args_list
        outbox_event = None
        for call in add_calls:
            if isinstance(call[0][0], Outbox):
                outbox_event = call[0][0]
                break

        assert outbox_event is not None
        assert outbox_event.event_type == "kb.archive"
        assert outbox_event.payload["kb_id"] == str(mock_kb.id)
        assert outbox_event.payload["is_archived"] is True


# =============================================================================
# Restore Method Tests (Story 7-25)
# =============================================================================


class TestKBServiceRestore:
    """Tests for KBService.restore() method."""

    @pytest.mark.asyncio
    async def test_restore_requires_admin_permission(
        self,
        mock_user: User,
        mock_session: AsyncMock,
    ) -> None:
        """Given non-admin user, When restore, Then raises PermissionError."""
        from app.services.kb_service import KBService

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=False)

        kb_id = uuid4()

        with pytest.raises(PermissionError, match="ADMIN permission required"):
            await service.restore(kb_id, mock_user)

    @pytest.mark.asyncio
    async def test_restore_returns_false_for_nonexistent_kb(
        self,
        mock_admin_user: User,
        mock_session: AsyncMock,
    ) -> None:
        """Given non-existent KB, When restore, Then returns False."""
        from app.services.kb_service import KBService

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        kb_id = uuid4()
        result = await service.restore(kb_id, mock_admin_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_restore_returns_false_for_active_kb(
        self,
        mock_admin_user: User,
        mock_kb: KnowledgeBase,
        mock_session: AsyncMock,
    ) -> None:
        """Given active KB (not archived), When restore, Then returns False.

        Note: The query filters by status='archived', so active KBs won't be found.
        """
        from app.services.kb_service import KBService

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        # Active KB won't be found by the query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.restore(mock_kb.id, mock_admin_user)

        assert result is False

    @pytest.mark.asyncio
    @patch("app.services.kb_service.audit_service")
    async def test_restore_clears_archived_status(
        self,
        mock_audit: MagicMock,
        mock_admin_user: User,
        mock_archived_kb: KnowledgeBase,
        mock_session: AsyncMock,
    ) -> None:
        """Given archived KB, When restore, Then clears status and archived_at."""
        from app.services.kb_service import KBService

        mock_audit.log_event = AsyncMock()

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = mock_archived_kb

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_session.execute.side_effect = [
            mock_kb_result,
            MagicMock(),  # Document update
            mock_count_result,
        ]

        result = await service.restore(mock_archived_kb.id, mock_admin_user)

        assert result is True
        assert mock_archived_kb.status == "active"
        assert mock_archived_kb.archived_at is None

    @pytest.mark.asyncio
    @patch("app.services.kb_service.audit_service")
    async def test_restore_creates_outbox_event(
        self,
        mock_audit: MagicMock,
        mock_admin_user: User,
        mock_archived_kb: KnowledgeBase,
        mock_session: AsyncMock,
    ) -> None:
        """Given restore succeeds, Then creates kb.restore outbox event."""
        from app.models.outbox import Outbox
        from app.services.kb_service import KBService

        mock_audit.log_event = AsyncMock()

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = mock_archived_kb

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_session.execute.side_effect = [
            mock_kb_result,
            MagicMock(),
            mock_count_result,
        ]

        await service.restore(mock_archived_kb.id, mock_admin_user)

        # Verify outbox event was added
        add_calls = mock_session.add.call_args_list
        outbox_event = None
        for call in add_calls:
            if isinstance(call[0][0], Outbox):
                outbox_event = call[0][0]
                break

        assert outbox_event is not None
        assert outbox_event.event_type == "kb.restore"
        assert outbox_event.payload["kb_id"] == str(mock_archived_kb.id)
        assert outbox_event.payload["is_archived"] is False


# =============================================================================
# Hard Delete Method Tests (Story 7-24)
# =============================================================================


class TestKBServiceHardDelete:
    """Tests for KBService.hard_delete() method."""

    @pytest.mark.asyncio
    async def test_hard_delete_requires_admin_permission(
        self,
        mock_user: User,
        mock_session: AsyncMock,
    ) -> None:
        """Given non-admin user, When hard_delete, Then raises PermissionError."""
        from app.services.kb_service import KBService

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=False)

        kb_id = uuid4()

        with pytest.raises(PermissionError, match="ADMIN permission required"):
            await service.hard_delete(kb_id, mock_user)

    @pytest.mark.asyncio
    async def test_hard_delete_returns_false_for_nonexistent_kb(
        self,
        mock_admin_user: User,
        mock_session: AsyncMock,
    ) -> None:
        """Given non-existent KB, When hard_delete, Then returns False."""
        from app.services.kb_service import KBService

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        kb_id = uuid4()
        result = await service.hard_delete(kb_id, mock_admin_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_hard_delete_raises_for_kb_with_documents(
        self,
        mock_admin_user: User,
        mock_kb: KnowledgeBase,
        mock_session: AsyncMock,
    ) -> None:
        """Given KB with documents, When hard_delete, Then raises ValueError."""
        from app.services.kb_service import KBService

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = mock_kb

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5  # KB has 5 documents

        mock_session.execute.side_effect = [
            mock_kb_result,
            mock_count_result,
        ]

        with pytest.raises(ValueError, match="Cannot delete KB with 5 documents"):
            await service.hard_delete(mock_kb.id, mock_admin_user)

    @pytest.mark.asyncio
    @patch("app.services.kb_service.audit_service")
    async def test_hard_delete_succeeds_for_empty_kb(
        self,
        mock_audit: MagicMock,
        mock_admin_user: User,
        mock_kb: KnowledgeBase,
        mock_session: AsyncMock,
    ) -> None:
        """Given empty KB (0 documents), When hard_delete, Then returns True."""
        from app.services.kb_service import KBService

        mock_audit.log_event = AsyncMock()

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = mock_kb

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0  # Empty KB

        mock_session.execute.side_effect = [
            mock_kb_result,
            mock_count_result,
        ]

        result = await service.hard_delete(mock_kb.id, mock_admin_user)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_kb)

    @pytest.mark.asyncio
    @patch("app.services.kb_service.audit_service")
    async def test_hard_delete_creates_outbox_event(
        self,
        mock_audit: MagicMock,
        mock_admin_user: User,
        mock_kb: KnowledgeBase,
        mock_session: AsyncMock,
    ) -> None:
        """Given hard_delete succeeds, Then creates kb.delete outbox event."""
        from app.models.outbox import Outbox
        from app.services.kb_service import KBService

        mock_audit.log_event = AsyncMock()

        service = KBService(mock_session)
        service.check_permission = AsyncMock(return_value=True)

        mock_kb_result = MagicMock()
        mock_kb_result.scalar_one_or_none.return_value = mock_kb

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_session.execute.side_effect = [
            mock_kb_result,
            mock_count_result,
        ]

        await service.hard_delete(mock_kb.id, mock_admin_user)

        # Verify outbox event was added
        add_calls = mock_session.add.call_args_list
        outbox_event = None
        for call in add_calls:
            if isinstance(call[0][0], Outbox):
                outbox_event = call[0][0]
                break

        assert outbox_event is not None
        assert outbox_event.event_type == "kb.delete"
        assert outbox_event.payload["kb_id"] == str(mock_kb.id)


# =============================================================================
# Permission Check Tests
# =============================================================================


class TestKBServicePermissionCheck:
    """Tests for permission checking logic in archive/restore/delete operations."""

    @pytest.mark.asyncio
    async def test_superuser_bypasses_permission_check(
        self,
        mock_admin_user: User,
        mock_session: AsyncMock,
    ) -> None:
        """Given superuser, When check_permission, Then returns True without DB query."""
        from app.services.kb_service import KBService

        service = KBService(mock_session)
        kb_id = uuid4()

        result = await service.check_permission(
            kb_id, mock_admin_user, PermissionLevel.ADMIN
        )

        assert result is True
        # Should not have queried the database for permissions
        # The superuser check happens before any DB queries

    @pytest.mark.asyncio
    async def test_owner_has_implicit_admin(
        self,
        mock_user: User,
        mock_session: AsyncMock,
    ) -> None:
        """Given KB owner, When check_permission for ADMIN, Then returns True."""
        from app.services.kb_service import KBService

        service = KBService(mock_session)

        # Mock the owner_id query to return the user's ID
        mock_owner_result = MagicMock()
        mock_owner_result.scalar_one_or_none.return_value = mock_user.id
        mock_session.execute.return_value = mock_owner_result

        kb_id = uuid4()
        result = await service.check_permission(kb_id, mock_user, PermissionLevel.ADMIN)

        assert result is True
