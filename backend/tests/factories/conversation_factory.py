"""Conversation data factories for chat tests.

Provides factory functions for creating test conversation data
for multi-turn chat integration tests.

Usage:
    from tests.factories import create_conversation, create_multi_turn_conversation

    # Basic conversation
    conv = create_conversation()

    # With multiple turns
    conv = create_multi_turn_conversation(turns=5)
"""

from datetime import datetime
from uuid import UUID, uuid4

from faker import Faker

fake = Faker()


def create_conversation(
    id: UUID | None = None,
    user_id: UUID | None = None,
    kb_id: UUID | None = None,
    title: str | None = None,
    messages: list | None = None,
    created_at: datetime | None = None,
) -> dict:
    """Factory for conversation data.

    Creates a dictionary representing a conversation session.
    All fields have sensible defaults that can be overridden.

    Args:
        id: Conversation UUID (generated if not provided)
        user_id: User UUID who owns the conversation
        kb_id: Knowledge base UUID the conversation is scoped to
        title: Conversation title (generated if not provided)
        messages: List of message dicts (empty list if not provided)
        created_at: Creation timestamp (current time if not provided)

    Returns:
        dict: Conversation data dictionary with all fields populated
    """
    return {
        "id": str(id) if id else str(uuid4()),
        "user_id": str(user_id) if user_id else str(uuid4()),
        "kb_id": str(kb_id) if kb_id else str(uuid4()),
        "title": title or f"Chat about {fake.word()}",
        "messages": messages if messages is not None else [],
        "created_at": (
            created_at.isoformat() if created_at else datetime.utcnow().isoformat()
        ),
    }


def create_multi_turn_conversation(
    turns: int = 5,
    user_id: UUID | None = None,
    kb_id: UUID | None = None,
) -> dict:
    """Create conversation with multiple message turns.

    Generates alternating user/assistant messages to simulate
    a realistic multi-turn conversation.

    Args:
        turns: Number of message turns (each turn = user + assistant)
        user_id: User UUID who owns the conversation
        kb_id: Knowledge base UUID the conversation is scoped to

    Returns:
        dict: Conversation with populated messages list
    """
    conv = create_conversation(user_id=user_id, kb_id=kb_id)
    messages = []

    for i in range(turns):
        # User message
        messages.append(
            {
                "role": "user",
                "content": fake.paragraph(nb_sentences=2),
                "citations": [],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Assistant response with citations
        messages.append(
            {
                "role": "assistant",
                "content": fake.paragraph(nb_sentences=3),
                "citations": [
                    {
                        "source": fake.file_name(extension="md"),
                        "text": fake.sentence(),
                        "score": round(0.95 - (i * 0.02), 2),  # Decreasing scores
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    conv["messages"] = messages
    conv["title"] = f"Chat about {fake.word()} ({turns} turns)"
    return conv


def create_chat_message(
    role: str = "user",
    content: str | None = None,
    citations: list | None = None,
) -> dict:
    """Factory for individual chat messages.

    Args:
        role: Message role ("user" or "assistant")
        content: Message content (generated if not provided)
        citations: List of citation dicts (empty for user messages)

    Returns:
        dict: Chat message dictionary
    """
    return {
        "role": role,
        "content": content or fake.paragraph(nb_sentences=2),
        "citations": citations or ([] if role == "user" else []),
        "timestamp": datetime.utcnow().isoformat(),
    }
