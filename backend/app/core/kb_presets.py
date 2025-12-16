"""KB Settings Presets for common use cases.

Story 7.16: Preset configurations for quick KB optimization.
Each preset contains optimized settings for specific use cases like legal,
technical, creative, code, and general documentation.
"""

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
# Preset Definitions (AC-7.16.2 through AC-7.16.6)
# =============================================================================

KB_PRESETS: dict[str, dict] = {
    "legal": {
        "name": "Legal",
        "description": "Optimized for legal documents with strict citations and formal language",
        "settings": KBSettings(
            chunking=ChunkingConfig(
                strategy=ChunkingStrategy.RECURSIVE,
                chunk_size=1000,
                chunk_overlap=200,
            ),
            retrieval=RetrievalConfig(
                top_k=15,
                similarity_threshold=0.75,
                method=RetrievalMethod.VECTOR,
            ),
            generation=GenerationConfig(
                temperature=0.3,
                top_p=0.9,
                max_tokens=4096,
            ),
            prompts=KBPromptConfig(
                system_prompt="""You are a precise legal document assistant for {kb_name}.

Context:
{context}

User Question:
{query}

When answering:
- Cite every claim with footnote notation [1], [2], etc.
- Never speculate beyond the provided documents
- Emphasize accuracy and exact wording from sources
- When uncertain, clearly state limitations
- Maintain formal, professional legal language
- Reference specific document sections when available

Format citations as footnotes at the end of each relevant statement.""",
                citation_style=CitationStyle.FOOTNOTE,
                uncertainty_handling=UncertaintyHandling.ACKNOWLEDGE,
            ),
            preset="legal",
        ),
    },
    "technical": {
        "name": "Technical",
        "description": "Optimized for technical documentation with inline citations",
        "settings": KBSettings(
            chunking=ChunkingConfig(
                strategy=ChunkingStrategy.RECURSIVE,
                chunk_size=800,
                chunk_overlap=100,
            ),
            retrieval=RetrievalConfig(
                top_k=10,
                similarity_threshold=0.7,
                method=RetrievalMethod.VECTOR,
            ),
            generation=GenerationConfig(
                temperature=0.5,
                top_p=0.9,
                max_tokens=4096,
            ),
            prompts=KBPromptConfig(
                system_prompt="""You are a technical documentation assistant for {kb_name}.

Context:
{context}

User Question:
{query}

When answering:
- Provide precise, technical answers
- Include code examples when relevant
- Use inline citations [1], [2] to reference sources
- Explain concepts clearly with examples
- Reference specific documentation sections
- Use technical terminology appropriately

Format responses with clear structure using headers and code blocks when needed.""",
                citation_style=CitationStyle.INLINE,
                uncertainty_handling=UncertaintyHandling.ACKNOWLEDGE,
            ),
            preset="technical",
        ),
    },
    "creative": {
        "name": "Creative",
        "description": "Higher creativity for brainstorming and exploration",
        "settings": KBSettings(
            chunking=ChunkingConfig(
                strategy=ChunkingStrategy.SEMANTIC,
                chunk_size=500,
                chunk_overlap=75,
            ),
            retrieval=RetrievalConfig(
                top_k=8,
                similarity_threshold=0.6,
                method=RetrievalMethod.VECTOR,
            ),
            generation=GenerationConfig(
                temperature=0.9,
                top_p=0.95,
                max_tokens=4096,
            ),
            prompts=KBPromptConfig(
                system_prompt="""You are a creative assistant exploring {kb_name}.

Context:
{context}

User Question:
{query}

When answering:
- Provide insightful, creative interpretations
- Make connections between different ideas
- Feel free to suggest new perspectives
- Be conversational and engaging
- Offer possibilities and alternatives
- Encourage exploration and discovery

Respond in an approachable, conversational tone.""",
                citation_style=CitationStyle.NONE,
                uncertainty_handling=UncertaintyHandling.BEST_EFFORT,
            ),
            preset="creative",
        ),
    },
    "code": {
        "name": "Code",
        "description": "Optimized for code repositories and programming",
        "settings": KBSettings(
            chunking=ChunkingConfig(
                strategy=ChunkingStrategy.RECURSIVE,
                chunk_size=600,
                chunk_overlap=50,
            ),
            retrieval=RetrievalConfig(
                top_k=12,
                similarity_threshold=0.72,
                method=RetrievalMethod.VECTOR,
            ),
            generation=GenerationConfig(
                temperature=0.2,
                top_p=0.9,
                max_tokens=4096,
            ),
            prompts=KBPromptConfig(
                system_prompt="""You are a code assistant for {kb_name}.

Context:
{context}

User Question:
{query}

When answering:
- Provide accurate code with correct syntax
- Explain code functionality clearly
- Reference specific files and line numbers using [1], [2] citations
- Follow established patterns in the codebase
- Suggest best practices when relevant
- Include working code examples

Format code blocks with appropriate language syntax highlighting.""",
                citation_style=CitationStyle.INLINE,
                uncertainty_handling=UncertaintyHandling.REFUSE,
            ),
            preset="code",
        ),
    },
    "general": {
        "name": "General",
        "description": "Balanced defaults for general knowledge bases",
        "settings": KBSettings(
            # Uses all system defaults
            preset="general",
        ),
    },
}


def get_preset(name: str) -> dict | None:
    """Get preset configuration by name.

    Args:
        name: Preset identifier (legal, technical, creative, code, general).

    Returns:
        Preset dictionary with name, description, and settings, or None if not found.
    """
    return KB_PRESETS.get(name)


def get_preset_settings(name: str) -> KBSettings | None:
    """Get just the KBSettings object for a preset.

    Args:
        name: Preset identifier.

    Returns:
        KBSettings instance for the preset, or None if not found.
    """
    preset = KB_PRESETS.get(name)
    if preset is None:
        return None
    return preset["settings"]


def list_presets() -> list[dict]:
    """List all available presets with metadata.

    Returns:
        List of preset info dicts with id, name, and description.
    """
    return [
        {
            "id": key,
            "name": preset["name"],
            "description": preset["description"],
        }
        for key, preset in KB_PRESETS.items()
    ]


def detect_preset(settings: KBSettings) -> str:
    """Detect which preset matches the given settings.

    Compares key settings fields against each preset definition to find
    an exact match. Returns "custom" if no preset matches.

    Args:
        settings: KBSettings to compare against presets.

    Returns:
        Preset ID string if match found, otherwise "custom".
    """
    # Check non-general presets first
    for preset_id, preset in KB_PRESETS.items():
        if preset_id == "general":
            continue
        if _settings_match_preset(settings, preset["settings"]):
            return preset_id

    # Check if settings match general (all defaults)
    general_settings = KB_PRESETS["general"]["settings"]
    if _settings_match_preset(settings, general_settings):
        return "general"

    return "custom"


def _settings_match_preset(current: KBSettings, preset: KBSettings) -> bool:
    """Check if current settings match a preset configuration.

    Compares key fields that define a preset. Fields that are typically
    customized (like system_prompt text) are compared for functional equivalence.

    Args:
        current: Current KB settings to check.
        preset: Preset settings to compare against.

    Returns:
        True if settings match the preset, False otherwise.
    """
    # Compare chunking
    if current.chunking.strategy != preset.chunking.strategy:
        return False
    if current.chunking.chunk_size != preset.chunking.chunk_size:
        return False
    if current.chunking.chunk_overlap != preset.chunking.chunk_overlap:
        return False

    # Compare retrieval
    if current.retrieval.top_k != preset.retrieval.top_k:
        return False
    if current.retrieval.similarity_threshold != preset.retrieval.similarity_threshold:
        return False
    if current.retrieval.method != preset.retrieval.method:
        return False

    # Compare generation
    if current.generation.temperature != preset.generation.temperature:
        return False
    if current.generation.top_p != preset.generation.top_p:
        return False
    if current.generation.max_tokens != preset.generation.max_tokens:
        return False

    # Compare prompts config (style and handling, not full system_prompt text)
    if current.prompts.citation_style != preset.prompts.citation_style:
        return False
    if current.prompts.uncertainty_handling != preset.prompts.uncertainty_handling:
        return False

    # Compare preset field itself
    return current.preset == preset.preset
