"""Query rewriter service for history-aware conversational RAG.

Story 8-0: History-Aware Query Rewriting
Implements query reformulation using conversation history context.
Uses a cheap LLM to resolve pronouns and expand implicit references.
"""

import time
from dataclasses import dataclass

import structlog

from app.integrations.litellm_client import LiteLLMEmbeddingClient
from app.services.config_service import ConfigService
from app.services.observability_service import ObservabilityService, TraceContext

logger = structlog.get_logger(__name__)


@dataclass
class RewriteResult:
    """Result of query rewriting operation.

    Attributes:
        original_query: The original user query
        rewritten_query: The reformulated standalone query
        was_rewritten: Whether the query was actually modified
        model_used: The LLM model ID used for rewriting
        latency_ms: Time taken for rewriting in milliseconds
    """

    original_query: str
    rewritten_query: str
    was_rewritten: bool
    model_used: str
    latency_ms: float


class QueryRewriterService:
    """History-aware query rewriting for conversational RAG.

    Uses a lightweight LLM to reformulate follow-up questions into
    standalone queries that can be understood without chat history.

    Key features:
    - Resolves pronouns (he/she/it/they) to specific entities
    - Expands implicit references ("the same thing", "that") to actual topics
    - Graceful degradation: returns original query on any failure
    - 5-second timeout to prevent blocking
    - Observability integration for tracing and metrics
    """

    REWRITE_PROMPT = """Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question which can be understood without the chat history.

Rules:
- Resolve all pronouns (he/she/it/they) to specific entities mentioned in history
- Expand implicit references ("the same thing", "that") to actual topics
- Do NOT answer the question, only reformulate it
- If the question is already standalone, return it unchanged
- Keep the reformulated question concise

Chat History:
{chat_history}

Latest Question: {question}

Standalone Question:"""

    # Pronouns and references that indicate a follow-up question
    PRONOUNS = frozenset(
        {
            "he",
            "she",
            "it",
            "they",
            "them",
            "his",
            "her",
            "its",
            "their",
            "him",
            "hers",
            "theirs",
            "himself",
            "herself",
            "itself",
            "themselves",
        }
    )
    REFERENCES = frozenset(
        {
            "this",
            "that",
            "these",
            "those",
            "the same",
            "above",
            "previous",
            "earlier",
            "mentioned",
            "said",
            "discussed",
            "talked about",
        }
    )
    # Follow-up question patterns that need context (phrases that start follow-ups)
    FOLLOW_UP_STARTERS = frozenset(
        {
            "what about",
            "how about",
            "and what",
            "and how",
            "and the",
            "what else",
            "anything else",
            "any other",
            "tell me more",
            "more about",
            "explain more",
            "go deeper",
            "elaborate on",
            "can you explain",
            "can you tell",
            "what is the next",
            "next phase",
            "next step",
            "other phases",
            "other steps",
            "similarly",
        }
    )

    def __init__(
        self,
        llm_client: LiteLLMEmbeddingClient,
        config_service: ConfigService,
    ):
        """Initialize query rewriter service.

        Args:
            llm_client: LiteLLM client for LLM calls
            config_service: Config service for getting rewriter model ID
        """
        self.llm = llm_client
        self.config = config_service

    async def rewrite_with_history(
        self,
        query: str,
        chat_history: list[dict],
        trace_ctx: TraceContext | None = None,
    ) -> RewriteResult:
        """Rewrite query using conversation history context.

        Args:
            query: The user's current query
            chat_history: List of previous messages with role/content keys
            trace_ctx: Optional trace context for observability

        Returns:
            RewriteResult with original and rewritten queries
        """
        start_time = time.time()

        # Log entry for debugging
        logger.info(
            "query_rewrite_started",
            query=query[:100],
            history_count=len(chat_history) if chat_history else 0,
        )

        # Skip if no history (first message in conversation)
        if not chat_history:
            logger.info("query_rewrite_skipped_no_history", query=query[:100])
            return RewriteResult(
                original_query=query,
                rewritten_query=query,
                was_rewritten=False,
                model_used="",
                latency_ms=0,
            )

        # Skip if query appears to be standalone (heuristic check)
        is_standalone = self._is_standalone(query)
        logger.info(
            "query_rewrite_standalone_check",
            query=query[:100],
            is_standalone=is_standalone,
        )

        if is_standalone:
            logger.info(
                "query_rewrite_skipped_standalone",
                query=query[:100],
            )
            return RewriteResult(
                original_query=query,
                rewritten_query=query,
                was_rewritten=False,
                model_used="",
                latency_ms=0,
            )

        # Get configured rewriter model and timeout (cheap/fast LLM)
        rewriter_model = await self.config.get_rewriter_model()
        rewriter_timeout = await self.config.get_rewriter_timeout()
        logger.info(
            "query_rewrite_model_resolved",
            model=rewriter_model,
            timeout=rewriter_timeout,
        )

        # Format chat history for prompt
        history_text = self._format_history(chat_history)

        # Build prompt
        prompt = self.REWRITE_PROMPT.format(
            chat_history=history_text,
            question=query,
        )

        try:
            obs = ObservabilityService.get_instance()

            if trace_ctx:
                async with obs.span(trace_ctx, "query_rewrite", "llm") as _span_id:
                    response = await self.llm.chat_completion(
                        model=rewriter_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0,
                        max_tokens=200,
                        timeout=rewriter_timeout,  # Model-configured timeout
                    )
            else:
                response = await self.llm.chat_completion(
                    model=rewriter_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=200,
                    timeout=rewriter_timeout,  # Model-configured timeout
                )

            raw_content = response.choices[0].message.content
            rewritten = raw_content.strip() if raw_content else query
            latency_ms = (time.time() - start_time) * 1000

            # Log successful rewrite
            logger.info(
                "query_rewritten",
                original=query[:100],
                rewritten=rewritten[:100],
                model=rewriter_model,
                latency_ms=round(latency_ms, 2),
            )

            # Log LLM call metrics if trace context available
            if trace_ctx:
                usage = getattr(response, "usage", None)
                await obs.log_llm_call(
                    ctx=trace_ctx,  # Fixed: was passing trace_id instead of ctx
                    name="query_rewrite",
                    model=rewriter_model,
                    input_tokens=usage.prompt_tokens if usage else None,
                    output_tokens=usage.completion_tokens if usage else None,
                )

            return RewriteResult(
                original_query=query,
                rewritten_query=rewritten,
                was_rewritten=True,
                model_used=rewriter_model,
                latency_ms=latency_ms,
            )

        except Exception as e:
            # Graceful degradation: return original query on any failure
            latency_ms = (time.time() - start_time) * 1000
            logger.warning(
                "query_rewriting_failed",
                error=str(e),
                error_type=type(e).__name__,
                query=query[:100],
                model=rewriter_model,
                latency_ms=round(latency_ms, 2),
            )
            return RewriteResult(
                original_query=query,
                rewritten_query=query,
                was_rewritten=False,
                model_used=rewriter_model,
                latency_ms=latency_ms,
            )

    def _is_standalone(self, query: str) -> bool:
        """Heuristic check if query needs rewriting.

        A query is considered standalone if it doesn't contain
        pronouns, reference words, or follow-up patterns that require context.

        Args:
            query: The user query to check

        Returns:
            True if query appears standalone, False if it needs rewriting
        """
        # Normalize query: lowercase and strip punctuation for word matching
        import re

        query_lower = query.lower()
        # Extract words, removing punctuation
        words = set(re.findall(r"\b[a-z]+\b", query_lower))

        # Check for pronouns
        if words & self.PRONOUNS:
            return False

        # Check for reference phrases (may span multiple words)
        if any(ref in query_lower for ref in self.REFERENCES):
            return False

        # Check for follow-up question patterns (e.g., "what about next phase")
        # Return True only if no follow-up patterns found (query is standalone)
        return not any(starter in query_lower for starter in self.FOLLOW_UP_STARTERS)

    def _format_history(self, history: list[dict]) -> str:
        """Format chat history for the rewrite prompt.

        Only includes the last 5 messages to keep context manageable.
        Truncates long messages to prevent prompt bloat.

        Args:
            history: List of message dicts with role/content

        Returns:
            Formatted string representation of chat history
        """
        lines = []
        # Take last 5 messages only (most recent context)
        for msg in history[-5:]:
            role = "Human" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            # Truncate long messages
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
