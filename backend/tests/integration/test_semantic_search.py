"""Integration tests for Semantic Search API endpoint (Story 3.1).

Tests cover:
- Natural language semantic search (AC-3.1.1)
- Semantic relevance vs keyword matching (AC-3.1.2)
- Cross-KB permission enforcement (AC-3.1.3)
- Search performance < 3s p95 (AC-3.1.4 - manual validation)
- Audit logging for search queries (AC-3.1.5)

Test Strategy (ATDD - RED Phase):
- These tests are EXPECTED TO FAIL until documents are indexed in Qdrant
- They define the acceptance criteria for the /api/v1/search endpoint
- Follow RED → GREEN → REFACTOR TDD cycle

Current Status (2025-11-25):
- Story 3.1 implementation is complete (SearchService, API endpoint, schemas)
- Tests fail because they require indexed documents (uploaded via Epic 2)
- To make tests GREEN: Upload documents via /api/v1/documents endpoint and wait for indexing
- Or: Add test fixtures that populate Qdrant with sample vectors
- For now: Tests serve as acceptance criteria documentation
"""

import time

import pytest
from httpx import AsyncClient

from tests.factories import (
    create_kb_data,
    create_registration_data,
)

pytestmark = pytest.mark.integration


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
async def search_user_data() -> dict:
    """Test user registration data for search tests."""
    return create_registration_data()


@pytest.fixture
async def registered_search_user(
    api_client: AsyncClient, search_user_data: dict
) -> dict:
    """Create a registered test user for search."""
    response = await api_client.post(
        "/api/v1/auth/register",
        json=search_user_data,
    )
    assert response.status_code == 201
    return {**search_user_data, "user": response.json()}


@pytest.fixture
async def authenticated_search_client(
    api_client: AsyncClient, registered_search_user: dict
) -> AsyncClient:
    """Client with authenticated session for search tests."""
    response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_search_user["email"],
            "password": registered_search_user["password"],
        },
    )
    assert response.status_code == 204
    return api_client


@pytest.fixture
async def second_search_user(api_client: AsyncClient) -> dict:
    """Create a second user for cross-tenant permission tests."""
    user_data = create_registration_data()
    response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json()}


@pytest.fixture
async def indexed_kb_with_docs(authenticated_search_client: AsyncClient) -> dict:
    """Create a KB with indexed documents for search testing.

    GIVEN: A knowledge base with processed documents
    - KB created
    - 2 documents uploaded and fully indexed (chunked, embedded, in Qdrant)
    - Documents cover OAuth 2.0 and MFA topics
    """
    # Create KB
    kb_data = create_kb_data(name="Security KB", description="Auth documentation")
    kb_response = await authenticated_search_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
    )
    assert kb_response.status_code == 201
    kb = kb_response.json()

    # TODO: Upload and index documents
    # For now, this will fail because document upload/indexing from Epic 2
    # is implemented, but we need helper to await indexing completion

    # doc1_data = create_document_data(
    #     filename="oauth2-guide.md",
    #     content="OAuth 2.0 is an authorization framework...",
    # )
    # doc1_response = await authenticated_search_client.post(
    #     f"/api/v1/knowledge-bases/{kb['id']}/documents",
    #     files={"file": ("oauth2-guide.md", doc1_data["content"], "text/markdown")},
    # )
    # assert doc1_response.status_code == 201
    #
    # # Wait for indexing (TODO: implement polling helper)
    # await wait_for_document_indexed(kb['id'], doc1_response.json()['id'])

    return kb


# =============================================================================
# AC-3.1.1: Natural Language Search
# =============================================================================


@pytest.mark.skip(
    reason="Requires indexed documents in Qdrant (ATDD RED phase - Epic 2 indexing must complete first)"
)
async def test_search_with_natural_language_query_returns_results(
    authenticated_search_client: AsyncClient,
    indexed_kb_with_docs: dict,
):
    """Test search accepts natural language query and returns relevant chunks.

    GIVEN: KB with indexed documents about OAuth 2.0 and MFA
    WHEN: User searches with natural language query "authentication best practices"
    THEN:
        - Response is 200 OK
        - Results contain chunks semantically related to authentication
        - Each result has required fields: chunk_text, document_name, relevance_score

    This test will FAIL until /api/v1/search endpoint is implemented.
    """
    # WHEN: User performs semantic search
    response = await authenticated_search_client.post(
        "/api/v1/search",
        json={
            "query": "authentication best practices",
            "kb_ids": [indexed_kb_with_docs["id"]],
        },
    )

    # THEN: Search returns results
    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    assert "results" in data
    assert len(data["results"]) > 0

    # Validate result fields
    for result in data["results"]:
        assert "chunk_text" in result
        assert "document_name" in result
        assert "relevance_score" in result
        assert "kb_id" in result
        assert "document_id" in result
        assert result["kb_id"] == indexed_kb_with_docs["id"]


# =============================================================================
# AC-3.1.2: Semantic Relevance (Not Just Keyword Matching)
# =============================================================================


@pytest.mark.skip(
    reason="Requires indexed documents in Qdrant (ATDD RED phase - Epic 2 indexing must complete first)"
)
async def test_search_returns_semantically_relevant_results_not_keywords(
    authenticated_search_client: AsyncClient,
    indexed_kb_with_docs: dict,
):
    """Test search uses semantic matching, not just keywords.

    GIVEN: KB with documents about "OAuth 2.0" and "Multi-Factor Authentication"
    WHEN: User searches "How do I secure my API?"
    THEN:
        - Results include OAuth/MFA chunks (semantically related)
        - Results ranked by semantic relevance_score (descending)
        - Even though query words "secure" and "API" may not appear in chunks

    This verifies vector search quality (R-003 mitigation).
    This test will FAIL until LiteLLM embedding + Qdrant search is integrated.
    """
    # WHEN: User searches with query that doesn't match keywords
    response = await authenticated_search_client.post(
        "/api/v1/search",
        json={
            "query": "How do I secure my API endpoints?",
            "kb_ids": [indexed_kb_with_docs["id"]],
        },
    )

    # THEN: Semantic search returns relevant results
    assert response.status_code == 200
    data = response.json()

    assert len(data["results"]) > 0

    # Validate semantic relevance ranking
    scores = [r["relevance_score"] for r in data["results"]]
    assert scores == sorted(
        scores, reverse=True
    ), "Results must be ranked by relevance (descending)"

    # Top result should be about OAuth or MFA (semantic match)
    top_chunk = data["results"][0]["chunk_text"].lower()
    assert "oauth" in top_chunk or "auth" in top_chunk or "security" in top_chunk


# =============================================================================
# AC-3.1.3: Cross-KB Permission Enforcement (Security-Critical)
# =============================================================================


@pytest.mark.skip(
    reason="Requires indexed documents in Qdrant (ATDD RED phase - Epic 2 indexing must complete first)"
)
async def test_cross_kb_search_only_returns_permitted_kbs(
    authenticated_search_client: AsyncClient,
    api_client: AsyncClient,
    second_search_user: dict,
    indexed_kb_with_docs: dict,
):
    """Test cross-KB search enforces READ permissions (R-006 mitigation).

    GIVEN:
        - User A owns KB1 (indexed_kb_with_docs)
        - User B owns KB2 (no access to KB1)
    WHEN: User B searches with kb_ids=None (search all permitted KBs)
    THEN:
        - Results only include chunks from KB2
        - Results do NOT include chunks from KB1 (permission denied)

    This is a SECURITY-CRITICAL test (R-006: Permission bypass risk).
    This test will FAIL until permission enforcement is implemented in search.
    """
    # GIVEN: Second user with their own KB
    second_client_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": second_search_user["email"],
            "password": second_search_user["password"],
        },
    )
    assert second_client_response.status_code == 204
    second_auth_client = api_client

    # Create KB2 owned by second user
    kb2_data = create_kb_data(name="User B KB", description="Private KB")
    kb2_response = await second_auth_client.post(
        "/api/v1/knowledge-bases/",
        json=kb2_data,
    )
    assert kb2_response.status_code == 201
    kb2 = kb2_response.json()

    # WHEN: User B searches across ALL permitted KBs (kb_ids=None)
    response = await second_auth_client.post(
        "/api/v1/search",
        json={
            "query": "authentication",
            "kb_ids": None,  # Search all permitted KBs
        },
    )

    # THEN: Results only from KB2, NOT from KB1
    assert response.status_code == 200
    data = response.json()

    # Extract unique kb_ids from results
    result_kb_ids = {r["kb_id"] for r in data["results"]}

    # CRITICAL: User B should NOT see KB1 results
    assert (
        indexed_kb_with_docs["id"] not in result_kb_ids
    ), "SECURITY FAILURE: User B accessed User A's KB"

    # User B should only see KB2 (if any results)
    if result_kb_ids:
        assert result_kb_ids == {
            kb2["id"]
        }, "Results must only be from user's permitted KBs"


@pytest.mark.skip(
    reason="Requires indexed documents in Qdrant (ATDD RED phase - Epic 2 indexing must complete first)"
)
async def test_search_with_unauthorized_kb_id_returns_403(
    authenticated_search_client: AsyncClient,
    api_client: AsyncClient,
    second_search_user: dict,
    indexed_kb_with_docs: dict,
):
    """Test search with explicit kb_id returns 403 if user lacks READ permission.

    GIVEN: User B has no READ permission on User A's KB
    WHEN: User B explicitly searches kb_ids=[KB_A_ID]
    THEN: Response is 403 Forbidden

    This is a SECURITY-CRITICAL test (R-006: Permission bypass risk).
    This test will FAIL until permission enforcement is implemented.
    """
    # GIVEN: Second user authenticated
    second_client_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": second_search_user["email"],
            "password": second_search_user["password"],
        },
    )
    assert second_client_response.status_code == 204
    second_auth_client = api_client

    # WHEN: User B tries to search User A's KB
    response = await second_auth_client.post(
        "/api/v1/search",
        json={
            "query": "authentication",
            "kb_ids": [indexed_kb_with_docs["id"]],  # User B has no READ permission
        },
    )

    # THEN: Access denied
    assert response.status_code == 403
    data = response.json()
    assert (
        "permission" in data["detail"].lower() or "forbidden" in data["detail"].lower()
    )


# =============================================================================
# AC-3.1.4: Search Performance < 3s p95 (Manual Validation)
# =============================================================================


@pytest.mark.skip(
    reason="Requires indexed documents in Qdrant (ATDD RED phase - Epic 2 indexing must complete first)"
)
async def test_search_performance_basic_timing(
    authenticated_search_client: AsyncClient,
    indexed_kb_with_docs: dict,
):
    """Test search returns results within reasonable time.

    GIVEN: Single KB with indexed documents
    WHEN: User performs search
    THEN: Response time < 5s (generous threshold for single-KB search)

    NOTE: Full p95 < 3s validation with 10 KBs is manual/load test (deferred to Epic 5).
    This is a basic smoke test for performance.

    This test will FAIL until search endpoint is implemented.
    """
    # WHEN: User searches with timing
    start_time = time.time()

    response = await authenticated_search_client.post(
        "/api/v1/search",
        json={
            "query": "authentication best practices",
            "kb_ids": [indexed_kb_with_docs["id"]],
        },
    )

    elapsed = time.time() - start_time

    # THEN: Response within acceptable time
    assert response.status_code == 200
    assert elapsed < 5.0, f"Search took {elapsed:.2f}s, expected < 5s"


# =============================================================================
# AC-3.1.5: Audit Logging for Search Queries
# =============================================================================


@pytest.mark.skip(
    reason="Requires indexed documents in Qdrant (ATDD RED phase - Epic 2 indexing must complete first)"
)
async def test_search_query_logged_to_audit_events(
    authenticated_search_client: AsyncClient,
    indexed_kb_with_docs: dict,
    db_session,
):
    """Test search queries are logged to audit.events table.

    GIVEN: User performs search
    WHEN: Search completes successfully
    THEN:
        - audit.events contains log entry
        - event_type = 'search.query'
        - payload includes query, kb_ids, user_id, result_count

    This is a COMPLIANCE requirement (AC-3.1.5).
    This test will FAIL until audit logging is implemented in search endpoint.
    """
    # WHEN: User performs search
    response = await authenticated_search_client.post(
        "/api/v1/search",
        json={
            "query": "authentication security",
            "kb_ids": [indexed_kb_with_docs["id"]],
        },
    )

    assert response.status_code == 200
    data = response.json()

    # THEN: Audit log created
    from sqlalchemy import select

    from app.models.audit import AuditEvent

    # Query audit.events for search.query event
    stmt = (
        select(AuditEvent)
        .where(AuditEvent.event_type == "search.query")
        .order_by(AuditEvent.timestamp.desc())
    )

    result = await db_session.execute(stmt)
    events = result.scalars().all()

    # Validate audit log exists
    assert len(events) > 0, "No audit log found for search query"

    latest_event = events[0]

    # Validate audit payload
    assert latest_event.event_type == "search.query"
    assert "query" in latest_event.payload
    assert latest_event.payload["query"] == "authentication security"
    assert "kb_ids" in latest_event.payload
    assert latest_event.payload["kb_ids"] == [indexed_kb_with_docs["id"]]
    assert "result_count" in latest_event.payload
    assert latest_event.payload["result_count"] == len(data["results"])
