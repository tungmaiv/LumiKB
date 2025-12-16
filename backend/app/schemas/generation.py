"""Document generation schemas for template-based generation."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.citation import Citation


class GenerationRequest(BaseModel):
    """Request schema for document generation."""

    kb_id: str = Field(..., description="Knowledge Base ID to generate from")
    mode: str = Field(
        ...,
        description="Generation mode: rfp_response, technical_checklist, requirements_summary, custom",
        pattern="^(rfp_response|technical_checklist|requirements_summary|custom)$",
    )
    additional_prompt: str = Field(
        "",
        max_length=500,
        description="Optional user instructions (max 500 chars)",
    )
    selected_chunk_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of chunk IDs from selected search results (at least 1 required)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "kb_id": "550e8400-e29b-41d4-a716-446655440000",
                "mode": "rfp_response",
                "additional_prompt": "Focus on security features and compliance certifications",
                "selected_chunk_ids": [
                    "chunk-abc123",
                    "chunk-def456",
                    "chunk-ghi789",
                ],
            }
        }
    }


class GenerationResponse(BaseModel):
    """Response schema for document generation."""

    document: str = Field(..., description="Generated document with citation markers")
    citations: list[Citation] = Field(
        ..., description="Citations mapping [n] markers to source chunks"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Generation confidence score (0.0-1.0)"
    )
    generation_id: str = Field(
        ..., description="Unique ID for this generation (for audit logging)"
    )
    mode: str = Field(..., description="Generation mode used")
    sources_used: int = Field(
        ..., description="Number of source chunks actually used in generation"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "document": """## Executive Summary
We propose a comprehensive security solution leveraging OAuth 2.0 [1] and PKCE authentication flow [2]...

## Technical Capabilities
Our platform supports enterprise-grade encryption [3] with AES-256 for data at rest...""",
                "citations": [
                    {
                        "number": 1,
                        "document_id": "550e8400-e29b-41d4-a716-446655440000",
                        "document_name": "Security Architecture.pdf",
                        "page_number": 14,
                        "section_header": "Authentication",
                        "excerpt": "OAuth 2.0 with PKCE flow...",
                        "char_start": 1234,
                        "char_end": 1456,
                        "confidence": 0.92,
                    }
                ],
                "confidence": 0.85,
                "generation_id": "gen-550e8400-e29b-41d4-a716-446655440001",
                "mode": "rfp_response",
                "sources_used": 12,
            }
        }
    }


# SSE Event Schemas for Streaming Generation


class StatusEvent(BaseModel):
    """Status update event during generation."""

    type: Literal["status"] = "status"
    content: str = Field(..., description="Status message (e.g., 'Preparing sources...')")

    model_config = {
        "json_schema_extra": {
            "example": {"type": "status", "content": "Preparing sources..."}
        }
    }


class TokenEvent(BaseModel):
    """Word-by-word streaming token event."""

    type: Literal["token"] = "token"
    content: str = Field(..., description="Single token/word from generated text")

    model_config = {
        "json_schema_extra": {"example": {"type": "token", "content": "OAuth"}}
    }


class CitationEvent(BaseModel):
    """Citation discovered during generation."""

    type: Literal["citation"] = "citation"
    number: int = Field(..., description="Citation number [n]")
    data: Citation = Field(..., description="Full citation details")

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "citation",
                "number": 1,
                "data": {
                    "number": 1,
                    "document_id": "550e8400-e29b-41d4-a716-446655440000",
                    "document_name": "Security Architecture.pdf",
                    "page_number": 14,
                    "section_header": "Authentication",
                    "excerpt": "OAuth 2.0 with PKCE flow...",
                    "char_start": 1234,
                    "char_end": 1456,
                    "confidence": 0.92,
                },
            }
        }
    }


class DoneEvent(BaseModel):
    """Generation completion event with final metadata."""

    type: Literal["done"] = "done"
    generation_id: str = Field(..., description="Unique generation ID")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence score"
    )
    sources_used: int = Field(..., description="Number of sources used")

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "done",
                "generation_id": "gen-550e8400-e29b-41d4-a716-446655440001",
                "confidence": 0.85,
                "sources_used": 12,
            }
        }
    }


class ErrorEvent(BaseModel):
    """Error event when generation fails."""

    type: Literal["error"] = "error"
    message: str = Field(..., description="Error message")

    model_config = {
        "json_schema_extra": {
            "example": {"type": "error", "message": "Insufficient sources provided"}
        }
    }


# Template Schemas for Story 4.9


class TemplateSchema(BaseModel):
    """Template configuration schema."""

    id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Human-readable template name")
    description: str = Field(..., description="Template description")
    system_prompt: str = Field(..., description="System prompt for LLM generation")
    sections: list[str] = Field(..., description="Expected output sections")
    example_output: Optional[str] = Field(
        None, description="Example output preview"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "rfp_response",
                "name": "RFP Response Section",
                "description": "Generate a structured RFP response with executive summary and technical approach",
                "system_prompt": "You are an expert proposal writer...",
                "sections": [
                    "Executive Summary",
                    "Technical Approach",
                    "Relevant Experience",
                    "Pricing",
                ],
                "example_output": "## Executive Summary\n\nOur authentication solution leverages OAuth 2.0 [1]...",
            }
        }
    }


class TemplateListResponse(BaseModel):
    """List of available templates."""

    templates: list[TemplateSchema] = Field(..., description="All available templates")

    model_config = {
        "json_schema_extra": {
            "example": {
                "templates": [
                    {
                        "id": "rfp_response",
                        "name": "RFP Response Section",
                        "description": "Generate a structured RFP response...",
                        "system_prompt": "You are an expert proposal writer...",
                        "sections": [
                            "Executive Summary",
                            "Technical Approach",
                            "Relevant Experience",
                            "Pricing",
                        ],
                        "example_output": "## Executive Summary...",
                    }
                ]
            }
        }
    }
