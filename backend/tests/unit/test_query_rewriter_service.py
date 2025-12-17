"""Unit tests for QueryRewriterService.

Story 8-0: History-Aware Query Rewriting
Tests for query reformulation using conversation history context.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.query_rewriter_service import QueryRewriterService, RewriteResult

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_llm_client():
    """Mock LiteLLM client."""
    client = MagicMock()
    client.chat_completion = AsyncMock()
    return client


@pytest.fixture
def mock_config_service():
    """Mock ConfigService."""
    service = MagicMock()
    service.get_rewriter_model = AsyncMock(return_value="ollama/llama3.2")
    service.get_rewriter_timeout = AsyncMock(return_value=5.0)
    return service


@pytest.fixture
def query_rewriter_service(mock_llm_client, mock_config_service):
    """QueryRewriterService instance with mocked dependencies."""
    return QueryRewriterService(
        llm_client=mock_llm_client,
        config_service=mock_config_service,
    )


@pytest.fixture
def sample_history():
    """Sample conversation history."""
    return [
        {"role": "user", "content": "What is OAuth 2.0?"},
        {"role": "assistant", "content": "OAuth 2.0 is an authorization framework..."},
        {"role": "user", "content": "How does it handle tokens?"},
        {
            "role": "assistant",
            "content": "OAuth 2.0 uses access tokens and refresh tokens...",
        },
    ]


class TestRewriteWithHistory:
    """Tests for rewrite_with_history method."""

    async def test_returns_original_when_no_history(
        self, query_rewriter_service, mock_llm_client
    ):
        """AC: Skip rewriting when no history exists."""
        query = "What is OAuth 2.0?"

        result = await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=[],
        )

        assert isinstance(result, RewriteResult)
        assert result.original_query == query
        assert result.rewritten_query == query
        assert result.was_rewritten is False
        assert result.model_used == ""
        assert result.latency_ms == 0
        mock_llm_client.chat_completion.assert_not_called()

    async def test_returns_original_for_standalone_query(
        self, query_rewriter_service, mock_llm_client, sample_history
    ):
        """AC: Skip rewriting for standalone queries without pronouns/references."""
        # A query without pronouns or references is standalone
        query = "What is the best authentication method?"

        result = await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=sample_history,
        )

        assert result.was_rewritten is False
        assert result.rewritten_query == query
        mock_llm_client.chat_completion.assert_not_called()

    async def test_rewrites_query_with_pronouns(
        self,
        query_rewriter_service,
        mock_llm_client,
        mock_config_service,
        sample_history,
    ):
        """AC: Rewrite queries containing pronouns (it/they/etc)."""
        query = "How does it compare to SAML?"

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="How does OAuth 2.0 compare to SAML?"))
        ]
        mock_response.usage = MagicMock(prompt_tokens=50, completion_tokens=10)
        mock_llm_client.chat_completion.return_value = mock_response

        result = await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=sample_history,
        )

        assert result.was_rewritten is True
        assert result.original_query == query
        assert result.rewritten_query == "How does OAuth 2.0 compare to SAML?"
        assert result.model_used == "ollama/llama3.2"
        assert result.latency_ms > 0
        mock_llm_client.chat_completion.assert_called_once()

    async def test_rewrites_query_with_references(
        self,
        query_rewriter_service,
        mock_llm_client,
        mock_config_service,
        sample_history,
    ):
        """AC: Rewrite queries containing reference words (that/this/etc)."""
        query = "Can you explain that further?"

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="Can you explain OAuth 2.0 token handling further?"
                )
            )
        ]
        mock_response.usage = None
        mock_llm_client.chat_completion.return_value = mock_response

        result = await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=sample_history,
        )

        assert result.was_rewritten is True
        assert "token" in result.rewritten_query.lower()

    async def test_graceful_degradation_on_llm_error(
        self,
        query_rewriter_service,
        mock_llm_client,
        mock_config_service,
        sample_history,
    ):
        """AC: Return original query on LLM failure."""
        query = "How does it handle errors?"

        # Mock LLM error
        mock_llm_client.chat_completion.side_effect = Exception("LLM timeout")

        result = await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=sample_history,
        )

        assert result.was_rewritten is False
        assert result.rewritten_query == query
        assert result.latency_ms >= 0  # Tracks time (may be very fast)

    async def test_uses_correct_model(
        self,
        query_rewriter_service,
        mock_llm_client,
        mock_config_service,
        sample_history,
    ):
        """AC: Uses configured rewriter model."""
        mock_config_service.get_rewriter_model.return_value = "gpt-4o-mini"
        query = "What happens when they expire?"

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(content="What happens when OAuth 2.0 tokens expire?")
            )
        ]
        mock_response.usage = None
        mock_llm_client.chat_completion.return_value = mock_response

        result = await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=sample_history,
        )

        mock_config_service.get_rewriter_model.assert_called_once()
        call_args = mock_llm_client.chat_completion.call_args
        assert call_args.kwargs["model"] == "gpt-4o-mini"
        assert result.model_used == "gpt-4o-mini"

    async def test_llm_called_with_timeout(
        self, query_rewriter_service, mock_llm_client, sample_history
    ):
        """AC: LLM calls have 5-second timeout."""
        query = "Tell me more about it"

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="..."))]
        mock_response.usage = None
        mock_llm_client.chat_completion.return_value = mock_response

        await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=sample_history,
        )

        call_args = mock_llm_client.chat_completion.call_args
        assert call_args.kwargs["timeout"] == 5.0


class TestIsStandalone:
    """Tests for _is_standalone heuristic."""

    @pytest.fixture
    def service(self, mock_llm_client, mock_config_service):
        return QueryRewriterService(mock_llm_client, mock_config_service)

    def test_detects_pronouns(self, service):
        """Detects queries with pronouns."""
        assert service._is_standalone("What is OAuth?") is True
        assert service._is_standalone("How does it work?") is False
        assert service._is_standalone("What about them?") is False
        assert service._is_standalone("Tell me about her approach") is False
        assert service._is_standalone("His implementation was good") is False
        assert service._is_standalone("Their solution is better") is False

    def test_detects_references(self, service):
        """Detects queries with reference words."""
        assert service._is_standalone("Explain that in detail") is False
        assert service._is_standalone("What about this?") is False
        assert service._is_standalone("Tell me more about the same thing") is False
        assert service._is_standalone("As mentioned earlier") is False
        assert service._is_standalone("The previous approach") is False

    def test_standalone_queries(self, service):
        """Identifies truly standalone queries."""
        assert service._is_standalone("What is the best database?") is True
        assert service._is_standalone("Explain microservices architecture") is True
        assert service._is_standalone("How to implement caching?") is True


class TestFormatHistory:
    """Tests for _format_history method."""

    @pytest.fixture
    def service(self, mock_llm_client, mock_config_service):
        return QueryRewriterService(mock_llm_client, mock_config_service)

    def test_formats_history_correctly(self, service):
        """Formats history with Human/Assistant labels."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        formatted = service._format_history(history)

        assert "Human: Hello" in formatted
        assert "Assistant: Hi there!" in formatted

    def test_limits_to_last_5_messages(self, service):
        """Only includes last 5 messages."""
        history = [{"role": "user", "content": f"Message {i}"} for i in range(10)]

        formatted = service._format_history(history)
        lines = [line for line in formatted.split("\n") if line.strip()]

        assert len(lines) == 5
        assert "Message 5" in formatted
        assert "Message 0" not in formatted

    def test_truncates_long_messages(self, service):
        """Truncates messages longer than 500 chars."""
        long_message = "x" * 1000
        history = [{"role": "user", "content": long_message}]

        formatted = service._format_history(history)

        assert len(formatted) < 600  # 500 + prefix + "..."
        assert formatted.endswith("...")


class TestRewriteResultDataclass:
    """Tests for RewriteResult dataclass."""

    def test_rewrite_result_attributes(self):
        """RewriteResult has correct attributes."""
        result = RewriteResult(
            original_query="What about it?",
            rewritten_query="What about OAuth 2.0?",
            was_rewritten=True,
            model_used="ollama/llama3.2",
            latency_ms=150.5,
        )

        assert result.original_query == "What about it?"
        assert result.rewritten_query == "What about OAuth 2.0?"
        assert result.was_rewritten is True
        assert result.model_used == "ollama/llama3.2"
        assert result.latency_ms == 150.5
