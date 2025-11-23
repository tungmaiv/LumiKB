"""Integration tests for Docker Compose service connectivity.

Tests verify that the backend can connect to all infrastructure services:
- PostgreSQL (database)
- Redis (cache/broker)
- MinIO (object storage)
- Qdrant (vector database)
- LiteLLM (LLM gateway) - optional, depends on API keys

Story 1.3: Docker Compose Development Environment
AC 5: Backend can connect to PostgreSQL, Redis, MinIO, and Qdrant successfully
"""

import pytest


@pytest.mark.integration
class TestServiceConnectivity:
    """Test connectivity to all Docker Compose services."""

    @pytest.mark.asyncio
    async def test_postgresql_connectivity(self):
        """Test PostgreSQL connection via asyncpg."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        from app.core.config import settings

        engine = create_async_engine(settings.database_url, echo=False)
        try:
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        finally:
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_redis_connectivity(self):
        """Test Redis connection via redis-py."""
        import redis.asyncio as redis

        from app.core.config import settings

        client = redis.from_url(settings.redis_url)
        try:
            # Test basic operations
            pong = await client.ping()
            assert pong is True

            # Test set/get
            await client.set("test_key", "test_value", ex=10)
            value = await client.get("test_key")
            assert value == b"test_value"

            # Cleanup
            await client.delete("test_key")
        finally:
            await client.aclose()

    @pytest.mark.asyncio
    async def test_minio_connectivity(self):
        """Test MinIO/S3 connection via boto3."""
        import boto3
        from botocore.client import Config

        from app.core.config import settings

        # Create S3 client for MinIO
        s3_client = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
        )

        # Test by listing buckets (works even with no buckets)
        response = s3_client.list_buckets()
        assert "Buckets" in response

        # Create test bucket if not exists
        import contextlib

        bucket_name = "test-connectivity"
        with contextlib.suppress(s3_client.exceptions.BucketAlreadyOwnedByYou):
            s3_client.create_bucket(Bucket=bucket_name)

        # Test upload/download
        test_content = b"Hello, MinIO!"
        s3_client.put_object(Bucket=bucket_name, Key="test.txt", Body=test_content)

        response = s3_client.get_object(Bucket=bucket_name, Key="test.txt")
        assert response["Body"].read() == test_content

        # Cleanup
        s3_client.delete_object(Bucket=bucket_name, Key="test.txt")
        s3_client.delete_bucket(Bucket=bucket_name)

    @pytest.mark.asyncio
    async def test_qdrant_connectivity(self):
        """Test Qdrant connection via qdrant-client."""
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        from app.core.config import settings

        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

        # Test health check
        health = client.get_collections()
        assert health is not None

        # Test collection operations
        collection_name = "test_connectivity"
        try:
            # Create collection
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=4, distance=Distance.COSINE),
            )

            # Verify collection exists
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            assert collection_name in collection_names

        finally:
            # Cleanup
            import contextlib

            with contextlib.suppress(Exception):
                client.delete_collection(collection_name=collection_name)

    @pytest.mark.asyncio
    async def test_litellm_health(self):
        """Test LiteLLM proxy is accessible (no API key needed for health check)."""
        import httpx

        from app.core.config import settings

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.litellm_url}/health/readiness")
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "healthy"


@pytest.mark.integration
class TestDataPersistence:
    """Test data persistence across container restarts (AC 3)."""

    @pytest.mark.asyncio
    async def test_postgresql_data_persists(self):
        """Verify PostgreSQL data persists in named volume."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        from app.core.config import settings

        engine = create_async_engine(settings.database_url, echo=False)
        try:
            async with engine.connect() as conn:
                # Check that our tables exist (created by migrations)
                result = await conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
                    )
                )
                tables = [row[0] for row in result.fetchall()]
                # Tables from Story 1.2 migrations should exist
                expected_tables = ["users", "knowledge_bases", "documents"]
                for table in expected_tables:
                    assert (
                        table in tables
                    ), f"Table {table} not found, data may not have persisted"
        finally:
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_redis_data_persists(self):
        """Verify Redis AOF persistence is enabled."""
        import redis.asyncio as redis

        from app.core.config import settings

        client = redis.from_url(settings.redis_url)
        try:
            # Check if appendonly is enabled
            config = await client.config_get("appendonly")
            assert (
                config.get("appendonly") == "yes"
            ), "Redis AOF persistence not enabled"
        finally:
            await client.aclose()
