"""Load and performance tests for async Qdrant migration.

Story 7-7: Async Qdrant Migration
AC-7.7.4: 100 concurrent requests with consistent response times

These tests verify that the async Qdrant migration eliminates
thread pool bottlenecks and achieves p99 latency < 500ms under load.

Tests focus on the _search_collections method which directly uses
the async Qdrant client, as this is the core operation being migrated.
"""

import asyncio
import statistics
import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

pytestmark = [pytest.mark.performance, pytest.mark.asyncio]


class TestAsyncQdrantLoadPerformance:
    """AC-7.7.4: 100 concurrent requests with consistent response times."""

    @pytest.fixture
    def mock_qdrant_service(self):
        """Create a mock qdrant_service for load testing patterns."""
        with patch("app.services.search_service.qdrant_service") as mock_qdrant:
            # Simulate async response with small delay
            async def mock_query_points(*args, **kwargs):
                await asyncio.sleep(0.01)  # 10ms simulated latency
                mock_response = MagicMock()
                mock_response.points = []
                return mock_response

            mock_qdrant.query_points = AsyncMock(side_effect=mock_query_points)

            yield mock_qdrant

    @pytest.fixture
    def search_service(self, mock_qdrant_service):
        """Create a SearchService with mocked dependencies for load testing."""
        from app.services.search_service import SearchService

        with patch("app.services.search_service.embedding_client") as mock_embed:

            async def mock_embed_fn(*args, **kwargs):
                return [[0.1] * 384]

            mock_embed.get_embeddings = AsyncMock(side_effect=mock_embed_fn)

            service = SearchService(
                permission_service=MagicMock(),
                audit_service=MagicMock(),
            )
            service.permission_service.check_permission = AsyncMock(return_value=True)
            service.permission_service.get_permitted_kb_ids = AsyncMock(
                return_value=["test-kb"]
            )

            yield service

    async def test_100_concurrent_search_collections_complete(
        self, search_service, mock_qdrant_service
    ) -> None:
        """
        GIVEN a SearchService with AsyncQdrantClient
        WHEN 100 concurrent _search_collections calls are made
        THEN all requests should complete successfully
        """
        service = search_service
        kb_ids = [str(uuid4())]
        embedding = [0.1] * 384

        async def single_search(i: int):
            return await service._search_collections(
                embedding=embedding,
                kb_ids=kb_ids,
                limit=10,
            )

        tasks = [single_search(i) for i in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful vs failed
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]

        assert len(failures) == 0, f"Failed requests: {failures[:5]}"
        assert (
            len(successes) == 100
        ), f"Expected 100 successful requests, got {len(successes)}"

    async def test_100_concurrent_requests_p99_under_500ms(
        self, search_service, mock_qdrant_service
    ) -> None:
        """
        GIVEN a SearchService with native async Qdrant
        WHEN 100 concurrent _search_collections calls are made
        THEN p99 latency should be under 500ms
        """
        service = search_service
        kb_ids = [str(uuid4())]
        embedding = [0.1] * 384
        latencies: list[float] = []

        async def timed_search(i: int) -> float:
            start = time.perf_counter()
            await service._search_collections(
                embedding=embedding,
                kb_ids=kb_ids,
                limit=10,
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

        print("\nLatency Statistics (100 concurrent):")
        print(f"  p50: {p50_latency*1000:.1f}ms")
        print(f"  p95: {p95_latency*1000:.1f}ms")
        print(f"  p99: {p99_latency*1000:.1f}ms")
        print(f"  max: {max(latencies)*1000:.1f}ms")

        assert p99_latency < 0.5, (
            f"p99 latency {p99_latency*1000:.1f}ms exceeds 500ms target. "
            "This may indicate thread pool bottleneck from asyncio.to_thread usage."
        )

    async def test_consistent_latency_under_load(
        self, search_service, mock_qdrant_service
    ) -> None:
        """
        GIVEN concurrent load on SearchService
        WHEN measuring request latencies
        THEN variance should be low (no thread pool bottleneck spikes)
        """
        service = search_service
        kb_ids = [str(uuid4())]
        embedding = [0.1] * 384
        latencies: list[float] = []

        async def timed_search(i: int) -> float:
            start = time.perf_counter()
            await service._search_collections(
                embedding=embedding,
                kb_ids=kb_ids,
                limit=10,
            )
            return time.perf_counter() - start

        tasks = [timed_search(i) for i in range(100)]
        latencies = await asyncio.gather(*tasks)

        # Calculate coefficient of variation (CV)
        mean_latency = statistics.mean(latencies)
        std_latency = statistics.stdev(latencies)
        cv = std_latency / mean_latency if mean_latency > 0 else 0

        print("\nLatency Consistency (100 concurrent):")
        print(f"  mean: {mean_latency*1000:.1f}ms")
        print(f"  std:  {std_latency*1000:.1f}ms")
        print(f"  CV:   {cv:.2f}")

        # CV > 1.0 would indicate high variance (thread pool bottleneck symptoms)
        assert cv < 1.0, (
            f"High latency variance (CV={cv:.2f}) suggests thread pool bottleneck. "
            "Native async should have consistent latencies."
        )

    async def test_no_thread_pool_exhaustion_at_150_concurrent(
        self, search_service, mock_qdrant_service
    ) -> None:
        """
        GIVEN 150 concurrent requests (above typical thread pool size)
        WHEN using native async Qdrant
        THEN no thread pool exhaustion errors should occur
        """
        import concurrent.futures

        service = search_service
        kb_ids = [str(uuid4())]
        embedding = [0.1] * 384

        async def search_with_error_capture(i: int):
            try:
                return await service._search_collections(
                    embedding=embedding,
                    kb_ids=kb_ids,
                    limit=10,
                )
            except concurrent.futures.BrokenExecutor as e:
                return f"ThreadPool error: {e}"
            except RuntimeError as e:
                if "thread" in str(e).lower():
                    return f"Thread error: {e}"
                raise
            except Exception as e:
                return f"Error: {type(e).__name__}: {e}"

        # Run 150 concurrent to stress test beyond default thread pool
        tasks = [search_with_error_capture(i) for i in range(150)]
        results = await asyncio.gather(*tasks)

        thread_errors = [
            r
            for r in results
            if isinstance(r, str) and ("ThreadPool" in r or "Thread error" in r)
        ]

        assert len(thread_errors) == 0, (
            f"Thread pool exhaustion detected with 150 concurrent requests: "
            f"{thread_errors[:3]}"
        )

    async def test_throughput_improves_with_concurrency(
        self, search_service, mock_qdrant_service
    ) -> None:
        """
        GIVEN native async Qdrant operations
        WHEN comparing sequential vs concurrent execution
        THEN concurrent should be significantly faster (async benefit)
        """
        service = search_service
        kb_ids = [str(uuid4())]
        embedding = [0.1] * 384

        async def single_search():
            return await service._search_collections(
                embedding=embedding,
                kb_ids=kb_ids,
                limit=10,
            )

        # Sequential execution time (10 requests)
        start_seq = time.perf_counter()
        for _ in range(10):
            await single_search()
        seq_time = time.perf_counter() - start_seq

        # Concurrent execution time (10 requests)
        start_conc = time.perf_counter()
        tasks = [single_search() for _ in range(10)]
        await asyncio.gather(*tasks)
        conc_time = time.perf_counter() - start_conc

        speedup = seq_time / conc_time if conc_time > 0 else 0

        print("\nThroughput Comparison (10 requests):")
        print(f"  Sequential: {seq_time*1000:.1f}ms")
        print(f"  Concurrent: {conc_time*1000:.1f}ms")
        print(f"  Speedup:    {speedup:.1f}x")

        # With true async, concurrent should be at least 2x faster
        assert speedup > 2.0, (
            f"Concurrent execution only {speedup:.1f}x faster than sequential. "
            "True async should provide significant speedup. "
            "This may indicate blocking operations."
        )


class TestAsyncQdrantRealWorldScenarios:
    """Real-world load scenarios for async Qdrant."""

    @pytest.fixture
    def mock_varied_qdrant_service(self):
        """Create mock with varied response times to simulate real conditions."""
        import random

        with patch("app.services.search_service.qdrant_service") as mock_qdrant:

            async def mock_query_varied(*args, **kwargs):
                # Simulate varied latency (5-50ms)
                await asyncio.sleep(random.uniform(0.005, 0.05))
                mock_response = MagicMock()
                mock_response.points = []  # Empty list to avoid processing
                return mock_response

            mock_qdrant.query_points = AsyncMock(side_effect=mock_query_varied)

            yield mock_qdrant

    @pytest.fixture
    def varied_search_service(self, mock_varied_qdrant_service):
        """Create SearchService with varied latency mocks."""
        from app.services.search_service import SearchService

        with patch("app.services.search_service.embedding_client") as mock_embed:
            mock_embed.get_embeddings = AsyncMock(return_value=[[0.1] * 384])

            service = SearchService(
                permission_service=MagicMock(),
                audit_service=MagicMock(),
            )
            service.permission_service.check_permission = AsyncMock(return_value=True)
            # Use qdrant_service from the test context
            service.qdrant_service = mock_varied_qdrant_service

            yield service

    async def test_burst_traffic_handling(
        self, varied_search_service, mock_varied_qdrant_service
    ) -> None:
        """
        GIVEN a burst of 50 requests arriving simultaneously
        WHEN processed with native async
        THEN all should complete within acceptable time
        """
        service = varied_search_service
        kb_ids = [str(uuid4())]
        embedding = [0.1] * 384

        start = time.perf_counter()

        tasks = [
            service._search_collections(
                embedding=embedding,
                kb_ids=kb_ids,
                limit=10,
            )
            for _ in range(50)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.perf_counter() - start

        failures = [r for r in results if isinstance(r, Exception)]

        print("\nBurst Traffic (50 requests):")
        print(f"  Total time: {total_time*1000:.1f}ms")
        print(f"  Failures:   {len(failures)}")

        assert len(failures) == 0, f"Burst traffic failures: {failures[:3]}"
        # 50 requests with 5-50ms each should complete in under 2 seconds with async
        assert total_time < 2.0, (
            f"Burst of 50 requests took {total_time:.2f}s. "
            "Native async should handle burst traffic efficiently."
        )

    async def test_sustained_load_stability(
        self, varied_search_service, mock_varied_qdrant_service
    ) -> None:
        """
        GIVEN sustained concurrent load
        WHEN running for multiple iterations
        THEN latency should remain stable (no degradation)
        """
        service = varied_search_service
        kb_ids = [str(uuid4())]
        embedding = [0.1] * 384
        iteration_latencies = []

        for iteration in range(5):
            start = time.perf_counter()

            tasks = [
                service._search_collections(
                    embedding=embedding,
                    kb_ids=kb_ids,
                    limit=10,
                )
                for _ in range(20)
            ]

            await asyncio.gather(*tasks)
            iteration_latencies.append(time.perf_counter() - start)

        print("\nSustained Load (5 iterations of 20 requests):")
        for i, lat in enumerate(iteration_latencies):
            print(f"  Iteration {i+1}: {lat*1000:.1f}ms")

        # Check that later iterations aren't significantly slower
        first_half_avg = statistics.mean(iteration_latencies[:2])
        second_half_avg = statistics.mean(iteration_latencies[3:])

        degradation = (second_half_avg - first_half_avg) / first_half_avg

        assert degradation < 0.5, (
            f"Performance degraded by {degradation*100:.1f}% over sustained load. "
            "This may indicate resource leaks or thread pool saturation."
        )
