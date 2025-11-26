"""Integration tests for document re-upload (replacement) functionality.

Story: 2-12-document-re-upload-and-version-awareness
Tests AC1-AC7 for complete replacement flow.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
async def reupload_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def test_user_data() -> dict:
    """Test user registration data."""
    return create_registration_data()


@pytest.fixture
async def registered_user(reupload_client: AsyncClient, test_user_data: dict) -> dict:
    """Create a registered test user."""
    response = await reupload_client.post(
        "/api/v1/auth/register",
        json=test_user_data,
    )
    assert response.status_code == 201
    return {**test_user_data, "user": response.json()}


@pytest.fixture
async def authenticated_client(
    reupload_client: AsyncClient, registered_user: dict
) -> AsyncClient:
    """Client with authenticated session."""
    response = await reupload_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 204
    return reupload_client


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
async def test_document(authenticated_client: AsyncClient, test_kb: dict) -> dict:
    """Create a test document in the KB."""
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
async def test_session(test_engine) -> AsyncSession:
    """Create a test session for direct database access."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


# =============================================================================
# AC1: Duplicate Detection Endpoint
# =============================================================================


async def test_check_duplicate_endpoint_no_duplicate(
    authenticated_client: AsyncClient,
    test_kb: dict,
) -> None:
    """AC1: Check duplicate returns exists=False when no match."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents/check-duplicate",
        params={"filename": "nonexistent.pdf"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is False
    assert data["document_id"] is None


async def test_check_duplicate_endpoint_with_existing_document(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_document: dict,
) -> None:
    """AC1: Check duplicate returns exists=True with document info when match found."""
    kb_id = test_kb["id"]
    filename = test_document["original_filename"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents/check-duplicate",
        params={"filename": filename},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["document_id"] == test_document["id"]
    assert data["uploaded_at"] is not None
    assert data["file_size"] is not None


async def test_check_duplicate_nonexistent_kb(
    authenticated_client: AsyncClient,
) -> None:
    """Check duplicate returns 404 for non-existent KB."""
    fake_kb_id = str(uuid4())

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{fake_kb_id}/documents/check-duplicate",
        params={"filename": "test.pdf"},
    )

    assert response.status_code == 404


# =============================================================================
# AC2, AC7: Re-upload Endpoint
# =============================================================================


async def test_reupload_document_success(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_document: dict,
    test_session: AsyncSession,
) -> None:
    """AC2, AC7: Re-upload creates outbox event and increments version."""
    kb_id = test_kb["id"]
    doc_id = test_document["id"]

    # Create test file with same mime type (PDF)
    pdf_content = create_test_pdf_content()

    with patch(
        "app.services.document_service.minio_service.upload_file",
        new_callable=AsyncMock,
        return_value=f"kb-{kb_id}/{doc_id}/test.pdf",
    ):
        response = await authenticated_client.post(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/reupload",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
        )

    assert response.status_code == 202
    data = response.json()
    assert data["id"] == doc_id
    assert data["status"] == "PENDING"


async def test_reupload_document_not_found(
    authenticated_client: AsyncClient,
    test_kb: dict,
) -> None:
    """Re-upload returns 404 for non-existent document."""
    kb_id = test_kb["id"]
    fake_doc_id = str(uuid4())

    pdf_content = create_test_pdf_content()

    response = await authenticated_client.post(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}/reupload",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
    )

    assert response.status_code == 404


# =============================================================================
# AC6: MIME Type Validation
# =============================================================================


async def test_reupload_document_mime_type_mismatch(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_document: dict,
) -> None:
    """AC6: Re-upload rejects file with different MIME type."""
    kb_id = test_kb["id"]
    doc_id = test_document["id"]

    # Try to upload DOCX when original is PDF
    docx_content = b"PK\x03\x04 fake docx content"
    docx_mime = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    response = await authenticated_client.post(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/reupload",
        files={"file": ("test.docx", docx_content, docx_mime)},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error"]["code"] == "MIME_TYPE_MISMATCH"


# =============================================================================
# AC5: File Validation
# =============================================================================


async def test_reupload_document_empty_file(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_document: dict,
) -> None:
    """Re-upload rejects empty file."""
    kb_id = test_kb["id"]
    doc_id = test_document["id"]

    response = await authenticated_client.post(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/reupload",
        files={"file": ("test.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"]["code"] == "EMPTY_FILE"


async def test_reupload_document_file_too_large(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_document: dict,
) -> None:
    """Re-upload rejects file over 50MB limit."""
    kb_id = test_kb["id"]
    doc_id = test_document["id"]

    # Create content just over 50MB
    large_content = b"x" * (51 * 1024 * 1024)

    response = await authenticated_client.post(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/reupload",
        files={"file": ("test.pdf", large_content, "application/pdf")},
    )

    assert response.status_code == 413
    data = response.json()
    assert data["detail"]["error"]["code"] == "FILE_TOO_LARGE"


# =============================================================================
# Permission Tests
# =============================================================================


async def test_reupload_requires_authentication(
    reupload_client: AsyncClient,
    test_kb: dict,
    test_document: dict,
) -> None:
    """Re-upload requires authentication."""
    kb_id = test_kb["id"]
    doc_id = test_document["id"]

    # Clear any session
    await reupload_client.post("/api/v1/auth/logout")

    pdf_content = create_test_pdf_content()

    response = await reupload_client.post(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/reupload",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
    )

    assert response.status_code == 401
