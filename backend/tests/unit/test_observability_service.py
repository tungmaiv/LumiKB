"""Unit tests for ObservabilityService and TraceContext (Story 9-3).

Tests for:
- TraceContext: W3C-compliant trace context container
- ObservabilityService: Central facade with provider fan-out

These tests verify AC #9 from Story 9-3:
- Unit tests for TraceContext
- Unit tests for ObservabilityService singleton and fan-out behavior
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.observability_service import (
    ObservabilityProvider,
    ObservabilityService,
    TraceContext,
    generate_span_id,
    generate_trace_id,
    get_observability_service,
)


class TestTraceContext:
    """Tests for TraceContext dataclass (AC #1, #2 from 9-3)."""

    def test_trace_context_creation_with_trace_id(self) -> None:
        """
        GIVEN: A trace ID
        WHEN: Creating a TraceContext
        THEN: The context stores the trace_id correctly
        """
        trace_id = generate_trace_id()
        ctx = TraceContext(trace_id=trace_id)

        assert ctx.trace_id == trace_id
        assert len(ctx.trace_id) == 32

    def test_trace_context_auto_generates_span_id(self) -> None:
        """
        GIVEN: A TraceContext created with only trace_id
        WHEN: Accessing the span_id
        THEN: A valid 16-character span_id is auto-generated
        """
        ctx = TraceContext(trace_id=generate_trace_id())

        assert len(ctx.span_id) == 16
        assert all(c in "0123456789abcdef" for c in ctx.span_id)

    def test_trace_context_optional_fields_default_to_none(self) -> None:
        """
        GIVEN: A TraceContext created with only required fields
        WHEN: Accessing optional fields
        THEN: All optional fields are None
        """
        ctx = TraceContext(trace_id=generate_trace_id())

        assert ctx.parent_span_id is None
        assert ctx.user_id is None
        assert ctx.session_id is None
        assert ctx.kb_id is None
        assert ctx.db_trace_id is None
        assert ctx.timestamp is None

    def test_trace_context_accepts_all_fields(self) -> None:
        """
        GIVEN: All TraceContext fields
        WHEN: Creating a TraceContext with all fields
        THEN: All fields are stored correctly
        """
        trace_id = generate_trace_id()
        span_id = generate_span_id()
        parent_span_id = generate_span_id()
        user_id = uuid4()
        session_id = "session-123"
        kb_id = uuid4()
        db_trace_id = uuid4()
        timestamp = datetime.utcnow()

        ctx = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            user_id=user_id,
            session_id=session_id,
            kb_id=kb_id,
            db_trace_id=db_trace_id,
            timestamp=timestamp,
        )

        assert ctx.trace_id == trace_id
        assert ctx.span_id == span_id
        assert ctx.parent_span_id == parent_span_id
        assert ctx.user_id == user_id
        assert ctx.session_id == session_id
        assert ctx.kb_id == kb_id
        assert ctx.db_trace_id == db_trace_id
        assert ctx.timestamp == timestamp

    def test_child_context_preserves_trace_id(self) -> None:
        """
        GIVEN: A TraceContext with a trace_id
        WHEN: Creating a child context
        THEN: The child preserves the same trace_id
        """
        parent_ctx = TraceContext(trace_id=generate_trace_id())
        child_ctx = parent_ctx.child_context(parent_span_id=parent_ctx.span_id)

        assert child_ctx.trace_id == parent_ctx.trace_id

    def test_child_context_generates_new_span_id(self) -> None:
        """
        GIVEN: A TraceContext
        WHEN: Creating a child context
        THEN: The child has a new unique span_id
        """
        parent_ctx = TraceContext(trace_id=generate_trace_id())
        child_ctx = parent_ctx.child_context(parent_span_id=parent_ctx.span_id)

        assert child_ctx.span_id != parent_ctx.span_id
        assert len(child_ctx.span_id) == 16

    def test_child_context_sets_parent_span_id(self) -> None:
        """
        GIVEN: A TraceContext
        WHEN: Creating a child context with parent_span_id
        THEN: The child's parent_span_id is set correctly
        """
        parent_ctx = TraceContext(trace_id=generate_trace_id())
        child_ctx = parent_ctx.child_context(parent_span_id=parent_ctx.span_id)

        assert child_ctx.parent_span_id == parent_ctx.span_id

    def test_child_context_preserves_user_context(self) -> None:
        """
        GIVEN: A TraceContext with user context
        WHEN: Creating a child context
        THEN: The child preserves user_id, session_id, kb_id
        """
        user_id = uuid4()
        session_id = "session-456"
        kb_id = uuid4()
        timestamp = datetime.utcnow()

        parent_ctx = TraceContext(
            trace_id=generate_trace_id(),
            user_id=user_id,
            session_id=session_id,
            kb_id=kb_id,
            timestamp=timestamp,
        )

        child_ctx = parent_ctx.child_context(parent_span_id=parent_ctx.span_id)

        assert child_ctx.user_id == user_id
        assert child_ctx.session_id == session_id
        assert child_ctx.kb_id == kb_id
        assert child_ctx.timestamp == timestamp


class TestObservabilityServiceSingleton:
    """Tests for ObservabilityService singleton pattern (AC #3)."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        ObservabilityService.reset_instance()

    def teardown_method(self) -> None:
        """Clean up singleton after each test."""
        ObservabilityService.reset_instance()

    def test_get_instance_returns_same_instance(self) -> None:
        """
        GIVEN: Multiple calls to get_instance
        WHEN: Comparing the returned instances
        THEN: All calls return the same instance
        """
        instance1 = ObservabilityService.get_instance()
        instance2 = ObservabilityService.get_instance()

        assert instance1 is instance2

    def test_reset_instance_clears_singleton(self) -> None:
        """
        GIVEN: An existing singleton instance
        WHEN: Calling reset_instance
        THEN: The next get_instance creates a new instance
        """
        instance1 = ObservabilityService.get_instance()
        ObservabilityService.reset_instance()
        instance2 = ObservabilityService.get_instance()

        assert instance1 is not instance2

    def test_get_observability_service_returns_singleton(self) -> None:
        """
        GIVEN: The get_observability_service function
        WHEN: Called multiple times
        THEN: Returns the same singleton instance
        """
        service1 = get_observability_service()
        service2 = get_observability_service()

        assert service1 is service2

    def test_service_initializes_with_postgresql_provider(self) -> None:
        """
        GIVEN: A fresh ObservabilityService
        WHEN: Getting the singleton instance
        THEN: PostgreSQL provider is included in the providers list
        """
        service = ObservabilityService.get_instance()

        assert len(service.providers) >= 1
        assert any(p.name == "postgresql" for p in service.providers)

    def test_service_only_registers_enabled_providers(self) -> None:
        """
        GIVEN: A list of providers with some disabled
        WHEN: Creating an ObservabilityService
        THEN: Only enabled providers are registered
        """
        enabled_provider = MagicMock(spec=ObservabilityProvider)
        enabled_provider.enabled = True
        enabled_provider.name = "enabled"

        disabled_provider = MagicMock(spec=ObservabilityProvider)
        disabled_provider.enabled = False
        disabled_provider.name = "disabled"

        service = ObservabilityService([enabled_provider, disabled_provider])

        assert len(service.providers) == 1
        assert service.providers[0].name == "enabled"


class TestObservabilityServiceStartTrace:
    """Tests for ObservabilityService.start_trace (AC #4, #5)."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        ObservabilityService.reset_instance()

    def teardown_method(self) -> None:
        """Clean up singleton after each test."""
        ObservabilityService.reset_instance()

    @pytest.mark.asyncio
    async def test_start_trace_returns_trace_context(self) -> None:
        """
        GIVEN: An ObservabilityService
        WHEN: Calling start_trace
        THEN: Returns a TraceContext with valid IDs
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test.trace")

        assert isinstance(ctx, TraceContext)
        assert len(ctx.trace_id) == 32
        assert len(ctx.span_id) == 16
        assert ctx.timestamp is not None

    @pytest.mark.asyncio
    async def test_start_trace_sets_user_context(self) -> None:
        """
        GIVEN: start_trace called with user context
        WHEN: Examining the returned TraceContext
        THEN: User context fields are set correctly
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        user_id = uuid4()
        session_id = "session-789"
        kb_id = uuid4()

        ctx = await service.start_trace(
            name="test.trace",
            user_id=user_id,
            session_id=session_id,
            kb_id=kb_id,
        )

        assert ctx.user_id == user_id
        assert ctx.session_id == session_id
        assert ctx.kb_id == kb_id

    @pytest.mark.asyncio
    async def test_start_trace_fans_out_to_providers(self) -> None:
        """
        GIVEN: Multiple providers
        WHEN: Calling start_trace
        THEN: All providers receive the start_trace call
        """
        provider1 = AsyncMock(spec=ObservabilityProvider)
        provider1.enabled = True
        provider1.name = "provider1"

        provider2 = AsyncMock(spec=ObservabilityProvider)
        provider2.enabled = True
        provider2.name = "provider2"

        service = ObservabilityService([provider1, provider2])
        user_id = uuid4()

        await service.start_trace(
            name="test.trace",
            user_id=user_id,
            metadata={"key": "value"},
        )

        provider1.start_trace.assert_called_once()
        provider2.start_trace.assert_called_once()

        # Verify call arguments
        call_args = provider1.start_trace.call_args
        assert call_args.kwargs["name"] == "test.trace"
        assert call_args.kwargs["user_id"] == user_id
        assert call_args.kwargs["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_start_trace_continues_on_provider_error(self) -> None:
        """
        GIVEN: A provider that raises an exception
        WHEN: Calling start_trace
        THEN: Other providers still receive the call (fire-and-forget)
        """
        failing_provider = AsyncMock(spec=ObservabilityProvider)
        failing_provider.enabled = True
        failing_provider.name = "failing"
        failing_provider.start_trace.side_effect = Exception("Provider error")

        working_provider = AsyncMock(spec=ObservabilityProvider)
        working_provider.enabled = True
        working_provider.name = "working"

        service = ObservabilityService([failing_provider, working_provider])

        # Should not raise
        ctx = await service.start_trace(name="test.trace")

        assert ctx is not None
        working_provider.start_trace.assert_called_once()


class TestObservabilityServiceEndTrace:
    """Tests for ObservabilityService.end_trace (AC #5)."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        ObservabilityService.reset_instance()

    def teardown_method(self) -> None:
        """Clean up singleton after each test."""
        ObservabilityService.reset_instance()

    @pytest.mark.asyncio
    async def test_end_trace_fans_out_to_providers(self) -> None:
        """
        GIVEN: A started trace
        WHEN: Calling end_trace
        THEN: All providers receive the end_trace call
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = await service.start_trace(name="test.trace")
        await service.end_trace(ctx, status="completed")

        provider.end_trace.assert_called_once()
        call_args = provider.end_trace.call_args
        assert call_args.kwargs["trace_id"] == ctx.trace_id
        assert call_args.kwargs["status"] == "completed"

    @pytest.mark.asyncio
    async def test_end_trace_calculates_duration(self) -> None:
        """
        GIVEN: A started trace with timestamp
        WHEN: Calling end_trace without duration_ms
        THEN: Duration is auto-calculated from timestamp
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        # Create context with timestamp in the past
        ctx = TraceContext(
            trace_id=generate_trace_id(),
            timestamp=datetime.utcnow() - timedelta(seconds=1),
        )

        await service.end_trace(ctx, status="completed")

        provider.end_trace.assert_called_once()
        call_args = provider.end_trace.call_args
        # Duration should be at least 1000ms (1 second)
        assert call_args.kwargs["duration_ms"] >= 1000

    @pytest.mark.asyncio
    async def test_end_trace_uses_provided_duration(self) -> None:
        """
        GIVEN: A started trace
        WHEN: Calling end_trace with explicit duration_ms
        THEN: The provided duration is used
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = TraceContext(
            trace_id=generate_trace_id(),
            timestamp=datetime.utcnow(),
        )

        await service.end_trace(ctx, status="completed", duration_ms=500)

        call_args = provider.end_trace.call_args
        assert call_args.kwargs["duration_ms"] == 500

    @pytest.mark.asyncio
    async def test_end_trace_handles_missing_timestamp(self) -> None:
        """
        GIVEN: A TraceContext without timestamp
        WHEN: Calling end_trace
        THEN: Returns early without calling providers
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = TraceContext(
            trace_id=generate_trace_id(),
            timestamp=None,
        )

        await service.end_trace(ctx, status="completed")

        provider.end_trace.assert_not_called()


class TestObservabilityServiceSpan:
    """Tests for ObservabilityService.span context manager (AC #7, #8)."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        ObservabilityService.reset_instance()

    def teardown_method(self) -> None:
        """Clean up singleton after each test."""
        ObservabilityService.reset_instance()

    @pytest.mark.asyncio
    async def test_span_yields_span_id(self) -> None:
        """
        GIVEN: A started trace
        WHEN: Using the span context manager
        THEN: Yields a valid span_id
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = TraceContext(trace_id=generate_trace_id())

        async with service.span(ctx, "test.span", "retrieval") as span_id:
            assert len(span_id) == 16
            assert all(c in "0123456789abcdef" for c in span_id)

    @pytest.mark.asyncio
    async def test_span_calls_start_and_end_span(self) -> None:
        """
        GIVEN: A provider
        WHEN: Using the span context manager
        THEN: Calls start_span on entry and end_span on exit
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = TraceContext(trace_id=generate_trace_id())

        async with service.span(ctx, "test.span", "retrieval"):
            pass

        provider.start_span.assert_called_once()
        provider.end_span.assert_called_once()

    @pytest.mark.asyncio
    async def test_span_passes_correct_arguments(self) -> None:
        """
        GIVEN: A span with metadata
        WHEN: Using the span context manager
        THEN: Correct arguments are passed to start_span
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = TraceContext(
            trace_id=generate_trace_id(),
            parent_span_id="parent123456789",
        )

        async with service.span(
            ctx, "test.span", "llm", metadata={"key": "value"}
        ) as span_id:
            call_args = provider.start_span.call_args
            assert call_args.kwargs["span_id"] == span_id
            assert call_args.kwargs["trace_id"] == ctx.trace_id
            assert call_args.kwargs["name"] == "test.span"
            assert call_args.kwargs["span_type"] == "llm"
            assert call_args.kwargs["parent_span_id"] == ctx.parent_span_id
            assert call_args.kwargs["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_span_measures_duration(self) -> None:
        """
        GIVEN: A span that takes some time
        WHEN: The span completes
        THEN: Duration is recorded in end_span
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = TraceContext(trace_id=generate_trace_id())

        import asyncio

        async with service.span(ctx, "test.span", "retrieval"):
            await asyncio.sleep(0.01)  # 10ms

        call_args = provider.end_span.call_args
        assert call_args.kwargs["duration_ms"] >= 10
        assert call_args.kwargs["status"] == "completed"

    @pytest.mark.asyncio
    async def test_span_captures_error_on_exception(self) -> None:
        """
        GIVEN: A span that raises an exception
        WHEN: The exception propagates
        THEN: Error is captured and span status is 'failed'
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = TraceContext(trace_id=generate_trace_id())

        with pytest.raises(ValueError, match="test error"):
            async with service.span(ctx, "test.span", "retrieval"):
                raise ValueError("test error")

        call_args = provider.end_span.call_args
        assert call_args.kwargs["status"] == "failed"
        assert "ValueError" in call_args.kwargs["error_message"]
        assert "test error" in call_args.kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_span_reraises_exception(self) -> None:
        """
        GIVEN: A span that raises an exception
        WHEN: The span exits
        THEN: The exception is re-raised to the caller
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = TraceContext(trace_id=generate_trace_id())

        with pytest.raises(RuntimeError, match="Original error"):
            async with service.span(ctx, "test.span", "retrieval"):
                raise RuntimeError("Original error")

    @pytest.mark.asyncio
    async def test_span_ends_even_on_provider_start_error(self) -> None:
        """
        GIVEN: A provider that fails on start_span
        WHEN: Using the span context manager
        THEN: end_span is still called
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        provider.start_span.side_effect = Exception("Start error")
        service = ObservabilityService([provider])

        ctx = TraceContext(trace_id=generate_trace_id())

        async with service.span(ctx, "test.span", "retrieval"):
            pass

        provider.end_span.assert_called_once()


class TestObservabilityServiceLogLlmCall:
    """Tests for ObservabilityService.log_llm_call (AC #8)."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        ObservabilityService.reset_instance()

    def teardown_method(self) -> None:
        """Clean up singleton after each test."""
        ObservabilityService.reset_instance()

    @pytest.mark.asyncio
    async def test_log_llm_call_returns_span_id(self) -> None:
        """
        GIVEN: An ObservabilityService
        WHEN: Calling log_llm_call
        THEN: Returns a valid span_id
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = TraceContext(trace_id=generate_trace_id())
        span_id = await service.log_llm_call(ctx, "chat", "gpt-4")

        assert len(span_id) == 16

    @pytest.mark.asyncio
    async def test_log_llm_call_fans_out_to_providers(self) -> None:
        """
        GIVEN: Multiple providers
        WHEN: Calling log_llm_call
        THEN: All providers receive the call
        """
        provider1 = AsyncMock(spec=ObservabilityProvider)
        provider1.enabled = True
        provider1.name = "provider1"

        provider2 = AsyncMock(spec=ObservabilityProvider)
        provider2.enabled = True
        provider2.name = "provider2"

        service = ObservabilityService([provider1, provider2])
        ctx = TraceContext(trace_id=generate_trace_id())

        await service.log_llm_call(
            ctx,
            name="chat",
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            duration_ms=200,
        )

        provider1.log_llm_call.assert_called_once()
        provider2.log_llm_call.assert_called_once()


class TestObservabilityServiceLogChatMessage:
    """Tests for ObservabilityService.log_chat_message (AC #8)."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        ObservabilityService.reset_instance()

    def teardown_method(self) -> None:
        """Clean up singleton after each test."""
        ObservabilityService.reset_instance()

    @pytest.mark.asyncio
    async def test_log_chat_message_fans_out_to_providers(self) -> None:
        """
        GIVEN: A provider
        WHEN: Calling log_chat_message
        THEN: Provider receives the call with correct arguments
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        user_id = uuid4()
        kb_id = uuid4()
        ctx = TraceContext(
            trace_id=generate_trace_id(),
            user_id=user_id,
            kb_id=kb_id,
        )

        await service.log_chat_message(
            ctx,
            role="user",
            content="Hello",
            conversation_id=uuid4(),
        )

        provider.log_chat_message.assert_called_once()
        call_args = provider.log_chat_message.call_args
        assert call_args.kwargs["trace_id"] == ctx.trace_id
        assert call_args.kwargs["role"] == "user"
        assert call_args.kwargs["content"] == "Hello"
        assert call_args.kwargs["user_id"] == user_id
        assert call_args.kwargs["kb_id"] == kb_id


class TestObservabilityServiceLogDocumentEvent:
    """Tests for ObservabilityService.log_document_event (AC #8)."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        ObservabilityService.reset_instance()

    def teardown_method(self) -> None:
        """Clean up singleton after each test."""
        ObservabilityService.reset_instance()

    @pytest.mark.asyncio
    async def test_log_document_event_fans_out_to_providers(self) -> None:
        """
        GIVEN: A provider
        WHEN: Calling log_document_event
        THEN: Provider receives the call with correct arguments
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        kb_id = uuid4()
        doc_id = uuid4()
        ctx = TraceContext(
            trace_id=generate_trace_id(),
            kb_id=kb_id,
        )

        await service.log_document_event(
            ctx,
            document_id=doc_id,
            event_type="parse",
            status="completed",
            duration_ms=100,
            chunk_count=10,
        )

        provider.log_document_event.assert_called_once()
        call_args = provider.log_document_event.call_args
        assert call_args.kwargs["trace_id"] == ctx.trace_id
        assert call_args.kwargs["document_id"] == doc_id
        assert call_args.kwargs["kb_id"] == kb_id
        assert call_args.kwargs["event_type"] == "parse"
        assert call_args.kwargs["status"] == "completed"

    @pytest.mark.asyncio
    async def test_log_document_event_requires_kb_id(self) -> None:
        """
        GIVEN: A TraceContext without kb_id
        WHEN: Calling log_document_event
        THEN: Returns early without calling providers
        """
        provider = AsyncMock(spec=ObservabilityProvider)
        provider.enabled = True
        provider.name = "mock"
        service = ObservabilityService([provider])

        ctx = TraceContext(
            trace_id=generate_trace_id(),
            kb_id=None,  # No KB ID
        )

        await service.log_document_event(
            ctx,
            document_id=uuid4(),
            event_type="parse",
            status="completed",
        )

        provider.log_document_event.assert_not_called()


class TestFireAndForgetBehavior:
    """Tests for fire-and-forget error handling (AC #6)."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        ObservabilityService.reset_instance()

    def teardown_method(self) -> None:
        """Clean up singleton after each test."""
        ObservabilityService.reset_instance()

    @pytest.mark.asyncio
    async def test_start_trace_never_raises_on_provider_error(self) -> None:
        """
        GIVEN: All providers fail
        WHEN: Calling start_trace
        THEN: No exception is raised
        """
        failing_provider = AsyncMock(spec=ObservabilityProvider)
        failing_provider.enabled = True
        failing_provider.name = "failing"
        failing_provider.start_trace.side_effect = Exception("Total failure")

        service = ObservabilityService([failing_provider])

        # Should not raise
        ctx = await service.start_trace(name="test.trace")
        assert ctx is not None

    @pytest.mark.asyncio
    async def test_end_trace_never_raises_on_provider_error(self) -> None:
        """
        GIVEN: All providers fail on end_trace
        WHEN: Calling end_trace
        THEN: No exception is raised
        """
        failing_provider = AsyncMock(spec=ObservabilityProvider)
        failing_provider.enabled = True
        failing_provider.name = "failing"
        failing_provider.end_trace.side_effect = Exception("End failure")

        service = ObservabilityService([failing_provider])
        ctx = TraceContext(
            trace_id=generate_trace_id(),
            timestamp=datetime.utcnow(),
        )

        # Should not raise
        await service.end_trace(ctx, status="completed")

    @pytest.mark.asyncio
    async def test_log_llm_call_never_raises_on_provider_error(self) -> None:
        """
        GIVEN: All providers fail on log_llm_call
        WHEN: Calling log_llm_call
        THEN: No exception is raised, returns a span_id
        """
        failing_provider = AsyncMock(spec=ObservabilityProvider)
        failing_provider.enabled = True
        failing_provider.name = "failing"
        failing_provider.log_llm_call.side_effect = Exception("LLM log failure")

        service = ObservabilityService([failing_provider])
        ctx = TraceContext(trace_id=generate_trace_id())

        # Should not raise
        span_id = await service.log_llm_call(ctx, name="chat", model="gpt-4")
        assert len(span_id) == 16

    @pytest.mark.asyncio
    async def test_log_chat_message_never_raises_on_provider_error(self) -> None:
        """
        GIVEN: All providers fail on log_chat_message
        WHEN: Calling log_chat_message
        THEN: No exception is raised
        """
        failing_provider = AsyncMock(spec=ObservabilityProvider)
        failing_provider.enabled = True
        failing_provider.name = "failing"
        failing_provider.log_chat_message.side_effect = Exception("Chat log failure")

        service = ObservabilityService([failing_provider])
        ctx = TraceContext(trace_id=generate_trace_id())

        # Should not raise
        await service.log_chat_message(ctx, role="user", content="Hello")

    @pytest.mark.asyncio
    async def test_log_document_event_never_raises_on_provider_error(self) -> None:
        """
        GIVEN: All providers fail on log_document_event
        WHEN: Calling log_document_event
        THEN: No exception is raised
        """
        failing_provider = AsyncMock(spec=ObservabilityProvider)
        failing_provider.enabled = True
        failing_provider.name = "failing"
        failing_provider.log_document_event.side_effect = Exception("Doc log failure")

        service = ObservabilityService([failing_provider])
        ctx = TraceContext(
            trace_id=generate_trace_id(),
            kb_id=uuid4(),
        )

        # Should not raise
        await service.log_document_event(
            ctx,
            document_id=uuid4(),
            event_type="parse",
            status="completed",
        )
