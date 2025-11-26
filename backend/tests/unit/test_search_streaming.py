"""Unit tests for SSE streaming search functionality.

Tests SearchService._search_stream() and SSE event serialization.
All dependencies (LiteLLM, Qdrant) are mocked.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.citation import Citation
from app.schemas.search import SearchResultSchema
from app.schemas.sse import (
    CitationEvent,
    DoneEvent,
    ErrorEvent,
    StatusEvent,
    TokenEvent,
)
from app.services.search_service import SearchService


@pytest.mark.unit
@pytest.mark.asyncio
class TestSSEEventSerialization:
    """Test SSE event model serialization to SSE format."""

    def test_status_event_serialization(self):
        """StatusEvent converts to proper SSE format."""
        event = StatusEvent(content="Searching knowledge bases...")

        sse_str = event.to_sse_format()

        assert sse_str.startswith("data: ")
        assert sse_str.endswith("\n\n")
        assert '"type":"status"' in sse_str
        assert '"content":"Searching knowledge bases..."' in sse_str

    def test_token_event_serialization(self):
        """TokenEvent converts to proper SSE format."""
        event = TokenEvent(content="OAuth ")

        sse_str = event.to_sse_format()

        assert sse_str.startswith("data: ")
        assert '"type":"token"' in sse_str
        assert '"content":"OAuth "' in sse_str

    def test_citation_event_serialization(self):
        """CitationEvent converts to proper SSE format with nested data."""
        event = CitationEvent(
            data={
                "number": 1,
                "document_id": "doc-123",
                "document_name": "Test.pdf",
                "page_number": 14,
                "excerpt": "Test excerpt",
                "char_start": 100,
                "char_end": 200,
                "confidence": 0.92,
            }
        )

        sse_str = event.to_sse_format()

        assert '"type":"citation"' in sse_str
        assert '"data":{' in sse_str
        assert '"number":1' in sse_str
        assert '"document_name":"Test.pdf"' in sse_str

    def test_done_event_serialization(self):
        """DoneEvent converts to proper SSE format."""
        event = DoneEvent(confidence=0.88, result_count=5)

        sse_str = event.to_sse_format()

        assert '"type":"done"' in sse_str
        assert '"confidence":0.88' in sse_str
        assert '"result_count":5' in sse_str

    def test_error_event_serialization(self):
        """ErrorEvent converts to proper SSE format."""
        event = ErrorEvent(
            message="Search service temporarily unavailable",
            code="SERVICE_UNAVAILABLE",
        )

        sse_str = event.to_sse_format()

        assert '"type":"error"' in sse_str
        assert '"message":"Search service temporarily unavailable"' in sse_str
        assert '"code":"SERVICE_UNAVAILABLE"' in sse_str


@pytest.mark.unit
@pytest.mark.asyncio
class TestSearchServiceStreaming:
    """Test SearchService streaming methods with mocked dependencies."""

    @pytest.fixture
    def mock_permission_service(self):
        """Mock permission service."""
        service = MagicMock()
        service.get_permitted_kb_ids = AsyncMock(return_value=["kb-123"])
        service.check_permission = AsyncMock(return_value=True)
        return service

    @pytest.fixture
    def mock_audit_service(self):
        """Mock audit service."""
        service = MagicMock()
        service.log_search = AsyncMock()
        return service

    @pytest.fixture
    def mock_citation_service(self):
        """Mock citation service."""
        service = MagicMock()
        # Mock _map_marker_to_chunk to return a Citation
        service._map_marker_to_chunk = MagicMock(
            return_value=Citation(
                number=1,
                document_id="doc-123",
                document_name="Test.pdf",
                page_number=14,
                section_header="Section",
                excerpt="Test excerpt",
                char_start=100,
                char_end=200,
                confidence=0.92,
            )
        )
        return service

    @pytest.fixture
    def search_service(
        self, mock_permission_service, mock_audit_service, mock_citation_service
    ):
        """Create SearchService with mocked dependencies."""
        # Mock qdrant_service to avoid initialization
        with patch("app.services.search_service.qdrant_service") as mock_qdrant_service:
            mock_qdrant_service.client = MagicMock()

            service = SearchService(
                permission_service=mock_permission_service,
                audit_service=mock_audit_service,
                citation_service=mock_citation_service,
            )
            # Keep mock active for test
            service.qdrant_client = MagicMock()
            return service

    @pytest.fixture
    def mock_search_results(self):
        """Mock search results."""
        return [
            SearchResultSchema(
                document_id="doc-123",
                document_name="Test.pdf",
                kb_id="kb-123",
                kb_name="Test KB",
                chunk_text="OAuth 2.0 authentication",
                relevance_score=0.92,
                page_number=14,
                section_header="Auth",
                char_start=100,
                char_end=200,
            )
        ]

    async def test_search_stream_yields_correct_event_types(
        self,
        search_service,
        mock_search_results,  # noqa: ARG002
    ):
        """_search_stream yields events in correct sequence."""
        # Mock dependencies
        with patch.object(
            search_service, "_embed_query", new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            with patch.object(
                search_service, "_search_collections", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = [
                    {
                        "document_id": "doc-123",
                        "document_name": "Test.pdf",
                        "kb_id": "kb-123",
                        "kb_name": "Test KB",
                        "chunk_text": "OAuth 2.0",
                        "score": 0.92,
                        "page_number": 14,
                        "section_header": "Auth",
                        "char_start": 100,
                        "char_end": 200,
                    }
                ]

                # Mock _synthesize_answer_stream to yield string tokens directly
                async def mock_llm_stream(*args, **kwargs):
                    """Mock async generator yielding string tokens (not chunk objects)."""
                    tokens = ["OAuth ", "2.0 ", "[1]"]
                    for token in tokens:
                        yield token

                with patch.object(
                    search_service,
                    "_synthesize_answer_stream",
                    side_effect=mock_llm_stream,
                ):
                    # Execute streaming search
                    events = []
                    async for event in search_service._search_stream(
                        query="test query",
                        kb_ids=["kb-123"],
                        user_id="user-1",
                        limit=10,
                    ):
                        events.append(event)

                    # Verify event sequence
                    assert len(events) >= 5  # 2 status + 3 tokens + 1 citation + 1 done
                    assert isinstance(events[0], StatusEvent)
                    assert events[0].content == "Searching knowledge bases..."
                    assert isinstance(events[1], StatusEvent)
                    assert events[1].content == "Generating answer..."

                    # Check for token events
                    token_events = [e for e in events if isinstance(e, TokenEvent)]
                    assert len(token_events) == 3
                    assert token_events[0].content == "OAuth "

                    # Check for citation event
                    citation_events = [
                        e for e in events if isinstance(e, CitationEvent)
                    ]
                    assert len(citation_events) == 1
                    assert citation_events[0].data["number"] == 1

                    # Check for done event
                    done_events = [e for e in events if isinstance(e, DoneEvent)]
                    assert len(done_events) == 1
                    assert 0.0 <= done_events[0].confidence <= 1.0
                    assert done_events[0].result_count > 0

    async def test_citation_event_emitted_when_marker_detected(
        self,
        search_service,
        mock_search_results,  # noqa: ARG002
    ):
        """Citation event is emitted immediately when [n] marker detected in stream."""
        # Mock dependencies
        with patch.object(
            search_service, "_embed_query", new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            with patch.object(
                search_service, "_search_collections", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = [
                    {
                        "document_id": "doc-123",
                        "document_name": "Test.pdf",
                        "kb_id": "kb-123",
                        "chunk_text": "OAuth 2.0",
                        "score": 0.92,
                        "page_number": 14,
                        "char_start": 100,
                        "char_end": 200,
                    }
                ]

                # Mock _synthesize_answer_stream to yield string tokens directly
                async def mock_llm_stream(*args, **kwargs):
                    """Mock async generator yielding string tokens with citation markers."""
                    tokens = ["Auth ", "uses ", "[1]", " and ", "[2]"]
                    for token in tokens:
                        yield token

                with patch.object(
                    search_service,
                    "_synthesize_answer_stream",
                    side_effect=mock_llm_stream,
                ):
                    # Execute
                    events = []
                    async for event in search_service._search_stream(
                        query="test", kb_ids=["kb-123"], user_id="user-1", limit=10
                    ):
                        events.append(event)

                    # Verify citation events emitted for [1] only (only 1 chunk available)
                    citation_events = [
                        e for e in events if isinstance(e, CitationEvent)
                    ]
                    assert len(citation_events) == 1  # Only [1] valid
                    assert citation_events[0].data["number"] == 1

    async def test_done_event_includes_confidence_and_count(
        self,
        search_service,
        mock_search_results,  # noqa: ARG002
    ):
        """Done event includes confidence score and result count."""
        # Mock dependencies
        with patch.object(
            search_service, "_embed_query", new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            with patch.object(
                search_service, "_search_collections", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = [
                    {
                        "document_id": "doc-123",
                        "document_name": "Test.pdf",
                        "kb_id": "kb-123",
                        "chunk_text": "OAuth 2.0",
                        "score": 0.85,
                        "page_number": 14,
                        "char_start": 100,
                        "char_end": 200,
                    },
                    {
                        "document_id": "doc-456",
                        "document_name": "Test2.pdf",
                        "kb_id": "kb-123",
                        "chunk_text": "MFA required",
                        "score": 0.80,
                        "page_number": 20,
                        "char_start": 300,
                        "char_end": 400,
                    },
                ]

                async def mock_llm_stream(*args, **kwargs):
                    """Mock async generator yielding single token."""
                    yield "Done"

                with patch.object(
                    search_service,
                    "_synthesize_answer_stream",
                    side_effect=mock_llm_stream,
                ):
                    # Execute
                    events = []
                    async for event in search_service._search_stream(
                        query="test", kb_ids=["kb-123"], user_id="user-1", limit=10
                    ):
                        events.append(event)

                    # Find done event
                    done_event = next(e for e in events if isinstance(e, DoneEvent))

                    assert 0.0 <= done_event.confidence <= 1.0
                    assert done_event.result_count == 2

    async def test_error_event_on_llm_failure(self, search_service):
        """Error event emitted when LLM streaming fails."""
        # Mock dependencies
        with patch.object(
            search_service, "_embed_query", new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            with patch.object(
                search_service, "_search_collections", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = [
                    {
                        "document_id": "doc-123",
                        "document_name": "Test.pdf",
                        "kb_id": "kb-123",
                        "chunk_text": "Test",
                        "score": 0.9,
                        "page_number": 1,
                        "char_start": 0,
                        "char_end": 100,
                    }
                ]

                # Mock LLM stream that raises exception - must be async generator
                async def mock_llm_stream(*args, **kwargs):
                    raise Exception("LLM timeout")
                    yield  # Make it a generator (unreachable but needed for typing)

                with patch.object(
                    search_service,
                    "_synthesize_answer_stream",
                    side_effect=mock_llm_stream,
                ):
                    # Execute
                    events = []
                    async for event in search_service._search_stream(
                        query="test", kb_ids=["kb-123"], user_id="user-1", limit=10
                    ):
                        events.append(event)

                    # Verify error event emitted
                    error_events = [e for e in events if isinstance(e, ErrorEvent)]
                    assert len(error_events) == 1
                    assert error_events[0].code == "SERVICE_ERROR"
                    assert "unavailable" in error_events[0].message.lower()

    async def test_no_results_emits_done_immediately(self, search_service):
        """When no search results, emit done event immediately with confidence=0."""
        # Mock empty search results
        with patch.object(
            search_service, "_embed_query", new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            with patch.object(
                search_service, "_search_collections", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = []  # No results

                # Execute
                events = []
                async for event in search_service._search_stream(
                    query="test", kb_ids=["kb-123"], user_id="user-1", limit=10
                ):
                    events.append(event)

                # Should only have: 1 status event + 1 done event
                assert len(events) == 2
                assert isinstance(events[0], StatusEvent)
                assert isinstance(events[1], DoneEvent)
                assert events[1].confidence == 0.0
                assert events[1].result_count == 0
