# Test Design: Story 7-10 KB Model Configuration

| Field | Value |
|-------|-------|
| Story ID | 7-10 |
| Story Title | KB Model Configuration |
| Epic | 7 - Infrastructure & DevOps |
| Author | TEA (Murat) |
| Date | 2025-12-08 |
| Status | Draft |
| Depends On | Story 7-9 (LLM Model Registry) |

---

## 1. Executive Summary

Story 7-10 enables Knowledge Base owners to select embedding and generation models from the Model Registry, with automatic Qdrant collection creation and parameter overrides. This story connects the Model Registry (7-9) with the KB lifecycle, enabling per-KB model customization.

### Risk Assessment Summary

| Priority | Count | Risk Categories |
|----------|-------|-----------------|
| P0 (Critical) | 2 | DATA (Embedding Model Lock), TECH (Qdrant Collection Mismatch) |
| P1 (High) | 5 | DATA (Document Processing), TECH (Search/Generation), OPS (Model Validation) |
| P2 (Medium) | 4 | TECH (API Updates), OPS (Parameter Overrides) |
| P3 (Low) | 3 | BUS (UI Display), OPS (Default Selection) |

---

## 2. Risk-Based Test Prioritization

### 2.1 Risk Assessment Matrix

| ID | Test Scenario | Category | Probability | Impact | Score | Priority | Action |
|----|---------------|----------|-------------|--------|-------|----------|--------|
| R1 | Embedding model change after documents exist | DATA | 3 | 3 | 9 | P0 | BLOCK |
| R2 | Qdrant collection dimensions mismatch | TECH | 2 | 3 | 6 | P1 | MITIGATE |
| R3 | Document processing with wrong model | DATA | 2 | 3 | 6 | P1 | MITIGATE |
| R4 | Search using mismatched embedding model | TECH | 2 | 3 | 6 | P1 | MITIGATE |
| R5 | Generation using wrong model | TECH | 2 | 2 | 4 | P2 | MONITOR |
| R6 | Inactive model selected for KB | OPS | 2 | 3 | 6 | P1 | MITIGATE |
| R7 | Qdrant collection creation failure | TECH | 2 | 3 | 6 | P1 | MITIGATE |
| R8 | Parameter override hierarchy incorrect | OPS | 2 | 2 | 4 | P2 | MONITOR |
| R9 | KB creation without model selection | TECH | 2 | 2 | 4 | P2 | MONITOR |
| R10 | Model deletion with KB dependency | DATA | 2 | 3 | 6 | P1 | MITIGATE |
| R11 | UI model info display incorrect | BUS | 1 | 1 | 1 | P3 | DOCUMENT |
| R12 | Default model pre-selection | OPS | 1 | 1 | 1 | P3 | DOCUMENT |

### 2.2 Risk Mitigation Strategies

| Risk ID | Mitigation Strategy | Test Coverage |
|---------|---------------------|---------------|
| R1 | Document count check before embedding model change | Integration: `test_embedding_model_lock` |
| R2 | Validate dimensions match on collection creation | Integration: `test_qdrant_collection_dimensions` |
| R3 | Fetch KB's embedding model in worker | Integration: `test_document_processing_uses_kb_model` |
| R4 | Search service loads KB model config | Integration: `test_search_uses_kb_embedding_model` |
| R6 | Validate model is_active before KB creation | Unit: `test_inactive_model_rejected` |
| R7 | Transaction rollback on collection failure | Integration: `test_kb_creation_rollback_on_qdrant_error` |

---

## 3. Test Coverage Matrix

### 3.1 Acceptance Criteria to Test Mapping

| AC | Description | Unit Tests | Integration Tests | E2E Tests |
|----|-------------|------------|-------------------|-----------|
| AC-7.10.1 | Model dropdown shows active models | - | `test_model_selection_*` | `kb-model-selection.spec.ts` |
| AC-7.10.2 | Only active models in dropdown | `test_active_models_filter` | `test_list_active_models_only` | - |
| AC-7.10.3 | Model info displayed on selection | - | - | `model-info-display.spec.ts` |
| AC-7.10.4 | Qdrant collection with correct dimensions | `test_collection_params` | `test_qdrant_collection_*` | - |
| AC-7.10.5 | KB-level parameter overrides | `test_param_hierarchy` | `test_kb_parameter_overrides` | `kb-settings.spec.ts` |
| AC-7.10.6 | Embedding lock warning | `test_embedding_lock_check` | `test_embedding_model_lock_*` | `embedding-lock.spec.ts` |
| AC-7.10.7 | Generation model changeable | - | `test_generation_model_changeable` | - |
| AC-7.10.8 | Document processing uses KB model | - | `test_document_processing_*` | - |
| AC-7.10.9 | Search uses KB model | - | `test_search_uses_kb_*` | - |
| AC-7.10.10 | Generation uses KB model | - | `test_generation_uses_kb_*` | - |

---

## 4. Unit Test Design

### 4.1 Schema Validation Tests

**File**: `backend/tests/unit/test_kb_model_configuration.py`

```python
class TestKBModelSchemaValidation:
    """Unit tests for KB model configuration schema validation."""

    # P2: Schema validation
    def test_kb_create_schema_with_model_ids(self):
        """Verify KBCreate schema accepts embedding_model_id and generation_model_id"""

    def test_kb_create_schema_model_ids_optional(self):
        """Verify model_ids are optional (defaults used if not provided)"""

    def test_kb_update_schema_with_model_ids(self):
        """Verify KBUpdate schema includes model change fields"""

    def test_kb_response_includes_model_details(self):
        """Verify KBResponse includes embedded model information"""
```

### 4.2 Model Validation Tests

**File**: `backend/tests/unit/test_kb_model_validation.py`

```python
class TestKBModelValidation:
    """Unit tests for KB model validation logic."""

    # P1: Model state validation
    def test_active_model_accepted(self):
        """Verify active model can be selected for KB"""

    def test_inactive_model_rejected(self):
        """Verify inactive model raises ValidationError"""

    def test_model_exists_validation(self):
        """Verify non-existent model_id raises ValidationError"""

    def test_embedding_model_type_validation(self):
        """Verify only embedding type models accepted for embedding_model_id"""

    def test_generation_model_type_validation(self):
        """Verify only generation type models accepted for generation_model_id"""
```

### 4.3 Embedding Lock Tests (P0)

**File**: `backend/tests/unit/test_embedding_model_lock.py`

```python
class TestEmbeddingModelLock:
    """Unit tests for embedding model lock logic (AC-7.10.6)."""

    # P0: Critical data integrity
    def test_embedding_lock_check_no_documents(self):
        """Verify embedding model changeable when document_count = 0"""

    def test_embedding_lock_check_with_documents(self):
        """Verify embedding model locked when document_count > 0"""

    def test_embedding_lock_returns_document_count(self):
        """Verify lock check returns document count for warning"""

    def test_generation_model_not_locked(self):
        """Verify generation model always changeable (AC-7.10.7)"""
```

### 4.4 Parameter Hierarchy Tests

**File**: `backend/tests/unit/test_kb_parameter_hierarchy.py`

```python
class TestKBParameterHierarchy:
    """Unit tests for parameter override hierarchy (AC-7.10.5)."""

    # P2: Parameter inheritance logic
    def test_kb_override_takes_precedence(self):
        """Verify KB-level override > Model default > System default"""

    def test_model_default_used_when_no_kb_override(self):
        """Verify Model default used when KB override is null"""

    def test_system_default_used_when_no_model_default(self):
        """Verify System default used when both KB and Model are null"""

    def test_similarity_threshold_hierarchy(self):
        """Test similarity_threshold parameter inheritance"""

    def test_search_top_k_hierarchy(self):
        """Test search_top_k parameter inheritance"""

    def test_temperature_hierarchy(self):
        """Test temperature parameter inheritance"""
```

### 4.5 Qdrant Collection Parameter Tests

**File**: `backend/tests/unit/test_qdrant_collection_params.py`

```python
class TestQdrantCollectionParams:
    """Unit tests for Qdrant collection configuration."""

    # P1: Collection configuration
    def test_collection_name_format(self):
        """Verify collection name follows kb_{uuid} format"""

    def test_vector_size_from_model(self):
        """Verify vector size matches embedding model dimensions"""

    def test_distance_metric_from_model(self):
        """Verify distance metric matches embedding model config"""

    def test_default_distance_metric_cosine(self):
        """Verify default distance metric is COSINE"""
```

---

## 5. Integration Test Design

### 5.1 KB Creation with Model Selection Tests (P1)

**File**: `backend/tests/integration/test_kb_model_creation.py`

```python
class TestKBCreationWithModels:
    """Integration tests for KB creation with model selection (AC-7.10.1, 7.10.4)."""

    # P1: KB creation core flow
    async def test_create_kb_with_embedding_model(self, api_client, admin_cookies, embedding_model):
        """POST /api/v1/knowledge-bases with embedding_model_id creates KB with model"""

    async def test_create_kb_with_generation_model(self, api_client, admin_cookies, generation_model):
        """POST /api/v1/knowledge-bases with generation_model_id creates KB with model"""

    async def test_create_kb_with_both_models(self, api_client, admin_cookies, embedding_model, generation_model):
        """POST /api/v1/knowledge-bases with both model_ids creates KB correctly"""

    async def test_create_kb_uses_default_models(self, api_client, admin_cookies, default_embedding, default_generation):
        """POST /api/v1/knowledge-bases without model_ids uses system defaults"""

    async def test_create_kb_rejects_inactive_embedding_model(self, api_client, admin_cookies, inactive_embedding):
        """POST returns 400 when embedding_model_id references inactive model"""

    async def test_create_kb_rejects_inactive_generation_model(self, api_client, admin_cookies, inactive_generation):
        """POST returns 400 when generation_model_id references inactive model"""

    async def test_create_kb_rejects_invalid_model_type(self, api_client, admin_cookies, generation_model):
        """POST returns 400 when using generation model as embedding_model_id"""
```

### 5.2 Qdrant Collection Creation Tests (P0/P1)

**File**: `backend/tests/integration/test_kb_qdrant_collection.py`

```python
class TestKBQdrantCollection:
    """Integration tests for Qdrant collection creation (AC-7.10.4)."""

    # P0: Collection must match model dimensions
    async def test_qdrant_collection_created_on_kb_creation(self, api_client, admin_cookies, embedding_model, qdrant_client):
        """KB creation triggers Qdrant collection creation"""

    async def test_qdrant_collection_dimensions_match_model(self, api_client, admin_cookies, embedding_model, qdrant_client):
        """Collection vector size matches embedding model dimensions"""

    async def test_qdrant_collection_distance_metric_match_model(self, api_client, admin_cookies, embedding_model, qdrant_client):
        """Collection distance metric matches embedding model config"""

    async def test_qdrant_collection_name_format(self, api_client, admin_cookies, embedding_model, qdrant_client):
        """Collection named kb_{kb_id}"""

    async def test_kb_stores_collection_metadata(self, api_client, admin_cookies, embedding_model):
        """KB record stores qdrant_collection_name and qdrant_vector_size"""

    # P1: Error handling
    async def test_kb_creation_rollback_on_qdrant_error(self, api_client, admin_cookies, embedding_model, mock_qdrant_error):
        """KB creation rolls back if Qdrant collection creation fails"""
```

### 5.3 Embedding Model Lock Tests (P0)

**File**: `backend/tests/integration/test_embedding_model_lock.py`

```python
class TestEmbeddingModelLockAPI:
    """Integration tests for embedding model lock enforcement (AC-7.10.6)."""

    # P0: Critical - prevent dimension mismatch
    async def test_embedding_model_changeable_no_documents(self, api_client, admin_cookies, kb_no_docs, new_embedding_model):
        """PUT /api/v1/knowledge-bases/{id} allows embedding model change when no documents"""

    async def test_embedding_model_locked_with_documents(self, api_client, admin_cookies, kb_with_docs, new_embedding_model):
        """PUT returns 409 when trying to change embedding model with existing documents"""

    async def test_embedding_lock_error_includes_document_count(self, api_client, admin_cookies, kb_with_docs, new_embedding_model):
        """409 response includes document count in error message"""

    async def test_embedding_lock_warning_in_get_response(self, api_client, admin_cookies, kb_with_docs):
        """GET /api/v1/knowledge-bases/{id} includes embedding_locked: true when documents exist"""
```

### 5.4 Generation Model Change Tests

**File**: `backend/tests/integration/test_generation_model_change.py`

```python
class TestGenerationModelChangeAPI:
    """Integration tests for generation model changes (AC-7.10.7)."""

    # P2: Generation model flexibility
    async def test_generation_model_changeable_with_documents(self, api_client, admin_cookies, kb_with_docs, new_generation_model):
        """PUT allows generation model change even with existing documents"""

    async def test_generation_model_change_no_reprocessing_required(self, api_client, admin_cookies, kb_with_docs, new_generation_model):
        """Generation model change does not trigger document reprocessing"""
```

### 5.5 Document Processing Integration Tests (P1)

**File**: `backend/tests/integration/test_kb_document_processing.py`

```python
class TestKBDocumentProcessing:
    """Integration tests for document processing with KB models (AC-7.10.8)."""

    # P1: Document embedding uses correct model
    async def test_document_processing_uses_kb_embedding_model(self, kb_with_custom_embedding, test_document, mock_litellm):
        """Document embedding uses KB's configured embedding model"""

    async def test_document_processing_uses_kb_dimensions(self, kb_with_custom_embedding, test_document, qdrant_client):
        """Embedded vectors match KB's embedding model dimensions"""

    async def test_document_stored_in_kb_collection(self, kb_with_custom_embedding, test_document, qdrant_client):
        """Document vectors stored in KB's Qdrant collection"""

    async def test_document_processing_uses_kb_batch_size(self, kb_with_custom_embedding, large_document, mock_litellm):
        """Embedding batching uses KB's model batch_size setting"""
```

### 5.6 Search Integration Tests (P1)

**File**: `backend/tests/integration/test_kb_search_integration.py`

```python
class TestKBSearchIntegration:
    """Integration tests for search with KB models (AC-7.10.9)."""

    # P1: Search uses correct model
    async def test_search_uses_kb_embedding_model(self, kb_with_custom_embedding, indexed_documents, mock_litellm):
        """Search query embedding uses KB's embedding model"""

    async def test_search_uses_kb_similarity_threshold(self, kb_with_custom_threshold, indexed_documents):
        """Search applies KB's similarity_threshold override"""

    async def test_search_uses_kb_top_k(self, kb_with_custom_top_k, indexed_documents):
        """Search applies KB's search_top_k override"""

    async def test_search_queries_correct_collection(self, kb_with_custom_embedding, indexed_documents, qdrant_client):
        """Search queries KB's specific Qdrant collection"""
```

### 5.7 Generation Integration Tests

**File**: `backend/tests/integration/test_kb_generation_integration.py`

```python
class TestKBGenerationIntegration:
    """Integration tests for generation with KB models (AC-7.10.10)."""

    # P2: Generation uses correct model
    async def test_generation_uses_kb_generation_model(self, kb_with_custom_generation, indexed_documents, mock_litellm):
        """Chat/generation uses KB's configured generation model"""

    async def test_generation_uses_kb_temperature(self, kb_with_custom_temperature, indexed_documents, mock_litellm):
        """Generation applies KB's temperature override"""

    async def test_generation_uses_kb_context_window(self, kb_with_custom_context, indexed_documents, mock_litellm):
        """Generation respects KB's model context_window setting"""
```

### 5.8 Parameter Override Tests

**File**: `backend/tests/integration/test_kb_parameter_overrides.py`

```python
class TestKBParameterOverrides:
    """Integration tests for KB parameter overrides (AC-7.10.5)."""

    # P2: Parameter inheritance
    async def test_create_kb_with_custom_similarity_threshold(self, api_client, admin_cookies):
        """POST /api/v1/knowledge-bases accepts similarity_threshold override"""

    async def test_create_kb_with_custom_top_k(self, api_client, admin_cookies):
        """POST /api/v1/knowledge-bases accepts search_top_k override"""

    async def test_update_kb_parameters(self, api_client, admin_cookies, test_kb):
        """PUT /api/v1/knowledge-bases/{id} updates RAG parameters"""

    async def test_get_kb_includes_effective_parameters(self, api_client, admin_cookies, test_kb):
        """GET response includes effective parameters after hierarchy resolution"""
```

---

## 6. E2E Test Design

### 6.1 KB Creation Model Selection Tests

**File**: `frontend/e2e/tests/kb/kb-model-selection.spec.ts`

```typescript
describe('KB Creation Model Selection (AC-7.10.1, 7.10.2, 7.10.3)', () => {
  // P2: UI model selection
  test('displays embedding model dropdown in create modal', async ({ userPage }) => {
    // Open KB create modal, verify embedding dropdown visible
  });

  test('displays generation model dropdown in create modal', async ({ userPage }) => {
    // Open KB create modal, verify generation dropdown visible
  });

  test('embedding dropdown shows only active models', async ({ userPage }) => {
    // Verify inactive models not in dropdown options
  });

  test('displays model info on selection', async ({ userPage }) => {
    // Select model, verify dimensions/context info displayed
  });

  test('pre-selects default models if configured', async ({ userPage }) => {
    // Verify default models pre-selected in dropdowns
  });
});
```

### 6.2 KB Settings Model Section Tests

**File**: `frontend/e2e/tests/kb/kb-settings.spec.ts`

```typescript
describe('KB Settings Model Section (AC-7.10.5, 7.10.6, 7.10.7)', () => {
  // P1: Model management in settings
  test('displays current embedding and generation models', async ({ userPage }) => {
    // Open KB settings, verify model names displayed
  });

  test('shows embedding lock warning when documents exist', async ({ userPage }) => {
    // KB with documents shows "Model locked" warning
  });

  test('allows generation model change with confirmation', async ({ userPage }) => {
    // Change generation model, verify confirmation dialog
  });

  test('displays RAG parameter override fields', async ({ userPage }) => {
    // Verify similarity_threshold, top_k fields visible
  });

  test('saves parameter overrides successfully', async ({ userPage }) => {
    // Update parameters, save, verify toast and persistence
  });
});
```

### 6.3 Embedding Lock UI Tests (P0)

**File**: `frontend/e2e/tests/kb/embedding-lock.spec.ts`

```typescript
describe('Embedding Model Lock UI (AC-7.10.6)', () => {
  // P0: Prevent accidental dimension mismatch
  test('embedding dropdown disabled when documents exist', async ({ userPage }) => {
    // KB with documents has disabled embedding dropdown
  });

  test('lock warning icon displayed next to embedding field', async ({ userPage }) => {
    // Lock icon visible when embedding locked
  });

  test('lock tooltip explains document reprocessing required', async ({ userPage }) => {
    // Hover lock icon, verify explanation tooltip
  });

  test('embedding changeable for new KB', async ({ userPage }) => {
    // New KB (no docs) has enabled embedding dropdown
  });
});
```

---

## 7. Test Data Requirements

### 7.1 Test Fixtures

```python
# backend/tests/fixtures/kb_model_fixtures.py

@pytest.fixture
async def embedding_model_768(db_session):
    """Create embedding model with 768 dimensions."""
    from tests.factories.model_factory import create_embedding_model
    return await create_embedding_model(db_session, dimensions=768, distance_metric="cosine")

@pytest.fixture
async def embedding_model_1536(db_session):
    """Create embedding model with 1536 dimensions."""
    from tests.factories.model_factory import create_embedding_model
    return await create_embedding_model(db_session, dimensions=1536)

@pytest.fixture
async def generation_model_gpt4(db_session):
    """Create GPT-4 generation model."""
    from tests.factories.model_factory import create_generation_model
    return await create_generation_model(db_session, model_id="gpt-4o", context_window=128000)

@pytest.fixture
async def kb_with_custom_embedding(db_session, user, embedding_model_768):
    """Create KB with custom embedding model."""
    from tests.factories.kb_factory import create_knowledge_base
    return await create_knowledge_base(
        db_session,
        owner=user,
        embedding_model_id=embedding_model_768.id
    )

@pytest.fixture
async def kb_with_docs(db_session, kb_with_custom_embedding):
    """Create KB with processed documents (embedding locked)."""
    from tests.factories.document_factory import create_processed_document
    await create_processed_document(db_session, kb_id=kb_with_custom_embedding.id)
    return kb_with_custom_embedding

@pytest.fixture
async def kb_no_docs(db_session, kb_with_custom_embedding):
    """KB without documents (embedding changeable)."""
    return kb_with_custom_embedding
```

### 7.2 Factory Extensions

```python
# backend/tests/factories/kb_factory.py (extend existing)

async def create_knowledge_base(
    db_session,
    owner: User,
    embedding_model_id: UUID | None = None,
    generation_model_id: UUID | None = None,
    similarity_threshold: float | None = None,
    search_top_k: int | None = None,
    **overrides
) -> KnowledgeBase:
    """Create KB with optional model configuration."""
    kb = KnowledgeBase(
        name=overrides.get("name", f"test-kb-{uuid4().hex[:8]}"),
        description=overrides.get("description", "Test KB"),
        owner_id=owner.id,
        embedding_model_id=embedding_model_id,
        generation_model_id=generation_model_id,
        similarity_threshold=similarity_threshold,
        search_top_k=search_top_k,
        status="active",
        **overrides
    )
    db_session.add(kb)
    await db_session.flush()
    return kb
```

---

## 8. Mock Requirements

### 8.1 Qdrant Client Mock

**Purpose:** Test collection creation without real Qdrant

```python
# backend/tests/mocks/qdrant_mock.py

class MockQdrantService:
    """Mock for Qdrant collection operations."""

    def __init__(self):
        self.collections = {}

    async def create_collection(self, name: str, vectors_config: dict) -> bool:
        """Mock collection creation."""
        self.collections[name] = vectors_config
        return True

    async def get_collection(self, name: str) -> dict | None:
        """Mock collection retrieval."""
        return self.collections.get(name)

    async def delete_collection(self, name: str) -> bool:
        """Mock collection deletion."""
        return self.collections.pop(name, None) is not None

@pytest.fixture
def mock_qdrant_service(mocker):
    """Replace QdrantService with mock."""
    mock = MockQdrantService()
    mocker.patch('app.integrations.qdrant_client.qdrant_service', mock)
    return mock

@pytest.fixture
def mock_qdrant_error(mocker):
    """Mock Qdrant to raise error on collection creation."""
    mocker.patch(
        'app.integrations.qdrant_client.qdrant_service.create_collection',
        side_effect=Exception("Qdrant connection failed")
    )
```

### 8.2 LiteLLM Client Mock

```python
# backend/tests/mocks/litellm_mock.py (extend)

class MockLiteLLMClient:
    """Mock for LiteLLM embedding/generation calls."""

    def __init__(self, dimensions: int = 768):
        self.dimensions = dimensions
        self.last_model_used = None

    async def embed(self, text: str, model: str) -> list[float]:
        """Mock embedding call."""
        self.last_model_used = model
        return [0.1] * self.dimensions

    async def generate(self, prompt: str, model: str, **params) -> str:
        """Mock generation call."""
        self.last_model_used = model
        return "Generated response"
```

---

## 9. Required data-testid Attributes

### 9.1 KB Create Modal (Model Selection)

- `kb-create-modal` - Modal container
- `kb-name-input` - Name field
- `kb-description-input` - Description field
- `embedding-model-select` - Embedding model dropdown
- `generation-model-select` - Generation model dropdown
- `model-info-panel` - Selected model info display
- `model-dimensions-display` - Dimensions value
- `model-context-window-display` - Context window value
- `similarity-threshold-input` - Similarity threshold override
- `search-top-k-input` - Top K override
- `create-kb-button` - Create button

### 9.2 KB Settings Page (Model Section)

- `kb-settings-models-section` - Models section container
- `current-embedding-model` - Current embedding model display
- `current-generation-model` - Current generation model display
- `embedding-lock-warning` - Lock warning message
- `embedding-lock-icon` - Lock icon
- `change-generation-model-button` - Change generation model button
- `generation-model-confirm-dialog` - Confirmation dialog
- `rag-parameters-section` - RAG parameters section
- `save-settings-button` - Save button

---

## 10. Test Execution Strategy

### 10.1 Test Execution Order

1. **P0 Tests** (Gate: BLOCK if any fail)
   - Embedding model lock enforcement
   - Qdrant collection dimension validation

2. **P1 Tests** (Gate: CONCERNS if >10% fail)
   - KB creation with models
   - Document processing with KB model
   - Search with KB model
   - Model validation (active only)

3. **P2 Tests** (Gate: MONITOR)
   - API CRUD with model fields
   - Parameter overrides
   - Generation model changes

4. **P3 Tests** (Gate: DOCUMENT)
   - UI display
   - Default selection

### 10.2 CI Pipeline Integration

```yaml
# .github/workflows/test-7-10.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run P0/P1 Unit Tests
        run: pytest backend/tests/unit/test_kb_model*.py backend/tests/unit/test_embedding_model_lock.py -m "p0 or p1" --tb=short

  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
      qdrant:
        image: qdrant/qdrant:latest
    steps:
      - name: Run Integration Tests
        run: pytest backend/tests/integration/test_kb_model*.py backend/tests/integration/test_embedding_model_lock.py --tb=short

  e2e-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run E2E Tests
        run: npx playwright test e2e/tests/kb/kb-model*.spec.ts e2e/tests/kb/embedding-lock.spec.ts
```

---

## 11. Gate Decision Criteria

### 11.1 Story Completion Gate

| Criteria | Threshold | Action if Failed |
|----------|-----------|------------------|
| P0 Tests Pass | 100% | FAIL - Block deployment |
| P1 Tests Pass | 100% | CONCERNS - Requires review |
| P2 Tests Pass | 90% | MONITOR - Log defects |
| P3 Tests Pass | 80% | DOCUMENT - Track in backlog |
| Code Coverage | 80% | CONCERNS if below |

### 11.2 Regression Gate

| Check | Requirement |
|-------|-------------|
| Existing KB tests | No new failures |
| Document processing tests | All passing |
| Search tests | All passing |
| Model Registry tests (7-9) | All passing |

---

## 12. Appendix

### A. Test File Locations

| Category | Path |
|----------|------|
| Unit Tests | `backend/tests/unit/test_kb_model_*.py` |
| Integration Tests | `backend/tests/integration/test_kb_model_*.py` |
| E2E Tests | `frontend/e2e/tests/kb/kb-model-*.spec.ts` |
| Fixtures | `backend/tests/fixtures/kb_model_fixtures.py` |
| Mocks | `backend/tests/mocks/qdrant_mock.py` |

### B. Referenced Architecture

- KB Service: [backend/app/services/kb_service.py](backend/app/services/kb_service.py)
- Qdrant Client: [backend/app/integrations/qdrant_client.py](backend/app/integrations/qdrant_client.py)
- Story 7-9 (Model Registry): [docs/sprint-artifacts/7-9-llm-model-registry.md](docs/sprint-artifacts/7-9-llm-model-registry.md)

### C. Traceability Matrix

| AC | Unit | Integration | E2E | Risk ID |
|----|------|-------------|-----|---------|
| AC-7.10.1 | - | `test_model_selection_*` | `kb-model-selection.spec.ts` | - |
| AC-7.10.2 | `test_active_models_filter` | `test_list_active_models_only` | - | R6 |
| AC-7.10.3 | - | - | `model-info-display.spec.ts` | R11 |
| AC-7.10.4 | `test_collection_params` | `test_qdrant_collection_*` | - | R2, R7 |
| AC-7.10.5 | `test_param_hierarchy` | `test_kb_parameter_overrides` | `kb-settings.spec.ts` | R8 |
| AC-7.10.6 | `test_embedding_lock_*` | `test_embedding_model_lock_*` | `embedding-lock.spec.ts` | R1 |
| AC-7.10.7 | `test_generation_not_locked` | `test_generation_model_changeable` | - | - |
| AC-7.10.8 | - | `test_document_processing_*` | - | R3 |
| AC-7.10.9 | - | `test_search_uses_kb_*` | - | R4 |
| AC-7.10.10 | - | `test_generation_uses_kb_*` | - | R5 |

### D. Parameter Override Reference

| Parameter | KB Field | Model Default | System Default |
|-----------|----------|---------------|----------------|
| similarity_threshold | kb.similarity_threshold | model.similarity_threshold | 0.7 |
| search_top_k | kb.search_top_k | model.search_top_k | 10 |
| temperature | kb.temperature | model.default_temperature | 0.7 |
| top_p | kb.top_p | model.top_p | 1.0 |

---

*Generated by TEA (Murat) - Master Test Architect*
*Risk-based prioritization using Probability x Impact matrix*
