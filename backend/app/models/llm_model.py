"""LLM Model registry for managing embedding and generation models.

Stores model configurations for multiple providers (Ollama, OpenAI, Azure, etc.)
with encrypted API key storage and default model designation per type.
"""

import enum
from typing import Any

from sqlalchemy import (
    Boolean,
    Index,
    LargeBinary,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, model_repr


class ModelType(str, enum.Enum):
    """Type of LLM model."""

    EMBEDDING = "embedding"
    GENERATION = "generation"
    NER = "ner"


class ModelProvider(str, enum.Enum):
    """Supported LLM providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    AZURE = "azure"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    MISTRAL = "mistral"
    LMSTUDIO = "lmstudio"


class ModelStatus(str, enum.Enum):
    """Status of an LLM model in the registry."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class LLMModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """LLM Model registry entry.

    Stores configuration for embedding and generation models from various providers.
    Supports encrypted API key storage and default model designation per type.

    Attributes:
        id: UUID primary key.
        type: Model type (embedding or generation).
        provider: LLM provider (ollama, openai, azure, etc.).
        name: Human-readable model name.
        model_id: Provider-specific model identifier.
        config: JSONB configuration specific to model type.
        api_endpoint: Optional custom API endpoint URL.
        api_key_encrypted: Encrypted API key (Fernet symmetric encryption).
        status: Model status (active, inactive, deprecated).
        is_default: Whether this is the default model for its type.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "llm_models"

    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    model_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )

    api_endpoint: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    api_key_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="active",
        index=True,
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    # Partial unique index to ensure only one default per type
    __table_args__ = (
        Index(
            "idx_llm_models_default_unique",
            "type",
            unique=True,
            postgresql_where=(is_default == True),  # noqa: E712
        ),
    )

    def __repr__(self) -> str:
        return model_repr(
            self, "id", "type", "provider", "name", "model_id", "status", "is_default"
        )

    @property
    def type_enum(self) -> ModelType:
        """Get type as enum."""
        return ModelType(self.type)

    @property
    def provider_enum(self) -> ModelProvider:
        """Get provider as enum."""
        return ModelProvider(self.provider)

    @property
    def status_enum(self) -> ModelStatus:
        """Get status as enum."""
        return ModelStatus(self.status)
