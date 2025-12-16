"""Integration tests for Chat API (Story 4.1)."""

import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import RedisClient

pytestmark = pytest.mark.integration


class TestChatAPI:
    """Test Chat API endpoints."""

    @pytest.mark.asyncio
    async def test_chat_single_turn(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """AC1: Single-turn conversation returns response with citations."""
        kb_id = demo_kb_with_indexed_docs["id"]

        response = await api_client.post(
            "/api/v1/chat/",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "What is the purpose of this document?",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure (AC1)
        assert "answer" in data
        assert "citations" in data
        assert "confidence" in data
        assert "conversation_id" in data

        # Verify citations
        assert isinstance(data["citations"], list)
        assert len(data["citations"]) > 0

        # Verify confidence
        assert 0.0 <= data["confidence"] <= 1.0

        # Verify conversation_id format
        assert data["conversation_id"].startswith("conv-")

    @pytest.mark.asyncio
    async def test_chat_multi_turn_maintains_context(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """AC2: Multi-turn conversation maintains context."""
        kb_id = demo_kb_with_indexed_docs["id"]

        # First message
        response1 = await api_client.post(
            "/api/v1/chat/",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "Tell me about authentication",
            },
        )

        assert response1.status_code == 200
        data1 = response1.json()
        conversation_id = data1["conversation_id"]

        # Follow-up message (references previous context)
        response2 = await api_client.post(
            "/api/v1/chat/",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "What about security?",  # Contextual follow-up
                "conversation_id": conversation_id,
            },
        )

        assert response2.status_code == 200
        data2 = response2.json()

        # Verify conversation_id is preserved
        assert data2["conversation_id"] == conversation_id

        # Verify response is contextual (contains answer)
        assert len(data2["answer"]) > 0

    @pytest.mark.asyncio
    async def test_chat_conversation_stored_in_redis(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """AC4: Conversation stored in Redis with correct structure."""
        kb_id = demo_kb_with_indexed_docs["id"]

        # Send message
        response = await api_client.post(
            "/api/v1/chat/",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "Test message",
            },
        )

        assert response.status_code == 200

        # Verify Redis storage
        redis_client = await RedisClient.get_client()

        # Extract session_id from authenticated user
        # In actual implementation, session_id = user_id
        # For test, we need to get user_id from authenticated_headers
        # Simplified: Check if any conversation key exists for this KB
        keys = await redis_client.keys(f"conversation:*:{kb_id}")
        assert len(keys) > 0, "Conversation not stored in Redis"

        # Read conversation history
        history_json = await redis_client.get(keys[0])
        assert history_json is not None

        history = json.loads(history_json)
        assert isinstance(history, list)
        assert len(history) >= 2  # User message + assistant response

        # Verify user message
        user_msg = history[0]
        assert user_msg["role"] == "user"
        assert user_msg["content"] == "Test message"
        assert "timestamp" in user_msg

        # Verify assistant response
        assistant_msg = history[1]
        assert assistant_msg["role"] == "assistant"
        assert "content" in assistant_msg
        assert "citations" in assistant_msg
        assert "confidence" in assistant_msg
        assert "timestamp" in assistant_msg

    @pytest.mark.asyncio
    async def test_chat_permission_enforcement(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
    ):
        """AC5: Permission check returns 404 for unauthorized KB."""
        # Use a non-existent KB ID (no permission)
        fake_kb_id = "00000000-0000-0000-0000-000000000000"

        response = await api_client.post(
            "/api/v1/chat/",
            cookies=authenticated_headers,
            json={
                "kb_id": fake_kb_id,
                "message": "Test message",
            },
        )

        # Should return 404 (not 403) to avoid leaking KB existence
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_empty_message_validation(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """AC6: Empty message returns 400 Bad Request."""
        kb_id = demo_kb_with_indexed_docs["id"]

        response = await api_client.post(
            "/api/v1/chat/",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "",  # Empty message
            },
        )

        # Pydantic validation should reject empty message
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_chat_kb_with_no_documents(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        empty_kb_factory,
    ):
        """AC6: KB with no documents returns clear error."""
        # Create empty KB (no documents)
        empty_kb = await empty_kb_factory()

        response = await api_client.post(
            "/api/v1/chat/",
            cookies=authenticated_headers,
            json={
                "kb_id": str(empty_kb.id),
                "message": "Test message",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "no indexed documents" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_chat_audit_logging(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        db_session: AsyncSession,
    ):
        """AC7: Audit event logged for chat message."""
        from app.models.audit import AuditEvent

        kb_id = demo_kb_with_indexed_docs["id"]

        # Send message
        response = await api_client.post(
            "/api/v1/chat/",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "Test message for audit",
            },
        )

        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]

        # Query audit log
        from sqlalchemy import select

        result = await db_session.execute(
            select(AuditEvent)
            .where(AuditEvent.action == "chat.message")
            .where(AuditEvent.resource_id == conversation_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(1)
        )
        audit_event = result.scalar_one_or_none()

        assert audit_event is not None, "Audit event not logged"
        assert audit_event.resource_type == "conversation"
        assert audit_event.details["kb_id"] == kb_id
        assert audit_event.details["message_length"] == len("Test message for audit")
        assert "response_length" in audit_event.details
        assert "citation_count" in audit_event.details
        assert "confidence" in audit_event.details
        assert "response_time_ms" in audit_event.details
        assert audit_event.details["success"] is True

    @pytest.mark.asyncio
    async def test_chat_invalid_conversation_id_starts_fresh(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """AC6: Invalid conversation_id starts fresh conversation."""
        kb_id = demo_kb_with_indexed_docs["id"]

        # Use invalid conversation_id
        response = await api_client.post(
            "/api/v1/chat/",
            cookies=authenticated_headers,
            json={
                "kb_id": kb_id,
                "message": "Test message",
                "conversation_id": "conv-invalid-does-not-exist",
            },
        )

        # Should succeed and create new conversation
        assert response.status_code == 200
        data = response.json()

        # Should return a conversation_id (fresh conversation started)
        assert "conversation_id" in data
        # Note: Implementation may reuse provided ID or generate new one
        # Both behaviors are acceptable per AC6
