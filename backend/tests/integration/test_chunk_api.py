"""Integration tests for Document Chunk API endpoints (Story 5-25).

Tests cover:
- GET /knowledge-bases/{kb_id}/documents/{doc_id}/chunks (AC-5.25.1, AC-5.25.2, AC-5.25.3)
- GET /knowledge-bases/{kb_id}/documents/{doc_id}/full-content (AC-5.25.4)
- Permission enforcement
- Pagination and search functionality
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from tests.factories import (
    create_kb_data,
    create_registration_data,
    create_test_pdf_content,
)
from tests.helpers.qdrant_helpers import insert_test_chunks

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def chunk_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def test_user_data() -> dict:
    """Test user registration data."""
    return create_registration_data()


@pytest.fixture
async def registered_user(chunk_client: AsyncClient, test_user_data: dict) -> dict:
    """Create a registered test user."""
    response = await chunk_client.post(
        "/api/v1/auth/register",
        json=test_user_data,
    )
    assert response.status_code == 201
    return {**test_user_data, "user": response.json()}


@pytest.fixture
async def authenticated_client(
    chunk_client: AsyncClient, registered_user: dict
) -> AsyncClient:
    """Client with authenticated session."""
    response = await chunk_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 204
    return chunk_client


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
    """Create a test document via API upload."""
    kb_id = test_kb["id"]

    with patch(
        "app.services.document_service.minio_service.upload_file",
        new_callable=AsyncMock,
        return_value=f"kb-{kb_id}/doc/file.pdf",
    ):
        with patch(
            "app.services.document_service.minio_service.ensure_bucket_exists",
            new_callable=AsyncMock,
        ):
            pdf_content = create_test_pdf_content()
            files = {"file": ("test-doc.pdf", pdf_content, "application/pdf")}
            response = await authenticated_client.post(
                f"/api/v1/knowledge-bases/{kb_id}/documents/upload",
                files=files,
            )
            assert response.status_code == 201
            return response.json()


@pytest.fixture
async def test_document_with_chunks(
    authenticated_client: AsyncClient,
    test_kb: dict,
    test_document: dict,
    test_qdrant_service,
) -> dict:
    """Create document with chunks in Qdrant."""
    kb_id = uuid.UUID(test_kb["id"])
    doc_id = test_document["id"]

    # Insert test chunks into Qdrant
    chunks_data = [
        {
            "text": "This is the first chunk with important content about authentication.",
            "document_id": doc_id,
            "document_name": test_document["name"],
            "chunk_index": 0,
            "char_start": 0,
            "char_end": 72,
            "page_number": 1,
            "section_header": "Introduction",
        },
        {
            "text": "The second chunk discusses OAuth 2.0 implementation details.",
            "document_id": doc_id,
            "document_name": test_document["name"],
            "chunk_index": 1,
            "char_start": 73,
            "char_end": 133,
            "page_number": 1,
            "section_header": "OAuth Section",
        },
        {
            "text": "Third chunk covers security best practices for API design.",
            "document_id": doc_id,
            "document_name": test_document["name"],
            "chunk_index": 2,
            "char_start": 134,
            "char_end": 192,
            "page_number": 2,
            "section_header": "Security",
        },
        {
            "text": "Fourth chunk explains token refresh mechanisms and session handling.",
            "document_id": doc_id,
            "document_name": test_document["name"],
            "chunk_index": 3,
            "char_start": 193,
            "char_end": 261,
            "page_number": 2,
            "section_header": "Sessions",
        },
        {
            "text": "Fifth and final chunk summarizes the key takeaways.",
            "document_id": doc_id,
            "document_name": test_document["name"],
            "chunk_index": 4,
            "char_start": 262,
            "char_end": 312,
            "page_number": 3,
            "section_header": "Summary",
        },
    ]

    await insert_test_chunks(kb_id, chunks_data)

    return {
        **test_document,
        "chunk_count": len(chunks_data),
        "chunks_data": chunks_data,
    }


# =============================================================================
# Test GET /documents/{id}/chunks - Pagination (AC-5.25.1, AC-5.25.2)
# =============================================================================


class TestGetDocumentChunks:
    """Tests for GET /knowledge-bases/{kb_id}/documents/{doc_id}/chunks endpoint."""

    async def test_get_chunks_returns_all_fields(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document_with_chunks: dict,
    ):
        """AC-5.25.1: Response includes chunk_id, chunk_index, text, char_start, char_end, page_number, section_header."""
        kb_id = test_kb["id"]
        doc_id = test_document_with_chunks["id"]

        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/chunks"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "chunks" in data
        assert "total" in data
        assert "has_more" in data
        assert "next_cursor" in data

        # Verify chunk fields (AC-5.25.1)
        assert len(data["chunks"]) > 0
        chunk = data["chunks"][0]
        assert "chunk_id" in chunk
        assert "chunk_index" in chunk
        assert "text" in chunk
        assert "char_start" in chunk
        assert "char_end" in chunk
        assert "page_number" in chunk
        assert "section_header" in chunk

    async def test_get_chunks_pagination_cursor(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document_with_chunks: dict,
    ):
        """AC-5.25.2: Cursor-based pagination using chunk_index."""
        kb_id = test_kb["id"]
        doc_id = test_document_with_chunks["id"]

        # Request first 2 chunks
        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/chunks",
            params={"cursor": 0, "limit": 2},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["chunks"]) == 2
        assert data["has_more"] is True
        assert data["next_cursor"] == 2

        # Request next page using cursor
        response2 = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/chunks",
            params={"cursor": data["next_cursor"], "limit": 2},
        )

        assert response2.status_code == 200
        data2 = response2.json()

        # Should get different chunks
        assert data2["chunks"][0]["chunk_index"] >= 2

    async def test_get_chunks_limit_clamped(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document_with_chunks: dict,
    ):
        """Test limit is clamped to max 100."""
        kb_id = test_kb["id"]
        doc_id = test_document_with_chunks["id"]

        # Request more than max limit
        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/chunks",
            params={"limit": 200},
        )

        # Should still succeed (limit clamped internally)
        assert response.status_code == 200

    async def test_get_chunks_empty_document(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document: dict,
        test_qdrant_service,
    ):
        """Test empty response for document with no chunks."""
        kb_id = test_kb["id"]
        doc_id = test_document["id"]

        # Ensure collection exists but is empty for this document
        await test_qdrant_service.create_collection(uuid.UUID(kb_id))

        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/chunks"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chunks"] == []
        assert data["total"] == 0
        assert data["has_more"] is False
        assert data["next_cursor"] is None


# =============================================================================
# Test GET /documents/{id}/chunks - Search (AC-5.25.3)
# =============================================================================


class TestGetDocumentChunksSearch:
    """Tests for search functionality in chunks endpoint."""

    async def test_get_chunks_with_search_query(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document_with_chunks: dict,
    ):
        """AC-5.25.3: Search with query returns scored results."""
        kb_id = test_kb["id"]
        doc_id = test_document_with_chunks["id"]

        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/chunks",
            params={"search": "OAuth authentication"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return chunks with scores
        assert len(data["chunks"]) > 0
        # Search results have scores
        for chunk in data["chunks"]:
            assert "score" in chunk
            # Note: score may be None or float depending on implementation

    async def test_get_chunks_search_pagination(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document_with_chunks: dict,
    ):
        """Test search with pagination."""
        kb_id = test_kb["id"]
        doc_id = test_document_with_chunks["id"]

        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/chunks",
            params={"search": "security", "limit": 2},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["chunks"]) <= 2


# =============================================================================
# Test GET /documents/{id}/full-content (AC-5.25.4)
# =============================================================================


class TestGetDocumentContent:
    """Tests for GET /knowledge-bases/{kb_id}/documents/{doc_id}/full-content endpoint."""

    async def test_get_content_pdf(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document: dict,
    ):
        """AC-5.25.4: Content endpoint returns text and mime_type."""
        kb_id = test_kb["id"]
        doc_id = test_document["id"]

        # Mock MinIO download
        with patch(
            "app.api.v1.documents.minio_client.download_file",
            new_callable=AsyncMock,
            return_value=b"%PDF-1.4 Sample PDF content",
        ):
            # Mock document having parsed text
            with patch(
                "app.services.document_service.document_service.get_document_text",
                new_callable=AsyncMock,
                return_value="This is the extracted text from the PDF document.",
            ):
                response = await authenticated_client.get(
                    f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/full-content"
                )

        assert response.status_code == 200
        data = response.json()

        assert "text" in data
        assert "mime_type" in data
        assert data["mime_type"] == "application/pdf"
        # PDF doesn't have HTML conversion
        assert data.get("html") is None

    async def test_get_content_docx_with_html(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
    ):
        """AC-5.25.4: DOCX documents return HTML rendering."""
        kb_id = test_kb["id"]

        # Create a DOCX document
        with patch(
            "app.services.document_service.minio_service.upload_file",
            new_callable=AsyncMock,
            return_value=f"kb-{kb_id}/doc/file.docx",
        ):
            with patch(
                "app.services.document_service.minio_service.ensure_bucket_exists",
                new_callable=AsyncMock,
            ):
                # Minimal DOCX bytes (would be real DOCX in production)
                docx_content = b"PK\x03\x04"  # ZIP signature (DOCX is a ZIP)
                files = {
                    "file": (
                        "test-doc.docx",
                        docx_content,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                }
                response = await authenticated_client.post(
                    f"/api/v1/knowledge-bases/{kb_id}/documents/upload",
                    files=files,
                )
                assert response.status_code == 201
                doc = response.json()

        doc_id = doc["id"]

        # Mock MinIO download and mammoth conversion
        with patch(
            "app.api.v1.documents.minio_client.download_file",
            new_callable=AsyncMock,
            return_value=b"PK\x03\x04 fake docx bytes",
        ):
            with patch(
                "app.services.document_service.document_service.get_document_text",
                new_callable=AsyncMock,
                return_value="DOCX extracted text content.",
            ):
                with patch(
                    "app.api.v1.documents.mammoth.convert_to_html",
                ) as mock_mammoth:
                    # Mock mammoth result
                    mock_result = MagicMock()
                    mock_result.value = "<p>DOCX content as HTML</p>"
                    mock_mammoth.return_value = mock_result

                    response = await authenticated_client.get(
                        f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/full-content"
                    )

        assert response.status_code == 200
        data = response.json()

        assert "text" in data
        assert "mime_type" in data
        assert "html" in data
        assert (
            data["mime_type"]
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert data["html"] == "<p>DOCX content as HTML</p>"


# =============================================================================
# Test Permission Enforcement
# =============================================================================


class TestChunkEndpointPermissions:
    """Tests for permission enforcement on chunk endpoints."""

    async def test_get_chunks_requires_authentication(
        self,
        chunk_client: AsyncClient,
        test_kb: dict,
        test_document: dict,
    ):
        """Unauthenticated request returns 401."""
        kb_id = test_kb["id"]
        doc_id = test_document["id"]

        response = await chunk_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/chunks"
        )

        assert response.status_code == 401

    async def test_get_content_requires_authentication(
        self,
        chunk_client: AsyncClient,
        test_kb: dict,
        test_document: dict,
    ):
        """Unauthenticated request returns 401."""
        kb_id = test_kb["id"]
        doc_id = test_document["id"]

        response = await chunk_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/full-content"
        )

        assert response.status_code == 401

    async def test_get_chunks_invalid_kb_returns_404(
        self,
        authenticated_client: AsyncClient,
        test_document: dict,
    ):
        """Request with invalid KB ID returns 404."""
        fake_kb_id = str(uuid.uuid4())
        doc_id = test_document["id"]

        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{fake_kb_id}/documents/{doc_id}/chunks"
        )

        # Should return 404 (KB not found) or 403 (no access)
        assert response.status_code in [403, 404]

    async def test_get_chunks_invalid_document_returns_404(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_qdrant_service,
    ):
        """Request with invalid document ID returns 404."""
        kb_id = test_kb["id"]
        fake_doc_id = str(uuid.uuid4())

        # Ensure collection exists
        await test_qdrant_service.create_collection(uuid.UUID(kb_id))

        response = await authenticated_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}/chunks"
        )

        assert response.status_code == 404


# =============================================================================
# Test Error Handling
# =============================================================================


class TestChunkEndpointErrors:
    """Tests for error handling in chunk endpoints."""

    async def test_get_chunks_qdrant_error_returns_500(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document: dict,
    ):
        """Qdrant errors are handled gracefully."""
        kb_id = test_kb["id"]
        doc_id = test_document["id"]

        # Mock Qdrant failure
        with patch(
            "app.services.chunk_service.qdrant_service.client.count",
            side_effect=Exception("Qdrant connection failed"),
        ):
            response = await authenticated_client.get(
                f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/chunks"
            )

        # Should return 500 with error details
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    async def test_get_content_minio_error_returns_500(
        self,
        authenticated_client: AsyncClient,
        test_kb: dict,
        test_document: dict,
    ):
        """MinIO download errors are handled gracefully."""
        kb_id = test_kb["id"]
        doc_id = test_document["id"]

        # Mock MinIO failure
        with patch(
            "app.api.v1.documents.minio_client.download_file",
            new_callable=AsyncMock,
            side_effect=Exception("MinIO connection failed"),
        ):
            with patch(
                "app.services.document_service.document_service.get_document_text",
                new_callable=AsyncMock,
                return_value="Some text",
            ):
                response = await authenticated_client.get(
                    f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/full-content"
                )

        # Should return 500 with error details
        assert response.status_code == 500
