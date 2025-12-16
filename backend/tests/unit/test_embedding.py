"""Unit tests for embedding generation module.

Tests embedding generation, batching, rate limit handling,
and token limit error recovery.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


class MockEmbeddingResponse:
    """Mock response from LiteLLM embedding API."""

    def __init__(self, embeddings: list[list[float]], total_tokens: int = 100):
        self.data = [{"embedding": e} for e in embeddings]
        self.usage = MagicMock(total_tokens=total_tokens)


@pytest.fixture
def mock_embedding_client():
    """Create a mock embedding client."""
    with patch("app.workers.embedding.embedding_client") as mock:
        mock.get_embeddings = AsyncMock()
        mock.total_tokens_used = 0
        yield mock


@pytest.fixture
def sample_chunks():
    """Create sample DocumentChunk objects for testing."""
    from app.workers.chunking import DocumentChunk

    return [
        DocumentChunk(
            text="First chunk content here.",
            chunk_index=0,
            document_id="doc-123",
            document_name="test.pdf",
            page_number=1,
            section_header="Introduction",
            char_start=0,
            char_end=25,
        ),
        DocumentChunk(
            text="Second chunk content here.",
            chunk_index=1,
            document_id="doc-123",
            document_name="test.pdf",
            page_number=1,
            section_header="Introduction",
            char_start=26,
            char_end=52,
        ),
    ]


class TestGenerateEmbeddings:
    """Tests for generate_embeddings function."""

    @pytest.mark.asyncio
    async def test_generate_embeddings_basic(
        self, mock_embedding_client, sample_chunks
    ):
        """Test basic embedding generation."""
        from app.workers.embedding import generate_embeddings

        # Mock embeddings (1536 dimensions each)
        mock_embeddings = [[0.1] * 1536, [0.2] * 1536]
        mock_embedding_client.get_embeddings.return_value = mock_embeddings

        result = await generate_embeddings(sample_chunks)

        assert len(result) == 2
        assert result[0].chunk == sample_chunks[0]
        assert result[0].embedding == mock_embeddings[0]
        assert result[1].chunk == sample_chunks[1]
        assert result[1].embedding == mock_embeddings[1]

    @pytest.mark.asyncio
    async def test_generate_embeddings_empty_list(self, mock_embedding_client):
        """Test that empty chunk list returns empty result."""
        from app.workers.embedding import generate_embeddings

        result = await generate_embeddings([])

        assert result == []
        mock_embedding_client.get_embeddings.assert_not_called()

    @pytest.mark.asyncio
    async def test_point_id_generation(self, mock_embedding_client, sample_chunks):
        """Test that point IDs are generated as deterministic UUIDs."""
        from uuid import UUID

        from app.workers.embedding import generate_embeddings

        mock_embedding_client.get_embeddings.return_value = [[0.1] * 1536, [0.2] * 1536]

        result = await generate_embeddings(sample_chunks)

        # Point IDs should be valid UUIDs (deterministic from doc_id + chunk_index)
        UUID(result[0].point_id)  # Raises ValueError if not valid UUID
        UUID(result[1].point_id)
        # Different chunks should have different point IDs
        assert result[0].point_id != result[1].point_id

    @pytest.mark.asyncio
    async def test_rate_limit_error_propagates(
        self, mock_embedding_client, sample_chunks
    ):
        """Test that rate limit errors are propagated correctly."""
        from app.integrations.litellm_client import RateLimitExceededError
        from app.workers.embedding import EmbeddingGenerationError, generate_embeddings

        mock_embedding_client.get_embeddings.side_effect = RateLimitExceededError(
            "Rate limit exceeded after 5 retries"
        )

        with pytest.raises(EmbeddingGenerationError) as exc_info:
            await generate_embeddings(sample_chunks)

        assert "Rate limit exceeded" in str(exc_info.value)


class TestChunkEmbedding:
    """Tests for ChunkEmbedding dataclass."""

    def test_chunk_embedding_point_id(self):
        """Test ChunkEmbedding point_id property generates valid UUID."""
        from uuid import UUID

        from app.workers.chunking import DocumentChunk
        from app.workers.embedding import ChunkEmbedding

        chunk = DocumentChunk(
            text="Test content",
            chunk_index=5,
            document_id="abc-123",
            document_name="test.pdf",
        )

        embedding = ChunkEmbedding(chunk=chunk, embedding=[0.1] * 1536)

        # Point ID should be a valid UUID (deterministic from doc_id + chunk_index)
        UUID(embedding.point_id)  # Raises ValueError if not valid UUID

    def test_chunk_embedding_attributes(self):
        """Test ChunkEmbedding stores chunk and embedding correctly."""
        from app.workers.chunking import DocumentChunk
        from app.workers.embedding import ChunkEmbedding

        chunk = DocumentChunk(
            text="Test",
            chunk_index=0,
            document_id="doc-1",
            document_name="test.md",
        )
        embedding_vector = [0.5] * 1536

        embedding = ChunkEmbedding(chunk=chunk, embedding=embedding_vector)

        assert embedding.chunk is chunk
        assert embedding.embedding == embedding_vector


class TestEmbeddingDimensions:
    """Tests for embedding dimension validation."""

    @pytest.mark.asyncio
    async def test_validates_embedding_dimensions(
        self, mock_embedding_client, sample_chunks
    ):
        """Test that dimension mismatch is logged but not fatal."""
        from app.workers.embedding import generate_embeddings

        # Return wrong dimension embeddings
        mock_embedding_client.get_embeddings.return_value = [
            [0.1] * 512,  # Wrong dimensions
            [0.2] * 512,
        ]

        # Should still return results (with warning logged)
        result = await generate_embeddings(sample_chunks)

        assert len(result) == 2
        assert len(result[0].embedding) == 512  # Wrong but accepted


class TestLiteLLMEmbeddingClient:
    """Tests for LiteLLMEmbeddingClient class."""

    def test_client_initialization_defaults(self):
        """Test client uses settings defaults."""
        from app.integrations.litellm_client import LiteLLMEmbeddingClient

        with patch("app.integrations.litellm_client.settings") as mock_settings:
            mock_settings.embedding_model = "test-model"
            mock_settings.embedding_batch_size = 10
            mock_settings.embedding_max_retries = 3
            mock_settings.litellm_url = "http://test:4000"
            mock_settings.litellm_api_key = "test-key"

            client = LiteLLMEmbeddingClient()

            assert client.model == "test-model"
            assert client.batch_size == 10
            assert client.max_retries == 3

    def test_client_initialization_custom(self):
        """Test client accepts custom parameters."""
        from app.integrations.litellm_client import LiteLLMEmbeddingClient

        client = LiteLLMEmbeddingClient(
            model="custom-model",
            batch_size=5,
            max_retries=2,
            api_base="http://custom:4000",
            api_key="custom-key",
        )

        assert client.model == "custom-model"
        assert client.batch_size == 5
        assert client.max_retries == 2

    def test_token_counter_tracking(self):
        """Test token usage tracking."""
        from app.integrations.litellm_client import LiteLLMEmbeddingClient

        client = LiteLLMEmbeddingClient()
        client.total_tokens_used = 100

        assert client.get_total_tokens_used() == 100

        client.reset_token_counter()
        assert client.get_total_tokens_used() == 0

    @pytest.mark.asyncio
    async def test_batching_behavior(self):
        """Test that texts are batched correctly."""
        from app.integrations.litellm_client import LiteLLMEmbeddingClient

        with patch("app.integrations.litellm_client.aembedding") as mock_aembedding:
            # Create response mock
            mock_response = MockEmbeddingResponse([[0.1] * 1536] * 5)
            mock_aembedding.return_value = mock_response

            client = LiteLLMEmbeddingClient(batch_size=5, max_retries=1)

            # Send 12 texts - should result in 3 batches (5, 5, 2)
            texts = [f"Text {i}" for i in range(12)]
            await client.get_embeddings(texts)

            # Should have been called 3 times for batching
            assert mock_aembedding.call_count == 3

    @pytest.mark.asyncio
    async def test_empty_texts_returns_empty(self):
        """Test that empty text list returns empty embeddings."""
        from app.integrations.litellm_client import LiteLLMEmbeddingClient

        client = LiteLLMEmbeddingClient()
        result = await client.get_embeddings([])

        assert result == []


class TestRetryLogic:
    """Tests for retry and backoff logic."""

    @pytest.mark.asyncio
    async def test_rate_limit_triggers_retry(self):
        """Test that 429 response triggers retry with backoff."""

        from litellm.exceptions import RateLimitError

        from app.integrations.litellm_client import LiteLLMEmbeddingClient

        with (
            patch("app.integrations.litellm_client.aembedding") as mock_aembedding,
            patch("asyncio.sleep") as mock_sleep,
        ):
            # First call raises rate limit, second succeeds
            mock_response = MockEmbeddingResponse([[0.1] * 1536])
            mock_aembedding.side_effect = [
                RateLimitError("Rate limited", "", ""),
                mock_response,
            ]

            client = LiteLLMEmbeddingClient(max_retries=2)
            result = await client.get_embeddings(["test"])

            # Should have slept for backoff
            mock_sleep.assert_called_once_with(30)  # First retry delay

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_max_retries_exceeded_raises(self):
        """Test that exceeding max retries raises RateLimitExceededError."""
        from litellm.exceptions import RateLimitError

        from app.integrations.litellm_client import (
            LiteLLMEmbeddingClient,
            RateLimitExceededError,
        )

        with (
            patch("app.integrations.litellm_client.aembedding") as mock_aembedding,
            patch("asyncio.sleep"),
        ):
            mock_aembedding.side_effect = RateLimitError("Rate limited", "", "")

            client = LiteLLMEmbeddingClient(max_retries=2)

            with pytest.raises(RateLimitExceededError) as exc_info:
                await client.get_embeddings(["test"])

            assert "2 retries" in str(exc_info.value)


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig NamedTuple (Story 7-10)."""

    def test_embedding_config_defaults(self):
        """Test EmbeddingConfig with default values."""
        from app.workers.embedding import (
            DEFAULT_EMBEDDING_DIMENSIONS,
            EmbeddingConfig,
        )

        config = EmbeddingConfig()

        assert config.model_id is None
        assert config.dimensions == DEFAULT_EMBEDDING_DIMENSIONS
        assert config.api_endpoint is None

    def test_embedding_config_custom_values(self):
        """Test EmbeddingConfig with custom values."""
        from app.workers.embedding import EmbeddingConfig

        config = EmbeddingConfig(
            model_id="openai/text-embedding-3-small",
            dimensions=1536,
            api_endpoint="https://api.openai.com",
        )

        assert config.model_id == "openai/text-embedding-3-small"
        assert config.dimensions == 1536
        assert config.api_endpoint == "https://api.openai.com"


class TestKBSpecificEmbedding:
    """Tests for KB-specific embedding model support (Story 7-10)."""

    @pytest.mark.asyncio
    async def test_generate_embeddings_with_kb_config(
        self, mock_embedding_client, sample_chunks
    ):
        """Test embedding generation with KB-specific config (AC-7.10.8)."""
        from unittest.mock import AsyncMock, patch

        from app.workers.embedding import EmbeddingConfig, generate_embeddings

        # Create KB-specific embedding config
        kb_config = EmbeddingConfig(
            model_id="openai/text-embedding-3-small",
            dimensions=1536,
            api_endpoint=None,
            provider="openai",
        )

        # Mock the KB-specific client
        mock_kb_client = AsyncMock()
        mock_kb_client.get_embeddings.return_value = [[0.1] * 1536, [0.2] * 1536]

        with patch(
            "app.workers.embedding.LiteLLMEmbeddingClient",
            return_value=mock_kb_client,
        ) as mock_client_class:
            result = await generate_embeddings(sample_chunks, kb_config)

            # Verify KB-specific client was created with provider
            mock_client_class.assert_called_once_with(
                model="openai/text-embedding-3-small",
                api_base=None,
                provider="openai",
            )

            # Verify embeddings were generated
            assert len(result) == 2
            assert len(result[0].embedding) == 1536

    @pytest.mark.asyncio
    async def test_generate_embeddings_without_config_uses_default(
        self, mock_embedding_client, sample_chunks
    ):
        """Test embedding generation falls back to default without config."""
        from app.workers.embedding import generate_embeddings

        mock_embedding_client.get_embeddings.return_value = [
            [0.1] * 768,
            [0.2] * 768,
        ]

        result = await generate_embeddings(sample_chunks)

        # Should use default embedding client
        mock_embedding_client.get_embeddings.assert_called_once()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_dimension_validation_with_kb_config(
        self, mock_embedding_client, sample_chunks
    ):
        """Test dimension validation uses KB config dimensions (AC-7.10.9)."""
        from unittest.mock import AsyncMock, patch

        from app.workers.embedding import EmbeddingConfig, generate_embeddings

        # KB config expects 1536 dimensions
        kb_config = EmbeddingConfig(
            model_id="openai/text-embedding-3-small",
            dimensions=1536,
            api_endpoint=None,
            provider="openai",
        )

        mock_kb_client = AsyncMock()
        # Return embeddings with wrong dimensions (512 instead of 1536)
        mock_kb_client.get_embeddings.return_value = [[0.1] * 512, [0.2] * 512]

        with (
            patch(
                "app.workers.embedding.LiteLLMEmbeddingClient",
                return_value=mock_kb_client,
            ),
            patch("app.workers.embedding.logger") as mock_logger,
        ):
            result = await generate_embeddings(sample_chunks, kb_config)

            # Should log warning about dimension mismatch
            warning_calls = [
                c
                for c in mock_logger.warning.call_args_list
                if "unexpected_embedding_dimensions" in str(c)
            ]
            assert len(warning_calls) == 2  # One for each chunk

            # Results should still be returned
            assert len(result) == 2
