"""Pydantic schemas for Observability Admin API.

Story 9-7: Observability Admin API
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# Trace Schemas
# ============================================================================


class TraceListItem(BaseModel):
    """Summary item for trace list responses."""

    trace_id: str = Field(..., description="W3C Trace ID (32-hex)")
    name: str = Field(
        ..., description="Trace name (e.g., chat_completion, document_processing)"
    )
    status: str = Field(..., description="Status: in_progress, completed, failed")
    user_id: UUID | None = Field(None, description="User who initiated the operation")
    kb_id: UUID | None = Field(None, description="Knowledge base context")
    document_id: UUID | None = Field(
        None, description="Associated document ID (from metadata)"
    )
    started_at: datetime = Field(..., description="When the trace started")
    ended_at: datetime | None = Field(None, description="When the trace ended")
    duration_ms: int | None = Field(None, description="Total duration in milliseconds")
    span_count: int = Field(0, description="Number of child spans")

    model_config = {"from_attributes": True}


class TraceListResponse(BaseModel):
    """Paginated response for trace list."""

    items: list[TraceListItem]
    total: int = Field(..., description="Total number of matching traces")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")


class SpanDetail(BaseModel):
    """Detailed span information for trace detail response."""

    span_id: str = Field(..., description="W3C Span ID (16-hex)")
    parent_span_id: str | None = Field(None, description="Parent span ID for nesting")
    name: str = Field(..., description="Span name")
    span_type: str = Field(
        ..., description="Type: llm, retrieval, generation, embedding, etc."
    )
    status: str = Field(..., description="Status: in_progress, completed, failed")
    started_at: datetime = Field(..., description="When the span started")
    ended_at: datetime | None = Field(None, description="When the span ended")
    duration_ms: int | None = Field(None, description="Span duration in milliseconds")
    input_tokens: int | None = Field(None, description="Input token count (LLM spans)")
    output_tokens: int | None = Field(
        None, description="Output token count (LLM spans)"
    )
    model: str | None = Field(None, description="Model identifier (LLM spans)")
    error_message: str | None = Field(None, description="Error message if failed")
    metadata: dict[str, Any] | None = Field(None, description="Type-specific metrics")

    model_config = {"from_attributes": True}


class TraceDetailResponse(BaseModel):
    """Detailed trace response with all child spans."""

    trace_id: str = Field(..., description="W3C Trace ID (32-hex)")
    name: str = Field(..., description="Trace name")
    status: str = Field(..., description="Status: in_progress, completed, failed")
    user_id: UUID | None = Field(None, description="User who initiated the operation")
    kb_id: UUID | None = Field(None, description="Knowledge base context")
    started_at: datetime = Field(..., description="When the trace started")
    ended_at: datetime | None = Field(None, description="When the trace ended")
    duration_ms: int | None = Field(None, description="Total duration in milliseconds")
    metadata: dict[str, Any] | None = Field(
        None, description="Additional trace metadata"
    )
    spans: list[SpanDetail] = Field(
        default_factory=list, description="Child spans ordered by start time"
    )

    model_config = {"from_attributes": True}


# ============================================================================
# Chat History Schemas
# ============================================================================


class CitationItem(BaseModel):
    """Citation reference in chat messages."""

    index: int = Field(..., description="Citation number [1], [2], etc.")
    document_id: str = Field(..., description="Source document UUID")
    document_name: str | None = Field(None, description="Display name")
    chunk_id: str | None = Field(None, description="Specific chunk reference")
    relevance_score: float | None = Field(None, description="Match score 0-1")


class DebugChunkInfo(BaseModel):
    """Debug info for a single retrieved chunk."""

    document_id: str = Field(..., description="Document UUID")
    chunk_index: int = Field(..., description="Chunk index within document")
    relevance_score: float = Field(..., description="Similarity score 0-1")


class DebugTimingInfo(BaseModel):
    """Debug timing info for RAG pipeline."""

    retrieval_ms: float = Field(..., description="Time for retrieval in ms")
    context_assembly_ms: float = Field(
        ..., description="Time for context assembly in ms"
    )


class DebugKBParamsInfo(BaseModel):
    """Debug info for KB parameters."""

    system_prompt_preview: str = Field(
        ..., description="First 100 chars of system prompt"
    )
    citation_style: str = Field(
        ..., description="Citation style (inline/footnote/none)"
    )
    response_language: str = Field(..., description="Response language code")
    uncertainty_handling: str = Field(..., description="Uncertainty handling mode")


class DebugInfoItem(BaseModel):
    """Debug information for RAG pipeline telemetry."""

    kb_params: DebugKBParamsInfo | None = Field(
        None, description="KB configuration used"
    )
    chunks_retrieved: list[DebugChunkInfo] | None = Field(
        None, description="Retrieved chunks info"
    )
    timing: DebugTimingInfo | None = Field(None, description="Pipeline timing metrics")


class ChatMessageItem(BaseModel):
    """Chat message item for history responses."""

    id: UUID = Field(..., description="Message UUID")
    trace_id: str = Field(..., description="W3C Trace ID for correlation")
    session_id: str | None = Field(None, description="Conversation session identifier")
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message text content")
    user_id: UUID | None = Field(None, description="User UUID")
    kb_id: UUID | None = Field(None, description="Knowledge Base UUID")
    created_at: datetime = Field(..., description="When the message was created")
    token_count: int | None = Field(None, description="Tokens used (assistant only)")
    response_time_ms: int | None = Field(
        None, description="Response time in ms (assistant only)"
    )
    citations: list[CitationItem] | None = Field(None, description="Source citations")
    debug_info: dict[str, Any] | None = Field(
        None, description="Debug info when KB debug mode enabled"
    )

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    """Paginated response for chat history."""

    items: list[ChatMessageItem]
    total: int = Field(..., description="Total number of matching messages")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")


class ChatSessionItem(BaseModel):
    """Chat session summary for session list responses."""

    session_id: str = Field(..., description="Conversation session identifier")
    user_id: UUID | None = Field(None, description="User UUID")
    user_name: str | None = Field(None, description="User display name")
    kb_id: UUID | None = Field(None, description="Knowledge Base UUID")
    kb_name: str | None = Field(None, description="Knowledge Base name")
    message_count: int = Field(0, description="Number of messages in session")
    last_message_at: datetime = Field(..., description="Timestamp of last message")
    first_message_at: datetime = Field(..., description="Timestamp of first message")

    model_config = {"from_attributes": True}


class ChatSessionsResponse(BaseModel):
    """Paginated response for chat sessions list."""

    items: list[ChatSessionItem]
    total: int = Field(..., description="Total number of matching sessions")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")


# ============================================================================
# Document Timeline Schemas
# ============================================================================


class DocumentEventItem(BaseModel):
    """Document processing event for timeline responses."""

    id: UUID = Field(..., description="Event UUID")
    trace_id: str = Field(..., description="W3C Trace ID for correlation")
    step_name: str = Field(..., description="Step: upload, parse, chunk, embed, index")
    status: str = Field(..., description="Status: started, completed, failed")
    started_at: datetime = Field(..., description="When the event started")
    ended_at: datetime | None = Field(None, description="When the event ended")
    duration_ms: int | None = Field(None, description="Event duration in milliseconds")
    metrics: dict[str, Any] | None = Field(None, description="Step-specific metrics")
    error_message: str | None = Field(None, description="Error message if failed")

    model_config = {"from_attributes": True}


class DocumentTimelineResponse(BaseModel):
    """Document processing timeline response."""

    document_id: UUID = Field(..., description="Document UUID")
    events: list[DocumentEventItem] = Field(
        default_factory=list, description="Events ordered by timestamp"
    )
    total_duration_ms: int | None = Field(None, description="Total processing duration")


# ============================================================================
# Stats Schemas
# ============================================================================


class LLMUsageStats(BaseModel):
    """LLM usage statistics."""

    total_requests: int = Field(0, description="Total LLM requests")
    total_input_tokens: int = Field(0, description="Total input tokens")
    total_output_tokens: int = Field(0, description="Total output tokens")
    avg_latency_ms: float | None = Field(None, description="Average latency in ms")
    by_model: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Stats breakdown by model"
    )


class ProcessingMetrics(BaseModel):
    """Document processing metrics."""

    total_documents: int = Field(0, description="Documents processed")
    total_chunks: int = Field(0, description="Chunks created")
    avg_processing_time_ms: float | None = Field(
        None, description="Average processing time"
    )
    success_count: int = Field(0, description="Successful processing count")
    failure_count: int = Field(0, description="Failed processing count")


class ChatMetrics(BaseModel):
    """Chat activity metrics."""

    total_messages: int = Field(0, description="Total chat messages")
    total_conversations: int = Field(0, description="Unique conversations")
    avg_response_time_ms: float | None = Field(
        None, description="Average response time"
    )
    avg_tokens_per_response: float | None = Field(
        None, description="Average tokens per response"
    )


class ObservabilityStatsResponse(BaseModel):
    """Aggregated observability statistics response."""

    time_period: str = Field(..., description="Time period: hour, day, week, month")
    start_date: datetime = Field(..., description="Period start date")
    end_date: datetime = Field(..., description="Period end date")
    llm_usage: LLMUsageStats = Field(default_factory=LLMUsageStats)
    processing_metrics: ProcessingMetrics = Field(default_factory=ProcessingMetrics)
    chat_metrics: ChatMetrics = Field(default_factory=ChatMetrics)
    error_rate: float = Field(0.0, description="Percentage of failed traces (0-100)")
