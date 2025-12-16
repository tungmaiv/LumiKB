# Story 7-28: Markdown Generation from DOCX/PDF (Backend)

**Epic:** 7 - Infrastructure & DevOps
**Story Points:** 3
**Status:** done
**Created:** 2025-12-11

---

## User Story

**As a** developer,
**I want to** convert PDF/DOCX documents to Markdown during parsing,
**So that** chunk positions can be accurately highlighted in the document viewer.

---

## Background

The current chunk viewer has position accuracy issues with PDF and DOCX documents:
- PDF: Page-level navigation only, no character-level highlighting
- DOCX: Scroll position estimation is imprecise (uses ratio calculation)
- Markdown/Text: Already accurate with line-based highlighting

This story implements the first phase of the Markdown-First Document Processing approach by adding markdown generation to the parsing pipeline.

---

## Acceptance Criteria

### AC-7.28.1: markdownify Dependency
**Given** I check backend/pyproject.toml
**Then** `markdownify>=0.11.0,<1.0.0` is listed as a dependency under worker extras

**Implementation Notes:**
- Add to `[project.optional-dependencies]` section
- Group with other document processing dependencies

### AC-7.28.2: elements_to_markdown Function
**Given** I import `elements_to_markdown` from `app.workers.parsing`
**Then** the function accepts `list[ParsedElement]` and returns a markdown string
**And** the function preserves element order and appropriate spacing

**Implementation Notes:**
```python
def elements_to_markdown(elements: list[ParsedElement]) -> str:
    """Convert parsed elements to Markdown format.

    Args:
        elements: List of ParsedElement from document parsing.

    Returns:
        Markdown-formatted string with heading levels, lists, and tables.
    """
```

### AC-7.28.3: ParsedContent Markdown Field
**Given** I inspect the `ParsedContent` dataclass in `app.workers.parsing`
**Then** it has an optional field `markdown_content: str | None = None`
**And** the field is populated for PDF and DOCX documents during parsing

**Implementation Notes:**
- Add field to existing dataclass
- Default to None for backwards compatibility

### AC-7.28.4: Markdown Stored in MinIO
**Given** a PDF or DOCX document is processed
**When** parsing completes successfully
**Then** the `.parsed.json` file in MinIO includes `markdown_content` field
**And** the markdown content is the full converted document

**Implementation Notes:**
- Update `document_tasks.py` to include markdown in parsed content storage
- Existing storage pattern uses `{doc_id}.parsed.json`

### AC-7.28.5: DOCX Markdown Quality
**Given** a DOCX document with headings, lists, and tables
**When** converted to markdown
**Then** output preserves:
  - Heading levels (# for Title, ## for Header, ### for nested)
  - List formatting (- for bullets, 1. for numbered)
  - Table structure (using | markdown syntax)
**And** code blocks are preserved with triple backticks

**Implementation Notes:**
- `markdownify` handles HTML-to-Markdown conversion
- `unstructured` elements have `.metadata.text_as_html` for rich content
- Map element types to markdown constructs

### AC-7.28.6: Unit Test Coverage
**Given** unit tests exist for `elements_to_markdown` function
**Then** coverage is >= 80% for the new function
**And** tests cover:
  - Empty elements list
  - Single element conversion
  - Multiple element types (Title, NarrativeText, ListItem, Table)
  - Heading level preservation
  - Table markdown formatting
  - Edge cases: empty text, special characters

---

## Technical Design

### Element Type to Markdown Mapping

| Element Type | Markdown Output |
|--------------|-----------------|
| Title | `# {text}` |
| Header | `## {text}` (or ### based on depth) |
| NarrativeText | `{text}\n\n` |
| ListItem | `- {text}` |
| Table | `| col1 | col2 |\n|---|---|\n| data |` |
| CodeSnippet | ` ``` \n{text}\n ``` ` |
| FigureCaption | `*{text}*` (italic) |

### Files to Modify

| File | Changes |
|------|---------|
| `backend/pyproject.toml` | Add `markdownify>=0.11.0,<1.0.0` to worker extras |
| `backend/app/workers/parsing.py` | Add `elements_to_markdown()`, update `ParsedContent` dataclass |
| `backend/app/workers/document_tasks.py` | Store `markdown_content` in parsed JSON |
| `backend/tests/unit/test_parsing.py` | Add tests for `elements_to_markdown()` |

### Sample Implementation

```python
# backend/app/workers/parsing.py

from markdownify import markdownify as md

@dataclass
class ParsedContent:
    text: str
    elements: list[ParsedElement]
    metadata: dict[str, Any]
    markdown_content: str | None = None  # NEW

def elements_to_markdown(elements: list[ParsedElement]) -> str:
    """Convert parsed elements to Markdown format."""
    markdown_parts: list[str] = []

    for el in elements:
        element_type = el.element_type
        text = el.text.strip()

        if not text:
            continue

        if element_type == "Title":
            markdown_parts.append(f"# {text}\n")
        elif element_type == "Header":
            level = el.metadata.get("heading_level", 2)
            prefix = "#" * min(level, 6)
            markdown_parts.append(f"{prefix} {text}\n")
        elif element_type == "ListItem":
            markdown_parts.append(f"- {text}\n")
        elif element_type == "Table":
            # Use markdownify for HTML tables
            html = el.metadata.get("text_as_html", f"<p>{text}</p>")
            markdown_parts.append(md(html) + "\n")
        elif element_type in ("NarrativeText", "Text"):
            markdown_parts.append(f"{text}\n\n")
        else:
            # Default: plain text with spacing
            markdown_parts.append(f"{text}\n\n")

    return "".join(markdown_parts).strip()
```

---

## Dependencies

### Prerequisites
- None (can start immediately)

### Blocked By
- None

### Blocks
- Story 7-29 (Markdown Content API Endpoint)

---

## Test Plan

### Unit Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_elements_to_markdown_empty` | Empty elements list | Returns empty string |
| `test_elements_to_markdown_title` | Single Title element | Returns `# Title` |
| `test_elements_to_markdown_headers` | Headers with depth | Returns appropriate # levels |
| `test_elements_to_markdown_narrative` | NarrativeText element | Returns text with double newline |
| `test_elements_to_markdown_list` | ListItem elements | Returns `- item` format |
| `test_elements_to_markdown_table_html` | Table with HTML metadata | Converts to markdown table |
| `test_elements_to_markdown_mixed` | Multiple element types | Preserves order and formatting |
| `test_parsed_content_markdown_field` | ParsedContent with markdown | Field accessible and correct |

### Integration Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_parse_docx_generates_markdown` | Parse DOCX file | `markdown_content` populated |
| `test_parse_pdf_generates_markdown` | Parse PDF file | `markdown_content` populated |
| `test_parsed_json_includes_markdown` | Check MinIO storage | `.parsed.json` contains markdown |

---

## Definition of Done

- [x] `markdownify>=0.11.0` added to pyproject.toml
- [x] `elements_to_markdown()` function implemented
- [x] `ParsedContent.markdown_content` field added
- [x] PDF parsing generates markdown
- [x] DOCX parsing generates markdown
- [x] Markdown stored in MinIO `.parsed.json`
- [x] Unit tests pass with >= 80% coverage (17 new tests, all pass)
- [x] Code review approved
- [x] Ruff lint/format passes

---

## Story Context References

- [Sprint Change Proposal](sprint-change-proposal-markdown-first-processing.md) - Feature rationale
- [Epic 7: Infrastructure](../epics/epic-7-infrastructure.md) - Story 7.28
- [parsing.py](../../backend/app/workers/parsing.py) - Current implementation
- [document_tasks.py](../../backend/app/workers/document_tasks.py) - Worker tasks

---

## Notes

- This story focuses on backend markdown generation only
- Frontend viewer changes are in Story 7-30
- API endpoint is in Story 7-29
- Start with DOCX which has better structure; PDF may need additional work
- Keep original `text` field for backwards compatibility
