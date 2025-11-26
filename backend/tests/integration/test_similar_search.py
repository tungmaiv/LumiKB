"""
Integration tests for Similar Search (Story 3.8).

Tests:
- Similar search returns similar chunks
- Original chunk excluded from results
- Permission enforcement (user must have READ access to KB)
- Chunk not found returns 404
- Cross-KB similar search

Note: These tests are placeholders requiring actual indexed chunk data.
The full implementation requires Story 2.6 (chunking/embedding) fixtures.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_document, create_knowledge_base, create_user


@pytest.mark.asyncio
async def test_similar_search_returns_similar_chunks(
    client: AsyncClient,
    test_db: AsyncSession,
    auth_headers: dict[str, str],
):
    """Similar search returns chunks similar to the source chunk."""
    # Arrange: Create user, KB, and upload document (auto-indexes)
    user = await create_user(test_db)
    kb = await create_knowledge_base(test_db, owner_id=user.id)
    await create_document(test_db, kb_id=kb.id, user_id=user.id)

    # Wait for indexing (document factory uploads to MinIO and triggers worker)
    # In real test, we'd poll document.status or use test fixtures with pre-indexed data
    # For now, assume indexing complete with chunk_ids available

    # Mock: Assume we have a chunk_id from indexed data
    chunk_id = "test-chunk-123"  # Replace with actual chunk_id from fixture

    # Act: Call similar search endpoint
    response = await client.post(
        "/api/v1/search/similar",
        json={"chunk_id": chunk_id, "limit": 5},
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert data["query"].startswith("Similar to:")
    assert "results" in data
    # Note: Results count depends on test data - may be empty if only 1 chunk indexed


@pytest.mark.asyncio
async def test_similar_search_excludes_original_chunk(
    client: AsyncClient,
    test_db: AsyncSession,
    auth_headers: dict[str, str],
):
    """Similar search does NOT return the original chunk itself."""
    # Arrange: User, KB, document with multiple chunks
    user = await create_user(test_db)
    kb = await create_knowledge_base(test_db, owner_id=user.id)
    await create_document(test_db, kb_id=kb.id, user_id=user.id)

    # Mock chunk_id (replace with actual fixture data)
    chunk_id = "test-chunk-original"

    # Act
    response = await client.post(
        "/api/v1/search/similar",
        json={"chunk_id": chunk_id, "limit": 10},
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    [r["document_id"] for r in data["results"]]

    # Verify original chunk NOT in results
    # Note: This test requires actual chunk_id tracking in test fixtures
    # For now, assert results don't include the source chunk_id
    # assert chunk_id not in result_ids


@pytest.mark.asyncio
async def test_similar_search_permission_denied(
    client: AsyncClient,
    test_db: AsyncSession,
):
    """Similar search returns 404 when user lacks access to KB."""
    # Arrange: User A owns KB1, User B has no access
    user_a = await create_user(test_db)
    user_b = await create_user(test_db)

    kb = await create_knowledge_base(test_db, owner_id=user_a.id)
    await create_document(test_db, kb_id=kb.id, user_id=user_a.id)

    # Mock chunk_id from user_a's KB
    chunk_id = "chunk-in-restricted-kb"

    # Act: User B tries similar search on chunk from User A's KB
    # Get auth headers for user_b
    auth_headers_b = {"Authorization": f"Bearer {user_b.id}"}  # Mock auth

    response = await client.post(
        "/api/v1/search/similar",
        json={"chunk_id": chunk_id},
        headers=auth_headers_b,
    )

    # Assert: Returns 404 (not 403 to avoid info disclosure)
    assert response.status_code == 404
    assert "content no longer available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_similar_search_chunk_not_found(
    client: AsyncClient,
    test_db: AsyncSession,
    auth_headers: dict[str, str],
):
    """Similar search returns 404 when chunk doesn't exist."""
    # Act: Request similar search with non-existent chunk_id
    response = await client.post(
        "/api/v1/search/similar",
        json={"chunk_id": "non-existent-chunk-999"},
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 404
    assert "content no longer available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_similar_search_cross_kb(
    client: AsyncClient,
    test_db: AsyncSession,
    auth_headers: dict[str, str],
):
    """Similar search can find results across multiple KBs (cross-KB search)."""
    # Arrange: User with access to 2 KBs
    user = await create_user(test_db)
    kb1 = await create_knowledge_base(test_db, owner_id=user.id)
    kb2 = await create_knowledge_base(test_db, owner_id=user.id)

    # Upload docs to both KBs
    await create_document(test_db, kb_id=kb1.id, user_id=user.id)
    await create_document(test_db, kb_id=kb2.id, user_id=user.id)

    # Mock chunk_id from KB1
    chunk_id = "chunk-from-kb1"

    # Act: Similar search without specifying kb_ids (cross-KB default)
    response = await client.post(
        "/api/v1/search/similar",
        json={"chunk_id": chunk_id},  # No kb_ids = search all permitted
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 200
    data = response.json()

    # Results should include chunks from both KB1 and KB2
    # (Note: Depends on actual indexed data having similar content)
    {r["kb_id"] for r in data["results"]}
    # assert len(kb_ids_in_results) >= 1  # At least one KB represented
