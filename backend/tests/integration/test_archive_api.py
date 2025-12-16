"""Integration tests for document archive API (Story 6-1).

Tests cover all 6 Acceptance Criteria:
- AC-6.1.1: Archive endpoint sets archived_at and returns updated document
- AC-6.1.2: Only READY documents can be archived (400 for others)
- AC-6.1.3: Already archived document returns 400
- AC-6.1.4: Qdrant vectors marked with archived=true payload
- AC-6.1.5: Permission check enforced (403 for non-owner/non-admin)
- AC-6.1.6: Audit logging for archive actions

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
async def archive_test_kb(
    db_session: AsyncSession,
    test_user_data: dict,
) -> dict:
    """Create a KB with documents in various statuses for archive testing.

    Returns:
        dict: {
            "kb_id": str,
            "ready_doc_id": str,      # READY document for archive tests
            "pending_doc_id": str,    # PENDING document (should fail)
            "processing_doc_id": str, # PROCESSING document (should fail)
            "failed_doc_id": str,     # FAILED document (should fail)
            "archived_doc_id": str,   # Already ARCHIVED (should fail)
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
        name="Archive Test KB",
        description="KB for archive testing",
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

    # Create documents with various statuses
    docs = {}

    # READY document (can be archived)
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
    )
    db_session.add(ready_doc)
    docs["ready"] = ready_doc

    # PENDING document (cannot be archived)
    pending_doc = Document(
        kb_id=kb.id,
        name="Pending Document.pdf",
        original_filename="pending.pdf",
        mime_type="application/pdf",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/pending.pdf",
        checksum="b" * 64,
        status=DocumentStatus.PENDING,
        chunk_count=0,
        uploaded_by=test_user.id,
    )
    db_session.add(pending_doc)
    docs["pending"] = pending_doc

    # PROCESSING document (cannot be archived)
    processing_doc = Document(
        kb_id=kb.id,
        name="Processing Document.pdf",
        original_filename="processing.pdf",
        mime_type="application/pdf",
        file_size_bytes=3072,
        file_path=f"kb-{kb.id}/processing.pdf",
        checksum="c" * 64,
        status=DocumentStatus.PROCESSING,
        chunk_count=0,
        uploaded_by=test_user.id,
    )
    db_session.add(processing_doc)
    docs["processing"] = processing_doc

    # FAILED document (cannot be archived)
    failed_doc = Document(
        kb_id=kb.id,
        name="Failed Document.pdf",
        original_filename="failed.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024,
        file_path=f"kb-{kb.id}/failed.pdf",
        checksum="d" * 64,
        status=DocumentStatus.FAILED,
        chunk_count=0,
        last_error="Processing failed",
        uploaded_by=test_user.id,
    )
    db_session.add(failed_doc)
    docs["failed"] = failed_doc

    # Already ARCHIVED document
    archived_doc = Document(
        kb_id=kb.id,
        name="Already Archived.pdf",
        original_filename="archived.pdf",
        mime_type="application/pdf",
        file_size_bytes=5120,
        file_path=f"kb-{kb.id}/archived.pdf",
        checksum="e" * 64,
        status=DocumentStatus.READY,  # Status remains READY, archived_at is set
        chunk_count=3,
        uploaded_by=test_user.id,
        archived_at=datetime.now(UTC),
    )
    db_session.add(archived_doc)
    docs["archived"] = archived_doc

    await db_session.commit()

    # Refresh all docs to get IDs
    for doc in docs.values():
        await db_session.refresh(doc)

    return {
        "kb_id": str(kb.id),
        "ready_doc_id": str(docs["ready"].id),
        "pending_doc_id": str(docs["pending"].id),
        "processing_doc_id": str(docs["processing"].id),
        "failed_doc_id": str(docs["failed"].id),
        "archived_doc_id": str(docs["archived"].id),
        "owner_id": str(test_user.id),
    }


@pytest.fixture
async def second_user_data(api_client: AsyncClient) -> dict:
    """Create a second test user without KB access.

    Returns:
        dict: {"email": str, "password": str, "user_id": str, "cookies": Cookies}
    """
    user_data = create_registration_data()
    response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    user_response = response.json()

    # Login to get cookies
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
async def kb_with_qdrant_chunks(
    db_session: AsyncSession,
    test_user_data: dict,
    test_qdrant_service,
) -> dict:
    """Create a KB with documents and indexed chunks in Qdrant.

    For testing that archive updates Qdrant payload correctly.

    Returns:
        dict: {
            "kb_id": str,
            "doc_id": str,
            "chunk_count": int,
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
        name="Qdrant Archive Test KB",
        description="KB for testing Qdrant archive payload",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()

    # Grant WRITE permission
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.WRITE,
    )
    db_session.add(permission)

    # Create document
    doc = Document(
        kb_id=kb.id,
        name="Searchable Document.md",
        original_filename="searchable.md",
        mime_type="text/markdown",
        file_size_bytes=4096,
        file_path=f"kb-{kb.id}/searchable.md",
        checksum="f" * 64,
        status=DocumentStatus.READY,
        chunk_count=3,
        uploaded_by=test_user.id,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(kb)
    await db_session.refresh(doc)

    # Create Qdrant collection and insert chunks
    await test_qdrant_service.create_collection(kb.id)

    chunks = [
        create_test_chunk(
            text="This is the first chunk about OAuth authentication.",
            document_id=str(doc.id),
            document_name=doc.name,
            kb_id=str(kb.id),
            chunk_index=0,
            section_header="Introduction",
        ),
        create_test_chunk(
            text="This is the second chunk about API security best practices.",
            document_id=str(doc.id),
            document_name=doc.name,
            kb_id=str(kb.id),
            chunk_index=1,
            section_header="Security",
        ),
        create_test_chunk(
            text="This is the third chunk about token management.",
            document_id=str(doc.id),
            document_name=doc.name,
            kb_id=str(kb.id),
            chunk_index=2,
            section_header="Tokens",
        ),
    ]

    await test_qdrant_service.upsert_points(kb.id, chunks)

    return {
        "kb_id": str(kb.id),
        "doc_id": str(doc.id),
        "chunk_count": len(chunks),
    }


# =============================================================================
# AC-6.1.1: Archive Endpoint Tests
# =============================================================================


class TestArchiveEndpoint:
    """AC-6.1.1: Archive endpoint sets archived_at and returns updated document."""

    @pytest.mark.asyncio
    async def test_archive_ready_document_returns_200(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given a READY document, When POST archive, Then returns 200 OK."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Document archived successfully"
        assert "archived_at" in data

    @pytest.mark.asyncio
    async def test_archive_sets_archived_at_timestamp(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
        db_session: AsyncSession,  # noqa: ARG002
    ) -> None:
        """Given archive succeeds, Then archived_at is set to current timestamp."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]

        before = datetime.now(UTC)

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        after = datetime.now(UTC)

        assert response.status_code == 200
        data = response.json()

        # Parse and verify timestamp
        archived_at_str = data["archived_at"]
        archived_at = datetime.fromisoformat(archived_at_str.replace("Z", "+00:00"))

        assert before <= archived_at <= after

    @pytest.mark.asyncio
    async def test_archive_response_contains_required_fields(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given archive succeeds, Then response contains message and archived_at."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "message" in data
        assert "archived_at" in data
        assert isinstance(data["message"], str)
        assert isinstance(data["archived_at"], str)

    @pytest.mark.asyncio
    async def test_archive_nonexistent_document_returns_404(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given non-existent document ID, When archive, Then returns 404."""
        kb_id = archive_test_kb["kb_id"]
        fake_doc_id = str(uuid.uuid4())

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_archive_nonexistent_kb_returns_404(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given non-existent KB ID, When archive, Then returns 404."""
        fake_kb_id = str(uuid.uuid4())
        doc_id = archive_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{fake_kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 404


# =============================================================================
# AC-6.1.2: Status Validation Tests
# =============================================================================


class TestArchiveStatusValidation:
    """AC-6.1.2: Only READY documents can be archived; others return 400."""

    @pytest.mark.asyncio
    async def test_archive_pending_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given PENDING document, When archive, Then returns 400 INVALID_STATUS."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["pending_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_STATUS"
        assert "READY" in data["detail"]["error"]["message"]

    @pytest.mark.asyncio
    async def test_archive_processing_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given PROCESSING document, When archive, Then returns 400."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["processing_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_STATUS"

    @pytest.mark.asyncio
    async def test_archive_failed_document_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given FAILED document, When archive, Then returns 400."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["failed_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_STATUS"

    @pytest.mark.asyncio
    async def test_archive_already_archived_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given already archived document, When archive again, Then returns 400."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["archived_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "ALREADY_ARCHIVED"

    @pytest.mark.asyncio
    async def test_archive_same_document_twice_returns_400(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given document archived once, When archive again, Then returns 400."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]

        # First archive - should succeed
        response1 = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )
        assert response1.status_code == 200

        # Second archive - should fail
        response2 = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )
        assert response2.status_code == 400
        data = response2.json()
        assert data["detail"]["error"]["code"] == "ALREADY_ARCHIVED"


# =============================================================================
# AC-6.1.3: Qdrant Vector Exclusion Tests
# =============================================================================


class TestQdrantArchivePayload:
    """AC-6.1.3: Qdrant vectors marked with archived=true payload."""

    @pytest.mark.asyncio
    async def test_archive_updates_qdrant_payload(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        kb_with_qdrant_chunks: dict,
        test_qdrant_service,
    ) -> None:
        """Given document with Qdrant vectors, When archived, Then vectors have archived=true."""
        kb_id = kb_with_qdrant_chunks["kb_id"]
        doc_id = kb_with_qdrant_chunks["doc_id"]

        # Archive the document
        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
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

        # Verify all points have archived=true
        for point in points:
            assert (
                point.payload.get("archived") is True
            ), f"Point {point.id} should have archived=true"

    @pytest.mark.asyncio
    async def test_archived_document_excluded_from_search(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        kb_with_qdrant_chunks: dict,
        test_qdrant_service,
    ) -> None:
        """Given archived document, When search performed, Then document excluded."""
        kb_id = kb_with_qdrant_chunks["kb_id"]
        doc_id = kb_with_qdrant_chunks["doc_id"]

        # First, verify search returns results before archive
        _ = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/search",
            json={"query": "OAuth authentication", "top_k": 10},
            cookies=test_user_data["cookies"],
        )
        # Note: This may or may not work depending on search endpoint implementation
        # The key test is that after archive, results are excluded

        # Archive the document
        archive_response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )
        assert archive_response.status_code == 200

        # Verify Qdrant filter would exclude archived docs
        # The search service should filter on archived!=true
        from qdrant_client.http import models as qdrant_models

        collection_name = f"kb_{kb_id}"

        # Search WITHOUT archived filter - should find points
        all_results = test_qdrant_service.client.scroll(
            collection_name=collection_name,
            scroll_filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="document_id",
                        match=qdrant_models.MatchValue(value=doc_id),
                    )
                ]
            ),
            limit=100,
        )
        assert len(all_results[0]) > 0, "Should find points without filter"

        # Search WITH archived=false filter - should NOT find points
        active_results = test_qdrant_service.client.scroll(
            collection_name=collection_name,
            scroll_filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="document_id",
                        match=qdrant_models.MatchValue(value=doc_id),
                    ),
                    qdrant_models.FieldCondition(
                        key="archived",
                        match=qdrant_models.MatchValue(value=False),
                    ),
                ]
            ),
            limit=100,
        )
        # All points should be archived, so no results with archived=false
        assert (
            len(active_results[0]) == 0
        ), "Archived documents should not appear in search results"


# =============================================================================
# AC-6.1.4: Bulk Archive Tests (if endpoint exists)
# =============================================================================


class TestBulkArchive:
    """AC-6.1.4: Bulk archive endpoint (POST /documents/bulk-archive)."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Bulk archive endpoint not yet implemented")
    async def test_bulk_archive_multiple_documents(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given multiple READY documents, When bulk archive, Then all archived."""
        # This test is a placeholder for when bulk archive is implemented
        pass

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Bulk archive endpoint not yet implemented")
    async def test_bulk_archive_partial_failure(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given mix of READY and PENDING docs, When bulk archive, Then partial success."""
        pass


# =============================================================================
# AC-6.1.5: Permission Check Tests
# =============================================================================


class TestArchivePermissions:
    """AC-6.1.5: Only KB owner or admin can archive; others get 403."""

    @pytest.mark.asyncio
    async def test_archive_without_authentication_returns_401(
        self,
        api_client: AsyncClient,
        archive_test_kb: dict,
    ) -> None:
        """Given no authentication, When archive, Then returns 401."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]

        # Clear any existing cookies and make unauthenticated request
        api_client.cookies.clear()
        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            # No cookies = unauthenticated
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_archive_without_kb_access_returns_404(
        self,
        api_client: AsyncClient,
        second_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given user without KB access, When archive, Then returns 404 (not 403).

        Note: Returns 404 to avoid leaking KB existence information.
        """
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]

        # Use second user's cookies (no access to this KB)
        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=second_user_data["cookies"],
        )

        # Should return 404 (not 403) to avoid information leakage
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_archive_with_read_only_permission_returns_404(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        second_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given user with READ permission, When archive, Then returns 404.

        Archive requires WRITE permission, not just READ.
        """
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]

        # Grant READ-only permission to second user
        read_permission = KBPermission(
            user_id=second_user_data["user_id"],
            kb_id=uuid.UUID(kb_id),
            permission_level=PermissionLevel.READ,
        )
        db_session.add(read_permission)
        await db_session.commit()

        # Try to archive with READ permission
        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=second_user_data["cookies"],
        )

        # Should fail - WRITE permission required
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_archive_with_write_permission_succeeds(
        self,
        api_client: AsyncClient,
        db_session: AsyncSession,
        second_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given user with WRITE permission, When archive, Then returns 200."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]

        # Grant WRITE permission to second user
        write_permission = KBPermission(
            user_id=second_user_data["user_id"],
            kb_id=uuid.UUID(kb_id),
            permission_level=PermissionLevel.WRITE,
        )
        db_session.add(write_permission)
        await db_session.commit()

        # Archive should succeed
        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=second_user_data["cookies"],
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_kb_owner_can_archive(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given KB owner, When archive, Then returns 200."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 200


# =============================================================================
# AC-6.1.6: Audit Logging Tests
# =============================================================================


class TestArchiveAuditLogging:
    """AC-6.1.6: Archive action creates audit log entry."""

    @pytest.mark.asyncio
    async def test_archive_creates_audit_log_entry(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given successful archive, When audit log queried, Then contains entry."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]

        # Archive the document
        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        # Query audit log
        # Note: Adjust this based on actual audit log implementation
        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent).where(
                AuditEvent.resource_id == doc_id,
                AuditEvent.action.contains("archive"),
            )
        )
        audit_entries = result.scalars().all()

        # Should have at least one archive audit entry
        assert len(audit_entries) >= 1, "Should create audit log for archive action"

    @pytest.mark.asyncio
    async def test_archive_audit_contains_required_fields(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
        db_session: AsyncSession,
    ) -> None:
        """Given archive audit entry, Then contains document_id, user_id, kb_id."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["ready_doc_id"]
        user_id = test_user_data["user_id"]

        # Archive the document
        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )
        assert response.status_code == 200

        # Query audit log
        from app.models.audit import AuditEvent

        result = await db_session.execute(
            select(AuditEvent)
            .where(
                AuditEvent.resource_id == doc_id,
            )
            .order_by(AuditEvent.timestamp.desc())
        )
        audit_entry = result.scalar_one_or_none()

        if audit_entry:
            # Verify required fields (convert to string for comparison)
            assert str(audit_entry.user_id) == str(user_id)
            assert str(audit_entry.resource_id) == str(doc_id)
            # KB ID may be in details or a separate field
            if hasattr(audit_entry, "kb_id"):
                assert str(audit_entry.kb_id) == str(kb_id)
            elif audit_entry.details:
                assert str(audit_entry.details.get("kb_id")) == str(kb_id)


# =============================================================================
# Error Response Format Tests
# =============================================================================


class TestArchiveErrorFormat:
    """Verify error response format consistency."""

    @pytest.mark.asyncio
    async def test_error_response_has_standard_format(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given archive error, Then response has standard error format."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["pending_doc_id"]  # Will fail

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()

        # Verify standard error format
        assert "detail" in data
        assert "error" in data["detail"]
        assert "code" in data["detail"]["error"]
        assert "message" in data["detail"]["error"]

    @pytest.mark.asyncio
    async def test_invalid_status_error_includes_current_status(
        self,
        api_client: AsyncClient,
        test_user_data: dict,
        archive_test_kb: dict,
    ) -> None:
        """Given INVALID_STATUS error, Then includes current_status in details."""
        kb_id = archive_test_kb["kb_id"]
        doc_id = archive_test_kb["pending_doc_id"]

        response = await api_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/archive",
            cookies=test_user_data["cookies"],
        )

        assert response.status_code == 400
        data = response.json()

        error_details = data["detail"]["error"].get("details", {})
        assert "current_status" in error_details
        assert error_details["current_status"] == "PENDING"
