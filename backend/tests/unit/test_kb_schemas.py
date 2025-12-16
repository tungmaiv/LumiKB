"""Unit tests for Knowledge Base Pydantic schemas."""

import uuid
from datetime import UTC

import pytest
from pydantic import ValidationError

from app.models.permission import PermissionLevel
from app.schemas.knowledge_base import (
    EmbeddingModelInfo,
    GenerationModelInfo,
    KBCreate,
    KBResponse,
    KBUpdate,
)

pytestmark = pytest.mark.unit


class TestKBCreate:
    """Tests for KBCreate schema validation."""

    def test_valid_name_only(self) -> None:
        """Test creating KB with only required name field."""
        schema = KBCreate(name="Test KB")
        assert schema.name == "Test KB"
        assert schema.description is None

    def test_valid_name_and_description(self) -> None:
        """Test creating KB with name and description."""
        schema = KBCreate(name="Test KB", description="A test knowledge base")
        assert schema.name == "Test KB"
        assert schema.description == "A test knowledge base"

    def test_name_min_length(self) -> None:
        """Test that name must be at least 1 character."""
        # Empty string should fail
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_name_max_length(self) -> None:
        """Test that name cannot exceed 255 characters."""
        # 256 characters should fail
        long_name = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name=long_name)
        assert "String should have at most 255 characters" in str(exc_info.value)

    def test_name_exactly_255_chars(self) -> None:
        """Test that name can be exactly 255 characters."""
        name_255 = "a" * 255
        schema = KBCreate(name=name_255)
        assert len(schema.name) == 255

    def test_description_max_length(self) -> None:
        """Test that description cannot exceed 2000 characters."""
        # 2001 characters should fail
        long_desc = "a" * 2001
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name="Test", description=long_desc)
        assert "String should have at most 2000 characters" in str(exc_info.value)

    def test_description_exactly_2000_chars(self) -> None:
        """Test that description can be exactly 2000 characters."""
        desc_2000 = "a" * 2000
        schema = KBCreate(name="Test", description=desc_2000)
        assert len(schema.description) == 2000

    def test_name_required(self) -> None:
        """Test that name is a required field."""
        with pytest.raises(ValidationError) as exc_info:
            KBCreate()  # type: ignore
        assert "Field required" in str(exc_info.value)


class TestKBUpdate:
    """Tests for KBUpdate schema validation."""

    def test_all_fields_optional(self) -> None:
        """Test that all fields are optional for updates."""
        schema = KBUpdate()
        assert schema.name is None
        assert schema.description is None

    def test_update_name_only(self) -> None:
        """Test updating only name."""
        schema = KBUpdate(name="New Name")
        assert schema.name == "New Name"
        assert schema.description is None

    def test_update_description_only(self) -> None:
        """Test updating only description."""
        schema = KBUpdate(description="New description")
        assert schema.name is None
        assert schema.description == "New description"

    def test_update_both_fields(self) -> None:
        """Test updating both name and description."""
        schema = KBUpdate(name="New Name", description="New description")
        assert schema.name == "New Name"
        assert schema.description == "New description"

    def test_name_min_length_if_provided(self) -> None:
        """Test that name must be at least 1 char if provided."""
        with pytest.raises(ValidationError) as exc_info:
            KBUpdate(name="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_name_max_length_if_provided(self) -> None:
        """Test that name cannot exceed 255 chars if provided."""
        with pytest.raises(ValidationError) as exc_info:
            KBUpdate(name="a" * 256)
        assert "String should have at most 255 characters" in str(exc_info.value)

    def test_description_max_length_if_provided(self) -> None:
        """Test that description cannot exceed 2000 chars if provided."""
        with pytest.raises(ValidationError) as exc_info:
            KBUpdate(description="a" * 2001)
        assert "String should have at most 2000 characters" in str(exc_info.value)


class TestPermissionHierarchy:
    """Tests for permission level hierarchy logic."""

    def test_permission_level_enum_values(self) -> None:
        """Test that PermissionLevel enum has correct values."""
        assert PermissionLevel.READ.value == "READ"
        assert PermissionLevel.WRITE.value == "WRITE"
        assert PermissionLevel.ADMIN.value == "ADMIN"

    def test_permission_level_from_string(self) -> None:
        """Test creating PermissionLevel from string."""
        assert PermissionLevel("READ") == PermissionLevel.READ
        assert PermissionLevel("WRITE") == PermissionLevel.WRITE
        assert PermissionLevel("ADMIN") == PermissionLevel.ADMIN

    def test_permission_level_ordering(self) -> None:
        """Test that permission hierarchy is correct conceptually.

        ADMIN > WRITE > READ
        This is tested via the PERMISSION_HIERARCHY dict in kb_service.
        """
        from app.services.kb_service import PERMISSION_HIERARCHY

        assert (
            PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
            > PERMISSION_HIERARCHY[PermissionLevel.WRITE]
        )
        assert (
            PERMISSION_HIERARCHY[PermissionLevel.WRITE]
            > PERMISSION_HIERARCHY[PermissionLevel.READ]
        )
        assert (
            PERMISSION_HIERARCHY[PermissionLevel.ADMIN]
            > PERMISSION_HIERARCHY[PermissionLevel.READ]
        )


class TestKBCreateModelConfiguration:
    """Tests for model configuration fields in KBCreate schema (Story 7-10)."""

    def test_valid_model_ids(self) -> None:
        """Test creating KB with valid model UUIDs."""
        embedding_id = uuid.uuid4()
        generation_id = uuid.uuid4()
        schema = KBCreate(
            name="Test KB",
            embedding_model_id=embedding_id,
            generation_model_id=generation_id,
        )
        assert schema.embedding_model_id == embedding_id
        assert schema.generation_model_id == generation_id

    def test_model_ids_optional(self) -> None:
        """Test that model IDs are optional."""
        schema = KBCreate(name="Test KB")
        assert schema.embedding_model_id is None
        assert schema.generation_model_id is None

    def test_rag_parameters_valid_ranges(self) -> None:
        """Test RAG parameters with valid values."""
        schema = KBCreate(
            name="Test KB",
            similarity_threshold=0.8,
            search_top_k=20,
            temperature=0.7,
            rerank_enabled=True,
        )
        assert schema.similarity_threshold == 0.8
        assert schema.search_top_k == 20
        assert schema.temperature == 0.7
        assert schema.rerank_enabled is True

    def test_similarity_threshold_min_boundary(self) -> None:
        """Test similarity_threshold minimum value (0.0)."""
        schema = KBCreate(name="Test KB", similarity_threshold=0.0)
        assert schema.similarity_threshold == 0.0

    def test_similarity_threshold_max_boundary(self) -> None:
        """Test similarity_threshold maximum value (1.0)."""
        schema = KBCreate(name="Test KB", similarity_threshold=1.0)
        assert schema.similarity_threshold == 1.0

    def test_similarity_threshold_below_min(self) -> None:
        """Test similarity_threshold below minimum fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name="Test KB", similarity_threshold=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_similarity_threshold_above_max(self) -> None:
        """Test similarity_threshold above maximum fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name="Test KB", similarity_threshold=1.1)
        assert "less than or equal to 1" in str(exc_info.value)

    def test_search_top_k_min_boundary(self) -> None:
        """Test search_top_k minimum value (1)."""
        schema = KBCreate(name="Test KB", search_top_k=1)
        assert schema.search_top_k == 1

    def test_search_top_k_max_boundary(self) -> None:
        """Test search_top_k maximum value (100)."""
        schema = KBCreate(name="Test KB", search_top_k=100)
        assert schema.search_top_k == 100

    def test_search_top_k_below_min(self) -> None:
        """Test search_top_k below minimum fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name="Test KB", search_top_k=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_search_top_k_above_max(self) -> None:
        """Test search_top_k above maximum fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name="Test KB", search_top_k=101)
        assert "less than or equal to 100" in str(exc_info.value)

    def test_temperature_min_boundary(self) -> None:
        """Test temperature minimum value (0.0)."""
        schema = KBCreate(name="Test KB", temperature=0.0)
        assert schema.temperature == 0.0

    def test_temperature_max_boundary(self) -> None:
        """Test temperature maximum value (2.0)."""
        schema = KBCreate(name="Test KB", temperature=2.0)
        assert schema.temperature == 2.0

    def test_temperature_below_min(self) -> None:
        """Test temperature below minimum fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name="Test KB", temperature=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_temperature_above_max(self) -> None:
        """Test temperature above maximum fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            KBCreate(name="Test KB", temperature=2.1)
        assert "less than or equal to 2" in str(exc_info.value)


class TestKBUpdateModelConfiguration:
    """Tests for model configuration fields in KBUpdate schema (Story 7-10)."""

    def test_update_model_ids(self) -> None:
        """Test updating model IDs."""
        embedding_id = uuid.uuid4()
        generation_id = uuid.uuid4()
        schema = KBUpdate(
            embedding_model_id=embedding_id,
            generation_model_id=generation_id,
        )
        assert schema.embedding_model_id == embedding_id
        assert schema.generation_model_id == generation_id

    def test_update_only_generation_model(self) -> None:
        """Test updating only generation model (allowed anytime)."""
        generation_id = uuid.uuid4()
        schema = KBUpdate(generation_model_id=generation_id)
        assert schema.embedding_model_id is None
        assert schema.generation_model_id == generation_id

    def test_update_rag_parameters(self) -> None:
        """Test updating RAG parameters."""
        schema = KBUpdate(
            similarity_threshold=0.9,
            search_top_k=50,
            temperature=1.0,
            rerank_enabled=False,
        )
        assert schema.similarity_threshold == 0.9
        assert schema.search_top_k == 50
        assert schema.temperature == 1.0
        assert schema.rerank_enabled is False

    def test_update_rag_parameters_validation(self) -> None:
        """Test RAG parameters validation in update."""
        with pytest.raises(ValidationError):
            KBUpdate(similarity_threshold=1.5)  # Above max

        with pytest.raises(ValidationError):
            KBUpdate(search_top_k=0)  # Below min

        with pytest.raises(ValidationError):
            KBUpdate(temperature=3.0)  # Above max


class TestEmbeddingModelInfo:
    """Tests for EmbeddingModelInfo schema (Story 7-10)."""

    def test_valid_embedding_model_info(self) -> None:
        """Test creating valid EmbeddingModelInfo."""
        model_id = uuid.uuid4()
        info = EmbeddingModelInfo(
            id=model_id,
            name="text-embedding-3-small",
            model_id="openai/text-embedding-3-small",
            dimensions=1536,
            distance_metric="cosine",
        )
        assert info.id == model_id
        assert info.name == "text-embedding-3-small"
        assert info.model_id == "openai/text-embedding-3-small"
        assert info.dimensions == 1536
        assert info.distance_metric == "cosine"

    def test_optional_fields(self) -> None:
        """Test that dimensions and distance_metric are optional."""
        model_id = uuid.uuid4()
        info = EmbeddingModelInfo(
            id=model_id,
            name="test-model",
            model_id="provider/test-model",
        )
        assert info.dimensions is None
        assert info.distance_metric is None


class TestGenerationModelInfo:
    """Tests for GenerationModelInfo schema (Story 7-10)."""

    def test_valid_generation_model_info(self) -> None:
        """Test creating valid GenerationModelInfo."""
        model_id = uuid.uuid4()
        info = GenerationModelInfo(
            id=model_id,
            name="GPT-4o",
            model_id="openai/gpt-4o",
            context_window=128000,
            max_tokens=4096,
        )
        assert info.id == model_id
        assert info.name == "GPT-4o"
        assert info.model_id == "openai/gpt-4o"
        assert info.context_window == 128000
        assert info.max_tokens == 4096

    def test_optional_fields(self) -> None:
        """Test that context_window and max_tokens are optional."""
        model_id = uuid.uuid4()
        info = GenerationModelInfo(
            id=model_id,
            name="test-model",
            model_id="provider/test-model",
        )
        assert info.context_window is None
        assert info.max_tokens is None


class TestKBResponseModelConfiguration:
    """Tests for model configuration fields in KBResponse schema (Story 7-10)."""

    def test_kb_response_with_models(self) -> None:
        """Test KBResponse with embedded model info."""
        from datetime import datetime

        kb_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        embedding_model_id = uuid.uuid4()
        generation_model_id = uuid.uuid4()

        response = KBResponse(
            id=kb_id,
            name="Test KB",
            description="Test description",
            owner_id=owner_id,
            status="active",
            document_count=10,
            total_size_bytes=1024000,
            permission_level=PermissionLevel.ADMIN,
            tags=["test", "demo"],
            embedding_model=EmbeddingModelInfo(
                id=embedding_model_id,
                name="text-embedding-3-small",
                model_id="openai/text-embedding-3-small",
                dimensions=1536,
                distance_metric="cosine",
            ),
            generation_model=GenerationModelInfo(
                id=generation_model_id,
                name="GPT-4o",
                model_id="openai/gpt-4o",
                context_window=128000,
                max_tokens=4096,
            ),
            qdrant_collection_name=f"kb_{kb_id}",
            qdrant_vector_size=1536,
            similarity_threshold=0.7,
            search_top_k=10,
            temperature=0.7,
            rerank_enabled=False,
            embedding_model_locked=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert response.embedding_model is not None
        assert response.embedding_model.dimensions == 1536
        assert response.generation_model is not None
        assert response.generation_model.context_window == 128000
        assert response.qdrant_collection_name == f"kb_{kb_id}"
        assert response.embedding_model_locked is True

    def test_kb_response_without_models(self) -> None:
        """Test KBResponse without model info (legacy KBs)."""
        from datetime import datetime

        kb_id = uuid.uuid4()
        owner_id = uuid.uuid4()

        response = KBResponse(
            id=kb_id,
            name="Legacy KB",
            owner_id=owner_id,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert response.embedding_model is None
        assert response.generation_model is None
        assert response.qdrant_collection_name is None
        assert response.qdrant_vector_size is None
        assert response.embedding_model_locked is False
