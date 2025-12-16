"""Unit tests for LiteLLM observability callback.

Tests verify callback handler behavior for Story 9-6 acceptance criteria:
- AC1: success_callback and failure_callback hooks
- AC2: Embedding calls create LLM spans
- AC3: Chat completion calls create LLM spans
- AC4: Streaming completions aggregate token counts
- AC5: Cost tracking
- AC6: Failed calls log error without prompt content
- AC7: Fire-and-forget pattern
- AC8: TraceContext passed via metadata
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.litellm_callback import ObservabilityCallback


class TestObservabilityCallbackSuccess:
    """Tests for successful LLM call tracing."""

    @pytest.fixture
    def callback(self):
        """Create callback instance with mocked observability service."""
        cb = ObservabilityCallback()
        cb._obs = MagicMock()
        cb._obs.log_llm_call = AsyncMock()
        return cb

    @pytest.fixture
    def embedding_response(self):
        """Mock embedding response."""
        response = MagicMock()
        response.call_type = "embedding"
        response.model = "text-embedding-3-small"
        response.usage = MagicMock(prompt_tokens=100)
        response.data = [MagicMock(embedding=[0.1] * 1536)]
        return response

    @pytest.fixture
    def completion_response(self):
        """Mock chat completion response."""
        response = MagicMock()
        response.call_type = None  # Simulates fallback detection
        response.model = "gpt-4"
        response.usage = MagicMock(prompt_tokens=150, completion_tokens=50)
        response.response_cost = 0.0045
        # No 'data' attribute triggers completion detection
        del response.data
        return response

    @pytest.mark.asyncio
    async def test_ac1_success_callback_called(self, callback, completion_response):
        """AC1: success_callback hook is invoked on LLM success."""
        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-abc123"}},
            "model": "gpt-4",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 1)  # 1 second

        await callback.async_log_success_event(
            kwargs, completion_response, start_time, end_time
        )

        callback._obs.log_llm_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_ac2_embedding_creates_llm_span(self, callback, embedding_response):
        """AC2: Embedding calls create LLM spans with model, input_tokens, dimensions."""
        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-embed-123"}},
            "model": "text-embedding-3-small",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 0, 500000)  # 500ms

        await callback.async_log_success_event(
            kwargs, embedding_response, start_time, end_time
        )

        callback._obs.log_llm_call.assert_called_once()
        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["name"] == "embedding"
        assert call_kwargs["model"] == "text-embedding-3-small"
        assert call_kwargs["input_tokens"] == 100
        assert call_kwargs["duration_ms"] == 500
        assert call_kwargs["metadata"]["dimensions"] == 1536

    @pytest.mark.asyncio
    async def test_ac3_completion_creates_llm_span(self, callback, completion_response):
        """AC3: Chat completion calls create LLM spans with token counts."""
        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-chat-123"}},
            "model": "gpt-4",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 2)  # 2 seconds

        await callback.async_log_success_event(
            kwargs, completion_response, start_time, end_time
        )

        callback._obs.log_llm_call.assert_called_once()
        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["name"] == "chat_completion"
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["input_tokens"] == 150
        assert call_kwargs["output_tokens"] == 50
        assert call_kwargs["duration_ms"] == 2000

    @pytest.mark.asyncio
    async def test_ac4_streaming_aggregates_tokens(self, callback):
        """AC4: Streaming completions use aggregated token counts from final response."""
        # Streaming response has final aggregated token counts
        streaming_response = MagicMock()
        streaming_response.call_type = None
        streaming_response.model = "gpt-4"
        streaming_response.usage = MagicMock(
            prompt_tokens=200,
            completion_tokens=100,  # Aggregated
        )
        streaming_response.response_cost = 0.0090
        # Remove data attr to trigger completion path
        if hasattr(streaming_response, "data"):
            del streaming_response.data

        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-stream-123"}},
            "model": "gpt-4",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 5)  # 5 seconds

        await callback.async_log_success_event(
            kwargs, streaming_response, start_time, end_time
        )

        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["input_tokens"] == 200
        assert call_kwargs["output_tokens"] == 100

    @pytest.mark.asyncio
    async def test_ac5_cost_tracking_extracted(self, callback, completion_response):
        """AC5: Cost tracking extracts cost_usd from LiteLLM response."""
        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-cost-123"}},
            "model": "gpt-4",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 1)

        await callback.async_log_success_event(
            kwargs, completion_response, start_time, end_time
        )

        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert "cost_usd" in call_kwargs["metadata"]
        # Stored as string for precision
        assert call_kwargs["metadata"]["cost_usd"] == str(Decimal("0.0045"))

    @pytest.mark.asyncio
    async def test_ac8_trace_context_from_metadata(self, callback, completion_response):
        """AC8: TraceContext passed via LiteLLM metadata for correlation."""
        trace_id = "trace-correlation-abc123"
        kwargs = {
            "litellm_params": {"metadata": {"trace_id": trace_id}},
            "model": "gpt-4",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 1)

        await callback.async_log_success_event(
            kwargs, completion_response, start_time, end_time
        )

        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["ctx"].trace_id == trace_id


class TestObservabilityCallbackFailure:
    """Tests for failed LLM call tracing."""

    @pytest.fixture
    def callback(self):
        """Create callback instance with mocked observability service."""
        cb = ObservabilityCallback()
        cb._obs = MagicMock()
        cb._obs.log_llm_call = AsyncMock()
        return cb

    @pytest.mark.asyncio
    async def test_ac1_failure_callback_called(self, callback):
        """AC1: failure_callback hook is invoked on LLM failure."""
        exception = ValueError("API key invalid")
        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-fail-123"}},
            "model": "gpt-4",
            "exception": exception,
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 0, 500000)

        await callback.async_log_failure_event(kwargs, None, start_time, end_time)

        callback._obs.log_llm_call.assert_called_once()
        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["status"] == "failed"

    @pytest.mark.asyncio
    async def test_ac6_error_logged_without_prompt_content(self, callback):
        """AC6: Failed calls log error type and message without exposing prompt content."""
        exception = Exception("Connection timeout after 30s")
        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-err-123"}},
            "model": "gpt-4",
            "exception": exception,
            # Note: prompt content should NOT appear in logged error
            "messages": [{"role": "user", "content": "Secret internal data"}],
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 30)

        await callback.async_log_failure_event(kwargs, None, start_time, end_time)

        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["name"] == "llm_call_failed"
        assert "Exception" in call_kwargs["error_message"]
        assert "Connection timeout" in call_kwargs["error_message"]
        # Prompt content should NOT be in error message
        assert "Secret internal data" not in call_kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_ac6_error_message_truncated(self, callback):
        """AC6: Error messages truncated to prevent large logs."""
        long_error = "A" * 500  # Very long error message
        exception = Exception(long_error)
        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-long-err"}},
            "model": "gpt-4",
            "exception": exception,
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 1)

        await callback.async_log_failure_event(kwargs, None, start_time, end_time)

        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        # Error message should be truncated (200 chars max)
        assert len(call_kwargs["error_message"]) <= 220  # 200 + "Exception: " prefix


class TestObservabilityCallbackFireAndForget:
    """Tests for fire-and-forget pattern."""

    @pytest.fixture
    def callback(self):
        """Create callback instance."""
        return ObservabilityCallback()

    @pytest.mark.asyncio
    async def test_ac7_success_never_blocks(self, callback):
        """AC7: Success callback never blocks even on observability errors."""
        # Mock observability service to raise exception
        callback._obs = MagicMock()
        callback._obs.log_llm_call = AsyncMock(
            side_effect=Exception("DB connection failed")
        )

        completion_response = MagicMock()
        completion_response.call_type = None
        completion_response.model = "gpt-4"
        completion_response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)
        if hasattr(completion_response, "data"):
            del completion_response.data

        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-123"}},
            "model": "gpt-4",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 1)

        # Should NOT raise exception despite observability failure
        await callback.async_log_success_event(
            kwargs, completion_response, start_time, end_time
        )
        # Test passes if no exception raised

    @pytest.mark.asyncio
    async def test_ac7_failure_never_blocks(self, callback):
        """AC7: Failure callback never blocks even on observability errors."""
        callback._obs = MagicMock()
        callback._obs.log_llm_call = AsyncMock(
            side_effect=Exception("Redis unavailable")
        )

        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-123"}},
            "model": "gpt-4",
            "exception": ValueError("API error"),
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 1)

        # Should NOT raise exception
        await callback.async_log_failure_event(kwargs, None, start_time, end_time)
        # Test passes if no exception raised


class TestObservabilityCallbackEdgeCases:
    """Tests for edge cases and fallback behavior."""

    @pytest.fixture
    def callback(self):
        """Create callback instance with mocked observability service."""
        cb = ObservabilityCallback()
        cb._obs = MagicMock()
        cb._obs.log_llm_call = AsyncMock()
        return cb

    @pytest.mark.asyncio
    async def test_missing_trace_id_generates_new(self, callback):
        """When trace_id not in metadata, generates a new one."""
        completion_response = MagicMock()
        completion_response.call_type = None
        completion_response.model = "gpt-4"
        completion_response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)
        completion_response.response_cost = None  # Explicitly set to None
        completion_response._hidden_params = {}  # No hidden cost either
        if hasattr(completion_response, "data"):
            del completion_response.data

        # No trace_id in metadata
        kwargs = {
            "litellm_params": {"metadata": {}},
            "model": "gpt-4",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 1)

        await callback.async_log_success_event(
            kwargs, completion_response, start_time, end_time
        )

        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        # Should have a generated trace_id
        assert call_kwargs["ctx"].trace_id is not None

    @pytest.mark.asyncio
    async def test_embedding_dict_response(self, callback):
        """Handle embedding response with dict items (not objects)."""
        embedding_response = MagicMock()
        embedding_response.call_type = "embedding"
        embedding_response.model = "text-embedding-ada-002"
        embedding_response.usage = MagicMock(prompt_tokens=50)
        # Dict-style embedding data
        embedding_response.data = [{"embedding": [0.2] * 768}]

        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-dict-123"}},
            "model": "text-embedding-ada-002",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 0, 300000)

        await callback.async_log_success_event(
            kwargs, embedding_response, start_time, end_time
        )

        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["metadata"]["dimensions"] == 768

    @pytest.mark.asyncio
    async def test_missing_usage_data(self, callback):
        """Handle response with missing usage data."""
        completion_response = MagicMock()
        completion_response.call_type = None
        completion_response.model = "gpt-4"
        completion_response.usage = None  # No usage data
        completion_response.response_cost = None  # Explicitly set to None
        completion_response._hidden_params = {}  # No hidden cost either
        if hasattr(completion_response, "data"):
            del completion_response.data

        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-no-usage"}},
            "model": "gpt-4",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 1)

        await callback.async_log_success_event(
            kwargs, completion_response, start_time, end_time
        )

        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["input_tokens"] is None
        assert call_kwargs["output_tokens"] is None

    @pytest.mark.asyncio
    async def test_cost_from_hidden_params(self, callback):
        """AC5: Extract cost from _hidden_params when response_cost not available."""
        completion_response = MagicMock()
        completion_response.call_type = None
        completion_response.model = "gpt-4"
        completion_response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)
        completion_response.response_cost = None
        completion_response._hidden_params = {"response_cost": 0.0025}
        if hasattr(completion_response, "data"):
            del completion_response.data

        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-hidden-cost"}},
            "model": "gpt-4",
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 1)

        await callback.async_log_success_event(
            kwargs, completion_response, start_time, end_time
        )

        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert call_kwargs["metadata"]["cost_usd"] == str(Decimal("0.0025"))

    @pytest.mark.asyncio
    async def test_unknown_exception_type(self, callback):
        """Handle failure with unknown exception type gracefully."""
        kwargs = {
            "litellm_params": {"metadata": {"trace_id": "trace-unknown"}},
            "model": "gpt-4",
            "exception": None,  # No exception object
        }
        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 1)

        await callback.async_log_failure_event(kwargs, None, start_time, end_time)

        call_kwargs = callback._obs.log_llm_call.call_args.kwargs
        assert "Unknown" in call_kwargs["error_message"]


class TestObservabilityCallbackIntegration:
    """Integration-like tests for callback registration."""

    def test_singleton_instance_exists(self):
        """Verify singleton callback instance is available for registration."""
        from app.integrations.litellm_callback import observability_callback

        assert observability_callback is not None
        assert isinstance(observability_callback, ObservabilityCallback)

    def test_callback_inherits_custom_logger(self):
        """Verify callback inherits from LiteLLM CustomLogger."""
        from litellm.integrations.custom_logger import CustomLogger

        cb = ObservabilityCallback()
        assert isinstance(cb, CustomLogger)

    def test_callback_lazy_init(self):
        """Verify observability service is lazily initialized."""
        cb = ObservabilityCallback()
        # _obs should be None initially
        assert cb._obs is None

        # Access through property initializes it
        with patch(
            "app.integrations.litellm_callback.ObservabilityService.get_instance"
        ) as mock_get:
            mock_get.return_value = MagicMock()
            obs = cb.obs
            assert obs is not None
            mock_get.assert_called_once()
