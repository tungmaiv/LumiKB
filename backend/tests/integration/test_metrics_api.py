"""Integration tests for Prometheus metrics endpoint.

Story 7.5: Monitoring and Observability (AC-7.5.1)
Tests that /metrics endpoint returns valid Prometheus-format metrics.
"""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.integration]


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""

    async def test_metrics_endpoint_returns_200(self, api_client: AsyncClient) -> None:
        """Test that /metrics endpoint is accessible."""
        response = await api_client.get("/metrics")
        assert response.status_code == 200

    async def test_metrics_returns_prometheus_format(
        self, api_client: AsyncClient
    ) -> None:
        """Test that /metrics returns valid Prometheus text format."""
        response = await api_client.get("/metrics")
        assert response.status_code == 200
        # Prometheus format uses text/plain with specific charset
        assert "text/plain" in response.headers.get("content-type", "")

    async def test_metrics_contains_http_request_metrics(
        self, api_client: AsyncClient
    ) -> None:
        """Test that HTTP request metrics are present."""
        # Make a request to generate some metrics
        await api_client.get("/api/v1/")

        response = await api_client.get("/metrics")
        content = response.text

        # Check for HTTP request duration histogram
        assert "lumikb_http_request_duration_seconds" in content

    async def test_metrics_contains_requests_inprogress(
        self, api_client: AsyncClient
    ) -> None:
        """Test that in-progress request gauge is present."""
        response = await api_client.get("/metrics")
        content = response.text

        assert "lumikb_http_requests_inprogress" in content

    async def test_metrics_contains_custom_gauges(
        self, api_client: AsyncClient
    ) -> None:
        """Test that custom application gauges are registered."""
        response = await api_client.get("/metrics")
        content = response.text

        # Check for queue depth gauge
        assert "lumikb_document_processing_queue_depth" in content

    async def test_metrics_excluded_from_instrumentation(
        self, api_client: AsyncClient
    ) -> None:
        """Test that /metrics endpoint doesn't instrument itself."""
        # Make multiple requests to /metrics
        for _ in range(3):
            await api_client.get("/metrics")

        response = await api_client.get("/metrics")
        content = response.text

        # The /metrics path should not appear in the metrics
        # (it's excluded from instrumentation)
        lines = content.split("\n")
        metrics_path_lines = [
            line
            for line in lines
            if 'path="/metrics"' in line and "lumikb_http_request" in line
        ]
        assert len(metrics_path_lines) == 0

    async def test_health_endpoints_excluded_from_instrumentation(
        self, api_client: AsyncClient
    ) -> None:
        """Test that health check endpoints are excluded from metrics."""
        # Make requests to health endpoints
        await api_client.get("/health")
        await api_client.get("/ready")
        await api_client.get("/api/health")

        response = await api_client.get("/metrics")
        content = response.text

        # Health paths should not appear in HTTP metrics
        lines = content.split("\n")
        health_path_lines = [
            line
            for line in lines
            if ('path="/health"' in line or 'path="/ready"' in line)
            and "lumikb_http_request" in line
        ]
        assert len(health_path_lines) == 0


class TestMetricsFormat:
    """Tests for Prometheus metrics format compliance."""

    async def test_metrics_has_help_lines(self, api_client: AsyncClient) -> None:
        """Test that metrics include HELP documentation."""
        response = await api_client.get("/metrics")
        content = response.text

        # Prometheus format should have HELP lines
        assert "# HELP" in content

    async def test_metrics_has_type_declarations(self, api_client: AsyncClient) -> None:
        """Test that metrics include TYPE declarations."""
        response = await api_client.get("/metrics")
        content = response.text

        # Prometheus format should have TYPE lines
        assert "# TYPE" in content

    async def test_metrics_histogram_has_buckets(self, api_client: AsyncClient) -> None:
        """Test that histogram metrics have bucket suffixes."""
        # Generate some request metrics
        await api_client.get("/api/v1/")

        response = await api_client.get("/metrics")
        content = response.text

        # Histograms should have _bucket, _count, _sum suffixes
        assert "_bucket{" in content
        assert "_count{" in content or "_count " in content
        assert "_sum{" in content or "_sum " in content


class TestCustomMetrics:
    """Tests for custom application metrics."""

    async def test_document_processing_metrics_registered(
        self, api_client: AsyncClient
    ) -> None:
        """Test that document processing metrics are registered."""
        response = await api_client.get("/metrics")
        content = response.text

        assert "lumikb_document_processing_queue_depth" in content
        assert "lumikb_document_processing_duration_seconds" in content
        assert "lumikb_document_processing_total" in content

    async def test_llm_metrics_registered(self, api_client: AsyncClient) -> None:
        """Test that LLM-related metrics are registered."""
        response = await api_client.get("/metrics")
        content = response.text

        assert "lumikb_llm_request_duration_seconds" in content
        assert "lumikb_llm_request_total" in content

    async def test_search_metrics_registered(self, api_client: AsyncClient) -> None:
        """Test that search metrics are registered."""
        response = await api_client.get("/metrics")
        content = response.text

        assert "lumikb_search_request_duration_seconds" in content

    async def test_embedding_metrics_registered(self, api_client: AsyncClient) -> None:
        """Test that embedding metrics are registered."""
        response = await api_client.get("/metrics")
        content = response.text

        assert "lumikb_embedding_batch_size" in content
        assert "lumikb_embedding_duration_seconds" in content
