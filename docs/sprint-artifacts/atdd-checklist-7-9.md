# ATDD Checklist - Epic 7, Story 7.9: LLM Model Registry

**Date:** 2025-12-08
**Author:** Tung Vu (TEA Agent)
**Primary Test Level:** API Integration
**Secondary Test Level:** E2E

---

## Story Summary

Administrators need a centralized registry to manage LLM models from multiple providers for embedding and generation tasks across Knowledge Bases.

**As an** administrator
**I want** a centralized LLM Model Registry to register and manage embedding and generation models from multiple providers
**So that** Knowledge Bases can be configured with specific models and the system supports diverse AI capabilities

---

## Acceptance Criteria

1. **AC-7.9.1:** Admin Model Registry page lists all registered models with type, provider, and status
2. **AC-7.9.2:** Add model form with type selection (Embedding/Generation)
3. **AC-7.9.3:** Type selection shows relevant parameter fields for embedding or generation models
4. **AC-7.9.4:** Provider selection (Ollama, OpenAI, Azure, Gemini, Anthropic, Cohere) shows dynamic fields
5. **AC-7.9.5:** Embedding model parameters include dimensions, max_tokens, normalize, distance_metric, batch_size
6. **AC-7.9.6:** Generation model parameters include context_window, max_output_tokens, temperature, top_p, top_k
7. **AC-7.9.7:** API endpoint and API key fields shown based on provider requirements
8. **AC-7.9.8:** Connection test validates model accessibility before saving
9. **AC-7.9.9:** Model status (active/inactive) displayed and toggleable
10. **AC-7.9.10:** Default model designation available per type (one default embedding, one default generation)
11. **AC-7.9.11:** Edit/delete actions with KB dependency warnings before deletion
12. **AC-7.9.12:** Audit logging for all model registry changes

---

## Failing Tests Created (RED Phase)

### API Integration Tests (16 tests)

**File:** `backend/tests/integration/test_model_registry_api.py` (TO BE CREATED)

#### Admin Route Protection (P0 - Critical Security)

- [ ] **Test:** `test_list_models_requires_admin`
  - **Status:** RED - Endpoint `/api/v1/admin/models` does not exist
  - **Verifies:** AC-7.9.1 - Non-admin user receives 403 Forbidden
  - **AC:** 7.9.1

- [ ] **Test:** `test_create_model_requires_admin`
  - **Status:** RED - POST endpoint not implemented
  - **Verifies:** Non-admin user cannot create models (403)
  - **AC:** 7.9.2

- [ ] **Test:** `test_delete_model_requires_admin`
  - **Status:** RED - DELETE endpoint not implemented
  - **Verifies:** Non-admin user cannot delete models (403)
  - **AC:** 7.9.11

- [ ] **Test:** `test_unauthenticated_returns_401`
  - **Status:** RED - Auth check not enforced
  - **Verifies:** Unauthenticated requests receive 401
  - **AC:** 7.9.1

#### Model CRUD Operations (P2 - Core Functionality)

- [ ] **Test:** `test_create_embedding_model_ollama`
  - **Status:** RED - LLMModel table does not exist
  - **Verifies:** AC-7.9.5 - Create Ollama embedding model with all parameters
  - **AC:** 7.9.2, 7.9.5

- [ ] **Test:** `test_create_generation_model_openai`
  - **Status:** RED - LLMModel table does not exist
  - **Verifies:** AC-7.9.6 - Create OpenAI generation model with all parameters
  - **AC:** 7.9.2, 7.9.6

- [ ] **Test:** `test_list_models_with_type_filter`
  - **Status:** RED - GET endpoint not implemented
  - **Verifies:** AC-7.9.1 - Filter models by type (embedding/generation)
  - **AC:** 7.9.1

- [ ] **Test:** `test_list_models_with_provider_filter`
  - **Status:** RED - GET endpoint not implemented
  - **Verifies:** AC-7.9.1 - Filter models by provider
  - **AC:** 7.9.1, 7.9.4

- [ ] **Test:** `test_update_model_parameters`
  - **Status:** RED - PUT endpoint not implemented
  - **Verifies:** Update model configuration
  - **AC:** 7.9.5, 7.9.6

- [ ] **Test:** `test_api_key_not_returned_in_response`
  - **Status:** RED - Response schema not filtering api_key
  - **Verifies:** AC-7.9.7 - API key excluded from all responses (P1 Security)
  - **AC:** 7.9.7

#### Connection Testing (P1 - Critical Validation)

- [ ] **Test:** `test_connection_test_success`
  - **Status:** RED - Test endpoint not implemented
  - **Verifies:** AC-7.9.8 - Valid config returns success
  - **AC:** 7.9.8

- [ ] **Test:** `test_connection_test_invalid_api_key`
  - **Status:** RED - Test endpoint not implemented
  - **Verifies:** AC-7.9.8 - Invalid API key returns detailed error
  - **AC:** 7.9.8

- [ ] **Test:** `test_connection_test_timeout`
  - **Status:** RED - Timeout handling not implemented
  - **Verifies:** AC-7.9.8 - Connection timeout handled gracefully
  - **AC:** 7.9.8

#### Default Model & Deletion (P1 - Data Integrity)

- [ ] **Test:** `test_set_default_model`
  - **Status:** RED - Default endpoint not implemented
  - **Verifies:** AC-7.9.10 - PATCH sets model as default
  - **AC:** 7.9.10

- [ ] **Test:** `test_delete_model_with_kb_dependency_blocked`
  - **Status:** RED - Dependency check not implemented
  - **Verifies:** AC-7.9.11 - DELETE returns 409 when KB uses model
  - **AC:** 7.9.11

- [ ] **Test:** `test_delete_response_includes_dependent_kbs`
  - **Status:** RED - Dependency info not included in response
  - **Verifies:** AC-7.9.11 - 409 response lists dependent KB names
  - **AC:** 7.9.11

---

### Unit Tests (12 tests)

**File:** `backend/tests/unit/test_model_registry_service.py` (TO BE CREATED)

#### Schema Validation (P2)

- [ ] **Test:** `test_model_type_enum_values`
  - **Status:** RED - ModelType enum not defined
  - **Verifies:** AC-7.9.2, 7.9.3 - model_type accepts: embedding, generation, ner
  - **AC:** 7.9.2, 7.9.3

- [ ] **Test:** `test_model_provider_enum_values`
  - **Status:** RED - ModelProvider enum not defined
  - **Verifies:** AC-7.9.4 - provider accepts: ollama, openai, azure, gemini, anthropic, cohere
  - **AC:** 7.9.4

- [ ] **Test:** `test_anthropic_embedding_rejected`
  - **Status:** RED - Provider validation not implemented
  - **Verifies:** AC-7.9.4 - Anthropic cannot be selected for embedding type
  - **AC:** 7.9.4

- [ ] **Test:** `test_embedding_dimensions_range`
  - **Status:** RED - Parameter validation not implemented
  - **Verifies:** AC-7.9.5 - dimensions accepts positive integers
  - **AC:** 7.9.5

- [ ] **Test:** `test_generation_temperature_range`
  - **Status:** RED - Parameter validation not implemented
  - **Verifies:** AC-7.9.6 - temperature between 0.0 and 2.0
  - **AC:** 7.9.6

- [ ] **Test:** `test_generation_top_p_range`
  - **Status:** RED - Parameter validation not implemented
  - **Verifies:** AC-7.9.6 - top_p between 0.0 and 1.0
  - **AC:** 7.9.6

#### Security Tests (P0/P1)

- [ ] **Test:** `test_api_key_encrypted_at_rest`
  - **Status:** RED - Encryption not implemented
  - **Verifies:** AC-7.9.7 - API key encrypted using pgcrypto
  - **AC:** 7.9.7

- [ ] **Test:** `test_api_key_decryption_for_connection_test`
  - **Status:** RED - Decryption not implemented
  - **Verifies:** AC-7.9.8 - API key decrypted for provider calls
  - **AC:** 7.9.7, 7.9.8

#### Default Model Logic (P1)

- [ ] **Test:** `test_only_one_default_per_type`
  - **Status:** RED - Default logic not implemented
  - **Verifies:** AC-7.9.10 - Setting new default clears previous
  - **AC:** 7.9.10

- [ ] **Test:** `test_default_model_must_be_active`
  - **Status:** RED - Active check not implemented
  - **Verifies:** AC-7.9.10 - Inactive model cannot be default
  - **AC:** 7.9.10

#### Audit Logging (P3)

- [ ] **Test:** `test_model_creation_audit_event`
  - **Status:** RED - Audit integration not implemented
  - **Verifies:** AC-7.9.12 - Model creation generates audit event
  - **AC:** 7.9.12

- [ ] **Test:** `test_model_deletion_audit_event`
  - **Status:** RED - Audit integration not implemented
  - **Verifies:** AC-7.9.12 - Model deletion logged with KB impact
  - **AC:** 7.9.12

---

### E2E Tests (10 tests)

**File:** `frontend/e2e/tests/admin/model-registry.spec.ts` (TO BE CREATED)

#### Model List Page (P2)

- [ ] **Test:** `test_model_registry_displays_model_list_table`
  - **Status:** RED - /admin/models route does not exist
  - **Verifies:** AC-7.9.1 - Table shows Name, Type, Provider, Status columns
  - **AC:** 7.9.1

- [ ] **Test:** `test_model_registry_filters_by_type_tabs`
  - **Status:** RED - Tab filtering not implemented
  - **Verifies:** AC-7.9.1 - All/Embedding/Generation tabs filter list
  - **AC:** 7.9.1

- [ ] **Test:** `test_model_registry_shows_status_badges`
  - **Status:** RED - Status badges not implemented
  - **Verifies:** AC-7.9.9 - Active/Inactive status displayed
  - **AC:** 7.9.9

#### Add Model Form (P2)

- [ ] **Test:** `test_add_model_type_selection_shows_relevant_fields`
  - **Status:** RED - AddModelModal not created
  - **Verifies:** AC-7.9.3 - Type selection toggles parameter fields
  - **AC:** 7.9.2, 7.9.3

- [ ] **Test:** `test_add_model_provider_selection_shows_dynamic_fields`
  - **Status:** RED - Provider fields not implemented
  - **Verifies:** AC-7.9.4 - Provider selection shows API key/endpoint fields
  - **AC:** 7.9.4, 7.9.7

- [ ] **Test:** `test_add_model_form_validation_prevents_invalid_submission`
  - **Status:** RED - Form validation not implemented
  - **Verifies:** AC-7.9.5, 7.9.6 - Required fields validated
  - **AC:** 7.9.5, 7.9.6

#### Connection Testing UI (P1)

- [ ] **Test:** `test_connection_test_button_shows_loading_state`
  - **Status:** RED - Test button not implemented
  - **Verifies:** AC-7.9.8 - Button shows spinner during test
  - **AC:** 7.9.8

- [ ] **Test:** `test_connection_test_success_shows_toast`
  - **Status:** RED - Success toast not implemented
  - **Verifies:** AC-7.9.8 - Success message displayed
  - **AC:** 7.9.8

- [ ] **Test:** `test_connection_test_failure_shows_error_details`
  - **Status:** RED - Error display not implemented
  - **Verifies:** AC-7.9.8 - Detailed error message shown
  - **AC:** 7.9.8

#### Delete with KB Warning (P1)

- [ ] **Test:** `test_delete_model_shows_kb_dependency_warning`
  - **Status:** RED - Delete dialog not implemented
  - **Verifies:** AC-7.9.11 - Warning lists dependent KB names
  - **AC:** 7.9.11

---

### Frontend Component Tests (6 tests)

**File:** `frontend/src/hooks/__tests__/useModelRegistry.test.ts` (TO BE CREATED)

- [ ] **Test:** `test_useModelRegistry_fetches_models_successfully`
  - **Status:** RED - Hook not created
  - **Verifies:** AC-7.9.1 - Hook fetches and returns model list
  - **AC:** 7.9.1

- [ ] **Test:** `test_useModelRegistry_filters_by_type`
  - **Status:** RED - Filter logic not implemented
  - **Verifies:** AC-7.9.1 - Hook supports type filter parameter
  - **AC:** 7.9.1

- [ ] **Test:** `test_useModelRegistry_handles_create_model`
  - **Status:** RED - Create mutation not implemented
  - **Verifies:** AC-7.9.2 - Hook provides createModel function
  - **AC:** 7.9.2

- [ ] **Test:** `test_useModelRegistry_handles_delete_with_error`
  - **Status:** RED - Error handling not implemented
  - **Verifies:** AC-7.9.11 - Hook handles 409 conflict response
  - **AC:** 7.9.11

- [ ] **Test:** `test_useModelRegistry_test_connection`
  - **Status:** RED - Test connection function not implemented
  - **Verifies:** AC-7.9.8 - Hook provides testConnection function
  - **AC:** 7.9.8

- [ ] **Test:** `test_useModelRegistry_set_default_model`
  - **Status:** RED - Set default function not implemented
  - **Verifies:** AC-7.9.10 - Hook provides setDefaultModel function
  - **AC:** 7.9.10

---

## Data Factories Created

### LLM Model Factory

**File:** `backend/tests/factories/model_factory.py` (TO BE CREATED)

**Exports:**

- `create_embedding_model(overrides?)` - Create embedding model with Ollama defaults
- `create_generation_model(overrides?)` - Create generation model with OpenAI defaults
- `create_model_with_kb_dependency(db_session)` - Create model linked to a KB

**Example Usage:**

```python
from tests.factories.model_factory import create_embedding_model, create_generation_model

# Create Ollama embedding model
model = create_embedding_model({
    "name": "custom-embedding",
    "dimensions": 1024
})

# Create OpenAI generation model
model = create_generation_model({
    "model_id": "gpt-4o",
    "temperature": 0.5
})
```

**Default Values:**

```python
EMBEDDING_MODEL_DEFAULTS = {
    "name": "test-embedding-{uuid}",
    "model_type": "embedding",
    "provider": "ollama",
    "model_id": "nomic-embed-text",
    "api_endpoint": "http://localhost:11434",
    "dimensions": 768,
    "max_tokens": 8192,
    "normalize": True,
    "distance_metric": "cosine",
    "batch_size": 32,
    "is_active": True,
    "is_default": False
}

GENERATION_MODEL_DEFAULTS = {
    "name": "test-generation-{uuid}",
    "model_type": "generation",
    "provider": "openai",
    "model_id": "gpt-4o-mini",
    "api_key": "sk-test-key-12345",
    "context_window": 128000,
    "max_output_tokens": 4096,
    "temperature": 0.7,
    "top_p": 1.0,
    "is_active": True,
    "is_default": False
}
```

---

## Fixtures Created

### Model Registry Test Fixtures

**File:** `backend/tests/integration/conftest.py` (EXTEND EXISTING)

**New Fixtures:**

```python
@pytest.fixture
async def embedding_model(db_session, admin_user):
    """Create test embedding model."""
    from tests.factories.model_factory import create_embedding_model
    model_data = create_embedding_model()
    # Insert into database
    return model

@pytest.fixture
async def generation_model(db_session, admin_user):
    """Create test generation model."""
    from tests.factories.model_factory import create_generation_model
    model_data = create_generation_model()
    # Insert into database
    return model

@pytest.fixture
async def model_with_kb_dependency(db_session, embedding_model, test_kb):
    """Create model that is linked to a KB."""
    # Link embedding_model to test_kb
    test_kb.embedding_model_id = embedding_model.id
    await db_session.commit()
    return embedding_model

@pytest.fixture
def mock_litellm_client(mocker):
    """Mock LiteLLM client for connection testing."""
    mock = mocker.patch('app.integrations.litellm_client.LiteLLMClient')
    mock.return_value.test_embedding.return_value = {"success": True, "dimensions": 768}
    mock.return_value.test_generation.return_value = {"success": True, "model": "gpt-4o-mini"}
    return mock
```

---

## Mock Requirements

### LiteLLM Client Mock (Connection Testing)

**Purpose:** Test connection validation without real provider calls

**Endpoint:** Provider-specific (Ollama, OpenAI, etc.)

**Success Response:**

```json
{
  "success": true,
  "model": "nomic-embed-text",
  "dimensions": 768,
  "latency_ms": 150
}
```

**Failure Responses:**

```json
// Invalid API Key
{
  "success": false,
  "error": "authentication_error",
  "message": "Invalid API key provided"
}

// Connection Timeout
{
  "success": false,
  "error": "timeout_error",
  "message": "Connection timed out after 30 seconds"
}

// Invalid Endpoint
{
  "success": false,
  "error": "connection_error",
  "message": "Could not connect to endpoint: http://invalid:11434"
}
```

**Implementation:**

```python
# backend/tests/mocks/litellm_mock.py
class MockLiteLLMClient:
    async def test_embedding(self, config: dict) -> dict:
        if config.get("api_key") == "invalid":
            return {"success": False, "error": "authentication_error", "message": "Invalid API key"}
        if "invalid" in config.get("api_endpoint", ""):
            return {"success": False, "error": "connection_error", "message": "Could not connect"}
        return {"success": True, "dimensions": config.get("dimensions", 768)}

    async def test_generation(self, config: dict) -> dict:
        if config.get("api_key") == "invalid":
            return {"success": False, "error": "authentication_error", "message": "Invalid API key"}
        return {"success": True, "model": config.get("model_id")}
```

---

## Required data-testid Attributes

### Model Registry Page (`/admin/models`)

- `model-list-table` - Main table container
- `model-type-tabs` - Tab container (All/Embedding/Generation)
- `model-type-tab-all` - "All" tab
- `model-type-tab-embedding` - "Embedding" tab
- `model-type-tab-generation` - "Generation" tab
- `add-model-button` - "Add Model" button
- `model-row-{id}` - Individual model row
- `model-status-badge-{id}` - Status badge (active/inactive)
- `model-actions-menu-{id}` - Actions dropdown
- `edit-model-button-{id}` - Edit action
- `delete-model-button-{id}` - Delete action
- `set-default-button-{id}` - Set as default action

### Add Model Modal

- `add-model-modal` - Modal container
- `model-name-input` - Name field
- `model-type-select` - Type dropdown
- `model-provider-select` - Provider dropdown
- `model-id-input` - Model ID field
- `api-endpoint-input` - API endpoint field
- `api-key-input` - API key field (password type)
- `embedding-dimensions-input` - Dimensions field (embedding only)
- `embedding-max-tokens-input` - Max tokens field (embedding only)
- `embedding-distance-metric-select` - Distance metric dropdown
- `generation-context-window-input` - Context window field (generation only)
- `generation-temperature-input` - Temperature slider
- `generation-top-p-input` - Top P slider
- `test-connection-button` - Test connection button
- `connection-status-indicator` - Success/failure indicator
- `save-model-button` - Save button
- `cancel-button` - Cancel button

### Delete Confirmation Modal

- `delete-model-modal` - Modal container
- `kb-dependency-warning` - Warning message
- `dependent-kb-list` - List of dependent KBs
- `confirm-delete-button` - Confirm delete
- `cancel-delete-button` - Cancel delete

**Implementation Example:**

```tsx
<Table data-testid="model-list-table">
  <TableRow data-testid={`model-row-${model.id}`}>
    <TableCell>{model.name}</TableCell>
    <TableCell>
      <Badge data-testid={`model-status-badge-${model.id}`}>
        {model.is_active ? 'Active' : 'Inactive'}
      </Badge>
    </TableCell>
    <TableCell>
      <DropdownMenu data-testid={`model-actions-menu-${model.id}`}>
        <DropdownMenuItem data-testid={`edit-model-button-${model.id}`}>
          Edit
        </DropdownMenuItem>
        <DropdownMenuItem data-testid={`delete-model-button-${model.id}`}>
          Delete
        </DropdownMenuItem>
      </DropdownMenu>
    </TableCell>
  </TableRow>
</Table>
```

---

## Implementation Checklist

### Task 1: Database Schema and Migration

**Tests:** `test_model_type_enum_values`, `test_model_provider_enum_values`, `test_embedding_dimensions_range`, `test_generation_temperature_range`

**Tasks to make these tests pass:**

- [ ] Create `backend/app/models/llm_model.py` with SQLAlchemy model
- [ ] Define `ModelType` enum: embedding, generation, ner
- [ ] Define `ModelProvider` enum: ollama, openai, azure, gemini, anthropic, cohere
- [ ] Add all columns: name, model_type, provider, model_id, api_endpoint, api_key (encrypted), dimensions, max_tokens, normalize, distance_metric, batch_size, context_window, max_output_tokens, temperature, top_p, top_k, is_active, is_default
- [ ] Create Alembic migration: `alembic revision --autogenerate -m "create_llm_models_table"`
- [ ] Add pgcrypto extension for API key encryption
- [ ] Run migration: `alembic upgrade head`
- [ ] Run tests: `pytest backend/tests/unit/test_model_registry_service.py -v -k "enum or range"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 3 hours

---

### Task 2: Model Registry API Endpoints (CRUD)

**Tests:** `test_create_embedding_model_ollama`, `test_create_generation_model_openai`, `test_list_models_with_type_filter`, `test_update_model_parameters`

**Tasks to make these tests pass:**

- [ ] Create `backend/app/schemas/llm_model.py` with Pydantic schemas
- [ ] Define `LLMModelCreate`, `LLMModelUpdate`, `LLMModelResponse` schemas
- [ ] Exclude `api_key` from `LLMModelResponse`
- [ ] Create `backend/app/services/model_registry_service.py`
- [ ] Implement `ModelRegistryService.create_model()`
- [ ] Implement `ModelRegistryService.get_models(type_filter, provider_filter)`
- [ ] Implement `ModelRegistryService.update_model()`
- [ ] Add endpoints to `backend/app/api/v1/admin.py`:
  - POST `/api/v1/admin/models`
  - GET `/api/v1/admin/models`
  - GET `/api/v1/admin/models/{id}`
  - PUT `/api/v1/admin/models/{id}`
- [ ] Run tests: `pytest backend/tests/integration/test_model_registry_api.py -v -k "create or list or update"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 4 hours

---

### Task 3: Admin Route Protection (P0 Security)

**Tests:** `test_list_models_requires_admin`, `test_create_model_requires_admin`, `test_delete_model_requires_admin`, `test_unauthenticated_returns_401`

**Tasks to make these tests pass:**

- [ ] Add `current_active_superuser` dependency to all model endpoints
- [ ] Verify 403 response for non-admin users
- [ ] Verify 401 response for unauthenticated requests
- [ ] Run tests: `pytest backend/tests/integration/test_model_registry_api.py -v -k "requires_admin or unauthenticated"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 1 hour

---

### Task 4: API Key Security (P1)

**Tests:** `test_api_key_not_returned_in_response`, `test_api_key_encrypted_at_rest`, `test_api_key_decryption_for_connection_test`

**Tasks to make these tests pass:**

- [ ] Implement API key encryption using pgcrypto in model creation
- [ ] Ensure `api_key` excluded from all response schemas
- [ ] Implement `decrypt_api_key()` utility for connection testing
- [ ] Add API key masking in audit logs
- [ ] Run tests: `pytest backend/tests/unit/test_model_registry_service.py -v -k "api_key"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 2 hours

---

### Task 5: Connection Testing API

**Tests:** `test_connection_test_success`, `test_connection_test_invalid_api_key`, `test_connection_test_timeout`

**Tasks to make these tests pass:**

- [ ] Create `backend/app/services/model_connection_tester.py`
- [ ] Implement provider-specific testers (OllamaConnectionTester, OpenAIConnectionTester, etc.)
- [ ] Integrate with LiteLLM client for actual provider calls
- [ ] Add timeout handling (30 second default)
- [ ] Return detailed error messages on failure
- [ ] Add POST `/api/v1/admin/models/{id}/test` endpoint
- [ ] Run tests: `pytest backend/tests/integration/test_model_registry_api.py -v -k "connection_test"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 3 hours

---

### Task 6: Default Model Management

**Tests:** `test_set_default_model`, `test_only_one_default_per_type`, `test_default_model_must_be_active`

**Tasks to make these tests pass:**

- [ ] Implement `ModelRegistryService.set_default_model()`
- [ ] Add logic to clear previous default of same type
- [ ] Validate model is active before setting as default
- [ ] Add PATCH `/api/v1/admin/models/{id}/default` endpoint
- [ ] Run tests: `pytest backend/tests/integration/test_model_registry_api.py -v -k "default"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 1.5 hours

---

### Task 7: Model Deletion with KB Dependency Check

**Tests:** `test_delete_model_with_kb_dependency_blocked`, `test_delete_response_includes_dependent_kbs`

**Tasks to make these tests pass:**

- [ ] Implement `ModelRegistryService.check_kb_dependencies(model_id)`
- [ ] Query knowledge_bases table for embedding_model_id or generation_model_id references
- [ ] Return 409 Conflict if dependencies exist
- [ ] Include list of dependent KB names in error response
- [ ] Add DELETE `/api/v1/admin/models/{id}` endpoint with dependency check
- [ ] Run tests: `pytest backend/tests/integration/test_model_registry_api.py -v -k "delete"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 2 hours

---

### Task 8: Audit Logging Integration

**Tests:** `test_model_creation_audit_event`, `test_model_deletion_audit_event`

**Tasks to make these tests pass:**

- [ ] Add audit event types: MODEL_CREATED, MODEL_UPDATED, MODEL_DELETED, MODEL_CONNECTION_TESTED
- [ ] Log model creation with full configuration (excluding api_key)
- [ ] Log model updates with changed fields only
- [ ] Log model deletion with any KB dependency warnings
- [ ] Log connection test attempts with success/failure
- [ ] Run tests: `pytest backend/tests/unit/test_model_registry_service.py -v -k "audit"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 1.5 hours

---

### Task 9: Model Registry Admin UI - List Page

**Tests:** `test_model_registry_displays_model_list_table`, `test_model_registry_filters_by_type_tabs`, `test_model_registry_shows_status_badges`

**Tasks to make these tests pass:**

- [ ] Create `frontend/src/app/(protected)/admin/models/page.tsx`
- [ ] Create `frontend/src/components/admin/model-list-table.tsx`
- [ ] Implement type tabs (All/Embedding/Generation)
- [ ] Add status badges (active/inactive)
- [ ] Create `frontend/src/hooks/useModelRegistry.ts`
- [ ] Add data-testid attributes as specified
- [ ] Run tests: `npx playwright test frontend/e2e/tests/admin/model-registry.spec.ts -g "displays\|filters\|status"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 4 hours

---

### Task 10: Add Model Modal with Dynamic Fields

**Tests:** `test_add_model_type_selection_shows_relevant_fields`, `test_add_model_provider_selection_shows_dynamic_fields`, `test_add_model_form_validation_prevents_invalid_submission`

**Tasks to make these tests pass:**

- [ ] Create `frontend/src/components/admin/add-model-modal.tsx`
- [ ] Implement type selector with conditional field rendering
- [ ] Show embedding fields when type=embedding (dimensions, max_tokens, etc.)
- [ ] Show generation fields when type=generation (context_window, temperature, etc.)
- [ ] Implement provider selector with dynamic API key/endpoint fields
- [ ] Add form validation using react-hook-form and zod
- [ ] Add data-testid attributes as specified
- [ ] Run tests: `npx playwright test frontend/e2e/tests/admin/model-registry.spec.ts -g "type_selection\|provider_selection\|validation"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 4 hours

---

### Task 11: Connection Test UI

**Tests:** `test_connection_test_button_shows_loading_state`, `test_connection_test_success_shows_toast`, `test_connection_test_failure_shows_error_details`

**Tasks to make these tests pass:**

- [ ] Add "Test Connection" button to add/edit model modal
- [ ] Implement loading state with spinner
- [ ] Show success toast on successful connection
- [ ] Show detailed error toast on failure
- [ ] Disable save button until connection tested successfully
- [ ] Add data-testid: `test-connection-button`, `connection-status-indicator`
- [ ] Run tests: `npx playwright test frontend/e2e/tests/admin/model-registry.spec.ts -g "connection_test"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 2 hours

---

### Task 12: Delete Modal with KB Warning

**Tests:** `test_delete_model_shows_kb_dependency_warning`

**Tasks to make these tests pass:**

- [ ] Create delete confirmation modal component
- [ ] Fetch KB dependencies when delete is initiated
- [ ] Display warning with list of dependent KB names
- [ ] Disable confirm button if dependencies exist
- [ ] Add data-testid: `delete-model-modal`, `kb-dependency-warning`, `dependent-kb-list`
- [ ] Run tests: `npx playwright test frontend/e2e/tests/admin/model-registry.spec.ts -g "delete\|dependency"`
- [ ] Tests pass (green phase)

**Estimated Effort:** 2 hours

---

## Running Tests

```bash
# Run all backend integration tests for model registry
pytest backend/tests/integration/test_model_registry_api.py -v

# Run all backend unit tests for model registry
pytest backend/tests/unit/test_model_registry_service.py -v

# Run all frontend E2E tests for model registry
npx playwright test frontend/e2e/tests/admin/model-registry.spec.ts

# Run frontend hook tests
npm run test:run -- frontend/src/hooks/__tests__/useModelRegistry.test.ts

# Run specific backend test
pytest backend/tests/integration/test_model_registry_api.py::test_create_embedding_model_ollama -v

# Run E2E tests in headed mode (see browser)
npx playwright test frontend/e2e/tests/admin/model-registry.spec.ts --headed

# Debug specific E2E test
npx playwright test frontend/e2e/tests/admin/model-registry.spec.ts --debug

# Run P0 security tests only
pytest backend/tests/integration/test_model_registry_api.py -v -k "requires_admin or unauthenticated"

# Run all model registry tests (backend + frontend)
pytest backend/tests/unit/test_model_registry_service.py backend/tests/integration/test_model_registry_api.py -v && npx playwright test frontend/e2e/tests/admin/model-registry.spec.ts
```

---

## Red-Green-Refactor Workflow

### RED Phase (Current) - Tests Written

**TEA Agent Responsibilities:**

- [ ] All tests written and documented (44 total tests)
  - 16 API integration tests
  - 12 backend unit tests
  - 10 E2E tests
  - 6 frontend component tests
- [ ] Data factory extensions documented
- [ ] Fixtures identified and documented
- [ ] Mock requirements documented (LiteLLM client)
- [ ] Required data-testid attributes listed (30+ attributes)
- [ ] Implementation checklist created (12 tasks with concrete steps)

**Verification:**

- All tests fail with clear error messages
- Failures are due to missing implementation, not test bugs
- Tests follow Given-When-Then structure
- Priority markers (P0, P1, P2, P3) assigned

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Pick one failing test** from implementation checklist (start with P0 security)
2. **Read the test** to understand expected behavior
3. **Implement minimal code** to make that specific test pass
4. **Run the test** to verify it now passes (green)
5. **Check off the task** in implementation checklist
6. **Move to next test** and repeat

**Recommended Implementation Order:**

1. **P0 First:** Admin route protection (Task 3)
2. **Schema & Migration:** Database setup (Task 1)
3. **API CRUD:** Core endpoints (Task 2)
4. **P1 Security:** API key handling (Task 4)
5. **P1 Features:** Connection testing, deletion, defaults (Tasks 5-7)
6. **P3 Compliance:** Audit logging (Task 8)
7. **Frontend:** UI components (Tasks 9-12)

**Key Principles:**

- One test at a time (don't try to fix all at once)
- Minimal implementation (don't over-engineer)
- Run tests frequently (immediate feedback)
- Use implementation checklist as roadmap

**Progress Tracking:**

- Check off tasks as you complete them
- Share progress in daily standup
- Mark story as IN PROGRESS in `sprint-status.yaml`

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

**DEV Agent Responsibilities:**

1. **Verify all tests pass** (green phase complete)
2. **Review code for quality** (readability, maintainability)
3. **Extract duplications** (DRY principle)
4. **Optimize performance** (database queries, caching)
5. **Ensure tests still pass** after each refactor
6. **Update documentation** (OpenAPI docs)

**Key Principles:**

- Tests provide safety net (refactor with confidence)
- Make small refactors (easier to debug if tests fail)
- Run tests after each change
- Don't change test behavior (only implementation)

**Completion:**

- All tests pass
- Code quality meets team standards
- No duplications or code smells
- Ready for code review and story approval

---

## Next Steps

1. **Review this checklist** with team in standup
2. **Create test files** (empty with test stubs)
3. **Run failing tests** to confirm RED phase
4. **Begin implementation** starting with Task 3 (P0 Security)
5. **Work one test at a time** (red -> green for each)
6. **Share progress** in daily standup
7. **When all tests pass**, refactor code for quality
8. **When refactoring complete**, run `/bmad:bmm:workflows:story-done 7-9`

---

## Knowledge Base References Applied

This ATDD workflow consulted the following knowledge fragments:

- **test-quality.md** - Test design principles (Given-When-Then, one assertion per test)
- **test-levels-framework.md** - Test level selection (API Integration primary, E2E secondary)
- **data-factories.md** - Factory patterns for model test data
- **fixture-architecture.md** - Reusable fixture patterns
- **risk-governance.md** - P0/P1/P2/P3 priority classification
- **probability-impact.md** - Risk scoring matrix

See `.bmad/bmm/testarch/tea-index.csv` for complete knowledge fragment mapping.

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `pytest backend/tests/integration/test_model_registry_api.py -v`

**Expected Results:**

```
FAILED - FileNotFoundError: test_model_registry_api.py does not exist
... (all 16 tests fail with file not found)
```

**Command:** `npx playwright test frontend/e2e/tests/admin/model-registry.spec.ts`

**Expected Results:**

```
ERROR: Could not load test file model-registry.spec.ts
... (all 10 tests fail with file not found)
```

**Summary:**

- Total tests: 44
- Passing: 0 (expected)
- Failing: 44 (expected)
- Status: RED phase verified (tests don't exist yet, ready for implementation)

---

## Notes

**Provider Support Matrix:**

| Provider | Embedding | Generation | API Key Required | Endpoint Required |
|----------|-----------|------------|------------------|-------------------|
| Ollama | Yes | Yes | No | Yes |
| OpenAI | Yes | Yes | Yes | No |
| Azure | Yes | Yes | Yes | Yes |
| Gemini | Yes | Yes | Yes | No |
| Anthropic | No | Yes | Yes | No |
| Cohere | Yes | Yes | Yes | No |

**Security Considerations:**

- API keys encrypted at rest using pgcrypto
- API keys NEVER returned in API responses
- API keys masked in audit logs
- All endpoints require admin authentication

**Dependencies:**

- Story 7-2 (Centralized LLM Configuration) must be complete
- LiteLLM integration already exists in codebase

---

## Contact

**Questions or Issues?**

- Ask in team standup
- Tag @tea in Slack/Discord
- Refer to `.bmad/bmm/testarch/knowledge` for testing best practices
- Consult story file: `docs/sprint-artifacts/7-9-llm-model-registry.md`
- Reference test design: `docs/sprint-artifacts/test-design-story-7-9.md`

---

**Generated by BMad TEA Agent** - 2025-12-08
