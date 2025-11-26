"""Integration tests for citation content range endpoint."""

from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.workers.parsed_content_storage import store_parsed_content
from app.workers.parsing import ParsedContent
from tests.factories import (
    create_kb_data,
    create_registration_data,
    create_test_markdown_content,
)

pytestmark = pytest.mark.integration


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
    """Create a test Knowledge Base via API (which handles permissions automatically)."""
    kb_data = create_kb_data()
    response = await authenticated_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_get_document_content_range_success(
    authenticated_client: AsyncClient,
    test_kb: dict,
):
    """Test fetching content range from a document."""
    kb_id = UUID(test_kb["id"])

    # Upload a document via API to create it in the database
    markdown_content = create_test_markdown_content()

    with patch(
        "app.services.document_service.minio_service.upload_file",
        new_callable=AsyncMock,
        return_value=f"kb-{kb_id}/doc-id/test.md",
    ):
        with patch(
            "app.services.document_service.minio_service.ensure_bucket_exists",
            new_callable=AsyncMock,
        ):
            upload_response = await authenticated_client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents",
                files={"file": ("test.md", markdown_content, "text/markdown")},
            )

    assert upload_response.status_code == 202
    doc_data = upload_response.json()
    doc_id = UUID(doc_data["id"])

    # Store parsed content directly (simulating what the worker would do)
    test_content = "The quick brown fox jumps over the lazy dog. This is a test document with sufficient content for range testing."
    parsed = ParsedContent(text=test_content, elements=[], metadata={"test": "data"})
    await store_parsed_content(kb_id, doc_id, parsed)

    # Test fetching a range
    response = await authenticated_client.get(
        f"/api/v1/documents/{doc_id}/content",
        params={"start": 4, "end": 19},  # "quick brown fox"
    )

    assert response.status_code == 200
    assert response.text == "quick brown fox"


@pytest.mark.asyncio
async def test_get_document_content_range_permissions(
    authenticated_client: AsyncClient,
    doc_client: AsyncClient,
    registered_user: dict,
):
    """Test that content range endpoint enforces permissions."""
    # Create a second user who will own a different KB
    other_user_data = create_registration_data()
    register_response = await doc_client.post(
        "/api/v1/auth/register",
        json=other_user_data,
    )
    assert register_response.status_code == 201

    # Logout first user
    await authenticated_client.post("/api/v1/auth/logout")

    # Login as second user (using the same client to maintain session overrides)
    login_response = await doc_client.post(
        "/api/v1/auth/login",
        data={
            "username": other_user_data["email"],
            "password": other_user_data["password"],
        },
    )
    assert login_response.status_code == 204

    # Create KB as second user
    other_kb_data = create_kb_data(name="Other User KB")
    kb_response = await doc_client.post(
        "/api/v1/knowledge-bases/",
        json=other_kb_data,
    )
    assert kb_response.status_code == 201
    other_kb = kb_response.json()
    other_kb_id = UUID(other_kb["id"])

    # Upload document as second user
    markdown_content = create_test_markdown_content()
    with patch(
        "app.services.document_service.minio_service.upload_file",
        new_callable=AsyncMock,
        return_value=f"kb-{other_kb_id}/doc-id/test.md",
    ):
        with patch(
            "app.services.document_service.minio_service.ensure_bucket_exists",
            new_callable=AsyncMock,
        ):
            upload_response = await doc_client.post(
                f"/api/v1/knowledge-bases/{other_kb_id}/documents",
                files={"file": ("test.md", markdown_content, "text/markdown")},
            )

    assert upload_response.status_code == 202
    doc_data = upload_response.json()
    doc_id = UUID(doc_data["id"])

    # Store parsed content
    parsed = ParsedContent(text="Secret content", elements=[], metadata={})
    await store_parsed_content(other_kb_id, doc_id, parsed)

    # Logout second user
    await doc_client.post("/api/v1/auth/logout")

    # Login back as first user
    await authenticated_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    # Try to fetch content as the first user - should return 404 (security)
    response = await authenticated_client.get(
        f"/api/v1/documents/{doc_id}/content", params={"start": 0, "end": 10}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


@pytest.mark.asyncio
async def test_get_document_content_range_invalid_range(
    authenticated_client: AsyncClient,
    test_kb: dict,
):
    """Test validation of character range parameters."""
    kb_id = UUID(test_kb["id"])

    # Upload document via API
    markdown_content = create_test_markdown_content()
    with patch(
        "app.services.document_service.minio_service.upload_file",
        new_callable=AsyncMock,
        return_value=f"kb-{kb_id}/doc-id/test.md",
    ):
        with patch(
            "app.services.document_service.minio_service.ensure_bucket_exists",
            new_callable=AsyncMock,
        ):
            upload_response = await authenticated_client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents",
                files={"file": ("test.md", markdown_content, "text/markdown")},
            )

    assert upload_response.status_code == 202
    doc_data = upload_response.json()
    doc_id = UUID(doc_data["id"])

    # Store short parsed content
    parsed = ParsedContent(text="Short content.", elements=[], metadata={})
    await store_parsed_content(kb_id, doc_id, parsed)

    # Test invalid range (beyond content length)
    response = await authenticated_client.get(
        f"/api/v1/documents/{doc_id}/content", params={"start": 0, "end": 1000}
    )

    assert response.status_code == 400
    assert "Invalid character range" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_document_content_range_start_greater_than_end(
    authenticated_client: AsyncClient,
    test_kb: dict,
):
    """Test validation when start > end."""
    kb_id = UUID(test_kb["id"])

    # Upload document via API
    markdown_content = create_test_markdown_content()
    with patch(
        "app.services.document_service.minio_service.upload_file",
        new_callable=AsyncMock,
        return_value=f"kb-{kb_id}/doc-id/test.md",
    ):
        with patch(
            "app.services.document_service.minio_service.ensure_bucket_exists",
            new_callable=AsyncMock,
        ):
            upload_response = await authenticated_client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents",
                files={"file": ("test.md", markdown_content, "text/markdown")},
            )

    assert upload_response.status_code == 202
    doc_data = upload_response.json()
    doc_id = UUID(doc_data["id"])

    # Store parsed content
    parsed = ParsedContent(text="Test content", elements=[], metadata={})
    await store_parsed_content(kb_id, doc_id, parsed)

    # Test start > end
    response = await authenticated_client.get(
        f"/api/v1/documents/{doc_id}/content", params={"start": 10, "end": 5}
    )

    assert response.status_code == 400
    assert (
        "Start position must be less than or equal to end position"
        in response.json()["detail"]
    )


@pytest.mark.asyncio
async def test_get_document_content_range_document_not_found(
    authenticated_client: AsyncClient,
):
    """Test fetching content for non-existent document."""
    response = await authenticated_client.get(
        f"/api/v1/documents/{uuid4()}/content", params={"start": 0, "end": 10}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


@pytest.mark.asyncio
async def test_get_document_content_range_no_parsed_content(
    authenticated_client: AsyncClient,
    test_kb: dict,
):
    """Test fetching content when parsed content doesn't exist."""
    kb_id = UUID(test_kb["id"])

    # Upload document via API (but don't store parsed content)
    markdown_content = create_test_markdown_content()
    with patch(
        "app.services.document_service.minio_service.upload_file",
        new_callable=AsyncMock,
        return_value=f"kb-{kb_id}/doc-id/test.md",
    ):
        with patch(
            "app.services.document_service.minio_service.ensure_bucket_exists",
            new_callable=AsyncMock,
        ):
            upload_response = await authenticated_client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents",
                files={"file": ("test.md", markdown_content, "text/markdown")},
            )

    assert upload_response.status_code == 202
    doc_data = upload_response.json()
    doc_id = UUID(doc_data["id"])

    # Try to fetch content (no parsed content stored)
    response = await authenticated_client.get(
        f"/api/v1/documents/{doc_id}/content", params={"start": 0, "end": 10}
    )

    assert response.status_code == 404
    assert "content not available" in response.json()["detail"]
