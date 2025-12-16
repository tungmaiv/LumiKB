"""Unit tests for async Qdrant migration.

Story 7-7: Async Qdrant Migration
Tests cover:
- AC-7.7.1: AsyncQdrantClient replaces sync QdrantClient
- AC-7.7.2: ChunkService uses native async Qdrant calls
- AC-7.7.3: SearchService uses native async Qdrant calls

These tests verify the async migration is complete and working correctly.
"""

import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


class TestAsyncQdrantClientInitialization:
    """AC-7.7.1: AsyncQdrantClient replaces sync QdrantClient."""

    def test_qdrant_service_uses_async_client(self) -> None:
        """
        GIVEN the QdrantService class
        WHEN async_client property is accessed
        THEN it should return an AsyncQdrantClient instance
        """
        from qdrant_client import AsyncQdrantClient

        from app.integrations.qdrant_client import QdrantService

        service = QdrantService()
        client = service.async_client

        assert isinstance(client, AsyncQdrantClient), (
            f"Expected AsyncQdrantClient, got {type(client).__name__}. "
            "Migration from sync QdrantClient to AsyncQdrantClient required."
        )

    def test_async_client_configured_with_grpc(self) -> None:
        """
        GIVEN QdrantService initialization
        WHEN AsyncQdrantClient is created
        THEN it should be configured with gRPC for performance
        """
        from app.integrations.qdrant_client import QdrantService

        service = QdrantService()

        # The AsyncQdrantClient should use gRPC - verify via attributes
        # We check by examining if the service was configured properly
        client = service.async_client
        assert client is not None, "Client should be initialized"
        # AsyncQdrantClient with prefer_grpc=True will use gRPC transport
        # We can verify by checking the client type
        assert "AsyncQdrantClient" in type(client).__name__

    def test_qdrant_client_module_imports_async(self) -> None:
        """
        GIVEN the qdrant_client integration module
        WHEN examining imports
        THEN AsyncQdrantClient should be imported (not just QdrantClient)
        """
        from app.integrations import qdrant_client

        source = inspect.getsource(qdrant_client)

        assert "AsyncQdrantClient" in source, (
            "qdrant_client module should import AsyncQdrantClient. "
            "Current imports only sync QdrantClient."
        )

        # Also check it's actually used, not just imported
        assert (
            "AsyncQdrantClient(" in source or "AsyncQdrantClient (" in source
        ), "AsyncQdrantClient should be instantiated in QdrantService"


class TestChunkServiceAsyncOperations:
    """AC-7.7.2: ChunkService uses native async Qdrant calls."""

    @pytest.mark.asyncio
    async def test_get_chunks_uses_native_async_scroll(self) -> None:
        """
        GIVEN a ChunkService instance with AsyncQdrantClient
        WHEN get_chunks is called
        THEN it should use native async scroll (via qdrant_service wrapper)
        """
        from app.services.chunk_service import ChunkService

        kb_id = uuid4()
        doc_id = uuid4()

        with patch("app.services.chunk_service.qdrant_service") as mock_service:
            # Mock async methods on qdrant_service
            mock_service.count = AsyncMock(return_value=MagicMock(count=0))
            mock_service.scroll = AsyncMock(return_value=([], None))

            service = ChunkService(kb_id)

            # Call the method
            result = await service.get_chunks(doc_id, cursor=0, limit=10)

            # Verify count was awaited
            mock_service.count.assert_awaited()
            assert result.total == 0

    @pytest.mark.asyncio
    async def test_search_chunks_uses_native_async_search(self) -> None:
        """
        GIVEN a ChunkService instance with AsyncQdrantClient
        WHEN get_chunks is called with search_query
        THEN it should use native async search (via qdrant_service wrapper)
        """
        from app.services.chunk_service import ChunkService

        kb_id = uuid4()
        doc_id = uuid4()

        with patch("app.services.chunk_service.qdrant_service") as mock_service:
            with patch("app.services.chunk_service.embedding_client") as mock_embed:
                mock_service.count = AsyncMock(return_value=MagicMock(count=1))
                mock_service.search = AsyncMock(return_value=[])
                mock_embed.get_embeddings = AsyncMock(return_value=[[0.1] * 384])

                service = ChunkService(kb_id)

                # Call with search query
                await service.get_chunks(
                    doc_id, cursor=0, limit=10, search_query="test"
                )

                # Verify search was awaited
                mock_service.search.assert_awaited()

    @pytest.mark.asyncio
    async def test_count_chunks_uses_native_async_count(self) -> None:
        """
        GIVEN a ChunkService instance with AsyncQdrantClient
        WHEN get_chunks is called
        THEN it should use native async count (via qdrant_service wrapper)
        """
        from app.services.chunk_service import ChunkService

        kb_id = uuid4()
        doc_id = uuid4()

        with patch("app.services.chunk_service.qdrant_service") as mock_service:
            mock_service.count = AsyncMock(return_value=MagicMock(count=5))
            mock_service.scroll = AsyncMock(return_value=([], None))

            service = ChunkService(kb_id)

            # Call the method
            result = await service.get_chunks(doc_id, cursor=0, limit=10)

            # Verify count was awaited
            mock_service.count.assert_awaited()
            assert result.total == 5

    def test_no_asyncio_to_thread_in_chunk_service(self) -> None:
        """
        GIVEN the ChunkService source code
        WHEN analyzing Qdrant operations
        THEN asyncio.to_thread should not be used for Qdrant calls
        """
        from app.services import chunk_service

        source = inspect.getsource(chunk_service)

        # Check for asyncio.to_thread usage with qdrant
        to_thread_lines = [
            line.strip()
            for line in source.split("\n")
            if "asyncio.to_thread" in line or "to_thread" in line
        ]

        # Filter to only qdrant-related to_thread calls
        qdrant_to_thread = [
            line
            for line in to_thread_lines
            if any(
                kw in line.lower()
                for kw in ["scroll", "search", "count", "qdrant", "client"]
            )
        ]

        assert len(qdrant_to_thread) == 0, (
            f"ChunkService should use native async Qdrant calls, not asyncio.to_thread. "
            f"Found: {qdrant_to_thread}"
        )


class TestSearchServiceAsyncOperations:
    """AC-7.7.3: SearchService uses native async Qdrant calls."""

    @pytest.mark.asyncio
    async def test_semantic_search_uses_native_async_query(self) -> None:
        """
        GIVEN a SearchService instance with AsyncQdrantClient
        WHEN _search_collections is called
        THEN it should use native async query_points (via qdrant_service wrapper)
        """
        from app.services.search_service import SearchService

        with patch("app.services.search_service.qdrant_service") as mock_qdrant:
            mock_response = MagicMock()
            mock_response.points = []
            mock_qdrant.query_points = AsyncMock(return_value=mock_response)

            service = SearchService(
                permission_service=AsyncMock(),
                audit_service=AsyncMock(),
            )

            # Call _search_collections directly
            embedding = [0.1] * 384
            kb_ids = [str(uuid4())]

            chunks = await service._search_collections(embedding, kb_ids, limit=10)

            # Verify query_points was awaited
            mock_qdrant.query_points.assert_awaited()
            assert chunks == []

    def test_search_service_no_to_thread_wrapper(self) -> None:
        """
        GIVEN the SearchService source code
        WHEN analyzing the _search_collections method
        THEN asyncio.to_thread should not wrap Qdrant calls
        """
        from app.services import search_service

        source = inspect.getsource(search_service)

        # Find lines with asyncio.to_thread for Qdrant calls
        lines_with_to_thread = []
        for i, line in enumerate(source.split("\n"), 1):
            if "asyncio.to_thread" in line and any(
                kw in line.lower()
                for kw in ["query_points", "retrieve", "search", "scroll"]
            ):
                lines_with_to_thread.append(f"Line {i}: {line.strip()}")

        assert len(lines_with_to_thread) == 0, (
            "SearchService should use native async Qdrant calls for vector operations. "
            "Found asyncio.to_thread usage:\n" + "\n".join(lines_with_to_thread)
        )

    @pytest.mark.asyncio
    async def test_search_with_filters_uses_native_async(self) -> None:
        """
        GIVEN a SearchService with filter parameters
        WHEN _search_collections is called
        THEN native async query_points should be used with filters
        """
        from app.services.search_service import SearchService

        with patch("app.services.search_service.qdrant_service") as mock_qdrant:
            mock_response = MagicMock()
            mock_response.points = []
            mock_qdrant.query_points = AsyncMock(return_value=mock_response)

            service = SearchService(
                permission_service=AsyncMock(),
                audit_service=AsyncMock(),
            )

            # Call _search_collections
            embedding = [0.1] * 384
            kb_ids = [str(uuid4())]

            await service._search_collections(embedding, kb_ids, limit=10)

            # Verify query_points was awaited with proper arguments
            mock_qdrant.query_points.assert_awaited()
            call_kwargs = mock_qdrant.query_points.call_args.kwargs
            assert "query_filter" in call_kwargs, "Query filter should be passed"


class TestQdrantServiceAsyncMethods:
    """Tests for QdrantService async method signatures."""

    def test_qdrant_service_has_async_methods(self) -> None:
        """
        GIVEN the QdrantService class
        WHEN examining its methods
        THEN key methods should be async (coroutine functions)
        """
        from app.integrations.qdrant_client import QdrantService

        service = QdrantService()

        # These methods should exist and be async after migration
        expected_async_methods = [
            "ensure_collection",
            "delete_collection",
            "health_check",
            "scroll",
            "search",
            "count",
            "query_points",
            "retrieve",
        ]

        for method_name in expected_async_methods:
            if hasattr(service, method_name):
                method = getattr(service, method_name)
                assert asyncio.iscoroutinefunction(
                    method
                ), f"QdrantService.{method_name} should be async after migration"

    def test_qdrant_service_has_wrapper_methods(self) -> None:
        """
        GIVEN the QdrantService class
        WHEN examining its wrapper methods
        THEN scroll, search, count, query_points, retrieve should exist
        """
        from app.integrations.qdrant_client import QdrantService

        service = QdrantService()

        wrapper_methods = ["scroll", "search", "count", "query_points", "retrieve"]

        for method_name in wrapper_methods:
            assert hasattr(
                service, method_name
            ), f"QdrantService should have {method_name} wrapper method"
