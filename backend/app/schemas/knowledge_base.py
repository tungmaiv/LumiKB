"""Knowledge Base Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.permission import PermissionLevel


# Nested model info schemas (Story 7-10)
class EmbeddingModelInfo(BaseModel):
    """Embedded model info in KB response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    model_id: str
    dimensions: int | None = Field(
        default=None, description="Vector dimensions from model config"
    )
    distance_metric: str | None = Field(
        default=None, description="Distance metric (cosine, euclidean, dot)"
    )


class GenerationModelInfo(BaseModel):
    """Generation model info in KB response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    model_id: str
    context_window: int | None = Field(
        default=None, description="Context window size from model config"
    )
    max_tokens: int | None = Field(
        default=None, description="Max output tokens from model config"
    )


# Request schemas
class KBCreate(BaseModel):
    """Request schema for creating a Knowledge Base."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    # Model selection (Story 7-10)
    embedding_model_id: UUID | None = Field(
        default=None, description="UUID of embedding model from registry"
    )
    generation_model_id: UUID | None = Field(
        default=None, description="UUID of generation model from registry"
    )
    # KB-level RAG parameter overrides
    similarity_threshold: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)"
    )
    search_top_k: int | None = Field(
        default=None, ge=1, le=100, description="Number of results to retrieve (1-100)"
    )
    temperature: float | None = Field(
        default=None, ge=0.0, le=2.0, description="Generation temperature (0.0-2.0)"
    )
    rerank_enabled: bool | None = Field(
        default=None, description="Enable reranking of search results"
    )


class KBUpdate(BaseModel):
    """Request schema for updating a Knowledge Base."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = Field(default=None, max_length=20)
    # Model selection (Story 7-10) - embedding_model_id may be locked
    embedding_model_id: UUID | None = Field(
        default=None,
        description="UUID of embedding model (locked after first document)",
    )
    generation_model_id: UUID | None = Field(
        default=None, description="UUID of generation model (always changeable)"
    )
    # KB-level RAG parameter overrides
    similarity_threshold: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)"
    )
    search_top_k: int | None = Field(
        default=None, ge=1, le=100, description="Number of results to retrieve (1-100)"
    )
    temperature: float | None = Field(
        default=None, ge=0.0, le=2.0, description="Generation temperature (0.0-2.0)"
    )
    rerank_enabled: bool | None = Field(
        default=None, description="Enable reranking of search results"
    )


# Response schemas
class KBSummary(BaseModel):
    """Summary schema for KB list endpoint (AC6)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    document_count: int = Field(
        default=0, description="Number of non-archived documents"
    )
    permission_level: PermissionLevel = Field(
        description="Current user's permission level on this KB"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    archived_at: datetime | None = Field(
        default=None, description="When the KB was archived (null if active)"
    )
    # Model IDs for KB Settings modal (Story 7-10)
    embedding_model_id: UUID | None = Field(
        default=None, description="Configured embedding model ID"
    )
    generation_model_id: UUID | None = Field(
        default=None, description="Configured generation model ID"
    )
    embedding_model_locked: bool = Field(
        default=False, description="True if KB has documents (embedding model locked)"
    )
    updated_at: datetime


class KBResponse(BaseModel):
    """Detailed response schema for a Knowledge Base (AC3)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    owner_id: UUID
    status: str
    document_count: int = Field(
        default=0, description="Count of non-archived documents"
    )
    total_size_bytes: int = Field(default=0, description="Sum of document file sizes")
    permission_level: PermissionLevel | None = Field(
        default=None,
        description="Current user's permission level on this KB",
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    # Model configuration (Story 7-10)
    embedding_model: EmbeddingModelInfo | None = Field(
        default=None, description="Configured embedding model"
    )
    generation_model: GenerationModelInfo | None = Field(
        default=None, description="Configured generation model"
    )
    qdrant_collection_name: str | None = Field(
        default=None, description="Qdrant collection name for this KB"
    )
    qdrant_vector_size: int | None = Field(
        default=None, description="Vector dimensions for this KB"
    )
    # RAG parameters
    similarity_threshold: float | None = Field(
        default=None, description="KB-level similarity threshold"
    )
    search_top_k: int | None = Field(
        default=None, description="KB-level top_k override"
    )
    temperature: float | None = Field(
        default=None, description="KB-level generation temperature"
    )
    rerank_enabled: bool | None = Field(
        default=None, description="Whether reranking is enabled"
    )
    # Model lock status
    embedding_model_locked: bool = Field(
        default=False,
        description="True if embedding model cannot be changed (documents exist)",
    )
    # Archive status (Story 7-24)
    archived_at: datetime | None = Field(
        default=None, description="When the KB was archived (null if active)"
    )
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseResponse(BaseModel):
    """Response schema for a Knowledge Base (legacy, kept for compatibility)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    status: str
    document_count: int = Field(default=0, description="Number of documents in the KB")
    permission_level: PermissionLevel | None = Field(
        default=None,
        description="Current user's permission level on this KB",
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    archived_at: datetime | None = Field(
        default=None, description="When the KB was archived (null if active)"
    )
    created_at: datetime
    updated_at: datetime


class KBListResponse(BaseModel):
    """Response schema for paginated list of Knowledge Base summaries."""

    data: list[KBSummary]
    total: int = Field(description="Total number of KBs available")
    page: int = Field(description="Current page number")
    limit: int = Field(description="Items per page")


class KnowledgeBaseListResponse(BaseModel):
    """Response schema for list of Knowledge Bases (legacy)."""

    data: list[KnowledgeBaseResponse]


class DocumentMetadataResponse(BaseModel):
    """Response schema for document metadata (minimal)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """Response schema for list of documents in a KB."""

    data: list[DocumentMetadataResponse]
