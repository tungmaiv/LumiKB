"""Integration test to verify testcontainers setup.

This test validates that:
1. PostgreSQL testcontainer starts correctly
2. Database schema is created
3. Session rollback provides test isolation
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
async def test_postgres_container_is_accessible(db_session: AsyncSession):
    """Test that PostgreSQL container is running and accessible."""
    result = await db_session.execute(text("SELECT 1 as value"))
    row = result.fetchone()
    assert row is not None
    assert row.value == 1


@pytest.mark.integration
async def test_database_schema_exists(db_session: AsyncSession):
    """Test that audit schema was created."""
    result = await db_session.execute(
        text(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'audit'"
        )
    )
    row = result.fetchone()
    assert row is not None
    assert row.schema_name == "audit"


@pytest.mark.integration
async def test_session_rollback_provides_isolation(db_session: AsyncSession):
    """Test that each test gets isolated database state.

    This test creates data that should be rolled back after the test.
    If isolation is working, subsequent tests won't see this data.
    """
    # Create a temporary table for this test
    await db_session.execute(
        text(
            "CREATE TABLE IF NOT EXISTS test_isolation_check (id serial PRIMARY KEY, value text)"
        )
    )
    await db_session.execute(
        text("INSERT INTO test_isolation_check (value) VALUES ('test_value')")
    )

    result = await db_session.execute(text("SELECT COUNT(*) FROM test_isolation_check"))
    count = result.scalar()
    assert count == 1

    # Note: This data will be rolled back due to db_session fixture behavior
