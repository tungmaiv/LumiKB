"""Citation extraction and mapping service - THE CORE DIFFERENTIATOR of LumiKB."""

import re

import structlog

from app.schemas.citation import Citation, CitationMappingError
from app.schemas.search import SearchResultSchema

logger = structlog.get_logger()

# Pattern for matching [n] citation markers
CITATION_PATTERN = r"\[(\d+)\]"


class CitationService:
    """
    Extracts citation markers [n] from LLM output and maps them to source chunks.

    This is THE CORE DIFFERENTIATOR of LumiKB - ensuring every AI-generated claim
    traces back to verifiable source documents.

    Key responsibilities:
    - Extract [1], [2], [3] markers from answer text
    - Map markers to source chunks (1-indexed: [1] → chunks[0])
    - Build rich Citation objects with full metadata
    - Validate citation accuracy (no orphaned markers)
    - Handle extraction errors gracefully (AC8)
    """

    def extract_citations(
        self, answer: str, source_chunks: list[SearchResultSchema]
    ) -> tuple[str, list[Citation]]:
        """
        Parse answer for [n] markers and map to source chunks.

        Args:
            answer: LLM-generated answer with inline [1], [2] markers
            source_chunks: Source chunks used to generate answer (must match marker count)

        Returns:
            (answer_with_markers, citations_list)

        Raises:
            CitationMappingError: If marker [n] > len(source_chunks) (orphaned marker)

        Example:
            answer = "OAuth 2.0 [1] with MFA [2] is required."
            chunks = [chunk_1, chunk_2]
            text, citations = service.extract_citations(answer, chunks)
            # citations = [Citation(number=1, ...), Citation(number=2, ...)]
        """
        try:
            markers = self._find_markers(answer)

            if not markers:
                logger.warning(
                    "No citation markers found in answer", answer_length=len(answer)
                )
                return answer, []

            # Validate all markers have corresponding chunks
            max_marker = max(markers)
            if max_marker > len(source_chunks):
                raise CitationMappingError(
                    marker_num=max_marker, chunk_count=len(source_chunks)
                )

            # Map each marker to its source chunk
            citations = [
                self._map_marker_to_chunk(marker_num, source_chunks)
                for marker_num in markers
            ]

            logger.info(
                "Citations extracted successfully",
                marker_count=len(markers),
                chunk_count=len(source_chunks),
            )

            return answer, citations

        except CitationMappingError:
            # Re-raise mapping errors (CRITICAL bug)
            raise
        except Exception as e:
            # Graceful degradation for other errors (AC8)
            logger.warning(
                "Citation extraction failed - returning answer without citations",
                error=str(e),
                answer_length=len(answer),
                chunk_count=len(source_chunks),
            )
            return answer, []

    def _find_markers(self, text: str) -> list[int]:
        """
        Extract all [n] citation markers from text.

        Uses regex pattern to find all markers, then returns sorted unique numbers.

        Args:
            text: Text containing [1], [2], etc. markers

        Returns:
            Sorted list of unique citation numbers

        Example:
            _find_markers("OAuth [1] and MFA [2] with backup [1]")
            # Returns [1, 2]
        """
        matches = re.findall(CITATION_PATTERN, text)
        return sorted({int(n) for n in matches})

    def _map_marker_to_chunk(
        self, marker_num: int, chunks: list[SearchResultSchema]
    ) -> Citation:
        """
        Map citation number to source chunk.

        Citations are 1-indexed: [1] maps to chunks[0], [2] to chunks[1], etc.

        Args:
            marker_num: Citation number from [n] marker (1-indexed)
            chunks: List of source chunks

        Returns:
            Citation object with full metadata

        Raises:
            CitationMappingError: If marker_num > len(chunks)
        """
        if marker_num < 1 or marker_num > len(chunks):
            raise CitationMappingError(marker_num, len(chunks))

        # Convert 1-indexed marker to 0-indexed array
        chunk = chunks[marker_num - 1]

        # Truncate excerpt to ~200 chars per tech spec
        excerpt = chunk.chunk_text
        if len(excerpt) > 200:
            excerpt = excerpt[:200] + "..."

        return Citation(
            number=marker_num,
            document_id=chunk.document_id,
            document_name=chunk.document_name,
            page_number=chunk.page_number,
            section_header=chunk.section_header,
            excerpt=excerpt,
            char_start=chunk.char_start,
            char_end=chunk.char_end,
            confidence=chunk.relevance_score,
        )
