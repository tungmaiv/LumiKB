"""Chat conversation schemas for multi-turn RAG conversations."""

from pydantic import BaseModel, Field

from app.schemas.citation import Citation


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
            }
        }
    }
