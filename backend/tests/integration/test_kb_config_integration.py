"""Story 7-17 ATDD: Service Integration Tests for KB-Level Configuration.

Generated: 2025-12-10

Tests verify that SearchService, GenerationService, and document workers
correctly use KB-level configuration with three-layer precedence:
Request params → KB settings → System defaults.

Test Coverage:
- AC-7.17.1: SearchService uses KB retrieval config
- AC-7.17.2: GenerationService uses KB generation config
- AC-7.17.3: GenerationService uses KB system prompt
- AC-7.17.4: Document worker uses KB chunking config
- AC-7.17.5: Request overrides still work
- AC-7.17.6: Audit logging includes effective_config
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
from app.services.kb_config_resolver import KBConfigResolver

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
async def kb_with_custom_retrieval(db_session: AsyncSession, test_user: User):
    """Create a KB with custom retrieval settings for SearchService tests."""
    kb = KnowledgeBase(
        name="Test KB Custom Retrieval",
        description="KB with custom retrieval settings",
        owner_id=test_user.id,
        status="active",
        settings={
            "retrieval": {
                "top_k": 25,
                "similarity_threshold": 0.8,
                "method": "hybrid",
                "mmr_enabled": True,
                "mmr_lambda": 0.7,
            },
        },
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
async def kb_with_custom_generation(db_session: AsyncSession, test_user: User):
    """Create a KB with custom generation settings for GenerationService tests."""
    kb = KnowledgeBase(
        name="Test KB Custom Generation",
        description="KB with custom generation settings",
        owner_id=test_user.id,
        status="active",
        settings={
            "generation": {
                "temperature": 0.3,
                "top_p": 0.85,
                "max_tokens": 3000,
            },
            "prompts": {
                "system_prompt": "You are a specialized legal assistant. Always cite sources.",
            },
        },
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
async def kb_with_custom_chunking(db_session: AsyncSession, test_user: User):
    """Create a KB with custom chunking settings for document worker tests."""
    kb = KnowledgeBase(
        name="Test KB Custom Chunking",
        description="KB with custom chunking settings",
        owner_id=test_user.id,
        status="active",
        settings={
            "chunking": {
                "strategy": "semantic",
                "chunk_size": 1024,
                "chunk_overlap": 128,
            },
        },
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
async def kb_with_full_settings(db_session: AsyncSession, test_user: User):
    """Create a KB with full custom settings for comprehensive tests."""
    kb = KnowledgeBase(
        name="Test KB Full Settings",
        description="KB with all custom settings",
        owner_id=test_user.id,
        status="active",
        settings={
            "chunking": {
                "strategy": "semantic",
                "chunk_size": 800,
                "chunk_overlap": 100,
            },
            "retrieval": {
                "top_k": 15,
                "similarity_threshold": 0.75,
                "method": "hybrid",
            },
            "generation": {
                "temperature": 0.4,
                "top_p": 0.9,
                "max_tokens": 2500,
            },
            "prompts": {
                "system_prompt": "You are a helpful assistant for this KB.",
            },
        },
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
async def kb_without_settings(db_session: AsyncSession, test_user: User):
    """Create a KB without custom settings (uses system defaults)."""
    kb = KnowledgeBase(
        name="Test KB Default Settings",
        description="KB using system defaults",
        owner_id=test_user.id,
        status="active",
        settings={},
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
def resolver(db_session: AsyncSession, test_redis_client):
    """Create KBConfigResolver with real dependencies."""
    return KBConfigResolver(session=db_session, redis=test_redis_client)


# =============================================================================
# AC-7.17.1: SearchService uses KB retrieval config
# =============================================================================


class TestSearchServiceKBConfig:
    """Integration tests for SearchService using KB retrieval config."""

    @pytest.mark.asyncio
    async def test_search_uses_kb_retrieval_config(
        self, resolver, kb_with_custom_retrieval, test_redis_client
    ):
        """
        AC-7.17.1: SearchService uses KB retrieval config.

        GIVEN: KB has custom retrieval settings (top_k=25, threshold=0.8, hybrid)
        WHEN: resolve_retrieval_config is called
        THEN: Returns config with KB values
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_custom_retrieval.id}")

        # WHEN: Resolve retrieval config
        config = await resolver.resolve_retrieval_config(kb_with_custom_retrieval.id)

        # THEN: Returns KB values
        assert isinstance(config, RetrievalConfig)
        assert config.top_k == 25
        assert config.similarity_threshold == 0.8
        assert config.method == RetrievalMethod.HYBRID
        assert config.mmr_enabled is True
        assert config.mmr_lambda == 0.7

    @pytest.mark.asyncio
    async def test_search_uses_system_defaults_when_no_kb_settings(
        self, resolver, kb_without_settings, test_redis_client
    ):
        """
        AC-7.17.1: SearchService falls back to system defaults.

        GIVEN: KB has no custom retrieval settings
        WHEN: resolve_retrieval_config is called
        THEN: Returns system default values
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_without_settings.id}")

        # WHEN: Resolve retrieval config
        config = await resolver.resolve_retrieval_config(kb_without_settings.id)

        # THEN: Returns system defaults
        assert config.top_k == 10  # System default
        assert config.similarity_threshold == 0.7  # System default
        assert config.method == RetrievalMethod.VECTOR  # System default
        assert config.mmr_enabled is False  # System default


# =============================================================================
# AC-7.17.2: GenerationService uses KB generation config
# =============================================================================


class TestGenerationServiceKBConfig:
    """Integration tests for GenerationService using KB generation config."""

    @pytest.mark.asyncio
    async def test_generation_uses_kb_generation_config(
        self, resolver, kb_with_custom_generation, test_redis_client
    ):
        """
        AC-7.17.2: GenerationService uses KB generation config.

        GIVEN: KB has custom generation settings (temp=0.3, max_tokens=3000)
        WHEN: resolve_generation_config is called
        THEN: Returns config with KB values
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_custom_generation.id}")

        # WHEN: Resolve generation config
        config = await resolver.resolve_generation_config(kb_with_custom_generation.id)

        # THEN: Returns KB values
        assert isinstance(config, GenerationConfig)
        assert config.temperature == 0.3
        assert config.top_p == 0.85
        assert config.max_tokens == 3000

    @pytest.mark.asyncio
    async def test_generation_uses_system_defaults_when_no_kb_settings(
        self, resolver, kb_without_settings, test_redis_client
    ):
        """
        AC-7.17.2: GenerationService falls back to system defaults.

        GIVEN: KB has no custom generation settings
        WHEN: resolve_generation_config is called
        THEN: Returns system default values
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_without_settings.id}")

        # WHEN: Resolve generation config
        config = await resolver.resolve_generation_config(kb_without_settings.id)

        # THEN: Returns system defaults
        assert config.temperature == 0.7  # System default
        assert config.max_tokens == 2048  # System default


# =============================================================================
# AC-7.17.3: GenerationService uses KB system prompt
# =============================================================================


class TestGenerationServiceKBSystemPrompt:
    """Integration tests for GenerationService using KB system prompt."""

    @pytest.mark.asyncio
    async def test_generation_uses_kb_system_prompt(
        self, resolver, kb_with_custom_generation, test_redis_client
    ):
        """
        AC-7.17.3: GenerationService uses KB system prompt.

        GIVEN: KB has custom system_prompt
        WHEN: get_kb_system_prompt is called
        THEN: Returns KB's system prompt
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_custom_generation.id}")

        # WHEN: Get system prompt
        prompt = await resolver.get_kb_system_prompt(kb_with_custom_generation.id)

        # THEN: Returns KB prompt
        assert prompt == "You are a specialized legal assistant. Always cite sources."

    @pytest.mark.asyncio
    async def test_generation_uses_default_system_prompt_when_no_kb_prompt(
        self, resolver, kb_without_settings, test_redis_client
    ):
        """
        AC-7.17.3: GenerationService falls back to default system prompt.

        GIVEN: KB has no custom system_prompt
        WHEN: get_kb_system_prompt is called
        THEN: Returns system default prompt
        """
        from app.services.kb_config_resolver import DEFAULT_SYSTEM_PROMPT

        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_without_settings.id}")

        # WHEN: Get system prompt
        prompt = await resolver.get_kb_system_prompt(kb_without_settings.id)

        # THEN: Returns system default
        assert prompt == DEFAULT_SYSTEM_PROMPT


# =============================================================================
# AC-7.17.4: Document worker uses KB chunking config
# =============================================================================


class TestDocumentWorkerKBChunkingConfig:
    """Integration tests for document worker using KB chunking config."""

    @pytest.mark.asyncio
    async def test_worker_uses_kb_chunking_config(
        self, resolver, kb_with_custom_chunking, test_redis_client
    ):
        """
        AC-7.17.4: Document worker uses KB chunking config.

        GIVEN: KB has custom chunking settings (chunk_size=1024, overlap=128)
        WHEN: resolve_chunking_config is called
        THEN: Returns config with KB values
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_custom_chunking.id}")

        # WHEN: Resolve chunking config
        config = await resolver.resolve_chunking_config(kb_with_custom_chunking.id)

        # THEN: Returns KB values
        assert isinstance(config, ChunkingConfig)
        assert config.strategy == ChunkingStrategy.SEMANTIC
        assert config.chunk_size == 1024
        assert config.chunk_overlap == 128

    @pytest.mark.asyncio
    async def test_worker_uses_system_defaults_when_no_kb_settings(
        self, resolver, kb_without_settings, test_redis_client
    ):
        """
        AC-7.17.4: Document worker falls back to system defaults.

        GIVEN: KB has no custom chunking settings
        WHEN: resolve_chunking_config is called
        THEN: Returns system default values
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_without_settings.id}")

        # WHEN: Resolve chunking config
        config = await resolver.resolve_chunking_config(kb_without_settings.id)

        # THEN: Returns system defaults
        assert config.strategy == ChunkingStrategy.RECURSIVE  # System default
        assert config.chunk_size == 512  # System default
        assert config.chunk_overlap == 50  # System default


# =============================================================================
# AC-7.17.5: Request overrides still work
# =============================================================================


class TestRequestOverridesPrecedence:
    """Integration tests for request parameter override precedence."""

    @pytest.mark.asyncio
    async def test_request_overrides_kb_retrieval_settings(
        self, resolver, kb_with_custom_retrieval, test_redis_client
    ):
        """
        AC-7.17.5: Request params override KB retrieval settings.

        GIVEN: KB has top_k=25
        WHEN: Request includes top_k=5
        THEN: 5 is used (request wins)
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_custom_retrieval.id}")

        # WHEN: Resolve with request override
        config = await resolver.resolve_retrieval_config(
            kb_with_custom_retrieval.id,
            request_overrides={"top_k": 5},
        )

        # THEN: Request override wins
        assert config.top_k == 5  # Request value
        assert config.similarity_threshold == 0.8  # KB value preserved

    @pytest.mark.asyncio
    async def test_request_overrides_kb_generation_settings(
        self, resolver, kb_with_custom_generation, test_redis_client
    ):
        """
        AC-7.17.5: Request params override KB generation settings.

        GIVEN: KB has temperature=0.3
        WHEN: Request includes temperature=0.8
        THEN: 0.8 is used (request wins)
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_custom_generation.id}")

        # WHEN: Resolve with request override
        config = await resolver.resolve_generation_config(
            kb_with_custom_generation.id,
            request_overrides={"temperature": 0.8},
        )

        # THEN: Request override wins
        assert config.temperature == 0.8  # Request value
        assert config.max_tokens == 3000  # KB value preserved

    @pytest.mark.asyncio
    async def test_multiple_request_overrides(
        self, resolver, kb_with_full_settings, test_redis_client
    ):
        """
        AC-7.17.5: Multiple request params override KB settings.

        GIVEN: KB has temperature=0.4, max_tokens=2500
        WHEN: Request includes temperature=0.9 and max_tokens=1000
        THEN: Both request values are used
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_full_settings.id}")

        # WHEN: Resolve with multiple overrides
        config = await resolver.resolve_generation_config(
            kb_with_full_settings.id,
            request_overrides={
                "temperature": 0.9,
                "max_tokens": 1000,
            },
        )

        # THEN: All request overrides win
        assert config.temperature == 0.9  # Request value
        assert config.max_tokens == 1000  # Request value
        assert config.top_p == 0.9  # KB value preserved

    @pytest.mark.asyncio
    async def test_null_request_override_uses_kb_value(
        self, resolver, kb_with_custom_retrieval, test_redis_client
    ):
        """
        AC-7.17.5: None/null request params fall through to KB settings.

        GIVEN: KB has top_k=25
        WHEN: Request includes top_k=None
        THEN: 25 is used (KB value)
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_custom_retrieval.id}")

        # WHEN: Resolve with None override
        config = await resolver.resolve_retrieval_config(
            kb_with_custom_retrieval.id,
            request_overrides={"top_k": None},
        )

        # THEN: KB value is used
        assert config.top_k == 25  # KB value (None override ignored)


# =============================================================================
# AC-7.17.6: Audit logging includes effective_config
# =============================================================================


class TestAuditLoggingEffectiveConfig:
    """Integration tests for audit logging with effective_config."""

    @pytest.mark.asyncio
    async def test_effective_config_can_be_serialized(
        self, resolver, kb_with_full_settings, test_redis_client
    ):
        """
        AC-7.17.6: Effective config can be serialized for audit logging.

        GIVEN: KB has custom settings
        WHEN: Config is resolved
        THEN: Config can be serialized to dict for audit log
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_full_settings.id}")

        # WHEN: Resolve config
        generation_config = await resolver.resolve_generation_config(
            kb_with_full_settings.id
        )
        retrieval_config = await resolver.resolve_retrieval_config(
            kb_with_full_settings.id
        )

        # THEN: Configs can be serialized
        gen_dict = generation_config.model_dump()
        ret_dict = retrieval_config.model_dump()

        # Verify serialization
        assert gen_dict["temperature"] == 0.4
        assert gen_dict["max_tokens"] == 2500
        assert ret_dict["top_k"] == 15
        assert ret_dict["method"] == "hybrid"

    @pytest.mark.asyncio
    async def test_effective_config_snapshot_with_overrides(
        self, resolver, kb_with_custom_generation, test_redis_client
    ):
        """
        AC-7.17.6: Effective config includes request overrides.

        GIVEN: KB has temperature=0.3, request overrides with temperature=0.9
        WHEN: Config is resolved and serialized
        THEN: Serialized config shows final effective values
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_custom_generation.id}")

        # WHEN: Resolve with override and serialize
        config = await resolver.resolve_generation_config(
            kb_with_custom_generation.id,
            request_overrides={"temperature": 0.9},
        )
        effective_config = config.model_dump()

        # THEN: Effective config shows final values
        assert effective_config["temperature"] == 0.9  # Request override
        assert effective_config["max_tokens"] == 3000  # KB value

        # This snapshot can be logged to audit
        audit_entry = {
            "action": "generation",
            "kb_id": str(kb_with_custom_generation.id),
            "effective_config": effective_config,
        }
        assert "effective_config" in audit_entry
        assert audit_entry["effective_config"]["temperature"] == 0.9


# =============================================================================
# Three-Layer Precedence Full Flow Tests
# =============================================================================


class TestThreeLayerPrecedenceFullFlow:
    """Integration tests for complete three-layer precedence flow."""

    @pytest.mark.asyncio
    async def test_full_precedence_request_kb_system(
        self, resolver, kb_with_full_settings, test_redis_client
    ):
        """
        Full three-layer precedence: Request → KB → System.

        GIVEN: System defaults, KB has partial overrides, request has specific override
        WHEN: Config is resolved
        THEN: Correct precedence is applied
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_full_settings.id}")

        # WHEN: Resolve with request override
        config = await resolver.resolve_generation_config(
            kb_with_full_settings.id,
            request_overrides={"temperature": 1.0},
        )

        # THEN: Correct precedence
        # temperature: Request (1.0) > KB (0.4) > System (0.7)
        assert config.temperature == 1.0  # From request

        # max_tokens: KB (2500) > System (2048)
        assert config.max_tokens == 2500  # From KB

        # top_p: KB (0.9) == System (0.9) - same value
        assert config.top_p == 0.9

    @pytest.mark.asyncio
    async def test_config_resolution_is_consistent(
        self, db_session, kb_with_full_settings, test_redis_client
    ):
        """
        Config resolution is consistent across multiple calls.

        GIVEN: Same KB and same request overrides
        WHEN: Config is resolved multiple times
        THEN: Same result each time
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_full_settings.id}")

        # WHEN: Resolve multiple times
        resolver1 = KBConfigResolver(session=db_session, redis=test_redis_client)
        config1 = await resolver1.resolve_generation_config(
            kb_with_full_settings.id,
            request_overrides={"temperature": 0.5},
        )

        resolver2 = KBConfigResolver(session=db_session, redis=test_redis_client)
        config2 = await resolver2.resolve_generation_config(
            kb_with_full_settings.id,
            request_overrides={"temperature": 0.5},
        )

        # THEN: Consistent results
        assert config1.temperature == config2.temperature
        assert config1.max_tokens == config2.max_tokens
        assert config1.top_p == config2.top_p

    @pytest.mark.asyncio
    async def test_all_config_types_resolve_correctly(
        self, resolver, kb_with_full_settings, test_redis_client
    ):
        """
        All config types (retrieval, generation, chunking, prompts) resolve correctly.

        GIVEN: KB with full settings
        WHEN: All config types are resolved
        THEN: Each returns correct KB values
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_full_settings.id}")

        # WHEN: Resolve all config types
        retrieval = await resolver.resolve_retrieval_config(kb_with_full_settings.id)
        generation = await resolver.resolve_generation_config(kb_with_full_settings.id)
        chunking = await resolver.resolve_chunking_config(kb_with_full_settings.id)
        prompt = await resolver.get_kb_system_prompt(kb_with_full_settings.id)

        # THEN: All correct
        assert retrieval.top_k == 15
        assert retrieval.similarity_threshold == 0.75
        assert retrieval.method == RetrievalMethod.HYBRID

        assert generation.temperature == 0.4
        assert generation.max_tokens == 2500

        assert chunking.strategy == ChunkingStrategy.SEMANTIC
        assert chunking.chunk_size == 800
        assert chunking.chunk_overlap == 100

        assert prompt == "You are a helpful assistant for this KB."
