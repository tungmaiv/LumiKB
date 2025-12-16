"""Integration tests for GET /api/v1/admin/knowledge-bases/{kb_id}/stats endpoint."""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from tests.factories import create_knowledge_base, create_registration_data


@pytest.fixture
async def admin_client_for_kb_stats(api_client: AsyncClient) -> AsyncClient:
    """Alias for shared api_client fixture."""
    return api_client


@pytest.fixture
async def db_session_for_kb_stats(test_engine, setup_database) -> AsyncSession:  # noqa: ARG001
    """Get a direct database session for admin user setup."""
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def admin_user_for_kb_stats(
    admin_client_for_kb_stats: AsyncClient, db_session_for_kb_stats: AsyncSession
) -> dict:
    """Create an admin test user."""
    user_data = create_registration_data()
    response = await admin_client_for_kb_stats.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    response_data = response.json()

    # Set is_superuser=True in database
    result = await db_session_for_kb_stats.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await db_session_for_kb_stats.commit()

    return {**user_data, "user": response_data}


@pytest.fixture
async def admin_cookies_for_kb_stats(
    admin_client_for_kb_stats: AsyncClient, admin_user_for_kb_stats: dict
) -> dict:
    """Login as admin and return cookies."""
    login_response = await admin_client_for_kb_stats.post(
        "/api/v1/auth/login",
        data={
            "username": admin_user_for_kb_stats["email"],
            "password": admin_user_for_kb_stats["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def regular_user_for_kb_stats(admin_client_for_kb_stats: AsyncClient) -> dict:
    """Create a regular (non-admin) test user."""
    user_data = create_registration_data()
    response = await admin_client_for_kb_stats.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert response.status_code == 201
    return {**user_data, "user": response.json()}


@pytest.fixture
async def regular_user_cookies_for_kb_stats(
    admin_client_for_kb_stats: AsyncClient, regular_user_for_kb_stats: dict
) -> dict:
    """Login as regular user and return cookies."""
    login_response = await admin_client_for_kb_stats.post(
        "/api/v1/auth/login",
        data={
            "username": regular_user_for_kb_stats["email"],
            "password": regular_user_for_kb_stats["password"],
        },
    )
    assert login_response.status_code in (200, 204)
    return login_response.cookies


@pytest.fixture
async def test_kb_for_stats(
    db_session_for_kb_stats: AsyncSession, admin_user_for_kb_stats: dict
) -> KnowledgeBase:
    """Create a test knowledge base for stats testing."""
    user = await db_session_for_kb_stats.execute(
        select(User).where(User.email == admin_user_for_kb_stats["email"])
    )
    user = user.scalar_one()

    kb = await create_knowledge_base(
        db_session_for_kb_stats,
        name="Test KB for Stats",
        description="KB for stats testing",
        owner_id=user.id,
    )
    await db_session_for_kb_stats.commit()
    await db_session_for_kb_stats.refresh(kb)
    return kb


@pytest.mark.asyncio
async def test_get_kb_stats_success(
    admin_client_for_kb_stats: AsyncClient,
    admin_cookies_for_kb_stats: dict,
    test_kb_for_stats: KnowledgeBase,
):
    """Test admin can successfully fetch KB statistics."""
    response = await admin_client_for_kb_stats.get(
        f"/api/v1/admin/knowledge-bases/{test_kb_for_stats.id}/stats",
        cookies=admin_cookies_for_kb_stats,
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    assert response.status_code == status.HTTP_200_OK

    # Verify response structure
    data = response.json()
    assert "kb_id" in data
    assert "kb_name" in data
    assert "document_count" in data
    assert "storage_bytes" in data
    assert "total_chunks" in data
    assert "total_embeddings" in data
    assert "searches_30d" in data
    assert "generations_30d" in data
    assert "unique_users_30d" in data
    assert "top_documents" in data
    assert "last_updated" in data

    # Verify KB identification
    assert data["kb_id"] == str(test_kb_for_stats.id)
    assert data["kb_name"] == "Test KB for Stats"

    # Verify empty KB returns zero metrics (no documents uploaded)
    assert data["document_count"] == 0
    assert data["storage_bytes"] == 0
    # Qdrant may or may not have collection yet (graceful degradation)
    assert isinstance(data["total_chunks"], int)
    assert isinstance(data["total_embeddings"], int)


@pytest.mark.asyncio
async def test_get_kb_stats_non_admin_forbidden(
    admin_client_for_kb_stats: AsyncClient,
    regular_user_cookies_for_kb_stats: dict,
    test_kb_for_stats: KnowledgeBase,
):
    """Test non-admin user gets 403 when accessing KB stats."""
    response = await admin_client_for_kb_stats.get(
        f"/api/v1/admin/knowledge-bases/{test_kb_for_stats.id}/stats",
        cookies=regular_user_cookies_for_kb_stats,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_kb_stats_unauthenticated(
    admin_client_for_kb_stats: AsyncClient,
    test_kb_for_stats: KnowledgeBase,
):
    """Test unauthenticated request gets 401."""
    response = await admin_client_for_kb_stats.get(
        f"/api/v1/admin/knowledge-bases/{test_kb_for_stats.id}/stats",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_kb_stats_kb_not_found(
    admin_client_for_kb_stats: AsyncClient,
    admin_cookies_for_kb_stats: dict,
):
    """Test 404 when KB does not exist."""
    from uuid import uuid4

    fake_kb_id = uuid4()

    response = await admin_client_for_kb_stats.get(
        f"/api/v1/admin/knowledge-bases/{fake_kb_id}/stats",
        cookies=admin_cookies_for_kb_stats,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Knowledge base not found" in response.json()["detail"]
