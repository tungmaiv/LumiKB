"""
ATDD Integration Tests: Epic 4 - Chat Conversation Backend (Story 4.1)
Status: RED phase - Tests written before implementation
Generated: 2025-11-26

Test Coverage:
- P0: Multi-turn conversation with context (R-001)
- P0: Token limit enforcement (R-001)
- P0: Conversation context stored in Redis (R-006)
- P1: New conversation clears context
- P1: Conversation retrieval

Risk Mitigation:
- R-001 (TECH): Token limit management - sliding window context
- R-006 (TECH): Redis session storage

Knowledge Base References:
- test-quality.md: Deterministic tests with explicit assertions
- data-factories.md: Factory patterns for test data
"""

import pytest
from fastapi import status
from httpx import AsyncClient


class TestChatConversationBackend:
    """Test chat conversation API endpoints and context management"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_turn_conversation_maintains_context(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        P0 Test - Story 4.1
        Risk: R-001 (Token limit management)

        GIVEN: User has an active conversation
        WHEN: User sends multiple follow-up messages (5 turns)
        THEN: Each response maintains context from previous turns
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        # Turn 1: Initial question
        response1 = await client.post(
            "/api/v1/chat",
            headers=authenticated_headers,
            json={
                "message": "What is OAuth 2.0?",
                "kb_id": kb_id,
            },
        )
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        conversation_id = data1["conversation_id"]
        assert "OAuth" in data1["answer"]
        assert len(data1["citations"]) > 0

        # Turn 2: Follow-up (requires context)
        response2 = await client.post(
            "/api/v1/chat",
            headers=authenticated_headers,
            json={
                "message": "How do I implement it?",  # "it" refers to OAuth
                "kb_id": kb_id,
                "conversation_id": conversation_id,
            },
        )
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        # Should reference OAuth implementation (context maintained)
        assert "implement" in data2["answer"].lower() or "OAuth" in data2["answer"]

        # Turn 3: Another follow-up
        response3 = await client.post(
            "/api/v1/chat",
            headers=authenticated_headers,
            json={
                "message": "What are the security risks?",  # Contextual to OAuth
                "kb_id": kb_id,
                "conversation_id": conversation_id,
            },
        )
        assert response3.status_code == status.HTTP_200_OK
        data3 = response3.json()
        # Should discuss OAuth security (maintains topic context)
        assert (
            "security" in data3["answer"].lower() or "risk" in data3["answer"].lower()
        )

        # Turn 4 & 5: Continue conversation
        for i in range(2):
            response = await client.post(
                "/api/v1/chat",
                headers=authenticated_headers,
                json={
                    "message": f"Tell me more about that (turn {i + 4})",
                    "kb_id": kb_id,
                    "conversation_id": conversation_id,
                },
            )
            assert response.status_code == status.HTTP_200_OK
            assert len(response.json()["answer"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_token_limit_enforced_in_long_conversation(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        P0 Test - Story 4.1
        Risk: R-001 (Token limit management)

        GIVEN: User has a very long conversation (20 turns)
        WHEN: Context is passed to LLM
        THEN: Total tokens do not exceed configured limit (4K context window)
        AND: Sliding window keeps recent messages + important context
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        # Create initial conversation
        response = await client.post(
            "/api/v1/chat",
            headers=authenticated_headers,
            json={"message": "What is OAuth?", "kb_id": kb_id},
        )
        conversation_id = response.json()["conversation_id"]

        # Simulate 20 turns with substantial messages
        for turn in range(20):
            response = await client.post(
                "/api/v1/chat",
                headers=authenticated_headers,
                json={
                    "message": f"Follow-up question {turn + 1}: "
                    + "word " * 50,  # ~50 tokens per message
                    "kb_id": kb_id,
                    "conversation_id": conversation_id,
                },
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify metadata includes token usage
            assert "metadata" in data
            assert "context_tokens" in data["metadata"]

            # CRITICAL: Context tokens should not exceed limit (4000 tokens)
            assert data["metadata"]["context_tokens"] <= 4000, (
                f"Turn {turn + 1}: Context tokens {data['metadata']['context_tokens']} "
                "exceeded limit of 4000"
            )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conversation_context_stored_in_redis(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
        redis_client,
    ):
        """
        P0 Test - Story 4.1
        Risk: R-006 (Redis session storage)

        GIVEN: User starts a conversation
        WHEN: Conversation progresses
        THEN: Context is stored in Redis with correct structure
        AND: Context includes messages + RAG chunks
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        # Send message
        response = await client.post(
            "/api/v1/chat",
            headers=authenticated_headers,
            json={"message": "What is OAuth?", "kb_id": kb_id},
        )
        assert response.status_code == status.HTTP_200_OK
        conversation_id = response.json()["conversation_id"]

        # Query Redis for conversation context
        redis_key = f"conversation:{conversation_id}"
        context_json = await redis_client.get(redis_key)

        assert context_json is not None, "Conversation not found in Redis"

        import json

        context = json.loads(context_json)

        # Verify context structure
        assert "messages" in context
        assert len(context["messages"]) >= 2  # User message + AI response
        assert "retrieved_chunks" in context
        assert len(context["retrieved_chunks"]) > 0

        # Verify message structure
        user_msg = context["messages"][0]
        assert user_msg["role"] == "user"
        assert "OAuth" in user_msg["content"]

        ai_msg = context["messages"][1]
        assert ai_msg["role"] == "assistant"
        assert len(ai_msg["content"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_new_conversation_clears_context(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        P1 Test - Story 4.3

        GIVEN: User has an existing conversation with context
        WHEN: User starts a new conversation
        THEN: Previous context is not referenced in responses
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        # First conversation about OAuth
        response1 = await client.post(
            "/api/v1/chat",
            headers=authenticated_headers,
            json={"message": "Tell me about OAuth 2.0", "kb_id": kb_id},
        )
        conv1_id = response1.json()["conversation_id"]

        # Follow-up in first conversation
        await client.post(
            "/api/v1/chat",
            headers=authenticated_headers,
            json={
                "message": "What are the grant types?",
                "kb_id": kb_id,
                "conversation_id": conv1_id,
            },
        )

        # Start NEW conversation (different topic)
        response2 = await client.post(
            "/api/v1/chat",
            headers=authenticated_headers,
            json={"message": "What is JWT?", "kb_id": kb_id},
            # NO conversation_id → new conversation
        )
        conv2_id = response2.json()["conversation_id"]

        assert conv2_id != conv1_id, "New conversation should have different ID"

        # Send ambiguous message that would reference old context if not cleared
        response3 = await client.post(
            "/api/v1/chat",
            headers=authenticated_headers,
            json={
                "message": "Which grant type should I use?",  # Would make sense in OAuth context
                "kb_id": kb_id,
                "conversation_id": conv2_id,
            },
        )

        # Should NOT reference OAuth grant types (context cleared)
        answer = response3.json()["answer"].lower()
        # JWT conversation context maintained, not OAuth
        assert "jwt" in answer or "token" in answer

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conversation_retrieval(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        demo_kb_with_indexed_docs: dict,
    ):
        """
        P1 Test - Story 4.3

        GIVEN: User has an active conversation with 3 messages
        WHEN: User retrieves conversation history
        THEN: All messages are returned in chronological order
        """
        kb_id = demo_kb_with_indexed_docs["id"]

        # Create conversation with 3 exchanges
        messages_sent = [
            "What is OAuth?",
            "How do I implement it?",
            "What are security risks?",
        ]
        conversation_id = None

        for msg in messages_sent:
            response = await client.post(
                "/api/v1/chat",
                headers=authenticated_headers,
                json={
                    "message": msg,
                    "kb_id": kb_id,
                    "conversation_id": conversation_id,
                },
            )
            if conversation_id is None:
                conversation_id = response.json()["conversation_id"]

        # Retrieve conversation
        response = await client.get(
            f"/api/v1/chat/conversations/{conversation_id}",
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify structure
        assert "messages" in data
        assert len(data["messages"]) == 6  # 3 user + 3 assistant messages

        # Verify order (user, assistant, user, assistant, ...)
        for i, message in enumerate(data["messages"]):
            expected_role = "user" if i % 2 == 0 else "assistant"
            assert message["role"] == expected_role

            if message["role"] == "user":
                user_idx = i // 2
                assert messages_sent[user_idx] in message["content"]
