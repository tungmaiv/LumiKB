"""KB Settings Pydantic schemas for KB-level configuration.

Story 7.12: Typed Pydantic schemas for KB-level configuration with runtime
validation and type safety throughout the codebase.
"""

from enum import Enum
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# Enum Types (Task 1: AC #1, #2, #7, #8)
# =============================================================================


class ChunkingStrategy(str, Enum):
    """Strategy for document chunking."""

    FIXED = "fixed"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"


class RetrievalMethod(str, Enum):
    """Method for document retrieval."""

    VECTOR = "vector"
    HYBRID = "hybrid"
    HYDE = "hyde"


class CitationStyle(str, Enum):
    """Style for citation formatting."""

    INLINE = "inline"
    FOOTNOTE = "footnote"
    NONE = "none"


class UncertaintyHandling(str, Enum):
    """How to handle uncertain/low-confidence responses."""

    ACKNOWLEDGE = "acknowledge"
    REFUSE = "refuse"
    BEST_EFFORT = "best_effort"


class TruncationStrategy(str, Enum):
    """Strategy for truncating text that exceeds max length."""

    START = "start"
    END = "end"
    NONE = "none"


class PoolingStrategy(str, Enum):
    """Strategy for pooling embeddings."""

    MEAN = "mean"
    CLS = "cls"
    MAX = "max"
    LAST = "last"


class DocumentParserBackend(str, Enum):
    """Document parser backend selection for all supported formats.

    Story 7.32: Docling Document Parser Integration
    - UNSTRUCTURED: Current default parser (Unstructured library)
    - DOCLING: Advanced parser with better table extraction and layout analysis
    - AUTO: Try Docling first, fallback to Unstructured on failure
    """

    UNSTRUCTURED = "unstructured"  # Current default
    DOCLING = "docling"  # Advanced parser (requires LUMIKB_PARSER_DOCLING_ENABLED=true)
    AUTO = "auto"  # Try docling, fallback to unstructured


# =============================================================================
# Sub-Config Schemas (Task 2: AC #1-8)
# =============================================================================


class ChunkingConfig(BaseModel):
    """Configuration for document chunking (AC-7.12.1)."""

    strategy: ChunkingStrategy = Field(default=ChunkingStrategy.RECURSIVE)
    chunk_size: int = Field(default=512, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    separators: list[str] = Field(default_factory=lambda: ["\n\n", "\n", " ", ""])

    model_config = {"extra": "forbid"}


class RetrievalConfig(BaseModel):
    """Configuration for document retrieval (AC-7.12.2)."""

    top_k: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    method: RetrievalMethod = Field(default=RetrievalMethod.VECTOR)
    mmr_enabled: bool = Field(default=False)
    mmr_lambda: float = Field(default=0.5, ge=0.0, le=1.0)
    hybrid_alpha: float = Field(default=0.5, ge=0.0, le=1.0)

    model_config = {"extra": "forbid"}


class RerankingConfig(BaseModel):
    """Configuration for result reranking (AC-7.12.3)."""

    enabled: bool = Field(default=False)
    model: str | None = Field(default=None)
    top_n: int = Field(default=10, ge=1, le=50)

    model_config = {"extra": "forbid"}


class GenerationConfig(BaseModel):
    """Configuration for text generation (AC-7.12.4)."""

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: int = Field(default=40, ge=1, le=100)
    max_tokens: int = Field(default=2048, ge=100, le=16000)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    stop_sequences: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class NERConfig(BaseModel):
    """Configuration for Named Entity Recognition (AC-7.12.5)."""

    enabled: bool = Field(default=False)
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    entity_types: list[str] = Field(default_factory=list)
    batch_size: int = Field(default=32, ge=1, le=100)

    model_config = {"extra": "forbid"}


class DocumentProcessingConfig(BaseModel):
    """Configuration for document processing (AC-7.12.6, AC-7.32.2).

    Story 7.32: Added parser_backend field for Docling integration.
    """

    ocr_enabled: bool = Field(default=False)
    language_detection: bool = Field(default=True)
    table_extraction: bool = Field(default=True)
    image_extraction: bool = Field(default=False)
    parser_backend: DocumentParserBackend = Field(
        default=DocumentParserBackend.UNSTRUCTURED,
        description=(
            "Document parser backend for all supported formats (PDF, DOCX, MD). "
            "Requires LUMIKB_PARSER_DOCLING_ENABLED=true for 'docling' or 'auto' options."
        ),
    )

    model_config = {"extra": "forbid"}


class KBPromptConfig(BaseModel):
    """Configuration for KB-specific prompts (AC-7.12.7)."""

    system_prompt: str = Field(default="", max_length=4000)
    context_template: str = Field(default="")
    citation_style: CitationStyle = Field(default=CitationStyle.INLINE)
    uncertainty_handling: UncertaintyHandling = Field(
        default=UncertaintyHandling.ACKNOWLEDGE
    )
    response_language: str = Field(default="en")

    model_config = {"extra": "forbid"}


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation (AC-7.12.8, AC-7.12.11)."""

    model_id: UUID | None = Field(default=None)
    batch_size: int = Field(default=32, ge=1, le=100)
    normalize: bool = Field(default=True)
    truncation: TruncationStrategy = Field(default=TruncationStrategy.END)
    max_length: int = Field(default=512, ge=128, le=16384)
    prefix_document: str = Field(default="", max_length=100)
    prefix_query: str = Field(default="", max_length=100)
    pooling_strategy: PoolingStrategy = Field(default=PoolingStrategy.MEAN)

    model_config = {"extra": "forbid"}

    # Re-indexing fields that invalidate existing vectors (AC-7.12.11)
    REINDEX_FIELDS: ClassVar[set[str]] = {
        "model_id",
        "normalize",
        "prefix_document",
        "prefix_query",
        "pooling_strategy",
    }

    def requires_reindex(self, previous: "EmbeddingConfig | None") -> bool:
        """Check if changes require document re-indexing.

        Args:
            previous: Previous embedding configuration to compare against.

        Returns:
            True if any re-indexing field changed, False otherwise.
        """
        if previous is None:
            return False
        for field in self.REINDEX_FIELDS:
            if getattr(self, field) != getattr(previous, field):
                return True
        return False

    def detect_reindex_fields(self, previous: "EmbeddingConfig | None") -> list[str]:
        """Return list of changed fields that require re-indexing.

        Args:
            previous: Previous embedding configuration to compare against.

        Returns:
            List of field names that changed and require re-indexing.
        """
        if previous is None:
            return []
        return [
            f for f in self.REINDEX_FIELDS if getattr(self, f) != getattr(previous, f)
        ]

    def get_reindex_warning(self, changed_fields: list[str]) -> str:
        """Generate user-friendly warning about re-indexing requirement.

        Args:
            changed_fields: List of field names that changed.

        Returns:
            Warning message string, or empty string if no fields changed.
        """
        if not changed_fields:
            return ""
        field_names = ", ".join(changed_fields)
        return (
            f"Changing {field_names} requires re-indexing all documents "
            "in this knowledge base. This operation may take significant time "
            "depending on the number of documents."
        )


# =============================================================================
# Composite KBSettings Schema (Task 3: AC #9-10)
# =============================================================================


class KBSettings(BaseModel):
    """Complete KB-level configuration stored in settings JSONB (AC-7.12.9).

    This schema aggregates all sub-configuration sections with default
    factories. Empty {} settings parse with all defaults applied (AC-7.12.10).

    The three-layer precedence is:
    - Request params (highest priority)
    - KB settings (this schema)
    - System defaults (lowest priority)
    """

    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    reranking: RerankingConfig = Field(default_factory=RerankingConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    ner: NERConfig = Field(default_factory=NERConfig)
    processing: DocumentProcessingConfig = Field(
        default_factory=DocumentProcessingConfig
    )
    prompts: KBPromptConfig = Field(default_factory=KBPromptConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    preset: str | None = Field(
        default=None,
        description="Preset name used for configuration (e.g., 'legal', 'technical')",
    )
    debug_mode: bool = Field(
        default=False,
        description=(
            "Enable debug mode for RAG pipeline telemetry. When enabled, "
            "chat responses include detailed information about retrieved chunks, "
            "similarity scores, KB parameters, and timing metrics."
        ),
    )

    model_config = {"extra": "forbid"}


# =============================================================================
# Preset Schemas (Story 7.16: KB Settings Presets)
# =============================================================================


class PresetInfo(BaseModel):
    """Information about a single KB settings preset (AC-7.16.1).

    Used for listing available presets in the UI dropdown.
    """

    id: str = Field(description="Preset identifier (e.g., 'legal', 'technical')")
    name: str = Field(description="Display name for the preset")
    description: str = Field(description="Brief description of the preset's purpose")


class PresetListResponse(BaseModel):
    """Response schema for listing all available presets (AC-7.16.1)."""

    presets: list[PresetInfo] = Field(
        description="List of available KB settings presets"
    )


class PresetDetailResponse(BaseModel):
    """Response schema for getting a single preset with full settings (AC-7.16.2-6)."""

    id: str = Field(description="Preset identifier (e.g., 'legal', 'technical')")
    name: str = Field(description="Display name for the preset")
    description: str = Field(description="Brief description of the preset's purpose")
    settings: "KBSettings" = Field(
        description="Full settings configuration for this preset"
    )


class PresetDetectRequest(BaseModel):
    """Request schema for detecting which preset matches given settings (AC-7.16.8)."""

    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    prompts: KBPromptConfig = Field(default_factory=KBPromptConfig)
    preset: str | None = Field(default=None)


class PresetDetectResponse(BaseModel):
    """Response schema for preset detection (AC-7.16.8)."""

    detected_preset: str = Field(
        description="Detected preset ID ('legal', 'technical', etc.) or 'custom' if no match"
    )
