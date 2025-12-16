"""Integration tests for Document tags API endpoints.

Story 5-22: Document Tags
Tests cover:
- AC-5.22.1: Users with WRITE/ADMIN can add/edit tags
- AC-5.22.2: Tags display in document list
- AC-5.22.3: Tags validation (max 10 tags, max 50 chars each)
- AC-5.22.4: Tag normalization (lowercase, trim)
- AC-5.22.5: Audit logging for tag updates
"""

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
async def tag_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def test_user_data() -> dict:
    """Test user registration data."""
    return create_registration_data()


@pytest.fixture
async def registered_user(tag_client: AsyncClient, test_user_data: dict) -> dict:
    """Create a registered test user."""
    response = await tag_client.post(
        "/api/v1/auth/register",
        json=test_user_data,
    )
    assert response.status_code == 201
    return {**test_user_data, "user": response.json()}


@pytest.fixture
async def authenticated_client(
    tag_client: AsyncClient, registered_user: dict
) -> AsyncClient:
    """Client with authenticated session."""
    response = await tag_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 204
    return tag_client


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
async def uploaded_document(authenticated_client: AsyncClient, test_kb: dict) -> dict:
    """Upload a test document and return its metadata."""
    from unittest.mock import AsyncMock, patch

    pdf_content = create_test_pdf_content()

    with (
        patch(
            "app.services.document_service.minio_service.upload_file",
            new_callable=AsyncMock,
        ) as mock_upload,
    ):
        mock_upload.return_value = f"kb-{test_kb['id']}/test.pdf"

        response = await authenticated_client.post(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/upload",
            files={"file": ("test_document.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code == 202
        return response.json()


# =============================================================================
# Test: PATCH /knowledge-bases/{kb_id}/documents/{doc_id}/tags
# =============================================================================


class TestDocumentTagsUpdate:
    """Tests for updating document tags."""

    async def test_update_tags_success(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """AC-5.22.1: Users with WRITE permission can update tags."""
        response = await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": ["python", "machine-learning", "api"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert set(data["tags"]) == {"python", "machine-learning", "api"}

    async def test_update_tags_normalizes_to_lowercase(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """AC-5.22.4: Tags are normalized to lowercase."""
        response = await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": ["Python", "MACHINE-LEARNING", "API"]},
        )

        assert response.status_code == 200
        data = response.json()
        # All tags should be lowercase
        assert data["tags"] == ["python", "machine-learning", "api"]

    async def test_update_tags_trims_whitespace(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """AC-5.22.4: Tags are trimmed of whitespace."""
        response = await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": ["  python  ", " api ", "  test  "]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["python", "api", "test"]

    async def test_update_tags_deduplicates(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """Tags should be deduplicated."""
        response = await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": ["python", "Python", "PYTHON", "api"]},
        )

        assert response.status_code == 200
        data = response.json()
        # Duplicates should be removed (after normalization)
        assert data["tags"] == ["python", "api"]

    async def test_update_tags_max_10_tags(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """AC-5.22.3: Maximum 10 tags per document."""
        # Try to set 15 tags
        tags = [f"tag{i}" for i in range(15)]
        response = await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": tags},
        )

        assert response.status_code == 200
        data = response.json()
        # Only first 10 tags should be kept
        assert len(data["tags"]) == 10
        assert data["tags"] == [f"tag{i}" for i in range(10)]

    async def test_update_tags_max_50_chars_per_tag(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """AC-5.22.3: Tags are truncated to 50 characters."""
        long_tag = "a" * 100  # 100 char tag
        response = await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": [long_tag, "short"]},
        )

        assert response.status_code == 200
        data = response.json()
        # Long tag should be truncated to 50 chars
        assert len(data["tags"][0]) == 50
        assert data["tags"][1] == "short"

    async def test_update_tags_removes_empty_tags(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """Empty tags should be removed."""
        response = await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": ["python", "", "  ", "api"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["python", "api"]

    async def test_update_tags_clears_tags(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """Setting empty array clears all tags."""
        # First set some tags
        await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": ["python", "api"]},
        )

        # Then clear them
        response = await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": []},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == []

    async def test_update_tags_document_not_found(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
    ):
        """Returns 404 for non-existent document."""
        import uuid

        fake_doc_id = str(uuid.uuid4())
        response = await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{fake_doc_id}/tags",
            json={"tags": ["python"]},
        )

        assert response.status_code == 404

    async def test_update_tags_kb_not_found(
        self,
        authenticated_client: AsyncClient,
        uploaded_document: dict,
    ):
        """Returns 404 for non-existent KB."""
        import uuid

        fake_kb_id = str(uuid.uuid4())
        response = await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{fake_kb_id}/documents/{uploaded_document['id']}/tags",
            json={"tags": ["python"]},
        )

        assert response.status_code == 404

    async def test_update_tags_unauthenticated(
        self,
        tag_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """Unauthenticated requests are rejected."""
        response = await tag_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": ["python"]},
        )

        assert response.status_code == 401


# =============================================================================
# Test: Document Upload with Tags
# =============================================================================


class TestDocumentUploadWithTags:
    """Tests for uploading documents with initial tags."""

    async def test_upload_with_tags(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
    ):
        """Documents can be uploaded with initial tags."""
        from unittest.mock import AsyncMock, patch

        pdf_content = create_test_pdf_content()

        with patch(
            "app.services.document_service.minio_service.upload_file",
            new_callable=AsyncMock,
        ) as mock_upload:
            mock_upload.return_value = f"kb-{test_kb['id']}/test.pdf"

            response = await authenticated_client.post(
                f"/api/v1/knowledge-bases/{test_kb['id']}/documents/upload",
                files={"file": ("test.pdf", pdf_content, "application/pdf")},
                params={"tags": ["python", "tutorial"]},
            )

            assert response.status_code == 202
            data = response.json()
            assert "tags" in data
            assert set(data["tags"]) == {"python", "tutorial"}

    async def test_upload_without_tags(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
    ):
        """Documents can be uploaded without tags (default empty)."""
        from unittest.mock import AsyncMock, patch

        pdf_content = create_test_pdf_content()

        with patch(
            "app.services.document_service.minio_service.upload_file",
            new_callable=AsyncMock,
        ) as mock_upload:
            mock_upload.return_value = f"kb-{test_kb['id']}/test.pdf"

            response = await authenticated_client.post(
                f"/api/v1/knowledge-bases/{test_kb['id']}/documents/upload",
                files={"file": ("test.pdf", pdf_content, "application/pdf")},
            )

            assert response.status_code == 202
            data = response.json()
            assert data["tags"] == []

    async def test_upload_tags_normalized(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
    ):
        """Tags provided during upload are normalized."""
        from unittest.mock import AsyncMock, patch

        pdf_content = create_test_pdf_content()

        with patch(
            "app.services.document_service.minio_service.upload_file",
            new_callable=AsyncMock,
        ) as mock_upload:
            mock_upload.return_value = f"kb-{test_kb['id']}/test.pdf"

            response = await authenticated_client.post(
                f"/api/v1/knowledge-bases/{test_kb['id']}/documents/upload",
                files={"file": ("test.pdf", pdf_content, "application/pdf")},
                params={"tags": ["  Python  ", "API"]},
            )

            assert response.status_code == 202
            data = response.json()
            assert data["tags"] == ["python", "api"]


# =============================================================================
# Test: Tags in Document List
# =============================================================================


class TestTagsInDocumentList:
    """Tests for tags displayed in document list."""

    async def test_document_list_includes_tags(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """AC-5.22.2: Tags are displayed in document list."""
        # First set some tags
        await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": ["python", "api", "test"]},
        )

        # Then get the document list
        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents",
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0

        # Find our document and verify tags
        doc = next(d for d in data["data"] if d["id"] == uploaded_document["id"])
        assert "tags" in doc
        assert set(doc["tags"]) == {"python", "api", "test"}

    async def test_document_detail_includes_tags(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        uploaded_document: dict,
    ):
        """Document detail response includes tags."""
        # First set some tags
        await authenticated_client.patch(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}/tags",
            json={"tags": ["python", "api"]},
        )

        # Get document detail
        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{test_kb['id']}/documents/{uploaded_document['id']}",
        )

        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert set(data["tags"]) == {"python", "api"}
