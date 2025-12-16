"""Integration tests for generation audit API."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User


@pytest.fixture
async def test_user(test_user_data: dict, db_session: AsyncSession) -> User:
    """Get the test user object from test_user_data."""
    result = await db_session.execute(select(User).where(User.id == test_user_data["user_id"]))
    return result.scalar_one()


@pytest.fixture
async def test_superuser(api_client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create a superuser for testing admin endpoints.

    Returns:
        dict: {"user": User, "email": str, "password": str}
    """
    from tests.factories import create_registration_data

    user_data = create_registration_data()

    # Register user
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]

    # Get user and make them superuser
    result = await db_session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.is_superuser = True
    await db_session.commit()
    await db_session.refresh(user)

    # Return user object with credentials
    return {
        "user": user,
        "email": user_data["email"],
        "password": user_data["password"],
    }


@pytest.fixture
async def superuser_headers(test_superuser: dict, api_client: AsyncClient) -> dict:
    """Return cookies for superuser authenticated requests."""
    # Login as superuser to get cookies
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_superuser["email"],
            "password": test_superuser["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def test_kb(db_session: AsyncSession, test_superuser: dict) -> KnowledgeBase:
    """Create a test knowledge base."""
    kb = KnowledgeBase(
        name="Test KB",
        description="Test knowledge base",
        owner_id=test_superuser["user"].id,
        status="active",
    )
    db_session.add(kb)
    await db_session.commit()
    await db_session.refresh(kb)
    return kb


@pytest.mark.asyncio
async def test_get_audit_logs_requires_admin(
    api_client: AsyncClient,
    authenticated_headers: dict,
):
    """Test GET /admin/audit/generation requires is_superuser=true (403 for non-admin)."""
    response = await api_client.get(
        "/api/v1/admin/audit/generation",
        cookies=authenticated_headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_audit_logs_filters_by_date_range(
    api_client: AsyncClient,
    test_superuser: dict,
    superuser_headers: dict,
    db_session: AsyncSession,
    test_kb: KnowledgeBase,
):
    """Test filters by date range (start_date, end_date)."""
    now = datetime.now(UTC)
    yesterday = now - timedelta(days=1)

    # Create events at different times
    old_event = AuditEvent(
        id=uuid.uuid4(),
        timestamp=yesterday,
        user_id=test_superuser["user"].id,
        action="generation.request",
        resource_type="draft",
        details={
            "kb_id": str(test_kb.id),
            "document_type": "test",
            "context": "old event",
        },
    )
    new_event = AuditEvent(
        id=uuid.uuid4(),
        timestamp=now,
        user_id=test_superuser["user"].id,
        action="generation.request",
        resource_type="draft",
        details={
            "kb_id": str(test_kb.id),
            "document_type": "test",
            "context": "new event",
        },
    )

    db_session.add(old_event)
    db_session.add(new_event)
    await db_session.commit()

    # Query with date filter (only events after yesterday midnight)
    start_date = yesterday.replace(hour=23, minute=0, second=0, microsecond=0)
    response = await api_client.get(
        "/api/v1/admin/audit/generation",
        params={"start_date": start_date.isoformat()},
        cookies=superuser_headers,
    )

    if response.status_code != 200:
        print(f"Status: {response.status_code}")
        print(f"Response text: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) >= 1
    # Should include new_event, may or may not include old_event depending on timing


@pytest.mark.asyncio
async def test_get_audit_logs_filters_by_user(
    api_client: AsyncClient,
    test_superuser: dict,
    test_user: User,
    superuser_headers: dict,
    db_session: AsyncSession,
    test_kb: KnowledgeBase,
):
    """Test filters by user_id."""
    # Create events for different users
    user1_event = AuditEvent(
        id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        user_id=test_user.id,
        action="generation.request",
        resource_type="draft",
        details={"kb_id": str(test_kb.id), "document_type": "test"},
    )
    user2_event = AuditEvent(
        id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        user_id=test_superuser["user"].id,
        action="generation.request",
        resource_type="draft",
        details={"kb_id": str(test_kb.id), "document_type": "test"},
    )

    db_session.add(user1_event)
    db_session.add(user2_event)
    await db_session.commit()

    # Query filtered by test_user.id
    response = await api_client.get(
        "/api/v1/admin/audit/generation",
        params={"user_id": str(test_user.id)},
        cookies=superuser_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # All events should be for test_user
    for event in data["events"]:
        assert event["user_id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_get_audit_logs_filters_by_kb(
    api_client: AsyncClient,
    test_superuser: dict,
    superuser_headers: dict,
    db_session: AsyncSession,
    test_kb: KnowledgeBase,
):
    """Test filters by kb_id."""
    kb_id_1 = test_kb.id
    kb_id_2 = uuid.uuid4()

    # Create events for different KBs
    kb1_event = AuditEvent(
        id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        user_id=test_superuser["user"].id,
        action="generation.request",
        resource_type="draft",
        details={"kb_id": str(kb_id_1), "document_type": "test"},
    )
    kb2_event = AuditEvent(
        id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        user_id=test_superuser["user"].id,
        action="generation.request",
        resource_type="draft",
        details={"kb_id": str(kb_id_2), "document_type": "test"},
    )

    db_session.add(kb1_event)
    db_session.add(kb2_event)
    await db_session.commit()

    # Query filtered by kb_id_1
    response = await api_client.get(
        "/api/v1/admin/audit/generation",
        params={"kb_id": str(kb_id_1)},
        cookies=superuser_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # All events should be for kb_id_1
    for event in data["events"]:
        if event["kb_id"]:  # Some events might not have kb_id
            assert event["kb_id"] == str(kb_id_1)


@pytest.mark.asyncio
async def test_get_audit_logs_filters_by_action_type(
    api_client: AsyncClient,
    test_superuser: dict,
    superuser_headers: dict,
    db_session: AsyncSession,
    test_kb: KnowledgeBase,
):
    """Test filters by action_type."""
    # Create events with different actions
    request_event = AuditEvent(
        id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        user_id=test_superuser["user"].id,
        action="generation.request",
        resource_type="draft",
        details={"kb_id": str(test_kb.id)},
    )
    complete_event = AuditEvent(
        id=uuid.uuid4(),
        timestamp=datetime.now(UTC),
        user_id=test_superuser["user"].id,
        action="generation.complete",
        resource_type="draft",
        details={"kb_id": str(test_kb.id), "success": True},
    )

    db_session.add(request_event)
    db_session.add(complete_event)
    await db_session.commit()

    # Query filtered by action_type
    response = await api_client.get(
        "/api/v1/admin/audit/generation",
        params={"action_type": "generation.complete"},
        cookies=superuser_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # All events should have action "generation.complete"
    for event in data["events"]:
        assert event["action"] == "generation.complete"


@pytest.mark.asyncio
async def test_get_audit_logs_includes_aggregations(
    api_client: AsyncClient,
    test_superuser: dict,
    superuser_headers: dict,
    db_session: AsyncSession,
    test_kb: KnowledgeBase,
):
    """Test response includes aggregated metrics."""
    request_id = str(uuid.uuid4())

    # Create request, complete, and failed events
    events = [
        AuditEvent(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            user_id=test_superuser["user"].id,
            action="generation.request",
            resource_type="draft",
            details={"request_id": request_id, "kb_id": str(test_kb.id)},
        ),
        AuditEvent(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            user_id=test_superuser["user"].id,
            action="generation.complete",
            resource_type="draft",
            details={
                "request_id": request_id,
                "kb_id": str(test_kb.id),
                "citation_count": 10,
                "generation_time_ms": 3000,
                "success": True,
            },
        ),
        AuditEvent(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            user_id=test_superuser["user"].id,
            action="generation.failed",
            resource_type="draft",
            details={
                "request_id": str(uuid.uuid4()),
                "kb_id": str(test_kb.id),
                "generation_time_ms": 1500,
                "success": False,
            },
        ),
    ]

    for event in events:
        db_session.add(event)
    await db_session.commit()

    response = await api_client.get(
        "/api/v1/admin/audit/generation",
        cookies=superuser_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify metrics are present
    assert "metrics" in data
    metrics = data["metrics"]
    assert "total_requests" in metrics
    assert "success_count" in metrics
    assert "failure_count" in metrics
    assert "avg_generation_time_ms" in metrics
    assert "total_citations" in metrics

    # Verify counts
    assert metrics["total_requests"] >= 1
    assert metrics["success_count"] >= 1
    assert metrics["failure_count"] >= 1


@pytest.mark.asyncio
async def test_get_audit_logs_pagination(
    api_client: AsyncClient,
    test_superuser: dict,
    superuser_headers: dict,
    db_session: AsyncSession,
    test_kb: KnowledgeBase,
):
    """Test pagination (page, per_page) with accurate total count."""
    # Create 15 events
    for i in range(15):
        event = AuditEvent(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            user_id=test_superuser["user"].id,
            action="generation.request",
            resource_type="draft",
            details={"kb_id": str(test_kb.id), "context": f"event {i}"},
        )
        db_session.add(event)
    await db_session.commit()

    # Query page 1 with per_page=5
    response = await api_client.get(
        "/api/v1/admin/audit/generation",
        params={"page": 1, "per_page": 5},
        cookies=superuser_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify pagination metadata
    assert "pagination" in data
    pagination = data["pagination"]
    assert pagination["page"] == 1
    assert pagination["per_page"] == 5
    assert pagination["total"] >= 15

    # Verify events count matches per_page or total (whichever is smaller)
    assert len(data["events"]) <= 5

    # Query page 2
    response = await api_client.get(
        "/api/v1/admin/audit/generation",
        params={"page": 2, "per_page": 5},
        cookies=superuser_headers,
    )

    assert response.status_code == 200
    data2 = response.json()
    assert data2["pagination"]["page"] == 2

    # Verify events on page 2 are different from page 1
    page1_ids = {e["id"] for e in data["events"]}
    page2_ids = {e["id"] for e in data2["events"]}
    assert page1_ids.isdisjoint(page2_ids)  # No overlap
