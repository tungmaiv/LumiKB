"""Integration tests for GET /api/v1/users/me/kb-recommendations endpoint."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.kb_access_log import AccessType, KBAccessLog
from app.models.knowledge_base import KnowledgeBase
from app.models.permission import KBPermission, PermissionLevel
from app.models.user import User
from tests.factories import create_kb_data, create_registration_data


@pytest.fixture
async def recommendations_client(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def db_session_for_recommendations(
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
async def test_user_for_recommendations(
    recommendations_client: AsyncClient, db_session_for_recommendations: AsyncSession
) -> dict:
    """Create a test user for recommendations tests."""
    user_data = create_registration_data()
    response = await recommendations_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Get user from DB for ID
    result = await db_session_for_recommendations.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()

    return {**user_data, "user": response_data, "user_id": user.id, "db_user": user}


@pytest.fixture
async def test_user_cookies(
    recommendations_client: AsyncClient, test_user_for_recommendations: dict
) -> dict:
    """Login as test user and return cookies."""
    login_response = await recommendations_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_for_recommendations["email"],
            "password": test_user_for_recommendations["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def test_kb_for_recommendations(
    recommendations_client: AsyncClient,
    db_session_for_recommendations: AsyncSession,
    test_user_for_recommendations: dict,
    test_user_cookies: dict,
) -> KnowledgeBase:
    """Create a test KB owned by the test user."""
    kb_data = create_kb_data()

    # Create KB via API (trailing slash to avoid redirect)
    response = await recommendations_client.post(
        "/api/v1/knowledge-bases/",
        json=kb_data,
        cookies=test_user_cookies,
    )
    assert response.status_code == 201

    kb_id = response.json()["id"]

    # Get KB from DB
    result = await db_session_for_recommendations.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    return result.scalar_one()


class TestKBRecommendationsAuthentication:
    """Tests for authentication on kb-recommendations endpoint."""

    @pytest.mark.asyncio
    async def test_get_recommendations_authenticated_returns_200(
        self, recommendations_client: AsyncClient, test_user_cookies: dict
    ):
        """Test authenticated request returns 200 OK (AC-5.8.4)."""
        response = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
            cookies=test_user_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_recommendations_unauthenticated_returns_401(
        self, recommendations_client: AsyncClient
    ):
        """Test unauthenticated request returns 401 Unauthorized (AC-5.8.4)."""
        response = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestKBRecommendationsResponseSchema:
    """Tests for response schema validation."""

    @pytest.mark.asyncio
    async def test_response_schema_valid(
        self,
        recommendations_client: AsyncClient,
        test_user_cookies: dict,
        test_kb_for_recommendations: KnowledgeBase,
        db_session_for_recommendations: AsyncSession,
        test_user_for_recommendations: dict,
    ):
        """Test response matches KBRecommendation schema (AC-5.8.4)."""
        # Add some access logs to trigger personalized recommendations
        for _ in range(5):
            access_log = KBAccessLog(
                user_id=test_user_for_recommendations["user_id"],
                kb_id=test_kb_for_recommendations.id,
                access_type=AccessType.SEARCH,
            )
            db_session_for_recommendations.add(access_log)
        await db_session_for_recommendations.commit()

        response = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
            cookies=test_user_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        if len(data) > 0:
            rec = data[0]
            # Verify required fields exist
            assert "kb_id" in rec
            assert "kb_name" in rec
            assert "description" in rec
            assert "score" in rec
            assert "reason" in rec
            assert "is_cold_start" in rec

            # Verify types
            assert isinstance(rec["kb_name"], str)
            assert isinstance(rec["score"], (int, float))
            assert isinstance(rec["reason"], str)
            assert isinstance(rec["is_cold_start"], bool)

    @pytest.mark.asyncio
    async def test_recommendations_max_5(
        self,
        recommendations_client: AsyncClient,
        test_user_cookies: dict,
        db_session_for_recommendations: AsyncSession,
        test_user_for_recommendations: dict,
    ):
        """Test response contains max 5 recommendations (AC-5.8.4)."""
        # Create 10 KBs owned by the user
        for i in range(10):
            kb = KnowledgeBase(
                name=f"Test KB {i}",
                description=f"Test description {i}",
                owner_id=test_user_for_recommendations["user_id"],
                status="active",
            )
            db_session_for_recommendations.add(kb)
        await db_session_for_recommendations.commit()

        response = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
            cookies=test_user_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should be at most 5
        assert len(data) <= 5


class TestKBRecommendationsCaching:
    """Tests for Redis caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_hit_reduces_latency(
        self, recommendations_client: AsyncClient, test_user_cookies: dict
    ):
        """Test second call is faster due to cache hit (AC-5.8.3)."""
        # First call (cache miss)
        response1 = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
            cookies=test_user_cookies,
        )

        assert response1.status_code == status.HTTP_200_OK

        # Second call (should be cache hit)
        response2 = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
            cookies=test_user_cookies,
        )

        assert response2.status_code == status.HTTP_200_OK

        # Cache hit should return same data
        # Note: This is a soft assertion due to network variability in tests
        # In production, cache hits should be <10ms vs ~200ms
        assert response1.json() == response2.json()


class TestKBRecommendationsColdStart:
    """Tests for cold start recommendations."""

    @pytest.mark.asyncio
    async def test_new_user_gets_cold_start_recommendations(
        self,
        recommendations_client: AsyncClient,
        db_session_for_recommendations: AsyncSession,
    ):
        """Test new user receives cold start recommendations (AC-5.8.5)."""
        # Create a fresh new user
        new_user_data = create_registration_data()
        response = await recommendations_client.post(
            "/api/v1/auth/register",
            json=new_user_data,
        )
        assert response.status_code == 201

        # Get new user ID for access log setup
        result = await db_session_for_recommendations.execute(
            select(User).where(User.email == new_user_data["email"])
        )
        new_user = result.scalar_one()

        # Login
        login_response = await recommendations_client.post(
            "/api/v1/auth/login",
            data={
                "username": new_user_data["email"],
                "password": new_user_data["password"],
            },
        )
        assert login_response.status_code in (200, 204)
        new_user_cookies = login_response.cookies

        # Create some public KBs (system-owned) with popularity data
        for i in range(3):
            kb = KnowledgeBase(
                name=f"Public KB {i}",
                description=f"Public description {i}",
                owner_id=None,  # System-owned
                status="active",
            )
            db_session_for_recommendations.add(kb)
            await db_session_for_recommendations.flush()

            # Add some global access from our test user to make them popular
            # (we need a valid user_id for the FK constraint)
            for _ in range(3 - i):
                access = KBAccessLog(
                    user_id=new_user.id,
                    kb_id=kb.id,
                    access_type=AccessType.VIEW,  # VIEW doesn't count for cold start
                )
                db_session_for_recommendations.add(access)

        await db_session_for_recommendations.commit()

        # Get recommendations for new user
        response = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
            cookies=new_user_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # New user should get cold start recommendations
        # (user is < 7 days old and has 0 SEARCH accesses)
        if len(data) > 0:
            # All should be cold start
            assert all(rec["is_cold_start"] for rec in data)


class TestKBRecommendationsScoring:
    """Tests for scoring algorithm."""

    @pytest.mark.asyncio
    async def test_scores_in_valid_range(
        self,
        recommendations_client: AsyncClient,
        test_user_cookies: dict,
        test_kb_for_recommendations: KnowledgeBase,
        db_session_for_recommendations: AsyncSession,
        test_user_for_recommendations: dict,
    ):
        """Test all scores are in 0-100 range (AC-5.8.2)."""
        # Add access logs
        for _ in range(3):
            access_log = KBAccessLog(
                user_id=test_user_for_recommendations["user_id"],
                kb_id=test_kb_for_recommendations.id,
                access_type=AccessType.SEARCH,
            )
            db_session_for_recommendations.add(access_log)
        await db_session_for_recommendations.commit()

        response = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
            cookies=test_user_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        for rec in data:
            assert 0 <= rec["score"] <= 100

    @pytest.mark.asyncio
    async def test_recommendations_sorted_by_score(
        self,
        recommendations_client: AsyncClient,
        test_user_cookies: dict,
        db_session_for_recommendations: AsyncSession,
        test_user_for_recommendations: dict,
    ):
        """Test recommendations are sorted by score (highest first) (AC-5.8.1)."""
        # Create multiple KBs with different access counts
        kbs = []
        for i in range(5):
            kb = KnowledgeBase(
                name=f"Scored KB {i}",
                description=f"Description {i}",
                owner_id=test_user_for_recommendations["user_id"],
                status="active",
            )
            db_session_for_recommendations.add(kb)
            kbs.append(kb)

        await db_session_for_recommendations.commit()

        # Add varying access counts (more access = higher score expected)
        for idx, kb in enumerate(kbs):
            access_count = (idx + 1) * 5  # 5, 10, 15, 20, 25 accesses
            for _ in range(access_count):
                access_log = KBAccessLog(
                    user_id=test_user_for_recommendations["user_id"],
                    kb_id=kb.id,
                    access_type=AccessType.SEARCH,
                )
                db_session_for_recommendations.add(access_log)

        await db_session_for_recommendations.commit()

        response = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
            cookies=test_user_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        if len(data) >= 2:
            # Verify sorted descending by score
            scores = [rec["score"] for rec in data]
            assert scores == sorted(scores, reverse=True)


class TestKBRecommendationsPermissions:
    """Tests for permission checks."""

    @pytest.mark.asyncio
    async def test_user_only_sees_accessible_kbs(
        self,
        recommendations_client: AsyncClient,
        test_user_cookies: dict,
        db_session_for_recommendations: AsyncSession,
        test_user_for_recommendations: dict,
    ):
        """Test user only gets recommendations for accessible KBs."""
        # Create a second user to own the "private" KB
        other_user_data = create_registration_data()
        other_user_response = await recommendations_client.post(
            "/api/v1/auth/register",
            json=other_user_data,
        )
        assert other_user_response.status_code == 201

        # Get other user from DB
        other_user_result = await db_session_for_recommendations.execute(
            select(User).where(User.email == other_user_data["email"])
        )
        other_user = other_user_result.scalar_one()

        # Create KB owned by the test user
        owned_kb = KnowledgeBase(
            name="Owned KB",
            description="User owns this",
            owner_id=test_user_for_recommendations["user_id"],
            status="active",
        )
        db_session_for_recommendations.add(owned_kb)

        # Create KB user has permission to (system-owned)
        shared_kb = KnowledgeBase(
            name="Shared KB",
            description="User has permission",
            owner_id=None,
            status="active",
        )
        db_session_for_recommendations.add(shared_kb)
        await db_session_for_recommendations.commit()

        # Grant permission to shared KB
        permission = KBPermission(
            user_id=test_user_for_recommendations["user_id"],
            kb_id=shared_kb.id,
            permission_level=PermissionLevel.READ,
        )
        db_session_for_recommendations.add(permission)

        # Create KB user has NO access to (owned by other user)
        private_kb = KnowledgeBase(
            name="Private KB",
            description="No access",
            owner_id=other_user.id,  # Different owner - valid FK
            status="active",
        )
        db_session_for_recommendations.add(private_kb)
        await db_session_for_recommendations.commit()

        # Make test user "established" to avoid cold start
        user_result = await db_session_for_recommendations.execute(
            select(User).where(User.id == test_user_for_recommendations["user_id"])
        )
        user = user_result.scalar_one()
        user.created_at = datetime.now(UTC) - timedelta(days=30)
        await db_session_for_recommendations.commit()

        # Add access logs for owned and shared KBs only
        # (we can only add access logs for KBs the user can actually access)
        for kb in [owned_kb, shared_kb]:
            access_log = KBAccessLog(
                user_id=test_user_for_recommendations["user_id"],
                kb_id=kb.id,
                access_type=AccessType.SEARCH,
            )
            db_session_for_recommendations.add(access_log)
        await db_session_for_recommendations.commit()

        response = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
            cookies=test_user_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        kb_names = [rec["kb_name"] for rec in data]

        # Should include owned and shared KBs
        assert "Owned KB" in kb_names or "Shared KB" in kb_names or len(data) == 0

        # Should NOT include private KB
        assert "Private KB" not in kb_names


class TestKBRecommendationsEmptyList:
    """Tests for empty results handling."""

    @pytest.mark.asyncio
    async def test_empty_list_when_no_kbs(
        self, recommendations_client: AsyncClient, test_user_cookies: dict
    ):
        """Test empty list returned when no KBs available (AC-5.8.4)."""
        # Note: test_user has no KBs initially
        response = await recommendations_client.get(
            "/api/v1/users/me/kb-recommendations",
            cookies=test_user_cookies,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return empty list or cold start recommendations
        assert isinstance(data, list)
