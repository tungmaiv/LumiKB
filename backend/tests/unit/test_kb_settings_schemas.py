"""Unit tests for KB Settings Pydantic schemas (Story 7.12)."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.kb_settings import (
    ChunkingConfig,
    ChunkingStrategy,
    CitationStyle,
    DocumentProcessingConfig,
    EmbeddingConfig,
    GenerationConfig,
    KBPromptConfig,
    KBSettings,
    NERConfig,
    PoolingStrategy,
    RerankingConfig,
    RetrievalConfig,
    RetrievalMethod,
    TruncationStrategy,
    UncertaintyHandling,
)

pytestmark = pytest.mark.unit


# =============================================================================
# Task 5: Unit Tests - Enum Types (AC: #1, #2, #7, #8)
# =============================================================================


class TestChunkingStrategyEnum:
    """Tests for ChunkingStrategy enum."""

    def test_enum_values(self) -> None:
        """Test ChunkingStrategy has correct values."""
        assert ChunkingStrategy.FIXED.value == "fixed"
        assert ChunkingStrategy.RECURSIVE.value == "recursive"
        assert ChunkingStrategy.SEMANTIC.value == "semantic"

    def test_enum_from_string(self) -> None:
        """Test creating enum from string value."""
        assert ChunkingStrategy("fixed") == ChunkingStrategy.FIXED
        assert ChunkingStrategy("recursive") == ChunkingStrategy.RECURSIVE
        assert ChunkingStrategy("semantic") == ChunkingStrategy.SEMANTIC

    def test_json_serialization(self) -> None:
        """Test enum JSON serialization."""
        config = ChunkingConfig(strategy=ChunkingStrategy.SEMANTIC)
        data = config.model_dump()
        assert data["strategy"] == "semantic"

    def test_json_deserialization(self) -> None:
        """Test enum JSON deserialization."""
        config = ChunkingConfig.model_validate({"strategy": "semantic"})
        assert config.strategy == ChunkingStrategy.SEMANTIC


class TestRetrievalMethodEnum:
    """Tests for RetrievalMethod enum."""

    def test_enum_values(self) -> None:
        """Test RetrievalMethod has correct values."""
        assert RetrievalMethod.VECTOR.value == "vector"
        assert RetrievalMethod.HYBRID.value == "hybrid"
        assert RetrievalMethod.HYDE.value == "hyde"

    def test_json_serialization(self) -> None:
        """Test enum JSON serialization."""
        config = RetrievalConfig(method=RetrievalMethod.HYBRID)
        data = config.model_dump()
        assert data["method"] == "hybrid"


class TestCitationStyleEnum:
    """Tests for CitationStyle enum."""

    def test_enum_values(self) -> None:
        """Test CitationStyle has correct values."""
        assert CitationStyle.INLINE.value == "inline"
        assert CitationStyle.FOOTNOTE.value == "footnote"
        assert CitationStyle.NONE.value == "none"


class TestUncertaintyHandlingEnum:
    """Tests for UncertaintyHandling enum."""

    def test_enum_values(self) -> None:
        """Test UncertaintyHandling has correct values."""
        assert UncertaintyHandling.ACKNOWLEDGE.value == "acknowledge"
        assert UncertaintyHandling.REFUSE.value == "refuse"
        assert UncertaintyHandling.BEST_EFFORT.value == "best_effort"


class TestTruncationStrategyEnum:
    """Tests for TruncationStrategy enum."""

    def test_enum_values(self) -> None:
        """Test TruncationStrategy has correct values."""
        assert TruncationStrategy.START.value == "start"
        assert TruncationStrategy.END.value == "end"
        assert TruncationStrategy.NONE.value == "none"


class TestPoolingStrategyEnum:
    """Tests for PoolingStrategy enum."""

    def test_enum_values(self) -> None:
        """Test PoolingStrategy has correct values."""
        assert PoolingStrategy.MEAN.value == "mean"
        assert PoolingStrategy.CLS.value == "cls"
        assert PoolingStrategy.MAX.value == "max"
        assert PoolingStrategy.LAST.value == "last"


# =============================================================================
# Task 6: Unit Tests - Sub-Config Validation (AC: #1-8)
# =============================================================================


class TestChunkingConfig:
    """Tests for ChunkingConfig schema validation (AC-7.12.1)."""

    def test_default_values(self) -> None:
        """Test ChunkingConfig with all defaults."""
        config = ChunkingConfig()
        assert config.strategy == ChunkingStrategy.RECURSIVE
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50
        assert config.separators == ["\n\n", "\n", " ", ""]

    def test_chunk_size_min_boundary(self) -> None:
        """Test chunk_size minimum value (100)."""
        config = ChunkingConfig(chunk_size=100)
        assert config.chunk_size == 100

    def test_chunk_size_max_boundary(self) -> None:
        """Test chunk_size maximum value (2000)."""
        config = ChunkingConfig(chunk_size=2000)
        assert config.chunk_size == 2000

    def test_chunk_size_below_min_fails(self) -> None:
        """Test chunk_size below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ChunkingConfig(chunk_size=99)
        assert "greater than or equal to 100" in str(exc_info.value)

    def test_chunk_size_above_max_fails(self) -> None:
        """Test chunk_size above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ChunkingConfig(chunk_size=2001)
        assert "less than or equal to 2000" in str(exc_info.value)

    def test_chunk_overlap_min_boundary(self) -> None:
        """Test chunk_overlap minimum value (0)."""
        config = ChunkingConfig(chunk_overlap=0)
        assert config.chunk_overlap == 0

    def test_chunk_overlap_max_boundary(self) -> None:
        """Test chunk_overlap maximum value (500)."""
        config = ChunkingConfig(chunk_overlap=500)
        assert config.chunk_overlap == 500

    def test_chunk_overlap_below_min_fails(self) -> None:
        """Test chunk_overlap below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ChunkingConfig(chunk_overlap=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_chunk_overlap_above_max_fails(self) -> None:
        """Test chunk_overlap above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ChunkingConfig(chunk_overlap=501)
        assert "less than or equal to 500" in str(exc_info.value)

    def test_separators_list(self) -> None:
        """Test separators accepts list of strings."""
        config = ChunkingConfig(separators=[".", "!", "?"])
        assert config.separators == [".", "!", "?"]

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError) as exc_info:
            ChunkingConfig(unknown_field="value")  # type: ignore
        assert "Extra inputs are not permitted" in str(exc_info.value)


class TestRetrievalConfig:
    """Tests for RetrievalConfig schema validation (AC-7.12.2)."""

    def test_default_values(self) -> None:
        """Test RetrievalConfig with all defaults."""
        config = RetrievalConfig()
        assert config.top_k == 10
        assert config.similarity_threshold == 0.7
        assert config.method == RetrievalMethod.VECTOR
        assert config.mmr_enabled is False
        assert config.mmr_lambda == 0.5
        assert config.hybrid_alpha == 0.5

    def test_top_k_min_boundary(self) -> None:
        """Test top_k minimum value (1)."""
        config = RetrievalConfig(top_k=1)
        assert config.top_k == 1

    def test_top_k_max_boundary(self) -> None:
        """Test top_k maximum value (100)."""
        config = RetrievalConfig(top_k=100)
        assert config.top_k == 100

    def test_top_k_below_min_fails(self) -> None:
        """Test top_k below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalConfig(top_k=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_top_k_above_max_fails(self) -> None:
        """Test top_k above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalConfig(top_k=101)
        assert "less than or equal to 100" in str(exc_info.value)

    def test_similarity_threshold_min_boundary(self) -> None:
        """Test similarity_threshold minimum value (0.0)."""
        config = RetrievalConfig(similarity_threshold=0.0)
        assert config.similarity_threshold == 0.0

    def test_similarity_threshold_max_boundary(self) -> None:
        """Test similarity_threshold maximum value (1.0)."""
        config = RetrievalConfig(similarity_threshold=1.0)
        assert config.similarity_threshold == 1.0

    def test_similarity_threshold_below_min_fails(self) -> None:
        """Test similarity_threshold below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalConfig(similarity_threshold=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_similarity_threshold_above_max_fails(self) -> None:
        """Test similarity_threshold above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalConfig(similarity_threshold=1.1)
        assert "less than or equal to 1" in str(exc_info.value)

    def test_mmr_lambda_min_boundary(self) -> None:
        """Test mmr_lambda minimum value (0.0)."""
        config = RetrievalConfig(mmr_lambda=0.0)
        assert config.mmr_lambda == 0.0

    def test_mmr_lambda_max_boundary(self) -> None:
        """Test mmr_lambda maximum value (1.0)."""
        config = RetrievalConfig(mmr_lambda=1.0)
        assert config.mmr_lambda == 1.0

    def test_mmr_lambda_below_min_fails(self) -> None:
        """Test mmr_lambda below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalConfig(mmr_lambda=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_hybrid_alpha_min_boundary(self) -> None:
        """Test hybrid_alpha minimum value (0.0)."""
        config = RetrievalConfig(hybrid_alpha=0.0)
        assert config.hybrid_alpha == 0.0

    def test_hybrid_alpha_max_boundary(self) -> None:
        """Test hybrid_alpha maximum value (1.0)."""
        config = RetrievalConfig(hybrid_alpha=1.0)
        assert config.hybrid_alpha == 1.0


class TestRerankingConfig:
    """Tests for RerankingConfig schema validation (AC-7.12.3)."""

    def test_default_values(self) -> None:
        """Test RerankingConfig with all defaults."""
        config = RerankingConfig()
        assert config.enabled is False
        assert config.model is None
        assert config.top_n == 10

    def test_top_n_min_boundary(self) -> None:
        """Test top_n minimum value (1)."""
        config = RerankingConfig(top_n=1)
        assert config.top_n == 1

    def test_top_n_max_boundary(self) -> None:
        """Test top_n maximum value (50)."""
        config = RerankingConfig(top_n=50)
        assert config.top_n == 50

    def test_top_n_below_min_fails(self) -> None:
        """Test top_n below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RerankingConfig(top_n=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_top_n_above_max_fails(self) -> None:
        """Test top_n above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RerankingConfig(top_n=51)
        assert "less than or equal to 50" in str(exc_info.value)

    def test_model_optional(self) -> None:
        """Test model accepts optional string."""
        config = RerankingConfig(model="cross-encoder/ms-marco-MiniLM-L-6-v2")
        assert config.model == "cross-encoder/ms-marco-MiniLM-L-6-v2"


class TestGenerationConfig:
    """Tests for GenerationConfig schema validation (AC-7.12.4)."""

    def test_default_values(self) -> None:
        """Test GenerationConfig with all defaults."""
        config = GenerationConfig()
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.top_k == 40
        assert config.max_tokens == 2048
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0
        assert config.stop_sequences == []

    def test_temperature_min_boundary(self) -> None:
        """Test temperature minimum value (0.0)."""
        config = GenerationConfig(temperature=0.0)
        assert config.temperature == 0.0

    def test_temperature_max_boundary(self) -> None:
        """Test temperature maximum value (2.0)."""
        config = GenerationConfig(temperature=2.0)
        assert config.temperature == 2.0

    def test_temperature_below_min_fails(self) -> None:
        """Test temperature below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(temperature=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_temperature_above_max_fails(self) -> None:
        """Test temperature above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(temperature=2.1)
        assert "less than or equal to 2" in str(exc_info.value)

    def test_top_p_min_boundary(self) -> None:
        """Test top_p minimum value (0.0)."""
        config = GenerationConfig(top_p=0.0)
        assert config.top_p == 0.0

    def test_top_p_max_boundary(self) -> None:
        """Test top_p maximum value (1.0)."""
        config = GenerationConfig(top_p=1.0)
        assert config.top_p == 1.0

    def test_top_k_min_boundary(self) -> None:
        """Test top_k minimum value (1)."""
        config = GenerationConfig(top_k=1)
        assert config.top_k == 1

    def test_top_k_max_boundary(self) -> None:
        """Test top_k maximum value (100)."""
        config = GenerationConfig(top_k=100)
        assert config.top_k == 100

    def test_max_tokens_min_boundary(self) -> None:
        """Test max_tokens minimum value (100)."""
        config = GenerationConfig(max_tokens=100)
        assert config.max_tokens == 100

    def test_max_tokens_max_boundary(self) -> None:
        """Test max_tokens maximum value (16000)."""
        config = GenerationConfig(max_tokens=16000)
        assert config.max_tokens == 16000

    def test_max_tokens_below_min_fails(self) -> None:
        """Test max_tokens below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(max_tokens=99)
        assert "greater than or equal to 100" in str(exc_info.value)

    def test_max_tokens_above_max_fails(self) -> None:
        """Test max_tokens above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(max_tokens=16001)
        assert "less than or equal to 16000" in str(exc_info.value)

    def test_frequency_penalty_min_boundary(self) -> None:
        """Test frequency_penalty minimum value (-2.0)."""
        config = GenerationConfig(frequency_penalty=-2.0)
        assert config.frequency_penalty == -2.0

    def test_frequency_penalty_max_boundary(self) -> None:
        """Test frequency_penalty maximum value (2.0)."""
        config = GenerationConfig(frequency_penalty=2.0)
        assert config.frequency_penalty == 2.0

    def test_frequency_penalty_below_min_fails(self) -> None:
        """Test frequency_penalty below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(frequency_penalty=-2.1)
        assert "greater than or equal to -2" in str(exc_info.value)

    def test_frequency_penalty_above_max_fails(self) -> None:
        """Test frequency_penalty above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(frequency_penalty=2.1)
        assert "less than or equal to 2" in str(exc_info.value)

    def test_presence_penalty_min_boundary(self) -> None:
        """Test presence_penalty minimum value (-2.0)."""
        config = GenerationConfig(presence_penalty=-2.0)
        assert config.presence_penalty == -2.0

    def test_presence_penalty_max_boundary(self) -> None:
        """Test presence_penalty maximum value (2.0)."""
        config = GenerationConfig(presence_penalty=2.0)
        assert config.presence_penalty == 2.0

    def test_stop_sequences_list(self) -> None:
        """Test stop_sequences accepts list of strings."""
        config = GenerationConfig(stop_sequences=["###", "END"])
        assert config.stop_sequences == ["###", "END"]


class TestNERConfig:
    """Tests for NERConfig schema validation (AC-7.12.5)."""

    def test_default_values(self) -> None:
        """Test NERConfig with all defaults."""
        config = NERConfig()
        assert config.enabled is False
        assert config.confidence_threshold == 0.8
        assert config.entity_types == []
        assert config.batch_size == 32

    def test_confidence_threshold_min_boundary(self) -> None:
        """Test confidence_threshold minimum value (0.0)."""
        config = NERConfig(confidence_threshold=0.0)
        assert config.confidence_threshold == 0.0

    def test_confidence_threshold_max_boundary(self) -> None:
        """Test confidence_threshold maximum value (1.0)."""
        config = NERConfig(confidence_threshold=1.0)
        assert config.confidence_threshold == 1.0

    def test_confidence_threshold_below_min_fails(self) -> None:
        """Test confidence_threshold below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NERConfig(confidence_threshold=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_batch_size_min_boundary(self) -> None:
        """Test batch_size minimum value (1)."""
        config = NERConfig(batch_size=1)
        assert config.batch_size == 1

    def test_batch_size_max_boundary(self) -> None:
        """Test batch_size maximum value (100)."""
        config = NERConfig(batch_size=100)
        assert config.batch_size == 100

    def test_entity_types_list(self) -> None:
        """Test entity_types accepts list of strings."""
        config = NERConfig(entity_types=["PERSON", "ORG", "LOC"])
        assert config.entity_types == ["PERSON", "ORG", "LOC"]


class TestDocumentProcessingConfig:
    """Tests for DocumentProcessingConfig schema validation (AC-7.12.6)."""

    def test_default_values(self) -> None:
        """Test DocumentProcessingConfig with all defaults."""
        config = DocumentProcessingConfig()
        assert config.ocr_enabled is False
        assert config.language_detection is True
        assert config.table_extraction is True
        assert config.image_extraction is False

    def test_all_booleans(self) -> None:
        """Test all boolean fields."""
        config = DocumentProcessingConfig(
            ocr_enabled=True,
            language_detection=False,
            table_extraction=False,
            image_extraction=True,
        )
        assert config.ocr_enabled is True
        assert config.language_detection is False
        assert config.table_extraction is False
        assert config.image_extraction is True


class TestKBPromptConfig:
    """Tests for KBPromptConfig schema validation (AC-7.12.7)."""

    def test_default_values(self) -> None:
        """Test KBPromptConfig with all defaults."""
        config = KBPromptConfig()
        assert config.system_prompt == ""
        assert config.context_template == ""
        assert config.citation_style == CitationStyle.INLINE
        assert config.uncertainty_handling == UncertaintyHandling.ACKNOWLEDGE
        assert config.response_language == "en"

    def test_system_prompt_max_length(self) -> None:
        """Test system_prompt maximum length (4000 chars)."""
        config = KBPromptConfig(system_prompt="a" * 4000)
        assert len(config.system_prompt) == 4000

    def test_system_prompt_above_max_fails(self) -> None:
        """Test system_prompt above max length raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KBPromptConfig(system_prompt="a" * 4001)
        assert "String should have at most 4000 characters" in str(exc_info.value)

    def test_context_template(self) -> None:
        """Test context_template accepts string."""
        template = "Context:\n{context}\n\nQuestion: {question}"
        config = KBPromptConfig(context_template=template)
        assert config.context_template == template


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig schema validation (AC-7.12.8)."""

    def test_default_values(self) -> None:
        """Test EmbeddingConfig with all defaults."""
        config = EmbeddingConfig()
        assert config.model_id is None
        assert config.batch_size == 32
        assert config.normalize is True
        assert config.truncation == TruncationStrategy.END
        assert config.max_length == 512
        assert config.prefix_document == ""
        assert config.prefix_query == ""
        assert config.pooling_strategy == PoolingStrategy.MEAN

    def test_model_id_uuid(self) -> None:
        """Test model_id accepts UUID."""
        model_uuid = uuid.uuid4()
        config = EmbeddingConfig(model_id=model_uuid)
        assert config.model_id == model_uuid

    def test_model_id_none(self) -> None:
        """Test model_id accepts None."""
        config = EmbeddingConfig(model_id=None)
        assert config.model_id is None

    def test_batch_size_min_boundary(self) -> None:
        """Test batch_size minimum value (1)."""
        config = EmbeddingConfig(batch_size=1)
        assert config.batch_size == 1

    def test_batch_size_max_boundary(self) -> None:
        """Test batch_size maximum value (100)."""
        config = EmbeddingConfig(batch_size=100)
        assert config.batch_size == 100

    def test_batch_size_below_min_fails(self) -> None:
        """Test batch_size below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingConfig(batch_size=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_max_length_min_boundary(self) -> None:
        """Test max_length minimum value (128)."""
        config = EmbeddingConfig(max_length=128)
        assert config.max_length == 128

    def test_max_length_max_boundary(self) -> None:
        """Test max_length maximum value (16384)."""
        config = EmbeddingConfig(max_length=16384)
        assert config.max_length == 16384

    def test_max_length_below_min_fails(self) -> None:
        """Test max_length below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingConfig(max_length=127)
        assert "greater than or equal to 128" in str(exc_info.value)

    def test_max_length_above_max_fails(self) -> None:
        """Test max_length above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingConfig(max_length=16385)
        assert "less than or equal to 16384" in str(exc_info.value)

    def test_prefix_document_max_length(self) -> None:
        """Test prefix_document max length (100 chars)."""
        config = EmbeddingConfig(prefix_document="a" * 100)
        assert len(config.prefix_document) == 100

    def test_prefix_document_above_max_fails(self) -> None:
        """Test prefix_document above max raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingConfig(prefix_document="a" * 101)
        assert "String should have at most 100 characters" in str(exc_info.value)

    def test_prefix_query_max_length(self) -> None:
        """Test prefix_query max length (100 chars)."""
        config = EmbeddingConfig(prefix_query="a" * 100)
        assert len(config.prefix_query) == 100

    def test_prefix_query_above_max_fails(self) -> None:
        """Test prefix_query above max raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingConfig(prefix_query="a" * 101)
        assert "String should have at most 100 characters" in str(exc_info.value)


# =============================================================================
# Task 7: Unit Tests - KBSettings Composite (AC: #9-10)
# =============================================================================


class TestKBSettings:
    """Tests for KBSettings composite schema (AC-7.12.9, AC-7.12.10)."""

    def test_default_values(self) -> None:
        """Test KBSettings instantiation with all defaults."""
        settings = KBSettings()
        assert isinstance(settings.chunking, ChunkingConfig)
        assert isinstance(settings.retrieval, RetrievalConfig)
        assert isinstance(settings.reranking, RerankingConfig)
        assert isinstance(settings.generation, GenerationConfig)
        assert isinstance(settings.ner, NERConfig)
        assert isinstance(settings.processing, DocumentProcessingConfig)
        assert isinstance(settings.prompts, KBPromptConfig)
        assert isinstance(settings.embedding, EmbeddingConfig)
        assert settings.preset is None

    def test_partial_overrides(self) -> None:
        """Test KBSettings instantiation with partial overrides."""
        settings = KBSettings(
            chunking=ChunkingConfig(chunk_size=1000),
            retrieval=RetrievalConfig(top_k=20),
        )
        assert settings.chunking.chunk_size == 1000
        assert settings.retrieval.top_k == 20
        # Other configs should have defaults
        assert settings.generation.temperature == 0.7
        assert settings.reranking.enabled is False

    def test_preset_field(self) -> None:
        """Test KBSettings preset field accepts string."""
        settings = KBSettings(preset="legal")
        assert settings.preset == "legal"

    def test_backwards_compatibility_empty_dict(self) -> None:
        """Test backwards compatibility: KBSettings.model_validate({}) succeeds (AC-7.12.10)."""
        settings = KBSettings.model_validate({})
        assert isinstance(settings, KBSettings)
        assert settings.chunking.chunk_size == 512
        assert settings.retrieval.top_k == 10
        assert settings.generation.temperature == 0.7

    def test_json_roundtrip(self) -> None:
        """Test KBSettings JSON round-trip (model_dump → model_validate)."""
        original = KBSettings(
            chunking=ChunkingConfig(chunk_size=1500),
            retrieval=RetrievalConfig(top_k=25, method=RetrievalMethod.HYBRID),
            generation=GenerationConfig(temperature=0.5),
            preset="technical",
        )
        data = original.model_dump()
        restored = KBSettings.model_validate(data)

        assert restored.chunking.chunk_size == 1500
        assert restored.retrieval.top_k == 25
        assert restored.retrieval.method == RetrievalMethod.HYBRID
        assert restored.generation.temperature == 0.5
        assert restored.preset == "technical"

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError) as exc_info:
            KBSettings(unknown_field="value")  # type: ignore
        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_nested_override(self) -> None:
        """Test nested config override in dict format."""
        settings = KBSettings.model_validate(
            {
                "chunking": {"chunk_size": 800},
                "retrieval": {"similarity_threshold": 0.85},
            }
        )
        assert settings.chunking.chunk_size == 800
        assert settings.chunking.strategy == ChunkingStrategy.RECURSIVE  # default
        assert settings.retrieval.similarity_threshold == 0.85
        assert settings.retrieval.top_k == 10  # default

    def test_debug_mode_default_false(self) -> None:
        """Test debug_mode defaults to False (AC-9.15.1)."""
        settings = KBSettings()
        assert settings.debug_mode is False

    def test_debug_mode_can_be_enabled(self) -> None:
        """Test debug_mode can be set to True (AC-9.15.1)."""
        settings = KBSettings(debug_mode=True)
        assert settings.debug_mode is True

    def test_debug_mode_json_serialization(self) -> None:
        """Test debug_mode JSON serialization (AC-9.15.1)."""
        settings = KBSettings(debug_mode=True)
        data = settings.model_dump()
        assert data["debug_mode"] is True

    def test_debug_mode_json_deserialization(self) -> None:
        """Test debug_mode JSON deserialization (AC-9.15.1)."""
        settings = KBSettings.model_validate({"debug_mode": True})
        assert settings.debug_mode is True

    def test_debug_mode_with_other_configs(self) -> None:
        """Test debug_mode works with other configurations (AC-9.15.1)."""
        settings = KBSettings(
            debug_mode=True,
            chunking=ChunkingConfig(chunk_size=1000),
            retrieval=RetrievalConfig(top_k=20),
        )
        assert settings.debug_mode is True
        assert settings.chunking.chunk_size == 1000
        assert settings.retrieval.top_k == 20


# =============================================================================
# Task 8: Unit Tests - Re-indexing Detection (AC: #11)
# =============================================================================


class TestEmbeddingConfigReindexDetection:
    """Tests for EmbeddingConfig re-indexing detection (AC-7.12.11)."""

    def test_requires_reindex_no_previous(self) -> None:
        """Test requires_reindex returns False when no previous config."""
        config = EmbeddingConfig()
        assert config.requires_reindex(None) is False

    def test_requires_reindex_no_changes(self) -> None:
        """Test requires_reindex returns False when no re-index fields changed."""
        previous = EmbeddingConfig()
        current = EmbeddingConfig(batch_size=64)  # batch_size not in REINDEX_FIELDS
        assert current.requires_reindex(previous) is False

    def test_requires_reindex_model_id_changes(self) -> None:
        """Test requires_reindex returns True when model_id changes."""
        previous = EmbeddingConfig()
        current = EmbeddingConfig(model_id=uuid.uuid4())
        assert current.requires_reindex(previous) is True

    def test_requires_reindex_normalize_changes(self) -> None:
        """Test requires_reindex returns True when normalize changes."""
        previous = EmbeddingConfig(normalize=True)
        current = EmbeddingConfig(normalize=False)
        assert current.requires_reindex(previous) is True

    def test_requires_reindex_prefix_document_changes(self) -> None:
        """Test requires_reindex returns True when prefix_document changes."""
        previous = EmbeddingConfig(prefix_document="")
        current = EmbeddingConfig(prefix_document="passage: ")
        assert current.requires_reindex(previous) is True

    def test_requires_reindex_prefix_query_changes(self) -> None:
        """Test requires_reindex returns True when prefix_query changes."""
        previous = EmbeddingConfig(prefix_query="")
        current = EmbeddingConfig(prefix_query="query: ")
        assert current.requires_reindex(previous) is True

    def test_requires_reindex_pooling_strategy_changes(self) -> None:
        """Test requires_reindex returns True when pooling_strategy changes."""
        previous = EmbeddingConfig(pooling_strategy=PoolingStrategy.MEAN)
        current = EmbeddingConfig(pooling_strategy=PoolingStrategy.CLS)
        assert current.requires_reindex(previous) is True

    def test_detect_reindex_fields_no_previous(self) -> None:
        """Test detect_reindex_fields returns empty list when no previous."""
        config = EmbeddingConfig()
        assert config.detect_reindex_fields(None) == []

    def test_detect_reindex_fields_returns_correct_list(self) -> None:
        """Test detect_reindex_fields returns correct field list."""
        previous = EmbeddingConfig(
            normalize=True,
            prefix_document="",
            pooling_strategy=PoolingStrategy.MEAN,
        )
        current = EmbeddingConfig(
            normalize=False,
            prefix_document="passage: ",
            pooling_strategy=PoolingStrategy.CLS,
        )
        changed = current.detect_reindex_fields(previous)
        assert "normalize" in changed
        assert "prefix_document" in changed
        assert "pooling_strategy" in changed
        assert len(changed) == 3

    def test_detect_reindex_fields_single_change(self) -> None:
        """Test detect_reindex_fields with single field change."""
        previous = EmbeddingConfig()
        current = EmbeddingConfig(normalize=False)
        changed = current.detect_reindex_fields(previous)
        assert changed == ["normalize"]

    def test_get_reindex_warning_empty_fields(self) -> None:
        """Test get_reindex_warning returns empty string for no changes."""
        config = EmbeddingConfig()
        assert config.get_reindex_warning([]) == ""

    def test_get_reindex_warning_returns_message(self) -> None:
        """Test get_reindex_warning returns user-friendly message."""
        config = EmbeddingConfig()
        warning = config.get_reindex_warning(["model_id", "normalize"])
        assert "model_id, normalize" in warning
        assert "re-indexing" in warning.lower()
        assert "documents" in warning.lower()

    def test_get_reindex_warning_single_field(self) -> None:
        """Test get_reindex_warning with single field."""
        config = EmbeddingConfig()
        warning = config.get_reindex_warning(["pooling_strategy"])
        assert "pooling_strategy" in warning
        assert "re-indexing" in warning.lower()


class TestReindexFieldsClassVar:
    """Tests for REINDEX_FIELDS class variable."""

    def test_reindex_fields_contains_expected(self) -> None:
        """Test REINDEX_FIELDS contains all expected fields."""
        expected = {
            "model_id",
            "normalize",
            "prefix_document",
            "prefix_query",
            "pooling_strategy",
        }
        assert expected == EmbeddingConfig.REINDEX_FIELDS

    def test_reindex_fields_is_class_variable(self) -> None:
        """Test REINDEX_FIELDS is a class variable, not instance."""
        config1 = EmbeddingConfig()
        config2 = EmbeddingConfig()
        assert config1.REINDEX_FIELDS is config2.REINDEX_FIELDS
        assert config1.REINDEX_FIELDS is EmbeddingConfig.REINDEX_FIELDS


# =============================================================================
# Additional Coverage Tests - Edge Cases and Validation Failures
# =============================================================================


class TestEnumInvalidValues:
    """Tests for invalid enum values raising ValidationError."""

    def test_chunking_strategy_invalid_value(self) -> None:
        """[P1] Test invalid ChunkingStrategy value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ChunkingConfig(strategy="invalid_strategy")  # type: ignore
        assert "Input should be" in str(exc_info.value)

    def test_retrieval_method_invalid_value(self) -> None:
        """[P1] Test invalid RetrievalMethod value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalConfig(method="invalid_method")  # type: ignore
        assert "Input should be" in str(exc_info.value)

    def test_citation_style_invalid_value(self) -> None:
        """[P1] Test invalid CitationStyle value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KBPromptConfig(citation_style="invalid")  # type: ignore
        assert "Input should be" in str(exc_info.value)

    def test_uncertainty_handling_invalid_value(self) -> None:
        """[P1] Test invalid UncertaintyHandling value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KBPromptConfig(uncertainty_handling="invalid")  # type: ignore
        assert "Input should be" in str(exc_info.value)

    def test_truncation_strategy_invalid_value(self) -> None:
        """[P1] Test invalid TruncationStrategy value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingConfig(truncation="invalid")  # type: ignore
        assert "Input should be" in str(exc_info.value)

    def test_pooling_strategy_invalid_value(self) -> None:
        """[P1] Test invalid PoolingStrategy value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingConfig(pooling_strategy="invalid")  # type: ignore
        assert "Input should be" in str(exc_info.value)


class TestGenerationConfigAdditionalValidation:
    """Additional validation tests for GenerationConfig edge cases."""

    def test_top_p_below_min_fails(self) -> None:
        """[P1] Test top_p below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(top_p=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_top_p_above_max_fails(self) -> None:
        """[P1] Test top_p above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(top_p=1.1)
        assert "less than or equal to 1" in str(exc_info.value)

    def test_top_k_below_min_fails(self) -> None:
        """[P1] Test top_k below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(top_k=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_top_k_above_max_fails(self) -> None:
        """[P1] Test top_k above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(top_k=101)
        assert "less than or equal to 100" in str(exc_info.value)

    def test_presence_penalty_below_min_fails(self) -> None:
        """[P1] Test presence_penalty below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(presence_penalty=-2.1)
        assert "greater than or equal to -2" in str(exc_info.value)

    def test_presence_penalty_above_max_fails(self) -> None:
        """[P1] Test presence_penalty above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationConfig(presence_penalty=2.1)
        assert "less than or equal to 2" in str(exc_info.value)


class TestRetrievalConfigAdditionalValidation:
    """Additional validation tests for RetrievalConfig edge cases."""

    def test_mmr_lambda_above_max_fails(self) -> None:
        """[P1] Test mmr_lambda above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalConfig(mmr_lambda=1.1)
        assert "less than or equal to 1" in str(exc_info.value)

    def test_hybrid_alpha_below_min_fails(self) -> None:
        """[P1] Test hybrid_alpha below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalConfig(hybrid_alpha=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_hybrid_alpha_above_max_fails(self) -> None:
        """[P1] Test hybrid_alpha above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RetrievalConfig(hybrid_alpha=1.1)
        assert "less than or equal to 1" in str(exc_info.value)


class TestNERConfigAdditionalValidation:
    """Additional validation tests for NERConfig edge cases."""

    def test_confidence_threshold_above_max_fails(self) -> None:
        """[P1] Test confidence_threshold above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NERConfig(confidence_threshold=1.1)
        assert "less than or equal to 1" in str(exc_info.value)

    def test_batch_size_below_min_fails(self) -> None:
        """[P1] Test batch_size below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NERConfig(batch_size=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_batch_size_above_max_fails(self) -> None:
        """[P1] Test batch_size above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NERConfig(batch_size=101)
        assert "less than or equal to 100" in str(exc_info.value)


class TestEmbeddingConfigAdditionalValidation:
    """Additional validation tests for EmbeddingConfig edge cases."""

    def test_batch_size_above_max_fails(self) -> None:
        """[P1] Test batch_size above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingConfig(batch_size=101)
        assert "less than or equal to 100" in str(exc_info.value)

    def test_model_id_invalid_uuid_fails(self) -> None:
        """[P1] Test model_id with invalid UUID string raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EmbeddingConfig(model_id="not-a-uuid")  # type: ignore
        assert "Input should be a valid UUID" in str(exc_info.value)

    def test_model_id_uuid_string_accepted(self) -> None:
        """[P1] Test model_id accepts valid UUID string."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        config = EmbeddingConfig(model_id=valid_uuid)  # type: ignore
        assert str(config.model_id) == valid_uuid


class TestKBSettingsEdgeCases:
    """Edge case tests for KBSettings composite schema."""

    def test_deeply_nested_invalid_value(self) -> None:
        """[P1] Test deeply nested invalid value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KBSettings.model_validate(
                {
                    "chunking": {"chunk_size": 50}  # Below minimum
                }
            )
        assert "greater than or equal to 100" in str(exc_info.value)

    def test_multiple_nested_configs(self) -> None:
        """[P1] Test multiple nested configs with custom values."""
        settings = KBSettings.model_validate(
            {
                "chunking": {"chunk_size": 1000, "strategy": "semantic"},
                "retrieval": {"top_k": 50, "method": "hybrid"},
                "generation": {"temperature": 0.5, "max_tokens": 4000},
                "embedding": {"normalize": False, "pooling_strategy": "cls"},
                "preset": "custom",
            }
        )
        assert settings.chunking.chunk_size == 1000
        assert settings.chunking.strategy == ChunkingStrategy.SEMANTIC
        assert settings.retrieval.top_k == 50
        assert settings.retrieval.method == RetrievalMethod.HYBRID
        assert settings.generation.temperature == 0.5
        assert settings.generation.max_tokens == 4000
        assert settings.embedding.normalize is False
        assert settings.embedding.pooling_strategy == PoolingStrategy.CLS
        assert settings.preset == "custom"

    def test_json_mode_serialization(self) -> None:
        """[P1] Test JSON serialization mode produces correct output."""
        settings = KBSettings(
            chunking=ChunkingConfig(strategy=ChunkingStrategy.SEMANTIC),
            retrieval=RetrievalConfig(method=RetrievalMethod.HYDE),
        )
        json_data = settings.model_dump(mode="json")
        assert json_data["chunking"]["strategy"] == "semantic"
        assert json_data["retrieval"]["method"] == "hyde"

    def test_empty_settings_all_defaults_sensible(self) -> None:
        """[P2] Test empty settings produce sensible production defaults."""
        settings = KBSettings.model_validate({})
        # Verify sensible defaults for production
        assert settings.chunking.chunk_size == 512  # Good default for most docs
        assert settings.chunking.strategy == ChunkingStrategy.RECURSIVE
        assert settings.retrieval.top_k == 10  # Reasonable default
        assert settings.retrieval.similarity_threshold == 0.7
        assert settings.generation.temperature == 0.7  # Balanced creativity
        assert settings.generation.max_tokens == 2048
        assert settings.embedding.normalize is True  # Important for similarity
        assert settings.processing.language_detection is True  # Good default


class TestReindexDetectionEdgeCases:
    """Edge case tests for re-indexing detection logic."""

    def test_multiple_reindex_fields_changed(self) -> None:
        """[P1] Test detection when multiple re-index fields changed."""
        previous = EmbeddingConfig(
            model_id=uuid.uuid4(),
            normalize=True,
            prefix_document="doc: ",
            prefix_query="query: ",
            pooling_strategy=PoolingStrategy.MEAN,
        )
        current = EmbeddingConfig(
            model_id=uuid.uuid4(),  # Different UUID
            normalize=False,
            prefix_document="passage: ",
            prefix_query="search: ",
            pooling_strategy=PoolingStrategy.CLS,
        )
        assert current.requires_reindex(previous) is True
        changed = current.detect_reindex_fields(previous)
        assert len(changed) == 5  # All re-index fields changed

    def test_non_reindex_fields_dont_trigger(self) -> None:
        """[P1] Test non-reindex fields don't trigger re-indexing."""
        previous = EmbeddingConfig(
            batch_size=32, truncation=TruncationStrategy.END, max_length=512
        )
        current = EmbeddingConfig(
            batch_size=64,  # Changed but not in REINDEX_FIELDS
            truncation=TruncationStrategy.START,  # Changed but not in REINDEX_FIELDS
            max_length=1024,  # Changed but not in REINDEX_FIELDS
        )
        assert current.requires_reindex(previous) is False
        assert current.detect_reindex_fields(previous) == []

    def test_reindex_warning_formatting(self) -> None:
        """[P1] Test re-index warning message formatting."""
        config = EmbeddingConfig()
        warning = config.get_reindex_warning(
            ["model_id", "normalize", "pooling_strategy"]
        )
        assert "model_id" in warning
        assert "normalize" in warning
        assert "pooling_strategy" in warning
        assert "re-indexing" in warning.lower()
        assert "documents" in warning.lower()
        assert "knowledge base" in warning.lower()
