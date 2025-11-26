"""Document chunking utilities for semantic text splitting.

Uses LangChain's RecursiveCharacterTextSplitter with tiktoken tokenizer
to split documents into semantic chunks for embedding.
"""

from dataclasses import dataclass, field
from typing import Any

import structlog
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.workers.parsing import ParsedContent, ParsedElement

logger = structlog.get_logger(__name__)

# Tiktoken encoding for OpenAI ada-002 model
ENCODING_NAME = "cl100k_base"


@dataclass
class DocumentChunk:
    """A single chunk of document content with metadata.

    Attributes:
        text: The chunk text content.
        chunk_index: Position in the sequence of chunks (0-indexed).
        document_id: UUID of the source document.
        document_name: Original filename of the document.
        page_number: Page number if available (from PDF).
        section_header: Section header if available.
        char_start: Character offset start in original document.
        char_end: Character offset end in original document.
        metadata: Additional metadata from parsing.
    """

    text: str
    chunk_index: int
    document_id: str
    document_name: str
    page_number: int | None = None
    section_header: str | None = None
    char_start: int = 0
    char_end: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        """Convert chunk to Qdrant point payload.

        Returns:
            Dict for Qdrant point payload (citation-critical).
        """
        return {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page_number": self.page_number,
            "section_header": self.section_header,
            "chunk_text": self.text,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "chunk_index": self.chunk_index,
        }


class ChunkingError(Exception):
    """Error during document chunking."""


def _get_token_encoder() -> tiktoken.Encoding:
    """Get tiktoken encoder for token counting.

    Returns:
        Tiktoken encoder for cl100k_base (ada-002).
    """
    return tiktoken.get_encoding(ENCODING_NAME)


def _count_tokens(text: str, encoder: tiktoken.Encoding | None = None) -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for.
        encoder: Optional encoder instance (for reuse).

    Returns:
        Number of tokens.
    """
    if encoder is None:
        encoder = _get_token_encoder()
    return len(encoder.encode(text))


def _find_element_metadata(
    elements: list[ParsedElement],
    char_offset: int,
) -> tuple[int | None, str | None]:
    """Find page_number and section_header for a character offset.

    Walks through elements to find the most recent page/section
    that applies to the given offset.

    Args:
        elements: Parsed elements with metadata.
        char_offset: Character offset to find metadata for.

    Returns:
        Tuple of (page_number, section_header).
    """
    current_page: int | None = None
    current_section: str | None = None
    accumulated_chars = 0

    for element in elements:
        # Check if we've passed the target offset
        element_end = accumulated_chars + len(element.text)

        # Update page number if available
        if "page_number" in element.metadata:
            current_page = element.metadata["page_number"]

        # Update section header from Title/Header elements
        if element.element_type in ("Title", "Header"):
            current_section = element.text[:100]  # Truncate long headers

        # If this element covers our target offset, use its metadata
        if accumulated_chars <= char_offset < element_end:
            break

        accumulated_chars = element_end + 2  # +2 for "\n\n" separator

    return current_page, current_section


def _split_oversized_chunk(
    chunk_text: str,
    max_tokens: int,
    encoder: tiktoken.Encoding,
) -> list[str]:
    """Recursively split an oversized chunk until all parts fit.

    Halves the chunk repeatedly until each part is under the token limit.

    Args:
        chunk_text: Text to split.
        max_tokens: Maximum tokens per chunk.
        encoder: Tiktoken encoder.

    Returns:
        List of smaller text chunks.
    """
    tokens = _count_tokens(chunk_text, encoder)

    if tokens <= max_tokens:
        return [chunk_text]

    # Find midpoint by character (rough approximation)
    mid = len(chunk_text) // 2

    # Try to find a good split point near the middle
    # Look for sentence boundaries
    for offset in range(min(500, mid)):
        # Check forward
        if mid + offset < len(chunk_text):
            char = chunk_text[mid + offset]
            if char in ".!?\n":
                mid = mid + offset + 1
                break
        # Check backward
        if mid - offset > 0:
            char = chunk_text[mid - offset]
            if char in ".!?\n":
                mid = mid - offset + 1
                break

    left = chunk_text[:mid].strip()
    right = chunk_text[mid:].strip()

    result = []
    if left:
        result.extend(_split_oversized_chunk(left, max_tokens, encoder))
    if right:
        result.extend(_split_oversized_chunk(right, max_tokens, encoder))

    return result


def chunk_document(
    parsed_content: ParsedContent,
    document_id: str,
    document_name: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[DocumentChunk]:
    """Chunk a parsed document into semantic pieces.

    Uses RecursiveCharacterTextSplitter with tiktoken tokenizer
    to create chunks of approximately chunk_size tokens with
    chunk_overlap token overlap.

    Args:
        parsed_content: ParsedContent from document parsing.
        document_id: UUID of the document (as string).
        document_name: Original filename.
        chunk_size: Target chunk size in tokens (default: from settings).
        chunk_overlap: Overlap between chunks in tokens (default: from settings).

    Returns:
        List of DocumentChunk objects with metadata.

    Raises:
        ChunkingError: If chunking fails.
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    logger.info(
        "chunking_started",
        document_id=document_id,
        document_name=document_name,
        text_length=len(parsed_content.text),
        element_count=len(parsed_content.elements),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not parsed_content.text.strip():
        logger.warning("chunking_empty_document", document_id=document_id)
        return []

    try:
        encoder = _get_token_encoder()

        # Create text splitter with token-based length function
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=lambda x: _count_tokens(x, encoder),
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # Split the full text
        raw_chunks = splitter.split_text(parsed_content.text)

        # Process chunks and add metadata
        chunks: list[DocumentChunk] = []
        char_offset = 0
        chunk_index = 0

        for raw_chunk in raw_chunks:
            # Handle potentially oversized chunks
            chunk_tokens = _count_tokens(raw_chunk, encoder)

            if chunk_tokens > chunk_size * 2:  # Significantly oversized
                # Split oversized chunk further
                sub_chunks = _split_oversized_chunk(raw_chunk, chunk_size, encoder)
                logger.debug(
                    "oversized_chunk_split",
                    original_tokens=chunk_tokens,
                    sub_chunk_count=len(sub_chunks),
                )
            else:
                sub_chunks = [raw_chunk]

            for sub_chunk in sub_chunks:
                # Find position in original text
                chunk_start = parsed_content.text.find(
                    sub_chunk, max(0, char_offset - 100)
                )
                if chunk_start == -1:
                    # Fallback: use approximate position
                    chunk_start = char_offset

                chunk_end = chunk_start + len(sub_chunk)

                # Get metadata from nearest element
                page_number, section_header = _find_element_metadata(
                    parsed_content.elements,
                    chunk_start,
                )

                chunks.append(
                    DocumentChunk(
                        text=sub_chunk,
                        chunk_index=chunk_index,
                        document_id=document_id,
                        document_name=document_name,
                        page_number=page_number,
                        section_header=section_header,
                        char_start=chunk_start,
                        char_end=chunk_end,
                        metadata={
                            "token_count": _count_tokens(sub_chunk, encoder),
                            "source_format": parsed_content.metadata.get(
                                "source_format"
                            ),
                        },
                    )
                )

                chunk_index += 1
                char_offset = chunk_end

        logger.info(
            "chunking_completed",
            document_id=document_id,
            chunk_count=len(chunks),
            avg_chunk_tokens=sum(c.metadata.get("token_count", 0) for c in chunks)
            // max(len(chunks), 1),
        )

        return chunks

    except Exception as e:
        logger.error(
            "chunking_failed",
            document_id=document_id,
            error=str(e),
        )
        raise ChunkingError(f"Failed to chunk document: {e}") from e
