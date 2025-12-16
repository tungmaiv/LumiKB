"""Generation service for template-based document generation."""

import re
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import structlog
from litellm import RateLimitError
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.litellm_client import embedding_client
from app.schemas.generation import GenerationRequest
from app.services.citation_service import CitationService
from app.services.template_registry import get_template

logger = structlog.get_logger(__name__)

# Configuration constants
MAX_GENERATION_TOKENS = 4000  # Max tokens for generated document
MAX_SOURCE_CHUNKS = 50  # Limit source chunks to prevent context overflow


class InsufficientSourcesError(Exception):
    """Raised when not enough source chunks are provided."""

    def __init__(self, provided: int, required: int = 1):
        self.provided = provided
        self.required = required
        self.message = f"Insufficient sources: {provided} provided, minimum {required} required."
        super().__init__(self.message)


class GenerationError(Exception):
    """Base exception for generation failures with recovery suggestions."""

    def __init__(
        self,
        message: str,
        error_type: str,
        recovery_options: list[dict[str, str]],
    ):
        """Initialize generation error.

        Args:
            message: Human-readable error message
            error_type: Error type identifier (LLMTimeout, RateLimitError, etc.)
            recovery_options: List of recovery alternative dicts
        """
        self.message = message
        self.error_type = error_type
        self.recovery_options = recovery_options
        super().__init__(message)


class GenerationService:
    """Service for generating documents using template-based LLM synthesis.

    Orchestrates:
    1. Template selection (get_template function)
    2. Source chunk retrieval (via session)
    3. Context building (chunk text + metadata)
    4. LLM generation (LiteLLMClient)
    5. Citation extraction (CitationService)
    """

    def __init__(
        self,
        citation_service: CitationService | None = None,
    ):
        """Initialize generation service.

        Args:
            citation_service: Citation service for extracting citations (default: new instance)
        """
        self.citation_service = citation_service or CitationService()
        self.llm_client = embedding_client  # Reuse singleton LiteLLM client

    async def generate_document(
        self,
        _session: Any,  # SQLAlchemy async session (unused in stub)
        request: GenerationRequest,
        user_id: str,
    ) -> dict[str, Any]:
        """Generate a document using selected source chunks and template.

        STUB IMPLEMENTATION for Story 4.4:
        - Validates request and logs audit events
        - Returns mock response with template-appropriate structure
        - Defers actual Qdrant retrieval + LLM generation to Story 4.5

        Args:
            session: Database session (unused in stub)
            request: GenerationRequest with mode, chunks, additional_prompt
            user_id: User ID for audit logging

        Returns:
            Dict with document, citations, confidence, generation_id, mode, sources_used

        Raises:
            InsufficientSourcesError: If no source chunks provided
            ValueError: If invalid generation mode
        """
        logger.info(
            "generation.request",
            user_id=user_id,
            kb_id=request.kb_id,
            mode=request.mode,
            chunk_count=len(request.selected_chunk_ids),
        )

        # Validate minimum sources
        if not request.selected_chunk_ids:
            raise InsufficientSourcesError(provided=0, required=1)

        # Validate template exists (raises ValueError if invalid)
        _ = get_template(request.mode)

        generation_id = f"gen-{uuid.uuid4()}"

        # STUB: Return mock response
        # TODO Story 4.5: Implement Qdrant chunk retrieval + actual LLM generation
        mock_document = self._generate_mock_document(request.mode)
        mock_citations = self._generate_mock_citations(len(request.selected_chunk_ids))

        logger.info(
            "generation.complete",
            generation_id=generation_id,
            sources_used=len(request.selected_chunk_ids),
            citations_found=len(mock_citations),
            confidence=0.85,
            stub=True,
        )

        return {
            "document": mock_document,
            "citations": mock_citations,
            "confidence": 0.85,
            "generation_id": generation_id,
            "mode": request.mode,
            "sources_used": len(request.selected_chunk_ids),
        }

    def _generate_mock_document(self, mode: str) -> str:
        """Generate mock document for stub implementation.

        Args:
            mode: Generation mode

        Returns:
            Mock document string with citations
        """
        templates = {
            "rfp_response": """## Executive Summary
We propose a comprehensive solution leveraging our proven OAuth 2.0 implementation [1] and enterprise-grade security architecture [2].

## Technical Approach
Our platform utilizes industry-standard authentication flows [1] with multi-factor authentication support [3]. The system architecture is designed for scalability and reliability [2].

## Relevant Experience
We have successfully deployed similar solutions for Fortune 500 clients, demonstrating our capability to handle enterprise-scale requirements [4].""",
            "technical_checklist": """## Security Requirements Checklist

### Authentication & Authorization
- [ ] OAuth 2.0 / PKCE implementation [1]
- [ ] Multi-factor authentication (MFA) support [3]
- [ ] Role-based access control (RBAC) [2]

### Data Security
- [ ] Encryption at rest (AES-256) [2]
- [ ] TLS 1.3 for data in transit [4]
- [ ] Regular security audits [5]""",
            "requirements_summary": """## Executive Requirements Summary

### Critical Requirements
- **Authentication**: OAuth 2.0 with PKCE for secure authentication [1]
- **Security**: Enterprise-grade encryption and access controls [2]
- **Scalability**: Support for 10,000+ concurrent users [3]

### Secondary Requirements
- Multi-factor authentication support [4]
- Comprehensive audit logging [5]

### Optional Enhancements
- Single Sign-On (SSO) integration [6]""",
            "custom": """## Generated Document

Based on the selected sources, here is a synthesis of the key information:

Our solution implements industry best practices for security and authentication [1]. The architecture supports enterprise-scale deployments [2] with built-in compliance features [3].

Key capabilities include secure authentication flows [1], data encryption [4], and comprehensive audit trails [5].""",
        }
        return templates.get(mode, templates["custom"])

    def _generate_mock_citations(self, count: int) -> list[dict[str, Any]]:
        """Generate mock citations for stub implementation.

        Args:
            count: Number of sources selected

        Returns:
            List of mock Citation dicts
        """
        citations = []
        for i in range(min(count, 6)):  # Max 6 citations in mock documents
            citations.append({
                "number": i + 1,
                "document_id": f"doc-{uuid.uuid4()}",
                "document_name": f"Source_Document_{i + 1}.pdf",
                "page_number": (i % 10) + 1,
                "section_header": f"Section {i + 1}",
                "excerpt": f"This is excerpt {i + 1} from the source document...",
                "char_start": i * 100,
                "char_end": (i + 1) * 100,
                "confidence": 0.85 + (i * 0.02),
            })
        return citations

    async def generate_document_stream(
        self,
        _session: AsyncSession,
        request: GenerationRequest,
        user_id: str,
        feedback: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream document generation with real-time tokens and citations.

        Yields SSE events as they occur:
        - status: Generation status updates
        - token: Individual LLM response tokens
        - citation: Citation data when markers detected
        - done: Completion with final metadata

        Args:
            _session: Database session (unused in stub implementation)
            request: GenerationRequest with mode, chunks, additional_prompt
            user_id: User ID for audit logging
            feedback: Optional feedback from previous generation
                {
                    "type": "needs_more_detail",
                    "comments": "Too high-level",
                    "previous_draft_id": "uuid"
                }

        Yields:
            Dict events for SSE streaming

        Raises:
            InsufficientSourcesError: If no source chunks provided
            ValueError: If invalid generation mode
        """
        logger.info(
            "generation.stream.started",
            user_id=user_id,
            kb_id=request.kb_id,
            mode=request.mode,
            chunk_count=len(request.selected_chunk_ids),
            has_feedback=feedback is not None,
        )

        # 1. Enhance additional_prompt with feedback context
        enhanced_prompt = request.additional_prompt
        if feedback:
            from app.services.feedback_service import FeedbackService
            feedback_service = FeedbackService()
            enhanced_prompt = feedback_service.build_regeneration_context(
                original_context=request.additional_prompt or "",
                feedback_type=feedback["type"],
                comments=feedback.get("comments"),
            )
            logger.info(
                "generation.feedback_applied",
                feedback_type=feedback["type"],
                previous_draft_id=feedback.get("previous_draft_id"),
            )

        # 2. Determine source retrieval strategy based on feedback
        chunk_ids_to_use = request.selected_chunk_ids

        if feedback:
            feedback_type = feedback["type"]
            if feedback_type == "not_relevant":
                # TODO Story 5.15: Retrieve NEW sources with refined query
                # For now, use selected chunks (no Qdrant integration yet)
                logger.info("generation.feedback_strategy", strategy="retrieve_new_sources")
            elif feedback_type == "needs_more_detail":
                # TODO Story 5.15: Add 5 more chunks to existing sources
                # For now, duplicate first 5 chunks as mock
                logger.info("generation.feedback_strategy", strategy="add_more_chunks")
                chunk_ids_to_use = request.selected_chunk_ids[:5] + request.selected_chunk_ids[:5]
            elif feedback_type == "low_confidence":
                # TODO Story 5.15: Filter sources by confidence score > 0.8
                # For now, use all selected chunks
                logger.info("generation.feedback_strategy", strategy="filter_high_confidence")
            else:  # wrong_format, other
                # Reuse same sources
                logger.info("generation.feedback_strategy", strategy="reuse_sources")

        # Validate minimum sources
        if not chunk_ids_to_use:
            raise InsufficientSourcesError(provided=0, required=1)

        # 3. Yield status: Preparing sources
        yield {"type": "status", "content": "Preparing sources..."}

        # 4. Build mock chunks (Story 4.5 - deferred Qdrant retrieval to Story 5.15)
        # TODO Story 5.15: Replace with actual Qdrant chunk retrieval
        chunks = self._build_mock_chunks_for_streaming(chunk_ids_to_use)

        # 5. Build system prompt from template (validates mode)
        template = get_template(request.mode)
        system_prompt = template.system_prompt
        if enhanced_prompt.strip():
            system_prompt = f"""{system_prompt}

ADDITIONAL USER INSTRUCTIONS:
{enhanced_prompt.strip()}

Remember to follow all CRITICAL RULES above while incorporating these additional instructions."""

        # 6. Build context from chunks
        context_text = self._build_context_from_chunks(chunks)
        generation_id = f"gen-{uuid.uuid4()}"

        # 7. Construct messages for LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Source Documents:\n\n{context_text}\n\nPlease generate the document."},
        ]

        # 8. Yield status: Generating
        yield {"type": "status", "content": "Generating draft..."}

        # 9. Stream from LLM - accumulate tokens and detect citations
        response_text = ""
        detected_citations = []
        citation_numbers_seen = set()

        # Get streaming response from LLM
        stream_response = await self.llm_client.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=MAX_GENERATION_TOKENS,
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
                if citation_num not in citation_numbers_seen and citation_num <= len(chunks):
                    # Extract citation for this marker
                    chunk_obj = chunks[citation_num - 1]
                    citation_data = {
                        "number": citation_num,
                        "document_id": chunk_obj["document_id"],
                        "document_name": chunk_obj["metadata"].get("document_name", "Unknown"),
                        "page_number": chunk_obj["metadata"].get("page_number"),
                        "section_header": chunk_obj["metadata"].get("section_header"),
                        "excerpt": chunk_obj["chunk_text"][:200],  # First 200 chars
                        "char_start": chunk_obj["char_start"],
                        "char_end": chunk_obj["char_end"],
                        "confidence": 0.85,  # Default confidence for generation
                    }
                    detected_citations.append(citation_data)
                    citation_numbers_seen.add(citation_num)

                    # Yield citation event immediately
                    yield {"type": "citation", "number": citation_num, "data": citation_data}

        # 10. Calculate confidence (simple heuristic: citation density)
        words = len(response_text.split())
        citation_density = len(detected_citations) / (words / 100) if words > 0 else 0.0
        confidence = min(citation_density * 0.5 + 0.5, 1.0)  # Scale 0.5-1.0

        logger.info(
            "generation.stream.complete",
            generation_id=generation_id,
            sources_used=len(chunks),
            citations_found=len(detected_citations),
            confidence=confidence,
        )

        # 11. Yield done event with metadata
        done_event = {
            "type": "done",
            "generation_id": generation_id,
            "confidence": confidence,
            "sources_used": len(chunks),
        }

        # Include previous_draft_id if feedback regeneration
        if feedback and feedback.get("previous_draft_id"):
            done_event["previous_draft_id"] = feedback["previous_draft_id"]

        yield done_event

    def _build_mock_chunks_for_streaming(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        """Build mock chunks for Story 4.5 streaming implementation.

        TODO Story 5.15: Replace with actual Qdrant retrieval.

        Args:
            chunk_ids: List of chunk IDs to mock

        Returns:
            List of mock chunk dicts
        """
        chunks = []
        for i, chunk_id in enumerate(chunk_ids):
            chunks.append({
                "id": chunk_id,
                "document_id": str(uuid.uuid4()),
                "chunk_text": f"Mock content for chunk {i + 1}: OAuth 2.0 implementation with PKCE flow ensures secure authentication and supports MFA.",
                "char_start": i * 100,
                "char_end": (i + 1) * 100,
                "metadata": {
                    "document_name": f"Source_Document_{i + 1}.pdf",
                    "page_number": i + 1,
                    "section_header": f"Section {i + 1}",
                },
            })
        return chunks

    def _build_context_from_chunks(self, chunks: list[dict[str, Any]]) -> str:
        """Build numbered context from chunks for LLM prompt.

        Args:
            chunks: List of chunk dicts

        Returns:
            Formatted context string with source numbering
        """
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk["metadata"].get("document_name", "Unknown")
            page = chunk["metadata"].get("page_number", "N/A")
            context_parts.append(
                f"[{i}] {doc_name} (Page {page}):\n{chunk['chunk_text']}\n"
            )
        return "\n".join(context_parts)

    async def generate_document_stream_with_recovery(
        self,
        _session: AsyncSession,
        request: GenerationRequest,
        user_id: str,
        feedback: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream document generation with automatic error recovery.

        Wraps generate_document_stream in try/except and maps errors to recovery options.

        Args:
            _session: Database session (unused in stub implementation)
            request: GenerationRequest
            user_id: User ID for audit
            feedback: Optional feedback context

        Yields:
            Dict events for SSE streaming

        Raises:
            GenerationError: With recovery options on error
        """
        try:
            async for event in self.generate_document_stream(_session, request, user_id, feedback):
                yield event

        except TimeoutError as e:
            # LLM timeout - suggest retry or template
            logger.error("generation.timeout", error=str(e))
            raise GenerationError(
                message="Generation took too long and was cancelled.",
                error_type="LLMTimeout",
                recovery_options=[
                    {
                        "type": "retry",
                        "description": "Retry generation with same parameters",
                        "action": "retry",
                    },
                    {
                        "type": "use_template",
                        "description": "Start from a structured template instead",
                        "action": "select_template",
                    },
                    {
                        "type": "search_more",
                        "description": "Search for more sources before generating",
                        "action": "search",
                    },
                ],
            ) from e

        except RateLimitError as e:
            # Rate limit - suggest wait + retry
            logger.error("generation.rate_limit", error=str(e))
            raise GenerationError(
                message="Too many requests. Please wait a moment and try again.",
                error_type="RateLimitError",
                recovery_options=[
                    {
                        "type": "wait_retry",
                        "description": "Wait 30 seconds and retry automatically",
                        "action": "auto_retry",
                    },
                    {
                        "type": "use_template",
                        "description": "Use a template while waiting",
                        "action": "select_template",
                    },
                ],
            ) from e

        except InsufficientSourcesError as e:
            # Not enough sources - suggest search
            logger.error("generation.insufficient_sources", error=str(e))
            raise GenerationError(
                message="Not enough relevant sources found for generation.",
                error_type="InsufficientSources",
                recovery_options=[
                    {
                        "type": "search_more",
                        "description": "Search for more sources with different query",
                        "action": "search",
                    },
                    {
                        "type": "use_template",
                        "description": "Start from a structured template",
                        "action": "select_template",
                    },
                ],
            ) from e

        except Exception as e:
            # Generic error
            logger.error("generation.error", error=str(e), error_type=type(e).__name__)
            raise GenerationError(
                message="Generation failed due to an unexpected error.",
                error_type="Unknown",
                recovery_options=[
                    {
                        "type": "retry",
                        "description": "Try again",
                        "action": "retry",
                    },
                    {
                        "type": "contact_support",
                        "description": "Contact support for help",
                        "action": "contact_support",
                    },
                ],
            ) from e
