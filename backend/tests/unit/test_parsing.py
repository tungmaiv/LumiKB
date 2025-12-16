"""Unit tests for document parsing utilities.

Tests parsing functions with mocked unstructured library responses.
Focuses on:
- PDF parsing with page metadata
- DOCX parsing with section headers
- Markdown parsing with heading structure
- Empty document detection (<100 chars)
- Scanned PDF detection
- Password-protected PDF handling
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.unit


# Check if unstructured is available for integration tests
try:
    import unstructured  # noqa: F401

    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False


class TestParsedContent:
    """Tests for ParsedContent dataclass."""

    def test_extracted_chars(self) -> None:
        """Test extracted_chars property."""
        from app.workers.parsing import ParsedContent

        content = ParsedContent(
            text="Hello world",
            elements=[],
            metadata={},
        )
        assert content.extracted_chars == 11

    def test_page_count_present(self) -> None:
        """Test page_count when present in metadata."""
        from app.workers.parsing import ParsedContent

        content = ParsedContent(
            text="Test",
            elements=[],
            metadata={"page_count": 5},
        )
        assert content.page_count == 5

    def test_page_count_missing(self) -> None:
        """Test page_count when not in metadata."""
        from app.workers.parsing import ParsedContent

        content = ParsedContent(
            text="Test",
            elements=[],
            metadata={},
        )
        assert content.page_count is None

    def test_section_count(self) -> None:
        """Test section_count property."""
        from app.workers.parsing import ParsedContent

        content = ParsedContent(
            text="Test",
            elements=[],
            metadata={"section_count": 3},
        )
        assert content.section_count == 3


@pytest.fixture
def mock_unstructured():
    """Setup mock unstructured module for testing.

    This fixture creates mock versions of unstructured submodules
    and injects them into sys.modules before tests run.
    """
    # Create mock partition functions
    mock_pdf = MagicMock()
    mock_docx = MagicMock()
    mock_md = MagicMock()

    # Create mock modules
    mock_unstructured_pkg = MagicMock()
    mock_partition = MagicMock()
    mock_partition_pdf = MagicMock()
    mock_partition_docx = MagicMock()
    mock_partition_md = MagicMock()

    mock_partition_pdf.partition_pdf = mock_pdf
    mock_partition_docx.partition_docx = mock_docx
    mock_partition_md.partition_md = mock_md

    # Store original modules
    original_modules = {}
    modules_to_mock = [
        "unstructured",
        "unstructured.partition",
        "unstructured.partition.pdf",
        "unstructured.partition.docx",
        "unstructured.partition.md",
    ]

    for mod in modules_to_mock:
        if mod in sys.modules:
            original_modules[mod] = sys.modules[mod]

    # Inject mocks
    sys.modules["unstructured"] = mock_unstructured_pkg
    sys.modules["unstructured.partition"] = mock_partition
    sys.modules["unstructured.partition.pdf"] = mock_partition_pdf
    sys.modules["unstructured.partition.docx"] = mock_partition_docx
    sys.modules["unstructured.partition.md"] = mock_partition_md

    # Reload parsing module to use mocks
    if "app.workers.parsing" in sys.modules:
        del sys.modules["app.workers.parsing"]

    yield {
        "partition_pdf": mock_pdf,
        "partition_docx": mock_docx,
        "partition_md": mock_md,
    }

    # Cleanup - restore original modules
    for mod in modules_to_mock:
        if mod in original_modules:
            sys.modules[mod] = original_modules[mod]
        else:
            sys.modules.pop(mod, None)

    # Clear cached parsing module
    if "app.workers.parsing" in sys.modules:
        del sys.modules["app.workers.parsing"]


class TestParsePdf:
    """Tests for PDF parsing function."""

    def test_parse_pdf_success(self, mock_unstructured) -> None:
        """Test successful PDF parsing with text and page metadata."""
        from app.workers.parsing import parse_pdf

        mock_partition = mock_unstructured["partition_pdf"]

        # Create mock elements with metadata
        mock_element1 = MagicMock()
        mock_element1.text = (
            "This is the first paragraph of the document with enough content."
        )
        mock_element1.metadata = MagicMock()
        mock_element1.metadata.page_number = 1
        mock_element1.metadata.coordinates = None
        type(mock_element1).__name__ = "NarrativeText"

        mock_element2 = MagicMock()
        mock_element2.text = "This is the second paragraph on page two with additional content for testing purposes."
        mock_element2.metadata = MagicMock()
        mock_element2.metadata.page_number = 2
        mock_element2.metadata.coordinates = None
        type(mock_element2).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_element1, mock_element2]

        result = parse_pdf("/tmp/test.pdf")

        assert result.extracted_chars > 100
        assert len(result.elements) == 2
        assert result.metadata["source_format"] == "pdf"
        mock_partition.assert_called_once_with(
            filename="/tmp/test.pdf", strategy="fast"
        )

    def test_parse_pdf_extracts_page_numbers(self, mock_unstructured) -> None:
        """Test that page numbers are extracted from element metadata."""
        from app.workers.parsing import parse_pdf

        mock_partition = mock_unstructured["partition_pdf"]

        mock_element = MagicMock()
        mock_element.text = "A" * 150  # Enough content
        mock_element.metadata = MagicMock()
        mock_element.metadata.page_number = 3
        mock_element.metadata.coordinates = None
        type(mock_element).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_element]

        result = parse_pdf("/tmp/test.pdf")

        assert result.elements[0].metadata.get("page_number") == 3
        assert result.metadata["page_count"] == 3

    def test_parse_pdf_scanned_document(self, mock_unstructured) -> None:
        """Test detection of scanned PDF (no text elements)."""
        from app.workers.parsing import ScannedDocumentError, parse_pdf

        mock_partition = mock_unstructured["partition_pdf"]
        mock_partition.return_value = []

        with pytest.raises(ScannedDocumentError) as exc_info:
            parse_pdf("/tmp/scanned.pdf")

        assert "no text could be extracted" in str(exc_info.value).lower()
        assert "OCR failed" in str(exc_info.value)

    def test_parse_pdf_password_protected(self, mock_unstructured) -> None:
        """Test handling of password-protected PDF."""
        from app.workers.parsing import PasswordProtectedError, parse_pdf

        mock_partition = mock_unstructured["partition_pdf"]
        mock_partition.side_effect = Exception("Cannot decrypt password-protected PDF")

        with pytest.raises(PasswordProtectedError) as exc_info:
            parse_pdf("/tmp/protected.pdf")

        assert "Password-protected" in str(exc_info.value)

    def test_parse_pdf_insufficient_content(self, mock_unstructured) -> None:
        """Test detection of document with less than 100 chars."""
        from app.workers.parsing import InsufficientContentError, parse_pdf

        mock_partition = mock_unstructured["partition_pdf"]

        mock_element = MagicMock()
        mock_element.text = "Short"  # Only 5 chars
        mock_element.metadata = MagicMock()
        mock_element.metadata.page_number = 1
        mock_element.metadata.coordinates = None
        type(mock_element).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_element]

        with pytest.raises(InsufficientContentError) as exc_info:
            parse_pdf("/tmp/short.pdf")

        assert "5 chars" in str(exc_info.value)
        assert "minimum 100" in str(exc_info.value)


class TestParseDocx:
    """Tests for DOCX parsing function."""

    def test_parse_docx_success(self, mock_unstructured) -> None:
        """Test successful DOCX parsing."""
        from app.workers.parsing import parse_docx

        mock_partition = mock_unstructured["partition_docx"]

        mock_title = MagicMock()
        mock_title.text = "Document Title"
        type(mock_title).__name__ = "Title"

        mock_content = MagicMock()
        mock_content.text = "This is the main content of the document with enough text to pass all validation checks. Adding more content here to ensure we exceed the minimum threshold."
        type(mock_content).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_title, mock_content]

        result = parse_docx("/tmp/test.docx")

        assert result.extracted_chars > 100
        assert result.metadata["source_format"] == "docx"
        assert result.metadata["section_count"] == 1  # Title counted as section

    def test_parse_docx_extracts_headers(self, mock_unstructured) -> None:
        """Test that section headers are extracted."""
        from app.workers.parsing import parse_docx

        mock_partition = mock_unstructured["partition_docx"]

        mock_header1 = MagicMock()
        mock_header1.text = "Introduction"
        type(mock_header1).__name__ = "Title"

        mock_header2 = MagicMock()
        mock_header2.text = "Background"
        type(mock_header2).__name__ = "Header"

        mock_content = MagicMock()
        mock_content.text = "A" * 100  # Enough content
        type(mock_content).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_header1, mock_header2, mock_content]

        result = parse_docx("/tmp/test.docx")

        assert result.metadata["section_count"] == 2
        assert "Introduction" in result.metadata["sections"]
        assert "Background" in result.metadata["sections"]

    def test_parse_docx_insufficient_content(self, mock_unstructured) -> None:
        """Test detection of DOCX with insufficient content."""
        from app.workers.parsing import InsufficientContentError, parse_docx

        mock_partition = mock_unstructured["partition_docx"]

        mock_element = MagicMock()
        mock_element.text = "X" * 50  # Only 50 chars
        type(mock_element).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_element]

        with pytest.raises(InsufficientContentError):
            parse_docx("/tmp/short.docx")


class TestParseMarkdown:
    """Tests for Markdown parsing function."""

    def test_parse_markdown_success(self, mock_unstructured) -> None:
        """Test successful Markdown parsing."""
        from app.workers.parsing import parse_markdown

        mock_partition = mock_unstructured["partition_md"]

        mock_title = MagicMock()
        mock_title.text = "Main Heading"
        mock_title.metadata = MagicMock()
        mock_title.metadata.category_depth = None
        type(mock_title).__name__ = "Title"

        mock_content = MagicMock()
        mock_content.text = "This is the content under the heading with sufficient text for validation. Adding more content to ensure we reach the minimum threshold of 100 characters."
        mock_content.metadata = MagicMock()
        mock_content.metadata.category_depth = None
        type(mock_content).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_title, mock_content]

        result = parse_markdown("/tmp/test.md")

        assert result.extracted_chars > 100
        assert result.metadata["source_format"] == "markdown"

    def test_parse_markdown_extracts_headings(self, mock_unstructured) -> None:
        """Test that heading structure is extracted."""
        from app.workers.parsing import parse_markdown

        mock_partition = mock_unstructured["partition_md"]

        mock_h1 = MagicMock()
        mock_h1.text = "Top Level"
        mock_h1.metadata = MagicMock()
        mock_h1.metadata.category_depth = None
        type(mock_h1).__name__ = "Title"

        mock_h2 = MagicMock()
        mock_h2.text = "Second Level"
        mock_h2.metadata = MagicMock()
        mock_h2.metadata.category_depth = 2
        type(mock_h2).__name__ = "Header"

        mock_content = MagicMock()
        mock_content.text = "B" * 100
        mock_content.metadata = MagicMock()
        mock_content.metadata.category_depth = None
        type(mock_content).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_h1, mock_h2, mock_content]

        result = parse_markdown("/tmp/test.md")

        assert result.metadata["section_count"] == 2
        headings = result.metadata["headings"]
        assert any(h["text"] == "Top Level" and h["level"] == 1 for h in headings)
        assert any(h["text"] == "Second Level" and h["level"] == 2 for h in headings)


class TestParseDocument:
    """Tests for generic parse_document dispatcher."""

    def test_parse_document_unsupported_mime(self) -> None:
        """Test error for unsupported MIME type."""
        from app.workers.parsing import ParsingError, parse_document

        with pytest.raises(ParsingError) as exc_info:
            parse_document("/tmp/test.txt", "text/plain")

        assert "Unsupported MIME type" in str(exc_info.value)

    def test_parse_document_routes_pdf(self, mock_unstructured) -> None:
        """Test PDF MIME type routes to parse_pdf."""
        from app.workers.parsing import parse_document

        mock_partition = mock_unstructured["partition_pdf"]

        # Setup mock to return sufficient content
        mock_element = MagicMock()
        mock_element.text = "A" * 200
        mock_element.metadata = MagicMock()
        mock_element.metadata.page_number = 1
        mock_element.metadata.coordinates = None
        type(mock_element).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_element]

        result = parse_document("/tmp/test.pdf", "application/pdf")

        assert result.extracted_chars >= 200
        mock_partition.assert_called_once()

    def test_parse_document_routes_docx(self, mock_unstructured) -> None:
        """Test DOCX MIME type routes to parse_docx."""
        from app.workers.parsing import parse_document

        mock_partition = mock_unstructured["partition_docx"]

        mock_element = MagicMock()
        mock_element.text = "A" * 200
        type(mock_element).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_element]

        result = parse_document(
            "/tmp/test.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        assert result.extracted_chars >= 200
        mock_partition.assert_called_once()

    def test_parse_document_routes_markdown(self, mock_unstructured) -> None:
        """Test Markdown MIME type routes to parse_markdown."""
        from app.workers.parsing import parse_document

        mock_partition = mock_unstructured["partition_md"]

        mock_element = MagicMock()
        mock_element.text = "A" * 200
        mock_element.metadata = MagicMock()
        mock_element.metadata.category_depth = None
        type(mock_element).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_element]

        result = parse_document("/tmp/test.md", "text/markdown")

        assert result.extracted_chars >= 200
        mock_partition.assert_called_once()


class TestParseMarkdownIntegration:
    """Integration test using real sample.md fixture."""

    @pytest.mark.skipif(
        not UNSTRUCTURED_AVAILABLE, reason="unstructured library not installed"
    )
    def test_parse_real_markdown_file(self) -> None:
        """Test parsing the actual sample.md test fixture."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "sample.md"

        if not fixture_path.exists():
            pytest.skip("Fixture sample.md not found")

        from app.workers.parsing import parse_markdown

        result = parse_markdown(str(fixture_path))

        # Verify basic extraction worked
        assert result.extracted_chars > 100
        assert result.metadata["source_format"] == "markdown"
        assert len(result.elements) > 0
        # Sample has multiple headings
        assert result.metadata["section_count"] > 0


class TestElementsToMarkdown:
    """Tests for elements_to_markdown function (Story 7.28 AC-7.28.6)."""

    def test_empty_elements_returns_empty_string(self) -> None:
        """Test that empty elements list returns empty string."""
        from app.workers.parsing import elements_to_markdown

        result = elements_to_markdown([])
        assert result == ""

    def test_title_element_becomes_h1(self) -> None:
        """Test that Title element becomes # heading."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(text="Document Title", element_type="Title", metadata={})
        ]
        result = elements_to_markdown(elements)
        assert result == "# Document Title"

    def test_header_element_with_default_level(self) -> None:
        """Test Header element defaults to ## (level 2)."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(text="Section Header", element_type="Header", metadata={})
        ]
        result = elements_to_markdown(elements)
        assert result == "## Section Header"

    def test_header_element_with_custom_level(self) -> None:
        """Test Header element respects heading_level from metadata."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(
                text="Level 3 Header",
                element_type="Header",
                metadata={"heading_level": 3},
            ),
            ParsedElement(
                text="Level 4 Header",
                element_type="Header",
                metadata={"heading_level": 4},
            ),
        ]
        result = elements_to_markdown(elements)
        assert "### Level 3 Header" in result
        assert "#### Level 4 Header" in result

    def test_header_level_clamped_to_valid_range(self) -> None:
        """Test that heading levels are clamped to 1-6."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(
                text="Too Low", element_type="Header", metadata={"heading_level": 0}
            ),
            ParsedElement(
                text="Too High", element_type="Header", metadata={"heading_level": 10}
            ),
        ]
        result = elements_to_markdown(elements)
        # Level 0 should become level 1
        assert "# Too Low" in result
        # Level 10 should become level 6
        assert "###### Too High" in result

    def test_list_item_element(self) -> None:
        """Test ListItem elements become bulleted list."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(text="First item", element_type="ListItem", metadata={}),
            ParsedElement(text="Second item", element_type="ListItem", metadata={}),
        ]
        result = elements_to_markdown(elements)
        assert "- First item" in result
        assert "- Second item" in result

    def test_narrative_text_element(self) -> None:
        """Test NarrativeText elements become paragraphs with spacing."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(
                text="This is a paragraph.", element_type="NarrativeText", metadata={}
            )
        ]
        result = elements_to_markdown(elements)
        assert result == "This is a paragraph."

    def test_text_element_same_as_narrative(self) -> None:
        """Test Text elements are treated same as NarrativeText."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(text="Plain text content.", element_type="Text", metadata={})
        ]
        result = elements_to_markdown(elements)
        assert result == "Plain text content."

    def test_code_snippet_element(self) -> None:
        """Test CodeSnippet elements become code blocks."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        code = "def hello():\n    print('Hello')"
        elements = [ParsedElement(text=code, element_type="CodeSnippet", metadata={})]
        result = elements_to_markdown(elements)
        assert "```" in result
        assert code in result
        assert result.startswith("```\n")
        assert result.endswith("\n```")

    def test_figure_caption_element(self) -> None:
        """Test FigureCaption elements become italic text."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(
                text="Figure 1: Architecture diagram",
                element_type="FigureCaption",
                metadata={},
            )
        ]
        result = elements_to_markdown(elements)
        assert result == "*Figure 1: Architecture diagram*"

    def test_table_element_with_html(self) -> None:
        """Test Table element uses markdownify for HTML conversion."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        html_table = "<table><tr><th>Name</th><th>Value</th></tr><tr><td>A</td><td>1</td></tr></table>"
        elements = [
            ParsedElement(
                text="Name | Value",
                element_type="Table",
                metadata={"text_as_html": html_table},
            )
        ]
        result = elements_to_markdown(elements)
        # markdownify converts to markdown table format
        assert "Name" in result
        assert "Value" in result

    def test_table_element_without_html_fallback(self) -> None:
        """Test Table element falls back to plain text when no HTML."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(
                text="Column1 | Column2",
                element_type="Table",
                metadata={},  # No text_as_html
            )
        ]
        result = elements_to_markdown(elements)
        assert "Column1 | Column2" in result

    def test_unknown_element_type_becomes_paragraph(self) -> None:
        """Test unknown element types are treated as paragraphs."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(
                text="Unknown content", element_type="CustomElement", metadata={}
            )
        ]
        result = elements_to_markdown(elements)
        assert result == "Unknown content"

    def test_empty_text_elements_skipped(self) -> None:
        """Test that elements with empty text are skipped."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(text="", element_type="Title", metadata={}),
            ParsedElement(text="   ", element_type="NarrativeText", metadata={}),
            ParsedElement(text="Valid content", element_type="Text", metadata={}),
        ]
        result = elements_to_markdown(elements)
        assert result == "Valid content"

    def test_none_text_elements_skipped(self) -> None:
        """Test that elements with None text are handled gracefully."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        # Create element with explicit None-like behavior
        elements = [
            ParsedElement(text="", element_type="Title", metadata={}),
            ParsedElement(text="Valid", element_type="Text", metadata={}),
        ]
        result = elements_to_markdown(elements)
        assert result == "Valid"

    def test_mixed_element_types_preserve_order(self) -> None:
        """Test that mixed element types preserve document order."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(text="Document Title", element_type="Title", metadata={}),
            ParsedElement(
                text="Introduction paragraph.",
                element_type="NarrativeText",
                metadata={},
            ),
            ParsedElement(
                text="Section 1", element_type="Header", metadata={"heading_level": 2}
            ),
            ParsedElement(text="First point", element_type="ListItem", metadata={}),
            ParsedElement(text="Second point", element_type="ListItem", metadata={}),
        ]
        result = elements_to_markdown(elements)

        # Verify order is preserved
        lines = result.split("\n")
        title_idx = next(
            i for i, line in enumerate(lines) if "# Document Title" in line
        )
        intro_idx = next(
            i for i, line in enumerate(lines) if "Introduction paragraph" in line
        )
        section_idx = next(i for i, line in enumerate(lines) if "## Section 1" in line)
        first_idx = next(i for i, line in enumerate(lines) if "- First point" in line)
        second_idx = next(i for i, line in enumerate(lines) if "- Second point" in line)

        assert title_idx < intro_idx < section_idx < first_idx < second_idx

    def test_special_characters_preserved(self) -> None:
        """Test that special characters in text are preserved."""
        from app.workers.parsing import ParsedElement, elements_to_markdown

        elements = [
            ParsedElement(
                text="Code: `var x = 1;` and *emphasis*",
                element_type="NarrativeText",
                metadata={},
            ),
        ]
        result = elements_to_markdown(elements)
        assert "`var x = 1;`" in result
        assert "*emphasis*" in result


class TestParsedContentMarkdownField:
    """Tests for ParsedContent.markdown_content field (Story 7.28 AC-7.28.3)."""

    def test_markdown_content_field_default_none(self) -> None:
        """Test that markdown_content defaults to None."""
        from app.workers.parsing import ParsedContent

        content = ParsedContent(text="Test", elements=[], metadata={})
        assert content.markdown_content is None

    def test_markdown_content_field_can_be_set(self) -> None:
        """Test that markdown_content can be set to a string."""
        from app.workers.parsing import ParsedContent

        content = ParsedContent(
            text="Test",
            elements=[],
            metadata={},
            markdown_content="# Heading\n\nParagraph",
        )
        assert content.markdown_content == "# Heading\n\nParagraph"

    def test_parse_pdf_generates_markdown(self, mock_unstructured) -> None:
        """Test that parse_pdf populates markdown_content field."""
        from app.workers.parsing import parse_pdf

        mock_partition = mock_unstructured["partition_pdf"]

        mock_title = MagicMock()
        mock_title.text = "PDF Document Title"
        mock_title.metadata = MagicMock()
        mock_title.metadata.page_number = 1
        mock_title.metadata.coordinates = None
        type(mock_title).__name__ = "Title"

        mock_content = MagicMock()
        mock_content.text = "This is the main content of the PDF document with enough text to pass validation checks and meet the minimum threshold."
        mock_content.metadata = MagicMock()
        mock_content.metadata.page_number = 1
        mock_content.metadata.coordinates = None
        type(mock_content).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_title, mock_content]

        result = parse_pdf("/tmp/test.pdf")

        assert result.markdown_content is not None
        assert "# PDF Document Title" in result.markdown_content
        assert "main content" in result.markdown_content

    def test_parse_docx_generates_markdown(self, mock_unstructured) -> None:
        """Test that parse_docx populates markdown_content field."""
        from app.workers.parsing import parse_docx

        mock_partition = mock_unstructured["partition_docx"]

        mock_title = MagicMock()
        mock_title.text = "DOCX Document Title"
        type(mock_title).__name__ = "Title"

        mock_content = MagicMock()
        mock_content.text = "This is the main content of the DOCX document with sufficient text to pass all validation requirements."
        type(mock_content).__name__ = "NarrativeText"

        mock_partition.return_value = [mock_title, mock_content]

        result = parse_docx("/tmp/test.docx")

        assert result.markdown_content is not None
        assert "# DOCX Document Title" in result.markdown_content
        assert "main content" in result.markdown_content
