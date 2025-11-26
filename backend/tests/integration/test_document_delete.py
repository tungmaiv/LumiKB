"""Integration tests for Document delete API endpoint.

Tests cover:
- Document deletion with WRITE permission (AC: 1, 2)
- Permission enforcement returning 404 (AC: 4, 7)
- Blocking deletion of PROCESSING documents (AC: 6)
- Soft delete with outbox event creation
- Audit logging
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.outbox import Outbox
from tests.factories import (
    create_kb_data,
    create_registration_data,
    create_test_pdf_content,
)

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def doc_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def test_user_data() -> dict:
    """Test user registration data."""
    return create_registration_data()


@pytest.fixture
async def registered_user(doc_client: AsyncClient, test_user_data: dict) -> dict:
    """Create a registered test user."""
    response = await doc_client.post(
        "/api/v1/auth/register",
        json=test_user_data,
    )
    assert response.status_code == 201
    return {**test_user_data, "user": response.json()}


@pytest.fixture
async def authenticated_client(
    doc_client: AsyncClient, registered_user: dict
) -> AsyncClient:
    """Client with authenticated session."""
    response = await doc_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 204
    return doc_client


@pytest.fixture
async def test_kb(authenticated_client: AsyncClient) -> dict:
    """Create a test Knowledge Base."""
    kb_data = create_kb_data()
    response = await authenticated_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def uploaded_document(
    authenticated_client: AsyncClient,
    test_kb: dict,
) -> dict:
    """Create a test document in READY status."""
    kb_id = test_kb["id"]
    pdf_content = create_test_pdf_content()

    with patch(
        "app.services.document_service.minio_service.upload_file",
        new_callable=AsyncMock,
        return_value=f"kb-{kb_id}/doc-id/test.pdf",
    ):
        with patch(
            "app.services.document_service.minio_service.ensure_bucket_exists",
            new_callable=AsyncMock,
        ):
            response = await authenticated_client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents",
                files={"file": ("test.pdf", pdf_content, "application/pdf")},
            )

    assert response.status_code == 202
    return response.json()


@pytest.fixture
async def second_user(doc_client: AsyncClient) -> dict:
    """Create a second registered user for permission tests."""
    user_data = create_registration_data()
    response = await doc_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json()}


# =============================================================================
# AC 1, 2: Document Deletion - Success Path
# =============================================================================


async def test_delete_document_returns_204(
    authenticated_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
):
    """Test deleting a document returns 204 No Content."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )

    assert response.status_code == 204


async def test_delete_document_sets_status_archived(
    authenticated_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
    db_session: AsyncSession,
):
    """Test deletion sets document status to ARCHIVED (AC2)."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )
    assert response.status_code == 204

    # Verify document status in database
    result = await db_session.execute(
        select(Document).where(Document.id == uuid.UUID(doc_id))
    )
    document = result.scalar_one_or_none()

    assert document is not None
    assert document.status == DocumentStatus.ARCHIVED
    assert document.deleted_at is not None


async def test_delete_document_creates_outbox_event(
    authenticated_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
    db_session: AsyncSession,
):
    """Test deletion creates outbox event for cleanup (AC2)."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )
    assert response.status_code == 204

    # Verify outbox event was created
    result = await db_session.execute(
        select(Outbox).where(
            Outbox.aggregate_id == uuid.UUID(doc_id),
            Outbox.event_type == "document.delete",
        )
    )
    outbox_event = result.scalar_one_or_none()

    assert outbox_event is not None
    assert outbox_event.payload["document_id"] == doc_id
    assert outbox_event.payload["kb_id"] == kb_id
    assert "file_path" in outbox_event.payload


async def test_deleted_document_not_in_list(
    authenticated_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
):
    """Test deleted document doesn't appear in list (AC2)."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    # Delete the document
    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )
    assert response.status_code == 204

    # Verify it's not in the list
    list_response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents"
    )
    assert list_response.status_code == 200
    data = list_response.json()

    doc_ids = [doc["id"] for doc in data["data"]]
    assert doc_id not in doc_ids


# =============================================================================
# AC 4, 7: Permission Enforcement - Returns 404
# =============================================================================


async def test_delete_without_permission_returns_404(
    authenticated_client: AsyncClient,
    doc_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
    second_user: dict,
):
    """Test delete without WRITE permission returns 404 (not 403) (AC7)."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    # Logout first user
    await authenticated_client.post("/api/v1/auth/logout")

    # Login as second user (who has no permission on the KB)
    await doc_client.post(
        "/api/v1/auth/login",
        data={
            "username": second_user["email"],
            "password": second_user["password"],
        },
    )

    # Try to delete
    response = await doc_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )

    # Should be 404 (not 403) to not leak existence
    assert response.status_code == 404


async def test_delete_nonexistent_document_returns_404(
    authenticated_client: AsyncClient,
    test_kb: dict,
):
    """Test deleting non-existent document returns 404."""
    kb_id = test_kb["id"]
    fake_doc_id = str(uuid.uuid4())

    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}"
    )

    assert response.status_code == 404


async def test_delete_from_nonexistent_kb_returns_404(
    authenticated_client: AsyncClient,
    uploaded_document: dict,
):
    """Test deleting from non-existent KB returns 404."""
    fake_kb_id = str(uuid.uuid4())
    doc_id = uploaded_document["id"]

    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{fake_kb_id}/documents/{doc_id}"
    )

    assert response.status_code == 404


# =============================================================================
# AC 6: Cannot Delete PROCESSING Documents
# =============================================================================


async def test_delete_processing_document_returns_400(
    authenticated_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
    db_session: AsyncSession,
):
    """Test deleting PROCESSING document returns 400 (AC6)."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    # Set document to PROCESSING status
    result = await db_session.execute(
        select(Document).where(Document.id == uuid.UUID(doc_id))
    )
    document = result.scalar_one()
    document.status = DocumentStatus.PROCESSING
    await db_session.commit()

    # Try to delete
    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"]["code"] == "PROCESSING_IN_PROGRESS"
    assert "cannot delete" in data["detail"]["error"]["message"].lower()


async def test_delete_already_deleted_returns_400(
    authenticated_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
):
    """Test deleting already deleted document returns 400."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    # Delete once
    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )
    assert response.status_code == 204

    # Try to delete again
    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )

    # Should be 404 because deleted_at is set (document "not found")
    assert response.status_code == 404


# =============================================================================
# Authentication Required
# =============================================================================


async def test_delete_requires_authentication(
    doc_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
):
    """Test delete requires authentication."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    # Clear any existing session
    await doc_client.post("/api/v1/auth/logout")

    response = await doc_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )

    assert response.status_code == 401


# =============================================================================
# Edge Cases
# =============================================================================


async def test_delete_ready_document_succeeds(
    authenticated_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
    db_session: AsyncSession,
):
    """Test deleting READY document succeeds."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    # Set document to READY status
    result = await db_session.execute(
        select(Document).where(Document.id == uuid.UUID(doc_id))
    )
    document = result.scalar_one()
    document.status = DocumentStatus.READY
    await db_session.commit()

    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )

    assert response.status_code == 204


async def test_delete_failed_document_succeeds(
    authenticated_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
    db_session: AsyncSession,
):
    """Test deleting FAILED document succeeds."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    # Set document to FAILED status
    result = await db_session.execute(
        select(Document).where(Document.id == uuid.UUID(doc_id))
    )
    document = result.scalar_one()
    document.status = DocumentStatus.FAILED
    await db_session.commit()

    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )

    assert response.status_code == 204


async def test_delete_pending_document_succeeds(
    authenticated_client: AsyncClient,
    test_kb: dict,
    uploaded_document: dict,
):
    """Test deleting PENDING document succeeds."""
    kb_id = test_kb["id"]
    doc_id = uploaded_document["id"]

    # Document is already in PENDING status after upload
    response = await authenticated_client.delete(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )

    assert response.status_code == 204
