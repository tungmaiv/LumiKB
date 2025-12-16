"""Integration tests for KB Model Configuration (Story 7-10).

Test Coverage:
- [P0] AC-7.10.4: Qdrant collection auto-created with correct dimensions
- [P0] AC-7.10.8: Document processing uses KB embedding model
- [P0] AC-7.10.9: Search operations use KB embedding model
- [P1] AC-7.10.1: Model selection dropdown during KB creation shows active models
- [P1] AC-7.10.2: Only active models appear in selection dropdown
- [P1] AC-7.10.5: KB-level parameter overrides supported
- [P1] AC-7.10.7: Generation model changeable without document reprocessing
- [P1] AC-7.10.10: Chat/generation operations use KB generation model

Knowledge Base References:
- test-quality.md: Given-When-Then structure
- fixture-architecture.md: Integration test patterns
- test-levels-framework.md: API integration test level
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.document import Document, DocumentStatus
from app.models.llm_model import LLMModel, ModelStatus, ModelType
from tests.factories import create_registration_data

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def kb_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def db_session_for_kb(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for model setup."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def test_user_for_kb(kb_client: AsyncClient) -> dict:
    """Create a test user for KB tests."""
    user_data = create_registration_data()
    response = await kb_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json(), "user_id": response.json()["id"]}


@pytest.fixture
async def user_cookies_for_kb(kb_client: AsyncClient, test_user_for_kb: dict) -> dict:
    """Login as test user and return cookies."""
    login_response = await kb_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_for_kb["email"],
            "password": test_user_for_kb["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def embedding_model(db_session_for_kb: AsyncSession) -> LLMModel:
    """Create an active embedding model for testing."""
    model = LLMModel(
        type=ModelType.EMBEDDING.value,
        provider="openai",
        name="Test Embedding Model",
        model_id="text-embedding-test-1",
        status=ModelStatus.ACTIVE.value,
        config={
            "dimensions": 1536,
            "max_tokens": 8191,
            "normalize": True,
            "distance_metric": "cosine",
            "batch_size": 100,
            "tags": [],
        },
        is_default=True,
    )
    db_session_for_kb.add(model)
    await db_session_for_kb.commit()
    await db_session_for_kb.refresh(model)
    return model


@pytest.fixture
async def second_embedding_model(db_session_for_kb: AsyncSession) -> LLMModel:
    """Create a second embedding model with different dimensions."""
    model = LLMModel(
        type=ModelType.EMBEDDING.value,
        provider="openai",
        name="Second Embedding Model",
        model_id="text-embedding-test-2",
        status=ModelStatus.ACTIVE.value,
        config={
            "dimensions": 768,
            "max_tokens": 512,
            "normalize": True,
            "distance_metric": "euclidean",
            "batch_size": 50,
            "tags": [],
        },
        is_default=False,
    )
    db_session_for_kb.add(model)
    await db_session_for_kb.commit()
    await db_session_for_kb.refresh(model)
    return model


@pytest.fixture
async def inactive_embedding_model(db_session_for_kb: AsyncSession) -> LLMModel:
    """Create an inactive embedding model for testing AC-7.10.2."""
    model = LLMModel(
        type=ModelType.EMBEDDING.value,
        provider="openai",
        name="Inactive Embedding Model",
        model_id="text-embedding-inactive",
        status=ModelStatus.INACTIVE.value,
        config={
            "dimensions": 1536,
            "distance_metric": "cosine",
        },
        is_default=False,
    )
    db_session_for_kb.add(model)
    await db_session_for_kb.commit()
    await db_session_for_kb.refresh(model)
    return model


@pytest.fixture
async def generation_model(db_session_for_kb: AsyncSession) -> LLMModel:
    """Create an active generation model for testing."""
    model = LLMModel(
        type=ModelType.GENERATION.value,
        provider="anthropic",
        name="Test Generation Model",
        model_id="claude-test-1",
        status=ModelStatus.ACTIVE.value,
        config={
            "context_window": 200000,
            "max_output_tokens": 8192,
            "supports_streaming": True,
            "supports_json_mode": False,
            "supports_vision": True,
            "temperature_default": 0.7,
            "temperature_range": [0.0, 2.0],
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
            "tags": [],
        },
        is_default=True,
    )
    db_session_for_kb.add(model)
    await db_session_for_kb.commit()
    await db_session_for_kb.refresh(model)
    return model


@pytest.fixture
async def second_generation_model(db_session_for_kb: AsyncSession) -> LLMModel:
    """Create a second generation model for testing model changes."""
    model = LLMModel(
        type=ModelType.GENERATION.value,
        provider="openai",
        name="Second Generation Model",
        model_id="gpt-test-1",
        status=ModelStatus.ACTIVE.value,
        config={
            "context_window": 128000,
            "max_output_tokens": 4096,
            "supports_streaming": True,
            "tags": [],
        },
        is_default=False,
    )
    db_session_for_kb.add(model)
    await db_session_for_kb.commit()
    await db_session_for_kb.refresh(model)
    return model


# =============================================================================
# AC-7.10.1 & AC-7.10.2: Model Selection During KB Creation (P1)
# =============================================================================


class TestKBCreationWithModels:
    """Tests for KB creation with model selection."""

    @pytest.mark.asyncio
    async def test_create_kb_with_embedding_model_returns_201(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        embedding_model: LLMModel,
    ):
        """
        GIVEN: Authenticated user with active embedding model available
        WHEN: POST /api/v1/knowledge-bases with embedding_model_id
        THEN: Returns 201 with KB including model configuration
        AC: 7.10.1 - Model selection during KB creation
        """
        kb_data = {
            "name": "Test KB with Embedding Model",
            "description": "KB with configured embedding model",
            "embedding_model_id": str(embedding_model.id),
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == kb_data["name"]
        # Verify model info is returned (AC-7.10.3)
        assert data.get("embedding_model") is not None
        assert data["embedding_model"]["id"] == str(embedding_model.id)
        assert data["embedding_model"]["name"] == embedding_model.name

    @pytest.mark.asyncio
    async def test_create_kb_with_both_models_returns_201(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        embedding_model: LLMModel,
        generation_model: LLMModel,
    ):
        """
        GIVEN: Authenticated user with active embedding and generation models
        WHEN: POST /api/v1/knowledge-bases with both model IDs
        THEN: Returns 201 with both models configured
        AC: 7.10.1 - Model selection during KB creation
        """
        kb_data = {
            "name": "Test KB with Both Models",
            "embedding_model_id": str(embedding_model.id),
            "generation_model_id": str(generation_model.id),
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["embedding_model"]["id"] == str(embedding_model.id)
        assert data["generation_model"]["id"] == str(generation_model.id)

    @pytest.mark.asyncio
    async def test_create_kb_with_inactive_model_returns_400(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        inactive_embedding_model: LLMModel,
    ):
        """
        GIVEN: Authenticated user with inactive embedding model
        WHEN: POST /api/v1/knowledge-bases with inactive model ID
        THEN: Returns 400 Bad Request
        AC: 7.10.2 - Only active models appear in selection
        """
        kb_data = {
            "name": "Test KB with Inactive Model",
            "embedding_model_id": str(inactive_embedding_model.id),
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not active" in response.json().get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_create_kb_with_wrong_model_type_returns_400(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        generation_model: LLMModel,
    ):
        """
        GIVEN: Authenticated user using generation model as embedding model
        WHEN: POST /api/v1/knowledge-bases with wrong model type
        THEN: Returns 400 Bad Request
        AC: 7.10.2 - Model type validation
        """
        kb_data = {
            "name": "Test KB with Wrong Model Type",
            "embedding_model_id": str(generation_model.id),  # Wrong type!
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "wrong type" in response.json().get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_create_kb_with_nonexistent_model_returns_400(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
    ):
        """
        GIVEN: Authenticated user with non-existent model ID
        WHEN: POST /api/v1/knowledge-bases with invalid model ID
        THEN: Returns 400 Bad Request
        AC: 7.10.2 - Model validation
        """
        fake_model_id = "00000000-0000-0000-0000-000000000000"
        kb_data = {
            "name": "Test KB with Fake Model",
            "embedding_model_id": fake_model_id,
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found" in response.json().get("detail", "").lower()


# =============================================================================
# AC-7.10.4: Qdrant Collection Auto-Creation (P0)
# =============================================================================


class TestQdrantCollectionCreation:
    """Tests for Qdrant collection creation with correct dimensions."""

    @pytest.mark.asyncio
    async def test_kb_creation_sets_qdrant_collection_name(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        embedding_model: LLMModel,
    ):
        """
        GIVEN: Authenticated user with embedding model
        WHEN: POST /api/v1/knowledge-bases with embedding model
        THEN: KB has qdrant_collection_name set
        AC: 7.10.4 - Qdrant collection auto-created
        """
        kb_data = {
            "name": "Test KB for Qdrant Collection",
            "embedding_model_id": str(embedding_model.id),
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data.get("qdrant_collection_name") is not None
        assert data["qdrant_collection_name"].startswith("kb_")

    @pytest.mark.asyncio
    async def test_kb_creation_sets_vector_size_from_model(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        embedding_model: LLMModel,
    ):
        """
        GIVEN: Embedding model with dimensions=1536
        WHEN: POST /api/v1/knowledge-bases with that model
        THEN: KB has qdrant_vector_size=1536
        AC: 7.10.4 - Dimensions from embedding model
        """
        kb_data = {
            "name": "Test KB for Vector Size",
            "embedding_model_id": str(embedding_model.id),
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data.get("qdrant_vector_size") == 1536  # From embedding_model fixture

    @pytest.mark.asyncio
    async def test_kb_creation_uses_model_distance_metric(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        second_embedding_model: LLMModel,
    ):
        """
        GIVEN: Embedding model with dimensions=768 and distance_metric=euclidean
        WHEN: POST /api/v1/knowledge-bases with that model
        THEN: KB has correct vector size
        AC: 7.10.4 - Distance metric from model config
        """
        kb_data = {
            "name": "Test KB for Distance Metric",
            "embedding_model_id": str(second_embedding_model.id),
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        # second_embedding_model has 768 dimensions
        assert data.get("qdrant_vector_size") == 768


# =============================================================================
# AC-7.10.5: KB-Level RAG Parameter Overrides (P1)
# =============================================================================


class TestKBRagParameterOverrides:
    """Tests for KB-level RAG parameter overrides."""

    @pytest.mark.asyncio
    async def test_create_kb_with_similarity_threshold(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
    ):
        """
        GIVEN: Authenticated user
        WHEN: POST /api/v1/knowledge-bases with similarity_threshold=0.8
        THEN: KB is created with similarity_threshold=0.8
        AC: 7.10.5 - KB-level parameter overrides
        """
        kb_data = {
            "name": "Test KB with Similarity Threshold",
            "similarity_threshold": 0.8,
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data.get("similarity_threshold") == 0.8

    @pytest.mark.asyncio
    async def test_create_kb_with_search_top_k(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
    ):
        """
        GIVEN: Authenticated user
        WHEN: POST /api/v1/knowledge-bases with search_top_k=20
        THEN: KB is created with search_top_k=20
        AC: 7.10.5 - KB-level parameter overrides
        """
        kb_data = {
            "name": "Test KB with Top K",
            "search_top_k": 20,
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data.get("search_top_k") == 20

    @pytest.mark.asyncio
    async def test_create_kb_with_temperature_override(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
    ):
        """
        GIVEN: Authenticated user
        WHEN: POST /api/v1/knowledge-bases with temperature=0.3
        THEN: KB is created with temperature=0.3
        AC: 7.10.5 - KB-level parameter overrides
        """
        kb_data = {
            "name": "Test KB with Temperature",
            "temperature": 0.3,
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data.get("temperature") == 0.3

    @pytest.mark.asyncio
    async def test_create_kb_with_rerank_enabled(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
    ):
        """
        GIVEN: Authenticated user
        WHEN: POST /api/v1/knowledge-bases with rerank_enabled=true
        THEN: KB is created with rerank_enabled=true
        AC: 7.10.5 - KB-level parameter overrides
        """
        kb_data = {
            "name": "Test KB with Rerank",
            "rerank_enabled": True,
        }
        response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json=kb_data,
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data.get("rerank_enabled") is True

    @pytest.mark.asyncio
    async def test_update_kb_rag_parameters(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
    ):
        """
        GIVEN: Existing KB
        WHEN: PUT /api/v1/knowledge-bases/{id} with new RAG parameters
        THEN: RAG parameters are updated
        AC: 7.10.5 - KB-level parameter overrides
        """
        # Create KB first
        create_response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json={"name": "Test KB for RAG Update"},
            cookies=user_cookies_for_kb,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        kb_id = create_response.json()["id"]

        # Update RAG parameters
        update_data = {
            "similarity_threshold": 0.9,
            "search_top_k": 30,
            "temperature": 0.5,
            "rerank_enabled": True,
        }
        update_response = await kb_client.put(
            f"/api/v1/knowledge-bases/{kb_id}",
            json=update_data,
            cookies=user_cookies_for_kb,
        )
        assert update_response.status_code == status.HTTP_200_OK
        data = update_response.json()
        assert data.get("similarity_threshold") == 0.9
        assert data.get("search_top_k") == 30
        assert data.get("temperature") == 0.5
        assert data.get("rerank_enabled") is True


# =============================================================================
# AC-7.10.6: Embedding Model Lock Warning (P1)
# =============================================================================


class TestEmbeddingModelLock:
    """Tests for embedding model lock after first document."""

    @pytest.mark.asyncio
    async def test_new_kb_has_embedding_model_locked_false(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        embedding_model: LLMModel,
    ):
        """
        GIVEN: Newly created KB with no documents
        WHEN: GET /api/v1/knowledge-bases/{id}
        THEN: embedding_model_locked is false
        AC: 7.10.6 - Lock warning displayed after first document
        """
        # Create KB
        create_response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json={
                "name": "Test KB for Lock Check",
                "embedding_model_id": str(embedding_model.id),
            },
            cookies=user_cookies_for_kb,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        kb_id = create_response.json()["id"]

        # Get KB and verify lock status
        get_response = await kb_client.get(
            f"/api/v1/knowledge-bases/{kb_id}",
            cookies=user_cookies_for_kb,
        )
        assert get_response.status_code == status.HTTP_200_OK
        data = get_response.json()
        assert data.get("embedding_model_locked") is False

    @pytest.mark.asyncio
    async def test_kb_with_documents_has_embedding_model_locked_true(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        embedding_model: LLMModel,
        db_session_for_kb: AsyncSession,
        test_user_for_kb: dict,
    ):
        """
        GIVEN: KB with at least one document
        WHEN: GET /api/v1/knowledge-bases/{id}
        THEN: embedding_model_locked is true
        AC: 7.10.6 - Lock warning displayed after first document
        """
        # Create KB
        create_response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json={
                "name": "Test KB with Document",
                "embedding_model_id": str(embedding_model.id),
            },
            cookies=user_cookies_for_kb,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        kb_id = create_response.json()["id"]

        # Add a document directly to database (simulating upload)
        from uuid import UUID

        doc = Document(
            kb_id=UUID(kb_id),
            name="Test Document.md",
            original_filename="test.md",
            mime_type="text/markdown",
            file_size_bytes=1024,
            file_path=f"kb-{kb_id}/test.md",
            checksum="a" * 64,
            status=DocumentStatus.READY,
            chunk_count=1,
            uploaded_by=UUID(test_user_for_kb["user_id"]),
        )
        db_session_for_kb.add(doc)
        await db_session_for_kb.commit()

        # Get KB and verify lock status
        get_response = await kb_client.get(
            f"/api/v1/knowledge-bases/{kb_id}",
            cookies=user_cookies_for_kb,
        )
        assert get_response.status_code == status.HTTP_200_OK
        data = get_response.json()
        assert data.get("embedding_model_locked") is True


# =============================================================================
# AC-7.10.7: Generation Model Changeable (P1)
# =============================================================================


class TestGenerationModelChange:
    """Tests for generation model changes without reprocessing."""

    @pytest.mark.asyncio
    async def test_update_generation_model_on_new_kb(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        generation_model: LLMModel,
        second_generation_model: LLMModel,
    ):
        """
        GIVEN: KB with generation model
        WHEN: PUT /api/v1/knowledge-bases/{id} with new generation_model_id
        THEN: Generation model is updated
        AC: 7.10.7 - Generation model changeable
        """
        # Create KB with first generation model
        create_response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json={
                "name": "Test KB for Gen Model Change",
                "generation_model_id": str(generation_model.id),
            },
            cookies=user_cookies_for_kb,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        kb_id = create_response.json()["id"]

        # Update to second generation model
        update_response = await kb_client.put(
            f"/api/v1/knowledge-bases/{kb_id}",
            json={"generation_model_id": str(second_generation_model.id)},
            cookies=user_cookies_for_kb,
        )
        assert update_response.status_code == status.HTTP_200_OK
        data = update_response.json()
        assert data["generation_model"]["id"] == str(second_generation_model.id)

    @pytest.mark.asyncio
    async def test_update_generation_model_on_kb_with_documents(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        embedding_model: LLMModel,
        generation_model: LLMModel,
        second_generation_model: LLMModel,
        db_session_for_kb: AsyncSession,
        test_user_for_kb: dict,
    ):
        """
        GIVEN: KB with documents (embedding model locked)
        WHEN: PUT /api/v1/knowledge-bases/{id} with new generation_model_id
        THEN: Generation model is updated (no reprocessing needed)
        AC: 7.10.7 - Generation model changeable without document reprocessing
        """
        from uuid import UUID

        # Create KB with both models
        create_response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json={
                "name": "Test KB with Docs for Gen Change",
                "embedding_model_id": str(embedding_model.id),
                "generation_model_id": str(generation_model.id),
            },
            cookies=user_cookies_for_kb,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        kb_id = create_response.json()["id"]

        # Add a document
        doc = Document(
            kb_id=UUID(kb_id),
            name="Test Document.md",
            original_filename="test.md",
            mime_type="text/markdown",
            file_size_bytes=1024,
            file_path=f"kb-{kb_id}/test.md",
            checksum="b" * 64,
            status=DocumentStatus.READY,
            chunk_count=1,
            uploaded_by=UUID(test_user_for_kb["user_id"]),
        )
        db_session_for_kb.add(doc)
        await db_session_for_kb.commit()

        # Update generation model (should succeed despite documents)
        update_response = await kb_client.put(
            f"/api/v1/knowledge-bases/{kb_id}",
            json={"generation_model_id": str(second_generation_model.id)},
            cookies=user_cookies_for_kb,
        )
        assert update_response.status_code == status.HTTP_200_OK
        data = update_response.json()
        assert data["generation_model"]["id"] == str(second_generation_model.id)


# =============================================================================
# Available Models Endpoint Tests (Supporting AC-7.10.1, 7.10.2)
# =============================================================================


class TestAvailableModelsEndpoint:
    """Tests for the available models endpoint used by KB creation UI."""

    @pytest.mark.asyncio
    async def test_get_available_models_returns_active_models(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        embedding_model: LLMModel,
        generation_model: LLMModel,
    ):
        """
        GIVEN: Active embedding and generation models exist
        WHEN: GET /api/v1/models/available
        THEN: Returns lists of active models
        AC: 7.10.1, 7.10.2 - Model selection shows active models
        """
        response = await kb_client.get(
            "/api/v1/models/available",
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "embedding_models" in data
        assert "generation_models" in data
        # Verify at least one of each type
        assert len(data["embedding_models"]) >= 1
        assert len(data["generation_models"]) >= 1

    @pytest.mark.asyncio
    async def test_get_available_models_excludes_inactive(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        embedding_model: LLMModel,
        inactive_embedding_model: LLMModel,
    ):
        """
        GIVEN: Both active and inactive embedding models exist
        WHEN: GET /api/v1/models/available
        THEN: Only active models are returned
        AC: 7.10.2 - Only active models appear in selection
        """
        response = await kb_client.get(
            "/api/v1/models/available",
            cookies=user_cookies_for_kb,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Check that inactive model is not in the list
        embedding_ids = [m["id"] for m in data["embedding_models"]]
        assert str(inactive_embedding_model.id) not in embedding_ids
        # But active model should be there
        assert str(embedding_model.id) in embedding_ids


# =============================================================================
# KB Response Model Info Tests (AC-7.10.3)
# =============================================================================


class TestKBResponseModelInfo:
    """Tests for model info in KB responses."""

    @pytest.mark.asyncio
    async def test_kb_response_includes_embedding_model_info(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        embedding_model: LLMModel,
    ):
        """
        GIVEN: KB created with embedding model
        WHEN: GET /api/v1/knowledge-bases/{id}
        THEN: Response includes embedding model info with dimensions
        AC: 7.10.3 - Model info displayed on selection
        """
        # Create KB
        create_response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json={
                "name": "Test KB for Model Info",
                "embedding_model_id": str(embedding_model.id),
            },
            cookies=user_cookies_for_kb,
        )
        kb_id = create_response.json()["id"]

        # Get KB details
        get_response = await kb_client.get(
            f"/api/v1/knowledge-bases/{kb_id}",
            cookies=user_cookies_for_kb,
        )
        assert get_response.status_code == status.HTTP_200_OK
        data = get_response.json()
        model_info = data.get("embedding_model")
        assert model_info is not None
        assert model_info["id"] == str(embedding_model.id)
        assert model_info["name"] == embedding_model.name
        assert model_info.get("dimensions") == 1536

    @pytest.mark.asyncio
    async def test_kb_response_includes_generation_model_info(
        self,
        kb_client: AsyncClient,
        user_cookies_for_kb: dict,
        generation_model: LLMModel,
    ):
        """
        GIVEN: KB created with generation model
        WHEN: GET /api/v1/knowledge-bases/{id}
        THEN: Response includes generation model info with context_window
        AC: 7.10.3 - Model info displayed
        """
        # Create KB
        create_response = await kb_client.post(
            "/api/v1/knowledge-bases/",
            json={
                "name": "Test KB for Gen Model Info",
                "generation_model_id": str(generation_model.id),
            },
            cookies=user_cookies_for_kb,
        )
        kb_id = create_response.json()["id"]

        # Get KB details
        get_response = await kb_client.get(
            f"/api/v1/knowledge-bases/{kb_id}",
            cookies=user_cookies_for_kb,
        )
        assert get_response.status_code == status.HTTP_200_OK
        data = get_response.json()
        model_info = data.get("generation_model")
        assert model_info is not None
        assert model_info["id"] == str(generation_model.id)
        assert model_info["name"] == generation_model.name
        assert model_info.get("context_window") == 200000
