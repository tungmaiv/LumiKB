# ATDD Checklist: Story 7-17 Service Integration

**Story ID:** 7.17
**Title:** Service Integration
**Generated:** 2025-12-09
**Generator:** TEA (Test Engineering Architect)
**Status:** RED (Failing Tests - Implementation Required)

---

## Story Summary

**As a** system
**I want** search and generation services to use KB-level configuration
**So that** each Knowledge Base behaves according to its settings

---

## Acceptance Criteria Coverage

| AC ID | Description | Test Level | Test File |
|-------|-------------|------------|-----------|
| 7.17.1 | SearchService uses KB retrieval config (top_k, similarity_threshold, method) | Unit, Integration | `test_search_service_kb_config.py`, `test_kb_config_integration.py` |
| 7.17.2 | GenerationService uses KB generation config (temperature, top_p, max_tokens) | Unit, Integration | `test_generation_service_kb_config.py`, `test_kb_config_integration.py` |
| 7.17.3 | GenerationService uses KB system_prompt instead of default | Unit, Integration | `test_generation_service_kb_config.py` |
| 7.17.4 | Document worker uses KB chunking config (chunk_size, chunk_overlap, strategy) | Unit | `test_document_worker_kb_config.py` |
| 7.17.5 | Request overrides take precedence over KB settings | Unit, Integration | All test files |
| 7.17.6 | Audit log includes effective_config snapshot | Unit, Integration | `test_search_service_kb_config.py`, `test_generation_service_kb_config.py` |

---

## Test Files to Create

### 1. SearchService Unit Tests (pytest)

**File:** `backend/tests/unit/test_search_service_kb_config.py`

```python
"""
Story 7-17 ATDD: SearchService KB Config Integration Tests
Generated: 2025-12-09
Status: RED - Implementation required to pass

Required implementation:
- Integrate KBConfigResolver with SearchService
- Update SearchService.__init__ to accept KBConfigResolver
- Call resolve_retrieval_config() in search methods
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.search_service import SearchService
from app.services.kb_config_resolver import KBConfigResolver
from app.schemas.kb_settings import RetrievalConfig, RetrievalMethod


@pytest.fixture
def mock_kb_config_resolver():
    """Mock KBConfigResolver with configurable return values."""
    resolver = AsyncMock(spec=KBConfigResolver)
    resolver.resolve_retrieval_config = AsyncMock(
        return_value=RetrievalConfig(
            top_k=10,
            similarity_threshold=0.7,
            method=RetrievalMethod.VECTOR,
            mmr_enabled=False,
            mmr_lambda=0.5,
        )
    )
    return resolver


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    client = AsyncMock()
    client.search = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    service = AsyncMock()
    service.embed = AsyncMock(return_value=[0.1] * 384)
    return service


@pytest.fixture
def search_service(mock_kb_config_resolver, mock_qdrant_client, mock_embedding_service):
    """SearchService with mocked dependencies."""
    return SearchService(
        qdrant_client=mock_qdrant_client,
        embedding_service=mock_embedding_service,
        kb_config_resolver=mock_kb_config_resolver,
    )


class TestSearchServiceKBConfigIntegration:
    """[P0] Test SearchService uses KB retrieval config."""

    @pytest.mark.asyncio
    async def test_search_uses_kb_top_k(
        self, search_service, mock_kb_config_resolver, mock_qdrant_client
    ):
        """
        GIVEN: KB with custom top_k=25
        WHEN: search() is called
        THEN: Qdrant query uses top_k=25
        AC-7.17.1
        """
        kb_id = uuid4()
        mock_kb_config_resolver.resolve_retrieval_config.return_value = RetrievalConfig(
            top_k=25,
            similarity_threshold=0.7,
            method=RetrievalMethod.VECTOR,
        )

        await search_service.search(kb_id=kb_id, query="test query")

        # Verify KBConfigResolver was called
        mock_kb_config_resolver.resolve_retrieval_config.assert_called_once_with(
            kb_id=kb_id,
            request_overrides=None,
        )

        # Verify Qdrant received correct top_k
        mock_qdrant_client.search.assert_called_once()
        call_args = mock_qdrant_client.search.call_args
        assert call_args.kwargs.get("limit") == 25 or call_args[1].get("limit") == 25

    @pytest.mark.asyncio
    async def test_search_uses_kb_similarity_threshold(
        self, search_service, mock_kb_config_resolver, mock_qdrant_client
    ):
        """
        GIVEN: KB with custom similarity_threshold=0.85
        WHEN: search() is called
        THEN: Results are filtered by threshold 0.85
        AC-7.17.1
        """
        kb_id = uuid4()
        mock_kb_config_resolver.resolve_retrieval_config.return_value = RetrievalConfig(
            top_k=10,
            similarity_threshold=0.85,
            method=RetrievalMethod.VECTOR,
        )

        # Mock results with various scores
        mock_qdrant_client.search.return_value = [
            MagicMock(score=0.9, payload={"content": "high"}),
            MagicMock(score=0.8, payload={"content": "medium"}),  # Below threshold
            MagicMock(score=0.7, payload={"content": "low"}),  # Below threshold
        ]

        results = await search_service.search(kb_id=kb_id, query="test query")

        # Only results above 0.85 threshold should be returned
        assert len(results) == 1
        assert results[0].score >= 0.85

    @pytest.mark.asyncio
    async def test_search_uses_kb_retrieval_method(
        self, search_service, mock_kb_config_resolver
    ):
        """
        GIVEN: KB with retrieval method=hybrid
        WHEN: search() is called
        THEN: Hybrid search is performed
        AC-7.17.1
        """
        kb_id = uuid4()
        mock_kb_config_resolver.resolve_retrieval_config.return_value = RetrievalConfig(
            top_k=10,
            similarity_threshold=0.7,
            method=RetrievalMethod.HYBRID,
            hybrid_alpha=0.6,
        )

        with patch.object(search_service, "_hybrid_search", new_callable=AsyncMock) as mock_hybrid:
            mock_hybrid.return_value = []
            await search_service.search(kb_id=kb_id, query="test query")

            mock_hybrid.assert_called_once()


class TestSearchServiceRequestOverrides:
    """[P0] Test request overrides take precedence."""

    @pytest.mark.asyncio
    async def test_request_top_k_overrides_kb_config(
        self, search_service, mock_kb_config_resolver, mock_qdrant_client
    ):
        """
        GIVEN: KB with top_k=10
        WHEN: search() is called with request_top_k=50
        THEN: Qdrant query uses top_k=50 (request wins)
        AC-7.17.5
        """
        kb_id = uuid4()

        # KB config has top_k=10
        mock_kb_config_resolver.resolve_retrieval_config.return_value = RetrievalConfig(
            top_k=50,  # Resolver should return overridden value
        )

        await search_service.search(
            kb_id=kb_id,
            query="test query",
            top_k=50,  # Request override
        )

        # Verify resolver was called with override
        mock_kb_config_resolver.resolve_retrieval_config.assert_called_once_with(
            kb_id=kb_id,
            request_overrides={"top_k": 50},
        )

    @pytest.mark.asyncio
    async def test_request_threshold_overrides_kb_config(
        self, search_service, mock_kb_config_resolver
    ):
        """
        GIVEN: KB with similarity_threshold=0.7
        WHEN: search() is called with request_threshold=0.9
        THEN: Results filtered by 0.9 (request wins)
        AC-7.17.5
        """
        kb_id = uuid4()

        await search_service.search(
            kb_id=kb_id,
            query="test query",
            similarity_threshold=0.9,  # Request override
        )

        # Verify resolver received override
        mock_kb_config_resolver.resolve_retrieval_config.assert_called_once()
        call_kwargs = mock_kb_config_resolver.resolve_retrieval_config.call_args.kwargs
        assert call_kwargs["request_overrides"]["similarity_threshold"] == 0.9


class TestSearchServiceAuditLogging:
    """[P1] Test audit logging includes effective config."""

    @pytest.mark.asyncio
    async def test_search_logs_effective_config(
        self, search_service, mock_kb_config_resolver
    ):
        """
        GIVEN: Search is performed
        WHEN: Audit log is created
        THEN: effective_config snapshot is included
        AC-7.17.6
        """
        kb_id = uuid4()
        resolved_config = RetrievalConfig(
            top_k=25,
            similarity_threshold=0.8,
            method=RetrievalMethod.HYBRID,
        )
        mock_kb_config_resolver.resolve_retrieval_config.return_value = resolved_config

        with patch("app.services.search_service.audit_service") as mock_audit:
            await search_service.search(kb_id=kb_id, query="test query")

            # Verify audit log includes effective_config
            mock_audit.log_search.assert_called_once()
            call_kwargs = mock_audit.log_search.call_args.kwargs
            assert "effective_config" in call_kwargs
            assert call_kwargs["effective_config"]["top_k"] == 25
            assert call_kwargs["effective_config"]["similarity_threshold"] == 0.8


class TestSearchServiceDefaultsWhenNoKBConfig:
    """[P2] Test SearchService uses defaults when KB has no custom settings."""

    @pytest.mark.asyncio
    async def test_search_uses_defaults_for_unconfigured_kb(
        self, search_service, mock_kb_config_resolver, mock_qdrant_client
    ):
        """
        GIVEN: KB with no custom retrieval settings
        WHEN: search() is called
        THEN: System defaults are used (top_k=10, threshold=0.7)
        """
        kb_id = uuid4()

        # Resolver returns defaults
        mock_kb_config_resolver.resolve_retrieval_config.return_value = RetrievalConfig()

        await search_service.search(kb_id=kb_id, query="test query")

        mock_qdrant_client.search.assert_called_once()
        call_args = mock_qdrant_client.search.call_args
        assert call_args.kwargs.get("limit", call_args[1].get("limit", None)) == 10
```

### 2. GenerationService Unit Tests (pytest)

**File:** `backend/tests/unit/test_generation_service_kb_config.py`

```python
"""
Story 7-17 ATDD: GenerationService KB Config Integration Tests
Generated: 2025-12-09
Status: RED - Implementation required to pass

Required implementation:
- Integrate KBConfigResolver with GenerationService
- Update GenerationService.__init__ to accept KBConfigResolver
- Call resolve_generation_config() and get_kb_system_prompt() in generate methods
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.generation_service import GenerationService
from app.services.kb_config_resolver import KBConfigResolver
from app.schemas.kb_settings import GenerationConfig


@pytest.fixture
def mock_kb_config_resolver():
    """Mock KBConfigResolver with configurable return values."""
    resolver = AsyncMock(spec=KBConfigResolver)
    resolver.resolve_generation_config = AsyncMock(
        return_value=GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            max_tokens=2048,
        )
    )
    resolver.get_kb_system_prompt = AsyncMock(return_value=None)
    return resolver


@pytest.fixture
def mock_litellm_client():
    """Mock LiteLLM client."""
    client = AsyncMock()
    client.completion = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="Generated response"))]
        )
    )
    return client


@pytest.fixture
def generation_service(mock_kb_config_resolver, mock_litellm_client):
    """GenerationService with mocked dependencies."""
    return GenerationService(
        litellm_client=mock_litellm_client,
        kb_config_resolver=mock_kb_config_resolver,
    )


class TestGenerationServiceKBConfigIntegration:
    """[P0] Test GenerationService uses KB generation config."""

    @pytest.mark.asyncio
    async def test_generate_uses_kb_temperature(
        self, generation_service, mock_kb_config_resolver, mock_litellm_client
    ):
        """
        GIVEN: KB with custom temperature=0.3
        WHEN: generate() is called
        THEN: LiteLLM call uses temperature=0.3
        AC-7.17.2
        """
        kb_id = uuid4()
        mock_kb_config_resolver.resolve_generation_config.return_value = GenerationConfig(
            temperature=0.3,
            top_p=0.9,
            max_tokens=2048,
        )

        await generation_service.generate(
            kb_id=kb_id,
            prompt="Generate a summary",
            context="Document context here",
        )

        # Verify LiteLLM received correct temperature
        mock_litellm_client.completion.assert_called_once()
        call_kwargs = mock_litellm_client.completion.call_args.kwargs
        assert call_kwargs["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_generate_uses_kb_top_p(
        self, generation_service, mock_kb_config_resolver, mock_litellm_client
    ):
        """
        GIVEN: KB with custom top_p=0.95
        WHEN: generate() is called
        THEN: LiteLLM call uses top_p=0.95
        AC-7.17.2
        """
        kb_id = uuid4()
        mock_kb_config_resolver.resolve_generation_config.return_value = GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            max_tokens=2048,
        )

        await generation_service.generate(
            kb_id=kb_id,
            prompt="Generate a summary",
            context="Document context here",
        )

        call_kwargs = mock_litellm_client.completion.call_args.kwargs
        assert call_kwargs["top_p"] == 0.95

    @pytest.mark.asyncio
    async def test_generate_uses_kb_max_tokens(
        self, generation_service, mock_kb_config_resolver, mock_litellm_client
    ):
        """
        GIVEN: KB with custom max_tokens=4096
        WHEN: generate() is called
        THEN: LiteLLM call uses max_tokens=4096
        AC-7.17.2
        """
        kb_id = uuid4()
        mock_kb_config_resolver.resolve_generation_config.return_value = GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            max_tokens=4096,
        )

        await generation_service.generate(
            kb_id=kb_id,
            prompt="Generate a summary",
            context="Document context here",
        )

        call_kwargs = mock_litellm_client.completion.call_args.kwargs
        assert call_kwargs["max_tokens"] == 4096


class TestGenerationServiceSystemPrompt:
    """[P0] Test GenerationService uses KB system prompt."""

    @pytest.mark.asyncio
    async def test_generate_uses_kb_system_prompt(
        self, generation_service, mock_kb_config_resolver, mock_litellm_client
    ):
        """
        GIVEN: KB with custom system_prompt
        WHEN: generate() is called
        THEN: LiteLLM receives KB system prompt
        AC-7.17.3
        """
        kb_id = uuid4()
        custom_prompt = "You are a legal assistant. Always cite sources."
        mock_kb_config_resolver.get_kb_system_prompt.return_value = custom_prompt

        await generation_service.generate(
            kb_id=kb_id,
            prompt="Generate a summary",
            context="Document context here",
        )

        # Verify system prompt was used
        call_kwargs = mock_litellm_client.completion.call_args.kwargs
        messages = call_kwargs["messages"]
        system_message = next((m for m in messages if m["role"] == "system"), None)

        assert system_message is not None
        assert custom_prompt in system_message["content"]

    @pytest.mark.asyncio
    async def test_generate_uses_default_prompt_when_kb_has_none(
        self, generation_service, mock_kb_config_resolver, mock_litellm_client
    ):
        """
        GIVEN: KB with no custom system_prompt
        WHEN: generate() is called
        THEN: Default system prompt is used
        AC-7.17.3
        """
        kb_id = uuid4()
        mock_kb_config_resolver.get_kb_system_prompt.return_value = None

        await generation_service.generate(
            kb_id=kb_id,
            prompt="Generate a summary",
            context="Document context here",
        )

        call_kwargs = mock_litellm_client.completion.call_args.kwargs
        messages = call_kwargs["messages"]
        system_message = next((m for m in messages if m["role"] == "system"), None)

        # Should have some default prompt
        assert system_message is not None
        assert len(system_message["content"]) > 0


class TestGenerationServiceRequestOverrides:
    """[P0] Test request overrides take precedence."""

    @pytest.mark.asyncio
    async def test_request_temperature_overrides_kb_config(
        self, generation_service, mock_kb_config_resolver, mock_litellm_client
    ):
        """
        GIVEN: KB with temperature=0.7
        WHEN: generate() is called with temperature=1.5
        THEN: LiteLLM uses temperature=1.5 (request wins)
        AC-7.17.5
        """
        kb_id = uuid4()

        # Resolver returns overridden value
        mock_kb_config_resolver.resolve_generation_config.return_value = GenerationConfig(
            temperature=1.5,  # Overridden
        )

        await generation_service.generate(
            kb_id=kb_id,
            prompt="Generate a summary",
            context="Document context here",
            temperature=1.5,  # Request override
        )

        # Verify resolver was called with override
        mock_kb_config_resolver.resolve_generation_config.assert_called_once()
        call_kwargs = mock_kb_config_resolver.resolve_generation_config.call_args.kwargs
        assert call_kwargs["request_overrides"]["temperature"] == 1.5

    @pytest.mark.asyncio
    async def test_request_max_tokens_overrides_kb_config(
        self, generation_service, mock_kb_config_resolver, mock_litellm_client
    ):
        """
        GIVEN: KB with max_tokens=2048
        WHEN: generate() is called with max_tokens=8000
        THEN: LiteLLM uses max_tokens=8000 (request wins)
        AC-7.17.5
        """
        kb_id = uuid4()

        mock_kb_config_resolver.resolve_generation_config.return_value = GenerationConfig(
            max_tokens=8000,
        )

        await generation_service.generate(
            kb_id=kb_id,
            prompt="Generate a summary",
            context="Document context here",
            max_tokens=8000,
        )

        call_kwargs = mock_litellm_client.completion.call_args.kwargs
        assert call_kwargs["max_tokens"] == 8000


class TestGenerationServiceAuditLogging:
    """[P1] Test audit logging includes effective config."""

    @pytest.mark.asyncio
    async def test_generate_logs_effective_config(
        self, generation_service, mock_kb_config_resolver
    ):
        """
        GIVEN: Generation is performed
        WHEN: Audit log is created
        THEN: effective_config snapshot is included
        AC-7.17.6
        """
        kb_id = uuid4()
        resolved_config = GenerationConfig(
            temperature=0.3,
            top_p=0.95,
            max_tokens=4096,
        )
        mock_kb_config_resolver.resolve_generation_config.return_value = resolved_config

        with patch("app.services.generation_service.audit_service") as mock_audit:
            await generation_service.generate(
                kb_id=kb_id,
                prompt="Generate a summary",
                context="Document context here",
            )

            # Verify audit log includes effective_config
            mock_audit.log_generation.assert_called_once()
            call_kwargs = mock_audit.log_generation.call_args.kwargs
            assert "effective_config" in call_kwargs
            assert call_kwargs["effective_config"]["temperature"] == 0.3
            assert call_kwargs["effective_config"]["top_p"] == 0.95
            assert call_kwargs["effective_config"]["max_tokens"] == 4096
```

### 3. Document Worker Unit Tests (pytest)

**File:** `backend/tests/unit/test_document_worker_kb_config.py`

```python
"""
Story 7-17 ATDD: Document Worker KB Config Integration Tests
Generated: 2025-12-09
Status: RED - Implementation required to pass

Required implementation:
- Integrate KBConfigResolver with document worker tasks
- Call resolve_chunking_config() in _chunk_embed_index
- Pass config to chunk_document()
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.workers.document_tasks import _chunk_embed_index
from app.services.kb_config_resolver import KBConfigResolver
from app.schemas.kb_settings import ChunkingConfig, ChunkingStrategy


@pytest.fixture
def mock_kb_config_resolver():
    """Mock KBConfigResolver with configurable return values."""
    resolver = AsyncMock(spec=KBConfigResolver)
    resolver.resolve_chunking_config = AsyncMock(
        return_value=ChunkingConfig(
            strategy=ChunkingStrategy.RECURSIVE,
            chunk_size=512,
            chunk_overlap=50,
        )
    )
    return resolver


class TestDocumentWorkerKBConfigIntegration:
    """[P0] Test document worker uses KB chunking config."""

    @pytest.mark.asyncio
    async def test_chunk_uses_kb_chunk_size(self, mock_kb_config_resolver):
        """
        GIVEN: KB with custom chunk_size=1000
        WHEN: Document is processed
        THEN: Chunking uses chunk_size=1000
        AC-7.17.4
        """
        kb_id = uuid4()
        document_id = uuid4()

        mock_kb_config_resolver.resolve_chunking_config.return_value = ChunkingConfig(
            strategy=ChunkingStrategy.RECURSIVE,
            chunk_size=1000,
            chunk_overlap=200,
        )

        with patch("app.workers.document_tasks.chunk_document") as mock_chunk:
            mock_chunk.return_value = []
            with patch("app.workers.document_tasks.get_kb_config_resolver") as mock_get:
                mock_get.return_value = mock_kb_config_resolver

                await _chunk_embed_index(
                    document_id=str(document_id),
                    kb_id=str(kb_id),
                    content="Document content here",
                )

                # Verify chunk_document received correct chunk_size
                mock_chunk.assert_called_once()
                call_kwargs = mock_chunk.call_args.kwargs
                assert call_kwargs["chunk_size"] == 1000

    @pytest.mark.asyncio
    async def test_chunk_uses_kb_chunk_overlap(self, mock_kb_config_resolver):
        """
        GIVEN: KB with custom chunk_overlap=200
        WHEN: Document is processed
        THEN: Chunking uses chunk_overlap=200
        AC-7.17.4
        """
        kb_id = uuid4()
        document_id = uuid4()

        mock_kb_config_resolver.resolve_chunking_config.return_value = ChunkingConfig(
            strategy=ChunkingStrategy.RECURSIVE,
            chunk_size=512,
            chunk_overlap=200,
        )

        with patch("app.workers.document_tasks.chunk_document") as mock_chunk:
            mock_chunk.return_value = []
            with patch("app.workers.document_tasks.get_kb_config_resolver") as mock_get:
                mock_get.return_value = mock_kb_config_resolver

                await _chunk_embed_index(
                    document_id=str(document_id),
                    kb_id=str(kb_id),
                    content="Document content here",
                )

                call_kwargs = mock_chunk.call_args.kwargs
                assert call_kwargs["chunk_overlap"] == 200

    @pytest.mark.asyncio
    async def test_chunk_uses_kb_chunking_strategy(self, mock_kb_config_resolver):
        """
        GIVEN: KB with chunking strategy=semantic
        WHEN: Document is processed
        THEN: Semantic chunking is used
        AC-7.17.4
        """
        kb_id = uuid4()
        document_id = uuid4()

        mock_kb_config_resolver.resolve_chunking_config.return_value = ChunkingConfig(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=512,
            chunk_overlap=50,
        )

        with patch("app.workers.document_tasks.chunk_document") as mock_chunk:
            mock_chunk.return_value = []
            with patch("app.workers.document_tasks.get_kb_config_resolver") as mock_get:
                mock_get.return_value = mock_kb_config_resolver

                await _chunk_embed_index(
                    document_id=str(document_id),
                    kb_id=str(kb_id),
                    content="Document content here",
                )

                call_kwargs = mock_chunk.call_args.kwargs
                assert call_kwargs["strategy"] == "semantic"


class TestDocumentWorkerDefaultsWhenNoKBConfig:
    """[P2] Test document worker uses defaults when KB has no custom settings."""

    @pytest.mark.asyncio
    async def test_chunk_uses_defaults_for_unconfigured_kb(
        self, mock_kb_config_resolver
    ):
        """
        GIVEN: KB with no custom chunking settings
        WHEN: Document is processed
        THEN: System defaults are used (chunk_size=512, overlap=50)
        """
        kb_id = uuid4()
        document_id = uuid4()

        # Resolver returns defaults
        mock_kb_config_resolver.resolve_chunking_config.return_value = ChunkingConfig()

        with patch("app.workers.document_tasks.chunk_document") as mock_chunk:
            mock_chunk.return_value = []
            with patch("app.workers.document_tasks.get_kb_config_resolver") as mock_get:
                mock_get.return_value = mock_kb_config_resolver

                await _chunk_embed_index(
                    document_id=str(document_id),
                    kb_id=str(kb_id),
                    content="Document content here",
                )

                call_kwargs = mock_chunk.call_args.kwargs
                assert call_kwargs["chunk_size"] == 512
                assert call_kwargs["chunk_overlap"] == 50
```

### 4. Integration Tests (pytest)

**File:** `backend/tests/integration/test_kb_config_integration.py`

```python
"""
Story 7-17 ATDD: Full KB Config Flow Integration Tests
Generated: 2025-12-09
Status: RED - Implementation required to pass

Tests full flow: Create KB with settings → Search/Generate → Verify config used
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestFullKBConfigFlow:
    """[P0] Full integration tests for KB config flow."""

    @pytest.mark.asyncio
    async def test_search_with_kb_custom_retrieval_config(
        self, client: AsyncClient, auth_headers: dict, test_kb_with_documents
    ):
        """
        GIVEN: KB with custom retrieval config (top_k=5, threshold=0.9)
        WHEN: Search is performed
        THEN: Results respect the KB config
        AC-7.17.1
        """
        kb_id = test_kb_with_documents["kb_id"]

        # Update KB settings
        settings_response = await client.put(
            f"/api/v1/knowledge-bases/{kb_id}/settings",
            headers=auth_headers,
            json={
                "retrieval": {
                    "top_k": 5,
                    "similarity_threshold": 0.9,
                    "method": "vector",
                }
            },
        )
        assert settings_response.status_code == 200

        # Perform search
        search_response = await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/search",
            headers=auth_headers,
            json={"query": "test query"},
        )
        assert search_response.status_code == 200

        results = search_response.json()
        # Should return at most 5 results
        assert len(results["results"]) <= 5
        # All results should have score >= 0.9
        for result in results["results"]:
            assert result["score"] >= 0.9

    @pytest.mark.asyncio
    async def test_search_request_override_wins_over_kb_config(
        self, client: AsyncClient, auth_headers: dict, test_kb_with_documents
    ):
        """
        GIVEN: KB with top_k=5
        WHEN: Search is performed with top_k=20 in request
        THEN: Returns up to 20 results (request wins)
        AC-7.17.5
        """
        kb_id = test_kb_with_documents["kb_id"]

        # Update KB settings
        await client.put(
            f"/api/v1/knowledge-bases/{kb_id}/settings",
            headers=auth_headers,
            json={"retrieval": {"top_k": 5}},
        )

        # Perform search with override
        search_response = await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/search",
            headers=auth_headers,
            json={"query": "test query", "top_k": 20},
        )
        assert search_response.status_code == 200

        # Should respect request override, not KB config
        results = search_response.json()
        # If more than 5 results, request override worked
        assert results.get("effective_config", {}).get("top_k") == 20

    @pytest.mark.asyncio
    async def test_generation_with_kb_custom_generation_config(
        self, client: AsyncClient, auth_headers: dict, test_kb_with_documents
    ):
        """
        GIVEN: KB with custom generation config (temperature=0.3)
        WHEN: Generation is performed
        THEN: Generation uses temperature=0.3
        AC-7.17.2
        """
        kb_id = test_kb_with_documents["kb_id"]

        # Update KB settings
        await client.put(
            f"/api/v1/knowledge-bases/{kb_id}/settings",
            headers=auth_headers,
            json={
                "generation": {
                    "temperature": 0.3,
                    "max_tokens": 1000,
                }
            },
        )

        # Perform generation (via chat or generate endpoint)
        gen_response = await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/generate",
            headers=auth_headers,
            json={"prompt": "Summarize the documents"},
        )
        assert gen_response.status_code == 200

        data = gen_response.json()
        # Should include effective_config in response
        assert data.get("effective_config", {}).get("temperature") == 0.3

    @pytest.mark.asyncio
    async def test_generation_with_kb_system_prompt(
        self, client: AsyncClient, auth_headers: dict, test_kb_with_documents
    ):
        """
        GIVEN: KB with custom system_prompt
        WHEN: Generation is performed
        THEN: Custom system prompt is used
        AC-7.17.3
        """
        kb_id = test_kb_with_documents["kb_id"]
        custom_prompt = "You are a legal advisor. Always cite specific laws."

        # Update KB settings with custom system prompt
        await client.put(
            f"/api/v1/knowledge-bases/{kb_id}/settings",
            headers=auth_headers,
            json={
                "prompts": {
                    "system_prompt": custom_prompt,
                }
            },
        )

        # Perform generation
        gen_response = await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/generate",
            headers=auth_headers,
            json={"prompt": "What are the requirements?"},
        )
        assert gen_response.status_code == 200

        # The effective system prompt should be the custom one
        data = gen_response.json()
        assert data.get("effective_config", {}).get("system_prompt") == custom_prompt


class TestAuditLoggingWithEffectiveConfig:
    """[P1] Test audit logs include effective_config."""

    @pytest.mark.asyncio
    async def test_search_audit_includes_effective_config(
        self, client: AsyncClient, auth_headers: dict, test_kb_with_documents
    ):
        """
        GIVEN: KB with custom retrieval config
        WHEN: Search is performed
        THEN: Audit log entry includes effective_config
        AC-7.17.6
        """
        kb_id = test_kb_with_documents["kb_id"]

        # Update KB settings
        await client.put(
            f"/api/v1/knowledge-bases/{kb_id}/settings",
            headers=auth_headers,
            json={"retrieval": {"top_k": 15}},
        )

        # Perform search
        await client.post(
            f"/api/v1/knowledge-bases/{kb_id}/search",
            headers=auth_headers,
            json={"query": "test query"},
        )

        # Fetch audit logs
        audit_response = await client.get(
            f"/api/v1/admin/audit-logs",
            headers=auth_headers,
            params={"action": "search", "kb_id": str(kb_id)},
        )
        assert audit_response.status_code == 200

        logs = audit_response.json()["items"]
        assert len(logs) > 0

        latest_log = logs[0]
        assert "effective_config" in latest_log.get("details", {})
        assert latest_log["details"]["effective_config"]["top_k"] == 15
```

---

## Required Implementation Changes

### Files to Modify

| File | Change Required |
|------|-----------------|
| `backend/app/services/search_service.py` | Add KBConfigResolver dependency, call `resolve_retrieval_config()` |
| `backend/app/services/generation_service.py` | Add KBConfigResolver dependency, call `resolve_generation_config()` and `get_kb_system_prompt()` |
| `backend/app/workers/document_tasks.py` | Call `resolve_chunking_config()` in `_chunk_embed_index` |
| `backend/app/services/audit_service.py` | Add `effective_config` field to log entries |
| `backend/app/core/dependencies.py` | Add `get_kb_config_resolver` factory |

### Integration Points

```python
# In SearchService.__init__
def __init__(
    self,
    qdrant_client: QdrantClient,
    embedding_service: EmbeddingService,
    kb_config_resolver: KBConfigResolver,  # NEW
):
    self.kb_config_resolver = kb_config_resolver

# In SearchService.search
async def search(self, kb_id: UUID, query: str, **overrides):
    retrieval_config = await self.kb_config_resolver.resolve_retrieval_config(
        kb_id=kb_id,
        request_overrides=overrides,
    )
    # Use retrieval_config.top_k, .similarity_threshold, .method
```

---

## Test Execution

```bash
# SearchService unit tests
cd backend && .venv/bin/pytest tests/unit/test_search_service_kb_config.py -v

# GenerationService unit tests
cd backend && .venv/bin/pytest tests/unit/test_generation_service_kb_config.py -v

# Document worker unit tests
cd backend && .venv/bin/pytest tests/unit/test_document_worker_kb_config.py -v

# Integration tests
cd backend && .venv/bin/pytest tests/integration/test_kb_config_integration.py -v

# Run all 7-17 tests
cd backend && .venv/bin/pytest -k "kb_config" -v
```

---

## Definition of Done

- [ ] All SearchService unit tests pass (0 → green)
- [ ] All GenerationService unit tests pass (0 → green)
- [ ] All Document worker unit tests pass (0 → green)
- [ ] All integration tests pass (0 → green)
- [ ] SearchService uses KB retrieval config (top_k, threshold, method)
- [ ] GenerationService uses KB generation config (temperature, top_p, max_tokens)
- [ ] GenerationService uses KB system_prompt
- [ ] Document worker uses KB chunking config (chunk_size, overlap, strategy)
- [ ] Request overrides take precedence over KB settings
- [ ] Audit logs include effective_config snapshot
- [ ] Dependency injection updated for all services
- [ ] Three-layer config precedence working (request > KB > system defaults)
