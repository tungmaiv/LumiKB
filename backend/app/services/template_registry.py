"""Template registry for document generation.

This module provides hardcoded template constants for common document types.
Templates are server-side only and cannot be modified by users.

Story 4.9: Generation Templates
"""

from typing import Optional

from pydantic import BaseModel


class Template(BaseModel):
    """Template configuration for document generation."""

    id: str
    name: str
    description: str
    system_prompt: str
    sections: list[str]
    example_output: Optional[str] = None


TEMPLATES: dict[str, Template] = {
    "rfp_response": Template(
        id="rfp_response",
        name="RFP Response Section",
        description="Generate a structured RFP response with executive summary and technical approach",
        system_prompt="""You are an expert proposal writer for Banking & Financial Services clients.

Generate a professional RFP response section using the provided sources.
Structure your response with these sections:

## Executive Summary
Brief overview (2-3 paragraphs) highlighting key capabilities

## Technical Approach
Detailed technical solution description with implementation details

## Relevant Experience
Past project examples from sources demonstrating similar successful implementations

## Pricing Considerations
Placeholder section for pricing team to complete

CRITICAL RULES:
- Cite every claim using [1], [2] format referencing the provided sources
- Never make uncited claims
- Maintain professional tone appropriate for banking clients
- Use specific examples and technical details from sources
- If information is not in sources, state "Information not available in provided sources"
""",
        sections=[
            "Executive Summary",
            "Technical Approach",
            "Relevant Experience",
            "Pricing",
        ],
        example_output="## Executive Summary\n\nOur authentication solution leverages OAuth 2.0 [1] with industry-standard security practices...",
    ),
    "checklist": Template(
        id="checklist",
        name="Technical Checklist",
        description="Create a requirement checklist from sources",
        system_prompt="""Generate a technical requirement checklist based on the provided sources.

Format each item as:
- [ ] **Requirement**: Description [citation]
  - **Status**: To be assessed
  - **Notes**: Additional context from sources

Group related requirements under ## headings (e.g., ## Authentication Requirements).
Cite the source for each requirement using [1], [2] format.

CRITICAL RULES:
- Every requirement must be cited from sources
- Use clear, actionable requirement language
- Group by logical categories
- Include technical details in Notes
- Never include requirements not found in sources
""",
        sections=["Requirements List"],
        example_output='## Authentication Requirements\n\n- [ ] **OAuth 2.0 Support**: System must support OAuth 2.0 authentication flow [1]\n  - **Status**: To be assessed\n  - **Notes**: PKCE extension required for mobile clients [1]',
    ),
    "gap_analysis": Template(
        id="gap_analysis",
        name="Gap Analysis",
        description="Compare requirements against current capabilities",
        system_prompt="""Generate a gap analysis table comparing requirements to current state.

Use this markdown table format:

| Requirement | Current State | Gap | Recommendation | Source |
|-------------|---------------|-----|----------------|--------|
| OAuth 2.0 | Partial implementation | Missing PKCE flow | Implement PKCE extension | [1] |

CRITICAL RULES:
- Every row must cite sources in the Source column using [1], [2] format
- Base "Current State" on information from sources (if available)
- Identify specific, actionable gaps
- Provide concrete recommendations
- Prioritize high-impact gaps first
- If current state not in sources, use "To be assessed"
""",
        sections=["Gap Analysis Table"],
        example_output="| Requirement | Current State | Gap | Recommendation | Source |\n|---|---|---|---|---|\n| OAuth 2.0 compliance | Partial | PKCE flow missing | Implement RFC 7636 PKCE | [1] |",
    ),
    "custom": Template(
        id="custom",
        name="Custom Prompt",
        description="Generate content based on your own instructions",
        system_prompt="""Generate content based on the user's custom instructions using the provided sources.

CRITICAL RULES:
- Use the provided sources to support your response
- Maintain professional tone appropriate for Banking & Financial Services
- Always cite sources using [1], [2] format
- Never make claims without citations
- If information is not in sources, explicitly state this
- Follow the user's formatting and structure instructions while maintaining citation requirements
""",
        sections=[],
        example_output=None,
    ),
}


def get_template(template_id: str) -> Template:
    """Retrieve a template by ID.

    Args:
        template_id: The unique identifier for the template

    Returns:
        Template configuration

    Raises:
        ValueError: If template_id is not found in TEMPLATES
    """
    if template_id not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_id}")
    return TEMPLATES[template_id]


def list_templates() -> list[Template]:
    """List all available templates.

    Returns:
        List of all template configurations
    """
    return list(TEMPLATES.values())
