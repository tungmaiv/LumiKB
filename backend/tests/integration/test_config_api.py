"""Integration tests for system configuration API endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit import AuditEvent
from app.models.config import SystemConfig
from app.models.llm_model import LLMModel, ModelStatus, ModelType
from app.models.user import User
from tests.factories import create_registration_data


@pytest.fixture
async def admin_client_for_config(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def db_session_for_config(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for admin user setup."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def admin_user_for_config(
    admin_client_for_config: AsyncClient, db_session_for_config: AsyncSession
) -> dict:
    """Create an admin test user."""
    user_data = create_registration_data()
    response = await admin_client_for_config.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Set is_superuser=True in database
    result = await db_session_for_config.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await db_session_for_config.commit()

    return {**user_data, "user": response_data}


@pytest.fixture
async def admin_cookies_for_config(
    admin_client_for_config: AsyncClient, admin_user_for_config: dict
) -> dict:
    """Login as admin and return cookies."""
    login_response = await admin_client_for_config.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user_for_config["email"],
            "password": admin_user_for_config["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_for_config(admin_client_for_config: AsyncClient) -> dict:
    """Create a regular (non-admin) test user."""
    user_data = create_registration_data()
    response = await admin_client_for_config.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json()}


@pytest.fixture
async def regular_user_cookies_for_config(
    admin_client_for_config: AsyncClient, regular_user_for_config: dict
) -> dict:
    """Login as regular user and return cookies."""
    login_response = await admin_client_for_config.post(
        "/api/v1/auth/login",
        data={
            "username": regular_user_for_config["email"],
            "password": regular_user_for_config["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.mark.asyncio
class TestGetSystemConfig:
    """Tests for GET /api/v1/admin/config."""

    async def test_get_config_admin_returns_200(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
    ):
        """Test GET /api/v1/admin/config returns 200 for admin."""
        response = await admin_client_for_config.get(
            "/api/v1/admin/config",
            cookies=admin_cookies_for_config,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return 8 default settings
        assert len(data) == 8
        assert "session_timeout_minutes" in data
        assert "login_rate_limit_per_hour" in data

        # Verify structure
        setting = data["session_timeout_minutes"]
        assert setting["key"] == "session_timeout_minutes"
        assert setting["value"] == 720
        assert setting["data_type"] == "integer"
        assert setting["category"] == "Security"

    async def test_get_config_non_admin_returns_403(
        self,
        admin_client_for_config: AsyncClient,
        regular_user_cookies_for_config: dict,
    ):
        """Test GET /api/v1/admin/config returns 403 for non-admin user."""
        response = await admin_client_for_config.get(
            "/api/v1/admin/config",
            cookies=regular_user_cookies_for_config,
        )

        assert response.status_code == 403

    async def test_get_config_unauthenticated_returns_401(
        self,
        admin_client_for_config: AsyncClient,
    ):
        """Test GET /api/v1/admin/config returns 401 for unauthenticated request."""
        response = await admin_client_for_config.get("/api/v1/admin/config")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUpdateConfigSetting:
    """Tests for PUT /api/v1/admin/config/{key}."""

    async def test_update_config_valid_value_returns_200(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
        db_session_for_config: AsyncSession,
        admin_user_for_config: dict,
    ):
        """Test PUT /api/v1/admin/config/{key} with valid value returns 200."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/config/session_timeout_minutes",
            cookies=admin_cookies_for_config,
            json={"value": 1440},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response
        assert data["setting"]["key"] == "session_timeout_minutes"
        assert data["setting"]["value"] == 1440
        assert "restart_required" in data

        # Verify DB updated
        query = select(SystemConfig).where(
            SystemConfig.key == "session_timeout_minutes"
        )
        result = await db_session_for_config.execute(query)
        db_setting = result.scalar_one_or_none()

        assert db_setting is not None
        assert db_setting.value == 1440
        assert db_setting.updated_by == admin_user_for_config["email"]

    async def test_update_config_creates_audit_event(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
        db_session_for_config: AsyncSession,
    ):
        """Test PUT /api/v1/admin/config/{key} creates audit event."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/config/login_rate_limit_per_hour",
            cookies=admin_cookies_for_config,
            json={"value": 15},
        )

        assert response.status_code == 200

        # Verify audit event created
        query = (
            select(AuditEvent)
            .where(AuditEvent.action == "config.update")
            .where(
                AuditEvent.details["setting_key"].as_string()
                == "login_rate_limit_per_hour"
            )
            .order_by(AuditEvent.timestamp.desc())
        )
        result = await db_session_for_config.execute(query)
        audit_event = result.scalars().first()

        assert audit_event is not None
        assert audit_event.resource_type == "system_config"
        assert audit_event.details["setting_key"] == "login_rate_limit_per_hour"
        assert audit_event.details["old_value"] == 10
        assert audit_event.details["new_value"] == 15

    async def test_update_config_invalid_type_returns_400(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
    ):
        """Test PUT /api/v1/admin/config/{key} with wrong type returns 400."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/config/session_timeout_minutes",
            cookies=admin_cookies_for_config,
            json={"value": "not_a_number"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid value type" in data["detail"]

    async def test_update_config_below_min_returns_400(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
    ):
        """Test PUT /api/v1/admin/config/{key} with value below min returns 400."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/config/session_timeout_minutes",
            cookies=admin_cookies_for_config,
            json={"value": 30},  # Min is 60
        )

        assert response.status_code == 400
        data = response.json()
        assert "below minimum" in data["detail"]

    async def test_update_config_above_max_returns_400(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
    ):
        """Test PUT /api/v1/admin/config/{key} with value above max returns 400."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/config/session_timeout_minutes",
            cookies=admin_cookies_for_config,
            json={"value": 50000},  # Max is 43200
        )

        assert response.status_code == 400
        data = response.json()
        assert "exceeds maximum" in data["detail"]

    async def test_update_config_nonexistent_key_returns_404(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
    ):
        """Test PUT /api/v1/admin/config/{key} with invalid key returns 404."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/config/invalid_key",
            cookies=admin_cookies_for_config,
            json={"value": 100},
        )

        assert response.status_code == 404

    async def test_update_config_non_admin_returns_403(
        self,
        admin_client_for_config: AsyncClient,
        regular_user_cookies_for_config: dict,
    ):
        """Test PUT /api/v1/admin/config/{key} returns 403 for non-admin."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/config/session_timeout_minutes",
            cookies=regular_user_cookies_for_config,
            json={"value": 1440},
        )

        assert response.status_code == 403


@pytest.mark.asyncio
class TestGetRestartRequiredSettings:
    """Tests for GET /api/v1/admin/config/restart-required."""

    async def test_get_restart_required_empty_initially(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
    ):
        """Test GET /api/v1/admin/config/restart-required returns empty list initially."""
        response = await admin_client_for_config.get(
            "/api/v1/admin/config/restart-required",
            cookies=admin_cookies_for_config,
        )

        assert response.status_code == 200
        assert response.json() == []

    async def test_get_restart_required_after_update(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
    ):
        """Test GET /api/v1/admin/config/restart-required returns keys after update."""
        # Update a setting that requires restart
        await admin_client_for_config.put(
            "/api/v1/admin/config/default_chunk_size_tokens",
            cookies=admin_cookies_for_config,
            json={"value": 1024},
        )

        response = await admin_client_for_config.get(
            "/api/v1/admin/config/restart-required",
            cookies=admin_cookies_for_config,
        )

        assert response.status_code == 200
        data = response.json()
        assert "default_chunk_size_tokens" in data

    async def test_get_restart_required_non_admin_returns_403(
        self,
        admin_client_for_config: AsyncClient,
        regular_user_cookies_for_config: dict,
    ):
        """Test GET /api/v1/admin/config/restart-required returns 403 for non-admin."""
        response = await admin_client_for_config.get(
            "/api/v1/admin/config/restart-required",
            cookies=regular_user_cookies_for_config,
        )

        assert response.status_code == 403


# =============================================================================
# LLM Configuration Tests (Story 7-2)
# =============================================================================


@pytest.fixture
async def embedding_model_for_config(db_session_for_config: AsyncSession) -> LLMModel:
    """Create a test embedding model, clearing any existing default first."""
    from sqlalchemy import update

    # Clear existing default embedding models to avoid unique constraint violation
    await db_session_for_config.execute(
        update(LLMModel)
        .where(LLMModel.type == ModelType.EMBEDDING.value)
        .where(LLMModel.is_default.is_(True))
        .values(is_default=False)
    )
    await db_session_for_config.commit()

    model = LLMModel(
        id=uuid.uuid4(),
        name="Test Embedding Model",
        provider="gemini",
        model_id="text-embedding-004",
        type=ModelType.EMBEDDING.value,
        status=ModelStatus.ACTIVE.value,
        is_default=True,
        config={"dimensions": 768},
    )
    db_session_for_config.add(model)
    await db_session_for_config.commit()
    return model


@pytest.fixture
async def generation_model_for_config(db_session_for_config: AsyncSession) -> LLMModel:
    """Create a test generation model, clearing any existing default first."""
    from sqlalchemy import update

    # Clear existing default generation models to avoid unique constraint violation
    await db_session_for_config.execute(
        update(LLMModel)
        .where(LLMModel.type == ModelType.GENERATION.value)
        .where(LLMModel.is_default.is_(True))
        .values(is_default=False)
    )
    await db_session_for_config.commit()

    model = LLMModel(
        id=uuid.uuid4(),
        name="Test Generation Model",
        provider="qwen",
        model_id="qwen2.5-32b-instruct",
        type=ModelType.GENERATION.value,
        status=ModelStatus.ACTIVE.value,
        is_default=True,
        config={},
    )
    db_session_for_config.add(model)
    await db_session_for_config.commit()
    return model


@pytest.fixture
async def second_embedding_model_for_config(
    db_session_for_config: AsyncSession,
) -> LLMModel:
    """Create a second embedding model with different dimensions."""
    model = LLMModel(
        id=uuid.uuid4(),
        name="Alternative Embedding Model",
        provider="openai",
        model_id="text-embedding-3-small",
        type=ModelType.EMBEDDING.value,
        status=ModelStatus.ACTIVE.value,
        is_default=False,
        config={"dimensions": 1536},
    )
    db_session_for_config.add(model)
    await db_session_for_config.commit()
    return model


@pytest.mark.asyncio
class TestGetLLMConfig:
    """Tests for GET /api/v1/admin/llm/config (AC-7.2.1)."""

    async def test_get_llm_config_admin_returns_200(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
        embedding_model_for_config: LLMModel,  # noqa: ARG002
        generation_model_for_config: LLMModel,  # noqa: ARG002
    ):
        """Test GET /api/v1/admin/llm/config returns 200 for admin."""
        response = await admin_client_for_config.get(
            "/api/v1/admin/llm/config",
            cookies=admin_cookies_for_config,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "embedding_model" in data
        assert "generation_model" in data
        assert "generation_settings" in data
        assert "litellm_base_url" in data

        # Verify embedding model info
        assert data["embedding_model"]["name"] == "Test Embedding Model"
        assert data["embedding_model"]["provider"] == "gemini"
        assert data["embedding_model"]["is_default"] is True

        # Verify generation model info
        assert data["generation_model"]["name"] == "Test Generation Model"
        assert data["generation_model"]["provider"] == "qwen"

        # Verify generation settings
        assert "temperature" in data["generation_settings"]
        assert "max_tokens" in data["generation_settings"]
        assert "top_p" in data["generation_settings"]

    async def test_get_llm_config_non_admin_returns_403(
        self,
        admin_client_for_config: AsyncClient,
        regular_user_cookies_for_config: dict,
    ):
        """Test GET /api/v1/admin/llm/config returns 403 for non-admin."""
        response = await admin_client_for_config.get(
            "/api/v1/admin/llm/config",
            cookies=regular_user_cookies_for_config,
        )

        assert response.status_code == 403

    async def test_get_llm_config_unauthenticated_returns_401(
        self,
        admin_client_for_config: AsyncClient,
    ):
        """Test GET /api/v1/admin/llm/config returns 401 for unauthenticated."""
        response = await admin_client_for_config.get("/api/v1/admin/llm/config")
        assert response.status_code == 401

    async def test_get_llm_config_returns_structure(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
    ):
        """Test GET /api/v1/admin/llm/config returns proper structure."""
        # Note: This test verifies the response structure without depending on specific models.
        # The "no models" scenario is covered by unit tests in test_config_service.py.
        response = await admin_client_for_config.get(
            "/api/v1/admin/llm/config",
            cookies=admin_cookies_for_config,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure has required keys
        assert "embedding_model" in data
        assert "generation_model" in data
        assert "generation_settings" in data
        assert "litellm_base_url" in data

        # Verify generation_settings structure
        settings = data["generation_settings"]
        assert "temperature" in settings
        assert "max_tokens" in settings
        assert "top_p" in settings


@pytest.mark.asyncio
class TestUpdateLLMConfig:
    """Tests for PUT /api/v1/admin/llm/config (AC-7.2.2, AC-7.2.3)."""

    async def test_update_llm_config_generation_settings_returns_200(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
        embedding_model_for_config: LLMModel,  # noqa: ARG002
        generation_model_for_config: LLMModel,  # noqa: ARG002
    ):
        """Test PUT /api/v1/admin/llm/config with generation settings returns 200."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/llm/config",
            cookies=admin_cookies_for_config,
            json={
                "generation_settings": {
                    "temperature": 0.9,
                    "max_tokens": 4096,
                    "top_p": 0.95,
                }
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify hot reload applied
        assert data["hot_reload_applied"] is True

        # Verify updated settings
        assert data["config"]["generation_settings"]["temperature"] == 0.9
        assert data["config"]["generation_settings"]["max_tokens"] == 4096
        assert data["config"]["generation_settings"]["top_p"] == 0.95

    async def test_update_llm_config_change_generation_model(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
        generation_model_for_config: LLMModel,  # noqa: ARG002
        db_session_for_config: AsyncSession,
    ):
        """Test PUT /api/v1/admin/llm/config can change generation model."""
        # Create a second generation model
        new_model = LLMModel(
            id=uuid.uuid4(),
            name="New Generation Model",
            provider="anthropic",
            model_id="claude-3-sonnet",
            type=ModelType.GENERATION.value,
            status=ModelStatus.ACTIVE.value,
            is_default=False,
        )
        db_session_for_config.add(new_model)
        await db_session_for_config.commit()

        response = await admin_client_for_config.put(
            "/api/v1/admin/llm/config",
            cookies=admin_cookies_for_config,
            json={"generation_model_id": str(new_model.id)},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify model changed
        assert data["config"]["generation_model"]["name"] == "New Generation Model"
        assert data["config"]["generation_model"]["provider"] == "anthropic"
        assert data["hot_reload_applied"] is True

    async def test_update_llm_config_dimension_mismatch_warning(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
        embedding_model_for_config: LLMModel,  # noqa: ARG002
        second_embedding_model_for_config: LLMModel,
    ):
        """Test PUT /api/v1/admin/llm/config returns dimension warning (AC-7.2.3)."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/llm/config",
            cookies=admin_cookies_for_config,
            json={"embedding_model_id": str(second_embedding_model_for_config.id)},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify dimension warning
        assert data["dimension_warning"] is not None
        assert data["dimension_warning"]["has_mismatch"] is True
        assert data["dimension_warning"]["current_dimensions"] == 768
        assert data["dimension_warning"]["new_dimensions"] == 1536
        assert "warning_message" in data["dimension_warning"]

    async def test_update_llm_config_invalid_model_returns_400(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
    ):
        """Test PUT /api/v1/admin/llm/config with invalid model ID returns 400."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/llm/config",
            cookies=admin_cookies_for_config,
            json={"embedding_model_id": str(uuid.uuid4())},
        )

        assert response.status_code == 400
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_update_llm_config_wrong_model_type_returns_400(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
        embedding_model_for_config: LLMModel,
    ):
        """Test PUT /api/v1/admin/llm/config with wrong model type returns 400."""
        # Try to set embedding model as generation model
        response = await admin_client_for_config.put(
            "/api/v1/admin/llm/config",
            cookies=admin_cookies_for_config,
            json={"generation_model_id": str(embedding_model_for_config.id)},
        )

        assert response.status_code == 400
        data = response.json()
        assert "not a generation model" in data["detail"].lower()

    async def test_update_llm_config_non_admin_returns_403(
        self,
        admin_client_for_config: AsyncClient,
        regular_user_cookies_for_config: dict,
    ):
        """Test PUT /api/v1/admin/llm/config returns 403 for non-admin."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/llm/config",
            cookies=regular_user_cookies_for_config,
            json={"generation_settings": {"temperature": 0.5}},
        )

        assert response.status_code == 403

    async def test_update_llm_config_creates_audit_event(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
        generation_model_for_config: LLMModel,  # noqa: ARG002
        db_session_for_config: AsyncSession,
    ):
        """Test PUT /api/v1/admin/llm/config creates audit event."""
        response = await admin_client_for_config.put(
            "/api/v1/admin/llm/config",
            cookies=admin_cookies_for_config,
            json={"generation_settings": {"temperature": 0.8}},
        )

        assert response.status_code == 200

        # Verify audit event created
        query = (
            select(AuditEvent)
            .where(AuditEvent.action == "llm_config.update")
            .order_by(AuditEvent.timestamp.desc())
        )
        result = await db_session_for_config.execute(query)
        audit_event = result.scalars().first()

        assert audit_event is not None
        assert audit_event.resource_type == "system_config"


@pytest.mark.asyncio
class TestGetLLMHealth:
    """Tests for GET /api/v1/admin/llm/health (AC-7.2.4)."""

    async def test_get_llm_health_admin_returns_200(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
    ):
        """Test GET /api/v1/admin/llm/health returns 200 for admin."""
        response = await admin_client_for_config.get(
            "/api/v1/admin/llm/health",
            cookies=admin_cookies_for_config,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "embedding_health" in data
        assert "generation_health" in data
        assert "overall_healthy" in data

    async def test_get_llm_health_with_filter_returns_filtered(
        self,
        admin_client_for_config: AsyncClient,
        admin_cookies_for_config: dict,
        embedding_model_for_config: LLMModel,  # noqa: ARG002
    ):
        """Test GET /api/v1/admin/llm/health with filter returns only filtered type."""
        response = await admin_client_for_config.get(
            "/api/v1/admin/llm/health?model_type=embedding",
            cookies=admin_cookies_for_config,
        )

        assert response.status_code == 200
        data = response.json()

        # Embedding health should be present (may be healthy or not depending on LiteLLM)
        # Generation health should be None since we filtered
        assert data["generation_health"] is None

    async def test_get_llm_health_non_admin_returns_403(
        self,
        admin_client_for_config: AsyncClient,
        regular_user_cookies_for_config: dict,
    ):
        """Test GET /api/v1/admin/llm/health returns 403 for non-admin."""
        response = await admin_client_for_config.get(
            "/api/v1/admin/llm/health",
            cookies=regular_user_cookies_for_config,
        )

        assert response.status_code == 403

    async def test_get_llm_health_unauthenticated_returns_401(
        self,
        admin_client_for_config: AsyncClient,
    ):
        """Test GET /api/v1/admin/llm/health returns 401 for unauthenticated."""
        response = await admin_client_for_config.get("/api/v1/admin/llm/health")
        assert response.status_code == 401
