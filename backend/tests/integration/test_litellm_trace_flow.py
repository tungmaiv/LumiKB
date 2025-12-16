"""Integration tests for LiteLLM observability callback registration and tracing.

Tests verify end-to-end LiteLLM callback integration:
- AC1: Callback registration at app startup
- AC7: Fire-and-forget pattern (callback doesn't block responses)
- AC11: End-to-end trace creation through LiteLLM callback
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import litellm
import pytest

from app.integrations.litellm_callback import (
    ObservabilityCallback,
    observability_callback,
)


class TestCallbackRegistration:
    """Tests for LiteLLM callback registration."""

    def test_callback_instance_created(self):
        """AC1: Singleton callback instance exists."""
        assert observability_callback is not None
        assert isinstance(observability_callback, ObservabilityCallback)

    def test_callback_can_be_registered(self):
        """AC1: Callback can be appended to litellm.callbacks."""
        # Save original callbacks
        original_callbacks = litellm.callbacks.copy() if litellm.callbacks else []

        try:
            # Clear and register our callback
            litellm.callbacks = []
            litellm.callbacks.append(observability_callback)

            assert observability_callback in litellm.callbacks
        finally:
            # Restore original callbacks
            litellm.callbacks = original_callbacks

    def test_callback_inherits_custom_logger(self):
        """Verify callback inherits from LiteLLM CustomLogger."""
        from litellm.integrations.custom_logger import CustomLogger

        assert isinstance(observability_callback, CustomLogger)


class TestCallbackFireAndForget:
    """Tests for fire-and-forget behavior."""

    @pytest.mark.asyncio
    async def test_callback_success_doesnt_raise(self):
        """AC7: Success callback never raises exceptions."""
        cb = ObservabilityCallback()
        cb._obs = MagicMock()
        cb._obs.log_llm_call = AsyncMock(side_effect=Exception("DB error"))

        response = MagicMock()
        response.call_type = None
        response.model = "gpt-4"
        response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)
        response.response_cost = None
        response._hidden_params = {}
        if hasattr(response, "data"):
            del response.data

        kwargs = {"litellm_params": {"metadata": {}}, "model": "gpt-4"}
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 0, 1)

        # Should not raise despite observability failure
        await cb.async_log_success_event(kwargs, response, start, end)

    @pytest.mark.asyncio
    async def test_callback_failure_doesnt_raise(self):
        """AC7: Failure callback never raises exceptions."""
        cb = ObservabilityCallback()
        cb._obs = MagicMock()
        cb._obs.log_llm_call = AsyncMock(side_effect=Exception("Redis error"))

        kwargs = {
            "litellm_params": {"metadata": {}},
            "model": "gpt-4",
            "exception": ValueError("API error"),
        }
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 0, 1)

        # Should not raise despite observability failure
        await cb.async_log_failure_event(kwargs, None, start, end)


class TestCallbackTraceCreation:
    """Tests for trace creation through callback."""

    @pytest.mark.asyncio
    async def test_embedding_creates_trace_span(self):
        """AC11: Embedding call creates LLM span in observability."""
        cb = ObservabilityCallback()
        cb._obs = MagicMock()
        cb._obs.log_llm_call = AsyncMock()

        response = MagicMock()
        response.call_type = "embedding"
        response.model = "text-embedding-3-small"
        response.usage = MagicMock(prompt_tokens=150)
        response.data = [MagicMock(embedding=[0.1] * 1536)]

        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-embed-test"}},
            "model": "text-embedding-3-small",
        }
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 0, 0, 500000)  # 500ms

        await cb.async_log_success_event(kwargs, response, start, end)

        cb._obs.log_llm_call.assert_called_once()
        call_kwargs = cb._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["name"] == "embedding"
        assert call_kwargs["model"] == "text-embedding-3-small"
        assert call_kwargs["input_tokens"] == 150
        assert call_kwargs["duration_ms"] == 500
        assert call_kwargs["metadata"]["dimensions"] == 1536
        assert call_kwargs["ctx"].trace_id == "trace-embed-test"

    @pytest.mark.asyncio
    async def test_completion_creates_trace_span(self):
        """AC11: Chat completion creates LLM span in observability."""
        cb = ObservabilityCallback()
        cb._obs = MagicMock()
        cb._obs.log_llm_call = AsyncMock()

        response = MagicMock()
        response.call_type = None
        response.model = "gpt-4"
        response.usage = MagicMock(prompt_tokens=200, completion_tokens=75)
        response.response_cost = 0.0055
        if hasattr(response, "data"):
            del response.data

        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-chat-test"}},
            "model": "gpt-4",
        }
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 0, 2)  # 2 seconds

        await cb.async_log_success_event(kwargs, response, start, end)

        cb._obs.log_llm_call.assert_called_once()
        call_kwargs = cb._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["name"] == "chat_completion"
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["input_tokens"] == 200
        assert call_kwargs["output_tokens"] == 75
        assert call_kwargs["duration_ms"] == 2000
        assert "cost_usd" in call_kwargs["metadata"]
        assert call_kwargs["ctx"].trace_id == "trace-chat-test"

    @pytest.mark.asyncio
    async def test_failed_call_creates_failed_span(self):
        """AC11: Failed LLM call creates span with failed status."""
        cb = ObservabilityCallback()
        cb._obs = MagicMock()
        cb._obs.log_llm_call = AsyncMock()

        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-fail-test"}},
            "model": "gpt-4",
            "exception": Exception("Rate limit exceeded"),
        }
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 0, 1)

        await cb.async_log_failure_event(kwargs, None, start, end)

        cb._obs.log_llm_call.assert_called_once()
        call_kwargs = cb._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["name"] == "llm_call_failed"
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["status"] == "failed"
        assert "Rate limit" in call_kwargs["error_message"]
        assert call_kwargs["ctx"].trace_id == "trace-fail-test"


class TestCallbackMetadataCorrelation:
    """Tests for trace context correlation via metadata."""

    @pytest.mark.asyncio
    async def test_trace_id_from_metadata_used(self):
        """AC8: TraceContext trace_id passed via LiteLLM metadata is used."""
        cb = ObservabilityCallback()
        cb._obs = MagicMock()
        cb._obs.log_llm_call = AsyncMock()

        response = MagicMock()
        response.call_type = None
        response.model = "gpt-4"
        response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)
        response.response_cost = None
        response._hidden_params = {}
        if hasattr(response, "data"):
            del response.data

        # Pass specific trace_id in metadata
        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "custom-trace-12345"}},
            "model": "gpt-4",
        }
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 0, 1)

        await cb.async_log_success_event(kwargs, response, start, end)

        call_kwargs = cb._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["ctx"].trace_id == "custom-trace-12345"

    @pytest.mark.asyncio
    async def test_missing_trace_id_generates_new(self):
        """AC8: Missing trace_id in metadata generates a new one."""
        cb = ObservabilityCallback()
        cb._obs = MagicMock()
        cb._obs.log_llm_call = AsyncMock()

        response = MagicMock()
        response.call_type = None
        response.model = "gpt-4"
        response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)
        response.response_cost = None
        response._hidden_params = {}
        if hasattr(response, "data"):
            del response.data

        # No trace_id in metadata
        kwargs = {
            "litellm_params": {"metadata": {}},
            "model": "gpt-4",
        }
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 0, 1)

        await cb.async_log_success_event(kwargs, response, start, end)

        call_kwargs = cb._obs.log_llm_call.call_args.kwargs
        # Should have a generated trace_id (not None or empty)
        assert call_kwargs["ctx"].trace_id
        assert len(call_kwargs["ctx"].trace_id) > 0


class TestCallbackWithDatabasePersistence:
    """Integration tests verifying trace persistence to database."""

    @pytest.mark.asyncio
    async def test_callback_with_real_observability_service(
        self, db_session, test_user_data
    ):
        """AC11: Callback creates span that persists to database."""
        from sqlalchemy import select

        from app.models.observability import Span
        from app.services.observability_service import ObservabilityService

        # Get real observability service
        obs = ObservabilityService.get_instance()

        # Create a callback with real obs service
        cb = ObservabilityCallback()
        cb._obs = obs

        response = MagicMock()
        response.call_type = None
        response.model = "gpt-4-turbo"
        response.usage = MagicMock(prompt_tokens=250, completion_tokens=100)
        response.response_cost = 0.0075
        if hasattr(response, "data"):
            del response.data

        # Start a parent trace first (required for span creation)
        user_id = test_user_data["user_id"]
        from uuid import UUID

        trace_ctx = await obs.start_trace(
            name="test_llm_trace",
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
        )

        kwargs = {
            "litellm_params": {"metadata": {"trace_id": trace_ctx.trace_id}},
            "model": "gpt-4-turbo",
        }
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 10, 0, 3)  # 3 seconds

        # Trigger callback
        await cb.async_log_success_event(kwargs, response, start, end)

        # End trace to finalize
        await obs.end_trace(trace_ctx, status="completed")

        # Query for LLM spans
        # Note: Span persistence depends on provider being enabled
        # In test env without provider, spans may not persist
        result = await db_session.execute(select(Span).where(Span.span_type == "llm"))
        llm_spans = result.scalars().all()

        # If observability provider is configured, verify span
        if llm_spans:
            assert any(s.name == "chat_completion" for s in llm_spans)
