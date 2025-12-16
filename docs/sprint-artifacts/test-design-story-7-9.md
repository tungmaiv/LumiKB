# Test Design: Story 7-9 LLM Model Registry

| Field | Value |
|-------|-------|
| Story ID | 7-9 |
| Story Title | LLM Model Registry |
| Epic | 7 - Infrastructure & DevOps |
| Author | TEA (Murat) |
| Date | 2025-12-08 |
| Status | Draft |

---

## 1. Executive Summary

Story 7-9 implements a centralized LLM Model Registry allowing administrators to register and manage embedding and generation models from multiple providers (Ollama, OpenAI, Azure, Gemini, Anthropic, Cohere). This test design provides comprehensive coverage for all 12 acceptance criteria with risk-based prioritization.

### Risk Assessment Summary

| Priority | Count | Risk Categories |
|----------|-------|-----------------|
| P0 (Critical) | 2 | SEC (API Key Security), DATA (Model Deletion) |
| P1 (High) | 5 | TECH (Connection Testing), SEC (Admin Access), OPS (Default Models) |
| P2 (Medium) | 4 | TECH (CRUD Operations), OPS (Status Management) |
| P3 (Low) | 3 | BUS (UI Display), OPS (Audit Logging) |

---

## 2. Risk-Based Test Prioritization

### 2.1 Risk Assessment Matrix

| ID | Test Scenario | Category | Probability | Impact | Score | Priority | Action |
|----|---------------|----------|-------------|--------|-------|----------|--------|
| R1 | API key exposure in responses | SEC | 2 | 3 | 6 | P1 | MITIGATE |
| R2 | API key encryption at rest | SEC | 2 | 3 | 6 | P1 | MITIGATE |
| R3 | Non-admin access to model endpoints | SEC | 3 | 3 | 9 | P0 | BLOCK |
| R4 | Model deletion with KB dependencies | DATA | 2 | 3 | 6 | P1 | MITIGATE |
| R5 | Connection test timeout/hang | TECH | 2 | 2 | 4 | P2 | MONITOR |
| R6 | Invalid provider credentials accepted | TECH | 2 | 3 | 6 | P1 | MITIGATE |
| R7 | Multiple default models per type | OPS | 2 | 3 | 6 | P1 | MITIGATE |
| R8 | Model CRUD validation errors | TECH | 2 | 2 | 4 | P2 | MONITOR |
| R9 | Provider-specific field validation | TECH | 2 | 2 | 4 | P2 | MONITOR |
| R10 | Audit log completeness | OPS | 1 | 2 | 2 | P3 | DOCUMENT |
| R11 | UI form state management | BUS | 2 | 1 | 2 | P3 | DOCUMENT |
| R12 | Status toggle race conditions | OPS | 2 | 2 | 4 | P2 | MONITOR |

### 2.2 Risk Mitigation Strategies

| Risk ID | Mitigation Strategy | Test Coverage |
|---------|---------------------|---------------|
| R3 | Admin role guard on all model endpoints | Integration: test_admin_route_protection |
| R1, R2 | pgcrypto encryption + response filtering | Unit: test_api_key_security |
| R4 | KB dependency check before deletion | Integration: test_model_deletion_dependency |
| R6 | Provider-specific connection validators | Integration: test_connection_validators |
| R7 | DB constraint + service validation | Unit: test_default_model_constraint |

---

## 3. Test Coverage Matrix

### 3.1 Acceptance Criteria to Test Mapping

| AC | Description | Unit Tests | Integration Tests | E2E Tests |
|----|-------------|------------|-------------------|-----------|
| AC-7.9.1 | Model list with type, provider, status | - | `test_list_models_*` | `model-registry.spec.ts` |
| AC-7.9.2 | Add model form with type selection | `test_model_schema_*` | `test_create_model_*` | `add-model.spec.ts` |
| AC-7.9.3 | Type-specific parameter fields | `test_type_params_*` | - | `model-form.spec.ts` |
| AC-7.9.4 | Provider selection dynamic fields | `test_provider_params_*` | - | `provider-fields.spec.ts` |
| AC-7.9.5 | Embedding parameters | `test_embedding_params` | `test_create_embedding_model` | - |
| AC-7.9.6 | Generation parameters | `test_generation_params` | `test_create_generation_model` | - |
| AC-7.9.7 | API endpoint/key fields | `test_api_key_encryption` | `test_api_key_security` | - |
| AC-7.9.8 | Connection test validation | `test_connection_tester_*` | `test_connection_test_*` | `connection-test.spec.ts` |
| AC-7.9.9 | Status display and toggle | - | `test_model_status_toggle` | `status-toggle.spec.ts` |
| AC-7.9.10 | Default model designation | `test_default_constraint` | `test_set_default_model` | - |
| AC-7.9.11 | Edit/delete with KB warnings | - | `test_model_deletion_*` | `delete-warning.spec.ts` |
| AC-7.9.12 | Audit logging | `test_audit_events` | `test_model_audit_*` | - |

---

## 4. Unit Test Design

### 4.1 Model Schema Validation Tests

**File**: `backend/tests/unit/test_model_registry_service.py`

```python
class TestLLMModelSchemaValidation:
    """Unit tests for LLM model schema validation (AC-7.9.2, 7.9.5, 7.9.6)."""

    # P2: Model type validation
    def test_model_type_enum_values(self):
        """Verify model_type accepts only: embedding, generation, ner"""

    def test_model_type_required_field(self):
        """Verify model_type is required on creation"""

    # P2: Provider validation
    def test_model_provider_enum_values(self):
        """Verify provider accepts: ollama, openai, azure, gemini, anthropic, cohere"""

    def test_anthropic_embedding_rejected(self):
        """Verify Anthropic cannot be selected for embedding type (AC-7.9.4)"""

    # P2: Embedding parameters (AC-7.9.5)
    def test_embedding_dimensions_range(self):
        """Verify dimensions accepts positive integers"""

    def test_embedding_max_tokens_validation(self):
        """Verify max_tokens within provider limits"""

    def test_embedding_distance_metric_enum(self):
        """Verify distance_metric: cosine, dot, euclidean"""

    # P2: Generation parameters (AC-7.9.6)
    def test_generation_temperature_range(self):
        """Verify temperature between 0.0 and 2.0"""

    def test_generation_top_p_range(self):
        """Verify top_p between 0.0 and 1.0"""

    def test_generation_context_window_validation(self):
        """Verify context_window is positive integer"""
```

### 4.2 API Key Security Tests (P0/P1)

**File**: `backend/tests/unit/test_model_security.py`

```python
class TestAPIKeySecurity:
    """Unit tests for API key encryption and security (AC-7.9.7)."""

    # P0: Critical security tests
    def test_api_key_encrypted_at_rest(self):
        """Verify API key is encrypted using pgcrypto before storage"""

    def test_api_key_not_in_response_schema(self):
        """Verify LLMModelResponse schema excludes api_key field"""

    def test_api_key_decryption_for_connection_test(self):
        """Verify API key can be decrypted for provider calls"""

    # P1: Security boundary tests
    def test_api_key_masked_in_logs(self):
        """Verify API keys are masked in audit/debug logs"""

    def test_empty_api_key_for_ollama(self):
        """Verify Ollama provider allows empty API key"""
```

### 4.3 Connection Tester Tests (P1)

**File**: `backend/tests/unit/test_connection_testers.py`

```python
class TestProviderConnectionTesters:
    """Unit tests for provider-specific connection testers (AC-7.9.8)."""

    # P1: Provider testers
    def test_ollama_connection_tester_embedding(self):
        """Verify Ollama embedding test with local endpoint"""

    def test_openai_connection_tester_generation(self):
        """Verify OpenAI generation test with API key"""

    def test_azure_connection_tester_with_endpoint(self):
        """Verify Azure requires both API key and endpoint"""

    def test_connection_timeout_handling(self):
        """Verify timeout returns proper error message"""

    def test_invalid_credentials_error_message(self):
        """Verify detailed error for invalid API key"""
```

### 4.4 Default Model Constraint Tests (P1)

**File**: `backend/tests/unit/test_default_model_service.py`

```python
class TestDefaultModelConstraint:
    """Unit tests for default model designation (AC-7.9.10)."""

    # P1: Business rule enforcement
    def test_only_one_default_per_type(self):
        """Verify setting new default clears previous default"""

    def test_default_model_must_be_active(self):
        """Verify inactive model cannot be set as default"""

    def test_cannot_deactivate_default_model(self):
        """Verify default model cannot be deactivated without replacement"""
```

---

## 5. Integration Test Design

### 5.1 Admin Route Protection Tests (P0)

**File**: `backend/tests/integration/test_model_registry_api.py`

```python
class TestModelRegistryAdminProtection:
    """Integration tests for admin-only access (P0 Security)."""

    # P0: Critical security - must pass before deployment
    async def test_list_models_requires_admin(self, api_client, regular_cookies):
        """GET /api/v1/admin/models returns 403 for non-admin"""

    async def test_create_model_requires_admin(self, api_client, regular_cookies):
        """POST /api/v1/admin/models returns 403 for non-admin"""

    async def test_update_model_requires_admin(self, api_client, regular_cookies):
        """PUT /api/v1/admin/models/{id} returns 403 for non-admin"""

    async def test_delete_model_requires_admin(self, api_client, regular_cookies):
        """DELETE /api/v1/admin/models/{id} returns 403 for non-admin"""

    async def test_connection_test_requires_admin(self, api_client, regular_cookies):
        """POST /api/v1/admin/models/{id}/test returns 403 for non-admin"""

    async def test_unauthenticated_returns_401(self, api_client):
        """All endpoints return 401 without authentication"""
```

### 5.2 Model CRUD Operations Tests (P2)

**File**: `backend/tests/integration/test_model_registry_api.py`

```python
class TestModelRegistryCRUD:
    """Integration tests for model CRUD operations (AC-7.9.1, 7.9.2)."""

    # P2: Core functionality
    async def test_create_embedding_model_ollama(self, api_client, admin_cookies):
        """Create Ollama embedding model with all parameters (AC-7.9.5)"""

    async def test_create_generation_model_openai(self, api_client, admin_cookies):
        """Create OpenAI generation model with all parameters (AC-7.9.6)"""

    async def test_list_models_with_type_filter(self, api_client, admin_cookies):
        """GET /api/v1/admin/models?type=embedding returns filtered list"""

    async def test_list_models_with_provider_filter(self, api_client, admin_cookies):
        """GET /api/v1/admin/models?provider=openai returns filtered list"""

    async def test_get_model_by_id(self, api_client, admin_cookies):
        """GET /api/v1/admin/models/{id} returns model details"""

    async def test_update_model_parameters(self, api_client, admin_cookies):
        """PUT /api/v1/admin/models/{id} updates model configuration"""

    async def test_api_key_not_returned_in_response(self, api_client, admin_cookies):
        """Verify API key is filtered from all responses (P1 Security)"""
```

### 5.3 Connection Testing Integration (P1)

**File**: `backend/tests/integration/test_model_connection_api.py`

```python
class TestModelConnectionAPI:
    """Integration tests for model connection testing (AC-7.9.8)."""

    # P1: Connection validation critical for model registration
    async def test_connection_test_success(self, api_client, admin_cookies, mock_litellm):
        """POST /api/v1/admin/models/{id}/test returns success for valid config"""

    async def test_connection_test_invalid_endpoint(self, api_client, admin_cookies):
        """Connection test returns detailed error for unreachable endpoint"""

    async def test_connection_test_invalid_api_key(self, api_client, admin_cookies, mock_litellm):
        """Connection test returns auth error for invalid API key"""

    async def test_connection_test_timeout(self, api_client, admin_cookies, mock_litellm):
        """Connection test handles timeout gracefully with error message"""

    async def test_embedding_test_validates_dimensions(self, api_client, admin_cookies, mock_litellm):
        """Embedding connection test validates returned dimensions match config"""
```

### 5.4 Model Deletion with Dependencies (P1)

**File**: `backend/tests/integration/test_model_deletion_api.py`

```python
class TestModelDeletionAPI:
    """Integration tests for model deletion with KB dependencies (AC-7.9.11)."""

    # P1: Data integrity protection
    async def test_delete_model_no_dependencies(self, api_client, admin_cookies):
        """DELETE /api/v1/admin/models/{id} succeeds when no KBs use model"""

    async def test_delete_model_with_kb_dependency_blocked(self, api_client, admin_cookies, kb_with_model):
        """DELETE returns 409 Conflict when KB uses model"""

    async def test_delete_response_includes_dependent_kbs(self, api_client, admin_cookies, kb_with_model):
        """409 response includes list of dependent KB names"""

    async def test_delete_default_model_blocked(self, api_client, admin_cookies):
        """DELETE returns 400 for default model without replacement"""
```

### 5.5 Default Model Management (P1)

**File**: `backend/tests/integration/test_default_model_api.py`

```python
class TestDefaultModelAPI:
    """Integration tests for default model designation (AC-7.9.10)."""

    # P1: System operation depends on default models
    async def test_set_default_model(self, api_client, admin_cookies):
        """PATCH /api/v1/admin/models/{id}/default sets model as default"""

    async def test_set_default_clears_previous(self, api_client, admin_cookies):
        """Setting new default clears previous default of same type"""

    async def test_only_active_model_can_be_default(self, api_client, admin_cookies):
        """PATCH returns 400 for inactive model"""

    async def test_get_default_embedding_model(self, api_client, admin_cookies):
        """GET /api/v1/admin/models?is_default=true&type=embedding"""
```

### 5.6 Public Model Endpoints (P2)

**File**: `backend/tests/integration/test_public_models_api.py`

```python
class TestPublicModelsAPI:
    """Integration tests for public model list endpoints (AC-7.9.1)."""

    # P2: User-facing model selection
    async def test_list_embedding_models_public(self, api_client, user_cookies):
        """GET /api/v1/models/embedding returns active models"""

    async def test_list_generation_models_public(self, api_client, user_cookies):
        """GET /api/v1/models/generation returns active models"""

    async def test_public_list_excludes_inactive(self, api_client, user_cookies):
        """Public endpoints only return is_active=true models"""

    async def test_public_list_excludes_api_key(self, api_client, user_cookies):
        """Public responses never include api_key or api_endpoint"""
```

### 5.7 Audit Logging Tests (P3)

**File**: `backend/tests/integration/test_model_audit_api.py`

```python
class TestModelAuditLogging:
    """Integration tests for model registry audit logging (AC-7.9.12)."""

    # P3: Compliance requirement but not blocking
    async def test_model_creation_logged(self, api_client, admin_cookies, audit_service):
        """Model creation generates MODEL_CREATED audit event"""

    async def test_model_update_logs_changed_fields(self, api_client, admin_cookies, audit_service):
        """Model update logs only changed fields in details"""

    async def test_model_deletion_logs_kb_impact(self, api_client, admin_cookies, audit_service):
        """Model deletion logs any KB dependency warnings"""

    async def test_connection_test_logged(self, api_client, admin_cookies, audit_service):
        """Connection test attempts logged with success/failure"""
```

---

## 6. E2E Test Design

### 6.1 Model Registry Page Tests

**File**: `frontend/e2e/tests/admin/model-registry.spec.ts`

```typescript
describe('Model Registry Admin Page (AC-7.9.1)', () => {
  // P2: Core UI functionality
  test('displays model list table with columns', async ({ adminPage }) => {
    // Verify: Name, Type, Provider, Status columns visible
  });

  test('filters models by type tab selection', async ({ adminPage }) => {
    // Click "Embedding" tab, verify only embedding models shown
  });

  test('displays status badge for each model', async ({ adminPage }) => {
    // Verify active/inactive status badges
  });
});
```

### 6.2 Add Model Flow Tests

**File**: `frontend/e2e/tests/admin/add-model.spec.ts`

```typescript
describe('Add Model Modal (AC-7.9.2, 7.9.3, 7.9.4)', () => {
  // P2: Model creation flow
  test('type selection shows relevant parameter fields', async ({ adminPage }) => {
    // Select "Embedding" -> dimensions, max_tokens visible
    // Select "Generation" -> context_window, temperature visible
  });

  test('provider selection shows dynamic fields', async ({ adminPage }) => {
    // Select "OpenAI" -> API key required
    // Select "Ollama" -> API endpoint required, API key optional
  });

  test('form validation prevents invalid submission', async ({ adminPage }) => {
    // Submit without required fields -> validation errors shown
  });
});
```

### 6.3 Connection Test Flow Tests (P1)

**File**: `frontend/e2e/tests/admin/connection-test.spec.ts`

```typescript
describe('Model Connection Testing (AC-7.9.8)', () => {
  // P1: Critical for model validation
  test('test connection button shows loading state', async ({ adminPage }) => {
    // Click "Test Connection" -> spinner visible
  });

  test('successful connection shows success toast', async ({ adminPage }) => {
    // Mock successful response -> success message displayed
  });

  test('failed connection shows error details', async ({ adminPage }) => {
    // Mock failure -> detailed error message in toast
  });

  test('connection test required before save', async ({ adminPage }) => {
    // Save button disabled until connection tested
  });
});
```

### 6.4 Delete with KB Warning Tests (P1)

**File**: `frontend/e2e/tests/admin/delete-warning.spec.ts`

```typescript
describe('Model Deletion with KB Dependencies (AC-7.9.11)', () => {
  // P1: Data integrity UI
  test('delete button opens confirmation dialog', async ({ adminPage }) => {
    // Click delete -> confirmation modal appears
  });

  test('KB dependency warning shown in dialog', async ({ adminPage }) => {
    // Model with KB deps -> warning lists KB names
  });

  test('deletion blocked when KBs depend on model', async ({ adminPage }) => {
    // Confirm delete on model with deps -> error toast
  });
});
```

---

## 7. Test Data Requirements

### 7.1 Test Fixtures

```python
# backend/tests/factories/model_factory.py

class LLMModelFactory:
    """Factory for creating test LLM models."""

    @staticmethod
    def create_embedding_model(**overrides) -> dict:
        return {
            "name": f"test-embedding-{uuid4().hex[:8]}",
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
            **overrides
        }

    @staticmethod
    def create_generation_model(**overrides) -> dict:
        return {
            "name": f"test-generation-{uuid4().hex[:8]}",
            "model_type": "generation",
            "provider": "openai",
            "model_id": "gpt-4o-mini",
            "api_key": "sk-test-key-12345",
            "context_window": 128000,
            "max_output_tokens": 4096,
            "temperature": 0.7,
            "top_p": 1.0,
            "is_active": True,
            **overrides
        }
```

### 7.2 Mock Services

```python
# backend/tests/mocks/litellm_mock.py

class MockLiteLLMClient:
    """Mock for LiteLLM provider calls in tests."""

    async def test_embedding(self, model_config: dict) -> dict:
        """Mock embedding test response."""
        if model_config.get("api_key") == "invalid":
            raise AuthenticationError("Invalid API key")
        return {"success": True, "dimensions": model_config.get("dimensions", 768)}

    async def test_generation(self, model_config: dict) -> dict:
        """Mock generation test response."""
        if model_config.get("api_endpoint", "").startswith("http://invalid"):
            raise ConnectionError("Failed to connect")
        return {"success": True, "model": model_config.get("model_id")}
```

---

## 8. Test Execution Strategy

### 8.1 Test Execution Order

1. **P0 Security Tests** (Gate: BLOCK if any fail)
   - Admin route protection
   - API key exposure prevention

2. **P1 Critical Tests** (Gate: CONCERNS if >10% fail)
   - Connection test validation
   - Model deletion with dependencies
   - Default model constraints
   - API key encryption

3. **P2 Core Functionality** (Gate: MONITOR)
   - CRUD operations
   - Provider-specific validation
   - Public model endpoints

4. **P3 Supporting Tests** (Gate: DOCUMENT)
   - Audit logging
   - UI state management

### 8.2 CI Pipeline Integration

```yaml
# .github/workflows/test-7-9.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run P0/P1 Unit Tests
        run: pytest backend/tests/unit/test_model_*.py -m "p0 or p1" --tb=short

  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
    steps:
      - name: Run Integration Tests
        run: pytest backend/tests/integration/test_model_*.py --tb=short

  e2e-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run E2E Tests
        run: npx playwright test e2e/tests/admin/model-*.spec.ts
```

---

## 9. Gate Decision Criteria

### 9.1 Story Completion Gate

| Criteria | Threshold | Action if Failed |
|----------|-----------|------------------|
| P0 Tests Pass | 100% | FAIL - Block deployment |
| P1 Tests Pass | 100% | CONCERNS - Requires review |
| P2 Tests Pass | 90% | MONITOR - Log defects |
| P3 Tests Pass | 80% | DOCUMENT - Track in backlog |
| Code Coverage | 80% | CONCERNS if below |

### 9.2 Regression Gate

| Check | Requirement |
|-------|-------------|
| Existing admin tests | No new failures |
| API security tests | All passing |
| Performance baseline | Response time < 500ms |

---

## 10. Appendix

### A. Test File Locations

| Category | Path |
|----------|------|
| Unit Tests | `backend/tests/unit/test_model_*.py` |
| Integration Tests | `backend/tests/integration/test_model_*.py` |
| E2E Tests | `frontend/e2e/tests/admin/model-*.spec.ts` |
| Test Factories | `backend/tests/factories/model_factory.py` |
| Mocks | `backend/tests/mocks/litellm_mock.py` |

### B. Referenced Architecture

- LLM Model Registry: [architecture.md#L425-L494](docs/architecture.md#L425-L494)
- LiteLLM Integration: [backend/app/integrations/litellm_client.py](backend/app/integrations/litellm_client.py)
- Admin Routes: [backend/app/api/v1/admin.py](backend/app/api/v1/admin.py)

### C. Traceability Matrix

| AC | Unit | Integration | E2E | Risk ID |
|----|------|-------------|-----|---------|
| AC-7.9.1 | - | `test_list_models_*` | `model-registry.spec.ts` | - |
| AC-7.9.2 | `test_model_schema_*` | `test_create_model_*` | `add-model.spec.ts` | R8 |
| AC-7.9.3 | `test_type_params_*` | - | `model-form.spec.ts` | R9 |
| AC-7.9.4 | `test_provider_params_*` | - | `provider-fields.spec.ts` | R9 |
| AC-7.9.5 | `test_embedding_params` | `test_create_embedding_model` | - | - |
| AC-7.9.6 | `test_generation_params` | `test_create_generation_model` | - | - |
| AC-7.9.7 | `test_api_key_*` | `test_api_key_security` | - | R1, R2 |
| AC-7.9.8 | `test_connection_tester_*` | `test_connection_test_*` | `connection-test.spec.ts` | R5, R6 |
| AC-7.9.9 | - | `test_model_status_toggle` | `status-toggle.spec.ts` | R12 |
| AC-7.9.10 | `test_default_constraint` | `test_set_default_model` | - | R7 |
| AC-7.9.11 | - | `test_model_deletion_*` | `delete-warning.spec.ts` | R4 |
| AC-7.9.12 | `test_audit_events` | `test_model_audit_*` | - | R10 |

---

*Generated by TEA (Murat) - Master Test Architect*
*Risk-based prioritization using Probability x Impact matrix*
