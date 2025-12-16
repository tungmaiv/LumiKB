"""Unit tests for KBStatsService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.knowledge_base import KnowledgeBase
from app.schemas.kb_stats import KBDetailedStats, TopDocument
from app.services.kb_stats_service import KBStatsService


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    session.scalar = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_minio_service():
    """Create a mock MinIOService."""
    return AsyncMock()


@pytest.fixture
def mock_qdrant_service():
    """Create a mock QdrantService."""
    return AsyncMock()


@pytest.fixture
def kb_stats_service(mock_session, mock_minio_service, mock_qdrant_service):
    """Create KBStatsService with mocked dependencies."""
    return KBStatsService(mock_session, mock_minio_service, mock_qdrant_service)


@pytest.fixture
def sample_kb_id():
    """Sample Knowledge Base UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_kb(sample_kb_id):
    """Sample Knowledge Base model for testing."""
    kb = MagicMock(spec=KnowledgeBase)
    kb.id = sample_kb_id
    kb.name = "Test KB"
    return kb


@pytest.mark.asyncio
async def test_get_kb_stats_cache_hit(kb_stats_service, mock_session, sample_kb_id):
    """Test that cache hit returns cached data without queries."""
    cached_stats = KBDetailedStats(
        kb_id=sample_kb_id,
        kb_name="Test KB",
        document_count=42,
        storage_bytes=104857600,
        total_chunks=1250,
        total_embeddings=1250,
        searches_30d=285,
        generations_30d=98,
        unique_users_30d=12,
        top_documents=[
            TopDocument(id=uuid4(), filename="doc1.pdf", access_count=50),
            TopDocument(id=uuid4(), filename="doc2.md", access_count=40),
        ],
        last_updated=datetime.now(UTC),
    )

    with patch("app.services.kb_stats_service.get_redis_client") as mock_redis_client:
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached_stats.model_dump_json())
        mock_redis_client.return_value = mock_redis

        result = await kb_stats_service.get_kb_stats(sample_kb_id)

        # Verify cache hit
        cache_key = f"kb:stats:{sample_kb_id}"
        mock_redis.get.assert_called_once_with(cache_key)
        # Verify no DB queries made
        mock_session.scalar.assert_not_called()
        # Verify result matches cached data
        assert result.kb_id == sample_kb_id
        assert result.kb_name == "Test KB"
        assert result.document_count == 42


@pytest.mark.asyncio
async def test_get_kb_stats_cache_miss(
    kb_stats_service,
    mock_session,
    mock_minio_service,
    mock_qdrant_service,
    sample_kb_id,
    sample_kb,
):
    """Test that cache miss triggers aggregation from all sources."""
    with patch("app.services.kb_stats_service.get_redis_client") as mock_redis_client:
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # Cache miss
        mock_redis.setex = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # Mock KB lookup
        mock_session.scalar.side_effect = [
            sample_kb,  # KB exists
            42,  # document_count
            285,  # searches_30d
            98,  # generations_30d
            12,  # unique_users_30d
        ]

        # Mock execute for storage query and top documents query
        storage_result = MagicMock()
        storage_result.all.return_value = [
            MagicMock(file_size_bytes=52428800),  # 50MB
            MagicMock(file_size_bytes=52428800),  # 50MB
        ]

        top_docs_result = MagicMock()
        top_docs_result.all.return_value = []  # No top documents

        mock_session.execute.side_effect = [storage_result, top_docs_result]

        # Mock Qdrant collection info
        mock_qdrant_service.get_collection_info.return_value = {
            "points_count": 1250,
            "vectors_count": 1250,
        }

        result = await kb_stats_service.get_kb_stats(sample_kb_id)

        # Verify cache miss and set
        cache_key = f"kb:stats:{sample_kb_id}"
        mock_redis.get.assert_called_once_with(cache_key)
        mock_redis.setex.assert_called_once()
        assert mock_redis.setex.call_args[0][0] == cache_key
        assert mock_redis.setex.call_args[0][1] == 600  # 10 minutes TTL

        # Verify aggregated results
        assert result.kb_id == sample_kb_id
        assert result.kb_name == "Test KB"
        assert result.document_count == 42
        assert result.storage_bytes == 104857600  # 100MB
        assert result.total_chunks == 1250
        assert result.total_embeddings == 1250
        assert result.searches_30d == 285
        assert result.generations_30d == 98
        assert result.unique_users_30d == 12


@pytest.mark.asyncio
async def test_get_kb_stats_kb_not_found(kb_stats_service, mock_session, sample_kb_id):
    """Test that ValueError raised if KB not found."""
    with patch("app.services.kb_stats_service.get_redis_client") as mock_redis_client:
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # Cache miss
        mock_redis_client.return_value = mock_redis

        # Mock KB not found
        mock_session.scalar.return_value = None

        with pytest.raises(
            ValueError, match=f"Knowledge base not found: {sample_kb_id}"
        ):
            await kb_stats_service.get_kb_stats(sample_kb_id)


@pytest.mark.asyncio
async def test_get_storage_bytes_graceful_degradation(
    kb_stats_service, mock_session, sample_kb_id
):
    """Test graceful degradation if storage query fails."""
    # Mock execute raising exception
    mock_session.execute.side_effect = Exception("Database error")

    result = await kb_stats_service._get_storage_bytes(sample_kb_id)

    # Should return 0 instead of raising
    assert result == 0


@pytest.mark.asyncio
async def test_get_vector_metrics_graceful_degradation(
    kb_stats_service, mock_qdrant_service, sample_kb_id
):
    """Test graceful degradation if Qdrant query fails."""
    # Mock Qdrant raising exception
    mock_qdrant_service.get_collection_info.side_effect = Exception(
        "Qdrant unavailable"
    )

    result = await kb_stats_service._get_vector_metrics(sample_kb_id)

    # Should return (0, 0) instead of raising
    assert result == (0, 0)


@pytest.mark.asyncio
async def test_get_usage_metrics_empty_audit_events(
    kb_stats_service, mock_session, sample_kb_id
):
    """Test usage metrics with no audit events."""
    # Mock audit.events queries returning 0
    mock_session.scalar.side_effect = [0, 0, 0]

    result = await kb_stats_service._get_usage_metrics(sample_kb_id)

    # Should return (0, 0, 0)
    assert result == (0, 0, 0)


@pytest.mark.asyncio
async def test_get_top_documents_empty_results(
    kb_stats_service, mock_session, sample_kb_id
):
    """Test top documents with no audit events."""
    mock_execute_result = MagicMock()
    mock_execute_result.all.return_value = []
    mock_session.execute.return_value = mock_execute_result

    result = await kb_stats_service._get_top_documents(sample_kb_id)

    # Should return empty list
    assert result == []


@pytest.mark.asyncio
async def test_redis_unavailable_graceful_fallback(
    kb_stats_service, mock_session, mock_qdrant_service, sample_kb_id, sample_kb
):
    """Test that service falls back to DB aggregation if Redis unavailable."""
    with patch("app.services.kb_stats_service.get_redis_client") as mock_redis_client:
        # Simulate Redis connection failure
        mock_redis_client.side_effect = Exception("Redis unavailable")

        # Mock KB lookup and stats
        mock_session.scalar.side_effect = [
            sample_kb,  # KB exists
            10,  # document_count
            50,  # searches_30d
            20,  # generations_30d
            5,  # unique_users_30d
        ]

        # Mock execute for storage query and top documents query
        storage_result = MagicMock()
        storage_result.all.return_value = []

        top_docs_result = MagicMock()
        top_docs_result.all.return_value = []

        mock_session.execute.side_effect = [storage_result, top_docs_result]

        # Mock Qdrant collection info
        mock_qdrant_service.get_collection_info.return_value = {
            "points_count": 100,
            "vectors_count": 100,
        }

        # Should not raise, should aggregate from DB
        result = await kb_stats_service.get_kb_stats(sample_kb_id)

        assert result.kb_id == sample_kb_id
        assert result.document_count == 10
