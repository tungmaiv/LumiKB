"""Unit tests for KBConfigResolver service.

Story 7-13: KBConfigResolver Service
GREEN PHASE - Tests updated to match actual implementation.

Test Coverage:
- [P0] AC-7.13.1: resolve_param with request value wins
- [P0] AC-7.13.2: resolve_param with KB setting fallback
- [P0] AC-7.13.3: resolve_param with system default fallback
- [P0] AC-7.13.4: resolve_generation_config with merged precedence
- [P0] AC-7.13.5: resolve_retrieval_config with merged precedence
- [P1] AC-7.13.6: resolve_chunking_config from KB or system
- [P1] AC-7.13.7: get_kb_system_prompt with KB/system fallback
- [P0] AC-7.13.8: Redis caching with 5min TTL and invalidation

Knowledge Base References:
- test-quality.md: Given-When-Then structure, one assertion per test
- test-levels-framework.md: Unit test characteristics (no external deps)
- data-factories.md: Factory patterns for test data
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.kb_settings import (
    ChunkingConfig,
    ChunkingStrategy,
    GenerationConfig,
    KBPromptConfig,
    KBSettings,
    RetrievalConfig,
    RetrievalMethod,
)
from app.services.kb_config_resolver import (
    DEFAULT_SYSTEM_PROMPT,
    KBConfigResolver,
    get_kb_config_resolver,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_redis():
    """Create mock Redis client for caching tests.

    Default behavior: Cache miss (returns None).
    Override in individual tests for cache hit scenarios.
    """
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)  # Cache miss by default
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def mock_session():
    """Create mock async database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_kb_id():
    """Generate sample KB UUID for tests."""
    return uuid4()


@pytest.fixture
def sample_kb_settings():
    """Create sample KBSettings for testing.

    Provides a complete KBSettings object with custom values
    different from system defaults for precedence testing.
    """
    return KBSettings(
        chunking=ChunkingConfig(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=1024,
            chunk_overlap=100,
        ),
        retrieval=RetrievalConfig(
            top_k=15,
            similarity_threshold=0.8,
            method=RetrievalMethod.HYBRID,
        ),
        generation=GenerationConfig(
            temperature=0.5,
            top_p=0.85,
            max_tokens=4096,
        ),
        prompts=KBPromptConfig(
            system_prompt="You are a helpful assistant for this knowledge base.",
        ),
    )


@pytest.fixture
def system_default_settings():
    """Create system default settings for fallback testing."""
    return KBSettings(
        chunking=ChunkingConfig(),  # Uses schema defaults
        retrieval=RetrievalConfig(),  # Uses schema defaults
        generation=GenerationConfig(),  # Uses schema defaults
        prompts=KBPromptConfig(),  # Empty prompt = use system default
    )


def mock_db_result_for_settings(settings_dict: dict | None):
    """Helper to create mock db result for settings query."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = settings_dict
    return result


# =============================================================================
# AC-7.13.1: resolve_param with request value wins
# =============================================================================


class TestResolveParamRequestWins:
    """Tests for resolve_param when request value takes precedence (AC-7.13.1)."""

    def test_resolve_param_returns_request_value_when_provided(
        self, mock_session, mock_redis
    ):
        """
        GIVEN: resolve_param called with request_value=0.5
        WHEN: KB settings has temperature=0.3 and system default is 0.7
        THEN: Returns 0.5 (request wins)
        """
        # GIVEN: Service with dependencies
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        kb_settings = {"temperature": 0.3}

        # WHEN: Call resolve_param with request value
        result = resolver.resolve_param(
            param_name="temperature",
            request_value=0.5,
            kb_settings=kb_settings,
            system_default=0.7,
        )

        # THEN: Request value wins
        assert result == 0.5

    def test_resolve_param_returns_request_value_zero(self, mock_session, mock_redis):
        """
        GIVEN: resolve_param called with request_value=0 (falsy but valid)
        WHEN: KB has temperature=0.3 and system default is 0.7
        THEN: Returns 0 (request value 0 is valid, not None)
        """
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        kb_settings = {"temperature": 0.3}

        # WHEN: Call resolve_param with request value 0
        result = resolver.resolve_param(
            param_name="temperature",
            request_value=0,
            kb_settings=kb_settings,
            system_default=0.7,
        )

        # THEN: Request value 0 wins (not treated as None)
        assert result == 0

    def test_resolve_param_returns_request_value_empty_string(
        self, mock_session, mock_redis
    ):
        """
        GIVEN: resolve_param called with request_value="" (empty string)
        WHEN: KB has system_prompt="KB prompt" and system default is "Default"
        THEN: Returns "" (empty string is valid, not None)
        """
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        kb_settings = {"system_prompt": "KB prompt"}

        # WHEN: Call resolve_param with empty string
        result = resolver.resolve_param(
            param_name="system_prompt",
            request_value="",
            kb_settings=kb_settings,
            system_default="Default prompt",
        )

        # THEN: Empty string wins (not treated as None)
        assert result == ""


# =============================================================================
# AC-7.13.2: resolve_param with KB setting fallback
# =============================================================================


class TestResolveParamKBFallback:
    """Tests for resolve_param when KB setting takes precedence (AC-7.13.2)."""

    def test_resolve_param_returns_kb_value_when_request_none(
        self, mock_session, mock_redis
    ):
        """
        GIVEN: resolve_param called with request_value=None
        WHEN: KB settings has temperature=0.3
        THEN: Returns 0.3 (KB wins)
        """
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        kb_settings = {"temperature": 0.3}

        # WHEN: Call resolve_param with None request value
        result = resolver.resolve_param(
            param_name="temperature",
            request_value=None,
            kb_settings=kb_settings,
            system_default=0.7,
        )

        # THEN: KB value wins
        assert result == 0.3

    def test_resolve_param_returns_kb_nested_config_value(
        self, mock_session, mock_redis
    ):
        """
        GIVEN: resolve_param called for nested config (top_k in retrieval)
        WHEN: Request is None and KB has top_k=20
        THEN: Returns 20 from KB settings
        """
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        kb_settings = {"top_k": 20}

        # WHEN: Call resolve_param for top_k
        result = resolver.resolve_param(
            param_name="top_k",
            request_value=None,
            kb_settings=kb_settings,
            system_default=10,
        )

        # THEN: KB value wins
        assert result == 20


# =============================================================================
# AC-7.13.3: resolve_param with system default fallback
# =============================================================================


class TestResolveParamSystemDefault:
    """Tests for resolve_param when system default takes precedence (AC-7.13.3)."""

    def test_resolve_param_returns_system_default_when_both_none(
        self, mock_session, mock_redis
    ):
        """
        GIVEN: resolve_param called with request_value=None and empty KB settings
        WHEN: System default is 0.7
        THEN: Returns 0.7 (system default)
        """
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        kb_settings = {}  # No KB setting

        # WHEN: Call resolve_param with no request or KB value
        result = resolver.resolve_param(
            param_name="temperature",
            request_value=None,
            kb_settings=kb_settings,
            system_default=0.7,
        )

        # THEN: System default wins
        assert result == 0.7

    def test_resolve_param_returns_system_default_when_kb_key_missing(
        self, mock_session, mock_redis
    ):
        """
        GIVEN: resolve_param called for param not in KB settings
        WHEN: KB settings has other keys but not requested one
        THEN: Returns system default
        """
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        kb_settings = {"top_p": 0.9}  # Has top_p but not temperature

        # WHEN: Call resolve_param for temperature
        result = resolver.resolve_param(
            param_name="temperature",
            request_value=None,
            kb_settings=kb_settings,
            system_default=0.7,
        )

        # THEN: System default wins
        assert result == 0.7

    def test_resolve_param_returns_system_default_when_kb_value_none(
        self, mock_session, mock_redis
    ):
        """
        GIVEN: resolve_param called when KB explicitly has None value
        WHEN: KB settings has temperature=None
        THEN: Returns system default
        """
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        kb_settings = {"temperature": None}  # Explicitly None

        # WHEN: Call resolve_param
        result = resolver.resolve_param(
            param_name="temperature",
            request_value=None,
            kb_settings=kb_settings,
            system_default=0.7,
        )

        # THEN: System default wins
        assert result == 0.7


# =============================================================================
# AC-7.13.4: resolve_generation_config with merged precedence
# =============================================================================


class TestResolveGenerationConfig:
    """Tests for resolve_generation_config method (AC-7.13.4)."""

    @pytest.mark.asyncio
    async def test_resolve_generation_config_returns_generation_config(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: resolve_generation_config called with kb_id
        WHEN: KB has custom generation settings
        THEN: Returns GenerationConfig instance with merged values
        """
        # Mock cache miss and DB result
        kb_settings_dict = {"generation": {"temperature": 0.5, "max_tokens": 4096}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call resolve_generation_config
        result = await resolver.resolve_generation_config(sample_kb_id)

        # THEN: Returns GenerationConfig with KB values
        assert isinstance(result, GenerationConfig)
        assert result.temperature == 0.5
        assert result.max_tokens == 4096

    @pytest.mark.asyncio
    async def test_resolve_generation_config_request_overrides_kb(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: resolve_generation_config called with request_overrides
        WHEN: KB has temperature=0.5 but request has temperature=0.8
        THEN: Returns GenerationConfig with request temperature=0.8
        """
        # Mock cache miss and DB result
        kb_settings_dict = {"generation": {"temperature": 0.5, "max_tokens": 4096}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        request_overrides = {"temperature": 0.8}

        # WHEN: Call resolve_generation_config with overrides
        result = await resolver.resolve_generation_config(
            sample_kb_id, request_overrides
        )

        # THEN: Request override wins
        assert result.temperature == 0.8
        assert result.max_tokens == 4096  # KB value preserved

    @pytest.mark.asyncio
    async def test_resolve_generation_config_uses_system_defaults(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: resolve_generation_config called
        WHEN: KB has no generation settings
        THEN: Returns GenerationConfig with system defaults
        """
        # Mock cache miss and empty DB result
        mock_session.execute = AsyncMock(return_value=mock_db_result_for_settings({}))

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call resolve_generation_config
        result = await resolver.resolve_generation_config(sample_kb_id)

        # THEN: Uses system defaults
        assert isinstance(result, GenerationConfig)
        assert result.temperature == 0.7  # Default from GenerationConfig
        assert result.max_tokens == 2048  # Default from GenerationConfig

    @pytest.mark.asyncio
    async def test_resolve_generation_config_partial_override(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: resolve_generation_config called with partial request_overrides
        WHEN: Request only overrides temperature, KB has max_tokens
        THEN: Returns merged config from all three layers
        """
        # Mock cache miss and DB result with only max_tokens
        kb_settings_dict = {"generation": {"max_tokens": 8192}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        request_overrides = {"temperature": 0.9}  # Only temperature

        # WHEN: Call resolve_generation_config with partial override
        result = await resolver.resolve_generation_config(
            sample_kb_id, request_overrides
        )

        # THEN: Merged from all layers
        assert result.temperature == 0.9  # From request
        assert result.max_tokens == 8192  # From KB
        assert result.top_p == 0.9  # From system default


# =============================================================================
# AC-7.13.5: resolve_retrieval_config with merged precedence
# =============================================================================


class TestResolveRetrievalConfig:
    """Tests for resolve_retrieval_config method (AC-7.13.5)."""

    @pytest.mark.asyncio
    async def test_resolve_retrieval_config_returns_retrieval_config(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: resolve_retrieval_config called with kb_id
        WHEN: KB has custom retrieval settings
        THEN: Returns RetrievalConfig instance with KB values
        """
        # Mock cache miss and DB result
        kb_settings_dict = {"retrieval": {"top_k": 20, "similarity_threshold": 0.85}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call resolve_retrieval_config
        result = await resolver.resolve_retrieval_config(sample_kb_id)

        # THEN: Returns RetrievalConfig with KB values
        assert isinstance(result, RetrievalConfig)
        assert result.top_k == 20
        assert result.similarity_threshold == 0.85

    @pytest.mark.asyncio
    async def test_resolve_retrieval_config_request_overrides_top_k(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: resolve_retrieval_config called with request_overrides
        WHEN: Request overrides top_k
        THEN: Returns RetrievalConfig with request top_k
        """
        # Mock cache miss and DB result
        kb_settings_dict = {"retrieval": {"top_k": 15, "similarity_threshold": 0.8}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        request_overrides = {"top_k": 5}

        # WHEN: Call with request override
        result = await resolver.resolve_retrieval_config(
            sample_kb_id, request_overrides
        )

        # THEN: Request override wins for top_k
        assert result.top_k == 5
        assert result.similarity_threshold == 0.8  # KB value preserved

    @pytest.mark.asyncio
    async def test_resolve_retrieval_config_uses_system_defaults(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: resolve_retrieval_config called
        WHEN: KB has no retrieval settings
        THEN: Returns RetrievalConfig with system defaults
        """
        # Mock cache miss and empty DB result
        mock_session.execute = AsyncMock(return_value=mock_db_result_for_settings({}))

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call resolve_retrieval_config
        result = await resolver.resolve_retrieval_config(sample_kb_id)

        # THEN: Uses system defaults
        assert isinstance(result, RetrievalConfig)
        assert result.top_k == 10  # Default
        assert result.similarity_threshold == 0.7  # Default
        assert result.method == RetrievalMethod.VECTOR  # Default


# =============================================================================
# AC-7.13.6: resolve_chunking_config from KB or system
# =============================================================================


class TestResolveChunkingConfig:
    """Tests for resolve_chunking_config method (AC-7.13.6)."""

    @pytest.mark.asyncio
    async def test_resolve_chunking_config_returns_kb_config(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: resolve_chunking_config called with kb_id
        WHEN: KB has custom chunking settings
        THEN: Returns ChunkingConfig with KB values
        """
        # Mock cache miss and DB result
        kb_settings_dict = {
            "chunking": {
                "strategy": "semantic",
                "chunk_size": 1024,
                "chunk_overlap": 100,
            }
        }
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call resolve_chunking_config
        result = await resolver.resolve_chunking_config(sample_kb_id)

        # THEN: Returns KB chunking config
        assert isinstance(result, ChunkingConfig)
        assert result.strategy == ChunkingStrategy.SEMANTIC
        assert result.chunk_size == 1024
        assert result.chunk_overlap == 100

    @pytest.mark.asyncio
    async def test_resolve_chunking_config_uses_system_defaults(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: resolve_chunking_config called
        WHEN: KB has no chunking settings
        THEN: Returns ChunkingConfig with system defaults
        """
        # Mock cache miss and empty DB result
        mock_session.execute = AsyncMock(return_value=mock_db_result_for_settings({}))

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call resolve_chunking_config
        result = await resolver.resolve_chunking_config(sample_kb_id)

        # THEN: Uses system defaults
        assert isinstance(result, ChunkingConfig)
        assert result.strategy == ChunkingStrategy.RECURSIVE  # Default
        assert result.chunk_size == 512  # Default
        assert result.chunk_overlap == 50  # Default


# =============================================================================
# AC-7.13.7: get_kb_system_prompt with KB/system fallback
# =============================================================================


class TestGetKBSystemPrompt:
    """Tests for get_kb_system_prompt method (AC-7.13.7)."""

    @pytest.mark.asyncio
    async def test_get_kb_system_prompt_returns_kb_prompt(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: get_kb_system_prompt called with kb_id
        WHEN: KB has custom system_prompt in prompts config
        THEN: Returns the KB's system_prompt
        """
        # Mock cache miss and DB result with custom prompt
        kb_settings_dict = {
            "prompts": {
                "system_prompt": "You are an expert assistant for legal documents."
            }
        }
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call get_kb_system_prompt
        result = await resolver.get_kb_system_prompt(sample_kb_id)

        # THEN: Returns KB prompt
        assert result == "You are an expert assistant for legal documents."

    @pytest.mark.asyncio
    async def test_get_kb_system_prompt_returns_system_default_when_kb_empty(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: get_kb_system_prompt called
        WHEN: KB has no custom system_prompt
        THEN: Returns system default prompt
        """
        # Mock cache miss and empty prompts
        mock_session.execute = AsyncMock(return_value=mock_db_result_for_settings({}))

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call get_kb_system_prompt
        result = await resolver.get_kb_system_prompt(sample_kb_id)

        # THEN: Returns system default
        assert result == DEFAULT_SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_get_kb_system_prompt_returns_system_default_when_kb_prompt_empty(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: get_kb_system_prompt called
        WHEN: KB has system_prompt="" (empty string)
        THEN: Returns system default prompt
        """
        # Mock cache miss and empty prompt
        kb_settings_dict = {"prompts": {"system_prompt": ""}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call get_kb_system_prompt
        result = await resolver.get_kb_system_prompt(sample_kb_id)

        # THEN: Returns system default (empty string treated as empty)
        assert result == DEFAULT_SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_get_kb_system_prompt_returns_system_default_when_whitespace_only(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: get_kb_system_prompt called
        WHEN: KB has system_prompt with only whitespace
        THEN: Returns system default prompt
        """
        # Mock cache miss and whitespace-only prompt
        kb_settings_dict = {"prompts": {"system_prompt": "   "}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call get_kb_system_prompt
        result = await resolver.get_kb_system_prompt(sample_kb_id)

        # THEN: Returns system default (whitespace treated as empty)
        assert result == DEFAULT_SYSTEM_PROMPT


# =============================================================================
# AC-7.13.8: Redis caching with 5min TTL and invalidation
# =============================================================================


class TestKBSettingsCaching:
    """Tests for Redis caching of KB settings (AC-7.13.8)."""

    @pytest.mark.asyncio
    async def test_get_kb_settings_cached_returns_cached_value(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: KB settings are already cached in Redis
        WHEN: _get_kb_settings_cached is called
        THEN: Returns cached value without DB query
        """
        # Mock cache hit
        cached_settings = KBSettings(generation=GenerationConfig(temperature=0.4))
        mock_redis.get.return_value = cached_settings.model_dump_json()

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Get KB settings
        result = await resolver._get_kb_settings_cached(sample_kb_id)

        # THEN: Returns cached value, no DB call
        assert result.generation.temperature == 0.4
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_kb_settings_cached_queries_db_on_miss(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: KB settings not in cache (cache miss)
        WHEN: _get_kb_settings_cached is called
        THEN: Queries database and caches result
        """
        # Mock cache miss
        mock_redis.get.return_value = None

        # Mock DB result
        kb_settings_dict = {"retrieval": {"top_k": 25}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Get KB settings
        result = await resolver._get_kb_settings_cached(sample_kb_id)

        # THEN: Queries DB and caches
        assert result.retrieval.top_k == 25
        mock_session.execute.assert_called_once()
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_kb_settings_cached_uses_5min_ttl(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: Cache miss requiring new cache entry
        WHEN: KB settings are cached
        THEN: Uses 300 second (5 minute) TTL
        """
        # Mock cache miss
        mock_redis.get.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_db_result_for_settings({}))

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Get KB settings (triggers caching)
        await resolver._get_kb_settings_cached(sample_kb_id)

        # THEN: Cache set with 300 second TTL
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 300  # TTL is 300 seconds

    @pytest.mark.asyncio
    async def test_get_kb_settings_cached_uses_correct_key_pattern(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: Cache miss requiring new cache entry
        WHEN: KB settings are cached
        THEN: Uses key pattern kb_settings:{kb_id}
        """
        # Mock cache miss
        mock_redis.get.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_db_result_for_settings({}))

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Get KB settings
        await resolver._get_kb_settings_cached(sample_kb_id)

        # THEN: Correct cache key pattern used
        expected_key = f"kb_settings:{sample_kb_id}"
        mock_redis.get.assert_called_with(expected_key)
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == expected_key

    @pytest.mark.asyncio
    async def test_invalidate_kb_settings_cache_deletes_cache_key(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: KB settings are cached
        WHEN: invalidate_kb_settings_cache is called
        THEN: Cache key is deleted
        """
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Invalidate cache
        await resolver.invalidate_kb_settings_cache(sample_kb_id)

        # THEN: Cache key deleted
        expected_key = f"kb_settings:{sample_kb_id}"
        mock_redis.delete.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_multiple_requests_use_cache(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: Multiple requests for same KB settings
        WHEN: Second request comes after first
        THEN: Second request uses cache (DB called only once)
        """
        # First request: cache miss
        mock_redis.get.return_value = None
        kb_settings_dict = {"generation": {"temperature": 0.6}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: First request
        result1 = await resolver._get_kb_settings_cached(sample_kb_id)

        # Simulate cache hit for second request
        cached_settings = KBSettings(generation=GenerationConfig(temperature=0.6))
        mock_redis.get.return_value = cached_settings.model_dump_json()

        # WHEN: Second request
        result2 = await resolver._get_kb_settings_cached(sample_kb_id)

        # THEN: DB called only once, cache used for second
        assert mock_session.execute.call_count == 1
        assert result1.generation.temperature == 0.6
        assert result2.generation.temperature == 0.6


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestKBConfigResolverEdgeCases:
    """Tests for edge cases and error handling."""

    def test_resolve_param_with_boolean_false_value(self, mock_session, mock_redis):
        """
        GIVEN: resolve_param called with request_value=False
        WHEN: False is a valid boolean value
        THEN: Returns False (not treated as None)
        """
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        kb_settings = {"enabled": True}

        # WHEN: Call resolve_param with False
        result = resolver.resolve_param(
            param_name="enabled",
            request_value=False,
            kb_settings=kb_settings,
            system_default=True,
        )

        # THEN: False wins (not treated as None)
        assert result is False

    @pytest.mark.asyncio
    async def test_kb_not_found_raises_value_error(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: KB not found in database
        WHEN: _get_kb_settings_cached is called
        THEN: Raises ValueError
        """
        # Mock cache miss and None from DB
        mock_redis.get.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_db_result_for_settings(None))

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN/THEN: Raises ValueError
        with pytest.raises(ValueError, match="Knowledge base not found"):
            await resolver._get_kb_settings_cached(sample_kb_id)

    @pytest.mark.asyncio
    async def test_cache_error_falls_back_to_db(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: Redis raises an error on get
        WHEN: _get_kb_settings_cached is called
        THEN: Falls back to database gracefully
        """
        # Mock Redis error
        mock_redis.get.side_effect = Exception("Redis connection failed")

        # Mock DB result
        mock_session.execute = AsyncMock(return_value=mock_db_result_for_settings({}))

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Get KB settings (cache error should be handled)
        result = await resolver._get_kb_settings_cached(sample_kb_id)

        # THEN: Falls back to DB successfully
        assert isinstance(result, KBSettings)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_set_error_does_not_fail_request(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: Redis raises an error on setex
        WHEN: _get_kb_settings_cached is called
        THEN: Returns result without failing (cache set error logged)
        """
        # Mock cache miss
        mock_redis.get.return_value = None
        # Mock cache set error
        mock_redis.setex.side_effect = Exception("Redis write failed")

        # Mock DB result
        mock_session.execute = AsyncMock(return_value=mock_db_result_for_settings({}))

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Get KB settings (cache set error should be handled)
        result = await resolver._get_kb_settings_cached(sample_kb_id)

        # THEN: Returns result despite cache error
        assert isinstance(result, KBSettings)

    @pytest.mark.asyncio
    async def test_invalidate_cache_error_does_not_raise(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: Redis raises an error on delete
        WHEN: invalidate_kb_settings_cache is called
        THEN: Does not raise (error is logged)
        """
        # Mock Redis error
        mock_redis.delete.side_effect = Exception("Redis delete failed")

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN/THEN: Does not raise
        await resolver.invalidate_kb_settings_cache(sample_kb_id)


# =============================================================================
# Service Initialization Tests
# =============================================================================


class TestKBConfigResolverInit:
    """Tests for KBConfigResolver initialization."""

    def test_init_with_dependencies(self, mock_session, mock_redis):
        """
        GIVEN: Dependencies provided
        WHEN: KBConfigResolver is initialized
        THEN: Dependencies are stored correctly
        """
        # WHEN: Initialize resolver
        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # THEN: Dependencies stored
        assert resolver._session is mock_session
        assert resolver._redis is mock_redis

    def test_cache_constants_defined(self):
        """
        GIVEN: KBConfigResolver class
        WHEN: Checking cache constants
        THEN: TTL and key prefix are defined correctly
        """
        # THEN: Constants defined
        assert KBConfigResolver.CACHE_TTL == 300  # 5 minutes
        assert KBConfigResolver.CACHE_KEY_PREFIX == "kb_settings:"


# =============================================================================
# Dependency Injection Factory Tests
# =============================================================================


class TestGetKBConfigResolver:
    """Tests for get_kb_config_resolver factory function."""

    @pytest.mark.asyncio
    async def test_get_kb_config_resolver_returns_instance(
        self, mock_session, mock_redis
    ):
        """
        GIVEN: Session and Redis dependencies
        WHEN: get_kb_config_resolver is called
        THEN: Returns configured KBConfigResolver instance
        """
        # WHEN: Call factory function
        resolver = await get_kb_config_resolver(mock_session, mock_redis)

        # THEN: Returns instance with dependencies
        assert isinstance(resolver, KBConfigResolver)
        assert resolver._session is mock_session
        assert resolver._redis is mock_redis


# =============================================================================
# Full Resolution Flow Tests
# =============================================================================


class TestFullResolutionFlow:
    """Tests for complete configuration resolution workflows."""

    @pytest.mark.asyncio
    async def test_full_generation_resolution_with_all_layers(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: Config values at request, KB, and system level
        WHEN: resolve_generation_config is called
        THEN: Returns merged config respecting precedence
        """
        # Mock cache miss and DB result
        # KB has: temperature=0.5, max_tokens=4096
        kb_settings_dict = {"generation": {"temperature": 0.5, "max_tokens": 4096}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # Request has: temperature=0.9 (overrides KB)
        request_overrides = {"temperature": 0.9}

        # WHEN: Resolve generation config
        result = await resolver.resolve_generation_config(
            sample_kb_id, request_overrides
        )

        # THEN: Correct precedence
        assert result.temperature == 0.9  # Request wins
        assert result.max_tokens == 4096  # KB value (no request override)
        assert result.top_p == 0.9  # System default (not in KB or request)
        assert result.top_k == 40  # System default

    @pytest.mark.asyncio
    async def test_full_retrieval_resolution_with_all_layers(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: Config values at request, KB, and system level
        WHEN: resolve_retrieval_config is called
        THEN: Returns merged config respecting precedence
        """
        # Mock cache miss and DB result
        # KB has: top_k=20, method=hybrid
        kb_settings_dict = {"retrieval": {"top_k": 20, "method": "hybrid"}}
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # Request has: top_k=5 (overrides KB)
        request_overrides = {"top_k": 5}

        # WHEN: Resolve retrieval config
        result = await resolver.resolve_retrieval_config(
            sample_kb_id, request_overrides
        )

        # THEN: Correct precedence
        assert result.top_k == 5  # Request wins
        assert result.method == RetrievalMethod.HYBRID  # KB value
        assert result.similarity_threshold == 0.7  # System default

    @pytest.mark.asyncio
    async def test_get_kb_settings_public_accessor(
        self, mock_session, mock_redis, sample_kb_id
    ):
        """
        GIVEN: KB with custom settings
        WHEN: get_kb_settings is called
        THEN: Returns full KBSettings object
        """
        # Mock cache miss and DB result
        kb_settings_dict = {
            "generation": {"temperature": 0.5},
            "retrieval": {"top_k": 20},
        }
        mock_session.execute = AsyncMock(
            return_value=mock_db_result_for_settings(kb_settings_dict)
        )

        resolver = KBConfigResolver(
            session=mock_session,
            redis=mock_redis,
        )

        # WHEN: Call public accessor
        result = await resolver.get_kb_settings(sample_kb_id)

        # THEN: Returns full KBSettings
        assert isinstance(result, KBSettings)
        assert result.generation.temperature == 0.5
        assert result.retrieval.top_k == 20
