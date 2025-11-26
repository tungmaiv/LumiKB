"""Shared pytest fixtures.

This file contains fixtures shared across all test types (unit, integration, e2e).
Database-specific fixtures are in integration/conftest.py.
"""

import logging
import os
import sys
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient


# Suppress LiteLLM async client cleanup logging errors during interpreter shutdown.
# LiteLLM's cleanup runs after pytest closes stdout/stderr, causing ValueError
# when asyncio tries to log "Using selector: EpollSelector".
# This filter catches and suppresses those specific messages.
class _SuppressAsyncioSelectorLog(logging.Filter):
    """Filter out asyncio selector debug messages during shutdown."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Suppress "Using selector: EpollSelector" messages from asyncio
        return not (record.name == "asyncio" and "selector" in record.getMessage().lower())


# Apply filter to asyncio logger to prevent shutdown logging errors
logging.getLogger("asyncio").addFilter(_SuppressAsyncioSelectorLog())


# Additionally, redirect stderr during interpreter shutdown to suppress
# the "--- Logging error ---" message from litellm's cleanup
_original_stderr = sys.stderr


def _quiet_shutdown() -> None:
    """Suppress stderr during final cleanup to avoid litellm logging errors."""
    try:
        sys.stderr = open(os.devnull, "w")
    except Exception:
        pass


# Register late to run after litellm's atexit handler
import atexit

atexit.register(_quiet_shutdown)

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
