"""Integration tests for LLM Model Registry API endpoints.

Story 7-9: LLM Model Registry (AC-7.9.1 through AC-7.9.11)

Test Coverage:
- [P0] Admin-only access enforcement (403 for non-admin, 401 for unauthenticated)
- [P1] CRUD operations for models (create, read, update, delete)
- [P1] List models with filters
- [P1] Set default model
- [P2] Connection test endpoint
- [P2] Public model endpoints

Knowledge Base References:
- test-quality.md: Given-When-Then structure
- fixture-architecture.md: Integration test patterns
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user import User
from tests.factories import create_registration_data

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def models_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def db_session_for_models(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for admin user setup."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def admin_user_for_models(
    models_client: AsyncClient, db_session_for_models: AsyncSession
) -> dict:
    """Create an admin test user for models tests."""
    user_data = create_registration_data()
    response = await models_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Set is_superuser=True in database
    result = await db_session_for_models.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await db_session_for_models.commit()

    return {**user_data, "user": response_data, "user_id": response_data["id"]}


@pytest.fixture
async def admin_cookies_for_models(
    models_client: AsyncClient, admin_user_for_models: dict
) -> dict:
    """Login as admin and return cookies."""
    login_response = await models_client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user_for_models["email"],
            "password": admin_user_for_models["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_for_models(models_client: AsyncClient) -> dict:
    """Create a regular (non-admin) test user."""
    user_data = create_registration_data()
    response = await models_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json(), "user_id": response.json()["id"]}


@pytest.fixture
async def regular_user_cookies_for_models(
    models_client: AsyncClient, regular_user_for_models: dict
) -> dict:
    """Login as regular user and return cookies."""
    login_response = await models_client.post(
        "/api/v1/auth/login",
        data={
            "username": regular_user_for_models["email"],
            "password": regular_user_for_models["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


def create_embedding_model_data(name: str = "Test Embedding Model") -> dict:
    """Create test data for embedding model."""
    return {
        "type": "embedding",
        "provider": "openai",
        "name": name,
        "model_id": f"text-embedding-{name.lower().replace(' ', '-')}",
        "config": {
            "dimensions": 1536,
            "max_tokens": 8191,
            "normalize": True,
            "distance_metric": "cosine",
            "batch_size": 100,
            "tags": [],
        },
        "is_default": False,
    }


def create_generation_model_data(name: str = "Test Generation Model") -> dict:
    """Create test data for generation model."""
    return {
        "type": "generation",
        "provider": "anthropic",
        "name": name,
        "model_id": f"claude-{name.lower().replace(' ', '-')}",
        "config": {
            "context_window": 200000,
            "max_output_tokens": 8192,
            "supports_streaming": True,
            "supports_json_mode": False,
            "supports_vision": True,
            "temperature_default": 0.7,
            "temperature_range": [0.0, 2.0],
            "top_p_default": 1.0,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
            "tags": [],
        },
        "is_default": False,
    }


@pytest.fixture
async def test_model(
    models_client: AsyncClient, admin_cookies_for_models: dict
) -> dict:
    """Create a test model for use in other tests."""
    model_data = create_embedding_model_data("Test Model Fixture")
    response = await models_client.post(
        "/api/v1/admin/models",
        json=model_data,
        cookies=admin_cookies_for_models,
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


# =============================================================================
# Access Control Tests (P0)
# =============================================================================


class TestModelAccessControl:
    """Tests for admin-only access enforcement."""

    @pytest.mark.asyncio
    async def test_list_models_unauthenticated_returns_401(
        self, models_client: AsyncClient
    ):
        """
        GIVEN: No authentication
        WHEN: GET /api/v1/admin/models is called
        THEN: Returns 401 Unauthorized
        """
        response = await models_client.get("/api/v1/admin/models")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_list_models_non_admin_returns_403(
        self, models_client: AsyncClient, regular_user_cookies_for_models: dict
    ):
        """
        GIVEN: Authenticated non-admin user
        WHEN: GET /api/v1/admin/models is called
        THEN: Returns 403 Forbidden
        """
        response = await models_client.get(
            "/api/v1/admin/models",
            cookies=regular_user_cookies_for_models,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_model_non_admin_returns_403(
        self, models_client: AsyncClient, regular_user_cookies_for_models: dict
    ):
        """
        GIVEN: Authenticated non-admin user
        WHEN: POST /api/v1/admin/models is called
        THEN: Returns 403 Forbidden
        """
        model_data = create_embedding_model_data()
        response = await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=regular_user_cookies_for_models,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_delete_model_non_admin_returns_403(
        self,
        models_client: AsyncClient,
        regular_user_cookies_for_models: dict,
        test_model: dict,
    ):
        """
        GIVEN: Authenticated non-admin user
        WHEN: DELETE /api/v1/admin/models/{id} is called
        THEN: Returns 403 Forbidden
        """
        response = await models_client.delete(
            f"/api/v1/admin/models/{test_model['id']}",
            cookies=regular_user_cookies_for_models,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# List Models Tests (P1)
# =============================================================================


class TestListModels:
    """Tests for listing models."""

    @pytest.mark.asyncio
    async def test_list_models_empty_returns_200(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, no models in database
        WHEN: GET /api/v1/admin/models is called
        THEN: Returns 200 with empty list
        """
        response = await models_client.get(
            "/api/v1/admin/models",
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "models" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_models_returns_created_models(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, models in database
        WHEN: GET /api/v1/admin/models is called
        THEN: Returns 200 with models list
        """
        # Create a model first
        model_data = create_embedding_model_data("List Test Model")
        create_response = await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=admin_cookies_for_models,
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # List models
        response = await models_client.get(
            "/api/v1/admin/models",
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert len(data["models"]) >= 1

    @pytest.mark.asyncio
    async def test_list_models_filter_by_type(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, models of different types
        WHEN: GET /api/v1/admin/models?type=embedding is called
        THEN: Returns only embedding models
        """
        # Create embedding model
        embedding_data = create_embedding_model_data("Filter Type Test")
        await models_client.post(
            "/api/v1/admin/models",
            json=embedding_data,
            cookies=admin_cookies_for_models,
        )

        # Filter by type
        response = await models_client.get(
            "/api/v1/admin/models?type=embedding",
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for model in data["models"]:
            assert model["type"] == "embedding"

    @pytest.mark.asyncio
    async def test_list_models_filter_by_provider(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, models of different providers
        WHEN: GET /api/v1/admin/models?provider=openai is called
        THEN: Returns only OpenAI models
        """
        # Create model
        model_data = create_embedding_model_data("Filter Provider Test")
        await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=admin_cookies_for_models,
        )

        # Filter by provider
        response = await models_client.get(
            "/api/v1/admin/models?provider=openai",
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for model in data["models"]:
            assert model["provider"] == "openai"


# =============================================================================
# Create Model Tests (P1)
# =============================================================================


class TestCreateModel:
    """Tests for creating models."""

    @pytest.mark.asyncio
    async def test_create_embedding_model_returns_201(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, valid embedding model data
        WHEN: POST /api/v1/admin/models is called
        THEN: Returns 201 with created model
        """
        model_data = create_embedding_model_data("Create Embedding Test")
        response = await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=admin_cookies_for_models,
        )
        if response.status_code != status.HTTP_201_CREATED:
            print(f"ERROR: {response.status_code} - {response.text}")
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == model_data["name"]
        assert data["type"] == "embedding"
        assert data["provider"] == "openai"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_generation_model_returns_201(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, valid generation model data
        WHEN: POST /api/v1/admin/models is called
        THEN: Returns 201 with created model
        """
        model_data = create_generation_model_data("Create Generation Test")
        response = await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == model_data["name"]
        assert data["type"] == "generation"
        assert data["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_create_model_with_api_key_hides_key(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, model data with API key
        WHEN: POST /api/v1/admin/models is called
        THEN: Returns 201, has_api_key=True, key not exposed
        """
        model_data = create_embedding_model_data("API Key Test")
        model_data["api_key"] = "sk-test-key-12345"
        response = await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["has_api_key"] is True
        # API key should never be exposed in response
        assert "api_key" not in data
        assert "api_key_encrypted" not in data

    @pytest.mark.asyncio
    async def test_create_model_as_default(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, model data with is_default=True
        WHEN: POST /api/v1/admin/models is called
        THEN: Returns 201 with is_default=True
        """
        model_data = create_embedding_model_data("Default Model Test")
        model_data["is_default"] = True
        response = await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_default"] is True


# =============================================================================
# Get Model Tests (P1)
# =============================================================================


class TestGetModel:
    """Tests for getting a single model."""

    @pytest.mark.asyncio
    async def test_get_model_returns_200(
        self,
        models_client: AsyncClient,
        admin_cookies_for_models: dict,
        test_model: dict,
    ):
        """
        GIVEN: Admin user, existing model
        WHEN: GET /api/v1/admin/models/{id} is called
        THEN: Returns 200 with model details
        """
        response = await models_client.get(
            f"/api/v1/admin/models/{test_model['id']}",
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_model["id"]
        assert data["name"] == test_model["name"]
        assert "config" in data  # Full config returned for single model

    @pytest.mark.asyncio
    async def test_get_model_not_found_returns_404(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, non-existent model ID
        WHEN: GET /api/v1/admin/models/{id} is called
        THEN: Returns 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await models_client.get(
            f"/api/v1/admin/models/{fake_id}",
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Update Model Tests (P1)
# =============================================================================


class TestUpdateModel:
    """Tests for updating models."""

    @pytest.mark.asyncio
    async def test_update_model_name_returns_200(
        self,
        models_client: AsyncClient,
        admin_cookies_for_models: dict,
        test_model: dict,
    ):
        """
        GIVEN: Admin user, existing model
        WHEN: PUT /api/v1/admin/models/{id} with new name
        THEN: Returns 200 with updated model
        """
        response = await models_client.put(
            f"/api/v1/admin/models/{test_model['id']}",
            json={"name": "Updated Model Name"},
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Model Name"

    @pytest.mark.asyncio
    async def test_update_model_status_returns_200(
        self,
        models_client: AsyncClient,
        admin_cookies_for_models: dict,
        test_model: dict,
    ):
        """
        GIVEN: Admin user, existing model
        WHEN: PUT /api/v1/admin/models/{id} with new status
        THEN: Returns 200 with updated status
        """
        response = await models_client.put(
            f"/api/v1/admin/models/{test_model['id']}",
            json={"status": "inactive"},
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_update_model_not_found_returns_404(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, non-existent model ID
        WHEN: PUT /api/v1/admin/models/{id} is called
        THEN: Returns 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await models_client.put(
            f"/api/v1/admin/models/{fake_id}",
            json={"name": "New Name"},
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Delete Model Tests (P1)
# =============================================================================


class TestDeleteModel:
    """Tests for deleting models."""

    @pytest.mark.asyncio
    async def test_delete_model_returns_204(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, existing model
        WHEN: DELETE /api/v1/admin/models/{id} is called
        THEN: Returns 204 No Content
        """
        # Create a model to delete
        model_data = create_embedding_model_data("Delete Test Model")
        create_response = await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=admin_cookies_for_models,
        )
        model_id = create_response.json()["id"]

        # Delete the model
        response = await models_client.delete(
            f"/api/v1/admin/models/{model_id}",
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's deleted
        get_response = await models_client.get(
            f"/api/v1/admin/models/{model_id}",
            cookies=admin_cookies_for_models,
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_model_not_found_returns_404(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, non-existent model ID
        WHEN: DELETE /api/v1/admin/models/{id} is called
        THEN: Returns 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await models_client.delete(
            f"/api/v1/admin/models/{fake_id}",
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Set Default Model Tests (P1)
# =============================================================================


class TestSetDefaultModel:
    """Tests for setting default model."""

    @pytest.mark.asyncio
    async def test_set_default_returns_200(
        self,
        models_client: AsyncClient,
        admin_cookies_for_models: dict,
        test_model: dict,
    ):
        """
        GIVEN: Admin user, existing model
        WHEN: POST /api/v1/admin/models/{id}/set-default is called
        THEN: Returns 200 with is_default=True
        """
        response = await models_client.post(
            f"/api/v1/admin/models/{test_model['id']}/set-default",
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_default"] is True

    @pytest.mark.asyncio
    async def test_set_default_clears_previous_default(
        self, models_client: AsyncClient, admin_cookies_for_models: dict
    ):
        """
        GIVEN: Admin user, two models of same type
        WHEN: Second model is set as default
        THEN: First model is no longer default
        """
        # Create first model as default
        model1_data = create_embedding_model_data("Default Model 1")
        model1_data["is_default"] = True
        response1 = await models_client.post(
            "/api/v1/admin/models",
            json=model1_data,
            cookies=admin_cookies_for_models,
        )
        model1_id = response1.json()["id"]

        # Create second model
        model2_data = create_embedding_model_data("Default Model 2")
        response2 = await models_client.post(
            "/api/v1/admin/models",
            json=model2_data,
            cookies=admin_cookies_for_models,
        )
        model2_id = response2.json()["id"]

        # Set second model as default
        await models_client.post(
            f"/api/v1/admin/models/{model2_id}/set-default",
            cookies=admin_cookies_for_models,
        )

        # Verify first model is no longer default
        get_model1 = await models_client.get(
            f"/api/v1/admin/models/{model1_id}",
            cookies=admin_cookies_for_models,
        )
        assert get_model1.json()["is_default"] is False

        # Verify second model is default
        get_model2 = await models_client.get(
            f"/api/v1/admin/models/{model2_id}",
            cookies=admin_cookies_for_models,
        )
        assert get_model2.json()["is_default"] is True


# =============================================================================
# Connection Test Tests (P2)
# =============================================================================


class TestConnectionTest:
    """Tests for model connection testing."""

    @pytest.mark.asyncio
    async def test_test_connection_endpoint_returns_200(
        self,
        models_client: AsyncClient,
        admin_cookies_for_models: dict,
        test_model: dict,
    ):
        """
        GIVEN: Admin user, existing model
        WHEN: POST /api/v1/admin/models/{id}/test is called
        THEN: Returns 200 with test result
        """
        response = await models_client.post(
            f"/api/v1/admin/models/{test_model['id']}/test",
            cookies=admin_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "message" in data


# =============================================================================
# Public Model Endpoints Tests (P2)
# =============================================================================


class TestPublicModelEndpoints:
    """Tests for public model listing endpoints."""

    @pytest.mark.asyncio
    async def test_get_available_models_authenticated(
        self,
        models_client: AsyncClient,
        regular_user_cookies_for_models: dict,
        admin_cookies_for_models: dict,
    ):
        """
        GIVEN: Authenticated user, some models exist
        WHEN: GET /api/v1/models/available is called
        THEN: Returns 200 with available models
        """
        # First create a model as admin
        model_data = create_embedding_model_data("Public Test Model")
        await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=admin_cookies_for_models,
        )

        # Then access as regular user
        response = await models_client.get(
            "/api/v1/models/available",
            cookies=regular_user_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "embedding_models" in data
        assert "generation_models" in data

    @pytest.mark.asyncio
    async def test_get_available_models_unauthenticated_returns_401(
        self, models_client: AsyncClient
    ):
        """
        GIVEN: No authentication
        WHEN: GET /api/v1/models/available is called
        THEN: Returns 401 Unauthorized
        """
        response = await models_client.get("/api/v1/models/available")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_embedding_models_returns_list(
        self,
        models_client: AsyncClient,
        regular_user_cookies_for_models: dict,
        admin_cookies_for_models: dict,
    ):
        """
        GIVEN: Authenticated user, embedding models exist
        WHEN: GET /api/v1/models/embedding is called
        THEN: Returns 200 with embedding models list
        """
        # Create embedding model as admin
        model_data = create_embedding_model_data("Embedding Public Test")
        await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=admin_cookies_for_models,
        )

        # Get embedding models as regular user
        response = await models_client.get(
            "/api/v1/models/embedding",
            cookies=regular_user_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_generation_models_returns_list(
        self,
        models_client: AsyncClient,
        regular_user_cookies_for_models: dict,
        admin_cookies_for_models: dict,
    ):
        """
        GIVEN: Authenticated user, generation models exist
        WHEN: GET /api/v1/models/generation is called
        THEN: Returns 200 with generation models list
        """
        # Create generation model as admin
        model_data = create_generation_model_data("Generation Public Test")
        await models_client.post(
            "/api/v1/admin/models",
            json=model_data,
            cookies=admin_cookies_for_models,
        )

        # Get generation models as regular user
        response = await models_client.get(
            "/api/v1/models/generation",
            cookies=regular_user_cookies_for_models,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
