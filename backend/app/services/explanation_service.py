"""Explanation service for generating relevance explanations for search results."""

import asyncio
import hashlib
import re
from uuid import UUID

import nltk
import structlog
from nltk.stem.porter import PorterStemmer

from app.core.config import settings
from app.core.redis import RedisClient
from app.integrations.litellm_client import acompletion
from app.integrations.qdrant_client import QdrantService
from app.schemas.search import ExplanationResponse, RelatedDocument

logger = structlog.get_logger(__name__)

# Ensure NLTK data is available (download if missing)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer data")
    nltk.download("punkt", quiet=True)

# Cache TTL for explanations (1 hour)
EXPLANATION_TTL = 3600

# LLM parameters for explanation generation
EXPLANATION_MAX_TOKENS = 50
EXPLANATION_TEMPERATURE = 0.3
EXPLANATION_TIMEOUT = 5.0


class ExplanationService:
    """Service for generating relevance explanations for search results.

    Provides transparent reasoning about why search results are relevant:
    - Keyword extraction via stemming
    - Semantic explanation generation via LLM
    - Related document discovery
    - Section context extraction

    All explanations are cached in Redis with 1 hour TTL.
    """

    def __init__(
        self,
        qdrant_service: QdrantService,
        redis_client: RedisClient | None = None,
    ):
        """Initialize explanation service.

        Args:
            qdrant_service: Qdrant service for vector search
            redis_client: Redis client for caching (optional, will create if None)
        """
        self.qdrant = qdrant_service
        self.redis = redis_client
        self.stemmer = PorterStemmer()

    async def explain(  # noqa: ARG002
        self,
        query: str,
        chunk_id: UUID,
        chunk_text: str,
        relevance_score: float,  # noqa: ARG002 - included for future use
        kb_id: UUID,
    ) -> ExplanationResponse:
        """Generate relevance explanation for a search result.

        Steps:
        1. Check cache for existing explanation
        2. Extract keywords (query tokens in chunk text)
        3. Generate semantic explanation via LLM
        4. Find related documents (similar chunks in same KB)
        5. Cache result and return

        Args:
            query: User's search query
            chunk_id: Chunk UUID
            chunk_text: Text content of the chunk
            relevance_score: Similarity score (0.0-1.0)
            kb_id: Knowledge base UUID

        Returns:
            ExplanationResponse with keywords, explanation, concepts, related docs
        """
        # 1. Check cache
        cache_key = self._cache_key(query, str(chunk_id))
        if self.redis:
            try:
                redis_client = await self.redis.get_client()
                cached = await redis_client.get(cache_key)
                if cached:
                    logger.info("Explanation cache hit", cache_key=cache_key)
                    import json

                    return ExplanationResponse(**json.loads(cached))
            except Exception as e:
                logger.warning("Cache lookup failed", error=str(e))

        # 2. Extract keywords
        keywords = self._extract_keywords(query, chunk_text)

        # 3 & 4. Generate explanation and find related documents in parallel
        explanation_task = self._generate_explanation(query, chunk_text, keywords)
        related_task = self._find_related_documents(str(chunk_id), str(kb_id), limit=3)

        try:
            explanation, related_docs = await asyncio.gather(
                explanation_task, related_task, return_exceptions=False
            )
        except Exception as e:
            logger.error("Parallel tasks failed", error=str(e))
            # Fallback: keyword-only explanation, no related docs
            explanation = f"Matches your query terms: {', '.join(keywords)}"
            related_docs = []

        # 5. Build response
        concepts = self._extract_concepts(explanation)
        section_context = "N/A"  # Will extract from chunk metadata if available

        response = ExplanationResponse(
            keywords=keywords,
            explanation=explanation,
            concepts=concepts,
            related_documents=related_docs,
            section_context=section_context,
        )

        # Cache for 1 hour
        if self.redis:
            try:
                redis_client = await self.redis.get_client()
                import json

                await redis_client.setex(
                    cache_key, EXPLANATION_TTL, json.dumps(response.model_dump())
                )
                logger.info("Explanation cached", cache_key=cache_key)
            except Exception as e:
                logger.warning("Cache write failed", error=str(e))

        return response

    def _cache_key(self, query: str, chunk_id: str) -> str:
        """Generate cache key from query and chunk ID.

        Args:
            query: User's search query
            chunk_id: Chunk UUID string

        Returns:
            Cache key string (e.g., "explain:a3f2b1c4:chunk-uuid")
        """
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        return f"explain:{query_hash}:{chunk_id}"

    def _extract_keywords(self, query: str, chunk_text: str) -> list[str]:
        """Extract keywords that appear in both query and chunk.

        Uses Porter stemming for fuzzy matching (e.g., "authenticate" matches "authentication").

        Args:
            query: User's search query
            chunk_text: Text content of the chunk

        Returns:
            List of matching keywords from the query
        """
        # Tokenize and stem query
        query_words = query.split()
        query_stems = {self.stemmer.stem(word.lower()): word for word in query_words}

        # Tokenize and stem chunk
        chunk_words = chunk_text.split()
        chunk_stems = {self.stemmer.stem(word.lower()) for word in chunk_words}

        # Find intersection (stemmed matches)
        matching_stems = set(query_stems.keys()) & chunk_stems

        # Map back to original words from query
        keywords = [query_stems[stem] for stem in matching_stems]

        logger.debug(
            "Keywords extracted",
            query=query,
            keywords=keywords,
            match_count=len(keywords),
        )

        return keywords

    async def _generate_explanation(
        self,
        query: str,
        chunk_text: str,
        keywords: list[str],
    ) -> str:
        """Generate semantic explanation via LLM.

        Max 50 tokens, 5 second timeout. Falls back to keyword-only explanation on error.

        Args:
            query: User's search query
            chunk_text: Text content of the chunk
            keywords: Matching keywords

        Returns:
            One-sentence explanation of relevance
        """
        prompt = f"""Explain in ONE sentence why this text is relevant to the query.
Focus on semantic similarity beyond just keyword matches.

Query: {query}
Matching keywords: {", ".join(keywords) if keywords else "none"}
Text: {chunk_text[:500]}...

Explanation (1 sentence):"""

        try:
            # Use acompletion from litellm_client with configured model
            # Apply litellm_proxy/ prefix for calls through LiteLLM proxy
            model_name = settings.llm_model
            if not model_name.startswith("litellm_proxy/"):
                if "/" in model_name:
                    model_name = model_name.split("/", 1)[1]
                model_name = f"litellm_proxy/{model_name}"

            response = await asyncio.wait_for(
                acompletion(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=EXPLANATION_MAX_TOKENS,
                    temperature=EXPLANATION_TEMPERATURE,
                    api_base=settings.litellm_url,
                    api_key=settings.litellm_api_key,
                ),
                timeout=EXPLANATION_TIMEOUT,
            )

            explanation = response.choices[0].message.content.strip()
            logger.debug("LLM explanation generated", explanation=explanation)
            return explanation

        except TimeoutError:
            logger.warning("LLM explanation timeout, using fallback")
            return self._fallback_explanation(keywords)
        except Exception as e:
            logger.error("LLM explanation failed", error=str(e))
            return self._fallback_explanation(keywords)

    def _fallback_explanation(self, keywords: list[str]) -> str:
        """Generate fallback keyword-based explanation.

        Args:
            keywords: Matching keywords

        Returns:
            Simple keyword-based explanation
        """
        if keywords:
            return f"Matches your query terms: {', '.join(keywords)}"
        return "This result was found through semantic similarity to your query"

    async def _find_related_documents(
        self,
        chunk_id: str,
        kb_id: str,
        limit: int = 3,
    ) -> list[RelatedDocument]:
        """Find similar chunks in the same KB.

        Reuses similar search logic from Story 3.8.

        Args:
            chunk_id: Chunk UUID string
            kb_id: Knowledge base UUID string
            limit: Max related documents to return

        Returns:
            List of related documents with relevance scores
        """
        try:
            collection_name = f"kb_{kb_id}"

            # Get chunk from Qdrant
            chunks = await self.qdrant.client.retrieve(
                collection_name=collection_name,
                ids=[chunk_id],
                with_vectors=True,
            )

            if not chunks:
                logger.warning("Chunk not found", chunk_id=chunk_id)
                return []

            # Search for similar chunks in same KB
            # NOTE: qdrant-client 1.16+ uses query_points instead of search
            query_response = self.qdrant.client.query_points(
                collection_name=collection_name,
                query=chunks[0].vector,
                limit=limit + 1,  # +1 to exclude self
            )

            # Exclude original chunk and build response
            related = []
            for result in query_response.points:
                if str(result.id) == chunk_id:
                    continue

                related.append(
                    RelatedDocument(
                        doc_id=UUID(result.payload["document_id"]),
                        doc_name=result.payload.get("document_name", "Unknown"),
                        relevance=result.score,
                    )
                )

                if len(related) >= limit:
                    break

            logger.debug(
                "Related documents found", chunk_id=chunk_id, related_count=len(related)
            )

            return related

        except Exception as e:
            logger.error("Related documents search failed", error=str(e))
            return []

    def _extract_concepts(self, explanation: str) -> list[str]:
        """Extract key concepts from LLM-generated explanation.

        Simple regex for capitalized phrases (e.g., "OAuth 2.0", "PKCE flow").

        Args:
            explanation: LLM-generated explanation text

        Returns:
            List of concepts (max 5)
        """
        # Match capitalized phrases (e.g., "OAuth 2.0", "PKCE Flow")
        concepts = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z0-9][a-z0-9.]*)*", explanation)

        # Return top 5 unique concepts
        unique_concepts = []
        seen = set()
        for concept in concepts:
            if concept.lower() not in seen:
                unique_concepts.append(concept)
                seen.add(concept.lower())
            if len(unique_concepts) >= 5:
                break

        return unique_concepts


async def get_explanation_service() -> ExplanationService:
    """FastAPI dependency for ExplanationService.

    Returns:
        ExplanationService: Service instance with Qdrant and Redis clients
    """
    from app.integrations.qdrant_client import qdrant_service

    return ExplanationService(
        qdrant_service=qdrant_service,
        redis_client=RedisClient,
    )
