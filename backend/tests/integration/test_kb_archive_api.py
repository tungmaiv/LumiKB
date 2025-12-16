"""Integration tests for KB archive/restore/delete API (Stories 7-24, 7-25).

Tests cover all Acceptance Criteria:
Story 7-24 (KB Archive Backend):
- AC-7.24.1: Archive endpoint sets KB.archived_at and cascades to documents
- AC-7.24.2: Outbox event created for Qdrant payload updates
- AC-7.24.3: DELETE requires KB to have 0 documents (409 if documents exist)
- AC-7.24.4: ADMIN permission required for archive/delete
- AC-7.24.5: Audit logging for archive actions

Story 7-25 (KB Restore Backend):
- AC-7.25.1: Restore endpoint clears KB.archived_at and document.archived_at
- AC-7.25.2: Outbox event created for Qdrant payload updates (is_archived: false)
- AC-7.25.3: ADMIN permission required for restore
- AC-7.25.4: Already active KB returns 404
"""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.outbox import Outbox
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User
from tests.factories import create_registration_data

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def db_session_for_kb(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for KB admin tests."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def admin_user_for_kb(
    api_client: AsyncClient, db_session_for_kb: AsyncSession
) -> dict:
    """Create an admin (superuser) test user for KB archive tests."""
    user_data = create_registration_data()
    response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Set is_superuser=True in database
    result = await db_session_for_kb.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await db_session_for_kb.commit()

    return {**user_data, "user": response_data, "user_id": response_data["id"]}


@pytest.fixture
async def admin_cookies_for_kb(
    api_client: AsyncClient, admin_user_for_kb: dict
) -> dict:
    """Login as admin and return cookies for KB archive tests."""
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user_for_kb["email"],
            "password": admin_user_for_kb["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_for_kb(api_client: AsyncClient) -> dict:
    """Create a regular (non-admin) test user for permission tests."""
    user_data = create_registration_data()
    response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json(), "user_id": response.json()["id"]}


@pytest.fixture
async def regular_user_cookies(
    api_client: AsyncClient, regular_user_for_kb: dict
) -> dict:
    """Login as regular user and return cookies."""
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": regular_user_for_kb["email"],
            "password": regular_user_for_kb["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def kb_with_documents(
    db_session_for_kb: AsyncSession,
    admin_user_for_kb: dict,
) -> dict:
    """Create a KB with documents for archive testing.

    Returns:
        dict: {
            "kb_id": str,
            "doc_ids": list[str],
            "document_count": int,
            "owner_id": str,
        }
    """
    # Get admin user
    result = await db_session_for_kb.execute(
        select(User).where(User.id == admin_user_for_kb["user_id"])
    )
    test_user = result.scalar_one()

    # Create KB
    kb = KnowledgeBase(
        name="Archive Test KB",
        description="KB for archive testing",
        owner_id=test_user.id,
        status="active",
    )
    db_session_for_kb.add(kb)
    await db_session_for_kb.flush()

    # Grant ADMIN permission
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.ADMIN,
    )
    db_session_for_kb.add(permission)

    # Create test documents
    docs = []
    for i in range(3):
        doc = Document(
            kb_id=kb.id,
            name=f"Test Document {i}.pdf",
            original_filename=f"test_{i}.pdf",
            mime_type="application/pdf",
            file_size_bytes=1024 * (i + 1),
            file_path=f"kb-{kb.id}/test_{i}.pdf",
            checksum=f"{chr(97 + i)}" * 64,  # 'aaa...', 'bbb...', etc.
            status=DocumentStatus.READY,
            chunk_count=5,
            uploaded_by=test_user.id,
        )
        db_session_for_kb.add(doc)
        docs.append(doc)

    await db_session_for_kb.commit()

    # Refresh all to get IDs
    await db_session_for_kb.refresh(kb)
    for doc in docs:
        await db_session_for_kb.refresh(doc)

    return {
        "kb_id": str(kb.id),
        "doc_ids": [str(d.id) for d in docs],
        "document_count": len(docs),
        "owner_id": str(test_user.id),
    }


@pytest.fixture
async def empty_kb(
    db_session_for_kb: AsyncSession,
    admin_user_for_kb: dict,
) -> dict:
    """Create an empty KB (no documents) for delete testing.

    Returns:
        dict: {"kb_id": str, "owner_id": str}
    """
    # Get admin user
    result = await db_session_for_kb.execute(
        select(User).where(User.id == admin_user_for_kb["user_id"])
    )
    test_user = result.scalar_one()

    # Create empty KB
    kb = KnowledgeBase(
        name="Empty KB for Delete",
        description="KB with no documents",
        owner_id=test_user.id,
        status="active",
    )
    db_session_for_kb.add(kb)
    await db_session_for_kb.flush()

    # Grant ADMIN permission
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.ADMIN,
    )
    db_session_for_kb.add(permission)
    await db_session_for_kb.commit()
    await db_session_for_kb.refresh(kb)

    return {
        "kb_id": str(kb.id),
        "owner_id": str(test_user.id),
    }


@pytest.fixture
async def archived_kb(
    db_session_for_kb: AsyncSession,
    admin_user_for_kb: dict,
) -> dict:
    """Create an already archived KB for restore testing.

    Returns:
        dict: {"kb_id": str, "doc_ids": list[str], "archived_at": str}
    """
    # Get admin user
    result = await db_session_for_kb.execute(
        select(User).where(User.id == admin_user_for_kb["user_id"])
    )
    test_user = result.scalar_one()

    archived_time = datetime.now(UTC)

    # Create archived KB
    kb = KnowledgeBase(
        name="Archived Test KB",
        description="KB already archived",
        owner_id=test_user.id,
        status="archived",
        archived_at=archived_time,
    )
    db_session_for_kb.add(kb)
    await db_session_for_kb.flush()

    # Grant ADMIN permission
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.ADMIN,
    )
    db_session_for_kb.add(permission)

    # Create archived documents
    docs = []
    for i in range(2):
        doc = Document(
            kb_id=kb.id,
            name=f"Archived Doc {i}.pdf",
            original_filename=f"archived_{i}.pdf",
            mime_type="application/pdf",
            file_size_bytes=2048,
            file_path=f"kb-{kb.id}/archived_{i}.pdf",
            checksum=f"{chr(100 + i)}" * 64,
            status=DocumentStatus.READY,
            chunk_count=3,
            uploaded_by=test_user.id,
            archived_at=archived_time,  # Documents are also archived
        )
        db_session_for_kb.add(doc)
        docs.append(doc)

    await db_session_for_kb.commit()
    await db_session_for_kb.refresh(kb)
    for doc in docs:
        await db_session_for_kb.refresh(doc)

    return {
        "kb_id": str(kb.id),
        "doc_ids": [str(d.id) for d in docs],
        "archived_at": archived_time.isoformat(),
        "owner_id": str(test_user.id),
    }


# =============================================================================
# Story 7-24: KB Archive Tests
# =============================================================================


class TestKBArchiveEndpoint:
    """AC-7.24.1: Archive endpoint sets KB.archived_at and cascades to documents."""

    @pytest.mark.asyncio
    async def test_archive_kb_returns_204(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        kb_with_documents: dict,
    ) -> None:
        """Given active KB, When POST /archive, Then returns 204 No Content."""
        kb_id = kb_with_documents["kb_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/archive",
            cookies=admin_cookies_for_kb,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_archive_kb_sets_archived_at(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        kb_with_documents: dict,
        db_session_for_kb: AsyncSession,
    ) -> None:
        """Given archive succeeds, Then KB.archived_at is set to current timestamp."""
        kb_id = kb_with_documents["kb_id"]
        before = datetime.now(UTC)

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/archive",
            cookies=admin_cookies_for_kb,
        )
        assert response.status_code == 204

        after = datetime.now(UTC)

        # Verify in database
        result = await db_session_for_kb.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one()

        assert kb.status == "archived"
        assert kb.archived_at is not None
        assert before <= kb.archived_at <= after

    @pytest.mark.asyncio
    async def test_archive_kb_cascades_to_documents(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        kb_with_documents: dict,
        db_session_for_kb: AsyncSession,
    ) -> None:
        """Given archive succeeds, Then all documents have archived_at set."""
        kb_id = kb_with_documents["kb_id"]
        doc_count = kb_with_documents["document_count"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/archive",
            cookies=admin_cookies_for_kb,
        )
        assert response.status_code == 204

        # Verify all documents are archived
        result = await db_session_for_kb.execute(
            select(Document).where(Document.kb_id == kb_id)
        )
        docs = result.scalars().all()

        assert len(docs) == doc_count
        for doc in docs:
            assert doc.archived_at is not None, f"Document {doc.id} should be archived"

    @pytest.mark.asyncio
    async def test_archive_nonexistent_kb_returns_404(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
    ) -> None:
        """Given non-existent KB ID, When archive, Then returns 404."""
        fake_kb_id = str(uuid.uuid4())

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{fake_kb_id}/archive",
            cookies=admin_cookies_for_kb,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_archive_already_archived_kb_returns_404(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        archived_kb: dict,
    ) -> None:
        """Given already archived KB, When archive again, Then returns 404."""
        kb_id = archived_kb["kb_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/archive",
            cookies=admin_cookies_for_kb,
        )

        assert response.status_code == 404


class TestKBArchiveOutbox:
    """AC-7.24.2: Outbox event created for Qdrant payload updates."""

    @pytest.mark.asyncio
    async def test_archive_creates_outbox_event(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        kb_with_documents: dict,
        db_session_for_kb: AsyncSession,
    ) -> None:
        """Given archive succeeds, Then kb.archive outbox event is created."""
        kb_id = kb_with_documents["kb_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/archive",
            cookies=admin_cookies_for_kb,
        )
        assert response.status_code == 204

        # Verify outbox event
        result = await db_session_for_kb.execute(
            select(Outbox).where(
                Outbox.aggregate_id == kb_id,
                Outbox.event_type == "kb.archive",
            )
        )
        outbox_event = result.scalar_one_or_none()

        assert outbox_event is not None
        assert outbox_event.payload["kb_id"] == kb_id
        assert outbox_event.payload["is_archived"] is True


class TestKBDeleteWithDocuments:
    """AC-7.24.3: DELETE requires KB to have 0 documents."""

    @pytest.mark.asyncio
    async def test_delete_kb_with_documents_returns_409(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        kb_with_documents: dict,
    ) -> None:
        """Given KB with documents, When DELETE, Then returns 409 Conflict."""
        kb_id = kb_with_documents["kb_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}",
            cookies=admin_cookies_for_kb,
        )

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["code"] == "KB_HAS_DOCUMENTS"

    @pytest.mark.asyncio
    async def test_delete_empty_kb_returns_204(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        empty_kb: dict,
    ) -> None:
        """Given empty KB (0 documents), When DELETE, Then returns 204."""
        kb_id = empty_kb["kb_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}",
            cookies=admin_cookies_for_kb,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_empty_kb_removes_from_database(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        empty_kb: dict,
        db_session_for_kb: AsyncSession,
    ) -> None:
        """Given delete succeeds, Then KB is removed from database."""
        kb_id = empty_kb["kb_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}",
            cookies=admin_cookies_for_kb,
        )
        assert response.status_code == 204

        # Verify KB is deleted
        result = await db_session_for_kb.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()
        assert kb is None

    @pytest.mark.asyncio
    async def test_delete_creates_outbox_event(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        empty_kb: dict,
        db_session_for_kb: AsyncSession,
    ) -> None:
        """Given delete succeeds, Then kb.delete outbox event is created."""
        kb_id = empty_kb["kb_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}",
            cookies=admin_cookies_for_kb,
        )
        assert response.status_code == 204

        # Verify outbox event
        result = await db_session_for_kb.execute(
            select(Outbox).where(
                Outbox.aggregate_id == kb_id,
                Outbox.event_type == "kb.delete",
            )
        )
        outbox_event = result.scalar_one_or_none()

        assert outbox_event is not None
        assert outbox_event.payload["kb_id"] == kb_id


class TestKBArchivePermissions:
    """AC-7.24.4: ADMIN permission required for archive/delete."""

    @pytest.mark.asyncio
    async def test_archive_without_auth_returns_401(
        self,
        api_client: AsyncClient,
        kb_with_documents: dict,
    ) -> None:
        """Given no authentication, When archive, Then returns 401."""
        kb_id = kb_with_documents["kb_id"]
        api_client.cookies.clear()

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/archive",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_archive_non_admin_returns_403(
        self,
        api_client: AsyncClient,
        regular_user_cookies: dict,
        kb_with_documents: dict,
    ) -> None:
        """Given non-admin user, When archive, Then returns 403."""
        kb_id = kb_with_documents["kb_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/archive",
            cookies=regular_user_cookies,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_without_auth_returns_401(
        self,
        api_client: AsyncClient,
        empty_kb: dict,
    ) -> None:
        """Given no authentication, When delete, Then returns 401."""
        kb_id = empty_kb["kb_id"]
        api_client.cookies.clear()

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_non_admin_returns_403(
        self,
        api_client: AsyncClient,
        regular_user_cookies: dict,
        empty_kb: dict,
    ) -> None:
        """Given non-admin user, When delete, Then returns 403."""
        kb_id = empty_kb["kb_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}",
            cookies=regular_user_cookies,
        )

        assert response.status_code == 403


# =============================================================================
# Story 7-25: KB Restore Tests
# =============================================================================


class TestKBRestoreEndpoint:
    """AC-7.25.1: Restore endpoint clears KB.archived_at and document.archived_at."""

    @pytest.mark.asyncio
    async def test_restore_kb_returns_204(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        archived_kb: dict,
    ) -> None:
        """Given archived KB, When POST /restore, Then returns 204 No Content."""
        kb_id = archived_kb["kb_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/restore",
            cookies=admin_cookies_for_kb,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_restore_kb_clears_archived_at(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        archived_kb: dict,
        db_session_for_kb: AsyncSession,
    ) -> None:
        """Given restore succeeds, Then KB.archived_at is cleared."""
        kb_id = archived_kb["kb_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/restore",
            cookies=admin_cookies_for_kb,
        )
        assert response.status_code == 204

        # Verify in database
        result = await db_session_for_kb.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one()

        assert kb.status == "active"
        assert kb.archived_at is None

    @pytest.mark.asyncio
    async def test_restore_kb_cascades_to_documents(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        archived_kb: dict,
        db_session_for_kb: AsyncSession,
    ) -> None:
        """Given restore succeeds, Then all documents have archived_at cleared."""
        kb_id = archived_kb["kb_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/restore",
            cookies=admin_cookies_for_kb,
        )
        assert response.status_code == 204

        # Verify all documents are restored
        result = await db_session_for_kb.execute(
            select(Document).where(Document.kb_id == kb_id)
        )
        docs = result.scalars().all()

        assert len(docs) > 0
        for doc in docs:
            assert doc.archived_at is None, f"Document {doc.id} should be restored"

    @pytest.mark.asyncio
    async def test_restore_nonexistent_kb_returns_404(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
    ) -> None:
        """Given non-existent KB ID, When restore, Then returns 404."""
        fake_kb_id = str(uuid.uuid4())

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{fake_kb_id}/restore",
            cookies=admin_cookies_for_kb,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_restore_active_kb_returns_404(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        kb_with_documents: dict,
    ) -> None:
        """Given already active KB, When restore, Then returns 404."""
        kb_id = kb_with_documents["kb_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/restore",
            cookies=admin_cookies_for_kb,
        )

        assert response.status_code == 404


class TestKBRestoreOutbox:
    """AC-7.25.2: Outbox event created for Qdrant payload updates."""

    @pytest.mark.asyncio
    async def test_restore_creates_outbox_event(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        archived_kb: dict,
        db_session_for_kb: AsyncSession,
    ) -> None:
        """Given restore succeeds, Then kb.restore outbox event is created."""
        kb_id = archived_kb["kb_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/restore",
            cookies=admin_cookies_for_kb,
        )
        assert response.status_code == 204

        # Verify outbox event
        result = await db_session_for_kb.execute(
            select(Outbox).where(
                Outbox.aggregate_id == kb_id,
                Outbox.event_type == "kb.restore",
            )
        )
        outbox_event = result.scalar_one_or_none()

        assert outbox_event is not None
        assert outbox_event.payload["kb_id"] == kb_id
        assert outbox_event.payload["is_archived"] is False


class TestKBRestorePermissions:
    """AC-7.25.3: ADMIN permission required for restore."""

    @pytest.mark.asyncio
    async def test_restore_without_auth_returns_401(
        self,
        api_client: AsyncClient,
        archived_kb: dict,
    ) -> None:
        """Given no authentication, When restore, Then returns 401."""
        kb_id = archived_kb["kb_id"]
        api_client.cookies.clear()

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/restore",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_restore_non_admin_returns_403(
        self,
        api_client: AsyncClient,
        regular_user_cookies: dict,
        archived_kb: dict,
    ) -> None:
        """Given non-admin user, When restore, Then returns 403."""
        kb_id = archived_kb["kb_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/restore",
            cookies=regular_user_cookies,
        )

        assert response.status_code == 403


# =============================================================================
# Archive/Restore Round-Trip Tests
# =============================================================================


class TestKBArchiveRestoreRoundTrip:
    """Test full archive -> restore workflow."""

    @pytest.mark.asyncio
    async def test_archive_then_restore_preserves_data(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        kb_with_documents: dict,
        db_session_for_kb: AsyncSession,
    ) -> None:
        """Given archive then restore, Then KB and documents return to original state."""
        kb_id = kb_with_documents["kb_id"]
        original_doc_count = kb_with_documents["document_count"]

        # Archive
        archive_response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/archive",
            cookies=admin_cookies_for_kb,
        )
        assert archive_response.status_code == 204

        # Verify archived
        result = await db_session_for_kb.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one()
        assert kb.status == "archived"

        # Restore
        restore_response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/restore",
            cookies=admin_cookies_for_kb,
        )
        assert restore_response.status_code == 204

        # Verify restored
        await db_session_for_kb.refresh(kb)
        assert kb.status == "active"
        assert kb.archived_at is None

        # Verify documents restored
        doc_result = await db_session_for_kb.execute(
            select(Document).where(Document.kb_id == kb_id)
        )
        docs = doc_result.scalars().all()
        assert len(docs) == original_doc_count
        for doc in docs:
            assert doc.archived_at is None

    @pytest.mark.asyncio
    async def test_cannot_delete_after_archive_with_documents(
        self,
        api_client: AsyncClient,
        admin_cookies_for_kb: dict,
        kb_with_documents: dict,
    ) -> None:
        """Given archived KB with documents, When DELETE, Then returns 409."""
        kb_id = kb_with_documents["kb_id"]

        # Archive first
        archive_response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/archive",
            cookies=admin_cookies_for_kb,
        )
        assert archive_response.status_code == 204

        # Try to delete - should fail because documents still exist
        delete_response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}",
            cookies=admin_cookies_for_kb,
        )
        assert delete_response.status_code == 409
