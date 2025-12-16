"""Unit tests for GenerationService (Story 4.5)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.generation import GenerationRequest
from app.services.generation_service import (
    GenerationService,
    InsufficientSourcesError,
)


class TestGenerationService:
    """Unit tests for GenerationService streaming generation."""

    @pytest.fixture
    def mock_chunks(self):
        """Mock Chunk objects."""
        chunks = []
        for i in range(3):
            chunk = MagicMock()
            chunk.id = f"chunk-{i + 1}"
            chunk.document_id = uuid.uuid4()
            chunk.chunk_text = f"This is chunk {i + 1} content with important information."
            chunk.char_start = i * 100
            chunk.char_end = (i + 1) * 100
            chunk.metadata = {
                "document_name": f"Document_{i + 1}.pdf",
                "page_number": i + 1,
                "section_header": f"Section {i + 1}",
            }
            chunks.append(chunk)
        return chunks

    @pytest.fixture
    def mock_session(self, mock_chunks):
        """Mock AsyncSession for database queries."""
        session = MagicMock()
        # Mock execute to return chunks
        result = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = mock_chunks
        result.scalars.return_value = scalars
        session.execute = AsyncMock(return_value=result)
        return session

    @pytest.mark.asyncio
    async def test_insufficient_sources_error(self):
        """Test error when no chunks provided (caught during streaming, not validation)."""
        service = GenerationService()
        # Manually construct request to bypass Pydantic validation for testing
        request = MagicMock()
        request.kb_id = "kb-123"
        request.mode = "rfp_response"
        request.additional_prompt = ""
        request.selected_chunk_ids = []  # Empty!

        with pytest.raises(InsufficientSourcesError) as exc_info:
            async for _ in service.generate_document_stream(
                session=MagicMock(),
                request=request,
                user_id="user-123",
            ):
                pass

        assert exc_info.value.provided == 0
        assert exc_info.value.required == 1

    @pytest.mark.asyncio
    async def test_stream_yields_status_events(self, mock_session, mock_chunks):
        """Test that status events are yielded during generation."""
        service = GenerationService()
        request = GenerationRequest(
            kb_id="kb-123",
            mode="technical_checklist",
            additional_prompt="Focus on security",
            selected_chunk_ids=["chunk-1", "chunk-2", "chunk-3"],
        )

        # Mock LLM streaming response
        mock_llm_response = AsyncMock()
        mock_llm_response.__aiter__.return_value = iter([])  # Empty stream for this test

        with patch.object(
            service.llm_client, "chat_completion", return_value=mock_llm_response
        ):
            events = []
            async for event in service.generate_document_stream(
                session=mock_session,
                request=request,
                user_id="user-123",
            ):
                events.append(event)

        # Verify status events emitted
        status_events = [e for e in events if e["type"] == "status"]
        assert len(status_events) >= 2  # At least "Preparing" and "Generating"
        assert any("Preparing" in e["content"] for e in status_events)
        assert any("Generating" in e["content"] for e in status_events)

    @pytest.mark.asyncio
    async def test_stream_yields_token_events(self, mock_session, mock_chunks):
        """Test that token events are yielded from LLM stream."""
        service = GenerationService()
        request = GenerationRequest(
            kb_id="kb-123",
            mode="rfp_response",
            additional_prompt="",
            selected_chunk_ids=["chunk-1", "chunk-2"],
        )

        # Mock LLM streaming response with tokens
        mock_chunks_llm = [
            self._create_llm_chunk("OAuth "),
            self._create_llm_chunk("2.0 "),
            self._create_llm_chunk("implementation [1]"),
        ]
        mock_llm_response = AsyncMock()
        mock_llm_response.__aiter__.return_value = iter(mock_chunks_llm)

        with patch.object(
            service.llm_client, "chat_completion", return_value=mock_llm_response
        ):
            events = []
            async for event in service.generate_document_stream(
                session=mock_session,
                request=request,
                user_id="user-123",
            ):
                events.append(event)

        # Verify token events
        token_events = [e for e in events if e["type"] == "token"]
        assert len(token_events) == 3
        assert token_events[0]["content"] == "OAuth "
        assert token_events[1]["content"] == "2.0 "

    @pytest.mark.asyncio
    async def test_citation_detection_and_emission(self, mock_session, mock_chunks):
        """Test that citations are detected and emitted as events."""
        service = GenerationService()
        request = GenerationRequest(
            kb_id="kb-123",
            mode="rfp_response",
            additional_prompt="",
            selected_chunk_ids=["chunk-1", "chunk-2", "chunk-3"],
        )

        # Mock LLM response with citation markers
        mock_chunks_llm = [
            self._create_llm_chunk("Our solution uses "),
            self._create_llm_chunk("OAuth 2.0 [1] and "),
            self._create_llm_chunk("AES-256 encryption [2]."),
        ]
        mock_llm_response = AsyncMock()
        mock_llm_response.__aiter__.return_value = iter(mock_chunks_llm)

        with patch.object(
            service.llm_client, "chat_completion", return_value=mock_llm_response
        ):
            events = []
            async for event in service.generate_document_stream(
                session=mock_session,
                request=request,
                user_id="user-123",
            ):
                events.append(event)

        # Verify citation events
        citation_events = [e for e in events if e["type"] == "citation"]
        assert len(citation_events) == 2  # [1] and [2]
        assert citation_events[0]["number"] == 1
        assert citation_events[1]["number"] == 2
        assert "data" in citation_events[0]
        assert citation_events[0]["data"]["document_name"] == "Source_Document_1.pdf"

    @pytest.mark.asyncio
    async def test_done_event_with_metadata(self, mock_session, mock_chunks):
        """Test that done event includes generation metadata."""
        service = GenerationService()
        request = GenerationRequest(
            kb_id="kb-123",
            mode="custom",
            additional_prompt="Test prompt",
            selected_chunk_ids=["chunk-1", "chunk-2"],
        )

        # Mock LLM response
        mock_llm_response = AsyncMock()
        mock_llm_response.__aiter__.return_value = iter([
            self._create_llm_chunk("Test content [1]")
        ])

        with patch.object(
            service.llm_client, "chat_completion", return_value=mock_llm_response
        ):
            events = []
            async for event in service.generate_document_stream(
                session=mock_session,
                request=request,
                user_id="user-123",
            ):
                events.append(event)

        # Verify done event
        done_events = [e for e in events if e["type"] == "done"]
        assert len(done_events) == 1
        done = done_events[0]
        assert "generation_id" in done
        assert done["generation_id"].startswith("gen-")
        assert "confidence" in done
        assert 0.0 <= done["confidence"] <= 1.0
        assert "sources_used" in done
        assert done["sources_used"] == 2

    @pytest.mark.asyncio
    async def test_build_context_from_chunks(self):
        """Test context building from chunks."""
        service = GenerationService()

        # Create test chunks as dicts (not MagicMock)
        chunks = [
            {
                "chunk_text": "Chunk 1 text",
                "metadata": {
                    "document_name": "Doc_1.pdf",
                    "page_number": 1,
                },
            },
            {
                "chunk_text": "Chunk 2 text",
                "metadata": {
                    "document_name": "Doc_2.pdf",
                    "page_number": 2,
                },
            },
        ]

        context = service._build_context_from_chunks(chunks)

        assert "[1] Doc_1.pdf (Page 1):" in context
        assert "Chunk 1 text" in context
        assert "[2] Doc_2.pdf (Page 2):" in context
        assert "Chunk 2 text" in context

    def _create_llm_chunk(self, content: str):
        """Helper to create mock LLM chunk."""
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta = MagicMock()
        chunk.choices[0].delta.content = content
        return chunk
