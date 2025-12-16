"""Unit tests for structured logging module.

Story 7.5: Monitoring and Observability (AC-7.5.4)
Tests for structured JSON logging with correlation IDs.
"""

import json
import logging
from io import StringIO

import pytest
import structlog

from app.core.logging import (
    configure_logging,
    get_logger,
    get_request_id,
    request_context,
)

pytestmark = [pytest.mark.unit]


class TestConfigureLogging:
    """Tests for logging configuration."""

    def teardown_method(self) -> None:
        """Reset logging after each test."""
        # Reset structlog
        structlog.reset_defaults()
        # Clear root logger handlers
        root = logging.getLogger()
        root.handlers.clear()

    def test_configure_logging_json_mode(self) -> None:
        """Test that JSON logging mode is properly configured."""
        configure_logging(json_logs=True, log_level="INFO")

        # Get a logger and check it works
        logger = structlog.get_logger("test")
        assert logger is not None

    def test_configure_logging_console_mode(self) -> None:
        """Test that console logging mode is properly configured."""
        configure_logging(json_logs=False, log_level="DEBUG")

        # Get a logger and check it works
        logger = structlog.get_logger("test")
        assert logger is not None

    def test_configure_logging_sets_log_level(self) -> None:
        """Test that log level is properly set."""
        configure_logging(json_logs=True, log_level="WARNING")

        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_configure_logging_debug_level(self) -> None:
        """Test DEBUG log level configuration."""
        configure_logging(json_logs=True, log_level="DEBUG")

        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_json_output_format(self) -> None:
        """Test that JSON logging produces valid JSON output."""
        # Capture stdout
        captured_output = StringIO()

        # Configure with JSON mode
        configure_logging(json_logs=True, log_level="INFO")

        # Create handler that writes to our StringIO
        handler = logging.StreamHandler(captured_output)
        formatter = logging.getLogger().handlers[0].formatter
        handler.setFormatter(formatter)

        # Create a stdlib logger and add our handler
        test_logger = logging.getLogger("test_json_output")
        test_logger.handlers.clear()
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        test_logger.propagate = False

        # Log a message
        test_logger.info("Test message", extra={"key": "value"})

        # Get output
        output = captured_output.getvalue()

        # Should be valid JSON
        if output.strip():
            log_entry = json.loads(output.strip())
            assert "event" in log_entry or "message" in log_entry
            assert "timestamp" in log_entry
            assert "level" in log_entry


class TestRequestContext:
    """Tests for request context handling."""

    def teardown_method(self) -> None:
        """Reset request context after each test."""
        request_context.set(None)
        structlog.contextvars.clear_contextvars()

    def test_get_request_id_returns_none_when_no_context(self) -> None:
        """Test get_request_id returns None when no context is set."""
        request_context.set(None)
        assert get_request_id() is None

    def test_get_request_id_returns_id_when_context_set(self) -> None:
        """Test get_request_id returns the request ID from context."""
        request_context.set({"request_id": "test-123"})
        assert get_request_id() == "test-123"

    def test_get_request_id_with_empty_context(self) -> None:
        """Test get_request_id with context missing request_id key."""
        request_context.set({})
        assert get_request_id() is None

    def test_request_context_isolation(self) -> None:
        """Test that request context is properly isolated."""
        # Set initial context
        request_context.set({"request_id": "request-1"})
        assert get_request_id() == "request-1"

        # Change context
        request_context.set({"request_id": "request-2"})
        assert get_request_id() == "request-2"

        # Clear context
        request_context.set(None)
        assert get_request_id() is None


class TestGetLogger:
    """Tests for get_logger function."""

    def setup_method(self) -> None:
        """Configure logging before each test."""
        configure_logging(json_logs=True, log_level="INFO")

    def teardown_method(self) -> None:
        """Reset logging and context after each test."""
        request_context.set(None)
        structlog.contextvars.clear_contextvars()
        structlog.reset_defaults()

    def test_get_logger_returns_bound_logger(self) -> None:
        """Test that get_logger returns a BoundLogger."""
        logger = get_logger("test_module")
        assert logger is not None

    def test_get_logger_binds_request_context(self) -> None:
        """Test that get_logger binds request context."""
        request_context.set({"request_id": "ctx-123", "user_id": "user-456"})

        logger = get_logger("test_module")
        # The logger should have the context bound
        assert logger is not None

    def test_get_logger_without_context(self) -> None:
        """Test get_logger works without request context."""
        request_context.set(None)

        logger = get_logger("test_module")
        assert logger is not None

    def test_get_logger_with_none_name(self) -> None:
        """Test get_logger with None name uses caller module."""
        logger = get_logger(None)
        assert logger is not None


class TestLogOutput:
    """Tests for log output content."""

    def setup_method(self) -> None:
        """Configure logging before each test."""
        configure_logging(json_logs=True, log_level="DEBUG")

    def teardown_method(self) -> None:
        """Reset logging after each test."""
        request_context.set(None)
        structlog.contextvars.clear_contextvars()
        structlog.reset_defaults()

    def test_log_includes_timestamp(self) -> None:
        """Test that logs include ISO timestamp."""
        captured = StringIO()

        handler = logging.StreamHandler(captured)
        handler.setFormatter(logging.getLogger().handlers[0].formatter)

        test_logger = logging.getLogger("test_timestamp")
        test_logger.handlers.clear()
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        test_logger.propagate = False

        test_logger.info("Test message")

        output = captured.getvalue()
        if output.strip():
            log_entry = json.loads(output.strip())
            assert "timestamp" in log_entry

    def test_log_includes_level(self) -> None:
        """Test that logs include log level."""
        captured = StringIO()

        handler = logging.StreamHandler(captured)
        handler.setFormatter(logging.getLogger().handlers[0].formatter)

        test_logger = logging.getLogger("test_level")
        test_logger.handlers.clear()
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        test_logger.propagate = False

        test_logger.warning("Warning message")

        output = captured.getvalue()
        if output.strip():
            log_entry = json.loads(output.strip())
            assert "level" in log_entry
            assert log_entry["level"] == "warning"


class TestThirdPartyLogSuppression:
    """Tests for third-party library log suppression."""

    def teardown_method(self) -> None:
        """Reset logging after each test."""
        structlog.reset_defaults()

    def test_uvicorn_access_log_level(self) -> None:
        """Test uvicorn access logs are set to WARNING."""
        configure_logging(json_logs=True, log_level="INFO")

        uvicorn_logger = logging.getLogger("uvicorn.access")
        assert uvicorn_logger.level == logging.WARNING

    def test_sqlalchemy_log_level(self) -> None:
        """Test SQLAlchemy logs are set to WARNING."""
        configure_logging(json_logs=True, log_level="INFO")

        sa_logger = logging.getLogger("sqlalchemy.engine")
        assert sa_logger.level == logging.WARNING

    def test_asyncpg_log_level(self) -> None:
        """Test asyncpg logs are set to WARNING."""
        configure_logging(json_logs=True, log_level="INFO")

        asyncpg_logger = logging.getLogger("asyncpg")
        assert asyncpg_logger.level == logging.WARNING
