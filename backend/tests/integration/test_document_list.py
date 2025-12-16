"""Integration tests for Document list and detail API endpoints.

Tests cover:
- Document list with pagination (AC: 1, 2)
- Document list sorting (AC: 3)
- Document detail retrieval (AC: 4)
- Permission enforcement
- Filter deleted documents
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

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
async def test_documents(
    authenticated_client: AsyncClient, test_kb: dict
) -> list[dict]:
    """Create test documents via API upload."""
    kb_id = test_kb["id"]
    documents = []

    with patch(
        "app.services.document_service.minio_service.upload_file",
        new_callable=AsyncMock,
        return_value=f"kb-{kb_id}/doc/file.pdf",
    ):
        with patch(
            "app.services.document_service.minio_service.ensure_bucket_exists",
            new_callable=AsyncMock,
        ):
            for i in range(5):
                pdf_content = create_test_pdf_content()
                response = await authenticated_client.post(
                    f"/api/v1/knowledge-bases/{kb_id}/documents",
                    files={
                        "file": (
                            f"document_{i + 1:02d}.pdf",
                            pdf_content,
                            "application/pdf",
                        )
                    },
                )
                assert response.status_code == 202
                documents.append(response.json())

    return documents


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
# AC 1: Document List - Basic Response
# =============================================================================


async def test_list_documents_returns_paginated_response(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test document list returns paginated response with metadata."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents"
    )

    assert response.status_code == 200
    data = response.json()

    # Check pagination fields
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data

    # Default pagination
    assert data["page"] == 1
    assert data["limit"] == 20
    assert data["total"] == 5
    assert data["total_pages"] == 1
    assert len(data["data"]) == 5


async def test_list_documents_includes_required_fields(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test each document includes all required fields (AC1)."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents"
    )

    assert response.status_code == 200
    data = response.json()
    doc = data["data"][0]

    # Required fields
    assert "id" in doc
    assert "name" in doc
    assert "original_filename" in doc
    assert "mime_type" in doc
    assert "file_size_bytes" in doc
    assert "status" in doc
    assert "chunk_count" in doc
    assert "created_at" in doc
    assert "updated_at" in doc
    assert "uploaded_by" in doc
    assert "uploader_email" in doc


async def test_list_documents_includes_uploader_email(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
    registered_user: dict,
):
    """Test document list includes uploader email."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents"
    )

    assert response.status_code == 200
    data = response.json()
    doc = data["data"][0]

    assert doc["uploader_email"] == registered_user["email"]


# =============================================================================
# AC 2: Pagination
# =============================================================================


async def test_list_documents_custom_limit(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test custom page limit."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?limit=2"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["limit"] == 2
    assert data["total_pages"] == 3
    assert len(data["data"]) == 2


async def test_list_documents_pagination_page_2(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test pagination returns correct page."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?page=2&limit=2"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 2
    assert len(data["data"]) == 2  # 5 total, page 2 with limit 2 has 2


async def test_list_documents_limit_validation(
    authenticated_client: AsyncClient,
    test_kb: dict,
):
    """Test limit validation."""
    kb_id = test_kb["id"]

    # Limit over 100 should fail validation
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?limit=200"
    )

    assert response.status_code == 422  # Validation error


async def test_list_documents_empty_kb(
    authenticated_client: AsyncClient,
):
    """Test empty KB returns empty list."""
    # Create new KB without documents
    kb_data = create_kb_data()
    response = await authenticated_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
    )
    empty_kb = response.json()

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{empty_kb['id']}/documents"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["data"] == []
    assert data["total"] == 0
    assert data["total_pages"] == 1


# =============================================================================
# AC 3: Sorting
# =============================================================================


async def test_list_documents_sort_by_name_asc(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test sorting by name ascending."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?sort_by=name&sort_order=asc"
    )

    assert response.status_code == 200
    data = response.json()

    names = [doc["name"] for doc in data["data"]]
    assert names == sorted(names)


async def test_list_documents_sort_by_name_desc(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test sorting by name descending."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?sort_by=name&sort_order=desc"
    )

    assert response.status_code == 200
    data = response.json()

    names = [doc["name"] for doc in data["data"]]
    assert names == sorted(names, reverse=True)


async def test_list_documents_sort_by_created_at_desc(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test sorting by date (default: newest first)."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?sort_by=created_at&sort_order=desc"
    )

    assert response.status_code == 200
    data = response.json()

    dates = [doc["created_at"] for doc in data["data"]]
    assert dates == sorted(dates, reverse=True)


async def test_list_documents_sort_by_file_size(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test sorting by file size."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?sort_by=file_size_bytes&sort_order=desc"
    )

    assert response.status_code == 200
    data = response.json()

    sizes = [doc["file_size_bytes"] for doc in data["data"]]
    assert sizes == sorted(sizes, reverse=True)


async def test_list_documents_default_sort(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test default sort is created_at descending."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents"
    )

    assert response.status_code == 200
    data = response.json()

    dates = [doc["created_at"] for doc in data["data"]]
    assert dates == sorted(dates, reverse=True)


# =============================================================================
# AC 4: Document Detail
# =============================================================================


async def test_get_document_returns_full_metadata(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test get document returns all metadata fields."""
    kb_id = test_kb["id"]
    doc_id = test_documents[0]["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )

    assert response.status_code == 200
    data = response.json()

    # All required fields
    assert data["id"] == doc_id
    assert data["kb_id"] == kb_id
    assert "name" in data
    assert "original_filename" in data
    assert "mime_type" in data
    assert "file_size_bytes" in data
    assert "file_path" in data
    assert "checksum" in data
    assert "status" in data
    assert "chunk_count" in data
    assert "processing_started_at" in data
    assert "processing_completed_at" in data
    assert "last_error" in data
    assert "retry_count" in data
    assert "uploaded_by" in data
    assert "uploader_email" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_get_document_includes_uploader_email(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
    registered_user: dict,
):
    """Test get document includes uploader email from join."""
    kb_id = test_kb["id"]
    doc_id = test_documents[0]["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["uploader_email"] == registered_user["email"]


async def test_get_document_not_found(
    authenticated_client: AsyncClient,
    test_kb: dict,
):
    """Test get non-existent document returns 404."""
    kb_id = test_kb["id"]
    fake_doc_id = str(uuid.uuid4())

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}"
    )

    assert response.status_code == 404


async def test_get_document_wrong_kb_returns_404(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents: list[dict],
):
    """Test get document from wrong KB returns 404."""
    # Create another KB
    kb_data = create_kb_data()
    response = await authenticated_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
    )
    other_kb = response.json()

    # Try to get document from original KB using other KB ID
    doc_id = test_documents[0]["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{other_kb['id']}/documents/{doc_id}"
    )

    assert response.status_code == 404


# =============================================================================
# Permission Tests
# =============================================================================


async def test_list_documents_requires_auth(
    doc_client: AsyncClient,
    test_kb: dict,
):
    """Test list documents requires authentication."""
    kb_id = test_kb["id"]

    # Ensure logged out
    await doc_client.post("/api/v1/auth/logout")

    response = await doc_client.get(f"/api/v1/knowledge-bases/{kb_id}/documents")

    assert response.status_code == 401


async def test_list_documents_requires_kb_permission(
    authenticated_client: AsyncClient,
    doc_client: AsyncClient,
    test_kb: dict,
    second_user: dict,
):
    """Test list documents requires READ permission on KB."""
    kb_id = test_kb["id"]

    # Logout first user
    await authenticated_client.post("/api/v1/auth/logout")

    # Login as second user
    await doc_client.post(
        "/api/v1/auth/login",
        data={
            "username": second_user["email"],
            "password": second_user["password"],
        },
    )

    response = await doc_client.get(f"/api/v1/knowledge-bases/{kb_id}/documents")

    assert response.status_code == 404


async def test_get_document_requires_auth(
    doc_client: AsyncClient,
    test_kb: dict,
):
    """Test get document requires authentication."""
    kb_id = test_kb["id"]
    fake_doc_id = str(uuid.uuid4())

    # Ensure logged out
    await doc_client.post("/api/v1/auth/logout")

    response = await doc_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}"
    )

    assert response.status_code == 401


async def test_list_documents_nonexistent_kb_returns_404(
    authenticated_client: AsyncClient,
):
    """Test list documents for non-existent KB returns 404."""
    fake_kb_id = str(uuid.uuid4())

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{fake_kb_id}/documents"
    )

    assert response.status_code == 404


# =============================================================================
# Story 5-24: Document Filtering Tests
# =============================================================================


@pytest.fixture
async def test_documents_with_tags(
    authenticated_client: AsyncClient, test_kb: dict
) -> list[dict]:
    """Create test documents with different tags for filtering tests."""
    kb_id = test_kb["id"]
    documents = []
    doc_configs = [
        {"filename": "report_2024.pdf", "tags": ["report", "2024", "finance"]},
        {"filename": "report_2023.pdf", "tags": ["report", "2023", "finance"]},
        {"filename": "invoice_001.pdf", "tags": ["invoice", "billing"]},
        {"filename": "contract_abc.pdf", "tags": ["contract", "legal"]},
        {"filename": "notes.md", "tags": []},
    ]

    with patch(
        "app.services.document_service.minio_service.upload_file",
        new_callable=AsyncMock,
        return_value=f"kb-{kb_id}/doc/file.pdf",
    ):
        with patch(
            "app.services.document_service.minio_service.ensure_bucket_exists",
            new_callable=AsyncMock,
        ):
            for config in doc_configs:
                pdf_content = create_test_pdf_content()
                # Use a different extension for markdown
                mime_type = (
                    "text/markdown"
                    if config["filename"].endswith(".md")
                    else "application/pdf"
                )
                response = await authenticated_client.post(
                    f"/api/v1/knowledge-bases/{kb_id}/documents",
                    files={
                        "file": (
                            config["filename"],
                            pdf_content,
                            mime_type,
                        )
                    },
                )
                assert response.status_code == 202
                doc = response.json()

                # Update tags for this document
                if config["tags"]:
                    tag_response = await authenticated_client.patch(
                        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc['id']}/tags",
                        json={"tags": config["tags"]},
                    )
                    assert tag_response.status_code == 200
                    doc["tags"] = config["tags"]

                documents.append(doc)

    return documents


async def test_filter_documents_by_search(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test filtering documents by search string (Story 5-24 AC-5.24.1)."""
    kb_id = test_kb["id"]

    # Search by filename
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?search=report"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert len(data["data"]) == 2
    for doc in data["data"]:
        assert (
            "report" in doc["name"].lower()
            or "report" in doc["original_filename"].lower()
        )


async def test_filter_documents_by_search_case_insensitive(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test search filter is case-insensitive."""
    kb_id = test_kb["id"]

    # Search with uppercase
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?search=REPORT"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2


async def test_filter_documents_by_status(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test filtering documents by status (Story 5-24 AC-5.24.1)."""
    kb_id = test_kb["id"]

    # Filter by PENDING status (all test docs should be PENDING)
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?status=PENDING"
    )

    assert response.status_code == 200
    data = response.json()

    # All test documents should be PENDING
    assert data["total"] == 5
    for doc in data["data"]:
        assert doc["status"] == "PENDING"


async def test_filter_documents_by_status_no_results(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test filtering documents by status with no matches."""
    kb_id = test_kb["id"]

    # Filter by READY status (none should be ready yet)
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?status=READY"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert data["data"] == []


async def test_filter_documents_by_mime_type(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test filtering documents by MIME type (Story 5-24 AC-5.24.1)."""
    kb_id = test_kb["id"]

    # Filter by PDF
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?mime_type=application/pdf"
    )

    assert response.status_code == 200
    data = response.json()

    # All PDFs should be returned
    assert data["total"] == 4
    for doc in data["data"]:
        assert doc["mime_type"] == "application/pdf"


async def test_filter_documents_by_tags_single(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test filtering documents by a single tag (Story 5-24 AC-5.24.1)."""
    kb_id = test_kb["id"]

    # Filter by 'report' tag
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?tags=report"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    for doc in data["data"]:
        assert "report" in doc["tags"]


async def test_filter_documents_by_tags_multiple(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test filtering documents by multiple tags (AND logic)."""
    kb_id = test_kb["id"]

    # Filter by 'report' AND 'finance' tags
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?tags=report&tags=finance"
    )

    assert response.status_code == 200
    data = response.json()

    # Only documents with BOTH tags
    assert data["total"] == 2
    for doc in data["data"]:
        assert "report" in doc["tags"]
        assert "finance" in doc["tags"]


async def test_filter_documents_by_tags_specific_year(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test filtering documents by specific year tag."""
    kb_id = test_kb["id"]

    # Filter by '2024' tag
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?tags=2024"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert "2024" in data["data"][0]["tags"]


async def test_filter_documents_combined_filters(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test combining multiple filter parameters (Story 5-24 AC-5.24.1)."""
    kb_id = test_kb["id"]

    # Filter by search, mime_type, and tags
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?"
        "search=report&mime_type=application/pdf&tags=finance"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    for doc in data["data"]:
        assert "report" in doc["original_filename"].lower()
        assert doc["mime_type"] == "application/pdf"
        assert "finance" in doc["tags"]


async def test_filter_documents_with_pagination(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test filtering works with pagination (Story 5-24 AC-5.24.2)."""
    kb_id = test_kb["id"]

    # Filter by PDF with pagination
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?"
        "mime_type=application/pdf&page=1&limit=2"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 4
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total_pages"] == 2
    assert len(data["data"]) == 2


async def test_filter_documents_with_sort(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test filtering works with sorting (Story 5-24 AC-5.24.2)."""
    kb_id = test_kb["id"]

    # Filter by PDF with sorting by name
    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?"
        "mime_type=application/pdf&sort_by=name&sort_order=asc"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 4
    names = [doc["name"] for doc in data["data"]]
    assert names == sorted(names)


async def test_filter_documents_no_matching_search(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_documents_with_tags: list[dict],
):
    """Test filter returns empty for no matching search."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?search=nonexistent"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert data["data"] == []


async def test_filter_documents_invalid_status(
    authenticated_client: AsyncClient,
    test_kb: dict,
):
    """Test filter with invalid status returns validation error."""
    kb_id = test_kb["id"]

    response = await authenticated_client.get(
        f"/api/v1/knowledge-bases/{kb_id}/documents?status=INVALID"
    )

    assert response.status_code == 422  # Validation error
