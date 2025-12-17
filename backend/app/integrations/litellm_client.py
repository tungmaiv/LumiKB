"""LiteLLM embedding client for generating document embeddings.

Uses LiteLLM proxy for OpenAI-compatible embedding API calls.
Implements batching, exponential backoff for rate limits, and cost tracking.

Connection Management:
- Provides explicit close_litellm_clients() for graceful shutdown
- Should be called in FastAPI lifespan before atexit handlers run
- Prevents "no event loop" errors during interpreter shutdown
"""

import asyncio
import time

import litellm
import structlog
from litellm import acompletion, aembedding
from litellm.exceptions import RateLimitError

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Suppress LiteLLM debug logging that causes issues during shutdown
litellm.suppress_debug_info = True

# Disable streaming logging to prevent event loop issues in Celery workers
# The LoggingWorker uses asyncio.Queue which gets bound to specific event loops
# and causes RuntimeError when used across Celery's forked worker processes
# See: https://github.com/BerriAI/litellm/issues/6921
litellm.disable_streaming_logging = True

# Turn off message logging to reduce logging worker activity
litellm.turn_off_message_logging = True

# Exponential backoff delays for rate limit (429) responses
RETRY_DELAYS = [30, 60, 120, 240, 300]  # seconds


class EmbeddingError(Exception):
    """Base exception for embedding errors."""


class RateLimitExceededError(EmbeddingError):
    """Raised when rate limit retries are exhausted."""


class TokenLimitExceededError(EmbeddingError):
    """Raised when input exceeds token limit."""

    def __init__(self, message: str, chunk_index: int):
        super().__init__(message)
        self.chunk_index = chunk_index


class LiteLLMEmbeddingClient:
    """Client for generating embeddings via LiteLLM proxy.

    Features:
    - Batched embedding requests (default: 20 chunks per batch)
    - Exponential backoff on rate limits (429)
    - Token usage tracking for cost monitoring
    - OpenAI-compatible API via LiteLLM
    """

    # Providers that require direct API calls (not through LiteLLM proxy)
    # These providers need their specific model name format (e.g., ollama/model)
    DIRECT_CALL_PROVIDERS = {"ollama", "lmstudio"}

    def __init__(
        self,
        model: str | None = None,
        batch_size: int | None = None,
        max_retries: int | None = None,
        api_base: str | None = None,
        api_key: str | None = None,
        provider: str | None = None,
    ):
        """Initialize the embedding client.

        Args:
            model: Embedding model name (default: from settings).
            batch_size: Chunks per batch (default: from settings).
            max_retries: Max retries for rate limits (default: from settings).
            api_base: LiteLLM proxy URL (default: from settings).
            api_key: API key for LiteLLM (default: from settings).
            provider: Model provider (ollama, openai, lmstudio, etc.) for routing.
        """
        self.model = model or settings.embedding_model
        self.batch_size = batch_size or settings.embedding_batch_size
        self.max_retries = max_retries or settings.embedding_max_retries
        self.api_base = api_base or settings.litellm_url
        self.api_key = api_key or settings.litellm_api_key
        self.provider = provider

        # Track total tokens for cost monitoring
        self.total_tokens_used = 0

    async def get_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Processes texts in batches and handles rate limits with exponential backoff.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (768 dimensions for Gemini text-embedding-004).

        Raises:
            RateLimitExceededError: If rate limit retries exhausted.
            TokenLimitExceededError: If a text exceeds token limit.
            EmbeddingError: For other embedding failures.
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        total_tokens = 0

        # Process in batches
        for batch_start in range(0, len(texts), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(texts))
            batch_texts = texts[batch_start:batch_end]

            logger.debug(
                "embedding_batch_started",
                batch_start=batch_start,
                batch_size=len(batch_texts),
                total_texts=len(texts),
            )

            batch_embeddings, batch_tokens = await self._embed_batch_with_retry(
                batch_texts, batch_start
            )
            all_embeddings.extend(batch_embeddings)
            total_tokens += batch_tokens

        self.total_tokens_used += total_tokens

        logger.info(
            "embeddings_generated",
            text_count=len(texts),
            total_tokens=total_tokens,
            embedding_dimensions=len(all_embeddings[0]) if all_embeddings else 0,
        )

        return all_embeddings

    async def _embed_batch_with_retry(
        self,
        texts: list[str],
        batch_start_index: int,
    ) -> tuple[list[list[float]], int]:
        """Embed a batch of texts with retry logic for rate limits.

        Args:
            texts: Batch of texts to embed.
            batch_start_index: Starting index in the original list (for error reporting).

        Returns:
            Tuple of (embeddings list, tokens used).

        Raises:
            RateLimitExceededError: If all retries exhausted.
            TokenLimitExceededError: If a text exceeds token limit.
            EmbeddingError: For other failures.
        """
        for retry in range(self.max_retries):
            try:
                return await self._call_embedding_api(texts)

            except RateLimitError as e:
                if retry >= self.max_retries - 1:
                    break

                delay = RETRY_DELAYS[min(retry, len(RETRY_DELAYS) - 1)]
                logger.warning(
                    "embedding_rate_limit",
                    retry=retry + 1,
                    max_retries=self.max_retries,
                    delay_seconds=delay,
                    error=str(e),
                )
                await asyncio.sleep(delay)

            except Exception as e:
                error_str = str(e).lower()

                # Check for token limit errors
                if "token" in error_str and (
                    "limit" in error_str or "maximum" in error_str
                ):
                    raise TokenLimitExceededError(
                        f"Token limit exceeded: {e}",
                        chunk_index=batch_start_index,
                    ) from e

                raise EmbeddingError(f"Embedding API error: {e}") from e

        # All retries exhausted
        raise RateLimitExceededError(
            f"Embedding rate limit exceeded after {self.max_retries} retries"
        )

    async def _call_embedding_api(
        self,
        texts: list[str],
    ) -> tuple[list[list[float]], int]:
        """Call the LiteLLM embedding API.

        Args:
            texts: Texts to embed.

        Returns:
            Tuple of (embeddings list, tokens used).
        """
        start_time = time.time()

        # Determine routing based on provider (not port number)
        # Providers like ollama, lmstudio require direct calls with provider prefix
        is_direct_provider = (
            self.provider and self.provider.lower() in self.DIRECT_CALL_PROVIDERS
        )

        if is_direct_provider:
            # Direct call to local provider (Ollama, LM Studio, etc.)
            # Format model name with provider prefix if not already present
            model_name = self.model
            provider_prefix = f"{self.provider.lower()}/"
            if not model_name.startswith(provider_prefix):
                model_name = f"{provider_prefix}{model_name}"

            response = await aembedding(
                model=model_name,
                input=texts,
                api_base=self.api_base,
                timeout=settings.embedding_timeout,
            )
        else:
            # Default: call through LiteLLM proxy with OpenAI-compatible format
            response = await aembedding(
                model=self.model,
                input=texts,
                api_base=self.api_base,
                api_key=self.api_key,
                timeout=settings.embedding_timeout,
                custom_llm_provider="openai",  # Use OpenAI-compatible API format for LiteLLM proxy
            )

        elapsed = time.time() - start_time

        # Extract embeddings from response
        embeddings = [item["embedding"] for item in response.data]

        # Extract token usage
        tokens_used = response.usage.total_tokens if response.usage else 0

        logger.debug(
            "embedding_api_call",
            text_count=len(texts),
            tokens_used=tokens_used,
            elapsed_seconds=round(elapsed, 2),
            provider=self.provider,
            is_direct_provider=is_direct_provider,
        )

        return embeddings, tokens_used

    def get_total_tokens_used(self) -> int:
        """Get total tokens used across all API calls.

        Returns:
            Total tokens used for cost tracking.
        """
        return self.total_tokens_used

    def reset_token_counter(self) -> None:
        """Reset the token usage counter."""
        self.total_tokens_used = 0

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 500,
        stream: bool = False,
        model: str | None = None,
        top_p: float | None = None,
        timeout: float | None = None,
    ):
        """Generate chat completion via LiteLLM.

        Story 7-10: Supports KB-specific generation model via model parameter.

        Args:
            messages: List of message dicts with 'role' and 'content'.
                Example: [{"role": "system", "content": "..."}, ...]
            temperature: Sampling temperature (0.0-2.0). Lower = more deterministic.
            max_tokens: Maximum tokens in response.
            stream: If True, return async generator of chunks. If False, return
                complete response.
            model: Optional model ID override for KB-specific generation (Story 7-10).
                If None, uses settings.llm_model default.
            top_p: Nucleus sampling parameter (0.0-1.0). Controls token diversity.
            timeout: Optional request timeout in seconds. If None, uses settings.llm_timeout.
                Story 8-0: Allows model-specific timeout for query rewriting.

        Returns:
            If stream=False: Response dict with 'choices' containing generated text.
                Example: {"choices": [{"message": {"content": "..."}}]}
            If stream=True: AsyncGenerator yielding chunks with delta content.

        Raises:
            EmbeddingError: If LLM API fails.
        """
        try:
            # Use litellm_proxy/ prefix when calling through LiteLLM proxy server
            # Per Context7 docs: model="litellm_proxy/your-model-name" for proxy calls
            # This prevents duplicate streaming requests that occur with other prefixes
            # Story 7-10: Use KB-specific model if provided, else use default
            model_name = model or settings.llm_model
            if not model_name.startswith("litellm_proxy/"):
                # Strip any existing prefix and use litellm_proxy/
                if "/" in model_name:
                    model_name = model_name.split("/", 1)[1]
                model_name = f"litellm_proxy/{model_name}"

            # Build completion kwargs
            completion_kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "api_base": self.api_base,
                "api_key": self.api_key,
                "timeout": timeout
                or settings.llm_timeout,  # Use custom or default (120s)
                "stream": stream,
                "num_retries": 0,  # Disable retries to prevent duplicate streaming requests
            }
            # Only include top_p if provided (some models don't support it)
            if top_p is not None:
                completion_kwargs["top_p"] = top_p

            response = await acompletion(**completion_kwargs)

            if stream:
                # Return async generator for streaming
                logger.debug(
                    "chat_completion_stream_started",
                    model=model_name,
                    message_count=len(messages),
                )
                return response
            else:
                # Return complete response
                logger.debug(
                    "chat_completion_success",
                    model=model_name,
                    message_count=len(messages),
                    response_length=(
                        len(response.choices[0].message.content)
                        if response.choices
                        else 0
                    ),
                )
                return response

        except Exception as e:
            logger.error("chat_completion_failed", error=str(e))
            raise EmbeddingError(f"LLM completion failed: {str(e)}") from e


# Singleton instance for use across the application
embedding_client = LiteLLMEmbeddingClient()


async def get_embeddings(
    texts: list[str],
    model: str | None = None,
) -> list[list[float]]:
    """Convenience function to generate embeddings.

    Args:
        texts: List of text strings to embed.
        model: Optional model override.

    Returns:
        List of embedding vectors.
    """
    if model and model != embedding_client.model:
        # Create a temporary client with different model
        client = LiteLLMEmbeddingClient(model=model)
        return await client.get_embeddings(texts)

    return await embedding_client.get_embeddings(texts)


def reset_litellm_logging_worker() -> None:
    """Reset LiteLLM's global logging worker queue.

    Call this when initializing a new event loop (e.g., in Celery worker tasks)
    to prevent "Queue is bound to a different event loop" errors.

    The LoggingWorker uses asyncio.Queue which gets bound to the event loop
    that was active when the queue was created. In Celery workers, each task
    may run in a different event loop context, causing RuntimeError.
    """
    try:
        from litellm.litellm_core_utils.logging_worker import GLOBAL_LOGGING_WORKER

        if GLOBAL_LOGGING_WORKER is not None:
            # Reset the queue to None so it will be recreated with the new event loop
            GLOBAL_LOGGING_WORKER._queue = None
            GLOBAL_LOGGING_WORKER._worker_task = None
            GLOBAL_LOGGING_WORKER._sem = None
            logger.debug("litellm_logging_worker_reset")
    except Exception as e:
        # Log but don't raise - this is best-effort
        logger.debug("litellm_logging_worker_reset_skipped", reason=str(e))


async def close_litellm_clients() -> None:
    """Close LiteLLM async HTTP clients gracefully.

    Should be called during application shutdown BEFORE the event loop closes.
    This prevents the "no event loop in thread" error that occurs when
    LiteLLM's atexit handler tries to cleanup after the loop is gone.

    Call this in FastAPI's lifespan shutdown handler.
    """
    try:
        # Use LiteLLM's built-in cleanup function if available
        if hasattr(litellm, "close_litellm_async_clients"):
            await litellm.close_litellm_async_clients()
            logger.info("litellm_clients_closed")
        else:
            # Fallback: close module-level clients directly
            if (
                hasattr(litellm, "module_level_aclient")
                and litellm.module_level_aclient
            ):
                await litellm.module_level_aclient.aclose()
            if hasattr(litellm, "aclient_session") and litellm.aclient_session:
                await litellm.aclient_session.aclose()
            logger.info("litellm_clients_closed_fallback")
    except Exception as e:
        # Log but don't raise - shutdown should be best-effort
        logger.warning("litellm_client_close_error", error=str(e))
