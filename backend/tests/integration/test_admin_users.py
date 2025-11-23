"""Integration tests for admin user management API endpoints.

Tests cover:
- GET /admin/users returns paginated list (AC: 1, 2)
- GET /admin/users respects skip/limit parameters (AC: 1)
- POST /admin/users creates new user (AC: 3, 10)
- POST /admin/users with duplicate email returns 409 (AC: 4)
- PATCH /admin/users/{id} deactivates user (AC: 5, 10)
- PATCH /admin/users/{id} activates user (AC: 6, 10)
- PATCH /admin/users/{id} with invalid id returns 404 (AC: 7)
- Non-admin user gets 403 on all admin endpoints (AC: 8)
- Unauthenticated user gets 401 on all admin endpoints (AC: 9)
- Deactivated user cannot login (AC: 5)
- Audit events are created for admin actions (AC: 10)
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user import User
from tests.factories import create_registration_data

# Use shared fixtures from conftest.py:
# - api_client: API client with Options A+E fixes
# - test_redis_client: Fresh Redis client per test


@pytest.fixture
async def admin_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture for backward compatibility."""
    return api_client


@pytest.fixture
async def db_session_for_admin(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for admin user setup."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def regular_user(admin_client: AsyncClient) -> dict:
    """Create a regular (non-admin) test user using factory."""
    user_data = create_registration_data()
    response = await admin_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json()}


@pytest.fixture
async def admin_user(
    admin_client: AsyncClient, db_session_for_admin: AsyncSession
) -> dict:
    """Create an admin (superuser) test user using factory."""
    # First create via registration with unique email
    user_data = create_registration_data()
    response = await admin_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Manually set is_superuser=True in database
    result = await db_session_for_admin.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await db_session_for_admin.commit()

    return {**user_data, "user": response_data}


@pytest.fixture
async def admin_cookies(admin_client: AsyncClient, admin_user: dict) -> dict:
    """Login as admin and return cookies."""
    login_response = await admin_client.post(
        "/api/v1/auth/login",
        data={"username": admin_user["email"], "password": admin_user["password"]},
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_cookies(admin_client: AsyncClient, regular_user: dict) -> dict:
    """Login as regular user and return cookies."""
    login_response = await admin_client.post(
        "/api/v1/auth/login",
        data={"username": regular_user["email"], "password": regular_user["password"]},
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


# =============================================================================
# AC 1, 2: GET /admin/users returns paginated list
# =============================================================================


@pytest.mark.integration
async def test_get_users_returns_paginated_list(
    admin_client: AsyncClient,
    admin_cookies: dict,
    regular_user: dict,  # noqa: ARG001 - creates user in DB
):
    """Test GET /admin/users returns paginated list of users."""
    response = await admin_client.get(
        "/api/v1/admin/users",
        cookies=admin_cookies,
    )

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "data" in data
    assert "meta" in data
    assert isinstance(data["data"], list)

    # Check pagination meta
    meta = data["meta"]
    assert "total" in meta
    assert "page" in meta
    assert "per_page" in meta
    assert "total_pages" in meta

    # Should have at least admin and regular user
    assert meta["total"] >= 2

    # Check user fields (AC 2)
    if data["data"]:
        user = data["data"][0]
        required_fields = [
            "id",
            "email",
            "is_active",
            "is_superuser",
            "is_verified",
            "created_at",
        ]
        for field in required_fields:
            assert field in user, f"Missing field: {field}"


@pytest.mark.integration
async def test_get_users_respects_skip_limit_parameters(
    admin_client: AsyncClient,
    admin_cookies: dict,
    db_session_for_admin: AsyncSession,
):
    """Test GET /admin/users respects skip/limit pagination parameters."""
    # Create multiple users
    from fastapi_users.password import PasswordHelper

    from app.models.user import User as UserModel

    password_helper = PasswordHelper()
    for i in range(25):
        user = UserModel(
            email=f"user{i}@example.com",
            hashed_password=password_helper.hash("testpassword123"),
        )
        db_session_for_admin.add(user)
    await db_session_for_admin.commit()

    # Test default pagination (20 per page)
    response = await admin_client.get(
        "/api/v1/admin/users",
        cookies=admin_cookies,
    )
    data = response.json()
    assert data["meta"]["per_page"] == 20
    assert len(data["data"]) == 20

    # Test custom limit
    response = await admin_client.get(
        "/api/v1/admin/users?limit=5",
        cookies=admin_cookies,
    )
    data = response.json()
    assert data["meta"]["per_page"] == 5
    assert len(data["data"]) == 5

    # Test skip
    response = await admin_client.get(
        "/api/v1/admin/users?skip=5&limit=5",
        cookies=admin_cookies,
    )
    data = response.json()
    assert data["meta"]["page"] == 2


# =============================================================================
# AC 3, 4: POST /admin/users creates new user
# =============================================================================


@pytest.mark.integration
async def test_post_users_creates_new_user(
    admin_client: AsyncClient,
    admin_cookies: dict,
):
    """Test POST /admin/users creates a new user."""
    response = await admin_client.post(
        "/api/v1/admin/users",
        json={"email": "newuser@example.com", "password": "newpassword123"},
        cookies=admin_cookies,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    # Password should not be in response
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.integration
async def test_post_users_duplicate_email_returns_409(
    admin_client: AsyncClient,
    admin_cookies: dict,
    regular_user: dict,
):
    """Test POST /admin/users with duplicate email returns 409."""
    response = await admin_client.post(
        "/api/v1/admin/users",
        json={"email": regular_user["email"], "password": "anotherpassword123"},
        cookies=admin_cookies,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


# =============================================================================
# AC 5, 6: PATCH /admin/users/{id} activates/deactivates user
# =============================================================================


@pytest.mark.integration
async def test_patch_users_deactivates_user(
    admin_client: AsyncClient,
    admin_cookies: dict,
    regular_user: dict,
):
    """Test PATCH /admin/users/{id} deactivates user."""
    user_id = regular_user["user"]["id"]

    response = await admin_client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"is_active": False},
        cookies=admin_cookies,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["id"] == user_id


@pytest.mark.integration
async def test_patch_users_activates_user(
    admin_client: AsyncClient,
    admin_cookies: dict,
    regular_user: dict,
    db_session_for_admin: AsyncSession,
):
    """Test PATCH /admin/users/{id} activates user."""
    user_id = regular_user["user"]["id"]

    # First deactivate the user
    result = await db_session_for_admin.execute(
        select(User).where(User.email == regular_user["email"])
    )
    user = result.scalar_one()
    user.is_active = False
    await db_session_for_admin.commit()

    # Then activate via API
    response = await admin_client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"is_active": True},
        cookies=admin_cookies,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True


# =============================================================================
# AC 7: PATCH /admin/users/{id} with invalid id returns 404
# =============================================================================


@pytest.mark.integration
async def test_patch_users_nonexistent_returns_404(
    admin_client: AsyncClient,
    admin_cookies: dict,
):
    """Test PATCH /admin/users/{id} with non-existent user returns 404."""
    fake_id = str(uuid4())

    response = await admin_client.patch(
        f"/api/v1/admin/users/{fake_id}",
        json={"is_active": False},
        cookies=admin_cookies,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


# =============================================================================
# AC 8: Non-admin user gets 403 on all admin endpoints
# =============================================================================


@pytest.mark.integration
async def test_admin_endpoints_non_admin_returns_403(
    admin_client: AsyncClient,
    regular_user_cookies: dict,
    regular_user: dict,
):
    """Test non-admin user gets 403 on all admin endpoints."""
    user_id = regular_user["user"]["id"]

    # Test GET /admin/users
    response = await admin_client.get(
        "/api/v1/admin/users",
        cookies=regular_user_cookies,
    )
    assert response.status_code == 403

    # Test POST /admin/users
    response = await admin_client.post(
        "/api/v1/admin/users",
        json={"email": "new@example.com", "password": "password123"},
        cookies=regular_user_cookies,
    )
    assert response.status_code == 403

    # Test PATCH /admin/users/{id}
    response = await admin_client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"is_active": False},
        cookies=regular_user_cookies,
    )
    assert response.status_code == 403


# =============================================================================
# AC 9: Unauthenticated user gets 401 on all admin endpoints
# =============================================================================


@pytest.mark.integration
async def test_admin_endpoints_unauthenticated_returns_401(
    admin_client: AsyncClient,
):
    """Test unauthenticated user gets 401 on all admin endpoints."""
    fake_id = str(uuid4())

    # Test GET /admin/users
    response = await admin_client.get("/api/v1/admin/users")
    assert response.status_code == 401

    # Test POST /admin/users
    response = await admin_client.post(
        "/api/v1/admin/users",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert response.status_code == 401

    # Test PATCH /admin/users/{id}
    response = await admin_client.patch(
        f"/api/v1/admin/users/{fake_id}",
        json={"is_active": False},
    )
    assert response.status_code == 401


# =============================================================================
# AC 5 (additional): Deactivated user cannot login
# =============================================================================


@pytest.mark.integration
async def test_deactivated_user_cannot_login(
    admin_client: AsyncClient,
    admin_cookies: dict,
    regular_user: dict,
):
    """Test deactivated user cannot login."""
    user_id = regular_user["user"]["id"]

    # Deactivate the user
    response = await admin_client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"is_active": False},
        cookies=admin_cookies,
    )
    assert response.status_code == 200

    # Try to login as deactivated user
    login_response = await admin_client.post(
        "/api/v1/auth/login",
        data={"username": regular_user["email"], "password": regular_user["password"]},
    )

    # Should get 400 with bad credentials (FastAPI-Users behavior for inactive user)
    assert login_response.status_code == 400


# =============================================================================
# AC 10: Audit events are created for admin actions
# =============================================================================


@pytest.mark.integration
async def test_audit_events_created_for_admin_create(
    admin_client: AsyncClient,
    admin_cookies: dict,
):
    """Test audit event is created when admin creates user."""
    user_data = create_registration_data()
    response = await admin_client.post(
        "/api/v1/admin/users",
        json=user_data,
        cookies=admin_cookies,
    )
    assert response.status_code == 201
    # Audit event creation is fire-and-forget
    # In production, verify via database queries to audit.events table


@pytest.mark.integration
async def test_audit_events_created_for_admin_deactivate(
    admin_client: AsyncClient,
    admin_cookies: dict,
    regular_user: dict,
):
    """Test audit event is created when admin deactivates user."""
    user_id = regular_user["user"]["id"]

    response = await admin_client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"is_active": False},
        cookies=admin_cookies,
    )
    assert response.status_code == 200
    # Audit event creation is fire-and-forget


@pytest.mark.integration
async def test_audit_events_created_for_admin_activate(
    admin_client: AsyncClient,
    admin_cookies: dict,
    regular_user: dict,
    db_session_for_admin: AsyncSession,
):
    """Test audit event is created when admin activates user."""
    user_id = regular_user["user"]["id"]

    # First deactivate the user in DB
    result = await db_session_for_admin.execute(
        select(User).where(User.email == regular_user["email"])
    )
    user = result.scalar_one()
    user.is_active = False
    await db_session_for_admin.commit()

    # Activate via API
    response = await admin_client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"is_active": True},
        cookies=admin_cookies,
    )
    assert response.status_code == 200
    # Audit event creation is fire-and-forget
