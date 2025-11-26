"""Knowledge Base Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.permission import PermissionLevel


# Request schemas
class KBCreate(BaseModel):
    """Request schema for creating a Knowledge Base."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class KBUpdate(BaseModel):
    """Request schema for updating a Knowledge Base."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


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
