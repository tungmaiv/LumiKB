"""Service for managing system configuration settings.

Story 7-2: Adds centralized LLM configuration with hot-reload capability.
"""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis_client
from app.models.config import SystemConfig
from app.models.knowledge_base import KnowledgeBase
from app.models.llm_model import LLMModel, ModelStatus, ModelType
from app.schemas.admin import (
    ConfigCategory,
    ConfigDataType,
    ConfigSetting,
    DimensionMismatchWarning,
    LLMConfig,
    LLMConfigModelInfo,
    LLMConfigSettings,
    LLMConfigUpdateRequest,
    LLMConfigUpdateResponse,
    LLMHealthResponse,
    ModelHealthStatus,
)
from app.services.audit_service import AuditService

logger = structlog.get_logger(__name__)


class ConfigService:
    """Service for managing system configuration settings.

    Story 7-2: Extended with LLM configuration methods for hot-reload.
    """

    # Cache key and TTL
    CACHE_KEY = "admin:config:all"
    CACHE_TTL = 300  # 5 minutes (same as Story 5.1 admin stats)

    # LLM config cache keys (Story 7-2)
    LLM_CONFIG_CACHE_KEY = "admin:config:llm"
    LLM_CONFIG_CACHE_TTL = 30  # 30 seconds for faster hot-reload responsiveness
    LLM_CONFIG_CHANNEL = "llm:config:updated"  # Redis pub/sub channel for hot-reload

    # Default settings (used if DB is empty)
    DEFAULT_SETTINGS = {
        "session_timeout_minutes": {
            "name": "Session Timeout",
            "value": 720,
            "default_value": 720,
            "data_type": ConfigDataType.integer,
            "description": "Duration in minutes before user sessions expire",
            "category": ConfigCategory.security,
            "min_value": 60,
            "max_value": 43200,
            "requires_restart": False,
        },
        "login_rate_limit_per_hour": {
            "name": "Login Rate Limit",
            "value": 10,
            "default_value": 10,
            "data_type": ConfigDataType.integer,
            "description": "Maximum login attempts per user per hour",
            "category": ConfigCategory.security,
            "min_value": 1,
            "max_value": 100,
            "requires_restart": False,
        },
        "max_upload_file_size_mb": {
            "name": "Max Upload File Size",
            "value": 50,
            "default_value": 50,
            "data_type": ConfigDataType.integer,
            "description": "Maximum file size for document uploads (MB)",
            "category": ConfigCategory.processing,
            "min_value": 1,
            "max_value": 500,
            "requires_restart": False,
        },
        "default_chunk_size_tokens": {
            "name": "Default Chunk Size",
            "value": 512,
            "default_value": 512,
            "data_type": ConfigDataType.integer,
            "description": "Default token count for document chunking",
            "category": ConfigCategory.processing,
            "min_value": 100,
            "max_value": 2000,
            "requires_restart": True,  # Celery workers must restart
        },
        "max_chunks_per_document": {
            "name": "Max Chunks Per Document",
            "value": 1000,
            "default_value": 1000,
            "data_type": ConfigDataType.integer,
            "description": "Maximum number of chunks allowed per document",
            "category": ConfigCategory.processing,
            "min_value": 10,
            "max_value": 10000,
            "requires_restart": True,  # Celery workers must restart
        },
        "search_rate_limit_per_hour": {
            "name": "Search Rate Limit",
            "value": 100,
            "default_value": 100,
            "data_type": ConfigDataType.integer,
            "description": "Maximum search queries per user per hour",
            "category": ConfigCategory.rate_limits,
            "min_value": 10,
            "max_value": 1000,
            "requires_restart": False,
        },
        "generation_rate_limit_per_hour": {
            "name": "Generation Rate Limit",
            "value": 20,
            "default_value": 20,
            "data_type": ConfigDataType.integer,
            "description": "Maximum document generations per user per hour",
            "category": ConfigCategory.rate_limits,
            "min_value": 1,
            "max_value": 100,
            "requires_restart": False,
        },
        "upload_rate_limit_per_hour": {
            "name": "Upload Rate Limit",
            "value": 50,
            "default_value": 50,
            "data_type": ConfigDataType.integer,
            "description": "Maximum document uploads per user per hour",
            "category": ConfigCategory.rate_limits,
            "min_value": 1,
            "max_value": 500,
            "requires_restart": False,
        },
    }

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
        self.audit_service = AuditService()

    async def get_all_settings(self) -> list[ConfigSetting]:
        """
        Get all system configuration settings.

        Returns from Redis cache if available (5-min TTL).
        Otherwise queries database and caches result.

        Returns:
            List of ConfigSetting objects.
        """
        # Check Redis cache
        redis = await get_redis_client()
        cached = await redis.get(self.CACHE_KEY)

        if cached:
            cached_data = json.loads(cached)
            return [ConfigSetting.model_validate(item) for item in cached_data]

        # Cache miss - query database
        query = select(SystemConfig)
        result = await self.db.execute(query)
        db_settings = result.scalars().all()

        # Convert to ConfigSetting objects
        settings = []
        for key, setting_def in self.DEFAULT_SETTINGS.items():
            # Find DB override if exists
            db_setting = next((s for s in db_settings if s.key == key), None)

            settings.append(
                ConfigSetting(
                    key=key,
                    name=setting_def["name"],
                    value=(
                        db_setting.value if db_setting else setting_def["default_value"]
                    ),
                    default_value=setting_def["default_value"],
                    data_type=setting_def["data_type"],
                    description=setting_def["description"],
                    category=setting_def["category"],
                    min_value=setting_def.get("min_value"),
                    max_value=setting_def.get("max_value"),
                    requires_restart=setting_def["requires_restart"],
                    last_modified=db_setting.updated_at if db_setting else None,
                    last_modified_by=db_setting.updated_by if db_setting else None,
                )
            )

        # Cache result
        cache_data = [setting.model_dump(mode="json") for setting in settings]
        await redis.setex(self.CACHE_KEY, self.CACHE_TTL, json.dumps(cache_data))

        return settings

    async def update_setting(
        self,
        key: str,
        value: Any,
        changed_by: str,
    ) -> ConfigSetting:
        """
        Update a configuration setting with validation.

        Args:
            key: Setting key (e.g., "session_timeout_minutes")
            value: New value
            changed_by: Email of user making the change

        Returns:
            Updated ConfigSetting object.

        Raises:
            ValueError: If value is invalid (wrong type, out of range)
        """
        # Validate setting exists
        if key not in self.DEFAULT_SETTINGS:
            raise ValueError(f"Setting '{key}' not found")

        setting_def = self.DEFAULT_SETTINGS[key]

        # Validate value type
        expected_type = {
            ConfigDataType.integer: int,
            ConfigDataType.float: float,
            ConfigDataType.boolean: bool,
            ConfigDataType.string: str,
        }[setting_def["data_type"]]

        if not isinstance(value, expected_type):
            raise ValueError(
                f"Invalid value type. Expected {expected_type.__name__}, received {type(value).__name__}"
            )

        # Validate range (for numeric types)
        if (
            setting_def.get("min_value") is not None
            and value < setting_def["min_value"]
        ):
            raise ValueError(
                f"Value {value} is below minimum allowed value {setting_def['min_value']}"
            )
        if (
            setting_def.get("max_value") is not None
            and value > setting_def["max_value"]
        ):
            raise ValueError(
                f"Value {value} exceeds maximum allowed value {setting_def['max_value']}"
            )

        # Get old value for audit logging
        query = select(SystemConfig).where(SystemConfig.key == key)
        result = await self.db.execute(query)
        db_setting = result.scalar_one_or_none()

        old_value = db_setting.value if db_setting else setting_def["default_value"]

        # Update database
        if db_setting:
            update_stmt = (
                update(SystemConfig)
                .where(SystemConfig.key == key)
                .values(
                    value=value,
                    updated_by=changed_by,
                    updated_at=datetime.now(UTC),
                )
            )
            await self.db.execute(update_stmt)
        else:
            # Setting doesn't exist - insert it
            new_setting = SystemConfig(
                key=key,
                value=value,
                updated_by=changed_by,
                updated_at=datetime.now(UTC),
            )
            self.db.add(new_setting)

        await self.db.commit()

        # Clear Redis cache
        redis = await get_redis_client()
        await redis.delete(self.CACHE_KEY)

        # Log to audit
        await self.audit_service.log_event(
            action="config.update",
            resource_type="system_config",
            resource_id=None,  # Config settings don't have UUID, key is in details
            details={
                "setting_key": key,
                "old_value": old_value,
                "new_value": value,
                "changed_by": changed_by,
                "requires_restart": setting_def["requires_restart"],
            },
        )

        # Return updated setting
        return ConfigSetting(
            key=key,
            name=setting_def["name"],
            value=value,
            default_value=setting_def["default_value"],
            data_type=setting_def["data_type"],
            description=setting_def["description"],
            category=setting_def["category"],
            min_value=setting_def.get("min_value"),
            max_value=setting_def.get("max_value"),
            requires_restart=setting_def["requires_restart"],
            last_modified=datetime.now(UTC),
            last_modified_by=changed_by,
        )

    async def setting_exists(self, key: str) -> bool:
        """Check if a setting key exists."""
        return key in self.DEFAULT_SETTINGS

    async def get_restart_required_settings(self) -> list[str]:
        """
        Get list of setting keys that have pending changes requiring service restart.

        Returns:
            List of setting keys (e.g., ["default_chunk_size_tokens"])
        """
        # Query settings that have been modified and require restart
        query = select(SystemConfig.key).where(
            SystemConfig.key.in_(
                [
                    key
                    for key, setting in self.DEFAULT_SETTINGS.items()
                    if setting["requires_restart"]
                ]
            )
        )
        result = await self.db.execute(query)
        modified_keys = result.scalars().all()

        return list(modified_keys)

    def validate_setting_value(self, key: str, value: Any) -> bool:
        """
        Validate a setting value.

        Returns True if valid, raises ValueError otherwise.
        """
        setting_def = self.DEFAULT_SETTINGS[key]

        # Validate type
        expected_type = {
            ConfigDataType.integer: int,
            ConfigDataType.float: float,
            ConfigDataType.boolean: bool,
            ConfigDataType.string: str,
        }[setting_def["data_type"]]

        if not isinstance(value, expected_type):
            raise ValueError(
                f"Invalid value type. Expected {expected_type.__name__}, received {type(value).__name__}"
            )

        # Validate range
        if (
            setting_def.get("min_value") is not None
            and value < setting_def["min_value"]
        ):
            raise ValueError(
                f"Value {value} is below minimum allowed value {setting_def['min_value']}"
            )
        if (
            setting_def.get("max_value") is not None
            and value > setting_def["max_value"]
        ):
            raise ValueError(
                f"Value {value} exceeds maximum allowed value {setting_def['max_value']}"
            )

        return True

    # =========================================================================
    # LLM Configuration Methods (Story 7-2)
    # =========================================================================

    async def get_llm_config(self) -> LLMConfig:
        """Get current LLM configuration.

        AC-7.2.1: Returns current LLM model settings including provider,
        model name, base URL, and key parameters.

        Returns from Redis cache if available (30s TTL for hot-reload responsiveness).
        Otherwise queries database for default models and caches result.

        Returns:
            LLMConfig with current embedding/generation model settings.
        """
        # Check Redis cache
        redis = await get_redis_client()
        cached = await redis.get(self.LLM_CONFIG_CACHE_KEY)

        if cached:
            cached_data = json.loads(cached)
            return LLMConfig.model_validate(cached_data)

        # Cache miss - query database for default models
        config = await self._build_llm_config()

        # Cache result
        cache_data = config.model_dump(mode="json")
        await redis.setex(
            self.LLM_CONFIG_CACHE_KEY,
            self.LLM_CONFIG_CACHE_TTL,
            json.dumps(cache_data),
        )

        return config

    async def _build_llm_config(self) -> LLMConfig:
        """Build LLM configuration from database.

        Queries default embedding and generation models from the registry.
        Falls back to settings if no default models are registered.

        Returns:
            LLMConfig with current model settings.
        """
        # Get default embedding model
        embedding_query = (
            select(LLMModel)
            .where(LLMModel.type == ModelType.EMBEDDING.value)
            .where(LLMModel.is_default == True)  # noqa: E712
            .where(LLMModel.status == ModelStatus.ACTIVE.value)
        )
        embedding_result = await self.db.execute(embedding_query)
        embedding_model = embedding_result.scalar_one_or_none()

        # Get default generation model
        generation_query = (
            select(LLMModel)
            .where(LLMModel.type == ModelType.GENERATION.value)
            .where(LLMModel.is_default == True)  # noqa: E712
            .where(LLMModel.status == ModelStatus.ACTIVE.value)
        )
        generation_result = await self.db.execute(generation_query)
        generation_model = generation_result.scalar_one_or_none()

        # Get generation settings from SystemConfig (or defaults)
        gen_settings = await self._get_generation_settings()

        # Get last modification info
        config_query = select(SystemConfig).where(
            SystemConfig.key == "llm_config_settings"
        )
        config_result = await self.db.execute(config_query)
        config_record = config_result.scalar_one_or_none()

        return LLMConfig(
            embedding_model=(
                self._model_to_config_info(embedding_model) if embedding_model else None
            ),
            generation_model=(
                self._model_to_config_info(generation_model)
                if generation_model
                else None
            ),
            generation_settings=gen_settings,
            litellm_base_url=settings.litellm_url,
            last_modified=config_record.updated_at if config_record else None,
            last_modified_by=config_record.updated_by if config_record else None,
        )

    def _model_to_config_info(self, model: LLMModel) -> LLMConfigModelInfo:
        """Convert LLMModel to LLMConfigModelInfo."""
        return LLMConfigModelInfo(
            model_id=model.id,
            name=model.name,
            provider=model.provider,
            model_identifier=model.model_id,
            api_endpoint=model.api_endpoint,
            is_default=model.is_default,
            status=model.status,
        )

    async def _get_generation_settings(self) -> LLMConfigSettings:
        """Get generation settings from SystemConfig or defaults."""
        query = select(SystemConfig).where(SystemConfig.key == "llm_config_settings")
        result = await self.db.execute(query)
        config_record = result.scalar_one_or_none()

        if config_record and isinstance(config_record.value, dict):
            gen_settings = config_record.value.get("generation_settings", {})
            return LLMConfigSettings(
                temperature=gen_settings.get("temperature", 0.7),
                max_tokens=gen_settings.get("max_tokens", 2048),
                top_p=gen_settings.get("top_p", 1.0),
            )

        return LLMConfigSettings()

    async def update_llm_config(
        self,
        request: LLMConfigUpdateRequest,
        changed_by: str,
    ) -> LLMConfigUpdateResponse:
        """Update LLM configuration with hot-reload support.

        AC-7.2.2: Model switching applies without service restart.
        AC-7.2.3: Embedding dimension mismatch triggers warning.

        Args:
            request: Configuration update request.
            changed_by: Email of user making the change.

        Returns:
            LLMConfigUpdateResponse with updated config and warnings.

        Raises:
            ValueError: If model not found or invalid.
        """
        dimension_warning = None

        # Update embedding model default if specified
        if request.embedding_model_id:
            dimension_warning = await self._update_embedding_model(
                request.embedding_model_id
            )

        # Update generation model default if specified
        if request.generation_model_id:
            await self._update_generation_model(request.generation_model_id)

        # Update generation settings if specified
        if request.generation_settings:
            await self._update_generation_settings(
                request.generation_settings,
                changed_by,
            )

        # Invalidate cache
        await self._invalidate_llm_config_cache()

        # Publish hot-reload notification via Redis pub/sub
        await self._publish_config_update()

        # Log to audit
        await self.audit_service.log_event(
            action="llm_config.update",
            resource_type="system_config",
            resource_id=None,
            details={
                "embedding_model_id": (
                    str(request.embedding_model_id)
                    if request.embedding_model_id
                    else None
                ),
                "generation_model_id": (
                    str(request.generation_model_id)
                    if request.generation_model_id
                    else None
                ),
                "generation_settings": (
                    request.generation_settings.model_dump()
                    if request.generation_settings
                    else None
                ),
                "changed_by": changed_by,
            },
        )

        logger.info(
            "llm_config_updated",
            changed_by=changed_by,
            embedding_model_id=(
                str(request.embedding_model_id) if request.embedding_model_id else None
            ),
            generation_model_id=(
                str(request.generation_model_id)
                if request.generation_model_id
                else None
            ),
        )

        # Get updated config
        config = await self.get_llm_config()

        return LLMConfigUpdateResponse(
            config=config,
            hot_reload_applied=True,
            dimension_warning=dimension_warning,
        )

    async def _update_embedding_model(
        self,
        model_id: UUID,
    ) -> DimensionMismatchWarning | None:
        """Update default embedding model and check for dimension mismatch.

        Args:
            model_id: UUID of the model to set as default.

        Returns:
            DimensionMismatchWarning if dimensions differ from existing KBs.

        Raises:
            ValueError: If model not found or not an embedding model.
        """
        # Get the new model
        query = select(LLMModel).where(LLMModel.id == model_id)
        result = await self.db.execute(query)
        new_model = result.scalar_one_or_none()

        if not new_model:
            raise ValueError(f"Model not found: {model_id}")
        if new_model.type != ModelType.EMBEDDING.value:
            raise ValueError(f"Model {model_id} is not an embedding model")

        # Get current default embedding model
        current_query = (
            select(LLMModel)
            .where(LLMModel.type == ModelType.EMBEDDING.value)
            .where(LLMModel.is_default == True)  # noqa: E712
        )
        current_result = await self.db.execute(current_query)
        current_model = current_result.scalar_one_or_none()

        # Check for dimension mismatch
        dimension_warning = await self._check_dimension_mismatch(
            current_model, new_model
        )

        # Clear existing default
        update_stmt = (
            update(LLMModel)
            .where(LLMModel.type == ModelType.EMBEDDING.value)
            .where(LLMModel.is_default == True)  # noqa: E712
            .values(is_default=False)
        )
        await self.db.execute(update_stmt)

        # Set new default
        new_model.is_default = True
        await self.db.commit()

        return dimension_warning

    async def _check_dimension_mismatch(
        self,
        current_model: LLMModel | None,
        new_model: LLMModel,
    ) -> DimensionMismatchWarning | None:
        """Check if embedding dimensions differ from existing KB collections.

        AC-7.2.3: Embedding dimension mismatch triggers warning.

        Args:
            current_model: Currently configured embedding model.
            new_model: New embedding model to configure.

        Returns:
            DimensionMismatchWarning if dimensions differ, else None.
        """
        current_dims = current_model.config.get("dimensions") if current_model else None
        new_dims = new_model.config.get("dimensions")

        if current_dims and new_dims and current_dims != new_dims:
            # Get KBs with existing embeddings (document count > 0)
            # Note: KnowledgeBase uses status field, not archived_at
            kb_query = select(KnowledgeBase.name).where(
                KnowledgeBase.status != "archived"
            )
            kb_result = await self.db.execute(kb_query)
            kb_names = [row[0] for row in kb_result.all()]

            return DimensionMismatchWarning(
                has_mismatch=True,
                current_dimensions=current_dims,
                new_dimensions=new_dims,
                affected_kbs=kb_names,
                warning_message=(
                    f"Changing embedding dimensions from {current_dims} to {new_dims} "
                    f"may cause inconsistent search results for {len(kb_names)} "
                    f"existing knowledge bases. Consider re-indexing affected documents."
                ),
            )

        return None

    async def _update_generation_model(self, model_id: UUID) -> None:
        """Update default generation model.

        Args:
            model_id: UUID of the model to set as default.

        Raises:
            ValueError: If model not found or not a generation model.
        """
        # Get the new model
        query = select(LLMModel).where(LLMModel.id == model_id)
        result = await self.db.execute(query)
        new_model = result.scalar_one_or_none()

        if not new_model:
            raise ValueError(f"Model not found: {model_id}")
        if new_model.type != ModelType.GENERATION.value:
            raise ValueError(f"Model {model_id} is not a generation model")

        # Clear existing default
        update_stmt = (
            update(LLMModel)
            .where(LLMModel.type == ModelType.GENERATION.value)
            .where(LLMModel.is_default == True)  # noqa: E712
            .values(is_default=False)
        )
        await self.db.execute(update_stmt)

        # Set new default
        new_model.is_default = True
        await self.db.commit()

    async def _update_generation_settings(
        self,
        gen_settings: LLMConfigSettings,
        changed_by: str,
    ) -> None:
        """Update generation settings (temperature, max_tokens, etc.).

        Args:
            gen_settings: New generation settings.
            changed_by: Email of user making the change.
        """
        # Get existing config or create new
        query = select(SystemConfig).where(SystemConfig.key == "llm_config_settings")
        result = await self.db.execute(query)
        config_record = result.scalar_one_or_none()

        settings_data = {
            "generation_settings": gen_settings.model_dump(),
        }

        if config_record:
            update_stmt = (
                update(SystemConfig)
                .where(SystemConfig.key == "llm_config_settings")
                .values(
                    value=settings_data,
                    updated_by=changed_by,
                    updated_at=datetime.now(UTC),
                )
            )
            await self.db.execute(update_stmt)
        else:
            new_config = SystemConfig(
                key="llm_config_settings",
                value=settings_data,
                updated_by=changed_by,
                updated_at=datetime.now(UTC),
            )
            self.db.add(new_config)

        await self.db.commit()

    async def _invalidate_llm_config_cache(self) -> None:
        """Invalidate LLM config cache in Redis."""
        redis = await get_redis_client()
        await redis.delete(self.LLM_CONFIG_CACHE_KEY)

    async def _publish_config_update(self) -> None:
        """Publish config update notification via Redis pub/sub.

        AC-7.2.2: Enables hot-reload without service restart.
        """
        redis = await get_redis_client()
        await redis.publish(
            self.LLM_CONFIG_CHANNEL,
            json.dumps(
                {
                    "event": "llm_config_updated",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ),
        )

    async def test_model_health(
        self,
        model_type: str | None = None,
    ) -> LLMHealthResponse:
        """Test connection health for configured models.

        AC-7.2.4: Health status shown for each configured model.

        Args:
            model_type: Optional filter ('embedding' or 'generation').

        Returns:
            LLMHealthResponse with health status for each model.
        """
        # Import here to avoid circular imports
        from app.services.model_connection_tester import test_model_connection
        from app.services.model_registry_service import ModelRegistryService

        embedding_health = None
        generation_health = None

        registry = ModelRegistryService(self.db)

        # Test embedding model if requested or no filter
        if model_type is None or model_type == "embedding":
            embedding_model = await registry.get_default_model("embedding")
            if embedding_model:
                result = await test_model_connection(embedding_model, registry)
                embedding_health = ModelHealthStatus(
                    model_type="embedding",
                    model_name=embedding_model.name,
                    is_healthy=result.success,
                    latency_ms=result.latency_ms,
                    error_message=result.message if not result.success else None,
                    last_checked=datetime.now(UTC),
                )

        # Test generation model if requested or no filter
        if model_type is None or model_type == "generation":
            generation_model = await registry.get_default_model("generation")
            if generation_model:
                result = await test_model_connection(generation_model, registry)
                generation_health = ModelHealthStatus(
                    model_type="generation",
                    model_name=generation_model.name,
                    is_healthy=result.success,
                    latency_ms=result.latency_ms,
                    error_message=result.message if not result.success else None,
                    last_checked=datetime.now(UTC),
                )

        # Determine overall health
        overall_healthy = True
        if embedding_health and not embedding_health.is_healthy:
            overall_healthy = False
        if generation_health and not generation_health.is_healthy:
            overall_healthy = False

        return LLMHealthResponse(
            embedding_health=embedding_health,
            generation_health=generation_health,
            overall_healthy=overall_healthy,
        )
