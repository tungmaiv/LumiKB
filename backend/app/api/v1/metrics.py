"""Prometheus metrics endpoint and instrumentation.

Story 7.5: Monitoring and Observability (AC-7.5.1)
Exposes /metrics endpoint with Prometheus-format metrics:
- HTTP request latency (histogram with method, path, status labels)
- HTTP request totals (counter with method, path, status labels)
- Document processing queue depth (gauge)
- Document processing duration (histogram with doc_type label)
"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.requests import Request
from starlette.responses import Response

# =============================================================================
# Custom Application Metrics
# =============================================================================
# Following the RED method: Rate, Errors, Duration

# Document Processing Metrics
DOCUMENT_PROCESSING_QUEUE_DEPTH = Gauge(
    "lumikb_document_processing_queue_depth",
    "Number of documents currently in processing queue",
    ["queue_name"],
)

DOCUMENT_PROCESSING_DURATION = Histogram(
    "lumikb_document_processing_duration_seconds",
    "Time spent processing documents",
    ["doc_type", "status"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)

DOCUMENT_PROCESSING_TOTAL = Counter(
    "lumikb_document_processing_total",
    "Total number of documents processed",
    ["doc_type", "status"],
)

# LLM/Search Metrics
LLM_REQUEST_DURATION = Histogram(
    "lumikb_llm_request_duration_seconds",
    "Time spent on LLM API calls",
    ["model", "operation"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

LLM_REQUEST_TOTAL = Counter(
    "lumikb_llm_request_total",
    "Total number of LLM API calls",
    ["model", "operation", "status"],
)

SEARCH_REQUEST_DURATION = Histogram(
    "lumikb_search_request_duration_seconds",
    "Time spent on semantic search operations",
    ["search_type"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
)

# Embedding Metrics
EMBEDDING_BATCH_SIZE = Histogram(
    "lumikb_embedding_batch_size",
    "Number of chunks per embedding batch",
    buckets=(1, 5, 10, 25, 50, 100, 200),
)

EMBEDDING_DURATION = Histogram(
    "lumikb_embedding_duration_seconds",
    "Time spent generating embeddings",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

# Active Sessions/Users
ACTIVE_SESSIONS = Gauge(
    "lumikb_active_sessions",
    "Number of active user sessions",
)

# Knowledge Base Metrics
KNOWLEDGE_BASE_COUNT = Gauge(
    "lumikb_knowledge_base_count",
    "Total number of knowledge bases",
)

DOCUMENT_COUNT = Gauge(
    "lumikb_document_count",
    "Total number of documents",
    ["status"],
)


# =============================================================================
# Prometheus FastAPI Instrumentator
# =============================================================================


def create_instrumentator() -> Instrumentator:
    """Create and configure the Prometheus instrumentator.

    Returns a configured instrumentator that:
    - Tracks request latency with histogram
    - Tracks request count with labels
    - Excludes /metrics endpoint from instrumentation
    - Excludes health check endpoints from instrumentation
    """
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=[
            "/metrics",
            "/health",
            "/ready",
            "/api/health",
            "/api/v1/health/liveness",
            "/api/v1/health/readiness",
        ],
        inprogress_name="lumikb_http_requests_inprogress",
        inprogress_labels=True,
    )

    # Add default metrics
    instrumentator.add(
        default_latency_histogram(),
    ).add(
        default_request_size_histogram(),
    ).add(
        default_response_size_histogram(),
    )

    return instrumentator


def default_latency_histogram():
    """Add latency histogram metric."""
    from prometheus_fastapi_instrumentator.metrics import latency

    return latency(
        metric_name="lumikb_http_request_duration_seconds",
        metric_doc="HTTP request latency in seconds",
        buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0),
    )


def default_request_size_histogram():
    """Add request size histogram metric."""
    from prometheus_fastapi_instrumentator.metrics import request_size

    return request_size(
        metric_name="lumikb_http_request_size_bytes",
        metric_doc="HTTP request size in bytes",
    )


def default_response_size_histogram():
    """Add response size histogram metric."""
    from prometheus_fastapi_instrumentator.metrics import response_size

    return response_size(
        metric_name="lumikb_http_response_size_bytes",
        metric_doc="HTTP response size in bytes",
    )


# =============================================================================
# Metrics Endpoint
# =============================================================================


async def metrics_endpoint(request: Request) -> Response:  # noqa: ARG001
    """Prometheus metrics endpoint.

    Returns metrics in Prometheus text format.
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# =============================================================================
# Metric Helper Functions
# =============================================================================


def record_document_processing(
    doc_type: str,
    status: str,
    duration_seconds: float,
) -> None:
    """Record document processing metrics.

    Args:
        doc_type: Type of document (pdf, docx, md, txt)
        status: Processing status (success, failed)
        duration_seconds: Time taken to process
    """
    DOCUMENT_PROCESSING_DURATION.labels(
        doc_type=doc_type,
        status=status,
    ).observe(duration_seconds)
    DOCUMENT_PROCESSING_TOTAL.labels(
        doc_type=doc_type,
        status=status,
    ).inc()


def record_llm_request(
    model: str,
    operation: str,
    status: str,
    duration_seconds: float,
) -> None:
    """Record LLM request metrics.

    Args:
        model: LLM model name
        operation: Operation type (synthesis, explanation, generation)
        status: Request status (success, failed)
        duration_seconds: Time taken for request
    """
    LLM_REQUEST_DURATION.labels(
        model=model,
        operation=operation,
    ).observe(duration_seconds)
    LLM_REQUEST_TOTAL.labels(
        model=model,
        operation=operation,
        status=status,
    ).inc()


def record_search_duration(search_type: str, duration_seconds: float) -> None:
    """Record search operation duration.

    Args:
        search_type: Type of search (semantic, similar, cross_kb)
        duration_seconds: Time taken for search
    """
    SEARCH_REQUEST_DURATION.labels(search_type=search_type).observe(duration_seconds)


def record_embedding_batch(batch_size: int, duration_seconds: float) -> None:
    """Record embedding batch metrics.

    Args:
        batch_size: Number of chunks in batch
        duration_seconds: Time taken to generate embeddings
    """
    EMBEDDING_BATCH_SIZE.observe(batch_size)
    EMBEDDING_DURATION.observe(duration_seconds)


def set_queue_depth(queue_name: str, depth: int) -> None:
    """Set the current queue depth.

    Args:
        queue_name: Name of the queue (default, document_processing)
        depth: Current number of items in queue
    """
    DOCUMENT_PROCESSING_QUEUE_DEPTH.labels(queue_name=queue_name).set(depth)


def set_active_sessions(count: int) -> None:
    """Set the current number of active sessions.

    Args:
        count: Number of active sessions
    """
    ACTIVE_SESSIONS.set(count)


def set_knowledge_base_count(count: int) -> None:
    """Set the total number of knowledge bases.

    Args:
        count: Total KB count
    """
    KNOWLEDGE_BASE_COUNT.set(count)


def set_document_count(status: str, count: int) -> None:
    """Set the total number of documents by status.

    Args:
        status: Document status (ready, processing, failed)
        count: Document count for that status
    """
    DOCUMENT_COUNT.labels(status=status).set(count)
