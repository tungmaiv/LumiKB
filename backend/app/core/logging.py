"""Structured logging configuration using structlog.

Provides JSON-formatted logging with request correlation IDs
for observability and audit trail support.
"""

import logging
import sys
from contextvars import ContextVar

import structlog

# Context variable for request-scoped data (request_id, user_id, etc.)
request_context: ContextVar[dict[str, str] | None] = ContextVar(
    "request_context", default=None
)


def get_request_id() -> str | None:
    """Get current request ID from context."""
    ctx = request_context.get()
    return ctx.get("request_id") if ctx else None


def configure_logging(json_logs: bool = True, log_level: str = "INFO") -> None:
    """Configure structlog for the application.

    Args:
        json_logs: If True, output JSON format (production).
                   If False, output console format (development).
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # Production: JSON output
        shared_processors.append(structlog.processors.format_exc_info)
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Development: Colored console output
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a logger instance with current request context.

    Args:
        name: Optional logger name. If None, uses caller's module name.

    Returns:
        Bound structlog logger with request context.
    """
    logger = structlog.get_logger(name)
    ctx = request_context.get()
    if ctx:
        logger = logger.bind(**ctx)
    return logger
