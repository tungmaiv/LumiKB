"""Integration tests for clear+undo workflow with Redis (Story 4-3, AC-2, AC-3).

Tests full clear → undo → restore workflow with Redis state verification.
Priority: P0 (critical conversation management flow).
"""

import json

import pytest


@pytest.mark.asyncio
async def test_clear_and_undo_workflow(
    api_client,
    authenticated_headers,
    demo_kb_with_indexed_docs,
    redis_client,
    test_user_data,
):
    """[P0] Test complete clear → undo → restore workflow with Redis verification (AC-2, AC-3)."""
    kb_id = demo_kb_with_indexed_docs["id"]
    user_id = test_user_data["user_id"]
    session_id = user_id
    conversation_key = f"conversation:{session_id}:{kb_id}"
    backup_key = f"{conversation_key}:backup"

    # GIVEN: Seed conversation history in Redis
    test_history = [
        {
            "role": "user",
            "content": "Test question 1",
            "timestamp": "2025-11-28T10:00:00Z",
        },
        {
            "role": "assistant",
            "content": "Test answer 1",
            "citations": [],
            "confidence": 0.9,
            "timestamp": "2025-11-28T10:00:02Z",
        },
        {
            "role": "user",
            "content": "Test question 2",
            "timestamp": "2025-11-28T10:01:00Z",
        },
        {
            "role": "assistant",
            "content": "Test answer 2",
            "citations": [],
            "confidence": 0.85,
            "timestamp": "2025-11-28T10:01:02Z",
        },
    ]
    await redis_client.setex(conversation_key, 86400, json.dumps(test_history))

    # Verify conversation exists before clear
    exists_before = await redis_client.exists(conversation_key)
    assert exists_before == 1

    # WHEN: Clear conversation
    clear_response = await api_client.delete(
        f"/api/v1/chat/clear?kb_id={kb_id}",
        cookies=authenticated_headers,
    )

    # THEN: Clear successful, undo available
    assert clear_response.status_code == 200
    clear_data = clear_response.json()
    assert clear_data["message"] == "Conversation cleared"
    assert clear_data["undo_available"] is True

    # Verify Redis state after clear
    conversation_exists = await redis_client.exists(conversation_key)
    backup_exists = await redis_client.exists(backup_key)
    assert conversation_exists == 0  # Main conversation deleted
    assert backup_exists == 1  # Backup created

    # Verify backup contains original conversation
    backup_data = await redis_client.get(backup_key)
    restored_history = json.loads(backup_data)
    assert len(restored_history) == 4
    assert restored_history[0]["content"] == "Test question 1"
    assert restored_history[3]["content"] == "Test answer 2"

    # WHEN: Undo clear
    undo_response = await api_client.post(
        f"/api/v1/chat/undo-clear?kb_id={kb_id}",
        cookies=authenticated_headers,
    )

    # THEN: Undo successful
    assert undo_response.status_code == 200
    undo_data = undo_response.json()
    assert undo_data["message"] == "Conversation restored"
    assert undo_data["success"] is True

    # Verify Redis state after undo
    conversation_exists_after = await redis_client.exists(conversation_key)
    backup_exists_after = await redis_client.exists(backup_key)
    assert conversation_exists_after == 1  # Conversation restored
    assert backup_exists_after == 0  # Backup deleted

    # Verify restored conversation matches original
    final_conversation = await redis_client.get(conversation_key)
    final_history = json.loads(final_conversation)
    assert len(final_history) == 4
    assert final_history == test_history

    # Verify conversation accessible via GET /history
    history_response = await api_client.get(
        f"/api/v1/chat/history?kb_id={kb_id}",
        cookies=authenticated_headers,
    )
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert history_data["message_count"] == 4
    assert history_data["messages"] == test_history


@pytest.mark.asyncio
async def test_undo_fails_when_backup_expired(
    api_client,
    authenticated_headers,
    demo_kb_with_indexed_docs,
    redis_client,
):
    """[P0] Test undo returns 410 when backup expired/missing (AC-3)."""
    kb_id = demo_kb_with_indexed_docs["id"]

    # GIVEN: No backup exists (simulate expired undo window)
    # WHEN: Attempt undo
    response = await api_client.post(
        f"/api/v1/chat/undo-clear?kb_id={kb_id}",
        cookies=authenticated_headers,
    )

    # THEN: 410 Gone error
    assert response.status_code == 410
    data = response.json()
    assert "expired" in data["detail"].lower()
    assert "30 seconds" in data["detail"]


@pytest.mark.asyncio
async def test_clear_with_empty_conversation(
    api_client,
    authenticated_headers,
    demo_kb_with_indexed_docs,
    redis_client,
    test_user_data,
):
    """[P1] Test clear on empty conversation returns safe response (AC-6)."""
    kb_id = demo_kb_with_indexed_docs["id"]
    user_id = test_user_data["user_id"]
    session_id = user_id
    conversation_key = f"conversation:{session_id}:{kb_id}"

    # GIVEN: No conversation exists
    exists = await redis_client.exists(conversation_key)
    assert exists == 0

    # WHEN: Clear conversation
    response = await api_client.delete(
        f"/api/v1/chat/clear?kb_id={kb_id}",
        cookies=authenticated_headers,
    )

    # THEN: Success response, no undo available
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "No conversation to clear"
    assert data["undo_available"] is False


@pytest.mark.asyncio
async def test_new_chat_clears_existing_conversation(
    api_client,
    authenticated_headers,
    demo_kb_with_indexed_docs,
    redis_client,
    test_user_data,
):
    """[P1] Test new chat deletes existing conversation in Redis (AC-1)."""
    kb_id = demo_kb_with_indexed_docs["id"]
    user_id = test_user_data["user_id"]
    session_id = user_id
    conversation_key = f"conversation:{session_id}:{kb_id}"

    # GIVEN: Existing conversation in Redis
    existing_history = [
        {"role": "user", "content": "Old message", "timestamp": "2025-11-28T10:00:00Z"}
    ]
    await redis_client.setex(conversation_key, 86400, json.dumps(existing_history))

    # Verify conversation exists
    exists_before = await redis_client.exists(conversation_key)
    assert exists_before == 1

    # WHEN: Start new chat
    response = await api_client.post(
        f"/api/v1/chat/new?kb_id={kb_id}",
        cookies=authenticated_headers,
    )

    # THEN: New conversation ID generated
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["conversation_id"].startswith("conv-")
    assert data["kb_id"] == kb_id

    # Verify old conversation deleted from Redis
    exists_after = await redis_client.exists(conversation_key)
    assert exists_after == 0


@pytest.mark.asyncio
async def test_kb_switching_preserves_conversations(
    api_client,
    authenticated_headers,
    demo_kb_with_indexed_docs,
    second_test_kb,
    redis_client,
    test_user_data,
):
    """[P1] Test switching KB preserves per-KB conversation isolation (AC-5)."""
    kb_a_id = demo_kb_with_indexed_docs["id"]
    kb_b_id = second_test_kb["id"]
    user_id = test_user_data["user_id"]
    session_id = user_id

    # GIVEN: Conversations in both KBs
    kb_a_history = [
        {"role": "user", "content": "KB-A question", "timestamp": "2025-11-28T10:00:00Z"}
    ]
    kb_b_history = [
        {"role": "user", "content": "KB-B question", "timestamp": "2025-11-28T10:05:00Z"}
    ]

    await redis_client.setex(
        f"conversation:{session_id}:{kb_a_id}",
        86400,
        json.dumps(kb_a_history),
    )
    await redis_client.setex(
        f"conversation:{session_id}:{kb_b_id}",
        86400,
        json.dumps(kb_b_history),
    )

    # WHEN: Get history for KB-A
    response_a = await api_client.get(
        f"/api/v1/chat/history?kb_id={kb_a_id}",
        cookies=authenticated_headers,
    )

    # THEN: Returns KB-A history only
    assert response_a.status_code == 200
    data_a = response_a.json()
    assert data_a["message_count"] == 1
    assert data_a["messages"][0]["content"] == "KB-A question"

    # WHEN: Get history for KB-B
    response_b = await api_client.get(
        f"/api/v1/chat/history?kb_id={kb_b_id}",
        cookies=authenticated_headers,
    )

    # THEN: Returns KB-B history only
    assert response_b.status_code == 200
    data_b = response_b.json()
    assert data_b["message_count"] == 1
    assert data_b["messages"][0]["content"] == "KB-B question"

    # WHEN: Clear KB-A
    await api_client.delete(
        f"/api/v1/chat/clear?kb_id={kb_a_id}",
        cookies=authenticated_headers,
    )

    # THEN: KB-A cleared, KB-B intact
    kb_a_exists = await redis_client.exists(f"conversation:{session_id}:{kb_a_id}")
    kb_b_exists = await redis_client.exists(f"conversation:{session_id}:{kb_b_id}")
    assert kb_a_exists == 0  # KB-A cleared
    assert kb_b_exists == 1  # KB-B untouched


@pytest.mark.asyncio
async def test_backup_ttl_expires_after_30_seconds(
    api_client,
    authenticated_headers,
    demo_kb_with_indexed_docs,
    redis_client,
    test_user_data,
):
    """[P1] Test backup key has 30-second TTL (AC-3)."""
    kb_id = demo_kb_with_indexed_docs["id"]
    user_id = test_user_data["user_id"]
    session_id = user_id
    conversation_key = f"conversation:{session_id}:{kb_id}"
    backup_key = f"{conversation_key}:backup"

    # GIVEN: Conversation exists
    test_history = [
        {"role": "user", "content": "Test", "timestamp": "2025-11-28T10:00:00Z"}
    ]
    await redis_client.setex(conversation_key, 86400, json.dumps(test_history))

    # WHEN: Clear conversation
    await api_client.delete(
        f"/api/v1/chat/clear?kb_id={kb_id}",
        cookies=authenticated_headers,
    )

    # THEN: Backup exists with TTL ≈ 30 seconds
    backup_exists = await redis_client.exists(backup_key)
    assert backup_exists == 1

    backup_ttl = await redis_client.ttl(backup_key)
    assert backup_ttl > 0
    assert backup_ttl <= 30  # Should be ≤ 30 seconds
