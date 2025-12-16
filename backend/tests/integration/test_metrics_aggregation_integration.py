"""Integration tests for Metrics Aggregation Worker.

Story 9-13: Metrics Aggregation Worker

RED PHASE: All tests are designed to FAIL until implementation is complete.
These tests verify the Celery beat task and API endpoints for metrics aggregation.

Run with: pytest backend/tests/integration/test_metrics_aggregation_integration.py -v
"""

import pytest
from httpx import AsyncClient

from tests.factories import (
    create_llm_span,
    generate_trace_id,
)


class TestMetricsAggregationTask:
    """Tests for AC1: Celery beat task runs hourly."""

    @pytest.mark.asyncio
    async def test_hourly_aggregation_task_exists(self) -> None:
        """Verify hourly aggregation task is scheduled."""
        from app.workers.celery_app import app

        schedule = app.conf.beat_schedule
        hourly_task = schedule.get("aggregate-observability-metrics-hourly")

        assert hourly_task is not None
        assert "aggregate_observability_metrics" in hourly_task["task"]

    @pytest.mark.asyncio
    async def test_daily_aggregation_task_exists(self) -> None:
        """Verify daily aggregation task is scheduled."""
        from app.workers.celery_app import app

        schedule = app.conf.beat_schedule
        daily_task = schedule.get("aggregate-observability-metrics-daily")

        assert daily_task is not None
        assert "aggregate_observability_metrics" in daily_task["task"]


class TestAggregatedMetricsAPI:
    """Tests for AC2: API returns aggregated metrics."""

    @pytest.mark.asyncio
    async def test_get_aggregated_metrics_requires_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Unauthenticated requests should be rejected."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_aggregated_metrics_returns_data(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should return aggregated metrics data."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day", "granularity": "hour"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have metric categories
        assert "llm_usage" in data or "llmUsage" in data
        assert "processing_pipeline" in data or "processingPipeline" in data
        assert "chat_activity" in data or "chatActivity" in data
        assert "system_health" in data or "systemHealth" in data


class TestLLMUsageAggregation:
    """Tests for AC3: LLM usage metrics aggregation."""

    @pytest.mark.asyncio
    async def test_aggregates_token_counts(
        self, async_client: AsyncClient, admin_token: str, db_session
    ) -> None:
        """Should aggregate total token counts."""
        # Create test LLM spans with token data
        trace_id = generate_trace_id()
        span1 = create_llm_span(
            trace_id=trace_id,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        span2 = create_llm_span(
            trace_id=trace_id,
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
        )
        db_session.add_all([span1, span2])
        await db_session.commit()

        # Trigger aggregation
        from app.workers.metrics_aggregation_tasks import (
            aggregate_observability_metrics,
        )

        aggregate_observability_metrics.delay(granularity="hour")

        # Fetch aggregated metrics
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day"},
        )

        assert response.status_code == 200
        data = response.json()

        llm_data = data.get("llm_usage") or data.get("llmUsage")
        assert llm_data is not None
        assert "total_tokens" in llm_data or "totalTokens" in llm_data

    @pytest.mark.asyncio
    async def test_aggregates_by_model(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should aggregate metrics by model."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day", "dimension": "model"},
        )

        assert response.status_code == 200
        data = response.json()

        llm_data = data.get("llm_usage") or data.get("llmUsage")
        if llm_data:
            assert "by_model" in llm_data or "byModel" in llm_data


class TestProcessingPipelineAggregation:
    """Tests for AC4: Document processing metrics."""

    @pytest.mark.asyncio
    async def test_aggregates_document_counts(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should aggregate document processing counts."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day"},
        )

        assert response.status_code == 200
        data = response.json()

        processing_data = data.get("processing_pipeline") or data.get(
            "processingPipeline"
        )
        assert processing_data is not None
        assert (
            "documents_processed" in processing_data
            or "documentsProcessed" in processing_data
        )

    @pytest.mark.asyncio
    async def test_calculates_error_rate(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should calculate error rate percentage."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day"},
        )

        assert response.status_code == 200
        data = response.json()

        processing_data = data.get("processing_pipeline") or data.get(
            "processingPipeline"
        )
        if processing_data:
            assert "error_rate" in processing_data or "errorRate" in processing_data


class TestChatActivityAggregation:
    """Tests for AC5: Chat activity metrics."""

    @pytest.mark.asyncio
    async def test_aggregates_message_counts(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should aggregate chat message counts."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day"},
        )

        assert response.status_code == 200
        data = response.json()

        chat_data = data.get("chat_activity") or data.get("chatActivity")
        assert chat_data is not None
        assert "message_count" in chat_data or "messageCount" in chat_data

    @pytest.mark.asyncio
    async def test_calculates_avg_response_time(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should calculate average response time."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day"},
        )

        assert response.status_code == 200
        data = response.json()

        chat_data = data.get("chat_activity") or data.get("chatActivity")
        if chat_data:
            assert (
                "avg_response_time_ms" in chat_data or "avgResponseTimeMs" in chat_data
            )


class TestSystemHealthAggregation:
    """Tests for AC6: System health metrics."""

    @pytest.mark.asyncio
    async def test_calculates_success_rate(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should calculate trace success rate."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day"},
        )

        assert response.status_code == 200
        data = response.json()

        health_data = data.get("system_health") or data.get("systemHealth")
        assert health_data is not None
        assert "trace_success_rate" in health_data or "traceSuccessRate" in health_data

    @pytest.mark.asyncio
    async def test_calculates_percentiles(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should calculate p95 latency percentile."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day"},
        )

        assert response.status_code == 200
        data = response.json()

        health_data = data.get("system_health") or data.get("systemHealth")
        if health_data:
            assert "p95_latency_ms" in health_data or "p95LatencyMs" in health_data


class TestPeriodFiltering:
    """Tests for AC7: Period-based filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_hour(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should filter metrics by hour."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "hour"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_by_day(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should filter metrics by day."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_by_week(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should filter metrics by week."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "week"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_by_month(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should filter metrics by month."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "month"},
        )

        assert response.status_code == 200


class TestDimensionGrouping:
    """Tests for AC8: Dimension-based grouping."""

    @pytest.mark.asyncio
    async def test_group_by_operation_type(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should group metrics by operation type."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day", "dimension": "operation_type"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_group_by_kb(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should group metrics by knowledge base."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day", "dimension": "kb_id"},
        )

        assert response.status_code == 200


class TestTrendData:
    """Tests for AC9: Trend data for sparklines."""

    @pytest.mark.asyncio
    async def test_returns_trend_data(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Should return trend data points for sparklines."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day", "include_trend": "true"},
        )

        assert response.status_code == 200
        data = response.json()

        # Each metric category should have trend data
        llm_data = data.get("llm_usage") or data.get("llmUsage")
        if llm_data:
            assert "trend" in llm_data
            assert isinstance(llm_data["trend"], list)

    @pytest.mark.asyncio
    async def test_trend_data_has_timestamps(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Trend data points should have timestamps."""
        response = await async_client.get(
            "/api/v1/admin/observability/metrics/aggregated",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"period": "day", "include_trend": "true"},
        )

        assert response.status_code == 200
        data = response.json()

        llm_data = data.get("llm_usage") or data.get("llmUsage")
        if llm_data and llm_data.get("trend"):
            for point in llm_data["trend"]:
                assert "timestamp" in point
                assert "value" in point


class TestBackfillAPI:
    """Tests for AC10: Backfill capability."""

    @pytest.mark.asyncio
    async def test_backfill_requires_admin(
        self, async_client: AsyncClient, regular_user_token: str
    ) -> None:
        """Backfill should require admin role."""
        response = await async_client.post(
            "/api/v1/admin/observability/metrics/backfill",
            headers={"Authorization": f"Bearer {regular_user_token}"},
            json={
                "start_date": "2025-12-01",
                "end_date": "2025-12-02",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_backfill_processes_date_range(
        self, async_client: AsyncClient, admin_token: str
    ) -> None:
        """Backfill should process specified date range."""
        response = await async_client.post(
            "/api/v1/admin/observability/metrics/backfill",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "start_date": "2025-12-01",
                "end_date": "2025-12-02",
                "granularity": "hour",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "buckets_processed" in data
        assert data["buckets_processed"] >= 0
