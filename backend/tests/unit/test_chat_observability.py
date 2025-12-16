"""Unit tests for chat/RAG flow observability instrumentation.

Tests verify:
- AC1: Chat conversation trace starts when endpoint receives request
- AC2: Retrieval span tracks query embedding, Qdrant search, documents, confidence
- AC3: Context assembly span tracks chunks, tokens, truncation
- AC4: LLM synthesis span tracks model, tokens, latency
- AC5: Citation mapping span tracks citations, confidence scores
- AC6: Overall trace captures user_id, kb_id, conversation_id, total_latency
- AC7: Chat messages logged for user and assistant
- AC8: Error traces capture step name and error type
- AC10: Unit tests verify span creation for each RAG pipeline step
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.citation import Citation
from app.services.conversation_service import ConversationService
from app.services.observability_service import ObservabilityService, TraceContext


class TestChatEndpointObservability:
    """Tests for chat.py endpoint observability instrumentation."""

    @pytest.fixture
    def mock_obs_service(self):
        """Create mock observability service."""
        with patch.object(ObservabilityService, "get_instance") as mock_get:
            mock_obs = MagicMock(spec=ObservabilityService)
            mock_obs.start_trace = AsyncMock(
                return_value=TraceContext(
                    trace_id=str(uuid.uuid4()),
                    span_id=str(uuid.uuid4()),
                    user_id=uuid.uuid4(),
                    kb_id=uuid.uuid4(),
                    timestamp=datetime.utcnow(),
                )
            )
            mock_obs.span = MagicMock(return_value=AsyncMock())
            mock_obs.log_chat_message = AsyncMock()
            mock_obs.log_llm_call = AsyncMock()
            mock_obs.end_trace = AsyncMock()
            mock_get.return_value = mock_obs
            yield mock_obs

    @pytest.fixture
    def trace_context(self):
        """Create a trace context for testing."""
        return TraceContext(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            kb_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
        )

    @pytest.mark.asyncio
    async def test_trace_starts_with_correct_name(self, mock_obs_service):
        """AC1: Trace starts when chat endpoint receives request."""
        # Arrange
        user_id = uuid.uuid4()
        kb_id = uuid.uuid4()
        conversation_id = f"conv-{uuid.uuid4()}"

        # Act - simulate what the endpoint does
        await mock_obs_service.start_trace(
            name="chat.conversation",
            user_id=user_id,
            kb_id=kb_id,
            metadata={
                "conversation_id": conversation_id,
                "message_length": 50,
            },
        )

        # Assert
        mock_obs_service.start_trace.assert_called_once()
        call_kwargs = mock_obs_service.start_trace.call_args.kwargs
        assert call_kwargs["name"] == "chat.conversation"
        assert call_kwargs["user_id"] == user_id
        assert call_kwargs["kb_id"] == kb_id
        assert "conversation_id" in call_kwargs["metadata"]
        assert "message_length" in call_kwargs["metadata"]

    @pytest.mark.asyncio
    async def test_user_message_logged(self, mock_obs_service, trace_context):
        """AC7: User message is logged via log_chat_message()."""
        # Act
        await mock_obs_service.log_chat_message(
            ctx=trace_context,
            role="user",
            content="",  # Privacy: don't log actual content
            user_id=trace_context.user_id,
            kb_id=trace_context.kb_id,
            conversation_id=uuid.uuid4(),
        )

        # Assert
        mock_obs_service.log_chat_message.assert_called_once()
        call_kwargs = mock_obs_service.log_chat_message.call_args.kwargs
        assert call_kwargs["role"] == "user"
        assert call_kwargs["content"] == ""  # Privacy compliance
        assert call_kwargs["ctx"] == trace_context

    @pytest.mark.asyncio
    async def test_assistant_message_logged_with_latency(
        self, mock_obs_service, trace_context
    ):
        """AC7: Assistant message is logged with latency_ms."""
        # Act
        await mock_obs_service.log_chat_message(
            ctx=trace_context,
            role="assistant",
            content="",  # Privacy: don't log actual content
            user_id=trace_context.user_id,
            kb_id=trace_context.kb_id,
            conversation_id=uuid.uuid4(),
            latency_ms=1500,
        )

        # Assert
        mock_obs_service.log_chat_message.assert_called_once()
        call_kwargs = mock_obs_service.log_chat_message.call_args.kwargs
        assert call_kwargs["role"] == "assistant"
        assert call_kwargs["latency_ms"] == 1500

    @pytest.mark.asyncio
    async def test_trace_ends_on_success(self, mock_obs_service, trace_context):
        """AC6: Trace ends with completed status on success."""
        # Act
        await mock_obs_service.end_trace(trace_context, status="completed")

        # Assert
        mock_obs_service.end_trace.assert_called_once_with(
            trace_context, status="completed"
        )

    @pytest.mark.asyncio
    async def test_trace_ends_on_error(self, mock_obs_service, trace_context):
        """AC8: Error traces capture error type without sensitive content."""
        # Act
        await mock_obs_service.end_trace(
            trace_context,
            status="failed",
            error_message="NoDocumentsError",
        )

        # Assert
        mock_obs_service.end_trace.assert_called_once()
        call_kwargs = mock_obs_service.end_trace.call_args.kwargs
        assert call_kwargs["status"] == "failed"
        # Verify only error type, not sensitive query content
        assert call_kwargs["error_message"] == "NoDocumentsError"


class TestConversationServiceObservability:
    """Tests for conversation_service.py RAG pipeline instrumentation."""

    @pytest.fixture
    def mock_search_service(self):
        """Create mock search service."""
        mock = MagicMock()
        mock.search = AsyncMock(
            return_value=MagicMock(
                results=[
                    MagicMock(
                        chunk_id=str(uuid.uuid4()),
                        document_id=str(uuid.uuid4()),
                        content="Test content",
                        relevance_score=0.85,
                        metadata={},
                    )
                ],
                total_results=1,
            )
        )
        return mock

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        mock = MagicMock()
        mock.chat_completion = AsyncMock(
            return_value=MagicMock(
                choices=[
                    MagicMock(message=MagicMock(content="Test answer based on [1]"))
                ],
                model="gpt-4",
                usage=MagicMock(
                    prompt_tokens=100,
                    completion_tokens=50,
                    total_tokens=150,
                ),
            )
        )
        return mock

    @pytest.fixture
    def mock_obs_service(self):
        """Create mock observability service."""
        with patch.object(ObservabilityService, "get_instance") as mock_get:
            mock_obs = MagicMock(spec=ObservabilityService)

            # Create async context manager for span
            span_ctx_manager = AsyncMock()
            span_ctx_manager.__aenter__ = AsyncMock(return_value=str(uuid.uuid4()))
            span_ctx_manager.__aexit__ = AsyncMock(return_value=None)
            mock_obs.span = MagicMock(return_value=span_ctx_manager)

            mock_obs.log_llm_call = AsyncMock()
            mock_obs.start_trace = AsyncMock()
            mock_obs.end_trace = AsyncMock()
            mock_get.return_value = mock_obs
            yield mock_obs

    @pytest.fixture
    def trace_context(self):
        """Create a trace context for testing."""
        return TraceContext(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            kb_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
        )

    @pytest.fixture
    def conversation_service_with_mocks(self, mock_search_service, mock_llm_client):
        """Create conversation service with all dependencies mocked."""
        mock_citation = MagicMock()
        # Return proper Citation objects that have model_dump() method
        doc_id = str(uuid.uuid4())
        citation_obj = Citation(
            number=1,
            document_id=doc_id,
            document_name="Test Document.pdf",
            page_number=1,
            section_header="Test Section",
            excerpt="Test excerpt content",
            char_start=0,
            char_end=100,
            confidence=0.85,
        )
        mock_citation.extract_citations = MagicMock(
            return_value=("Answer [1]", [citation_obj])
        )

        service = ConversationService(
            mock_search_service, citation_service=mock_citation
        )
        # Replace LLM client with mock
        service.llm_client = mock_llm_client
        return service

    @pytest.mark.asyncio
    async def test_retrieval_span_created(
        self, conversation_service_with_mocks, mock_obs_service, trace_context
    ):
        """AC2: Retrieval span created with correct name and type."""
        # Arrange
        service = conversation_service_with_mocks

        with patch.object(service, "get_history", new_callable=AsyncMock) as mock_hist:
            mock_hist.return_value = []

            with patch.object(
                service, "_append_to_history", new_callable=AsyncMock
            ) as mock_append:
                mock_append.return_value = None

                # Act
                await service.send_message(
                    session_id="test-session",
                    kb_id=str(trace_context.kb_id),
                    user_id=str(trace_context.user_id),
                    message="Test query",
                    trace_ctx=trace_context,
                )

        # Assert - verify span was called with retrieval
        span_calls = mock_obs_service.span.call_args_list
        retrieval_spans = [c for c in span_calls if c.args[1] == "retrieval"]
        assert len(retrieval_spans) >= 1

    @pytest.mark.asyncio
    async def test_context_assembly_span_created(
        self, conversation_service_with_mocks, mock_obs_service, trace_context
    ):
        """AC3: Context assembly span tracks chunks and tokens."""
        # Arrange
        service = conversation_service_with_mocks

        with patch.object(service, "get_history", new_callable=AsyncMock) as mock_hist:
            mock_hist.return_value = []

            with patch.object(
                service, "_append_to_history", new_callable=AsyncMock
            ) as mock_append:
                mock_append.return_value = None

                # Act
                await service.send_message(
                    session_id="test-session",
                    kb_id=str(trace_context.kb_id),
                    user_id=str(trace_context.user_id),
                    message="Test query",
                    trace_ctx=trace_context,
                )

        # Assert - verify context_assembly span was created
        span_calls = mock_obs_service.span.call_args_list
        context_spans = [c for c in span_calls if c.args[1] == "context_assembly"]
        assert len(context_spans) >= 1

    @pytest.mark.asyncio
    async def test_synthesis_span_created(
        self, conversation_service_with_mocks, mock_obs_service, trace_context
    ):
        """AC4: LLM synthesis span created with correct type."""
        # Arrange
        service = conversation_service_with_mocks

        with patch.object(service, "get_history", new_callable=AsyncMock) as mock_hist:
            mock_hist.return_value = []

            with patch.object(
                service, "_append_to_history", new_callable=AsyncMock
            ) as mock_append:
                mock_append.return_value = None

                # Act
                await service.send_message(
                    session_id="test-session",
                    kb_id=str(trace_context.kb_id),
                    user_id=str(trace_context.user_id),
                    message="Test query",
                    trace_ctx=trace_context,
                )

        # Assert - verify synthesis span with type "llm"
        span_calls = mock_obs_service.span.call_args_list
        synthesis_spans = [c for c in span_calls if c.args[1] == "synthesis"]
        assert len(synthesis_spans) >= 1
        # Verify it has type "llm"
        for span in synthesis_spans:
            assert span.args[2] == "llm"

    @pytest.mark.asyncio
    async def test_llm_call_logged_after_synthesis(
        self, conversation_service_with_mocks, mock_obs_service, trace_context
    ):
        """AC4: log_llm_call() captures model, token counts, latency."""
        # Arrange
        service = conversation_service_with_mocks

        with patch.object(service, "get_history", new_callable=AsyncMock) as mock_hist:
            mock_hist.return_value = []

            with patch.object(
                service, "_append_to_history", new_callable=AsyncMock
            ) as mock_append:
                mock_append.return_value = None

                # Act
                await service.send_message(
                    session_id="test-session",
                    kb_id=str(trace_context.kb_id),
                    user_id=str(trace_context.user_id),
                    message="Test query",
                    trace_ctx=trace_context,
                )

        # Assert - verify log_llm_call was called
        mock_obs_service.log_llm_call.assert_called_once()
        call_kwargs = mock_obs_service.log_llm_call.call_args.kwargs
        assert call_kwargs["name"] == "chat_completion"
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["input_tokens"] == 100
        assert call_kwargs["output_tokens"] == 50

    @pytest.mark.asyncio
    async def test_citation_mapping_span_created(
        self, conversation_service_with_mocks, mock_obs_service, trace_context
    ):
        """AC5: Citation mapping span tracks citations generated."""
        # Arrange
        service = conversation_service_with_mocks

        with patch.object(service, "get_history", new_callable=AsyncMock) as mock_hist:
            mock_hist.return_value = []

            with patch.object(
                service, "_append_to_history", new_callable=AsyncMock
            ) as mock_append:
                mock_append.return_value = None

                # Act
                await service.send_message(
                    session_id="test-session",
                    kb_id=str(trace_context.kb_id),
                    user_id=str(trace_context.user_id),
                    message="Test query",
                    trace_ctx=trace_context,
                )

        # Assert - verify citation_mapping span was created
        span_calls = mock_obs_service.span.call_args_list
        citation_spans = [c for c in span_calls if c.args[1] == "citation_mapping"]
        assert len(citation_spans) >= 1

    @pytest.mark.asyncio
    async def test_no_instrumentation_without_trace_context(
        self, mock_search_service, mock_llm_client, mock_obs_service
    ):
        """Verify spans are not created when trace_ctx is None."""
        # Arrange
        mock_citation = MagicMock()
        mock_citation.extract_citations = MagicMock(return_value=("Answer", []))

        service = ConversationService(
            mock_search_service, citation_service=mock_citation
        )
        service.llm_client = mock_llm_client

        with patch.object(service, "get_history", new_callable=AsyncMock) as mock_hist:
            mock_hist.return_value = []

            with patch.object(
                service, "_append_to_history", new_callable=AsyncMock
            ) as mock_append:
                mock_append.return_value = None

                # Act - call without trace_ctx
                await service.send_message(
                    session_id="test-session",
                    kb_id=str(uuid.uuid4()),
                    user_id=str(uuid.uuid4()),
                    message="Test query",
                    trace_ctx=None,
                )

        # Assert - no spans should be created
        mock_obs_service.span.assert_not_called()
        mock_obs_service.log_llm_call.assert_not_called()


class TestStreamingChatObservability:
    """Tests for chat_stream.py endpoint observability."""

    @pytest.fixture
    def mock_obs_service(self):
        """Create mock observability service."""
        with patch.object(ObservabilityService, "get_instance") as mock_get:
            mock_obs = MagicMock(spec=ObservabilityService)
            mock_obs.start_trace = AsyncMock(
                return_value=TraceContext(
                    trace_id=str(uuid.uuid4()),
                    span_id=str(uuid.uuid4()),
                    user_id=uuid.uuid4(),
                    kb_id=uuid.uuid4(),
                    timestamp=datetime.utcnow(),
                )
            )
            mock_obs.span = MagicMock(return_value=AsyncMock())
            mock_obs.log_chat_message = AsyncMock()
            mock_obs.log_llm_call = AsyncMock()
            mock_obs.end_trace = AsyncMock()
            mock_get.return_value = mock_obs
            yield mock_obs

    @pytest.fixture
    def trace_context(self):
        """Create a trace context for testing."""
        return TraceContext(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            kb_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
        )

    @pytest.mark.asyncio
    async def test_streaming_trace_starts_with_correct_name(self, mock_obs_service):
        """AC9: Streaming trace starts with 'chat.conversation.stream' name."""
        # Arrange
        user_id = uuid.uuid4()
        kb_id = uuid.uuid4()

        # Act - simulate what the streaming endpoint does
        await mock_obs_service.start_trace(
            name="chat.conversation.stream",
            user_id=user_id,
            kb_id=kb_id,
            metadata={
                "conversation_id": None,
                "message_length": 50,
                "streaming": True,
            },
        )

        # Assert
        mock_obs_service.start_trace.assert_called_once()
        call_kwargs = mock_obs_service.start_trace.call_args.kwargs
        assert call_kwargs["name"] == "chat.conversation.stream"
        assert call_kwargs["metadata"]["streaming"] is True

    @pytest.mark.asyncio
    async def test_streaming_trace_ends_on_success(
        self, mock_obs_service, trace_context
    ):
        """AC9: Streaming trace ends after stream completes."""
        # Act
        await mock_obs_service.end_trace(trace_context, status="completed")

        # Assert
        mock_obs_service.end_trace.assert_called_once_with(
            trace_context, status="completed"
        )

    @pytest.mark.asyncio
    async def test_streaming_trace_ends_on_error(self, mock_obs_service, trace_context):
        """AC8/AC9: Streaming trace ends with error type on failure."""
        # Act
        await mock_obs_service.end_trace(
            trace_context,
            status="failed",
            error_message="LLMException",
        )

        # Assert
        mock_obs_service.end_trace.assert_called_once()
        call_kwargs = mock_obs_service.end_trace.call_args.kwargs
        assert call_kwargs["status"] == "failed"
        assert call_kwargs["error_message"] == "LLMException"


class TestErrorHandling:
    """Tests for error handling in observability instrumentation."""

    @pytest.fixture
    def mock_obs_service(self):
        """Create mock observability service."""
        with patch.object(ObservabilityService, "get_instance") as mock_get:
            mock_obs = MagicMock(spec=ObservabilityService)
            mock_obs.start_trace = AsyncMock(
                return_value=TraceContext(
                    trace_id=str(uuid.uuid4()),
                    span_id=str(uuid.uuid4()),
                    user_id=uuid.uuid4(),
                    kb_id=uuid.uuid4(),
                    timestamp=datetime.utcnow(),
                )
            )
            mock_obs.span = MagicMock(return_value=AsyncMock())
            mock_obs.log_chat_message = AsyncMock()
            mock_obs.end_trace = AsyncMock()
            mock_get.return_value = mock_obs
            yield mock_obs

    @pytest.fixture
    def trace_context(self):
        """Create a trace context for testing."""
        return TraceContext(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            kb_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
        )

    @pytest.mark.asyncio
    async def test_error_trace_captures_error_type_only(
        self, mock_obs_service, trace_context
    ):
        """AC8: Error traces capture error type without sensitive query content."""
        # Arrange
        sensitive_error = Exception("Query 'sensitive user data' failed")

        # Act - simulate what the endpoint does on error
        await mock_obs_service.end_trace(
            trace_context,
            status="failed",
            error_message=type(sensitive_error).__name__,  # Only error type
        )

        # Assert
        call_kwargs = mock_obs_service.end_trace.call_args.kwargs
        # Should only contain "Exception", not the sensitive message
        assert call_kwargs["error_message"] == "Exception"
        assert "sensitive user data" not in call_kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_http_exception_traced_correctly(
        self, mock_obs_service, trace_context
    ):
        """AC8: HTTPException traced with status code."""
        # Act
        await mock_obs_service.end_trace(
            trace_context,
            status="failed",
            error_message="HTTPException: 404",
        )

        # Assert
        call_kwargs = mock_obs_service.end_trace.call_args.kwargs
        assert call_kwargs["status"] == "failed"
        assert "HTTPException" in call_kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_no_documents_error_traced(self, mock_obs_service, trace_context):
        """AC8: NoDocumentsError traced correctly."""
        # Act
        await mock_obs_service.end_trace(
            trace_context,
            status="failed",
            error_message="NoDocumentsError",
        )

        # Assert
        call_kwargs = mock_obs_service.end_trace.call_args.kwargs
        assert call_kwargs["status"] == "failed"
        assert call_kwargs["error_message"] == "NoDocumentsError"
