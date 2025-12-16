"""Integration tests for end-to-end observability trace flow (Story 9-3).

Tests verify complete trace lifecycle with ObservabilityService:
- start_trace -> span -> end_trace flow
- Nested spans with parent references
- Error capture in span context manager
- Timing accuracy with controlled intervals
- Fire-and-forget behavior (mocked database)

These tests verify AC #7 and #10 from Story 9-3:
- AC #7: span() async context manager handles timing, error capture, cleanup
- AC #10: Integration test demonstrates end-to-end trace flow
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.observability_service import (
    ObservabilityProvider,
    ObservabilityService,
    generate_span_id,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset ObservabilityService singleton before and after each test."""
    ObservabilityService.reset_instance()
    yield
    ObservabilityService.reset_instance()


def create_mock_provider(name: str = "mock") -> MagicMock:
    """Create a mock observability provider with all required methods."""
    provider = MagicMock(spec=ObservabilityProvider)
    provider.name = name
    provider.enabled = True
    provider.start_trace = AsyncMock()
    provider.end_trace = AsyncMock()
    provider.start_span = AsyncMock()
    provider.end_span = AsyncMock()
    provider.log_llm_call = AsyncMock(return_value=generate_span_id())
    provider.log_chat_message = AsyncMock()
    provider.log_document_event = AsyncMock()
    return provider


@pytest.mark.asyncio
class TestCompleteTraceFlow:
    """Tests for complete trace lifecycle (AC #10)."""

    async def test_start_trace_creates_context_with_valid_ids(self) -> None:
        """
        GIVEN: ObservabilityService with mock provider
        WHEN: Calling start_trace()
        THEN: TraceContext with valid W3C IDs is returned
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(
            name="chat.conversation",
            user_id=uuid4(),
            session_id=str(uuid4()),
            kb_id=uuid4(),
        )

        # Verify W3C compliant IDs
        assert len(ctx.trace_id) == 32
        assert len(ctx.span_id) == 16
        assert ctx.timestamp is not None

        # Verify provider was called
        provider.start_trace.assert_called_once()
        call_kwargs = provider.start_trace.call_args.kwargs
        assert call_kwargs["name"] == "chat.conversation"
        assert call_kwargs["trace_id"] == ctx.trace_id

    async def test_span_context_manager_calls_start_and_end(self) -> None:
        """
        GIVEN: An active trace
        WHEN: Using span() context manager
        THEN: Provider receives start_span on entry and end_span on exit
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test")

        async with service.span(ctx, "retrieval", "retrieval") as span_id:
            assert len(span_id) == 16
            # Verify start_span was called
            provider.start_span.assert_called_once()

        # Verify end_span was called
        provider.end_span.assert_called_once()
        end_kwargs = provider.end_span.call_args.kwargs
        assert end_kwargs["status"] == "completed"
        assert end_kwargs["duration_ms"] >= 0

    async def test_end_trace_completes_flow_with_duration(self) -> None:
        """
        GIVEN: A trace with completed spans
        WHEN: Calling end_trace()
        THEN: Provider receives end_trace with calculated duration
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test")

        async with service.span(ctx, "work", "llm"):
            await asyncio.sleep(0.01)

        await service.end_trace(ctx=ctx, status="completed")

        # Verify end_trace was called
        provider.end_trace.assert_called_once()
        end_kwargs = provider.end_trace.call_args.kwargs
        assert end_kwargs["status"] == "completed"
        assert end_kwargs["duration_ms"] >= 10

    async def test_full_chat_operation_flow(self) -> None:
        """
        GIVEN: A chat operation requiring multiple spans
        WHEN: Complete chat flow is traced
        THEN: All provider methods are called correctly
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        # Start trace
        ctx = await service.start_trace(
            name="chat.conversation",
            user_id=uuid4(),
            session_id=str(uuid4()),
            kb_id=uuid4(),
        )

        # Retrieval span
        async with service.span(ctx, "retrieval", "retrieval"):
            pass  # Simulated retrieval

        # LLM call
        await service.log_llm_call(
            ctx=ctx,
            name="chat_completion",
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            duration_ms=500,
        )

        # Log chat message
        await service.log_chat_message(
            ctx=ctx,
            role="user",
            content="What is the authentication flow?",
            conversation_id=uuid4(),
        )

        # End trace
        await service.end_trace(ctx=ctx, status="completed")

        # Verify all methods were called
        assert provider.start_trace.call_count == 1
        assert provider.start_span.call_count == 1
        assert provider.end_span.call_count == 1
        assert provider.log_llm_call.call_count == 1
        assert provider.log_chat_message.call_count == 1
        assert provider.end_trace.call_count == 1


@pytest.mark.asyncio
class TestNestedSpans:
    """Tests for nested span hierarchy (AC #2 from 9-3, AC #10)."""

    async def test_nested_spans_with_parent_references(self) -> None:
        """
        GIVEN: Multiple nested operations
        WHEN: Creating child spans using child_context
        THEN: Parent references are correctly passed to provider
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test")

        # Parent span
        async with service.span(ctx, "parent_op", "llm") as parent_span_id:
            # Create child context
            child_ctx = ctx.child_context(parent_span_id=parent_span_id)

            # Child span
            async with service.span(child_ctx, "child_op", "retrieval"):
                pass

        # Verify parent span call
        first_call_kwargs = provider.start_span.call_args_list[0].kwargs
        assert first_call_kwargs["name"] == "parent_op"
        assert first_call_kwargs["parent_span_id"] == ctx.parent_span_id

        # Verify child span call
        second_call_kwargs = provider.start_span.call_args_list[1].kwargs
        assert second_call_kwargs["name"] == "child_op"
        assert second_call_kwargs["parent_span_id"] == parent_span_id

    async def test_deeply_nested_spans(self) -> None:
        """
        GIVEN: Three levels of nesting
        WHEN: Creating grandchild spans
        THEN: Full hierarchy is preserved in provider calls
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test")

        async with service.span(ctx, "level1", "llm") as span1:
            child_ctx = ctx.child_context(parent_span_id=span1)
            async with service.span(child_ctx, "level2", "retrieval") as span2:
                grandchild_ctx = child_ctx.child_context(parent_span_id=span2)
                async with service.span(grandchild_ctx, "level3", "embedding"):
                    pass

        # Verify 3 spans were started
        assert provider.start_span.call_count == 3

        # Verify hierarchy
        calls = provider.start_span.call_args_list
        assert calls[0].kwargs["name"] == "level1"
        assert calls[1].kwargs["name"] == "level2"
        assert calls[1].kwargs["parent_span_id"] == span1
        assert calls[2].kwargs["name"] == "level3"
        assert calls[2].kwargs["parent_span_id"] == span2


@pytest.mark.asyncio
class TestSpanTimingAccuracy:
    """Tests for span timing accuracy (AC #7)."""

    async def test_span_duration_reflects_actual_time(self) -> None:
        """
        GIVEN: A span with known sleep duration
        WHEN: Span completes
        THEN: duration_ms accurately reflects elapsed time
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test")

        async with service.span(ctx, "timed_op", "llm"):
            await asyncio.sleep(0.05)  # 50ms

        end_kwargs = provider.end_span.call_args.kwargs

        # Allow tolerance for timing variations
        assert end_kwargs["duration_ms"] >= 45
        assert end_kwargs["duration_ms"] <= 150

    async def test_short_span_has_minimal_duration(self) -> None:
        """
        GIVEN: A span with no work
        WHEN: Span completes immediately
        THEN: duration_ms is very small but non-negative
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test")

        async with service.span(ctx, "fast_op", "llm"):
            pass  # No work

        end_kwargs = provider.end_span.call_args.kwargs
        assert end_kwargs["duration_ms"] >= 0
        assert end_kwargs["duration_ms"] < 100  # Should be very fast


@pytest.mark.asyncio
class TestSpanErrorCapture:
    """Tests for error capture in span context manager (AC #7)."""

    async def test_span_captures_exception(self) -> None:
        """
        GIVEN: An exception raised within span
        WHEN: Context manager exits
        THEN: Error is captured and span marked as failed
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test")

        with pytest.raises(ValueError):
            async with service.span(ctx, "failing_op", "llm"):
                raise ValueError("Test error")

        end_kwargs = provider.end_span.call_args.kwargs
        assert end_kwargs["status"] == "failed"
        assert "ValueError" in end_kwargs["error_message"]
        assert "Test error" in end_kwargs["error_message"]

    async def test_span_captures_exception_and_reraises(self) -> None:
        """
        GIVEN: An exception within span
        WHEN: Context manager exits
        THEN: Exception is re-raised after capture
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test")

        with pytest.raises(RuntimeError, match="Critical failure"):
            async with service.span(ctx, "op", "llm"):
                raise RuntimeError("Critical failure")

    async def test_span_cleanup_on_exception(self) -> None:
        """
        GIVEN: An exception within span
        WHEN: Context manager exits
        THEN: Span is properly ended with duration
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test")

        with pytest.raises(ValueError, match="Test error"):
            async with service.span(ctx, "op", "llm"):
                await asyncio.sleep(0.01)
                raise ValueError("Test error")

        end_kwargs = provider.end_span.call_args.kwargs
        assert end_kwargs["status"] == "failed"
        assert end_kwargs["duration_ms"] >= 10


@pytest.mark.asyncio
class TestSpanReturnsPrimaryId:
    """Tests for span ID return (AC #7)."""

    async def test_span_returns_valid_w3c_span_id(self) -> None:
        """
        GIVEN: Multiple providers registered
        WHEN: Using span context manager
        THEN: Valid W3C span ID (16 hex chars) is returned
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test")

        async with service.span(ctx, "op", "llm") as span_id:
            assert len(span_id) == 16
            assert all(c in "0123456789abcdef" for c in span_id)


@pytest.mark.asyncio
class TestDocumentProcessingFlow:
    """Tests for document processing tracing (AC #10)."""

    async def test_document_processing_complete_flow(self) -> None:
        """
        GIVEN: A document processing operation
        WHEN: All steps are traced (upload, parse, chunk, embed, index)
        THEN: All events are logged correctly
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        document_id = uuid4()
        kb_id = uuid4()

        ctx = await service.start_trace(
            name="document.process",
            kb_id=kb_id,
        )

        # Upload event
        await service.log_document_event(
            ctx=ctx,
            document_id=document_id,
            event_type="upload",
            status="completed",
            metadata={"file_size_bytes": 2048000},
        )

        # Parse span
        async with service.span(ctx, "parse", "parse"):
            pass

        # Parse complete event
        await service.log_document_event(
            ctx=ctx,
            document_id=document_id,
            event_type="parse",
            status="completed",
            chunk_count=50,
        )

        # Chunking event
        await service.log_document_event(
            ctx=ctx,
            document_id=document_id,
            event_type="chunk",
            status="completed",
            chunk_count=100,
        )

        # Embedding event
        await service.log_document_event(
            ctx=ctx,
            document_id=document_id,
            event_type="embed",
            status="completed",
            token_count=5000,
        )

        await service.end_trace(ctx=ctx, status="completed")

        # Verify all events recorded
        assert provider.log_document_event.call_count == 4
        assert provider.start_span.call_count == 1
        assert provider.end_trace.call_count == 1


@pytest.mark.asyncio
class TestProviderFanout:
    """Tests for provider fanout behavior (AC #5, #6)."""

    async def test_start_trace_calls_all_enabled_providers(self) -> None:
        """
        GIVEN: Multiple enabled providers
        WHEN: start_trace is called
        THEN: All providers receive the call
        """
        provider1 = create_mock_provider("provider1")
        provider2 = create_mock_provider("provider2")
        service = ObservabilityService([provider1, provider2])

        await service.start_trace(name="test")

        provider1.start_trace.assert_called_once()
        provider2.start_trace.assert_called_once()

    async def test_disabled_provider_not_registered(self) -> None:
        """
        GIVEN: A disabled provider in the list
        WHEN: ObservabilityService is created
        THEN: Disabled provider is not in the providers list
        """
        enabled = create_mock_provider("enabled")
        disabled = create_mock_provider("disabled")
        disabled.enabled = False

        service = ObservabilityService([enabled, disabled])

        assert len(service.providers) == 1
        assert service.providers[0].name == "enabled"

    async def test_provider_error_does_not_block_others(self) -> None:
        """
        GIVEN: One provider that fails
        WHEN: Operations are performed
        THEN: Other providers still receive calls
        """
        failing = create_mock_provider("failing")
        failing.start_trace.side_effect = Exception("Provider failure")

        working = create_mock_provider("working")

        service = ObservabilityService([failing, working])

        # Should not raise
        ctx = await service.start_trace(name="test")
        assert ctx is not None

        # Working provider should have been called
        working.start_trace.assert_called_once()


@pytest.mark.asyncio
class TestTraceContextPropagation:
    """Tests for trace context propagation through operations."""

    async def test_user_context_propagates_to_chat_message(self) -> None:
        """
        GIVEN: A trace with user context
        WHEN: Logging a chat message
        THEN: User context is passed to provider
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        user_id = uuid4()
        kb_id = uuid4()
        ctx = await service.start_trace(
            name="test",
            user_id=user_id,
            kb_id=kb_id,
        )

        await service.log_chat_message(
            ctx=ctx,
            role="user",
            content="Hello",
        )

        call_kwargs = provider.log_chat_message.call_args.kwargs
        assert call_kwargs["user_id"] == user_id
        assert call_kwargs["kb_id"] == kb_id
        assert call_kwargs["trace_id"] == ctx.trace_id

    async def test_kb_context_propagates_to_document_event(self) -> None:
        """
        GIVEN: A trace with KB context
        WHEN: Logging a document event
        THEN: KB ID is passed to provider
        """
        provider = create_mock_provider()
        service = ObservabilityService([provider])

        kb_id = uuid4()
        ctx = await service.start_trace(name="test", kb_id=kb_id)

        await service.log_document_event(
            ctx=ctx,
            document_id=uuid4(),
            event_type="parse",
            status="completed",
        )

        call_kwargs = provider.log_document_event.call_args.kwargs
        assert call_kwargs["kb_id"] == kb_id


@pytest.mark.asyncio
class TestFireAndForgetIntegration:
    """Integration tests for fire-and-forget behavior."""

    async def test_complete_flow_with_failing_provider(self) -> None:
        """
        GIVEN: A provider that fails on all operations
        WHEN: Complete trace flow is executed
        THEN: All operations complete without raising
        """
        failing = create_mock_provider("failing")
        failing.start_trace.side_effect = Exception("Start failed")
        failing.start_span.side_effect = Exception("Span failed")
        failing.end_span.side_effect = Exception("End span failed")
        failing.end_trace.side_effect = Exception("End trace failed")
        failing.log_llm_call.side_effect = Exception("LLM failed")
        failing.log_chat_message.side_effect = Exception("Chat failed")
        failing.log_document_event.side_effect = Exception("Doc failed")

        service = ObservabilityService([failing])

        # Complete flow should not raise
        ctx = await service.start_trace(name="test", kb_id=uuid4())

        async with service.span(ctx, "op", "llm"):
            pass

        await service.log_llm_call(ctx, "chat", "gpt-4")
        await service.log_chat_message(ctx, "user", "Hello")
        await service.log_document_event(ctx, uuid4(), "parse", "completed")
        await service.end_trace(ctx, "completed")

        # All should have been attempted
        assert failing.start_trace.called
        assert failing.start_span.called
        assert failing.end_span.called
        assert failing.log_llm_call.called
        assert failing.log_chat_message.called
        assert failing.log_document_event.called
        assert failing.end_trace.called
