"""Citation schema definitions for answer synthesis."""

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation metadata for inline [n] markers in synthesized answers."""

    number: int = Field(..., description="Citation number [1], [2], etc.")
    document_id: str = Field(..., description="UUID of source document")
    document_name: str = Field(..., description="Display name of source document")
    page_number: int | None = Field(
        None, description="Page number in source (if available)"
    )
    section_header: str | None = Field(
        None, description="Section header in source (if available)"
    )
    excerpt: str = Field(..., description="Excerpt from chunk (~200 chars)")
    char_start: int = Field(..., description="Character start position in document")
    char_end: int = Field(..., description="Character end position in document")
    confidence: float = Field(
        ..., description="Confidence score inherited from chunk relevance"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "number": 1,
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "document_name": "Acme Bank Proposal.pdf",
                "page_number": 14,
                "section_header": "Authentication Architecture",
                "excerpt": "OAuth 2.0 with PKCE flow ensures secure authentication without storing secrets on client...",
                "char_start": 3450,
                "char_end": 3892,
                "confidence": 0.92,
            }
        }
    }


class CitationMappingError(Exception):
    """Raised when a citation marker cannot be mapped to a source chunk."""

    def __init__(self, marker_num: int, chunk_count: int, message: str | None = None):
        self.marker_num = marker_num
        self.chunk_count = chunk_count
        self.message = (
            message
            or f"Citation [{marker_num}] references non-existent source (only {chunk_count} sources available)"
        )
        super().__init__(self.message)
