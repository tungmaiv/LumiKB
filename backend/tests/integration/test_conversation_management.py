"""Integration tests for conversation management (Story 4-3).

Note: These tests focus on endpoint behavior without requiring Qdrant.
Full conversation flow (with RAG) is tested in test_chat_api.py.
"""

import pytest


@pytest.mark.asyncio
async def test_new_conversation_endpoint(
    api_client,
    authenticated_headers,
    demo_kb_with_indexed_docs,
):
    """Test POST /chat/new generates new conversation ID (AC-1)."""
    kb_id = demo_kb_with_indexed_docs["id"]

    # Start new conversation
    response = await api_client.post(
        f"/api/v1/chat/new?kb_id={kb_id}",
        cookies=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["kb_id"] == kb_id
    assert data["conversation_id"].startswith("conv-")


@pytest.mark.asyncio
async def test_clear_conversation_endpoint(
    api_client,
    authenticated_headers,
    demo_kb_with_indexed_docs,
):
    """Test DELETE /chat/clear responds correctly (AC-2)."""
    kb_id = demo_kb_with_indexed_docs["id"]

    # Clear conversation (should succeed even if empty)
    response = await api_client.delete(
        f"/api/v1/chat/clear?kb_id={kb_id}",
        cookies=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "undo_available" in data
    # Empty KB → no history to clear
    assert data["message"] == "No conversation to clear"
    assert data["undo_available"] is False


@pytest.mark.asyncio
async def test_undo_clear_expired(
    api_client,
    authenticated_headers,
    demo_kb_with_indexed_docs,
):
    """Test undo clear fails with 410 when no backup exists."""
    kb_id = demo_kb_with_indexed_docs["id"]

    # Attempt undo without prior clear - should fail with 410
    response = await api_client.post(
        f"/api/v1/chat/undo-clear?kb_id={kb_id}",
        cookies=authenticated_headers,
    )
    assert response.status_code == 410
    data = response.json()
    assert "expired" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_conversation_history(
    api_client,
    authenticated_headers,
    demo_kb_with_indexed_docs,
):
    """Test GET /chat/history retrieves conversation (AC-4)."""
    kb_id = demo_kb_with_indexed_docs["id"]

    # Get history (empty initially)
    response = await api_client.get(
        f"/api/v1/chat/history?kb_id={kb_id}",
        cookies=authenticated_headers,
    )
    assert response.status_code == 200
    data = response.json()

    # Verify structure
    assert "messages" in data
    assert "message_count" in data
    assert isinstance(data["messages"], list)
    assert data["message_count"] == len(data["messages"])


@pytest.mark.asyncio
async def test_conversation_permission_check(
    api_client,
    authenticated_headers,
):
    """Test permission checks on conversation management."""
    # Use non-existent KB
    kb_id = "non-existent-kb-00000000-0000-0000-0000-000000000000"

    # New conversation - should fail permission check
    response1 = await api_client.post(
        f"/api/v1/chat/new?kb_id={kb_id}",
        cookies=authenticated_headers,
    )
    assert response1.status_code in [404, 403]

    # Clear conversation - should fail permission check
    response2 = await api_client.delete(
        f"/api/v1/chat/clear?kb_id={kb_id}",
        cookies=authenticated_headers,
    )
    assert response2.status_code in [404, 403]

    # Get history - should fail permission check
    response3 = await api_client.get(
        f"/api/v1/chat/history?kb_id={kb_id}",
        cookies=authenticated_headers,
    )
    assert response3.status_code in [404, 403]
