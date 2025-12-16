"""Integration tests for PostgreSQL Observability Provider (Story 9-2).

Tests verify:
- PostgreSQLProvider implements ObservabilityProvider interface
- Fire-and-forget exception handling (never propagates errors)
- Text truncation utilities
- Trace/Span ID generation

Note: Database persistence tests are covered by unit tests with mocking
since the provider uses a separate session factory from the test infrastructure.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.observability_service import (
    MAX_ERROR_MESSAGE_LENGTH,
    MAX_PREVIEW_LENGTH,
    ObservabilityProvider,
    PostgreSQLProvider,
    generate_span_id,
    generate_trace_id,
    truncate_text,
)


class TestPostgreSQLProviderInterface:
    """Tests for PostgreSQLProvider interface compliance (AC #1)."""

    def test_postgresql_provider_implements_interface(self) -> None:
        """
        GIVEN: PostgreSQLProvider class
        WHEN: Checking class hierarchy
        THEN: It implements ObservabilityProvider
        """
        provider = PostgreSQLProvider()
        assert isinstance(provider, ObservabilityProvider)

    def test_provider_name_is_postgresql(self) -> None:
        """
        GIVEN: PostgreSQLProvider instance
        WHEN: Accessing name property
        THEN: Returns "postgresql"
        """
        provider = PostgreSQLProvider()
        assert provider.name == "postgresql"

    def test_provider_is_always_enabled(self) -> None:
        """
        GIVEN: PostgreSQLProvider instance
        WHEN: Accessing enabled property
        THEN: Returns True (always enabled)
        """
        provider = PostgreSQLProvider()
        assert provider.enabled is True


@pytest.mark.asyncio
class TestStartTraceWithMocks:
    """Tests for start_trace behavior with mocked DB (AC #2)."""

    async def test_start_trace_creates_record_with_session(self) -> None:
        """
        GIVEN: PostgreSQLProvider with mocked session
        WHEN: Calling start_trace with all context fields
        THEN: Session.add and commit are called
        """
        provider = PostgreSQLProvider()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        # session.add() is synchronous, use MagicMock
        mock_session.add = MagicMock()

        with patch.object(provider, "_get_session", return_value=mock_session):
            trace_id = generate_trace_id()
            user_id = uuid4()
            kb_id = uuid4()
            metadata = {"operation": "test"}

            await provider.start_trace(
                trace_id=trace_id,
                name="test.operation",
                timestamp=datetime.utcnow(),
                user_id=user_id,
                kb_id=kb_id,
                metadata=metadata,
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_awaited_once()

    async def test_start_trace_with_minimal_fields(self) -> None:
        """
        GIVEN: PostgreSQLProvider with mocked session
        WHEN: Calling start_trace with only required fields
        THEN: Session operations succeed
        """
        provider = PostgreSQLProvider()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        # session.add() is synchronous, use MagicMock
        mock_session.add = MagicMock()

        with patch.object(provider, "_get_session", return_value=mock_session):
            await provider.start_trace(
                trace_id=generate_trace_id(),
                name="minimal.trace",
                timestamp=datetime.utcnow(),
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
class TestEndTraceWithMocks:
    """Tests for end_trace behavior with mocked DB (AC #3)."""

    async def test_end_trace_calls_update(self) -> None:
        """
        GIVEN: PostgreSQLProvider with mocked session
        WHEN: Calling end_trace
        THEN: Execute and commit are called
        """
        provider = PostgreSQLProvider()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(provider, "_get_session", return_value=mock_session):
            await provider.end_trace(
                trace_id=generate_trace_id(),
                timestamp=datetime.utcnow(),
                status="completed",
                duration_ms=150,
            )

            mock_session.execute.assert_awaited_once()
            mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
class TestStartSpanWithMocks:
    """Tests for start_span behavior with mocked DB (AC #4)."""

    async def test_start_span_creates_record(self) -> None:
        """
        GIVEN: PostgreSQLProvider with mocked session
        WHEN: Calling start_span
        THEN: Session.add and commit are called
        """
        provider = PostgreSQLProvider()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        # session.add() is synchronous, use MagicMock
        mock_session.add = MagicMock()

        with patch.object(provider, "_get_session", return_value=mock_session):
            await provider.start_span(
                span_id=generate_span_id(),
                trace_id=generate_trace_id(),
                name="retrieval.search",
                span_type="retrieval",
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
class TestEndSpanWithMocks:
    """Tests for end_span behavior with mocked DB (AC #5)."""

    async def test_end_span_calls_update(self) -> None:
        """
        GIVEN: PostgreSQLProvider with mocked session
        WHEN: Calling end_span
        THEN: Execute and commit are called
        """
        provider = PostgreSQLProvider()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch.object(provider, "_get_session", return_value=mock_session):
            await provider.end_span(
                span_id=generate_span_id(),
                timestamp=datetime.utcnow(),
                status="completed",
                duration_ms=200,
            )

            mock_session.execute.assert_awaited_once()
            mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
class TestLogLLMCallWithMocks:
    """Tests for log_llm_call behavior with mocked DB (AC #6)."""

    async def test_log_llm_call_creates_span(self) -> None:
        """
        GIVEN: PostgreSQLProvider with mocked session
        WHEN: Calling log_llm_call
        THEN: Session.add and commit are called, span_id is returned
        """
        provider = PostgreSQLProvider()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        # session.add() is synchronous, use MagicMock
        mock_session.add = MagicMock()

        with patch.object(provider, "_get_session", return_value=mock_session):
            span_id = await provider.log_llm_call(
                trace_id=generate_trace_id(),
                name="chat_completion",
                model="gpt-4-turbo",
                input_tokens=500,
                output_tokens=150,
                duration_ms=1200,
            )

            assert span_id is not None
            assert len(span_id) == 16
            mock_session.add.assert_called_once()
            mock_session.commit.assert_awaited_once()

    async def test_log_llm_call_returns_generated_span_id(self) -> None:
        """
        GIVEN: PostgreSQLProvider
        WHEN: Calling log_llm_call
        THEN: Returns auto-generated span_id regardless of DB success
        """
        provider = PostgreSQLProvider()

        # Even with exception, span_id should be returned
        with patch.object(provider, "_get_session", side_effect=Exception("DB Error")):
            span_id = await provider.log_llm_call(
                trace_id=generate_trace_id(),
                name="embedding",
                model="text-embedding-3-small",
            )

        assert span_id is not None
        assert len(span_id) == 16


@pytest.mark.asyncio
class TestLogChatMessageWithMocks:
    """Tests for log_chat_message behavior with mocked DB (AC #7)."""

    async def test_log_chat_message_creates_record(self) -> None:
        """
        GIVEN: PostgreSQLProvider with mocked session
        WHEN: Calling log_chat_message
        THEN: Session.add and commit are called
        """
        provider = PostgreSQLProvider()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        # session.add() is synchronous, use MagicMock
        mock_session.add = MagicMock()

        with patch.object(provider, "_get_session", return_value=mock_session):
            await provider.log_chat_message(
                trace_id=generate_trace_id(),
                role="user",
                content="What is the authentication flow?",
                user_id=uuid4(),
                kb_id=uuid4(),
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
class TestLogDocumentEventWithMocks:
    """Tests for log_document_event behavior with mocked DB (AC #8)."""

    @pytest.mark.parametrize(
        "event_type",
        ["upload", "parse", "chunk", "embed", "index", "delete", "reprocess"],
    )
    async def test_log_document_event_for_all_types(self, event_type: str) -> None:
        """
        GIVEN: PostgreSQLProvider with mocked session
        WHEN: Calling log_document_event with different event types
        THEN: Session.add and commit are called for each type
        """
        provider = PostgreSQLProvider()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        # session.add() is synchronous, use MagicMock
        mock_session.add = MagicMock()

        with patch.object(provider, "_get_session", return_value=mock_session):
            await provider.log_document_event(
                trace_id=generate_trace_id(),
                document_id=uuid4(),
                kb_id=uuid4(),
                event_type=event_type,
                status="completed",
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
class TestFireAndForget:
    """Tests for fire-and-forget exception handling (AC #9)."""

    async def test_start_trace_catches_exception(self, caplog) -> None:
        """
        GIVEN: A database error during start_trace
        WHEN: Exception occurs
        THEN: Exception is caught and logged, not propagated
        """
        provider = PostgreSQLProvider()

        with patch.object(
            provider,
            "_get_session",
            side_effect=Exception("Database connection failed"),
        ):
            # Should not raise
            await provider.start_trace(
                trace_id=generate_trace_id(),
                name="test",
                timestamp=datetime.utcnow(),
            )

        assert "postgresql_start_trace_failed" in caplog.text

    async def test_end_trace_catches_exception(self, caplog) -> None:
        """
        GIVEN: A database error during end_trace
        WHEN: Exception occurs
        THEN: Exception is caught and logged, not propagated
        """
        provider = PostgreSQLProvider()

        with patch.object(
            provider, "_get_session", side_effect=Exception("Connection timeout")
        ):
            # Should not raise
            await provider.end_trace(
                trace_id=generate_trace_id(),
                timestamp=datetime.utcnow(),
                status="completed",
                duration_ms=100,
            )

        assert "postgresql_end_trace_failed" in caplog.text

    async def test_start_span_catches_exception(self, caplog) -> None:
        """
        GIVEN: A database error during start_span
        WHEN: Exception occurs
        THEN: Exception is caught and logged, not propagated
        """
        provider = PostgreSQLProvider()

        with patch.object(
            provider, "_get_session", side_effect=Exception("Insert failed")
        ):
            # Should not raise
            await provider.start_span(
                span_id=generate_span_id(),
                trace_id=generate_trace_id(),
                name="test",
                span_type="llm",
            )

        assert "postgresql_start_span_failed" in caplog.text

    async def test_log_llm_call_catches_exception(self, caplog) -> None:
        """
        GIVEN: A database error during log_llm_call
        WHEN: Exception occurs
        THEN: Exception is caught, span_id is still returned
        """
        provider = PostgreSQLProvider()

        with patch.object(
            provider, "_get_session", side_effect=Exception("Insert failed")
        ):
            span_id = await provider.log_llm_call(
                trace_id=generate_trace_id(),
                name="test",
                model="gpt-4",
            )

        # Should still return a span_id
        assert span_id is not None
        assert len(span_id) == 16
        assert "postgresql_log_llm_call_failed" in caplog.text

    async def test_log_chat_message_catches_exception(self, caplog) -> None:
        """
        GIVEN: A database error during log_chat_message
        WHEN: Exception occurs
        THEN: Exception is caught and logged, not propagated
        """
        provider = PostgreSQLProvider()

        with patch.object(
            provider, "_get_session", side_effect=Exception("Insert failed")
        ):
            # Should not raise
            await provider.log_chat_message(
                trace_id=generate_trace_id(),
                role="user",
                content="test message",
            )

        assert "postgresql_log_chat_message_failed" in caplog.text

    async def test_log_document_event_catches_exception(self, caplog) -> None:
        """
        GIVEN: A database error during log_document_event
        WHEN: Exception occurs
        THEN: Exception is caught and logged, not propagated
        """
        provider = PostgreSQLProvider()

        with patch.object(
            provider, "_get_session", side_effect=Exception("Constraint violation")
        ):
            # Should not raise
            await provider.log_document_event(
                trace_id=generate_trace_id(),
                document_id=uuid4(),
                kb_id=uuid4(),
                event_type="upload",
                status="started",
            )

        assert "postgresql_log_document_event_failed" in caplog.text


class TestTextTruncation:
    """Tests for text truncation utilities (AC #9 - Task 3)."""

    def test_truncate_text_under_limit(self) -> None:
        """
        GIVEN: Text shorter than limit
        WHEN: truncate_text is called
        THEN: Original text is returned
        """
        text = "Short text"
        result = truncate_text(text, 100)
        assert result == text

    def test_truncate_text_over_limit(self) -> None:
        """
        GIVEN: Text longer than limit
        WHEN: truncate_text is called
        THEN: Text is truncated with ellipsis
        """
        text = "A" * 100
        result = truncate_text(text, 50)
        assert len(result) == 50
        assert result.endswith("...")

    def test_truncate_text_handles_none(self) -> None:
        """
        GIVEN: None value
        WHEN: truncate_text is called
        THEN: None is returned
        """
        result = truncate_text(None, 100)
        assert result is None

    def test_truncate_text_exact_limit(self) -> None:
        """
        GIVEN: Text exactly at limit
        WHEN: truncate_text is called
        THEN: Original text is returned
        """
        text = "A" * 50
        result = truncate_text(text, 50)
        assert result == text

    def test_error_message_truncation_limit(self) -> None:
        """
        GIVEN: MAX_ERROR_MESSAGE_LENGTH constant
        WHEN: Checking value
        THEN: It is 1000 chars
        """
        assert MAX_ERROR_MESSAGE_LENGTH == 1000

    def test_preview_truncation_limit(self) -> None:
        """
        GIVEN: MAX_PREVIEW_LENGTH constant
        WHEN: Checking value
        THEN: It is 500 chars
        """
        assert MAX_PREVIEW_LENGTH == 500


class TestIdGeneration:
    """Tests for trace/span ID generation."""

    def test_generate_trace_id_produces_32_hex_chars(self) -> None:
        """
        GIVEN: A request to generate a trace ID
        WHEN: generate_trace_id() is called
        THEN: Returns a 32-character hexadecimal string
        """
        trace_id = generate_trace_id()

        assert len(trace_id) == 32
        assert all(c in "0123456789abcdef" for c in trace_id)

    def test_generate_span_id_produces_16_hex_chars(self) -> None:
        """
        GIVEN: A request to generate a span ID
        WHEN: generate_span_id() is called
        THEN: Returns a 16-character hexadecimal string
        """
        span_id = generate_span_id()

        assert len(span_id) == 16
        assert all(c in "0123456789abcdef" for c in span_id)

    def test_generated_ids_are_unique(self) -> None:
        """
        GIVEN: Multiple ID generation requests
        WHEN: Generating 100 IDs
        THEN: All IDs are unique
        """
        trace_ids = {generate_trace_id() for _ in range(100)}
        span_ids = {generate_span_id() for _ in range(100)}

        assert len(trace_ids) == 100
        assert len(span_ids) == 100

    def test_trace_id_not_all_zeros(self) -> None:
        """
        GIVEN: W3C trace context spec
        WHEN: Generating trace ID
        THEN: It is not all zeros (invalid per spec)
        """
        trace_id = generate_trace_id()
        assert trace_id != "0" * 32

    def test_span_id_not_all_zeros(self) -> None:
        """
        GIVEN: W3C trace context spec
        WHEN: Generating span ID
        THEN: It is not all zeros (invalid per spec)
        """
        span_id = generate_span_id()
        assert span_id != "0" * 16
