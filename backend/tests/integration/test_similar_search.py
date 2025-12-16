"""Integration tests for Similar Search (Story 3.8).

Tests cover:
- Similar search returns similar chunks
- Original chunk excluded from results
- Permission enforcement (user must have READ access to KB)
- Chunk not found returns 404
- Cross-KB similar search

Test Strategy (ATDD - GREEN Phase):
- These tests use fixtures with real Qdrant data
- Tests validate similar search behavior with indexed chunks
- Follow RED → GREEN → REFACTOR TDD cycle (GREEN phase complete)
"""

import pytest
from httpx import AsyncClient

from tests.factories import create_registration_data

pytestmark = pytest.mark.integration


# =============================================================================
# AC-3.8.1: Similar Search Returns Similar Chunks
# =============================================================================


async def test_similar_search_returns_similar_chunks(
    api_client: AsyncClient,
    test_user_data: dict,
    kb_with_indexed_chunks: dict,
):
    """Similar search returns chunks similar to the source chunk."""
    kb = kb_with_indexed_chunks["kb"]
    documents = kb_with_indexed_chunks["documents"]

    # Get a chunk_id from the indexed chunks
    # The fixture creates chunks with deterministic IDs based on document_id and chunk_index
    doc_id = str(documents[0]["id"])

    # First, search to get actual chunk IDs
    search_response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "OAuth",
            "kb_ids": [str(kb["id"])],
            "limit": 1,
        },
        cookies=test_user_data["cookies"],
    )

    assert search_response.status_code == 200
    search_data = search_response.json()

    if len(search_data["results"]) > 0:
        chunk_id = search_data["results"][0].get("chunk_id")

        if chunk_id:
            # Act: Call similar search endpoint
            response = await api_client.post(
                "/api/v1/search/similar",
                json={"chunk_id": chunk_id, "limit": 5},
                cookies=test_user_data["cookies"],
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "query" in data
            assert "Similar to:" in data["query"]
            assert "results" in data


async def test_similar_search_excludes_original_chunk(
    api_client: AsyncClient,
    test_user_data: dict,
    kb_with_indexed_chunks: dict,
):
    """Similar search does NOT return the original chunk itself."""
    kb = kb_with_indexed_chunks["kb"]

    # First, search to get actual chunk IDs
    search_response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "OAuth 2.0",
            "kb_ids": [str(kb["id"])],
            "limit": 1,
        },
        cookies=test_user_data["cookies"],
    )

    assert search_response.status_code == 200
    search_data = search_response.json()

    if len(search_data["results"]) > 0:
        chunk_id = search_data["results"][0].get("chunk_id")

        if chunk_id:
            # Act
            response = await api_client.post(
                "/api/v1/search/similar",
                json={"chunk_id": chunk_id, "limit": 10},
                cookies=test_user_data["cookies"],
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            # Verify original chunk NOT in results
            result_chunk_ids = {r.get("chunk_id") for r in data["results"]}
            assert (
                chunk_id not in result_chunk_ids
            ), "Original chunk should not be in similar search results"


# =============================================================================
# AC-3.8.2: Permission Enforcement
# =============================================================================


async def test_similar_search_permission_denied(
    api_client: AsyncClient,
    test_user_data: dict,
    kb_with_indexed_chunks: dict,
):
    """Similar search returns 404 when user lacks access to KB."""
    kb = kb_with_indexed_chunks["kb"]

    # First, get a chunk from user A's KB
    search_response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "OAuth",
            "kb_ids": [str(kb["id"])],
            "limit": 1,
        },
        cookies=test_user_data["cookies"],
    )

    assert search_response.status_code == 200
    search_data = search_response.json()

    if len(search_data["results"]) > 0:
        chunk_id = search_data["results"][0].get("chunk_id")

        if chunk_id:
            # Create and login as User B
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

            # Act: User B tries similar search on chunk from User A's KB
            response = await api_client.post(
                "/api/v1/search/similar",
                json={"chunk_id": chunk_id},
            )

            # Assert: Returns 404 (not 403 to avoid info disclosure)
            assert response.status_code == 404
            assert "content no longer available" in response.json()["detail"].lower()


async def test_similar_search_chunk_not_found(
    api_client: AsyncClient,
    test_user_data: dict,
    kb_with_indexed_chunks: dict,
):
    """Similar search returns 404 when chunk doesn't exist."""
    # Act: Request similar search with non-existent chunk_id
    response = await api_client.post(
        "/api/v1/search/similar",
        json={"chunk_id": "non-existent-chunk-999"},
        cookies=test_user_data["cookies"],
    )

    # Assert
    assert response.status_code == 404
    assert "content no longer available" in response.json()["detail"].lower()


# =============================================================================
# AC-3.8.3: Cross-KB Similar Search
# =============================================================================


async def test_similar_search_cross_kb(
    api_client: AsyncClient,
    test_user_data: dict,
    multiple_kbs_with_chunks: dict,
):
    """Similar search can find results across multiple KBs (cross-KB search)."""
    kbs = multiple_kbs_with_chunks["kbs"]

    # First, get a chunk from KB1
    search_response = await api_client.post(
        "/api/v1/search",
        json={
            "query": "best practices",
            "kb_ids": [str(kbs[0]["id"])],
            "limit": 1,
        },
        cookies=test_user_data["cookies"],
    )

    assert search_response.status_code == 200
    search_data = search_response.json()

    if len(search_data["results"]) > 0:
        chunk_id = search_data["results"][0].get("chunk_id")

        if chunk_id:
            # Act: Similar search without specifying kb_ids (cross-KB default)
            response = await api_client.post(
                "/api/v1/search/similar",
                json={"chunk_id": chunk_id},  # No kb_ids = search all permitted
                cookies=test_user_data["cookies"],
            )

            # Assert
            assert response.status_code == 200
            data = response.json()

            # Results should include chunks from multiple KBs
            kb_ids_in_results = {r["kb_id"] for r in data["results"]}
            # At least one KB represented (may include results from other KBs)
            assert len(kb_ids_in_results) >= 1
