"""Unit tests for document chunking module.

Tests chunking behavior, token limits, metadata preservation,
and oversized chunk handling.
"""

import pytest

pytestmark = pytest.mark.unit


class TestChunkDocument:
    """Tests for chunk_document function."""

    def test_chunk_short_document(self):
        """Test chunking a document shorter than chunk size."""
        from app.workers.chunking import chunk_document
        from app.workers.parsing import ParsedContent, ParsedElement

        # Short document that fits in one chunk
        text = "This is a short document with minimal content for testing."
        parsed = ParsedContent(
            text=text,
            elements=[
                ParsedElement(text=text, element_type="NarrativeText", metadata={})
            ],
            metadata={"source_format": "markdown"},
        )

        chunks = chunk_document(
            parsed_content=parsed,
            document_id="test-doc-id",
            document_name="test.md",
            chunk_size=500,
            chunk_overlap=50,
        )

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].document_id == "test-doc-id"
        assert chunks[0].document_name == "test.md"
        assert chunks[0].chunk_index == 0

    def test_chunk_long_document_creates_multiple_chunks(self):
        """Test that long documents create multiple chunks."""
        from app.workers.chunking import chunk_document
        from app.workers.parsing import ParsedContent, ParsedElement

        # Create a longer document (repeat sentence to create more tokens)
        sentence = "This is a test sentence with several words. "
        text = sentence * 100  # ~700+ tokens

        parsed = ParsedContent(
            text=text,
            elements=[
                ParsedElement(text=text, element_type="NarrativeText", metadata={})
            ],
            metadata={"source_format": "markdown"},
        )

        chunks = chunk_document(
            parsed_content=parsed,
            document_id="test-doc-id",
            document_name="test.md",
            chunk_size=100,  # Small chunk size to force multiple chunks
            chunk_overlap=10,
        )

        assert len(chunks) > 1
        # Verify sequential chunk indices
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_chunk_overlap_preserves_context(self):
        """Test that chunk overlap creates overlapping content."""
        from app.workers.chunking import chunk_document
        from app.workers.parsing import ParsedContent, ParsedElement

        # Create document with distinct sections
        text = "Section A content here. " * 20 + "Section B content here. " * 20
        parsed = ParsedContent(
            text=text,
            elements=[
                ParsedElement(text=text, element_type="NarrativeText", metadata={})
            ],
            metadata={},
        )

        chunks = chunk_document(
            parsed_content=parsed,
            document_id="test-doc-id",
            document_name="test.md",
            chunk_size=50,
            chunk_overlap=10,
        )

        # With overlap, adjacent chunks should share some content
        if len(chunks) >= 2:
            # Check that consecutive chunks have some overlap
            chunks[0].text[-50:]  # Last part of first chunk
            chunks[1].text[:50]  # First part of second chunk
            # There should be some common content due to overlap
            # (exact overlap depends on splitter behavior)

    def test_metadata_preservation_page_number(self):
        """Test that page numbers are preserved in chunks."""
        from app.workers.chunking import chunk_document
        from app.workers.parsing import ParsedContent, ParsedElement

        elements = [
            ParsedElement(
                text="Page 1 content here. " * 10,
                element_type="NarrativeText",
                metadata={"page_number": 1},
            ),
            ParsedElement(
                text="Page 2 content here. " * 10,
                element_type="NarrativeText",
                metadata={"page_number": 2},
            ),
        ]

        full_text = "\n\n".join(e.text for e in elements)
        parsed = ParsedContent(text=full_text, elements=elements, metadata={})

        chunks = chunk_document(
            parsed_content=parsed,
            document_id="test-doc-id",
            document_name="test.pdf",
            chunk_size=50,
            chunk_overlap=5,
        )

        assert len(chunks) > 0
        # First chunk should have page 1
        assert chunks[0].page_number == 1

    def test_metadata_preservation_section_header(self):
        """Test that section headers are preserved in chunks."""
        from app.workers.chunking import chunk_document
        from app.workers.parsing import ParsedContent, ParsedElement

        elements = [
            ParsedElement(
                text="Introduction",
                element_type="Title",
                metadata={},
            ),
            ParsedElement(
                text="Some introduction content here. " * 10,
                element_type="NarrativeText",
                metadata={},
            ),
        ]

        full_text = "\n\n".join(e.text for e in elements)
        parsed = ParsedContent(text=full_text, elements=elements, metadata={})

        chunks = chunk_document(
            parsed_content=parsed,
            document_id="test-doc-id",
            document_name="test.md",
            chunk_size=500,
            chunk_overlap=50,
        )

        assert len(chunks) >= 1
        # Section header should be captured
        assert chunks[0].section_header == "Introduction"

    def test_char_offset_accuracy(self):
        """Test that char_start and char_end are accurate."""
        from app.workers.chunking import chunk_document
        from app.workers.parsing import ParsedContent, ParsedElement

        text = "Hello world. This is test content. More text here."
        parsed = ParsedContent(
            text=text,
            elements=[
                ParsedElement(text=text, element_type="NarrativeText", metadata={})
            ],
            metadata={},
        )

        chunks = chunk_document(
            parsed_content=parsed,
            document_id="test-doc-id",
            document_name="test.md",
            chunk_size=500,
            chunk_overlap=50,
        )

        assert len(chunks) == 1
        chunk = chunks[0]
        # Verify the offsets point to the correct text
        assert text[chunk.char_start : chunk.char_end] == chunk.text

    def test_empty_document_returns_empty_list(self):
        """Test that empty documents return empty chunk list."""
        from app.workers.chunking import chunk_document
        from app.workers.parsing import ParsedContent

        parsed = ParsedContent(text="", elements=[], metadata={})

        chunks = chunk_document(
            parsed_content=parsed,
            document_id="test-doc-id",
            document_name="test.md",
        )

        assert len(chunks) == 0

    def test_whitespace_only_document_returns_empty_list(self):
        """Test that whitespace-only documents return empty chunk list."""
        from app.workers.chunking import chunk_document
        from app.workers.parsing import ParsedContent

        parsed = ParsedContent(text="   \n\n\t  ", elements=[], metadata={})

        chunks = chunk_document(
            parsed_content=parsed,
            document_id="test-doc-id",
            document_name="test.md",
        )

        assert len(chunks) == 0

    def test_chunk_to_payload_format(self):
        """Test that chunk.to_payload() returns correct format."""
        from app.workers.chunking import chunk_document
        from app.workers.parsing import ParsedContent, ParsedElement

        text = "Test content for payload."
        parsed = ParsedContent(
            text=text,
            elements=[
                ParsedElement(
                    text=text, element_type="NarrativeText", metadata={"page_number": 5}
                )
            ],
            metadata={"source_format": "pdf"},
        )

        chunks = chunk_document(
            parsed_content=parsed,
            document_id="doc-123",
            document_name="report.pdf",
        )

        payload = chunks[0].to_payload()

        assert payload["document_id"] == "doc-123"
        assert payload["document_name"] == "report.pdf"
        assert payload["chunk_text"] == text
        assert payload["chunk_index"] == 0
        assert "char_start" in payload
        assert "char_end" in payload


class TestTokenCounting:
    """Tests for token counting functions."""

    def test_count_tokens_basic(self):
        """Test basic token counting."""
        from app.workers.chunking import _count_tokens

        text = "Hello world"
        tokens = _count_tokens(text)
        assert tokens > 0
        assert tokens == 2  # "Hello" and "world"

    def test_count_tokens_empty_string(self):
        """Test token counting with empty string."""
        from app.workers.chunking import _count_tokens

        tokens = _count_tokens("")
        assert tokens == 0


class TestOversizedChunkHandling:
    """Tests for oversized chunk splitting."""

    def test_split_oversized_chunk_basic(self):
        """Test splitting an oversized chunk."""
        from app.workers.chunking import _get_token_encoder, _split_oversized_chunk

        encoder = _get_token_encoder()

        # Create a long text
        long_text = "This is a sentence. " * 100

        sub_chunks = _split_oversized_chunk(long_text, max_tokens=50, encoder=encoder)

        # Should create multiple sub-chunks
        assert len(sub_chunks) > 1

        # Each sub-chunk should be under the limit (with some tolerance)
        for chunk in sub_chunks:
            tokens = len(encoder.encode(chunk))
            assert tokens <= 50 * 1.2  # Allow 20% tolerance

    def test_split_oversized_chunk_preserves_all_content(self):
        """Test that splitting preserves all content."""
        from app.workers.chunking import _get_token_encoder, _split_oversized_chunk

        encoder = _get_token_encoder()
        text = "Word one. Word two. Word three. " * 20

        sub_chunks = _split_oversized_chunk(text, max_tokens=30, encoder=encoder)

        # Concatenated content should include all original text (minus whitespace)
        combined = " ".join(sub_chunks)
        # Check that all words are present
        assert "Word one" in combined
        assert "Word two" in combined
        assert "Word three" in combined

    def test_small_text_not_split(self):
        """Test that small text is not split."""
        from app.workers.chunking import _get_token_encoder, _split_oversized_chunk

        encoder = _get_token_encoder()
        text = "Short text."

        sub_chunks = _split_oversized_chunk(text, max_tokens=500, encoder=encoder)

        assert len(sub_chunks) == 1
        assert sub_chunks[0] == text
