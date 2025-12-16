"""Integration tests for template API endpoints.

Story 4.9: Generation Templates
Tests AC-1 (API access to templates)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_get_templates_returns_all(client: AsyncClient, authenticated_headers: dict):
    """Test GET /api/v1/generate/templates returns all templates."""
    response = await client.get("/api/v1/generate/templates", cookies=authenticated_headers)

    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    assert len(data["templates"]) == 4

    # Verify all template IDs present
    template_ids = [t["id"] for t in data["templates"]]
    assert "rfp_response" in template_ids
    assert "checklist" in template_ids
    assert "gap_analysis" in template_ids
    assert "custom" in template_ids

    # Verify first template has all fields
    first_template = data["templates"][0]
    assert "id" in first_template
    assert "name" in first_template
    assert "description" in first_template
    assert "system_prompt" in first_template
    assert "sections" in first_template
    # example_output is optional


@pytest.mark.integration
async def test_get_template_by_id_success(client: AsyncClient, authenticated_headers: dict):
    """Test GET /api/v1/generate/templates/{id} returns specific template."""
    response = await client.get(
        "/api/v1/generate/templates/rfp_response", cookies=authenticated_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "rfp_response"
    assert data["name"] == "RFP Response Section"
    assert "Executive Summary" in data["sections"]
    assert "cite every claim" in data["system_prompt"].lower()
    assert data["example_output"] is not None


@pytest.mark.integration
async def test_get_template_not_found(client: AsyncClient, authenticated_headers: dict):
    """Test GET /api/v1/generate/templates/invalid_id returns 404."""
    response = await client.get(
        "/api/v1/generate/templates/invalid_id", cookies=authenticated_headers
    )

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.integration
async def test_get_templates_requires_authentication(client: AsyncClient):
    """Test GET /api/v1/generate/templates requires authentication."""
    # Request without auth header
    response = await client.get("/api/v1/generate/templates")

    assert response.status_code == 401
