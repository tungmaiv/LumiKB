"""Database connection and session management.

Story 5.20 Tech Debt Fix: Configure proper connection pooling to prevent
PostgreSQL connection exhaustion ("too many clients" errors).
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Create async engine with connection pool configuration
# Tech Debt Fix 3.2: Proper pool settings to prevent connection exhaustion
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Verify connection is alive before use
    pool_size=10,  # Base number of persistent connections
    max_overflow=20,  # Extra connections when pool is exhausted
    pool_timeout=30,  # Wait 30s for connection before timeout
    pool_recycle=1800,  # Recycle connections after 30 minutes
)

# Separate engine for Celery workers - uses NullPool to avoid connection
# management issues with async event loops in worker processes
celery_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,  # No pooling - each session gets fresh connection
)

# Create async session factory for FastAPI
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create async session factory for Celery workers
# Tech Debt Fix 3.3: Separate factory with NullPool for workers
celery_session_factory = async_sessionmaker(
    celery_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.

    Yields:
        AsyncSession: An async SQLAlchemy session.

    Example:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_celery_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for Celery workers.

    Tech Debt Fix 3.3: Uses NullPool engine to avoid connection pool
    issues with Celery's async event loop management.

    Yields:
        AsyncSession: An async SQLAlchemy session for worker use.

    Example:
        async with get_celery_session() as session:
            # ... do work
            await session.commit()
    """
    async with celery_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions (for use outside FastAPI).

    This is useful for Celery tasks, scripts, and other contexts where
    you can't use FastAPI's dependency injection.

    Yields:
        AsyncSession: An async SQLAlchemy session.

    Example:
        async with get_async_session_context() as session:
            result = await session.execute(query)
    """
    async with celery_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> bool:
    """Health check for database connectivity.

    Tech Debt Fix 3.4: Simple health check to verify DB is reachable.

    Returns:
        bool: True if connection successful, False otherwise.
    """
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
