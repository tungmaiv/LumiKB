"""KB Configuration Resolver Service.

Story 7.13: Configuration resolver implementing three-layer precedence:
Request params (highest) → KB-level settings → System defaults (lowest).
"""

from typing import Any, TypeVar
from uuid import UUID

import structlog
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase
from app.schemas.kb_settings import (
    ChunkingConfig,
    GenerationConfig,
    KBSettings,
    RetrievalConfig,
)


class EmbeddingModelConfig(BaseModel):
    """Configuration for embedding model.

    Used by search service to generate query embeddings with the correct model.
    """

    model_id: str
    """LiteLLM model identifier (e.g., 'ollama/mxbai-embed-large:latest')."""

    dimensions: int
    """Vector dimensions for this model."""

    provider: str | None = None
    """Model provider (ollama, openai, etc.)."""

    api_endpoint: str | None = None
    """Custom API endpoint if not using LiteLLM proxy."""


logger = structlog.get_logger(__name__)

T = TypeVar("T")

# Default system prompt used when KB has no custom prompt
DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based on the provided context. "
    "Always cite your sources and be clear about the limitations of your knowledge."
)


class KBConfigResolver:
    """Resolves configuration with request → KB → system precedence.

    This service implements three-layer configuration resolution:
    1. Request Parameters (highest priority) - values passed in API calls
    2. KB-Level Settings (KnowledgeBase.settings JSONB) - per-KB customization
    3. System Defaults (lowest priority) - global fallbacks

    Resolution: First non-null value wins.

    Attributes:
        CACHE_TTL: Cache time-to-live in seconds (5 minutes).
        CACHE_KEY_PREFIX: Prefix for Redis cache keys.
    """

    CACHE_TTL = 300  # 5 minutes, same as ConfigService
    CACHE_KEY_PREFIX = "kb_settings:"

    def __init__(
        self,
        session: AsyncSession,
        redis: Redis,
    ) -> None:
        """Initialize KBConfigResolver.

        Args:
            session: Async SQLAlchemy session for database access.
            redis: Redis client for caching.
        """
        self._session = session
        self._redis = redis

    def resolve_param(
        self,
        param_name: str,
        request_value: T | None,
        kb_settings: dict[str, Any],
        system_default: T,
    ) -> T:
        """Resolve single parameter with three-layer precedence.

        AC-7.13.1: Request value takes precedence.
        AC-7.13.2: KB setting wins when request is None.
        AC-7.13.3: System default used when both request and KB are None.

        Args:
            param_name: Name of the parameter to resolve.
            request_value: Value from request (highest priority).
            kb_settings: Dictionary of KB-level settings.
            system_default: System default value (lowest priority).

        Returns:
            Resolved value with correct precedence.
        """
        # AC-7.13.1: Request value wins if provided
        if request_value is not None:
            return request_value

        # AC-7.13.2: KB setting wins if request is None
        kb_value = kb_settings.get(param_name)
        if kb_value is not None:
            return kb_value

        # AC-7.13.3: Fall back to system default
        return system_default

    async def resolve_generation_config(
        self,
        kb_id: UUID,
        request_overrides: dict[str, Any] | None = None,
    ) -> GenerationConfig:
        """Merge request → KB → system for generation settings.

        AC-7.13.4: Returns merged GenerationConfig with correct precedence.

        Args:
            kb_id: Knowledge base UUID.
            request_overrides: Optional request-level overrides.

        Returns:
            GenerationConfig with merged values.
        """
        kb_settings = await self._get_kb_settings_cached(kb_id)
        kb_gen = kb_settings.generation
        system_defaults = GenerationConfig()
        overrides = request_overrides or {}

        return GenerationConfig(
            temperature=self.resolve_param(
                "temperature",
                overrides.get("temperature"),
                kb_gen.model_dump(),
                system_defaults.temperature,
            ),
            top_p=self.resolve_param(
                "top_p",
                overrides.get("top_p"),
                kb_gen.model_dump(),
                system_defaults.top_p,
            ),
            top_k=self.resolve_param(
                "top_k",
                overrides.get("top_k"),
                kb_gen.model_dump(),
                system_defaults.top_k,
            ),
            max_tokens=self.resolve_param(
                "max_tokens",
                overrides.get("max_tokens"),
                kb_gen.model_dump(),
                system_defaults.max_tokens,
            ),
            frequency_penalty=self.resolve_param(
                "frequency_penalty",
                overrides.get("frequency_penalty"),
                kb_gen.model_dump(),
                system_defaults.frequency_penalty,
            ),
            presence_penalty=self.resolve_param(
                "presence_penalty",
                overrides.get("presence_penalty"),
                kb_gen.model_dump(),
                system_defaults.presence_penalty,
            ),
            stop_sequences=self.resolve_param(
                "stop_sequences",
                overrides.get("stop_sequences"),
                kb_gen.model_dump(),
                system_defaults.stop_sequences,
            ),
        )

    async def resolve_retrieval_config(
        self,
        kb_id: UUID,
        request_overrides: dict[str, Any] | None = None,
    ) -> RetrievalConfig:
        """Merge request → KB → system for retrieval settings.

        AC-7.13.5: Returns merged RetrievalConfig with correct precedence.

        Args:
            kb_id: Knowledge base UUID.
            request_overrides: Optional request-level overrides.

        Returns:
            RetrievalConfig with merged values.
        """
        kb_settings = await self._get_kb_settings_cached(kb_id)
        kb_ret = kb_settings.retrieval
        system_defaults = RetrievalConfig()
        overrides = request_overrides or {}

        return RetrievalConfig(
            top_k=self.resolve_param(
                "top_k",
                overrides.get("top_k"),
                kb_ret.model_dump(),
                system_defaults.top_k,
            ),
            similarity_threshold=self.resolve_param(
                "similarity_threshold",
                overrides.get("similarity_threshold"),
                kb_ret.model_dump(),
                system_defaults.similarity_threshold,
            ),
            method=self.resolve_param(
                "method",
                overrides.get("method"),
                kb_ret.model_dump(),
                system_defaults.method,
            ),
            mmr_enabled=self.resolve_param(
                "mmr_enabled",
                overrides.get("mmr_enabled"),
                kb_ret.model_dump(),
                system_defaults.mmr_enabled,
            ),
            mmr_lambda=self.resolve_param(
                "mmr_lambda",
                overrides.get("mmr_lambda"),
                kb_ret.model_dump(),
                system_defaults.mmr_lambda,
            ),
            hybrid_alpha=self.resolve_param(
                "hybrid_alpha",
                overrides.get("hybrid_alpha"),
                kb_ret.model_dump(),
                system_defaults.hybrid_alpha,
            ),
        )

    async def resolve_chunking_config(self, kb_id: UUID) -> ChunkingConfig:
        """Get chunking config from KB or system defaults.

        AC-7.13.6: Returns ChunkingConfig from KB or system defaults.

        Note: Chunking config is typically set at KB level and not overridden
        per-request, so this method only merges KB settings with system defaults.

        Args:
            kb_id: Knowledge base UUID.

        Returns:
            ChunkingConfig with KB settings or defaults.
        """
        kb_settings = await self._get_kb_settings_cached(kb_id)
        # Chunking config is used as-is from KB settings (or defaults)
        return kb_settings.chunking

    async def get_kb_system_prompt(self, kb_id: UUID) -> str:
        """Get KB's custom system prompt or system default.

        AC-7.13.7: Returns KB's system_prompt if set, otherwise system default.

        Args:
            kb_id: Knowledge base UUID.

        Returns:
            System prompt string.
        """
        kb_settings = await self._get_kb_settings_cached(kb_id)
        kb_prompt = kb_settings.prompts.system_prompt

        # Return KB prompt if set and not empty
        if kb_prompt and kb_prompt.strip():
            return kb_prompt

        # Fall back to system default
        return DEFAULT_SYSTEM_PROMPT

    async def _get_kb_settings_cached(self, kb_id: UUID) -> KBSettings:
        """Load KB settings with Redis caching.

        AC-7.13.8: KB settings are cached with 5-minute TTL.

        Args:
            kb_id: Knowledge base UUID.

        Returns:
            KBSettings parsed from KB.settings JSONB field.

        Raises:
            ValueError: If KB not found.
        """
        cache_key = f"{self.CACHE_KEY_PREFIX}{kb_id}"

        # Check cache first
        try:
            cached = await self._redis.get(cache_key)
            if cached:
                logger.debug("kb_settings_cache_hit", kb_id=str(kb_id))
                return KBSettings.model_validate_json(cached)
        except Exception as e:
            # Log but continue to database if cache fails
            logger.warning(
                "kb_settings_cache_error",
                kb_id=str(kb_id),
                error=str(e),
            )

        logger.debug("kb_settings_cache_miss", kb_id=str(kb_id))

        # Load from database
        result = await self._session.execute(
            select(KnowledgeBase.settings).where(KnowledgeBase.id == kb_id)
        )
        settings_data = result.scalar_one_or_none()

        if settings_data is None:
            raise ValueError(f"Knowledge base not found: {kb_id}")

        # Parse settings (empty dict {} gets all defaults applied)
        settings = KBSettings.model_validate(settings_data or {})

        # Cache for 5 minutes
        try:
            await self._redis.setex(
                cache_key,
                self.CACHE_TTL,
                settings.model_dump_json(),
            )
            logger.debug("kb_settings_cached", kb_id=str(kb_id))
        except Exception as e:
            # Log but don't fail if caching fails
            logger.warning(
                "kb_settings_cache_set_error",
                kb_id=str(kb_id),
                error=str(e),
            )

        return settings

    async def invalidate_kb_settings_cache(self, kb_id: UUID) -> None:
        """Invalidate cached KB settings.

        AC-7.13.8: Cache invalidated on KB settings update.

        Args:
            kb_id: Knowledge base UUID.
        """
        cache_key = f"{self.CACHE_KEY_PREFIX}{kb_id}"
        try:
            await self._redis.delete(cache_key)
            logger.info("kb_settings_cache_invalidated", kb_id=str(kb_id))
        except Exception as e:
            logger.warning(
                "kb_settings_cache_invalidate_error",
                kb_id=str(kb_id),
                error=str(e),
            )

    async def get_kb_settings(self, kb_id: UUID) -> KBSettings:
        """Get full KB settings (public accessor for cached settings).

        Args:
            kb_id: Knowledge base UUID.

        Returns:
            Full KBSettings object.
        """
        return await self._get_kb_settings_cached(kb_id)

    async def get_kb_embedding_model(self, kb_id: UUID) -> EmbeddingModelConfig | None:
        """Get KB's configured embedding model.

        Loads the embedding model configuration for a KB. This is used by the
        search service to generate query embeddings with the correct model,
        ensuring vector dimensions match between indexing and querying.

        Args:
            kb_id: Knowledge base UUID.

        Returns:
            EmbeddingModelConfig if KB has a configured embedding model, None otherwise.
            None means the system should use the default embedding model.
        """
        from sqlalchemy.orm import joinedload

        cache_key = f"kb_embedding_model:{kb_id}"

        # Check cache first
        try:
            cached = await self._redis.get(cache_key)
            if cached:
                if cached == b"null":
                    return None
                logger.debug("kb_embedding_model_cache_hit", kb_id=str(kb_id))
                return EmbeddingModelConfig.model_validate_json(cached)
        except Exception as e:
            logger.warning(
                "kb_embedding_model_cache_error",
                kb_id=str(kb_id),
                error=str(e),
            )

        logger.debug("kb_embedding_model_cache_miss", kb_id=str(kb_id))

        # Load KB with embedding model relationship
        result = await self._session.execute(
            select(KnowledgeBase)
            .options(joinedload(KnowledgeBase.embedding_model))
            .where(KnowledgeBase.id == kb_id)
        )
        kb = result.unique().scalar_one_or_none()

        if kb is None:
            raise ValueError(f"Knowledge base not found: {kb_id}")

        if kb.embedding_model is None:
            # Cache null result to avoid repeated DB lookups
            try:
                await self._redis.setex(cache_key, self.CACHE_TTL, "null")
            except Exception as e:
                logger.warning(
                    "kb_embedding_model_cache_set_error",
                    kb_id=str(kb_id),
                    error=str(e),
                )
            return None

        # Extract model configuration
        model = kb.embedding_model
        dimensions = model.config.get("dimensions", 768) if model.config else 768

        # Resolve api_endpoint for local development
        # host.docker.internal is used when backend runs in Docker,
        # but we need localhost when running directly on the host
        api_endpoint = model.api_endpoint
        if api_endpoint and "host.docker.internal" in api_endpoint:
            api_endpoint = api_endpoint.replace("host.docker.internal", "localhost")
            logger.debug(
                "api_endpoint_resolved_for_local_dev",
                original=model.api_endpoint,
                resolved=api_endpoint,
            )

        config = EmbeddingModelConfig(
            model_id=model.model_id,
            dimensions=dimensions,
            provider=model.provider,
            api_endpoint=api_endpoint,
        )

        # Cache for 5 minutes
        try:
            await self._redis.setex(
                cache_key,
                self.CACHE_TTL,
                config.model_dump_json(),
            )
            logger.debug("kb_embedding_model_cached", kb_id=str(kb_id))
        except Exception as e:
            logger.warning(
                "kb_embedding_model_cache_set_error",
                kb_id=str(kb_id),
                error=str(e),
            )

        logger.info(
            "kb_embedding_model_loaded",
            kb_id=str(kb_id),
            model_id=model.model_id,
            dimensions=dimensions,
            provider=model.provider,
        )

        return config


async def get_kb_config_resolver(
    session: AsyncSession,
    redis: Redis,
) -> KBConfigResolver:
    """Dependency injection factory for KBConfigResolver.

    Usage with FastAPI:
        @router.get("/example")
        async def example(
            session: AsyncSession = Depends(get_db),
            redis: Redis = Depends(get_redis_client),
        ):
            resolver = await get_kb_config_resolver(session, redis)
            config = await resolver.resolve_generation_config(kb_id)

    Args:
        session: Async SQLAlchemy session.
        redis: Redis client.

    Returns:
        Configured KBConfigResolver instance.
    """
    return KBConfigResolver(session=session, redis=redis)
