"""Integration tests for Cross-KB Search (Story 3.6).

Tests cover:
- Cross-KB search queries all permitted KBs (AC-3.6.1)
- Results merged and ranked by relevance (AC-3.6.2)
- Each result shows source KB name (AC-3.6.3)
- Performance within acceptable limits (AC-3.6.4)

Test Strategy (ATDD - RED Phase):
- These tests are EXPECTED TO FAIL until cross-KB search is implemented
- They define the acceptance criteria for multi-KB querying
- Follow RED → GREEN → REFACTOR TDD cycle

Risk Mitigation:
- R-003: Cross-KB search performance (validates parallel queries)
- R-006: Permission bypass (validates cross-tenant isolation)
"""

import pytest
from httpx import AsyncClient

from tests.factories import create_kb_data, create_registration_data

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def cross_kb_user_data() -> dict:
    """Test user for cross-KB search tests."""
    return create_registration_data()


@pytest.fixture
async def registered_cross_kb_user(
    api_client: AsyncClient, cross_kb_user_data: dict
) -> dict:
    """Create registered user for cross-KB tests."""
    response = await api_client.post(
        "/api/v1/auth/register",
        json=cross_kb_user_data,
    )
    assert response.status_code == 201
    return {**cross_kb_user_data, "user": response.json()}


@pytest.fixture
async def authenticated_cross_kb_client(
    api_client: AsyncClient, registered_cross_kb_user: dict
) -> AsyncClient:
    """Authenticated client for cross-KB tests."""
    response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_cross_kb_user["email"],
            "password": registered_cross_kb_user["password"],
        },
    )
    assert response.status_code == 204
    return api_client


@pytest.fixture
async def multiple_kbs(authenticated_cross_kb_client: AsyncClient) -> list[dict]:
    """Create 3 KBs for cross-KB search testing.

    Returns:
        List of KB dicts with structure:
        [
            {"id": "kb1_id", "name": "Sales KB", ...},
            {"id": "kb2_id", "name": "Engineering KB", ...},
            {"id": "kb3_id", "name": "Security KB", ...}
        ]
    """
    kbs = []

    # Create KB1: Sales KB
    kb1_data = create_kb_data(name="Sales Knowledge Base")
    kb1_response = await authenticated_cross_kb_client.post(
        "/api/v1/knowledge-bases/",
        json=kb1_data,
    )
    assert kb1_response.status_code == 201
    kbs.append(kb1_response.json())

    # Create KB2: Engineering KB
    kb2_data = create_kb_data(name="Engineering Knowledge Base")
    kb2_response = await authenticated_cross_kb_client.post(
        "/api/v1/knowledge-bases/",
        json=kb2_data,
    )
    assert kb2_response.status_code == 201
    kbs.append(kb2_response.json())

    # Create KB3: Security KB
    kb3_data = create_kb_data(name="Security Knowledge Base")
    kb3_response = await authenticated_cross_kb_client.post(
        "/api/v1/knowledge-bases/",
        json=kb3_data,
    )
    assert kb3_response.status_code == 201
    kbs.append(kb3_response.json())

    return kbs


# =============================================================================
# AC-3.6.1: Cross-KB Search Queries All Permitted KBs
# =============================================================================


async def test_cross_kb_search_queries_all_permitted_kbs(
    authenticated_cross_kb_client: AsyncClient,
    multiple_kbs: list[dict],
):
    """Test search with kb_ids=None queries all user's KBs.

    GIVEN: User has 3 KBs (all owned = all permitted)
    WHEN: POST /api/v1/search with kb_ids=None (or omitted)
    THEN:
        - Search queries all 3 KBs in parallel
        - Results include chunks from all KBs
        - Each result indicates source KB

    This test will FAIL until cross-KB search is implemented.
    """
    # WHEN: User searches without specifying kb_ids (default = all)
    response = await authenticated_cross_kb_client.post(
        "/api/v1/search",
        json={
            "query": "best practices",
            # kb_ids: None (default - search all permitted KBs)
            "synthesize": False,  # Just return chunks for this test
        },
    )

    # THEN: Response includes results from all KBs
    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    results = data["results"]

    # Should have results from multiple KBs
    kb_ids_in_results = {r["kb_id"] for r in results}

    # At least 2 KBs should have results (realistic for test data)
    # (We can't guarantee all 3 KBs have relevant docs for "best practices")
    assert len(kb_ids_in_results) >= 2, "Results should span multiple KBs"

    # Verify all results are from permitted KBs
    permitted_kb_ids = {kb["id"] for kb in multiple_kbs}
    assert kb_ids_in_results.issubset(
        permitted_kb_ids
    ), "Results should only come from permitted KBs"


async def test_cross_kb_search_respects_permissions(
    authenticated_cross_kb_client: AsyncClient,
    api_client: AsyncClient,
    multiple_kbs: list[dict],
):
    """Test cross-KB search only queries KBs user has READ access to.

    GIVEN: User A has KB1, KB2
          User B has KB3
    WHEN: User A searches with kb_ids=None
    THEN:
        - Results include KB1, KB2 only
        - Results do NOT include KB3 (not permitted)

    This mitigates R-006 (permission bypass).
    This test will FAIL until permission filtering is implemented.
    """
    # Create second user (User B)
    user_b_data = create_registration_data()
    await api_client.post("/api/v1/auth/register", json=user_b_data)

    user_b_login = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": user_b_data["email"],
            "password": user_b_data["password"],
        },
    )
    assert user_b_login.status_code == 204

    # User B creates their own KB (KB4)
    kb4_data = create_kb_data(name="User B Private KB")
    kb4_response = await api_client.post(
        "/api/v1/knowledge-bases/",
        json=kb4_data,
    )
    assert kb4_response.status_code == 201
    user_b_kb = kb4_response.json()

    # WHEN: User A searches with kb_ids=None (default)
    response = await authenticated_cross_kb_client.post(
        "/api/v1/search",
        json={
            "query": "security",
            "synthesize": False,
        },
    )

    # THEN: Results do NOT include User B's KB
    assert response.status_code == 200
    data = response.json()
    results = data["results"]

    kb_ids_in_results = {r["kb_id"] for r in results}

    # CRITICAL: User B's KB should NOT appear
    assert (
        user_b_kb["id"] not in kb_ids_in_results
    ), "Cross-KB search must NOT return unpermitted KBs"


# =============================================================================
# AC-3.6.2: Results Merged and Ranked by Relevance
# =============================================================================


async def test_cross_kb_results_ranked_by_relevance(
    authenticated_cross_kb_client: AsyncClient,
    multiple_kbs: list[dict],
):
    """Test results from multiple KBs are merged and ranked by score.

    GIVEN: KB1 has result with score=0.85
           KB2 has result with score=0.92
           KB3 has result with score=0.78
    WHEN: Cross-KB search
    THEN: Results ordered [KB2_result, KB1_result, KB3_result]

    This test will FAIL until ranking logic is implemented.
    """
    # WHEN: Cross-KB search
    response = await authenticated_cross_kb_client.post(
        "/api/v1/search",
        json={
            "query": "authentication methods",
            "limit": 10,
            "synthesize": False,
        },
    )

    # THEN: Results ranked by relevance_score (descending)
    assert response.status_code == 200
    data = response.json()
    results = data["results"]

    # Extract relevance scores
    scores = [r["relevance_score"] for r in results]

    # Verify descending order
    assert scores == sorted(
        scores, reverse=True
    ), "Results must be ranked by relevance_score descending"

    # Verify scores are in valid range [0, 1]
    for score in scores:
        assert 0 <= score <= 1, f"Invalid relevance_score: {score}"


async def test_cross_kb_search_merges_results_with_limit(
    authenticated_cross_kb_client: AsyncClient,
    multiple_kbs: list[dict],
):
    """Test cross-KB search respects limit across all KBs.

    GIVEN: User requests limit=5
           KB1 has 10 results, KB2 has 8 results, KB3 has 6 results
    WHEN: Cross-KB search with limit=5
    THEN:
        - Total results returned = 5 (not 15)
        - Top 5 results by score across all KBs

    This test will FAIL until result merging is implemented.
    """
    # WHEN: Cross-KB search with limit
    response = await authenticated_cross_kb_client.post(
        "/api/v1/search",
        json={
            "query": "OAuth 2.0",
            "limit": 5,
            "synthesize": False,
        },
    )

    # THEN: Total results = limit (not limit * num_kbs)
    assert response.status_code == 200
    data = response.json()
    results = data["results"]

    assert len(results) <= 5, "Result count must respect limit parameter"

    # Results should be top-5 by score (already tested in previous test)


# =============================================================================
# AC-3.6.3: Each Result Shows Source KB Name
# =============================================================================


async def test_cross_kb_results_include_kb_name(
    authenticated_cross_kb_client: AsyncClient,
    multiple_kbs: list[dict],
):
    """Test each result includes source KB metadata.

    GIVEN: Cross-KB search returns results
    WHEN: Response received
    THEN: Each result has:
        - kb_id: str (KB identifier)
        - kb_name: str (KB display name)

    This test will FAIL until KB metadata is added to results.
    """
    # WHEN: Cross-KB search
    response = await authenticated_cross_kb_client.post(
        "/api/v1/search",
        json={
            "query": "best practices",
            "synthesize": False,
        },
    )

    # THEN: Each result includes KB metadata
    assert response.status_code == 200
    data = response.json()
    results = data["results"]

    assert len(results) > 0, "Should have at least 1 result for this test"

    for result in results:
        # Each result must have kb_id and kb_name
        assert "kb_id" in result, "Result missing kb_id field"
        assert "kb_name" in result, "Result missing kb_name field"

        # Verify kb_name is one of our created KBs
        kb_names_expected = {kb["name"] for kb in multiple_kbs}
        assert (
            result["kb_name"] in kb_names_expected
        ), f"Unexpected kb_name: {result['kb_name']}"


# =============================================================================
# AC-3.6.4: Performance Within Acceptable Limits
# =============================================================================


async def test_cross_kb_search_performance_basic_timing(
    authenticated_cross_kb_client: AsyncClient,
    multiple_kbs: list[dict],
):
    """Test cross-KB search performance (smoke test).

    GIVEN: User has 3 KBs with indexed documents
    WHEN: Cross-KB search
    THEN: Response time < 5s (generous for integration test)

    NOTE: Full p95 < 3s validation is manual/load test (Epic 5).
    This is a basic smoke test to catch obvious performance issues.

    This test will FAIL if cross-KB search is inefficient.
    """
    import time

    # WHEN: Cross-KB search with timing
    start_time = time.time()

    response = await authenticated_cross_kb_client.post(
        "/api/v1/search",
        json={
            "query": "authentication security",
            "limit": 10,
            "synthesize": False,  # No LLM synthesis for perf test
        },
    )

    elapsed_time = time.time() - start_time

    # THEN: Response within acceptable time
    assert response.status_code == 200

    # Generous 5s limit for integration test (production p95 target is 3s)
    assert elapsed_time < 5.0, f"Cross-KB search took {elapsed_time:.2f}s (limit: 5s)"


async def test_cross_kb_search_uses_parallel_queries(
    authenticated_cross_kb_client: AsyncClient,
    multiple_kbs: list[dict],
):
    """Test cross-KB search queries KBs in parallel (not sequential).

    GIVEN: User has 3 KBs
    WHEN: Cross-KB search
    THEN:
        - Queries run in parallel (concurrent)
        - Total time ≈ single KB query time (not 3x)

    This mitigates R-003 (performance risk).
    This test will FAIL if queries are sequential.
    """
    import time

    # Baseline: Query single KB
    single_kb_start = time.time()
    single_response = await authenticated_cross_kb_client.post(
        "/api/v1/search",
        json={
            "query": "OAuth",
            "kb_ids": [multiple_kbs[0]["id"]],  # Single KB
            "limit": 10,
            "synthesize": False,
        },
    )
    single_kb_time = time.time() - single_kb_start

    assert single_response.status_code == 200

    # Cross-KB: Query all 3 KBs
    cross_kb_start = time.time()
    cross_response = await authenticated_cross_kb_client.post(
        "/api/v1/search",
        json={
            "query": "OAuth",
            # kb_ids=None (all KBs)
            "limit": 10,
            "synthesize": False,
        },
    )
    cross_kb_time = time.time() - cross_kb_start

    assert cross_response.status_code == 200

    # CRITICAL: Cross-KB time should NOT be 3x single KB time
    # Allow 2x margin (parallel overhead + merging)
    max_acceptable_time = single_kb_time * 2

    assert (
        cross_kb_time < max_acceptable_time
    ), f"Cross-KB ({cross_kb_time:.2f}s) should be parallel, not 3x single KB ({single_kb_time:.2f}s)"


# =============================================================================
# Additional Edge Case Tests
# =============================================================================


async def test_cross_kb_search_with_no_results(
    authenticated_cross_kb_client: AsyncClient,
    multiple_kbs: list[dict],
):
    """Test cross-KB search when no KBs have matching results.

    GIVEN: Query unlikely to match any documents
    WHEN: Cross-KB search
    THEN:
        - Response status 200 (not error)
        - Empty results array
        - Appropriate message (optional)
    """
    # WHEN: Search with nonsensical query
    response = await authenticated_cross_kb_client.post(
        "/api/v1/search",
        json={
            "query": "xyzabc123notfoundquery999",
            "synthesize": False,
        },
    )

    # THEN: Empty results (not error)
    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert len(data["results"]) == 0


async def test_cross_kb_search_with_explicit_kb_ids(
    authenticated_cross_kb_client: AsyncClient,
    multiple_kbs: list[dict],
):
    """Test user can specify subset of KBs explicitly.

    GIVEN: User has KB1, KB2, KB3
    WHEN: Search with kb_ids=[KB1, KB3] (explicit subset)
    THEN:
        - Results from KB1 and KB3 only
        - Results do NOT include KB2

    This allows filtering after default cross-KB search.
    """
    # WHEN: Search with explicit KB subset
    response = await authenticated_cross_kb_client.post(
        "/api/v1/search",
        json={
            "query": "security",
            "kb_ids": [multiple_kbs[0]["id"], multiple_kbs[2]["id"]],  # KB1, KB3 only
            "synthesize": False,
        },
    )

    # THEN: Results only from specified KBs
    assert response.status_code == 200
    data = response.json()
    results = data["results"]

    if len(results) > 0:
        kb_ids_in_results = {r["kb_id"] for r in results}

        # Should only have KB1 and/or KB3
        allowed_kb_ids = {multiple_kbs[0]["id"], multiple_kbs[2]["id"]}
        assert kb_ids_in_results.issubset(
            allowed_kb_ids
        ), "Results should only come from specified KBs"

        # Should NOT have KB2
        assert multiple_kbs[1]["id"] not in kb_ids_in_results
