"""Integration tests for KBConfigResolver service.

Story 7-13: KBConfigResolver Service
GREEN PHASE - Integration tests with real database and Redis.

Test Coverage:
- [P0] AC-7.13.4: resolve_generation_config with real KB
- [P0] AC-7.13.5: resolve_retrieval_config with real KB
- [P1] AC-7.13.6: resolve_chunking_config with real KB
- [P1] AC-7.13.7: get_kb_system_prompt with real KB
- [P0] AC-7.13.8: Redis caching integration with real Redis

Knowledge Base References:
- test-quality.md: Given-When-Then structure
- test-levels-framework.md: Integration test patterns
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.kb_settings import (
    ChunkingConfig,
    ChunkingStrategy,
    GenerationConfig,
    RetrievalConfig,
    RetrievalMethod,
)
from app.services.kb_config_resolver import (
    DEFAULT_SYSTEM_PROMPT,
    KBConfigResolver,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for KB ownership."""
    user = User(
        email=f"testuser-{uuid4().hex[:8]}@example.com",
        hashed_password="hashed_test_password",
        is_superuser=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def kb_with_settings(db_session: AsyncSession, test_user: User):
    """Create a KB with custom settings for testing."""
    kb = KnowledgeBase(
        name="Test KB with Settings",
        description="KB with full custom settings",
        owner_id=test_user.id,
        status="active",
        settings={
            "chunking": {
                "strategy": "semantic",
                "chunk_size": 1024,
                "chunk_overlap": 100,
            },
            "retrieval": {
                "top_k": 20,
                "similarity_threshold": 0.85,
                "method": "hybrid",
            },
            "generation": {
                "temperature": 0.5,
                "top_p": 0.85,
                "max_tokens": 4096,
            },
            "prompts": {
                "system_prompt": "You are an expert assistant for this knowledge base.",
            },
        },
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
async def kb_without_settings(db_session: AsyncSession, test_user: User):
    """Create a KB without custom settings (uses defaults)."""
    kb = KnowledgeBase(
        name="Test KB Default Settings",
        description="KB using default settings",
        owner_id=test_user.id,
        status="active",
        settings={},  # Empty settings = use defaults
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
async def kb_with_partial_settings(db_session: AsyncSession, test_user: User):
    """Create a KB with partial settings for testing merging."""
    kb = KnowledgeBase(
        name="Test KB Partial Settings",
        description="KB with partial settings",
        owner_id=test_user.id,
        status="active",
        settings={
            "generation": {
                "temperature": 0.3,
                # Other generation settings not specified
            },
            "retrieval": {
                "top_k": 25,
                # Other retrieval settings not specified
            },
        },
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
def resolver(db_session: AsyncSession, test_redis_client):
    """Create KBConfigResolver with real dependencies."""
    return KBConfigResolver(session=db_session, redis=test_redis_client)


# =============================================================================
# AC-7.13.4: Resolve generation config with real KB
# =============================================================================


class TestResolveGenerationConfigIntegration:
    """Integration tests for generation config resolution with real KB."""

    @pytest.mark.asyncio
    async def test_resolve_generation_config_returns_kb_values(
        self, resolver, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB has custom generation settings
        WHEN: resolve_generation_config is called
        THEN: Returns GenerationConfig with KB values
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_with_settings.id}")

        # WHEN: Resolve generation config
        result = await resolver.resolve_generation_config(kb_with_settings.id)

        # THEN: Returns KB values
        assert isinstance(result, GenerationConfig)
        assert result.temperature == 0.5
        assert result.top_p == 0.85
        assert result.max_tokens == 4096

    @pytest.mark.asyncio
    async def test_resolve_generation_config_with_request_override(
        self, resolver, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB has temperature=0.5
        WHEN: resolve_generation_config called with temperature=0.9 override
        THEN: Returns request value (0.9) overriding KB value
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_with_settings.id}")

        # WHEN: Resolve with override
        result = await resolver.resolve_generation_config(
            kb_with_settings.id,
            request_overrides={"temperature": 0.9},
        )

        # THEN: Request override wins
        assert result.temperature == 0.9
        assert result.max_tokens == 4096  # KB value preserved

    @pytest.mark.asyncio
    async def test_resolve_generation_config_uses_system_defaults(
        self, resolver, kb_without_settings, test_redis_client
    ):
        """
        GIVEN: KB has no custom generation settings
        WHEN: resolve_generation_config is called
        THEN: Returns system default values
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_without_settings.id}")

        # WHEN: Resolve generation config
        result = await resolver.resolve_generation_config(kb_without_settings.id)

        # THEN: Returns system defaults
        assert isinstance(result, GenerationConfig)
        assert result.temperature == 0.7  # System default
        assert result.max_tokens == 2048  # System default

    @pytest.mark.asyncio
    async def test_resolve_generation_config_merges_partial_settings(
        self, resolver, kb_with_partial_settings, test_redis_client
    ):
        """
        GIVEN: KB has partial generation settings (only temperature)
        WHEN: resolve_generation_config is called
        THEN: Returns merged config with system defaults for missing fields
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_with_partial_settings.id}")

        # WHEN: Resolve generation config
        result = await resolver.resolve_generation_config(kb_with_partial_settings.id)

        # THEN: Merged from KB and defaults
        assert result.temperature == 0.3  # From KB
        assert result.max_tokens == 2048  # System default


# =============================================================================
# AC-7.13.5: Resolve retrieval config with real KB
# =============================================================================


class TestResolveRetrievalConfigIntegration:
    """Integration tests for retrieval config resolution with real KB."""

    @pytest.mark.asyncio
    async def test_resolve_retrieval_config_returns_kb_values(
        self, resolver, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB has custom retrieval settings
        WHEN: resolve_retrieval_config is called
        THEN: Returns RetrievalConfig with KB values
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_with_settings.id}")

        # WHEN: Resolve retrieval config
        result = await resolver.resolve_retrieval_config(kb_with_settings.id)

        # THEN: Returns KB values
        assert isinstance(result, RetrievalConfig)
        assert result.top_k == 20
        assert result.similarity_threshold == 0.85
        assert result.method == RetrievalMethod.HYBRID

    @pytest.mark.asyncio
    async def test_resolve_retrieval_config_with_request_override(
        self, resolver, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB has top_k=20
        WHEN: resolve_retrieval_config called with top_k=5 override
        THEN: Returns request value overriding KB value
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_with_settings.id}")

        # WHEN: Resolve with override
        result = await resolver.resolve_retrieval_config(
            kb_with_settings.id,
            request_overrides={"top_k": 5},
        )

        # THEN: Request override wins
        assert result.top_k == 5
        assert result.similarity_threshold == 0.85  # KB value preserved

    @pytest.mark.asyncio
    async def test_resolve_retrieval_config_uses_system_defaults(
        self, resolver, kb_without_settings, test_redis_client
    ):
        """
        GIVEN: KB has no custom retrieval settings
        WHEN: resolve_retrieval_config is called
        THEN: Returns system default values
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_without_settings.id}")

        # WHEN: Resolve retrieval config
        result = await resolver.resolve_retrieval_config(kb_without_settings.id)

        # THEN: Returns system defaults
        assert isinstance(result, RetrievalConfig)
        assert result.top_k == 10  # System default
        assert result.similarity_threshold == 0.7  # System default
        assert result.method == RetrievalMethod.VECTOR  # System default


# =============================================================================
# AC-7.13.6: Resolve chunking config with real KB
# =============================================================================


class TestResolveChunkingConfigIntegration:
    """Integration tests for chunking config resolution with real KB."""

    @pytest.mark.asyncio
    async def test_resolve_chunking_config_returns_kb_values(
        self, resolver, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB has custom chunking settings
        WHEN: resolve_chunking_config is called
        THEN: Returns ChunkingConfig with KB values
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_with_settings.id}")

        # WHEN: Resolve chunking config
        result = await resolver.resolve_chunking_config(kb_with_settings.id)

        # THEN: Returns KB values
        assert isinstance(result, ChunkingConfig)
        assert result.strategy == ChunkingStrategy.SEMANTIC
        assert result.chunk_size == 1024
        assert result.chunk_overlap == 100

    @pytest.mark.asyncio
    async def test_resolve_chunking_config_uses_system_defaults(
        self, resolver, kb_without_settings, test_redis_client
    ):
        """
        GIVEN: KB has no custom chunking settings
        WHEN: resolve_chunking_config is called
        THEN: Returns system default values
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_without_settings.id}")

        # WHEN: Resolve chunking config
        result = await resolver.resolve_chunking_config(kb_without_settings.id)

        # THEN: Returns system defaults
        assert isinstance(result, ChunkingConfig)
        assert result.strategy == ChunkingStrategy.RECURSIVE  # System default
        assert result.chunk_size == 512  # System default
        assert result.chunk_overlap == 50  # System default


# =============================================================================
# AC-7.13.7: Get KB system prompt with real KB
# =============================================================================


class TestGetKBSystemPromptIntegration:
    """Integration tests for system prompt retrieval with real KB."""

    @pytest.mark.asyncio
    async def test_get_kb_system_prompt_returns_kb_prompt(
        self, resolver, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB has custom system_prompt
        WHEN: get_kb_system_prompt is called
        THEN: Returns KB's system prompt
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_with_settings.id}")

        # WHEN: Get system prompt
        result = await resolver.get_kb_system_prompt(kb_with_settings.id)

        # THEN: Returns KB prompt
        assert result == "You are an expert assistant for this knowledge base."

    @pytest.mark.asyncio
    async def test_get_kb_system_prompt_returns_system_default(
        self, resolver, kb_without_settings, test_redis_client
    ):
        """
        GIVEN: KB has no custom system_prompt
        WHEN: get_kb_system_prompt is called
        THEN: Returns system default prompt
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_without_settings.id}")

        # WHEN: Get system prompt
        result = await resolver.get_kb_system_prompt(kb_without_settings.id)

        # THEN: Returns system default
        assert result == DEFAULT_SYSTEM_PROMPT


# =============================================================================
# AC-7.13.8: Redis caching integration
# =============================================================================


class TestKBSettingsCachingIntegration:
    """Integration tests for KB settings caching with real Redis."""

    @pytest.mark.asyncio
    async def test_settings_cached_after_first_request(
        self, resolver, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB settings not in cache
        WHEN: resolve_generation_config called
        THEN: Settings are cached in Redis
        """
        cache_key = f"kb_settings:{kb_with_settings.id}"

        # Clear any existing cache
        await test_redis_client.delete(cache_key)

        # Verify cache is empty
        cached_before = await test_redis_client.get(cache_key)
        assert cached_before is None

        # WHEN: Resolve config (triggers cache)
        await resolver.resolve_generation_config(kb_with_settings.id)

        # THEN: Cache is populated
        cached_after = await test_redis_client.get(cache_key)
        assert cached_after is not None

    @pytest.mark.asyncio
    async def test_cached_settings_used_on_subsequent_requests(
        self, db_session, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB settings are cached
        WHEN: Multiple requests made
        THEN: Same cached value is returned
        """
        cache_key = f"kb_settings:{kb_with_settings.id}"

        # Clear cache
        await test_redis_client.delete(cache_key)

        # Create resolver and populate cache
        resolver1 = KBConfigResolver(session=db_session, redis=test_redis_client)
        result1 = await resolver1.resolve_generation_config(kb_with_settings.id)

        # Create new resolver (simulating new request)
        resolver2 = KBConfigResolver(session=db_session, redis=test_redis_client)
        result2 = await resolver2.resolve_generation_config(kb_with_settings.id)

        # THEN: Both return same values
        assert result1.temperature == result2.temperature
        assert result1.max_tokens == result2.max_tokens

    @pytest.mark.asyncio
    async def test_cache_ttl_is_5_minutes(
        self, resolver, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB settings are cached
        WHEN: Checking cache TTL
        THEN: TTL is approximately 300 seconds (5 minutes)
        """
        cache_key = f"kb_settings:{kb_with_settings.id}"

        # Clear any existing cache
        await test_redis_client.delete(cache_key)

        # WHEN: Resolve config to populate cache
        await resolver.resolve_generation_config(kb_with_settings.id)

        # THEN: TTL should be around 300 seconds
        ttl = await test_redis_client.ttl(cache_key)
        assert 290 <= ttl <= 300  # Allow small variance

    @pytest.mark.asyncio
    async def test_invalidate_cache_removes_cached_settings(
        self, resolver, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB settings are cached
        WHEN: invalidate_kb_settings_cache is called
        THEN: Cache is cleared
        """
        cache_key = f"kb_settings:{kb_with_settings.id}"

        # Ensure cache is populated
        await test_redis_client.delete(cache_key)
        await resolver.resolve_generation_config(kb_with_settings.id)

        # Verify cache exists
        cached_before = await test_redis_client.get(cache_key)
        assert cached_before is not None

        # WHEN: Invalidate cache
        await resolver.invalidate_kb_settings_cache(kb_with_settings.id)

        # THEN: Cache is cleared
        cached_after = await test_redis_client.get(cache_key)
        assert cached_after is None


# =============================================================================
# Error Handling Integration Tests
# =============================================================================


class TestErrorHandlingIntegration:
    """Integration tests for error handling with real dependencies."""

    @pytest.mark.asyncio
    async def test_nonexistent_kb_raises_value_error(
        self, db_session, test_redis_client
    ):
        """
        GIVEN: Non-existent KB ID
        WHEN: resolve_generation_config is called
        THEN: Raises ValueError
        """
        resolver = KBConfigResolver(session=db_session, redis=test_redis_client)
        fake_kb_id = uuid4()

        # WHEN/THEN: Raises ValueError
        with pytest.raises(ValueError, match="Knowledge base not found"):
            await resolver.resolve_generation_config(fake_kb_id)


# =============================================================================
# Full Resolution Flow Tests
# =============================================================================


class TestFullResolutionFlowIntegration:
    """Integration tests for complete configuration resolution workflows."""

    @pytest.mark.asyncio
    async def test_three_layer_precedence_with_real_data(
        self, resolver, kb_with_partial_settings, test_redis_client
    ):
        """
        GIVEN: KB with partial settings and request overrides
        WHEN: resolve_generation_config is called with overrides
        THEN: Returns correctly merged config from all three layers
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_with_partial_settings.id}")

        # KB has temperature=0.3, no max_tokens
        # Request overrides temperature=0.9
        # System default for max_tokens=2048

        # WHEN: Resolve with override
        result = await resolver.resolve_generation_config(
            kb_with_partial_settings.id,
            request_overrides={"temperature": 0.9},
        )

        # THEN: Correct three-layer precedence
        assert result.temperature == 0.9  # Request wins over KB's 0.3
        assert result.max_tokens == 2048  # System default (not in KB)
        assert result.top_p == 0.9  # System default

    @pytest.mark.asyncio
    async def test_get_kb_settings_returns_full_settings(
        self, resolver, kb_with_settings, test_redis_client
    ):
        """
        GIVEN: KB with full settings
        WHEN: get_kb_settings is called
        THEN: Returns complete KBSettings object
        """
        # Clear cache first
        await test_redis_client.delete(f"kb_settings:{kb_with_settings.id}")

        # WHEN: Get full settings
        result = await resolver.get_kb_settings(kb_with_settings.id)

        # THEN: Returns full KBSettings
        assert result.generation.temperature == 0.5
        assert result.retrieval.top_k == 20
        assert result.chunking.chunk_size == 1024
        assert (
            result.prompts.system_prompt
            == "You are an expert assistant for this knowledge base."
        )
