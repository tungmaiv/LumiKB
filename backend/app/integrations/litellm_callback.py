"""LiteLLM observability callback for automatic LLM call tracing.

Story 9-6: Implements LiteLLM callback handler to automatically trace all LLM calls
(embeddings, completions) with model, tokens, and cost metrics without manual
instrumentation at each call site.

AC1: success_callback and failure_callback hooks
AC2: Embedding calls create LLM spans with model, input_tokens, dimensions, duration_ms
AC3: Chat completion calls create LLM spans with model, prompt_tokens, completion_tokens, duration_ms
AC4: Streaming completions aggregate token counts after stream completes
AC5: Cost tracking extracts cost_usd from LiteLLM response
AC6: Failed calls log error type and message without exposing prompt content
AC7: Fire-and-forget pattern - never blocks LLM responses
AC8: TraceContext passed via LiteLLM metadata for correlation
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from litellm.integrations.custom_logger import CustomLogger

from app.core.logging import get_logger
from app.services.observability_service import (
    ObservabilityService,
    TraceContext,
    generate_trace_id,
)

logger = get_logger()


class ObservabilityCallback(CustomLogger):
    """Callback handler for automatic LLM observability.

    Implements LiteLLM callback interface to trace:
    - Embedding calls (model, input_tokens, dimensions, duration_ms)
    - Chat completions (model, prompt_tokens, completion_tokens, duration_ms)
    - Streaming completions (aggregated tokens after stream completes)
    - Failed calls (error type, message - no prompt content)

    All methods are fire-and-forget: exceptions logged but never propagated.
    """

    def __init__(self) -> None:
        """Initialize callback with lazy observability service reference."""
        self._obs: ObservabilityService | None = None

    @property
    def obs(self) -> ObservabilityService:
        """Get observability service instance lazily.

        Lazy initialization prevents import errors during startup.
        """
        if self._obs is None:
            self._obs = ObservabilityService.get_instance()
        return self._obs

    async def async_log_success_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Called after successful LLM API call.

        AC7: Fire-and-forget - exceptions logged but never propagated.

        Args:
            kwargs: Original call kwargs (contains litellm_params with metadata)
            response_obj: LiteLLM response object
            start_time: Call start timestamp
            end_time: Call end timestamp
        """
        try:
            # AC8: Extract trace context from metadata
            metadata = kwargs.get("litellm_params", {}).get("metadata", {})
            trace_id = metadata.get("trace_id") or generate_trace_id()

            # Calculate duration
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Detect call type from response
            call_type = getattr(response_obj, "call_type", None)
            if call_type is None:
                # Fallback: check response structure
                call_type = (
                    "embedding" if hasattr(response_obj, "data") else "completion"
                )

            if call_type == "embedding":
                # AC2: Embedding call tracing
                await self._log_embedding(trace_id, response_obj, duration_ms, metadata)
            else:
                # AC3/AC4: Completion call tracing (includes streaming)
                await self._log_completion(
                    trace_id, response_obj, duration_ms, metadata
                )

        except Exception as e:
            # AC7: Fire-and-forget - log but never propagate
            logger.warning("litellm_callback_success_error", error=str(e))

    async def async_log_failure_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,  # noqa: ARG002 - Required by LiteLLM callback interface
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Called after failed LLM API call.

        AC6: Logs error type and message without exposing prompt content.
        AC7: Fire-and-forget - exceptions logged but never propagated.

        Args:
            kwargs: Original call kwargs (contains exception info)
            response_obj: LiteLLM response object (may be None)
            start_time: Call start timestamp
            end_time: Call end timestamp
        """
        try:
            # AC8: Extract trace context from metadata
            metadata = kwargs.get("litellm_params", {}).get("metadata", {})
            trace_id = metadata.get("trace_id") or generate_trace_id()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # AC6: Extract error info safely - no prompt content
            exception = kwargs.get("exception")
            error_type = type(exception).__name__ if exception else "Unknown"
            # Truncate error message to prevent large error logs
            error_message = str(exception)[:200] if exception else "LLM call failed"

            # Create minimal context for logging
            ctx = TraceContext(trace_id=trace_id)

            await self.obs.log_llm_call(
                ctx=ctx,
                name="llm_call_failed",
                model=kwargs.get("model", "unknown"),
                duration_ms=duration_ms,
                status="failed",
                error_message=f"{error_type}: {error_message}",
            )

            logger.debug(
                "litellm_failure_traced",
                trace_id=trace_id,
                model=kwargs.get("model"),
                error_type=error_type,
                duration_ms=duration_ms,
            )

        except Exception as e:
            # AC7: Fire-and-forget
            logger.warning("litellm_callback_failure_error", error=str(e))

    async def _log_embedding(
        self,
        trace_id: str,
        response: Any,
        duration_ms: int,
        metadata: dict[str, Any],  # noqa: ARG002 - Reserved for future use
    ) -> None:
        """Log embedding call with metrics.

        AC2: Creates LLM span with model, input_tokens, dimensions, duration_ms.

        Args:
            trace_id: Trace ID for correlation
            response: LiteLLM embedding response
            duration_ms: Call duration in milliseconds
            metadata: Additional metadata from caller
        """
        model = getattr(response, "model", "unknown")
        usage = getattr(response, "usage", None)
        input_tokens = usage.prompt_tokens if usage else None

        # Get embedding dimensions from first result
        dimensions = None
        if hasattr(response, "data") and response.data:
            first_item = response.data[0]
            # Handle both dict and object access patterns
            if isinstance(first_item, dict):
                first_embedding = first_item.get("embedding", [])
            else:
                first_embedding = getattr(first_item, "embedding", [])
            dimensions = len(first_embedding)

        ctx = TraceContext(trace_id=trace_id)

        span_metadata = {}
        if dimensions:
            span_metadata["dimensions"] = dimensions

        await self.obs.log_llm_call(
            ctx=ctx,
            name="embedding",
            model=model,
            input_tokens=input_tokens,
            duration_ms=duration_ms,
            metadata=span_metadata if span_metadata else None,
        )

        logger.debug(
            "litellm_embedding_traced",
            trace_id=trace_id,
            model=model,
            input_tokens=input_tokens,
            dimensions=dimensions,
            duration_ms=duration_ms,
        )

    async def _log_completion(
        self,
        trace_id: str,
        response: Any,
        duration_ms: int,
        metadata: dict[str, Any],  # noqa: ARG002 - Reserved for future use
    ) -> None:
        """Log chat completion with metrics.

        AC3: Creates LLM span with model, prompt_tokens, completion_tokens, duration_ms.
        AC4: For streaming, uses aggregated token counts from final response.
        AC5: Extracts cost_usd from response when available.

        Args:
            trace_id: Trace ID for correlation
            response: LiteLLM completion response
            duration_ms: Call duration in milliseconds
            metadata: Additional metadata from caller
        """
        model = getattr(response, "model", "unknown")
        usage = getattr(response, "usage", None)

        # AC5: Extract cost from LiteLLM response
        cost = getattr(response, "response_cost", None)
        if cost is None:
            # Alternative cost attribute names
            cost = getattr(response, "_hidden_params", {}).get("response_cost")

        ctx = TraceContext(trace_id=trace_id)

        span_metadata = {}
        if cost is not None:
            try:
                # Convert to Decimal for precision, store as string
                span_metadata["cost_usd"] = str(Decimal(str(cost)))
            except (ValueError, TypeError):
                # Log but don't fail on cost conversion issues
                logger.debug("litellm_cost_conversion_failed", cost=cost)

        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None

        await self.obs.log_llm_call(
            ctx=ctx,
            name="chat_completion",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            metadata=span_metadata if span_metadata else None,
        )

        logger.debug(
            "litellm_completion_traced",
            trace_id=trace_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            has_cost=cost is not None,
        )


# Singleton callback instance
observability_callback = ObservabilityCallback()
