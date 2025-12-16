"""Draft factory with sensible defaults and explicit overrides.

Factory functions generate unique, parallel-safe test data using faker.
Override specific fields to make test intent explicit.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from faker import Faker

from app.models.draft import DraftStatus

fake = Faker()


def create_draft(**overrides: Any) -> dict:
    """Factory function for draft test data.

    Usage:
        draft = create_draft()  # All defaults
        editing = create_draft(status=DraftStatus.EDITING)  # Override status
        with_content = create_draft(content="# Test Draft\n\nContent [1]")

    Args:
        **overrides: Any field to override from defaults

    Returns:
        dict: Draft data matching Draft model schema
    """
    defaults = {
        "id": str(uuid.uuid4()),
        "kb_id": str(uuid.uuid4()),  # Must be overridden with valid KB ID
        "user_id": str(uuid.uuid4()),  # Must be overridden with valid user ID
        "title": fake.sentence(nb_words=4),
        "content": f"# {fake.sentence(nb_words=3)}\n\n{fake.paragraph(nb_sentences=3)}",
        "status": "complete",  # Use string value, not enum
        "citations": [],
        "word_count": fake.random_int(min=100, max=1000),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    # Apply overrides
    defaults.update(overrides)
    return defaults


def create_draft_with_citations(**overrides: Any) -> dict:
    """Factory for draft with pre-populated citations.

    Usage:
        draft = create_draft_with_citations()  # Default with 2 citations
        draft = create_draft_with_citations(citation_count=5)  # 5 citations

    Returns:
        dict: Draft with citations array populated
    """
    citation_count = overrides.pop("citation_count", 2)

    citations = []
    content_parts = ["# Authentication System\n\n"]

    for i in range(citation_count):
        citation_num = i + 1
        citation = create_citation(number=citation_num)
        citations.append(citation)

        # Add citation marker to content
        content_parts.append(
            f"The system uses OAuth 2.0 [{citation_num}] for authentication. "
        )

    content = "".join(content_parts)

    return create_draft(
        content=content,
        citations=citations,
        word_count=len(content.split()),
        **overrides,
    )


def create_citation(number: int = 1, **overrides: Any) -> dict:
    """Factory for citation metadata.

    Usage:
        citation = create_citation(number=1)
        citation = create_citation(number=2, page=14, confidence_score=0.95)

    Args:
        number: Citation number (e.g., 1 for [1])
        **overrides: Any field to override from defaults

    Returns:
        dict: Citation metadata
    """
    defaults = {
        "number": number,
        "document_id": str(uuid.uuid4()),
        "document_name": fake.file_name(extension="pdf"),
        "page": fake.random_int(min=1, max=50),
        "chunk_index": fake.random_int(min=0, max=100),
        "confidence_score": round(fake.random.uniform(0.7, 0.99), 2),
        "snippet": fake.sentence(nb_words=15),
    }

    defaults.update(overrides)
    return defaults


def create_draft_update_data(**overrides: Any) -> dict:
    """Factory for draft update API payload.

    Usage:
        data = create_draft_update_data()
        data = create_draft_update_data(content="New content", status="editing")

    Returns:
        dict: Draft update payload
    """
    defaults = {
        "content": fake.paragraph(nb_sentences=5),
        "citations": [],
        "status": "editing",
        "word_count": fake.random_int(min=100, max=500),
    }
    defaults.update(overrides)
    return defaults


def create_regenerate_request(**overrides: Any) -> dict:
    """Factory for section regeneration API payload.

    Usage:
        data = create_regenerate_request()
        data = create_regenerate_request(
            selected_text="OAuth 2.0 [1] is secure",
            instructions="Make it more technical",
            keep_citations=True
        )

    Returns:
        dict: Regeneration request payload
    """
    selected_text = fake.paragraph(nb_sentences=2)
    defaults = {
        "selected_text": selected_text,
        "instructions": fake.sentence(nb_words=8),
        "keep_citations": False,
        "selection_start": 0,
        "selection_end": len(selected_text),
    }
    defaults.update(overrides)
    return defaults
