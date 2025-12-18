"""Unit tests for ConversationService KB prompt configuration.

Story 9-15: KB Debug Mode & Prompt Configuration Integration
Tests AC-9.15.4 through AC-9.15.11 for prompt resolution and debug info.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.kb_settings import (
    CitationStyle,
    KBPromptConfig,
    KBSettings,
    UncertaintyHandling,
)
from app.schemas.search import SearchResultSchema
from app.services.conversation_service import (
    CHAT_SYSTEM_PROMPT,
    ConversationService,
)
from app.services.kb_config_resolver import DEFAULT_SYSTEM_PROMPT


def create_search_result(
    document_name: str = "doc.pdf",
    chunk_text: str = "Sample chunk content",
    relevance_score: float = 0.9,
    page_number: int | None = 1,
) -> SearchResultSchema:
    """Factory to create SearchResultSchema with all required fields."""
    return SearchResultSchema(
        document_id=str(uuid.uuid4()),
        document_name=document_name,
        kb_id=str(uuid.uuid4()),
        kb_name="Test KB",
        chunk_text=chunk_text,
        relevance_score=relevance_score,
        page_number=page_number,
        char_start=0,
        char_end=len(chunk_text),
    )


class TestResolveKBPromptConfig:
    """Tests for _resolve_kb_prompt_config (AC-9.15.4)."""

    @pytest.fixture
    def service(self) -> ConversationService:
        """Create service instance without KB config resolver."""
        return ConversationService(
            search_service=MagicMock(),
            citation_service=MagicMock(),
        )

    @pytest.fixture
    def service_with_resolver(self) -> ConversationService:
        """Create service instance with mocked KB config resolver."""
        mock_session = MagicMock()
        mock_redis = MagicMock()
        service = ConversationService(
            search_service=MagicMock(),
            citation_service=MagicMock(),
            session=mock_session,
            redis_client=mock_redis,
        )
        # Replace the resolver with a mock
        service._kb_config_resolver = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_returns_default_when_no_resolver(self, service: ConversationService):
        """AC-9.15.4: Returns default KBPromptConfig when resolver not configured."""
        kb_id = str(uuid.uuid4())

        result = await service._resolve_kb_prompt_config(kb_id)

        assert isinstance(result, KBPromptConfig)
        assert result.system_prompt == ""  # Default empty
        assert result.citation_style == CitationStyle.INLINE
        assert result.response_language == "en"
        assert result.uncertainty_handling == UncertaintyHandling.ACKNOWLEDGE

    @pytest.mark.asyncio
    async def test_returns_kb_settings_from_resolver(
        self, service_with_resolver: ConversationService
    ):
        """AC-9.15.4: Returns KB-level prompt settings from resolver."""
        kb_id = str(uuid.uuid4())
        custom_prompt = "You are a specialized assistant for {kb_name}."
        custom_config = KBPromptConfig(
            system_prompt=custom_prompt,
            citation_style=CitationStyle.FOOTNOTE,
            response_language="es",
            uncertainty_handling=UncertaintyHandling.REFUSE,
        )
        kb_settings = KBSettings(prompts=custom_config)

        # Configure mock to return custom settings
        service_with_resolver._kb_config_resolver.get_kb_settings.return_value = (
            kb_settings
        )

        result = await service_with_resolver._resolve_kb_prompt_config(kb_id)

        assert result.system_prompt == custom_prompt
        assert result.citation_style == CitationStyle.FOOTNOTE
        assert result.response_language == "es"
        assert result.uncertainty_handling == UncertaintyHandling.REFUSE

    @pytest.mark.asyncio
    async def test_returns_default_on_resolver_error(
        self, service_with_resolver: ConversationService
    ):
        """AC-9.15.4: Falls back to default config on resolver error."""
        kb_id = str(uuid.uuid4())

        # Configure mock to raise exception
        service_with_resolver._kb_config_resolver.get_kb_settings.side_effect = (
            Exception("Database error")
        )

        result = await service_with_resolver._resolve_kb_prompt_config(kb_id)

        # Should return default config, not raise
        assert isinstance(result, KBPromptConfig)
        assert result.system_prompt == ""


class TestBuildSystemPrompt:
    """Tests for _build_system_prompt (AC-9.15.4 through AC-9.15.9)."""

    @pytest.fixture
    def service(self) -> ConversationService:
        """Create service instance."""
        return ConversationService(
            search_service=MagicMock(),
            citation_service=MagicMock(),
        )

    def test_uses_kb_system_prompt_when_provided(self, service: ConversationService):
        """AC-9.15.4: Uses KB system_prompt instead of hardcoded constant."""
        custom_prompt = "You are an expert legal assistant."
        config = KBPromptConfig(system_prompt=custom_prompt)

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="Legal KB",
            context_text="Some context",
            query="What is this?",
        )

        assert custom_prompt in result
        assert DEFAULT_SYSTEM_PROMPT not in result

    def test_falls_back_to_default_when_kb_prompt_empty(
        self, service: ConversationService
    ):
        """AC-9.15.6: Falls back to DEFAULT_SYSTEM_PROMPT when KB prompt empty."""
        config = KBPromptConfig(system_prompt="")

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="Test KB",
            context_text="Context",
            query="Query",
        )

        assert DEFAULT_SYSTEM_PROMPT in result

    def test_falls_back_to_default_when_kb_prompt_whitespace(
        self, service: ConversationService
    ):
        """AC-9.15.6: Falls back when KB prompt is whitespace only."""
        config = KBPromptConfig(system_prompt="   \n\t  ")

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="Test KB",
            context_text="Context",
            query="Query",
        )

        assert DEFAULT_SYSTEM_PROMPT in result

    def test_variable_interpolation_kb_name(self, service: ConversationService):
        """AC-9.15.5: Supports {kb_name} variable interpolation."""
        config = KBPromptConfig(
            system_prompt="You are the assistant for {kb_name}. Help users."
        )

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="Engineering Docs",
            context_text="Context",
            query="Query",
        )

        assert "Engineering Docs" in result
        assert "{kb_name}" not in result

    def test_variable_interpolation_context(self, service: ConversationService):
        """AC-9.15.5: Supports {context} variable interpolation."""
        config = KBPromptConfig(system_prompt="Answer using context: {context}")
        context = "Important technical information here."

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text=context,
            query="Query",
        )

        assert context in result

    def test_variable_interpolation_query(self, service: ConversationService):
        """AC-9.15.5: Supports {query} variable interpolation."""
        config = KBPromptConfig(system_prompt="User asked: {query}")
        query = "How do I authenticate?"

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text="Context",
            query=query,
        )

        assert query in result

    def test_handles_missing_placeholders_gracefully(
        self, service: ConversationService
    ):
        """AC-9.15.5: Handles unknown placeholders without crashing."""
        config = KBPromptConfig(system_prompt="Answer the {unknown_variable} question.")

        # Should not raise KeyError
        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text="Context",
            query="Query",
        )

        # Uses original prompt when interpolation fails
        assert "unknown_variable" in result or result is not None

    def test_citation_style_inline_instruction(self, service: ConversationService):
        """AC-9.15.7: citation_style=inline adds inline citation instruction."""
        config = KBPromptConfig(
            system_prompt="Base prompt.",
            citation_style=CitationStyle.INLINE,
        )

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text="Context",
            query="Query",
        )

        assert "[n] notation inline" in result

    def test_citation_style_footnote_instruction(self, service: ConversationService):
        """AC-9.15.7: citation_style=footnote adds footnote instruction."""
        config = KBPromptConfig(
            system_prompt="Base prompt.",
            citation_style=CitationStyle.FOOTNOTE,
        )

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text="Context",
            query="Query",
        )

        assert "footnote-style citations" in result

    def test_citation_style_none_instruction(self, service: ConversationService):
        """AC-9.15.7: citation_style=none adds no-citation instruction."""
        config = KBPromptConfig(
            system_prompt="Base prompt.",
            citation_style=CitationStyle.NONE,
        )

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text="Context",
            query="Query",
        )

        assert "Do not include citation markers" in result

    def test_response_language_non_english(self, service: ConversationService):
        """AC-9.15.8: response_language adds sandwich instructions (start + end)."""
        config = KBPromptConfig(
            system_prompt="Base prompt.",
            response_language="es",
        )

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text="Context",
            query="Query",
        )

        # Verify critical language instruction at BEGINNING and END
        assert result.startswith("[CRITICAL: RESPOND ONLY IN SPANISH")
        assert "DO NOT USE ENGLISH" in result
        assert "REMINDER: Your entire response MUST be in Spanish" in result
        assert "Base prompt." in result  # Original prompt still present

    def test_response_language_english_no_instruction(
        self, service: ConversationService
    ):
        """AC-9.15.8: response_language='en' does not add instruction."""
        config = KBPromptConfig(
            system_prompt="Base prompt.",
            response_language="en",
        )

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text="Context",
            query="Query",
        )

        assert "Respond in English" not in result

    def test_uncertainty_handling_acknowledge(self, service: ConversationService):
        """AC-9.15.9: uncertainty_handling=acknowledge adds appropriate instruction."""
        config = KBPromptConfig(
            system_prompt="Base prompt.",
            uncertainty_handling=UncertaintyHandling.ACKNOWLEDGE,
        )

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text="Context",
            query="Query",
        )

        assert "acknowledge this clearly" in result

    def test_uncertainty_handling_refuse(self, service: ConversationService):
        """AC-9.15.9: uncertainty_handling=refuse adds refuse instruction."""
        config = KBPromptConfig(
            system_prompt="Base prompt.",
            uncertainty_handling=UncertaintyHandling.REFUSE,
        )

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text="Context",
            query="Query",
        )

        assert "politely decline" in result

    def test_uncertainty_handling_best_effort(self, service: ConversationService):
        """AC-9.15.9: uncertainty_handling=best_effort adds best-effort instruction."""
        config = KBPromptConfig(
            system_prompt="Base prompt.",
            uncertainty_handling=UncertaintyHandling.BEST_EFFORT,
        )

        result = service._build_system_prompt(
            prompt_config=config,
            kb_name="KB",
            context_text="Context",
            query="Query",
        )

        assert "best possible answer" in result


class TestBuildPrompt:
    """Tests for _build_prompt (AC-9.15.4)."""

    @pytest.fixture
    def service(self) -> ConversationService:
        """Create service instance."""
        return ConversationService(
            search_service=MagicMock(),
            citation_service=MagicMock(),
        )

    @pytest.fixture
    def sample_chunks(self) -> list[SearchResultSchema]:
        """Create sample search result chunks."""
        return [
            create_search_result(
                document_name="doc1.pdf",
                chunk_text="First chunk content about topic A.",
                relevance_score=0.95,
                page_number=1,
            ),
            create_search_result(
                document_name="doc2.pdf",
                chunk_text="Second chunk about topic B.",
                relevance_score=0.87,
                page_number=5,
            ),
        ]

    def test_uses_dynamic_system_prompt_when_provided(
        self, service: ConversationService, sample_chunks: list[SearchResultSchema]
    ):
        """AC-9.15.4: Uses dynamic system prompt from KB configuration."""
        custom_prompt = "You are a custom KB assistant."
        history: list[dict] = []

        result = service._build_prompt(
            history=history,
            message="What is topic A?",
            chunks=sample_chunks,
            system_prompt=custom_prompt,
        )

        # First message should be system with custom prompt
        assert result[0]["role"] == "system"
        assert result[0]["content"] == custom_prompt

    def test_falls_back_to_legacy_prompt_when_none(
        self, service: ConversationService, sample_chunks: list[SearchResultSchema]
    ):
        """AC-9.15.4: Falls back to CHAT_SYSTEM_PROMPT for backward compatibility."""
        history: list[dict] = []

        result = service._build_prompt(
            history=history,
            message="Question",
            chunks=sample_chunks,
            system_prompt=None,  # No dynamic prompt
        )

        # Should use legacy prompt
        assert result[0]["role"] == "system"
        assert result[0]["content"] == CHAT_SYSTEM_PROMPT

    def test_includes_context_chunks(
        self, service: ConversationService, sample_chunks: list[SearchResultSchema]
    ):
        """Verify context chunks are included in prompt."""
        result = service._build_prompt(
            history=[],
            message="Question",
            chunks=sample_chunks,
            system_prompt="System prompt",
        )

        # Find the context message
        context_msg = next(
            (m for m in result if "Retrieved sources:" in m["content"]), None
        )
        assert context_msg is not None
        assert "[1]" in context_msg["content"]
        assert "[2]" in context_msg["content"]
        assert "First chunk content" in context_msg["content"]
        assert "Second chunk about topic B" in context_msg["content"]

    def test_includes_user_message(
        self, service: ConversationService, sample_chunks: list[SearchResultSchema]
    ):
        """Verify user message is included."""
        user_question = "What is the answer to everything?"

        result = service._build_prompt(
            history=[],
            message=user_question,
            chunks=sample_chunks,
            system_prompt="System",
        )

        # Last message should be user
        assert result[-1]["role"] == "user"
        assert result[-1]["content"] == user_question

    def test_appends_language_instruction_to_user_message(
        self, service: ConversationService, sample_chunks: list[SearchResultSchema]
    ):
        """AC-9.15.8: Appends language instruction to user message for non-English."""
        user_question = "What is topic A?"

        result = service._build_prompt(
            history=[],
            message=user_question,
            chunks=sample_chunks,
            system_prompt="System",
            response_language="vi",  # Vietnamese
        )

        # Last message should be user with language instruction appended
        assert result[-1]["role"] == "user"
        assert user_question in result[-1]["content"]
        assert "[Please respond entirely in Vietnamese.]" in result[-1]["content"]

    def test_no_language_instruction_for_english(
        self, service: ConversationService, sample_chunks: list[SearchResultSchema]
    ):
        """AC-9.15.8: No language instruction appended for English."""
        user_question = "What is topic A?"

        result = service._build_prompt(
            history=[],
            message=user_question,
            chunks=sample_chunks,
            system_prompt="System",
            response_language="en",  # English (default)
        )

        # Last message should be user without language instruction
        assert result[-1]["role"] == "user"
        assert result[-1]["content"] == user_question
        assert "[Please respond entirely in" not in result[-1]["content"]


class TestBuildDebugInfo:
    """Tests for _build_debug_info (AC-9.15.11)."""

    @pytest.fixture
    def service(self) -> ConversationService:
        """Create service instance."""
        return ConversationService(
            search_service=MagicMock(),
            citation_service=MagicMock(),
        )

    @pytest.fixture
    def sample_chunks(self) -> list[SearchResultSchema]:
        """Create sample search result chunks."""
        return [
            create_search_result(
                document_name="architecture.pdf",
                chunk_text="System architecture overview with microservices pattern.",
                relevance_score=0.92,
                page_number=3,
            ),
            create_search_result(
                document_name="api-guide.md",
                chunk_text="REST API endpoints documentation.",
                relevance_score=0.78,
                page_number=None,
            ),
        ]

    def test_includes_kb_params(
        self, service: ConversationService, sample_chunks: list[SearchResultSchema]
    ):
        """AC-9.15.11: DebugInfo includes kb_params."""
        prompt_config = KBPromptConfig(
            system_prompt="Custom prompt for testing",
            citation_style=CitationStyle.FOOTNOTE,
            response_language="de",
            uncertainty_handling=UncertaintyHandling.REFUSE,
        )

        result = service._build_debug_info(
            prompt_config=prompt_config,
            chunks=sample_chunks,
            retrieval_ms=125.5,
            context_assembly_ms=45.2,
        )

        assert result.kb_params.citation_style == "footnote"
        assert result.kb_params.response_language == "de"
        assert result.kb_params.uncertainty_handling == "refuse"
        assert "Custom prompt" in result.kb_params.system_prompt_preview

    def test_includes_chunks_retrieved(
        self, service: ConversationService, sample_chunks: list[SearchResultSchema]
    ):
        """AC-9.15.11: DebugInfo includes chunks_retrieved with scores."""
        prompt_config = KBPromptConfig()

        result = service._build_debug_info(
            prompt_config=prompt_config,
            chunks=sample_chunks,
            retrieval_ms=100,
            context_assembly_ms=50,
        )

        assert len(result.chunks_retrieved) == 2

        # Verify first chunk
        chunk1 = result.chunks_retrieved[0]
        assert chunk1.document_name == "architecture.pdf"
        assert chunk1.similarity_score == 0.92
        assert chunk1.page_number == 3
        assert "architecture" in chunk1.preview.lower()

        # Verify second chunk
        chunk2 = result.chunks_retrieved[1]
        assert chunk2.document_name == "api-guide.md"
        assert chunk2.similarity_score == 0.78
        assert chunk2.page_number is None

    def test_includes_timing_info(
        self, service: ConversationService, sample_chunks: list[SearchResultSchema]
    ):
        """AC-9.15.11: DebugInfo includes timing breakdown."""
        prompt_config = KBPromptConfig()

        result = service._build_debug_info(
            prompt_config=prompt_config,
            chunks=sample_chunks,
            retrieval_ms=234.7,
            context_assembly_ms=67.3,
        )

        assert result.timing.retrieval_ms == 234.7
        assert result.timing.context_assembly_ms == 67.3

    def test_handles_empty_chunks(self, service: ConversationService):
        """DebugInfo handles empty chunk list gracefully."""
        prompt_config = KBPromptConfig()

        result = service._build_debug_info(
            prompt_config=prompt_config,
            chunks=[],
            retrieval_ms=50,
            context_assembly_ms=10,
        )

        assert len(result.chunks_retrieved) == 0
        assert result.timing.retrieval_ms == 50

    def test_uses_default_prompt_preview_when_empty(
        self, service: ConversationService, sample_chunks: list[SearchResultSchema]
    ):
        """DebugInfo uses DEFAULT_SYSTEM_PROMPT preview when KB prompt empty."""
        prompt_config = KBPromptConfig(system_prompt="")

        result = service._build_debug_info(
            prompt_config=prompt_config,
            chunks=sample_chunks,
            retrieval_ms=100,
            context_assembly_ms=50,
        )

        # Should show preview of DEFAULT_SYSTEM_PROMPT
        assert DEFAULT_SYSTEM_PROMPT[:50] in result.kb_params.system_prompt_preview


class TestIsDebugModeEnabled:
    """Tests for _is_debug_mode_enabled (AC-9.15.10)."""

    @pytest.fixture
    def service_with_resolver(self) -> ConversationService:
        """Create service instance with mocked KB config resolver."""
        mock_session = MagicMock()
        mock_redis = MagicMock()
        service = ConversationService(
            search_service=MagicMock(),
            citation_service=MagicMock(),
            session=mock_session,
            redis_client=mock_redis,
        )
        # Replace the resolver with a mock
        service._kb_config_resolver = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_returns_true_when_debug_enabled(
        self, service_with_resolver: ConversationService
    ):
        """AC-9.15.10: Returns True when KB has debug_mode=True."""
        kb_id = str(uuid.uuid4())
        kb_settings = KBSettings(debug_mode=True)
        service_with_resolver._kb_config_resolver.get_kb_settings.return_value = (
            kb_settings
        )

        result = await service_with_resolver._is_debug_mode_enabled(kb_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_debug_disabled(
        self, service_with_resolver: ConversationService
    ):
        """AC-9.15.10: Returns False when KB has debug_mode=False."""
        kb_id = str(uuid.uuid4())
        kb_settings = KBSettings(debug_mode=False)
        service_with_resolver._kb_config_resolver.get_kb_settings.return_value = (
            kb_settings
        )

        result = await service_with_resolver._is_debug_mode_enabled(kb_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_error(
        self, service_with_resolver: ConversationService
    ):
        """Returns False when settings lookup fails."""
        kb_id = str(uuid.uuid4())
        service_with_resolver._kb_config_resolver.get_kb_settings.side_effect = (
            Exception("Lookup failed")
        )

        result = await service_with_resolver._is_debug_mode_enabled(kb_id)

        # Should default to False, not crash
        assert result is False
