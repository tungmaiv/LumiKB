"""Pydantic schemas for LLM Model Registry.

Defines request/response schemas for model CRUD operations,
connection testing, and type-specific configuration.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Type and Provider Literals for validation
ModelTypeLiteral = Literal["embedding", "generation", "ner"]
ModelProviderLiteral = Literal[
    "ollama",
    "openai",
    "azure",
    "gemini",
    "anthropic",
    "cohere",
    "deepseek",
    "qwen",
    "mistral",
    "lmstudio",
]
ModelStatusLiteral = Literal["active", "inactive", "deprecated"]
DistanceMetricLiteral = Literal["cosine", "dot", "euclidean"]
ResponseFormatLiteral = Literal["json", "text"]


class EmbeddingModelConfig(BaseModel):
    """Configuration specific to embedding models."""

    dimensions: int = Field(
        ge=1, le=8192, description="Vector dimensions (e.g., 768, 1536, 3072)"
    )
    max_tokens: int = Field(ge=1, le=32768, description="Maximum input tokens")
    normalize: bool = Field(default=True, description="Whether to normalize vectors")
    distance_metric: DistanceMetricLiteral = Field(
        default="cosine", description="Distance metric for similarity"
    )
    batch_size: int = Field(
        default=32, ge=1, le=1000, description="Batch size for embedding requests"
    )
    tags: list[str] = Field(
        default_factory=list, description="Model tags for filtering"
    )


class GenerationModelConfig(BaseModel):
    """Configuration specific to generation models."""

    context_window: int = Field(
        ge=1024, le=10000000, description="Context window size in tokens"
    )
    max_output_tokens: int = Field(ge=1, le=100000, description="Maximum output tokens")
    supports_streaming: bool = Field(
        default=True, description="Whether model supports streaming"
    )
    supports_json_mode: bool = Field(
        default=False, description="Whether model supports JSON output mode"
    )
    supports_vision: bool = Field(
        default=False, description="Whether model supports vision/images"
    )
    temperature_default: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Default temperature"
    )
    temperature_range: tuple[float, float] = Field(
        default=(0.0, 2.0), description="Valid temperature range"
    )
    top_p_default: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Default top_p value"
    )
    timeout_seconds: float = Field(
        default=120.0,
        ge=1.0,
        le=600.0,
        description="Request timeout in seconds (default 120s, max 10 min)",
    )
    cost_per_1m_input: float = Field(
        default=0.0, ge=0.0, description="Cost per 1M input tokens (USD)"
    )
    cost_per_1m_output: float = Field(
        default=0.0, ge=0.0, description="Cost per 1M output tokens (USD)"
    )
    tags: list[str] = Field(
        default_factory=list, description="Model tags for filtering"
    )


class NERModelConfig(BaseModel):
    """Configuration specific to NER (Named Entity Recognition) models.

    Used for entity extraction in GraphRAG pipelines (Epic 8).
    """

    max_tokens: int = Field(ge=1, le=100000, description="Maximum output tokens")
    temperature_default: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Default temperature (0 for deterministic)",
    )
    top_p_default: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Default top_p value (0.1-0.2 recommended)",
    )
    top_k_default: int = Field(
        default=30, ge=1, le=100, description="Default top_k value (20-40 recommended)"
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Request timeout in seconds (default 30s for fast NER)",
    )
    response_format: ResponseFormatLiteral = Field(
        default="json", description="Response format (json for strict output)"
    )
    logprobs_enabled: bool = Field(
        default=True, description="Whether to enable logprobs"
    )
    stop_sequences: list[str] = Field(
        default_factory=lambda: ["\n\n", "<END>", "</json>"],
        description="Stop sequences",
    )
    cost_per_1m_input: float = Field(
        default=0.0, ge=0.0, description="Cost per 1M input tokens (USD)"
    )
    cost_per_1m_output: float = Field(
        default=0.0, ge=0.0, description="Cost per 1M output tokens (USD)"
    )
    tags: list[str] = Field(
        default_factory=list, description="Model tags for filtering"
    )


class LLMModelBase(BaseModel):
    """Base schema for LLM model operations."""

    name: str = Field(
        min_length=1, max_length=255, description="Human-readable model name"
    )
    model_id: str = Field(
        min_length=1, max_length=255, description="Provider-specific model identifier"
    )
    api_endpoint: str | None = Field(
        default=None, max_length=500, description="Custom API endpoint URL"
    )


class LLMModelCreate(LLMModelBase):
    """Schema for creating a new LLM model."""

    type: ModelTypeLiteral = Field(description="Model type: embedding or generation")
    provider: ModelProviderLiteral = Field(description="LLM provider")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Type-specific configuration"
    )
    api_key: str | None = Field(default=None, description="API key (will be encrypted)")
    is_default: bool = Field(
        default=False, description="Set as default model for this type"
    )


class LLMModelUpdate(BaseModel):
    """Schema for updating an LLM model."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    model_id: str | None = Field(default=None, min_length=1, max_length=255)
    config: dict[str, Any] | None = Field(default=None)
    api_endpoint: str | None = Field(default=None, max_length=500)
    api_key: str | None = Field(
        default=None, description="New API key (will be encrypted)"
    )
    status: ModelStatusLiteral | None = Field(default=None)
    is_default: bool | None = Field(default=None)


class LLMModelResponse(LLMModelBase):
    """Schema for LLM model response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: ModelTypeLiteral
    provider: ModelProviderLiteral
    config: dict[str, Any]
    status: ModelStatusLiteral
    is_default: bool
    has_api_key: bool = Field(description="Whether an API key is configured")
    created_at: datetime
    updated_at: datetime


class LLMModelSummary(BaseModel):
    """Summary schema for model lists (excludes config details)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: ModelTypeLiteral
    provider: ModelProviderLiteral
    name: str
    model_id: str
    status: ModelStatusLiteral
    is_default: bool
    has_api_key: bool


class LLMModelList(BaseModel):
    """Schema for paginated model list response."""

    models: list[LLMModelSummary]
    total: int


class ConnectionTestRequest(BaseModel):
    """Schema for connection test request."""

    test_input: str | None = Field(default=None, description="Optional test input text")


class ConnectionTestResult(BaseModel):
    """Schema for connection test result."""

    success: bool
    message: str
    latency_ms: float | None = Field(
        default=None, description="Response latency in milliseconds"
    )
    details: dict[str, Any] | None = Field(
        default=None, description="Additional test details"
    )


class SetDefaultRequest(BaseModel):
    """Schema for setting a model as default."""

    # Empty body - model ID comes from path parameter
    pass


class ModelAvailableResponse(BaseModel):
    """Schema for available models response (public endpoint)."""

    embedding_models: list[LLMModelSummary]
    generation_models: list[LLMModelSummary]
    ner_models: list[LLMModelSummary]


class ModelPublicInfo(BaseModel):
    """Public-facing model information for KB selection."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    provider: ModelProviderLiteral
    model_id: str
    config: dict[str, Any]  # Include dimensions for embedding models
