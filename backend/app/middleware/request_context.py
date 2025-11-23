"""Request context middleware for request ID generation and structlog integration.

Adds request_id to each request for correlation across logs and audit events.
"""

import uuid
from collections.abc import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_context


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set request context for logging and correlation.

    Generates a unique request_id for each request and binds it to
    structlog context variables for automatic inclusion in all logs.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Process request with context binding.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/route handler.

        Returns:
            The HTTP response with X-Request-ID header.
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Set context for this request
        ctx = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }
        token = request_context.set(ctx)

        # Bind to structlog contextvars for automatic inclusion
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(**ctx)

        try:
            response = await call_next(request)
            # Add request ID to response headers for client correlation
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Reset context
            request_context.reset(token)
            structlog.contextvars.clear_contextvars()
