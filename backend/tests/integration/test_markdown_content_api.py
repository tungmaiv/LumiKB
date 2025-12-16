"""Integration tests for Markdown Content API endpoint (Story 7-29).

Tests cover:
- GET /knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content
- AC-7.29.1: 200 with valid markdown content
- AC-7.29.2: 404 for document without markdown
- AC-7.29.3: 400 for processing document
- AC-7.29.5: 403 for unauthorized access
- AC-7.29.6: 404 for non-existent document/KB
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User
from tests.factories import create_registration_data

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures (Direct DB Access - Bypasses API Permission Requirements)
# =============================================================================


@pytest.fixture
async def markdown_test_user(
    api_client: "AsyncClient",
    db_session: AsyncSession,
) -> dict:
    """Create a test user via API and return user data with auth cookies.

    Returns:
        dict with email, password, cookies, user_id
    """
    user_data = create_registration_data()

    # Register user via API
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert register_response.status_code == 201
    user_response = register_response.json()

    # Login to get JWT cookie
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
        "cookies": login_response.cookies,
        "user_id": user_response["id"],
    }


@pytest.fixture
async def markdown_second_user(api_client: "AsyncClient") -> dict:
    """Create a second test user (no KB access) via API.

    Returns:
        dict with email, password, cookies, user_id
    """
    user_data = create_registration_data()

    # Register second user
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert register_response.status_code == 201
    user_response = register_response.json()

    # Login to get JWT cookie
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
        "cookies": login_response.cookies,
        "user_id": user_response["id"],
    }


@pytest.fixture
async def markdown_test_kb(
    db_session: AsyncSession,
    markdown_test_user: dict,
) -> dict:
    """Create a test KB directly in DB (bypasses API permission check).

    Returns:
        dict with KB id and name
    """
    # Get test user from DB
    result = await db_session.execute(
        select(User).where(User.id == markdown_test_user["user_id"])
    )
    test_user = result.scalar_one()

    # Create KB directly in database
    kb = KnowledgeBase(
        name="Markdown Test KB",
        description="Test KB for markdown content API tests",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()

    # Grant READ permission to test user (owner already has implicit ADMIN)
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.READ,
    )
    db_session.add(permission)
    await db_session.commit()
    await db_session.refresh(kb)

    return {
        "id": str(kb.id),
        "name": kb.name,
    }


@pytest.fixture
async def markdown_test_document(
    db_session: AsyncSession,
    markdown_test_kb: dict,
    markdown_test_user: dict,
) -> dict:
    """Create a test document directly in DB.

    Returns:
        dict with document id and metadata
    """
    kb_id = uuid.UUID(markdown_test_kb["id"])
    user_id = uuid.UUID(markdown_test_user["user_id"])

    # Create document directly in database (starts as PENDING)
    document = Document(
        kb_id=kb_id,
        name="test-markdown-doc.pdf",
        original_filename="test-markdown-doc.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024,
        file_path=f"kb-{kb_id}/test-doc.pdf",
        checksum="a" * 64,  # Valid SHA256 hex length
        status=DocumentStatus.PENDING,
        chunk_count=0,
        uploaded_by=user_id,
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    return {
        "id": str(document.id),
        "name": document.name,
        "status": document.status.value,
    }


# =============================================================================
# AC-7.29.1: Success - Returns markdown content
# =============================================================================


class TestGetMarkdownContentSuccess:
    """Tests for successful markdown content retrieval (AC-7.29.1)."""

    async def test_get_markdown_content_returns_200(
        self,
        api_client: "AsyncClient",
        db_session: AsyncSession,
        markdown_test_user: dict,
        markdown_test_kb: dict,
        markdown_test_document: dict,
    ):
        """AC-7.29.1: Valid document with markdown returns 200."""
        from app.workers.parsing import ParsedContent, ParsedElement

        kb_id = markdown_test_kb["id"]
        doc_id = markdown_test_document["id"]

        # Update document status to READY
        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        document = result.scalar_one()
        document.status = DocumentStatus.READY
        document.processing_completed_at = datetime.now(UTC)
        await db_session.commit()

        # Mock parsed content with markdown
        mock_parsed = ParsedContent(
            text="Test document content",
            elements=[
                ParsedElement(
                    text="Test document content",
                    element_type="paragraph",
                    metadata={},
                )
            ],
            metadata={"page_count": 1},
            markdown_content="# Test Document\n\nTest document content",
        )

        with patch(
            "app.api.v1.documents.load_parsed_content",
            new_callable=AsyncMock,
            return_value=mock_parsed,
        ):
            response = await api_client.get(
                f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content",
                cookies=markdown_test_user["cookies"],
            )

            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == doc_id
            assert (
                data["markdown_content"] == "# Test Document\n\nTest document content"
            )
            assert "generated_at" in data

    async def test_get_markdown_content_response_schema(
        self,
        api_client: "AsyncClient",
        db_session: AsyncSession,
        markdown_test_user: dict,
        markdown_test_kb: dict,
        markdown_test_document: dict,
    ):
        """AC-7.29.4: Response includes document_id, markdown_content, generated_at."""
        from app.workers.parsing import ParsedContent, ParsedElement

        kb_id = markdown_test_kb["id"]
        doc_id = markdown_test_document["id"]

        # Update document status to READY
        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        document = result.scalar_one()
        document.status = DocumentStatus.READY
        document.processing_completed_at = datetime.now(UTC)
        await db_session.commit()

        mock_parsed = ParsedContent(
            text="Content",
            elements=[ParsedElement(text="Content", element_type="text", metadata={})],
            metadata={},
            markdown_content="# Heading\n\nContent",
        )

        with patch(
            "app.api.v1.documents.load_parsed_content",
            new_callable=AsyncMock,
            return_value=mock_parsed,
        ):
            response = await api_client.get(
                f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content",
                cookies=markdown_test_user["cookies"],
            )

            assert response.status_code == 200
            data = response.json()

            # Verify all required fields per AC-7.29.4
            assert "document_id" in data
            assert "markdown_content" in data
            assert "generated_at" in data

            # Verify types
            assert isinstance(data["document_id"], str)
            assert isinstance(data["markdown_content"], str)
            assert isinstance(data["generated_at"], str)  # ISO datetime


# =============================================================================
# AC-7.29.2: 404 for documents without markdown
# =============================================================================


class TestGetMarkdownContentNotFound:
    """Tests for 404 responses (AC-7.29.2)."""

    async def test_get_markdown_content_no_markdown_returns_404(
        self,
        api_client: "AsyncClient",
        db_session: AsyncSession,
        markdown_test_user: dict,
        markdown_test_kb: dict,
        markdown_test_document: dict,
    ):
        """AC-7.29.2: Document without markdown content returns 404."""
        from app.workers.parsing import ParsedContent, ParsedElement

        kb_id = markdown_test_kb["id"]
        doc_id = markdown_test_document["id"]

        # Update document status to READY
        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        document = result.scalar_one()
        document.status = DocumentStatus.READY
        await db_session.commit()

        # Mock parsed content WITHOUT markdown
        mock_parsed = ParsedContent(
            text="Old document content",
            elements=[
                ParsedElement(text="Old content", element_type="text", metadata={})
            ],
            metadata={},
            markdown_content=None,  # No markdown
        )

        with patch(
            "app.api.v1.documents.load_parsed_content",
            new_callable=AsyncMock,
            return_value=mock_parsed,
        ):
            response = await api_client.get(
                f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content",
                cookies=markdown_test_user["cookies"],
            )

            assert response.status_code == 404
            assert "Markdown content not available" in response.json()["detail"]

    async def test_get_markdown_content_no_parsed_content_returns_404(
        self,
        api_client: "AsyncClient",
        db_session: AsyncSession,
        markdown_test_user: dict,
        markdown_test_kb: dict,
        markdown_test_document: dict,
    ):
        """AC-7.29.2: Document without parsed content file returns 404."""
        kb_id = markdown_test_kb["id"]
        doc_id = markdown_test_document["id"]

        # Update document status to READY
        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        document = result.scalar_one()
        document.status = DocumentStatus.READY
        await db_session.commit()

        # Mock no parsed content found
        with patch(
            "app.api.v1.documents.load_parsed_content",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await api_client.get(
                f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content",
                cookies=markdown_test_user["cookies"],
            )

            assert response.status_code == 404
            assert "Markdown content not available" in response.json()["detail"]

    async def test_get_markdown_content_document_not_found_returns_404(
        self,
        api_client: "AsyncClient",
        markdown_test_user: dict,
        markdown_test_kb: dict,
    ):
        """AC-7.29.6: Non-existent document returns 404."""
        kb_id = markdown_test_kb["id"]
        fake_doc_id = str(uuid.uuid4())

        response = await api_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{fake_doc_id}/markdown-content",
            cookies=markdown_test_user["cookies"],
        )

        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]

    async def test_get_markdown_content_kb_not_found_returns_403(
        self,
        api_client: "AsyncClient",
        markdown_test_user: dict,
    ):
        """AC-7.29.6: Non-existent KB returns 403 (no access)."""
        fake_kb_id = str(uuid.uuid4())
        fake_doc_id = str(uuid.uuid4())

        response = await api_client.get(
            f"/api/v1/knowledge-bases/{fake_kb_id}/documents/{fake_doc_id}/markdown-content",
            cookies=markdown_test_user["cookies"],
        )

        # Returns 403 because user has no access to non-existent KB
        assert response.status_code == 403


# =============================================================================
# AC-7.29.3: 400 for processing documents
# =============================================================================


class TestGetMarkdownContentProcessing:
    """Tests for 400 responses on processing documents (AC-7.29.3)."""

    async def test_get_markdown_content_pending_returns_400(
        self,
        api_client: "AsyncClient",
        markdown_test_user: dict,
        markdown_test_kb: dict,
        markdown_test_document: dict,
    ):
        """AC-7.29.3: Document with PENDING status returns 400."""
        kb_id = markdown_test_kb["id"]
        doc_id = markdown_test_document["id"]

        # Document starts as PENDING by default
        response = await api_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content",
            cookies=markdown_test_user["cookies"],
        )

        assert response.status_code == 400
        assert "Document is still processing" in response.json()["detail"]

    async def test_get_markdown_content_processing_returns_400(
        self,
        api_client: "AsyncClient",
        db_session: AsyncSession,
        markdown_test_user: dict,
        markdown_test_kb: dict,
        markdown_test_document: dict,
    ):
        """AC-7.29.3: Document with PROCESSING status returns 400."""
        kb_id = markdown_test_kb["id"]
        doc_id = markdown_test_document["id"]

        # Update document to PROCESSING
        result = await db_session.execute(
            select(Document).where(Document.id == uuid.UUID(doc_id))
        )
        document = result.scalar_one()
        document.status = DocumentStatus.PROCESSING
        await db_session.commit()

        response = await api_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content",
            cookies=markdown_test_user["cookies"],
        )

        assert response.status_code == 400
        assert "Document is still processing" in response.json()["detail"]


# =============================================================================
# AC-7.29.5: 403 for unauthorized access
# =============================================================================


class TestGetMarkdownContentUnauthorized:
    """Tests for 403 responses (AC-7.29.5)."""

    async def test_get_markdown_content_no_kb_access_returns_403(
        self,
        api_client: "AsyncClient",
        markdown_test_kb: dict,
        markdown_test_document: dict,
        markdown_second_user: dict,
    ):
        """AC-7.29.5: User without KB access returns 403."""
        kb_id = markdown_test_kb["id"]
        doc_id = markdown_test_document["id"]

        # Use second user's cookies (no KB access)
        response = await api_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content",
            cookies=markdown_second_user["cookies"],
        )

        assert response.status_code == 403
        assert "No read access" in response.json()["detail"]

    async def test_get_markdown_content_unauthenticated_returns_401(
        self,
        api_client: "AsyncClient",
        markdown_test_kb: dict,
        markdown_test_document: dict,
    ):
        """Unauthenticated request returns 401."""
        kb_id = markdown_test_kb["id"]
        doc_id = markdown_test_document["id"]

        # Clear any cookies from previous fixture setups
        api_client.cookies.clear()

        # No cookies = unauthenticated
        response = await api_client.get(
            f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content",
        )

        assert response.status_code == 401
