"""KB Recommendation Pydantic schemas for API request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class KBRecommendation(BaseModel):
    """Schema for KB recommendation response.

    Represents a personalized KB recommendation with scoring details.
    Used by GET /api/v1/users/me/kb-recommendations endpoint.
    """

    kb_id: UUID = Field(..., description="Knowledge Base UUID")
    kb_name: str = Field(..., description="Knowledge Base name")
    description: str = Field(..., description="Knowledge Base description")
    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Recommendation score (0-100, higher is better)",
    )
    reason: str = Field(
        ..., description="Human-readable explanation for the recommendation"
    )
    last_accessed: datetime | None = Field(
        None, description="Last time user accessed this KB"
    )
    is_cold_start: bool = Field(
        False, description="True if user has no history (cold start fallback)"
    )

    model_config = {"from_attributes": True}


class KBRecommendationList(BaseModel):
    """Schema for list of KB recommendations.

    Wrapper for recommendation list with metadata.
    """

    recommendations: list[KBRecommendation] = Field(
        default_factory=list, description="List of KB recommendations"
    )
    is_cold_start: bool = Field(
        False, description="True if all recommendations are cold start fallbacks"
    )
