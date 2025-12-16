# ATDD Checklist: Story 7-7 Async Qdrant Migration

**Story ID:** 7-7
**Title:** Async Qdrant Migration
**Date:** 2025-12-09
**Phase:** RED (Failing Tests First)

## Story Summary

Migrate from synchronous `QdrantClient` to `AsyncQdrantClient` for true non-blocking vector operations. This eliminates the thread pool bottleneck from `asyncio.to_thread()` wrappers and enables native async/await patterns throughout the Qdrant integration layer.

## Acceptance Criteria Overview

| AC | Description | Test Level | Status |
|----|-------------|------------|--------|
| AC-7.7.1 | AsyncQdrantClient replaces sync QdrantClient | Unit | RED |
| AC-7.7.2 | ChunkService uses native async Qdrant calls | Unit + Integration | RED |
| AC-7.7.3 | SearchService uses native async Qdrant calls | Unit + Integration | RED |
| AC-7.7.4 | 100 concurrent requests with consistent response times | Load/Performance | RED |

---

## AC-7.7.1: AsyncQdrantClient Initialization

### Requirement
AsyncQdrantClient from `qdrant_client` replaces synchronous QdrantClient for all vector operations.

### Test Level: Unit

### Failing Tests

#### Test 1.1: QdrantService uses AsyncQdrantClient
```python
# File: backend/tests/unit/test_async_qdrant.py

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from qdrant_client import AsyncQdrantClient

pytestmark = pytest.mark.unit


class TestAsyncQdrantClientInitialization:
    """AC-7.7.1: AsyncQdrantClient replaces sync QdrantClient."""

    def test_qdrant_service_uses_async_client(self) -> None:
        """
        GIVEN the QdrantService class
        WHEN client property is accessed
        THEN it should return an AsyncQdrantClient instance
        """
        from app.integrations.qdrant_client import QdrantService

        service = QdrantService()
        client = service.client

        assert isinstance(client, AsyncQdrantClient), \
            f"Expected AsyncQdrantClient, got {type(client).__name__}"

    def test_async_client_configured_with_grpc(self) -> None:
        """
        GIVEN QdrantService initialization
        WHEN AsyncQdrantClient is created
        THEN it should be configured with gRPC for performance
        """
        with patch("app.integrations.qdrant_client.AsyncQdrantClient") as mock_client:
            from app.integrations.qdrant_client import QdrantService

            service = QdrantService()
            _ = service.client

            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args.kwargs
            assert call_kwargs.get("prefer_grpc") is True, \
                "AsyncQdrantClient should use gRPC for performance"

    async def test_async_client_connection_is_awaitable(self) -> None:
        """
        GIVEN an AsyncQdrantClient instance
        WHEN checking connection health
        THEN the operation should be awaitable (async)
        """
        from app.integrations.qdrant_client import qdrant_service

        # This should be an async operation, not sync
        import asyncio
        result = qdrant_service.client.get_collections()

        # If it returns a coroutine, it's properly async
        assert asyncio.iscoroutine(result) or hasattr(result, '__await__'), \
            "get_collections() should return an awaitable"

        # Clean up coroutine if not awaited
        if asyncio.iscoroutine(result):
            result.close()
```

### Given-When-Then Summary
| Test | Given | When | Then |
|------|-------|------|------|
| 1.1 | QdrantService class | client accessed | Returns AsyncQdrantClient |
| 1.2 | QdrantService init | AsyncQdrantClient created | Configured with gRPC |
| 1.3 | AsyncQdrantClient instance | checking connection | Operation is awaitable |

---

## AC-7.7.2: ChunkService Native Async

### Requirement
ChunkService uses native async Qdrant methods (scroll, search, count) without `asyncio.to_thread()`.

### Test Level: Unit + Integration

### Failing Tests

#### Test 2.1: ChunkService scroll is native async
```python
# File: backend/tests/unit/test_async_qdrant.py (continued)

class TestChunkServiceAsyncOperations:
    """AC-7.7.2: ChunkService uses native async Qdrant calls."""

    @pytest.fixture
    def mock_async_qdrant(self):
        """Mock AsyncQdrantClient for ChunkService tests."""
        with patch("app.services.chunk_service.qdrant_service") as mock:
            mock_client = AsyncMock()
            mock.client = mock_client
            yield mock_client

    async def test_get_chunks_uses_native_async_scroll(
        self, mock_async_qdrant: AsyncMock
    ) -> None:
        """
        GIVEN a ChunkService instance with AsyncQdrantClient
        WHEN get_chunks_by_document is called
        THEN it should use native async scroll (not asyncio.to_thread)
        """
        from app.services.chunk_service import ChunkService

        mock_async_qdrant.scroll.return_value = ([], None)

        service = ChunkService()
        await service.get_chunks_by_document(
            kb_id="test-kb",
            document_id="test-doc"
        )

        # Verify native async scroll was called, not wrapped in to_thread
        mock_async_qdrant.scroll.assert_awaited_once()

    async def test_search_chunks_uses_native_async_search(
        self, mock_async_qdrant: AsyncMock
    ) -> None:
        """
        GIVEN a ChunkService instance with AsyncQdrantClient
        WHEN search_chunks is called
        THEN it should use native async search (not asyncio.to_thread)
        """
        from app.services.chunk_service import ChunkService

        mock_async_qdrant.search.return_value = []

        service = ChunkService()
        await service.search_chunks(
            kb_id="test-kb",
            query_embedding=[0.1] * 384,
            limit=10
        )

        mock_async_qdrant.search.assert_awaited_once()

    async def test_count_chunks_uses_native_async_count(
        self, mock_async_qdrant: AsyncMock
    ) -> None:
        """
        GIVEN a ChunkService instance with AsyncQdrantClient
        WHEN count_chunks is called
        THEN it should use native async count (not asyncio.to_thread)
        """
        from app.services.chunk_service import ChunkService
        from unittest.mock import MagicMock

        mock_count_result = MagicMock()
        mock_count_result.count = 42
        mock_async_qdrant.count.return_value = mock_count_result

        service = ChunkService()
        result = await service.count_chunks(kb_id="test-kb")

        mock_async_qdrant.count.assert_awaited_once()
        assert result == 42

    async def test_no_asyncio_to_thread_in_chunk_service(self) -> None:
        """
        GIVEN the ChunkService source code
        WHEN analyzing Qdrant operations
        THEN asyncio.to_thread should not be used for Qdrant calls
        """
        import inspect
        from app.services import chunk_service

        source = inspect.getsource(chunk_service)

        # Check that asyncio.to_thread is not used with qdrant operations
        assert "asyncio.to_thread" not in source or "qdrant" not in source.lower(), \
            "ChunkService should use native async Qdrant calls, not asyncio.to_thread"
```

#### Test 2.2: Integration test for ChunkService async operations
```python
# File: backend/tests/integration/test_async_qdrant_integration.py

import pytest
from uuid import uuid4

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestChunkServiceAsyncIntegration:
    """Integration tests for ChunkService async Qdrant operations."""

    async def test_scroll_chunks_returns_results_async(
        self,
        async_session,
        test_kb_with_documents,
    ) -> None:
        """
        GIVEN a knowledge base with indexed documents
        WHEN scrolling chunks asynchronously
        THEN results should be returned without blocking
        """
        from app.services.chunk_service import ChunkService

        kb, documents = test_kb_with_documents
        service = ChunkService()

        # This should be a true async operation
        chunks, next_offset = await service.get_chunks_by_document(
            kb_id=str(kb.id),
            document_id=str(documents[0].id)
        )

        assert isinstance(chunks, list)

    async def test_concurrent_chunk_operations_no_blocking(
        self,
        async_session,
        test_kb_with_documents,
    ) -> None:
        """
        GIVEN multiple chunk operations
        WHEN executed concurrently
        THEN they should not block each other (true async)
        """
        import asyncio
        from app.services.chunk_service import ChunkService

        kb, documents = test_kb_with_documents
        service = ChunkService()

        # Run 10 concurrent operations
        tasks = [
            service.get_chunks_by_document(
                kb_id=str(kb.id),
                document_id=str(documents[0].id)
            )
            for _ in range(10)
        ]

        # Should complete without thread pool exhaustion
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
```

### Given-When-Then Summary
| Test | Given | When | Then |
|------|-------|------|------|
| 2.1 | ChunkService with AsyncQdrantClient | get_chunks called | Native async scroll used |
| 2.2 | ChunkService with AsyncQdrantClient | search_chunks called | Native async search used |
| 2.3 | ChunkService with AsyncQdrantClient | count_chunks called | Native async count used |
| 2.4 | ChunkService source code | analyzing operations | No asyncio.to_thread |
| 2.5 | KB with indexed documents | scrolling chunks | Results returned async |
| 2.6 | Multiple chunk operations | executed concurrently | No blocking |

---

## AC-7.7.3: SearchService Native Async

### Requirement
SearchService uses native async Qdrant query methods, removing the `asyncio.to_thread()` wrapper currently in use.

### Test Level: Unit + Integration

### Failing Tests

#### Test 3.1: SearchService query_points is native async
```python
# File: backend/tests/unit/test_async_qdrant.py (continued)

class TestSearchServiceAsyncOperations:
    """AC-7.7.3: SearchService uses native async Qdrant calls."""

    @pytest.fixture
    def mock_async_qdrant_for_search(self):
        """Mock AsyncQdrantClient for SearchService tests."""
        with patch("app.services.search_service.qdrant_service") as mock:
            mock_client = AsyncMock()
            mock.client = mock_client
            mock.get_client.return_value = mock_client
            yield mock_client

    async def test_semantic_search_uses_native_async_query(
        self, mock_async_qdrant_for_search: AsyncMock
    ) -> None:
        """
        GIVEN a SearchService instance with AsyncQdrantClient
        WHEN semantic_search is called
        THEN it should use native async query_points (not asyncio.to_thread)
        """
        from app.services.search_service import SearchService
        from unittest.mock import MagicMock

        # Setup mock response
        mock_response = MagicMock()
        mock_response.points = []
        mock_async_qdrant_for_search.query_points.return_value = mock_response

        service = SearchService(
            permission_service=MagicMock(),
            audit_service=MagicMock()
        )

        await service.semantic_search(
            query="test query",
            kb_ids=["test-kb"],
            user_id="test-user",
            limit=10
        )

        # Verify native async was called
        mock_async_qdrant_for_search.query_points.assert_awaited()

    async def test_search_service_no_to_thread_wrapper(self) -> None:
        """
        GIVEN the SearchService source code
        WHEN analyzing the semantic_search method
        THEN asyncio.to_thread should not wrap Qdrant calls
        """
        import inspect
        from app.services import search_service

        source = inspect.getsource(search_service)

        # The current implementation uses asyncio.to_thread - this test should FAIL
        # until we migrate to native async
        lines_with_to_thread = [
            line for line in source.split('\n')
            if 'asyncio.to_thread' in line and 'qdrant' in line.lower()
        ]

        assert len(lines_with_to_thread) == 0, \
            f"Found asyncio.to_thread wrapping Qdrant calls: {lines_with_to_thread}"

    async def test_search_with_filters_uses_native_async(
        self, mock_async_qdrant_for_search: AsyncMock
    ) -> None:
        """
        GIVEN a SearchService with filter parameters
        WHEN searching with archive filters
        THEN native async query_points should be used with filters
        """
        from app.services.search_service import SearchService
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.points = []
        mock_async_qdrant_for_search.query_points.return_value = mock_response

        service = SearchService(
            permission_service=MagicMock(),
            audit_service=MagicMock()
        )

        await service.semantic_search(
            query="test",
            kb_ids=["test-kb"],
            user_id="test-user",
            limit=10,
            include_archived=False
        )

        # Verify filter was passed to native async call
        call_kwargs = mock_async_qdrant_for_search.query_points.call_args.kwargs
        assert "query_filter" in call_kwargs
```

#### Test 3.2: Integration test for SearchService async
```python
# File: backend/tests/integration/test_async_qdrant_integration.py (continued)

class TestSearchServiceAsyncIntegration:
    """Integration tests for SearchService async Qdrant operations."""

    async def test_semantic_search_async_returns_results(
        self,
        async_session,
        test_kb_with_indexed_chunks,
        test_user,
    ) -> None:
        """
        GIVEN a knowledge base with indexed chunks
        WHEN performing semantic search asynchronously
        THEN results should be returned without thread blocking
        """
        from app.services.search_service import SearchService
        from app.services.permission_service import PermissionService
        from app.services.search_audit_service import SearchAuditService

        kb = test_kb_with_indexed_chunks

        service = SearchService(
            permission_service=PermissionService(async_session),
            audit_service=SearchAuditService(async_session)
        )

        results = await service.semantic_search(
            query="test document content",
            kb_ids=[str(kb.id)],
            user_id=str(test_user.id),
            limit=5
        )

        assert isinstance(results, list)

    async def test_concurrent_searches_scale_efficiently(
        self,
        async_session,
        test_kb_with_indexed_chunks,
        test_user,
    ) -> None:
        """
        GIVEN multiple search operations
        WHEN executed concurrently with native async
        THEN they should scale without thread pool limits
        """
        import asyncio
        import time
        from app.services.search_service import SearchService

        kb = test_kb_with_indexed_chunks

        service = SearchService(
            permission_service=MagicMock(),
            audit_service=MagicMock()
        )

        # 50 concurrent searches should complete quickly with native async
        start = time.perf_counter()

        tasks = [
            service.semantic_search(
                query=f"test query {i}",
                kb_ids=[str(kb.id)],
                user_id=str(test_user.id),
                limit=5
            )
            for i in range(50)
        ]

        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        assert len(results) == 50
        # With native async, 50 concurrent should be much faster than sequential
        # This is a sanity check, not a strict performance test
        assert elapsed < 30, f"50 concurrent searches took {elapsed}s - possible thread blocking"
```

### Given-When-Then Summary
| Test | Given | When | Then |
|------|-------|------|------|
| 3.1 | SearchService with AsyncQdrantClient | semantic_search called | Native async query_points used |
| 3.2 | SearchService source code | analyzing code | No asyncio.to_thread wrapper |
| 3.3 | SearchService with filters | searching with archive filter | Native async with filters |
| 3.4 | KB with indexed chunks | semantic search async | Results returned |
| 3.5 | Multiple search operations | executed concurrently | Scales efficiently |

---

## AC-7.7.4: Load Test - 100 Concurrent Requests

### Requirement
System handles 100 concurrent search requests with p99 latency < 500ms demonstrating no thread pool bottleneck.

### Test Level: Load/Performance

### Failing Tests

#### Test 4.1: 100 concurrent requests performance
```python
# File: backend/tests/performance/test_qdrant_load.py

import pytest
import asyncio
import time
import statistics
from typing import List

pytestmark = [pytest.mark.performance, pytest.mark.asyncio]


class TestAsyncQdrantLoadPerformance:
    """AC-7.7.4: 100 concurrent requests with consistent response times."""

    @pytest.fixture
    async def search_service_for_load(self, async_session, test_kb_with_indexed_chunks):
        """Setup SearchService with real indexed data for load testing."""
        from app.services.search_service import SearchService
        from unittest.mock import MagicMock

        service = SearchService(
            permission_service=MagicMock(),
            audit_service=MagicMock()
        )
        return service, test_kb_with_indexed_chunks

    async def test_100_concurrent_requests_complete(
        self, search_service_for_load
    ) -> None:
        """
        GIVEN a SearchService with AsyncQdrantClient
        WHEN 100 concurrent search requests are made
        THEN all requests should complete successfully
        """
        service, kb = search_service_for_load

        async def single_search(i: int) -> dict:
            return await service.semantic_search(
                query=f"test query number {i}",
                kb_ids=[str(kb.id)],
                user_id="load-test-user",
                limit=10
            )

        tasks = [single_search(i) for i in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful vs failed
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]

        assert len(failures) == 0, f"Failed requests: {failures[:5]}"
        assert len(successes) == 100

    async def test_100_concurrent_requests_p99_under_500ms(
        self, search_service_for_load
    ) -> None:
        """
        GIVEN a SearchService with native async Qdrant
        WHEN 100 concurrent search requests are made
        THEN p99 latency should be under 500ms
        """
        service, kb = search_service_for_load
        latencies: List[float] = []

        async def timed_search(i: int) -> float:
            start = time.perf_counter()
            await service.semantic_search(
                query=f"performance test {i}",
                kb_ids=[str(kb.id)],
                user_id="load-test-user",
                limit=10
            )
            return time.perf_counter() - start

        tasks = [timed_search(i) for i in range(100)]
        latencies = await asyncio.gather(*tasks)

        # Calculate p99
        sorted_latencies = sorted(latencies)
        p99_index = int(len(sorted_latencies) * 0.99)
        p99_latency = sorted_latencies[p99_index]

        # Also capture p50 and p95 for analysis
        p50_latency = sorted_latencies[int(len(sorted_latencies) * 0.50)]
        p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]

        print(f"\nLatency Statistics:")
        print(f"  p50: {p50_latency*1000:.1f}ms")
        print(f"  p95: {p95_latency*1000:.1f}ms")
        print(f"  p99: {p99_latency*1000:.1f}ms")
        print(f"  max: {max(latencies)*1000:.1f}ms")

        assert p99_latency < 0.5, \
            f"p99 latency {p99_latency*1000:.1f}ms exceeds 500ms target"

    async def test_consistent_latency_under_load(
        self, search_service_for_load
    ) -> None:
        """
        GIVEN concurrent load on SearchService
        WHEN measuring request latencies
        THEN variance should be low (no thread pool bottleneck spikes)
        """
        service, kb = search_service_for_load
        latencies: List[float] = []

        async def timed_search(i: int) -> float:
            start = time.perf_counter()
            await service.semantic_search(
                query=f"consistency test {i}",
                kb_ids=[str(kb.id)],
                user_id="load-test-user",
                limit=10
            )
            return time.perf_counter() - start

        tasks = [timed_search(i) for i in range(100)]
        latencies = await asyncio.gather(*tasks)

        # Calculate coefficient of variation (CV)
        mean_latency = statistics.mean(latencies)
        std_latency = statistics.stdev(latencies)
        cv = std_latency / mean_latency

        print(f"\nLatency Consistency:")
        print(f"  mean: {mean_latency*1000:.1f}ms")
        print(f"  std:  {std_latency*1000:.1f}ms")
        print(f"  CV:   {cv:.2f}")

        # CV > 1.0 would indicate high variance (thread pool bottleneck symptoms)
        assert cv < 1.0, \
            f"High latency variance (CV={cv:.2f}) suggests thread pool bottleneck"

    async def test_no_thread_pool_exhaustion(
        self, search_service_for_load
    ) -> None:
        """
        GIVEN 100+ concurrent requests
        WHEN using native async Qdrant
        THEN no thread pool exhaustion errors should occur
        """
        import concurrent.futures
        service, kb = search_service_for_load

        async def search_with_error_capture(i: int):
            try:
                return await service.semantic_search(
                    query=f"exhaustion test {i}",
                    kb_ids=[str(kb.id)],
                    user_id="load-test-user",
                    limit=10
                )
            except concurrent.futures.ThreadPoolExecutor as e:
                return f"ThreadPool error: {e}"
            except Exception as e:
                return f"Error: {type(e).__name__}: {e}"

        # Run 150 concurrent to stress test
        tasks = [search_with_error_capture(i) for i in range(150)]
        results = await asyncio.gather(*tasks)

        thread_errors = [r for r in results if isinstance(r, str) and "ThreadPool" in r]

        assert len(thread_errors) == 0, \
            f"Thread pool exhaustion detected: {thread_errors}"
```

### Given-When-Then Summary
| Test | Given | When | Then |
|------|-------|------|------|
| 4.1 | SearchService with AsyncQdrantClient | 100 concurrent requests | All complete successfully |
| 4.2 | SearchService native async | 100 concurrent requests | p99 < 500ms |
| 4.3 | Concurrent load | measuring latencies | Low variance (no spikes) |
| 4.4 | 150 concurrent requests | stress testing | No thread pool exhaustion |

---

## Test File Structure

```
backend/tests/
├── unit/
│   └── test_async_qdrant.py          # AC-7.7.1, 7.7.2, 7.7.3 unit tests
├── integration/
│   └── test_async_qdrant_integration.py  # AC-7.7.2, 7.7.3 integration tests
└── performance/
    └── test_qdrant_load.py           # AC-7.7.4 load tests
```

## Data Factories Required

```python
# File: backend/tests/factories/qdrant_factory.py

from typing import List
import uuid

def create_test_embedding(dimension: int = 384) -> List[float]:
    """Create a normalized test embedding vector."""
    import random
    vec = [random.random() for _ in range(dimension)]
    norm = sum(x**2 for x in vec) ** 0.5
    return [x / norm for x in vec]

def create_test_chunk_payload(
    kb_id: str = None,
    document_id: str = None,
    chunk_index: int = 0,
) -> dict:
    """Create test chunk payload for Qdrant."""
    return {
        "kb_id": kb_id or str(uuid.uuid4()),
        "document_id": document_id or str(uuid.uuid4()),
        "chunk_index": chunk_index,
        "content": f"Test chunk content {chunk_index}",
        "archived_at": None,
    }
```

## Pytest Fixtures Required

```python
# File: backend/tests/conftest.py (additions)

@pytest.fixture
async def test_kb_with_indexed_chunks(async_session, test_user):
    """Create KB with documents indexed in Qdrant for async tests."""
    from tests.factories import KnowledgeBaseFactory, DocumentFactory
    from app.integrations.qdrant_client import qdrant_service

    kb = await KnowledgeBaseFactory.create(
        session=async_session,
        owner_id=test_user.id
    )

    # Index test chunks in Qdrant
    collection_name = f"kb_{kb.id}"
    # ... setup collection and insert test vectors

    yield kb

    # Cleanup
    await qdrant_service.client.delete_collection(collection_name)
```

## Commands to Run Tests

```bash
# Run all Story 7-7 tests (should all FAIL initially - RED phase)
cd backend

# Unit tests only
.venv/bin/pytest tests/unit/test_async_qdrant.py -v --tb=short

# Integration tests
.venv/bin/pytest tests/integration/test_async_qdrant_integration.py -v --tb=short

# Performance/Load tests
.venv/bin/pytest tests/performance/test_qdrant_load.py -v --tb=short -s

# All tests for story
.venv/bin/pytest tests/unit/test_async_qdrant.py tests/integration/test_async_qdrant_integration.py tests/performance/test_qdrant_load.py -v
```

## Implementation Checklist (GREEN Phase)

After tests are written and failing (RED), implement:

- [ ] **Task 1**: Replace `QdrantClient` with `AsyncQdrantClient` in `qdrant_client.py`
- [ ] **Task 2**: Update `ChunkService` methods to use `await client.scroll()`, `await client.search()`, `await client.count()`
- [ ] **Task 3**: Remove `asyncio.to_thread()` wrapper from `SearchService.semantic_search()`
- [ ] **Task 4**: Update all callers to properly await async Qdrant operations
- [ ] **Task 5**: Run load tests to verify p99 < 500ms under 100 concurrent requests

## Notes

- Current implementation uses `asyncio.to_thread()` in SearchService which blocks the thread pool
- ChunkService uses sync client calls directly (`qdrant_service.client.scroll()`)
- Migration requires `qdrant-client>=1.7.0` for stable AsyncQdrantClient
- gRPC should be preferred for performance (`prefer_grpc=True`)
