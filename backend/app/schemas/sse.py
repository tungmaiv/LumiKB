"""Server-Sent Events (SSE) schemas for streaming responses.

This module defines SSE event types for streaming search results and AI-generated
answers with citations. Events are emitted in sequence:

1. StatusEvent - "Searching knowledge bases..."
2. StatusEvent - "Generating answer..."
3. TokenEvent* - Word-by-word answer tokens
4. CitationEvent* - Citation metadata when [n] markers detected
5. DoneEvent - Completion signal with confidence
6. ErrorEvent - If errors occur during streaming

*These events repeat as needed during the streaming process.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SSEEventType(str, Enum):
    """SSE event types for streaming responses."""

    STATUS = "status"
    TOKEN = "token"
    CITATION = "citation"
    DONE = "done"
    ERROR = "error"


class SSEEvent(BaseModel):
    """Base SSE event model.

    All SSE events inherit from this base class and implement to_sse_format()
    for proper SSE message formatting.
    """

    type: SSEEventType

    def to_sse_format(self) -> str:
        """Convert event to SSE message format.

        SSE format specification:
        ```
        data: {"type": "...", ...}

        ```
        (Note the blank line after data field)

        Returns:
            Formatted SSE message string with trailing newlines
        """
        data = self.model_dump_json()
        return f"data: {data}\n\n"


class StatusEvent(SSEEvent):
    """Status update event for progress feedback.

    Example:
        {"type": "status", "content": "Searching knowledge bases..."}
    """

    type: SSEEventType = SSEEventType.STATUS
    content: str = Field(
        ...,
        description="Status message to display to user",
        examples=["Searching knowledge bases...", "Generating answer..."],
    )


class TokenEvent(SSEEvent):
    """Answer token event for streaming text.

    Emitted for each word/token as the LLM generates the answer.
    Tokens are streamed word-by-word (not character-by-character) for readability.

    Example:
        {"type": "token", "content": "OAuth "}
        {"type": "token", "content": "2.0 "}
    """

    type: SSEEventType = SSEEventType.TOKEN
    content: str = Field(
        ...,
        description="Answer token (word or phrase)",
        examples=["OAuth ", "2.0 ", "[1] "],
    )


class CitationEvent(SSEEvent):
    """Citation metadata event.

    Emitted immediately when a citation marker [n] is detected in the token stream.
    Frontend can populate the citation panel as citations arrive.

    Example:
        {
          "type": "citation",
          "data": {
            "number": 1,
            "document_id": "doc-uuid",
            "document_name": "Acme Proposal.pdf",
            "page_number": 14,
            "section_header": "Authentication",
            "excerpt": "OAuth 2.0 with PKCE flow ensures...",
            "char_start": 3450,
            "char_end": 3892,
            "confidence": 0.92
          }
        }
    """

    type: SSEEventType = SSEEventType.CITATION
    data: dict[str, Any] = Field(
        ..., description="Full citation object with metadata (matches Citation schema)"
    )


class DoneEvent(SSEEvent):
    """Completion event signaling end of stream.

    Sent after all tokens and citations have been streamed.
    Includes final confidence score and result count for UI display.

    Example:
        {"type": "done", "confidence": 0.88, "result_count": 5}
    """

    type: SSEEventType = SSEEventType.DONE
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Answer confidence score (0.0-1.0)",
        examples=[0.88],
    )
    result_count: int = Field(
        ..., ge=0, description="Total number of search results", examples=[5]
    )


class ErrorEvent(SSEEvent):
    """Error event for streaming failures.

    Sent when an error occurs during streaming (LLM timeout, Qdrant failure, etc.).
    SSE connection closes immediately after error event.

    Example:
        {
          "type": "error",
          "message": "Search service temporarily unavailable",
          "code": "SERVICE_UNAVAILABLE"
        }
    """

    type: SSEEventType = SSEEventType.ERROR
    message: str = Field(
        ...,
        description="User-friendly error message",
        examples=["Search service temporarily unavailable"],
    )
    code: str = Field(
        ...,
        description="Error code for client-side handling",
        examples=["SERVICE_UNAVAILABLE", "LLM_TIMEOUT", "QDRANT_ERROR"],
    )
