"""Integration tests for GET /api/v1/admin/stats endpoint."""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user import User
from tests.factories import create_registration_data


@pytest.fixture
async def admin_client_for_stats(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def db_session_for_stats(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for admin user setup."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def admin_user_for_stats(
    admin_client_for_stats: AsyncClient, db_session_for_stats: AsyncSession
) -> dict:
    """Create an admin test user."""
    user_data = create_registration_data()
    response = await admin_client_for_stats.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Set is_superuser=True in database
    result = await db_session_for_stats.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await db_session_for_stats.commit()

    return {**user_data, "user": response_data}


@pytest.fixture
async def admin_cookies_for_stats(admin_client_for_stats: AsyncClient, admin_user_for_stats: dict) -> dict:
    """Login as admin and return cookies."""
    login_response = await admin_client_for_stats.post(
        "/api/v1/auth/login",
        data={"username": admin_user_for_stats["email"], "password": admin_user_for_stats["password"]},
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_for_stats(admin_client_for_stats: AsyncClient) -> dict:
    """Create a regular (non-admin) test user."""
    user_data = create_registration_data()
    response = await admin_client_for_stats.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json()}


@pytest.fixture
async def regular_user_cookies_for_stats(admin_client_for_stats: AsyncClient, regular_user_for_stats: dict) -> dict:
    """Login as regular user and return cookies."""
    login_response = await admin_client_for_stats.post(
        "/api/v1/auth/login",
        data={"username": regular_user_for_stats["email"], "password": regular_user_for_stats["password"]},
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.mark.asyncio
async def test_get_admin_stats_success(admin_client_for_stats: AsyncClient, admin_cookies_for_stats: dict):
    """Test admin can successfully fetch dashboard stats."""
    response = await admin_client_for_stats.get(
        '/api/v1/admin/stats',
        cookies=admin_cookies_for_stats,
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Verify structure
    assert 'users' in data
    assert 'knowledge_bases' in data
    assert 'documents' in data
    assert 'storage' in data
    assert 'activity' in data
    assert 'trends' in data

    # Verify user stats
    assert 'total' in data['users']
    assert 'active' in data['users']
    assert 'inactive' in data['users']
    assert isinstance(data['users']['total'], int)

    # Verify activity stats
    assert 'searches' in data['activity']
    assert 'generations' in data['activity']
    assert 'last_24h' in data['activity']['searches']
    assert 'last_7d' in data['activity']['searches']
    assert 'last_30d' in data['activity']['searches']

    # Verify trends (sparkline data)
    assert isinstance(data['trends']['searches'], list)
    assert isinstance(data['trends']['generations'], list)
    assert len(data['trends']['searches']) == 30
    assert len(data['trends']['generations']) == 30


@pytest.mark.asyncio
async def test_get_admin_stats_non_admin_forbidden(
    admin_client_for_stats: AsyncClient, regular_user_cookies_for_stats: dict
):
    """Test non-admin user receives 403 Forbidden."""
    response = await admin_client_for_stats.get(
        '/api/v1/admin/stats',
        cookies=regular_user_cookies_for_stats,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_admin_stats_unauthenticated(admin_client_for_stats: AsyncClient):
    """Test unauthenticated request receives 401."""
    response = await admin_client_for_stats.get('/api/v1/admin/stats')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_admin_stats_returns_consistent_data(
    admin_client_for_stats: AsyncClient, admin_cookies_for_stats: dict
):
    """Test stats endpoint returns consistent data across requests."""
    # First request
    response1 = await admin_client_for_stats.get(
        '/api/v1/admin/stats',
        cookies=admin_cookies_for_stats,
    )
    data1 = response1.json()

    # Second request (should hit cache)
    response2 = await admin_client_for_stats.get(
        '/api/v1/admin/stats',
        cookies=admin_cookies_for_stats,
    )
    data2 = response2.json()

    # Verify both responses are successful
    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK

    # Verify data is consistent (cache hit)
    assert data1['users']['total'] == data2['users']['total']
    assert data1['knowledge_bases']['total'] == data2['knowledge_bases']['total']
    assert data1['documents']['total'] == data2['documents']['total']


@pytest.mark.asyncio
async def test_get_admin_stats_storage_metrics(
    admin_client_for_stats: AsyncClient, admin_cookies_for_stats: dict
):
    """Test storage statistics are calculated correctly."""
    response = await admin_client_for_stats.get(
        '/api/v1/admin/stats',
        cookies=admin_cookies_for_stats,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Verify storage stats structure
    assert 'total_bytes' in data['storage']
    assert 'avg_doc_size_bytes' in data['storage']
    assert isinstance(data['storage']['total_bytes'], int)
    assert isinstance(data['storage']['avg_doc_size_bytes'], int)

    # Verify non-negative values
    assert data['storage']['total_bytes'] >= 0
    assert data['storage']['avg_doc_size_bytes'] >= 0


@pytest.mark.asyncio
async def test_get_admin_stats_document_status_breakdown(
    admin_client_for_stats: AsyncClient, admin_cookies_for_stats: dict
):
    """Test document counts are grouped by status."""
    response = await admin_client_for_stats.get(
        '/api/v1/admin/stats',
        cookies=admin_cookies_for_stats,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Verify by_status exists
    assert 'by_status' in data['documents']
    assert isinstance(data['documents']['by_status'], dict)

    # Verify total matches sum of status counts (if any docs exist)
    if data['documents']['total'] > 0:
        status_sum = sum(data['documents']['by_status'].values())
        assert status_sum == data['documents']['total']


@pytest.mark.asyncio
async def test_get_admin_stats_kb_status_breakdown(
    admin_client_for_stats: AsyncClient, admin_cookies_for_stats: dict
):
    """Test knowledge base counts are grouped by status."""
    response = await admin_client_for_stats.get(
        '/api/v1/admin/stats',
        cookies=admin_cookies_for_stats,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Verify by_status exists
    assert 'by_status' in data['knowledge_bases']
    assert isinstance(data['knowledge_bases']['by_status'], dict)

    # Verify total matches sum of status counts (if any KBs exist)
    if data['knowledge_bases']['total'] > 0:
        status_sum = sum(data['knowledge_bases']['by_status'].values())
        assert status_sum == data['knowledge_bases']['total']


@pytest.mark.asyncio
async def test_get_admin_stats_period_metrics_structure(
    admin_client_for_stats: AsyncClient, admin_cookies_for_stats: dict
):
    """Test activity metrics have correct period structure."""
    response = await admin_client_for_stats.get(
        '/api/v1/admin/stats',
        cookies=admin_cookies_for_stats,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Verify searches period stats
    searches = data['activity']['searches']
    assert isinstance(searches['last_24h'], int)
    assert isinstance(searches['last_7d'], int)
    assert isinstance(searches['last_30d'], int)

    # Verify logical ordering: 24h <= 7d <= 30d
    assert searches['last_24h'] <= searches['last_7d']
    assert searches['last_7d'] <= searches['last_30d']

    # Verify generations period stats
    generations = data['activity']['generations']
    assert isinstance(generations['last_24h'], int)
    assert isinstance(generations['last_7d'], int)
    assert isinstance(generations['last_30d'], int)

    # Verify logical ordering
    assert generations['last_24h'] <= generations['last_7d']
    assert generations['last_7d'] <= generations['last_30d']
