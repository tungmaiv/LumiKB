"""Conversation service for multi-turn RAG conversations."""

import json
import re
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import structlog

from app.core.redis import RedisClient
from app.integrations.litellm_client import embedding_client
from app.schemas.citation import Citation
from app.schemas.search import SearchResultSchema
from app.services.citation_service import CitationService
from app.services.search_service import SearchService

logger = structlog.get_logger(__name__)

# Configuration constants
MAX_CONTEXT_TOKENS = 6000  # Reserve 2000 for response
MAX_HISTORY_MESSAGES = 10  # Last 10 message pairs
CONVERSATION_TTL = 86400  # 24 hours in seconds

# LLM System Prompt for Chat (citation-first architecture)
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
    ):
        """Initialize conversation service.

        Args:
            search_service: Search service for RAG retrieval
            citation_service: Citation service for extracting citations (default: new instance)
        """
        self.search_service = search_service
        self.citation_service = citation_service or CitationService()
        self.llm_client = embedding_client  # Reuse singleton LiteLLM client

    async def send_message(
        self,
        session_id: str,
        kb_id: str,
        user_id: str,
        message: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a chat message and get response with citations.

        Args:
            session_id: User session ID
            kb_id: Knowledge Base ID
            user_id: User ID for permission checks
            message: User message
            conversation_id: Existing conversation ID (optional)

        Returns:
            Dict with answer, citations, confidence, conversation_id

        Raises:
            NoDocumentsError: If KB has no indexed documents
        """
        # 1. Retrieve conversation history
        history = await self.get_history(session_id, kb_id)

        # 2. Perform RAG retrieval
        search_response = await self.search_service.search(
            query=message,
            kb_ids=[kb_id],
            user_id=user_id,
            limit=10,
            stream=False,
        )

        if not search_response.results:
            raise NoDocumentsError(kb_id)

        # 3. Build prompt with history + context
        prompt_messages = self._build_prompt(history, message, search_response.results)

        # 4. Generate response via LiteLLM
        response = await self.llm_client.chat_completion(
            messages=prompt_messages,
            temperature=0.3,
            max_tokens=2000,
            stream=False,
        )

        response_text = response.choices[0].message.content

        # 5. Extract citations
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

        return {
            "answer": answer_with_markers,
            "citations": [citation.model_dump() for citation in citations],
            "confidence": confidence,
            "conversation_id": conversation_id,
        }

    async def send_message_stream(
        self,
        session_id: str,
        kb_id: str,
        user_id: str,
        message: str,
        conversation_id: str | None = None,
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

        Yields:
            Dict events for SSE streaming

        Raises:
            NoDocumentsError: If KB has no indexed documents
        """
        # 1. Yield status: Searching
        yield {"type": "status", "content": "Searching relevant documents..."}

        # 2. Retrieve conversation history
        history = await self.get_history(session_id, kb_id)

        # 3. Perform RAG retrieval
        search_response = await self.search_service.search(
            query=message,
            kb_ids=[kb_id],
            user_id=user_id,
            limit=10,
            stream=False,
        )

        if not search_response.results:
            raise NoDocumentsError(kb_id)

        # 4. Build prompt with history + context
        prompt_messages = self._build_prompt(history, message, search_response.results)

        # 5. Yield status: Generating
        yield {"type": "status", "content": "Generating answer..."}

        # 6. Stream from LLM - accumulate tokens and detect citations
        response_text = ""
        detected_citations = []
        citation_numbers_seen = set()

        # Get streaming response from LLM
        stream_response = await self.llm_client.chat_completion(
            messages=prompt_messages,
            temperature=0.3,
            max_tokens=2000,
            stream=True,
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
            matches = re.finditer(r'\[(\d+)\]', response_text)
            for match in matches:
                citation_num = int(match.group(1))
                if citation_num not in citation_numbers_seen and citation_num <= len(search_response.results):
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

        # 7. Calculate confidence (average of chunk scores)
        confidence = (
            sum(result.relevance_score for result in search_response.results)
            / len(search_response.results)
            if search_response.results
            else 0.0
        )

        # 8. Store in Redis
        conversation_id = conversation_id or self._generate_conversation_id()
        await self._append_to_history(
            session_id=session_id,
            kb_id=kb_id,
            user_message=message,
            assistant_response=response_text,
            citations=[Citation(**cit) for cit in detected_citations],
            confidence=confidence,
        )

        # 9. Yield done event with metadata
        yield {
            "type": "done",
            "confidence": confidence,
            "conversation_id": conversation_id,
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
    ) -> list[dict[str, str]]:
        """Build prompt with context window management.

        Args:
            history: Conversation history
            message: Current user message
            chunks: Retrieved context chunks

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

        # Build final prompt
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]

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
