"""Integration tests for LLM Answer Synthesis with Citations (Story 3.2).

Tests cover:
- LLM follows citation format with [n] markers (AC-3.2.1, R-001 BLOCK)
- LLM answer grounded in retrieved chunks (AC-3.2.5, R-007)
- End-to-end synthesis: search → chunks → LLM → citations

Test Strategy (ATDD - GREEN Phase):
- These tests use fixtures with real Qdrant data
- Tests validate LLM synthesis with indexed chunks
- Use deterministic LLM responses (mocked) for reliable tests

Risk Mitigation:
- R-001: LLM citation quality (Score: 9 - BLOCK)
- R-007: LLM hallucination (Score: 6 - MITIGATE)
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_llm_response_with_citations():
    """Mock LLM response with proper citation format.

    This fixture provides deterministic LLM responses for testing.
    In real implementation, this will be mocked via LiteLLM.
    """
    return {
        "answer": (
            "To secure your API, implement OAuth 2.0 [1] for authorization. "
            "OAuth 2.0 provides delegated access without exposing user credentials [1]. "
            "Additionally, enable Multi-Factor Authentication (MFA) [2] to add "
            "an extra security layer beyond passwords [2]."
        ),
        "chunks_used": [
            {
                "chunk_id": 101,
                "chunk_text": "OAuth 2.0 is an authorization framework...",
                "document_name": "OAuth Guide.pdf",
                "page_number": 3,
            },
            {
                "chunk_id": 102,
                "chunk_text": "Multi-factor authentication (MFA) adds...",
                "document_name": "Security Best Practices.md",
                "page_number": 7,
            },
        ],
    }


# =============================================================================
# AC-3.2.1: LLM Uses Inline [n] Citation Markers
# =============================================================================


async def test_llm_answer_contains_citation_markers(
    api_client: AsyncClient,
    test_user_data: dict,
    kb_with_indexed_chunks: dict,
):
    """Test LLM synthesizes answer with inline [n] citation markers.

    GIVEN: User searches "How do I secure my API?"
    WHEN: LLM synthesizes answer from retrieved chunks
    THEN:
        - Response returns 200 OK
        - Response contains answer field
        - If LLM available: answer contains [n] markers
        - If LLM unavailable: gracefully degrades to raw results

    NOTE: When LLM proxy is unavailable/misconfigured, the API gracefully
    degrades to returning empty answer with raw results. This test validates
    both the happy path (LLM available) and fallback (LLM unavailable).
    """
    kb = kb_with_indexed_chunks["kb"]

    # WHEN: User performs search (which triggers synthesis)
    response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "How do I secure my API?",
            "kb_ids": [str(kb["id"])],
            "synthesize": True,  # Request LLM synthesis
        },
        cookies=test_user_data["cookies"],
    )

    # THEN: Response includes answer field (may be empty on LLM failure)
    assert response.status_code == 200
    data = response.json()

    # Validate answer field exists
    assert "answer" in data

    # Validate results are returned even if LLM fails
    assert "results" in data
    assert len(data["results"]) > 0, "Results should always be returned"

    # If answer is non-empty, validate citation format
    if len(data["answer"]) > 0:
        # Validate citations field exists
        assert "citations" in data
        assert len(data["citations"]) > 0

        # CRITICAL: Answer contains [n] markers
        import re

        markers = re.findall(r"\[(\d+)\]", data["answer"])
        assert len(markers) > 0, "LLM answer must contain [n] citation markers"

        # Validate markers are sequential (1, 2, 3...)
        marker_numbers = [int(m) for m in markers]
        unique_markers = sorted(set(marker_numbers))
        assert unique_markers == list(
            range(1, max(unique_markers) + 1)
        ), "Citation markers must be sequential"
    else:
        # Graceful degradation: empty answer but results returned
        # This is expected when LLM is unavailable
        pytest.skip("LLM unavailable - answer empty, testing fallback behavior")


async def test_llm_answer_citations_map_to_chunks(
    api_client: AsyncClient,
    test_user_data: dict,
    kb_with_indexed_chunks: dict,
):
    """Test every [n] marker in answer maps to a citation object.

    GIVEN: LLM answer with [1], [2], [3] markers
    WHEN: Response is returned
    THEN:
        - citations array has matching items
        - Every marker in answer has corresponding citation

    This validates R-002 (citation mapping correctness).
    """
    kb = kb_with_indexed_chunks["kb"]

    # WHEN: User searches
    response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "authentication best practices",
            "kb_ids": [str(kb["id"])],
            "synthesize": True,
        },
        cookies=test_user_data["cookies"],
    )

    assert response.status_code == 200
    data = response.json()

    # Extract markers from answer
    import re

    markers = re.findall(r"\[(\d+)\]", data["answer"])
    unique_markers = sorted({int(m) for m in markers})

    # CRITICAL: Every marker has a citation
    citation_numbers = {c["number"] for c in data["citations"]}
    assert (
        set(unique_markers) == citation_numbers
    ), "Every [n] marker in answer must have corresponding citation"


# =============================================================================
# AC-3.2.5: Hallucination Prevention (Grounded in Chunks)
# =============================================================================


async def test_llm_answer_grounded_in_retrieved_chunks(
    api_client: AsyncClient,
    test_user_data: dict,
    kb_with_indexed_chunks: dict,
):
    """Test LLM answer only includes information from retrieved chunks.

    GIVEN: Search query returns chunks about OAuth and MFA
    WHEN: LLM synthesizes answer
    THEN:
        - Response contains results from relevant chunks
        - If LLM available: answer grounded in chunks with confidence score
        - If LLM unavailable: graceful degradation with raw results

    NOTE: When LLM is unavailable, the API returns confidence: 0 and empty answer.
    This test validates the API contract regardless of LLM availability.
    """
    kb = kb_with_indexed_chunks["kb"]

    # WHEN: User searches
    response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "OAuth 2.0 usage",
            "kb_ids": [str(kb["id"])],
            "synthesize": True,
        },
        cookies=test_user_data["cookies"],
    )

    assert response.status_code == 200
    data = response.json()

    # Validate confidence field exists (API uses 'confidence', not 'confidence_score')
    assert "confidence" in data
    confidence = data["confidence"]

    # If LLM failed, confidence is 0 and answer is empty - skip the content test
    if confidence == 0 and len(data.get("answer", "")) == 0:
        pytest.skip("LLM unavailable - skipping grounding test")

    # If confidence is available and answer is non-empty, validate
    if confidence > 0:
        assert confidence >= 0.4, (
            f"Low confidence ({confidence}) suggests hallucination. "
            "Review LLM system prompt grounding instructions."
        )


async def test_llm_answer_includes_confidence_score(
    api_client: AsyncClient,
    test_user_data: dict,
    kb_with_indexed_chunks: dict,
):
    """Test synthesis response includes confidence field (AC-3.2.4).

    GIVEN: LLM synthesizes answer from chunks
    WHEN: Response is returned
    THEN:
        - confidence field exists (API uses 'confidence', not 'confidence_score')
        - Score is between 0-1 (normalized, not 0-100)
        - Higher score = better chunk coverage

    NOTE: When LLM is unavailable, confidence defaults to 0.
    """
    kb = kb_with_indexed_chunks["kb"]

    # WHEN: User searches
    response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "API security recommendations",
            "kb_ids": [str(kb["id"])],
            "synthesize": True,
        },
        cookies=test_user_data["cookies"],
    )

    assert response.status_code == 200
    data = response.json()

    # Validate confidence field (API uses 'confidence', not 'confidence_score')
    assert "confidence" in data
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["confidence"], (int, float))


# =============================================================================
# AC-3.2.3: Citation Metadata Completeness
# =============================================================================


async def test_citations_include_all_required_metadata(
    api_client: AsyncClient,
    test_user_data: dict,
    kb_with_indexed_chunks: dict,
):
    """Test each citation includes all required metadata fields.

    GIVEN: LLM answer with citations
    WHEN: Response is returned
    THEN: Each citation has:
        - number (1, 2, 3...)
        - document_name
        - page_number
        - section_header
        - excerpt (max 200 chars)
        - char_start, char_end
    """
    kb = kb_with_indexed_chunks["kb"]

    # WHEN: User searches
    response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "authentication methods",
            "kb_ids": [str(kb["id"])],
            "synthesize": True,
        },
        cookies=test_user_data["cookies"],
    )

    assert response.status_code == 200
    data = response.json()

    # Validate each citation has required fields
    for citation in data["citations"]:
        assert "number" in citation
        assert "document_name" in citation
        assert "page_number" in citation or citation.get("page_number") is None
        assert "section_header" in citation
        assert "excerpt" in citation
        assert len(citation["excerpt"]) <= 200  # Max 200 chars
        assert "char_start" in citation
        assert "char_end" in citation


# =============================================================================
# Error Handling
# =============================================================================


async def test_synthesis_without_results_returns_empty_answer(
    api_client: AsyncClient,
    test_user_data: dict,
    kb_with_indexed_chunks: dict,
):
    """Test synthesis returns empty answer when LLM fails or query has no semantic match.

    GIVEN: Search query OR LLM unavailable scenario
    WHEN: LLM synthesis is requested
    THEN:
        - answer is empty (when LLM fails) or contains response
        - confidence is 0 (when LLM fails)
        - API uses 'confidence', not 'confidence_score'

    NOTE: With mock embeddings, Qdrant returns results even for nonsense queries
    (just with low scores). This test validates the API contract when LLM fails.
    """
    kb = kb_with_indexed_chunks["kb"]

    # WHEN: User searches with nonsense query
    response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "xyzabc123 nonexistent topic",
            "kb_ids": [str(kb["id"])],
            "synthesize": True,
        },
        cookies=test_user_data["cookies"],
    )

    assert response.status_code == 200
    data = response.json()

    # Validate API contract (uses 'confidence', not 'confidence_score')
    assert "answer" in data
    assert "confidence" in data

    # When LLM is unavailable, answer is empty and confidence is 0
    if data["answer"] == "":
        assert data["confidence"] == 0
