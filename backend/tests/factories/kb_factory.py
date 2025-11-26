"""Knowledge Base factory with sensible defaults.

Factory functions generate unique, parallel-safe KB test data using faker.
"""

import uuid
from typing import TYPE_CHECKING, Any

from faker import Faker

from app.models.knowledge_base import KnowledgeBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

fake = Faker()


def create_kb_data(**overrides: Any) -> dict:
    """Factory function for KB creation API payload.

    Usage:
        kb = create_kb_data()  # All defaults
        named_kb = create_kb_data(name="My KB")

    Args:
        **overrides: Any field to override from defaults

    Returns:
        dict: KB creation payload matching KBCreate schema
    """
    defaults = {
        "name": f"KB-{fake.word()}-{uuid.uuid4().hex[:6]}",
        "description": fake.sentence(),
    }

    defaults.update(overrides)
    return defaults


def create_kb_update_data(**overrides: Any) -> dict:
    """Factory function for KB update API payload.

    Usage:
        update = create_kb_update_data()  # Random name and description
        name_only = create_kb_update_data(description=None)  # Only update name

    Returns:
        dict: KB update payload matching KBUpdate schema
    """
    defaults = {
        "name": f"Updated-{fake.word()}",
        "description": fake.sentence(),
    }

    defaults.update(overrides)
    # Remove None values to allow partial updates
    return {k: v for k, v in defaults.items() if v is not None}


async def create_knowledge_base(
    session: "AsyncSession",
    **overrides: Any,
) -> KnowledgeBase:
    """Create a KB record in the database.

    Args:
        session: Database session.
        **overrides: Any field to override from defaults.

    Returns:
        KnowledgeBase: Created KB instance.
    """
    data = create_kb_data(**overrides)

    # Add model-specific defaults
    defaults = {
        "id": uuid.uuid4(),
        "status": "active",
    }
    defaults.update(data)

    kb = KnowledgeBase(**defaults)
    session.add(kb)
    await session.flush()
    return kb
