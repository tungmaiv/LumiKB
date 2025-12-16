# ATDD Checklist: Story 7-32 - Docling Document Parser Integration

**Story:** 7-32 - Docling Document Parser Integration
**Epic:** 7 - Production Infrastructure & Performance
**Story Points:** 2
**Generated:** 2025-12-16
**Completed:** 2025-12-16
**Status:** GREEN PHASE (All Tests Passing)

---

## Test Summary

| Test Level | Total Tests | Failing | Passing | Skip |
|------------|-------------|---------|---------|------|
| Unit | 30 | 0 | 30 | 0 |
| Integration | 9 | 0 | 7 | 2* |
| E2E | 0 | 0 | 0 | 0 |
| **Total** | **39** | **0** | **37** | **2** |

*Note: 2 Integration tests with `@pytest.mark.skipif(not DOCLING_INSTALLED)` skipped as expected (Docling not installed).

---

## Test Files Created

### Unit Tests
- **File:** [`backend/tests/unit/test_docling_parser.py`](../../backend/tests/unit/test_docling_parser.py)
- **Tests:** 27 test cases
- **Run Command:** `pytest tests/unit/test_docling_parser.py -v`

### Integration Tests
- **File:** [`backend/tests/integration/test_parser_strategy.py`](../../backend/tests/integration/test_parser_strategy.py)
- **Tests:** 10 test cases (conditional on Docling availability)
- **Run Command:** `pytest tests/integration/test_parser_strategy.py -v`

---

## Acceptance Criteria Coverage Matrix

| AC ID | Description | Test Level | Test Class/Method | Status |
|-------|-------------|------------|-------------------|--------|
| AC-7.32.1 | System-level feature flag | Unit | `TestDoclingFeatureFlag::test_feature_flag_default_false` | GREEN |
| AC-7.32.1 | Feature flag enables Docling | Unit | `TestDoclingFeatureFlag::test_feature_flag_can_be_enabled` | GREEN |
| AC-7.32.2 | KB parser_backend enum | Unit | `TestKBParserBackendSetting::test_document_parser_backend_enum_values` | GREEN |
| AC-7.32.2 | DocumentProcessingConfig field | Unit | `TestKBParserBackendSetting::test_document_processing_config_has_parser_backend` | GREEN |
| AC-7.32.4 | Default behavior unchanged | Integration | `TestDefaultBehavior::test_default_uses_unstructured_when_flag_disabled` | GREEN |
| AC-7.32.5 | Existing documents valid | Integration | `TestExistingDocumentsValid::test_existing_parsed_content_still_valid` | GREEN |
| AC-7.32.6 | ParsedContent interface | Unit | `TestParsedContentInterfacePreservation::test_parse_pdf_docling_returns_parsed_content` | GREEN |
| AC-7.32.7 | Strategy pattern param | Unit | `TestParserStrategyPattern::test_parse_document_accepts_parser_backend_param` | GREEN |
| AC-7.32.7 | Dispatch to Unstructured | Unit | `TestParserStrategyPattern::test_parse_document_dispatches_to_unstructured` | GREEN |
| AC-7.32.7 | Dispatch to Docling | Unit | `TestParserStrategyPattern::test_parse_document_dispatches_to_docling` | GREEN |
| AC-7.32.8 | Module exports parse_pdf_docling | Unit | `TestDoclingParserModuleExports::test_module_exports_parse_pdf_docling` | GREEN |
| AC-7.32.8 | Module exports parse_docx_docling | Unit | `TestDoclingParserModuleExports::test_module_exports_parse_docx_docling` | GREEN |
| AC-7.32.8 | Module exports is_docling_available | Unit | `TestDoclingParserModuleExports::test_module_exports_is_docling_available` | GREEN |
| AC-7.32.9 | Auto mode fallback | Unit | `TestAutoModeFallback::test_auto_mode_fallback_on_docling_failure` | GREEN |
| AC-7.32.9 | Fallback warning logged | Unit | `TestAutoModeFallback::test_auto_mode_logs_fallback_warning` | GREEN |
| AC-7.32.10 | Graceful degradation | Unit | `TestGracefulDegradation::test_docling_unavailable_fallback_to_unstructured` | GREEN |
| AC-7.32.10 | is_docling_available false | Unit | `TestGracefulDegradation::test_is_docling_available_returns_false_when_not_installed` | GREEN |
| AC-7.32.11 | PDF Heron layout model | Unit | `TestDoclingFormatSpecificParsing::test_pdf_parsing_uses_docling_when_enabled` | GREEN |
| AC-7.32.11 | PDF cell-level tables | Unit | `TestDoclingFormatSpecificParsing::test_pdf_tables_extracted_at_cell_level` | GREEN |
| AC-7.32.12 | DOCX formatting preserved | Unit | `TestDoclingFormatSpecificParsing::test_docx_parsing_preserves_formatting` | GREEN |
| AC-7.32.13 | Markdown passthrough | Unit | `TestMarkdownPassthrough::test_markdown_uses_unstructured_by_default` | GREEN |
| AC-7.32.13 | Markdown in AUTO mode | Unit | `TestMarkdownPassthrough::test_markdown_passthrough_with_auto_mode` | GREEN |
| AC-7.32.15 | Integration tests conditional | Integration | `TestDoclingIntegration` (class) | SKIP* |
| AC-7.32.16 | Existing tests unchanged | Unit | `TestBackwardCompatibility::test_parse_document_without_parser_backend_works` | GREEN |
| AC-7.32.17 | Parser backend in metadata | Unit | `TestParserAuditLogging::test_metadata_includes_parser_backend` | RED |
| AC-7.32.17 | Fallback indicator | Unit | `TestParserAuditLogging::test_metadata_includes_fallback_indicator` | RED |

---

## Implementation Checklist

### Task 1: Add System Feature Flag (AC-7.32.1)

**File:** `backend/app/core/config.py`

```python
# Add to Settings class
parser_docling_enabled: bool = False  # LUMIKB_PARSER_DOCLING_ENABLED
```

**Verification:**
- [ ] `parser_docling_enabled` field exists in Settings
- [ ] Default value is `False`
- [ ] Can be enabled via `LUMIKB_PARSER_DOCLING_ENABLED=true`
- [ ] Tests pass: `test_feature_flag_default_false`, `test_feature_flag_can_be_enabled`

---

### Task 2: Create Docling Parser Module (AC-7.32.8)

**File:** `backend/app/workers/docling_parser.py` (NEW FILE)

```python
"""Docling document parser implementation.

Story 7-32: Docling Document Parser Integration
Provides alternative parser backend with better table extraction.
"""

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from app.workers.parsing import ParsedContent

logger = structlog.get_logger(__name__)


def is_docling_available() -> bool:
    """Check if Docling library is installed and available."""
    try:
        import docling  # noqa: F401
        return True
    except ImportError:
        return False


def parse_pdf_docling(file_path: str) -> "ParsedContent":
    """Parse PDF document using Docling.

    Args:
        file_path: Path to the PDF file.

    Returns:
        ParsedContent with extracted text and metadata.

    Raises:
        ParsingError: If parsing fails.
    """
    # Implementation goes here
    pass


def parse_docx_docling(file_path: str) -> "ParsedContent":
    """Parse DOCX document using Docling.

    Args:
        file_path: Path to the DOCX file.

    Returns:
        ParsedContent with extracted text and metadata.

    Raises:
        ParsingError: If parsing fails.
    """
    # Implementation goes here
    pass
```

**Verification:**
- [ ] Module exists at `backend/app/workers/docling_parser.py`
- [ ] Exports `is_docling_available()` function
- [ ] Exports `parse_pdf_docling(file_path)` function
- [ ] Exports `parse_docx_docling(file_path)` function
- [ ] Tests pass: `test_module_exports_*` tests

---

### Task 3: Implement Strategy Pattern in parsing.py (AC-7.32.7)

**File:** `backend/app/workers/parsing.py`

**Changes:**
1. Add `parser_backend` parameter to `parse_document()` function
2. Implement dispatch logic based on parser_backend value
3. Check system feature flag before using Docling

```python
def parse_document(
    file_path: str,
    mime_type: str,
    parser_backend: DocumentParserBackend | None = None  # NEW PARAM
) -> ParsedContent:
    """Parse a document based on its MIME type.

    Args:
        file_path: Path to the document file.
        mime_type: MIME type of the document.
        parser_backend: Optional parser backend override.
                       If None, uses Unstructured (backward compatible).

    Returns:
        ParsedContent with extracted text and metadata.
    """
    # Implementation: check feature flag, dispatch to appropriate parser
    pass
```

**Verification:**
- [ ] `parse_document()` accepts `parser_backend` parameter
- [ ] Default value is `None` (backward compatible)
- [ ] Dispatches to correct parser based on value
- [ ] Tests pass: `test_parse_document_accepts_parser_backend_param`, `test_parse_document_dispatches_*`

---

### Task 4: Implement Fallback Logic (AC-7.32.9, AC-7.32.10)

**File:** `backend/app/workers/parsing.py`

**Changes:**
1. Implement AUTO mode: try Docling first, fallback to Unstructured
2. Graceful degradation when Docling unavailable
3. Log warnings on fallback

```python
def _parse_with_fallback(
    file_path: str,
    mime_type: str,
    parser_backend: DocumentParserBackend
) -> ParsedContent:
    """Parse with fallback logic for AUTO mode and graceful degradation."""
    # Implementation goes here
    pass
```

**Verification:**
- [ ] AUTO mode tries Docling first
- [ ] Fallback to Unstructured on Docling failure
- [ ] Warning logged on fallback
- [ ] Graceful degradation when Docling not installed
- [ ] Tests pass: `test_auto_mode_fallback_*`, `test_docling_unavailable_fallback_*`

---

### Task 5: Markdown Passthrough (AC-7.32.13)

**File:** `backend/app/workers/parsing.py`

**Changes:**
1. Markdown files always use Unstructured regardless of parser_backend

**Verification:**
- [ ] Markdown uses Unstructured even when parser_backend=DOCLING
- [ ] Markdown uses Unstructured in AUTO mode
- [ ] Tests pass: `test_markdown_always_uses_unstructured`, `test_markdown_passthrough_with_auto_mode`

---

### Task 6: Audit Logging (AC-7.32.17)

**File:** `backend/app/workers/parsing.py`, `backend/app/workers/docling_parser.py`

**Changes:**
1. Include `parser_backend` in ParsedContent metadata
2. Include `parser_fallback_from` when fallback occurs

**Verification:**
- [ ] `metadata["parser_backend"]` populated
- [ ] `metadata["parser_fallback_from"]` populated on fallback
- [ ] Tests pass: `test_metadata_includes_parser_backend`, `test_metadata_includes_fallback_indicator`

---

### Task 7: Add Docling Dependency (Optional)

**File:** `backend/pyproject.toml`

```toml
[project.optional-dependencies]
docling = ["docling>=2.0.0"]
```

**Verification:**
- [ ] Docling is optional dependency
- [ ] App works without Docling installed
- [ ] Tests pass when Docling is not installed

---

## Mock Requirements

### Unit Tests - Mocked Dependencies

| Mock Target | Purpose | Location |
|-------------|---------|----------|
| `docling` module | Simulate Docling library | `sys.modules` patch |
| `docling.document_converter.DocumentConverter` | Mock conversion | `mock_docling_converter` fixture |
| `app.workers.docling_parser.is_docling_available` | Control availability | `patch()` |
| `app.workers.parsing.parse_pdf` | Verify Unstructured dispatch | `patch()` |
| `app.workers.docling_parser.parse_pdf_docling` | Verify Docling dispatch | `patch()` |
| `os.environ` | Control feature flag | `patch.dict()` |

### Integration Tests - Conditional Execution

| Condition | Behavior |
|-----------|----------|
| `DOCLING_INSTALLED = True` | Run all Docling integration tests |
| `DOCLING_INSTALLED = False` | Skip Docling-specific tests, run fallback tests |

---

## Fixture Catalog

### `mock_docling` (Unit Test Fixture)

```python
@pytest.fixture
def mock_docling():
    """Mock docling library for testing."""
    mock_doc_converter = MagicMock()
    mock_result = MagicMock()
    mock_result.document.export_to_markdown.return_value = "# Test\n\nContent"
    mock_result.pages = [MagicMock()]
    mock_doc_converter.return_value.convert.return_value = mock_result

    mock_docling_pkg = MagicMock()
    mock_docling_pkg.document_converter.DocumentConverter = mock_doc_converter

    return {
        "docling": mock_docling_pkg,
        "document_converter": mock_doc_converter,
        "result": mock_result,
    }
```

### `mock_docling_converter` (Format-Specific Fixture)

```python
@pytest.fixture
def mock_docling_converter():
    """Create mock Docling DocumentConverter."""
    mock_converter = MagicMock()
    mock_result = MagicMock()
    mock_result.document.export_to_markdown.return_value = (
        "# Document Title\n\n## Section 1\n\nContent.\n\n"
        "| Column 1 | Column 2 |\n|----------|----------|\n| Cell 1 | Cell 2 |\n"
    )
    mock_result.pages = [MagicMock(), MagicMock()]
    mock_converter.convert.return_value = mock_result
    return mock_converter
```

---

## Test Execution Commands

```bash
# Run all unit tests for Story 7-32
pytest tests/unit/test_docling_parser.py -v

# Run integration tests
pytest tests/integration/test_parser_strategy.py -v

# Run all 7-32 tests with coverage
pytest tests/unit/test_docling_parser.py tests/integration/test_parser_strategy.py \
    --cov=app/workers/parsing --cov=app/workers/docling_parser --cov-report=term-missing

# Verify existing parsing tests still pass
pytest tests/unit/test_parsing.py -v
```

---

## Risk Mitigation

| Risk | Mitigation | Test Coverage |
|------|------------|---------------|
| Memory issues with large PDFs | `max_pages` limit configuration | Not directly tested (operational) |
| Docling library not installed | Graceful degradation to Unstructured | `test_docling_unavailable_fallback_*` |
| Docling parsing failure | AUTO mode fallback | `test_auto_mode_fallback_*` |
| Breaking existing behavior | Backward compatibility tests | `test_parse_document_without_parser_backend_works` |
| Feature flag bypass | System flag takes precedence | `test_kb_settings_parser_backend_ignored_when_flag_disabled` |

---

## Definition of Done

- [ ] All 37 tests pass (30 currently RED)
- [ ] No regressions in existing `test_parsing.py` tests (160+ tests)
- [ ] Feature flag `LUMIKB_PARSER_DOCLING_ENABLED` implemented
- [ ] `docling_parser.py` module created with required exports
- [ ] Strategy pattern implemented in `parse_document()`
- [ ] Fallback logic implemented for AUTO mode
- [ ] Graceful degradation when Docling unavailable
- [ ] Markdown passthrough preserved
- [ ] Audit metadata includes `parser_backend`
- [ ] Code review completed
- [ ] Documentation updated (if applicable)

---

## References

- [Story 7-32 Definition](7-32-docling-parser-integration.md)
- [Docling GitHub Repository](https://github.com/docling-project/docling)
- [Correct-Course Handover](correct-course-handover-docling-integration.md)
- [Sprint Change Proposal](sprint-change-proposal-docling-2025-12-16.md)
