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

    async with test_session_factory() as session, session.begin():
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
