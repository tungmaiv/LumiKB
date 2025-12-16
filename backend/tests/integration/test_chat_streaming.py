"""Integration tests for Chat Streaming API (Story 4.2).

DEFERRED TO STORY 5.15 - Technical Debt TD-4.2-1
Status: Tests written but skipped due to missing external service mocks
Blocking Issue: Requires Qdrant mock and LiteLLM mock fixtures from Story 4.1 (TD-4.1-1)

Implementation Status:
✅ SSE streaming endpoint implemented (backend/app/api/v1/chat_stream.py)
✅ ConversationService.send_message_stream() method implemented
✅ Real LLM token streaming (not word-split simulation)
✅ Inline citation detection during streaming
✅ Event schema: status, token, citation, confidence, done, error

Test Coverage Plan:
- P1: SSE connection establishment (Content-Type: text/event-stream)
- P1: Event order validation (status → tokens → citations → confidence → done)
- P1: Token streaming in real-time
- P1: Citation events emitted inline as markers appear
- P1: Confidence event after streaming complete
- P1: Error event handling (LLM failure, permission denied)
- P1: Connection cleanup (done event closes stream)
- P2: Permission enforcement (404 for unauthorized KB)
- P2: Empty KB error handling

Resolution Plan:
Epic 5, Story 5.15: "Epic 4 ATDD Transition to GREEN"
1. Implement Qdrant mock fixture (mock_qdrant_search)
2. Implement LiteLLM mock fixture (mock_litellm_generate_stream)
3. Remove pytest.mark.skip decorators
4. Transition all tests to GREEN

Reference:
- docs/sprint-artifacts/epic-4-tech-debt.md#TD-4.2-1
- docs/sprint-artifacts/epic-5-tech-debt.md#TD-4.2-1
- backend/app/api/v1/chat_stream.py - SSE endpoint implementation
"""

import json

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


@pytest.mark.skip(reason="Deferred to Story 5.15 - Missing Qdrant + LiteLLM mocks (TD-4.2-1)")
class TestChatStreamingAPI:
    """Test Chat Streaming SSE API endpoints."""

    @pytest.mark.asyncio
    async def test_sse_connection_established(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        mock_qdrant_search,  # TODO: Implement in Story 5.15
        mock_litellm_generate_stream,  # TODO: Implement in Story 5.15
    ):
        """
        AC1: SSE connection returns text/event-stream Content-Type.

        GIVEN: User sends message to streaming endpoint
        WHEN: POST /api/v1/chat/stream is called
        THEN: Response has Content-Type: text/event-stream
        AND: Connection stays open during streaming
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        # Use streaming client
        async with api_client.stream(
            "POST",
            "/api/v1/chat/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "What is OAuth 2.0?",
            },
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            assert response.headers["cache-control"] == "no-cache"

            # Stream should remain open
            assert not response.is_closed

    @pytest.mark.asyncio
    async def test_sse_events_in_correct_order(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        mock_qdrant_search,
        mock_litellm_generate_stream,
    ):
        """
        AC1: SSE events arrive in correct order.

        GIVEN: User sends message
        WHEN: Response streams
        THEN: Events arrive in order: status → tokens → citations → confidence → done
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        events = []
        async with api_client.stream(
            "POST",
            "/api/v1/chat/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "What is JWT?",
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data["type"])

                    if event_data["type"] == "done":
                        break

        # Verify event order
        assert events[0] == "status"  # First event is status
        assert "token" in events  # Tokens streamed
        assert "citation" in events or "confidence" in events  # Citations or confidence
        assert events[-1] == "done"  # Last event is done

    @pytest.mark.asyncio
    async def test_sse_token_events_stream_incrementally(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        mock_qdrant_search,
        mock_litellm_generate_stream,
    ):
        """
        AC2: Token events arrive incrementally (not batched).

        GIVEN: LLM is generating response
        WHEN: Tokens arrive from LLM
        THEN: Each token is sent as separate SSE event immediately
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        token_events = []
        async with api_client.stream(
            "POST",
            "/api/v1/chat/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "Explain authentication",
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])

                    if event_data["type"] == "token":
                        token_events.append(event_data["content"])

                    if event_data["type"] == "done":
                        break

        # Should have multiple token events (not batched into one)
        assert len(token_events) > 1

        # Each token should be small (word-by-word streaming)
        for token in token_events:
            assert len(token) < 50  # Tokens are words/phrases, not full sentences

    @pytest.mark.asyncio
    async def test_sse_citation_events_emitted_inline(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        mock_qdrant_search,
        mock_litellm_generate_stream,
    ):
        """
        AC3: Citation events emitted as [n] markers appear in token stream.

        GIVEN: LLM response contains citation markers [1], [2]
        WHEN: Token events include markers
        THEN: Citation events emitted immediately when markers detected
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        citation_events = []
        token_stream = ""

        async with api_client.stream(
            "POST",
            "/api/v1/chat/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "What is OAuth 2.0?",
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])

                    if event_data["type"] == "token":
                        token_stream += event_data["content"]

                    if event_data["type"] == "citation":
                        citation_events.append(event_data)

                    if event_data["type"] == "done":
                        break

        # Should have citation events
        assert len(citation_events) > 0

        # Verify citation data structure
        citation = citation_events[0]
        assert "number" in citation
        assert "data" in citation
        assert citation["data"]["document_name"]
        assert citation["data"]["excerpt"]
        assert citation["data"]["confidence"]

        # Token stream should contain citation markers
        assert "[1]" in token_stream or "[2]" in token_stream

    @pytest.mark.asyncio
    async def test_sse_confidence_event_after_streaming(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        mock_qdrant_search,
        mock_litellm_generate_stream,
    ):
        """
        AC4: Confidence event emitted after token streaming completes.

        GIVEN: Response has finished streaming
        WHEN: Confidence calculation is complete
        THEN: Confidence event emitted before done event
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        events = []
        async with api_client.stream(
            "POST",
            "/api/v1/chat/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "Test query",
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)

                    if event_data["type"] == "done":
                        break

        # Find confidence event
        confidence_events = [e for e in events if e["type"] == "confidence"]
        assert len(confidence_events) == 1

        confidence_event = confidence_events[0]
        assert "score" in confidence_event
        assert 0.0 <= confidence_event["score"] <= 1.0

        # Confidence should come before done
        confidence_index = events.index(confidence_events[0])
        done_index = next(i for i, e in enumerate(events) if e["type"] == "done")
        assert confidence_index < done_index

    @pytest.mark.asyncio
    async def test_sse_error_event_on_llm_failure(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        mock_qdrant_search,
        mock_litellm_generate_stream_failure,  # TODO: Mock that raises exception
    ):
        """
        AC6: Error event emitted when LLM generation fails.

        GIVEN: LLM raises exception during generation
        WHEN: Error occurs
        THEN: Error event is streamed with error message
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        error_event = None
        async with api_client.stream(
            "POST",
            "/api/v1/chat/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "Trigger LLM failure",
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])

                    if event_data["type"] == "error":
                        error_event = event_data
                        break

        assert error_event is not None
        assert "message" in error_event
        assert len(error_event["message"]) > 0

    @pytest.mark.asyncio
    async def test_sse_permission_enforcement(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
    ):
        """
        AC5: Permission check returns 404 for unauthorized KB.

        GIVEN: User does not have READ permission on KB
        WHEN: User tries to stream chat
        THEN: Response is 404 (not 403 to avoid leaking KB existence)
        """
        fake_kb_id = "00000000-0000-0000-0000-000000000000"

        response = await api_client.post(
            "/api/v1/chat/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": fake_kb_id,
                "message": "Test message",
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_sse_empty_kb_error(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        empty_kb_factory,
        mock_qdrant_search_empty,  # TODO: Mock returns empty results
    ):
        """
        AC6: KB with no documents returns error event.

        GIVEN: KB has no indexed documents
        WHEN: User sends message
        THEN: Error event is streamed with "no indexed documents" message
        """
        empty_kb = await empty_kb_factory()

        error_event = None
        async with api_client.stream(
            "POST",
            "/api/v1/chat/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": str(empty_kb.id),
                "message": "Test message",
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])

                    if event_data["type"] == "error":
                        error_event = event_data
                        break

        assert error_event is not None
        assert "no indexed documents" in error_event["message"].lower()

    @pytest.mark.asyncio
    async def test_sse_connection_cleanup_on_done(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        mock_qdrant_search,
        mock_litellm_generate_stream,
    ):
        """
        AC6: SSE connection closes cleanly after done event.

        GIVEN: Streaming is complete
        WHEN: Done event is emitted
        THEN: Connection closes (no more events sent)
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        done_event_received = False
        events_after_done = []

        async with api_client.stream(
            "POST",
            "/api/v1/chat/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "Test query",
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])

                    if done_event_received:
                        # Should not receive events after done
                        events_after_done.append(event_data)

                    if event_data["type"] == "done":
                        done_event_received = True

        assert done_event_received
        # No events should come after done
        assert len(events_after_done) == 0
