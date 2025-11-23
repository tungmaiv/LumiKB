"""Shared pytest fixtures.

This file contains fixtures shared across all test types (unit, integration, e2e).
Database-specific fixtures are in integration/conftest.py.
"""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# Set debug mode BEFORE importing app to disable secure cookies in tests
os.environ.setdefault("LUMIKB_DEBUG", "true")

from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for API testing.

    This fixture is shared across unit and integration tests.
    For integration tests requiring auth, use authenticated_client from fixtures/.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
