"""Integration tests for onboarding API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestOnboardingAPI:
    """Test onboarding API endpoints."""

    async def test_get_user_me_returns_onboarding_fields(
        self, client: AsyncClient, authenticated_headers: dict
    ):
        """Test GET /api/v1/users/me includes onboarding_completed and last_active."""
        response = await client.get("/api/v1/users/me", cookies=authenticated_headers)

        assert response.status_code == 200
        data = response.json()
        assert "onboarding_completed" in data
        assert "last_active" in data
        assert isinstance(data["onboarding_completed"], bool)

    async def test_put_onboarding_authenticated_user_returns_200(
        self, client: AsyncClient, authenticated_headers: dict
    ):
        """Test PUT /api/v1/users/me/onboarding with authenticated user returns 200."""
        response = await client.put(
            "/api/v1/users/me/onboarding", cookies=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_completed"] is True

    async def test_put_onboarding_unauthenticated_returns_401(
        self, client: AsyncClient
    ):
        """Test PUT /api/v1/users/me/onboarding without auth returns 401."""
        response = await client.put("/api/v1/users/me/onboarding")

        assert response.status_code == 401

    async def test_onboarding_response_schema_validation(
        self, client: AsyncClient, authenticated_headers: dict
    ):
        """Test PUT /api/v1/users/me/onboarding returns valid UserRead schema."""
        response = await client.put(
            "/api/v1/users/me/onboarding", cookies=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify UserRead schema fields
        assert "id" in data
        assert "email" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "onboarding_completed" in data
        assert "last_active" in data

    async def test_onboarding_database_persistence(
        self, client: AsyncClient, authenticated_headers: dict
    ):
        """Test onboarding_completed field persists in database."""
        # Mark onboarding complete
        response = await client.put(
            "/api/v1/users/me/onboarding", cookies=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["onboarding_completed"] is True

        # Verify persistence by fetching user again
        response = await client.get("/api/v1/users/me", cookies=authenticated_headers)
        assert response.status_code == 200
        assert response.json()["onboarding_completed"] is True

    async def test_onboarding_idempotency(
        self, client: AsyncClient, authenticated_headers: dict
    ):
        """Test calling PUT /api/v1/users/me/onboarding multiple times is safe."""
        # Call endpoint first time
        response1 = await client.put(
            "/api/v1/users/me/onboarding", cookies=authenticated_headers
        )
        assert response1.status_code == 200
        assert response1.json()["onboarding_completed"] is True

        # Call endpoint second time (idempotent)
        response2 = await client.put(
            "/api/v1/users/me/onboarding", cookies=authenticated_headers
        )
        assert response2.status_code == 200
        assert response2.json()["onboarding_completed"] is True

        # Should be safe to call multiple times
        response3 = await client.put(
            "/api/v1/users/me/onboarding", cookies=authenticated_headers
        )
        assert response3.status_code == 200
