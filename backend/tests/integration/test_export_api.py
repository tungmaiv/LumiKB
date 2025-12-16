"""Integration tests for draft export API (Story 4.7, AC1-AC6)."""

import pytest
from httpx import AsyncClient

from app.models.draft import DraftStatus

pytestmark = pytest.mark.integration


async def test_export_docx_success(
    client: AsyncClient,
    authenticated_user,
    draft_factory,
    kb_with_permission,
):
    """Test successful DOCX export (AC1, AC3)."""
    # Create draft with citations
    draft = await draft_factory(
        kb_id=kb_with_permission.id,
        user_id=authenticated_user.id,
        title="Export Test Draft",
        content="Our solution uses OAuth 2.0 [1].",
        citations=[
            {
                "number": 1,
                "document_id": "doc-1",
                "document_name": "Auth Spec.pdf",
                "page_number": 5,
                "section_header": "OAuth",
                "excerpt": "OAuth 2.0 framework...",
                "char_start": 100,
                "char_end": 300,
                "confidence": 0.95,
            }
        ],
        status=DraftStatus.COMPLETE,
    )

    response = await client.post(
        f"/api/v1/drafts/{draft.id}/export",
        json={"format": "docx"},
    )

    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert "attachment" in response.headers.get("content-disposition", "")
    assert ".docx" in response.headers.get("content-disposition", "")
    assert len(response.content) > 0
    # DOCX files start with PK (ZIP header)
    assert response.content[:2] == b"PK"


async def test_export_pdf_success(
    client: AsyncClient,
    authenticated_user,
    draft_factory,
    kb_with_permission,
):
    """Test successful PDF export (AC1, AC4)."""
    draft = await draft_factory(
        kb_id=kb_with_permission.id,
        user_id=authenticated_user.id,
        title="PDF Export Test",
        content="## Summary\n\nTest content [1].",
        citations=[
            {
                "number": 1,
                "document_id": "doc-1",
                "document_name": "Test.pdf",
                "page_number": 1,
                "section_header": None,
                "excerpt": "Test excerpt",
                "char_start": 0,
                "char_end": 100,
                "confidence": 0.9,
            }
        ],
        status=DraftStatus.EDITING,
    )

    response = await client.post(
        f"/api/v1/drafts/{draft.id}/export",
        json={"format": "pdf"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers.get("content-disposition", "")
    assert ".pdf" in response.headers.get("content-disposition", "")
    assert len(response.content) > 0
    # PDF files start with %PDF
    assert response.content[:4] == b"%PDF"


async def test_export_markdown_success(
    client: AsyncClient,
    authenticated_user,
    draft_factory,
    kb_with_permission,
):
    """Test successful Markdown export (AC1, AC5)."""
    draft = await draft_factory(
        kb_id=kb_with_permission.id,
        user_id=authenticated_user.id,
        title="Markdown Test",
        content="Content with citation [1]",
        citations=[
            {
                "number": 1,
                "document_id": "doc-1",
                "document_name": "Source.md",
                "page_number": None,
                "section_header": "Intro",
                "excerpt": "Source text...",
                "char_start": 0,
                "char_end": 50,
                "confidence": 0.85,
            }
        ],
        status=DraftStatus.COMPLETE,
    )

    response = await client.post(
        f"/api/v1/drafts/{draft.id}/export",
        json={"format": "markdown"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown"
    assert "attachment" in response.headers.get("content-disposition", "")
    assert ".md" in response.headers.get("content-disposition", "")

    content = response.content.decode("utf-8")
    assert "Content with citation [^1]" in content  # Converted to footnote syntax
    assert "## References" in content
    assert "[^1]: **Source.md**" in content


async def test_export_permission_denied(
    client: AsyncClient,
    authenticated_user,
    draft_factory,
    kb_factory,
):
    """Test export fails without READ permission (AC1)."""
    # Create KB without permission for this user
    other_kb = await kb_factory(name="Other KB")

    draft = await draft_factory(
        kb_id=other_kb.id,
        user_id=authenticated_user.id,  # Draft belongs to user
        title="Inaccessible Draft",
        content="Content",
        citations=[],
        status=DraftStatus.COMPLETE,
    )

    response = await client.post(
        f"/api/v1/drafts/{draft.id}/export",
        json={"format": "docx"},
    )

    # Should fail permission check
    assert response.status_code in [403, 404]


async def test_export_invalid_format(
    client: AsyncClient,
    authenticated_user,
    draft_factory,
    kb_with_permission,
):
    """Test export rejects invalid format (AC1)."""
    draft = await draft_factory(
        kb_id=kb_with_permission.id,
        user_id=authenticated_user.id,
        title="Test",
        content="Content",
        citations=[],
        status=DraftStatus.COMPLETE,
    )

    response = await client.post(
        f"/api/v1/drafts/{draft.id}/export",
        json={"format": "invalid"},
    )

    assert response.status_code == 400
    assert "Invalid format" in response.json().get("detail", "")


async def test_export_draft_not_found(
    client: AsyncClient,
    authenticated_user,
):
    """Test export fails for non-existent draft."""
    response = await client.post(
        "/api/v1/drafts/00000000-0000-0000-0000-000000000000/export",
        json={"format": "docx"},
    )

    assert response.status_code == 404


async def test_export_filename_sanitization(
    client: AsyncClient,
    authenticated_user,
    draft_factory,
    kb_with_permission,
):
    """Test special characters removed from filename (AC3)."""
    draft = await draft_factory(
        kb_id=kb_with_permission.id,
        user_id=authenticated_user.id,
        title="Test/Draft:With*Special?Chars<>",
        content="Content [1]",
        citations=[
            {
                "number": 1,
                "document_id": "d1",
                "document_name": "Doc.pdf",
                "page_number": 1,
                "section_header": None,
                "excerpt": "Text",
                "char_start": 0,
                "char_end": 10,
                "confidence": 0.9,
            }
        ],
        status=DraftStatus.COMPLETE,
    )

    response = await client.post(
        f"/api/v1/drafts/{draft.id}/export",
        json={"format": "docx"},
    )

    assert response.status_code == 200
    content_disposition = response.headers.get("content-disposition", "")

    # Special characters should be removed
    assert "/" not in content_disposition
    assert "*" not in content_disposition
    assert "?" not in content_disposition
    assert "<" not in content_disposition
    assert ">" not in content_disposition
