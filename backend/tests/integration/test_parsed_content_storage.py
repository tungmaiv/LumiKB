"""Integration tests for parsed content storage (Story 7-28: AC-7.28.4).

Tests verify that markdown_content field is properly stored and loaded
from MinIO .parsed.json files during document processing pipeline.

These tests require Docker infrastructure (MinIO) to be running.
"""

import json
import uuid
from uuid import UUID

import pytest

from app.integrations.minio_client import minio_service
from app.workers.parsed_content_storage import (
    delete_parsed_content,
    load_parsed_content,
    store_parsed_content,
)
from app.workers.parsing import ParsedContent, ParsedElement

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_kb_id() -> UUID:
    """Generate a sample knowledge base ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_doc_id() -> UUID:
    """Generate a sample document ID."""
    return uuid.uuid4()


@pytest.fixture
def parsed_content_with_markdown() -> ParsedContent:
    """Create ParsedContent with markdown_content populated (Story 7-28)."""
    elements = [
        ParsedElement(text="Introduction", element_type="Title", metadata={}),
        ParsedElement(
            text="This is the first paragraph of the document.",
            element_type="NarrativeText",
            metadata={},
        ),
        ParsedElement(
            text="Key Points", element_type="Header", metadata={"heading_level": 2}
        ),
        ParsedElement(text="First item", element_type="ListItem", metadata={}),
        ParsedElement(text="Second item", element_type="ListItem", metadata={}),
        ParsedElement(
            text="| Name | Value |\n|------|-------|\n| Key | 42 |",
            element_type="Table",
            metadata={
                "text_as_html": "<table><tr><td>Name</td><td>Value</td></tr></table>"
            },
        ),
    ]

    # Build markdown from elements (as elements_to_markdown would)
    markdown_content = """# Introduction

This is the first paragraph of the document.

## Key Points

- First item
- Second item

| Name | Value |
|------|-------|
| Key | 42 |"""

    return ParsedContent(
        text="Introduction This is the first paragraph of the document. Key Points First item Second item",
        elements=elements,
        metadata={
            "page_count": 1,
            "section_count": 2,
            "element_count": 6,
            "source_format": "docx",
        },
        markdown_content=markdown_content,
    )


@pytest.fixture
def parsed_content_without_markdown() -> ParsedContent:
    """Create ParsedContent without markdown_content (backwards compatibility)."""
    elements = [
        ParsedElement(
            text="Plain text document content.",
            element_type="NarrativeText",
            metadata={},
        ),
    ]

    return ParsedContent(
        text="Plain text document content.",
        elements=elements,
        metadata={"page_count": 1, "section_count": 1, "element_count": 1},
        markdown_content=None,
    )


@pytest.fixture
async def ensure_bucket(sample_kb_id: UUID):
    """Ensure MinIO bucket exists for tests."""
    try:
        await minio_service.ensure_bucket_exists(sample_kb_id)
        yield
    finally:
        # Cleanup is handled by delete_parsed_content in tests
        pass


# =============================================================================
# AC-7.28.4: Markdown Stored in MinIO
# =============================================================================


async def test_store_parsed_content_includes_markdown(
    sample_kb_id: UUID,
    sample_doc_id: UUID,
    parsed_content_with_markdown: ParsedContent,
    ensure_bucket,
) -> None:
    """Test that store_parsed_content includes markdown_content in .parsed.json.

    AC-7.28.4: The .parsed.json file in MinIO includes markdown_content field.
    """
    # Store parsed content
    storage_path = await store_parsed_content(
        kb_id=sample_kb_id,
        document_id=sample_doc_id,
        parsed=parsed_content_with_markdown,
    )

    # Verify storage path format
    assert storage_path is not None
    assert ".parsed.json" in storage_path

    # Download and verify JSON structure
    object_path = f"{sample_doc_id}/.parsed.json"
    raw_data = await minio_service.download_file(sample_kb_id, object_path)
    content_dict = json.loads(raw_data.decode("utf-8"))

    # Verify markdown_content is present and correct
    assert "markdown_content" in content_dict
    assert (
        content_dict["markdown_content"]
        == parsed_content_with_markdown.markdown_content
    )
    assert "# Introduction" in content_dict["markdown_content"]
    assert "## Key Points" in content_dict["markdown_content"]
    assert "- First item" in content_dict["markdown_content"]

    # Cleanup
    await delete_parsed_content(sample_kb_id, sample_doc_id)


async def test_load_parsed_content_retrieves_markdown(
    sample_kb_id: UUID,
    sample_doc_id: UUID,
    parsed_content_with_markdown: ParsedContent,
    ensure_bucket,
) -> None:
    """Test that load_parsed_content retrieves markdown_content from .parsed.json.

    AC-7.28.4: Verify round-trip storage and retrieval of markdown_content.
    """
    # Store parsed content
    await store_parsed_content(
        kb_id=sample_kb_id,
        document_id=sample_doc_id,
        parsed=parsed_content_with_markdown,
    )

    # Load parsed content back
    loaded = await load_parsed_content(sample_kb_id, sample_doc_id)

    # Verify loaded content
    assert loaded is not None
    assert loaded.markdown_content is not None
    assert loaded.markdown_content == parsed_content_with_markdown.markdown_content

    # Verify other fields are preserved
    assert loaded.text == parsed_content_with_markdown.text
    assert len(loaded.elements) == len(parsed_content_with_markdown.elements)

    # Cleanup
    await delete_parsed_content(sample_kb_id, sample_doc_id)


async def test_store_parsed_content_null_markdown_backwards_compatible(
    sample_kb_id: UUID,
    sample_doc_id: UUID,
    parsed_content_without_markdown: ParsedContent,
    ensure_bucket,
) -> None:
    """Test that null markdown_content is handled for backwards compatibility.

    AC-7.28.3: markdown_content defaults to None for backwards compatibility.
    """
    # Store parsed content without markdown
    await store_parsed_content(
        kb_id=sample_kb_id,
        document_id=sample_doc_id,
        parsed=parsed_content_without_markdown,
    )

    # Download and verify JSON structure
    object_path = f"{sample_doc_id}/.parsed.json"
    raw_data = await minio_service.download_file(sample_kb_id, object_path)
    content_dict = json.loads(raw_data.decode("utf-8"))

    # Verify markdown_content key exists but is null
    assert "markdown_content" in content_dict
    assert content_dict["markdown_content"] is None

    # Cleanup
    await delete_parsed_content(sample_kb_id, sample_doc_id)


async def test_load_parsed_content_null_markdown_backwards_compatible(
    sample_kb_id: UUID,
    sample_doc_id: UUID,
    parsed_content_without_markdown: ParsedContent,
    ensure_bucket,
) -> None:
    """Test that loading content without markdown_content returns None.

    AC-7.28.3: Backwards compatibility for documents without markdown.
    """
    # Store parsed content without markdown
    await store_parsed_content(
        kb_id=sample_kb_id,
        document_id=sample_doc_id,
        parsed=parsed_content_without_markdown,
    )

    # Load parsed content back
    loaded = await load_parsed_content(sample_kb_id, sample_doc_id)

    # Verify markdown_content is None
    assert loaded is not None
    assert loaded.markdown_content is None

    # Verify other fields are preserved
    assert loaded.text == parsed_content_without_markdown.text
    assert len(loaded.elements) == 1

    # Cleanup
    await delete_parsed_content(sample_kb_id, sample_doc_id)


async def test_store_parsed_content_preserves_markdown_special_characters(
    sample_kb_id: UUID,
    sample_doc_id: UUID,
    ensure_bucket,
) -> None:
    """Test that special characters in markdown are preserved during storage.

    AC-7.28.5: Code blocks and special formatting are preserved.
    """
    # Create content with special markdown characters
    markdown_with_special = """# Code Example

Here's some code:

```python
def hello():
    print("Hello, World!")
```

Special chars: < > & " ' | \\ / * _ `
Unicode: é ñ ü 中文 日本語
"""
    elements = [
        ParsedElement(text="Code Example", element_type="Title", metadata={}),
        ParsedElement(
            text='def hello():\n    print("Hello, World!")',
            element_type="CodeSnippet",
            metadata={},
        ),
    ]

    parsed = ParsedContent(
        text="Code Example def hello print Hello World",
        elements=elements,
        metadata={"page_count": 1, "section_count": 1, "element_count": 2},
        markdown_content=markdown_with_special,
    )

    # Store and load
    await store_parsed_content(
        kb_id=sample_kb_id,
        document_id=sample_doc_id,
        parsed=parsed,
    )

    loaded = await load_parsed_content(sample_kb_id, sample_doc_id)

    # Verify special characters preserved
    assert loaded is not None
    assert loaded.markdown_content == markdown_with_special
    assert "```python" in loaded.markdown_content
    assert "< > & " in loaded.markdown_content
    assert "中文" in loaded.markdown_content

    # Cleanup
    await delete_parsed_content(sample_kb_id, sample_doc_id)


async def test_delete_parsed_content_removes_file(
    sample_kb_id: UUID,
    sample_doc_id: UUID,
    parsed_content_with_markdown: ParsedContent,
    ensure_bucket,
) -> None:
    """Test that delete_parsed_content removes the .parsed.json file."""
    # Store parsed content
    await store_parsed_content(
        kb_id=sample_kb_id,
        document_id=sample_doc_id,
        parsed=parsed_content_with_markdown,
    )

    # Verify file exists
    object_path = f"{sample_doc_id}/.parsed.json"
    exists_before = await minio_service.file_exists(sample_kb_id, object_path)
    assert exists_before is True

    # Delete parsed content
    result = await delete_parsed_content(sample_kb_id, sample_doc_id)
    assert result is True

    # Verify file no longer exists
    exists_after = await minio_service.file_exists(sample_kb_id, object_path)
    assert exists_after is False


async def test_load_parsed_content_nonexistent_returns_none(
    sample_kb_id: UUID,
    ensure_bucket,
) -> None:
    """Test that loading nonexistent parsed content returns None."""
    nonexistent_doc_id = uuid.uuid4()

    loaded = await load_parsed_content(sample_kb_id, nonexistent_doc_id)

    assert loaded is None


# =============================================================================
# AC-7.28.5: DOCX Markdown Quality Tests
# =============================================================================


async def test_store_load_preserves_heading_levels(
    sample_kb_id: UUID,
    sample_doc_id: UUID,
    ensure_bucket,
) -> None:
    """Test that heading levels (h1-h6) are preserved in markdown storage.

    AC-7.28.5: Heading levels (# for Title, ## for Header, ### for nested).
    """
    markdown_with_headings = """# Title Level 1

## Header Level 2

### Header Level 3

#### Header Level 4

##### Header Level 5

###### Header Level 6"""

    parsed = ParsedContent(
        text="Title Level 1 Header Level 2 Header Level 3",
        elements=[],
        metadata={},
        markdown_content=markdown_with_headings,
    )

    await store_parsed_content(sample_kb_id, sample_doc_id, parsed)
    loaded = await load_parsed_content(sample_kb_id, sample_doc_id)

    assert loaded is not None
    assert "# Title Level 1" in loaded.markdown_content
    assert "## Header Level 2" in loaded.markdown_content
    assert "###### Header Level 6" in loaded.markdown_content

    await delete_parsed_content(sample_kb_id, sample_doc_id)


async def test_store_load_preserves_list_formatting(
    sample_kb_id: UUID,
    sample_doc_id: UUID,
    ensure_bucket,
) -> None:
    """Test that list formatting is preserved in markdown storage.

    AC-7.28.5: List formatting (- for bullets, 1. for numbered).
    """
    markdown_with_lists = """# Lists

## Bullet List

- First bullet item
- Second bullet item
- Third bullet item

## Numbered List

1. First numbered item
2. Second numbered item
3. Third numbered item"""

    parsed = ParsedContent(
        text="Lists Bullet List Numbered List items",
        elements=[],
        metadata={},
        markdown_content=markdown_with_lists,
    )

    await store_parsed_content(sample_kb_id, sample_doc_id, parsed)
    loaded = await load_parsed_content(sample_kb_id, sample_doc_id)

    assert loaded is not None
    assert "- First bullet item" in loaded.markdown_content
    assert "1. First numbered item" in loaded.markdown_content

    await delete_parsed_content(sample_kb_id, sample_doc_id)


async def test_store_load_preserves_table_structure(
    sample_kb_id: UUID,
    sample_doc_id: UUID,
    ensure_bucket,
) -> None:
    """Test that table structure is preserved in markdown storage.

    AC-7.28.5: Table structure (using | markdown syntax).
    """
    markdown_with_table = """# Data Table

| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |"""

    parsed = ParsedContent(
        text="Data Table Column A Column B Column C values",
        elements=[],
        metadata={},
        markdown_content=markdown_with_table,
    )

    await store_parsed_content(sample_kb_id, sample_doc_id, parsed)
    loaded = await load_parsed_content(sample_kb_id, sample_doc_id)

    assert loaded is not None
    assert "| Column A |" in loaded.markdown_content
    assert "|----------|" in loaded.markdown_content
    assert "| Value 1  |" in loaded.markdown_content

    await delete_parsed_content(sample_kb_id, sample_doc_id)
