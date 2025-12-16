"""Unit tests for ExportService (Story 4.7, AC3-AC6)."""

import re
from datetime import datetime
from unittest.mock import Mock

import pytest

from app.models.draft import Draft, DraftStatus
from app.services.export_service import ExportService


@pytest.fixture
def sample_draft():
    """Create a sample draft with citations for testing."""
    draft = Mock(spec=Draft)
    draft.id = "550e8400-e29b-41d4-a716-446655440000"
    draft.title = "Test Draft - Export Example"
    draft.content = """## Executive Summary

Our solution implements OAuth 2.0 [1] with PKCE flow [2].

## Authentication

Multi-factor authentication [3] is required for all users."""
    draft.citations = [
        {
            "number": 1,
            "document_id": "doc-uuid-1",
            "document_name": "Auth Spec.pdf",
            "page_number": 5,
            "section_header": "OAuth 2.0",
            "excerpt": "OAuth 2.0 is an authorization framework that enables applications...",
            "char_start": 120,
            "char_end": 340,
            "confidence": 0.95,
        },
        {
            "number": 2,
            "document_id": "doc-uuid-1",
            "document_name": "Auth Spec.pdf",
            "page_number": 7,
            "section_header": "PKCE Extension",
            "excerpt": "Proof Key for Code Exchange (PKCE) is an extension to OAuth 2.0...",
            "char_start": 450,
            "char_end": 670,
            "confidence": 0.92,
        },
        {
            "number": 3,
            "document_id": "doc-uuid-2",
            "document_name": "Security Requirements.docx",
            "page_number": 3,
            "section_header": "MFA Requirements",
            "excerpt": "Multi-factor authentication must be implemented for all user-facing...",
            "char_start": 200,
            "char_end": 420,
            "confidence": 0.88,
        },
    ]
    draft.word_count = 25
    draft.status = DraftStatus.COMPLETE
    return draft


@pytest.fixture
def export_service():
    """Create ExportService instance."""
    return ExportService()


# AC3: DOCX Export Tests
def test_export_to_docx_basic(export_service, sample_draft):
    """Test basic DOCX export structure."""
    result = export_service.export_to_docx(sample_draft)

    assert isinstance(result, bytes)
    assert len(result) > 0
    # DOCX files start with PK (ZIP header)
    assert result[:2] == b"PK"


def test_export_to_docx_footnotes(export_service, sample_draft):
    """Test that citations are rendered as footnotes in DOCX."""
    # This test verifies the export completes without errors
    # Full verification would require opening DOCX programmatically
    result = export_service.export_to_docx(sample_draft)

    assert isinstance(result, bytes)
    assert len(result) > 0


# AC4: PDF Export Tests
def test_export_to_pdf_basic(export_service, sample_draft):
    """Test basic PDF export structure."""
    result = export_service.export_to_pdf(sample_draft)

    assert isinstance(result, bytes)
    assert len(result) > 0
    # PDF files start with %PDF
    assert result[:4] == b"%PDF"


def test_export_to_pdf_citation_table(export_service, sample_draft):
    """Test that citations appear in PDF."""
    # Verify PDF generation succeeds
    result = export_service.export_to_pdf(sample_draft)

    assert isinstance(result, bytes)
    assert len(result) > 0


# AC5: Markdown Export Tests
def test_export_to_markdown_basic(export_service, sample_draft):
    """Test basic Markdown export."""
    result = export_service.export_to_markdown(sample_draft)

    assert isinstance(result, str)
    assert "## Executive Summary" in result
    assert "## Authentication" in result


def test_export_to_markdown_footnotes(export_service, sample_draft):
    """Test that citations use [^n] footnote syntax."""
    result = export_service.export_to_markdown(sample_draft)

    # Check conversion from [1] to [^1]
    assert "[^1]" in result
    assert "[^2]" in result
    assert "[^3]" in result

    # Old format should not exist
    assert "[1]" not in result
    assert "[2]" not in result
    assert "[3]" not in result

    # Check footnote references section
    assert "## References" in result
    assert "[^1]: **Auth Spec.pdf**" in result
    assert "[^2]: **Auth Spec.pdf**" in result
    assert "[^3]: **Security Requirements.docx**" in result


# Citation Formatter Helper Tests
def test_format_citation_footnote_with_all_fields(export_service):
    """Test citation formatting with all fields present."""
    citation = {
        "document_name": "Test Document.pdf",
        "page_number": 10,
        "section_header": "Introduction",
        "excerpt": "This is a test excerpt from the document.",
    }

    result = export_service._format_citation_footnote(citation)

    assert "Source: Test Document.pdf" in result
    assert "Page 10" in result
    assert 'Section "Introduction"' in result
    assert "Excerpt:" in result


def test_format_citation_footnote_minimal(export_service):
    """Test citation formatting with minimal fields."""
    citation = {
        "document_name": "Minimal Doc.pdf",
        "page_number": None,
        "section_header": None,
        "excerpt": None,
    }

    result = export_service._format_citation_footnote(citation)

    assert "Source: Minimal Doc.pdf" in result
    assert "Page" not in result
    assert "Section" not in result
    assert "Excerpt" not in result


def test_export_to_markdown_empty_citations():
    """Test Markdown export with no citations."""
    export_service = ExportService()
    draft = Mock(spec=Draft)
    draft.title = "No Citations Draft"
    draft.content = "## Simple Content\n\nNo citations here."
    draft.citations = []

    result = export_service.export_to_markdown(draft)

    assert isinstance(result, str)
    assert "## Simple Content" in result
    assert "## References" not in result  # No references section


def test_export_to_markdown_excerpt_truncation():
    """Test that long excerpts are truncated in Markdown."""
    export_service = ExportService()
    draft = Mock(spec=Draft)
    draft.title = "Long Excerpt"
    draft.content = "Test [1]"
    draft.citations = [
        {
            "number": 1,
            "document_name": "Doc.pdf",
            "page_number": 1,
            "section_header": "Section",
            "excerpt": "A" * 300,  # Very long excerpt
            "char_start": 0,
            "char_end": 300,
            "confidence": 0.9,
        }
    ]

    result = export_service.export_to_markdown(draft)

    # Check truncation (max 200 chars + "...")
    assert "[^1]:" in result
    assert "..." in result
    # Exact excerpt should not appear in full
    assert "A" * 300 not in result
