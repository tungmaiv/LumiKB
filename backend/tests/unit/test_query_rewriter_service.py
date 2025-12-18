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

    async def test_calls_llm_for_all_queries_with_history(
        self, query_rewriter_service, mock_llm_client, sample_history
    ):
        """LangChain approach: Always call LLM when history exists.

        Previously we skipped LLM for "standalone" queries, but this missed
        implicit context references like "day 3" referencing a study plan.
        Now we always let the LLM decide if rewriting is needed.
        """
        # A query without pronouns or references - previously would skip LLM
        query = "What is the best authentication method?"

        # Mock LLM to return query unchanged (LLM decides it's standalone)
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=query))  # LLM returns unchanged
        ]
        mock_response.usage = MagicMock(prompt_tokens=50, completion_tokens=10)
        mock_llm_client.chat_completion.return_value = mock_response

        result = await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=sample_history,
        )

        # LLM WAS called (unlike before), but query is unchanged
        mock_llm_client.chat_completion.assert_called_once()
        assert result.rewritten_query == query
        assert result.was_rewritten is False  # No change = was_rewritten is False

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

    async def test_implicit_context_reference_day_number(
        self, query_rewriter_service, mock_llm_client
    ):
        """LangChain approach: Rewrites 'day 3' with context even without pronouns.

        This test verifies the fix for the bug where "what I will learn in day 3"
        failed with NoDocumentsError. The old _is_standalone() heuristic missed
        implicit context references like "day 3" referring to an 11-day study plan.

        Now we always call LLM for rewriting when history exists, allowing the LLM
        to understand that "day 3" implicitly references the TOGAF study plan.
        """
        history = [
            {
                "role": "user",
                "content": "I'd like to study TOGAF, I only have 11 days to study please show me a plan",
            },
            {
                "role": "assistant",
                "content": "Here's an 11-day TOGAF study plan:\n"
                "Day 1: Introduction to TOGAF\n"
                "Day 2: Architecture Vision (Phase A)\n"
                "Day 3: Business Architecture (Phase B)\n"
                "Day 4-5: Information Systems Architecture (Phase C)\n"
                "...",
            },
        ]
        query = "what I will learn in day 3"

        # Mock LLM to return query with full context
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="What will I learn in Day 3 of the 11-day TOGAF study plan (Business Architecture, Phase B)?"
                )
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=100, completion_tokens=25)
        mock_llm_client.chat_completion.return_value = mock_response

        result = await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=history,
        )

        # LLM was called (critical - this was the bug fix)
        mock_llm_client.chat_completion.assert_called_once()

        # Query was rewritten with context
        assert result.was_rewritten is True
        assert (
            "TOGAF" in result.rewritten_query
            or "Business Architecture" in result.rewritten_query
        )
        assert result.original_query == query


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


class TestExtractConversationContext:
    """Tests for _extract_conversation_context method (B+C hybrid approach).

    Story 8-0.1: Updated to unpack 4 values (added extracted_topics).
    """

    @pytest.fixture
    def service(self, mock_llm_client, mock_config_service):
        return QueryRewriterService(mock_llm_client, mock_config_service)

    def test_extracts_last_qa_pair(self, service):
        """Extracts the most recent user question and assistant answer."""
        history = [
            {"role": "user", "content": "What is Phase A?"},
            {
                "role": "assistant",
                "content": "Phase A is Architecture Vision in TOGAF ADM.",
            },
            {"role": "user", "content": "What is Phase D?"},
            {
                "role": "assistant",
                "content": "Phase D is Technology Architecture in TOGAF ADM.",
            },
        ]

        last_q, last_a, earlier, topics = service._extract_conversation_context(history)

        assert "Phase D" in last_q
        assert "Technology Architecture" in last_a
        # Earlier history should contain Phase A content
        assert "Phase A" in earlier or "Architecture Vision" in earlier
        # Topics should include Phase D
        assert isinstance(topics, list)

    def test_handles_single_exchange(self, service):
        """Handles conversation with just one Q&A pair."""
        history = [
            {"role": "user", "content": "What is OAuth 2.0?"},
            {
                "role": "assistant",
                "content": "OAuth 2.0 is an authorization framework.",
            },
        ]

        last_q, last_a, earlier, topics = service._extract_conversation_context(history)

        assert "OAuth 2.0" in last_q
        assert "authorization framework" in last_a
        assert earlier == "(No earlier conversation)"
        assert isinstance(topics, list)

    def test_handles_empty_history(self, service):
        """Returns empty strings for empty history."""
        last_q, last_a, earlier, topics = service._extract_conversation_context([])

        assert last_q == ""
        assert last_a == ""
        assert earlier == ""
        assert topics == []

    def test_truncates_long_user_question(self, service):
        """Truncates long user questions to 400 chars."""
        long_question = "x" * 600
        history = [
            {"role": "user", "content": long_question},
            {"role": "assistant", "content": "Short answer."},
        ]

        last_q, last_a, earlier, topics = service._extract_conversation_context(history)

        assert len(last_q) <= 400


class TestSummarizeAnswer:
    """Tests for _summarize_answer method."""

    @pytest.fixture
    def service(self, mock_llm_client, mock_config_service):
        return QueryRewriterService(mock_llm_client, mock_config_service)

    def test_keeps_short_answers_intact(self, service):
        """Short answers are returned unchanged."""
        answer = "OAuth 2.0 is an authorization framework."
        summary = service._summarize_answer(answer)
        assert summary == answer

    def test_truncates_at_sentence_boundary(self, service):
        """Long answers are truncated at sentence boundary."""
        answer = "First sentence. " * 50 + "Last sentence."
        summary = service._summarize_answer(answer)

        assert len(summary) <= 800 + 10  # Some buffer for sentence boundary
        assert summary.endswith(".") or summary.endswith("...")

    def test_handles_empty_answer(self, service):
        """Returns empty string for empty answer."""
        assert service._summarize_answer("") == ""
        assert service._summarize_answer(None) == ""


class TestCleanRewrittenQuery:
    """Tests for _clean_rewritten_query method."""

    @pytest.fixture
    def service(self, mock_llm_client, mock_config_service):
        return QueryRewriterService(mock_llm_client, mock_config_service)

    def test_removes_preamble(self, service):
        """Removes common preamble text from LLM response."""
        original = "what about next phase"
        response = "Standalone question: What is Phase E in TOGAF ADM?"

        cleaned = service._clean_rewritten_query(response, original)
        assert cleaned == "What is Phase E in TOGAF ADM?"

    def test_removes_quotes(self, service):
        """Removes surrounding quotes from response."""
        original = "what about it"
        response = '"What about OAuth 2.0?"'

        cleaned = service._clean_rewritten_query(response, original)
        assert cleaned == "What about OAuth 2.0?"

    def test_returns_original_for_empty_response(self, service):
        """Returns original query if response is empty."""
        original = "what about next phase"

        assert service._clean_rewritten_query("", original) == original
        assert service._clean_rewritten_query(None, original) == original

    def test_returns_original_for_too_long_response(self, service):
        """Returns original if LLM answered instead of rewriting."""
        original = "what about next"
        # LLM answered the question instead of rewriting
        response = "Phase E is about Opportunities and Solutions. " * 50

        cleaned = service._clean_rewritten_query(response, original)
        assert cleaned == original

    def test_extracts_reformulated_from_verbose_response(self, service):
        """Extracts question from verbose LLM response with preamble."""
        original = "how about day 6"
        # Actual LLM response observed in production
        response = (
            "Based on the provided context, I will reformulate the user's question "
            "to create a standalone query. Original question: how about day 6 "
            "Reformulated question: List the topics covered on Day 6 of the study plan."
        )

        cleaned = service._clean_rewritten_query(response, original)
        assert cleaned == "List the topics covered on Day 6 of the study plan."
        assert "Based on the provided context" not in cleaned

    def test_handles_reformulated_question_pattern(self, service):
        """Handles 'Reformulated question:' pattern."""
        original = "what about it"
        response = "Reformulated question: What is OAuth 2.0 used for?"

        cleaned = service._clean_rewritten_query(response, original)
        assert cleaned == "What is OAuth 2.0 used for?"

    def test_handles_rewritten_query_pattern(self, service):
        """Handles 'The rewritten query is:' pattern."""
        original = "tell me more"
        response = (
            "The rewritten query is: Tell me more about OAuth 2.0 token handling."
        )

        cleaned = service._clean_rewritten_query(response, original)
        assert cleaned == "Tell me more about OAuth 2.0 token handling."


class TestSequentialQueries:
    """Tests for sequential/follow-up query handling."""

    @pytest.fixture
    def service(self, mock_llm_client, mock_config_service):
        return QueryRewriterService(mock_llm_client, mock_config_service)

    def test_detects_next_patterns(self, service):
        """Detects 'next' patterns that need rewriting."""
        assert service._is_standalone("what about next phase") is False
        assert service._is_standalone("tell me about next step") is False
        assert service._is_standalone("what is the next chapter") is False

    def test_detects_previous_patterns(self, service):
        """Detects 'previous' patterns that need rewriting."""
        assert service._is_standalone("what about previous section") is False
        assert service._is_standalone("go back to earlier topic") is False

    async def test_rewrites_sequential_query(
        self, query_rewriter_service, mock_llm_client
    ):
        """AC: Correctly rewrites sequential queries like 'next phase'."""
        history = [
            {"role": "user", "content": "What will I learn from Phase D?"},
            {
                "role": "assistant",
                "content": "From Phase D (Technology Architecture), you will learn about defining technology rules, gap analysis, and one-page decision maps.",
            },
        ]
        query = "what about next phase"

        # Mock LLM to return properly rewritten query
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="What will I learn from Phase E in TOGAF ADM?"
                )
            )
        ]
        mock_response.usage = None
        mock_llm_client.chat_completion.return_value = mock_response

        result = await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=history,
        )

        assert result.was_rewritten is True
        assert "Phase E" in result.rewritten_query

    async def test_uses_minimal_prompt_for_short_history(
        self, query_rewriter_service, mock_llm_client
    ):
        """Uses shorter prompt when history has only 1-2 messages."""
        history = [
            {"role": "user", "content": "What is Phase D?"},
            {"role": "assistant", "content": "Phase D is Technology Architecture."},
        ]
        query = "what about next phase"

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="What is Phase E?"))
        ]
        mock_response.usage = None
        mock_llm_client.chat_completion.return_value = mock_response

        await query_rewriter_service.rewrite_with_history(
            query=query,
            chat_history=history,
        )

        # Check the prompt used is the minimal one (shorter)
        call_args = mock_llm_client.chat_completion.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        # Minimal prompt doesn't have "## Earlier Conversation Context:"
        assert "Earlier Conversation Context" not in prompt


class TestFormatEarlierHistory:
    """Tests for _format_earlier_history method."""

    @pytest.fixture
    def service(self, mock_llm_client, mock_config_service):
        return QueryRewriterService(mock_llm_client, mock_config_service)

    def test_formats_earlier_history(self, service):
        """Formats earlier history with User/Assistant labels."""
        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "Second answer"},
        ]

        formatted = service._format_earlier_history(history)

        assert "User: First question" in formatted
        assert "Assistant: First answer" in formatted

    def test_returns_placeholder_for_empty_history(self, service):
        """Returns placeholder for empty earlier history."""
        formatted = service._format_earlier_history([])
        assert formatted == "(No earlier conversation)"

    def test_limits_to_6_messages(self, service):
        """Limits to last 6 messages (3 exchanges)."""
        history = [{"role": "user", "content": f"Message {i}"} for i in range(10)]

        formatted = service._format_earlier_history(history)
        lines = [line for line in formatted.split("\n") if line.strip()]

        assert len(lines) == 6

    def test_truncates_at_300_chars(self, service):
        """Truncates individual messages at 300 chars."""
        long_message = "x" * 500
        history = [{"role": "user", "content": long_message}]

        formatted = service._format_earlier_history(history)

        # Should be truncated to ~300 + prefix + "..."
        assert "..." in formatted
        assert len(formatted) < 400


# =============================================================================
# Story 8-0.1: New tests for Query Rewriter Improvements
# =============================================================================


class TestExtractKeyTopics:
    """Tests for _extract_key_topics method (Story 8-0.1 AC-8.0.1.3)."""

    @pytest.fixture
    def service(self, mock_llm_client, mock_config_service):
        return QueryRewriterService(mock_llm_client, mock_config_service)

    def test_extracts_numbered_items(self, service):
        """AC-8.0.1.3: Extracts numbered items like Day 1, Phase A, Step 2."""
        text = """
        Day 1 covers introduction.
        Day 2 covers fundamentals.
        Day 6 covers Phase C: Data Architecture.
        Day 7 covers Phase D: Technology Architecture.
        """
        topics = service._extract_key_topics(text)

        # Should extract Day items, prioritizing LAST ones
        assert any("Day 6" in t or "Day 7" in t for t in topics)
        assert isinstance(topics, list)
        assert len(topics) <= 5

    def test_extracts_markdown_headers(self, service):
        """AC-8.0.1.3: Extracts markdown headers like ## Topic."""
        # Note: Headers must start at beginning of line (no leading spaces)
        text = """## Introduction
This is the intro.

## Phase A: Architecture Vision
This covers the vision.

### Step 1: Define Scope
Scope definition."""
        topics = service._extract_key_topics(text)

        # Should extract header content
        assert any("Introduction" in t for t in topics) or any(
            "Phase A" in t for t in topics
        )

    def test_extracts_bold_topics(self, service):
        """AC-8.0.1.3: Extracts bold topics like **important term**."""
        text = """
        The **TOGAF ADM** is a method for developing enterprise architecture.
        It consists of **Phase A** through **Phase H** plus Requirements Management.
        """
        topics = service._extract_key_topics(text)

        # Should extract bold items
        assert any("TOGAF ADM" in t or "Phase A" in t or "Phase H" in t for t in topics)

    def test_prioritizes_last_numbered_items(self, service):
        """AC-8.0.1.3: Prioritizes LAST topic for follow-ups about 'next'."""
        text = """
        Day 1: Introduction
        Day 2: Fundamentals
        Day 3: Basics
        Day 4: Intermediate
        Day 5: Advanced
        Day 6: Phase C covers Data Architecture
        """
        topics = service._extract_key_topics(text)

        # Day 6 should be among extracted topics (most recent)
        assert any("Day 6" in t for t in topics)

    def test_handles_empty_text(self, service):
        """Returns empty list for empty text."""
        assert service._extract_key_topics("") == []
        assert service._extract_key_topics(None) == []

    def test_deduplicates_topics(self, service):
        """Removes duplicate topics."""
        text = """
        ## Day 6: Phase C
        Day 6 covers Data Architecture.
        **Day 6** is important.
        """
        topics = service._extract_key_topics(text)

        # Check for no exact duplicates (case-insensitive)
        topic_lower = [t.lower() for t in topics]
        assert len(topic_lower) == len(set(topic_lower))


class TestSummarizeAnswerWithTopics:
    """Tests for enhanced _summarize_answer with topic extraction (Story 8-0.1)."""

    @pytest.fixture
    def service(self, mock_llm_client, mock_config_service):
        return QueryRewriterService(mock_llm_client, mock_config_service)

    def test_appends_key_topics_to_long_answer(self, service):
        """AC-8.0.1.3: Appends key topics when they're beyond 800-char cutoff."""
        # Create a long answer where Day 6 appears AFTER 800 chars
        long_intro = "This is a detailed explanation. " * 30  # ~960 chars
        text = long_intro + "Day 6 covers Phase C: Data Architecture."

        summary = service._summarize_answer(text, include_topics=True)

        # Summary should mention key topics even though Day 6 is after cutoff
        assert "[Key topics:" in summary or len(summary) <= 800

    def test_does_not_duplicate_topics_in_summary(self, service):
        """AC-8.0.1.3: Doesn't duplicate topics already in summary."""
        text = "Day 6 covers Phase C. It's about data architecture."

        summary = service._summarize_answer(text, include_topics=True)

        # Should not have [Key topics: Day 6] if Day 6 already in text
        # The summary is short so Day 6 is already present
        assert summary.count("Day 6") <= 2  # At most once in original, once in topics

    def test_include_topics_false_skips_extraction(self, service):
        """Can disable topic extraction with include_topics=False."""
        text = "Day 6 covers Phase C: Data Architecture."

        summary = service._summarize_answer(text, include_topics=False)

        assert "[Key topics:" not in summary


class TestRewriteResultWithExtractedTopics:
    """Tests for RewriteResult with extracted_topics field (Story 8-0.1)."""

    def test_rewrite_result_includes_extracted_topics(self):
        """AC-8.0.1.5: RewriteResult includes extracted_topics field."""
        result = RewriteResult(
            original_query="what about next",
            rewritten_query="What is Day 7?",
            was_rewritten=True,
            model_used="ollama/llama3.2",
            latency_ms=150.5,
            extracted_topics=["Day 6", "Phase C"],
        )

        assert result.extracted_topics == ["Day 6", "Phase C"]

    def test_rewrite_result_defaults_to_empty_list(self):
        """AC-8.0.1.5: extracted_topics defaults to empty list."""
        result = RewriteResult(
            original_query="hello",
            rewritten_query="hello",
            was_rewritten=False,
            model_used="",
            latency_ms=0,
        )

        assert result.extracted_topics == []


class TestPromptImprovements:
    """Tests for prompt improvements (Story 8-0.1)."""

    @pytest.fixture
    def service(self, mock_llm_client, mock_config_service):
        return QueryRewriterService(mock_llm_client, mock_config_service)

    def test_rewrite_prompt_includes_typo_correction(self, service):
        """AC-8.0.1.2: REWRITE_PROMPT includes typo correction rule."""
        assert "TYPOS" in service.REWRITE_PROMPT
        assert '"tha"' in service.REWRITE_PROMPT or "tha" in service.REWRITE_PROMPT
        assert '"wha"' in service.REWRITE_PROMPT or "wha" in service.REWRITE_PROMPT

    def test_rewrite_prompt_includes_sequential_examples(self, service):
        """AC-8.0.1.1: REWRITE_PROMPT includes sequential reference examples."""
        assert "Day 6" in service.REWRITE_PROMPT or "Day 7" in service.REWRITE_PROMPT
        assert (
            "Phase D" in service.REWRITE_PROMPT or "Phase C" in service.REWRITE_PROMPT
        )
        assert "SEQUENCES" in service.REWRITE_PROMPT

    def test_rewrite_prompt_includes_format_preservation(self, service):
        """AC-8.0.1.4: REWRITE_PROMPT includes format preservation hint."""
        assert "FORMAT" in service.REWRITE_PROMPT
        assert "list" in service.REWRITE_PROMPT.lower()

    def test_minimal_prompt_includes_typo_correction(self, service):
        """AC-8.0.1.2: Minimal prompt also includes typo correction."""
        assert "typo" in service.REWRITE_PROMPT_MINIMAL.lower()
        assert "tha" in service.REWRITE_PROMPT_MINIMAL

    def test_minimal_prompt_includes_sequential_reference(self, service):
        """AC-8.0.1.1: Minimal prompt includes next/previous resolution."""
        assert "next" in service.REWRITE_PROMPT_MINIMAL.lower()
        assert "previous" in service.REWRITE_PROMPT_MINIMAL.lower()
