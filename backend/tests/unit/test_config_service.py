"""Unit tests for ConfigService.

Story 7-2: Centralized LLM Configuration with hot-reload capability.

Test Coverage:
- [P0] get_llm_config: Retrieve current LLM config with caching
- [P0] update_llm_config: Update models/settings with hot-reload
- [P0] test_model_health: Health check for configured models
- [P1] _check_dimension_mismatch: AC-7.2.3 dimension warning
- [P1] _publish_config_update: Redis pub/sub for hot-reload
- [P2] Cache invalidation on update

Knowledge Base References:
- test-quality.md: Given-When-Then structure
- test-levels-framework.md: Unit test characteristics
"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.llm_model import LLMModel, ModelType
from app.schemas.admin import (
    DimensionMismatchWarning,
    LLMConfig,
    LLMConfigModelInfo,
    LLMConfigSettings,
    LLMConfigUpdateRequest,
    LLMConfigUpdateResponse,
    LLMHealthResponse,
    ModelHealthStatus,
)
from app.services.config_service import ConfigService


class TestConfigServiceGetLLMConfig:
    """Tests for ConfigService.get_llm_config method (AC-7.2.1)."""

    @pytest.mark.asyncio
    async def test_get_llm_config_returns_cached_config(self):
        """
        GIVEN: ConfigService with cached LLM config in Redis
        WHEN: get_llm_config is called
        THEN: Returns cached config without DB query
        """
        # GIVEN: Mock session and Redis with cached data
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        cached_config = {
            "embedding_model": {
                "model_id": str(uuid4()),
                "name": "text-embedding-3-small",
                "provider": "openai",
                "model_identifier": "text-embedding-3-small",
                "api_endpoint": None,
                "is_default": True,
                "status": "active",
            },
            "generation_model": {
                "model_id": str(uuid4()),
                "name": "GPT-4o",
                "provider": "openai",
                "model_identifier": "gpt-4o",
                "api_endpoint": None,
                "is_default": True,
                "status": "active",
            },
            "generation_settings": {
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 1.0,
            },
            "litellm_base_url": "http://localhost:4000",
            "last_modified": None,
            "last_modified_by": None,
        }

        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(cached_config)

        with patch(
            "app.services.config_service.get_redis_client",
            return_value=mock_redis,
        ):
            # WHEN: Call get_llm_config
            result = await service.get_llm_config()

            # THEN: Returns cached config, no DB queries
            assert isinstance(result, LLMConfig)
            assert result.embedding_model.name == "text-embedding-3-small"
            assert result.generation_model.name == "GPT-4o"
            mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_llm_config_builds_from_db_on_cache_miss(self):
        """
        GIVEN: ConfigService with no cached config (cache miss)
        WHEN: get_llm_config is called
        THEN: Queries database for default models and caches result
        """
        # GIVEN: Mock session and Redis without cache
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        # Mock embedding model
        mock_embedding = MagicMock(spec=LLMModel)
        mock_embedding.id = uuid4()
        mock_embedding.name = "Embedding Model"
        mock_embedding.provider = "openai"
        mock_embedding.model_id = "text-embedding-ada-002"
        mock_embedding.api_endpoint = None
        mock_embedding.is_default = True
        mock_embedding.status = "active"

        # Mock generation model
        mock_generation = MagicMock(spec=LLMModel)
        mock_generation.id = uuid4()
        mock_generation.name = "Generation Model"
        mock_generation.provider = "openai"
        mock_generation.model_id = "gpt-4"
        mock_generation.api_endpoint = None
        mock_generation.is_default = True
        mock_generation.status = "active"

        # Setup mock query results
        embedding_result = MagicMock()
        embedding_result.scalar_one_or_none.return_value = mock_embedding

        generation_result = MagicMock()
        generation_result.scalar_one_or_none.return_value = mock_generation

        settings_result = MagicMock()
        settings_result.scalar_one_or_none.return_value = None  # No custom settings

        mock_session.execute.side_effect = [
            embedding_result,
            generation_result,
            settings_result,
            settings_result,  # For last_modified query
        ]

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Cache miss

        with (
            patch(
                "app.services.config_service.get_redis_client",
                return_value=mock_redis,
            ),
            patch("app.services.config_service.settings") as mock_settings,
        ):
            mock_settings.litellm_url = "http://localhost:4000"

            # WHEN: Call get_llm_config
            result = await service.get_llm_config()

            # THEN: Returns config from DB and caches
            assert isinstance(result, LLMConfig)
            assert result.embedding_model.name == "Embedding Model"
            assert result.generation_model.name == "Generation Model"
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_llm_config_returns_none_models_when_not_configured(self):
        """
        GIVEN: ConfigService with no default models configured
        WHEN: get_llm_config is called
        THEN: Returns config with None for embedding/generation models
        """
        # GIVEN: Mock session with no default models
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        # All queries return None
        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = no_result

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with (
            patch(
                "app.services.config_service.get_redis_client",
                return_value=mock_redis,
            ),
            patch("app.services.config_service.settings") as mock_settings,
        ):
            mock_settings.litellm_url = "http://localhost:4000"

            # WHEN: Call get_llm_config
            result = await service.get_llm_config()

            # THEN: Models are None
            assert result.embedding_model is None
            assert result.generation_model is None
            assert result.litellm_base_url == "http://localhost:4000"


class TestConfigServiceUpdateLLMConfig:
    """Tests for ConfigService.update_llm_config method (AC-7.2.2)."""

    @pytest.mark.asyncio
    async def test_update_llm_config_updates_embedding_model(self):
        """
        GIVEN: ConfigService with existing embedding model
        WHEN: update_llm_config is called with new embedding_model_id
        THEN: Default embedding model is updated
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        new_model_id = uuid4()
        mock_new_model = MagicMock(spec=LLMModel)
        mock_new_model.id = new_model_id
        mock_new_model.type = ModelType.EMBEDDING.value
        mock_new_model.is_default = False
        mock_new_model.config = {"dimensions": 768}
        mock_new_model.name = "New Embedding"
        mock_new_model.provider = "openai"
        mock_new_model.model_id = "text-embedding-3"
        mock_new_model.api_endpoint = None
        mock_new_model.status = "active"

        # Mock multiple query results using side_effect
        def mock_execute(query):
            result = MagicMock()
            # Return model for most queries
            result.scalar_one_or_none.return_value = mock_new_model
            result.all.return_value = []  # For KB queries
            return result

        mock_session.execute.side_effect = mock_execute

        mock_redis = AsyncMock()
        # Return cached config for get_llm_config at end
        mock_redis.get.return_value = json.dumps(
            {
                "embedding_model": {
                    "model_id": str(new_model_id),
                    "name": "New Embedding",
                    "provider": "openai",
                    "model_identifier": "text-embedding-3",
                    "api_endpoint": None,
                    "is_default": True,
                    "status": "active",
                },
                "generation_model": None,
                "generation_settings": {
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "top_p": 1.0,
                },
                "litellm_base_url": "http://localhost:4000",
                "last_modified": None,
                "last_modified_by": None,
            }
        )

        request = LLMConfigUpdateRequest(embedding_model_id=new_model_id)

        with (
            patch(
                "app.services.config_service.get_redis_client",
                return_value=mock_redis,
            ),
            patch("app.services.config_service.settings") as mock_settings,
        ):
            mock_settings.litellm_url = "http://localhost:4000"

            # WHEN: Call update_llm_config
            result = await service.update_llm_config(request, "admin@test.com")

            # THEN: Returns response with hot_reload_applied
            assert isinstance(result, LLMConfigUpdateResponse)
            assert result.hot_reload_applied is True
            mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_update_llm_config_updates_generation_model(self):
        """
        GIVEN: ConfigService with existing generation model
        WHEN: update_llm_config is called with new generation_model_id
        THEN: Default generation model is updated
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        new_model_id = uuid4()
        mock_new_model = MagicMock(spec=LLMModel)
        mock_new_model.id = new_model_id
        mock_new_model.type = ModelType.GENERATION.value
        mock_new_model.is_default = False
        mock_new_model.name = "New Generation"
        mock_new_model.provider = "openai"
        mock_new_model.model_id = "gpt-4"
        mock_new_model.api_endpoint = None
        mock_new_model.status = "active"

        # Mock multiple query results using side_effect
        def mock_execute(query):
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_new_model
            result.all.return_value = []
            return result

        mock_session.execute.side_effect = mock_execute

        mock_redis = AsyncMock()
        # Return cached config for get_llm_config at end
        mock_redis.get.return_value = json.dumps(
            {
                "embedding_model": None,
                "generation_model": {
                    "model_id": str(new_model_id),
                    "name": "New Generation",
                    "provider": "openai",
                    "model_identifier": "gpt-4",
                    "api_endpoint": None,
                    "is_default": True,
                    "status": "active",
                },
                "generation_settings": {
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "top_p": 1.0,
                },
                "litellm_base_url": "http://localhost:4000",
                "last_modified": None,
                "last_modified_by": None,
            }
        )

        request = LLMConfigUpdateRequest(generation_model_id=new_model_id)

        with (
            patch(
                "app.services.config_service.get_redis_client",
                return_value=mock_redis,
            ),
            patch("app.services.config_service.settings") as mock_settings,
        ):
            mock_settings.litellm_url = "http://localhost:4000"

            # WHEN: Call update_llm_config
            result = await service.update_llm_config(request, "admin@test.com")

            # THEN: Returns response with hot_reload_applied
            assert result.hot_reload_applied is True

    @pytest.mark.asyncio
    async def test_update_llm_config_updates_generation_settings(self):
        """
        GIVEN: ConfigService
        WHEN: update_llm_config is called with new generation_settings
        THEN: Generation settings are updated in SystemConfig
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        # No existing settings
        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = config_result

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        new_settings = LLMConfigSettings(temperature=0.5, max_tokens=4096, top_p=0.9)
        request = LLMConfigUpdateRequest(generation_settings=new_settings)

        with (
            patch(
                "app.services.config_service.get_redis_client",
                return_value=mock_redis,
            ),
            patch("app.services.config_service.settings") as mock_settings,
        ):
            mock_settings.litellm_url = "http://localhost:4000"

            # WHEN: Call update_llm_config
            result = await service.update_llm_config(request, "admin@test.com")

            # THEN: Settings are saved
            assert result.hot_reload_applied is True
            mock_session.add.assert_called()  # New SystemConfig created

    @pytest.mark.asyncio
    async def test_update_llm_config_invalidates_cache(self):
        """
        GIVEN: ConfigService with cached config
        WHEN: update_llm_config is called
        THEN: Redis cache is invalidated
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = config_result

        request = LLMConfigUpdateRequest(
            generation_settings=LLMConfigSettings(temperature=0.8)
        )

        with (
            patch(
                "app.services.config_service.get_redis_client",
                return_value=mock_redis,
            ),
            patch("app.services.config_service.settings") as mock_settings,
        ):
            mock_settings.litellm_url = "http://localhost:4000"

            # WHEN: Call update_llm_config
            await service.update_llm_config(request, "admin@test.com")

            # THEN: Cache is deleted
            mock_redis.delete.assert_called_with(ConfigService.LLM_CONFIG_CACHE_KEY)

    @pytest.mark.asyncio
    async def test_update_llm_config_publishes_hot_reload_event(self):
        """
        GIVEN: ConfigService
        WHEN: update_llm_config is called
        THEN: Redis pub/sub message is published for hot-reload
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = config_result

        request = LLMConfigUpdateRequest(
            generation_settings=LLMConfigSettings(temperature=0.6)
        )

        with (
            patch(
                "app.services.config_service.get_redis_client",
                return_value=mock_redis,
            ),
            patch("app.services.config_service.settings") as mock_settings,
        ):
            mock_settings.litellm_url = "http://localhost:4000"

            # WHEN: Call update_llm_config
            await service.update_llm_config(request, "admin@test.com")

            # THEN: Pub/sub message is published
            mock_redis.publish.assert_called_once()
            call_args = mock_redis.publish.call_args
            assert call_args[0][0] == ConfigService.LLM_CONFIG_CHANNEL

    @pytest.mark.asyncio
    async def test_update_llm_config_raises_on_invalid_embedding_model(self):
        """
        GIVEN: ConfigService
        WHEN: update_llm_config is called with non-existent embedding_model_id
        THEN: Raises ValueError
        """
        # GIVEN: Mock session with no model
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        model_result = MagicMock()
        model_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = model_result

        request = LLMConfigUpdateRequest(embedding_model_id=uuid4())

        with patch(
            "app.services.config_service.get_redis_client",
            return_value=AsyncMock(),
        ):
            # WHEN/THEN: Raises ValueError
            with pytest.raises(ValueError) as exc:
                await service.update_llm_config(request, "admin@test.com")

            assert "not found" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_update_llm_config_raises_on_wrong_model_type(self):
        """
        GIVEN: ConfigService
        WHEN: update_llm_config is called with generation model as embedding
        THEN: Raises ValueError
        """
        # GIVEN: Mock session with wrong model type
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        mock_model = MagicMock(spec=LLMModel)
        mock_model.id = uuid4()
        mock_model.type = ModelType.GENERATION.value  # Wrong type

        model_result = MagicMock()
        model_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = model_result

        request = LLMConfigUpdateRequest(embedding_model_id=mock_model.id)

        with patch(
            "app.services.config_service.get_redis_client",
            return_value=AsyncMock(),
        ):
            # WHEN/THEN: Raises ValueError
            with pytest.raises(ValueError) as exc:
                await service.update_llm_config(request, "admin@test.com")

            assert "not an embedding model" in str(exc.value).lower()


class TestConfigServiceCheckDimensionMismatch:
    """Tests for ConfigService._check_dimension_mismatch method (AC-7.2.3)."""

    @pytest.mark.asyncio
    async def test_check_dimension_mismatch_returns_warning_on_mismatch(self):
        """
        GIVEN: Current embedding model with different dimensions than new model
        WHEN: _check_dimension_mismatch is called
        THEN: Returns DimensionMismatchWarning with details
        """
        # GIVEN: Mock session with KBs
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        current_model = MagicMock(spec=LLMModel)
        current_model.config = {"dimensions": 1536}

        new_model = MagicMock(spec=LLMModel)
        new_model.config = {"dimensions": 768}

        # Mock KB query
        kb_result = MagicMock()
        kb_result.all.return_value = [("KB 1",), ("KB 2",)]
        mock_session.execute.return_value = kb_result

        # WHEN: Check dimension mismatch
        result = await service._check_dimension_mismatch(current_model, new_model)

        # THEN: Returns warning
        assert isinstance(result, DimensionMismatchWarning)
        assert result.has_mismatch is True
        assert result.current_dimensions == 1536
        assert result.new_dimensions == 768
        assert len(result.affected_kbs) == 2
        assert "re-indexing" in result.warning_message.lower()

    @pytest.mark.asyncio
    async def test_check_dimension_mismatch_returns_none_when_same(self):
        """
        GIVEN: Current and new embedding models with same dimensions
        WHEN: _check_dimension_mismatch is called
        THEN: Returns None (no warning)
        """
        # GIVEN: Models with same dimensions
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        current_model = MagicMock(spec=LLMModel)
        current_model.config = {"dimensions": 768}

        new_model = MagicMock(spec=LLMModel)
        new_model.config = {"dimensions": 768}

        # WHEN: Check dimension mismatch
        result = await service._check_dimension_mismatch(current_model, new_model)

        # THEN: Returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_check_dimension_mismatch_returns_none_when_no_current_model(self):
        """
        GIVEN: No current embedding model configured
        WHEN: _check_dimension_mismatch is called
        THEN: Returns None (no warning)
        """
        # GIVEN: No current model
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        new_model = MagicMock(spec=LLMModel)
        new_model.config = {"dimensions": 768}

        # WHEN: Check dimension mismatch
        result = await service._check_dimension_mismatch(None, new_model)

        # THEN: Returns None
        assert result is None


class TestConfigServiceTestModelHealth:
    """Tests for ConfigService.test_model_health method (AC-7.2.4)."""

    @pytest.mark.asyncio
    async def test_test_model_health_returns_healthy_status(self):
        """
        GIVEN: ConfigService with healthy default models
        WHEN: test_model_health is called
        THEN: Returns healthy status for all models
        """
        # GIVEN: Mock session and services
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        mock_embedding_model = MagicMock(spec=LLMModel)
        mock_embedding_model.name = "Embedding Model"

        mock_generation_model = MagicMock(spec=LLMModel)
        mock_generation_model.name = "Generation Model"

        mock_test_result = MagicMock()
        mock_test_result.success = True
        mock_test_result.latency_ms = 150.5
        mock_test_result.message = "Success"

        # Patch at source locations since they're imported locally in the method
        with (
            patch(
                "app.services.model_registry_service.ModelRegistryService"
            ) as MockRegistry,
            patch(
                "app.services.model_connection_tester.test_model_connection",
                return_value=mock_test_result,
            ),
        ):
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_default_model.side_effect = [
                mock_embedding_model,
                mock_generation_model,
            ]
            MockRegistry.return_value = mock_registry_instance

            # WHEN: Test model health
            result = await service.test_model_health()

            # THEN: Returns healthy status
            assert isinstance(result, LLMHealthResponse)
            assert result.overall_healthy is True
            assert result.embedding_health.is_healthy is True
            assert result.generation_health.is_healthy is True
            assert result.embedding_health.latency_ms == 150.5

    @pytest.mark.asyncio
    async def test_test_model_health_returns_unhealthy_on_failure(self):
        """
        GIVEN: ConfigService with unhealthy embedding model
        WHEN: test_model_health is called
        THEN: Returns unhealthy status with error message
        """
        # GIVEN: Mock session and services
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        mock_embedding_model = MagicMock(spec=LLMModel)
        mock_embedding_model.name = "Embedding Model"

        mock_test_result = MagicMock()
        mock_test_result.success = False
        mock_test_result.latency_ms = 5000.0
        mock_test_result.message = "Connection timeout"

        # Patch at source locations since they're imported locally in the method
        with (
            patch(
                "app.services.model_registry_service.ModelRegistryService"
            ) as MockRegistry,
            patch(
                "app.services.model_connection_tester.test_model_connection",
                return_value=mock_test_result,
            ),
        ):
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_default_model.side_effect = [
                mock_embedding_model,
                None,  # No generation model
            ]
            MockRegistry.return_value = mock_registry_instance

            # WHEN: Test model health
            result = await service.test_model_health()

            # THEN: Returns unhealthy status
            assert result.overall_healthy is False
            assert result.embedding_health.is_healthy is False
            assert result.embedding_health.error_message == "Connection timeout"

    @pytest.mark.asyncio
    async def test_test_model_health_filters_by_type(self):
        """
        GIVEN: ConfigService
        WHEN: test_model_health is called with model_type filter
        THEN: Only tests specified model type
        """
        # GIVEN: Mock session and services
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        mock_embedding_model = MagicMock(spec=LLMModel)
        mock_embedding_model.name = "Embedding Model"

        mock_test_result = MagicMock()
        mock_test_result.success = True
        mock_test_result.latency_ms = 100.0
        mock_test_result.message = "Success"

        # Patch at source locations since they're imported locally in the method
        with (
            patch(
                "app.services.model_registry_service.ModelRegistryService"
            ) as MockRegistry,
            patch(
                "app.services.model_connection_tester.test_model_connection",
                return_value=mock_test_result,
            ),
        ):
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_default_model.return_value = mock_embedding_model
            MockRegistry.return_value = mock_registry_instance

            # WHEN: Test only embedding health
            result = await service.test_model_health(model_type="embedding")

            # THEN: Only embedding tested
            assert result.embedding_health is not None
            assert result.generation_health is None
            mock_registry_instance.get_default_model.assert_called_once_with(
                "embedding"
            )

    @pytest.mark.asyncio
    async def test_test_model_health_handles_no_models(self):
        """
        GIVEN: ConfigService with no default models configured
        WHEN: test_model_health is called
        THEN: Returns healthy (no models to fail)
        """
        # GIVEN: Mock session with no models
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        # Patch at source locations since they're imported locally in the method
        with patch(
            "app.services.model_registry_service.ModelRegistryService"
        ) as MockRegistry:
            mock_registry_instance = AsyncMock()
            mock_registry_instance.get_default_model.return_value = None
            MockRegistry.return_value = mock_registry_instance

            # WHEN: Test model health
            result = await service.test_model_health()

            # THEN: Returns healthy (no failures)
            assert result.overall_healthy is True
            assert result.embedding_health is None
            assert result.generation_health is None


class TestConfigServiceModelToConfigInfo:
    """Tests for ConfigService._model_to_config_info helper method."""

    def test_model_to_config_info_converts_correctly(self):
        """
        GIVEN: LLMModel instance
        WHEN: _model_to_config_info is called
        THEN: Returns LLMConfigModelInfo with correct fields
        """
        # GIVEN: Mock session and model
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        model_id = uuid4()
        mock_model = MagicMock(spec=LLMModel)
        mock_model.id = model_id
        mock_model.name = "Test Model"
        mock_model.provider = "openai"
        mock_model.model_id = "gpt-4"
        mock_model.api_endpoint = "https://api.openai.com"
        mock_model.is_default = True
        mock_model.status = "active"

        # WHEN: Convert
        result = service._model_to_config_info(mock_model)

        # THEN: Returns correct info
        assert isinstance(result, LLMConfigModelInfo)
        assert result.model_id == model_id
        assert result.name == "Test Model"
        assert result.provider == "openai"
        assert result.model_identifier == "gpt-4"
        assert result.api_endpoint == "https://api.openai.com"
        assert result.is_default is True
        assert result.status == "active"


class TestConfigServiceGetGenerationSettings:
    """Tests for ConfigService._get_generation_settings helper method."""

    @pytest.mark.asyncio
    async def test_get_generation_settings_returns_stored_settings(self):
        """
        GIVEN: ConfigService with stored generation settings
        WHEN: _get_generation_settings is called
        THEN: Returns stored settings
        """
        # GIVEN: Mock session with stored config
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        mock_config = MagicMock()
        mock_config.value = {
            "generation_settings": {
                "temperature": 0.5,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        }

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config
        mock_session.execute.return_value = config_result

        # WHEN: Get settings
        result = await service._get_generation_settings()

        # THEN: Returns stored settings
        assert isinstance(result, LLMConfigSettings)
        assert result.temperature == 0.5
        assert result.max_tokens == 4096
        assert result.top_p == 0.95

    @pytest.mark.asyncio
    async def test_get_generation_settings_returns_defaults_when_not_stored(self):
        """
        GIVEN: ConfigService with no stored generation settings
        WHEN: _get_generation_settings is called
        THEN: Returns default settings
        """
        # GIVEN: Mock session with no config
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = config_result

        # WHEN: Get settings
        result = await service._get_generation_settings()

        # THEN: Returns defaults
        assert result.temperature == 0.7
        assert result.max_tokens == 2048
        assert result.top_p == 1.0


class TestLLMConfigSchemas:
    """Tests for LLM configuration Pydantic schemas."""

    def test_llm_config_settings_validation(self):
        """
        GIVEN: LLMConfigSettings schema
        WHEN: Created with valid values
        THEN: Validates and creates correctly
        """
        # WHEN: Create settings
        settings = LLMConfigSettings(temperature=0.8, max_tokens=1024, top_p=0.9)

        # THEN: Values are correct
        assert settings.temperature == 0.8
        assert settings.max_tokens == 1024
        assert settings.top_p == 0.9

    def test_llm_config_settings_defaults(self):
        """
        GIVEN: LLMConfigSettings schema
        WHEN: Created without values
        THEN: Uses defaults
        """
        # WHEN: Create with defaults
        settings = LLMConfigSettings()

        # THEN: Defaults are used
        assert settings.temperature == 0.7
        assert settings.max_tokens == 2048
        assert settings.top_p == 1.0

    def test_llm_config_settings_temperature_range(self):
        """
        GIVEN: LLMConfigSettings schema
        WHEN: Created with out-of-range temperature
        THEN: Raises validation error
        """
        from pydantic import ValidationError

        # WHEN/THEN: Invalid temperature raises error
        with pytest.raises(ValidationError):
            LLMConfigSettings(temperature=2.5)  # Max is 2.0

    def test_dimension_mismatch_warning_schema(self):
        """
        GIVEN: DimensionMismatchWarning schema
        WHEN: Created with mismatch data
        THEN: Contains correct warning information
        """
        # WHEN: Create warning
        warning = DimensionMismatchWarning(
            has_mismatch=True,
            current_dimensions=1536,
            new_dimensions=768,
            affected_kbs=["KB 1", "KB 2"],
            warning_message="Dimension mismatch detected",
        )

        # THEN: Values are correct
        assert warning.has_mismatch is True
        assert warning.current_dimensions == 1536
        assert warning.new_dimensions == 768
        assert len(warning.affected_kbs) == 2

    def test_model_health_status_schema(self):
        """
        GIVEN: ModelHealthStatus schema
        WHEN: Created with health data
        THEN: Contains correct status information
        """
        # WHEN: Create status
        status = ModelHealthStatus(
            model_type="embedding",
            model_name="text-embedding-3-small",
            is_healthy=True,
            latency_ms=125.5,
            error_message=None,
            last_checked=datetime.now(UTC),
        )

        # THEN: Values are correct
        assert status.model_type == "embedding"
        assert status.is_healthy is True
        assert status.latency_ms == 125.5
        assert status.error_message is None


class TestConfigServiceCacheKeys:
    """Tests for ConfigService cache key constants."""

    def test_llm_config_cache_key_defined(self):
        """
        GIVEN: ConfigService class
        WHEN: Checking cache constants
        THEN: LLM config cache key is defined
        """
        assert ConfigService.LLM_CONFIG_CACHE_KEY == "admin:config:llm"

    def test_llm_config_cache_ttl_is_short_for_hot_reload(self):
        """
        GIVEN: ConfigService class
        WHEN: Checking cache TTL
        THEN: LLM config TTL is short (30s) for hot-reload responsiveness
        """
        assert ConfigService.LLM_CONFIG_CACHE_TTL == 30  # 30 seconds

    def test_llm_config_channel_defined(self):
        """
        GIVEN: ConfigService class
        WHEN: Checking pub/sub channel
        THEN: LLM config channel is defined for hot-reload
        """
        assert ConfigService.LLM_CONFIG_CHANNEL == "llm:config:updated"


class TestConfigServiceRewriterModel:
    """Tests for ConfigService rewriter model methods (Story 8-0)."""

    @pytest.mark.asyncio
    async def test_get_rewriter_model_id_returns_none_when_not_set(self):
        """
        GIVEN: ConfigService with no rewriter model configured
        WHEN: get_rewriter_model_id is called
        THEN: Returns None
        """
        # GIVEN: Mock session with no config record
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = config_result

        # WHEN: Get rewriter model ID
        result = await service.get_rewriter_model_id()

        # THEN: Returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_get_rewriter_model_id_returns_uuid_when_set(self):
        """
        GIVEN: ConfigService with rewriter model configured
        WHEN: get_rewriter_model_id is called
        THEN: Returns the stored UUID
        """
        # GIVEN: Mock session with config record
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        model_uuid = uuid4()
        mock_config = MagicMock()
        mock_config.value = str(model_uuid)

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config
        mock_session.execute.return_value = config_result

        # WHEN: Get rewriter model ID
        result = await service.get_rewriter_model_id()

        # THEN: Returns the UUID
        assert result == model_uuid

    @pytest.mark.asyncio
    async def test_get_rewriter_model_id_returns_none_on_invalid_uuid(self):
        """
        GIVEN: ConfigService with invalid UUID stored
        WHEN: get_rewriter_model_id is called
        THEN: Returns None and logs warning
        """
        # GIVEN: Mock session with invalid UUID
        mock_session = AsyncMock()
        service = ConfigService(mock_session)

        mock_config = MagicMock()
        mock_config.value = "not-a-valid-uuid"

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config
        mock_session.execute.return_value = config_result

        # WHEN: Get rewriter model ID
        result = await service.get_rewriter_model_id()

        # THEN: Returns None (gracefully handles invalid data)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_rewriter_model_id_stores_uuid(self):
        """
        GIVEN: ConfigService
        WHEN: set_rewriter_model_id is called with valid model UUID
        THEN: Stores the UUID in SystemConfig
        """
        # GIVEN: Mock session with valid generation model
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        model_uuid = uuid4()
        mock_model = MagicMock(spec=LLMModel)
        mock_model.id = model_uuid
        mock_model.type = ModelType.GENERATION.value
        mock_model.name = "Test Generation Model"

        # First query returns the model, second returns no existing config
        model_result = MagicMock()
        model_result.scalar_one_or_none.return_value = mock_model

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [model_result, config_result]

        mock_redis = AsyncMock()

        with patch(
            "app.services.config_service.get_redis_client",
            return_value=mock_redis,
        ):
            # WHEN: Set rewriter model ID
            await service.set_rewriter_model_id(model_uuid, "admin@test.com")

            # THEN: SystemConfig is created
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_rewriter_model_id_clears_when_none(self):
        """
        GIVEN: ConfigService with existing rewriter model
        WHEN: set_rewriter_model_id is called with None
        THEN: Updates the config to None value
        """
        # GIVEN: Mock session with existing config
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        mock_config = MagicMock()
        mock_config.value = str(uuid4())

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config
        mock_session.execute.return_value = config_result

        mock_redis = AsyncMock()

        with patch(
            "app.services.config_service.get_redis_client",
            return_value=mock_redis,
        ):
            # WHEN: Set rewriter model ID to None
            await service.set_rewriter_model_id(None, "admin@test.com")

            # THEN: Config is updated (not deleted - update sets value to None)
            # Second execute call is the update statement
            assert mock_session.execute.call_count == 2
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_rewriter_model_id_raises_on_invalid_model(self):
        """
        GIVEN: ConfigService
        WHEN: set_rewriter_model_id is called with non-existent model UUID
        THEN: Raises ValueError
        """
        # GIVEN: Mock session with no model
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        model_result = MagicMock()
        model_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = model_result

        # WHEN/THEN: Raises ValueError
        with pytest.raises(ValueError) as exc:
            await service.set_rewriter_model_id(uuid4(), "admin@test.com")

        assert "not found" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_set_rewriter_model_id_raises_on_wrong_type(self):
        """
        GIVEN: ConfigService
        WHEN: set_rewriter_model_id is called with embedding model UUID
        THEN: Raises ValueError (must be generation type)
        """
        # GIVEN: Mock session with embedding model
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        model_uuid = uuid4()
        mock_model = MagicMock(spec=LLMModel)
        mock_model.id = model_uuid
        mock_model.type = ModelType.EMBEDDING.value  # Wrong type
        mock_model.name = "Embedding Model"

        model_result = MagicMock()
        model_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = model_result

        # WHEN/THEN: Raises ValueError
        with pytest.raises(ValueError) as exc:
            await service.set_rewriter_model_id(model_uuid, "admin@test.com")

        assert "generation" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_set_rewriter_model_id_invalidates_cache(self):
        """
        GIVEN: ConfigService with cached config
        WHEN: set_rewriter_model_id is called
        THEN: Cache is invalidated
        """
        # GIVEN: Mock session with valid generation model
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        model_uuid = uuid4()
        mock_model = MagicMock(spec=LLMModel)
        mock_model.id = model_uuid
        mock_model.type = ModelType.GENERATION.value
        mock_model.name = "Test Model"

        model_result = MagicMock()
        model_result.scalar_one_or_none.return_value = mock_model

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [model_result, config_result]

        mock_redis = AsyncMock()

        with patch(
            "app.services.config_service.get_redis_client",
            return_value=mock_redis,
        ):
            # WHEN: Set rewriter model ID
            await service.set_rewriter_model_id(model_uuid, "admin@test.com")

            # THEN: Cache is invalidated
            mock_redis.delete.assert_called()

    @pytest.mark.asyncio
    async def test_set_rewriter_model_id_updates_existing_config(self):
        """
        GIVEN: ConfigService with existing rewriter model config
        WHEN: set_rewriter_model_id is called with new UUID
        THEN: Updates the existing config record (not creates new)
        """
        # GIVEN: Mock session with existing config and valid model
        mock_session = AsyncMock()
        service = ConfigService(mock_session)
        service.audit_service = AsyncMock()

        old_uuid = uuid4()
        new_uuid = uuid4()

        mock_model = MagicMock(spec=LLMModel)
        mock_model.id = new_uuid
        mock_model.type = ModelType.GENERATION.value
        mock_model.name = "New Model"

        mock_config = MagicMock()
        mock_config.value = str(old_uuid)

        model_result = MagicMock()
        model_result.scalar_one_or_none.return_value = mock_model

        config_result = MagicMock()
        config_result.scalar_one_or_none.return_value = mock_config

        update_result = MagicMock()  # Result of update statement

        # 1) model lookup, 2) config lookup, 3) update statement
        mock_session.execute.side_effect = [model_result, config_result, update_result]

        mock_redis = AsyncMock()

        with patch(
            "app.services.config_service.get_redis_client",
            return_value=mock_redis,
        ):
            # WHEN: Set rewriter model ID
            await service.set_rewriter_model_id(new_uuid, "admin@test.com")

            # THEN: Existing config is updated via UPDATE statement (not add)
            mock_session.add.assert_not_called()
            assert mock_session.execute.call_count == 3  # model + config + update
            mock_session.commit.assert_called_once()
