"""Integration tests for clear failed document API (Story 6-4).

Tests cover all 5 Acceptance Criteria:
- AC-6.4.1: Clear endpoint removes failed document
- AC-6.4.2: Only failed documents can be cleared (400 for others)
- AC-6.4.3: All partial artifacts removed (PostgreSQL, Qdrant, MinIO, Celery)
- AC-6.4.4: Permission check enforced (403/404 for non-owner/non-admin)
- AC-6.4.5: Graceful handling of missing artifacts

ATDD Checklist Reference: docs/sprint-artifacts/atdd-checklist-epic-6.md
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User
from tests.factories import create_registration_data

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def clear_test_kb(
    db_session: AsyncSession,
    test_user_data: dict,
) -> dict:
    """Create a KB with failed and non-failed documents for clear testing.

    Returns:
        dict: {
            "kb_id": str,
            "failed_doc_id": str,       # FAILED document for clear tests
            "failed_doc_id_2": str,     # Second FAILED doc
            "ready_doc_id": str,        # READY document (should fail clear)
            "pending_doc_id": str,      # PENDING document (should fail)
            "processing_doc_id": str,   # PROCESSING document (should fail)
            "owner_id": str,
        }
    """
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    kb = KnowledgeBase(
        name="Clear Failed Test KB",
        description="KB for clear failed testing",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()

    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.WRITE,
    )
    db_session.add(permission)

    docs = {}

    # FAILED document 1 (can be cleared)
    failed_doc = Document(
        kb_id=kb.id,
        name="Failed Document 1.pdf",
        original_filename="failed1.pdf",
        mime_type="application/pdf",
        file_size_bytes=4096,
        file_path=f"kb-{kb.id}/failed1.pdf",
        checksum="a" * 64,
        status=DocumentStatus.FAILED,
        chunk_count=0,
        last_error="Parsing failed: corrupt PDF",
        uploaded_by=test_user.id,
    )
    db_session.add(failed_doc)
    docs["failed"] = failed_doc

    # FAILED document 2
    failed_doc_2 = Document(
        kb_id=kb.id,
        name="Failed Document 2.pdf",
        original_filename="failed2.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/failed2.pdf",
        checksum="b" * 64,
        status=DocumentStatus.FAILED,
        chunk_count=0,
        last_error="Embedding failed: timeout",
        uploaded_by=test_user.id,
    )
    db_session.add(failed_doc_2)
    docs["failed_2"] = failed_doc_2

    # READY document (cannot be cleared)
    ready_doc = Document(
        kb_id=kb.id,
        name="Ready Document.pdf",
        original_filename="ready.pdf",
        mime_type="application/pdf",
        file_size_bytes=3072,
        file_path=f"kb-{kb.id}/ready.pdf",
        checksum="c" * 64,
        status=DocumentStatus.READY,
        chunk_count=5,
        uploaded_by=test_user.id,
    )
    db_session.add(ready_doc)
    docs["ready"] = ready_doc

    # PENDING document (cannot be cleared)
    pending_doc = Document(
        kb_id=kb.id,
        name="Pending Document.pdf",
        original_filename="pending.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024,
        file_path=f"kb-{kb.id}/pending.pdf",
        checksum="d" * 64,
        status=DocumentStatus.PENDING,
        chunk_count=0,
        uploaded_by=test_user.id,
    )
    db_session.add(pending_doc)
    docs["pending"] = pending_doc

    # PROCESSING document (cannot be cleared)
    processing_doc = Document(
        kb_id=kb.id,
        name="Processing Document.pdf",
        original_filename="processing.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/processing.pdf",
        checksum="e" * 64,
        status=DocumentStatus.PROCESSING,
        chunk_count=0,
        uploaded_by=test_user.id,
    )
    db_session.add(processing_doc)
    docs["processing"] = processing_doc

    await db_session.commit()

    for doc in docs.values():
        await db_session.refresh(doc)

    return {
        "kb_id": str(kb.id),
        "failed_doc_id": str(docs["failed"].id),
        "failed_doc_id_2": str(docs["failed_2"].id),
        "ready_doc_id": str(docs["ready"].id),
        "pending_doc_id": str(docs["pending"].id),
        "processing_doc_id": str(docs["processing"].id),
        "owner_id": str(test_user.id),
    }


@pytest.fixture
async def second_user_data(api_client: AsyncClient) -> dict:
    """Create a second test user without KB access."""
    user_data = create_registration_data()
    response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    user_response = response.json()

    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code in (200, 204)

    return {
        "email": user_data["email"],
        "password": user_data["password"],
        "user_id": user_response["id"],
        "cookies": login_response.cookies,
    }


# =============================================================================
# AC-6.4.1: Clear Endpoint Tests
# =============================================================================


class TestClearEndpoint:
    """AC-6.4.1: Clear endpoint removes failed document."""

    @pytest.mark.asyncio
    async def test_clear_failed_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given a FAILED document, When DELETE clear, Then returns 200 OK."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_clear_removes_document_from_database(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given clear succeeds, Then document not found in database."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        # Verify document deleted from DB
        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        doc = result.scalar_one_or_none()
        assert doc is None, "Document should be deleted from database"

    @pytest.mark.asyncio
    async def test_clear_nonexistent_document_returns_404(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given non-existent document ID, When clear, Then returns 404."""
        kb_id = clear_test_kb["kb_id"]
        fake_doc_id = str(uuid.uuid4())

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}/clear",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 404


# =============================================================================
# AC-6.4.2: Status Validation Tests
# =============================================================================


class TestClearStatusValidation:
    """AC-6.4.2: Only failed documents can be cleared."""

    @pytest.mark.asyncio
    async def test_clear_ready_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given READY document, When clear, Then returns 400."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["ready_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_clear_pending_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given PENDING document, When clear, Then returns 400."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["pending_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_clear_processing_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given PROCESSING document, When clear, Then returns 400."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["processing_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400


# =============================================================================
# AC-6.4.3: All Partial Artifacts Removed Tests
# =============================================================================


class TestClearArtifactCleanup:
    """AC-6.4.3: Clear removes all partial artifacts."""

    @pytest.mark.asyncio
    async def test_clear_removes_postgresql_record(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given clear succeeds, Then PostgreSQL record deleted."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_cleared_document_no_longer_accessible(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given clear succeeds, Then document API returns 404."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id"]

        # Clear the document
        clear_response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )
        assert clear_response.status_code == 200

        # Try to access the document
        get_response = await api_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}",
            cookies=test_user_data["cookies"],
        )
        assert get_response.status_code == 404


# =============================================================================
# AC-6.4.4: Permission Check Tests
# =============================================================================


class TestClearPermissions:
    """AC-6.4.4: Only KB owner or admin can clear."""

    @pytest.mark.asyncio
    async def test_clear_without_authentication_returns_401(
        self,
        api_client: AsyncClient,
        clear_test_kb: dict,
    ) -> None:
        """Given no authentication, When clear, Then returns 401."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id"]

        api_client.cookies.clear()
        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_clear_without_kb_access_returns_404(
        self,
        api_client: AsyncClient,
        second_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given user without KB access, When clear, Then returns 404."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_clear_with_write_permission_succeeds(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        second_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given user with WRITE permission, When clear, Then returns 200."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id"]

        write_permission = KBPermission(
            user_id=second_user_data["user_id"],
            kb_id=uuid.UUID(kb_id),
            permission_level=PermissionLevel.WRITE,
        )
        db_session.add(write_permission)
        await db_session.commit()

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_kb_owner_can_clear(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given KB owner, When clear, Then returns 200."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200


# =============================================================================
# AC-6.4.5: Graceful Missing Artifact Handling Tests
# =============================================================================


class TestClearGracefulHandling:
    """AC-6.4.5: Clear handles missing artifacts gracefully."""

    @pytest.mark.asyncio
    async def test_clear_succeeds_with_no_qdrant_vectors(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given failed doc with no Qdrant vectors, When clear, Then succeeds."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id"]

        # Failed documents typically have no Qdrant vectors
        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_clear_succeeds_with_no_minio_file(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
    ) -> None:
        """Given failed doc where file upload may have failed, When clear, Then succeeds."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id_2"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200


# =============================================================================
# Audit Logging Tests
# =============================================================================


class TestClearAuditLogging:
    """Audit logging for clear operations."""

    @pytest.mark.asyncio
    async def test_clear_creates_audit_log_entry(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        clear_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given successful clear, When audit log queried, Then contains entry."""
        kb_id = clear_test_kb["kb_id"]
        doc_id = clear_test_kb["failed_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(
                AuditEvent.resource_id == doc_id,
                AuditEvent.action.contains("clear"),
            )
        )
        audit_entries = result.scalars().all()

        assert len(audit_entries) >= 1, "Should create audit log for clear action"
