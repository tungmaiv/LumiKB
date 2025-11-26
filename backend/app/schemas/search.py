"""Search request and response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.citation import Citation


class SearchRequest(BaseModel):
    """Search request schema."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    kb_ids: list[str] | None = Field(
        default=None,
        description="List of Knowledge Base IDs to search. If None, searches all permitted KBs.",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return",
    )


class SearchResultSchema(BaseModel):
    """Individual search result."""

    document_id: str
    document_name: str
    kb_id: str
    kb_name: str
    chunk_text: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    page_number: int | None = None
    section_header: str | None = None
    char_start: int
    char_end: int


class SearchResponse(BaseModel):
    """Search response schema with answer synthesis and citations (Story 3.2)."""

    query: str
    answer: str = Field(
        default="", description="LLM-synthesized answer with inline [n] markers"
    )
    citations: list[Citation] = Field(
        default_factory=list, description="Citation metadata for [n] markers"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Answer confidence score"
    )
    results: list[SearchResultSchema]
    result_count: int
    message: str | None = None  # For empty state messaging


class QuickSearchRequest(BaseModel):
    """Quick search request schema for command palette (Story 3.7)."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    kb_ids: list[str] | None = Field(
        default=None,
        description="List of Knowledge Base IDs to search. If None, searches all permitted KBs.",
    )


class QuickSearchResult(BaseModel):
    """Individual quick search result (lightweight version)."""

    document_id: str
    document_name: str
    kb_id: str
    kb_name: str
    excerpt: str = Field(..., description="Truncated chunk text (100 chars max)")
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class QuickSearchResponse(BaseModel):
    """Quick search response schema (Story 3.7) - no LLM synthesis."""

    query: str
    results: list[QuickSearchResult]
    kb_count: int = Field(..., description="Number of KBs searched")
    response_time_ms: int


class SimilarSearchRequest(BaseModel):
    """Similar search request schema (Story 3.8)."""

    chunk_id: str = Field(..., description="Qdrant point ID of source chunk")
    kb_ids: list[str] | None = Field(
        default=None,
        description="List of Knowledge Base IDs to search. If None, searches all permitted KBs.",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return",
    )


class ExplainRequest(BaseModel):
    """Explanation request schema (Story 3.9)."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    chunk_id: UUID = Field(..., description="Chunk UUID")
    chunk_text: str = Field(..., description="Text content of the chunk")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    kb_id: UUID = Field(..., description="Knowledge base UUID")


class RelatedDocument(BaseModel):
    """Related document schema for explanation."""

    doc_id: UUID
    doc_name: str
    relevance: float = Field(..., ge=0.0, le=1.0)


class ExplanationResponse(BaseModel):
    """Explanation response schema (Story 3.9)."""

    keywords: list[str] = Field(
        default_factory=list, description="Matching keywords from query"
    )
    explanation: str = Field(..., description="One-sentence relevance explanation")
    concepts: list[str] = Field(
        default_factory=list, description="Key semantic concepts (max 5)"
    )
    related_documents: list[RelatedDocument] = Field(
        default_factory=list, description="Related docs (max 3)"
    )
    section_context: str = Field(default="N/A", description="Document section context")
