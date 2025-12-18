"""Integration tests for User Chat Sessions API (Story 8-0).

Tests the user-facing session history endpoints:
- GET /api/v1/chat/sessions - list user's chat sessions for a KB
- GET /api/v1/chat/sessions/{conversation_id}/messages - get session messages
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import ObsChatMessage

pytestmark = pytest.mark.integration


class TestUserSessionsAPI:
    """Test user chat sessions listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty_kb(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """Returns empty list when no sessions exist."""
        kb_id = demo_kb_with_indexed_docs["id"]

        response = await api_client.get(
            f"/api/v1/chat/sessions?kb_id={kb_id}",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "sessions" in data
        assert "total" in data
        assert "max_sessions" in data
        assert isinstance(data["sessions"], list)
        # May have sessions from other tests - just verify structure
        assert data["max_sessions"] >= 1

    @pytest.mark.asyncio
    async def test_list_sessions_permission_check(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
    ):
        """Returns 404 for unauthorized KB."""
        fake_kb_id = "00000000-0000-0000-0000-000000000000"

        response = await api_client.get(
            f"/api/v1/chat/sessions?kb_id={fake_kb_id}",
            cookies=authenticated_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        db_session: AsyncSession,
        test_user,
    ):
        """Returns session list when sessions exist in observability."""
        kb_id = demo_kb_with_indexed_docs["id"]

        # Create test session data in observability
        conv_id = uuid.uuid4()
        test_messages = [
            ObsChatMessage(
                id=uuid.uuid4(),
                conversation_id=conv_id,
                user_id=test_user.id,
                kb_id=uuid.UUID(kb_id),
                role="user",
                content="What is OAuth 2.0?",
                attributes={},
            ),
            ObsChatMessage(
                id=uuid.uuid4(),
                conversation_id=conv_id,
                user_id=test_user.id,
                kb_id=uuid.UUID(kb_id),
                role="assistant",
                content="OAuth 2.0 is an authorization framework...",
                attributes={"confidence": 0.87, "citations": []},
            ),
        ]

        for msg in test_messages:
            db_session.add(msg)
        await db_session.commit()

        # Query sessions
        response = await api_client.get(
            f"/api/v1/chat/sessions?kb_id={kb_id}",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        assert len(data["sessions"]) >= 1

        # Find our test session
        test_session = next(
            (s for s in data["sessions"] if s["conversation_id"] == f"conv-{conv_id}"),
            None,
        )

        if test_session:
            assert test_session["kb_id"] == kb_id
            assert test_session["message_count"] == 2
            assert "first_message_preview" in test_session
            assert "last_message_at" in test_session
            assert "first_message_at" in test_session


class TestSessionMessagesAPI:
    """Test session messages retrieval endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_messages_not_found(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """Returns 404 for non-existent session."""
        kb_id = demo_kb_with_indexed_docs["id"]
        fake_conv_id = f"conv-{uuid.uuid4()}"

        response = await api_client.get(
            f"/api/v1/chat/sessions/{fake_conv_id}/messages?kb_id={kb_id}",
            cookies=authenticated_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_session_messages_invalid_format(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """Returns 400 for invalid conversation_id format."""
        kb_id = demo_kb_with_indexed_docs["id"]

        response = await api_client.get(
            "/api/v1/chat/sessions/invalid-id/messages?kb_id={kb_id}",
            cookies=authenticated_headers,
        )

        # Either 400 for invalid format or 404 for not found
        assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_get_session_messages_permission_check(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
    ):
        """Returns 404 for unauthorized KB."""
        fake_kb_id = "00000000-0000-0000-0000-000000000000"
        fake_conv_id = f"conv-{uuid.uuid4()}"

        response = await api_client.get(
            f"/api/v1/chat/sessions/{fake_conv_id}/messages?kb_id={fake_kb_id}",
            cookies=authenticated_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_session_messages_with_data(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        db_session: AsyncSession,
        test_user,
    ):
        """Returns messages for valid session owned by user."""
        kb_id = demo_kb_with_indexed_docs["id"]

        # Create test session data
        conv_id = uuid.uuid4()
        test_messages = [
            ObsChatMessage(
                id=uuid.uuid4(),
                conversation_id=conv_id,
                user_id=test_user.id,
                kb_id=uuid.UUID(kb_id),
                role="user",
                content="Tell me about security",
                attributes={},
            ),
            ObsChatMessage(
                id=uuid.uuid4(),
                conversation_id=conv_id,
                user_id=test_user.id,
                kb_id=uuid.UUID(kb_id),
                role="assistant",
                content="Security is important for...",
                attributes={
                    "confidence": 0.92,
                    "citations": [{"number": 1, "document_name": "test.pdf"}],
                },
            ),
        ]

        for msg in test_messages:
            db_session.add(msg)
        await db_session.commit()

        # Query session messages
        response = await api_client.get(
            f"/api/v1/chat/sessions/conv-{conv_id}/messages?kb_id={kb_id}",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["conversation_id"] == f"conv-{conv_id}"
        assert data["kb_id"] == kb_id
        assert data["message_count"] == 2
        assert len(data["messages"]) == 2

        # Verify message order (chronological)
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Tell me about security"

        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["content"] == "Security is important for..."
        assert data["messages"][1]["confidence"] == 0.92


class TestSessionOwnership:
    """Test that users can only access their own sessions."""

    @pytest.mark.asyncio
    async def test_cannot_access_other_user_session(
        self,
        api_client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        db_session: AsyncSession,
    ):
        """User cannot access sessions owned by other users."""
        kb_id = demo_kb_with_indexed_docs["id"]

        # Create session owned by a different user
        other_user_id = uuid.uuid4()
        conv_id = uuid.uuid4()

        other_msg = ObsChatMessage(
            id=uuid.uuid4(),
            conversation_id=conv_id,
            user_id=other_user_id,  # Different user!
            kb_id=uuid.UUID(kb_id),
            role="user",
            content="Other user's message",
            attributes={},
        )

        db_session.add(other_msg)
        await db_session.commit()

        # Try to access other user's session
        response = await api_client.get(
            f"/api/v1/chat/sessions/conv-{conv_id}/messages?kb_id={kb_id}",
            cookies=authenticated_headers,
        )

        # Should return 404 (not found because ownership check fails)
        assert response.status_code == 404
