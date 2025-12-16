"""LLM Model Registry Service.

Provides CRUD operations for managing embedding and generation models,
including encrypted API key storage and default model management.

Models are automatically synced to the LiteLLM proxy when created/updated
so connection tests work without manual YAML configuration.
"""

import base64
from typing import Any
from uuid import UUID

import structlog
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.llm_model import LLMModel, ModelStatus, ModelType
from app.schemas.llm_model import (
    EmbeddingModelConfig,
    GenerationModelConfig,
    LLMModelCreate,
    LLMModelUpdate,
    NERModelConfig,
)
from app.services.litellm_proxy_service import (
    register_model_with_proxy,
    unregister_model_from_proxy,
)

logger = structlog.get_logger(__name__)


class ModelRegistryError(Exception):
    """Base exception for model registry errors."""


class ModelNotFoundError(ModelRegistryError):
    """Raised when a model is not found."""


class ModelValidationError(ModelRegistryError):
    """Raised when model configuration is invalid."""


class EncryptionError(ModelRegistryError):
    """Raised when API key encryption/decryption fails."""


def _get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption.

    Uses the encryption_key from settings, padding to 32 bytes if needed.
    """
    key = settings.encryption_key
    # Ensure key is exactly 32 bytes (Fernet requirement)
    key_bytes = key.encode() if isinstance(key, str) else key
    # Pad or truncate to 32 bytes
    key_bytes = key_bytes.ljust(32, b"0")[:32]
    # Base64 encode for Fernet
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_api_key(api_key: str) -> bytes:
    """Encrypt an API key using Fernet symmetric encryption.

    Args:
        api_key: Plaintext API key.

    Returns:
        Encrypted bytes.

    Raises:
        EncryptionError: If encryption fails.
    """
    try:
        fernet = _get_fernet()
        return fernet.encrypt(api_key.encode())
    except Exception as e:
        raise EncryptionError(f"Failed to encrypt API key: {e}") from e


def decrypt_api_key(encrypted_key: bytes) -> str:
    """Decrypt an API key.

    Args:
        encrypted_key: Encrypted bytes.

    Returns:
        Plaintext API key.

    Raises:
        EncryptionError: If decryption fails.
    """
    try:
        fernet = _get_fernet()
        return fernet.decrypt(encrypted_key).decode()
    except InvalidToken as e:
        raise EncryptionError("Invalid encryption token - key may have changed") from e
    except Exception as e:
        raise EncryptionError(f"Failed to decrypt API key: {e}") from e


def validate_model_config(model_type: str, config: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize model configuration.

    Args:
        model_type: 'embedding', 'generation', or 'ner'.
        config: Configuration dictionary.

    Returns:
        Validated and normalized configuration.

    Raises:
        ModelValidationError: If configuration is invalid.
    """
    try:
        if model_type == ModelType.EMBEDDING.value:
            validated = EmbeddingModelConfig(**config)
            return validated.model_dump()
        elif model_type == ModelType.GENERATION.value:
            validated = GenerationModelConfig(**config)
            return validated.model_dump()
        elif model_type == ModelType.NER.value:
            validated = NERModelConfig(**config)
            return validated.model_dump()
        else:
            raise ModelValidationError(f"Invalid model type: {model_type}")
    except Exception as e:
        raise ModelValidationError(
            f"Invalid configuration for {model_type}: {e}"
        ) from e


class ModelRegistryService:
    """Service for managing LLM models in the registry."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session.

        Args:
            db: Async SQLAlchemy session.
        """
        self.db = db

    async def list_models(
        self,
        model_type: str | None = None,
        provider: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[LLMModel], int]:
        """List models with optional filters.

        Args:
            model_type: Filter by type (embedding, generation).
            provider: Filter by provider.
            status: Filter by status.
            skip: Number of records to skip.
            limit: Maximum records to return.

        Returns:
            Tuple of (models list, total count).
        """
        query = select(LLMModel)

        if model_type:
            query = query.where(LLMModel.type == model_type)
        if provider:
            query = query.where(LLMModel.provider == provider)
        if status:
            query = query.where(LLMModel.status == status)

        # Get total count
        count_query = select(LLMModel.id)
        if model_type:
            count_query = count_query.where(LLMModel.type == model_type)
        if provider:
            count_query = count_query.where(LLMModel.provider == provider)
        if status:
            count_query = count_query.where(LLMModel.status == status)

        count_result = await self.db.execute(count_query)
        total = len(count_result.all())

        # Get paginated results
        query = query.order_by(LLMModel.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        models = list(result.scalars().all())

        logger.debug(
            "models_listed",
            model_type=model_type,
            provider=provider,
            status=status,
            count=len(models),
            total=total,
        )

        return models, total

    async def get_model(self, model_id: UUID) -> LLMModel:
        """Get a model by ID.

        Args:
            model_id: Model UUID.

        Returns:
            LLMModel instance.

        Raises:
            ModelNotFoundError: If model not found.
        """
        result = await self.db.execute(select(LLMModel).where(LLMModel.id == model_id))
        model = result.scalar_one_or_none()

        if not model:
            raise ModelNotFoundError(f"Model not found: {model_id}")

        return model

    async def get_default_model(self, model_type: str) -> LLMModel | None:
        """Get the default model for a type.

        Args:
            model_type: 'embedding' or 'generation'.

        Returns:
            Default LLMModel or None.
        """
        result = await self.db.execute(
            select(LLMModel)
            .where(LLMModel.type == model_type)
            .where(LLMModel.is_default == True)  # noqa: E712
            .where(LLMModel.status == ModelStatus.ACTIVE.value)
        )
        return result.scalar_one_or_none()

    async def create_model(self, data: LLMModelCreate) -> LLMModel:
        """Create a new model and register with LiteLLM proxy.

        Args:
            data: Model creation data.

        Returns:
            Created LLMModel.

        Raises:
            ModelValidationError: If configuration invalid.
        """
        # Validate config
        validated_config = validate_model_config(data.type, data.config)

        # Encrypt API key if provided
        encrypted_key = None
        if data.api_key:
            encrypted_key = encrypt_api_key(data.api_key)

        # If setting as default, clear existing default
        if data.is_default:
            await self._clear_default(data.type)

        model = LLMModel(
            type=data.type,
            provider=data.provider,
            name=data.name,
            model_id=data.model_id,
            config=validated_config,
            api_endpoint=data.api_endpoint,
            api_key_encrypted=encrypted_key,
            status=ModelStatus.ACTIVE.value,
            is_default=data.is_default,
        )

        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)

        # Register with LiteLLM proxy for connection testing
        # Uses plaintext API key (before encryption) for proxy registration
        await register_model_with_proxy(model, data.api_key)

        logger.info(
            "model_created",
            model_id=str(model.id),
            type=model.type,
            provider=model.provider,
            name=model.name,
            is_default=model.is_default,
        )

        return model

    async def update_model(self, model_id: UUID, data: LLMModelUpdate) -> LLMModel:
        """Update a model and re-register with LiteLLM proxy.

        Args:
            model_id: Model UUID.
            data: Update data.

        Returns:
            Updated LLMModel.

        Raises:
            ModelNotFoundError: If model not found.
            ModelValidationError: If configuration invalid.
        """
        model = await self.get_model(model_id)
        old_values = {
            "name": model.name,
            "model_id": model.model_id,
            "status": model.status,
            "is_default": model.is_default,
        }

        # Track if API key was updated
        api_key_updated = data.api_key is not None

        # Update fields
        if data.name is not None:
            model.name = data.name
        if data.model_id is not None:
            model.model_id = data.model_id
        if data.api_endpoint is not None:
            model.api_endpoint = data.api_endpoint
        if data.status is not None:
            model.status = data.status
        if data.config is not None:
            model.config = validate_model_config(model.type, data.config)
        if data.api_key is not None:
            model.api_key_encrypted = encrypt_api_key(data.api_key)

        # Handle default change
        if data.is_default is not None and data.is_default != model.is_default:
            if data.is_default:
                await self._clear_default(model.type)
            model.is_default = data.is_default

        await self.db.commit()
        await self.db.refresh(model)

        # Re-register with LiteLLM proxy (overwrites existing registration)
        # Use new API key if updated, otherwise decrypt existing
        decrypted_key = (
            data.api_key if api_key_updated else self.get_decrypted_api_key(model)
        )
        await register_model_with_proxy(model, decrypted_key)

        logger.info(
            "model_updated",
            model_id=str(model_id),
            old_values=old_values,
            new_name=model.name,
            new_status=model.status,
        )

        return model

    async def delete_model(self, model_id: UUID) -> None:
        """Delete a model and unregister from LiteLLM proxy.

        Args:
            model_id: Model UUID.

        Raises:
            ModelNotFoundError: If model not found.
        """
        model = await self.get_model(model_id)

        # Unregister from LiteLLM proxy first
        await unregister_model_from_proxy(model)

        await self.db.delete(model)
        await self.db.commit()

        logger.info(
            "model_deleted",
            model_id=str(model_id),
            type=model.type,
            provider=model.provider,
            name=model.name,
        )

    async def set_default(self, model_id: UUID) -> LLMModel:
        """Set a model as the default for its type.

        Args:
            model_id: Model UUID.

        Returns:
            Updated LLMModel.

        Raises:
            ModelNotFoundError: If model not found.
        """
        model = await self.get_model(model_id)

        # Clear existing default for this type
        await self._clear_default(model.type)

        # Set new default
        model.is_default = True
        await self.db.commit()
        await self.db.refresh(model)

        logger.info(
            "model_set_default",
            model_id=str(model_id),
            type=model.type,
            name=model.name,
        )

        return model

    async def _clear_default(self, model_type: str) -> None:
        """Clear the default flag for all models of a type.

        Args:
            model_type: 'embedding' or 'generation'.
        """
        await self.db.execute(
            update(LLMModel)
            .where(LLMModel.type == model_type)
            .where(LLMModel.is_default == True)  # noqa: E712
            .values(is_default=False)
        )

    async def get_active_models_by_type(self, model_type: str) -> list[LLMModel]:
        """Get all active models of a type.

        Args:
            model_type: 'embedding' or 'generation'.

        Returns:
            List of active LLMModels.
        """
        result = await self.db.execute(
            select(LLMModel)
            .where(LLMModel.type == model_type)
            .where(LLMModel.status == ModelStatus.ACTIVE.value)
            .order_by(LLMModel.is_default.desc(), LLMModel.name)
        )
        return list(result.scalars().all())

    async def get_all_active_models(self) -> list[LLMModel]:
        """Get all active models for proxy sync.

        Used on application startup to sync all DB models to LiteLLM proxy.

        Returns:
            List of all active LLMModels.
        """
        result = await self.db.execute(
            select(LLMModel)
            .where(LLMModel.status == ModelStatus.ACTIVE.value)
            .order_by(LLMModel.created_at)
        )
        return list(result.scalars().all())

    def get_decrypted_api_key(self, model: LLMModel) -> str | None:
        """Get decrypted API key for a model.

        Args:
            model: LLMModel instance.

        Returns:
            Decrypted API key or None.
        """
        if model.api_key_encrypted:
            return decrypt_api_key(model.api_key_encrypted)
        return None

    def model_has_api_key(self, model: LLMModel) -> bool:
        """Check if a model has an API key configured.

        Args:
            model: LLMModel instance.

        Returns:
            True if API key is configured.
        """
        return model.api_key_encrypted is not None
