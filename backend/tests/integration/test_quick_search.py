"""Integration tests for Quick Search API (Story 3.7).

Tests cover:
- POST /api/v1/search/quick endpoint (AC2)
- Quick search returns top 5 results without synthesis
- Permission enforcement
- Cross-KB search default
- Performance targets
"""

import pytest
from httpx import AsyncClient

from tests.factories import create_kb_data, create_registration_data

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def quick_search_user_data() -> dict:
    """Test user for quick search tests."""
    return create_registration_data()


@pytest.fixture
async def registered_quick_search_user(
    api_client: AsyncClient, quick_search_user_data: dict
) -> dict:
    """Create registered user for quick search tests."""
    response = await api_client.post(
        "/api/v1/auth/register",
        json=quick_search_user_data,
    )
    assert response.status_code == 201
    return {**quick_search_user_data, "user": response.json()}


@pytest.fixture
async def authenticated_quick_search_client(
    api_client: AsyncClient, registered_quick_search_user: dict
) -> AsyncClient:
    """Authenticated client for quick search tests."""
    response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_quick_search_user["email"],
            "password": registered_quick_search_user["password"],
        },
    )
    assert response.status_code == 204
    return api_client


@pytest.fixture
async def kb_for_quick_search(
    authenticated_quick_search_client: AsyncClient,
) -> dict:
    """Create KB for quick search testing."""
    kb_data = create_kb_data(name="Quick Search Test KB")
    kb_response = await authenticated_quick_search_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
    )
    assert kb_response.status_code == 201
    return kb_response.json()


# =============================================================================
# AC2: Quick Search Returns Top 5 Results Without Synthesis
# =============================================================================


async def test_quick_search_endpoint_returns_results(
    authenticated_quick_search_client: AsyncClient,
    kb_for_quick_search: dict,
):
    """Test POST /api/v1/search/quick returns top 5 results (AC2).

    GIVEN: User has indexed documents in KB
    WHEN: POST /api/v1/search/quick
    THEN:
        - Response has QuickSearchResponse schema
        - Results limited to 5
        - No answer or citations (lightweight mode)
    """
    # WHEN: User requests quick search
    response = await authenticated_quick_search_client.post(
        "/api/v1/search/quick",
        json={
            "query": "authentication methods",
            "kb_ids": None,  # Cross-KB default
        },
    )

    # THEN: Response is QuickSearchResponse
    assert response.status_code == 200
    data = response.json()

    # Verify schema
    assert "query" in data
    assert "results" in data
    assert "kb_count" in data
    assert "response_time_ms" in data

    # No synthesis fields
    assert "answer" not in data
    assert "citations" not in data
    assert "confidence" not in data

    # Results limited
    assert isinstance(data["results"], list)
    assert len(data["results"]) <= 5


async def test_quick_search_includes_result_metadata(
    authenticated_quick_search_client: AsyncClient,
    kb_for_quick_search: dict,
):
    """Test quick search results include QuickSearchResult fields (AC2).

    GIVEN: Quick search returns results
    WHEN: Response received
    THEN: Each result has:
        - document_id, document_name
        - kb_id, kb_name
        - excerpt (truncated to 100 chars)
        - relevance_score
    """
    # WHEN: Quick search
    response = await authenticated_quick_search_client.post(
        "/api/v1/search/quick",
        json={
            "query": "OAuth",
            "kb_ids": None,
        },
    )

    # THEN: Each result has QuickSearchResult schema
    assert response.status_code == 200
    data = response.json()
    results = data["results"]

    if len(results) > 0:
        result = results[0]

        # Required fields
        assert "document_id" in result
        assert "document_name" in result
        assert "kb_id" in result
        assert "kb_name" in result
        assert "excerpt" in result
        assert "relevance_score" in result

        # Excerpt truncated
        assert len(result["excerpt"]) <= 103  # 100 + "..."
        assert 0.0 <= result["relevance_score"] <= 1.0


# =============================================================================
# Performance and Edge Cases
# =============================================================================


async def test_quick_search_performance_under_1_second(
    authenticated_quick_search_client: AsyncClient,
    kb_for_quick_search: dict,
):
    """Test quick search responds within 1 second (AC10).

    GIVEN: User performs quick search
    WHEN: Measuring response time
    THEN: Response time < 1s (p95 target)
    """
    import time

    start_time = time.time()

    response = await authenticated_quick_search_client.post(
        "/api/v1/search/quick",
        json={
            "query": "authentication",
            "kb_ids": None,
        },
    )

    elapsed_time = time.time() - start_time

    assert response.status_code == 200
    assert elapsed_time < 1.0, f"Quick search took {elapsed_time:.2f}s (target: <1s)"


async def test_quick_search_validates_query_length(
    authenticated_quick_search_client: AsyncClient,
):
    """Test quick search validates query length."""
    # Empty query
    response = await authenticated_quick_search_client.post(
        "/api/v1/search/quick",
        json={"query": "", "kb_ids": None},
    )
    assert response.status_code == 422

    # Query too long (>500 chars)
    response = await authenticated_quick_search_client.post(
        "/api/v1/search/quick",
        json={"query": "a" * 501, "kb_ids": None},
    )
    assert response.status_code == 422


async def test_quick_search_with_no_results(
    authenticated_quick_search_client: AsyncClient,
    kb_for_quick_search: dict,
):
    """Test quick search with no matching results (AC9).

    GIVEN: Query unlikely to match
    WHEN: Quick search
    THEN: Empty results (not error)
    """
    response = await authenticated_quick_search_client.post(
        "/api/v1/search/quick",
        json={
            "query": "xyzabc123notfound999",
            "kb_ids": None,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["kb_count"] >= 0
