"""Unit tests for Qdrant indexing module.

Tests vector indexing, point ID generation, payload structure,
idempotency, and orphan chunk cleanup.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_qdrant_service():
    """Create a mock Qdrant service."""
    with patch("app.workers.indexing.qdrant_service") as mock:
        mock.collection_exists = AsyncMock(return_value=True)
        mock.create_collection = AsyncMock()
        mock.upsert_points = AsyncMock(return_value=2)
        mock.delete_points_by_filter = AsyncMock(return_value=0)
        mock.client = MagicMock()
        mock.client.count = MagicMock(return_value=MagicMock(count=5))
        yield mock


@pytest.fixture
def sample_embeddings():
    """Create sample ChunkEmbedding objects for testing."""
    from app.workers.chunking import DocumentChunk
    from app.workers.embedding import ChunkEmbedding

    chunks = [
        DocumentChunk(
            text="First chunk content.",
            chunk_index=0,
            document_id="doc-abc-123",
            document_name="test.pdf",
            page_number=1,
            section_header="Introduction",
            char_start=0,
            char_end=20,
        ),
        DocumentChunk(
            text="Second chunk content.",
            chunk_index=1,
            document_id="doc-abc-123",
            document_name="test.pdf",
            page_number=1,
            section_header="Introduction",
            char_start=21,
            char_end=42,
        ),
    ]

    return [
        ChunkEmbedding(chunk=chunks[0], embedding=[0.1] * 1536),
        ChunkEmbedding(chunk=chunks[1], embedding=[0.2] * 1536),
    ]


class TestIndexDocument:
    """Tests for index_document function."""

    @pytest.mark.asyncio
    async def test_index_document_basic(self, mock_qdrant_service, sample_embeddings):
        """Test basic document indexing."""
        from app.workers.indexing import index_document

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        result = await index_document(
            doc_id="doc-abc-123",
            kb_id=kb_id,
            embeddings=sample_embeddings,
        )

        assert result == 2
        mock_qdrant_service.upsert_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_document_creates_collection_if_missing(
        self, mock_qdrant_service, sample_embeddings
    ):
        """Test that collection is created if it doesn't exist."""
        from app.workers.indexing import index_document

        mock_qdrant_service.collection_exists.return_value = False
        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        await index_document(
            doc_id="doc-abc-123",
            kb_id=kb_id,
            embeddings=sample_embeddings,
        )

        mock_qdrant_service.create_collection.assert_called_once_with(kb_id)

    @pytest.mark.asyncio
    async def test_index_document_empty_embeddings(self, mock_qdrant_service):
        """Test that empty embeddings returns 0."""
        from app.workers.indexing import index_document

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        result = await index_document(
            doc_id="doc-abc-123",
            kb_id=kb_id,
            embeddings=[],
        )

        assert result == 0
        mock_qdrant_service.upsert_points.assert_not_called()

    @pytest.mark.asyncio
    async def test_index_document_retries_on_failure(
        self, mock_qdrant_service, sample_embeddings
    ):
        """Test that indexing retries on transient failures."""
        from app.workers.indexing import index_document

        # First call fails, second succeeds
        mock_qdrant_service.upsert_points.side_effect = [
            Exception("Connection error"),
            2,
        ]

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        result = await index_document(
            doc_id="doc-abc-123",
            kb_id=kb_id,
            embeddings=sample_embeddings,
            max_retries=3,
        )

        assert result == 2
        assert mock_qdrant_service.upsert_points.call_count == 2

    @pytest.mark.asyncio
    async def test_index_document_raises_after_max_retries(
        self, mock_qdrant_service, sample_embeddings
    ):
        """Test that IndexingError is raised after max retries."""
        from app.workers.indexing import IndexingError, index_document

        mock_qdrant_service.upsert_points.side_effect = Exception("Persistent error")

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        with pytest.raises(IndexingError) as exc_info:
            await index_document(
                doc_id="doc-abc-123",
                kb_id=kb_id,
                embeddings=sample_embeddings,
                max_retries=2,
            )

        assert "2 retries" in str(exc_info.value)
        assert mock_qdrant_service.upsert_points.call_count == 2


class TestPointCreation:
    """Tests for point creation and ID generation."""

    def test_create_points_structure(self, sample_embeddings):
        """Test that PointStruct objects are created correctly."""
        from app.workers.indexing import _create_points

        points = _create_points(sample_embeddings)

        assert len(points) == 2

        # Check first point
        assert points[0].id == "doc-abc-123_0"
        assert len(points[0].vector) == 1536
        assert points[0].payload["document_id"] == "doc-abc-123"
        assert points[0].payload["document_name"] == "test.pdf"
        assert points[0].payload["chunk_text"] == "First chunk content."
        assert points[0].payload["chunk_index"] == 0
        assert points[0].payload["page_number"] == 1
        assert points[0].payload["section_header"] == "Introduction"

        # Check second point
        assert points[1].id == "doc-abc-123_1"
        assert points[1].payload["chunk_index"] == 1

    def test_point_id_format_deterministic(self):
        """Test that point IDs are deterministic for idempotency."""
        from app.workers.chunking import DocumentChunk
        from app.workers.embedding import ChunkEmbedding
        from app.workers.indexing import _create_points

        chunk = DocumentChunk(
            text="Test",
            chunk_index=42,
            document_id="uuid-123",
            document_name="test.pdf",
        )
        embedding = ChunkEmbedding(chunk=chunk, embedding=[0.1] * 1536)

        points1 = _create_points([embedding])
        points2 = _create_points([embedding])

        # Same input should produce same point ID
        assert points1[0].id == points2[0].id == "uuid-123_42"


class TestOrphanCleanup:
    """Tests for orphan chunk cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_orphan_chunks_basic(self, mock_qdrant_service):
        """Test orphan chunk cleanup."""
        from app.workers.indexing import cleanup_orphan_chunks

        mock_qdrant_service.delete_points_by_filter.return_value = 5

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        result = await cleanup_orphan_chunks(
            doc_id="doc-abc-123",
            kb_id=kb_id,
            max_chunk_index=9,
        )

        assert result == 5
        mock_qdrant_service.delete_points_by_filter.assert_called_once()

        # Check filter was constructed correctly
        call_args = mock_qdrant_service.delete_points_by_filter.call_args
        assert call_args.kwargs["kb_id"] == kb_id

    @pytest.mark.asyncio
    async def test_cleanup_orphan_chunks_no_orphans(self, mock_qdrant_service):
        """Test cleanup when there are no orphan chunks."""
        from app.workers.indexing import cleanup_orphan_chunks

        mock_qdrant_service.delete_points_by_filter.return_value = 0

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        result = await cleanup_orphan_chunks(
            doc_id="doc-abc-123",
            kb_id=kb_id,
            max_chunk_index=10,
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_orphan_chunks_handles_errors(self, mock_qdrant_service):
        """Test that cleanup errors are handled gracefully."""
        from app.workers.indexing import cleanup_orphan_chunks

        mock_qdrant_service.delete_points_by_filter.side_effect = Exception(
            "Qdrant error"
        )

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        # Should not raise, just return 0
        result = await cleanup_orphan_chunks(
            doc_id="doc-abc-123",
            kb_id=kb_id,
            max_chunk_index=5,
        )

        assert result == 0


class TestDeleteDocumentVectors:
    """Tests for document vector deletion."""

    @pytest.mark.asyncio
    async def test_delete_document_vectors(self, mock_qdrant_service):
        """Test deleting all vectors for a document."""
        from app.workers.indexing import delete_document_vectors

        mock_qdrant_service.delete_points_by_filter.return_value = 10

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        result = await delete_document_vectors(
            doc_id="doc-abc-123",
            kb_id=kb_id,
        )

        assert result == 10
        mock_qdrant_service.delete_points_by_filter.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_vectors_raises_on_error(self, mock_qdrant_service):
        """Test that deletion errors are raised."""
        from app.workers.indexing import IndexingError, delete_document_vectors

        mock_qdrant_service.delete_points_by_filter.side_effect = Exception(
            "Qdrant error"
        )

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        with pytest.raises(IndexingError):
            await delete_document_vectors(
                doc_id="doc-abc-123",
                kb_id=kb_id,
            )


class TestGetDocumentChunkCount:
    """Tests for getting document chunk count."""

    @pytest.mark.asyncio
    async def test_get_document_chunk_count(self, mock_qdrant_service):
        """Test getting chunk count for a document."""
        from app.workers.indexing import get_document_chunk_count

        mock_qdrant_service.client.count.return_value = MagicMock(count=15)

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        result = await get_document_chunk_count(
            doc_id="doc-abc-123",
            kb_id=kb_id,
        )

        assert result == 15

    @pytest.mark.asyncio
    async def test_get_document_chunk_count_handles_errors(self, mock_qdrant_service):
        """Test that errors return 0."""
        from app.workers.indexing import get_document_chunk_count

        mock_qdrant_service.client.count.side_effect = Exception("Qdrant error")

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        result = await get_document_chunk_count(
            doc_id="doc-abc-123",
            kb_id=kb_id,
        )

        assert result == 0
