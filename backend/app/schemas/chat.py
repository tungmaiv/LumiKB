"""Chat conversation schemas for multi-turn RAG conversations."""

from pydantic import BaseModel, Field

from app.schemas.citation import Citation


class ChunkDebugInfo(BaseModel):
    """Debug information for a single retrieved chunk (AC-9.15.11)."""

    preview: str = Field(..., description="First 100 characters of chunk text")
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance/similarity score"
    )
    document_name: str = Field(..., description="Source document name")
    page_number: int | None = Field(None, description="Page number if available")


class KBParamsDebugInfo(BaseModel):
    """Debug information for KB parameters (AC-9.15.11)."""

    system_prompt_preview: str = Field(
        ..., description="First 100 chars of system prompt"
    )
    citation_style: str = Field(
        ..., description="Citation style (inline/footnote/none)"
    )
    response_language: str = Field(..., description="Response language code")
    uncertainty_handling: str = Field(..., description="Uncertainty handling strategy")


class TimingDebugInfo(BaseModel):
    """Debug timing metrics (AC-9.15.11)."""

    retrieval_ms: float = Field(
        ..., ge=0, description="Time spent on retrieval in milliseconds"
    )
    context_assembly_ms: float = Field(
        ..., ge=0, description="Time spent on context assembly in milliseconds"
    )


class DebugInfo(BaseModel):
    """Complete debug information for RAG pipeline telemetry (AC-9.15.10-13).

    Emitted as SSE event type="debug" when KB debug_mode is enabled.
    Contains KB parameters, retrieved chunks with scores, and timing metrics.
    """

    kb_params: KBParamsDebugInfo = Field(
        ..., description="KB prompt configuration parameters"
    )
    chunks_retrieved: list[ChunkDebugInfo] = Field(
        ..., description="Retrieved chunks with scores"
    )
    timing: TimingDebugInfo = Field(..., description="Pipeline timing breakdown")

    model_config = {
        "json_schema_extra": {
            "example": {
                "kb_params": {
                    "system_prompt_preview": "You are a helpful assistant...",
                    "citation_style": "inline",
                    "response_language": "en",
                    "uncertainty_handling": "acknowledge",
                },
                "chunks_retrieved": [
                    {
                        "preview": "OAuth 2.0 with PKCE flow ensures secure...",
                        "similarity_score": 0.89,
                        "document_name": "technical-guide.pdf",
                        "page_number": 12,
                    }
                ],
                "timing": {
                    "retrieval_ms": 145.2,
                    "context_assembly_ms": 12.5,
                },
            }
        }
    }


class ChatRequest(BaseModel):
    """Request schema for chat message."""

    kb_id: str = Field(..., description="Knowledge Base ID to chat with")
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User message (1-5000 characters)",
    )
    conversation_id: str | None = Field(
        None, description="Existing conversation ID for multi-turn (optional)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "kb_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "How did we handle authentication for banking?",
                "conversation_id": "conv-abc123",
            }
        }
    }


class ChatResponse(BaseModel):
    """Response schema for chat message."""

    answer: str = Field(..., description="AI-generated answer with citation markers")
    citations: list[Citation] = Field(
        ..., description="Citations mapping [n] markers to source chunks"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Answer confidence score (0.0-1.0)"
    )
    conversation_id: str = Field(
        ..., description="Conversation ID for follow-up messages"
    )
    debug_info: DebugInfo | None = Field(
        None,
        description="Debug information (AC-9.15.13) - only present when KB debug_mode is enabled",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "Our authentication approach uses OAuth 2.0 [1] with PKCE flow [2] to ensure secure authentication...",
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
                "confidence": 0.87,
                "conversation_id": "conv-abc123",
                "debug_info": None,
            }
        }
    }
