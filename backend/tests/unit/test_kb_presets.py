"""Unit tests for KB Settings Presets.

Story 7.16: KB Settings Presets
Tests the preset definitions, retrieval, and detection functions.
"""

from app.core.kb_presets import (
    KB_PRESETS,
    detect_preset,
    get_preset,
    get_preset_settings,
    list_presets,
)
from app.schemas.kb_settings import (
    ChunkingConfig,
    ChunkingStrategy,
    CitationStyle,
    GenerationConfig,
    KBPromptConfig,
    KBSettings,
    RetrievalConfig,
    RetrievalMethod,
    UncertaintyHandling,
)

# =============================================================================
# Test Preset Definitions (AC-7.16.2-6)
# =============================================================================


class TestPresetDefinitions:
    """Tests for preset content definitions."""

    def test_all_five_presets_exist(self) -> None:
        """AC-7.16.1: Verify all five presets are defined."""
        expected_presets = ["legal", "technical", "creative", "code", "general"]
        for preset_id in expected_presets:
            assert preset_id in KB_PRESETS, f"Missing preset: {preset_id}"

    def test_legal_preset_values(self) -> None:
        """AC-7.16.2: Legal preset has strict citations and conservative temperature."""
        preset = get_preset_settings("legal")
        assert preset is not None

        # Chunking: larger chunks for legal documents
        assert preset.chunking.chunk_size == 1000
        assert preset.chunking.chunk_overlap == 200
        assert preset.chunking.strategy == ChunkingStrategy.RECURSIVE

        # Retrieval: higher threshold for accuracy
        assert preset.retrieval.top_k == 15
        assert preset.retrieval.similarity_threshold == 0.75

        # Generation: low temperature for consistency
        assert preset.generation.temperature == 0.3

        # Prompts: footnote citations required
        assert preset.prompts.citation_style == CitationStyle.FOOTNOTE
        assert preset.prompts.uncertainty_handling == UncertaintyHandling.ACKNOWLEDGE
        assert preset.preset == "legal"

    def test_technical_preset_values(self) -> None:
        """AC-7.16.3: Technical preset has inline citations and moderate temperature."""
        preset = get_preset_settings("technical")
        assert preset is not None

        assert preset.chunking.chunk_size == 800
        assert preset.chunking.chunk_overlap == 100

        assert preset.retrieval.top_k == 10
        assert preset.retrieval.similarity_threshold == 0.7

        assert preset.generation.temperature == 0.5

        assert preset.prompts.citation_style == CitationStyle.INLINE
        assert preset.prompts.uncertainty_handling == UncertaintyHandling.ACKNOWLEDGE
        assert preset.preset == "technical"

    def test_creative_preset_values(self) -> None:
        """AC-7.16.4: Creative preset has higher temperature and lower threshold."""
        preset = get_preset_settings("creative")
        assert preset is not None

        assert preset.chunking.chunk_size == 500
        assert preset.chunking.chunk_overlap == 75
        assert preset.chunking.strategy == ChunkingStrategy.SEMANTIC

        assert preset.retrieval.top_k == 8
        assert preset.retrieval.similarity_threshold == 0.6

        # High temperature for creativity
        assert preset.generation.temperature == 0.9
        assert preset.generation.top_p == 0.95

        assert preset.prompts.citation_style == CitationStyle.NONE
        assert preset.prompts.uncertainty_handling == UncertaintyHandling.BEST_EFFORT
        assert preset.preset == "creative"

    def test_code_preset_values(self) -> None:
        """AC-7.16.5: Code preset has low temperature and refuses on uncertainty."""
        preset = get_preset_settings("code")
        assert preset is not None

        assert preset.chunking.chunk_size == 600
        assert preset.chunking.chunk_overlap == 50

        assert preset.retrieval.top_k == 12
        assert preset.retrieval.similarity_threshold == 0.72

        # Very low temperature for accurate code
        assert preset.generation.temperature == 0.2

        assert preset.prompts.citation_style == CitationStyle.INLINE
        assert preset.prompts.uncertainty_handling == UncertaintyHandling.REFUSE
        assert preset.preset == "code"

    def test_general_preset_values(self) -> None:
        """AC-7.16.6: General preset uses system defaults."""
        preset = get_preset_settings("general")
        assert preset is not None

        # General should use defaults - verify preset field is set
        assert preset.preset == "general"

    def test_each_preset_has_name_and_description(self) -> None:
        """All presets should have name and description metadata."""
        for preset_id, preset_data in KB_PRESETS.items():
            assert "name" in preset_data, f"{preset_id} missing name"
            assert "description" in preset_data, f"{preset_id} missing description"
            assert "settings" in preset_data, f"{preset_id} missing settings"
            assert len(preset_data["name"]) > 0
            assert len(preset_data["description"]) > 0

    def test_each_preset_settings_is_kbsettings_instance(self) -> None:
        """All preset settings should be valid KBSettings instances."""
        for preset_id, preset_data in KB_PRESETS.items():
            settings = preset_data["settings"]
            assert isinstance(
                settings, KBSettings
            ), f"{preset_id} settings not KBSettings"


# =============================================================================
# Test get_preset Function
# =============================================================================


class TestGetPreset:
    """Tests for get_preset function."""

    def test_get_existing_preset(self) -> None:
        """Get returns full preset dict for valid preset ID."""
        preset = get_preset("legal")
        assert preset is not None
        assert preset["name"] == "Legal"
        assert "description" in preset
        assert "settings" in preset
        assert isinstance(preset["settings"], KBSettings)

    def test_get_nonexistent_preset_returns_none(self) -> None:
        """Get returns None for invalid preset ID."""
        result = get_preset("nonexistent")
        assert result is None

    def test_get_all_valid_presets(self) -> None:
        """Get works for all defined preset IDs."""
        for preset_id in ["legal", "technical", "creative", "code", "general"]:
            preset = get_preset(preset_id)
            assert preset is not None, f"Failed to get preset: {preset_id}"


# =============================================================================
# Test get_preset_settings Function
# =============================================================================


class TestGetPresetSettings:
    """Tests for get_preset_settings function."""

    def test_get_settings_returns_kbsettings(self) -> None:
        """Get settings returns just the KBSettings object."""
        settings = get_preset_settings("technical")
        assert settings is not None
        assert isinstance(settings, KBSettings)

    def test_get_settings_nonexistent_returns_none(self) -> None:
        """Get settings returns None for invalid preset ID."""
        result = get_preset_settings("invalid_preset")
        assert result is None

    def test_get_settings_all_presets(self) -> None:
        """Get settings works for all preset IDs."""
        for preset_id in KB_PRESETS.keys():
            settings = get_preset_settings(preset_id)
            assert settings is not None
            assert isinstance(settings, KBSettings)


# =============================================================================
# Test list_presets Function (AC-7.16.1)
# =============================================================================


class TestListPresets:
    """Tests for list_presets function."""

    def test_list_presets_returns_all(self) -> None:
        """List returns all five presets."""
        presets = list_presets()
        assert len(presets) == 5
        preset_ids = [p["id"] for p in presets]
        assert "legal" in preset_ids
        assert "technical" in preset_ids
        assert "creative" in preset_ids
        assert "code" in preset_ids
        assert "general" in preset_ids

    def test_list_presets_format(self) -> None:
        """List returns correctly formatted preset info."""
        presets = list_presets()
        for preset in presets:
            assert "id" in preset
            assert "name" in preset
            assert "description" in preset
            assert isinstance(preset["id"], str)
            assert isinstance(preset["name"], str)
            assert isinstance(preset["description"], str)

    def test_list_presets_names_match_definitions(self) -> None:
        """Listed names match the defined preset names."""
        presets = list_presets()
        for preset in presets:
            original = KB_PRESETS[preset["id"]]
            assert preset["name"] == original["name"]
            assert preset["description"] == original["description"]


# =============================================================================
# Test detect_preset Function (AC-7.16.8)
# =============================================================================


class TestDetectPreset:
    """Tests for detect_preset function."""

    def test_detect_legal_preset(self) -> None:
        """Detect correctly identifies legal preset settings."""
        legal_settings = get_preset_settings("legal")
        assert legal_settings is not None
        result = detect_preset(legal_settings)
        assert result == "legal"

    def test_detect_technical_preset(self) -> None:
        """Detect correctly identifies technical preset settings."""
        technical_settings = get_preset_settings("technical")
        assert technical_settings is not None
        result = detect_preset(technical_settings)
        assert result == "technical"

    def test_detect_creative_preset(self) -> None:
        """Detect correctly identifies creative preset settings."""
        creative_settings = get_preset_settings("creative")
        assert creative_settings is not None
        result = detect_preset(creative_settings)
        assert result == "creative"

    def test_detect_code_preset(self) -> None:
        """Detect correctly identifies code preset settings."""
        code_settings = get_preset_settings("code")
        assert code_settings is not None
        result = detect_preset(code_settings)
        assert result == "code"

    def test_detect_general_preset(self) -> None:
        """Detect correctly identifies general preset settings."""
        general_settings = get_preset_settings("general")
        assert general_settings is not None
        result = detect_preset(general_settings)
        assert result == "general"

    def test_detect_custom_settings_returns_custom(self) -> None:
        """Detect returns 'custom' for non-preset settings."""
        custom_settings = KBSettings(
            chunking=ChunkingConfig(
                strategy=ChunkingStrategy.RECURSIVE,
                chunk_size=999,  # Non-standard value
                chunk_overlap=123,
            ),
            retrieval=RetrievalConfig(
                top_k=7,
                similarity_threshold=0.65,
                method=RetrievalMethod.VECTOR,
            ),
            generation=GenerationConfig(
                temperature=0.42,
                top_p=0.88,
                max_tokens=2048,
            ),
            prompts=KBPromptConfig(
                system_prompt="Custom prompt",
                citation_style=CitationStyle.INLINE,
                uncertainty_handling=UncertaintyHandling.ACKNOWLEDGE,
            ),
            preset="custom",
        )
        result = detect_preset(custom_settings)
        assert result == "custom"

    def test_detect_modified_legal_returns_custom(self) -> None:
        """Detect returns 'custom' if legal settings are modified."""
        legal_settings = get_preset_settings("legal")
        assert legal_settings is not None

        # Modify one setting
        modified = KBSettings(
            chunking=ChunkingConfig(
                strategy=legal_settings.chunking.strategy,
                chunk_size=legal_settings.chunking.chunk_size + 100,  # Modified
                chunk_overlap=legal_settings.chunking.chunk_overlap,
            ),
            retrieval=legal_settings.retrieval,
            generation=legal_settings.generation,
            prompts=legal_settings.prompts,
            preset="legal",  # Even with preset field set
        )
        result = detect_preset(modified)
        assert result == "custom"

    def test_detect_with_different_citation_style_returns_custom(self) -> None:
        """Detect returns 'custom' if citation style differs."""
        technical_settings = get_preset_settings("technical")
        assert technical_settings is not None

        # Same as technical but with different citation style
        modified = KBSettings(
            chunking=technical_settings.chunking,
            retrieval=technical_settings.retrieval,
            generation=technical_settings.generation,
            prompts=KBPromptConfig(
                system_prompt=technical_settings.prompts.system_prompt,
                citation_style=CitationStyle.FOOTNOTE,  # Changed from INLINE
                uncertainty_handling=technical_settings.prompts.uncertainty_handling,
            ),
            preset="technical",
        )
        result = detect_preset(modified)
        assert result == "custom"


# =============================================================================
# Test Preset System Prompts
# =============================================================================


class TestPresetSystemPrompts:
    """Tests for preset system prompt content."""

    def test_legal_prompt_mentions_citations(self) -> None:
        """Legal preset prompt emphasizes citation requirements."""
        preset = get_preset_settings("legal")
        assert preset is not None
        prompt = preset.prompts.system_prompt
        assert "citation" in prompt.lower() or "cite" in prompt.lower()

    def test_technical_prompt_mentions_code(self) -> None:
        """Technical preset prompt mentions code examples."""
        preset = get_preset_settings("technical")
        assert preset is not None
        prompt = preset.prompts.system_prompt
        assert "code" in prompt.lower() or "technical" in prompt.lower()

    def test_creative_prompt_mentions_creative(self) -> None:
        """Creative preset prompt encourages creativity."""
        preset = get_preset_settings("creative")
        assert preset is not None
        prompt = preset.prompts.system_prompt
        assert "creative" in prompt.lower() or "explore" in prompt.lower()

    def test_code_prompt_emphasizes_accuracy(self) -> None:
        """Code preset prompt emphasizes code accuracy."""
        preset = get_preset_settings("code")
        assert preset is not None
        prompt = preset.prompts.system_prompt
        assert "code" in prompt.lower() and "accurate" in prompt.lower()

    def test_all_prompts_are_non_empty(self) -> None:
        """All preset system prompts should have content."""
        for preset_id in ["legal", "technical", "creative", "code"]:
            preset = get_preset_settings(preset_id)
            assert preset is not None
            assert len(preset.prompts.system_prompt) > 50
