"""Docling document parser for enhanced PDF/DOCX/Markdown processing.

Story 7-32: Docling Document Parser Integration

This module provides document parsing using IBM's Docling library for better:
- Table extraction and structure preservation
- Layout analysis and document understanding
- Markdown generation with accurate formatting

Docling is an optional dependency - install with: pip install docling
"""

from dataclasses import dataclass
from typing import Any

import structlog

from app.workers.parsing import (
    MIN_CONTENT_CHARS,
    InsufficientContentError,
    ParsedContent,
    ParsedElement,
    ParsingError,
    PasswordProtectedError,
)

logger = structlog.get_logger(__name__)


class DoclingNotAvailableError(ParsingError):
    """Raised when Docling library is not installed."""


@dataclass
class DoclingParserConfig:
    """Configuration for Docling parser behavior.

    Attributes:
        ocr_enabled: Enable OCR for scanned documents.
        table_structure: Enable advanced table structure detection.
        generate_markdown: Generate markdown representation.
    """

    ocr_enabled: bool = False
    table_structure: bool = True
    generate_markdown: bool = True


def _check_docling_available() -> bool:
    """Check if Docling library is available.

    Returns:
        True if docling is installed and importable.
    """
    try:
        import docling  # noqa: F401

        return True
    except ImportError:
        return False


def is_docling_available() -> bool:
    """Public API to check if Docling library is available.

    Story 7-32 (AC-7.32.8): Exported function for availability checking.

    Returns:
        True if docling is installed and importable, False otherwise.
    """
    return _check_docling_available()


def _convert_docling_to_parsed_elements(
    doc_result: Any,
) -> tuple[list[ParsedElement], str, dict[str, Any]]:
    """Convert Docling document result to ParsedElement list.

    Args:
        doc_result: Docling DocumentConverterResult object.

    Returns:
        Tuple of (elements, full_text, metadata).
    """
    from docling_core.types.doc import DocItemLabel

    elements: list[ParsedElement] = []
    text_parts: list[str] = []
    page_numbers: set[int] = set()
    section_count = 0

    # Map Docling labels to our element types
    label_map = {
        DocItemLabel.TITLE: "Title",
        DocItemLabel.SECTION_HEADER: "Header",
        DocItemLabel.PARAGRAPH: "NarrativeText",
        DocItemLabel.TEXT: "Text",
        DocItemLabel.LIST_ITEM: "ListItem",
        DocItemLabel.TABLE: "Table",
        DocItemLabel.CAPTION: "FigureCaption",
        DocItemLabel.CODE: "CodeSnippet",
        DocItemLabel.FORMULA: "Formula",
        DocItemLabel.FOOTNOTE: "Footnote",
        DocItemLabel.PAGE_HEADER: "PageHeader",
        DocItemLabel.PAGE_FOOTER: "PageFooter",
    }

    document = doc_result.document

    # Iterate through document items
    for item, level in document.iterate_items():
        # Skip empty items
        text = ""
        if hasattr(item, "text"):
            text = item.text.strip() if item.text else ""
        elif hasattr(item, "export_to_markdown"):
            # For tables and complex items, get markdown representation
            # docling-core 2.x requires passing the document object
            try:
                text = item.export_to_markdown(document).strip()
            except TypeError:
                # Fallback for older API without doc argument
                text = item.export_to_markdown().strip()

        if not text:
            continue

        # Determine element type
        element_type = "Text"  # default
        if hasattr(item, "label"):
            element_type = label_map.get(item.label, "Text")

        # Track sections
        if element_type in ("Title", "Header"):
            section_count += 1

        # Build metadata
        element_meta: dict[str, Any] = {}
        if hasattr(item, "prov") and item.prov:
            for prov in item.prov:
                if hasattr(prov, "page_no") and prov.page_no:
                    element_meta["page_number"] = prov.page_no
                    page_numbers.add(prov.page_no)
                if hasattr(prov, "bbox") and prov.bbox:
                    element_meta["bbox"] = {
                        "l": prov.bbox.l,
                        "t": prov.bbox.t,
                        "r": prov.bbox.r,
                        "b": prov.bbox.b,
                    }

        # Handle heading levels
        if element_type == "Header" and level is not None:
            element_meta["heading_level"] = min(level + 1, 6)  # 1-based, max 6

        # For tables, store markdown representation
        if element_type == "Table" and hasattr(item, "export_to_markdown"):
            element_meta["text_as_html"] = None  # No HTML, use markdown
            element_meta["table_markdown"] = text

        elements.append(
            ParsedElement(
                text=text,
                element_type=element_type,
                metadata=element_meta,
            )
        )
        text_parts.append(text)

    full_text = "\n\n".join(text_parts)

    metadata = {
        "page_count": max(page_numbers) if page_numbers else None,
        "section_count": section_count,
        "element_count": len(elements),
        "parser": "docling",
    }

    return elements, full_text, metadata


def _docling_elements_to_markdown(elements: list[ParsedElement]) -> str:
    """Convert Docling-parsed elements to Markdown format.

    Similar to elements_to_markdown in parsing.py but optimized for
    Docling's element structure.

    Args:
        elements: List of ParsedElement from Docling parsing.

    Returns:
        Markdown-formatted string.
    """
    if not elements:
        return ""

    markdown_parts: list[str] = []

    for el in elements:
        element_type = el.element_type
        text = el.text.strip() if el.text else ""

        if not text:
            continue

        if element_type == "Title":
            markdown_parts.append(f"# {text}\n")
        elif element_type == "Header":
            level = el.metadata.get("heading_level", 2)
            level = max(1, min(level, 6))
            prefix = "#" * level
            markdown_parts.append(f"{prefix} {text}\n")
        elif element_type == "ListItem":
            markdown_parts.append(f"- {text}\n")
        elif element_type == "Table":
            # Tables from Docling are already in markdown format
            table_md = el.metadata.get("table_markdown", text)
            markdown_parts.append(f"{table_md}\n\n")
        elif element_type == "CodeSnippet":
            markdown_parts.append(f"```\n{text}\n```\n\n")
        elif element_type == "FigureCaption":
            markdown_parts.append(f"*{text}*\n\n")
        elif element_type == "Formula":
            markdown_parts.append(f"$${text}$$\n\n")
        elif element_type in ("PageHeader", "PageFooter"):
            # Skip page headers/footers in markdown output
            continue
        elif element_type in ("NarrativeText", "Text"):
            markdown_parts.append(f"{text}\n\n")
        else:
            markdown_parts.append(f"{text}\n\n")

    return "".join(markdown_parts).strip()


def parse_pdf_docling(
    file_path: str,
    config: DoclingParserConfig | None = None,
) -> ParsedContent:
    """Parse a PDF document using Docling.

    Story 7-32 (AC-7.32.3): Docling parser for PDF with enhanced table extraction.

    Args:
        file_path: Path to the PDF file.
        config: Optional parser configuration.

    Returns:
        ParsedContent with extracted text and metadata.

    Raises:
        DoclingNotAvailableError: If Docling is not installed.
        PasswordProtectedError: If PDF is password-protected.
        InsufficientContentError: If extracted text is below minimum.
        ParsingError: For other parsing failures.
    """
    if not _check_docling_available():
        raise DoclingNotAvailableError(
            "Docling library not installed. Install with: pip install docling"
        )

    config = config or DoclingParserConfig()

    logger.info("parsing_pdf_docling_started", file_path=file_path)

    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(file_path)

    except Exception as e:
        error_str = str(e).lower()
        if "password" in error_str or "encrypted" in error_str:
            raise PasswordProtectedError(
                "Password-protected PDF cannot be processed"
            ) from e
        raise ParsingError(f"Docling failed to parse PDF: {e}") from e

    # Convert to our format
    elements, full_text, metadata = _convert_docling_to_parsed_elements(result)

    # Validate content
    if len(full_text) < MIN_CONTENT_CHARS:
        raise InsufficientContentError(
            f"Insufficient content extracted ({len(full_text)} chars, minimum {MIN_CONTENT_CHARS})"
        )

    metadata["source_format"] = "pdf"

    # Generate markdown
    markdown_content = None
    if config.generate_markdown:
        # Use Docling's native markdown export for best quality
        try:
            markdown_content = result.document.export_to_markdown()
        except Exception:
            # Fallback to our converter
            markdown_content = _docling_elements_to_markdown(elements)

    logger.info(
        "parsing_pdf_docling_completed",
        file_path=file_path,
        extracted_chars=len(full_text),
        page_count=metadata.get("page_count"),
        element_count=len(elements),
        markdown_chars=len(markdown_content) if markdown_content else 0,
    )

    return ParsedContent(
        text=full_text,
        elements=elements,
        metadata=metadata,
        markdown_content=markdown_content,
    )


def parse_docx_docling(
    file_path: str,
    config: DoclingParserConfig | None = None,
) -> ParsedContent:
    """Parse a DOCX document using Docling.

    Story 7-32 (AC-7.32.3): Docling parser for DOCX with enhanced structure.

    Args:
        file_path: Path to the DOCX file.
        config: Optional parser configuration.

    Returns:
        ParsedContent with extracted text and metadata.

    Raises:
        DoclingNotAvailableError: If Docling is not installed.
        InsufficientContentError: If extracted text is below minimum.
        ParsingError: For other parsing failures.
    """
    if not _check_docling_available():
        raise DoclingNotAvailableError(
            "Docling library not installed. Install with: pip install docling"
        )

    config = config or DoclingParserConfig()

    logger.info("parsing_docx_docling_started", file_path=file_path)

    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(file_path)

    except Exception as e:
        raise ParsingError(f"Docling failed to parse DOCX: {e}") from e

    # Convert to our format
    elements, full_text, metadata = _convert_docling_to_parsed_elements(result)

    # Validate content
    if len(full_text) < MIN_CONTENT_CHARS:
        raise InsufficientContentError(
            f"Insufficient content extracted ({len(full_text)} chars, minimum {MIN_CONTENT_CHARS})"
        )

    metadata["source_format"] = "docx"

    # Extract sections for DOCX metadata compatibility
    sections = [el.text for el in elements if el.element_type in ("Title", "Header")]
    metadata["sections"] = sections[:20]

    # Generate markdown
    markdown_content = None
    if config.generate_markdown:
        try:
            markdown_content = result.document.export_to_markdown()
        except Exception:
            markdown_content = _docling_elements_to_markdown(elements)

    logger.info(
        "parsing_docx_docling_completed",
        file_path=file_path,
        extracted_chars=len(full_text),
        section_count=metadata.get("section_count"),
        element_count=len(elements),
        markdown_chars=len(markdown_content) if markdown_content else 0,
    )

    return ParsedContent(
        text=full_text,
        elements=elements,
        metadata=metadata,
        markdown_content=markdown_content,
    )


def parse_markdown_docling(
    file_path: str,
    config: DoclingParserConfig | None = None,
) -> ParsedContent:
    """Parse a Markdown document using Docling.

    Story 7-32 (AC-7.32.3): Docling parser for Markdown with structure analysis.

    Note: For markdown files, Docling provides limited benefit over direct parsing.
    This function exists for API consistency and potential future enhancements.

    Args:
        file_path: Path to the Markdown file.
        config: Optional parser configuration.

    Returns:
        ParsedContent with extracted text and metadata.

    Raises:
        DoclingNotAvailableError: If Docling is not installed.
        InsufficientContentError: If extracted text is below minimum.
        ParsingError: For other parsing failures.
    """
    if not _check_docling_available():
        raise DoclingNotAvailableError(
            "Docling library not installed. Install with: pip install docling"
        )

    config = config or DoclingParserConfig()

    logger.info("parsing_markdown_docling_started", file_path=file_path)

    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(file_path)

    except Exception as e:
        raise ParsingError(f"Docling failed to parse Markdown: {e}") from e

    # Convert to our format
    elements, full_text, metadata = _convert_docling_to_parsed_elements(result)

    # Validate content
    if len(full_text) < MIN_CONTENT_CHARS:
        raise InsufficientContentError(
            f"Insufficient content extracted ({len(full_text)} chars, minimum {MIN_CONTENT_CHARS})"
        )

    metadata["source_format"] = "markdown"

    # Extract headings for markdown metadata compatibility
    headings = []
    for el in elements:
        if el.element_type == "Title":
            headings.append({"level": 1, "text": el.text})
        elif el.element_type == "Header":
            level = el.metadata.get("heading_level", 2)
            headings.append({"level": level, "text": el.text})
    metadata["headings"] = headings[:30]

    # For markdown, the original file is already markdown
    # Read it directly for markdown_content
    markdown_content = None
    if config.generate_markdown:
        try:
            with open(file_path, encoding="utf-8") as f:
                markdown_content = f.read()
        except Exception:
            markdown_content = _docling_elements_to_markdown(elements)

    logger.info(
        "parsing_markdown_docling_completed",
        file_path=file_path,
        extracted_chars=len(full_text),
        heading_count=len(headings),
        element_count=len(elements),
    )

    return ParsedContent(
        text=full_text,
        elements=elements,
        metadata=metadata,
        markdown_content=markdown_content,
    )


def parse_document_docling(
    file_path: str,
    mime_type: str,
    config: DoclingParserConfig | None = None,
) -> ParsedContent:
    """Parse a document using Docling based on MIME type.

    Story 7-32 (AC-7.32.3): Unified Docling parser entry point.

    Args:
        file_path: Path to the document file.
        mime_type: MIME type of the document.
        config: Optional parser configuration.

    Returns:
        ParsedContent with extracted text and metadata.

    Raises:
        DoclingNotAvailableError: If Docling is not installed.
        ParsingError: If MIME type is unsupported or parsing fails.
    """
    mime_parsers = {
        "application/pdf": parse_pdf_docling,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": parse_docx_docling,
        "text/markdown": parse_markdown_docling,
        "text/x-markdown": parse_markdown_docling,
    }

    parser = mime_parsers.get(mime_type)
    if not parser:
        raise ParsingError(f"Unsupported MIME type for Docling: {mime_type}")

    return parser(file_path, config)
