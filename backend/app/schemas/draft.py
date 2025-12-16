"""Draft schemas for document drafts with citations."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.draft import DraftStatus
from app.schemas.citation import Citation


class DraftBase(BaseModel):
    """Base draft schema."""

    title: str = Field(..., max_length=500, description="Draft title")
    template_type: str | None = Field(None, description="Template used for generation")


class DraftCreate(DraftBase):
    """Schema for creating a new draft."""

    kb_id: str = Field(..., description="Knowledge Base ID this draft belongs to")
    content: str = Field("", description="Draft content (markdown with citations)")
    citations: list[Citation] = Field(
        default_factory=list, description="Citation metadata"
    )
    status: DraftStatus = Field(
        DraftStatus.STREAMING, description="Initial draft status"
    )
    word_count: int = Field(0, description="Word count")

    model_config = {
        "json_schema_extra": {
            "example": {
                "kb_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "RFP Response - Acme Corp Security Requirements",
                "template_type": "rfp_response",
                "content": "",
                "citations": [],
                "status": "streaming",
                "word_count": 0,
            }
        }
    }


class DraftUpdate(BaseModel):
    """Schema for updating draft content (PATCH /api/v1/drafts/{id})."""

    content: str = Field(..., description="Updated markdown content with [n] markers")
    citations: list[Citation] = Field(
        ..., description="Updated citations array (sync with markers)"
    )
    status: DraftStatus = Field(
        DraftStatus.EDITING, description="Status after edit (typically 'editing')"
    )
    word_count: int = Field(..., ge=0, description="Updated word count")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "## Executive Summary\n\nOur solution uses OAuth 2.0 [1] with PKCE flow [2] for authentication...",
                "citations": [
                    {
                        "number": 1,
                        "document_id": "550e8400-e29b-41d4-a716-446655440000",
                        "document_name": "Auth Spec.pdf",
                        "page_number": 5,
                        "section_header": "OAuth 2.0",
                        "excerpt": "OAuth 2.0 is an authorization framework...",
                        "char_start": 120,
                        "char_end": 340,
                        "confidence": 0.95,
                    }
                ],
                "status": "editing",
                "word_count": 850,
            }
        }
    }


class RegenerateRequest(BaseModel):
    """Request schema for section regeneration (POST /api/v1/drafts/{id}/regenerate)."""

    selected_text: str = Field(
        ..., description="Original selected text to regenerate"
    )
    instructions: str = Field(
        "",
        max_length=500,
        description="User instructions for regeneration (e.g., 'Make it more technical')",
    )
    keep_citations: bool = Field(
        True, description="Preserve existing citations in selection"
    )
    selection_start: int = Field(
        ..., ge=0, description="Character offset where selection starts"
    )
    selection_end: int = Field(..., gt=0, description="Character offset where selection ends")

    model_config = {
        "json_schema_extra": {
            "example": {
                "selected_text": "Our authentication approach leverages industry-standard protocols.",
                "instructions": "Make it more technical, include MFA details",
                "keep_citations": True,
                "selection_start": 150,
                "selection_end": 220,
            }
        }
    }


class RegenerateResponse(BaseModel):
    """Response schema for section regeneration."""

    regenerated_text: str = Field(..., description="New regenerated section content")
    citations: list[Citation] = Field(
        ..., description="Citations for regenerated section"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "regenerated_text": "Our authentication architecture implements OAuth 2.0 [1] with PKCE extension [2] and supports multi-factor authentication [3]...",
                "citations": [
                    {
                        "number": 1,
                        "document_id": "550e8400-e29b-41d4-a716-446655440000",
                        "document_name": "Auth Spec.pdf",
                        "page_number": 5,
                        "section_header": "OAuth 2.0",
                        "excerpt": "OAuth 2.0 framework...",
                        "char_start": 120,
                        "char_end": 340,
                        "confidence": 0.95,
                    }
                ],
            }
        }
    }


class DraftResponse(DraftBase):
    """Response schema for draft."""

    id: str = Field(..., description="Draft UUID")
    kb_id: str = Field(..., description="Knowledge Base UUID")
    user_id: str | None = Field(None, description="Creator user UUID (nullable)")
    content: str = Field(..., description="Draft content (markdown with citations)")
    citations: list[Citation] = Field(..., description="Citation metadata")
    status: DraftStatus = Field(..., description="Current draft status")
    word_count: int = Field(..., description="Word count")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(
        ..., description="Last update timestamp (for optimistic locking)"
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440123",
                "kb_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440456",
                "title": "RFP Response - Acme Corp Security Requirements",
                "template_type": "rfp_response",
                "content": "## Executive Summary\n\nOur solution...",
                "citations": [],
                "status": "editing",
                "word_count": 850,
                "created_at": "2025-11-28T10:00:00Z",
                "updated_at": "2025-11-28T10:30:00Z",
            }
        },
    }


class DraftListResponse(BaseModel):
    """Response schema for listing drafts."""

    drafts: list[DraftResponse] = Field(..., description="List of drafts")
    total: int = Field(..., description="Total number of drafts for this KB")

    model_config = {
        "json_schema_extra": {
            "example": {
                "drafts": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440123",
                        "kb_id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "550e8400-e29b-41d4-a716-446655440456",
                        "title": "RFP Response - Acme Corp",
                        "template_type": "rfp_response",
                        "content": "...",
                        "citations": [],
                        "status": "complete",
                        "word_count": 1200,
                        "created_at": "2025-11-28T10:00:00Z",
                        "updated_at": "2025-11-28T10:30:00Z",
                    }
                ],
                "total": 1,
            }
        }
    }


class ExportRequest(BaseModel):
    """Request schema for exporting a draft (POST /api/v1/drafts/{id}/export)."""

    format: str = Field(
        ...,
        description="Export format: 'docx', 'pdf', or 'markdown'",
        pattern="^(docx|pdf|markdown)$",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "format": "docx",
            }
        }
    }


class FeedbackRequest(BaseModel):
    """Request schema for submitting feedback on a draft."""

    feedback_type: str = Field(
        ...,
        description="Type of feedback: 'not_relevant', 'wrong_format', 'needs_more_detail', 'low_confidence', or 'other'",
        pattern="^(not_relevant|wrong_format|needs_more_detail|low_confidence|other)$",
    )
    comments: str | None = Field(
        None,
        max_length=500,
        description="Optional custom feedback comments (required for 'other' type)",
    )
    previous_draft_id: str | None = Field(
        None,
        description="Optional previous draft ID for regeneration tracking and history linking",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "feedback_type": "needs_more_detail",
                "comments": "Too high-level, needs more technical depth",
                "previous_draft_id": "550e8400-e29b-41d4-a716-446655440789",
            }
        }
    }


class Alternative(BaseModel):
    """Recovery alternative suggestion."""

    type: str = Field(..., description="Action type identifier")
    description: str = Field(..., description="Human-readable description")
    action: str = Field(..., description="Frontend action to trigger")

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "regenerate_detailed",
                "description": "Regenerate with instructions to provide more detail and examples",
                "action": "regenerate_detailed",
            }
        }
    }


class AlternativeResponse(BaseModel):
    """Response schema for feedback alternatives."""

    alternatives: list[Alternative] = Field(
        ..., description="List of suggested recovery alternatives (max 3)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "alternatives": [
                    {
                        "type": "regenerate_detailed",
                        "description": "Regenerate with instructions to provide more detail and examples",
                        "action": "regenerate_detailed",
                    },
                    {
                        "type": "add_sections",
                        "description": "Manually add specific sections that are missing",
                        "action": "add_sections",
                    },
                    {
                        "type": "start_fresh",
                        "description": "Clear this draft and start over",
                        "action": "new_draft",
                    },
                ]
            }
        }
    }
