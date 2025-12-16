"""Test helpers for integration testing.

This module provides utilities for integration tests that need
to interact with external services (Qdrant, MinIO, etc.)

Usage:
    from tests.helpers import wait_for_document_indexed, poll_document_status
"""

from .document_helpers import poll_document_status, wait_for_document_indexed
from .export_validation import (
    count_citations_in_content,
    extract_docx_text,
    extract_pdf_text,
    validate_docx_citations,
    validate_export_format,
    validate_markdown_citations,
    validate_pdf_citations,
)
from .qdrant_helpers import (
    create_test_chunk,
    create_test_embedding,
    insert_test_chunks,
)

__all__ = [
    # Document helpers
    "wait_for_document_indexed",
    "poll_document_status",
    # Export validation helpers
    "validate_docx_citations",
    "validate_pdf_citations",
    "validate_markdown_citations",
    "extract_docx_text",
    "extract_pdf_text",
    "validate_export_format",
    "count_citations_in_content",
    # Qdrant helpers
    "create_test_embedding",
    "create_test_chunk",
    "insert_test_chunks",
]
