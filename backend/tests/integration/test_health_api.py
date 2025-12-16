"""Integration tests for health check endpoints.

Story 7.4: Production Deployment Configuration
AC-7.4.4: /health and /ready endpoints available for orchestrator probes

Tests cover:
- Liveness probe (/health) returns 200 when service is running
- Readiness probe (/ready) returns 200 when all dependencies are accessible
- Readiness probe returns 503 when dependencies are unavailable
- Health check timeout handling (5s max)
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestLivenessProbe:
    """Tests for /health liveness probe endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200_when_service_running(
        self, client: AsyncClient
    ) -> None:
        """Test /health returns 200 if service is running."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "lumikb-api"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_v1_endpoint_also_works(self, client: AsyncClient) -> None:
        """Test /api/v1/health also returns 200."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestReadinessProbe:
    """Tests for /ready readiness probe endpoint."""

    @pytest.mark.asyncio
    async def test_ready_returns_200_when_all_dependencies_healthy(
        self, client: AsyncClient
    ) -> None:
        """Test /ready returns 200 when DB, Redis, Qdrant are accessible."""
        response = await client.get("/ready")
        # In test environment, dependencies should be available
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert "qdrant" in data["checks"]
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_ready_returns_503_when_database_unavailable(
        self, client: AsyncClient
    ) -> None:
        """Test /ready returns 503 when database is unavailable."""
        # Mock the database check to return unhealthy
        with patch(
            "app.api.v1.health._check_database",
            new_callable=AsyncMock,
            return_value={"healthy": False, "error": "Connection refused"},
        ):
            response = await client.get("/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_ready"
            assert data["checks"]["database"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_ready_returns_503_when_redis_unavailable(
        self, client: AsyncClient
    ) -> None:
        """Test /ready returns 503 when Redis is unavailable."""
        with patch(
            "app.api.v1.health._check_redis",
            new_callable=AsyncMock,
            return_value={"healthy": False, "error": "Connection refused"},
        ):
            response = await client.get("/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_ready"
            assert data["checks"]["redis"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_ready_returns_503_when_qdrant_unavailable(
        self, client: AsyncClient
    ) -> None:
        """Test /ready returns 503 when Qdrant is unavailable."""
        with patch(
            "app.api.v1.health._check_qdrant",
            new_callable=AsyncMock,
            return_value={"healthy": False, "error": "Connection refused"},
        ):
            response = await client.get("/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_ready"
            assert data["checks"]["qdrant"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_ready_v1_endpoint_also_works(self, client: AsyncClient) -> None:
        """Test /api/v1/health/ready also returns readiness status."""
        response = await client.get("/api/v1/health/ready")
        # Status depends on actual dependency availability
        assert response.status_code in [200, 503]
        data = response.json()
        assert data["status"] in ["ready", "not_ready"]
        assert "checks" in data


class TestHealthCheckTimeouts:
    """Tests for health check timeout handling."""

    @pytest.mark.asyncio
    async def test_database_check_timeout_returns_unhealthy(
        self, client: AsyncClient
    ) -> None:
        """Test database check returns unhealthy on timeout."""
        with patch(
            "app.api.v1.health._check_database",
            new_callable=AsyncMock,
            return_value={"healthy": False, "error": "timeout"},
        ):
            response = await client.get("/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["checks"]["database"]["error"] == "timeout"

    @pytest.mark.asyncio
    async def test_redis_check_timeout_returns_unhealthy(
        self, client: AsyncClient
    ) -> None:
        """Test Redis check returns unhealthy on timeout."""
        with patch(
            "app.api.v1.health._check_redis",
            new_callable=AsyncMock,
            return_value={"healthy": False, "error": "timeout"},
        ):
            response = await client.get("/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["checks"]["redis"]["error"] == "timeout"

    @pytest.mark.asyncio
    async def test_qdrant_check_timeout_returns_unhealthy(
        self, client: AsyncClient
    ) -> None:
        """Test Qdrant check returns unhealthy on timeout."""
        with patch(
            "app.api.v1.health._check_qdrant",
            new_callable=AsyncMock,
            return_value={"healthy": False, "error": "timeout"},
        ):
            response = await client.get("/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["checks"]["qdrant"]["error"] == "timeout"


class TestLegacyHealthEndpoint:
    """Tests for legacy /api/health endpoint."""

    @pytest.mark.asyncio
    async def test_legacy_health_endpoint_returns_healthy(
        self, client: AsyncClient
    ) -> None:
        """Test legacy /api/health returns healthy status with version."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
