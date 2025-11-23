"""Knowledge Base Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.permission import PermissionLevel


class KnowledgeBaseResponse(BaseModel):
    """Response schema for a Knowledge Base."""

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


class KnowledgeBaseListResponse(BaseModel):
    """Response schema for list of Knowledge Bases."""

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
