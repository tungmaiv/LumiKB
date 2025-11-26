# ATDD Checklist: Story 3.1 - Semantic Search Backend

**Date:** 2025-11-25
**Story ID:** 3.1
**Status:** RED Phase (Tests Failing - Implementation Pending)

---

## Story Summary

**Epic**: 3 - Semantic Search & Citations
**Story**: 3.1 - Semantic Search Backend

**Description:**
Implement semantic search API endpoint that allows users to search across permitted knowledge bases using natural language queries. Search uses vector embeddings (via LiteLLM) and Qdrant for semantic relevance, not just keyword matching.

**Risk Level:** HIGH
- R-001: LLM citation quality (Score: 9 - BLOCK)
- R-002: Citation mapping errors (Score: 6 - MITIGATE)
- R-003: Cross-KB search performance (Score: 6 - MITIGATE)
- R-006: Permission bypass (Score: 3 - DOCUMENT, but security-critical)

---

## Acceptance Criteria Breakdown

| AC ID | Requirement | Test Level | Test File | Status |
|-------|------------|------------|-----------|--------|
| AC-3.1.1 | Natural language search returns relevant chunks | Integration | `test_semantic_search.py::test_search_with_natural_language_query_returns_results` | ❌ RED |
| AC-3.1.2 | Semantic relevance (not keyword matching) | Integration | `test_semantic_search.py::test_search_returns_semantically_relevant_results_not_keywords` | ❌ RED |
| AC-3.1.3 | Permission enforcement (cross-KB) | Integration | `test_semantic_search.py::test_cross_kb_search_only_returns_permitted_kbs` | ❌ RED |
| AC-3.1.3 | Permission enforcement (403 on unauthorized) | Integration | `test_semantic_search.py::test_search_with_unauthorized_kb_id_returns_403` | ❌ RED |
| AC-3.1.4 | Performance < 3s p95 (basic smoke test) | Integration | `test_semantic_search.py::test_search_performance_basic_timing` | ❌ RED |
| AC-3.1.5 | Audit logging for search queries | Integration | `test_semantic_search.py::test_search_query_logged_to_audit_events` | ❌ RED |

**Total Tests**: 6 integration tests

---

## Test Files Created

### Integration Tests

**File**: `backend/tests/integration/test_semantic_search.py`

**Tests:**
1. ✅ `test_search_with_natural_language_query_returns_results` - Validates search endpoint returns results with required fields
2. ✅ `test_search_returns_semantically_relevant_results_not_keywords` - Verifies vector search quality (semantic > keyword)
3. ✅ `test_cross_kb_search_only_returns_permitted_kbs` - Security: cross-tenant isolation
4. ✅ `test_search_with_unauthorized_kb_id_returns_403` - Security: permission enforcement
5. ✅ `test_search_performance_basic_timing` - Basic performance smoke test (< 5s)
6. ✅ `test_search_query_logged_to_audit_events` - Compliance: audit logging

**Pattern**: Given-When-Then structure, follows existing test style from Epic 2

---

## Supporting Infrastructure

### Test Fixtures

**Created in `test_semantic_search.py`:**

- `search_user_data` - Test user registration data
- `registered_search_user` - Registered test user for search
- `authenticated_search_client` - Authenticated HTTP client
- `second_search_user` - Second user for cross-tenant permission tests
- `indexed_kb_with_docs` - KB with indexed documents (TODO: needs helper for awaiting indexing)

**NOTE**: `indexed_kb_with_docs` fixture is scaffolded but incomplete. Needs helper function to:
1. Upload documents via `/api/v1/knowledge-bases/{kb_id}/documents`
2. Poll document status until `status='ready'`
3. Verify chunks are indexed in Qdrant

### Data Factories

**Existing factories (reused from Epic 2):**
- `create_kb_data()` - Generate KB creation payload
- `create_registration_data()` - Generate user registration payload
- `create_document_data()` - Generate document upload payload (needed for fixture completion)

**No new factories required for Story 3.1.**

### Mock Requirements

None - Integration tests use real services via testcontainers:
- PostgreSQL (testcontainer)
- Redis (testcontainer)
- Qdrant (requires setup - see notes below)
- LiteLLM (requires setup - see notes below)

---

## Required Service Setup

### Qdrant Integration

**Status**: NOT YET CONFIGURED for tests

**Requirements**:
1. Add Qdrant testcontainer to `backend/tests/integration/conftest.py`
2. Create fixture `qdrant_client` with connection to test Qdrant instance
3. Mock or inject Qdrant client into search service

**Example**:
```python
@pytest.fixture(scope="session")
def qdrant_container():
    """Session-scoped Qdrant container."""
    from testcontainers.core.generic import GenericContainer

    with GenericContainer("qdrant/qdrant:latest").with_exposed_ports(6333) as qdrant:
        yield qdrant

@pytest.fixture
async def qdrant_client(qdrant_container):
    """Qdrant client for test instance."""
    from qdrant_client import AsyncQdrantClient

    host = qdrant_container.get_container_host_ip()
    port = qdrant_container.get_exposed_port(6333)

    client = AsyncQdrantClient(host=host, port=port)
    yield client

    # Cleanup: delete test collections
    collections = await client.get_collections()
    for collection in collections.collections:
        if collection.name.startswith("test_"):
            await client.delete_collection(collection.name)
```

### LiteLLM Mock

**Status**: NOT YET CONFIGURED for tests

**Requirements**:
1. Mock LiteLLM embedding responses for deterministic tests
2. Avoid real API calls during tests (cost + speed)

**Example**:
```python
@pytest.fixture
def mock_litellm_embedding(monkeypatch):
    """Mock LiteLLM embedding to return deterministic vectors."""
    async def mock_embedding(text: str, model: str = "text-embedding-3-small"):
        # Return fake 1536-dim vector (OpenAI embedding size)
        import numpy as np
        return np.random.rand(1536).tolist()

    monkeypatch.setattr("app.integrations.litellm_client.get_embedding", mock_embedding)
```

---

## Implementation Checklist

### RED Phase (Complete)

- [x] All tests written and failing
- [x] Fixtures scaffolded (some incomplete - see notes)
- [x] Existing factories identified (no new ones needed)
- [x] Service mock requirements documented

### GREEN Phase (DEV Team - Implementation Tasks)

#### Task 1: Create Search API Endpoint

- [ ] Create `backend/app/api/v1/search.py`
- [ ] Define `POST /api/v1/search` endpoint
- [ ] Request schema: `{ query: str, kb_ids: list[int] | None }`
- [ ] Response schema: `{ results: list[SearchResult] }`
- [ ] Register route in `backend/app/api/v1/__init__.py`
- [ ] Run test: `test_search_with_natural_language_query_returns_results`
- [ ] ✅ Test passes (basic endpoint created)

#### Task 2: Integrate LiteLLM for Query Embedding

- [ ] Create `backend/app/services/search_service.py`
- [ ] Implement `embed_query(query: str) -> list[float]`
- [ ] Use `app.integrations.litellm_client` (from Epic 2)
- [ ] Call `litellm.embedding(model="text-embedding-3-small", input=query)`
- [ ] Cache query embeddings in Redis (1hr TTL) - optional optimization
- [ ] Run test: `test_search_with_natural_language_query_returns_results`
- [ ] ✅ Test passes (query embedding works)

#### Task 3: Integrate Qdrant for Vector Search

- [ ] In `search_service.py`, implement `search_vectors(embedding, kb_ids, limit=10)`
- [ ] Use `app.integrations.qdrant_client` (from Epic 2)
- [ ] Query Qdrant collections (one collection per KB)
- [ ] If `kb_ids=None`, search ALL permitted KBs (see Task 4)
- [ ] Return chunks with relevance_score (vector similarity)
- [ ] Run test: `test_search_returns_semantically_relevant_results_not_keywords`
- [ ] ✅ Test passes (semantic search works)

#### Task 4: Implement Permission Enforcement

- [ ] In `search_service.py`, add `filter_permitted_kbs(user_id, kb_ids)`
- [ ] Query `kb_permissions` table for READ or WRITE access
- [ ] If `kb_ids=None`, fetch all permitted KB IDs
- [ ] If `kb_ids` provided, validate user has READ on ALL requested KBs
- [ ] Return 403 if any KB is unauthorized
- [ ] Run test: `test_cross_kb_search_only_returns_permitted_kbs`
- [ ] Run test: `test_search_with_unauthorized_kb_id_returns_403`
- [ ] ✅ Tests pass (permission enforcement works)

#### Task 5: Implement Cross-KB Search with Parallel Queries

- [ ] In `search_service.py`, implement parallel Qdrant queries
- [ ] Use `asyncio.gather()` to query multiple collections concurrently
- [ ] Merge results from all KBs
- [ ] Re-rank by relevance_score (descending)
- [ ] Limit to top N results (default 10)
- [ ] Run test: `test_search_performance_basic_timing`
- [ ] ✅ Test passes (performance acceptable)

#### Task 6: Add Audit Logging

- [ ] In search endpoint, log to `audit.events` after search completes
- [ ] Event type: `search.query`
- [ ] Payload: `{ query, kb_ids, user_id, result_count, elapsed_ms }`
- [ ] Use existing audit logging pattern from Epic 2
- [ ] Run test: `test_search_query_logged_to_audit_events`
- [ ] ✅ Test passes (audit logging works)

#### Task 7: Complete Test Fixture (indexed_kb_with_docs)

- [ ] Create helper: `wait_for_document_indexed(kb_id, doc_id, timeout=30s)`
- [ ] Poll `/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}` until `status='ready'`
- [ ] Update `indexed_kb_with_docs` fixture to upload and index 2 test documents
- [ ] Run ALL tests again to verify end-to-end
- [ ] ✅ All tests pass (full GREEN phase)

---

## RED-GREEN-REFACTOR Workflow

### RED Phase (Complete ✅)

- ✅ All 6 tests written and failing
- ✅ Tests define expected behavior for search endpoint
- ✅ Failures due to missing implementation (endpoint doesn't exist yet)

### GREEN Phase (DEV Team - Current)

1. **Pick one failing test** (suggested order above)
2. **Implement minimal code** to make it pass
3. **Run test** to verify green
4. **Move to next test**
5. **Repeat** until all tests pass

**Execution Order**:
- Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7

### REFACTOR Phase (DEV Team - After all tests green)

1. All tests passing ✅
2. Improve code quality (extract helpers, add type hints)
3. Optimize performance (Redis caching, parallel queries)
4. Ensure tests still pass
5. Commit with message: "feat: implement semantic search API (Story 3.1)"

---

## Running Tests

### Run All Failing Tests

```bash
# From backend/ directory
pytest tests/integration/test_semantic_search.py -v

# Expected: All 6 tests FAIL (RED phase)
```

### Run Specific Test

```bash
# Test natural language search
pytest tests/integration/test_semantic_search.py::test_search_with_natural_language_query_returns_results -v

# Test permission enforcement (security-critical)
pytest tests/integration/test_semantic_search.py::test_cross_kb_search_only_returns_permitted_kbs -v
```

### Run in Headed Mode (Debug)

```bash
# Run with verbose output and stop on first failure
pytest tests/integration/test_semantic_search.py -vv -x

# Run with print statements visible
pytest tests/integration/test_semantic_search.py -s
```

### Run After Implementation

```bash
# Run full test suite to verify GREEN phase
pytest tests/integration/test_semantic_search.py -v

# Expected: All 6 tests PASS (GREEN phase)
```

---

## Required Dependencies

### Python Packages (Add to pyproject.toml if missing)

```toml
[tool.poetry.dependencies]
litellm = "^1.0.0"          # LLM API client for embeddings
qdrant-client = "^1.7.0"    # Vector database client
```

### Environment Variables (Add to .env.test)

```bash
# LiteLLM Configuration
LITELLM_MODEL=text-embedding-3-small
LITELLM_API_KEY=sk-test-...  # Use test API key or mock

# Qdrant Configuration
QDRANT_URL=http://localhost:6333  # Testcontainer will override
QDRANT_API_KEY=  # Not needed for local testcontainer
```

---

## Known Issues / TODOs

### Incomplete Fixtures

**`indexed_kb_with_docs` fixture** needs helper function:

```python
async def wait_for_document_indexed(
    client: AsyncClient,
    kb_id: int,
    doc_id: int,
    timeout: int = 30
) -> None:
    """Poll document status until indexed or timeout."""
    import asyncio

    start = time.time()
    while time.time() - start < timeout:
        response = await client.get(f"/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}")
        assert response.status_code == 200

        doc = response.json()
        if doc["status"] == "ready":
            return  # Success
        elif doc["status"] == "failed":
            raise AssertionError(f"Document indexing failed: {doc.get('error')}")

        await asyncio.sleep(1)  # Poll every 1s

    raise TimeoutError(f"Document {doc_id} not indexed after {timeout}s")
```

**Action**: Create helper in `backend/tests/support/helpers/document_helpers.py`

### Testcontainer Setup

**Qdrant testcontainer** not yet configured. Add to `backend/tests/integration/conftest.py` (see example above).

**Action**: Add `qdrant_container` and `qdrant_client` fixtures before running tests.

### LiteLLM Mocking

**LiteLLM embedding** should be mocked for deterministic tests and cost savings.

**Action**: Create `mock_litellm_embedding` fixture (see example above).

---

## Next Steps for DEV Team

### Immediate Actions

1. **Review this checklist** and ask questions (Slack #epic-3-channel)
2. **Set up Qdrant testcontainer** in `conftest.py`
3. **Set up LiteLLM mock** for tests
4. **Run failing tests** to confirm RED phase: `pytest tests/integration/test_semantic_search.py -v`
5. **Start GREEN phase** with Task 1 (create search endpoint)

### Daily Standup Updates

**Report progress using task numbers:**
- "Task 1 complete (search endpoint created)"
- "Task 3 in progress (integrating Qdrant)"
- "Blocked on Task 4 (permission logic unclear)"

### Definition of Done

- [ ] All 6 integration tests pass (GREEN phase)
- [ ] Code reviewed by senior dev
- [ ] Performance validated (search < 5s for single KB)
- [ ] Security review (permission enforcement tests pass)
- [ ] Merged to main branch

---

## Knowledge Base References Applied

**Frameworks and Patterns:**
- `test-levels-framework.md` - Integration test level selection
- `test-quality.md` - Given-When-Then structure, atomic tests
- `test-priorities-matrix.md` - P0 prioritization (security + compliance)

**Test Design:**
- `test-design-epic-3.md` - Risk assessment (R-001, R-003, R-006)
- `risk-governance.md` - Risk scoring and mitigation planning

---

## Output Summary

### ATDD Complete - Tests in RED Phase ✅

**Story**: 3.1 - Semantic Search Backend
**Primary Test Level**: Integration

**Failing Tests Created**:
- Integration tests: 6 tests in `backend/tests/integration/test_semantic_search.py`

**Supporting Infrastructure**:
- Fixtures: 5 fixtures created (1 incomplete - `indexed_kb_with_docs`)
- Factories: 0 new factories (reused 3 from Epic 2)
- Mock requirements: 2 services documented (Qdrant, LiteLLM)

**Implementation Checklist**:
- Total tasks: 7 tasks
- Estimated effort: 12-16 hours

**Required Dependencies**:
- Qdrant testcontainer setup
- LiteLLM mock fixture
- Document indexing helper function

**Next Steps for DEV Team**:
1. Run failing tests: `pytest tests/integration/test_semantic_search.py -v`
2. Review implementation checklist (7 tasks)
3. Set up Qdrant + LiteLLM mocks
4. Implement Task 1 (create endpoint)
5. Follow RED → GREEN → REFACTOR cycle

**Output File**: `docs/atdd-checklist-3.1.md`

---

**Generated by**: Murat (TEA Agent - Test Architect Module)
**Workflow**: `.bmad/bmm/workflows/testarch/atdd`
**Date**: 2025-11-25
