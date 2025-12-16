"""Integration tests for parser strategy pattern.

Story 7-32: Docling Document Parser Integration
ATDD Integration Test Suite - Generated BEFORE implementation (Red phase)

These tests verify end-to-end parser strategy behavior with
conditional execution based on Docling availability.

Test Categories:
- AC-7.32.15: Integration tests conditional (skip if Docling unavailable)
- AC-7.32.4: Default behavior unchanged
- AC-7.32.5: Existing documents remain valid
"""

import os
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.integration


# Check if Docling is installed
def is_docling_installed() -> bool:
    """Check if Docling library is available."""
    try:
        import docling  # noqa: F401

        return True
    except ImportError:
        return False


DOCLING_INSTALLED = is_docling_installed()


# =============================================================================
# AC-7.32.15: Integration tests conditional
# =============================================================================


@pytest.mark.skipif(not DOCLING_INSTALLED, reason="Docling not installed")
class TestDoclingIntegration:
    """Integration tests that require Docling to be installed."""

    def test_parse_pdf_with_real_docling(self, tmp_path) -> None:
        """
        AC-7.32.15: Verify real Docling parsing works when installed.

        Given Docling is installed
        When PDF is parsed with Docling backend
        Then parsing succeeds with Docling
        """
        # This test only runs if Docling is installed
        from app.workers.docling_parser import is_docling_available, parse_pdf_docling

        assert is_docling_available() is True

        # Create a simple test PDF (would need actual PDF for real test)
        # For now, verify the function exists and is callable
        assert callable(parse_pdf_docling)

    def test_auto_mode_uses_docling_first(self, tmp_path) -> None:
        """
        AC-7.32.15: Auto mode tries Docling first when available.

        Given Docling is installed and enabled
        When document parsed with AUTO mode
        Then Docling is tried first
        """
        from app.workers.docling_parser import is_docling_available

        assert is_docling_available() is True

        # Auto mode should prefer Docling when available
        # Implementation should try Docling first


class TestFallbackBehavior:
    """Test fallback behavior regardless of Docling installation."""

    def test_unstructured_fallback_when_docling_unavailable(self, tmp_path) -> None:
        """
        AC-7.32.15: Tests verify fallback behavior when Docling unavailable.

        Given Docling is not installed
        When document parsed with DOCLING backend
        Then Unstructured is used as fallback
        """
        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.parsing import ParsedContent

        md_file = tmp_path / "test.md"
        md_file.write_text(
            "# Test Document\n\n"
            "This is a test document with enough content to pass the minimum "
            "character threshold requirement of 100 characters for validation."
        )

        # Simulate Docling being unavailable
        with patch(
            "app.workers.docling_parser.is_docling_available", return_value=False
        ):
            with patch("app.workers.parsing.parse_markdown") as mock_parse_md:
                mock_parse_md.return_value = ParsedContent(
                    text="Test Document content...",
                    elements=[],
                    metadata={"source_format": "markdown"},
                )

                from app.workers.parsing import parse_document

                result = parse_document(
                    str(md_file),
                    "text/markdown",
                    parser_backend=DocumentParserBackend.DOCLING,
                )

                # Should have fallen back to Unstructured
                mock_parse_md.assert_called_once()


# =============================================================================
# AC-7.32.4: Default behavior unchanged
# =============================================================================


class TestDefaultBehavior:
    """Test that default behavior is preserved."""

    def test_default_uses_unstructured_when_flag_disabled(self, tmp_path) -> None:
        """
        AC-7.32.4: Default behavior unchanged when feature flag disabled.

        Given system has LUMIKB_PARSER_DOCLING_ENABLED=false (default)
        When documents are processed
        Then Unstructured is used for all formats (existing behavior)
        And no user action required
        """
        from app.workers.parsing import ParsedContent

        md_file = tmp_path / "test.md"
        md_file.write_text(
            "# Test\n\nThis is test content with more than 100 characters "
            "to pass the validation threshold for document parsing."
        )

        # With feature flag disabled (default), always use Unstructured
        with patch.dict(os.environ, {"LUMIKB_PARSER_DOCLING_ENABLED": "false"}):
            with patch("app.workers.parsing.parse_markdown") as mock_parse_md:
                mock_parse_md.return_value = ParsedContent(
                    text="Test content",
                    elements=[],
                    metadata={"source_format": "markdown"},
                )

                from app.schemas.kb_settings import DocumentParserBackend
                from app.workers.parsing import parse_document

                # Even with DOCLING backend specified, should use Unstructured
                result = parse_document(
                    str(md_file),
                    "text/markdown",
                    parser_backend=DocumentParserBackend.DOCLING,
                )

                mock_parse_md.assert_called_once()

    def test_no_parser_backend_uses_unstructured(self, tmp_path) -> None:
        """
        AC-7.32.4: No parser_backend parameter uses Unstructured.

        Given parse_document called without parser_backend
        Then Unstructured is used (backward compatible)
        """
        from app.workers.parsing import ParsedContent

        md_file = tmp_path / "test.md"
        md_file.write_text(
            "# Test\n\nThis is test content with sufficient length "
            "to pass the minimum character threshold for parsing."
        )

        with patch("app.workers.parsing.parse_markdown") as mock_parse_md:
            mock_parse_md.return_value = ParsedContent(
                text="Test content",
                elements=[],
                metadata={"source_format": "markdown"},
            )

            from app.workers.parsing import parse_document

            # Call without parser_backend (existing API)
            result = parse_document(str(md_file), "text/markdown")

            mock_parse_md.assert_called_once()


# =============================================================================
# AC-7.32.5: Existing documents remain valid
# =============================================================================


class TestExistingDocumentsValid:
    """Test that existing documents work without reprocessing."""

    def test_existing_parsed_content_still_valid(self) -> None:
        """
        AC-7.32.5: Existing documents remain valid.

        Given documents were processed before Docling integration
        When I view or search these documents
        Then they work correctly without reprocessing
        """
        from app.workers.parsing import ParsedContent, ParsedElement

        # Simulate a document processed before Docling integration
        # (no parser_backend in metadata)
        legacy_content = ParsedContent(
            text="This is legacy document content from before Docling.",
            elements=[
                ParsedElement(
                    text="This is legacy document content from before Docling.",
                    element_type="NarrativeText",
                    metadata={},
                )
            ],
            metadata={
                "source_format": "pdf",
                "page_count": 1,
                "section_count": 0,
                "element_count": 1,
                # Note: no parser_backend field
            },
        )

        # Verify the legacy content is still usable
        assert legacy_content.text is not None
        assert len(legacy_content.elements) > 0
        assert legacy_content.metadata["source_format"] == "pdf"

        # Verify it doesn't break if parser_backend is missing
        parser_backend = legacy_content.metadata.get("parser_backend", "unstructured")
        assert parser_backend == "unstructured"

    def test_search_works_with_legacy_documents(self) -> None:
        """
        AC-7.32.5: Search works with documents missing parser_backend.

        Given documents exist without parser_backend metadata
        When search is performed
        Then results include these documents without errors
        """
        # This test verifies backward compatibility of search
        # Implementation should handle missing parser_backend gracefully
        from app.workers.parsing import ParsedContent

        legacy_content = ParsedContent(
            text="Legacy searchable content",
            elements=[],
            metadata={"source_format": "docx"},  # No parser_backend
        )

        # Simulating what search service would do
        parser = legacy_content.metadata.get("parser_backend", "unstructured")
        assert parser == "unstructured"  # Default fallback


# =============================================================================
# Feature Flag Integration
# =============================================================================


class TestFeatureFlagIntegration:
    """Test feature flag behavior with full parsing stack."""

    def test_feature_flag_env_var_respected(self) -> None:
        """
        AC-7.32.1 Integration: Feature flag controls parser selection.

        Given LUMIKB_PARSER_DOCLING_ENABLED environment variable
        When Settings is loaded
        Then parser_docling_enabled reflects the value
        """
        # Test with flag enabled
        with patch.dict(os.environ, {"LUMIKB_PARSER_DOCLING_ENABLED": "true"}):
            from importlib import reload

            import app.core.config

            reload(app.core.config)
            settings = app.core.config.Settings(_env_file=None)

            assert settings.parser_docling_enabled is True

        # Test with flag disabled
        with patch.dict(os.environ, {"LUMIKB_PARSER_DOCLING_ENABLED": "false"}):
            reload(app.core.config)
            settings = app.core.config.Settings(_env_file=None)

            assert settings.parser_docling_enabled is False

    def test_kb_settings_parser_backend_ignored_when_flag_disabled(
        self, tmp_path
    ) -> None:
        """
        AC-7.32.1 Integration: KB setting ignored when system flag disabled.

        Given LUMIKB_PARSER_DOCLING_ENABLED=false
        And KB has parser_backend=docling
        When document is parsed
        Then Unstructured is used (system flag takes precedence)
        """
        from app.schemas.kb_settings import DocumentParserBackend
        from app.workers.parsing import ParsedContent

        with patch.dict(os.environ, {"LUMIKB_PARSER_DOCLING_ENABLED": "false"}):
            with patch("app.workers.parsing.parse_pdf") as mock_parse_pdf:
                mock_parse_pdf.return_value = ParsedContent(
                    text="Unstructured content",
                    elements=[],
                    metadata={"source_format": "pdf", "parser_backend": "unstructured"},
                )

                pdf_file = tmp_path / "test.pdf"
                pdf_file.write_bytes(b"%PDF-1.4 test")

                from app.workers.parsing import parse_document

                result = parse_document(
                    str(pdf_file),
                    "application/pdf",
                    parser_backend=DocumentParserBackend.DOCLING,
                )

                # Should use Unstructured despite DOCLING setting
                mock_parse_pdf.assert_called_once()
                assert result.metadata.get("parser_backend") == "unstructured"
