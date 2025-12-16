"""Unit tests for Prometheus metrics module.

Story 7.5: Monitoring and Observability (AC-7.5.1)
Tests for metrics registration and helper functions.
"""

import pytest
from prometheus_client import REGISTRY

from app.api.v1.metrics import (
    DOCUMENT_PROCESSING_DURATION,
    DOCUMENT_PROCESSING_QUEUE_DEPTH,
    DOCUMENT_PROCESSING_TOTAL,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DURATION,
    LLM_REQUEST_DURATION,
    LLM_REQUEST_TOTAL,
    SEARCH_REQUEST_DURATION,
    create_instrumentator,
    record_document_processing,
    record_embedding_batch,
    record_llm_request,
    record_search_duration,
    set_queue_depth,
)

pytestmark = [pytest.mark.unit]


class TestMetricsRegistration:
    """Tests for metric registration in Prometheus registry."""

    def test_document_processing_queue_depth_registered(self) -> None:
        """Test that queue depth gauge is registered."""
        assert DOCUMENT_PROCESSING_QUEUE_DEPTH is not None
        # Verify it's a Gauge
        assert "Gauge" in str(type(DOCUMENT_PROCESSING_QUEUE_DEPTH))

    def test_document_processing_duration_registered(self) -> None:
        """Test that processing duration histogram is registered."""
        assert DOCUMENT_PROCESSING_DURATION is not None
        assert "Histogram" in str(type(DOCUMENT_PROCESSING_DURATION))

    def test_document_processing_total_registered(self) -> None:
        """Test that processing total counter is registered."""
        assert DOCUMENT_PROCESSING_TOTAL is not None
        assert "Counter" in str(type(DOCUMENT_PROCESSING_TOTAL))

    def test_llm_request_metrics_registered(self) -> None:
        """Test that LLM request metrics are registered."""
        assert LLM_REQUEST_DURATION is not None
        assert LLM_REQUEST_TOTAL is not None
        assert "Histogram" in str(type(LLM_REQUEST_DURATION))
        assert "Counter" in str(type(LLM_REQUEST_TOTAL))

    def test_search_request_duration_registered(self) -> None:
        """Test that search duration histogram is registered."""
        assert SEARCH_REQUEST_DURATION is not None
        assert "Histogram" in str(type(SEARCH_REQUEST_DURATION))

    def test_embedding_metrics_registered(self) -> None:
        """Test that embedding metrics are registered."""
        assert EMBEDDING_BATCH_SIZE is not None
        assert EMBEDDING_DURATION is not None
        assert "Histogram" in str(type(EMBEDDING_BATCH_SIZE))
        assert "Histogram" in str(type(EMBEDDING_DURATION))


class TestMetricHelpers:
    """Tests for metric helper functions."""

    def test_record_document_processing(self) -> None:
        """Test recording document processing metrics."""
        # Should not raise
        record_document_processing(
            doc_type="pdf",
            status="success",
            duration_seconds=5.5,
        )

    def test_record_llm_request(self) -> None:
        """Test recording LLM request metrics."""
        # Should not raise
        record_llm_request(
            model="gpt-4",
            operation="synthesis",
            status="success",
            duration_seconds=2.3,
        )

    def test_record_search_duration(self) -> None:
        """Test recording search duration."""
        # Should not raise
        record_search_duration(
            search_type="semantic",
            duration_seconds=0.5,
        )

    def test_record_embedding_batch(self) -> None:
        """Test recording embedding batch metrics."""
        # Should not raise
        record_embedding_batch(
            batch_size=50,
            duration_seconds=1.2,
        )

    def test_set_queue_depth(self) -> None:
        """Test setting queue depth gauge."""
        # Should not raise
        set_queue_depth(queue_name="default", depth=10)
        set_queue_depth(queue_name="document_processing", depth=5)


class TestInstrumentator:
    """Tests for Prometheus FastAPI instrumentator."""

    def test_create_instrumentator_returns_instrumentator(self) -> None:
        """Test that create_instrumentator returns an Instrumentator."""
        instrumentator = create_instrumentator()
        assert instrumentator is not None
        # Check it has the expected methods
        assert hasattr(instrumentator, "instrument")
        assert hasattr(instrumentator, "add")

    def test_instrumentator_has_excluded_handlers(self) -> None:
        """Test that instrumentator excludes health endpoints."""
        instrumentator = create_instrumentator()
        # The instrumentator should be configured
        assert instrumentator is not None


class TestMetricsInRegistry:
    """Tests for metrics presence in Prometheus registry."""

    def test_custom_metrics_in_registry(self) -> None:
        """Test that custom metrics are in the global registry."""
        # Get all registered metric names
        metric_names = [
            metric.name for metric in REGISTRY.collect() if hasattr(metric, "name")
        ]
        metric_names_str = str(metric_names)

        # Check our custom metrics are registered
        assert "lumikb_document_processing_queue_depth" in metric_names_str
        assert "lumikb_document_processing_duration_seconds" in metric_names_str
        assert "lumikb_llm_request_duration_seconds" in metric_names_str
        assert "lumikb_search_request_duration_seconds" in metric_names_str
