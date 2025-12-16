"""Recent KB Pydantic schemas for API request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RecentKB(BaseModel):
    """Schema for recent KB response.

    Represents a recently accessed knowledge base.
    Used by GET /api/v1/users/me/recent-kbs endpoint.
    """

    kb_id: UUID = Field(..., description="Knowledge Base UUID")
    kb_name: str = Field(..., description="Knowledge Base name")
    description: str = Field("", description="Knowledge Base description")
    last_accessed: datetime = Field(..., description="Last time user accessed this KB")
    document_count: int = Field(0, ge=0, description="Number of documents in the KB")

    model_config = {"from_attributes": True}
