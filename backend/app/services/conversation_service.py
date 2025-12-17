"""Conversation service for multi-turn RAG conversations."""

import json
import re
import time
import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import structlog
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.redis import RedisClient
from app.integrations.litellm_client import embedding_client
from app.models.knowledge_base import KnowledgeBase
from app.schemas.chat import (
    ChunkDebugInfo,
    DebugInfo,
    KBParamsDebugInfo,
    QueryRewriteDebugInfo,
    TimingDebugInfo,
)
from app.schemas.citation import Citation
from app.schemas.kb_settings import (
    CitationStyle,
    GenerationConfig,
    KBPromptConfig,
    KBSettings,
    UncertaintyHandling,
)
from app.schemas.search import SearchResultSchema
from app.services.citation_service import CitationService
from app.services.kb_config_resolver import DEFAULT_SYSTEM_PROMPT, KBConfigResolver
from app.services.observability_service import ObservabilityService, TraceContext
from app.services.query_rewriter_service import QueryRewriterService, RewriteResult
from app.services.search_service import SearchService

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)

# Configuration constants
MAX_CONTEXT_TOKENS = 6000  # Reserve 2000 for response
MAX_HISTORY_MESSAGES = 10  # Last 10 message pairs
CONVERSATION_TTL = 86400  # 24 hours in seconds

# Legacy system prompt constant - kept for reference/fallback (see DEFAULT_SYSTEM_PROMPT in kb_config_resolver.py)
# Story 9-15: Dynamic prompts now resolved from KB settings via _resolve_kb_prompt_config()
CHAT_SYSTEM_PROMPT = """You are a helpful assistant answering questions based on provided source documents.

CRITICAL RULES:
1. Every factual claim MUST have a citation using [n] notation
2. Use [1] for first source, [2] for second source, etc.
3. Multiple sources for one claim: [1][2]
4. If information isn't in sources, say "I don't have information about that in the available documents."
5. Be conversational and maintain context from previous messages
6. When user refers to previous context (e.g., "What about..."), understand they mean within the current conversation

Example:
User: "How did we handle authentication?"
Assistant: "Our authentication approach uses OAuth 2.0 with PKCE [1] and supports MFA via TOTP [2]."
User: "What about session timeout?"
Assistant: "The session timeout for OAuth flows [3] is configured to 60 minutes..."

Sources will be provided below with their numbers."""

# Language name mapping for response_language instruction
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "ru": "Russian",
    "vi": "Vietnamese",
}


class NoDocumentsError(Exception):
    """Raised when KB has no indexed documents."""

    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        self.message = "This Knowledge Base has no indexed documents. Please upload documents first."
        super().__init__(self.message)


class ConversationService:
    """Service for managing multi-turn RAG conversations.

    Orchestrates:
    1. Conversation history management (Redis)
    2. RAG retrieval (SearchService)
    3. Context window management (token counting, truncation)
    4. LLM response generation (LiteLLMClient)
    5. Citation extraction (CitationService)
    """

    def __init__(
        self,
        search_service: SearchService,
        citation_service: CitationService | None = None,
        session: AsyncSession | None = None,
        redis_client: Redis | None = None,
        query_rewriter: QueryRewriterService | None = None,
    ):
        """Initialize conversation service.

        Args:
            search_service: Search service for RAG retrieval
            citation_service: Citation service for extracting citations (default: new instance)
            session: Database session for KB model lookup (optional)
            redis_client: Redis client for KB config caching (optional)
            query_rewriter: Query rewriter service for history-aware rewriting (optional)
        """
        self.search_service = search_service
        self.citation_service = citation_service or CitationService()
        self.llm_client = embedding_client  # Reuse singleton LiteLLM client
        self._session = session
        self._redis_client = redis_client
        self._kb_config_resolver: KBConfigResolver | None = None
        self._query_rewriter = query_rewriter
        if session and redis_client:
            self._kb_config_resolver = KBConfigResolver(session, redis_client)

    async def _get_kb_generation_model(self, kb_id: str) -> str | None:
        """Get KB-specific generation model ID.

        Args:
            kb_id: Knowledge Base ID

        Returns:
            Model ID string (e.g., 'ollama/llama3.2') or None if using default
        """
        if not self._session:
            logger.debug("no_db_session_for_kb_model_lookup", kb_id=kb_id)
            return None

        try:
            result = await self._session.execute(
                select(KnowledgeBase)
                .options(joinedload(KnowledgeBase.generation_model))
                .where(KnowledgeBase.id == uuid.UUID(kb_id))
            )
            kb = result.unique().scalar_one_or_none()

            if kb and kb.generation_model:
                # Use proxy alias format (db-{uuid}) that LiteLLM proxy recognizes
                proxy_model_id = f"db-{kb.generation_model.id}"
                logger.info(
                    "using_kb_generation_model",
                    kb_id=kb_id,
                    model_id=kb.generation_model.model_id,
                    proxy_model_id=proxy_model_id,
                    model_name=kb.generation_model.name,
                )
                return proxy_model_id
            else:
                logger.debug(
                    "kb_has_no_generation_model",
                    kb_id=kb_id,
                    using_default=True,
                )
                return None
        except Exception as e:
            logger.warning(
                "kb_model_lookup_failed",
                kb_id=kb_id,
                error=str(e),
            )
            return None

    async def _resolve_generation_config(self, kb_id: str) -> GenerationConfig:
        """Resolve generation config for a KB.

        Uses three-layer precedence: Request → KB settings → System defaults.
        Returns schema defaults if no resolver is configured.

        Args:
            kb_id: Knowledge Base ID

        Returns:
            GenerationConfig with KB-level settings or defaults
        """
        if self._kb_config_resolver is None:
            # Fallback to schema defaults if no resolver configured
            logger.debug("no_kb_config_resolver_using_defaults", kb_id=kb_id)
            return GenerationConfig()

        try:
            config = await self._kb_config_resolver.resolve_generation_config(
                kb_id=uuid.UUID(kb_id),
            )
            logger.debug(
                "resolved_kb_generation_config",
                kb_id=kb_id,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
            )
            return config
        except Exception as e:
            logger.warning(
                "kb_generation_config_resolution_failed",
                kb_id=kb_id,
                error=str(e),
            )
            return GenerationConfig()

    async def _resolve_kb_prompt_config(self, kb_id: str) -> KBPromptConfig:
        """Resolve prompt configuration for a KB.

        AC-9.15.4: Returns KBPromptConfig with KB-level prompt settings.

        Args:
            kb_id: Knowledge Base ID

        Returns:
            KBPromptConfig with KB-level settings or defaults
        """
        if self._kb_config_resolver is None:
            logger.debug("no_kb_config_resolver_using_default_prompts", kb_id=kb_id)
            return KBPromptConfig()

        try:
            kb_settings = await self._kb_config_resolver.get_kb_settings(
                kb_id=uuid.UUID(kb_id)
            )
            logger.debug(
                "resolved_kb_prompt_config",
                kb_id=kb_id,
                has_custom_prompt=bool(kb_settings.prompts.system_prompt),
                citation_style=kb_settings.prompts.citation_style.value,
                response_language=kb_settings.prompts.response_language,
                uncertainty_handling=kb_settings.prompts.uncertainty_handling.value,
            )
            return kb_settings.prompts
        except Exception as e:
            logger.warning(
                "kb_prompt_config_resolution_failed",
                kb_id=kb_id,
                error=str(e),
            )
            return KBPromptConfig()

    async def _get_kb_name(self, kb_id: str) -> str:
        """Get KB name for variable interpolation.

        Args:
            kb_id: Knowledge Base ID

        Returns:
            KB name string or "Knowledge Base" as fallback
        """
        if not self._session:
            return "Knowledge Base"

        try:
            result = await self._session.execute(
                select(KnowledgeBase.name).where(KnowledgeBase.id == uuid.UUID(kb_id))
            )
            name = result.scalar_one_or_none()
            return name or "Knowledge Base"
        except Exception as e:
            logger.warning("kb_name_lookup_failed", kb_id=kb_id, error=str(e))
            return "Knowledge Base"

    def _build_system_prompt(
        self,
        prompt_config: KBPromptConfig,
        kb_name: str,
        context_text: str,
        query: str,
    ) -> str:
        """Build dynamic system prompt from KB configuration.

        AC-9.15.4: Uses KB system_prompt instead of hardcoded constant.
        AC-9.15.5: Supports variable interpolation: {kb_name}, {context}, {query}.
        AC-9.15.6: Falls back to DEFAULT_SYSTEM_PROMPT if KB prompt empty.
        AC-9.15.7: citation_style affects LLM instruction.
        AC-9.15.8: response_language instruction appended when not "en".
        AC-9.15.9: uncertainty_handling affects LLM behavior.

        Args:
            prompt_config: KB prompt configuration
            kb_name: Name of the knowledge base for interpolation
            context_text: Retrieved context for {context} interpolation
            query: User query for {query} interpolation

        Returns:
            Fully constructed system prompt string
        """
        # AC-9.15.6: Use KB prompt or fallback to default
        base_prompt = prompt_config.system_prompt.strip()
        if not base_prompt:
            base_prompt = DEFAULT_SYSTEM_PROMPT

        # AC-9.15.5: Variable interpolation (safe - only interpolate if placeholders exist)
        # Using format_map with defaultdict to avoid KeyError for missing placeholders
        try:
            system_prompt = base_prompt.format(
                kb_name=kb_name,
                context=context_text,
                query=query,
            )
        except KeyError:
            # If format string has unknown placeholders, use base prompt as-is
            logger.warning(
                "system_prompt_interpolation_failed",
                base_prompt_preview=base_prompt[:100],
            )
            system_prompt = base_prompt

        # Build additional instructions based on config
        instructions: list[str] = []

        # AC-9.15.7: Citation style instruction
        if prompt_config.citation_style == CitationStyle.INLINE:
            instructions.append(
                "Always cite sources using [n] notation inline with the text. "
                "For example: 'The approach uses OAuth 2.0 [1].'"
            )
        elif prompt_config.citation_style == CitationStyle.FOOTNOTE:
            instructions.append(
                "Add footnote-style citations at the end of your response. "
                "Reference them in text with superscript numbers."
            )
        elif prompt_config.citation_style == CitationStyle.NONE:
            instructions.append(
                "Do not include citation markers in your response. "
                "Integrate source information naturally into the text."
            )

        # AC-9.15.8: Response language instruction
        if prompt_config.response_language != "en":
            lang_code = prompt_config.response_language
            lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
            instructions.append(f"Respond in {lang_name}.")

        # AC-9.15.9: Uncertainty handling instruction
        if prompt_config.uncertainty_handling == UncertaintyHandling.ACKNOWLEDGE:
            instructions.append(
                "If information is not in the provided sources or you're uncertain, "
                "acknowledge this clearly and explain what you do know."
            )
        elif prompt_config.uncertainty_handling == UncertaintyHandling.REFUSE:
            instructions.append(
                "If you cannot find relevant information in the provided sources, "
                "politely decline to answer rather than speculate."
            )
        elif prompt_config.uncertainty_handling == UncertaintyHandling.BEST_EFFORT:
            instructions.append(
                "Provide the best possible answer based on available sources. "
                "If sources are limited, use your knowledge while noting limitations."
            )

        # Append instructions to system prompt
        if instructions:
            system_prompt += "\n\n" + "\n".join(instructions)

        return system_prompt

    async def _get_kb_settings(self, kb_id: str) -> KBSettings:
        """Get full KB settings including debug_mode flag.

        Args:
            kb_id: Knowledge Base ID

        Returns:
            KBSettings with all configuration including debug_mode
        """
        if self._kb_config_resolver is None:
            return KBSettings()

        try:
            return await self._kb_config_resolver.get_kb_settings(
                kb_id=uuid.UUID(kb_id)
            )
        except Exception as e:
            logger.warning("kb_settings_lookup_failed", kb_id=kb_id, error=str(e))
            return KBSettings()

    async def _is_debug_mode_enabled(self, kb_id: str) -> bool:
        """Check if debug mode is enabled for a KB.

        AC-9.15.10: Returns True if KB has debug_mode=True.

        Args:
            kb_id: Knowledge Base ID

        Returns:
            True if debug mode is enabled, False otherwise
        """
        kb_settings = await self._get_kb_settings(kb_id)
        return kb_settings.debug_mode

    def _build_debug_info(
        self,
        prompt_config: KBPromptConfig,
        chunks: list[SearchResultSchema],
        retrieval_ms: float,
        context_assembly_ms: float,
        rewrite_result: RewriteResult | None = None,
    ) -> DebugInfo:
        """Build debug info from RAG pipeline data.

        AC-9.15.11: Constructs DebugInfo with kb_params, chunks_retrieved, timing.
        Story 8-0: Adds query_rewrite info when history-aware rewriting is performed.

        Args:
            prompt_config: KB prompt configuration
            chunks: Retrieved chunks with scores
            retrieval_ms: Time spent on retrieval in milliseconds
            context_assembly_ms: Time spent on context assembly in milliseconds
            rewrite_result: Query rewriting result (optional, Story 8-0)

        Returns:
            DebugInfo with pipeline telemetry
        """
        # Build KB params debug info
        kb_params = KBParamsDebugInfo(
            system_prompt_preview=prompt_config.system_prompt[:100]
            if prompt_config.system_prompt
            else DEFAULT_SYSTEM_PROMPT[:100],
            citation_style=prompt_config.citation_style.value,
            response_language=prompt_config.response_language,
            uncertainty_handling=prompt_config.uncertainty_handling.value,
        )

        # Build chunks debug info
        chunks_debug = [
            ChunkDebugInfo(
                preview=chunk.chunk_text[:100] if chunk.chunk_text else "",
                similarity_score=chunk.relevance_score,
                document_name=chunk.document_name or "Unknown",
                page_number=chunk.page_number,
            )
            for chunk in chunks
        ]

        # Build timing debug info (include rewrite time if available)
        timing = TimingDebugInfo(
            retrieval_ms=retrieval_ms,
            context_assembly_ms=context_assembly_ms,
            query_rewrite_ms=rewrite_result.latency_ms if rewrite_result else 0,
        )

        # Build query rewrite debug info (Story 8-0)
        query_rewrite = None
        if rewrite_result:
            query_rewrite = QueryRewriteDebugInfo(
                original_query=rewrite_result.original_query,
                rewritten_query=rewrite_result.rewritten_query,
                was_rewritten=rewrite_result.was_rewritten,
                model_used=rewrite_result.model_used,
                latency_ms=rewrite_result.latency_ms,
            )

        return DebugInfo(
            kb_params=kb_params,
            chunks_retrieved=chunks_debug,
            timing=timing,
            query_rewrite=query_rewrite,
        )

    async def send_message(
        self,
        session_id: str,
        kb_id: str,
        user_id: str,
        message: str,
        conversation_id: str | None = None,
        trace_ctx: TraceContext | None = None,
    ) -> dict[str, Any]:
        """Send a chat message and get response with citations.

        Args:
            session_id: User session ID
            kb_id: Knowledge Base ID
            user_id: User ID for permission checks
            message: User message
            conversation_id: Existing conversation ID (optional)
            trace_ctx: Optional trace context for observability instrumentation

        Returns:
            Dict with answer, citations, confidence, conversation_id

        Raises:
            NoDocumentsError: If KB has no indexed documents
        """
        obs = ObservabilityService.get_instance()

        # Check if debug mode is enabled for this KB (AC-9.15.13)
        debug_mode_enabled = await self._is_debug_mode_enabled(kb_id)

        # 1. Retrieve conversation history
        history = await self.get_history(session_id, kb_id)

        # 1.5. Story 8-0: Rewrite query using conversation history
        rewrite_result: RewriteResult | None = None
        search_query = message  # Default to original message

        if self._query_rewriter and history:
            rewrite_result = await self._query_rewriter.rewrite_with_history(
                query=message,
                chat_history=history,
                trace_ctx=trace_ctx,
            )
            if rewrite_result.was_rewritten:
                search_query = rewrite_result.rewritten_query
                logger.info(
                    "query_rewritten_for_search",
                    original=message[:100],
                    rewritten=search_query[:100],
                    latency_ms=round(rewrite_result.latency_ms, 2),
                )

        # 2. Perform RAG retrieval with observability span and timing
        # Uses rewritten query if available, otherwise original message
        retrieval_start = time.time()
        if trace_ctx:
            async with obs.span(trace_ctx, "retrieval", "retrieval") as _span_id:
                search_response = await self.search_service.search(
                    query=search_query,
                    kb_ids=[kb_id],
                    user_id=user_id,
                    limit=10,
                    stream=False,
                )
        else:
            search_response = await self.search_service.search(
                query=search_query,
                kb_ids=[kb_id],
                user_id=user_id,
                limit=10,
                stream=False,
            )
        retrieval_ms = (time.time() - retrieval_start) * 1000

        if not search_response.results:
            raise NoDocumentsError(kb_id)

        # 3. Resolve KB prompt configuration (AC-9.15.4 through AC-9.15.9)
        prompt_config = await self._resolve_kb_prompt_config(kb_id)
        kb_name = await self._get_kb_name(kb_id)

        # Build context text for system prompt interpolation
        context_assembly_start = time.time()
        context_text = "\n\n".join(
            [
                f"[{i + 1}] {chunk.chunk_text}"
                for i, chunk in enumerate(search_response.results)
            ]
        )

        # Build dynamic system prompt with KB configuration
        system_prompt = self._build_system_prompt(
            prompt_config=prompt_config,
            kb_name=kb_name,
            context_text=context_text,
            query=message,
        )

        # 4. Build prompt with history + context (with observability span)
        if trace_ctx:
            async with obs.span(trace_ctx, "context_assembly", "retrieval") as _span_id:
                prompt_messages = self._build_prompt(
                    history, message, search_response.results, system_prompt
                )
                context_tokens = self._count_tokens(
                    "\n".join(msg["content"] for msg in prompt_messages)
                )
        else:
            prompt_messages = self._build_prompt(
                history, message, search_response.results, system_prompt
            )
            context_tokens = 0
        context_assembly_ms = (time.time() - context_assembly_start) * 1000

        # 5. Get KB-specific generation model and config (Story 7-10, 7-17)
        kb_model = await self._get_kb_generation_model(kb_id)
        gen_config = await self._resolve_generation_config(kb_id)

        # 5. Generate response via LiteLLM (with observability span)
        # Use KB-level generation settings (temperature, max_tokens, top_p)
        if trace_ctx:
            async with obs.span(trace_ctx, "synthesis", "llm") as _span_id:
                response = await self.llm_client.chat_completion(
                    messages=prompt_messages,
                    temperature=gen_config.temperature,
                    max_tokens=gen_config.max_tokens,
                    top_p=gen_config.top_p,
                    stream=False,
                    model=kb_model,  # Use KB-specific model if configured
                )
            # Log LLM call metrics
            usage = getattr(response, "usage", None)
            await obs.log_llm_call(
                trace_id=trace_ctx.trace_id,
                name="chat_completion",
                model=getattr(response, "model", kb_model or "default"),
                input_tokens=usage.prompt_tokens if usage else None,
                output_tokens=usage.completion_tokens if usage else None,
            )
        else:
            response = await self.llm_client.chat_completion(
                messages=prompt_messages,
                temperature=gen_config.temperature,
                max_tokens=gen_config.max_tokens,
                top_p=gen_config.top_p,
                stream=False,
                model=kb_model,  # Use KB-specific model if configured
            )

        response_text = response.choices[0].message.content

        # 5. Extract citations (with observability span)
        if trace_ctx:
            async with obs.span(trace_ctx, "citation_mapping", "retrieval") as _span_id:
                answer_with_markers, citations = (
                    self.citation_service.extract_citations(
                        response_text, search_response.results
                    )
                )
        else:
            answer_with_markers, citations = self.citation_service.extract_citations(
                response_text, search_response.results
            )

        # 6. Calculate confidence (average of chunk scores)
        confidence = (
            sum(result.relevance_score for result in search_response.results)
            / len(search_response.results)
            if search_response.results
            else 0.0
        )

        # 7. Store in Redis
        conversation_id = conversation_id or self._generate_conversation_id()
        await self._append_to_history(
            session_id=session_id,
            kb_id=kb_id,
            user_message=message,
            assistant_response=answer_with_markers,
            citations=citations,
            confidence=confidence,
        )

        # Log debug metrics
        logger.debug(
            "rag_pipeline_metrics",
            documents_retrieved=len(search_response.results),
            context_tokens=context_tokens,
            citations_generated=len(citations),
            confidence=confidence,
            debug_mode=debug_mode_enabled,
        )

        # Build response
        response_data = {
            "answer": answer_with_markers,
            "citations": [citation.model_dump() for citation in citations],
            "confidence": confidence,
            "conversation_id": conversation_id,
        }

        # AC-9.15.13: Include debug_info in non-streaming response when enabled
        if debug_mode_enabled:
            debug_info = self._build_debug_info(
                prompt_config=prompt_config,
                chunks=search_response.results,
                retrieval_ms=retrieval_ms,
                context_assembly_ms=context_assembly_ms,
                rewrite_result=rewrite_result,  # Story 8-0: Include query rewrite info
            )
            response_data["debug_info"] = debug_info.model_dump()
            logger.info(
                "debug_info_included_in_response",
                kb_id=kb_id,
                chunks_count=len(search_response.results),
                retrieval_ms=retrieval_ms,
                context_assembly_ms=context_assembly_ms,
                query_rewritten=rewrite_result.was_rewritten
                if rewrite_result
                else False,
            )

        return response_data

    async def send_message_stream(
        self,
        session_id: str,
        kb_id: str,
        user_id: str,
        message: str,
        conversation_id: str | None = None,
        trace_ctx: TraceContext | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream chat message with real-time LLM tokens and citations.

        Yields SSE events as they occur:
        - status: Search/generation status updates
        - token: Individual LLM response tokens
        - citation: Citation data when markers detected
        - done: Completion with final metadata

        Args:
            session_id: User session ID
            kb_id: Knowledge Base ID
            user_id: User ID for permission checks
            message: User message
            conversation_id: Existing conversation ID (optional)
            trace_ctx: Optional trace context for observability instrumentation

        Yields:
            Dict events for SSE streaming

        Raises:
            NoDocumentsError: If KB has no indexed documents
        """
        obs = ObservabilityService.get_instance()

        # Check if debug mode is enabled for this KB (AC-9.15.10)
        debug_mode_enabled = await self._is_debug_mode_enabled(kb_id)

        # 1. Yield status: Searching
        yield {"type": "status", "content": "Searching relevant documents..."}

        # 2. Retrieve conversation history
        history = await self.get_history(session_id, kb_id)

        # 2.5. Story 8-0: Rewrite query using conversation history
        rewrite_result: RewriteResult | None = None
        search_query = message  # Default to original message

        if self._query_rewriter and history:
            rewrite_result = await self._query_rewriter.rewrite_with_history(
                query=message,
                chat_history=history,
                trace_ctx=trace_ctx,
            )
            if rewrite_result.was_rewritten:
                search_query = rewrite_result.rewritten_query
                logger.info(
                    "query_rewritten_for_stream_search",
                    original=message[:100],
                    rewritten=search_query[:100],
                    latency_ms=round(rewrite_result.latency_ms, 2),
                )

        # 3. Perform RAG retrieval (with observability span and timing)
        # Uses rewritten query if available, otherwise original message
        retrieval_start = time.time()
        if trace_ctx:
            async with obs.span(trace_ctx, "retrieval", "retrieval") as _span_id:
                search_response = await self.search_service.search(
                    query=search_query,
                    kb_ids=[kb_id],
                    user_id=user_id,
                    limit=10,
                    stream=False,
                )
        else:
            search_response = await self.search_service.search(
                query=search_query,
                kb_ids=[kb_id],
                user_id=user_id,
                limit=10,
                stream=False,
            )
        retrieval_ms = (time.time() - retrieval_start) * 1000

        if not search_response.results:
            raise NoDocumentsError(kb_id)

        # Yield retrieval metrics event for observability
        yield {
            "type": "retrieval_complete",
            "chunks_retrieved": len(search_response.results),
            "avg_relevance": sum(r.relevance_score for r in search_response.results)
            / len(search_response.results),
        }

        # 4. Resolve KB prompt configuration (AC-9.15.4 through AC-9.15.9)
        prompt_config = await self._resolve_kb_prompt_config(kb_id)
        kb_name = await self._get_kb_name(kb_id)

        # Build context text for system prompt interpolation with timing
        context_assembly_start = time.time()
        context_text = "\n\n".join(
            [
                f"[{i + 1}] {chunk.chunk_text}"
                for i, chunk in enumerate(search_response.results)
            ]
        )

        # Build dynamic system prompt with KB configuration
        system_prompt = self._build_system_prompt(
            prompt_config=prompt_config,
            kb_name=kb_name,
            context_text=context_text,
            query=message,
        )

        # 5. Build prompt with history + context (with observability span)
        if trace_ctx:
            async with obs.span(trace_ctx, "context_assembly", "retrieval") as _span_id:
                prompt_messages = self._build_prompt(
                    history, message, search_response.results, system_prompt
                )
        else:
            prompt_messages = self._build_prompt(
                history, message, search_response.results, system_prompt
            )
        context_assembly_ms = (time.time() - context_assembly_start) * 1000

        # AC-9.15.10, AC-9.15.12: Emit debug event BEFORE first token when debug_mode=true
        if debug_mode_enabled:
            debug_info = self._build_debug_info(
                prompt_config=prompt_config,
                chunks=search_response.results,
                retrieval_ms=retrieval_ms,
                context_assembly_ms=context_assembly_ms,
                rewrite_result=rewrite_result,  # Story 8-0: Include query rewrite info
            )
            yield {"type": "debug", "data": debug_info.model_dump()}
            logger.info(
                "debug_event_emitted",
                kb_id=kb_id,
                chunks_count=len(search_response.results),
                retrieval_ms=retrieval_ms,
                context_assembly_ms=context_assembly_ms,
                query_rewritten=rewrite_result.was_rewritten
                if rewrite_result
                else False,
            )

        # 5. Yield status: Generating
        yield {"type": "status", "content": "Generating answer..."}

        # 6. Get KB-specific generation model and config (Story 7-10, 7-17)
        kb_model = await self._get_kb_generation_model(kb_id)
        gen_config = await self._resolve_generation_config(kb_id)

        # 7. Stream from LLM - accumulate tokens and detect citations
        response_text = ""
        detected_citations = []
        citation_numbers_seen: set[int] = set()

        # Get streaming response from LLM (synthesis span wraps entire streaming)
        # Use KB-level generation settings (temperature, max_tokens, top_p)
        if trace_ctx:
            async with obs.span(trace_ctx, "synthesis", "llm") as _span_id:
                stream_response = await self.llm_client.chat_completion(
                    messages=prompt_messages,
                    temperature=gen_config.temperature,
                    max_tokens=gen_config.max_tokens,
                    top_p=gen_config.top_p,
                    stream=True,
                    model=kb_model,  # Use KB-specific model if configured
                )

                # Process chunks from LLM stream
                async for chunk in stream_response:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta
                    if not delta.content:
                        continue

                    token = delta.content
                    response_text += token

                    # Yield token event
                    yield {"type": "token", "content": token}

                    # Check for new citation markers [n] in accumulated text
                    matches = re.finditer(r"\[(\d+)\]", response_text)
                    for match in matches:
                        citation_num = int(match.group(1))
                        if (
                            citation_num not in citation_numbers_seen
                            and citation_num <= len(search_response.results)
                        ):
                            # Extract citation for this marker
                            chunk_result = search_response.results[citation_num - 1]
                            citation_data = {
                                "number": citation_num,
                                "document_id": chunk_result.document_id,
                                "document_name": chunk_result.document_name,
                                "page_number": chunk_result.page_number,
                                "section_header": chunk_result.section_header,
                                "excerpt": chunk_result.chunk_text[
                                    :200
                                ],  # First 200 chars
                                "char_start": chunk_result.char_start,
                                "char_end": chunk_result.char_end,
                                "confidence": chunk_result.relevance_score,
                            }
                            detected_citations.append(citation_data)
                            citation_numbers_seen.add(citation_num)

                            # Yield citation event immediately
                            yield {"type": "citation", "data": citation_data}
        else:
            stream_response = await self.llm_client.chat_completion(
                messages=prompt_messages,
                temperature=gen_config.temperature,
                max_tokens=gen_config.max_tokens,
                top_p=gen_config.top_p,
                stream=True,
                model=kb_model,  # Use KB-specific model if configured
            )

            # Process chunks from LLM stream
            async for chunk in stream_response:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                if not delta.content:
                    continue

                token = delta.content
                response_text += token

                # Yield token event
                yield {"type": "token", "content": token}

                # Check for new citation markers [n] in accumulated text
                matches = re.finditer(r"\[(\d+)\]", response_text)
                for match in matches:
                    citation_num = int(match.group(1))
                    if (
                        citation_num not in citation_numbers_seen
                        and citation_num <= len(search_response.results)
                    ):
                        # Extract citation for this marker
                        chunk_result = search_response.results[citation_num - 1]
                        citation_data = {
                            "number": citation_num,
                            "document_id": chunk_result.document_id,
                            "document_name": chunk_result.document_name,
                            "page_number": chunk_result.page_number,
                            "section_header": chunk_result.section_header,
                            "excerpt": chunk_result.chunk_text[:200],  # First 200 chars
                            "char_start": chunk_result.char_start,
                            "char_end": chunk_result.char_end,
                            "confidence": chunk_result.relevance_score,
                        }
                        detected_citations.append(citation_data)
                        citation_numbers_seen.add(citation_num)

                        # Yield citation event immediately
                        yield {"type": "citation", "data": citation_data}

        # 7. Citation mapping span (after streaming completes)
        if trace_ctx and detected_citations:
            # Log citation mapping metrics (already extracted during streaming)
            pass  # Citations were extracted during streaming

        # 8. Calculate confidence (average of chunk scores)
        confidence = (
            sum(result.relevance_score for result in search_response.results)
            / len(search_response.results)
            if search_response.results
            else 0.0
        )

        # 9. Store in Redis
        conversation_id = conversation_id or self._generate_conversation_id()
        await self._append_to_history(
            session_id=session_id,
            kb_id=kb_id,
            user_message=message,
            assistant_response=response_text,
            citations=[Citation(**cit) for cit in detected_citations],
            confidence=confidence,
        )

        # 10. Yield done event with metadata
        yield {
            "type": "done",
            "confidence": confidence,
            "conversation_id": conversation_id,
            "chunks_retrieved": len(search_response.results),
            "citations_count": len(detected_citations),
            "response_length": len(response_text),
        }

    async def get_history(self, session_id: str, kb_id: str) -> list[dict[str, Any]]:
        """Retrieve conversation history from Redis.

        Args:
            session_id: User session ID
            kb_id: Knowledge Base ID

        Returns:
            List of message dicts (role, content, timestamp)
        """
        redis_client = await RedisClient.get_client()
        key = f"conversation:{session_id}:{kb_id}"

        history_json = await redis_client.get(key)
        if not history_json:
            return []

        return json.loads(history_json)

    async def _append_to_history(
        self,
        session_id: str,
        kb_id: str,
        user_message: str,
        assistant_response: str,
        citations: list[Citation],
        confidence: float,
    ) -> None:
        """Append messages to conversation history in Redis.

        Args:
            session_id: User session ID
            kb_id: Knowledge Base ID
            user_message: User message
            assistant_response: Assistant response
            citations: Citations list
            confidence: Confidence score
        """
        from datetime import UTC, datetime

        history = await self.get_history(session_id, kb_id)

        # Append user message
        history.append(
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now(UTC).isoformat() + "Z",
            }
        )

        # Append assistant response
        history.append(
            {
                "role": "assistant",
                "content": assistant_response,
                "citations": [citation.model_dump() for citation in citations],
                "confidence": confidence,
                "timestamp": datetime.now(UTC).isoformat() + "Z",
            }
        )

        # Store in Redis with TTL
        redis_client = await RedisClient.get_client()
        key = f"conversation:{session_id}:{kb_id}"
        await redis_client.setex(key, CONVERSATION_TTL, json.dumps(history))

        logger.info(
            "conversation_history_updated",
            session_id=session_id,
            kb_id=kb_id,
            message_count=len(history),
        )

    def _build_prompt(
        self,
        history: list[dict[str, Any]],
        message: str,
        chunks: list[SearchResultSchema],
        system_prompt: str | None = None,
    ) -> list[dict[str, str]]:
        """Build prompt with context window management.

        AC-9.15.4: Uses dynamic system prompt from KB configuration when provided,
        falls back to CHAT_SYSTEM_PROMPT for backward compatibility.

        Args:
            history: Conversation history
            message: Current user message
            chunks: Retrieved context chunks
            system_prompt: Dynamic system prompt from KB config (optional, defaults to legacy)

        Returns:
            List of message dicts for LLM API
        """
        # Count tokens for chunks
        context_text = "\n\n".join(
            [f"[{i + 1}] {chunk.chunk_text}" for i, chunk in enumerate(chunks)]
        )
        context_tokens = self._count_tokens(context_text)

        # Count tokens for history and truncate if needed
        history_tokens = 0
        included_history = []

        # Include recent history (last N messages, up to token limit)
        for msg in reversed(history[-MAX_HISTORY_MESSAGES:]):
            msg_tokens = self._count_tokens(msg["content"])

            if history_tokens + msg_tokens + context_tokens > MAX_CONTEXT_TOKENS:
                break  # Stop adding history

            included_history.insert(0, {"role": msg["role"], "content": msg["content"]})
            history_tokens += msg_tokens

        # Build final prompt - use dynamic system prompt or legacy fallback
        effective_prompt = system_prompt if system_prompt else CHAT_SYSTEM_PROMPT
        messages = [{"role": "system", "content": effective_prompt}]

        # Add conversation history
        messages.extend(included_history)

        # Add context chunks
        messages.append(
            {
                "role": "system",
                "content": f"Retrieved sources:\n{context_text}",
            }
        )

        # Add current query
        messages.append({"role": "user", "content": message})

        logger.debug(
            "prompt_built",
            history_messages=len(included_history),
            context_chunks=len(chunks),
            total_messages=len(messages),
            using_kb_prompt=system_prompt is not None,
        )

        return messages

    def _count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 chars).

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID.

        Returns:
            Conversation ID in format: conv-{uuid4}
        """
        return f"conv-{uuid.uuid4()}"
