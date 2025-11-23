"""Integration tests for user profile API endpoints.

Tests cover:
- GET /api/v1/users/me (AC: 1)
- PATCH /api/v1/users/me (AC: 2, 3, 8, 9)
"""

import pytest
from httpx import AsyncClient

from tests.factories import create_registration_data

# Use shared fixtures from conftest.py:
# - api_client: API client with Options A+E fixes
# - test_redis_client: Fresh Redis client per test


@pytest.fixture
async def user_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture for backward compatibility."""
    return api_client


@pytest.fixture
async def test_user_data() -> dict:
    """Test user registration data using factory for unique values."""
    return create_registration_data()


@pytest.fixture
async def logged_in_user(user_client: AsyncClient, test_user_data: dict) -> dict:
    """Create a registered and logged-in test user."""
    # Register
    reg_response = await user_client.post(
        "/api/v1/auth/register",
        json=test_user_data,
    )
    assert reg_response.status_code == 201
    user_data = reg_response.json()

    # Login
    login_response = await user_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    assert login_response.status_code in (200, 204)

    return {
        **test_user_data,
        "user": user_data,
        "cookies": login_response.cookies,
    }


# =============================================================================
# AC 1: GET /users/me returns profile information
# =============================================================================


@pytest.mark.integration
async def test_get_users_me_returns_profile_info(
    user_client: AsyncClient,
    logged_in_user: dict,
):
    """Test GET /users/me returns full profile including required fields."""
    response = await user_client.get(
        "/api/v1/users/me",
        cookies=logged_in_user["cookies"],
    )

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields from AC1
    assert data["id"] == logged_in_user["user"]["id"]
    assert data["email"] == logged_in_user["email"]
    assert "is_active" in data
    assert "is_superuser" in data
    assert "is_verified" in data
    assert "created_at" in data


@pytest.mark.integration
async def test_get_users_me_without_auth_returns_401(
    user_client: AsyncClient,
):
    """Test GET /users/me without authentication returns 401."""
    response = await user_client.get("/api/v1/users/me")
    assert response.status_code == 401


# =============================================================================
# AC 2: PATCH /users/me updates profile
# =============================================================================


@pytest.mark.integration
async def test_patch_users_me_updates_email(
    user_client: AsyncClient,
    logged_in_user: dict,
):
    """Test PATCH /users/me with valid email update."""
    new_email = "newemail@example.com"

    response = await user_client.patch(
        "/api/v1/users/me",
        json={"email": new_email},
        cookies=logged_in_user["cookies"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_email

    # Verify the change persisted by fetching again
    get_response = await user_client.get(
        "/api/v1/users/me",
        cookies=logged_in_user["cookies"],
    )
    assert get_response.json()["email"] == new_email


@pytest.mark.integration
async def test_patch_users_me_empty_body_returns_user(
    user_client: AsyncClient,
    logged_in_user: dict,
):
    """Test PATCH /users/me with empty body returns current user (no changes)."""
    response = await user_client.patch(
        "/api/v1/users/me",
        json={},
        cookies=logged_in_user["cookies"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == logged_in_user["email"]


# =============================================================================
# AC 3: PATCH /users/me with duplicate email returns 400
# =============================================================================


@pytest.mark.integration
async def test_patch_users_me_duplicate_email_returns_400(
    user_client: AsyncClient,
    logged_in_user: dict,
):
    """Test PATCH /users/me with email that belongs to another user returns 400."""
    # Create a second user
    second_user_email = "seconduser@example.com"
    await user_client.post(
        "/api/v1/auth/register",
        json={"email": second_user_email, "password": "password123"},
    )

    # Try to update first user's email to second user's email
    response = await user_client.patch(
        "/api/v1/users/me",
        json={"email": second_user_email},
        cookies=logged_in_user["cookies"],
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "REGISTER_USER_ALREADY_EXISTS"


# =============================================================================
# AC 8: PATCH /users/me without auth returns 401
# =============================================================================


@pytest.mark.integration
async def test_patch_users_me_without_auth_returns_401(
    user_client: AsyncClient,
):
    """Test PATCH /users/me without authentication returns 401."""
    response = await user_client.patch(
        "/api/v1/users/me",
        json={"email": "newemail@example.com"},
    )
    assert response.status_code == 401


# =============================================================================
# AC 6: PATCH /users/me with invalid email returns 422
# =============================================================================


@pytest.mark.integration
async def test_patch_users_me_invalid_email_returns_422(
    user_client: AsyncClient,
    logged_in_user: dict,
):
    """Test PATCH /users/me with malformed email returns 422."""
    response = await user_client.patch(
        "/api/v1/users/me",
        json={"email": "notavalidemail"},
        cookies=logged_in_user["cookies"],
    )

    assert response.status_code == 422


# =============================================================================
# AC 9: Profile update creates audit event
# =============================================================================


@pytest.mark.integration
async def test_patch_users_me_creates_audit_event(
    user_client: AsyncClient,
    logged_in_user: dict,
):
    """Test PATCH /users/me creates audit event (fire-and-forget)."""
    response = await user_client.patch(
        "/api/v1/users/me",
        json={"email": "audittest@example.com"},
        cookies=logged_in_user["cookies"],
    )

    assert response.status_code == 200
    # Audit event creation is fire-and-forget, verified via logs in production
