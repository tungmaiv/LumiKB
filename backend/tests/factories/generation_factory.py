"""Generation request factories for document generation tests.

Provides factory functions for creating generation request data
for document generation integration tests.

Note: create_draft and create_draft_with_citations already exist
in draft_factory.py. This module provides the request factory only.

Usage:
    from tests.factories import create_generation_request

    # Basic generation request
    request = create_generation_request()

    # With specific template
    request = create_generation_request(template_id="rfp_response")
"""

from uuid import UUID, uuid4

from faker import Faker

fake = Faker()


def create_generation_request(
    kb_id: UUID | None = None,
    prompt: str | None = None,
    template_id: str | None = None,
    selected_sources: list | None = None,
    max_tokens: int | None = None,
    include_citations: bool = True,
) -> dict:
    """Factory for generation request data.

    Creates a dictionary representing a document generation request.
    Suitable for testing POST /api/v1/generate endpoint.

    Args:
        kb_id: Knowledge base UUID to generate from
        prompt: User prompt/instruction for generation
        template_id: Template identifier (e.g., "rfp_response", "summary")
        selected_sources: List of document IDs to use as sources
        max_tokens: Maximum tokens for generation (default: 2000)
        include_citations: Whether to include citations in output

    Returns:
        dict: Generation request payload ready for API submission
    """
    return {
        "kb_id": str(kb_id) if kb_id else str(uuid4()),
        "prompt": prompt or fake.paragraph(nb_sentences=3),
        "template_id": template_id or "general",
        "selected_sources": selected_sources or [],
        "max_tokens": max_tokens or 2000,
        "include_citations": include_citations,
    }


def create_template_request(
    template_id: str = "rfp_response",
    variables: dict | None = None,
) -> dict:
    """Factory for template-based generation request.

    Creates a request that uses a specific template with variables.

    Args:
        template_id: Template identifier
        variables: Template variable values

    Returns:
        dict: Template request payload
    """
    default_variables = {
        "company_name": fake.company(),
        "product_name": fake.word().capitalize(),
        "deadline": fake.date(),
    }

    return {
        "template_id": template_id,
        "variables": variables or default_variables,
    }


def create_streaming_generation_request(
    kb_id: UUID | None = None,
    prompt: str | None = None,
    template_id: str | None = None,
) -> dict:
    """Factory for SSE streaming generation request.

    Creates a request suitable for testing /api/v1/generate/stream endpoint.

    Args:
        kb_id: Knowledge base UUID
        prompt: Generation prompt
        template_id: Template to use

    Returns:
        dict: Streaming generation request payload
    """
    return {
        "kb_id": str(kb_id) if kb_id else str(uuid4()),
        "prompt": prompt or f"Generate a detailed analysis of {fake.word()}",
        "template_id": template_id or "general",
        "stream": True,
    }
