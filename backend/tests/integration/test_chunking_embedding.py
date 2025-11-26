"""Integration tests for chunking and embedding pipeline.

Tests the full flow from parsed content to Qdrant vectors,
including status transitions and cleanup.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def mock_qdrant_service():
    """Mock Qdrant service for integration tests."""
    with patch("app.workers.indexing.qdrant_service") as mock:
        mock.collection_exists = AsyncMock(return_value=True)
        mock.create_collection = AsyncMock()
        mock.upsert_points = AsyncMock(return_value=10)
        mock.delete_points_by_filter = AsyncMock(return_value=0)
        mock.client = MagicMock()
        mock.client.count = MagicMock(return_value=MagicMock(count=10))
        yield mock


@pytest.fixture
def mock_litellm():
    """Mock LiteLLM for deterministic embeddings."""
    with patch("app.integrations.litellm_client.aembedding") as mock:
        # Return deterministic embeddings
        def make_response(texts):
            embeddings = [[float(i) * 0.001] * 1536 for i in range(len(texts))]
            response = MagicMock()
            response.data = [{"embedding": e} for e in embeddings]
            response.usage = MagicMock(total_tokens=len(texts) * 10)
            return response

        mock.side_effect = lambda **kwargs: make_response(  # noqa: ARG005
            kwargs.get("input", [])
        )
        yield mock


@pytest.fixture
def sample_parsed_content():
    """Create sample ParsedContent for testing."""
    from app.workers.parsing import ParsedContent, ParsedElement

    # Create a document with multiple pages and sections
    elements = [
        ParsedElement(
            text="Introduction",
            element_type="Title",
            metadata={},
        ),
        ParsedElement(
            text="This is the introduction section with important content. " * 20,
            element_type="NarrativeText",
            metadata={"page_number": 1},
        ),
        ParsedElement(
            text="Methods",
            element_type="Header",
            metadata={"page_number": 2},
        ),
        ParsedElement(
            text="The methods section describes the approach. " * 20,
            element_type="NarrativeText",
            metadata={"page_number": 2},
        ),
        ParsedElement(
            text="Results",
            element_type="Header",
            metadata={"page_number": 3},
        ),
        ParsedElement(
            text="The results show significant findings. " * 20,
            element_type="NarrativeText",
            metadata={"page_number": 3},
        ),
    ]

    full_text = "\n\n".join(el.text for el in elements)

    return ParsedContent(
        text=full_text,
        elements=elements,
        metadata={
            "page_count": 3,
            "section_count": 3,
            "source_format": "pdf",
        },
    )


class TestFullPipeline:
    """Integration tests for the full chunking -> embedding -> indexing pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_flow(
        self,
        mock_qdrant_service,
        mock_litellm,  # noqa: ARG002
        sample_parsed_content,  # noqa: ARG002
    ):
        """Test the complete flow from parsed content to indexed vectors."""
        from app.workers.chunking import chunk_document
        from app.workers.embedding import generate_embeddings
        from app.workers.indexing import index_document

        doc_id = "test-doc-123"
        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        # Step 1: Chunk the document
        chunks = chunk_document(
            parsed_content=sample_parsed_content,
            document_id=doc_id,
            document_name="research.pdf",
            chunk_size=100,
            chunk_overlap=10,
        )

        assert len(chunks) > 1
        assert all(c.document_id == doc_id for c in chunks)

        # Step 2: Generate embeddings
        embeddings = await generate_embeddings(chunks)

        assert len(embeddings) == len(chunks)
        assert all(len(e.embedding) == 1536 for e in embeddings)

        # Step 3: Index in Qdrant
        mock_qdrant_service.upsert_points.return_value = len(embeddings)

        chunk_count = await index_document(
            doc_id=doc_id,
            kb_id=kb_id,
            embeddings=embeddings,
        )

        assert chunk_count == len(chunks)
        mock_qdrant_service.upsert_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_metadata_preserved_through_pipeline(
        self,
        mock_qdrant_service,  # noqa: ARG002
        mock_litellm,  # noqa: ARG002
        sample_parsed_content,  # noqa: ARG002
    ):
        """Test that metadata is preserved from parsing through to Qdrant payload."""
        from app.workers.chunking import chunk_document
        from app.workers.embedding import generate_embeddings
        from app.workers.indexing import _create_points

        doc_id = "test-doc-456"

        # Chunk and embed
        chunks = chunk_document(
            parsed_content=sample_parsed_content,
            document_id=doc_id,
            document_name="report.pdf",
            chunk_size=200,
            chunk_overlap=20,
        )

        embeddings = await generate_embeddings(chunks)

        # Create Qdrant points
        points = _create_points(embeddings)

        # Verify metadata in payloads
        for point in points:
            payload = point.payload
            assert payload["document_id"] == doc_id
            assert payload["document_name"] == "report.pdf"
            assert "chunk_text" in payload
            assert "char_start" in payload
            assert "char_end" in payload
            assert "chunk_index" in payload

    @pytest.mark.asyncio
    async def test_chunk_count_accuracy(
        self,
        mock_qdrant_service,
        mock_litellm,  # noqa: ARG002
        sample_parsed_content,  # noqa: ARG002
    ):
        """Test that chunk count is accurate for document record update."""
        from app.workers.chunking import chunk_document
        from app.workers.embedding import generate_embeddings
        from app.workers.indexing import index_document

        doc_id = "test-doc-789"
        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        chunks = chunk_document(
            parsed_content=sample_parsed_content,
            document_id=doc_id,
            document_name="doc.pdf",
            chunk_size=100,
            chunk_overlap=10,
        )

        embeddings = await generate_embeddings(chunks)

        mock_qdrant_service.upsert_points.return_value = len(embeddings)

        chunk_count = await index_document(
            doc_id=doc_id,
            kb_id=kb_id,
            embeddings=embeddings,
        )

        # Chunk count should match what we created
        assert chunk_count == len(chunks)
        assert chunk_count == len(embeddings)


class TestReuploadScenario:
    """Tests for document re-upload with orphan cleanup."""

    @pytest.mark.asyncio
    async def test_reupload_cleans_orphan_chunks(
        self,
        mock_qdrant_service,
        mock_litellm,  # noqa: ARG002
    ):
        """Test that re-upload cleans up orphan chunks from previous version."""
        from app.workers.chunking import chunk_document
        from app.workers.embedding import generate_embeddings
        from app.workers.indexing import cleanup_orphan_chunks, index_document
        from app.workers.parsing import ParsedContent, ParsedElement

        doc_id = "reupload-doc-123"
        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        # Simulate a shorter document on re-upload
        shorter_content = ParsedContent(
            text="Short content. " * 10,
            elements=[
                ParsedElement(
                    text="Short content. " * 10,
                    element_type="NarrativeText",
                    metadata={},
                )
            ],
            metadata={},
        )

        chunks = chunk_document(
            parsed_content=shorter_content,
            document_id=doc_id,
            document_name="doc.pdf",
            chunk_size=500,
            chunk_overlap=50,
        )

        embeddings = await generate_embeddings(chunks)

        # Index new version
        mock_qdrant_service.upsert_points.return_value = len(embeddings)

        await index_document(
            doc_id=doc_id,
            kb_id=kb_id,
            embeddings=embeddings,
        )

        # Cleanup should be called for orphans
        mock_qdrant_service.delete_points_by_filter.return_value = 5

        max_chunk_index = len(chunks) - 1
        await cleanup_orphan_chunks(doc_id, kb_id, max_chunk_index)

        # Should have attempted cleanup
        mock_qdrant_service.delete_points_by_filter.assert_called()

    @pytest.mark.asyncio
    async def test_atomic_switch_new_vectors_before_cleanup(
        self,
        mock_qdrant_service,
        mock_litellm,  # noqa: ARG002
    ):
        """Test that new vectors are indexed before orphans are cleaned."""
        from app.workers.chunking import chunk_document
        from app.workers.embedding import generate_embeddings
        from app.workers.indexing import cleanup_orphan_chunks, index_document
        from app.workers.parsing import ParsedContent, ParsedElement

        doc_id = "atomic-doc-123"
        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        content = ParsedContent(
            text="Test content. " * 20,
            elements=[
                ParsedElement(
                    text="Test content. " * 20,
                    element_type="NarrativeText",
                    metadata={},
                )
            ],
            metadata={},
        )

        chunks = chunk_document(
            parsed_content=content,
            document_id=doc_id,
            document_name="doc.pdf",
            chunk_size=100,
            chunk_overlap=10,
        )

        embeddings = await generate_embeddings(chunks)

        call_order = []

        async def track_upsert(*args, **kwargs):
            call_order.append("upsert")
            return len(embeddings)

        async def track_delete(*args, **kwargs):
            call_order.append("delete")
            return 0

        mock_qdrant_service.upsert_points.side_effect = track_upsert
        mock_qdrant_service.delete_points_by_filter.side_effect = track_delete

        # Execute in order: index then cleanup
        await index_document(doc_id=doc_id, kb_id=kb_id, embeddings=embeddings)
        await cleanup_orphan_chunks(doc_id, kb_id, len(chunks) - 1)

        # Verify upsert happened before delete (atomic switch)
        assert call_order == ["upsert", "delete"]


class TestErrorRecovery:
    """Tests for error handling and recovery."""

    @pytest.mark.asyncio
    async def test_embedding_failure_handling(self, mock_qdrant_service):  # noqa: ARG002
        """Test handling of embedding API failures."""
        from app.integrations.litellm_client import RateLimitExceededError
        from app.workers.chunking import chunk_document
        from app.workers.embedding import EmbeddingGenerationError, generate_embeddings
        from app.workers.parsing import ParsedContent, ParsedElement

        with patch("app.workers.embedding.embedding_client") as mock_client:
            mock_client.get_embeddings = AsyncMock(
                side_effect=RateLimitExceededError("Rate limit exceeded")
            )

            content = ParsedContent(
                text="Test content. " * 10,
                elements=[
                    ParsedElement(
                        text="Test content. " * 10,
                        element_type="NarrativeText",
                        metadata={},
                    )
                ],
                metadata={},
            )

            chunks = chunk_document(
                parsed_content=content,
                document_id="test-doc",
                document_name="doc.pdf",
            )

            with pytest.raises(EmbeddingGenerationError):
                await generate_embeddings(chunks)

    @pytest.mark.asyncio
    async def test_indexing_failure_does_not_cleanup(
        self,
        mock_qdrant_service,
        mock_litellm,  # noqa: ARG002
    ):
        """Test that indexing failure preserves partial vectors for retry."""
        from app.workers.chunking import chunk_document
        from app.workers.embedding import generate_embeddings
        from app.workers.indexing import IndexingError, index_document
        from app.workers.parsing import ParsedContent, ParsedElement

        # Make all upserts fail
        mock_qdrant_service.upsert_points.side_effect = Exception("Qdrant error")

        content = ParsedContent(
            text="Test content for indexing.",
            elements=[
                ParsedElement(
                    text="Test content for indexing.",
                    element_type="NarrativeText",
                    metadata={},
                )
            ],
            metadata={},
        )

        chunks = chunk_document(
            parsed_content=content,
            document_id="test-doc",
            document_name="doc.pdf",
        )

        embeddings = await generate_embeddings(chunks)

        kb_id = UUID("12345678-1234-1234-1234-123456789abc")

        with pytest.raises(IndexingError):
            await index_document(
                doc_id="test-doc",
                kb_id=kb_id,
                embeddings=embeddings,
                max_retries=2,
            )

        # Delete should NOT have been called (no cleanup on failure)
        mock_qdrant_service.delete_points_by_filter.assert_not_called()
