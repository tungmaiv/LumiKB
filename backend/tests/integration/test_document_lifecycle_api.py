"""Integration tests for document lifecycle API (Stories 6-2 through 6-6).

Tests cover:
- Story 6-2: Restore Document API
- Story 6-3: Purge Document API
- Story 6-4: Clear Failed Document API
- Story 6-5: Duplicate Detection during Upload
- Story 6-6: Replace Document API

ATDD Checklist Reference: docs/sprint-artifacts/atdd-checklist-epic-6.md
"""

import io
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
async def lifecycle_test_kb(
    db_session: AsyncSession,
    test_user_data: dict,
    test_qdrant_service,
) -> dict:
    """Create a KB with documents in various statuses for lifecycle testing.

    Also sets up a Qdrant collection for the KB to enable restore/purge operations.

    Returns:
        dict: {
            "kb_id": str,
            "ready_doc_id": str,
            "archived_doc_id": str,
            "failed_doc_id": str,
            "processing_doc_id": str,
            "owner_id": str,
        }
    """
    from tests.helpers.qdrant_helpers import create_test_chunk

    # Get test user
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    # Create KB
    kb = KnowledgeBase(
        name="Lifecycle Test KB",
        description="KB for lifecycle testing",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()

    # Create Qdrant collection for this KB (needed for restore/purge operations)
    await test_qdrant_service.create_collection(kb.id)

    # Grant WRITE permission to owner
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.WRITE,
    )
    db_session.add(permission)

    docs = {}

    # READY document
    ready_doc = Document(
        kb_id=kb.id,
        name="Ready Document.pdf",
        original_filename="ready.pdf",
        mime_type="application/pdf",
        file_size_bytes=4096,
        file_path=f"kb-{kb.id}/ready.pdf",
        checksum="a" * 64,
        status=DocumentStatus.READY,
        chunk_count=5,
        uploaded_by=test_user.id,
        tags=["test", "ready"],
    )
    db_session.add(ready_doc)
    docs["ready"] = ready_doc

    # ARCHIVED document
    archived_doc = Document(
        kb_id=kb.id,
        name="Archived Document.pdf",
        original_filename="archived.pdf",
        mime_type="application/pdf",
        file_size_bytes=5120,
        file_path=f"kb-{kb.id}/archived.pdf",
        checksum="b" * 64,
        status=DocumentStatus.READY,
        chunk_count=3,
        uploaded_by=test_user.id,
        archived_at=datetime.now(UTC),
    )
    db_session.add(archived_doc)
    docs["archived"] = archived_doc

    # FAILED document
    failed_doc = Document(
        kb_id=kb.id,
        name="Failed Document.pdf",
        original_filename="failed.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024,
        file_path=f"kb-{kb.id}/failed.pdf",
        checksum="c" * 64,
        status=DocumentStatus.FAILED,
        chunk_count=0,
        last_error="Processing failed",
        uploaded_by=test_user.id,
    )
    db_session.add(failed_doc)
    docs["failed"] = failed_doc

    # PROCESSING document
    processing_doc = Document(
        kb_id=kb.id,
        name="Processing Document.pdf",
        original_filename="processing.pdf",
        mime_type="application/pdf",
        file_size_bytes=3072,
        file_path=f"kb-{kb.id}/processing.pdf",
        checksum="d" * 64,
        status=DocumentStatus.PROCESSING,
        chunk_count=0,
        uploaded_by=test_user.id,
    )
    db_session.add(processing_doc)
    docs["processing"] = processing_doc

    await db_session.commit()

    # Refresh all docs to get IDs
    for doc in docs.values():
        await db_session.refresh(doc)

    # Add chunks to Qdrant for READY and ARCHIVED documents
    # (needed for restore operation which updates Qdrant payload)
    chunks = []
    for doc in [docs["ready"], docs["archived"]]:
        for i in range(doc.chunk_count):
            chunks.append(
                create_test_chunk(
                    text=f"Test content for {doc.name} chunk {i}",
                    document_id=str(doc.id),
                    document_name=doc.name,
                    kb_id=str(kb.id),
                    chunk_index=i,
                    section_header=f"Section {i}",
                )
            )

    if chunks:
        await test_qdrant_service.upsert_points(kb.id, chunks)

    return {
        "kb_id": str(kb.id),
        "ready_doc_id": str(docs["ready"].id),
        "archived_doc_id": str(docs["archived"].id),
        "failed_doc_id": str(docs["failed"].id),
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
# Story 6-2: Restore Document API Tests
# =============================================================================


class TestRestoreDocumentAPI:
    """Tests for POST /documents/{doc_id}/restore endpoint (Story 6-2)."""

    @pytest.mark.asyncio
    async def test_restore_archived_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.2.1: Restore archived document returns 200 OK."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Document restored successfully"
        assert "restored_at" in data

    @pytest.mark.asyncio
    async def test_restore_non_archived_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.2.2: Restore non-archived document returns 400."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "NOT_ARCHIVED"

    @pytest.mark.asyncio
    async def test_restore_without_permission_returns_404(
        self,
        api_client: AsyncClient,
        second_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.2.3: Restore without permission returns 404."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_restore_nonexistent_document_returns_404(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.2.4: Restore non-existent document returns 404."""
        kb_id = lifecycle_test_kb["kb_id"]
        fake_doc_id = str(uuid.uuid4())

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 404


# =============================================================================
# Story 6-3: Purge Document API Tests
# =============================================================================


class TestPurgeDocumentAPI:
    """Tests for DELETE /documents/{doc_id}/purge endpoint (Story 6-3)."""

    @pytest.mark.asyncio
    async def test_purge_archived_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.3.1: Purge archived document returns 200 OK."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["archived_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Document permanently deleted"

    @pytest.mark.asyncio
    async def test_purge_non_archived_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.3.2: Purge non-archived document returns 400."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["ready_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "NOT_ARCHIVED"

    @pytest.mark.asyncio
    async def test_purge_without_permission_returns_404(
        self,
        api_client: AsyncClient,
        second_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.3.3: Purge without permission returns 404."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["archived_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 404


class TestBulkPurgeAPI:
    """Tests for POST /documents/bulk-purge endpoint (Story 6-3)."""

    @pytest.mark.asyncio
    async def test_bulk_purge_returns_counts(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.3.4: Bulk purge returns purged/skipped counts."""
        kb_id = lifecycle_test_kb["kb_id"]
        archived_id = lifecycle_test_kb["archived_doc_id"]
        ready_id = lifecycle_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/bulk-purge",
            json={"document_ids": [archived_id, ready_id]},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert "purged" in data
        assert "skipped" in data
        assert "skipped_ids" in data
        # Only archived should be purged, ready should be skipped
        assert data["purged"] == 1
        assert data["skipped"] == 1


# =============================================================================
# Story 6-4: Clear Failed Document API Tests
# =============================================================================


class TestClearFailedDocumentAPI:
    """Tests for DELETE /documents/{doc_id}/clear endpoint (Story 6-4)."""

    @pytest.mark.asyncio
    async def test_clear_failed_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.4.1: Clear failed document returns 200 OK."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["failed_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Failed document cleared successfully"

    @pytest.mark.asyncio
    async def test_clear_non_failed_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.4.2: Clear non-failed document returns 400."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["ready_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "NOT_FAILED"

    @pytest.mark.asyncio
    async def test_clear_without_permission_returns_404(
        self,
        api_client: AsyncClient,
        second_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.4.3: Clear without permission returns 404."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["failed_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 404


# =============================================================================
# Story 6-5: Duplicate Detection Tests
# =============================================================================


class TestDuplicateDetectionAPI:
    """Tests for duplicate detection during upload (Story 6-5)."""

    @pytest.mark.asyncio
    async def test_upload_duplicate_ready_returns_409(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.5.1: Upload duplicate of READY document returns 409."""
        kb_id = lifecycle_test_kb["kb_id"]

        # Upload with same filename as existing READY document
        files = {
            "file": ("ready.pdf", io.BytesIO(b"test content"), "application/pdf"),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            files=files,
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"]["code"] == "DUPLICATE_DOCUMENT"

    @pytest.mark.asyncio
    async def test_upload_duplicate_processing_returns_409(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.5.2: Upload duplicate of PROCESSING document returns 409."""
        kb_id = lifecycle_test_kb["kb_id"]

        # Upload with same filename as PROCESSING document
        files = {
            "file": (
                "processing.pdf",
                io.BytesIO(b"test content"),
                "application/pdf",
            ),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            files=files,
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"]["code"] == "DUPLICATE_PROCESSING"

    @pytest.mark.asyncio
    async def test_upload_duplicate_case_insensitive(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.5.3: Duplicate detection is case-insensitive."""
        kb_id = lifecycle_test_kb["kb_id"]

        # Upload with different case filename
        files = {
            "file": ("READY.PDF", io.BytesIO(b"test content"), "application/pdf"),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            files=files,
            cookies=test_user_data["cookies"],
        )

        # Should still detect as duplicate (case insensitive)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_upload_duplicate_failed_auto_clears(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
        db_session: AsyncSession,  # noqa: ARG002 - fixture required for test isolation
    ) -> None:
        """AC-6.5.4: Upload duplicate of FAILED document auto-clears old one."""
        kb_id = lifecycle_test_kb["kb_id"]
        failed_doc_id = lifecycle_test_kb["failed_doc_id"]

        # Upload with same filename as FAILED document
        files = {
            "file": ("failed.pdf", io.BytesIO(b"new content"), "application/pdf"),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents",
            files=files,
            cookies=test_user_data["cookies"],
        )

        # Should succeed with auto-clear
        assert response.status_code == 202
        data = response.json()
        assert data.get("auto_cleared_document_id") == failed_doc_id
        assert data.get("message") == "Previous failed upload was automatically cleared"


# =============================================================================
# Story 6-6: Replace Document API Tests
# =============================================================================


class TestReplaceDocumentAPI:
    """Tests for POST /documents/{doc_id}/replace endpoint (Story 6-6)."""

    @pytest.mark.asyncio
    async def test_replace_ready_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.6.1: Replace READY document returns 200 OK."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["ready_doc_id"]

        files = {
            "file": (
                "new_document.pdf",
                io.BytesIO(b"new content"),
                "application/pdf",
            ),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files=files,
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id  # Same ID preserved
        assert data["status"] == "PENDING"  # Reset to PENDING for reprocessing
        assert data["message"] == "Document replaced and queued for processing"

    @pytest.mark.asyncio
    async def test_replace_processing_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.6.2: Replace PROCESSING document returns 400."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["processing_doc_id"]

        files = {
            "file": (
                "new_document.pdf",
                io.BytesIO(b"new content"),
                "application/pdf",
            ),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files=files,
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "PROCESSING_IN_PROGRESS"

    @pytest.mark.asyncio
    async def test_replace_archived_document_clears_archived(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """AC-6.6.3: Replace archived document clears archived_at."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["archived_doc_id"]

        files = {
            "file": (
                "replacement.pdf",
                io.BytesIO(b"replacement content"),
                "application/pdf",
            ),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files=files,
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200

        # Verify archived_at was cleared in database
        db_session.expire_all()
        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        doc = result.scalar_one()
        assert doc.archived_at is None

    @pytest.mark.asyncio
    async def test_replace_preserves_document_id(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.6.4: Replace preserves document ID."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["ready_doc_id"]

        files = {
            "file": (
                "new_document.pdf",
                io.BytesIO(b"new content"),
                "application/pdf",
            ),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files=files,
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id

    @pytest.mark.asyncio
    async def test_replace_without_permission_returns_404(
        self,
        api_client: AsyncClient,
        second_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.6.5: Replace without permission returns 404."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["ready_doc_id"]

        files = {
            "file": (
                "new_document.pdf",
                io.BytesIO(b"new content"),
                "application/pdf",
            ),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files=files,
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_replace_nonexistent_document_returns_404(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
    ) -> None:
        """AC-6.6.6: Replace non-existent document returns 404."""
        kb_id = lifecycle_test_kb["kb_id"]
        fake_doc_id = str(uuid.uuid4())

        files = {
            "file": (
                "new_document.pdf",
                io.BytesIO(b"new content"),
                "application/pdf",
            ),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}/replace",
            files=files,
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 404


# =============================================================================
# Audit Logging Tests
# =============================================================================


class TestLifecycleAuditLogging:
    """Tests for audit logging across lifecycle operations."""

    @pytest.mark.asyncio
    async def test_restore_creates_audit_entry(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Restore action creates audit log entry."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        # Query audit log
        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(
                AuditEvent.resource_id == doc_id,
                AuditEvent.action.contains("restore"),
            )
        )
        audit_entries = result.scalars().all()
        assert len(audit_entries) >= 1

    @pytest.mark.asyncio
    async def test_purge_creates_audit_entry(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Purge action creates audit log entry."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["archived_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/purge",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        # Query audit log
        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(
                AuditEvent.resource_id == doc_id,
                AuditEvent.action.contains("purge"),
            )
        )
        audit_entries = result.scalars().all()
        assert len(audit_entries) >= 1

    @pytest.mark.asyncio
    async def test_clear_creates_audit_entry(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Clear action creates audit log entry."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["failed_doc_id"]

        response = await api_client.delete(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/clear",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        # Query audit log
        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(
                AuditEvent.resource_id == doc_id,
                AuditEvent.action.contains("clear"),
            )
        )
        audit_entries = result.scalars().all()
        assert len(audit_entries) >= 1

    @pytest.mark.asyncio
    async def test_replace_creates_audit_entry(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        lifecycle_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Replace action creates audit log entry."""
        kb_id = lifecycle_test_kb["kb_id"]
        doc_id = lifecycle_test_kb["ready_doc_id"]

        files = {
            "file": (
                "new_document.pdf",
                io.BytesIO(b"new content"),
                "application/pdf",
            ),
        }

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files=files,
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        # Query audit log
        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(
                AuditEvent.resource_id == doc_id,
                AuditEvent.action.contains("replace"),
            )
        )
        audit_entries = result.scalars().all()
        assert len(audit_entries) >= 1
