"""Query rewriter service for history-aware conversational RAG.

Story 8-0: History-Aware Query Rewriting
Implements query reformulation using conversation history context.
Uses a cheap LLM to resolve pronouns and expand implicit references.

Enhanced with Option B+C hybrid approach:
- Explicit last Q&A pair highlighting for better context resolution
- Generic sequence/reference resolution (works for any topic/KB)
- Increased context limits for recent exchanges
"""

import re
import time
from dataclasses import dataclass, field

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
        extracted_topics: Key topics extracted from conversation context (Story 8-0.1)
    """

    original_query: str
    rewritten_query: str
    was_rewritten: bool
    model_used: str
    latency_ms: float
    extracted_topics: list[str] = field(default_factory=list)


class QueryRewriterService:
    """History-aware query rewriting for conversational RAG.

    Uses a lightweight LLM to reformulate follow-up questions into
    standalone queries that can be understood without chat history.

    Key features:
    - Resolves pronouns (he/she/it/they) to specific entities
    - Expands implicit references ("the same thing", "that") to actual topics
    - Resolves sequential references ("next", "previous", "before/after")
    - Graceful degradation: returns original query on any failure
    - Configurable timeout to prevent blocking
    - Observability integration for tracing and metrics

    Enhanced B+C Hybrid Approach:
    - Last Q&A pair is highlighted separately for better context
    - Earlier history provides additional background
    - Generic resolution works for any topic sequence (phases, steps, chapters, etc.)
    """

    # Enhanced prompt with explicit last exchange, typo tolerance, and sequence resolution
    # Story 8-0.1: Added typo correction (AC-8.0.1.2), sequential examples (AC-8.0.1.1),
    #              and format preservation hints (AC-8.0.1.4)
    REWRITE_PROMPT = """You are a query rewriter for a conversational search system. Your task is to reformulate follow-up questions into standalone queries.

## Most Recent Exchange (IMPORTANT - use this for context resolution):
User asked: {last_user_question}
Assistant answered about: {last_answer_summary}

## Earlier Conversation Context:
{earlier_history}

## Current User Question:
{question}

## Instructions:
1. TYPOS: First, correct obvious typos before interpreting:
   - "tha" → "that", "wha" → "what", "tel" → "tell", "teh" → "the"
   - "mroe" → "more", "abuot" → "about", "beofre" → "before"
2. PRONOUNS: Replace he/she/it/they/this/that with the specific entity from the conversation
3. REFERENCES: Expand "the same", "that one", "it" to the actual topic being discussed
4. SEQUENCES: When user says "next/previous/before/after/following":
   - Identify what sequence is being discussed (phases, steps, chapters, days, sections, etc.)
   - Determine the current position in that sequence from the last exchange
   - Resolve to the specific next/previous item in that sequence
   - Example: If discussing "Day 6", "next" or "day after" → "Day 7"
   - Example: If discussing "Phase D", "before that" → "Phase C"
5. COMPARISONS: When user asks "what about X" or "how about X", include the comparison context
6. FORMAT HINTS: If the previous answer used a numbered list format, phrase your query to elicit similar format
   - Example: "List the topics covered on Day 7" instead of "What is Day 7 about?"
7. Keep the rewritten question concise and natural
8. If the question is already standalone, return it unchanged
9. Do NOT answer the question, only reformulate it

## Examples:
Example 1 - Sequential + Typo:
History: User asked about Day 6 study plan
Question: "how about a day after tha"
Reformulated: What is covered on Day 7 of the study plan?

Example 2 - Previous Reference:
History: User asked about Phase D
Question: "and the one before"
Reformulated: What is Phase C in the TOGAF framework?

## Standalone Question:"""

    # Shorter prompt for cases with minimal history (only 1 exchange)
    # Story 8-0.1: Added typo correction and sequential reference rules
    REWRITE_PROMPT_MINIMAL = """Reformulate this follow-up question into a standalone question.

Last exchange:
- User asked: {last_user_question}
- Topic discussed: {last_answer_summary}

Current question: {question}

Rules:
- FIRST, correct obvious typos: "tha"→"that", "wha"→"what", "tel"→"tell", "teh"→"the"
- Replace pronouns (it/they/this/that) with actual entities
- Resolve "next/previous/after/before" to specific items (if Day 6 → next = Day 7)
- If previous answer was a list, phrase query to elicit similar format
- Keep it concise and natural
- If already standalone, return unchanged

Standalone question:"""

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

        Enhanced B+C hybrid approach:
        - Extracts last Q&A pair explicitly for better context resolution
        - Summarizes last assistant response for topic identification
        - Formats earlier history as background context
        - Uses appropriate prompt based on history depth

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

        # LangChain approach: Always use LLM for rewriting when history exists
        # The LLM will return the query unchanged if it's truly standalone
        # This handles ALL implicit context references (day 3, session 5, module N, etc.)
        # without needing to enumerate patterns
        #
        # Previous approach used _is_standalone() heuristic to skip rewriting for queries
        # without pronouns/references, but this missed implicit context like "day 3"
        # referencing a study plan from the previous message.
        #
        # See: LangChain's create_history_aware_retriever which always reformulates
        # when chat_history exists, letting the LLM decide if context is needed.

        # Log heuristic result for observability only (not used for flow control)
        is_standalone_heuristic = self._is_standalone(query)
        logger.info(
            "query_rewrite_with_history",
            query=query[:100],
            history_count=len(chat_history),
            heuristic_standalone=is_standalone_heuristic,
        )

        # Get configured rewriter model and timeout (cheap/fast LLM)
        rewriter_model = await self.config.get_rewriter_model()
        rewriter_timeout = await self.config.get_rewriter_timeout()
        logger.info(
            "query_rewrite_model_resolved",
            model=rewriter_model,
            timeout=rewriter_timeout,
        )

        # Extract last Q&A pair explicitly (B+C hybrid approach)
        last_user_question, last_answer_summary, earlier_history, extracted_topics = (
            self._extract_conversation_context(chat_history)
        )

        logger.info(
            "query_rewrite_context_extracted",
            last_user_q_len=len(last_user_question),
            last_answer_len=len(last_answer_summary),
            earlier_history_len=len(earlier_history),
            extracted_topics=extracted_topics,
        )

        # Choose prompt based on history depth
        if len(chat_history) <= 2:
            # Minimal history - use shorter prompt
            prompt = self.REWRITE_PROMPT_MINIMAL.format(
                last_user_question=last_user_question,
                last_answer_summary=last_answer_summary,
                question=query,
            )
        else:
            # Full history - use comprehensive prompt
            prompt = self.REWRITE_PROMPT.format(
                last_user_question=last_user_question,
                last_answer_summary=last_answer_summary,
                earlier_history=earlier_history,
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
                        timeout=rewriter_timeout,
                    )
            else:
                response = await self.llm.chat_completion(
                    model=rewriter_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=200,
                    timeout=rewriter_timeout,
                )

            raw_content = response.choices[0].message.content
            rewritten = self._clean_rewritten_query(raw_content, query)
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
                    ctx=trace_ctx,
                    name="query_rewrite",
                    model=rewriter_model,
                    input_tokens=usage.prompt_tokens if usage else None,
                    output_tokens=usage.completion_tokens if usage else None,
                )

            return RewriteResult(
                original_query=query,
                rewritten_query=rewritten,
                was_rewritten=rewritten != query,
                model_used=rewriter_model,
                latency_ms=latency_ms,
                extracted_topics=extracted_topics,
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
                extracted_topics=extracted_topics,
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

    def _extract_conversation_context(
        self, history: list[dict]
    ) -> tuple[str, str, str, list[str]]:
        """Extract structured context from conversation history.

        B+C Hybrid approach: Separates last Q&A pair from earlier history
        for more effective context resolution.

        Enhanced in Story 8-0.1 to also extract key topics from last answer.

        Args:
            history: List of message dicts with role/content

        Returns:
            Tuple of (last_user_question, last_answer_summary, earlier_history, extracted_topics)
        """
        if not history:
            return "", "", "", []

        # Find the last user question and assistant answer
        last_user_question = ""
        last_assistant_answer = ""

        # Iterate backwards to find the most recent Q&A pair
        for i in range(len(history) - 1, -1, -1):
            msg = history[i]
            if msg.get("role") == "assistant" and not last_assistant_answer:
                last_assistant_answer = msg.get("content", "")
            elif msg.get("role") == "user" and not last_user_question:
                last_user_question = msg.get("content", "")

            # Stop once we have both
            if last_user_question and last_assistant_answer:
                break

        # Story 8-0.1: Extract key topics BEFORE summarizing (need full answer)
        extracted_topics = self._extract_key_topics(last_assistant_answer)

        # Summarize the last assistant answer (extract key topic/entity)
        # Increase limit to 800 chars to capture more context
        last_answer_summary = self._summarize_answer(last_assistant_answer)

        # Format earlier history (excluding the last Q&A pair)
        earlier_messages = []
        skip_count = 0

        for msg in reversed(history):
            if skip_count < 2 and (
                (
                    msg.get("role") == "assistant"
                    and msg.get("content") == last_assistant_answer
                )
                or (
                    msg.get("role") == "user"
                    and msg.get("content") == last_user_question
                )
            ):
                skip_count += 1
                continue
            earlier_messages.insert(0, msg)

        earlier_history = self._format_earlier_history(earlier_messages)

        return (
            last_user_question[:400],
            last_answer_summary,
            earlier_history,
            extracted_topics,
        )

    def _extract_key_topics(self, text: str) -> list[str]:
        """Extract key topics from assistant response (Story 8-0.1 AC-8.0.1.3).

        Identifies important topics that may be referenced in follow-up questions:
        - Numbered items (Day 1, Step 2, Phase A, Chapter 3)
        - Markdown headers (## Topic)
        - Bold text (**important term**)

        Prioritizes LAST items in sequences (most relevant for "next/previous" follow-ups).

        Args:
            text: Full assistant response text

        Returns:
            List of up to 5 deduplicated key topics
        """
        if not text:
            return []

        topics = []

        # 1. Extract markdown headers (##, ###)
        headers = re.findall(r"^#{1,3}\s*(.+?)$", text, re.MULTILINE)
        # Clean headers: remove trailing punctuation and limit length
        headers = [h.strip().rstrip(":").strip()[:50] for h in headers]
        topics.extend(headers[:3])  # First 3 headers

        # 2. Extract numbered/lettered items (Day 1, Step 2, Phase A, Chapter 3, etc.)
        # Pattern matches: Day 6, Phase C, Step 1, Chapter 3, Part A, Section 2
        numbered_items = re.findall(
            r"\b((?:Day|Step|Phase|Chapter|Part|Section|Module|Lesson|Unit|Week)\s+\d+[A-Z]?)\b",
            text,
            re.IGNORECASE,
        )
        # Normalize case: "day 6" -> "Day 6"
        numbered_items = [item.title() for item in numbered_items]
        # Take LAST 3 items (most relevant for follow-ups about "next")
        topics.extend(numbered_items[-3:])

        # 3. Extract bold topics (**topic**)
        bold_items = re.findall(r"\*\*([^*]{2,50})\*\*", text)
        # Filter out overly generic terms
        bold_items = [
            b.strip()
            for b in bold_items
            if len(b.strip()) >= 3
            and b.strip().lower() not in {"the", "and", "for", "but"}
        ]
        topics.extend(bold_items[:3])  # First 3 bold items

        # Deduplicate while preserving order (keep last occurrence for numbered items)
        seen = set()
        unique_topics = []
        for topic in reversed(topics):
            topic_lower = topic.lower()
            if topic_lower not in seen:
                seen.add(topic_lower)
                unique_topics.insert(0, topic)

        return unique_topics[:5]  # Max 5 topics

    def _summarize_answer(self, answer: str, include_topics: bool = True) -> str:
        """Summarize assistant answer to extract key topic information.

        Enhanced in Story 8-0.1 to include extracted key topics at the end
        of the summary, ensuring sequential references can be resolved.

        Args:
            answer: Full assistant response
            include_topics: Whether to append extracted topics (default True)

        Returns:
            Summarized answer focusing on topic identification (up to 800 chars)
        """
        if not answer:
            return ""

        # Take first 800 chars to capture the main topic
        # This is increased from 500 to ensure key context isn't truncated
        summary = answer[:800]

        # If truncated mid-sentence, try to end at a sentence boundary
        if len(answer) > 800:
            # Find last sentence boundary
            for punct in [". ", ".\n", "! ", "? "]:
                last_punct = summary.rfind(punct)
                if last_punct > 400:  # Keep at least 400 chars
                    summary = summary[: last_punct + 1]
                    break
            else:
                summary += "..."

        # Story 8-0.1: Append extracted key topics for better context resolution
        if include_topics:
            topics = self._extract_key_topics(answer)
            if topics:
                # Add topics that might be beyond the 800-char cutoff
                topic_str = ", ".join(topics)
                # Check if last topic already in summary (avoid duplication)
                if topics[-1].lower() not in summary.lower():
                    summary += f" [Key topics: {topic_str}]"

        return summary

    def _format_earlier_history(self, history: list[dict]) -> str:
        """Format earlier conversation history (excluding last Q&A pair).

        Provides background context for multi-turn conversations.
        Limited to last 3 exchanges to keep prompt manageable.

        Args:
            history: List of message dicts (excluding last Q&A pair)

        Returns:
            Formatted string of earlier conversation
        """
        if not history:
            return "(No earlier conversation)"

        lines = []
        # Take last 6 messages (3 exchanges) for background context
        for msg in history[-6:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            # Shorter truncation for earlier messages
            if len(content) > 300:
                content = content[:300] + "..."
            lines.append(f"{role}: {content}")

        return "\n".join(lines) if lines else "(No earlier conversation)"

    def _clean_rewritten_query(self, raw_response: str, original_query: str) -> str:
        """Clean and validate the rewritten query from LLM response.

        Handles common LLM output issues:
        - Strips whitespace and quotes
        - Removes any preamble text
        - Falls back to original if response is empty or invalid

        Args:
            raw_response: Raw LLM response text
            original_query: Original query to fall back to

        Returns:
            Cleaned rewritten query
        """
        import re

        if not raw_response:
            return original_query

        cleaned = raw_response.strip()

        # Remove common preamble patterns (static prefixes)
        prefixes_to_remove = [
            "Standalone question:",
            "Standalone Question:",
            "Here is the standalone question:",
            "The standalone question is:",
            "Rewritten question:",
            "Rewritten:",
            "Reformulated question:",
            "Reformulated:",
        ]
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix) :].strip()

        # Handle verbose LLM responses with preamble followed by actual question
        # Pattern: "Based on... Original question: X Reformulated question: Y"
        # or "I will reformulate... Reformulated question: Y"
        reformulated_patterns = [
            r"(?:Reformulated|Rewritten|Standalone)\s+question:\s*(.+?)(?:\s*$)",
            r"(?:The\s+)?(?:reformulated|rewritten|standalone)\s+(?:question|query)\s+(?:is|would be):\s*(.+?)(?:\s*$)",
        ]
        for pattern in reformulated_patterns:
            match = re.search(pattern, cleaned, re.IGNORECASE | re.DOTALL)
            if match:
                extracted = match.group(1).strip()
                if extracted and len(extracted) >= 5:
                    cleaned = extracted
                    break

        # Remove surrounding quotes if present
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (
            cleaned.startswith("'") and cleaned.endswith("'")
        ):
            cleaned = cleaned[1:-1].strip()

        # Validate: if empty or too short, return original
        if not cleaned or len(cleaned) < 3:
            return original_query

        # Validate: if response is suspiciously long (LLM answered instead of rewriting)
        if len(cleaned) > len(original_query) * 5 and len(cleaned) > 500:
            logger.warning(
                "query_rewrite_response_too_long",
                original_len=len(original_query),
                response_len=len(cleaned),
            )
            return original_query

        return cleaned

    def _format_history(self, history: list[dict]) -> str:
        """Format chat history for the rewrite prompt (legacy method).

        Kept for backward compatibility. New code should use
        _extract_conversation_context() for better context resolution.

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
