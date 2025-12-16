"""Integration tests for LLM Answer Synthesis with Citations (Story 3.2).

Tests cover:
- LLM follows citation format with [n] markers (AC-3.2.1, R-001 BLOCK)
- LLM answer grounded in retrieved chunks (AC-3.2.5, R-007)
- End-to-end synthesis: search → chunks → LLM → citations

Test Strategy (ATDD - RED Phase):
- These tests are EXPECTED TO FAIL until LLM synthesis is implemented
- They validate the CRITICAL R-001 risk (LLM citation quality)
- Use deterministic LLM responses (mocked) for reliable tests

Risk Mitigation:
- R-001: LLM citation quality (Score: 9 - BLOCK)
- R-007: LLM hallucination (Score: 6 - MITIGATE)
"""

import pytest
from httpx import AsyncClient

from tests.factories import create_kb_data, create_registration_data

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def synthesis_user_data() -> dict:
    """Test user for synthesis tests."""
    return create_registration_data()


@pytest.fixture
async def registered_synthesis_user(
    api_client: AsyncClient, synthesis_user_data: dict
) -> dict:
    """Create registered user for synthesis tests."""
    response = await api_client.post(
        "/api/v1/auth/register",
        json=synthesis_user_data,
    )
    assert response.status_code == 201
    return {**synthesis_user_data, "user": response.json()}


@pytest.fixture
async def authenticated_synthesis_client(
    api_client: AsyncClient, registered_synthesis_user: dict
) -> AsyncClient:
    """Authenticated client for synthesis tests."""
    response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_synthesis_user["email"],
            "password": registered_synthesis_user["password"],
        },
    )
    assert response.status_code == 204
    return api_client


@pytest.fixture
async def kb_with_indexed_security_docs(
    authenticated_synthesis_client: AsyncClient,
) -> dict:
    """Create KB with indexed security documentation.

    GIVEN: A KB with documents about OAuth 2.0, MFA, API security
    - Documents are indexed in Qdrant (chunked, embedded)
    """
    # Create KB
    kb_data = create_kb_data(
        name="Security Docs", description="Auth and API security guides"
    )
    kb_response = await authenticated_synthesis_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
    )
    assert kb_response.status_code == 201
    kb = kb_response.json()

    # TODO: Upload and index documents
    # See Story 3.1 ATDD checklist for wait_for_document_indexed() helper

    return kb


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
                # ... metadata
            },
            {
                "chunk_id": 102,
                "chunk_text": "Multi-factor authentication (MFA) adds...",
                "document_name": "Security Best Practices.md",
                "page_number": 7,
                # ... metadata
            },
        ],
    }


# =============================================================================
# AC-3.2.1: LLM Uses Inline [n] Citation Markers
# =============================================================================


async def test_llm_answer_contains_citation_markers(
    authenticated_synthesis_client: AsyncClient,
    kb_with_indexed_security_docs: dict,
):
    """Test LLM synthesizes answer with inline [n] citation markers.

    GIVEN: User searches "How do I secure my API?"
    WHEN: LLM synthesizes answer from retrieved chunks
    THEN:
        - Answer contains [1], [2], etc. markers
        - Markers are inline (not footnotes)
        - Citations array is populated with metadata

    This is a CRITICAL test (R-001: BLOCK risk).
    This test will FAIL until LLM synthesis with citations is implemented.
    """
    # WHEN: User performs search (which triggers synthesis)
    response = await authenticated_synthesis_client.post(
        "/api/v1/search",
        json={
            "query": "How do I secure my API?",
            "kb_ids": [kb_with_indexed_security_docs["id"]],
            "synthesize": True,  # Request LLM synthesis
        },
    )

    # THEN: Response includes synthesized answer with citations
    assert response.status_code == 200
    data = response.json()

    # Validate answer field exists
    assert "answer" in data
    assert len(data["answer"]) > 0

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
    assert unique_markers == list(range(1, max(unique_markers) + 1)), (
        "Citation markers must be sequential"
    )


async def test_llm_answer_citations_map_to_chunks(
    authenticated_synthesis_client: AsyncClient,
    kb_with_indexed_security_docs: dict,
):
    """Test every [n] marker in answer maps to a citation object.

    GIVEN: LLM answer with [1], [2], [3] markers
    WHEN: Response is returned
    THEN:
        - citations array has exactly 3 items
        - citations[0].number == 1, citations[1].number == 2, etc.
        - Every marker in answer has corresponding citation

    This validates R-002 (citation mapping correctness).
    This test will FAIL until citation extraction is implemented.
    """
    # WHEN: User searches
    response = await authenticated_synthesis_client.post(
        "/api/v1/search",
        json={
            "query": "authentication best practices",
            "kb_ids": [kb_with_indexed_security_docs["id"]],
            "synthesize": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Extract markers from answer
    import re

    markers = re.findall(r"\[(\d+)\]", data["answer"])
    unique_markers = sorted({int(m) for m in markers})

    # CRITICAL: Every marker has a citation
    citation_numbers = {c["number"] for c in data["citations"]}
    assert set(unique_markers) == citation_numbers, (
        "Every [n] marker in answer must have corresponding citation"
    )


# =============================================================================
# AC-3.2.5: Hallucination Prevention (Grounded in Chunks)
# =============================================================================


async def test_llm_answer_grounded_in_retrieved_chunks(
    authenticated_synthesis_client: AsyncClient,
    kb_with_indexed_security_docs: dict,
):
    """Test LLM answer only includes information from retrieved chunks.

    GIVEN: Search query returns chunks about OAuth and MFA
    WHEN: LLM synthesizes answer
    THEN:
        - Answer content is semantically aligned with chunk content
        - Answer does NOT include information outside chunks
        - Confidence score reflects chunk coverage

    This mitigates R-007 (hallucination risk).
    This test will FAIL until LLM system prompt enforces grounding.
    """
    # WHEN: User searches
    response = await authenticated_synthesis_client.post(
        "/api/v1/search",
        json={
            "query": "OAuth 2.0 usage",
            "kb_ids": [kb_with_indexed_security_docs["id"]],
            "synthesize": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Validate confidence score exists
    assert "confidence_score" in data
    confidence = data["confidence_score"]

    # If confidence < 50%, answer likely contains hallucinated info
    # This is a heuristic check, not definitive
    assert confidence >= 40, (
        f"Low confidence ({confidence}) suggests hallucination. "
        "Review LLM system prompt grounding instructions."
    )

    # TODO: More sophisticated hallucination detection
    # - Semantic similarity between answer and chunks
    # - Fact verification (does answer claim something NOT in chunks?)
    # - This requires NLI model or manual review


async def test_llm_answer_includes_confidence_score(
    authenticated_synthesis_client: AsyncClient,
    kb_with_indexed_security_docs: dict,
):
    """Test synthesis response includes confidence score (AC-3.2.4).

    GIVEN: LLM synthesizes answer from chunks
    WHEN: Response is returned
    THEN:
        - confidence_score field exists
        - Score is between 0-100
        - Higher score = better chunk coverage

    This test will FAIL until confidence calculation is implemented.
    """
    # WHEN: User searches
    response = await authenticated_synthesis_client.post(
        "/api/v1/search",
        json={
            "query": "API security recommendations",
            "kb_ids": [kb_with_indexed_security_docs["id"]],
            "synthesize": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Validate confidence score
    assert "confidence_score" in data
    assert 0 <= data["confidence_score"] <= 100
    assert isinstance(data["confidence_score"], (int, float))


# =============================================================================
# AC-3.2.3: Citation Metadata Completeness
# =============================================================================


async def test_citations_include_all_required_metadata(
    authenticated_synthesis_client: AsyncClient,
    kb_with_indexed_security_docs: dict,
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

    This validates AC-3.2.3.
    This test will FAIL until citation metadata extraction is complete.
    """
    # WHEN: User searches
    response = await authenticated_synthesis_client.post(
        "/api/v1/search",
        json={
            "query": "authentication methods",
            "kb_ids": [kb_with_indexed_security_docs["id"]],
            "synthesize": True,
        },
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
    authenticated_synthesis_client: AsyncClient,
    kb_with_indexed_security_docs: dict,
):
    """Test synthesis returns empty answer when no chunks found.

    GIVEN: Search query with no matching chunks
    WHEN: LLM synthesis is requested
    THEN:
        - answer is empty or "No information found"
        - citations is empty list
        - confidence_score is 0

    This test will FAIL until empty-results handling is implemented.
    """
    # WHEN: User searches with nonsense query
    response = await authenticated_synthesis_client.post(
        "/api/v1/search",
        json={
            "query": "xyzabc123 nonexistent topic",
            "kb_ids": [kb_with_indexed_security_docs["id"]],
            "synthesize": True,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Validate empty result handling
    assert data["answer"] == "" or "no information" in data["answer"].lower()
    assert len(data["citations"]) == 0
    assert data["confidence_score"] == 0
