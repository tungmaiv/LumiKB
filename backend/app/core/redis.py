"""Redis client and session storage for authentication.

This module provides:
- Async Redis client connection management
- Session storage for login metadata
- Rate limiting for failed login attempts
"""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import redis.asyncio as redis

from app.core.config import settings

# Redis key prefixes
SESSION_PREFIX = "session:"
FAILED_LOGIN_PREFIX = "failed_login:"

# TTL values in seconds
# Default session TTL - will be overridden by get_session_timeout_seconds()
DEFAULT_SESSION_TTL = settings.jwt_expiry_minutes * 60  # Fallback: 60 minutes
FAILED_LOGIN_TTL = 15 * 60  # 15 minutes for rate limiting window

# Cache for session timeout from DB config
_session_timeout_cache: dict[str, int | float] = {"value": 0, "expires_at": 0}


async def get_session_timeout_seconds() -> int:
    """Get session timeout in seconds from DB config with caching.

    Queries the session_timeout_minutes setting from SystemConfig table.
    Caches the result for 60 seconds to avoid DB queries on every request.

    Returns:
        Session timeout in seconds (default: 720 minutes = 43200 seconds).
    """
    import time

    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.models.config import SystemConfig

    # Check cache first (60 second TTL)
    now = time.time()
    if (
        _session_timeout_cache["expires_at"] > now
        and _session_timeout_cache["value"] > 0
    ):
        return int(_session_timeout_cache["value"])

    # Query database for session_timeout_minutes
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(SystemConfig.value).where(
                    SystemConfig.key == "session_timeout_minutes"
                )
            )
            db_value = result.scalar_one_or_none()

            # Use DB value if set, otherwise default (720 minutes)
            timeout_seconds = int(db_value) * 60 if db_value is not None else 720 * 60

            # Update cache
            _session_timeout_cache["value"] = timeout_seconds
            _session_timeout_cache["expires_at"] = now + 60  # 60 second cache

            return timeout_seconds
    except Exception:
        # Fallback to env config if DB query fails
        return DEFAULT_SESSION_TTL


# Rate limiting threshold
MAX_FAILED_ATTEMPTS = 5


class RedisClient:
    """Singleton Redis client manager."""

    _client: redis.Redis | None = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        """Get or create Redis client connection.

        Returns:
            redis.Redis: Async Redis client.
        """
        if cls._client is None:
            cls._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        """Close Redis client connection."""
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None


async def get_redis_client() -> redis.Redis:
    """FastAPI dependency for Redis client.

    Returns:
        redis.Redis: Async Redis client.
    """
    return await RedisClient.get_client()


class RedisSessionStore:
    """Session storage using Redis for login metadata and rate limiting."""

    def __init__(self, client: redis.Redis) -> None:
        """Initialize session store with Redis client.

        Args:
            client: Async Redis client.
        """
        self._client = client

    async def store_session(
        self,
        user_id: UUID,
        session_data: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Store session data for a user.

        Args:
            user_id: The user's UUID.
            session_data: Session metadata (login_time, ip_address, etc.).
            ttl: Time-to-live in seconds. If None, uses session_timeout_minutes from DB config.
        """
        if ttl is None:
            ttl = await get_session_timeout_seconds()

        key = f"{SESSION_PREFIX}{user_id}"
        # Add user_id to session data
        session_data["user_id"] = str(user_id)
        await self._client.setex(key, ttl, json.dumps(session_data))

    async def get_session(self, user_id: UUID) -> dict[str, Any] | None:
        """Retrieve session data for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            Session data dict or None if not found/expired.
        """
        key = f"{SESSION_PREFIX}{user_id}"
        data = await self._client.get(key)
        if data:
            return json.loads(data)
        return None

    async def invalidate_session(self, user_id: UUID) -> None:
        """Invalidate (delete) a user's session.

        Args:
            user_id: The user's UUID.
        """
        key = f"{SESSION_PREFIX}{user_id}"
        await self._client.delete(key)

    async def increment_failed_attempts(self, ip_address: str) -> int:
        """Increment failed login attempt counter for an IP address.

        Args:
            ip_address: The client's IP address.

        Returns:
            Current count of failed attempts.
        """
        key = f"{FAILED_LOGIN_PREFIX}{ip_address}"
        # INCR creates key with value 1 if it doesn't exist
        count = await self._client.incr(key)
        # Set TTL on first increment (when count becomes 1)
        if count == 1:
            await self._client.expire(key, FAILED_LOGIN_TTL)
        return count

    async def get_failed_attempts(self, ip_address: str) -> int:
        """Get current failed login attempt count for an IP address.

        Args:
            ip_address: The client's IP address.

        Returns:
            Current count of failed attempts (0 if none).
        """
        key = f"{FAILED_LOGIN_PREFIX}{ip_address}"
        count = await self._client.get(key)
        return int(count) if count else 0

    async def reset_failed_attempts(self, ip_address: str) -> None:
        """Reset failed login attempts for an IP address (after successful login).

        Args:
            ip_address: The client's IP address.
        """
        key = f"{FAILED_LOGIN_PREFIX}{ip_address}"
        await self._client.delete(key)

    def is_rate_limited(self, failed_attempts: int) -> bool:
        """Check if an IP address is rate limited.

        Args:
            failed_attempts: Current count of failed attempts.

        Returns:
            True if rate limited (5+ attempts in 15 minutes).
        """
        return failed_attempts >= MAX_FAILED_ATTEMPTS

    async def invalidate_all_user_sessions(self, user_id: UUID) -> int:
        """Invalidate all sessions for a user.

        Used during password reset to ensure all existing sessions are logged out.
        Since we store sessions with key pattern "session:{user_id}",
        this simply deletes the session key.

        Note: Current implementation stores single session per user.
        If multi-session support is added later, this would need to use
        SCAN to find all keys matching "session:{user_id}:*" pattern.

        Args:
            user_id: The user's UUID.

        Returns:
            Number of sessions invalidated (0 or 1 currently).
        """
        key = f"{SESSION_PREFIX}{user_id}"
        result = await self._client.delete(key)
        return result


def get_client_ip(request: Any) -> str:
    """Extract client IP address from request.

    Handles X-Forwarded-For header for reverse proxy setups.

    Args:
        request: FastAPI Request object.

    Returns:
        Client IP address string.
    """
    # Check for X-Forwarded-For header (reverse proxy)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP (client IP) from comma-separated list
        return forwarded_for.split(",")[0].strip()
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    return "unknown"


def create_session_data(ip_address: str) -> dict[str, Any]:
    """Create session data dict for storing in Redis.

    Args:
        ip_address: The client's IP address.

    Returns:
        Session data dict with login_time and ip_address.
    """
    return {
        "login_time": datetime.now(UTC).isoformat(),
        "ip_address": ip_address,
    }
