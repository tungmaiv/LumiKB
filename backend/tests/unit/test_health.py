"""Health check endpoint tests."""

import pytest
from httpx import AsyncClient

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test health check endpoint returns healthy status."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Test API root endpoint."""
    response = await client.get("/api/v1/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
