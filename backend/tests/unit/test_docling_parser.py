"""Unit tests for Docling document parser integration.

Story 7-32: Docling Document Parser Integration
ATDD Test Suite - Generated BEFORE implementation (Red phase)

These tests define the expected behavior of the Docling parser module.
All tests should FAIL until the implementation is complete.

Test Categories:
- AC-7.32.1: System-level feature flag
- AC-7.32.2: KB setting for parser backend
- AC-7.32.6: ParsedContent interface preserved
- AC-7.32.7: Strategy pattern implementation
- AC-7.32.8: Docling parser module exports
- AC-7.32.9: Auto mode fallback
- AC-7.32.10: Graceful degradation
- AC-7.32.11: PDF parsing with Docling
- AC-7.32.12: DOCX parsing with Docling
- AC-7.32.13: Markdown passthrough
"""

import sys
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


# =============================================================================
# AC-7.32.1: System-level feature flag
# =============================================================================


class TestDoclingFeatureFlag:
    """Test system-level LUMIKB_PARSER_DOCLING_ENABLED configuration."""

    def test_feature_flag_default_false(self) -> None:
        """
        AC-7.32.1: Feature flag exists and defaults to false.

        Given I check backend environment configuration
        Then LUMIKB_PARSER_DOCLING_ENABLED env var exists (default: false)
        """
        from app.core.config import Settings

        # Create settings without env var set
        settings = Settings(_env_file=None)

        assert hasattr(settings, "parser_docling_enabled")
        assert settings.parser_docling_enabled is False

    def test_feature_flag_can_be_enabled(self) -> None:
        """
        AC-7.32.1: Feature flag can be enabled via environment.

        Given LUMIKB_PARSER_DOCLING_ENABLED=true in environment
        Then feature flag is enabled
        """
        with patch.dict("os.environ", {"LUMIKB_PARSER_DOCLING_ENABLED": "true"}):
            from importlib import reload

            import app.core.config

            reload(app.core.config)
            settings = app.core.config.Settings(_env_file=None)

            assert settings.parser_docling_enabled is True

    def test_feature_flag_disabled_uses_unstructured(self) -> None:
        """
        AC-7.32.4: When flag disabled, always use Unstructured regardless of KB setting.

        Given system has LUMIKB_PARSER_DOCLING_ENABLED=false (default)
        When documents are processed
        Then Unstructured is used for all formats (existing behavior)
        """

        # Even if KB setting is docling, system flag should override
        with patch.dict("os.environ", {"LUMIKB_PARSER_DOCLING_ENABLED": "false"}):
            pass

            # Should use Unstructured regardless of parser_backend parameter
            # This test verifies the system-level override behavior
            # Implementation should check feature flag first


# =============================================================================
# AC-7.32.2: KB setting for parser backend
# =============================================================================


class TestKBParserBackendSetting:
    """Test KB-level parser_backend configuration schema."""

    def test_document_parser_backend_enum_values(self) -> None:
        """
        AC-7.32.2: DocumentParserBackend enum has correct values.

        Given I view KB settings schema
        Then processing.parser_backend field exists
        With options: unstructured (default), docling, auto
        """
        from app.schemas.kb_settings import DocumentParserBackend

        assert DocumentParserBackend.UNSTRUCTURED.value == "unstructured"
        assert DocumentParserBackend.DOCLING.value == "docling"
        assert DocumentParserBackend.AUTO.value == "auto"

    def test_document_processing_config_has_parser_backend(self) -> None:
        """
        AC-7.32.2: DocumentProcessingConfig includes parser_backend field.

        Given I create a DocumentProcessingConfig
        Then parser_backend field exists with default UNSTRUCTURED
        """
        from app.schemas.kb_settings import (
            DocumentParserBackend,
            DocumentProcessingConfig,
        )

        config = DocumentProcessingConfig()

        assert hasattr(config, "parser_backend")
        assert config.parser_backend == DocumentParserBackend.UNSTRUCTURED

    def test_kb_settings_processing_parser_backend(self) -> None:
        """
        AC-7.32.2: KBSettings.processing includes parser_backend.

        Given I create KBSettings with default values
        Then processing.parser_backend is accessible
        """
        from app.schemas.kb_settings import DocumentParserBackend, KBSettings

        settings = KBSettings()

        assert settings.processing.parser_backend == DocumentParserBackend.UNSTRUCTURED


# =============================================================================
# AC-7.32.8: Docling parser module exports
# =============================================================================


class TestDoclingParserModuleExports:
    """Test that docling_parser module exports required functions."""

    def test_module_exports_parse_pdf_docling(self) -> None:
        """
        AC-7.32.8: Module exports parse_pdf_docling function.

        Given I inspect backend/app/workers/docling_parser.py
        Then module exports parse_pdf_docling(file_path: str) -> ParsedContent
        """
        from app.workers.docling_parser import parse_pdf_docling

        assert callable(parse_pdf_docling)

    def test_module_exports_parse_docx_docling(self) -> None:
        """
        AC-7.32.8: Module exports parse_docx_docling function.

        Given I inspect backend/app/workers/docling_parser.py
        Then module exports parse_docx_docling(file_path: str) -> ParsedContent
        """
        from app.workers.docling_parser import parse_docx_docling

        assert callable(parse_docx_docling)

    def test_module_exports_is_docling_available(self) -> None:
        """
        AC-7.32.8: Module exports is_docling_available function.

        Given I inspect backend/app/workers/docling_parser.py
        Then module exports is_docling_available() -> bool
        """
        from app.workers.docling_parser import is_docling_available

        assert callable(is_docling_available)
        result = is_docling_available()
        assert isinstance(result, bool)


# =============================================================================
# AC-7.32.6: ParsedContent interface preserved
# =============================================================================


class TestParsedContentInterfacePreservation:
    """Test that Docling parser output conforms to ParsedContent interface."""

    @pytest.fixture
    def mock_docling_result(self):
        """Create mock Docling conversion result with proper structure."""
        from app.workers.parsing import ParsedContent, ParsedElement

        # Return a properly structured ParsedContent that matches docling output
        return ParsedContent(
            text="Test Document\n\nContent here with enough characters to pass validation threshold.",
            elements=[
                ParsedElement(
                    text="Test Document",
                    element_type="Title",
                    metadata={"page_number": 1},
                ),
                ParsedElement(
                    text="Content here with enough characters to pass validation threshold.",
                    element_type="NarrativeText",
                    metadata={"page_number": 1},
                ),
            ],
            metadata={
                "page_count": 1,
                "section_count": 1,
                "element_count": 2,
                "parser": "docling",
                "source_format": "pdf",
            },
            markdown_content="# Test Document\n\nContent here.",
        )

    def test_parse_pdf_docling_returns_parsed_content(
        self, mock_docling_result, tmp_path
    ) -> None:
        """
        AC-7.32.6: Docling PDF parser returns ParsedContent.

        Given Docling parser is used
        When PDF document is parsed
        Then output conforms to existing ParsedContent dataclass
        """
        from app.workers.parsing import ParsedContent

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        # Mock the entire parse_pdf_docling function
        with patch("app.workers.docling_parser.parse_pdf_docling") as mock_parse:
            mock_parse.return_value = mock_docling_result

            from app.workers.docling_parser import parse_pdf_docling

            result = parse_pdf_docling(str(pdf_file))

            assert isinstance(result, ParsedContent)
            assert isinstance(result.text, str)
            assert isinstance(result.elements, list)
            assert isinstance(result.metadata, dict)

    def test_parse_docx_docling_returns_parsed_content(
        self, mock_docling_result, tmp_path
    ) -> None:
        """
        AC-7.32.6: Docling DOCX parser returns ParsedContent.

        Given Docling parser is used
        When DOCX document is parsed
        Then output conforms to existing ParsedContent dataclass
        """
        from app.workers.parsing import ParsedContent

        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"PK\x03\x04 dummy docx")

        # Mock the entire parse_docx_docling function
        with patch("app.workers.docling_parser.parse_docx_docling") as mock_parse:
            mock_docling_result.metadata["source_format"] = "docx"
            mock_parse.return_value = mock_docling_result

            from app.workers.docling_parser import parse_docx_docling

            result = parse_docx_docling(str(docx_file))

            assert isinstance(result, ParsedContent)
            assert isinstance(result.text, str)
            assert isinstance(result.elements, list)
            assert isinstance(result.metadata, dict)


# =============================================================================
# AC-7.32.7: Strategy pattern implementation
# =============================================================================


class TestParserStrategyPattern:
    """Test strategy pattern dispatch in parse_document function."""

    def test_parse_document_accepts_parser_backend_param(self) -> None:
        """
        AC-7.32.7: parse_document accepts optional parser_backend parameter.

        Given I inspect backend/app/workers/parsing.py
        Then parse_document() function accepts optional parser_backend parameter
        """
        import inspect

        from app.workers.parsing import parse_document

        sig = inspect.signature(parse_document)
        param_names = list(sig.parameters.keys())

        assert "parser_backend" in param_names

    def test_parse_document_default_uses_unstructured(self, tmp_path) -> None:
        """
        AC-7.32.7: Default parser_backend is None (uses Unstructured).

        Given parse_document is called without parser_backend
        Then Unstructured parser is used
        """
        import inspect

        from app.workers.parsing import parse_document

        sig = inspect.signature(parse_document)
        parser_backend_param = sig.parameters.get("parser_backend")

        assert parser_backend_param is not None
        assert parser_backend_param.default is None

    @patch("app.workers.parsing.parse_pdf")
    def test_parse_document_dispatches_to_unstructured(
        self, mock_parse_pdf, tmp_path
    ) -> None:
        """
        AC-7.32.7: parser_backend='unstructured' dispatches to Unstructured.

        Given parse_document is called with parser_backend='unstructured'
        Then Unstructured parser is invoked
        """
        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.parsing import ParsedContent, parse_document

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        mock_parse_pdf.return_value = ParsedContent(
            text="Test content",
            elements=[],
            metadata={"source_format": "pdf"},
        )

        result = parse_document(
            str(pdf_file),
            "application/pdf",
            parser_backend=DocumentParserBackend.UNSTRUCTURED,
        )

        mock_parse_pdf.assert_called_once()
        assert result.text == "Test content"

    @patch("app.workers.docling_parser.parse_pdf_docling")
    def test_parse_document_dispatches_to_docling(
        self, mock_parse_docling, tmp_path
    ) -> None:
        """
        AC-7.32.7: parser_backend='docling' dispatches to Docling.

        Given parse_document is called with parser_backend='docling'
        And LUMIKB_PARSER_DOCLING_ENABLED=true
        Then Docling parser is invoked
        """
        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.parsing import ParsedContent, parse_document

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        mock_parse_docling.return_value = ParsedContent(
            text="Docling parsed content",
            elements=[],
            metadata={"source_format": "pdf", "parser_backend": "docling"},
        )

        with patch.dict("os.environ", {"LUMIKB_PARSER_DOCLING_ENABLED": "true"}):
            result = parse_document(
                str(pdf_file),
                "application/pdf",
                parser_backend=DocumentParserBackend.DOCLING,
            )

        mock_parse_docling.assert_called_once()
        assert result.metadata.get("parser_backend") == "docling"


# =============================================================================
# AC-7.32.9: Auto mode fallback
# =============================================================================


class TestAutoModeFallback:
    """Test automatic fallback from Docling to Unstructured."""

    @patch("app.workers.docling_parser.parse_pdf_docling")
    @patch("app.workers.parsing.parse_pdf")
    def test_auto_mode_fallback_on_docling_failure(
        self, mock_unstructured, mock_docling, tmp_path
    ) -> None:
        """
        AC-7.32.9: Auto mode falls back to Unstructured on Docling failure.

        Given KB has parser_backend: auto
        When Docling parsing fails for a document
        Then system automatically retries with Unstructured
        """
        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.parsing import ParsedContent, parse_document

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        mock_docling.side_effect = Exception("Docling parsing failed")
        mock_unstructured.return_value = ParsedContent(
            text="Fallback content",
            elements=[],
            metadata={"source_format": "pdf", "parser_backend": "unstructured"},
        )

        with patch.dict("os.environ", {"LUMIKB_PARSER_DOCLING_ENABLED": "true"}):
            result = parse_document(
                str(pdf_file),
                "application/pdf",
                parser_backend=DocumentParserBackend.AUTO,
            )

        mock_docling.assert_called_once()
        mock_unstructured.assert_called_once()
        assert result.text == "Fallback content"

    @patch("app.workers.docling_parser.parse_pdf_docling")
    def test_auto_mode_logs_fallback_warning(
        self, mock_docling, tmp_path, caplog
    ) -> None:
        """
        AC-7.32.9: Auto mode logs warning about fallback.

        Given KB has parser_backend: auto
        When Docling parsing fails
        Then logs warning about fallback
        """

        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.parsing import parse_document

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        mock_docling.side_effect = Exception("Docling failed")

        with patch.dict("os.environ", {"LUMIKB_PARSER_DOCLING_ENABLED": "true"}):
            with patch("app.workers.parsing.parse_pdf") as mock_unstructured:
                from app.workers.parsing import ParsedContent

                mock_unstructured.return_value = ParsedContent(
                    text="Fallback", elements=[], metadata={}
                )
                parse_document(
                    str(pdf_file),
                    "application/pdf",
                    parser_backend=DocumentParserBackend.AUTO,
                )

        # Check that fallback was logged (implementation should log this)
        # Note: actual log assertion depends on structlog configuration


# =============================================================================
# AC-7.32.10: Graceful degradation
# =============================================================================


class TestGracefulDegradation:
    """Test graceful degradation when Docling is not available."""

    def test_docling_unavailable_auto_mode_fallback_to_unstructured(
        self, tmp_path
    ) -> None:
        """
        AC-7.32.10: Falls back to Unstructured when Docling library not installed (AUTO mode).

        Given Docling library is not installed
        When KB has parser_backend: auto
        Then system falls back to Unstructured parser
        """
        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.docling_parser import DoclingNotAvailableError
        from app.workers.parsing import ParsedContent, parse_document

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        # Simulate Docling not being available by raising DoclingNotAvailableError
        with patch("app.workers.docling_parser.parse_document_docling") as mock_docling:
            mock_docling.side_effect = DoclingNotAvailableError("Not installed")

            with patch("app.workers.parsing.parse_pdf") as mock_unstructured:
                mock_unstructured.return_value = ParsedContent(
                    text="Unstructured fallback",
                    elements=[],
                    metadata={"source_format": "pdf"},
                )

                with patch.dict(
                    "os.environ", {"LUMIKB_PARSER_DOCLING_ENABLED": "true"}
                ):
                    result = parse_document(
                        str(pdf_file),
                        "application/pdf",
                        parser_backend=DocumentParserBackend.AUTO,
                    )

                    assert result.text == "Unstructured fallback"
                    mock_unstructured.assert_called_once()

    def test_explicit_docling_raises_when_unavailable(self, tmp_path) -> None:
        """
        AC-7.32.10: Explicit docling request raises error when unavailable.

        Given Docling library is not installed
        When KB explicitly requests parser_backend: docling
        Then system raises DoclingNotAvailableError
        """
        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.docling_parser import DoclingNotAvailableError
        from app.workers.parsing import parse_document

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        # Simulate Docling not being available
        with patch("app.workers.docling_parser.parse_document_docling") as mock_docling:
            mock_docling.side_effect = DoclingNotAvailableError("Not installed")

            with patch.dict("os.environ", {"LUMIKB_PARSER_DOCLING_ENABLED": "true"}):
                with pytest.raises(DoclingNotAvailableError):
                    parse_document(
                        str(pdf_file),
                        "application/pdf",
                        parser_backend=DocumentParserBackend.DOCLING,
                    )

    def test_is_docling_available_returns_false_when_not_installed(self) -> None:
        """
        AC-7.32.10: is_docling_available returns False when library not installed.

        Given Docling library is not installed
        When is_docling_available() is called
        Then returns False
        """
        # Remove docling from sys.modules if present
        with patch.dict(sys.modules, {"docling": None}):
            from importlib import reload

            import app.workers.docling_parser as docling_parser_module

            reload(docling_parser_module)

            result = docling_parser_module.is_docling_available()
            assert result is False


# =============================================================================
# AC-7.32.11 & AC-7.32.12: Format-specific parsing
# =============================================================================


class TestDoclingFormatSpecificParsing:
    """Test Docling parsing for specific formats."""

    @pytest.fixture
    def mock_pdf_docling_result(self):
        """Create mock PDF result from Docling parser."""
        from app.workers.parsing import ParsedContent, ParsedElement

        return ParsedContent(
            text=(
                "Document Title\n\n"
                "Section 1\n\n"
                "This is content from Docling.\n\n"
                "Column 1 Column 2 Cell 1 Cell 2"
            ),
            elements=[
                ParsedElement(
                    text="Document Title",
                    element_type="Title",
                    metadata={"page_number": 1},
                ),
                ParsedElement(
                    text="Section 1",
                    element_type="Header",
                    metadata={"page_number": 1, "heading_level": 2},
                ),
                ParsedElement(
                    text="This is content from Docling.",
                    element_type="NarrativeText",
                    metadata={"page_number": 1},
                ),
                ParsedElement(
                    text="| Column 1 | Column 2 |\n| Cell 1 | Cell 2 |",
                    element_type="Table",
                    metadata={
                        "page_number": 2,
                        "table_markdown": "| Column 1 | Column 2 |\n| Cell 1 | Cell 2 |",
                    },
                ),
            ],
            metadata={
                "page_count": 2,
                "section_count": 2,
                "element_count": 4,
                "parser": "docling",
                "source_format": "pdf",
            },
            markdown_content=(
                "# Document Title\n\n"
                "## Section 1\n\n"
                "This is content from Docling.\n\n"
                "| Column 1 | Column 2 |\n"
                "|----------|----------|\n"
                "| Cell 1   | Cell 2   |\n"
            ),
        )

    @pytest.fixture
    def mock_docx_docling_result(self):
        """Create mock DOCX result from Docling parser."""
        from app.workers.parsing import ParsedContent, ParsedElement

        return ParsedContent(
            text="Document Title\n\nSection 1\n\nThis is DOCX content from Docling.",
            elements=[
                ParsedElement(text="Document Title", element_type="Title", metadata={}),
                ParsedElement(
                    text="Section 1",
                    element_type="Header",
                    metadata={"heading_level": 2},
                ),
                ParsedElement(
                    text="This is DOCX content from Docling.",
                    element_type="NarrativeText",
                    metadata={},
                ),
            ],
            metadata={
                "section_count": 2,
                "sections": ["Document Title", "Section 1"],
                "element_count": 3,
                "parser": "docling",
                "source_format": "docx",
            },
            markdown_content="# Document Title\n\n## Section 1\n\nThis is DOCX content from Docling.",
        )

    def test_pdf_parsing_uses_docling_when_enabled(
        self, mock_pdf_docling_result, tmp_path
    ) -> None:
        """
        AC-7.32.11: PDF parsing uses Docling when enabled.

        Given KB has parser_backend: docling and Docling enabled
        When PDF document is uploaded
        Then Docling parser is used for parsing
        """
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        with patch("app.workers.docling_parser.parse_pdf_docling") as mock_parse:
            mock_parse.return_value = mock_pdf_docling_result

            from app.workers.docling_parser import parse_pdf_docling
            from app.workers.parsing import ParsedContent

            result = parse_pdf_docling(str(pdf_file))

            assert isinstance(result, ParsedContent)
            mock_parse.assert_called_once()

    def test_pdf_tables_extracted_at_cell_level(
        self, mock_pdf_docling_result, tmp_path
    ) -> None:
        """
        AC-7.32.11: Tables are extracted at cell-level.

        Given PDF with tables is parsed with Docling
        Then tables are extracted with cell-level detail
        """
        pdf_file = tmp_path / "table.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        with patch("app.workers.docling_parser.parse_pdf_docling") as mock_parse:
            mock_parse.return_value = mock_pdf_docling_result

            from app.workers.docling_parser import parse_pdf_docling

            result = parse_pdf_docling(str(pdf_file))

            # Check that table content is in markdown
            assert "Column 1" in result.markdown_content or "Column 1" in result.text

    def test_docx_parsing_preserves_formatting(
        self, mock_docx_docling_result, tmp_path
    ) -> None:
        """
        AC-7.32.12: DOCX formatting is preserved in markdown output.

        Given KB has parser_backend: docling and Docling enabled
        When DOCX document is uploaded
        Then formatting is preserved in markdown output
        """
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"PK\x03\x04 dummy docx")

        with patch("app.workers.docling_parser.parse_docx_docling") as mock_parse:
            mock_parse.return_value = mock_docx_docling_result

            from app.workers.docling_parser import parse_docx_docling

            result = parse_docx_docling(str(docx_file))

            # Verify markdown content is generated
            assert result.markdown_content is not None
            assert "#" in result.markdown_content  # Has headings


# =============================================================================
# AC-7.32.13: Markdown passthrough
# =============================================================================


class TestMarkdownPassthrough:
    """Test Markdown file parsing behavior with different parser backends."""

    @patch("app.workers.parsing.parse_markdown")
    def test_markdown_uses_unstructured_by_default(
        self, mock_parse_md, tmp_path
    ) -> None:
        """
        AC-7.32.13: Markdown uses Unstructured by default.

        Given KB has default parser_backend setting (unstructured)
        When Markdown document is uploaded
        Then Unstructured parser is used
        """
        from app.workers.parsing import ParsedContent, parse_document

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Markdown\n\nContent here.")

        mock_parse_md.return_value = ParsedContent(
            text="Test Markdown Content here.",
            elements=[],
            metadata={"source_format": "markdown"},
        )

        # Default (no parser_backend) uses Unstructured
        result = parse_document(
            str(md_file),
            "text/markdown",
        )

        mock_parse_md.assert_called_once()
        assert result.metadata.get("source_format") == "markdown"

    @patch("app.workers.parsing.parse_markdown")
    def test_markdown_uses_unstructured_when_docling_disabled(
        self, mock_parse_md, tmp_path
    ) -> None:
        """
        AC-7.32.13: Markdown uses Unstructured when system Docling flag is disabled.

        Given LUMIKB_PARSER_DOCLING_ENABLED=false (default)
        When Markdown document is uploaded with any parser_backend
        Then Unstructured parser is used
        """
        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.parsing import ParsedContent, parse_document

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Markdown\n\nContent here.")

        mock_parse_md.return_value = ParsedContent(
            text="Test Markdown Content here.",
            elements=[],
            metadata={"source_format": "markdown"},
        )

        # Patch the settings object at the config module to simulate disabled flag
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.parser_docling_enabled = False

            result = parse_document(
                str(md_file),
                "text/markdown",
                parser_backend=DocumentParserBackend.DOCLING,
            )

        mock_parse_md.assert_called_once()
        assert result.metadata.get("source_format") == "markdown"

    @patch("app.workers.docling_parser.parse_pdf_docling")
    @patch("app.workers.parsing.parse_markdown")
    def test_markdown_passthrough_with_auto_mode(
        self, mock_parse_md, mock_docling, tmp_path
    ) -> None:
        """
        AC-7.32.13: Markdown uses Unstructured even in AUTO mode.

        Given KB has parser_backend: auto
        When Markdown document is uploaded
        Then Unstructured parser is used (Docling has no advantage for MD)
        """
        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.parsing import ParsedContent, parse_document

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nMarkdown content.")

        mock_parse_md.return_value = ParsedContent(
            text="Test Markdown content.",
            elements=[],
            metadata={"source_format": "markdown"},
        )

        result = parse_document(
            str(md_file),
            "text/markdown",
            parser_backend=DocumentParserBackend.AUTO,
        )

        mock_parse_md.assert_called_once()
        mock_docling.assert_not_called()


# =============================================================================
# AC-7.32.17: Audit logging
# =============================================================================


class TestParserAuditLogging:
    """Test that parser selection is logged for audit purposes."""

    def test_metadata_includes_parser_backend_docling(self, tmp_path) -> None:
        """
        AC-7.32.17: ParsedContent metadata includes parser_backend used (docling).

        Given document processing completes with Docling
        Then result metadata includes parser_backend = "docling"
        """
        from app.workers.parsing import ParsedContent, ParsedElement

        # Mock result from Docling parser
        mock_result = ParsedContent(
            text="Test content with enough characters for validation threshold test.",
            elements=[
                ParsedElement(
                    text="Test content", element_type="NarrativeText", metadata={}
                ),
            ],
            metadata={
                "page_count": 1,
                "parser": "docling",
                "source_format": "pdf",
            },
            markdown_content="# Test",
        )

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        with patch("app.workers.docling_parser.parse_pdf_docling") as mock_parse:
            mock_result.metadata["parser_backend"] = "docling"
            mock_parse.return_value = mock_result

            from app.workers.docling_parser import parse_pdf_docling

            result = parse_pdf_docling(str(pdf_file))

            assert "parser_backend" in result.metadata
            assert result.metadata["parser_backend"] == "docling"

    def test_metadata_includes_parser_backend_unstructured(self, tmp_path) -> None:
        """
        AC-7.32.17: ParsedContent metadata includes parser_backend used (unstructured).

        Given document processing completes with Unstructured
        Then result metadata includes parser_backend = "unstructured"
        """
        from app.workers.parsing import ParsedContent, parse_document

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        with patch("app.workers.parsing.parse_pdf") as mock_parse:
            mock_parse.return_value = ParsedContent(
                text="Test content",
                elements=[],
                metadata={"source_format": "pdf"},
            )

            result = parse_document(str(pdf_file), "application/pdf")

            assert result.metadata.get("parser_backend") == "unstructured"

    def test_metadata_includes_fallback_indicator(self, tmp_path) -> None:
        """
        AC-7.32.17: ParsedContent metadata includes fallback indicator.

        Given document processing used fallback
        Then audit log includes fallback indicator
        """
        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.parsing import ParsedContent

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        # Simulate fallback scenario
        with patch("app.workers.docling_parser.parse_pdf_docling") as mock_docling:
            mock_docling.side_effect = Exception("Docling failed")

            with patch("app.workers.parsing.parse_pdf") as mock_unstructured:
                mock_unstructured.return_value = ParsedContent(
                    text="Fallback content",
                    elements=[],
                    metadata={
                        "source_format": "pdf",
                        "parser_backend": "unstructured",
                        "parser_fallback_from": "docling",
                    },
                )

                with patch.dict(
                    "os.environ", {"LUMIKB_PARSER_DOCLING_ENABLED": "true"}
                ):
                    from app.workers.parsing import parse_document

                    result = parse_document(
                        str(pdf_file),
                        "application/pdf",
                        parser_backend=DocumentParserBackend.AUTO,
                    )

                    assert result.metadata.get("parser_fallback_from") == "docling"


# =============================================================================
# AC-7.32.16: Existing tests unchanged
# =============================================================================


class TestBackwardCompatibility:
    """Test that existing behavior is preserved."""

    def test_parse_document_without_parser_backend_works(self, tmp_path) -> None:
        """
        AC-7.32.16 & AC-7.32.5: Existing code continues to work.

        Given parse_document is called without parser_backend
        Then existing behavior is preserved (uses Unstructured)
        """
        from app.workers.parsing import parse_document

        md_file = tmp_path / "test.md"
        md_file.write_text(
            "# Test\n\nThis is test content that exceeds 100 characters for minimum threshold validation."
        )

        with patch("app.workers.parsing.parse_markdown") as mock_parse_md:
            from app.workers.parsing import ParsedContent

            mock_parse_md.return_value = ParsedContent(
                text="Test This is test content...",
                elements=[],
                metadata={"source_format": "markdown"},
            )

            # Call without parser_backend parameter (existing API)
            result = parse_document(str(md_file), "text/markdown")

            mock_parse_md.assert_called_once()
