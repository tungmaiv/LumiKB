"""Admin dashboard schemas."""

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditEventType(str, Enum):
    """Audit event action types."""

    # Search operations
    SEARCH = "search"

    # Generation operations
    GENERATION_REQUEST = "generation.request"
    GENERATION_COMPLETE = "generation.complete"
    GENERATION_FAILED = "generation.failed"
    GENERATION_FEEDBACK = "generation.feedback"

    # Document operations
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_RETRY = "document.retry"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_REPLACED = "document.replaced"
    DOCUMENT_EXPORT = "document.export"
    DOCUMENT_EXPORT_FAILED = "document.export_failed"

    # Knowledge base operations
    KB_CREATED = "kb.created"
    KB_UPDATED = "kb.updated"
    KB_ARCHIVED = "kb.archived"
    KB_PERMISSION_GRANTED = "kb.permission_granted"
    KB_PERMISSION_REVOKED = "kb.permission_revoked"

    # User operations
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"

    # Feedback operations
    CHANGE_SEARCH = "change_search"
    ADD_CONTEXT = "add_context"
    NEW_DRAFT = "new_draft"
    SELECT_TEMPLATE = "select_template"
    REGENERATE_WITH_STRUCTURE = "regenerate_with_structure"
    REGENERATE_DETAILED = "regenerate_detailed"
    ADD_SECTIONS = "add_sections"
    SEARCH_BETTER_SOURCES = "search_better_sources"
    REVIEW_CITATIONS = "review_citations"
    REGENERATE_WITH_FEEDBACK = "regenerate_with_feedback"
    ADJUST_PARAMETERS = "adjust_parameters"


class AuditResourceType(str, Enum):
    """Audit resource types."""

    DOCUMENT = "document"
    KNOWLEDGE_BASE = "knowledge_base"
    DRAFT = "draft"
    SEARCH = "search"
    USER = "user"


class UserStats(BaseModel):
    """User statistics."""

    total: int = Field(..., description="Total registered users")
    active: int = Field(..., description="Users active in last 30 days")
    inactive: int = Field(..., description="Inactive users")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 150,
                "active": 120,
                "inactive": 30,
            }
        }
    )


class KnowledgeBaseStats(BaseModel):
    """Knowledge Base statistics."""

    total: int = Field(..., description="Total knowledge bases")
    by_status: dict[str, int] = Field(
        ..., description="Knowledge base counts by status"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 45,
                "by_status": {"active": 40, "archived": 5},
            }
        }
    )


class DocumentStats(BaseModel):
    """Document statistics."""

    total: int = Field(..., description="Total documents")
    by_status: dict[str, int] = Field(..., description="Document counts by status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1250,
                "by_status": {"READY": 1100, "PENDING": 50, "FAILED": 100},
            }
        }
    )


class StorageStats(BaseModel):
    """Storage usage statistics."""

    total_bytes: int = Field(..., description="Total storage used in bytes")
    avg_doc_size_bytes: int = Field(..., description="Average document size in bytes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_bytes": 524288000,  # ~500MB
                "avg_doc_size_bytes": 419430,  # ~410KB
            }
        }
    )


class PeriodStats(BaseModel):
    """Activity statistics for time periods."""

    last_24h: int = Field(..., description="Count in last 24 hours")
    last_7d: int = Field(..., description="Count in last 7 days")
    last_30d: int = Field(..., description="Count in last 30 days")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "last_24h": 42,
                "last_7d": 285,
                "last_30d": 1150,
            }
        }
    )


class ActivityStats(BaseModel):
    """User activity statistics."""

    searches: PeriodStats = Field(..., description="Search query counts")
    generations: PeriodStats = Field(..., description="Generation request counts")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "searches": {
                    "last_24h": 42,
                    "last_7d": 285,
                    "last_30d": 1150,
                },
                "generations": {
                    "last_24h": 15,
                    "last_7d": 98,
                    "last_30d": 420,
                },
            }
        }
    )


class TrendData(BaseModel):
    """Trend data for sparkline visualization."""

    searches: list[int] = Field(..., description="Daily search counts for last 30 days")
    generations: list[int] = Field(
        ..., description="Daily generation counts for last 30 days"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "searches": [38, 42, 35, 40, 45, 50, 48, 52, 55, 60] + [0] * 20,
                "generations": [12, 15, 18, 20, 22, 25, 28, 30, 32, 35] + [0] * 20,
            }
        }
    )


class AdminStats(BaseModel):
    """Comprehensive admin dashboard statistics.

    Aggregates system-wide metrics for monitoring and capacity planning.
    Results cached in Redis for 5 minutes to reduce database load.
    """

    users: UserStats = Field(..., description="User statistics")
    knowledge_bases: KnowledgeBaseStats = Field(
        ..., description="Knowledge base statistics"
    )
    documents: DocumentStats = Field(..., description="Document statistics")
    storage: StorageStats = Field(..., description="Storage usage statistics")
    activity: ActivityStats = Field(..., description="User activity statistics")
    trends: TrendData = Field(
        ..., description="Trend data for sparkline visualization (last 30 days)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": {"total": 150, "active": 120, "inactive": 30},
                "knowledge_bases": {
                    "total": 45,
                    "by_status": {"active": 40, "archived": 5},
                },
                "documents": {
                    "total": 1250,
                    "by_status": {"READY": 1100, "PENDING": 50, "FAILED": 100},
                },
                "storage": {
                    "total_bytes": 524288000,
                    "avg_doc_size_bytes": 419430,
                },
                "activity": {
                    "searches": {
                        "last_24h": 42,
                        "last_7d": 285,
                        "last_30d": 1150,
                    },
                    "generations": {
                        "last_24h": 15,
                        "last_7d": 98,
                        "last_30d": 420,
                    },
                },
                "trends": {
                    "searches": [38, 42, 35, 40, 45, 50, 48, 52, 55, 60] + [0] * 20,
                    "generations": [12, 15, 18, 20, 22, 25, 28, 30, 32, 35] + [0] * 20,
                },
            }
        }
    )


class AuditLogFilterRequest(BaseModel):
    """Audit log query filters."""

    start_date: datetime | None = Field(
        None, description="Filter events after this timestamp (UTC, ISO 8601)"
    )
    end_date: datetime | None = Field(
        None, description="Filter events before this timestamp (UTC, ISO 8601)"
    )
    user_email: str | None = Field(
        None, description="Filter by user email (case-insensitive partial match)"
    )
    event_type: AuditEventType | None = Field(None, description="Filter by event type")
    resource_type: AuditResourceType | None = Field(
        None, description="Filter by resource type"
    )
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=50, ge=1, le=10000, description="Items per page (max 10000)"
    )


class AuditEventResponse(BaseModel):
    """Audit event with optional PII redaction."""

    id: UUID
    timestamp: datetime
    user_id: UUID | None
    user_email: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    ip_address: str | None  # Redacted by default
    details: dict | None
    duration_ms: int | None = None
    status: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedAuditResponse(BaseModel):
    """Paginated audit log response."""

    events: list[AuditEventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class AuditExportRequest(BaseModel):
    """Audit log export request."""

    format: Literal["csv", "json"] = Field(
        ..., description="Export format (csv or json)"
    )
    filters: AuditLogFilterRequest = Field(
        ..., description="Filter criteria for export"
    )


class WorkerInfo(BaseModel):
    """Celery worker information."""

    worker_id: str = Field(..., description="Worker ID (e.g., 'worker1@hostname')")
    status: Literal["online", "offline"] = Field(
        ..., description="Worker status (online if heartbeat <= 60s, offline otherwise)"
    )
    active_tasks: int = Field(..., description="Number of active tasks for this worker")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "worker_id": "worker1@localhost",
                "status": "online",
                "active_tasks": 2,
            }
        }
    )


class StepStatusType(str, Enum):
    """Processing step status types for UI badges (AC-7.27.4)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


class StepInfo(BaseModel):
    """Processing step breakdown information (AC-7.27.2).

    Displays per-step timing with columns: Step, Status, Started, Completed, Duration.
    """

    step: str = Field(..., description="Step name (parse, chunk, embed, index)")
    status: StepStatusType = Field(..., description="Step execution status")
    started_at: datetime | None = Field(None, description="Step start time (ISO 8601)")
    completed_at: datetime | None = Field(
        None, description="Step completion time (ISO 8601)"
    )
    duration_ms: int | None = Field(None, description="Step duration in milliseconds")
    error_message: str | None = Field(
        None, description="Error message if status is error"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step": "parse",
                "status": "done",
                "started_at": "2025-12-02T14:30:00Z",
                "completed_at": "2025-12-02T14:30:05Z",
                "duration_ms": 5000,
                "error_message": None,
            }
        }
    )


class TaskInfo(BaseModel):
    """Celery task information with processing step details (AC-7.27.1-7.27.5).

    Extended to support expandable task rows showing per-step breakdown.
    """

    task_id: str = Field(..., description="Task UUID")
    task_name: str = Field(
        ...,
        description="Task name (e.g., 'app.workers.document_tasks.process_document')",
    )
    status: Literal["active"] = Field(
        ..., description="Task status (always 'active' for inspect API)"
    )
    started_at: datetime | None = Field(..., description="Task start time (ISO 8601)")
    estimated_duration: int | None = Field(
        ..., description="Elapsed time in milliseconds"
    )
    # Story 7-27: Extended fields for processing step visibility
    document_id: UUID | None = Field(
        None, description="Associated document UUID for step lookup"
    )
    document_name: str | None = Field(None, description="Document filename for display")
    current_step: str | None = Field(
        None, description="Current processing step (parse, chunk, embed, index)"
    )
    processing_steps: list[StepInfo] | None = Field(
        None, description="Step breakdown with timing (AC-7.27.2)"
    )
    step_errors: dict[str, str] | None = Field(
        None, description="Errors by step name for tooltip display (AC-7.27.5)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "abc-123-def-456",
                "task_name": "app.workers.document_tasks.process_document",
                "status": "active",
                "started_at": "2025-12-02T14:30:00Z",
                "estimated_duration": 540000,
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "document_name": "quarterly_report.pdf",
                "current_step": "chunk",
                "processing_steps": [
                    {
                        "step": "parse",
                        "status": "done",
                        "started_at": "2025-12-02T14:30:00Z",
                        "completed_at": "2025-12-02T14:30:05Z",
                        "duration_ms": 5000,
                    },
                    {
                        "step": "chunk",
                        "status": "in_progress",
                        "started_at": "2025-12-02T14:30:05Z",
                        "completed_at": None,
                        "duration_ms": None,
                    },
                    {"step": "embed", "status": "pending"},
                    {"step": "index", "status": "pending"},
                ],
                "step_errors": None,
            }
        }
    )


class QueueStatus(BaseModel):
    """Celery queue status."""

    queue_name: str = Field(..., description="Queue name (e.g., 'document_processing')")
    pending_tasks: int = Field(..., description="Number of pending tasks in queue")
    active_tasks: int = Field(..., description="Number of active tasks in queue")
    workers: list[WorkerInfo] = Field(..., description="Workers assigned to this queue")
    status: Literal["available", "unavailable"] = Field(
        ...,
        description="Queue status (unavailable if Celery broker unreachable)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "queue_name": "document_processing",
                "pending_tasks": 12,
                "active_tasks": 3,
                "workers": [
                    {
                        "worker_id": "worker1@localhost",
                        "status": "online",
                        "active_tasks": 2,
                    },
                    {
                        "worker_id": "worker2@localhost",
                        "status": "offline",
                        "active_tasks": 0,
                    },
                ],
                "status": "available",
            }
        }
    )


class ConfigCategory(str, Enum):
    """Configuration setting categories."""

    security = "Security"
    processing = "Processing"
    rate_limits = "Rate Limits"


class ConfigDataType(str, Enum):
    """Configuration setting data types."""

    integer = "integer"
    float = "float"
    boolean = "boolean"
    string = "string"


class ConfigSetting(BaseModel):
    """System configuration setting."""

    key: str
    name: str
    value: int | float | bool | str
    default_value: int | float | bool | str
    data_type: ConfigDataType
    description: str
    category: ConfigCategory
    min_value: int | float | None = None
    max_value: int | float | None = None
    requires_restart: bool
    last_modified: datetime | None
    last_modified_by: str | None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "session_timeout_minutes",
                "name": "Session Timeout",
                "value": 720,
                "default_value": 720,
                "data_type": "integer",
                "description": "Duration in minutes before user sessions expire",
                "category": "Security",
                "min_value": 60,
                "max_value": 43200,
                "requires_restart": False,
                "last_modified": "2025-12-02T14:30:00Z",
                "last_modified_by": "admin@example.com",
            }
        }
    )


class ConfigUpdateRequest(BaseModel):
    """Request to update a configuration setting."""

    value: int | float | bool | str


class ConfigUpdateResponse(BaseModel):
    """Response after updating a configuration setting."""

    setting: ConfigSetting
    restart_required: list[str]  # List of setting keys requiring restart


# =============================================================================
# LLM Configuration Schemas (Story 7-2)
# =============================================================================


class LLMConfigModelInfo(BaseModel):
    """Information about a configured LLM model."""

    model_id: UUID | None = Field(None, description="Model registry UUID")
    name: str = Field(..., description="Human-readable model name")
    provider: str = Field(..., description="LLM provider (e.g., ollama, openai)")
    model_identifier: str = Field(..., description="Provider-specific model ID")
    api_endpoint: str | None = Field(None, description="Custom API endpoint")
    is_default: bool = Field(False, description="Whether this is the system default")
    status: str = Field("active", description="Model status")


class LLMConfigSettings(BaseModel):
    """LLM configuration settings for temperature, tokens, etc."""

    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Generation temperature"
    )
    max_tokens: int = Field(
        default=2048, ge=1, le=100000, description="Maximum output tokens"
    )
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Top-p sampling")


class LLMConfig(BaseModel):
    """Centralized LLM configuration response.

    AC-7.2.1: Displays current LLM model settings including provider,
    model name, base URL, and key parameters.
    """

    embedding_model: LLMConfigModelInfo | None = Field(
        None, description="Current embedding model configuration"
    )
    generation_model: LLMConfigModelInfo | None = Field(
        None, description="Current generation model configuration"
    )
    generation_settings: LLMConfigSettings = Field(
        default_factory=LLMConfigSettings,
        description="Generation parameters (temperature, max_tokens)",
    )
    litellm_base_url: str = Field(..., description="LiteLLM proxy base URL")
    last_modified: datetime | None = Field(
        None, description="Last configuration change"
    )
    last_modified_by: str | None = Field(None, description="User who made last change")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "embedding_model": {
                    "model_id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Gemini Text Embedding",
                    "provider": "gemini",
                    "model_identifier": "text-embedding-004",
                    "api_endpoint": None,
                    "is_default": True,
                    "status": "active",
                },
                "generation_model": {
                    "model_id": "123e4567-e89b-12d3-a456-426614174001",
                    "name": "Qwen 2.5",
                    "provider": "qwen",
                    "model_identifier": "qwen2.5-32b-instruct",
                    "api_endpoint": None,
                    "is_default": True,
                    "status": "active",
                },
                "generation_settings": {
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "top_p": 1.0,
                },
                "litellm_base_url": "http://litellm:4000",
                "last_modified": "2025-12-02T14:30:00Z",
                "last_modified_by": "admin@example.com",
            }
        }
    )


class LLMConfigUpdateRequest(BaseModel):
    """Request to update LLM configuration.

    AC-7.2.2: Model switching applies without service restart.
    """

    embedding_model_id: UUID | None = Field(
        None, description="Set embedding model by registry UUID"
    )
    generation_model_id: UUID | None = Field(
        None, description="Set generation model by registry UUID"
    )
    generation_settings: LLMConfigSettings | None = Field(
        None, description="Update generation parameters"
    )


class DimensionMismatchWarning(BaseModel):
    """Warning about embedding dimension mismatch.

    AC-7.2.3: Triggered when selected model dimensions differ from existing KB collections.
    """

    has_mismatch: bool = Field(..., description="Whether there is a dimension mismatch")
    current_dimensions: int | None = Field(
        None, description="Dimensions of currently configured model"
    )
    new_dimensions: int | None = Field(
        None, description="Dimensions of newly selected model"
    )
    affected_kbs: list[str] = Field(
        default_factory=list, description="Names of KBs with existing embeddings"
    )
    warning_message: str | None = Field(None, description="Human-readable warning")


class LLMConfigUpdateResponse(BaseModel):
    """Response after updating LLM configuration."""

    config: LLMConfig = Field(..., description="Updated configuration")
    hot_reload_applied: bool = Field(
        True, description="Whether changes were applied without restart"
    )
    dimension_warning: DimensionMismatchWarning | None = Field(
        None, description="Warning if embedding dimensions changed"
    )


class ModelHealthStatus(BaseModel):
    """Health status for a configured model.

    AC-7.2.4: Health status shown for each configured model.
    """

    model_type: str = Field(..., description="Model type (embedding or generation)")
    model_name: str = Field(..., description="Model name")
    is_healthy: bool = Field(..., description="Whether model is accessible")
    latency_ms: float | None = Field(None, description="Response latency in ms")
    error_message: str | None = Field(None, description="Error message if unhealthy")
    last_checked: datetime = Field(..., description="When health was last checked")


# =============================================================================
# Query Rewriter Model Schemas (Story 8-0)
# =============================================================================


class RewriterModelResponse(BaseModel):
    """Response for query rewriter model configuration.

    Story 8-0: History-Aware Query Rewriting
    Returns the currently configured query rewriter model ID, or null
    if using the default generation model fallback.
    """

    model_id: UUID | None = Field(
        None,
        description="Configured rewriter model UUID, or null to use default generation model",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )


class RewriterModelUpdateRequest(BaseModel):
    """Request to update query rewriter model configuration.

    Story 8-0: History-Aware Query Rewriting
    Set model_id to a generation model UUID, or null to use
    the default generation model fallback.
    """

    model_id: UUID | None = Field(
        None,
        description="Generation model UUID to use for query rewriting, "
        "or null to use default generation model",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )


class LLMHealthResponse(BaseModel):
    """Health status response for all configured models."""

    embedding_health: ModelHealthStatus | None = Field(
        None, description="Embedding model health"
    )
    generation_health: ModelHealthStatus | None = Field(
        None, description="Generation model health"
    )
    overall_healthy: bool = Field(..., description="Whether all models are healthy")


# =============================================================================
# Feedback Analytics Schemas (Story 7-23)
# =============================================================================


class FeedbackTypeCount(BaseModel):
    """Feedback count by type for pie chart visualization (AC-7.23.2)."""

    type: str = Field(
        ..., description="Feedback type (e.g., 'not_relevant', 'inaccurate')"
    )
    count: int = Field(..., description="Number of feedback submissions of this type")

    model_config = ConfigDict(
        json_schema_extra={"example": {"type": "not_relevant", "count": 42}}
    )


class FeedbackDayCount(BaseModel):
    """Daily feedback count for trend chart (AC-7.23.3)."""

    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    count: int = Field(..., description="Number of feedback submissions on this date")

    model_config = ConfigDict(
        json_schema_extra={"example": {"date": "2025-12-01", "count": 5}}
    )


class RecentFeedbackItem(BaseModel):
    """Recent feedback item with user context (AC-7.23.4)."""

    id: str = Field(..., description="Audit event UUID")
    timestamp: str | None = Field(
        ..., description="ISO datetime when feedback was submitted"
    )
    user_id: str | None = Field(None, description="User UUID who submitted feedback")
    user_email: str | None = Field(None, description="User email for display")
    draft_id: str | None = Field(None, description="Draft UUID that received feedback")
    feedback_type: str | None = Field(..., description="Type of feedback submitted")
    feedback_comments: str | None = Field(
        None, description="User's comments (may be truncated)"
    )
    related_request_id: str | None = Field(
        None, description="Related generation request ID"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2025-12-02T14:30:00Z",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "user_email": "user@example.com",
                "draft_id": "123e4567-e89b-12d3-a456-426614174002",
                "feedback_type": "not_relevant",
                "feedback_comments": "The response didn't address my question about...",
                "related_request_id": "req-123",
            }
        }
    )


class FeedbackAnalyticsResponse(BaseModel):
    """Comprehensive feedback analytics response (AC-7.23.6).

    Aggregates all feedback analytics into a single response for the
    admin dashboard. Includes distribution by type, 30-day trend,
    and recent items with user context.
    """

    by_type: list[FeedbackTypeCount] = Field(
        ..., description="Feedback distribution by type for pie chart"
    )
    by_day: list[FeedbackDayCount] = Field(
        ..., description="Daily feedback counts for last 30 days (trend chart)"
    )
    recent: list[RecentFeedbackItem] = Field(
        ..., description="20 most recent feedback items"
    )
    total_count: int = Field(..., description="Total number of feedback submissions")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "by_type": [
                    {"type": "not_relevant", "count": 42},
                    {"type": "inaccurate", "count": 28},
                    {"type": "incomplete", "count": 15},
                ],
                "by_day": [
                    {"date": "2025-12-01", "count": 5},
                    {"date": "2025-12-02", "count": 8},
                ],
                "recent": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "timestamp": "2025-12-02T14:30:00Z",
                        "user_email": "user@example.com",
                        "draft_id": "123e4567-e89b-12d3-a456-426614174002",
                        "feedback_type": "not_relevant",
                        "feedback_comments": "The response didn't address...",
                    }
                ],
                "total_count": 85,
            }
        }
    )


# =============================================================================
# Bulk Queue Retry Schemas (Story 7-27)
# =============================================================================


class BulkRetryError(BaseModel):
    """Error detail for failed retry attempt (AC-7.27.9)."""

    document_id: UUID = Field(..., description="Document that failed to queue")
    error: str = Field(..., description="Error reason")


class BulkRetryRequest(BaseModel):
    """Request to retry failed documents in bulk (AC-7.27.6-7.27.10).

    Supports selective retry by document_ids or retry_all_failed flag.
    Optional kb_id to scope retry to a specific knowledge base.
    """

    document_ids: list[UUID] | None = Field(
        None, description="Specific document UUIDs to retry (selective retry)"
    )
    retry_all_failed: bool = Field(
        False, description="Retry all FAILED documents (overrides document_ids)"
    )
    kb_id: UUID | None = Field(
        None, description="Scope retry to specific knowledge base (optional)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "123e4567-e89b-12d3-a456-426614174001",
                ],
                "retry_all_failed": False,
                "kb_id": None,
            }
        }
    )


class BulkRetryResponse(BaseModel):
    """Response after bulk retry operation (AC-7.27.9).

    Shows queued count, failed count, and error details.
    """

    queued: int = Field(..., description="Number of documents successfully queued")
    failed: int = Field(..., description="Number of documents that failed to queue")
    errors: list[BulkRetryError] = Field(
        default_factory=list, description="Error details for failed retries"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "queued": 15,
                "failed": 2,
                "errors": [
                    {
                        "document_id": "123e4567-e89b-12d3-a456-426614174000",
                        "error": "Document not found",
                    },
                    {
                        "document_id": "123e4567-e89b-12d3-a456-426614174001",
                        "error": "Document already processing",
                    },
                ],
            }
        }
    )


class DocumentStatusFilter(str, Enum):
    """Document status filter for queue tasks endpoint (AC-7.27.15)."""

    ALL = "all"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


# =============================================================================
# Data Retention Cleanup Schemas (Story 9-14)
# =============================================================================


class TableCleanupResult(BaseModel):
    """Result of cleaning up a single table."""

    table: str = Field(..., description="Fully qualified table name")
    chunks_dropped: int | None = Field(
        None, description="Number of chunks dropped (TimescaleDB)"
    )
    chunks_to_drop: int | None = Field(
        None, description="Number of chunks that would be dropped (dry-run)"
    )
    records_deleted: int | None = Field(
        None, description="Number of records deleted (fallback DELETE)"
    )
    records_to_delete: int | None = Field(
        None, description="Number of records that would be deleted (dry-run)"
    )
    chunk_names: list[str] | None = Field(
        None, description="Sample chunk names (limited to 10, dry-run only)"
    )
    dry_run: bool = Field(..., description="Whether this was a dry-run")
    error: str | None = Field(None, description="Error message if cleanup failed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "table": "observability.traces",
                "chunks_dropped": 5,
                "chunks_to_drop": None,
                "records_deleted": None,
                "records_to_delete": None,
                "chunk_names": None,
                "dry_run": False,
                "error": None,
            }
        }
    )


class CleanupError(BaseModel):
    """Error detail for cleanup failure."""

    table: str = Field(..., description="Table that failed cleanup")
    error: str = Field(..., description="Error message")


class CleanupResponse(BaseModel):
    """Response for data retention cleanup operation (Story 9-14).

    Provides detailed results for each table cleaned up, including
    chunk counts for TimescaleDB or row counts for fallback DELETE.
    """

    status: str = Field(
        ..., description="Overall status: 'success', 'partial', or 'failed'"
    )
    dry_run: bool = Field(
        ..., description="Whether this was a preview (no actual deletion)"
    )
    timescaledb_used: bool = Field(
        ..., description="Whether TimescaleDB chunk management was used"
    )
    results: dict[str, TableCleanupResult] = Field(
        ..., description="Cleanup results by table name"
    )
    errors: list[CleanupError] = Field(
        default_factory=list, description="List of errors encountered"
    )
    duration_ms: float = Field(
        ..., description="Total cleanup duration in milliseconds"
    )
    task_id: str | None = Field(None, description="Celery task ID for async tracking")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "dry_run": False,
                "timescaledb_used": True,
                "results": {
                    "observability.traces": {
                        "table": "observability.traces",
                        "chunks_dropped": 5,
                        "dry_run": False,
                    },
                    "observability.spans": {
                        "table": "observability.spans",
                        "chunks_dropped": 3,
                        "dry_run": False,
                    },
                },
                "errors": [],
                "duration_ms": 1250.5,
                "task_id": None,
            }
        }
    )


class CleanupPreviewResponse(BaseModel):
    """Response for cleanup preview (dry-run mode).

    Shows what would be deleted without actually performing deletion.
    """

    dry_run: bool = Field(True, description="Always true for preview")
    timescaledb_available: bool = Field(
        ..., description="Whether TimescaleDB is available"
    )
    tables: list[TableCleanupResult] = Field(
        ..., description="Preview results for each table"
    )
    total_chunks_to_drop: int = Field(
        0, description="Total chunks that would be dropped"
    )
    total_records_to_delete: int = Field(
        0, description="Total records that would be deleted"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dry_run": True,
                "timescaledb_available": True,
                "tables": [
                    {
                        "table": "observability.traces",
                        "chunks_to_drop": 5,
                        "chunk_names": [
                            "_hyper_1_1_chunk",
                            "_hyper_1_2_chunk",
                        ],
                        "dry_run": True,
                    },
                ],
                "total_chunks_to_drop": 8,
                "total_records_to_delete": 0,
            }
        }
    )
