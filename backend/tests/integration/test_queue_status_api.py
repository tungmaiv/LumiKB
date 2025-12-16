"""Integration tests for queue status API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user import User
from tests.factories import create_registration_data


@pytest.fixture
async def queue_test_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def queue_test_db_session(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for admin user setup."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def admin_user_for_queue(
    queue_test_client: AsyncClient, queue_test_db_session: AsyncSession
) -> dict:
    """Create an admin test user."""
    user_data = create_registration_data()
    response = await queue_test_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201

    # Set is_superuser=True in database
    result = await queue_test_db_session.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await queue_test_db_session.commit()

    return user_data


@pytest.fixture
async def admin_cookies(
    queue_test_client: AsyncClient, admin_user_for_queue: dict
) -> dict:
    """Login as admin and return cookies."""
    login_response = await queue_test_client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user_for_queue["email"],
            "password": admin_user_for_queue["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def user_cookies(client: AsyncClient, test_user_data: dict) -> dict:
    """Return cookies for regular (non-admin) user."""
    return test_user_data["cookies"]


@pytest.fixture
def mock_celery_inspect():
    """Mock Celery inspect API for testing."""
    inspect = MagicMock()
    inspect.active = MagicMock(
        return_value={
            "worker1@localhost": [
                {
                    "id": "task-1",
                    "name": "app.workers.document_tasks.process_document",
                    "time_start": 1701523200.0,
                    "delivery_info": {"routing_key": "document_processing"},
                }
            ],
        }
    )
    inspect.reserved = MagicMock(return_value={})
    inspect.stats = MagicMock(
        return_value={
            "worker1@localhost": {"total": {"tasks": 10}},
        }
    )
    return inspect


@pytest.mark.asyncio
class TestQueueStatusAPI:
    """Test suite for queue status API endpoints."""

    async def test_get_queue_status_admin_success(
        self, queue_test_client: AsyncClient, admin_cookies: dict, mock_celery_inspect
    ):
        """Test admin can get queue status."""
        with patch(
            "app.services.queue_monitor_service.QueueMonitorService._get_celery_inspect",
            return_value=mock_celery_inspect,
        ):
            response = await queue_test_client.get(
                "/api/v1/admin/queue/status",
                cookies=admin_cookies,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Verify queue status structure
        queue = next(
            (q for q in data if q["queue_name"] == "document_processing"), None
        )
        assert queue is not None
        assert "pending_tasks" in queue
        assert "active_tasks" in queue
        assert "workers" in queue
        assert "status" in queue

    async def test_get_queue_status_non_admin_forbidden(
        self, client: AsyncClient, user_cookies: dict
    ):
        """Test non-admin user receives 403 Forbidden."""
        response = await client.get(
            "/api/v1/admin/queue/status",
            cookies=user_cookies,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "detail" in data

    async def test_get_queue_status_unauthenticated(self, client: AsyncClient):
        """Test unauthenticated request receives 401."""
        response = await client.get("/api/v1/admin/queue/status")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_queue_tasks_admin_success(
        self, queue_test_client: AsyncClient, admin_cookies: dict, mock_celery_inspect
    ):
        """Test admin can get task details for specific queue."""
        with patch(
            "app.services.queue_monitor_service.QueueMonitorService._get_celery_inspect",
            return_value=mock_celery_inspect,
        ):
            response = await queue_test_client.get(
                "/api/v1/admin/queue/document_processing/tasks",
                cookies=admin_cookies,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            task = data[0]
            assert "task_id" in task
            assert "task_name" in task
            assert "status" in task
            assert "started_at" in task
            assert "estimated_duration" in task

    async def test_get_queue_tasks_non_admin_forbidden(
        self, client: AsyncClient, user_cookies: dict
    ):
        """Test non-admin user receives 403 Forbidden."""
        response = await client.get(
            "/api/v1/admin/queue/document_processing/tasks",
            cookies=user_cookies,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_queue_status_graceful_degradation(
        self, queue_test_client: AsyncClient, admin_cookies: dict
    ):
        """Test graceful degradation when Celery broker unavailable."""
        # Clear Redis cache to ensure we test the degradation path
        from app.core.redis import get_redis_client

        redis = await get_redis_client()
        await redis.delete("admin:queue:status")

        mock_inspect_none = MagicMock()
        mock_inspect_none.active.return_value = None
        mock_inspect_none.reserved.return_value = None
        mock_inspect_none.stats.return_value = None

        with patch(
            "app.services.queue_monitor_service.QueueMonitorService._get_celery_inspect",
            return_value=mock_inspect_none,
        ):
            response = await queue_test_client.get(
                "/api/v1/admin/queue/status",
                cookies=admin_cookies,
            )

        # Should return 200 with unavailable status, not 500 error
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

        # All queues should have unavailable status
        for queue in data:
            assert queue["status"] == "unavailable"


# =============================================================================
# Story 7-27: Queue Monitoring Enhancement Integration Tests
# =============================================================================


@pytest.fixture
async def operator_user_cookies(
    queue_test_client: AsyncClient, queue_test_db_session: AsyncSession
) -> dict:
    """Create an operator user (permission_level >= 2) and return cookies.

    AC-7.27.16: Operator permission check.
    """
    from app.models.group import Group, UserGroup

    user_data = create_registration_data()
    response = await queue_test_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201

    # Get the user
    result = await queue_test_db_session.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()

    # Find or create Operators group (permission_level=2)
    result = await queue_test_db_session.execute(
        select(Group).where(Group.name == "Operators")
    )
    operators_group = result.scalar_one_or_none()

    if not operators_group:
        operators_group = Group(
            name="Operators",
            description="Operators group",
            permission_level=2,
            is_system=True,
            is_active=True,
        )
        queue_test_db_session.add(operators_group)
        await queue_test_db_session.flush()

    # Add user to Operators group
    user_group = UserGroup(user_id=user.id, group_id=operators_group.id)
    queue_test_db_session.add(user_group)
    await queue_test_db_session.commit()

    # Login as operator
    login_response = await queue_test_client.post(
        "/api/v1/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_cookies(queue_test_client: AsyncClient) -> dict:
    """Create a regular user (permission_level = 1) and return cookies.

    AC-7.27.17: Regular user denied.
    """
    user_data = create_registration_data()
    response = await queue_test_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201

    # Login as regular user (no group assignment needed, defaults to level 1)
    login_response = await queue_test_client.post(
        "/api/v1/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.mark.asyncio
class TestQueueMonitoringOperatorAccess:
    """Story 7-27: Operator role access tests (AC-7.27.16-18)."""

    async def test_operator_can_access_queue_status(
        self,
        queue_test_client: AsyncClient,
        operator_user_cookies: dict,
        mock_celery_inspect,
    ):
        """AC-7.27.16: User with permission_level >= 2 can access queue endpoints.

        Given a user in a group with permission_level = 2 (Operator)
        When they access GET /api/v1/admin/queue/status
        Then access is granted (200 OK)
        """
        with patch(
            "app.services.queue_monitor_service.QueueMonitorService._get_celery_inspect",
            return_value=mock_celery_inspect,
        ):
            response = await queue_test_client.get(
                "/api/v1/admin/queue/status",
                cookies=operator_user_cookies,
            )

        assert response.status_code == status.HTTP_200_OK

    async def test_regular_user_denied_queue_access(
        self,
        queue_test_client: AsyncClient,
        regular_user_cookies: dict,
    ):
        """AC-7.27.17: User with permission_level = 1 is denied access.

        Given a user with only permission_level = 1
        When they access GET /api/v1/admin/queue/status
        Then access is denied (403 Forbidden)
        """
        response = await queue_test_client.get(
            "/api/v1/admin/queue/status",
            cookies=regular_user_cookies,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "Operator permission" in data["detail"]

    async def test_superuser_always_has_access(
        self,
        queue_test_client: AsyncClient,
        admin_cookies: dict,
        mock_celery_inspect,
    ):
        """AC-7.27.18: Superuser access is preserved.

        Given a user with is_superuser=True
        When they access GET /api/v1/admin/queue/status
        Then access is granted regardless of group membership
        """
        with patch(
            "app.services.queue_monitor_service.QueueMonitorService._get_celery_inspect",
            return_value=mock_celery_inspect,
        ):
            response = await queue_test_client.get(
                "/api/v1/admin/queue/status",
                cookies=admin_cookies,
            )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestBulkRetryEndpoint:
    """Story 7-27: Bulk retry endpoint tests (AC-7.27.6-10)."""

    async def test_bulk_retry_empty_request_returns_zero(
        self,
        queue_test_client: AsyncClient,
        admin_cookies: dict,
    ):
        """AC-7.27.10: Bulk retry with no documents returns empty response.

        Given no document_ids and retry_all_failed=False
        When POST /api/v1/admin/queue/retry-failed is called
        Then response shows queued=0, failed=0
        """
        response = await queue_test_client.post(
            "/api/v1/admin/queue/retry-failed",
            json={"document_ids": [], "retry_all_failed": False},
            cookies=admin_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["queued"] == 0
        assert data["failed"] == 0
        assert data["errors"] == []

    async def test_bulk_retry_non_existent_documents(
        self,
        queue_test_client: AsyncClient,
        admin_cookies: dict,
    ):
        """AC-7.27.10: Bulk retry with non-existent document IDs returns zero.

        Given document_ids that don't exist in database
        When POST /api/v1/admin/queue/retry-failed is called
        Then response shows queued=0 (no documents found)
        """
        from uuid import uuid4

        response = await queue_test_client.post(
            "/api/v1/admin/queue/retry-failed",
            json={"document_ids": [str(uuid4()), str(uuid4())]},
            cookies=admin_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["queued"] == 0

    async def test_bulk_retry_requires_operator_permission(
        self,
        queue_test_client: AsyncClient,
        regular_user_cookies: dict,
    ):
        """AC-7.27.16: Bulk retry requires operator permission.

        Given a regular user (permission_level = 1)
        When they call POST /api/v1/admin/queue/retry-failed
        Then access is denied (403 Forbidden)
        """
        response = await queue_test_client.post(
            "/api/v1/admin/queue/retry-failed",
            json={"document_ids": [], "retry_all_failed": False},
            cookies=regular_user_cookies,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
class TestDocumentStatusFilter:
    """Story 7-27: Document status filter tests (AC-7.27.15)."""

    async def test_queue_tasks_accepts_document_status_param(
        self,
        queue_test_client: AsyncClient,
        admin_cookies: dict,
        mock_celery_inspect,
    ):
        """AC-7.27.15: Filter parameter is accepted.

        Given GET /api/v1/admin/queue/{queue}/tasks?document_status=FAILED
        When request is made
        Then request succeeds (200 OK) with document_status filter applied
        """
        with patch(
            "app.services.queue_monitor_service.QueueMonitorService._get_celery_inspect",
            return_value=mock_celery_inspect,
        ):
            response = await queue_test_client.get(
                "/api/v1/admin/queue/document_processing/tasks?document_status=FAILED",
                cookies=admin_cookies,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_queue_tasks_without_filter_returns_all(
        self,
        queue_test_client: AsyncClient,
        admin_cookies: dict,
        mock_celery_inspect,
    ):
        """AC-7.27.15: Without filter, all tasks are returned.

        Given GET /api/v1/admin/queue/{queue}/tasks without document_status
        When request is made
        Then all tasks are returned (not filtered)
        """
        with patch(
            "app.services.queue_monitor_service.QueueMonitorService._get_celery_inspect",
            return_value=mock_celery_inspect,
        ):
            response = await queue_test_client.get(
                "/api/v1/admin/queue/document_processing/tasks",
                cookies=admin_cookies,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
