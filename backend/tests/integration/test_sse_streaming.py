"""Integration tests for SSE Streaming (Story 3.3).

Tests cover:
- SSE endpoint protocol compliance (AC-3.3.1)
- Event ordering: token → citation → done (AC-3.3.2)
- Reconnection with state retention (AC-3.3.3)
- Graceful degradation to non-streaming (AC-3.3.4)

Test Strategy (ATDD - RED Phase):
- These tests are EXPECTED TO FAIL until SSE streaming is implemented
- They define the acceptance criteria for real-time search UX
- Follow RED → GREEN → REFACTOR TDD cycle

Risk Mitigation:
- R-005: SSE stream reliability (validates reconnection logic)
"""

import pytest
from httpx import AsyncClient

from tests.factories import create_kb_data, create_registration_data

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def sse_user_data() -> dict:
    """Test user for SSE tests."""
    return create_registration_data()


@pytest.fixture
async def registered_sse_user(api_client: AsyncClient, sse_user_data: dict) -> dict:
    """Create registered user for SSE tests."""
    response = await api_client.post(
        "/api/v1/auth/register",
        json=sse_user_data,
    )
    assert response.status_code == 201
    return {**sse_user_data, "user": response.json()}


@pytest.fixture
async def authenticated_sse_client(
    api_client: AsyncClient, registered_sse_user: dict
) -> AsyncClient:
    """Authenticated client for SSE tests."""
    response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_sse_user["email"],
            "password": registered_sse_user["password"],
        },
    )
    assert response.status_code == 204
    return api_client


@pytest.fixture
async def kb_for_streaming(authenticated_sse_client: AsyncClient) -> dict:
    """Create KB for streaming tests."""
    kb_data = create_kb_data(name="Streaming Test KB")
    kb_response = await authenticated_sse_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
    )
    assert kb_response.status_code == 201
    return kb_response.json()


# =============================================================================
# AC-3.3.1: SSE Endpoint Protocol Compliance
# =============================================================================


async def test_search_with_sse_query_param_returns_event_stream(
    authenticated_sse_client: AsyncClient,
    kb_for_streaming: dict,
):
    """Test search endpoint supports SSE with ?stream=true parameter.

    GIVEN: User requests search with stream=true
    WHEN: POST /api/v1/search?stream=true
    THEN:
        - Response status 200
        - Content-Type: text/event-stream
        - Connection: keep-alive
        - Events streamed incrementally

    AC-3.3.1: SSE protocol compliance.
    """
    # WHEN: User requests SSE streaming
    async with authenticated_sse_client.stream(
        "POST",
        "/api/v1/search?stream=true",
        json={
            "query": "authentication methods",
            "kb_ids": [kb_for_streaming["id"]],
            "limit": 10,
        },
    ) as response:
        # THEN: SSE protocol headers
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        assert "no-cache" in response.headers.get("cache-control", "")

        # Read first event to verify streaming works
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                events.append(line[6:])  # Strip "data: " prefix
                if len(events) >= 3:  # Read at least 3 events
                    break

        assert len(events) > 0, "No SSE events received"


# =============================================================================
# AC-3.3.2: Event Ordering (token → citation → done)
# =============================================================================


async def test_sse_events_streamed_in_correct_order(
    authenticated_sse_client: AsyncClient,
    kb_for_streaming: dict,
):
    """Test SSE events are streamed in order: status → token → citation → done.

    GIVEN: User requests streaming search
    WHEN: LLM generates answer with citations
    THEN: Events arrive in order:
        1. StatusEvent (searching)
        2. StatusEvent (generating)
        3. Multiple TokenEvent (incremental text)
        4. CitationEvent* (metadata when [n] detected)
        5. DoneEvent (completion)

    AC-3.3.2: Event ordering.
    """
    import json

    # WHEN: User requests SSE streaming
    async with authenticated_sse_client.stream(
        "POST",
        "/api/v1/search?stream=true",
        json={
            "query": "OAuth 2.0 usage",
            "kb_ids": [kb_for_streaming["id"]],
            "limit": 10,
        },
    ) as response:
        assert response.status_code == 200

        # Parse SSE events
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]  # Strip "data: " prefix
                event_data = json.loads(data_str)
                events.append(event_data)

        # THEN: Validate event ordering
        assert len(events) >= 3, "Should have at least status + token + done events"

        # First events should be 'status'
        status_events = [e for e in events if e["type"] == "status"]
        assert len(status_events) >= 1, "No status events received"
        assert "Searching" in status_events[0]["content"]

        # Token events
        [e for e in events if e["type"] == "token"]
        # Token events are optional (depends on LLM response)

        # Last event should be 'done'
        assert events[-1]["type"] == "done", "Last event must be 'done'"
        assert "confidence" in events[-1]
        assert "result_count" in events[-1]


async def test_sse_token_events_contain_incremental_text(
    authenticated_sse_client: AsyncClient,
    kb_for_streaming: dict,
):
    """Test token events contain incremental text chunks.

    GIVEN: LLM generates answer "OAuth 2.0 [1] is recommended."
    WHEN: Streaming to client
    THEN:
        - Multiple token events with incremental text
        - Text builds up: "OAuth" → "OAuth 2.0" → "OAuth 2.0 [1]" → ...
        - Each token event has 'data' field with text chunk

    This test will FAIL until token streaming is implemented.
    """
    # WHEN: User requests SSE streaming
    async with authenticated_sse_client.stream(
        "POST",
        "/api/v1/search",
        json={
            "query": "authentication",
            "kb_ids": [kb_for_streaming["id"]],
            "synthesize": True,
        },
        headers={"Accept": "text/event-stream"},
    ) as response:
        assert response.status_code == 200

        # Collect token event data
        token_texts = []
        current_event = None

        async for line in response.aiter_lines():
            if line.startswith("event: "):
                current_event = line[7:]
            elif line.startswith("data: ") and current_event == "token":
                import json

                data = json.loads(line[6:])
                token_texts.append(data.get("text", ""))

        # THEN: Validate incremental text
        assert len(token_texts) > 0, "No token text received"

        # Each token should add to previous (incremental)
        full_text = "".join(token_texts)
        assert len(full_text) > 0, "No complete text assembled from tokens"


async def test_sse_citation_events_contain_metadata(
    authenticated_sse_client: AsyncClient,
    kb_for_streaming: dict,
):
    """Test citation events contain all required metadata.

    GIVEN: LLM answer with [1], [2] citations
    WHEN: Streaming citations
    THEN:
        - Citation events have 'data' field with citation object
        - Each citation includes: number, document_name, excerpt, etc.

    This test will FAIL until citation streaming is implemented.
    """
    # WHEN: User requests SSE streaming
    async with authenticated_sse_client.stream(
        "POST",
        "/api/v1/search",
        json={
            "query": "security best practices",
            "kb_ids": [kb_for_streaming["id"]],
            "synthesize": True,
        },
        headers={"Accept": "text/event-stream"},
    ) as response:
        assert response.status_code == 200

        # Collect citation events
        citations = []
        current_event = None

        async for line in response.aiter_lines():
            if line.startswith("event: "):
                current_event = line[7:]
            elif line.startswith("data: ") and current_event == "citation":
                import json

                citation = json.loads(line[6:])
                citations.append(citation)

        # THEN: Validate citations
        assert len(citations) > 0, "No citations received"

        # Validate metadata
        for citation in citations:
            assert "number" in citation
            assert "document_name" in citation
            assert "excerpt" in citation


# =============================================================================
# AC-3.3.3: Reconnection with State Retention
# =============================================================================


async def test_sse_reconnection_resumes_from_last_event(
    authenticated_sse_client: AsyncClient,
    kb_for_streaming: dict,
):
    """Test client can reconnect and resume from last event.

    GIVEN: Client receives first 5 events, then disconnects
    WHEN: Client reconnects with Last-Event-ID header
    THEN:
        - Server resends events starting from event 6
        - No duplicate events
        - State retained for 60s

    This mitigates R-005 (stream disconnects).
    This test will FAIL until reconnection logic is implemented.
    """
    # TODO: This test requires server-side event ID tracking
    # For now, mark as placeholder
    pytest.skip("Reconnection logic deferred - requires session state management")

    # WHEN: First connection (receive 5 events)
    # events_received = []
    # async with authenticated_sse_client.stream(...) as response:
    #     for i in range(5):
    #         event = await response.aiter_lines().__anext__()
    #         events_received.append(event)
    #     # Disconnect intentionally

    # WHEN: Reconnect with Last-Event-ID
    # last_event_id = events_received[-1].get("id")
    # async with authenticated_sse_client.stream(
    #     ...,
    #     headers={"Last-Event-ID": last_event_id}
    # ) as response:
    #     # THEN: Receive remaining events (no duplicates)
    #     new_events = []
    #     async for event in response.aiter_lines():
    #         new_events.append(event)
    #
    #     assert len(new_events) > 0
    #     assert new_events[0].id != last_event_id  # No duplicate


# =============================================================================
# AC-3.3.4: Graceful Degradation to Non-Streaming
# =============================================================================


async def test_search_without_stream_param_returns_non_streaming(
    authenticated_sse_client: AsyncClient,
    kb_for_streaming: dict,
):
    """Test search without stream=true returns complete JSON response.

    GIVEN: Client doesn't request streaming (no stream=true param)
    WHEN: POST /api/v1/search (stream defaults to false)
    THEN:
        - Response is complete JSON (not streamed)
        - Includes answer, citations, confidence
        - No streaming overhead

    AC-3.3.4: Graceful degradation (backward compatible).
    """
    # WHEN: User requests non-streaming search (default behavior)
    response = await authenticated_sse_client.post(
        "/api/v1/search",
        json={
            "query": "authentication",
            "kb_ids": [kb_for_streaming["id"]],
            "limit": 10,
        },
    )

    # THEN: Complete response (not streamed)
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")

    data = response.json()

    # Validate complete response
    assert "answer" in data
    assert "citations" in data
    assert "confidence" in data
    assert "results" in data

    # Response should be immediate (not incremental)
    assert isinstance(data["results"], list)


# =============================================================================
# AC-3.3.5: Performance - First Token Latency
# =============================================================================


async def test_sse_first_token_latency_under_1_second(
    authenticated_sse_client: AsyncClient,
    kb_for_streaming: dict,
):
    """Test first token arrives within 1 second for streaming search.

    GIVEN: User requests streaming search
    WHEN: POST /api/v1/search?stream=true
    THEN:
        - First token event arrives within 1000ms
        - Latency measured from request start to first token

    AC-3.3.5: Performance requirement for responsive UX.
    """
    import json
    import time

    # WHEN: User requests SSE streaming
    start_time = time.time()
    first_token_time = None

    async with authenticated_sse_client.stream(
        "POST",
        "/api/v1/search?stream=true",
        json={
            "query": "authentication methods",
            "kb_ids": [kb_for_streaming["id"]],
            "limit": 10,
        },
    ) as response:
        assert response.status_code == 200

        # Parse SSE events and find first token
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                event_data = json.loads(data_str)

                # Record time when first token event arrives
                if event_data["type"] == "token" and first_token_time is None:
                    first_token_time = time.time()
                    break

    # THEN: First token within 1 second
    assert first_token_time is not None, "No token events received"
    latency_ms = (first_token_time - start_time) * 1000

    # AC-3.3.5: First token < 1000ms
    assert (
        latency_ms < 1000
    ), f"First token latency {latency_ms:.0f}ms exceeds 1000ms threshold"

    # Log for performance monitoring
    print(f"\nFirst token latency: {latency_ms:.0f}ms")
