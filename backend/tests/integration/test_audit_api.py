"""Integration tests for audit log API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user import User
from tests.factories import create_registration_data


@pytest.fixture
async def audit_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def audit_db_session(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for admin user setup and audit event creation."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def admin_user_for_audit(
    audit_client: AsyncClient, audit_db_session: AsyncSession
) -> dict:
    """Create an admin test user for audit log tests."""
    user_data = create_registration_data()
    response = await audit_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Set is_superuser=True in database
    result = await audit_db_session.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await audit_db_session.commit()

    return {**user_data, "user": response_data, "user_obj": user}


@pytest.fixture
async def admin_cookies_for_audit(
    audit_client: AsyncClient, admin_user_for_audit: dict
) -> dict:
    """Login as admin and return cookies."""
    login_response = await audit_client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user_for_audit["email"],
            "password": admin_user_for_audit["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_for_audit(audit_client: AsyncClient) -> dict:
    """Create a regular (non-admin) test user."""
    user_data = create_registration_data()
    response = await audit_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json()}


@pytest.fixture
async def regular_user_cookies_for_audit(
    audit_client: AsyncClient, regular_user_for_audit: dict
) -> dict:
    """Login as regular user and return cookies."""
    login_response = await audit_client.post(
        "/api/v1/auth/login",
        data={
            "username": regular_user_for_audit["email"],
            "password": regular_user_for_audit["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.mark.asyncio
async def test_admin_can_query_audit_logs_with_filters(
    audit_client: AsyncClient,
    audit_db_session: AsyncSession,
    admin_user_for_audit: dict,
    admin_cookies_for_audit: dict,
):
    """Test that admin can query audit logs with filters."""
    # Create some audit events for testing
    from app.repositories.audit_repo import AuditRepository

    repo = AuditRepository(audit_db_session)
    user = admin_user_for_audit["user_obj"]

    for i in range(3):
        await repo.create_event(
            action="search",
            resource_type="search",
            user_id=user.id,
            resource_id=uuid4(),
            details={"query": f"test query {i}"},
            ip_address=f"192.168.1.{i + 1}",
        )

    # Query audit logs with event_type filter
    response = await audit_client.post(
        "/api/v1/admin/audit/logs",
        json={
            "event_type": "search",
            "page": 1,
            "page_size": 50,
        },
        cookies=admin_cookies_for_audit,
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "total" in data
    assert data["total"] >= 3  # At least our 3 test events
    # All returned events should be search type
    for event in data["events"]:
        assert event["action"] == "search"


@pytest.mark.asyncio
async def test_non_admin_receives_403_forbidden(
    audit_client: AsyncClient,
    regular_user_cookies_for_audit: dict,
):
    """Test that non-admin users receive 403 Forbidden."""
    # Attempt to query audit logs
    response = await audit_client.post(
        "/api/v1/admin/audit/logs",
        json={
            "page": 1,
            "page_size": 50,
        },
        cookies=regular_user_cookies_for_audit,
    )

    # Assert 403 Forbidden
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_receives_redacted_pii_by_default(
    audit_client: AsyncClient,
    audit_db_session: AsyncSession,
    admin_user_for_audit: dict,
    admin_cookies_for_audit: dict,
):
    """Test that PII is redacted by default."""
    # Create audit event with IP address and sensitive data
    from app.repositories.audit_repo import AuditRepository

    repo = AuditRepository(audit_db_session)
    user = admin_user_for_audit["user_obj"]

    await repo.create_event(
        action="generation.request",
        resource_type="draft",
        user_id=user.id,
        resource_id=uuid4(),
        details={"password": "secret123", "query": "test"},
        ip_address="192.168.1.100",
    )

    # Query audit logs
    response = await audit_client.post(
        "/api/v1/admin/audit/logs",
        json={
            "page": 1,
            "page_size": 50,
        },
        cookies=admin_cookies_for_audit,
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) > 0

    # Verify IP address is redacted
    for event in data["events"]:
        if event["ip_address"]:
            assert event["ip_address"] == "XXX.XXX.XXX.XXX"

        # Verify sensitive details are redacted
        if event["details"] and "password" in event["details"]:
            assert event["details"]["password"] == "[REDACTED]"
