"""Search service for semantic search and answer synthesis.

Story 7-7: AsyncQdrantClient Migration (AC-7.7.3)
Story 7-17: Service Integration with KB-level configuration (AC-7.17.1, AC-7.17.5)
"""

import hashlib
import json
import re
import time
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

import redis.asyncio as redis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.logging import get_logger
from app.core.redis import RedisClient, get_redis_client
from app.integrations.litellm_client import LiteLLMEmbeddingClient, embedding_client
from app.integrations.qdrant_client import qdrant_service
from app.models.kb_access_log import AccessType
from app.schemas.citation import Citation
from app.schemas.kb_settings import RetrievalConfig
from app.schemas.search import (
    QuickSearchResponse,
    QuickSearchResult,
    SearchResponse,
    SearchResultSchema,
)
from app.schemas.sse import (
    CitationEvent,
    DoneEvent,
    ErrorEvent,
    SSEEvent,
    StatusEvent,
    TokenEvent,
)
from app.services.audit_service import AuditService, get_audit_service
from app.services.citation_service import CitationService
from app.services.kb_config_resolver import KBConfigResolver
from app.services.kb_recommendation_service import KBRecommendationService
from app.services.kb_service import KBPermissionService, get_kb_permission_service

logger = get_logger()

# Pattern for detecting [n] markers in token stream
CITATION_MARKER_PATTERN = r"\[(\d+)\]"

# LLM System Prompt for Citation Instructions (from tech-spec-epic-3.md)
CITATION_SYSTEM_PROMPT = """You are a helpful assistant answering questions based on provided source documents.

CRITICAL RULES:
1. Every factual claim MUST have a citation using [n] notation
2. Use [1] for first source, [2] for second source, etc.
3. Multiple sources for one claim: [1][2]
4. If information isn't in sources, say "I don't have information about that in the available documents."
5. Be concise but complete

Example:
"Our authentication approach uses OAuth 2.0 with PKCE [1] and supports MFA via TOTP [2]."

Sources will be provided below with their numbers."""


class SearchService:
    """Service for semantic search operations.

    Story 7-17: Integrates KBConfigResolver for KB-level retrieval configuration.

    Orchestrates the search pipeline:
    1. Permission check
    2. KB config resolution (AC-7.17.1)
    3. Query embedding generation (with Redis caching)
    4. Qdrant vector search with KB-specific top_k, similarity_threshold
    5. Metadata assembly
    6. Audit logging (async) with effective_config (AC-7.17.6)
    """

    def __init__(
        self,
        permission_service: KBPermissionService,
        audit_service: AuditService,
        kb_config_resolver: KBConfigResolver | None = None,
        citation_service: CitationService | None = None,
        kb_recommendation_service: KBRecommendationService | None = None,
    ):
        """Initialize search service.

        Args:
            permission_service: Permission service for access checks
            audit_service: Audit service for logging
            kb_config_resolver: Config resolver for KB-level settings (Story 7-17)
            citation_service: Citation service for extracting citations (default: new instance)
            kb_recommendation_service: KB recommendation service for logging access (optional)
        """
        self.permission_service = permission_service
        self.audit_service = audit_service
        self.kb_config_resolver = kb_config_resolver
        self.citation_service = citation_service or CitationService()
        self.kb_recommendation_service = kb_recommendation_service
        # Story 7-7: Use qdrant_service directly for async methods (AC-7.7.3)
        self.qdrant_service = qdrant_service

    async def _resolve_retrieval_config(
        self,
        kb_id: str,
        request_limit: int | None = None,
        request_similarity_threshold: float | None = None,
    ) -> RetrievalConfig:
        """Resolve retrieval config for a KB with request overrides.

        Story 7-17 (AC-7.17.1, AC-7.17.5): Implements three-layer precedence:
        Request params → KB settings → System defaults.

        Args:
            kb_id: Knowledge base ID
            request_limit: Request-level override for top_k
            request_similarity_threshold: Request-level override for similarity_threshold

        Returns:
            RetrievalConfig with resolved values
        """
        if self.kb_config_resolver is None:
            # Fallback to schema defaults if no resolver configured
            # Use RetrievalConfig() defaults instead of hardcoded values
            defaults = RetrievalConfig()
            return RetrievalConfig(
                top_k=request_limit if request_limit is not None else defaults.top_k,
                similarity_threshold=request_similarity_threshold
                if request_similarity_threshold is not None
                else defaults.similarity_threshold,
                method=defaults.method,
                mmr_enabled=defaults.mmr_enabled,
                mmr_lambda=defaults.mmr_lambda,
                hybrid_alpha=defaults.hybrid_alpha,
            )

        try:
            # Build request overrides dict (only include non-None values)
            overrides: dict[str, Any] = {}
            if request_limit is not None:
                overrides["top_k"] = request_limit
            if request_similarity_threshold is not None:
                overrides["similarity_threshold"] = request_similarity_threshold

            # Resolve config with KB settings and request overrides
            config = await self.kb_config_resolver.resolve_retrieval_config(
                kb_id=UUID(kb_id) if isinstance(kb_id, str) else kb_id,
                request_overrides=overrides if overrides else None,
            )
            return config
        except Exception as e:
            # Log warning and fallback to schema defaults on resolver error
            # Use RetrievalConfig() defaults instead of hardcoded values
            logger.warning(
                "kb_config_resolution_failed",
                kb_id=kb_id,
                error=str(e),
            )
            defaults = RetrievalConfig()
            return RetrievalConfig(
                top_k=request_limit if request_limit is not None else defaults.top_k,
                similarity_threshold=request_similarity_threshold
                if request_similarity_threshold is not None
                else defaults.similarity_threshold,
                method=defaults.method,
                mmr_enabled=defaults.mmr_enabled,
                mmr_lambda=defaults.mmr_lambda,
                hybrid_alpha=defaults.hybrid_alpha,
            )

    async def search(
        self,
        query: str,
        kb_ids: list[str] | None,
        user_id: str,
        limit: int = 10,
        stream: bool = False,
    ) -> SearchResponse | AsyncGenerator[SSEEvent, None]:
        """Execute semantic search.

        Args:
            query: Natural language search query
            kb_ids: List of KB IDs to search, or None for all permitted KBs
            user_id: User ID for permission checks
            limit: Maximum number of results
            stream: If True, return SSE stream generator

        Returns:
            SearchResponse with results, or AsyncGenerator[SSEEvent, None]

        Raises:
            PermissionError: If user lacks READ access to any specified KB
            ConnectionError: If Qdrant or LiteLLM unavailable
        """
        # Branch to streaming or non-streaming mode (AC8)
        if stream:
            return self._search_stream(query, kb_ids, user_id, limit)
        else:
            return await self._search_sync(query, kb_ids, user_id, limit)

    async def _search_sync(
        self,
        query: str,
        kb_ids: list[str] | None,
        user_id: str,
        limit: int = 10,
        similarity_threshold: float | None = None,
    ) -> SearchResponse:
        """Execute non-streaming search (backward compatible).

        Story 7-17 (AC-7.17.1, AC-7.17.5, AC-7.17.6): Uses KB-level retrieval config
        with request override precedence.

        Args:
            query: Natural language search query
            kb_ids: List of KB IDs to search, or None for all permitted KBs
            user_id: User ID for permission checks
            limit: Maximum number of results (request override for top_k)
            similarity_threshold: Minimum similarity score (request override)

        Returns:
            SearchResponse with complete results

        Raises:
            PermissionError: If user lacks READ access to any specified KB
            ConnectionError: If Qdrant or LiteLLM unavailable
        """
        start_time = time.time()
        effective_config: dict[str, Any] | None = None

        try:
            # Get permitted KBs if not specified
            if kb_ids is None:
                kb_ids = await self.permission_service.get_permitted_kb_ids(
                    user_id, "READ"
                )

            # Check permissions for all specified KBs
            for kb_id in kb_ids:
                has_access = await self.permission_service.check_permission(
                    user_id, kb_id, "READ"
                )
                if not has_access:
                    raise PermissionError("Knowledge Base not found")

            # Story 7-17 (AC-7.17.1): Resolve retrieval config from first KB
            # When searching multiple KBs, use first KB's config as baseline
            # Request overrides always take precedence (AC-7.17.5)
            retrieval_config = await self._resolve_retrieval_config(
                kb_id=kb_ids[0] if kb_ids else "",
                request_limit=limit
                if limit != 10
                else None,  # Only override if non-default
                request_similarity_threshold=similarity_threshold,
            )

            # Store effective config for audit logging (AC-7.17.6)
            effective_config = {
                "top_k": retrieval_config.top_k,
                "similarity_threshold": retrieval_config.similarity_threshold,
                "method": retrieval_config.method.value
                if hasattr(retrieval_config.method, "value")
                else str(retrieval_config.method),
                "mmr_enabled": retrieval_config.mmr_enabled,
            }

            # Resolve KB embedding model (use first KB's model for consistency)
            # This ensures query embedding dimensions match indexed vectors
            embedding_model_config = None
            if self.kb_config_resolver and kb_ids:
                try:
                    embedding_model_config = (
                        await self.kb_config_resolver.get_kb_embedding_model(
                            UUID(kb_ids[0]) if isinstance(kb_ids[0], str) else kb_ids[0]
                        )
                    )
                except Exception as e:
                    logger.warning(
                        "kb_embedding_model_resolution_failed",
                        kb_id=kb_ids[0],
                        error=str(e),
                    )

            # Generate query embedding with KB-specific model
            if embedding_model_config:
                embedding = await self._embed_query(
                    query,
                    model_id=embedding_model_config.model_id,
                    provider=embedding_model_config.provider,
                    api_endpoint=embedding_model_config.api_endpoint,
                )
                effective_config["embedding_model"] = embedding_model_config.model_id
            else:
                embedding = await self._embed_query(query)

            # Fetch KB names for display (graceful fallback)
            try:
                kb_name_map = await self._get_kb_names(kb_ids)
            except Exception as e:
                logger.warning("kb_name_fetch_failed", error=str(e))
                kb_name_map = {}

            # Search Qdrant collections with resolved config
            chunks = await self._search_collections(
                embedding,
                kb_ids,
                limit=retrieval_config.top_k,
                kb_name_map=kb_name_map,
                similarity_threshold=retrieval_config.similarity_threshold,
            )

            # Assemble response
            results = [
                SearchResultSchema(
                    document_id=chunk["document_id"],
                    document_name=chunk["document_name"],
                    kb_id=chunk["kb_id"],
                    kb_name=chunk.get("kb_name", "Unknown"),
                    chunk_text=chunk["chunk_text"],
                    relevance_score=chunk["score"],
                    page_number=chunk.get("page_number"),
                    section_header=chunk.get("section_header"),
                    char_start=chunk["char_start"],
                    char_end=chunk["char_end"],
                )
                for chunk in chunks
            ]

            # Story 3.2: Answer Synthesis with Citations
            answer = ""
            citations: list[Citation] = []
            confidence = 0.0

            if results:
                try:
                    # Synthesize answer using top-5 chunks (AC1)
                    answer = await self._synthesize_answer(query, results[:5])

                    # Extract citations (AC2, AC3)
                    answer, citations = self.citation_service.extract_citations(
                        answer, results[:5]
                    )

                    # Calculate confidence (AC4)
                    confidence = self._calculate_confidence(results[:5], query)

                except Exception as e:
                    # Graceful degradation (AC7, AC8)
                    logger.warning(
                        "answer_synthesis_failed_fallback_to_raw_results",
                        error=str(e),
                        query_length=len(query),
                        chunk_count=len(results),
                    )
                    # Return raw results without synthesis
                    answer = ""
                    citations = []
                    confidence = 0.0

            response = SearchResponse(
                query=query,
                answer=answer,
                citations=citations,
                confidence=confidence,
                results=results,
                result_count=len(results),
                message=(
                    None
                    if results
                    else "No relevant documents found for your query. Try rephrasing or searching across all Knowledge Bases."
                ),
            )

            # Log search query (async, non-blocking) - Story 5.14, 7.17
            latency_ms = int((time.time() - start_time) * 1000)
            await self.audit_service.log_search(
                user_id=user_id,
                query=query,
                kb_ids=kb_ids,
                result_count=len(results),
                latency_ms=latency_ms,
                search_type="semantic",
                status="success",
                effective_config=effective_config,  # Story 7-17 (AC-7.17.6)
            )

            # Log KB access for recommendations (fire-and-forget, Story 5.8)
            if self.kb_recommendation_service and kb_ids:
                from uuid import UUID as UUIDType

                for kb_id in kb_ids:
                    try:
                        kb_uuid = UUIDType(kb_id) if isinstance(kb_id, str) else kb_id
                        await self.kb_recommendation_service.log_kb_access(
                            user_id=UUIDType(user_id)
                            if isinstance(user_id, str)
                            else user_id,
                            kb_id=kb_uuid,
                            access_type=AccessType.SEARCH,
                        )
                    except Exception as e:
                        # Fire-and-forget - don't fail search on logging error
                        logger.warning(
                            "kb_access_log_failed",
                            kb_id=str(kb_id),
                            error=str(e),
                        )

            logger.info(
                "search_completed",
                query_length=len(query),
                kb_count=len(kb_ids),
                result_count=len(results),
                latency_ms=latency_ms,
            )

            return response

        except ConnectionError:
            raise
        except PermissionError:
            raise
        except Exception as e:
            logger.error("search_failed", error=str(e), query=query[:100])
            raise

    async def _embed_query(
        self,
        query: str,
        model_id: str | None = None,
        provider: str | None = None,
        api_endpoint: str | None = None,
    ) -> list[float]:
        """Generate query embedding with Redis caching.

        Uses KB-specific embedding model if provided, otherwise falls back
        to the system default. This ensures vector dimensions match between
        document indexing and query embedding.

        Args:
            query: Query text
            model_id: LiteLLM model identifier (e.g., 'mxbai-embed-large:latest')
            provider: Model provider (e.g., 'ollama') for direct API routing
            api_endpoint: Custom API endpoint if not using LiteLLM proxy

        Returns:
            Embedding vector

        Raises:
            ConnectionError: If LiteLLM unavailable after retries
        """
        # Check Redis cache - include model_id in cache key to avoid cross-model collisions
        redis = await RedisClient.get_client()
        cache_suffix = f":{model_id}" if model_id else ""
        cache_key = (
            f"embedding:{hashlib.sha256(query.encode()).hexdigest()}{cache_suffix}"
        )

        cached = await redis.get(cache_key)
        if cached:
            logger.debug(
                "embedding_cache_hit",
                query_length=len(query),
                model_id=model_id or "default",
            )
            return json.loads(cached)

        # Generate embedding via LiteLLM with retry logic
        try:
            if model_id:
                # Use KB-specific embedding model
                client = LiteLLMEmbeddingClient(
                    model=model_id,
                    provider=provider,
                    api_base=api_endpoint,
                )
                logger.debug(
                    "using_kb_embedding_model",
                    model_id=model_id,
                    provider=provider,
                )
                embeddings = await client.get_embeddings([query])
            else:
                # Use default embedding client
                embeddings = await embedding_client.get_embeddings([query])

            embedding = embeddings[0]

            # Cache for 1 hour
            await redis.setex(cache_key, 3600, json.dumps(embedding))

            logger.debug(
                "embedding_generated",
                query_length=len(query),
                model_id=model_id or "default",
                dimensions=len(embedding),
            )
            return embedding

        except Exception as e:
            logger.error(
                "embedding_failed",
                error=str(e),
                model_id=model_id or "default",
            )
            raise ConnectionError(f"Embedding service unavailable: {str(e)}") from e

    async def _get_kb_names(self, kb_ids: list[str]) -> dict[str, str]:
        """Fetch KB names from database (Story 3.6).

        Args:
            kb_ids: List of KB IDs

        Returns:
            Mapping of kb_id -> kb_name
        """
        from sqlalchemy import select

        from app.core.database import async_session_factory
        from app.models.knowledge_base import KnowledgeBase

        async with async_session_factory() as session:
            result = await session.execute(
                select(KnowledgeBase.id, KnowledgeBase.name).where(
                    KnowledgeBase.id.in_(kb_ids)
                )
            )
            return {str(row.id): row.name for row in result.all()}

    async def _search_collections(
        self,
        embedding: list[float],
        kb_ids: list[str],
        limit: int,
        kb_name_map: dict[str, str] | None = None,
        similarity_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search Qdrant collections in parallel (Story 3.6, Story 7-17).

        Story 7-17 (AC-7.17.1): Uses KB-level similarity_threshold for filtering.

        Args:
            embedding: Query embedding vector
            kb_ids: List of KB IDs to search
            limit: Max results per KB
            kb_name_map: Optional mapping of kb_id -> kb_name for display (default: Unknown for all)
            similarity_threshold: Minimum similarity score filter (AC-7.17.1)

        Returns:
            List of matching chunks with metadata including kb_name

        Raises:
            ConnectionError: If Qdrant unavailable
        """
        if kb_name_map is None:
            kb_name_map = {}
        try:
            import asyncio  # Needed for asyncio.gather

            # Ensure Qdrant connection is healthy (auto-reset if stale after Docker restart)
            await self.qdrant_service.ensure_connection()

            # Define async search function for single collection
            async def search_single_kb(kb_id: str) -> list[dict[str, Any]]:
                from qdrant_client.http import models as qdrant_models

                collection_name = f"kb_{kb_id}"

                # AC: Exclude archived documents from search results (Story 6-1)
                # Filter points where archived is not true (archived=false or null/missing)
                archive_filter = qdrant_models.Filter(
                    must_not=[
                        qdrant_models.FieldCondition(
                            key="archived",
                            match=qdrant_models.MatchValue(value=True),
                        )
                    ]
                )

                # Story 7-7: Use native async query_points method (AC-7.7.3)
                # Story 7-17: Apply similarity_threshold via score_threshold (AC-7.17.1)
                # NOTE: qdrant-client 1.16+ uses query_points instead of search
                query_response = await self.qdrant_service.query_points(
                    collection_name=collection_name,
                    query=embedding,
                    query_filter=archive_filter,
                    limit=limit,
                    with_payload=True,
                    score_threshold=similarity_threshold
                    if similarity_threshold > 0
                    else None,
                )

                # Extract and enrich results with KB metadata
                # query_points returns QueryResponse with .points attribute
                chunks = []
                for result in query_response.points:
                    # Clamp score to [0, 1] range - cosine similarity can be negative
                    # for dissimilar vectors, but relevance scores should be non-negative
                    score = max(0.0, min(1.0, result.score))
                    chunk = {
                        "kb_id": kb_id,
                        "kb_name": kb_name_map.get(kb_id, "Unknown"),
                        "score": score,
                        **result.payload,
                    }
                    chunks.append(chunk)
                return chunks

            # Query all collections in parallel (AC2, AC4)
            all_results = []
            tasks = [search_single_kb(kb_id) for kb_id in kb_ids]
            results_per_kb = await asyncio.gather(*tasks, return_exceptions=True)

            # Merge results, handle exceptions gracefully (AC partial failure handling)
            failed_kbs = []
            for kb_id, kb_results in zip(kb_ids, results_per_kb, strict=False):
                if isinstance(kb_results, Exception):
                    logger.warning(
                        "collection_search_failed", kb_id=kb_id, error=str(kb_results)
                    )
                    failed_kbs.append(kb_id)
                    continue
                all_results.extend(kb_results)

            # If ALL collections failed, raise ConnectionError
            if len(failed_kbs) == len(kb_ids):
                logger.error("all_collections_failed", kb_count=len(kb_ids))
                raise ConnectionError(
                    f"Vector search unavailable for all {len(kb_ids)} KBs"
                )

            # Sort by relevance score (descending) - AC3
            all_results.sort(key=lambda x: x["score"], reverse=True)

            # Return top-k across all KBs
            return all_results[:limit]

        except Exception as e:
            logger.error("qdrant_search_failed", error=str(e))
            raise ConnectionError(f"Vector search unavailable: {str(e)}") from e

    async def _synthesize_answer(
        self, query: str, chunks: list[SearchResultSchema]
    ) -> str:
        """Generate answer via LLM with citation instructions (AC1).

        Args:
            query: User's natural language query
            chunks: Top-k search chunks to use as context (typically 5)

        Returns:
            LLM-generated answer with inline [1], [2], [3] markers

        Raises:
            Exception: If LLM call fails (caught by caller for graceful degradation)
        """
        # Build context from chunks with citation numbers
        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            context_parts.append(
                f"[{i}] {chunk.chunk_text}\n"
                f"   (Source: {chunk.document_name}"
                + (f", page {chunk.page_number}" if chunk.page_number else "")
                + ")"
            )

        context = "\n\n".join(context_parts)

        # Build LLM messages
        messages = [
            {"role": "system", "content": CITATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\n\nSources:\n{context}"},
        ]

        # Call LiteLLM with lower temperature for deterministic citations
        response = await embedding_client.chat_completion(
            messages=messages,
            temperature=0.3,  # Low temperature for consistent citation format
            max_tokens=500,
        )

        answer = response.choices[0].message.content

        logger.info(
            "answer_synthesized",
            query_length=len(query),
            chunk_count=len(chunks),
            answer_length=len(answer),
        )

        return answer

    def _calculate_confidence(
        self,
        chunks: list[SearchResultSchema],
        query: str,  # noqa: ARG002 - Reserved for semantic similarity calculation
    ) -> float:
        """Calculate confidence score (0-1) for answer (AC4).

        Formula per tech spec:
        - Average retrieval relevance scores (40% weight)
        - Number of supporting sources (30% weight: 1=0.3, 2=0.6, 3+=1.0)
        - Semantic similarity between query and answer (30% weight, simplified for MVP)

        Args:
            chunks: Source chunks used for synthesis
            query: Original query

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not chunks:
            return 0.0

        # Average relevance scores (40%)
        avg_relevance = sum(c.relevance_score for c in chunks) / len(chunks)

        # Source count score (30%)
        # 1 source = 0.3, 2 sources = 0.6, 3+ sources = 1.0
        source_count_score = min(len(chunks) / 3.0, 1.0)

        # Simplified similarity score (30%)
        # For MVP, assume high similarity if we have high relevance
        # Future: compute embedding similarity between query and answer
        similarity_score = avg_relevance

        # Weighted combination
        confidence = (
            avg_relevance * 0.4 + source_count_score * 0.3 + similarity_score * 0.3
        )

        return min(confidence, 1.0)

    async def _search_stream(
        self,
        query: str,
        kb_ids: list[str] | None,
        user_id: str,
        limit: int,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Stream search results and answer synthesis via SSE (AC1, AC3, AC4, AC5, AC6).

        Yields SSE events in sequence:
        1. StatusEvent - "Searching knowledge bases..."
        2. StatusEvent - "Generating answer..."
        3. TokenEvent* - Answer tokens word-by-word
        4. CitationEvent* - Citation metadata when [n] detected
        5. DoneEvent - Confidence and result_count

        Args:
            query: Natural language query
            kb_ids: KB IDs to search or None for all permitted
            user_id: User ID for permissions
            limit: Max results

        Yields:
            SSE events (StatusEvent, TokenEvent, CitationEvent, DoneEvent, ErrorEvent)

        Raises:
            PermissionError: If user lacks READ access
        """
        start_time = time.time()
        effective_config: dict[str, Any] | None = None

        try:
            # Permission checks
            if kb_ids is None:
                kb_ids = await self.permission_service.get_permitted_kb_ids(
                    user_id, "READ"
                )

            for kb_id in kb_ids:
                has_access = await self.permission_service.check_permission(
                    user_id, kb_id, "READ"
                )
                if not has_access:
                    raise PermissionError("Knowledge Base not found")

            # Status: searching (AC2)
            yield StatusEvent(content="Searching knowledge bases...")

            # Story 7-17 (AC-7.17.1): Resolve retrieval config from first KB
            # When searching multiple KBs, use first KB's config as baseline
            # Request overrides always take precedence (AC-7.17.5)
            retrieval_config = await self._resolve_retrieval_config(
                kb_id=kb_ids[0] if kb_ids else "",
                request_limit=limit
                if limit != 10
                else None,  # Only override if non-default
            )

            # Store effective config for audit logging (AC-7.17.6)
            effective_config = {
                "top_k": retrieval_config.top_k,
                "similarity_threshold": retrieval_config.similarity_threshold,
                "method": retrieval_config.method.value
                if hasattr(retrieval_config.method, "value")
                else str(retrieval_config.method),
                "mmr_enabled": retrieval_config.mmr_enabled,
            }

            # Resolve KB embedding model (use first KB's model for consistency)
            embedding_model_config = None
            if self.kb_config_resolver and kb_ids:
                try:
                    embedding_model_config = (
                        await self.kb_config_resolver.get_kb_embedding_model(
                            UUID(kb_ids[0]) if isinstance(kb_ids[0], str) else kb_ids[0]
                        )
                    )
                except Exception as e:
                    logger.warning(
                        "kb_embedding_model_resolution_failed",
                        kb_id=kb_ids[0],
                        error=str(e),
                    )

            # Generate embedding with KB-specific model
            if embedding_model_config:
                embedding = await self._embed_query(
                    query,
                    model_id=embedding_model_config.model_id,
                    provider=embedding_model_config.provider,
                    api_endpoint=embedding_model_config.api_endpoint,
                )
                effective_config["embedding_model"] = embedding_model_config.model_id
            else:
                embedding = await self._embed_query(query)

            # Fetch KB names (graceful fallback)
            try:
                kb_name_map = await self._get_kb_names(kb_ids)
            except Exception as e:
                logger.warning("kb_name_fetch_failed", error=str(e))
                kb_name_map = {}

            # Search collections with resolved KB config (Story 7-17)
            chunks = await self._search_collections(
                embedding,
                kb_ids,
                limit=retrieval_config.top_k,
                kb_name_map=kb_name_map,
                similarity_threshold=retrieval_config.similarity_threshold,
            )

            # Assemble results
            results = [
                SearchResultSchema(
                    document_id=chunk["document_id"],
                    document_name=chunk["document_name"],
                    kb_id=chunk["kb_id"],
                    kb_name=chunk.get("kb_name", "Unknown"),
                    chunk_text=chunk["chunk_text"],
                    relevance_score=chunk["score"],
                    page_number=chunk.get("page_number"),
                    section_header=chunk.get("section_header"),
                    char_start=chunk["char_start"],
                    char_end=chunk["char_end"],
                )
                for chunk in chunks
            ]

            if not results:
                # No results - emit done event immediately
                yield DoneEvent(confidence=0.0, result_count=0)
                return

            # Status: generating (AC2)
            yield StatusEvent(content="Generating answer...")

            # Stream answer synthesis with citations (AC3, AC4)
            answer_buffer = []
            citation_buffer: set[int] = set()  # Track emitted citations

            async for token in self._synthesize_answer_stream(query, results[:5]):
                answer_buffer.append(token)

                # Emit token event (AC3)
                yield TokenEvent(content=token)

                # Check for citation markers in accumulated text
                full_text = "".join(answer_buffer)
                markers = re.findall(CITATION_MARKER_PATTERN, full_text)
                detected_markers = sorted({int(n) for n in markers})

                # Emit citation events for new markers (AC4)
                for marker_num in detected_markers:
                    if marker_num not in citation_buffer and marker_num <= len(
                        results[:5]
                    ):
                        # Build citation from source chunk
                        citation = self.citation_service._map_marker_to_chunk(
                            marker_num, results[:5]
                        )

                        # Emit citation event immediately (AC4)
                        yield CitationEvent(data=citation.model_dump())

                        # Mark as emitted
                        citation_buffer.add(marker_num)

            # Calculate confidence after full answer (AC5)
            confidence = self._calculate_confidence(results[:5], query)

            # Emit done event (AC5)
            yield DoneEvent(confidence=confidence, result_count=len(results))

            # Background audit logging (async, non-blocking) - Story 5.14, 7.17
            latency_ms = int((time.time() - start_time) * 1000)
            await self.audit_service.log_search(
                user_id=user_id,
                query=query,
                kb_ids=kb_ids,
                result_count=len(results),
                latency_ms=latency_ms,
                search_type="semantic",
                status="success",
                effective_config=effective_config,  # Story 7-17 (AC-7.17.6)
            )

            # Log KB access for recommendations (fire-and-forget, Story 5.8)
            if self.kb_recommendation_service and kb_ids:
                from uuid import UUID as UUIDType

                for kb_id in kb_ids:
                    try:
                        kb_uuid = UUIDType(kb_id) if isinstance(kb_id, str) else kb_id
                        await self.kb_recommendation_service.log_kb_access(
                            user_id=UUIDType(user_id)
                            if isinstance(user_id, str)
                            else user_id,
                            kb_id=kb_uuid,
                            access_type=AccessType.SEARCH,
                        )
                    except Exception as e:
                        # Fire-and-forget - don't fail search on logging error
                        logger.warning(
                            "kb_access_log_failed",
                            kb_id=str(kb_id),
                            error=str(e),
                        )

            logger.info(
                "search_stream_completed",
                query_length=len(query),
                kb_count=len(kb_ids),
                result_count=len(results),
                latency_ms=latency_ms,
            )

        except PermissionError:
            # Re-raise permission errors
            raise
        except Exception as e:
            # Emit error event for all other failures (AC6)
            logger.error("search_stream_failed", error=str(e), query=query[:100])
            yield ErrorEvent(
                message="Search service temporarily unavailable",
                code="SERVICE_ERROR",
            )

    async def _synthesize_answer_stream(
        self, query: str, chunks: list[SearchResultSchema]
    ) -> AsyncGenerator[str, None]:
        """Stream LLM answer synthesis token-by-token (AC3).

        Calls LiteLLM with stream=True to get incremental response.
        Yields tokens as they arrive from the LLM.

        Args:
            query: User's natural language query
            chunks: Top-k search chunks to use as context (typically 5)

        Yields:
            Answer tokens (words/phrases) as they're generated

        Raises:
            Exception: If LLM call fails (caught by caller)
        """
        # Build context from chunks with citation numbers
        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            context_parts.append(
                f"[{i}] {chunk.chunk_text}\n"
                f"   (Source: {chunk.document_name}"
                + (f", page {chunk.page_number}" if chunk.page_number else "")
                + ")"
            )

        context = "\n\n".join(context_parts)

        # Build LLM messages
        messages = [
            {"role": "system", "content": CITATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Query: {query}\n\nSources:\n{context}"},
        ]

        # Call LiteLLM with streaming enabled (AC3)
        stream = await embedding_client.chat_completion(
            messages=messages,
            temperature=0.3,  # Low temperature for consistent citation format
            max_tokens=500,
            stream=True,  # Enable streaming
        )

        # Yield tokens as they arrive
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                yield token

        logger.info(
            "answer_stream_complete", query_length=len(query), chunk_count=len(chunks)
        )

    async def quick_search(
        self,
        query: str,
        kb_ids: list[str] | None,
        user_id: str,
    ) -> QuickSearchResponse:
        """Quick search for command palette (Story 3.7).

        Lightweight search returning top 5 results WITHOUT LLM synthesis.
        Optimized for speed by skipping answer generation and citation extraction.

        Args:
            query: Natural language search query
            kb_ids: List of KB IDs to search, or None for all permitted KBs
            user_id: User ID for permission checks

        Returns:
            QuickSearchResponse with top 5 results

        Raises:
            PermissionError: If user lacks READ access
        """
        start_time = time.time()

        logger.info(
            "quick_search_started",
            query_length=len(query),
            kb_ids=kb_ids,
            user_id=user_id,
        )

        try:
            # 1. Permission check and KB resolution
            if kb_ids is None:
                target_kb_ids = await self.permission_service.get_permitted_kb_ids(
                    user_id, "READ"
                )
            else:
                # Check permissions for all specified KBs
                for kb_id in kb_ids:
                    has_access = await self.permission_service.check_permission(
                        user_id, kb_id, "READ"
                    )
                    if not has_access:
                        raise PermissionError("Knowledge Base not found")
                target_kb_ids = kb_ids

            if not target_kb_ids:
                raise PermissionError("No permitted Knowledge Bases found")

            # Story 7-17: Resolve retrieval config from first KB for quick search
            retrieval_config = await self._resolve_retrieval_config(
                kb_id=target_kb_ids[0],
                request_limit=5,  # Quick search always returns 5 results
            )

            # Resolve KB embedding model (use first KB's model for consistency)
            embedding_model_config = None
            if self.kb_config_resolver and target_kb_ids:
                try:
                    embedding_model_config = (
                        await self.kb_config_resolver.get_kb_embedding_model(
                            UUID(target_kb_ids[0])
                            if isinstance(target_kb_ids[0], str)
                            else target_kb_ids[0]
                        )
                    )
                except Exception as e:
                    logger.warning(
                        "kb_embedding_model_resolution_failed",
                        kb_id=target_kb_ids[0],
                        error=str(e),
                    )

            # 2. Generate embedding (with caching) using KB-specific model
            if embedding_model_config:
                embedding = await self._embed_query(
                    query,
                    model_id=embedding_model_config.model_id,
                    provider=embedding_model_config.provider,
                    api_endpoint=embedding_model_config.api_endpoint,
                )
            else:
                embedding = await self._embed_query(query)

            # Fetch KB names for display (graceful fallback)
            try:
                kb_name_map = await self._get_kb_names(target_kb_ids)
            except Exception as e:
                logger.warning("kb_name_fetch_failed", error=str(e))
                kb_name_map = {}

            # 3. Search collections with KB-level similarity_threshold (Story 7-17)
            chunks = await self._search_collections(
                embedding,
                target_kb_ids,
                limit=5,  # Quick search always returns 5 results
                kb_name_map=kb_name_map,
                similarity_threshold=retrieval_config.similarity_threshold,
            )

            # 4. Build lightweight results
            results = [
                QuickSearchResult(
                    document_id=chunk["document_id"],
                    document_name=chunk["document_name"],
                    kb_id=chunk["kb_id"],
                    kb_name=chunk.get("kb_name", "Unknown"),
                    excerpt=chunk["chunk_text"][:100] + "..."
                    if len(chunk["chunk_text"]) > 100
                    else chunk["chunk_text"],
                    relevance_score=chunk["score"],
                )
                for chunk in chunks
            ]

            response_time_ms = int((time.time() - start_time) * 1000)

            # Log quick search (async, non-blocking) - Story 5.14
            await self.audit_service.log_search(
                user_id=user_id,
                query=query,
                kb_ids=target_kb_ids,
                result_count=len(results),
                latency_ms=response_time_ms,
                search_type="quick",
                status="success",
            )

            logger.info(
                "quick_search_complete",
                result_count=len(results),
                kb_count=len(target_kb_ids),
                response_time_ms=response_time_ms,
            )

            return QuickSearchResponse(
                query=query,
                results=results,
                kb_count=len(target_kb_ids),
                response_time_ms=response_time_ms,
            )

        except PermissionError:
            # Log failed search (AC4) - Story 5.14
            latency_ms = int((time.time() - start_time) * 1000)
            await self.audit_service.log_search(
                user_id=user_id,
                query=query,
                kb_ids=kb_ids or [],
                result_count=0,
                latency_ms=latency_ms,
                search_type="quick",
                status="failed",
                error_message="Knowledge Base not found or access denied",
                error_type="access_denied",
            )
            raise
        except ConnectionError as e:
            # Log failed search (AC4) - Story 5.14
            latency_ms = int((time.time() - start_time) * 1000)
            await self.audit_service.log_search(
                user_id=user_id,
                query=query,
                kb_ids=kb_ids or [],
                result_count=0,
                latency_ms=latency_ms,
                search_type="quick",
                status="failed",
                error_message=str(e),
                error_type="internal_error",
            )
            raise
        except Exception as e:
            # Log failed search (AC4) - Story 5.14
            latency_ms = int((time.time() - start_time) * 1000)
            await self.audit_service.log_search(
                user_id=user_id,
                query=query,
                kb_ids=kb_ids or [],
                result_count=0,
                latency_ms=latency_ms,
                search_type="quick",
                status="failed",
                error_message=str(e),
                error_type="internal_error",
            )
            logger.error(
                "quick_search_failed",
                query=query,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def similar_search(
        self,
        chunk_id: str,
        kb_ids: list[str] | None,
        user_id: str,
        limit: int = 10,
    ) -> SearchResponse:
        """Find content similar to a given chunk (Story 3.8).

        Uses the chunk's pre-computed embedding for similarity search.
        Excludes the original chunk from results.

        Args:
            chunk_id: Qdrant point ID of source chunk
            kb_ids: List of KB IDs to search, or None for all permitted KBs
            user_id: User ID for permission checks
            limit: Maximum number of results

        Returns:
            SearchResponse with similar chunks

        Raises:
            PermissionError: If user lacks READ access to chunk's KB
            ValueError: If chunk not found (404)
        """
        start_time = time.time()

        logger.info(
            "similar_search_started",
            chunk_id=chunk_id,
            kb_ids=kb_ids,
            user_id=user_id,
            limit=limit,
        )

        try:
            # 1. Retrieve original chunk from Qdrant to get its embedding
            # Extract KB ID from chunk_id (format: kb_{kb_id})
            # We need to search across all collections to find the chunk
            if kb_ids is None:
                target_kb_ids = await self.permission_service.get_permitted_kb_ids(
                    user_id, "READ"
                )
            else:
                # Check permissions for all specified KBs
                for kb_id in kb_ids:
                    has_access = await self.permission_service.check_permission(
                        user_id, kb_id, "READ"
                    )
                    if not has_access:
                        raise PermissionError("Knowledge Base not found")
                target_kb_ids = kb_ids

            if not target_kb_ids:
                raise PermissionError("No permitted Knowledge Bases found")

            # Try to retrieve chunk from each permitted KB collection
            # Story 7-7: Use native async retrieve method (AC-7.7.3)
            original_chunk = None
            for kb_id in target_kb_ids:
                collection_name = f"kb_{kb_id}"
                try:
                    points = await self.qdrant_service.retrieve(
                        collection_name=collection_name,
                        ids=[chunk_id],
                        with_vectors=True,
                        with_payload=True,
                    )
                    if points:
                        original_chunk = points[0]
                        break
                except Exception:
                    # Collection might not exist or chunk not in this KB
                    continue

            if not original_chunk:
                # Chunk not found in any permitted KB (AC6)
                raise ValueError("Source content no longer available")

            # 2. Extract embedding vector from chunk
            embedding = original_chunk.vector

            # 3. Get document name for query text
            document_name = original_chunk.payload.get(
                "document_name", "Unknown Document"
            )

            # Story 7-17: Resolve retrieval config from first KB for similar search
            retrieval_config = await self._resolve_retrieval_config(
                kb_id=target_kb_ids[0],
                request_limit=limit + 1,  # +1 to account for filtering original
            )

            # Fetch KB names for display
            try:
                kb_name_map = await self._get_kb_names(target_kb_ids)
            except Exception as e:
                logger.warning("kb_name_fetch_failed", error=str(e))
                kb_name_map = {}

            # 4. Search using chunk's embedding with KB-level similarity_threshold (Story 7-17)
            chunks = await self._search_collections(
                embedding,
                target_kb_ids,
                limit=limit + 1,  # +1 to account for filtering original
                kb_name_map=kb_name_map,
                similarity_threshold=retrieval_config.similarity_threshold,
            )

            # 5. Exclude original chunk from results (AC5)
            filtered_chunks = [
                chunk for chunk in chunks if chunk.get("chunk_id") != chunk_id
            ][:limit]

            # 6. Assemble response
            results = [
                SearchResultSchema(
                    document_id=chunk["document_id"],
                    document_name=chunk["document_name"],
                    kb_id=chunk["kb_id"],
                    kb_name=chunk.get("kb_name", "Unknown"),
                    chunk_text=chunk["chunk_text"],
                    relevance_score=chunk["score"],
                    page_number=chunk.get("page_number"),
                    section_header=chunk.get("section_header"),
                    char_start=chunk["char_start"],
                    char_end=chunk["char_end"],
                )
                for chunk in filtered_chunks
            ]

            # 7. Generate answer synthesis for similar content (optional)
            answer = ""
            citations: list[Citation] = []
            confidence = 0.0

            if results:
                try:
                    # Synthesize answer using top-5 similar chunks
                    query = f"Similar to: {document_name}"
                    answer = await self._synthesize_answer(query, results[:5])

                    # Extract citations
                    answer, citations = self.citation_service.extract_citations(
                        answer, results[:5]
                    )

                    # Calculate confidence
                    confidence = self._calculate_confidence(results[:5], query)

                except Exception as e:
                    # Graceful degradation - return results without synthesis
                    logger.warning(
                        "similar_search_synthesis_failed",
                        error=str(e),
                        chunk_id=chunk_id,
                    )
                    answer = ""
                    citations = []
                    confidence = 0.0

            response = SearchResponse(
                query=f"Similar to: {document_name}",
                answer=answer,
                citations=citations,
                confidence=confidence,
                results=results,
                result_count=len(results),
                message=(
                    None
                    if results
                    else "No similar content found. Try broadening your search."
                ),
            )

            # Log similar search (async, non-blocking) - Story 5.14
            latency_ms = int((time.time() - start_time) * 1000)
            await self.audit_service.log_search(
                user_id=user_id,
                query=f"Similar to: {document_name}",
                kb_ids=target_kb_ids,
                result_count=len(results),
                latency_ms=latency_ms,
                search_type="similar",
                status="success",
            )

            logger.info(
                "similar_search_completed",
                chunk_id=chunk_id,
                kb_count=len(target_kb_ids),
                result_count=len(results),
                latency_ms=latency_ms,
            )

            return response

        except ValueError:
            # Chunk not found - return 404-friendly error (AC6)
            logger.warning("similar_search_chunk_not_found", chunk_id=chunk_id)
            raise
        except PermissionError:
            # Permission denied - re-raise
            raise
        except Exception as e:
            logger.error(
                "similar_search_failed",
                chunk_id=chunk_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise


async def get_search_service(
    audit_service: AuditService = Depends(get_audit_service),
    session: AsyncSession = Depends(get_async_session),
    redis_client: redis.Redis = Depends(get_redis_client),
) -> SearchService:
    """Dependency injection for SearchService.

    Story 7-17: Now includes KBConfigResolver for KB-level configuration.

    Args:
        audit_service: Audit service dependency
        session: Database session dependency
        redis_client: Redis client for config caching

    Returns:
        SearchService instance with KB config resolver (Story 7-17)
    """
    permission_service = get_kb_permission_service(session)
    kb_recommendation_service = KBRecommendationService(session)
    kb_config_resolver = KBConfigResolver(session, redis_client)
    return SearchService(
        permission_service,
        audit_service,
        kb_config_resolver=kb_config_resolver,
        kb_recommendation_service=kb_recommendation_service,
    )
