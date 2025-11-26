"""Unit tests for SearchService (Story 3.1 - Task 4)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.search import QuickSearchResponse, SearchResponse
from app.services.search_service import SearchService

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_permission_service():
    """Mock KBPermissionService."""
    service = AsyncMock()
    service.get_permitted_kb_ids.return_value = ["kb-123", "kb-456"]
    service.check_permission.return_value = True
    return service


@pytest.fixture
def mock_audit_service():
    """Mock AuditService."""
    service = AsyncMock()
    service.log_search.return_value = None
    return service


@pytest.fixture
def search_service(mock_permission_service, mock_audit_service):
    """SearchService instance with mocked dependencies."""
    with patch("app.services.search_service.qdrant_service") as mock_qdrant:
        mock_qdrant.get_client.return_value = MagicMock()
        service = SearchService(
            permission_service=mock_permission_service,
            audit_service=mock_audit_service,
        )
        return service


# =============================================================================
# Task 4.2: Test _embed_query() with mocked LiteLLM client
# =============================================================================


@pytest.mark.asyncio
async def test_embed_query_generates_embedding(search_service):
    """Test _embed_query generates embedding via LiteLLM."""
    query = "test query"
    expected_embedding = [0.1, 0.2, 0.3]

    with patch("app.services.search_service.embedding_client") as mock_client:
        mock_client.get_embeddings = AsyncMock(return_value=[expected_embedding])

        with patch("app.services.search_service.RedisClient.get_client") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None  # Cache miss
            mock_redis_instance.setex = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            result = await search_service._embed_query(query)

            assert result == expected_embedding
            mock_client.get_embeddings.assert_called_once_with([query])
            mock_redis_instance.setex.assert_called_once()


@pytest.mark.asyncio
async def test_embed_query_raises_connection_error_on_litellm_failure(search_service):
    """Test _embed_query raises ConnectionError when LiteLLM fails."""
    query = "test query"

    with patch("app.services.search_service.embedding_client") as mock_client:
        mock_client.get_embeddings = AsyncMock(side_effect=Exception("LiteLLM error"))

        with patch("app.services.search_service.RedisClient.get_client") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis.return_value = mock_redis_instance

            with pytest.raises(ConnectionError, match="Embedding service unavailable"):
                await search_service._embed_query(query)


# =============================================================================
# Task 4.6: Test Redis cache hit/miss scenarios
# =============================================================================


@pytest.mark.asyncio
async def test_embed_query_cache_hit(search_service):
    """Test _embed_query returns cached embedding on cache hit."""
    query = "cached query"
    cached_embedding = [0.4, 0.5, 0.6]

    with patch("app.services.search_service.RedisClient.get_client") as mock_redis:
        mock_redis_instance = AsyncMock()
        mock_redis_instance.get.return_value = json.dumps(cached_embedding)
        mock_redis.return_value = mock_redis_instance

        result = await search_service._embed_query(query)

        assert result == cached_embedding
        mock_redis_instance.get.assert_called_once()


@pytest.mark.asyncio
async def test_embed_query_cache_miss_stores_result(search_service):
    """Test _embed_query stores result in Redis on cache miss."""
    query = "new query"
    embedding = [0.7, 0.8, 0.9]

    with patch("app.services.search_service.embedding_client") as mock_client:
        mock_client.get_embeddings = AsyncMock(return_value=[embedding])

        with patch("app.services.search_service.RedisClient.get_client") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.setex = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            await search_service._embed_query(query)

            # Verify cache was populated with 1-hour TTL (3600s)
            mock_redis_instance.setex.assert_called_once()
            call_args = mock_redis_instance.setex.call_args[0]
            assert call_args[1] == 3600  # TTL


# =============================================================================
# Task 4.3: Test _search_collections() with mocked Qdrant client
# =============================================================================


@pytest.mark.asyncio
async def test_search_collections_returns_chunks(search_service):
    """Test _search_collections returns chunks from Qdrant."""
    embedding = [0.1, 0.2, 0.3]
    kb_ids = ["kb-123"]
    limit = 10

    # Mock Qdrant search result
    mock_result = MagicMock()
    mock_result.score = 0.95
    mock_result.payload = {
        "document_id": "doc-1",
        "document_name": "test.pdf",
        "chunk_text": "Test content",
        "page_number": 1,
        "section_header": "Introduction",
        "char_start": 0,
        "char_end": 100,
    }

    search_service.qdrant_client = MagicMock()
    search_service.qdrant_client.search.return_value = [mock_result]

    chunks = await search_service._search_collections(embedding, kb_ids, limit)

    assert len(chunks) == 1
    assert chunks[0]["kb_id"] == "kb-123"
    assert chunks[0]["score"] == 0.95
    assert chunks[0]["document_id"] == "doc-1"
    assert chunks[0]["char_start"] == 0
    assert chunks[0]["char_end"] == 100


@pytest.mark.asyncio
async def test_search_collections_sorts_by_relevance(search_service):
    """Test _search_collections sorts results by relevance score."""
    embedding = [0.1, 0.2, 0.3]
    kb_ids = ["kb-123", "kb-456"]
    limit = 10

    # Mock results from two KBs with different scores
    mock_result1 = MagicMock()
    mock_result1.score = 0.7
    mock_result1.payload = {
        "document_id": "doc-1",
        "document_name": "test1.pdf",
        "chunk_text": "Content 1",
        "char_start": 0,
        "char_end": 50,
    }

    mock_result2 = MagicMock()
    mock_result2.score = 0.9
    mock_result2.payload = {
        "document_id": "doc-2",
        "document_name": "test2.pdf",
        "chunk_text": "Content 2",
        "char_start": 0,
        "char_end": 50,
    }

    search_service.qdrant_client = MagicMock()
    search_service.qdrant_client.search.side_effect = [
        [mock_result1],  # First KB
        [mock_result2],  # Second KB
    ]

    chunks = await search_service._search_collections(embedding, kb_ids, limit)

    # Should be sorted by score descending
    assert chunks[0]["score"] == 0.9
    assert chunks[1]["score"] == 0.7


# =============================================================================
# Task 4.5: Test Qdrant unavailable returns 503 error
# =============================================================================


@pytest.mark.asyncio
async def test_search_collections_raises_connection_error_on_qdrant_failure(
    search_service,
):
    """Test _search_collections raises ConnectionError when Qdrant fails."""
    embedding = [0.1, 0.2, 0.3]
    kb_ids = ["kb-123"]
    limit = 10

    search_service.qdrant_client = MagicMock()
    search_service.qdrant_client.search.side_effect = Exception("Qdrant error")

    with pytest.raises(ConnectionError, match="Vector search unavailable"):
        await search_service._search_collections(embedding, kb_ids, limit)


# =============================================================================
# Task 4.4: Test empty results scenario returns empty array with message
# =============================================================================


@pytest.mark.asyncio
async def test_search_returns_empty_results_with_message(search_service):
    """Test search returns empty array and helpful message when no results."""
    query = "no matches query"
    kb_ids = ["kb-123"]
    user_id = "user-1"

    with patch("app.services.search_service.embedding_client") as mock_client:
        mock_client.get_embeddings = AsyncMock(return_value=[[0.1, 0.2]])

        with patch("app.services.search_service.RedisClient.get_client") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.setex = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            search_service.qdrant_client = MagicMock()
            search_service.qdrant_client.search.return_value = []  # No results

            response = await search_service.search(query, kb_ids, user_id, limit=10)

            assert isinstance(response, SearchResponse)
            assert response.result_count == 0
            assert len(response.results) == 0
            assert "No relevant documents found" in response.message


# =============================================================================
# Integration with permission and audit services
# =============================================================================


@pytest.mark.asyncio
async def test_search_checks_permissions_before_search(
    search_service, mock_permission_service
):
    """Test search checks permissions before executing query."""
    query = "test"
    kb_ids = ["kb-123"]
    user_id = "user-1"

    mock_permission_service.check_permission.return_value = False

    with pytest.raises(PermissionError):
        await search_service.search(query, kb_ids, user_id)

    mock_permission_service.check_permission.assert_called_once_with(
        user_id, "kb-123", "READ"
    )


@pytest.mark.asyncio
async def test_search_logs_audit_event(search_service, mock_audit_service):
    """Test search logs audit event after completion."""
    query = "audit test"
    kb_ids = ["kb-123"]
    user_id = "user-1"

    with patch("app.services.search_service.embedding_client") as mock_client:
        mock_client.get_embeddings = AsyncMock(return_value=[[0.1, 0.2]])

        with patch("app.services.search_service.RedisClient.get_client") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.setex = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            search_service.qdrant_client = MagicMock()
            search_service.qdrant_client.search.return_value = []

            await search_service.search(query, kb_ids, user_id)

            mock_audit_service.log_search.assert_called_once()
            call_args = mock_audit_service.log_search.call_args[1]
            assert call_args["query"] == query
            assert call_args["kb_ids"] == kb_ids
            assert call_args["result_count"] == 0


# =============================================================================
# Story 3.2: Answer Synthesis with Citations Unit Tests
# =============================================================================


@pytest.mark.asyncio
async def test_synthesize_answer_calls_llm_with_correct_format(search_service):
    """AC1: _synthesize_answer calls LLM with citation instructions and chunks."""
    from app.schemas.search import SearchResultSchema

    query = "What is OAuth 2.0?"
    chunks = [
        SearchResultSchema(
            document_id="doc-1",
            document_name="OAuth Guide.pdf",
            kb_id="kb-1",
            kb_name="Tech KB",
            chunk_text="OAuth 2.0 is an authorization framework.",
            relevance_score=0.92,
            page_number=3,
            section_header="Introduction",
            char_start=100,
            char_end=200,
        )
    ]

    with patch("app.services.search_service.embedding_client") as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = "OAuth 2.0 [1] is an authorization framework."
        mock_client.chat_completion = AsyncMock(return_value=mock_response)

        answer = await search_service._synthesize_answer(query, chunks)

        assert answer == "OAuth 2.0 [1] is an authorization framework."
        mock_client.chat_completion.assert_called_once()
        call_args = mock_client.chat_completion.call_args[1]
        assert call_args["temperature"] == 0.3  # Low temp for deterministic citations
        assert call_args["max_tokens"] == 500


@pytest.mark.asyncio
async def test_calculate_confidence_with_high_relevance_chunks(search_service):
    """AC4: _calculate_confidence returns high score for high relevance chunks."""
    from app.schemas.search import SearchResultSchema

    chunks = [
        SearchResultSchema(
            document_id="doc-1",
            document_name="Test.pdf",
            kb_id="kb-1",
            kb_name="KB",
            chunk_text="test",
            relevance_score=0.9,
            page_number=1,
            section_header="Test",
            char_start=0,
            char_end=4,
        ),
        SearchResultSchema(
            document_id="doc-2",
            document_name="Test2.pdf",
            kb_id="kb-1",
            kb_name="KB",
            chunk_text="test2",
            relevance_score=0.85,
            page_number=2,
            section_header="Test",
            char_start=0,
            char_end=5,
        ),
    ]

    confidence = search_service._calculate_confidence(chunks, "test query")

    # With 2 chunks at 0.9 and 0.85, average = 0.875
    # Source count score = min(2/3, 1.0) = 0.67
    # Formula: 0.875*0.4 + 0.67*0.3 + 0.875*0.3 = 0.35 + 0.2 + 0.26 = 0.81
    assert confidence > 0.8
    assert confidence <= 1.0


@pytest.mark.asyncio
async def test_calculate_confidence_with_single_chunk(search_service):
    """AC4: _calculate_confidence returns moderate score for single chunk."""
    from app.schemas.search import SearchResultSchema

    chunks = [
        SearchResultSchema(
            document_id="doc-1",
            document_name="Test.pdf",
            kb_id="kb-1",
            kb_name="KB",
            chunk_text="test",
            relevance_score=0.9,
            page_number=1,
            section_header="Test",
            char_start=0,
            char_end=4,
        )
    ]

    confidence = search_service._calculate_confidence(chunks, "test query")

    # Single chunk: source_count_score = 1/3 = 0.33
    # Formula: 0.9*0.4 + 0.33*0.3 + 0.9*0.3 = 0.36 + 0.099 + 0.27 = 0.729
    assert 0.6 < confidence < 0.8  # Moderate confidence


@pytest.mark.asyncio
async def test_calculate_confidence_empty_chunks_returns_zero(search_service):
    """AC4: _calculate_confidence returns 0 for empty chunks."""
    confidence = search_service._calculate_confidence([], "test query")
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_search_with_answer_synthesis_success(search_service):
    """AC5: Full search with answer synthesis and citations."""

    query = "What is OAuth 2.0?"
    kb_ids = ["kb-123"]
    user_id = "user-1"

    with patch("app.services.search_service.embedding_client") as mock_embed_client:
        mock_embed_client.get_embeddings = AsyncMock(return_value=[[0.1, 0.2]])

        # Mock chat completion for answer synthesis
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = "OAuth 2.0 [1] is an authorization framework."
        mock_embed_client.chat_completion = AsyncMock(return_value=mock_response)

        with patch("app.services.search_service.RedisClient.get_client") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.setex = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            # Mock Qdrant results
            search_service.qdrant_client = MagicMock()
            mock_result = MagicMock()
            mock_result.score = 0.92
            mock_result.payload = {
                "document_id": "doc-1",
                "document_name": "OAuth Guide.pdf",
                "chunk_text": "OAuth 2.0 is an authorization framework.",
                "page_number": 3,
                "section_header": "Introduction",
                "char_start": 100,
                "char_end": 200,
                "kb_name": "Tech KB",
            }
            search_service.qdrant_client.search.return_value = [mock_result]

            response = await search_service.search(query, kb_ids, user_id, limit=10)

            assert isinstance(response, SearchResponse)
            assert response.answer == "OAuth 2.0 [1] is an authorization framework."
            assert len(response.citations) == 1
            assert response.citations[0].number == 1
            assert response.citations[0].document_name == "OAuth Guide.pdf"
            assert response.confidence > 0
            assert response.result_count == 1


@pytest.mark.asyncio
async def test_search_synthesis_failure_graceful_degradation(search_service):
    """AC7, AC8: If synthesis fails, return raw results without answer."""
    query = "test"
    kb_ids = ["kb-123"]
    user_id = "user-1"

    with patch("app.services.search_service.embedding_client") as mock_client:
        mock_client.get_embeddings = AsyncMock(return_value=[[0.1, 0.2]])
        mock_client.chat_completion = AsyncMock(side_effect=Exception("LLM error"))

        with patch("app.services.search_service.RedisClient.get_client") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis_instance.setex = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            # Mock Qdrant results
            search_service.qdrant_client = MagicMock()
            mock_result = MagicMock()
            mock_result.score = 0.92
            mock_result.payload = {
                "document_id": "doc-1",
                "document_name": "Test.pdf",
                "chunk_text": "test",
                "page_number": 1,
                "section_header": "Test",
                "char_start": 0,
                "char_end": 4,
                "kb_name": "KB",
            }
            search_service.qdrant_client.search.return_value = [mock_result]

            response = await search_service.search(query, kb_ids, user_id)

            # Should succeed with raw results, no answer/citations
            assert isinstance(response, SearchResponse)
            assert response.answer == ""  # Empty answer on failure
            assert response.citations == []  # Empty citations
            assert response.confidence == 0.0
            assert response.result_count == 1  # Raw results still returned


# =============================================================================
# Story 3.7: Test quick_search() method
# =============================================================================


@pytest.mark.asyncio
async def test_quick_search_returns_top_5_results(
    search_service, mock_permission_service
):
    """Test quick_search returns top 5 results without LLM synthesis (AC2)."""
    query = "test query"
    kb_ids = None  # Cross-KB search
    user_id = "user-1"

    # Mock permission check
    mock_permission_service.get_permitted_kb_ids.return_value = ["kb-123"]

    with (
        patch("app.services.search_service.embedding_client") as mock_client,
        patch("app.services.search_service.RedisClient.get_client") as mock_redis,
    ):
        # Mock embedding
        mock_client.get_embeddings = AsyncMock(return_value=[[0.1] * 1536])

        # Mock Redis (no cache)
        mock_redis_instance = AsyncMock()
        mock_redis_instance.get.return_value = None
        mock_redis_instance.setex = AsyncMock()
        mock_redis.return_value = mock_redis_instance

        # Mock Qdrant results (5 results)
        search_service.qdrant_client = MagicMock()
        mock_results = []
        for i in range(5):
            mock_result = MagicMock()
            mock_result.score = 0.9 - (i * 0.1)
            mock_result.payload = {
                "document_id": f"doc-{i}",
                "document_name": f"Test{i}.pdf",
                "chunk_text": f"This is test chunk {i} with some content here.",
                "page_number": i + 1,
                "section_header": f"Section {i}",
                "char_start": 0,
                "char_end": 50,
                "kb_name": "Test KB",
                "kb_id": "kb-123",
            }
            mock_results.append(mock_result)
        search_service.qdrant_client.search.return_value = mock_results

        response = await search_service.quick_search(query, kb_ids, user_id)

        # Assertions
        assert isinstance(response, QuickSearchResponse)
        assert response.query == query
        assert len(response.results) == 5  # Top 5 only
        assert response.kb_count == 1
        assert response.response_time_ms > 0

        # Verify result structure
        first_result = response.results[0]
        assert first_result.document_id == "doc-0"
        assert first_result.document_name == "Test0.pdf"
        assert first_result.kb_id == "kb-123"
        assert first_result.kb_name == "Test KB"
        assert first_result.relevance_score == 0.9
        assert len(first_result.excerpt) <= 103  # 100 chars + "..."


@pytest.mark.asyncio
async def test_quick_search_truncates_excerpt(search_service, mock_permission_service):
    """Test quick_search truncates excerpts to 100 characters (AC2)."""
    query = "test"
    user_id = "user-1"

    mock_permission_service.get_permitted_kb_ids.return_value = ["kb-123"]

    with (
        patch("app.services.search_service.embedding_client") as mock_client,
        patch("app.services.search_service.RedisClient.get_client") as mock_redis,
    ):
        mock_client.get_embeddings = AsyncMock(return_value=[[0.1] * 1536])
        mock_redis_instance = AsyncMock()
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance

        # Mock result with long chunk_text
        search_service.qdrant_client = MagicMock()
        mock_result = MagicMock()
        mock_result.score = 0.95
        long_text = "a" * 200  # 200 characters
        mock_result.payload = {
            "document_id": "doc-1",
            "document_name": "Test.pdf",
            "chunk_text": long_text,
            "kb_id": "kb-123",
            "kb_name": "KB",
        }
        search_service.qdrant_client.search.return_value = [mock_result]

        response = await search_service.quick_search(query, None, user_id)

        # Excerpt should be truncated
        assert len(response.results[0].excerpt) == 103  # 100 chars + "..."
        assert response.results[0].excerpt.endswith("...")


@pytest.mark.asyncio
async def test_quick_search_respects_permissions(
    search_service, mock_permission_service
):
    """Test quick_search respects user permissions (AC2)."""
    query = "test"
    kb_ids = ["kb-restricted"]
    user_id = "user-1"

    # User only has access to kb-123, not kb-restricted
    mock_permission_service.get_permitted_kb_ids.return_value = ["kb-123"]
    mock_permission_service.check_permission = AsyncMock(
        return_value=False
    )  # No access

    # Should raise PermissionError
    with pytest.raises(PermissionError, match="Knowledge Base not found"):
        await search_service.quick_search(query, kb_ids, user_id)


@pytest.mark.asyncio
async def test_quick_search_cross_kb_default(search_service, mock_permission_service):
    """Test quick_search defaults to cross-KB when kb_ids is None (AC6)."""
    query = "test"
    user_id = "user-1"

    # User has access to multiple KBs
    mock_permission_service.get_permitted_kb_ids.return_value = ["kb-1", "kb-2", "kb-3"]

    with (
        patch("app.services.search_service.embedding_client") as mock_client,
        patch("app.services.search_service.RedisClient.get_client") as mock_redis,
    ):
        mock_client.get_embeddings = AsyncMock(return_value=[[0.1] * 1536])
        mock_redis_instance = AsyncMock()
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance

        search_service.qdrant_client = MagicMock()
        search_service.qdrant_client.search.return_value = []  # No results

        response = await search_service.quick_search(
            query, None, user_id
        )  # kb_ids=None

        # Should search all 3 KBs
        assert response.kb_count == 3
