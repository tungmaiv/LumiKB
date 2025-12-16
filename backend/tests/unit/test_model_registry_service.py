"""Unit tests for ModelRegistryService.

Story 7-9: LLM Model Registry (AC-7.9.1 through AC-7.9.11)

Test Coverage:
- [P0] list_models: Pagination, filters, total count
- [P0] get_model: Retrieve by ID
- [P0] create_model: Create with validation and encryption
- [P0] update_model: Update fields with encryption
- [P0] delete_model: Delete model
- [P1] set_default: Set default model for type
- [P1] get_default_model: Get default for type
- [P1] API key encryption/decryption
- [P2] Config validation for embedding vs generation

Knowledge Base References:
- test-quality.md: Given-When-Then structure
- test-levels-framework.md: Unit test characteristics
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.llm_model import LLMModel
from app.schemas.llm_model import LLMModelCreate, LLMModelUpdate
from app.services.model_registry_service import (
    ModelNotFoundError,
    ModelRegistryService,
    ModelValidationError,
    decrypt_api_key,
    encrypt_api_key,
    validate_model_config,
)


class TestModelRegistryServiceListModels:
    """Tests for ModelRegistryService.list_models method."""

    @pytest.mark.asyncio
    async def test_list_models_returns_all_models(self):
        """
        GIVEN: ModelRegistryService with models in database
        WHEN: list_models is called without filters
        THEN: All models are returned with total count
        """
        # GIVEN: Mock session with models
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_models = [
            MagicMock(spec=LLMModel, id=uuid4(), name="Model 1", type="embedding"),
            MagicMock(spec=LLMModel, id=uuid4(), name="Model 2", type="generation"),
        ]

        # Setup mock execute results - count query first, then list query
        mock_count_result = MagicMock()
        mock_count_result.all.return_value = [MagicMock(), MagicMock()]

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = mock_models

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # WHEN: Call list_models
        models, total = await service.list_models(skip=0, limit=20)

        # THEN: Returns models and total count
        assert len(models) == 2
        assert total == 2
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_list_models_with_type_filter(self):
        """
        GIVEN: ModelRegistryService with multiple model types
        WHEN: list_models is called with type filter
        THEN: Only models of specified type are returned
        """
        # GIVEN: Mock session
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_models = [
            MagicMock(spec=LLMModel, type="embedding"),
        ]

        mock_count_result = MagicMock()
        mock_count_result.all.return_value = [MagicMock()]

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = mock_models

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # WHEN: Call list_models with type filter
        models, total = await service.list_models(model_type="embedding")

        # THEN: Returns filtered results
        assert len(models) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_list_models_with_provider_filter(self):
        """
        GIVEN: ModelRegistryService with multiple providers
        WHEN: list_models is called with provider filter
        THEN: Only models of specified provider are returned
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_models = [MagicMock(spec=LLMModel, provider="openai")]

        mock_count_result = MagicMock()
        mock_count_result.all.return_value = [MagicMock()]

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = mock_models

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # WHEN: Filter by provider
        models, total = await service.list_models(provider="openai")

        # THEN: Returns filtered results
        assert len(models) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_list_models_with_status_filter(self):
        """
        GIVEN: ModelRegistryService with models of different statuses
        WHEN: list_models is called with status filter
        THEN: Only models with specified status are returned
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_models = [MagicMock(spec=LLMModel, status="active")]

        mock_count_result = MagicMock()
        mock_count_result.all.return_value = [MagicMock()]

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = mock_models

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # WHEN: Filter by status
        models, total = await service.list_models(status="active")

        # THEN: Returns filtered results
        assert len(models) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_list_models_pagination(self):
        """
        GIVEN: ModelRegistryService with many models
        WHEN: list_models is called with skip and limit
        THEN: Returns paginated results with correct total
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_models = [MagicMock(spec=LLMModel) for _ in range(10)]

        mock_count_result = MagicMock()
        mock_count_result.all.return_value = [MagicMock() for _ in range(50)]

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = mock_models

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # WHEN: Call with pagination
        models, total = await service.list_models(skip=10, limit=10)

        # THEN: Returns correct page with total count
        assert len(models) == 10
        assert total == 50

    @pytest.mark.asyncio
    async def test_list_models_empty_result(self):
        """
        GIVEN: ModelRegistryService with no models
        WHEN: list_models is called
        THEN: Returns empty list with zero count
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_count_result = MagicMock()
        mock_count_result.all.return_value = []

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_list_result]

        # WHEN: Call list_models
        models, total = await service.list_models()

        # THEN: Returns empty results
        assert models == []
        assert total == 0


class TestModelRegistryServiceGetModel:
    """Tests for ModelRegistryService.get_model method."""

    @pytest.mark.asyncio
    async def test_get_model_returns_model(self):
        """
        GIVEN: ModelRegistryService with model in database
        WHEN: get_model is called with valid ID
        THEN: Returns the model
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        model_id = uuid4()
        mock_model = MagicMock(spec=LLMModel, id=model_id, name="Test Model")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        # WHEN: Call get_model
        result = await service.get_model(model_id)

        # THEN: Returns the model
        assert result == mock_model
        assert result.id == model_id

    @pytest.mark.asyncio
    async def test_get_model_not_found_raises_error(self):
        """
        GIVEN: ModelRegistryService with no matching model
        WHEN: get_model is called with non-existent ID
        THEN: Raises ModelNotFoundError
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # WHEN/THEN: get_model raises error
        with pytest.raises(ModelNotFoundError) as exc:
            await service.get_model(uuid4())

        assert "not found" in str(exc.value).lower()


class TestModelRegistryServiceCreateModel:
    """Tests for ModelRegistryService.create_model method."""

    @pytest.mark.asyncio
    async def test_create_model_embedding_success(self):
        """
        GIVEN: ModelRegistryService
        WHEN: create_model is called with valid embedding data
        THEN: Model is created and returned
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        create_data = LLMModelCreate(
            type="embedding",
            provider="openai",
            name="text-embedding-3-small",
            model_id="text-embedding-3-small",
            config={
                "dimensions": 1536,
                "max_tokens": 8191,
                "normalize": True,
                "distance_metric": "cosine",
                "batch_size": 100,
                "tags": [],
            },
            is_default=False,
        )

        # WHEN: Create model
        result = await service.create_model(create_data)

        # THEN: Model is added and committed
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_model_generation_success(self):
        """
        GIVEN: ModelRegistryService
        WHEN: create_model is called with valid generation data
        THEN: Model is created with generation config
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        create_data = LLMModelCreate(
            type="generation",
            provider="anthropic",
            name="Claude 3.5 Sonnet",
            model_id="claude-3-5-sonnet-20241022",
            config={
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
            is_default=False,
        )

        # WHEN: Create model
        await service.create_model(create_data)

        # THEN: Model is added
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_model_with_api_key_encrypts(self):
        """
        GIVEN: ModelRegistryService
        WHEN: create_model is called with API key
        THEN: API key is encrypted before storage
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        create_data = LLMModelCreate(
            type="embedding",
            provider="openai",
            name="Test Model",
            model_id="test-model",
            config={
                "dimensions": 1536,
                "max_tokens": 8191,
                "normalize": True,
                "distance_metric": "cosine",
                "batch_size": 100,
                "tags": [],
            },
            api_key="sk-test-key-12345",
            is_default=False,
        )

        # WHEN: Create model
        await service.create_model(create_data)

        # THEN: Model is created (API key encrypted internally)
        mock_session.add.assert_called_once()
        # Verify the model that was added has encrypted key
        added_model = mock_session.add.call_args[0][0]
        assert added_model.api_key_encrypted is not None
        # Encrypted key should not equal plaintext
        assert added_model.api_key_encrypted != b"sk-test-key-12345"

    @pytest.mark.asyncio
    async def test_create_model_as_default_clears_existing(self):
        """
        GIVEN: ModelRegistryService with existing default
        WHEN: create_model is called with is_default=True
        THEN: Existing default is cleared before creating new default
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        create_data = LLMModelCreate(
            type="embedding",
            provider="openai",
            name="New Default",
            model_id="new-default",
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

        # WHEN: Create as default
        await service.create_model(create_data)

        # THEN: Execute called for clearing default + add + commit
        # At least 1 execute for clearing default
        assert mock_session.execute.call_count >= 1


class TestModelRegistryServiceUpdateModel:
    """Tests for ModelRegistryService.update_model method."""

    @pytest.mark.asyncio
    async def test_update_model_name_success(self):
        """
        GIVEN: ModelRegistryService with existing model
        WHEN: update_model is called with new name
        THEN: Model name is updated
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        model_id = uuid4()
        mock_model = MagicMock(
            spec=LLMModel,
            id=model_id,
            name="Old Name",
            type="embedding",
            is_default=False,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        update_data = LLMModelUpdate(name="New Name")

        # WHEN: Update model
        result = await service.update_model(model_id, update_data)

        # THEN: Name is updated
        assert mock_model.name == "New Name"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_model_status_success(self):
        """
        GIVEN: ModelRegistryService with existing model
        WHEN: update_model is called with new status
        THEN: Model status is updated
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        model_id = uuid4()
        mock_model = MagicMock(
            spec=LLMModel,
            id=model_id,
            status="active",
            type="embedding",
            is_default=False,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        update_data = LLMModelUpdate(status="inactive")

        # WHEN: Update status
        await service.update_model(model_id, update_data)

        # THEN: Status is updated
        assert mock_model.status == "inactive"

    @pytest.mark.asyncio
    async def test_update_model_api_key_encrypts(self):
        """
        GIVEN: ModelRegistryService with existing model
        WHEN: update_model is called with new API key
        THEN: New API key is encrypted
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        model_id = uuid4()
        mock_model = MagicMock(
            spec=LLMModel,
            id=model_id,
            type="embedding",
            is_default=False,
            api_key_encrypted=None,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        update_data = LLMModelUpdate(api_key="new-api-key")

        # WHEN: Update API key
        await service.update_model(model_id, update_data)

        # THEN: API key is encrypted
        assert mock_model.api_key_encrypted is not None
        assert mock_model.api_key_encrypted != b"new-api-key"

    @pytest.mark.asyncio
    async def test_update_model_not_found_raises_error(self):
        """
        GIVEN: ModelRegistryService with no matching model
        WHEN: update_model is called
        THEN: Raises ModelNotFoundError
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        update_data = LLMModelUpdate(name="New Name")

        # WHEN/THEN: Raises error
        with pytest.raises(ModelNotFoundError):
            await service.update_model(uuid4(), update_data)


class TestModelRegistryServiceDeleteModel:
    """Tests for ModelRegistryService.delete_model method."""

    @pytest.mark.asyncio
    async def test_delete_model_success(self):
        """
        GIVEN: ModelRegistryService with existing model
        WHEN: delete_model is called
        THEN: Model is deleted
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        model_id = uuid4()
        mock_model = MagicMock(
            spec=LLMModel,
            id=model_id,
            name="Test Model",
            type="embedding",
            provider="openai",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        # WHEN: Delete model
        await service.delete_model(model_id)

        # THEN: Model is deleted
        mock_session.delete.assert_called_once_with(mock_model)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_model_not_found_raises_error(self):
        """
        GIVEN: ModelRegistryService with no matching model
        WHEN: delete_model is called
        THEN: Raises ModelNotFoundError
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # WHEN/THEN: Raises error
        with pytest.raises(ModelNotFoundError):
            await service.delete_model(uuid4())


class TestModelRegistryServiceSetDefault:
    """Tests for ModelRegistryService.set_default method."""

    @pytest.mark.asyncio
    async def test_set_default_success(self):
        """
        GIVEN: ModelRegistryService with model
        WHEN: set_default is called
        THEN: Model is marked as default, others cleared
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        model_id = uuid4()
        mock_model = MagicMock(
            spec=LLMModel,
            id=model_id,
            type="embedding",
            is_default=False,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        # WHEN: Set default
        result = await service.set_default(model_id)

        # THEN: Model is marked as default
        assert mock_model.is_default is True
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_set_default_not_found_raises_error(self):
        """
        GIVEN: ModelRegistryService with no matching model
        WHEN: set_default is called
        THEN: Raises ModelNotFoundError
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # WHEN/THEN: Raises error
        with pytest.raises(ModelNotFoundError):
            await service.set_default(uuid4())


class TestModelRegistryServiceGetDefaultModel:
    """Tests for ModelRegistryService.get_default_model method."""

    @pytest.mark.asyncio
    async def test_get_default_model_returns_default(self):
        """
        GIVEN: ModelRegistryService with default model
        WHEN: get_default_model is called
        THEN: Returns the default model
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_model = MagicMock(
            spec=LLMModel,
            type="embedding",
            is_default=True,
            status="active",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        # WHEN: Get default
        result = await service.get_default_model("embedding")

        # THEN: Returns default model
        assert result == mock_model
        assert result.is_default is True

    @pytest.mark.asyncio
    async def test_get_default_model_returns_none_when_no_default(self):
        """
        GIVEN: ModelRegistryService with no default model
        WHEN: get_default_model is called
        THEN: Returns None
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # WHEN: Get default
        result = await service.get_default_model("embedding")

        # THEN: Returns None
        assert result is None


class TestApiKeyEncryption:
    """Tests for API key encryption/decryption functions."""

    def test_encrypt_api_key_returns_bytes(self):
        """
        GIVEN: A plaintext API key
        WHEN: encrypt_api_key is called
        THEN: Returns encrypted bytes
        """
        api_key = "sk-test-key-12345"

        # WHEN: Encrypt
        result = encrypt_api_key(api_key)

        # THEN: Returns bytes, not plaintext
        assert isinstance(result, bytes)
        assert result != api_key.encode()

    def test_decrypt_api_key_returns_plaintext(self):
        """
        GIVEN: An encrypted API key
        WHEN: decrypt_api_key is called
        THEN: Returns original plaintext
        """
        original_key = "sk-test-key-12345"
        encrypted = encrypt_api_key(original_key)

        # WHEN: Decrypt
        result = decrypt_api_key(encrypted)

        # THEN: Returns original
        assert result == original_key

    def test_encrypt_decrypt_roundtrip(self):
        """
        GIVEN: Various API keys
        WHEN: Encrypted then decrypted
        THEN: Original value is restored
        """
        test_keys = [
            "sk-simple",
            "sk-with-special-chars!@#$%",
            "A" * 1000,  # Long key
            "",  # Empty key
        ]

        for key in test_keys:
            encrypted = encrypt_api_key(key)
            decrypted = decrypt_api_key(encrypted)
            assert decrypted == key


class TestValidateModelConfig:
    """Tests for validate_model_config function."""

    def test_validate_embedding_config_success(self):
        """
        GIVEN: Valid embedding configuration
        WHEN: validate_model_config is called
        THEN: Returns validated config
        """
        config = {
            "dimensions": 1536,
            "max_tokens": 8191,
            "normalize": True,
            "distance_metric": "cosine",
            "batch_size": 100,
            "tags": ["test"],
        }

        # WHEN: Validate
        result = validate_model_config("embedding", config)

        # THEN: Returns validated config
        assert result["dimensions"] == 1536
        assert result["distance_metric"] == "cosine"

    def test_validate_generation_config_success(self):
        """
        GIVEN: Valid generation configuration
        WHEN: validate_model_config is called
        THEN: Returns validated config
        """
        config = {
            "context_window": 128000,
            "max_output_tokens": 4096,
            "supports_streaming": True,
            "supports_json_mode": True,
            "supports_vision": False,
            "temperature_default": 0.7,
            "temperature_range": [0.0, 2.0],
            "top_p_default": 1.0,
            "cost_per_1k_input": 0.01,
            "cost_per_1k_output": 0.03,
            "tags": [],
        }

        # WHEN: Validate
        result = validate_model_config("generation", config)

        # THEN: Returns validated config
        assert result["context_window"] == 128000
        assert result["supports_streaming"] is True

    def test_validate_invalid_type_raises_error(self):
        """
        GIVEN: Invalid model type
        WHEN: validate_model_config is called
        THEN: Raises ModelValidationError
        """
        with pytest.raises(ModelValidationError) as exc:
            validate_model_config("invalid_type", {})

        assert "invalid" in str(exc.value).lower()


class TestModelHasApiKey:
    """Tests for ModelRegistryService.model_has_api_key method."""

    def test_model_has_api_key_returns_true_when_present(self):
        """
        GIVEN: Model with encrypted API key
        WHEN: model_has_api_key is called
        THEN: Returns True
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_model = MagicMock(spec=LLMModel, api_key_encrypted=b"encrypted-data")

        # WHEN: Check
        result = service.model_has_api_key(mock_model)

        # THEN: Returns True
        assert result is True

    def test_model_has_api_key_returns_false_when_none(self):
        """
        GIVEN: Model without API key
        WHEN: model_has_api_key is called
        THEN: Returns False
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_model = MagicMock(spec=LLMModel, api_key_encrypted=None)

        # WHEN: Check
        result = service.model_has_api_key(mock_model)

        # THEN: Returns False
        assert result is False


class TestGetDecryptedApiKey:
    """Tests for ModelRegistryService.get_decrypted_api_key method."""

    def test_get_decrypted_api_key_returns_key(self):
        """
        GIVEN: Model with encrypted API key
        WHEN: get_decrypted_api_key is called
        THEN: Returns decrypted key
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        original_key = "sk-test-key"
        encrypted_key = encrypt_api_key(original_key)
        mock_model = MagicMock(spec=LLMModel, api_key_encrypted=encrypted_key)

        # WHEN: Get decrypted
        result = service.get_decrypted_api_key(mock_model)

        # THEN: Returns original key
        assert result == original_key

    def test_get_decrypted_api_key_returns_none_when_no_key(self):
        """
        GIVEN: Model without API key
        WHEN: get_decrypted_api_key is called
        THEN: Returns None
        """
        mock_session = AsyncMock()
        service = ModelRegistryService(mock_session)

        mock_model = MagicMock(spec=LLMModel, api_key_encrypted=None)

        # WHEN: Get decrypted
        result = service.get_decrypted_api_key(mock_model)

        # THEN: Returns None
        assert result is None
