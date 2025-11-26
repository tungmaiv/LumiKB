"""Document parsing utilities using unstructured library.

This module provides format-specific parsing functions for PDF, DOCX, and Markdown
documents. All parsers return a ParsedContent dataclass with extracted text,
elements, and metadata.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ParsingError(Exception):
    """Base exception for parsing errors."""


class PasswordProtectedError(ParsingError):
    """Raised when a PDF is password-protected."""


class ScannedDocumentError(ParsingError):
    """Raised when a document appears to be scanned (no extractable text)."""


class InsufficientContentError(ParsingError):
    """Raised when extracted content is below minimum threshold."""


@dataclass
class ParsedElement:
    """A single parsed element from a document.

    Attributes:
        text: The text content of the element.
        element_type: Type of element (e.g., Title, NarrativeText, ListItem).
        metadata: Additional metadata (page_number, section, etc.).
    """

    text: str
    element_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedContent:
    """Result of parsing a document.

    Attributes:
        text: Full concatenated text content.
        elements: List of parsed elements with metadata.
        metadata: Document-level metadata (page_count, sections, etc.).
    """

    text: str
    elements: list[ParsedElement]
    metadata: dict[str, Any]

    @property
    def extracted_chars(self) -> int:
        """Total character count of extracted text."""
        return len(self.text)

    @property
    def page_count(self) -> int | None:
        """Number of pages if available."""
        return self.metadata.get("page_count")

    @property
    def section_count(self) -> int:
        """Number of sections/headings found."""
        return self.metadata.get("section_count", 0)


# Minimum character threshold for valid content
MIN_CONTENT_CHARS = 100


def parse_pdf(file_path: str) -> ParsedContent:
    """Parse a PDF document and extract text content.

    Uses unstructured.partition_pdf() with auto strategy.

    Args:
        file_path: Path to the PDF file.

    Returns:
        ParsedContent with extracted text and page metadata.

    Raises:
        PasswordProtectedError: If PDF is password-protected.
        ScannedDocumentError: If PDF appears to be scanned (no text extracted).
        InsufficientContentError: If extracted text is below minimum.
        ParsingError: For other parsing failures.
    """
    try:
        from unstructured.partition.pdf import partition_pdf
    except ImportError as e:
        raise ParsingError(f"unstructured library not available: {e}") from e

    logger.info("parsing_pdf_started", file_path=file_path)

    try:
        elements = partition_pdf(
            filename=file_path,
            strategy="auto",  # auto-detect best strategy
        )
    except Exception as e:
        error_str = str(e).lower()
        if "password" in error_str or "encrypted" in error_str:
            raise PasswordProtectedError(
                "Password-protected PDF cannot be processed"
            ) from e
        raise ParsingError(f"Failed to parse PDF: {e}") from e

    # Check for scanned document (no text elements)
    text_elements = [el for el in elements if hasattr(el, "text") and el.text.strip()]
    if not text_elements:
        raise ScannedDocumentError(
            "Document appears to be scanned (OCR required - MVP 2)"
        )

    # Extract elements with metadata
    parsed_elements = []
    pages = set()

    for el in elements:
        if not hasattr(el, "text") or not el.text.strip():
            continue

        element_meta = {}
        if hasattr(el, "metadata"):
            meta = el.metadata
            if hasattr(meta, "page_number") and meta.page_number:
                element_meta["page_number"] = meta.page_number
                pages.add(meta.page_number)
            if hasattr(meta, "coordinates") and meta.coordinates:
                element_meta["coordinates"] = {
                    "points": meta.coordinates.points
                    if hasattr(meta.coordinates, "points")
                    else None,
                }

        parsed_elements.append(
            ParsedElement(
                text=el.text,
                element_type=type(el).__name__,
                metadata=element_meta,
            )
        )

    # Concatenate all text
    full_text = "\n\n".join(el.text for el in parsed_elements)

    # Validate content length
    if len(full_text) < MIN_CONTENT_CHARS:
        raise InsufficientContentError(
            f"No text content found (extracted {len(full_text)} chars, minimum {MIN_CONTENT_CHARS})"
        )

    metadata = {
        "page_count": max(pages) if pages else None,
        "section_count": sum(
            1 for el in parsed_elements if el.element_type in ("Title", "Header")
        ),
        "element_count": len(parsed_elements),
        "source_format": "pdf",
    }

    logger.info(
        "parsing_pdf_completed",
        file_path=file_path,
        extracted_chars=len(full_text),
        page_count=metadata["page_count"],
        element_count=len(parsed_elements),
    )

    return ParsedContent(
        text=full_text,
        elements=parsed_elements,
        metadata=metadata,
    )


def parse_docx(file_path: str) -> ParsedContent:
    """Parse a DOCX document and extract text content.

    Uses unstructured.partition_docx().

    Args:
        file_path: Path to the DOCX file.

    Returns:
        ParsedContent with extracted text and section headers.

    Raises:
        InsufficientContentError: If extracted text is below minimum.
        ParsingError: For other parsing failures.
    """
    try:
        from unstructured.partition.docx import partition_docx
    except ImportError as e:
        raise ParsingError(f"unstructured library not available: {e}") from e

    logger.info("parsing_docx_started", file_path=file_path)

    try:
        elements = partition_docx(filename=file_path)
    except Exception as e:
        raise ParsingError(f"Failed to parse DOCX: {e}") from e

    # Extract elements with metadata
    parsed_elements = []
    sections = []

    for el in elements:
        if not hasattr(el, "text") or not el.text.strip():
            continue

        element_type = type(el).__name__
        element_meta = {}

        # Track section headers
        if element_type in ("Title", "Header"):
            sections.append(el.text)
            element_meta["is_header"] = True

        parsed_elements.append(
            ParsedElement(
                text=el.text,
                element_type=element_type,
                metadata=element_meta,
            )
        )

    # Concatenate all text
    full_text = "\n\n".join(el.text for el in parsed_elements)

    # Validate content length
    if len(full_text) < MIN_CONTENT_CHARS:
        raise InsufficientContentError(
            f"No text content found (extracted {len(full_text)} chars, minimum {MIN_CONTENT_CHARS})"
        )

    metadata = {
        "section_count": len(sections),
        "sections": sections[:20],  # Store first 20 section headers
        "element_count": len(parsed_elements),
        "source_format": "docx",
    }

    logger.info(
        "parsing_docx_completed",
        file_path=file_path,
        extracted_chars=len(full_text),
        section_count=len(sections),
        element_count=len(parsed_elements),
    )

    return ParsedContent(
        text=full_text,
        elements=parsed_elements,
        metadata=metadata,
    )


def parse_markdown(file_path: str) -> ParsedContent:
    """Parse a Markdown document and extract text content.

    Uses unstructured.partition_md().

    Args:
        file_path: Path to the Markdown file.

    Returns:
        ParsedContent with extracted text and heading structure.

    Raises:
        InsufficientContentError: If extracted text is below minimum.
        ParsingError: For other parsing failures.
    """
    try:
        from unstructured.partition.md import partition_md
    except ImportError as e:
        raise ParsingError(f"unstructured library not available: {e}") from e

    logger.info("parsing_markdown_started", file_path=file_path)

    try:
        elements = partition_md(filename=file_path)
    except Exception as e:
        raise ParsingError(f"Failed to parse Markdown: {e}") from e

    # Extract elements with metadata
    parsed_elements = []
    headings = []

    for el in elements:
        if not hasattr(el, "text") or not el.text.strip():
            continue

        element_type = type(el).__name__
        element_meta = {}

        # Track headings
        if element_type == "Title":
            headings.append({"level": 1, "text": el.text})
            element_meta["heading_level"] = 1
        elif element_type == "Header":
            # Try to infer heading level from metadata
            level = 2  # Default
            if hasattr(el, "metadata") and hasattr(el.metadata, "category_depth"):
                level = el.metadata.category_depth or 2
            headings.append({"level": level, "text": el.text})
            element_meta["heading_level"] = level

        parsed_elements.append(
            ParsedElement(
                text=el.text,
                element_type=element_type,
                metadata=element_meta,
            )
        )

    # Concatenate all text
    full_text = "\n\n".join(el.text for el in parsed_elements)

    # Validate content length
    if len(full_text) < MIN_CONTENT_CHARS:
        raise InsufficientContentError(
            f"No text content found (extracted {len(full_text)} chars, minimum {MIN_CONTENT_CHARS})"
        )

    metadata = {
        "section_count": len(headings),
        "headings": headings[:30],  # Store first 30 headings
        "element_count": len(parsed_elements),
        "source_format": "markdown",
    }

    logger.info(
        "parsing_markdown_completed",
        file_path=file_path,
        extracted_chars=len(full_text),
        heading_count=len(headings),
        element_count=len(parsed_elements),
    )

    return ParsedContent(
        text=full_text,
        elements=parsed_elements,
        metadata=metadata,
    )


def parse_document(file_path: str, mime_type: str) -> ParsedContent:
    """Parse a document based on its MIME type.

    Dispatches to appropriate parser based on MIME type.

    Args:
        file_path: Path to the document file.
        mime_type: MIME type of the document.

    Returns:
        ParsedContent with extracted text and metadata.

    Raises:
        ParsingError: If MIME type is unsupported or parsing fails.
    """
    mime_parsers = {
        "application/pdf": parse_pdf,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": parse_docx,
        "text/markdown": parse_markdown,
        "text/x-markdown": parse_markdown,
    }

    parser = mime_parsers.get(mime_type)
    if not parser:
        raise ParsingError(f"Unsupported MIME type: {mime_type}")

    return parser(file_path)
