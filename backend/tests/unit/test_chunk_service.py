"""Unit tests for ChunkService (Story 5-25, 7-7)."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.schemas.document import DocumentChunkResponse, DocumentChunksResponse
from app.services.chunk_service import (
    DEFAULT_CHUNK_LIMIT,
    MAX_CHUNK_LIMIT,
    ChunkService,
    ChunkServiceError,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def kb_id():
    """Test KB UUID."""
    return uuid4()


@pytest.fixture
def doc_id():
    """Test document UUID."""
    return uuid4()


@pytest.fixture
def chunk_service(kb_id):
    """ChunkService instance for testing."""
    return ChunkService(kb_id)


@pytest.fixture
def mock_qdrant_points():
    """Sample Qdrant points for testing."""
    return [
        MagicMock(
            id="point-1",
            payload={
                "document_id": str(uuid4()),
                "chunk_index": 0,
                "chunk_text": "First chunk text content",
                "char_start": 0,
                "char_end": 25,
                "page_number": 1,
                "section_header": "Introduction",
            },
        ),
        MagicMock(
            id="point-2",
            payload={
                "document_id": str(uuid4()),
                "chunk_index": 1,
                "chunk_text": "Second chunk text content",
                "char_start": 26,
                "char_end": 51,
                "page_number": 1,
                "section_header": "Introduction",
            },
        ),
        MagicMock(
            id="point-3",
            payload={
                "document_id": str(uuid4()),
                "chunk_index": 2,
                "chunk_text": "Third chunk text content",
                "char_start": 52,
                "char_end": 76,
                "page_number": 2,
                "section_header": "Body",
            },
        ),
    ]


# =============================================================================
# Test ChunkService initialization
# =============================================================================


def test_chunk_service_init(kb_id):
    """Test ChunkService initializes with correct collection name."""
    service = ChunkService(kb_id)
    assert service.kb_id == kb_id
    assert service.collection_name == f"kb_{kb_id}"


# =============================================================================
# Test get_chunks() pagination
# =============================================================================


@pytest.mark.asyncio
async def test_get_chunks_returns_paginated_response(
    chunk_service, doc_id, mock_qdrant_points
):
    """Test get_chunks returns paginated chunks from Qdrant."""
    with patch("app.services.chunk_service.qdrant_service") as mock_qdrant:
        # Story 7-7: Mock async methods directly on qdrant_service
        mock_qdrant.count = AsyncMock(return_value=MagicMock(count=3))
        mock_qdrant.scroll = AsyncMock(return_value=(mock_qdrant_points, None))

        result = await chunk_service.get_chunks(doc_id, cursor=0, limit=50)

        assert isinstance(result, DocumentChunksResponse)
        assert len(result.chunks) == 3
        assert result.total == 3
        assert result.has_more is False
        assert result.next_cursor is None


@pytest.mark.asyncio
async def test_get_chunks_with_cursor(chunk_service, doc_id, mock_qdrant_points):
    """Test get_chunks respects cursor parameter."""
    with patch("app.services.chunk_service.qdrant_service") as mock_qdrant:
        # Story 7-7: Mock async methods directly on qdrant_service
        mock_qdrant.count = AsyncMock(return_value=MagicMock(count=10))
        mock_qdrant.scroll = AsyncMock(return_value=(mock_qdrant_points[1:], None))

        result = await chunk_service.get_chunks(doc_id, cursor=1, limit=50)

        assert len(result.chunks) == 2
        # Verify scroll was called with cursor filter
        call_args = mock_qdrant.scroll.call_args
        assert call_args is not None


@pytest.mark.asyncio
async def test_get_chunks_has_more_when_limit_reached(chunk_service, doc_id):
    """Test has_more is True when more chunks exist beyond limit."""
    with patch("app.services.chunk_service.qdrant_service") as mock_qdrant:
        # Story 7-7: Mock async methods directly on qdrant_service
        mock_qdrant.count = AsyncMock(return_value=MagicMock(count=100))
        # Return limit+1 points to trigger has_more
        points = [
            MagicMock(
                id=f"point-{i}",
                payload={
                    "chunk_index": i,
                    "chunk_text": f"Chunk {i}",
                    "char_start": i * 100,
                    "char_end": (i + 1) * 100,
                },
            )
            for i in range(11)  # limit + 1
        ]
        mock_qdrant.scroll = AsyncMock(return_value=(points, None))

        result = await chunk_service.get_chunks(doc_id, cursor=0, limit=10)

        assert result.has_more is True
        assert result.next_cursor == 10
        assert len(result.chunks) == 10


@pytest.mark.asyncio
async def test_get_chunks_clamps_limit(chunk_service, doc_id, mock_qdrant_points):
    """Test get_chunks clamps limit to MAX_CHUNK_LIMIT."""
    with patch("app.services.chunk_service.qdrant_service") as mock_qdrant:
        # Story 7-7: Mock async methods directly on qdrant_service
        mock_qdrant.count = AsyncMock(return_value=MagicMock(count=3))
        mock_qdrant.scroll = AsyncMock(return_value=(mock_qdrant_points, None))

        # Request more than max
        result = await chunk_service.get_chunks(doc_id, cursor=0, limit=200)

        # Should still work, limit clamped internally
        assert isinstance(result, DocumentChunksResponse)


@pytest.mark.asyncio
async def test_get_chunks_empty_document(chunk_service, doc_id):
    """Test get_chunks returns empty response for document with no chunks."""
    with patch("app.services.chunk_service.qdrant_service") as mock_qdrant:
        # Story 7-7: Mock async methods directly on qdrant_service
        mock_qdrant.count = AsyncMock(return_value=MagicMock(count=0))

        result = await chunk_service.get_chunks(doc_id, cursor=0, limit=50)

        assert result.chunks == []
        assert result.total == 0
        assert result.has_more is False
        assert result.next_cursor is None


# =============================================================================
# Test get_chunks() with search query
# =============================================================================


@pytest.mark.asyncio
async def test_get_chunks_with_search_query(chunk_service, doc_id, mock_qdrant_points):
    """Test get_chunks with search query uses embedding search."""
    with patch("app.services.chunk_service.qdrant_service") as mock_qdrant:
        with patch("app.services.chunk_service.embedding_client") as mock_embed:
            # Story 7-7: Mock async methods directly on qdrant_service
            mock_qdrant.count = AsyncMock(return_value=MagicMock(count=3))
            # Mock embedding
            mock_embed.get_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
            # Mock search results as ScoredPoints
            scored_points = [
                MagicMock(
                    id="point-1",
                    score=0.95,
                    payload={
                        "chunk_index": 0,
                        "chunk_text": "Relevant chunk",
                        "char_start": 0,
                        "char_end": 14,
                    },
                ),
                MagicMock(
                    id="point-2",
                    score=0.85,
                    payload={
                        "chunk_index": 1,
                        "chunk_text": "Another chunk",
                        "char_start": 15,
                        "char_end": 28,
                    },
                ),
            ]
            # Story 7-7: Mock async search method
            mock_qdrant.search = AsyncMock(return_value=scored_points)

            result = await chunk_service.get_chunks(
                doc_id, cursor=0, limit=50, search_query="test search"
            )

            assert len(result.chunks) == 2
            assert result.chunks[0].score == 0.95
            assert result.chunks[1].score == 0.85
            mock_embed.get_embeddings.assert_called_once_with(["test search"])


# =============================================================================
# Test get_chunk_by_index()
# =============================================================================


@pytest.mark.asyncio
async def test_get_chunk_by_index_returns_chunk(
    chunk_service, doc_id, mock_qdrant_points
):
    """Test get_chunk_by_index returns single chunk."""
    with patch("app.services.chunk_service.qdrant_service") as mock_qdrant:
        # Story 7-7: Mock async scroll method
        mock_qdrant.scroll = AsyncMock(return_value=([mock_qdrant_points[0]], None))

        result = await chunk_service.get_chunk_by_index(doc_id, chunk_index=0)

        assert result is not None
        assert isinstance(result, DocumentChunkResponse)
        assert result.chunk_index == 0


@pytest.mark.asyncio
async def test_get_chunk_by_index_not_found(chunk_service, doc_id):
    """Test get_chunk_by_index returns None when not found."""
    with patch("app.services.chunk_service.qdrant_service") as mock_qdrant:
        # Story 7-7: Mock async scroll method
        mock_qdrant.scroll = AsyncMock(return_value=([], None))

        result = await chunk_service.get_chunk_by_index(doc_id, chunk_index=999)

        assert result is None


# =============================================================================
# Test error handling
# =============================================================================


@pytest.mark.asyncio
async def test_get_chunks_raises_on_qdrant_error(chunk_service, doc_id):
    """Test get_chunks raises ChunkServiceError on Qdrant failure."""
    with patch("app.services.chunk_service.qdrant_service") as mock_qdrant:
        # Story 7-7: Mock async count method to raise exception
        mock_qdrant.count = AsyncMock(side_effect=Exception("Qdrant connection failed"))

        with pytest.raises(ChunkServiceError) as exc_info:
            await chunk_service.get_chunks(doc_id)

        assert exc_info.value.code == "QDRANT_ERROR"
        assert "Failed to retrieve chunks" in exc_info.value.message


# =============================================================================
# Test _point_to_chunk() conversion
# =============================================================================


def test_point_to_chunk_conversion(chunk_service):
    """Test _point_to_chunk correctly converts Qdrant Record."""
    point = MagicMock()
    point.id = "test-uuid-123"
    point.payload = {
        "chunk_index": 5,
        "chunk_text": "Sample text content",
        "char_start": 100,
        "char_end": 119,
        "page_number": 3,
        "section_header": "Methods",
    }

    result = chunk_service._point_to_chunk(point)

    assert result.chunk_id == "test-uuid-123"
    assert result.chunk_index == 5
    assert result.text == "Sample text content"
    assert result.char_start == 100
    assert result.char_end == 119
    assert result.page_number == 3
    assert result.section_header == "Methods"
    assert result.score is None


def test_point_to_chunk_with_missing_fields(chunk_service):
    """Test _point_to_chunk handles missing optional fields."""
    point = MagicMock()
    point.id = "test-uuid-456"
    point.payload = {
        "chunk_index": 0,
        "chunk_text": "Minimal chunk",
    }

    result = chunk_service._point_to_chunk(point)

    assert result.chunk_id == "test-uuid-456"
    assert result.chunk_index == 0
    assert result.text == "Minimal chunk"
    assert result.char_start == 0  # Default
    assert result.char_end == 0  # Default
    assert result.page_number is None
    assert result.section_header is None


def test_scored_point_to_chunk_includes_score(chunk_service):
    """Test _scored_point_to_chunk includes relevance score."""
    point = MagicMock()
    point.id = "scored-point-123"
    point.score = 0.92
    point.payload = {
        "chunk_index": 2,
        "chunk_text": "Scored chunk",
        "char_start": 50,
        "char_end": 62,
    }

    result = chunk_service._scored_point_to_chunk(point)

    assert result.score == 0.92
    assert result.chunk_index == 2


# =============================================================================
# Test constants
# =============================================================================


def test_default_chunk_limit():
    """Test DEFAULT_CHUNK_LIMIT is set correctly."""
    assert DEFAULT_CHUNK_LIMIT == 50


def test_max_chunk_limit():
    """Test MAX_CHUNK_LIMIT is set correctly."""
    assert MAX_CHUNK_LIMIT == 100
