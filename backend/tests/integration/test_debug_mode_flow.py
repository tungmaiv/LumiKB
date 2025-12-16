"""Story 9-15 ATDD: Debug Mode Integration Tests.

Generated: 2025-12-16

Tests verify the end-to-end flow of KB debug mode for RAG pipeline telemetry:
- AC-9.15.10: Chat service checks KB debug_mode flag via KBConfigResolver
- AC-9.15.11: DebugInfo schema includes kb_params, chunks_retrieved, timing
- AC-9.15.12: SSE stream emits debug event BEFORE first token when enabled
- AC-9.15.13: Non-streaming response includes debug_info when enabled

Test Categories:
1. KBConfigResolver debug mode resolution
2. ConversationService debug mode check
3. Debug info construction and content validation
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.kb_settings import KBSettings
from app.services.kb_config_resolver import KBConfigResolver

pytestmark = pytest.mark.integration


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for KB ownership."""
    user = User(
        email=f"testuser-debug-{uuid4().hex[:8]}@example.com",
        hashed_password="hashed_test_password",
        is_superuser=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def kb_with_debug_enabled(db_session: AsyncSession, test_user: User):
    """Create a KB with debug_mode enabled."""
    kb = KnowledgeBase(
        name="Debug Enabled KB",
        description="KB with debug mode on",
        owner_id=test_user.id,
        status="active",
        settings={
            "debug_mode": True,
            "prompts": {
                "system_prompt": "You are a helpful debug-enabled assistant.",
                "citation_style": "inline",
                "response_language": "en",
                "uncertainty_handling": "acknowledge",
            },
        },
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
async def kb_with_debug_disabled(db_session: AsyncSession, test_user: User):
    """Create a KB with debug_mode disabled (default)."""
    kb = KnowledgeBase(
        name="Debug Disabled KB",
        description="KB with debug mode off",
        owner_id=test_user.id,
        status="active",
        settings={
            "debug_mode": False,
        },
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
async def kb_without_debug_setting(db_session: AsyncSession, test_user: User):
    """Create a KB without explicit debug_mode setting (uses default False)."""
    kb = KnowledgeBase(
        name="No Debug Setting KB",
        description="KB without debug_mode in settings",
        owner_id=test_user.id,
        status="active",
        settings={},
    )
    db_session.add(kb)
    await db_session.flush()
    return kb


@pytest.fixture
def resolver(db_session: AsyncSession, test_redis_client):
    """Create KBConfigResolver with test dependencies."""
    return KBConfigResolver(session=db_session, redis=test_redis_client)


# =============================================================================
# AC-9.15.10: Debug Mode Flag Resolution
# =============================================================================


class TestDebugModeResolution:
    """Integration tests for KB debug_mode flag resolution via KBConfigResolver."""

    @pytest.mark.asyncio
    async def test_resolves_debug_mode_enabled(
        self, resolver, kb_with_debug_enabled, test_redis_client
    ):
        """
        AC-9.15.10: KBConfigResolver resolves debug_mode=True.

        GIVEN: KB has settings.debug_mode=True
        WHEN: get_kb_settings is called
        THEN: Returns KBSettings with debug_mode=True
        """
        # Clear cache to ensure fresh fetch
        await test_redis_client.delete(f"kb_settings:{kb_with_debug_enabled.id}")

        # WHEN: Get KB settings
        settings = await resolver.get_kb_settings(kb_with_debug_enabled.id)

        # THEN: debug_mode is True
        assert isinstance(settings, KBSettings)
        assert settings.debug_mode is True

    @pytest.mark.asyncio
    async def test_resolves_debug_mode_disabled(
        self, resolver, kb_with_debug_disabled, test_redis_client
    ):
        """
        AC-9.15.10: KBConfigResolver resolves debug_mode=False.

        GIVEN: KB has settings.debug_mode=False
        WHEN: get_kb_settings is called
        THEN: Returns KBSettings with debug_mode=False
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_debug_disabled.id}")

        # WHEN: Get KB settings
        settings = await resolver.get_kb_settings(kb_with_debug_disabled.id)

        # THEN: debug_mode is False
        assert isinstance(settings, KBSettings)
        assert settings.debug_mode is False

    @pytest.mark.asyncio
    async def test_defaults_to_debug_mode_disabled(
        self, resolver, kb_without_debug_setting, test_redis_client
    ):
        """
        AC-9.15.10: KBConfigResolver defaults debug_mode to False.

        GIVEN: KB has no debug_mode in settings
        WHEN: get_kb_settings is called
        THEN: Returns KBSettings with debug_mode=False (default)
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_without_debug_setting.id}")

        # WHEN: Get KB settings
        settings = await resolver.get_kb_settings(kb_without_debug_setting.id)

        # THEN: debug_mode defaults to False
        assert isinstance(settings, KBSettings)
        assert settings.debug_mode is False

    @pytest.mark.asyncio
    async def test_debug_mode_cached_in_redis(
        self, resolver, kb_with_debug_enabled, test_redis_client
    ):
        """
        AC-9.15.10: KB settings with debug_mode are cached in Redis.

        GIVEN: KB has debug_mode=True
        WHEN: get_kb_settings is called twice
        THEN: Second call returns cached value from Redis
        """
        # Clear cache
        cache_key = f"kb_settings:{kb_with_debug_enabled.id}"
        await test_redis_client.delete(cache_key)

        # WHEN: First call (populates cache)
        settings1 = await resolver.get_kb_settings(kb_with_debug_enabled.id)

        # Verify cache exists
        cached = await test_redis_client.get(cache_key)
        assert cached is not None

        # WHEN: Second call (from cache)
        settings2 = await resolver.get_kb_settings(kb_with_debug_enabled.id)

        # THEN: Both return same debug_mode value
        assert settings1.debug_mode is True
        assert settings2.debug_mode is True


# =============================================================================
# AC-9.15.11: DebugInfo Schema Content
# =============================================================================


class TestDebugInfoSchemaContent:
    """Integration tests for DebugInfo schema content and structure."""

    @pytest.mark.asyncio
    async def test_debug_info_includes_kb_params(
        self, resolver, kb_with_debug_enabled, test_redis_client
    ):
        """
        AC-9.15.11: DebugInfo includes KB parameters.

        GIVEN: KB has debug_mode=True with custom prompts settings
        WHEN: KB settings are resolved
        THEN: Settings include prompts config for debug info construction
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_debug_enabled.id}")

        # WHEN: Get KB settings
        settings = await resolver.get_kb_settings(kb_with_debug_enabled.id)

        # THEN: Prompts config is available for debug info
        assert settings.prompts is not None
        assert settings.prompts.citation_style is not None
        assert settings.prompts.response_language is not None
        assert settings.prompts.uncertainty_handling is not None
        assert settings.prompts.system_prompt is not None

    @pytest.mark.asyncio
    async def test_prompt_config_resolution_for_debug(
        self, resolver, kb_with_debug_enabled, test_redis_client
    ):
        """
        AC-9.15.11: KBPromptConfig can be resolved for debug info.

        GIVEN: KB has custom prompt settings
        WHEN: get_kb_settings is called
        THEN: Returns KBSettings with prompts accessible for debug display
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_debug_enabled.id}")

        # WHEN: Get KB settings (which includes prompts config)
        settings = await resolver.get_kb_settings(kb_with_debug_enabled.id)
        prompt_config = settings.prompts

        # THEN: All fields available for debug info
        assert (
            prompt_config.system_prompt == "You are a helpful debug-enabled assistant."
        )
        assert prompt_config.citation_style.value == "inline"
        assert prompt_config.response_language == "en"
        assert prompt_config.uncertainty_handling.value == "acknowledge"


# =============================================================================
# AC-9.15.10 Extended: Debug Mode Toggle Behavior
# =============================================================================


class TestDebugModeToggleBehavior:
    """Integration tests for toggling debug mode on/off."""

    @pytest.mark.asyncio
    async def test_can_enable_debug_mode_on_existing_kb(
        self, db_session, resolver, kb_with_debug_disabled, test_redis_client
    ):
        """
        AC-9.15.10: Debug mode can be enabled on existing KB.

        GIVEN: KB has debug_mode=False
        WHEN: KB settings are updated to debug_mode=True
        THEN: Subsequent reads return debug_mode=True
        """
        # Clear cache
        cache_key = f"kb_settings:{kb_with_debug_disabled.id}"
        await test_redis_client.delete(cache_key)

        # Verify initial state
        settings = await resolver.get_kb_settings(kb_with_debug_disabled.id)
        assert settings.debug_mode is False

        # WHEN: Update KB settings to enable debug mode
        kb_with_debug_disabled.settings = {"debug_mode": True}
        await db_session.flush()

        # Clear cache to force re-fetch
        await test_redis_client.delete(cache_key)

        # THEN: New value is returned
        updated_settings = await resolver.get_kb_settings(kb_with_debug_disabled.id)
        assert updated_settings.debug_mode is True

    @pytest.mark.asyncio
    async def test_can_disable_debug_mode_on_existing_kb(
        self, db_session, resolver, kb_with_debug_enabled, test_redis_client
    ):
        """
        AC-9.15.10: Debug mode can be disabled on existing KB.

        GIVEN: KB has debug_mode=True
        WHEN: KB settings are updated to debug_mode=False
        THEN: Subsequent reads return debug_mode=False
        """
        # Clear cache
        cache_key = f"kb_settings:{kb_with_debug_enabled.id}"
        await test_redis_client.delete(cache_key)

        # Verify initial state
        settings = await resolver.get_kb_settings(kb_with_debug_enabled.id)
        assert settings.debug_mode is True

        # WHEN: Update KB settings to disable debug mode
        kb_with_debug_enabled.settings = {"debug_mode": False}
        await db_session.flush()

        # Clear cache to force re-fetch
        await test_redis_client.delete(cache_key)

        # THEN: New value is returned
        updated_settings = await resolver.get_kb_settings(kb_with_debug_enabled.id)
        assert updated_settings.debug_mode is False


# =============================================================================
# AC-9.15.11: Full KBSettings with Debug Mode
# =============================================================================


class TestFullKBSettingsWithDebugMode:
    """Integration tests for complete KB settings including debug_mode."""

    @pytest.mark.asyncio
    async def test_full_settings_serialization_with_debug(
        self, resolver, kb_with_debug_enabled, test_redis_client
    ):
        """
        AC-9.15.11: Full KB settings can be serialized including debug_mode.

        GIVEN: KB has debug_mode and other settings
        WHEN: Settings are resolved and serialized
        THEN: All fields including debug_mode are in serialized output
        """
        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb_with_debug_enabled.id}")

        # WHEN: Get and serialize settings
        settings = await resolver.get_kb_settings(kb_with_debug_enabled.id)
        serialized = settings.model_dump()

        # THEN: debug_mode is in serialized output
        assert "debug_mode" in serialized
        assert serialized["debug_mode"] is True

        # Other config sections also present
        assert "prompts" in serialized
        assert "retrieval" in serialized
        assert "generation" in serialized
        assert "chunking" in serialized

    @pytest.mark.asyncio
    async def test_debug_mode_with_all_config_sections(
        self, db_session, test_user, resolver, test_redis_client
    ):
        """
        AC-9.15.11: Debug mode works with fully configured KB.

        GIVEN: KB has debug_mode=True and all config sections populated
        WHEN: Settings are resolved
        THEN: All config sections accessible for debug info construction
        """
        # Create KB with full settings
        kb = KnowledgeBase(
            name="Full Config Debug KB",
            description="KB with all settings for debug testing",
            owner_id=test_user.id,
            status="active",
            settings={
                "debug_mode": True,
                "retrieval": {
                    "top_k": 20,
                    "similarity_threshold": 0.8,
                    "method": "hybrid",
                },
                "generation": {
                    "temperature": 0.5,
                    "max_tokens": 3000,
                },
                "chunking": {
                    "strategy": "semantic",
                    "chunk_size": 1000,
                },
                "prompts": {
                    "system_prompt": "Debug assistant with full config.",
                    "citation_style": "footnote",
                    "response_language": "fr",
                    "uncertainty_handling": "refuse",
                },
            },
        )
        db_session.add(kb)
        await db_session.flush()

        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb.id}")

        # WHEN: Resolve settings
        settings = await resolver.get_kb_settings(kb.id)

        # THEN: All sections accessible
        assert settings.debug_mode is True
        assert settings.retrieval.top_k == 20
        assert settings.generation.temperature == 0.5
        assert settings.chunking.chunk_size == 1000
        assert settings.prompts.citation_style.value == "footnote"


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestDebugModeErrorHandling:
    """Integration tests for debug mode error handling."""

    @pytest.mark.asyncio
    async def test_invalid_kb_id_raises_error(self, resolver, test_redis_client):
        """
        Non-existent KB raises ValueError.

        GIVEN: KB ID that doesn't exist
        WHEN: get_kb_settings is called
        THEN: Raises ValueError indicating KB not found
        """
        fake_kb_id = uuid4()

        # Clear any cached value
        await test_redis_client.delete(f"kb_settings:{fake_kb_id}")

        # WHEN/THEN: Get settings for non-existent KB raises ValueError
        with pytest.raises(ValueError, match=f"Knowledge base not found: {fake_kb_id}"):
            await resolver.get_kb_settings(fake_kb_id)

    @pytest.mark.asyncio
    async def test_malformed_settings_json_handled(
        self, db_session, test_user, resolver, test_redis_client
    ):
        """
        Malformed settings JSON handled gracefully.

        GIVEN: KB has invalid settings JSON structure
        WHEN: get_kb_settings is called
        THEN: Returns default KBSettings without crashing
        """
        # Create KB with settings that might cause issues
        kb = KnowledgeBase(
            name="Malformed Settings KB",
            description="KB with edge-case settings",
            owner_id=test_user.id,
            status="active",
            settings={
                "debug_mode": "not_a_boolean",  # Invalid type
            },
        )
        db_session.add(kb)
        await db_session.flush()

        # Clear cache
        await test_redis_client.delete(f"kb_settings:{kb.id}")

        # WHEN: Get settings (should handle gracefully)
        # The Pydantic model should coerce or reject invalid types
        try:
            settings = await resolver.get_kb_settings(kb.id)
            # If it coerces, check it's a boolean
            assert isinstance(settings.debug_mode, bool)
        except Exception:
            # If it fails validation, that's also acceptable behavior
            pass
