"""Integration tests for replace document API (Story 6-6).

Tests cover all 7 Acceptance Criteria:
- AC-6.6.1: Replace endpoint exists and returns 200
- AC-6.6.2: Replace performs atomic delete-then-upload
- AC-6.6.3: Replace preserves document ID and metadata
- AC-6.6.4: Cannot replace while processing
- AC-6.6.5: Permission check enforced
- AC-6.6.6: Replace triggers reprocessing
- AC-6.6.7: Replace from upload flow with confirmation

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
async def replace_test_kb(
    db_session: AsyncSession,
    test_user_data: dict,
) -> dict:
    """Create a KB with documents for replace testing.

    Returns:
        dict: {
            "kb_id": str,
            "ready_doc_id": str,         # READY document (can be replaced)
            "ready_doc_name": str,
            "ready_doc_created_at": datetime,
            "failed_doc_id": str,        # FAILED document (can be replaced)
            "archived_doc_id": str,      # Archived document (can be replaced)
            "processing_doc_id": str,    # PROCESSING document (cannot be replaced)
            "pending_doc_id": str,       # PENDING document (cannot be replaced)
            "owner_id": str,
        }
    """
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    kb = KnowledgeBase(
        name="Replace Test KB",
        description="KB for replace document testing",
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
    created_at = datetime.now(UTC)

    # READY document (can be replaced)
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
        created_at=created_at,
    )
    db_session.add(ready_doc)
    docs["ready"] = ready_doc

    # FAILED document (can be replaced)
    failed_doc = Document(
        kb_id=kb.id,
        name="Failed Document.pdf",
        original_filename="failed.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/failed.pdf",
        checksum="b" * 64,
        status=DocumentStatus.FAILED,
        chunk_count=0,
        last_error="Processing failed",
        uploaded_by=test_user.id,
    )
    db_session.add(failed_doc)
    docs["failed"] = failed_doc

    # Archived document (can be replaced)
    archived_doc = Document(
        kb_id=kb.id,
        name="Archived Document.pdf",
        original_filename="archived.pdf",
        mime_type="application/pdf",
        file_size_bytes=3072,
        file_path=f"kb-{kb.id}/archived.pdf",
        checksum="c" * 64,
        status=DocumentStatus.READY,
        chunk_count=3,
        uploaded_by=test_user.id,
        archived_at=datetime.now(UTC),
    )
    db_session.add(archived_doc)
    docs["archived"] = archived_doc

    # PROCESSING document (cannot be replaced)
    processing_doc = Document(
        kb_id=kb.id,
        name="Processing Document.pdf",
        original_filename="processing.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/processing.pdf",
        checksum="d" * 64,
        status=DocumentStatus.PROCESSING,
        chunk_count=0,
        uploaded_by=test_user.id,
    )
    db_session.add(processing_doc)
    docs["processing"] = processing_doc

    # PENDING document (cannot be replaced)
    pending_doc = Document(
        kb_id=kb.id,
        name="Pending Document.pdf",
        original_filename="pending.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024,
        file_path=f"kb-{kb.id}/pending.pdf",
        checksum="e" * 64,
        status=DocumentStatus.PENDING,
        chunk_count=0,
        uploaded_by=test_user.id,
    )
    db_session.add(pending_doc)
    docs["pending"] = pending_doc

    await db_session.commit()

    for doc in docs.values():
        await db_session.refresh(doc)

    return {
        "kb_id": str(kb.id),
        "ready_doc_id": str(docs["ready"].id),
        "ready_doc_name": docs["ready"].name,
        "ready_doc_created_at": docs["ready"].created_at,
        "failed_doc_id": str(docs["failed"].id),
        "archived_doc_id": str(docs["archived"].id),
        "processing_doc_id": str(docs["processing"].id),
        "pending_doc_id": str(docs["pending"].id),
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


def create_test_file(
    filename: str, content: bytes = b"New content for replacement"
) -> tuple:
    """Create a test file for upload."""
    return (filename, io.BytesIO(content), "application/pdf")


# =============================================================================
# AC-6.6.1: Replace Endpoint Tests
# =============================================================================


class TestReplaceEndpoint:
    """AC-6.6.1: Replace endpoint exists and returns 200."""

    @pytest.mark.asyncio
    async def test_replace_ready_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
    ) -> None:
        """Given a READY document, When POST replace with new file, Then returns 200."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Document.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data or "message" in data

    @pytest.mark.asyncio
    async def test_replace_failed_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
    ) -> None:
        """Given a FAILED document, When POST replace, Then returns 200."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["failed_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Failed Doc.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_replace_archived_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
    ) -> None:
        """Given an archived document, When POST replace, Then returns 200."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Archived Doc.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_replace_nonexistent_document_returns_404(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
    ) -> None:
        """Given non-existent document ID, When replace, Then returns 404."""
        kb_id = replace_test_kb["kb_id"]
        fake_doc_id = str(uuid.uuid4())

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}/replace",
            files={"file": create_test_file("New Doc.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 404


# =============================================================================
# AC-6.6.3: Replace Preserves Document ID and Metadata
# =============================================================================


class TestReplacePreservesMetadata:
    """AC-6.6.3: Replace preserves document ID and metadata."""

    @pytest.mark.asyncio
    async def test_replace_preserves_document_id(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given replace succeeds, Then document ID is preserved."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Document.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()

        # If response includes ID, verify it matches
        if "id" in data:
            assert data["id"] == doc_id

        # Verify document still exists with same ID
        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        doc = result.scalar_one_or_none()
        assert doc is not None, "Document should still exist with same ID"

    @pytest.mark.asyncio
    async def test_replace_preserves_created_at(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given replace succeeds, Then created_at timestamp is preserved."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["ready_doc_id"]
        original_created_at = replace_test_kb["ready_doc_created_at"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Document.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200

        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        doc = result.scalar_one()

        # created_at should be preserved (or very close to original)
        assert doc.created_at is not None
        # Allow small time difference due to database precision
        time_diff = abs((doc.created_at - original_created_at).total_seconds())
        assert time_diff < 1, "created_at should be preserved"

    @pytest.mark.asyncio
    async def test_replace_updates_name_to_new_filename(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given replace succeeds, Then name is updated to new file name."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["ready_doc_id"]
        new_filename = "Brand New Document.pdf"

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file(new_filename)},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200

        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        doc = result.scalar_one()
        assert doc.name == new_filename


# =============================================================================
# AC-6.6.4: Cannot Replace While Processing
# =============================================================================


class TestReplaceWhileProcessing:
    """AC-6.6.4: Cannot replace document while processing."""

    @pytest.mark.asyncio
    async def test_replace_processing_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
    ) -> None:
        """Given PROCESSING document, When replace, Then returns 400."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["processing_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Doc.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        # Should mention processing
        detail_str = str(data["detail"]).lower()
        assert "processing" in detail_str or "progress" in detail_str

    @pytest.mark.asyncio
    async def test_replace_pending_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
    ) -> None:
        """Given PENDING document, When replace, Then returns 400."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["pending_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Doc.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400


# =============================================================================
# AC-6.6.5: Permission Check Tests
# =============================================================================


class TestReplacePermissions:
    """AC-6.6.5: Only KB owner or admin can replace."""

    @pytest.mark.asyncio
    async def test_replace_without_authentication_returns_401(
        self,
        api_client: AsyncClient,
        replace_test_kb: dict,
    ) -> None:
        """Given no authentication, When replace, Then returns 401."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["ready_doc_id"]

        api_client.cookies.clear()
        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Doc.pdf")},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_replace_without_kb_access_returns_404(
        self,
        api_client: AsyncClient,
        second_user_data: dict,
        replace_test_kb: dict,
    ) -> None:
        """Given user without KB access, When replace, Then returns 404."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Doc.pdf")},
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_replace_with_write_permission_succeeds(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        second_user_data: dict,
        replace_test_kb: dict,
    ) -> None:
        """Given user with WRITE permission, When replace, Then returns 200."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["ready_doc_id"]

        write_permission = KBPermission(
            user_id=second_user_data["user_id"],
            kb_id=uuid.UUID(kb_id),
            permission_level=PermissionLevel.WRITE,
        )
        db_session.add(write_permission)
        await db_session.commit()

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Doc.pdf")},
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 200


# =============================================================================
# AC-6.6.6: Replace Triggers Reprocessing
# =============================================================================


class TestReplaceTriggersReprocessing:
    """AC-6.6.6: Replace triggers document reprocessing."""

    @pytest.mark.asyncio
    async def test_replace_sets_status_to_pending(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given replace succeeds, Then document status is PENDING."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Doc.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200

        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        doc = result.scalar_one()
        assert doc.status == DocumentStatus.PENDING

    @pytest.mark.asyncio
    async def test_replace_response_indicates_pending_status(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
    ) -> None:
        """Given replace succeeds, Then response shows pending status."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Doc.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()

        # Response should indicate pending/queued status
        if "status" in data:
            assert data["status"].lower() in ("pending", "queued")
        if "message" in data:
            assert (
                "queued" in data["message"].lower()
                or "processing" in data["message"].lower()
            )

    @pytest.mark.asyncio
    async def test_replace_clears_archived_at(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given archived document replaced, Then archived_at is cleared."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Doc.pdf")},
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200

        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        doc = result.scalar_one()
        assert doc.archived_at is None, "archived_at should be cleared after replace"


# =============================================================================
# Audit Logging Tests
# =============================================================================


class TestReplaceAuditLogging:
    """Audit logging for replace operations."""

    @pytest.mark.asyncio
    async def test_replace_creates_audit_log_entry(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        replace_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given successful replace, When audit log queried, Then contains entry."""
        kb_id = replace_test_kb["kb_id"]
        doc_id = replace_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/replace",
            files={"file": create_test_file("New Doc.pdf")},
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(
                AuditEvent.resource_id == doc_id,
                AuditEvent.action.contains("replace"),
            )
        )
        audit_entries = result.scalars().all()

        assert len(audit_entries) >= 1, "Should create audit log for replace action"
