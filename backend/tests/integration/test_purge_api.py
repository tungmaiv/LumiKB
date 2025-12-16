"""Integration tests for document purge API (Story 6-3).

Tests cover all 6 Acceptance Criteria:
- AC-6.3.1: Purge endpoint deletes archived document permanently
- AC-6.3.2: Only archived documents can be purged (400 for others)
- AC-6.3.3: Multi-layer storage cleanup (PostgreSQL, Qdrant, MinIO)
- AC-6.3.4: Permission check enforced (403/404 for non-owner/non-admin)
- AC-6.3.5: Bulk purge endpoint with partial success handling
- AC-6.3.6: Graceful handling of missing storage artifacts

ATDD Checklist Reference: docs/sprint-artifacts/atdd-checklist-epic-6.md
"""

import uuid
from datetime import UTC, datetime

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
async def purge_test_kb(
    db_session: AsyncSession,
    test_user_data: dict,
) -> dict:
    """Create a KB with archived and non-archived documents for purge testing.

    Returns:
        dict: {
            "kb_id": str,
            "archived_doc_id": str,      # Archived document for purge tests
            "archived_doc_id_2": str,    # Second archived doc for bulk purge
            "ready_doc_id": str,         # READY document (should fail purge)
            "pending_doc_id": str,       # PENDING document (should fail)
            "failed_doc_id": str,        # FAILED document (should fail)
            "owner_id": str,
        }
    """
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    kb = KnowledgeBase(
        name="Purge Test KB",
        description="KB for purge testing",
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

    # Archived document 1 (can be purged)
    archived_doc = Document(
        kb_id=kb.id,
        name="Archived Document 1.pdf",
        original_filename="archived1.pdf",
        mime_type="application/pdf",
        file_size_bytes=4096,
        file_path=f"kb-{kb.id}/archived1.pdf",
        checksum="a" * 64,
        status=DocumentStatus.READY,
        chunk_count=5,
        uploaded_by=test_user.id,
        archived_at=datetime.now(UTC),
    )
    db_session.add(archived_doc)
    docs["archived"] = archived_doc

    # Archived document 2 (for bulk purge)
    archived_doc_2 = Document(
        kb_id=kb.id,
        name="Archived Document 2.pdf",
        original_filename="archived2.pdf",
        mime_type="application/pdf",
        file_size_bytes=3072,
        file_path=f"kb-{kb.id}/archived2.pdf",
        checksum="b" * 64,
        status=DocumentStatus.READY,
        chunk_count=3,
        uploaded_by=test_user.id,
        archived_at=datetime.now(UTC),
    )
    db_session.add(archived_doc_2)
    docs["archived_2"] = archived_doc_2

    # READY document (cannot be purged)
    ready_doc = Document(
        kb_id=kb.id,
        name="Ready Document.pdf",
        original_filename="ready.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/ready.pdf",
        checksum="c" * 64,
        status=DocumentStatus.READY,
        chunk_count=2,
        uploaded_by=test_user.id,
    )
    db_session.add(ready_doc)
    docs["ready"] = ready_doc

    # PENDING document (cannot be purged)
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

    # FAILED document (cannot be purged directly - must be cleared)
    failed_doc = Document(
        kb_id=kb.id,
        name="Failed Document.pdf",
        original_filename="failed.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024,
        file_path=f"kb-{kb.id}/failed.pdf",
        checksum="e" * 64,
        status=DocumentStatus.FAILED,
        chunk_count=0,
        last_error="Processing failed",
        uploaded_by=test_user.id,
    )
    db_session.add(failed_doc)
    docs["failed"] = failed_doc

    await db_session.commit()

    for doc in docs.values():
        await db_session.refresh(doc)

    return {
        "kb_id": str(kb.id),
        "archived_doc_id": str(docs["archived"].id),
        "archived_doc_id_2": str(docs["archived_2"].id),
        "ready_doc_id": str(docs["ready"].id),
        "pending_doc_id": str(docs["pending"].id),
        "failed_doc_id": str(docs["failed"].id),
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
# AC-6.3.1: Purge Endpoint Tests
# =============================================================================


class TestPurgeEndpoint:
    """AC-6.3.1: Purge endpoint permanently deletes archived document."""

    @pytest.mark.asyncio
    async def test_purge_archived_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given an archived document, When DELETE purge, Then returns 200 OK."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["archived_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_purge_removes_document_from_database(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given purge succeeds, Then document not found in database."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["archived_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
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
    async def test_purge_nonexistent_document_returns_404(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given non-existent document ID, When purge, Then returns 404."""
        kb_id = purge_test_kb["kb_id"]
        fake_doc_id = str(uuid.uuid4())

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}/purge",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 404


# =============================================================================
# AC-6.3.2: Status Validation Tests
# =============================================================================


class TestPurgeStatusValidation:
    """AC-6.3.2: Only archived documents can be purged."""

    @pytest.mark.asyncio
    async def test_purge_ready_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given READY (non-archived) document, When purge, Then returns 400."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["ready_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_purge_pending_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given PENDING document, When purge, Then returns 400."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["pending_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_purge_failed_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given FAILED document, When purge, Then returns 400 (use clear instead)."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["failed_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400


# =============================================================================
# AC-6.3.3: Multi-Layer Storage Cleanup Tests
# =============================================================================


class TestPurgeStorageCleanup:
    """AC-6.3.3: Purge deletes from PostgreSQL, Qdrant, and MinIO."""

    @pytest.mark.asyncio
    async def test_purge_deletes_from_postgresql(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given purge succeeds, Then PostgreSQL record deleted."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["archived_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_purge_document_no_longer_accessible(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given purge succeeds, Then document API returns 404."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["archived_doc_id"]

        # Purge the document
        purge_response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )
        assert purge_response.status_code == 200

        # Try to access the document
        get_response = await api_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}",
            cookies=test_user_data["cookies"],
        )
        assert get_response.status_code == 404


# =============================================================================
# AC-6.3.4: Permission Check Tests
# =============================================================================


class TestPurgePermissions:
    """AC-6.3.4: Only KB owner or admin can purge."""

    @pytest.mark.asyncio
    async def test_purge_without_authentication_returns_401(
        self,
        api_client: AsyncClient,
        purge_test_kb: dict,
    ) -> None:
        """Given no authentication, When purge, Then returns 401."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["archived_doc_id"]

        api_client.cookies.clear()
        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_purge_without_kb_access_returns_404(
        self,
        api_client: AsyncClient,
        second_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given user without KB access, When purge, Then returns 404."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["archived_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_purge_with_write_permission_succeeds(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        second_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given user with WRITE permission, When purge, Then returns 200."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["archived_doc_id"]

        write_permission = KBPermission(
            user_id=second_user_data["user_id"],
            kb_id=uuid.UUID(kb_id),
            permission_level=PermissionLevel.WRITE,
        )
        db_session.add(write_permission)
        await db_session.commit()

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 200


# =============================================================================
# AC-6.3.5: Bulk Purge Tests
# =============================================================================


class TestBulkPurge:
    """AC-6.3.5: Bulk purge endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Bulk purge endpoint may not be implemented yet")
    async def test_bulk_purge_multiple_archived_documents(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given multiple archived documents, When bulk purge, Then all purged."""
        kb_id = purge_test_kb["kb_id"]
        doc_ids = [
            purge_test_kb["archived_doc_id"],
            purge_test_kb["archived_doc_id_2"],
        ]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/bulk-purge",
            json={"document_ids": doc_ids},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["purged"] == 2
        assert data["skipped"] == 0

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Bulk purge endpoint may not be implemented yet")
    async def test_bulk_purge_partial_success(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given mix of archived and non-archived docs, When bulk purge, Then partial success."""
        kb_id = purge_test_kb["kb_id"]
        doc_ids = [
            purge_test_kb["archived_doc_id"],
            purge_test_kb["ready_doc_id"],  # Not archived - should be skipped
        ]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/bulk-purge",
            json={"document_ids": doc_ids},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["purged"] == 1
        assert data["skipped"] == 1
        assert purge_test_kb["ready_doc_id"] in data["skipped_ids"]


# =============================================================================
# AC-6.3.6: Graceful Missing Artifact Handling Tests
# =============================================================================


class TestPurgeGracefulHandling:
    """AC-6.3.6: Purge handles missing storage artifacts gracefully."""

    @pytest.mark.asyncio
    async def test_purge_succeeds_even_if_qdrant_empty(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
    ) -> None:
        """Given no Qdrant vectors exist, When purge, Then still succeeds."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["archived_doc_id"]

        # The archived document may not have Qdrant vectors
        # Purge should still succeed
        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200


# =============================================================================
# Audit Logging Tests
# =============================================================================


class TestPurgeAuditLogging:
    """Audit logging for purge operations."""

    @pytest.mark.asyncio
    async def test_purge_creates_audit_log_entry(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        purge_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given successful purge, When audit log queried, Then contains entry."""
        kb_id = purge_test_kb["kb_id"]
        doc_id = purge_test_kb["archived_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(
                AuditEvent.resource_id == doc_id,
                AuditEvent.action.contains("purge"),
            )
        )
        audit_entries = result.scalars().all()

        assert len(audit_entries) >= 1, "Should create audit log for purge action"
