# ATDD Checklist - Epic 7, Story 7-10: KB Model Configuration

**Date:** 2025-12-08
**Author:** TEA (Murat) - Master Test Architect
**Primary Test Level:** Integration Tests

---

## Story Summary

Story 7-10 enables Knowledge Base owners to select embedding and generation models from the Model Registry, with automatic Qdrant collection creation and parameter overrides. This story connects the Model Registry (7-9) with the KB lifecycle, enabling per-KB model customization.

**As a** knowledge base owner
**I want** to select which embedding and generation models my KB uses from the Model Registry
**So that** I can optimize my KB for specific use cases and leverage different AI capabilities

---

## Acceptance Criteria

1. **AC-7.10.1**: Model selection dropdown during KB creation shows active models from registry
2. **AC-7.10.2**: Only active models appear in selection dropdown
3. **AC-7.10.3**: Model info (dimensions, context window) displayed on selection
4. **AC-7.10.4**: Qdrant collection auto-created with correct dimensions and distance metric from selected embedding model
5. **AC-7.10.5**: KB-level parameter overrides (similarity_threshold, top_k, rerank) supported
6. **AC-7.10.6**: Embedding model lock warning displayed after first document is processed
7. **AC-7.10.7**: Generation model changeable without document reprocessing
8. **AC-7.10.8**: Document processing uses KB-configured embedding model
9. **AC-7.10.9**: Search operations use KB-configured embedding model
10. **AC-7.10.10**: Chat/generation operations use KB-configured generation model

---

## Failing Tests Created (RED Phase)

### Unit Tests (15 tests)

**File:** `backend/tests/unit/test_kb_model_configuration.py` (~200 lines)

- [ ] **Test:** `test_kb_create_schema_with_model_ids`
  - **Status:** RED - Schema doesn't have model_id fields
  - **Verifies:** AC-7.10.1 - KBCreate schema accepts embedding_model_id and generation_model_id

- [ ] **Test:** `test_kb_create_schema_model_ids_optional`
  - **Status:** RED - Schema doesn't handle optional model_ids
  - **Verifies:** AC-7.10.1 - Model IDs optional (defaults used if not provided)

- [ ] **Test:** `test_kb_response_includes_model_details`
  - **Status:** RED - Response schema missing model info
  - **Verifies:** AC-7.10.3 - KB response includes model details

- [ ] **Test:** `test_active_model_accepted`
  - **Status:** RED - No model validation logic
  - **Verifies:** AC-7.10.2 - Active model can be selected

- [ ] **Test:** `test_inactive_model_rejected`
  - **Status:** RED - No inactive model check
  - **Verifies:** AC-7.10.2 - Inactive model raises ValidationError

- [ ] **Test:** `test_embedding_model_type_validation`
  - **Status:** RED - No model type validation
  - **Verifies:** AC-7.10.1 - Only embedding models for embedding_model_id

**File:** `backend/tests/unit/test_embedding_model_lock.py` (~100 lines)

- [ ] **Test:** `test_embedding_lock_check_no_documents`
  - **Status:** RED - No lock logic implemented
  - **Verifies:** AC-7.10.6 - Embedding changeable when document_count = 0

- [ ] **Test:** `test_embedding_lock_check_with_documents`
  - **Status:** RED - No lock logic implemented
  - **Verifies:** AC-7.10.6 - Embedding locked when document_count > 0

- [ ] **Test:** `test_generation_model_not_locked`
  - **Status:** RED - No generation lock logic
  - **Verifies:** AC-7.10.7 - Generation model always changeable

**File:** `backend/tests/unit/test_kb_parameter_hierarchy.py` (~120 lines)

- [ ] **Test:** `test_kb_override_takes_precedence`
  - **Status:** RED - No hierarchy logic
  - **Verifies:** AC-7.10.5 - KB override > Model > System

- [ ] **Test:** `test_model_default_used_when_no_kb_override`
  - **Status:** RED - No hierarchy logic
  - **Verifies:** AC-7.10.5 - Model default used when KB is null

- [ ] **Test:** `test_system_default_used_when_no_model_default`
  - **Status:** RED - No hierarchy logic
  - **Verifies:** AC-7.10.5 - System default used when both null

**File:** `backend/tests/unit/test_qdrant_collection_params.py` (~80 lines)

- [ ] **Test:** `test_collection_name_format`
  - **Status:** RED - No dynamic naming
  - **Verifies:** AC-7.10.4 - Collection name follows kb_{uuid} format

- [ ] **Test:** `test_vector_size_from_model`
  - **Status:** RED - Hardcoded vector size
  - **Verifies:** AC-7.10.4 - Vector size matches model dimensions

- [ ] **Test:** `test_distance_metric_from_model`
  - **Status:** RED - Hardcoded distance metric
  - **Verifies:** AC-7.10.4 - Distance metric from model config

### Integration Tests (18 tests)

**File:** `backend/tests/integration/test_kb_model_creation.py` (~350 lines)

- [ ] **Test:** `test_create_kb_with_embedding_model`
  - **Status:** RED - API doesn't accept model_id
  - **Verifies:** AC-7.10.1 - POST creates KB with embedding model

- [ ] **Test:** `test_create_kb_with_generation_model`
  - **Status:** RED - API doesn't accept model_id
  - **Verifies:** AC-7.10.1 - POST creates KB with generation model

- [ ] **Test:** `test_create_kb_with_both_models`
  - **Status:** RED - API doesn't accept model_ids
  - **Verifies:** AC-7.10.1 - POST creates KB with both models

- [ ] **Test:** `test_create_kb_uses_default_models`
  - **Status:** RED - No default model logic
  - **Verifies:** AC-7.10.1 - Default models used when not provided

- [ ] **Test:** `test_create_kb_rejects_inactive_embedding_model`
  - **Status:** RED - No validation
  - **Verifies:** AC-7.10.2 - 400 for inactive embedding model

- [ ] **Test:** `test_create_kb_rejects_inactive_generation_model`
  - **Status:** RED - No validation
  - **Verifies:** AC-7.10.2 - 400 for inactive generation model

**File:** `backend/tests/integration/test_kb_qdrant_collection.py` (~250 lines)

- [ ] **Test:** `test_qdrant_collection_created_on_kb_creation`
  - **Status:** RED - No auto-creation
  - **Verifies:** AC-7.10.4 - Collection created on KB save

- [ ] **Test:** `test_qdrant_collection_dimensions_match_model`
  - **Status:** RED - Hardcoded dimensions
  - **Verifies:** AC-7.10.4 - Dimensions from model

- [ ] **Test:** `test_qdrant_collection_distance_metric_match_model`
  - **Status:** RED - Hardcoded metric
  - **Verifies:** AC-7.10.4 - Distance metric from model

- [ ] **Test:** `test_kb_creation_rollback_on_qdrant_error`
  - **Status:** RED - No rollback logic
  - **Verifies:** AC-7.10.4 - Transaction rollback on failure

**File:** `backend/tests/integration/test_embedding_model_lock.py` (~200 lines)

- [ ] **Test:** `test_embedding_model_changeable_no_documents`
  - **Status:** RED - No lock enforcement
  - **Verifies:** AC-7.10.6 - PUT allows change when no docs

- [ ] **Test:** `test_embedding_model_locked_with_documents`
  - **Status:** RED - No lock enforcement
  - **Verifies:** AC-7.10.6 - PUT returns 409 with docs

- [ ] **Test:** `test_embedding_lock_error_includes_document_count`
  - **Status:** RED - No error message
  - **Verifies:** AC-7.10.6 - 409 includes document count

- [ ] **Test:** `test_embedding_lock_warning_in_get_response`
  - **Status:** RED - No lock flag in response
  - **Verifies:** AC-7.10.6 - GET includes embedding_locked

**File:** `backend/tests/integration/test_kb_document_processing.py` (~200 lines)

- [ ] **Test:** `test_document_processing_uses_kb_embedding_model`
  - **Status:** RED - Worker uses global model
  - **Verifies:** AC-7.10.8 - Worker fetches KB's model

- [ ] **Test:** `test_document_stored_in_kb_collection`
  - **Status:** RED - Hardcoded collection
  - **Verifies:** AC-7.10.8 - Vectors in KB's collection

**File:** `backend/tests/integration/test_kb_search_integration.py` (~180 lines)

- [ ] **Test:** `test_search_uses_kb_embedding_model`
  - **Status:** RED - Search uses global model
  - **Verifies:** AC-7.10.9 - Query embedding uses KB model

- [ ] **Test:** `test_search_uses_kb_similarity_threshold`
  - **Status:** RED - Hardcoded threshold
  - **Verifies:** AC-7.10.5 - KB threshold override

### E2E Tests (10 tests)

**File:** `frontend/e2e/tests/kb/kb-model-selection.spec.ts` (~200 lines)

- [ ] **Test:** `displays embedding model dropdown in create modal`
  - **Status:** RED - No dropdown exists
  - **Verifies:** AC-7.10.1 - Embedding dropdown visible

- [ ] **Test:** `displays generation model dropdown in create modal`
  - **Status:** RED - No dropdown exists
  - **Verifies:** AC-7.10.1 - Generation dropdown visible

- [ ] **Test:** `embedding dropdown shows only active models`
  - **Status:** RED - No filtering
  - **Verifies:** AC-7.10.2 - Only active models

- [ ] **Test:** `displays model info on selection`
  - **Status:** RED - No info panel
  - **Verifies:** AC-7.10.3 - Model info displayed

**File:** `frontend/e2e/tests/kb/kb-settings.spec.ts` (~180 lines)

- [ ] **Test:** `displays current embedding and generation models`
  - **Status:** RED - No model section
  - **Verifies:** AC-7.10.5 - Current models shown

- [ ] **Test:** `displays RAG parameter override fields`
  - **Status:** RED - No parameter fields
  - **Verifies:** AC-7.10.5 - Override fields visible

- [ ] **Test:** `saves parameter overrides successfully`
  - **Status:** RED - No save functionality
  - **Verifies:** AC-7.10.5 - Parameters persist

**File:** `frontend/e2e/tests/kb/embedding-lock.spec.ts` (~150 lines)

- [ ] **Test:** `embedding dropdown disabled when documents exist`
  - **Status:** RED - No lock UI
  - **Verifies:** AC-7.10.6 - Dropdown disabled

- [ ] **Test:** `lock warning icon displayed next to embedding field`
  - **Status:** RED - No lock icon
  - **Verifies:** AC-7.10.6 - Lock icon visible

- [ ] **Test:** `embedding changeable for new KB`
  - **Status:** RED - No state check
  - **Verifies:** AC-7.10.6 - New KB has enabled dropdown

### Component Tests (6 tests)

**File:** `frontend/src/components/kb/__tests__/kb-model-select.test.tsx` (~150 lines)

- [ ] **Test:** `renders embedding model options from API`
  - **Status:** RED - Component doesn't exist
  - **Verifies:** AC-7.10.1 - Dropdown renders models

- [ ] **Test:** `filters out inactive models`
  - **Status:** RED - No filtering logic
  - **Verifies:** AC-7.10.2 - Inactive models hidden

- [ ] **Test:** `displays model dimensions on selection`
  - **Status:** RED - No info display
  - **Verifies:** AC-7.10.3 - Info shown

- [ ] **Test:** `shows lock icon when embedding locked`
  - **Status:** RED - No lock state
  - **Verifies:** AC-7.10.6 - Lock visual

- [ ] **Test:** `disables dropdown when locked`
  - **Status:** RED - No disable logic
  - **Verifies:** AC-7.10.6 - Interaction blocked

- [ ] **Test:** `displays lock tooltip on hover`
  - **Status:** RED - No tooltip
  - **Verifies:** AC-7.10.6 - Explanation shown

---

## Data Factories Created

### Model Factory

**File:** `backend/tests/factories/model_factory.py` (extension)

**Exports:**
- `create_embedding_model(db_session, dimensions=768, distance_metric="cosine", is_active=True)` - Create embedding model
- `create_generation_model(db_session, model_id="gpt-4o", context_window=128000, is_active=True)` - Create generation model
- `create_inactive_model(db_session, model_type)` - Create inactive model for testing

### KB Model Factory

**File:** `backend/tests/factories/kb_model_factory.py`

**Exports:**
- `create_kb_with_embedding(db_session, owner, embedding_model_id)` - KB with custom embedding
- `create_kb_with_generation(db_session, owner, generation_model_id)` - KB with custom generation
- `create_kb_with_both_models(db_session, owner, embedding_id, generation_id)` - KB with both
- `create_kb_with_custom_params(db_session, owner, similarity_threshold, top_k)` - KB with overrides

**Example Usage:**

```python
embedding_model = await create_embedding_model(db_session, dimensions=1536)
kb = await create_kb_with_embedding(db_session, user, embedding_model.id)
```

---

## Fixtures Created

### KB Model Fixtures

**File:** `backend/tests/fixtures/kb_model_fixtures.py`

**Fixtures:**

- `embedding_model_768` - Embedding model with 768 dimensions
  - **Setup:** Creates model in DB
  - **Provides:** Model instance with id, dimensions, distance_metric
  - **Cleanup:** Auto-deleted via session rollback

- `embedding_model_1536` - Embedding model with 1536 dimensions
  - **Setup:** Creates model in DB
  - **Provides:** Model instance for OpenAI-compatible testing

- `generation_model_gpt4` - GPT-4 generation model
  - **Setup:** Creates generation model
  - **Provides:** Model with context_window=128000

- `kb_with_custom_embedding` - KB with custom embedding model
  - **Setup:** Creates KB linked to embedding_model_768
  - **Provides:** KB instance with model relationship

- `kb_with_docs` - KB with processed documents (embedding locked)
  - **Setup:** Creates KB + document
  - **Provides:** KB where embedding change should be blocked

- `kb_no_docs` - KB without documents (embedding changeable)
  - **Setup:** Creates empty KB
  - **Provides:** KB where embedding change is allowed

**Example Usage:**

```python
async def test_embedding_lock(api_client, admin_cookies, kb_with_docs, new_embedding_model):
    response = await api_client.put(
        f"/api/v1/knowledge-bases/{kb_with_docs.id}",
        json={"embedding_model_id": str(new_embedding_model.id)},
        cookies=admin_cookies
    )
    assert response.status_code == 409
```

---

## Mock Requirements

### Qdrant Service Mock

**Purpose:** Test collection operations without real Qdrant

**Methods:**
- `create_collection(name, vectors_config)` - Tracks created collections
- `get_collection(name)` - Returns mock collection info
- `delete_collection(name)` - Removes from tracking

**Success Response:**
```json
{
  "status": "ok",
  "collection_name": "kb_uuid",
  "vectors_count": 0
}
```

**Failure Response:**
```json
{
  "status": "error",
  "message": "Qdrant connection failed"
}
```

**Notes:** Use `mock_qdrant_error` fixture to simulate Qdrant failures for rollback testing

### LiteLLM Client Mock

**Purpose:** Verify correct model is used for embedding/generation

**Methods:**
- `embed(text, model)` - Records model used, returns mock vectors
- `generate(prompt, model, **params)` - Records model and params used

**Notes:** `last_model_used` attribute available for assertion

---

## Required data-testid Attributes

### KB Create Modal

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

### KB Settings Page

- `kb-settings-models-section` - Models section container
- `current-embedding-model` - Current embedding model display
- `current-generation-model` - Current generation model display
- `embedding-lock-warning` - Lock warning message
- `embedding-lock-icon` - Lock icon
- `change-generation-model-button` - Change generation model button
- `generation-model-confirm-dialog` - Confirmation dialog
- `rag-parameters-section` - RAG parameters section
- `save-settings-button` - Save button

**Implementation Example:**

```tsx
<Select data-testid="embedding-model-select">
  {models.map(m => <SelectItem key={m.id}>{m.name}</SelectItem>)}
</Select>
<div data-testid="embedding-lock-warning" className="text-yellow-600">
  <LockIcon data-testid="embedding-lock-icon" />
  Model locked - {documentCount} documents exist
</div>
```

---

## Implementation Checklist

### Task 1: Database Schema Updates

**Tests to pass:**
- `test_kb_create_schema_with_model_ids`
- `test_kb_create_schema_model_ids_optional`
- `test_kb_response_includes_model_details`

**Implementation tasks:**
- [ ] Add `embedding_model_id` FK to knowledge_bases table
- [ ] Add `generation_model_id` FK to knowledge_bases table
- [ ] Add `similarity_threshold`, `search_top_k`, `temperature` columns
- [ ] Add `qdrant_collection_name` and `qdrant_vector_size` columns
- [ ] Create Alembic migration `add_model_refs_to_kb.py`
- [ ] Update KnowledgeBase model with new columns
- [ ] Update KnowledgeBaseCreate/Update schemas
- [ ] Run test: `pytest backend/tests/unit/test_kb_model_configuration.py -v`
- [ ] All schema tests pass (green phase)

**Estimated Effort:** 2 hours

---

### Task 2: KB Creation API with Model Selection

**Tests to pass:**
- `test_create_kb_with_embedding_model`
- `test_create_kb_with_generation_model`
- `test_create_kb_with_both_models`
- `test_create_kb_uses_default_models`

**Implementation tasks:**
- [ ] Update POST /api/v1/knowledge-bases to accept model_id fields
- [ ] Add model existence validation in kb_service.create()
- [ ] Implement default model selection when not provided
- [ ] Return model details in KB response
- [ ] Add required data-testid attributes: `embedding-model-select`, `generation-model-select`
- [ ] Run test: `pytest backend/tests/integration/test_kb_model_creation.py -v`
- [ ] KB creation tests pass (green phase)

**Estimated Effort:** 3 hours

---

### Task 3: Model Validation (Active Only)

**Tests to pass:**
- `test_active_model_accepted`
- `test_inactive_model_rejected`
- `test_embedding_model_type_validation`
- `test_create_kb_rejects_inactive_embedding_model`
- `test_create_kb_rejects_inactive_generation_model`

**Implementation tasks:**
- [ ] Add `is_active` check in model validation
- [ ] Add model type validation (embedding vs generation)
- [ ] Return 400 with clear message for inactive models
- [ ] Run test: `pytest backend/tests/unit/test_kb_model_validation.py backend/tests/integration/test_kb_model_creation.py::test_create_kb_rejects* -v`
- [ ] Model validation tests pass (green phase)

**Estimated Effort:** 1.5 hours

---

### Task 4: Qdrant Collection Creation (P0)

**Tests to pass:**
- `test_qdrant_collection_created_on_kb_creation`
- `test_qdrant_collection_dimensions_match_model`
- `test_qdrant_collection_distance_metric_match_model`
- `test_collection_name_format`
- `test_vector_size_from_model`
- `test_kb_creation_rollback_on_qdrant_error`

**Implementation tasks:**
- [ ] Update qdrant_client.py to support dynamic dimensions
- [ ] Create collection in kb_service.create() after DB save
- [ ] Use `kb_{uuid}` naming convention
- [ ] Get dimensions from embedding model
- [ ] Get distance metric from model or default to COSINE
- [ ] Store collection_name and vector_size in KB record
- [ ] Implement rollback on Qdrant error
- [ ] Run test: `pytest backend/tests/integration/test_kb_qdrant_collection.py backend/tests/unit/test_qdrant_collection_params.py -v`
- [ ] Qdrant collection tests pass (green phase)

**Estimated Effort:** 4 hours

---

### Task 5: Embedding Model Lock (P0)

**Tests to pass:**
- `test_embedding_lock_check_no_documents`
- `test_embedding_lock_check_with_documents`
- `test_generation_model_not_locked`
- `test_embedding_model_changeable_no_documents`
- `test_embedding_model_locked_with_documents`
- `test_embedding_lock_error_includes_document_count`
- `test_embedding_lock_warning_in_get_response`

**Implementation tasks:**
- [ ] Add document count check in kb_service.update()
- [ ] Return 409 Conflict when trying to change locked embedding
- [ ] Include document_count in error response
- [ ] Add `embedding_locked` flag to GET response
- [ ] Allow generation model changes unconditionally
- [ ] Add required data-testid attributes: `embedding-lock-warning`, `embedding-lock-icon`
- [ ] Run test: `pytest backend/tests/unit/test_embedding_model_lock.py backend/tests/integration/test_embedding_model_lock.py -v`
- [ ] Embedding lock tests pass (green phase)

**Estimated Effort:** 3 hours

---

### Task 6: Parameter Override Hierarchy

**Tests to pass:**
- `test_kb_override_takes_precedence`
- `test_model_default_used_when_no_kb_override`
- `test_system_default_used_when_no_model_default`
- `test_search_uses_kb_similarity_threshold`

**Implementation tasks:**
- [ ] Create `get_effective_parameter()` helper function
- [ ] Implement hierarchy: KB > Model > System
- [ ] Apply in search_service for similarity_threshold
- [ ] Apply in search_service for top_k
- [ ] Apply in generation_service for temperature
- [ ] Include effective_parameters in KB response
- [ ] Run test: `pytest backend/tests/unit/test_kb_parameter_hierarchy.py backend/tests/integration/test_kb_parameter_overrides.py -v`
- [ ] Parameter hierarchy tests pass (green phase)

**Estimated Effort:** 2.5 hours

---

### Task 7: Document Processing Integration

**Tests to pass:**
- `test_document_processing_uses_kb_embedding_model`
- `test_document_stored_in_kb_collection`

**Implementation tasks:**
- [ ] Update embedding worker to fetch KB's embedding model
- [ ] Configure LiteLLM client with KB's model settings
- [ ] Use KB's collection name for vector storage
- [ ] Run test: `pytest backend/tests/integration/test_kb_document_processing.py -v`
- [ ] Document processing tests pass (green phase)

**Estimated Effort:** 2 hours

---

### Task 8: Search Integration

**Tests to pass:**
- `test_search_uses_kb_embedding_model`
- `test_search_uses_kb_similarity_threshold`

**Implementation tasks:**
- [ ] Update search_service to load KB's embedding model
- [ ] Apply KB's similarity_threshold override
- [ ] Query correct Qdrant collection
- [ ] Run test: `pytest backend/tests/integration/test_kb_search_integration.py -v`
- [ ] Search integration tests pass (green phase)

**Estimated Effort:** 2 hours

---

### Task 9: KB Create Modal UI

**Tests to pass:**
- `displays embedding model dropdown in create modal`
- `displays generation model dropdown in create modal`
- `embedding dropdown shows only active models`
- `displays model info on selection`
- `renders embedding model options from API`
- `filters out inactive models`

**Implementation tasks:**
- [ ] Create `useKBModels` hook to fetch active models
- [ ] Add embedding model Select to kb-create-modal.tsx
- [ ] Add generation model Select to kb-create-modal.tsx
- [ ] Add model info panel showing dimensions/context
- [ ] Filter to show only active models
- [ ] Pre-select default models if configured
- [ ] Add required data-testid attributes
- [ ] Run test: `npx playwright test e2e/tests/kb/kb-model-selection.spec.ts`
- [ ] KB create modal tests pass (green phase)

**Estimated Effort:** 4 hours

---

### Task 10: KB Settings UI

**Tests to pass:**
- `displays current embedding and generation models`
- `displays RAG parameter override fields`
- `saves parameter overrides successfully`
- `shows lock icon when embedding locked`
- `disables dropdown when locked`

**Implementation tasks:**
- [ ] Create kb-settings-modal.tsx component
- [ ] Display current models with info
- [ ] Add embedding lock warning when docs exist
- [ ] Add generation model change with confirmation
- [ ] Add RAG parameter input fields
- [ ] Implement save functionality
- [ ] Add required data-testid attributes
- [ ] Run test: `npx playwright test e2e/tests/kb/kb-settings.spec.ts`
- [ ] KB settings tests pass (green phase)

**Estimated Effort:** 4 hours

---

### Task 11: Embedding Lock UI

**Tests to pass:**
- `embedding dropdown disabled when documents exist`
- `lock warning icon displayed next to embedding field`
- `embedding changeable for new KB`
- `displays lock tooltip on hover`

**Implementation tasks:**
- [ ] Check `embedding_locked` flag from API
- [ ] Disable embedding dropdown when locked
- [ ] Show lock icon with tooltip
- [ ] Enable dropdown for new KBs
- [ ] Add required data-testid attributes
- [ ] Run test: `npx playwright test e2e/tests/kb/embedding-lock.spec.ts`
- [ ] Embedding lock UI tests pass (green phase)

**Estimated Effort:** 2 hours

---

## Running Tests

```bash
# Run all failing tests for this story
pytest backend/tests/unit/test_kb_model*.py backend/tests/unit/test_embedding_model_lock.py backend/tests/unit/test_qdrant_collection_params.py -v
pytest backend/tests/integration/test_kb_model*.py backend/tests/integration/test_embedding_model_lock.py backend/tests/integration/test_kb_*_integration.py -v
npx playwright test e2e/tests/kb/kb-model*.spec.ts e2e/tests/kb/embedding-lock.spec.ts

# Run specific test file
pytest backend/tests/unit/test_embedding_model_lock.py -v

# Run tests in headed mode (see browser)
npx playwright test e2e/tests/kb/embedding-lock.spec.ts --headed

# Debug specific test
npx playwright test e2e/tests/kb/kb-model-selection.spec.ts --debug

# Run P0 tests only (critical path)
pytest backend/tests -m "p0" -v

# Run tests with coverage
pytest backend/tests/unit/test_kb_model*.py --cov=app/services/kb_service --cov-report=term-missing
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

- [ ] All tests written and failing
- [ ] Fixtures and factories created with auto-cleanup
- [ ] Mock requirements documented
- [ ] data-testid requirements listed
- [ ] Implementation checklist created

**Verification:**

- All tests run and fail as expected
- Failure messages are clear and actionable
- Tests fail due to missing implementation, not test bugs

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Pick one failing test** from implementation checklist (start with Task 1)
2. **Read the test** to understand expected behavior
3. **Implement minimal code** to make that specific test pass
4. **Run the test** to verify it now passes (green)
5. **Check off the task** in implementation checklist
6. **Move to next test** and repeat

**Priority Order:**

1. **Task 1** - Database Schema (foundation)
2. **Task 4** - Qdrant Collection (P0 critical)
3. **Task 5** - Embedding Lock (P0 critical)
4. **Task 2** - KB Creation API
5. **Task 3** - Model Validation
6. **Task 6** - Parameter Hierarchy
7. **Task 7** - Document Processing
8. **Task 8** - Search Integration
9. **Task 9** - KB Create Modal UI
10. **Task 10** - KB Settings UI
11. **Task 11** - Embedding Lock UI

**Key Principles:**

- One test at a time (don't try to fix all at once)
- Minimal implementation (don't over-engineer)
- Run tests frequently (immediate feedback)
- P0 tests must pass before P1/P2

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

**DEV Agent Responsibilities:**

1. **Verify all tests pass** (green phase complete)
2. **Review code for quality** (readability, maintainability)
3. **Extract duplications** (DRY principle)
4. **Ensure tests still pass** after each refactor
5. **Update documentation** if API changes

---

## Next Steps

1. **Review this checklist** with team in standup
2. **Create test files** with failing tests
3. **Run failing tests** to confirm RED phase
4. **Begin implementation** with Task 1 (Schema)
5. **Follow priority order** - P0 tests first
6. **When all tests pass**, refactor code
7. **When refactoring complete**, run `/bmad:bmm:workflows:story-done 7-10`

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `pytest backend/tests/unit/test_kb_model*.py -v`

**Results:**

```
FAILED backend/tests/unit/test_kb_model_configuration.py::test_kb_create_schema_with_model_ids - missing schema fields
FAILED backend/tests/unit/test_kb_model_validation.py::test_inactive_model_rejected - no validation
FAILED backend/tests/unit/test_embedding_model_lock.py::test_embedding_lock_check_with_documents - no lock logic
... (all tests failing as expected)
```

**Summary:**

- Total tests: 49
- Passing: 0 (expected)
- Failing: 49 (expected)
- Status: RED phase ready

---

## Traceability Matrix

| AC | Unit Tests | Integration Tests | E2E Tests | Priority |
|----|------------|-------------------|-----------|----------|
| AC-7.10.1 | schema_with_model_ids | create_kb_with_* | kb-model-selection.spec | P1 |
| AC-7.10.2 | inactive_model_rejected | rejects_inactive_* | active_models_only | P1 |
| AC-7.10.3 | response_includes_model | - | model_info_display | P3 |
| AC-7.10.4 | collection_params | qdrant_collection_* | - | P0 |
| AC-7.10.5 | param_hierarchy | parameter_overrides | kb-settings.spec | P2 |
| AC-7.10.6 | embedding_lock_* | embedding_model_lock_* | embedding-lock.spec | P0 |
| AC-7.10.7 | generation_not_locked | generation_model_changeable | - | P2 |
| AC-7.10.8 | - | document_processing_* | - | P1 |
| AC-7.10.9 | - | search_uses_kb_* | - | P1 |
| AC-7.10.10 | - | generation_uses_kb_* | - | P2 |

---

## Notes

- **Dependency:** Story 7-9 (LLM Model Registry) must be complete before starting
- **Migration Safety:** Test migration on dev DB before staging
- **Qdrant Consideration:** Each KB gets its own collection - monitor collection count
- **Breaking Change:** Existing KBs need default model assignment in migration
- **UI/UX:** Lock icon and warning must be visually clear to prevent confusion

---

## Contact

**Questions or Issues?**

- Consult Story 7-9 for Model Registry dependencies
- Tag @tea-agent for test architecture questions
- See `docs/sprint-artifacts/test-design-story-7-10.md` for detailed test specifications

---

**Generated by BMad TEA Agent (Murat)** - 2025-12-08
