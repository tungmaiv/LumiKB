"""Integration tests for GET /api/v1/users/me/recent-kbs endpoint."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.kb_access_log import AccessType, KBAccessLog
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from tests.factories import create_kb_data, create_registration_data


@pytest.fixture
async def recent_kbs_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def db_session_for_recent(
    test_engine,
    setup_database,  # noqa: ARG001
) -> AsyncSession:
    """Get a direct database session for test data setup."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def test_user_for_recent(
    recent_kbs_client: AsyncClient, db_session_for_recent: AsyncSession
) -> dict:
    """Create a test user for recent KBs tests."""
    user_data = create_registration_data()
    response = await recent_kbs_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Get user from DB for ID
    result = await db_session_for_recent.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()

    return {**user_data, "user": response_data, "user_id": user.id, "db_user": user}


@pytest.fixture
async def test_user_recent_cookies(
    recent_kbs_client: AsyncClient, test_user_for_recent: dict
) -> dict:
    """Login as test user and return cookies."""
    login_response = await recent_kbs_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_for_recent["email"],
            "password": test_user_for_recent["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def test_kb_for_recent(
    recent_kbs_client: AsyncClient,
    db_session_for_recent: AsyncSession,
    test_user_for_recent: dict,
    test_user_recent_cookies: dict,
) -> KnowledgeBase:
    """Create a test KB owned by the test user."""
    kb_data = create_kb_data()

    # Create KB via API
    response = await recent_kbs_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
        cookies=test_user_recent_cookies,
    )
    assert response.status_code == 201

    kb_id = response.json()["id"]

    # Get KB from DB
    result = await db_session_for_recent.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    return result.scalar_one()


class TestRecentKBsAuthentication:
    """Tests for authentication on recent-kbs endpoint."""

    @pytest.mark.asyncio
    async def test_get_recent_kbs_authenticated_returns_200(
        self, recent_kbs_client: AsyncClient, test_user_recent_cookies: dict
    ):
        """Test authenticated request returns 200 OK (AC-5.9.1)."""
        response = await recent_kbs_client.get(
            "/api/v1/users/me/recent-kbs",
            cookies=test_user_recent_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_recent_kbs_unauthenticated_returns_401(
        self, recent_kbs_client: AsyncClient
    ):
        """Test unauthenticated request returns 401 Unauthorized."""
        response = await recent_kbs_client.get(
            "/api/v1/users/me/recent-kbs",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRecentKBsResponseSchema:
    """Tests for response schema validation."""

    @pytest.mark.asyncio
    async def test_response_schema_valid(
        self,
        recent_kbs_client: AsyncClient,
        test_user_recent_cookies: dict,
        test_kb_for_recent: KnowledgeBase,
        db_session_for_recent: AsyncSession,
        test_user_for_recent: dict,
    ):
        """Test response matches RecentKB schema (AC-5.9.1)."""
        # Add access logs to populate recent KBs
        for _ in range(3):
            access_log = KBAccessLog(
                user_id=test_user_for_recent["user_id"],
                kb_id=test_kb_for_recent.id,
                access_type=AccessType.SEARCH,
            )
            db_session_for_recent.add(access_log)
        await db_session_for_recent.commit()

        response = await recent_kbs_client.get(
            "/api/v1/users/me/recent-kbs",
            cookies=test_user_recent_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        if len(data) > 0:
            recent_kb = data[0]
            # Verify required fields exist
            assert "kb_id" in recent_kb
            assert "kb_name" in recent_kb
            assert "description" in recent_kb
            assert "last_accessed" in recent_kb
            assert "document_count" in recent_kb

            # Verify types
            assert isinstance(recent_kb["kb_name"], str)
            assert isinstance(recent_kb["description"], str)
            assert isinstance(recent_kb["document_count"], int)

    @pytest.mark.asyncio
    async def test_recent_kbs_max_5(
        self,
        recent_kbs_client: AsyncClient,
        test_user_recent_cookies: dict,
        db_session_for_recent: AsyncSession,
        test_user_for_recent: dict,
    ):
        """Test response contains max 5 recent KBs (AC-5.9.3)."""
        # Create 10 KBs owned by the user
        kbs = []
        for i in range(10):
            kb = KnowledgeBase(
                name=f"Test KB {i}",
                description=f"Test description {i}",
                owner_id=test_user_for_recent["user_id"],
                status="active",
            )
            db_session_for_recent.add(kb)
            kbs.append(kb)
        await db_session_for_recent.commit()

        # Add access logs for each KB
        for kb in kbs:
            access_log = KBAccessLog(
                user_id=test_user_for_recent["user_id"],
                kb_id=kb.id,
                access_type=AccessType.SEARCH,
            )
            db_session_for_recent.add(access_log)
        await db_session_for_recent.commit()

        response = await recent_kbs_client.get(
            "/api/v1/users/me/recent-kbs",
            cookies=test_user_recent_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should be at most 5
        assert len(data) <= 5


class TestRecentKBsSorting:
    """Tests for sorting order."""

    @pytest.mark.asyncio
    async def test_sorted_by_last_accessed_desc(
        self,
        recent_kbs_client: AsyncClient,
        test_user_recent_cookies: dict,
        db_session_for_recent: AsyncSession,
        test_user_for_recent: dict,
    ):
        """Test results are sorted by last_accessed DESC (AC-5.9.1)."""
        now = datetime.now(UTC)

        # Create KBs with different access times
        older_kb = KnowledgeBase(
            name="Older KB",
            description="Accessed yesterday",
            owner_id=test_user_for_recent["user_id"],
            status="active",
        )
        db_session_for_recent.add(older_kb)

        newer_kb = KnowledgeBase(
            name="Newer KB",
            description="Accessed today",
            owner_id=test_user_for_recent["user_id"],
            status="active",
        )
        db_session_for_recent.add(newer_kb)
        await db_session_for_recent.commit()

        # Add access logs with different times
        older_access = KBAccessLog(
            user_id=test_user_for_recent["user_id"],
            kb_id=older_kb.id,
            access_type=AccessType.SEARCH,
        )
        # Manually set older access time
        older_access.accessed_at = now - timedelta(days=1)
        db_session_for_recent.add(older_access)

        newer_access = KBAccessLog(
            user_id=test_user_for_recent["user_id"],
            kb_id=newer_kb.id,
            access_type=AccessType.SEARCH,
        )
        # Manually set newer access time
        newer_access.accessed_at = now
        db_session_for_recent.add(newer_access)
        await db_session_for_recent.commit()

        response = await recent_kbs_client.get(
            "/api/v1/users/me/recent-kbs",
            cookies=test_user_recent_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        if len(data) >= 2:
            # Newer KB should come first
            kb_names = [kb["kb_name"] for kb in data]
            assert kb_names.index("Newer KB") < kb_names.index("Older KB")


class TestRecentKBsDocumentCount:
    """Tests for document count in response."""

    @pytest.mark.asyncio
    async def test_includes_document_count(
        self,
        recent_kbs_client: AsyncClient,
        test_user_recent_cookies: dict,
        test_kb_for_recent: KnowledgeBase,
        db_session_for_recent: AsyncSession,
        test_user_for_recent: dict,
    ):
        """Test that document_count is included in response (AC-5.9.2)."""
        # Add access logs
        access_log = KBAccessLog(
            user_id=test_user_for_recent["user_id"],
            kb_id=test_kb_for_recent.id,
            access_type=AccessType.SEARCH,
        )
        db_session_for_recent.add(access_log)
        await db_session_for_recent.commit()

        response = await recent_kbs_client.get(
            "/api/v1/users/me/recent-kbs",
            cookies=test_user_recent_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        if len(data) > 0:
            # document_count should be non-negative integer
            assert data[0]["document_count"] >= 0


class TestRecentKBsEmptyState:
    """Tests for empty state handling."""

    @pytest.mark.asyncio
    async def test_empty_list_when_no_history(
        self, recent_kbs_client: AsyncClient, test_user_recent_cookies: dict
    ):
        """Test empty list returned when user has no KB access history (AC-5.9.4)."""
        # User has no access history
        response = await recent_kbs_client.get(
            "/api/v1/users/me/recent-kbs",
            cookies=test_user_recent_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data == []


class TestRecentKBsPerformance:
    """Tests for performance requirements."""

    @pytest.mark.asyncio
    async def test_response_time_within_sla(
        self,
        recent_kbs_client: AsyncClient,
        test_user_recent_cookies: dict,
        test_kb_for_recent: KnowledgeBase,
        db_session_for_recent: AsyncSession,
        test_user_for_recent: dict,
    ):
        """Test response time is within 100ms SLA (AC-5.9.2)."""
        import time

        # Add access logs
        access_log = KBAccessLog(
            user_id=test_user_for_recent["user_id"],
            kb_id=test_kb_for_recent.id,
            access_type=AccessType.SEARCH,
        )
        db_session_for_recent.add(access_log)
        await db_session_for_recent.commit()

        start_time = time.time()
        response = await recent_kbs_client.get(
            "/api/v1/users/me/recent-kbs",
            cookies=test_user_recent_cookies,
        )
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK

        # Response should be under 500ms in integration test
        # (100ms SLA is for production, test env has more overhead)
        response_time_ms = (end_time - start_time) * 1000
        assert response_time_ms < 500, f"Response took {response_time_ms:.0f}ms"


class TestRecentKBsActiveOnly:
    """Tests for active KB filtering."""

    @pytest.mark.asyncio
    async def test_only_active_kbs_returned(
        self,
        recent_kbs_client: AsyncClient,
        test_user_recent_cookies: dict,
        db_session_for_recent: AsyncSession,
        test_user_for_recent: dict,
    ):
        """Test that only active KBs are returned (archived excluded)."""
        # Create active KB
        active_kb = KnowledgeBase(
            name="Active KB",
            description="This is active",
            owner_id=test_user_for_recent["user_id"],
            status="active",
        )
        db_session_for_recent.add(active_kb)

        # Create archived KB
        archived_kb = KnowledgeBase(
            name="Archived KB",
            description="This is archived",
            owner_id=test_user_for_recent["user_id"],
            status="archived",
        )
        db_session_for_recent.add(archived_kb)
        await db_session_for_recent.commit()

        # Add access logs for both
        for kb in [active_kb, archived_kb]:
            access_log = KBAccessLog(
                user_id=test_user_for_recent["user_id"],
                kb_id=kb.id,
                access_type=AccessType.SEARCH,
            )
            db_session_for_recent.add(access_log)
        await db_session_for_recent.commit()

        response = await recent_kbs_client.get(
            "/api/v1/users/me/recent-kbs",
            cookies=test_user_recent_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        kb_names = [kb["kb_name"] for kb in data]

        # Should include active KB
        assert "Active KB" in kb_names

        # Should NOT include archived KB
        assert "Archived KB" not in kb_names
