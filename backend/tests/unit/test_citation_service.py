"""Unit tests for CitationService."""

import pytest

from app.schemas.citation import Citation, CitationMappingError
from app.schemas.search import SearchResultSchema
from app.services.citation_service import CitationService

pytestmark = pytest.mark.unit


@pytest.fixture
def citation_service():
    """Citation service instance."""
    return CitationService()


@pytest.fixture
def mock_chunks():
    """Sample search chunks with rich metadata."""
    return [
        SearchResultSchema(
            document_id="doc-1",
            document_name="Acme Proposal.pdf",
            kb_id="kb-1",
            kb_name="Sales KB",
            chunk_text="OAuth 2.0 with PKCE flow ensures secure authentication without storing secrets on client devices.",
            relevance_score=0.92,
            page_number=14,
            section_header="Authentication Architecture",
            char_start=3450,
            char_end=3540,
        ),
        SearchResultSchema(
            document_id="doc-2",
            document_name="Security Policy.pdf",
            kb_id="kb-1",
            kb_name="Sales KB",
            chunk_text="Multi-factor authentication (MFA) via TOTP is required for all administrative access.",
            relevance_score=0.88,
            page_number=7,
            section_header="Access Control",
            char_start=1200,
            char_end=1285,
        ),
    ]


class TestExtractCitations:
    """Test CitationService.extract_citations()."""

    def test_extract_citations_with_valid_markers(self, citation_service, mock_chunks):
        """AC2: Extract [1], [2] markers from answer."""
        answer = "Our authentication approach uses OAuth 2.0 [1] with MFA [2]."

        text, citations = citation_service.extract_citations(answer, mock_chunks)

        assert text == answer  # Answer unchanged
        assert len(citations) == 2
        assert citations[0].number == 1
        assert citations[0].document_name == "Acme Proposal.pdf"
        assert citations[1].number == 2
        assert citations[1].document_name == "Security Policy.pdf"

    def test_extract_citations_orphaned_marker_raises_error(
        self, citation_service, mock_chunks
    ):
        """AC2: Raise CitationMappingError if [3] exists but only 2 chunks provided."""
        answer = "OAuth [1] and biometric [3] support."  # [3] is invalid

        with pytest.raises(CitationMappingError) as exc_info:
            citation_service.extract_citations(answer, mock_chunks)

        assert exc_info.value.marker_num == 3
        assert exc_info.value.chunk_count == 2

    def test_extract_citations_no_markers(self, citation_service, mock_chunks):
        """AC8: Return empty citations list if no markers found."""
        answer = "No citations in this answer."

        text, citations = citation_service.extract_citations(answer, mock_chunks)

        assert text == answer
        assert citations == []

    def test_extract_citations_duplicate_markers(self, citation_service, mock_chunks):
        """Multiple references to same source return unique citations."""
        answer = "OAuth [1] is secure [1] and recommended [1]."

        text, citations = citation_service.extract_citations(answer, mock_chunks)

        # Should only return one citation for [1]
        assert len(citations) == 1
        assert citations[0].number == 1

    def test_extract_citations_out_of_order(self, citation_service, mock_chunks):
        """Citations are sorted by number even if markers appear out of order."""
        answer = "MFA [2] complements OAuth [1]."

        text, citations = citation_service.extract_citations(answer, mock_chunks)

        # Should be sorted: [1], [2]
        assert len(citations) == 2
        assert citations[0].number == 1
        assert citations[1].number == 2


class TestFindMarkers:
    """Test CitationService._find_markers()."""

    def test_find_markers_extracts_correct_numbers(self, citation_service):
        """AC2: Regex extracts all [n] patterns."""
        text = "OAuth [1] with MFA [2] and biometric [3]."

        markers = citation_service._find_markers(text)

        assert markers == [1, 2, 3]

    def test_find_markers_returns_sorted_unique(self, citation_service):
        """Markers are sorted and deduplicated."""
        text = "Source [3] and [1] and [2] and [1] again."

        markers = citation_service._find_markers(text)

        assert markers == [1, 2, 3]

    def test_find_markers_empty_text(self, citation_service):
        """No markers in empty text."""
        markers = citation_service._find_markers("")
        assert markers == []

    def test_find_markers_no_citations(self, citation_service):
        """No markers found returns empty list."""
        markers = citation_service._find_markers("No citations here.")
        assert markers == []


class TestMapMarkerToChunk:
    """Test CitationService._map_marker_to_chunk()."""

    def test_map_marker_to_chunk_builds_citation_object(
        self, citation_service, mock_chunks
    ):
        """AC3: Map marker to chunk and build Citation with all fields."""
        citation = citation_service._map_marker_to_chunk(1, mock_chunks)

        assert isinstance(citation, Citation)
        assert citation.number == 1
        assert citation.document_id == "doc-1"
        assert citation.document_name == "Acme Proposal.pdf"
        assert citation.page_number == 14
        assert citation.section_header == "Authentication Architecture"
        assert citation.char_start == 3450
        assert citation.char_end == 3540
        assert citation.confidence == 0.92

    def test_map_marker_excerpt_truncation(self, citation_service):
        """AC3: Excerpt truncated to ~200 chars with ellipsis."""
        long_chunk = SearchResultSchema(
            document_id="doc-1",
            document_name="Test.pdf",
            kb_id="kb-1",
            kb_name="Test KB",
            chunk_text="A" * 250,  # 250 characters
            relevance_score=0.9,
            page_number=1,
            section_header="Test",
            char_start=0,
            char_end=250,
        )

        citation = citation_service._map_marker_to_chunk(1, [long_chunk])

        assert len(citation.excerpt) == 203  # 200 + "..."
        assert citation.excerpt.endswith("...")

    def test_map_marker_invalid_number_raises_error(
        self, citation_service, mock_chunks
    ):
        """Marker number > chunk count raises CitationMappingError."""
        with pytest.raises(CitationMappingError):
            citation_service._map_marker_to_chunk(5, mock_chunks)

    def test_map_marker_zero_raises_error(self, citation_service, mock_chunks):
        """Marker number 0 raises CitationMappingError (1-indexed)."""
        with pytest.raises(CitationMappingError):
            citation_service._map_marker_to_chunk(0, mock_chunks)


class TestCitationExtractionErrorHandling:
    """Test AC8: Graceful error handling."""

    def test_extraction_handles_malformed_input_gracefully(self, citation_service):
        """AC8: Malformed input returns answer without citations (no crash)."""
        # Invalid marker format (missing closing bracket)
        answer = "OAuth [1 with MFA."
        chunks = [
            SearchResultSchema(
                document_id="doc-1",
                document_name="Test.pdf",
                kb_id="kb-1",
                kb_name="Test",
                chunk_text="test",
                relevance_score=0.9,
                page_number=1,
                section_header=None,
                char_start=0,
                char_end=4,
            )
        ]

        # Should not crash
        text, citations = citation_service.extract_citations(answer, chunks)

        assert text == answer
        assert citations == []  # No valid markers found
