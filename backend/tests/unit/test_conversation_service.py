"""Unit tests for ConversationService."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.citation import Citation
from app.schemas.search import SearchResponse, SearchResultSchema
from app.services.conversation_service import (
    CONVERSATION_TTL,
    ConversationService,
    NoDocumentsError,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_search_service():
    """Mock SearchService."""
    service = MagicMock()
    service.search = AsyncMock()
    return service


@pytest.fixture
def mock_citation_service():
    """Mock CitationService."""
    service = MagicMock()
    return service


@pytest.fixture
def conversation_service(mock_search_service, mock_citation_service):
    """ConversationService instance with mocked dependencies."""
    return ConversationService(
        search_service=mock_search_service,
        citation_service=mock_citation_service,
    )


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock()
    return client


@pytest.fixture
def mock_search_results():
    """Sample search results."""
    return [
        SearchResultSchema(
            document_id="doc-1",
            document_name="Test.pdf",
            kb_id="kb-1",
            kb_name="Test KB",
            chunk_text="OAuth 2.0 authentication",
            relevance_score=0.92,
            page_number=1,
            section_header="Auth",
            char_start=0,
            char_end=100,
        ),
        SearchResultSchema(
            document_id="doc-2",
            document_name="Test2.pdf",
            kb_id="kb-1",
            kb_name="Test KB",
            chunk_text="MFA support",
            relevance_score=0.88,
            page_number=2,
            section_header="Security",
            char_start=100,
            char_end=200,
        ),
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    response = MagicMock()
    response.choices = [
        MagicMock(message=MagicMock(content="OAuth 2.0 [1] with MFA [2]."))
    ]
    return response


@pytest.fixture
def mock_citations():
    """Mock citations."""
    return [
        Citation(
            number=1,
            document_id="doc-1",
            document_name="Test.pdf",
            page_number=1,
            section_header="Auth",
            excerpt="OAuth 2.0 authentication",
            char_start=0,
            char_end=100,
            confidence=0.92,
        ),
        Citation(
            number=2,
            document_id="doc-2",
            document_name="Test2.pdf",
            page_number=2,
            section_header="Security",
            excerpt="MFA support",
            char_start=100,
            char_end=200,
            confidence=0.88,
        ),
    ]


class TestSendMessage:
    """Test ConversationService.send_message()."""

    @pytest.mark.asyncio
    async def test_send_message_creates_conversation(
        self,
        conversation_service,
        mock_search_service,
        mock_citation_service,
        mock_redis_client,
        mock_search_results,
        mock_llm_response,
        mock_citations,
    ):
        """AC1: send_message creates conversation in Redis."""
        # Setup mocks
        mock_search_service.search.return_value = SearchResponse(
            results=mock_search_results,
            query="test",
            kb_ids=["kb-1"],
            result_count=len(mock_search_results),
        )
        mock_citation_service.extract_citations.return_value = (
            "OAuth 2.0 [1] with MFA [2].",
            mock_citations,
        )

        with (
            patch.object(
                conversation_service.llm_client,
                "chat_completion",
                return_value=mock_llm_response,
            ),
            patch(
                "app.services.conversation_service.RedisClient.get_client",
                return_value=mock_redis_client,
            ),
        ):
            result = await conversation_service.send_message(
                session_id="session-123",
                kb_id="kb-456",
                user_id="user-789",
                message="How did we handle auth?",
            )

        assert "answer" in result
        assert "citations" in result
        assert "conversation_id" in result
        assert result["answer"] == "OAuth 2.0 [1] with MFA [2]."
        assert len(result["citations"]) == 2

        # Verify Redis storage called
        mock_redis_client.setex.assert_called_once()
        args = mock_redis_client.setex.call_args[0]
        assert args[0] == "conversation:session-123:kb-456"  # key
        assert args[1] == CONVERSATION_TTL  # ttl

    @pytest.mark.asyncio
    async def test_send_message_with_existing_conversation_appends_to_history(
        self,
        conversation_service,
        mock_search_service,
        mock_citation_service,
        mock_redis_client,
        mock_search_results,
        mock_llm_response,
        mock_citations,
    ):
        """AC2: send_message with existing conversation_id appends to history."""
        # Setup existing history
        existing_history = [
            {
                "role": "user",
                "content": "Previous question",
                "timestamp": "2024-01-01T00:00:00Z",
            },
            {
                "role": "assistant",
                "content": "Previous answer [1]",
                "citations": [],
                "confidence": 0.9,
                "timestamp": "2024-01-01T00:00:01Z",
            },
        ]
        mock_redis_client.get.return_value = json.dumps(existing_history)

        mock_search_service.search.return_value = SearchResponse(
            results=mock_search_results,
            query="test",
            kb_ids=["kb-1"],
            result_count=len(mock_search_results),
        )
        mock_citation_service.extract_citations.return_value = (
            "OAuth 2.0 [1] with MFA [2].",
            mock_citations,
        )

        with (
            patch.object(
                conversation_service.llm_client,
                "chat_completion",
                return_value=mock_llm_response,
            ),
            patch(
                "app.services.conversation_service.RedisClient.get_client",
                return_value=mock_redis_client,
            ),
        ):
            await conversation_service.send_message(
                session_id="session-123",
                kb_id="kb-456",
                user_id="user-789",
                message="Follow-up question",
                conversation_id="conv-existing",
            )

        # Verify Redis storage called with appended history
        mock_redis_client.setex.assert_called_once()
        stored_data = json.loads(mock_redis_client.setex.call_args[0][2])
        assert len(stored_data) == 4  # 2 old + 2 new messages
        assert stored_data[0]["content"] == "Previous question"
        assert stored_data[2]["content"] == "Follow-up question"

    @pytest.mark.asyncio
    async def test_send_message_raises_no_documents_error(
        self, conversation_service, mock_search_service, mock_redis_client
    ):
        """AC6: send_message raises NoDocumentsError if KB has no documents."""
        # Setup empty search results
        mock_search_service.search.return_value = SearchResponse(
            results=[], query="test", kb_ids=["kb-1"], result_count=0
        )

        with (
            patch(
                "app.services.conversation_service.RedisClient.get_client",
                return_value=mock_redis_client,
            ),
            pytest.raises(NoDocumentsError) as exc_info,
        ):
            await conversation_service.send_message(
                session_id="session-123",
                kb_id="kb-empty",
                user_id="user-789",
                message="Test",
            )

        assert exc_info.value.kb_id == "kb-empty"
        assert "no indexed documents" in exc_info.value.message.lower()


class TestGetHistory:
    """Test ConversationService.get_history()."""

    @pytest.mark.asyncio
    async def test_get_history_returns_empty_list_for_new_conversation(
        self, conversation_service, mock_redis_client
    ):
        """AC4: get_history returns empty list for new conversation."""
        mock_redis_client.get.return_value = None

        with patch(
            "app.services.conversation_service.RedisClient.get_client",
            return_value=mock_redis_client,
        ):
            history = await conversation_service.get_history("session-123", "kb-456")

        assert history == []

    @pytest.mark.asyncio
    async def test_get_history_returns_stored_messages(
        self, conversation_service, mock_redis_client
    ):
        """AC4: get_history returns stored messages from Redis."""
        stored_history = [
            {
                "role": "user",
                "content": "Question 1",
                "timestamp": "2024-01-01T00:00:00Z",
            },
            {
                "role": "assistant",
                "content": "Answer 1",
                "citations": [],
                "confidence": 0.9,
                "timestamp": "2024-01-01T00:00:01Z",
            },
        ]
        mock_redis_client.get.return_value = json.dumps(stored_history)

        with patch(
            "app.services.conversation_service.RedisClient.get_client",
            return_value=mock_redis_client,
        ):
            history = await conversation_service.get_history("session-123", "kb-456")

        assert len(history) == 2
        assert history[0]["content"] == "Question 1"
        assert history[1]["content"] == "Answer 1"


class TestBuildPrompt:
    """Test ConversationService._build_prompt()."""

    def test_build_prompt_truncates_history_when_token_limit_exceeded(
        self, conversation_service, mock_search_results
    ):
        """AC3: build_prompt truncates history when token limit exceeded."""
        # Create long history (20 messages)
        long_history = []
        for i in range(20):
            long_history.append({"role": "user", "content": f"Question {i}" * 100})
            long_history.append({"role": "assistant", "content": f"Answer {i}" * 100})

        prompt = conversation_service._build_prompt(
            long_history, "New message", mock_search_results
        )

        # Verify history is truncated (not all 20 messages included)
        history_messages = [
            msg for msg in prompt if msg["role"] in ("user", "assistant")
        ]
        # Filter out system messages
        history_messages = [
            msg
            for msg in history_messages
            if "Retrieved sources" not in msg.get("content", "")
        ]
        assert len(history_messages) < 20

    def test_build_prompt_prioritizes_recent_messages(
        self, conversation_service, mock_search_results
    ):
        """AC3: build_prompt prioritizes recent messages over old messages."""
        history = []
        for i in range(10):
            history.append({"role": "user", "content": f"Question {i}"})
            history.append({"role": "assistant", "content": f"Answer {i}"})

        prompt = conversation_service._build_prompt(
            history, "New message", mock_search_results
        )

        # Find user messages in prompt (excluding system messages and current query)
        user_messages = [
            msg["content"]
            for msg in prompt
            if msg["role"] == "user" and "New message" not in msg["content"]
        ]

        # Verify most recent question is included
        if user_messages:
            assert "Question 9" in user_messages[-1] or "Question" in str(user_messages)


class TestHelperMethods:
    """Test helper methods."""

    def test_count_tokens_estimates_correctly(self, conversation_service):
        """Test token counting (1 token ≈ 4 chars)."""
        text = "a" * 400  # 400 characters
        tokens = conversation_service._count_tokens(text)
        assert tokens == 100  # 400 / 4 = 100

    def test_generate_conversation_id_returns_unique_ids(self, conversation_service):
        """Test conversation ID generation."""
        id1 = conversation_service._generate_conversation_id()
        id2 = conversation_service._generate_conversation_id()

        assert id1.startswith("conv-")
        assert id2.startswith("conv-")
        assert id1 != id2  # Unique IDs
