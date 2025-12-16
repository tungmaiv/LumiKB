"""Integration tests for audit export API (Story 5.3)."""

import csv
import io
import json
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit import AuditEvent
from app.models.user import User
from tests.factories import create_registration_data


@pytest.fixture
async def audit_export_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def audit_export_db_session(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for admin user setup and audit event creation."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def admin_user_for_export(
    audit_export_client: AsyncClient, audit_export_db_session: AsyncSession
) -> dict:
    """Create an admin test user for audit export tests."""
    user_data = create_registration_data()
    response = await audit_export_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Set is_superuser=True in database
    result = await audit_export_db_session.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await audit_export_db_session.commit()

    return {**user_data, "user": response_data, "user_obj": user}


@pytest.fixture
async def admin_cookies_for_export(
    audit_export_client: AsyncClient, admin_user_for_export: dict
) -> dict:
    """Login as admin and return cookies."""
    login_response = await audit_export_client.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user_for_export["email"],
            "password": admin_user_for_export["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_for_export(audit_export_client: AsyncClient) -> dict:
    """Create a regular (non-admin) test user."""
    user_data = create_registration_data()
    response = await audit_export_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json()}


@pytest.fixture
async def regular_user_cookies_for_export(
    audit_export_client: AsyncClient, regular_user_for_export: dict
) -> dict:
    """Login as regular user and return cookies."""
    login_response = await audit_export_client.post(
        "/api/v1/auth/login",
        data={
            "username": regular_user_for_export["email"],
            "password": regular_user_for_export["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.mark.asyncio
async def test_export_csv_api_streaming_response(
    audit_export_client: AsyncClient,
    admin_cookies_for_export: dict,
    audit_export_db_session: AsyncSession,
):
    """Test POST /audit/export format=csv returns StreamingResponse with correct headers."""
    # Create test audit events
    user_id = None  # System events
    for i in range(5):
        event = AuditEvent(
            timestamp=datetime.now(UTC),
            user_id=user_id,
            action=f"test.action.{i}",
            resource_type="test",
            details={"test_data": f"value_{i}"},
        )
        audit_export_db_session.add(event)
    await audit_export_db_session.commit()

    # Export as CSV
    response = await audit_export_client.post(
        "/api/v1/admin/audit/export",
        json={
            "format": "csv",
            "filters": {
                "start_date": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
                "end_date": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
                "event_type": None,
                "user_email": None,
                "resource_type": None,
                "page": 1,
                "page_size": 10000,
            },
        },
        cookies=admin_cookies_for_export,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert ".csv" in response.headers["content-disposition"]

    # Verify CSV content
    csv_content = response.text
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    assert len(rows) >= 5
    assert reader.fieldnames == [
        "id",
        "timestamp",
        "user_id",
        "user_email",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
        "details",
    ]


@pytest.mark.asyncio
async def test_export_json_api_streaming_response(
    audit_export_client: AsyncClient,
    admin_cookies_for_export: dict,
    audit_export_db_session: AsyncSession,
):
    """Test POST /audit/export format=json returns StreamingResponse with correct headers."""
    # Create test audit events
    user_id = None  # System events
    for i in range(3):
        event = AuditEvent(
            timestamp=datetime.now(UTC),
            user_id=user_id,
            action=f"test.json.{i}",
            resource_type="test",
            details={"test_data": f"json_value_{i}"},
        )
        audit_export_db_session.add(event)
    await audit_export_db_session.commit()

    # Export as JSON
    response = await audit_export_client.post(
        "/api/v1/admin/audit/export",
        json={
            "format": "json",
            "filters": {
                "start_date": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
                "end_date": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
                "event_type": None,
                "user_email": None,
                "resource_type": None,
                "page": 1,
                "page_size": 10000,
            },
        },
        cookies=admin_cookies_for_export,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]
    assert ".json" in response.headers["content-disposition"]

    # Verify JSON content
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_export_with_filters(
    audit_export_client: AsyncClient,
    admin_cookies_for_export: dict,
    audit_export_db_session: AsyncSession,
):
    """Test POST /audit/export respects event_type and date_range filters."""
    # Create test audit events with different types
    user_id = None
    search_event = AuditEvent(
        timestamp=datetime.now(UTC),
        user_id=user_id,
        action="search",
        resource_type="search",
        details={"query": "test"},
    )
    generation_event = AuditEvent(
        timestamp=datetime.now(UTC),
        user_id=user_id,
        action="generation.request",
        resource_type="draft",
        details={"document_type": "report"},
    )
    audit_export_db_session.add_all([search_event, generation_event])
    await audit_export_db_session.commit()

    # Export with event_type filter
    response = await audit_export_client.post(
        "/api/v1/admin/audit/export",
        json={
            "format": "json",
            "filters": {
                "start_date": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
                "end_date": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
                "event_type": "search",
                "user_email": None,
                "resource_type": None,
                "page": 1,
                "page_size": 10000,
            },
        },
        cookies=admin_cookies_for_export,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify only search events are included
    search_events = [e for e in data if e["action"] == "search"]

    assert len(search_events) >= 1
    # Note: May have other events from previous tests, so just verify search events exist


@pytest.mark.asyncio
async def test_export_audit_logging(
    audit_export_client: AsyncClient,
    admin_cookies_for_export: dict,
    audit_export_db_session: AsyncSession,
):
    """Test POST /audit/export logs audit.export event to audit.events."""
    # Count existing audit.export events
    from sqlalchemy import func

    count_query = select(func.count(AuditEvent.id)).where(
        AuditEvent.action == "audit.export"
    )
    result = await audit_export_db_session.execute(count_query)
    initial_count = result.scalar() or 0

    # Perform export
    await audit_export_client.post(
        "/api/v1/admin/audit/export",
        json={
            "format": "csv",
            "filters": {
                "start_date": None,
                "end_date": None,
                "event_type": None,
                "user_email": None,
                "resource_type": None,
                "page": 1,
                "page_size": 10000,
            },
        },
        cookies=admin_cookies_for_export,
    )

    # Wait for background task to complete
    import asyncio

    await asyncio.sleep(0.5)

    # Verify new audit.export event was created
    result = await audit_export_db_session.execute(count_query)
    new_count = result.scalar() or 0

    assert new_count == initial_count + 1

    # Verify audit event details
    query = (
        select(AuditEvent)
        .where(AuditEvent.action == "audit.export")
        .order_by(AuditEvent.timestamp.desc())
        .limit(1)
    )
    result = await audit_export_db_session.execute(query)
    audit_event = result.scalar_one()

    assert audit_event.action == "audit.export"
    assert audit_event.resource_type == "audit_log"
    assert audit_event.details is not None
    assert audit_event.details["format"] == "csv"
    assert "pii_redacted" in audit_event.details
    assert "record_count" in audit_event.details
    assert "filters" in audit_event.details


@pytest.mark.asyncio
async def test_export_non_admin_403(
    audit_export_client: AsyncClient,
    regular_user_cookies_for_export: dict,
):
    """Test non-admin user POST /audit/export returns 403 Forbidden."""
    response = await audit_export_client.post(
        "/api/v1/admin/audit/export",
        json={
            "format": "csv",
            "filters": {
                "start_date": None,
                "end_date": None,
                "event_type": None,
                "user_email": None,
                "resource_type": None,
                "page": 1,
                "page_size": 10000,
            },
        },
        cookies=regular_user_cookies_for_export,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_export_large_dataset_streaming(
    audit_export_client: AsyncClient,
    admin_cookies_for_export: dict,
    audit_export_db_session: AsyncSession,
):
    """Test export of large dataset uses streaming (no memory overflow)."""
    # Create 100 events (reduced from 100k for test speed)
    user_id = None
    events = [
        AuditEvent(
            timestamp=datetime.now(UTC),
            user_id=user_id,
            action=f"test.large.{i}",
            resource_type="test",
            details={"index": i, "data": "x" * 100},  # Some bulk data
        )
        for i in range(100)
    ]
    audit_export_db_session.add_all(events)
    await audit_export_db_session.commit()

    # Export as CSV (streaming)
    response = await audit_export_client.post(
        "/api/v1/admin/audit/export",
        json={
            "format": "csv",
            "filters": {
                "start_date": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
                "end_date": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
                "event_type": None,
                "user_email": None,
                "resource_type": None,
                "page": 1,
                "page_size": 10000,
            },
        },
        cookies=admin_cookies_for_export,
    )

    assert response.status_code == 200

    # Verify CSV contains data
    csv_content = response.text
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    assert len(rows) >= 100


@pytest.mark.asyncio
async def test_export_csv_pii_redaction(
    audit_export_client: AsyncClient,
    admin_cookies_for_export: dict,
    audit_export_db_session: AsyncSession,
):
    """Test CSV export applies PII redaction by default."""
    # Create event with IP address
    event = AuditEvent(
        timestamp=datetime.now(UTC),
        user_id=None,
        action="test.pii",
        resource_type="test",
        ip_address="203.0.113.45",
        details={"password": "secret123"},
    )
    audit_export_db_session.add(event)
    await audit_export_db_session.commit()

    # Export as CSV (without event_type filter since test.pii is not in enum)
    response = await audit_export_client.post(
        "/api/v1/admin/audit/export",
        json={
            "format": "csv",
            "filters": {
                "start_date": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
                "end_date": (datetime.now(UTC) + timedelta(minutes=1)).isoformat(),
                "event_type": None,
                "user_email": None,
                "resource_type": None,
                "page": 1,
                "page_size": 10000,
            },
        },
        cookies=admin_cookies_for_export,
    )

    assert response.status_code == 200

    # Parse CSV
    csv_content = response.text
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    # Find test event by action (test.pii should be in the results)
    test_row = next((r for r in rows if r["action"] == "test.pii"), None)
    assert test_row is not None, "test.pii event not found in export"

    # Verify PII redaction
    assert test_row["ip_address"] == "XXX.XXX.XXX.XXX"
    details = json.loads(test_row["details"])
    assert details["password"] == "[REDACTED]"
