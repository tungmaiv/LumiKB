"""Integration tests for Observability Admin API.

Story 9-7: Observability Admin API

Tests for:
- Traces list and detail endpoints
- Chat history endpoint
- Document timeline endpoint
- Stats endpoint
- Admin authentication requirements
- Pagination and filtering
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import DocumentEvent, ObsChatMessage, Span, Trace
from app.models.user import User
from tests.factories import create_registration_data

# Test data prefixes (combined with unique suffix in fixture)
TRACE_PREFIX_1 = "a" * 24
TRACE_PREFIX_2 = "b" * 24
SPAN_PREFIX_1 = "1" * 8
SPAN_PREFIX_2 = "2" * 8
SPAN_PREFIX_3 = "3" * 8


def generate_trace_id(prefix: str) -> str:
    """Generate unique 32-char trace ID with given prefix."""
    import secrets

    suffix = secrets.token_hex(4)  # 8 hex chars
    return prefix + suffix


def generate_span_id(prefix: str) -> str:
    """Generate unique 16-char span ID with given prefix."""
    import secrets

    suffix = secrets.token_hex(4)  # 8 hex chars
    return prefix + suffix


# =============================================================================
# Admin and User Fixtures for Observability Tests
# =============================================================================


@pytest.fixture
async def admin_user_cookies(api_client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create an admin user and return auth cookies.

    Registers a user via API, then promotes to superuser in DB, then logs in.

    Returns:
        httpx.Cookies: Cookies for authenticated admin requests.
    """
    # Register unique admin user
    user_data = create_registration_data()
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert register_response.status_code == 201

    # Promote to admin in database
    result = await db_session.execute(
        select(User).where(User.email == user_data["email"])
    )
    user = result.scalar_one()
    user.is_superuser = True
    await db_session.commit()

    # Login to get JWT cookie
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code in (200, 204)

    return login_response.cookies


@pytest.fixture
async def regular_user_cookies(api_client: AsyncClient) -> dict:
    """Create a regular (non-admin) user and return auth cookies.

    Returns:
        httpx.Cookies: Cookies for authenticated non-admin requests.
    """
    # Register unique regular user
    user_data = create_registration_data()
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert register_response.status_code == 201

    # Login to get JWT cookie
    login_response = await api_client.post(
        "/api/v1/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )
    assert login_response.status_code in (200, 204)

    return login_response.cookies


@pytest.fixture
async def observability_test_data(db_session: AsyncSession) -> dict:
    """Create test data in observability schema."""
    now = datetime.now(UTC)
    user_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    document_id = uuid.uuid4()
    conversation_id = uuid.uuid4()

    # Generate unique IDs for this test run
    trace_id_1 = generate_trace_id(TRACE_PREFIX_1)
    trace_id_2 = generate_trace_id(TRACE_PREFIX_2)
    span_id_1 = generate_span_id(SPAN_PREFIX_1)
    span_id_2 = generate_span_id(SPAN_PREFIX_2)
    span_id_3 = generate_span_id(SPAN_PREFIX_3)

    # Create traces
    trace1 = Trace(
        trace_id=trace_id_1,
        timestamp=now - timedelta(hours=1),
        name="chat_completion",
        user_id=user_id,
        kb_id=kb_id,
        status="completed",
        duration_ms=1500,
        attributes={"model": "gpt-4"},
    )
    trace2 = Trace(
        trace_id=trace_id_2,
        timestamp=now - timedelta(hours=2),
        name="document_processing",
        user_id=user_id,
        kb_id=kb_id,
        status="failed",
        duration_ms=5000,
        attributes={"error": "timeout"},
    )

    # Create spans
    span1 = Span(
        span_id=span_id_1,
        trace_id=trace_id_1,
        timestamp=now - timedelta(hours=1),
        name="llm_call",
        span_type="llm",
        status="completed",
        duration_ms=800,
        input_tokens=100,
        output_tokens=200,
        model="gpt-4",
    )
    span2 = Span(
        span_id=span_id_2,
        trace_id=trace_id_1,
        parent_span_id=span_id_1,
        timestamp=now - timedelta(hours=1) + timedelta(seconds=1),
        name="embedding",
        span_type="embedding",
        status="completed",
        duration_ms=500,
    )
    span3 = Span(
        span_id=span_id_3,
        trace_id=trace_id_2,
        timestamp=now - timedelta(hours=2),
        name="parse_document",
        span_type="internal",
        status="failed",
        duration_ms=3000,
        error_message="Parsing failed",
    )

    # Create chat messages
    msg1 = ObsChatMessage(
        id=uuid.uuid4(),
        trace_id=trace_id_1,
        timestamp=now - timedelta(hours=1),
        user_id=user_id,
        kb_id=kb_id,
        conversation_id=conversation_id,
        role="user",
        content="What is the meaning of life?",
    )
    msg2 = ObsChatMessage(
        id=uuid.uuid4(),
        trace_id=trace_id_1,
        timestamp=now - timedelta(hours=1) + timedelta(seconds=2),
        user_id=user_id,
        kb_id=kb_id,
        conversation_id=conversation_id,
        role="assistant",
        content="The meaning of life is 42.",
        input_tokens=100,
        output_tokens=200,
        latency_ms=1500,
        model="gpt-4",
        attributes={
            "citations": [
                {
                    "index": 1,
                    "document_id": str(document_id),
                    "document_name": "Guide.pdf",
                }
            ]
        },
    )

    # Create document events
    event1 = DocumentEvent(
        id=uuid.uuid4(),
        trace_id=trace_id_2,
        timestamp=now - timedelta(hours=2),
        document_id=document_id,
        kb_id=kb_id,
        event_type="upload",
        status="completed",
        duration_ms=100,
    )
    event2 = DocumentEvent(
        id=uuid.uuid4(),
        trace_id=trace_id_2,
        timestamp=now - timedelta(hours=2) + timedelta(seconds=1),
        document_id=document_id,
        kb_id=kb_id,
        event_type="parse",
        status="completed",
        duration_ms=2000,
    )
    event3 = DocumentEvent(
        id=uuid.uuid4(),
        trace_id=trace_id_2,
        timestamp=now - timedelta(hours=2) + timedelta(seconds=3),
        document_id=document_id,
        kb_id=kb_id,
        event_type="chunk",
        status="completed",
        duration_ms=500,
        chunk_count=10,
    )
    event4 = DocumentEvent(
        id=uuid.uuid4(),
        trace_id=trace_id_2,
        timestamp=now - timedelta(hours=2) + timedelta(seconds=4),
        document_id=document_id,
        kb_id=kb_id,
        event_type="embed",
        status="failed",
        duration_ms=1000,
        error_message="Embedding service unavailable",
    )

    # Add all to session
    db_session.add_all(
        [
            trace1,
            trace2,
            span1,
            span2,
            span3,
            msg1,
            msg2,
            event1,
            event2,
            event3,
            event4,
        ]
    )
    await db_session.commit()

    return {
        "user_id": user_id,
        "kb_id": kb_id,
        "document_id": document_id,
        "conversation_id": conversation_id,
        "trace_id_1": trace_id_1,
        "trace_id_2": trace_id_2,
        "trace_ids": [trace_id_1, trace_id_2],
        "now": now,
    }


class TestListTraces:
    """Tests for GET /api/v1/observability/traces endpoint."""

    async def test_list_traces_requires_admin(
        self, api_client: AsyncClient, regular_user_cookies
    ):
        """Non-admin users should get 403."""
        response = await api_client.get(
            "/api/v1/observability/traces",
            cookies=regular_user_cookies,
        )
        assert response.status_code == 403

    async def test_list_traces_unauthenticated(self, api_client: AsyncClient):
        """Unauthenticated requests should get 401."""
        response = await api_client.get("/api/v1/observability/traces")
        assert response.status_code == 401

    async def test_list_traces_success(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Admin can list traces successfully."""
        response = await api_client.get(
            "/api/v1/observability/traces",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

        # Check trace structure
        trace = data["items"][0]
        assert "trace_id" in trace
        assert "name" in trace
        assert "status" in trace
        assert "started_at" in trace
        assert "span_count" in trace

    async def test_list_traces_filter_by_status(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Filter traces by status."""
        response = await api_client.get(
            "/api/v1/observability/traces",
            params={"status": "completed"},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(t["status"] == "completed" for t in data["items"])

    async def test_list_traces_filter_by_operation_type(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Filter traces by operation type."""
        response = await api_client.get(
            "/api/v1/observability/traces",
            params={"operation_type": "chat_completion"},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(t["name"] == "chat_completion" for t in data["items"])

    async def test_list_traces_filter_by_user_id(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Filter traces by user ID."""
        user_id = observability_test_data["user_id"]
        response = await api_client.get(
            "/api/v1/observability/traces",
            params={"user_id": str(user_id)},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2

    async def test_list_traces_pagination(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Test pagination parameters."""
        response = await api_client.get(
            "/api/v1/observability/traces",
            params={"skip": 0, "limit": 1},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["skip"] == 0
        assert data["limit"] == 1

    async def test_list_traces_pagination_max_limit(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
    ):
        """Limit cannot exceed 100."""
        response = await api_client.get(
            "/api/v1/observability/traces",
            params={"limit": 200},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 422  # Validation error


class TestGetTrace:
    """Tests for GET /api/v1/observability/traces/{trace_id} endpoint."""

    async def test_get_trace_success(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Get trace detail with spans."""
        trace_id_1 = observability_test_data["trace_id_1"]
        response = await api_client.get(
            f"/api/v1/observability/traces/{trace_id_1}",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["trace_id"] == trace_id_1
        assert data["name"] == "chat_completion"
        assert data["status"] == "completed"
        assert "spans" in data
        assert len(data["spans"]) == 2

        # Check spans are ordered by start time
        spans = data["spans"]
        for i in range(len(spans) - 1):
            assert spans[i]["started_at"] <= spans[i + 1]["started_at"]

    async def test_get_trace_not_found(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
    ):
        """Return 404 for non-existent trace."""
        fake_trace_id = "c" * 32
        response = await api_client.get(
            f"/api/v1/observability/traces/{fake_trace_id}",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 404

    async def test_get_trace_invalid_format(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
    ):
        """Return 400 for invalid trace ID format."""
        response = await api_client.get(
            "/api/v1/observability/traces/invalid-trace-id",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 400
        assert "Invalid trace_id format" in response.json()["detail"]

    async def test_get_trace_requires_admin(
        self,
        api_client: AsyncClient,
        regular_user_cookies,
        observability_test_data: dict,
    ):
        """Non-admin users should get 403."""
        trace_id_1 = observability_test_data["trace_id_1"]
        response = await api_client.get(
            f"/api/v1/observability/traces/{trace_id_1}",
            cookies=regular_user_cookies,
        )
        assert response.status_code == 403


class TestChatHistory:
    """Tests for GET /api/v1/observability/chat-history endpoint."""

    async def test_chat_history_success(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Get chat history successfully."""
        response = await api_client.get(
            "/api/v1/observability/chat-history",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2

    async def test_chat_history_filter_by_user(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Filter chat history by user ID."""
        user_id = observability_test_data["user_id"]
        response = await api_client.get(
            "/api/v1/observability/chat-history",
            params={"user_id": str(user_id)},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2

    async def test_chat_history_filter_by_kb(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Filter chat history by knowledge base ID."""
        kb_id = observability_test_data["kb_id"]
        response = await api_client.get(
            "/api/v1/observability/chat-history",
            params={"kb_id": str(kb_id)},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2

    async def test_chat_history_search_query(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Search chat history by content."""
        response = await api_client.get(
            "/api/v1/observability/chat-history",
            params={"search_query": "meaning of life"},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("meaning" in msg["content"].lower() for msg in data["items"])

    async def test_chat_history_includes_citations(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Chat history includes citations for assistant messages."""
        response = await api_client.get(
            "/api/v1/observability/chat-history",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()

        # Find assistant message with citations
        assistant_msgs = [m for m in data["items"] if m["role"] == "assistant"]
        assert len(assistant_msgs) >= 1

        # At least one should have citations
        msg_with_citations = [m for m in assistant_msgs if m.get("citations")]
        assert len(msg_with_citations) >= 1

    async def test_chat_history_pagination_max_limit(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
    ):
        """Chat history limit cannot exceed 500."""
        response = await api_client.get(
            "/api/v1/observability/chat-history",
            params={"limit": 600},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 422

    async def test_chat_history_requires_admin(
        self,
        api_client: AsyncClient,
        regular_user_cookies,
    ):
        """Non-admin users should get 403."""
        response = await api_client.get(
            "/api/v1/observability/chat-history",
            cookies=regular_user_cookies,
        )
        assert response.status_code == 403


class TestDocumentTimeline:
    """Tests for GET /api/v1/observability/documents/{document_id}/timeline endpoint."""

    async def test_document_timeline_success(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Get document timeline successfully."""
        document_id = observability_test_data["document_id"]
        response = await api_client.get(
            f"/api/v1/observability/documents/{document_id}/timeline",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == str(document_id)
        assert "events" in data
        assert len(data["events"]) == 4

        # Check events are ordered by timestamp
        events = data["events"]
        for i in range(len(events) - 1):
            assert events[i]["started_at"] <= events[i + 1]["started_at"]

    async def test_document_timeline_includes_metrics(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Document timeline includes step-specific metrics."""
        document_id = observability_test_data["document_id"]
        response = await api_client.get(
            f"/api/v1/observability/documents/{document_id}/timeline",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()

        # Find chunk event
        chunk_events = [e for e in data["events"] if e["step_name"] == "chunk"]
        assert len(chunk_events) == 1
        assert chunk_events[0]["metrics"]["chunk_count"] == 10

    async def test_document_timeline_not_found(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
    ):
        """Return 404 for document with no events."""
        fake_doc_id = uuid.uuid4()
        response = await api_client.get(
            f"/api/v1/observability/documents/{fake_doc_id}/timeline",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 404

    async def test_document_timeline_invalid_uuid(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
    ):
        """Return 422 for invalid UUID."""
        response = await api_client.get(
            "/api/v1/observability/documents/not-a-uuid/timeline",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 422

    async def test_document_timeline_requires_admin(
        self,
        api_client: AsyncClient,
        regular_user_cookies,
        observability_test_data: dict,
    ):
        """Non-admin users should get 403."""
        document_id = observability_test_data["document_id"]
        response = await api_client.get(
            f"/api/v1/observability/documents/{document_id}/timeline",
            cookies=regular_user_cookies,
        )
        assert response.status_code == 403


class TestStats:
    """Tests for GET /api/v1/observability/stats endpoint."""

    async def test_stats_success(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Get aggregated stats successfully."""
        response = await api_client.get(
            "/api/v1/observability/stats",
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert "time_period" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "llm_usage" in data
        assert "processing_metrics" in data
        assert "chat_metrics" in data
        assert "error_rate" in data

    async def test_stats_time_period_day(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Get stats for day period."""
        response = await api_client.get(
            "/api/v1/observability/stats",
            params={"time_period": "day"},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["time_period"] == "day"

    async def test_stats_time_period_week(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
    ):
        """Get stats for week period."""
        response = await api_client.get(
            "/api/v1/observability/stats",
            params={"time_period": "week"},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["time_period"] == "week"

    async def test_stats_invalid_time_period(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
    ):
        """Invalid time period returns validation error."""
        response = await api_client.get(
            "/api/v1/observability/stats",
            params={"time_period": "invalid"},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 422

    async def test_stats_filter_by_kb(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Filter stats by knowledge base ID."""
        kb_id = observability_test_data["kb_id"]
        response = await api_client.get(
            "/api/v1/observability/stats",
            params={"kb_id": str(kb_id)},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200

    async def test_stats_requires_admin(
        self,
        api_client: AsyncClient,
        regular_user_cookies,
    ):
        """Non-admin users should get 403."""
        response = await api_client.get(
            "/api/v1/observability/stats",
            cookies=regular_user_cookies,
        )
        assert response.status_code == 403

    async def test_stats_llm_usage_breakdown(
        self,
        api_client: AsyncClient,
        admin_user_cookies,
        observability_test_data: dict,
    ):
        """Stats includes LLM usage breakdown by model."""
        response = await api_client.get(
            "/api/v1/observability/stats",
            params={"time_period": "day"},
            cookies=admin_user_cookies,
        )
        assert response.status_code == 200
        data = response.json()
        llm_usage = data["llm_usage"]
        assert "total_requests" in llm_usage
        assert "total_input_tokens" in llm_usage
        assert "total_output_tokens" in llm_usage
        assert "by_model" in llm_usage
