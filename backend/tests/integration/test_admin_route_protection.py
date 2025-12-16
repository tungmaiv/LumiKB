"""Integration tests for admin route protection (AC-5.17.3).

Verifies that all admin endpoints:
- Return 403 Forbidden for non-admin users
- Return 401 Unauthorized for unauthenticated users
- Return 200 OK for admin users

Story 5.17: Main Application Navigation Menu
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user import User
from tests.factories import create_registration_data


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
async def admin_user_for_protection(
    api_client: AsyncClient, db_session_for_admin: AsyncSession
) -> dict:
    """Create an admin test user."""
    user_data = create_registration_data()
    response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Set is_superuser=True in database
    result = await db_session_for_admin.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await db_session_for_admin.commit()

    return {**user_data, "user": response_data}


@pytest.fixture
async def admin_cookies(
    api_client: AsyncClient, admin_user_for_protection: dict
) -> dict:
    """Login as admin and return cookies."""
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user_for_protection["email"],
            "password": admin_user_for_protection["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_for_protection(api_client: AsyncClient) -> dict:
    """Create a regular (non-admin) test user."""
    user_data = create_registration_data()
    response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json()}


@pytest.fixture
async def regular_cookies(
    api_client: AsyncClient, regular_user_for_protection: dict
) -> dict:
    """Login as regular user and return cookies."""
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": regular_user_for_protection["email"],
            "password": regular_user_for_protection["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


# List of admin endpoints to test
# Format: (method, path, description)
ADMIN_ENDPOINTS = [
    ("GET", "/api/v1/admin/stats", "Admin Dashboard Stats"),
    ("GET", "/api/v1/admin/users", "List Users"),
    ("GET", "/api/v1/admin/outbox/stats", "Outbox Stats"),
    ("GET", "/api/v1/admin/audit/generation", "Generation Audit Logs"),
    ("POST", "/api/v1/admin/audit/logs", "Query Audit Logs"),
    ("GET", "/api/v1/admin/queue/status", "Queue Status"),
    ("GET", "/api/v1/admin/config", "System Config"),
    ("GET", "/api/v1/admin/config/restart-required", "Restart Required Settings"),
]


class TestAdminRouteProtection:
    """Test suite for admin route protection (AC-5.17.3)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,path,description", ADMIN_ENDPOINTS)
    async def test_unauthenticated_returns_401(
        self,
        api_client: AsyncClient,
        method: str,
        path: str,
        description: str,
    ):
        """Test unauthenticated requests return 401 Unauthorized."""
        if method == "GET":
            response = await api_client.get(path)
        elif method == "POST":
            response = await api_client.post(path, json={})
        else:
            pytest.fail(f"Unsupported method: {method}")

        assert (
            response.status_code == status.HTTP_401_UNAUTHORIZED
        ), f"{description} ({path}): Expected 401, got {response.status_code}"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,path,description", ADMIN_ENDPOINTS)
    async def test_non_admin_returns_403(
        self,
        api_client: AsyncClient,
        regular_cookies: dict,
        method: str,
        path: str,
        description: str,
    ):
        """Test non-admin users receive 403 Forbidden on admin endpoints."""
        if method == "GET":
            response = await api_client.get(path, cookies=regular_cookies)
        elif method == "POST":
            response = await api_client.post(path, json={}, cookies=regular_cookies)
        else:
            pytest.fail(f"Unsupported method: {method}")

        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), f"{description} ({path}): Expected 403, got {response.status_code}"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method,path,description",
        [
            ("GET", "/api/v1/admin/stats", "Admin Dashboard Stats"),
            ("GET", "/api/v1/admin/users", "List Users"),
            ("GET", "/api/v1/admin/outbox/stats", "Outbox Stats"),
            ("GET", "/api/v1/admin/queue/status", "Queue Status"),
            ("GET", "/api/v1/admin/config", "System Config"),
            (
                "GET",
                "/api/v1/admin/config/restart-required",
                "Restart Required Settings",
            ),
        ],
    )
    async def test_admin_returns_200(
        self,
        api_client: AsyncClient,
        admin_cookies: dict,
        method: str,
        path: str,
        description: str,
    ):
        """Test admin users receive 200 OK on admin endpoints."""
        if method == "GET":
            response = await api_client.get(path, cookies=admin_cookies)
        else:
            pytest.fail(f"Unsupported method: {method}")

        assert response.status_code == status.HTTP_200_OK, (
            f"{description} ({path}): Expected 200, got {response.status_code}. "
            f"Response: {response.text[:200]}"
        )


class TestAdminAuditEndpoints:
    """Test admin audit endpoints with proper request bodies."""

    @pytest.mark.asyncio
    async def test_audit_logs_non_admin_403(
        self, api_client: AsyncClient, regular_cookies: dict
    ):
        """Test POST /api/v1/admin/audit/logs returns 403 for non-admin."""
        response = await api_client.post(
            "/api/v1/admin/audit/logs",
            json={"page": 1, "page_size": 10},
            cookies=regular_cookies,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_audit_logs_admin_200(
        self, api_client: AsyncClient, admin_cookies: dict
    ):
        """Test POST /api/v1/admin/audit/logs returns 200 for admin."""
        response = await api_client.post(
            "/api/v1/admin/audit/logs",
            json={"page": 1, "page_size": 10},
            cookies=admin_cookies,
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_audit_export_non_admin_403(
        self, api_client: AsyncClient, regular_cookies: dict
    ):
        """Test POST /api/v1/admin/audit/export returns 403 for non-admin."""
        response = await api_client.post(
            "/api/v1/admin/audit/export",
            json={"format": "csv", "filters": {}},
            cookies=regular_cookies,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_audit_export_admin_200(
        self, api_client: AsyncClient, admin_cookies: dict
    ):
        """Test POST /api/v1/admin/audit/export returns 200 for admin."""
        response = await api_client.post(
            "/api/v1/admin/audit/export",
            json={"format": "csv", "filters": {}},
            cookies=admin_cookies,
        )
        assert response.status_code == status.HTTP_200_OK


class TestAdminQueueEndpoints:
    """Test admin queue endpoints."""

    @pytest.mark.asyncio
    async def test_queue_tasks_non_admin_403(
        self, api_client: AsyncClient, regular_cookies: dict
    ):
        """Test GET /api/v1/admin/queue/{name}/tasks returns 403 for non-admin."""
        response = await api_client.get(
            "/api/v1/admin/queue/default/tasks",
            cookies=regular_cookies,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_queue_tasks_admin_200(
        self, api_client: AsyncClient, admin_cookies: dict
    ):
        """Test GET /api/v1/admin/queue/{name}/tasks returns 200 for admin."""
        response = await api_client.get(
            "/api/v1/admin/queue/default/tasks",
            cookies=admin_cookies,
        )
        assert response.status_code == status.HTTP_200_OK
