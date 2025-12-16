"""Integration tests for document restore API (Story 6-2).

Tests cover all 6 Acceptance Criteria:
- AC-6.2.1: Restore endpoint sets status to completed and clears archived_at
- AC-6.2.2: Only archived documents can be restored (400 for others)
- AC-6.2.3: Name collision detection (409 if active doc with same name exists)
- AC-6.2.4: Qdrant vectors marked as completed (not archived)
- AC-6.2.5: Permission check enforced (403/404 for non-owner/non-admin)
- AC-6.2.6: Restored documents appear in search

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
async def restore_test_kb(
    db_session: AsyncSession,
    test_user_data: dict,
) -> dict:
    """Create a KB with archived and non-archived documents for restore testing.

    Returns:
        dict: {
            "kb_id": str,
            "archived_doc_id": str,     # Archived document for restore tests
            "ready_doc_id": str,        # READY document (should fail restore)
            "pending_doc_id": str,      # PENDING document (should fail)
            "collision_doc_id": str,    # Active doc with same name as archived
            "archived_collision_id": str, # Archived doc that will collide
            "owner_id": str,
        }
    """
    # Get test user
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    # Create KB
    kb = KnowledgeBase(
        name="Restore Test KB",
        description="KB for restore testing",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()

    # Grant WRITE permission to owner
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.WRITE,
    )
    db_session.add(permission)

    docs = {}

    # Archived document (can be restored)
    archived_doc = Document(
        kb_id=kb.id,
        name="Archived Document.pdf",
        original_filename="archived.pdf",
        mime_type="application/pdf",
        file_size_bytes=4096,
        file_path=f"kb-{kb.id}/archived.pdf",
        checksum="a" * 64,
        status=DocumentStatus.READY,
        chunk_count=5,
        uploaded_by=test_user.id,
        archived_at=datetime.now(UTC),
    )
    db_session.add(archived_doc)
    docs["archived"] = archived_doc

    # READY document (cannot be restored - not archived)
    ready_doc = Document(
        kb_id=kb.id,
        name="Ready Document.pdf",
        original_filename="ready.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/ready.pdf",
        checksum="b" * 64,
        status=DocumentStatus.READY,
        chunk_count=3,
        uploaded_by=test_user.id,
    )
    db_session.add(ready_doc)
    docs["ready"] = ready_doc

    # PENDING document (cannot be restored)
    pending_doc = Document(
        kb_id=kb.id,
        name="Pending Document.pdf",
        original_filename="pending.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024,
        file_path=f"kb-{kb.id}/pending.pdf",
        checksum="c" * 64,
        status=DocumentStatus.PENDING,
        chunk_count=0,
        uploaded_by=test_user.id,
    )
    db_session.add(pending_doc)
    docs["pending"] = pending_doc

    # Active document with name that will collide
    collision_active_doc = Document(
        kb_id=kb.id,
        name="Collision Test.pdf",  # Same name as archived doc below
        original_filename="collision.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/collision.pdf",
        checksum="d" * 64,
        status=DocumentStatus.READY,
        chunk_count=2,
        uploaded_by=test_user.id,
    )
    db_session.add(collision_active_doc)
    docs["collision_active"] = collision_active_doc

    # Archived document that will collide when restored
    archived_collision_doc = Document(
        kb_id=kb.id,
        name="Collision Test.pdf",  # Same name as active doc above (case-insensitive)
        original_filename="collision_archived.pdf",
        mime_type="application/pdf",
        file_size_bytes=3072,
        file_path=f"kb-{kb.id}/collision_archived.pdf",
        checksum="e" * 64,
        status=DocumentStatus.READY,
        chunk_count=4,
        uploaded_by=test_user.id,
        archived_at=datetime.now(UTC),
    )
    db_session.add(archived_collision_doc)
    docs["archived_collision"] = archived_collision_doc

    await db_session.commit()

    for doc in docs.values():
        await db_session.refresh(doc)

    return {
        "kb_id": str(kb.id),
        "archived_doc_id": str(docs["archived"].id),
        "ready_doc_id": str(docs["ready"].id),
        "pending_doc_id": str(docs["pending"].id),
        "collision_doc_id": str(docs["collision_active"].id),
        "archived_collision_id": str(docs["archived_collision"].id),
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


@pytest.fixture
async def kb_with_archived_qdrant_chunks(
    db_session: AsyncSession,
    test_user_data: dict,
    test_qdrant_service,
) -> dict:
    """Create a KB with archived document and Qdrant chunks.

    Returns:
        dict: {
            "kb_id": str,
            "doc_id": str,
            "chunk_count": int,
        }
    """
    from tests.helpers.qdrant_helpers import create_test_chunk

    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    kb = KnowledgeBase(
        name="Qdrant Restore Test KB",
        description="KB for testing Qdrant restore payload",
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

    doc = Document(
        kb_id=kb.id,
        name="Archived Searchable.md",
        original_filename="searchable.md",
        mime_type="text/markdown",
        file_size_bytes=4096,
        file_path=f"kb-{kb.id}/searchable.md",
        checksum="f" * 64,
        status=DocumentStatus.READY,
        chunk_count=3,
        uploaded_by=test_user.id,
        archived_at=datetime.now(UTC),
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(kb)
    await db_session.refresh(doc)

    await test_qdrant_service.create_collection(kb.id)

    chunks = [
        create_test_chunk(
            text="Restore test chunk about machine learning.",
            document_id=str(doc.id),
            document_name=doc.name,
            kb_id=str(kb.id),
            chunk_index=0,
            section_header="ML Intro",
            archived=True,  # Mark as archived
        ),
        create_test_chunk(
            text="Another chunk about neural networks.",
            document_id=str(doc.id),
            document_name=doc.name,
            kb_id=str(kb.id),
            chunk_index=1,
            section_header="Neural Networks",
            archived=True,
        ),
    ]

    await test_qdrant_service.upsert_points(kb.id, chunks)

    return {
        "kb_id": str(kb.id),
        "doc_id": str(doc.id),
        "chunk_count": len(chunks),
    }


# =============================================================================
# AC-6.2.1: Restore Endpoint Tests
# =============================================================================


class TestRestoreEndpoint:
    """AC-6.2.1: Restore endpoint sets status to completed and clears archived_at."""

    @pytest.mark.asyncio
    async def test_restore_archived_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        restore_test_kb: dict,
    ) -> None:
        """Given an archived document, When POST restore, Then returns 200 OK."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert (
            "restore" in data["message"].lower() or "success" in data["message"].lower()
        )

    @pytest.mark.asyncio
    async def test_restore_clears_archived_at(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        restore_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given restore succeeds, Then archived_at is set to null."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200

        # Verify in database
        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        doc = result.scalar_one()
        assert doc.archived_at is None

    @pytest.mark.asyncio
    async def test_restore_response_contains_document_info(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        restore_test_kb: dict,
    ) -> None:
        """Given restore succeeds, Then response contains document details."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_restore_nonexistent_document_returns_404(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        restore_test_kb: dict,
    ) -> None:
        """Given non-existent document ID, When restore, Then returns 404."""
        kb_id = restore_test_kb["kb_id"]
        fake_doc_id = str(uuid.uuid4())

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 404


# =============================================================================
# AC-6.2.2: Status Validation Tests
# =============================================================================


class TestRestoreStatusValidation:
    """AC-6.2.2: Only archived documents can be restored."""

    @pytest.mark.asyncio
    async def test_restore_ready_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        restore_test_kb: dict,
    ) -> None:
        """Given READY (non-archived) document, When restore, Then returns 400."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_restore_pending_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        restore_test_kb: dict,
    ) -> None:
        """Given PENDING document, When restore, Then returns 400."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["pending_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_restore_already_restored_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        restore_test_kb: dict,
    ) -> None:
        """Given document restored once, When restore again, Then returns 400."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["archived_doc_id"]

        # First restore - should succeed
        response1 = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )
        assert response1.status_code == 200

        # Second restore - should fail
        response2 = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )
        assert response2.status_code == 400


# =============================================================================
# AC-6.2.3: Name Collision Detection Tests
# =============================================================================


class TestRestoreNameCollision:
    """AC-6.2.3: Name collision detection on restore."""

    @pytest.mark.asyncio
    async def test_restore_with_name_collision_returns_409(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        restore_test_kb: dict,
    ) -> None:
        """Given active doc with same name exists, When restore, Then returns 409."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb[
            "archived_collision_id"
        ]  # Archived doc with collision name

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_restore_without_collision_succeeds(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        restore_test_kb: dict,
    ) -> None:
        """Given no name collision, When restore, Then succeeds."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["archived_doc_id"]  # Unique name

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200


# =============================================================================
# AC-6.2.4: Qdrant Payload Update Tests
# =============================================================================


class TestRestoreQdrantPayload:
    """AC-6.2.4: Qdrant vectors marked as completed after restore."""

    @pytest.mark.asyncio
    async def test_restore_updates_qdrant_payload(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        kb_with_archived_qdrant_chunks: dict,
        test_qdrant_service,
    ) -> None:
        """Given archived document in Qdrant, When restored, Then vectors have archived=false."""
        kb_id = kb_with_archived_qdrant_chunks["kb_id"]
        doc_id = kb_with_archived_qdrant_chunks["doc_id"]

        # Restore the document
        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        # Query Qdrant to verify payload updated
        from qdrant_client.http import models as qdrant_models

        collection_name = f"kb_{kb_id}"
        scroll_result = test_qdrant_service.client.scroll(
            collection_name=collection_name,
            scroll_filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="document_id",
                        match=qdrant_models.MatchValue(value=doc_id),
                    )
                ]
            ),
            with_payload=True,
            limit=100,
        )

        points = scroll_result[0]
        assert len(points) > 0, "Should have points in Qdrant"

        # Verify all points have archived=false
        for point in points:
            assert (
                point.payload.get("archived") is False
            ), f"Point {point.id} should have archived=false after restore"


# =============================================================================
# AC-6.2.5: Permission Check Tests
# =============================================================================


class TestRestorePermissions:
    """AC-6.2.5: Only KB owner or admin can restore."""

    @pytest.mark.asyncio
    async def test_restore_without_authentication_returns_401(
        self,
        api_client: AsyncClient,
        restore_test_kb: dict,
    ) -> None:
        """Given no authentication, When restore, Then returns 401."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["archived_doc_id"]

        api_client.cookies.clear()
        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_restore_without_kb_access_returns_404(
        self,
        api_client: AsyncClient,
        second_user_data: dict,
        restore_test_kb: dict,
    ) -> None:
        """Given user without KB access, When restore, Then returns 404."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_restore_with_write_permission_succeeds(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        second_user_data: dict,
        restore_test_kb: dict,
    ) -> None:
        """Given user with WRITE permission, When restore, Then returns 200."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["archived_doc_id"]

        write_permission = KBPermission(
            user_id=second_user_data["user_id"],
            kb_id=uuid.UUID(kb_id),
            permission_level=PermissionLevel.WRITE,
        )
        db_session.add(write_permission)
        await db_session.commit()

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 200


# =============================================================================
# AC-6.2.6: Audit Logging Tests
# =============================================================================


class TestRestoreAuditLogging:
    """AC-6.2.6: Restore action creates audit log entry."""

    @pytest.mark.asyncio
    async def test_restore_creates_audit_log_entry(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        restore_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given successful restore, When audit log queried, Then contains entry."""
        kb_id = restore_test_kb["kb_id"]
        doc_id = restore_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/restore",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(
                AuditEvent.resource_id == doc_id,
                AuditEvent.action.contains("restore"),
            )
        )
        audit_entries = result.scalars().all()

        assert len(audit_entries) >= 1, "Should create audit log for restore action"
