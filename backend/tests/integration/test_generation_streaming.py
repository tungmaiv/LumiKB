"""Integration tests for Generation Streaming API (Story 4.5).

DEFERRED TO STORY 5.15 - Technical Debt TD-4.5-1
Status: Tests written but skipped due to missing external service mocks
Blocking Issue: Requires LiteLLM mock fixtures from Story 4.1 (TD-4.1-1)

Implementation Status:
✅ SSE streaming endpoint implemented (backend/app/api/v1/generate_stream.py)
✅ GenerationService.generate_document_stream() method implemented
✅ Real LLM token streaming with progressive citation detection
✅ Event schema: status, token, citation, done, error
✅ AbortController cancellation support

Test Coverage Plan:
- P1: SSE connection establishment (Content-Type: text/event-stream)
- P1: Event order validation (status → tokens → citations → done)
- P1: Token streaming in real-time
- P1: Citation events emitted inline as markers appear
- P1: Confidence calculation in done event
- P1: Error event handling (LLM failure, permission denied, insufficient sources)
- P1: Connection cleanup (done event closes stream)
- P2: Permission enforcement (403 for unauthorized KB)
- P2: Chunk retrieval from database

Resolution Plan:
Epic 5, Story 5.15: "Epic 4 ATDD Transition to GREEN"
1. Implement LiteLLM mock fixture (mock_litellm_generate_stream)
2. Remove pytest.mark.skip decorators
3. Transition all tests to GREEN

Reference:
- docs/sprint-artifacts/epic-5-tech-debt.md#TD-4.5-1
- backend/app/api/v1/generate_stream.py - SSE endpoint implementation
"""

import json

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


@pytest.mark.skip(reason="Deferred to Story 5.15 - Missing LiteLLM mocks (TD-4.5-1)")
class TestGenerationStreamingAPI:
    """Test Generation Streaming SSE API endpoints."""

    @pytest.mark.asyncio
    async def test_sse_connection_established(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        mock_litellm_generate_stream,  # TODO: Implement in Story 5.15
    ):
        """
        AC1: SSE connection returns text/event-stream Content-Type.

        GIVEN: User triggers document generation with selected chunks
        WHEN: POST /api/v1/generate/stream is called
        THEN: Response has Content-Type: text/event-stream
        AND: Connection stays open during streaming
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        # Use streaming client
        async with api_client.stream(
            "POST",
            "/api/v1/generate/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "mode": "rfp_response",
                "additional_prompt": "Focus on security features",
                "selected_chunk_ids": ["chunk-1", "chunk-2", "chunk-3"],
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
        mock_litellm_generate_stream,
    ):
        """
        AC1 + AC3: SSE events arrive in correct order with citations.

        GIVEN: User triggers generation
        WHEN: Response streams
        THEN: Events arrive in order: status → token → citation → done
        AND: Citations appear progressively as markers detected
        """
        kb_id = demo_kb_with_indexed_docs["id"]
        events = []

        async with api_client.stream(
            "POST",
            "/api/v1/generate/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "mode": "technical_checklist",
                "additional_prompt": "",
                "selected_chunk_ids": ["chunk-1", "chunk-2"],
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    events.append(data)

        # Verify event sequence
        event_types = [e["type"] for e in events]
        assert event_types[0] == "status"  # Preparing sources
        assert "token" in event_types  # At least one token
        assert "done" in event_types  # Final event
        assert event_types[-1] == "done"  # Done is last

    @pytest.mark.asyncio
    async def test_citation_events_emitted_progressively(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        mock_litellm_generate_stream,
    ):
        """
        AC3: Citation events emitted as markers detected in stream.

        GIVEN: LLM generates text with citation markers [1], [2]
        WHEN: Markers appear in token stream
        THEN: Citation events emitted immediately with full details
        AND: Citation number matches marker [n]
        """
        kb_id = demo_kb_with_indexed_docs["id"]
        citation_events = []

        async with api_client.stream(
            "POST",
            "/api/v1/generate/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "mode": "rfp_response",
                "additional_prompt": "",
                "selected_chunk_ids": ["chunk-1", "chunk-2", "chunk-3"],
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    if event["type"] == "citation":
                        citation_events.append(event)

        # Verify citations emitted
        assert len(citation_events) > 0
        for cit_event in citation_events:
            assert "number" in cit_event
            assert "data" in cit_event
            assert cit_event["data"]["document_name"]
            assert cit_event["data"]["excerpt"]

    @pytest.mark.asyncio
    async def test_done_event_includes_metadata(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        mock_litellm_generate_stream,
    ):
        """
        AC1: Done event includes generation metadata.

        GIVEN: Generation completes successfully
        WHEN: Final done event emitted
        THEN: Includes generation_id, confidence, sources_used
        """
        kb_id = demo_kb_with_indexed_docs["id"]
        done_event = None

        async with api_client.stream(
            "POST",
            "/api/v1/generate/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "mode": "requirements_summary",
                "additional_prompt": "",
                "selected_chunk_ids": ["chunk-1"],
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    if event["type"] == "done":
                        done_event = event

        assert done_event is not None
        assert "generation_id" in done_event
        assert "confidence" in done_event
        assert "sources_used" in done_event
        assert 0.0 <= done_event["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_insufficient_sources_error(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        AC1: Error response when no sources provided.

        GIVEN: Empty selected_chunk_ids list
        WHEN: POST /api/v1/generate/stream called
        THEN: Returns 400 error
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        response = await api_client.post(
            "/api/v1/generate/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "mode": "custom",
                "additional_prompt": "",
                "selected_chunk_ids": [],  # Empty!
            },
        )

        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_permission_enforcement(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        AC1: Permission check enforced.

        GIVEN: User without READ permission on KB
        WHEN: POST /api/v1/generate/stream called
        THEN: Returns 403 error
        """
        # Use a KB the user doesn't have access to
        other_kb_id = "00000000-0000-0000-0000-000000000000"

        response = await api_client.post(
            "/api/v1/generate/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": other_kb_id,
                "mode": "rfp_response",
                "additional_prompt": "",
                "selected_chunk_ids": ["chunk-1"],
            },
        )

        # Should fail permission check
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_invalid_generation_mode(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        AC1: Validation of generation mode.

        GIVEN: Invalid generation mode
        WHEN: POST /api/v1/generate/stream called
        THEN: Returns 400 error
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        response = await api_client.post(
            "/api/v1/generate/stream",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "mode": "invalid_mode",
                "additional_prompt": "",
                "selected_chunk_ids": ["chunk-1"],
            },
        )

        assert response.status_code == 400
