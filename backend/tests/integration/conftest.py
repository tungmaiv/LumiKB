"""Integration test fixtures using testcontainers.

These fixtures provide isolated, self-contained database and cache
infrastructure for integration tests without requiring docker-compose.
"""

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.models.base import Base

if TYPE_CHECKING:
    from httpx import AsyncClient

# Register integration marker for all tests in this directory
pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def postgres_container():
    """Session-scoped PostgreSQL container.

    Starts once per test session and is reused across all integration tests.
    """
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def postgres_url(postgres_container):
    """Async-compatible PostgreSQL connection URL."""
    url = postgres_container.get_connection_url()
    # Convert to async driver
    return url.replace("postgresql://", "postgresql+asyncpg://").replace(
        "psycopg2", "asyncpg"
    )


@pytest.fixture(scope="session")
def redis_container():
    """Session-scoped Redis container."""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture(scope="session")
def redis_url(redis_container):
    """Redis connection URL."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}"


@pytest.fixture
async def test_engine(postgres_url):
    """Create async engine for test database.

    Function-scoped to work with pytest-asyncio's default loop scope.
    Container is session-scoped, so this is still efficient.

    Uses NullPool to avoid connection pooling issues between async tests.
    Each test gets fresh connections that are properly closed.
    """
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        postgres_url,
        echo=False,
        poolclass=NullPool,  # Disable pooling to avoid cross-test connection issues
    )

    # Create schema and tables
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))

        # Create enum types before tables (PostgreSQL requires this)
        # Use DO block since CREATE TYPE doesn't support IF NOT EXISTS
        await conn.execute(
            text("""
                DO $$ BEGIN
                    CREATE TYPE draft_status AS ENUM ('streaming', 'partial', 'complete', 'editing', 'exported');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
        )

        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Explicit cleanup
    await engine.dispose()


@pytest.fixture
async def setup_database(test_engine):
    """Alias fixture to signal database is ready.

    Some test modules use this fixture name to depend on schema setup.
    The test_engine fixture already creates the schema.
    """
    yield test_engine


@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    """Function-scoped session with automatic rollback.

    Each test gets isolated database state through transaction rollback.
    This ensures tests don't pollute each other's data.
    """
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with test_session_factory() as session:
        yield session
        await session.rollback()


# =============================================================================
# Shared API Client Fixtures (Options A + E for async event loop fix)
# =============================================================================


@pytest.fixture
async def test_redis_client(redis_url):
    """Get fresh Redis client for API tests (per-test connection).

    This fixture creates a dedicated Redis client for each test,
    ensuring proper isolation and cleanup.
    """
    import redis.asyncio as aioredis

    client = aioredis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    yield client

    # Explicit cleanup: remove test keys before closing
    try:
        keys = await client.keys("session:*")
        failed_keys = await client.keys("failed_login:*")
        keys.extend(failed_keys)
        if keys:
            await client.delete(*keys)
    except Exception:
        pass  # Ignore cleanup errors

    # Close with explicit error handling
    try:
        await client.aclose()
    except Exception:
        pass


@pytest.fixture
async def api_client(
    test_engine,
    setup_database,  # noqa: ARG001
    test_redis_client,
    redis_url,
) -> "AsyncClient":
    """Shared API test client with proper async cleanup.

    Implements Options A + E for fixing async event loop issues:
    - Option A: raise_app_exceptions=False in ASGITransport
    - Option E: Explicit cleanup of Redis singleton and connections

    Also patches module-level async_session_factory used by audit_service
    and auth modules to ensure they use the test database.

    Usage:
        async def test_something(api_client):
            response = await api_client.get("/api/v1/health")
    """
    from httpx import ASGITransport, AsyncClient

    from app.core import auth as auth_module
    from app.core import database as db_module
    from app.core import redis as redis_module
    from app.core.config import settings
    from app.core.database import get_async_session
    from app.main import app
    from app.services import audit_service as audit_module

    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Save original values to restore later
    original_db_factory = db_module.async_session_factory
    original_audit_factory = audit_module.async_session_factory
    original_auth_factory = auth_module.async_session_factory
    original_redis_url = settings.redis_url

    # Patch ALL module-level references to async_session_factory
    db_module.async_session_factory = test_session_factory
    audit_module.async_session_factory = test_session_factory
    auth_module.async_session_factory = test_session_factory

    # Patch Redis URL to use test container
    settings.redis_url = redis_url

    async def override_get_session():
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_async_session] = override_get_session

    # Reset the Redis singleton so it creates a new connection with test URL
    redis_module.RedisClient._client = None

    # Option A: Use raise_app_exceptions=False to prevent middleware
    # exception propagation across event loop boundaries
    transport = ASGITransport(app=app, raise_app_exceptions=False)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Option E: Explicit cleanup
    app.dependency_overrides.clear()

    # Restore original values
    db_module.async_session_factory = original_db_factory
    audit_module.async_session_factory = original_audit_factory
    auth_module.async_session_factory = original_auth_factory
    settings.redis_url = original_redis_url

    # Close Redis singleton with grace handling
    try:
        if redis_module.RedisClient._client is not None:
            await redis_module.RedisClient._client.aclose()
    except Exception:
        pass
    finally:
        redis_module.RedisClient._client = None


# =============================================================================
# Chat API Test Fixtures (Story 4.1)
# =============================================================================


@pytest.fixture
async def test_user_data(api_client: "AsyncClient") -> dict:
    """Create a unique test user and return user data with authentication.

    Registers a unique test user via API and logs them in.

    Returns:
        dict: {"email": str, "password": str, "cookies": httpx.Cookies, "user_id": str}
    """
    from tests.factories import create_registration_data

    # Register unique test user
    user_data = create_registration_data()
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert register_response.status_code == 201
    user_response = register_response.json()

    # Login to get JWT cookie (returns 204 No Content with Set-Cookie header)
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code in (200, 204), (
        f"Login failed: {login_response.status_code}"
    )

    # Return user data with cookies (keep as httpx.Cookies object)
    return {
        "email": user_data["email"],
        "password": user_data["password"],
        "cookies": login_response.cookies,  # Keep as httpx.Cookies object
        "user_id": user_response["id"],
    }


@pytest.fixture
async def authenticated_headers(test_user_data: dict) -> dict:
    """Return cookies for authenticated requests.

    Note: Despite the name "headers", this actually returns cookies dict.
    The name is kept for backward compatibility.
    Tests should use `cookies=authenticated_headers` in requests.

    Returns:
        dict: Cookies dictionary for authenticated requests.
    """
    return test_user_data["cookies"]


@pytest.fixture
async def demo_kb_with_indexed_docs(
    db_session: AsyncSession,
    test_user_data: dict,
) -> dict:
    """Create a demo KB with indexed documents for testing.

    Creates a Knowledge Base with the test user as owner, adds test documents
    with READY status (simulating processed/indexed documents), and grants
    READ permission to the authenticated test user.

    Returns:
        dict: KB metadata including id, name, and document count.
    """
    from sqlalchemy import select

    from app.models.document import Document, DocumentStatus
    from app.models.knowledge_base import KnowledgeBase
    from app.models.permission import KBPermission, PermissionLevel
    from app.models.user import User

    # Get test user by ID
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    # Create KB owned by test user
    kb = KnowledgeBase(
        name="Test Knowledge Base",
        description="Test KB with indexed documents",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()

    # Grant READ permission to test user (owner already has implicit ADMIN)
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.READ,
    )
    db_session.add(permission)

    # Create test documents with READY status (simulating indexed docs)
    documents = [
        Document(
            kb_id=kb.id,
            name="Authentication Guide.md",
            original_filename="auth-guide.md",
            mime_type="text/markdown",
            file_size_bytes=4096,
            file_path=f"kb-{kb.id}/auth-guide.md",
            checksum="a" * 64,  # SHA-256 placeholder
            status=DocumentStatus.READY,
            chunk_count=5,
            uploaded_by=test_user.id,
        ),
        Document(
            kb_id=kb.id,
            name="Security Best Practices.pdf",
            original_filename="security.pdf",
            mime_type="application/pdf",
            file_size_bytes=8192,
            file_path=f"kb-{kb.id}/security.pdf",
            checksum="b" * 64,
            status=DocumentStatus.READY,
            chunk_count=8,
            uploaded_by=test_user.id,
        ),
        Document(
            kb_id=kb.id,
            name="API Documentation.md",
            original_filename="api-docs.md",
            mime_type="text/markdown",
            file_size_bytes=6144,
            file_path=f"kb-{kb.id}/api-docs.md",
            checksum="c" * 64,
            status=DocumentStatus.READY,
            chunk_count=6,
            uploaded_by=test_user.id,
        ),
    ]
    db_session.add_all(documents)
    await db_session.commit()

    # Refresh to get IDs
    await db_session.refresh(kb)

    return {
        "id": str(kb.id),
        "name": kb.name,
        "document_count": len(documents),
    }


@pytest.fixture
async def empty_kb_factory(db_session: AsyncSession, test_user_data: dict):
    """Factory fixture for creating empty KBs on demand.

    Returns an async function that creates a KB with no documents.
    Useful for testing error cases (e.g., chat with empty KB).

    Returns:
        async function: Factory that creates and returns empty KB model.
    """
    from sqlalchemy import select

    from app.models.knowledge_base import KnowledgeBase
    from app.models.permission import KBPermission, PermissionLevel
    from app.models.user import User

    async def _create_empty_kb() -> KnowledgeBase:
        # Get test user by ID
        result = await db_session.execute(
            select(User).where(User.id == test_user_data["user_id"])
        )
        test_user = result.scalar_one()

        # Create empty KB
        kb = KnowledgeBase(
            name="Empty Test KB",
            description="KB with no documents for testing",
            owner_id=test_user.id,
            status="active",
        )
        db_session.add(kb)
        await db_session.flush()

        # Grant READ permission
        permission = KBPermission(
            user_id=test_user.id,
            kb_id=kb.id,
            permission_level=PermissionLevel.READ,
        )
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(kb)

        return kb

    return _create_empty_kb


@pytest.fixture
async def redis_client(test_redis_client):
    """Alias for test_redis_client for Story 4-3 workflow tests.

    Provides direct Redis access for state verification in conversation tests.
    """
    return test_redis_client


@pytest.fixture
async def second_test_kb(db_session: AsyncSession, test_user_data: dict) -> dict:
    """Create a second KB for cross-KB testing (Story 4-3 AC-5).

    Creates a second Knowledge Base with the same test user as owner,
    with test documents for testing KB-scoped conversation isolation.

    Returns:
        dict: KB metadata including id (str) for consistency with demo_kb_with_indexed_docs.
    """
    from sqlalchemy import select

    from app.models.document import Document, DocumentStatus
    from app.models.knowledge_base import KnowledgeBase
    from app.models.permission import KBPermission, PermissionLevel
    from app.models.user import User

    # Get test user
    result = await db_session.execute(
        select(User).where(User.id == test_user_data["user_id"])
    )
    test_user = result.scalar_one()

    # Create second KB
    kb = KnowledgeBase(
        name="Second Test KB",
        description="Second KB for cross-KB testing",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add(kb)
    await db_session.flush()

    # Grant READ permission
    permission = KBPermission(
        user_id=test_user.id,
        kb_id=kb.id,
        permission_level=PermissionLevel.READ,
    )
    db_session.add(permission)

    # Add test document
    document = Document(
        kb_id=kb.id,
        name="Second KB Doc.md",
        original_filename="second-kb-doc.md",
        mime_type="text/markdown",
        file_size_bytes=2048,
        file_path=f"kb-{kb.id}/second-kb-doc.md",
        checksum="d" * 64,
        status=DocumentStatus.READY,
        chunk_count=3,
        uploaded_by=test_user.id,
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(kb)

    return {
        "id": str(kb.id),  # Changed from kb_id to id for consistency
        "name": kb.name,
    }
