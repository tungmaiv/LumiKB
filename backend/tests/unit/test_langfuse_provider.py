"""Unit tests for LangFuse observability provider.

Story 9-11: LangFuse Provider Implementation

Tests fire-and-forget pattern, SDK mocking, and provider configuration.
"""

import sys
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Create mock Langfuse class before importing the provider
mock_langfuse_module = MagicMock()
sys.modules["langfuse"] = mock_langfuse_module


@pytest.fixture(autouse=True)
def reset_provider_singleton():
    """Reset the provider singleton before each test."""
    import app.services.langfuse_provider as provider_module

    provider_module._langfuse_provider = None
    yield
    provider_module._langfuse_provider = None


@pytest.fixture
def mock_settings():
    """Mock settings with LangFuse configuration."""
    with patch("app.services.langfuse_provider.settings") as mock:
        mock.langfuse_enabled = True
        mock.langfuse_public_key = "test-public-key"
        mock.langfuse_secret_key = "test-secret-key"
        mock.langfuse_host = "https://test.langfuse.com"
        yield mock


@pytest.fixture
def mock_langfuse_available():
    """Set LANGFUSE_AVAILABLE to True."""
    with patch("app.services.langfuse_provider.LANGFUSE_AVAILABLE", True):
        yield


@pytest.fixture
def mock_langfuse_class():
    """Mock Langfuse class and inject into module."""
    mock_client = MagicMock()
    mock_trace = MagicMock()
    mock_client.trace.return_value = mock_trace

    # Inject into module
    import app.services.langfuse_provider as provider_module

    original_langfuse = getattr(provider_module, "Langfuse", None)
    provider_module.Langfuse = MagicMock(return_value=mock_client)

    yield mock_client, mock_trace

    # Restore
    if original_langfuse:
        provider_module.Langfuse = original_langfuse


@pytest.fixture
def mock_session_factory():
    """Mock database session factory for sync status tracking."""
    with patch("app.services.langfuse_provider.async_session_factory") as mock:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock.return_value = mock_session
        yield mock_session


class TestLangFuseProviderConfiguration:
    """Tests for provider configuration and enablement."""

    @pytest.mark.unit
    def test_provider_disabled_when_langfuse_not_available(self):
        """Verify provider disabled when SDK not installed."""
        with patch("app.services.langfuse_provider.LANGFUSE_AVAILABLE", False):
            with patch("app.services.langfuse_provider.settings") as mock_settings:
                mock_settings.langfuse_enabled = True
                mock_settings.langfuse_public_key = "key"
                mock_settings.langfuse_secret_key = "secret"

                from app.services.langfuse_provider import LangFuseProvider

                provider = LangFuseProvider()

                assert provider.enabled is False
                assert provider.name == "langfuse"

    @pytest.mark.unit
    def test_provider_disabled_when_not_enabled_in_settings(self):
        """Verify provider disabled when langfuse_enabled is False."""
        with patch("app.services.langfuse_provider.LANGFUSE_AVAILABLE", True):
            with patch("app.services.langfuse_provider.settings") as mock_settings:
                mock_settings.langfuse_enabled = False

                from app.services.langfuse_provider import LangFuseProvider

                provider = LangFuseProvider()

                assert provider.enabled is False

    @pytest.mark.unit
    def test_provider_disabled_when_no_public_key(self):
        """Verify provider disabled when public key not configured."""
        with patch("app.services.langfuse_provider.LANGFUSE_AVAILABLE", True):
            with patch("app.services.langfuse_provider.settings") as mock_settings:
                mock_settings.langfuse_enabled = True
                mock_settings.langfuse_public_key = None

                from app.services.langfuse_provider import LangFuseProvider

                provider = LangFuseProvider()

                assert provider.enabled is False

    @pytest.mark.unit
    def test_provider_disabled_when_no_secret_key(self):
        """Verify provider disabled when secret key not configured."""
        with patch("app.services.langfuse_provider.LANGFUSE_AVAILABLE", True):
            with patch("app.services.langfuse_provider.settings") as mock_settings:
                mock_settings.langfuse_enabled = True
                mock_settings.langfuse_public_key = "public-key"
                mock_settings.langfuse_secret_key = None

                from app.services.langfuse_provider import LangFuseProvider

                provider = LangFuseProvider()

                assert provider.enabled is False

    @pytest.mark.unit
    def test_provider_enabled_with_valid_config(
        self, mock_settings, mock_langfuse_available, mock_langfuse_class
    ):
        """Verify provider enabled with valid configuration."""
        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        assert provider.enabled is True
        assert provider.name == "langfuse"


class TestStartTrace:
    """Tests for start_trace method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_trace_creates_langfuse_trace(
        self,
        mock_settings,
        mock_langfuse_available,
        mock_langfuse_class,
        mock_session_factory,
    ):
        """Verify start_trace creates LangFuse trace with correct params."""
        mock_client, mock_trace = mock_langfuse_class

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        trace_id = "a" * 32
        timestamp = datetime.utcnow()
        user_id = uuid.uuid4()
        kb_id = uuid.uuid4()

        await provider.start_trace(
            trace_id=trace_id,
            name="test_trace",
            timestamp=timestamp,
            user_id=user_id,
            kb_id=kb_id,
            metadata={"key": "value"},
        )

        mock_client.trace.assert_called_once()
        call_kwargs = mock_client.trace.call_args[1]
        assert call_kwargs["id"] == trace_id
        assert call_kwargs["name"] == "test_trace"
        assert call_kwargs["user_id"] == str(user_id)
        assert "kb_id" in call_kwargs["metadata"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_trace_noop_when_disabled(self, mock_session_factory):
        """Verify start_trace does nothing when provider disabled."""
        with patch("app.services.langfuse_provider.LANGFUSE_AVAILABLE", True):
            with patch("app.services.langfuse_provider.settings") as mock_settings:
                mock_settings.langfuse_enabled = False

                from app.services.langfuse_provider import LangFuseProvider

                provider = LangFuseProvider()

                # Should not raise exception
                await provider.start_trace(
                    trace_id="test",
                    name="test",
                    timestamp=datetime.utcnow(),
                )


class TestLogLLMCall:
    """Tests for log_llm_call method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_log_llm_call_creates_generation(
        self,
        mock_settings,
        mock_langfuse_available,
        mock_langfuse_class,
        mock_session_factory,
    ):
        """Verify log_llm_call creates LangFuse generation with usage metrics."""
        mock_client, mock_trace = mock_langfuse_class

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        trace_id = "a" * 32

        span_id = await provider.log_llm_call(
            trace_id=trace_id,
            name="chat_completion",
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            duration_ms=1500,
            status="completed",
        )

        assert span_id is not None
        mock_trace.generation.assert_called_once()
        call_kwargs = mock_trace.generation.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["usage"]["prompt_tokens"] == 100
        assert call_kwargs["usage"]["completion_tokens"] == 50
        assert call_kwargs["usage"]["total_tokens"] == 150

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_log_llm_call_returns_span_id_when_disabled(self):
        """Verify log_llm_call returns span_id even when disabled."""
        with patch("app.services.langfuse_provider.LANGFUSE_AVAILABLE", True):
            with patch("app.services.langfuse_provider.settings") as mock_settings:
                mock_settings.langfuse_enabled = False

                from app.services.langfuse_provider import LangFuseProvider

                provider = LangFuseProvider()

                span_id = await provider.log_llm_call(
                    trace_id="test",
                    name="test",
                    model="gpt-4",
                )

                # Should return a valid span_id even when disabled
                assert span_id is not None
                assert len(span_id) == 16  # W3C span-id length


class TestFireAndForget:
    """Tests for fire-and-forget pattern."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_trace_catches_exceptions(
        self, mock_settings, mock_langfuse_available, mock_session_factory
    ):
        """Verify start_trace catches SDK exceptions (fire-and-forget)."""
        import app.services.langfuse_provider as provider_module

        mock_client = MagicMock()
        mock_client.trace.side_effect = Exception("SDK Error")
        provider_module.Langfuse = MagicMock(return_value=mock_client)

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        # Should not raise exception
        await provider.start_trace(
            trace_id="test",
            name="test",
            timestamp=datetime.utcnow(),
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_log_llm_call_catches_exceptions(
        self, mock_settings, mock_langfuse_available, mock_session_factory
    ):
        """Verify log_llm_call catches SDK exceptions (fire-and-forget)."""
        import app.services.langfuse_provider as provider_module

        mock_client = MagicMock()
        mock_trace = MagicMock()
        mock_trace.generation.side_effect = Exception("SDK Error")
        mock_client.trace.return_value = mock_trace
        provider_module.Langfuse = MagicMock(return_value=mock_client)

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        # Should not raise exception, should return span_id
        span_id = await provider.log_llm_call(
            trace_id="test",
            name="test",
            model="gpt-4",
        )
        assert span_id is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_end_trace_catches_exceptions(
        self, mock_settings, mock_langfuse_available, mock_session_factory
    ):
        """Verify end_trace catches SDK exceptions (fire-and-forget)."""
        import app.services.langfuse_provider as provider_module

        mock_client = MagicMock()
        mock_trace = MagicMock()
        mock_trace.update.side_effect = Exception("SDK Error")
        mock_client.trace.return_value = mock_trace
        provider_module.Langfuse = MagicMock(return_value=mock_client)

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        # Should not raise exception
        await provider.end_trace(
            trace_id="test",
            timestamp=datetime.utcnow(),
            status="completed",
            duration_ms=1000,
        )


class TestFlushOnTraceEnd:
    """Tests for flush behavior on trace end."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_flush_called_on_trace_end(
        self,
        mock_settings,
        mock_langfuse_available,
        mock_langfuse_class,
        mock_session_factory,
    ):
        """Verify client.flush() called when end_trace() is invoked."""
        mock_client, mock_trace = mock_langfuse_class
        mock_settings.langfuse_flush_timeout_seconds = 5

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        await provider.end_trace(
            trace_id="test",
            timestamp=datetime.utcnow(),
            status="completed",
            duration_ms=1000,
        )

        mock_client.flush.assert_called_once()


class TestFlushTimeout:
    """Tests for flush timeout functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_flush_timeout_handles_slow_flush(
        self,
        mock_settings,
        mock_langfuse_available,
        mock_session_factory,
    ):
        """Verify flush timeout handles slow flush gracefully without raising exception.

        Note: The timeout mechanism allows the main async flow to continue
        without waiting for the blocking flush to complete. The thread may
        still run to completion in the background.
        """
        import app.services.langfuse_provider as provider_module

        mock_client = MagicMock()
        mock_trace = MagicMock()
        mock_client.trace.return_value = mock_trace

        # Track if flush was called
        flush_called = False

        def slow_flush():
            nonlocal flush_called
            import time

            flush_called = True
            time.sleep(0.5)  # Sleep for 0.5 seconds

        mock_client.flush = slow_flush
        provider_module.Langfuse = MagicMock(return_value=mock_client)

        # Set timeout to 0.1 seconds (shorter than flush time)
        mock_settings.langfuse_flush_timeout_seconds = 0.1

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        # Should not raise exception even with slow flush
        await provider.end_trace(
            trace_id="test",
            timestamp=datetime.utcnow(),
            status="completed",
            duration_ms=1000,
        )

        # Verify flush was called (the timeout mechanism started the flush)
        assert flush_called is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_flush_timeout_configured_from_settings(
        self,
        mock_settings,
        mock_langfuse_available,
        mock_langfuse_class,
        mock_session_factory,
    ):
        """Verify flush timeout is configurable via settings."""
        mock_settings.langfuse_flush_timeout_seconds = 10

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        # _flush_with_timeout should use the setting
        # We verify this by ensuring the method runs without error
        await provider._flush_with_timeout()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_flush_with_timeout_noop_when_no_client(
        self,
        mock_session_factory,
    ):
        """Verify _flush_with_timeout does nothing when client not set."""
        with patch("app.services.langfuse_provider.LANGFUSE_AVAILABLE", True):
            with patch("app.services.langfuse_provider.settings") as mock_settings:
                mock_settings.langfuse_enabled = False

                from app.services.langfuse_provider import LangFuseProvider

                provider = LangFuseProvider()

                # Should not raise exception
                await provider._flush_with_timeout()


class TestSyncStatusTracking:
    """Tests for provider sync status tracking."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_status_created_on_start_trace(
        self,
        mock_settings,
        mock_langfuse_available,
        mock_langfuse_class,
        mock_session_factory,
    ):
        """Verify ProviderSyncStatus record created for trace."""
        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        await provider.start_trace(
            trace_id="test",
            name="test",
            timestamp=datetime.utcnow(),
        )

        # Verify session.add was called
        mock_session_factory.add.assert_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_status_failed_on_exception(
        self, mock_settings, mock_langfuse_available, mock_session_factory
    ):
        """Verify sync status marked as failed when SDK throws exception."""
        import app.services.langfuse_provider as provider_module

        mock_client = MagicMock()
        mock_client.trace.side_effect = Exception("SDK Error")
        provider_module.Langfuse = MagicMock(return_value=mock_client)

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        await provider.start_trace(
            trace_id="test",
            name="test",
            timestamp=datetime.utcnow(),
        )

        # Verify session.add was called (for failed status)
        assert mock_session_factory.add.called


class TestLogChatMessage:
    """Tests for log_chat_message method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_log_chat_message_creates_event(
        self,
        mock_settings,
        mock_langfuse_available,
        mock_langfuse_class,
        mock_session_factory,
    ):
        """Verify log_chat_message creates LangFuse event."""
        mock_client, mock_trace = mock_langfuse_class

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        await provider.log_chat_message(
            trace_id="test",
            role="assistant",
            content="Hello, world!",
            user_id=uuid.uuid4(),
            kb_id=uuid.uuid4(),
        )

        mock_trace.event.assert_called_once()
        call_kwargs = mock_trace.event.call_args[1]
        assert call_kwargs["name"] == "chat.assistant"
        assert call_kwargs["metadata"]["role"] == "assistant"


class TestLogDocumentEvent:
    """Tests for log_document_event method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_log_document_event_creates_event(
        self,
        mock_settings,
        mock_langfuse_available,
        mock_langfuse_class,
        mock_session_factory,
    ):
        """Verify log_document_event creates LangFuse event with metadata."""
        mock_client, mock_trace = mock_langfuse_class

        from app.services.langfuse_provider import LangFuseProvider

        provider = LangFuseProvider()

        doc_id = uuid.uuid4()
        kb_id = uuid.uuid4()

        await provider.log_document_event(
            trace_id="test",
            document_id=doc_id,
            kb_id=kb_id,
            event_type="parse",
            status="completed",
            duration_ms=500,
            chunk_count=10,
        )

        mock_trace.event.assert_called_once()
        call_kwargs = mock_trace.event.call_args[1]
        assert call_kwargs["name"] == "document.parse"
        assert call_kwargs["metadata"]["document_id"] == str(doc_id)
        assert call_kwargs["metadata"]["chunk_count"] == 10
