# Story 7.9: LLM Model Registry

Status: done

## Story

As an **administrator**,
I want **a centralized LLM Model Registry to register and manage embedding and generation models from multiple providers**,
so that **Knowledge Bases can be configured with specific models and the system supports diverse AI capabilities**.

## Acceptance Criteria

1. **AC-7.9.1**: Admin Model Registry page lists all registered models with type, provider, and status
2. **AC-7.9.2**: Add model form with type selection (Embedding/Generation)
3. **AC-7.9.3**: Type selection shows relevant parameter fields for embedding or generation models
4. **AC-7.9.4**: Provider selection (Ollama, OpenAI, Azure, Gemini, Anthropic, Cohere) shows dynamic fields
5. **AC-7.9.5**: Embedding model parameters include dimensions, max_tokens, normalize, distance_metric, batch_size
6. **AC-7.9.6**: Generation model parameters include context_window, max_output_tokens, temperature, top_p, top_k
7. **AC-7.9.7**: API endpoint and API key fields shown based on provider requirements
8. **AC-7.9.8**: Connection test validates model accessibility before saving
9. **AC-7.9.9**: Model status (active/inactive) displayed and toggleable
10. **AC-7.9.10**: Default model designation available per type (one default embedding, one default generation)
11. **AC-7.9.11**: Edit/delete actions with KB dependency warnings before deletion
12. **AC-7.9.12**: Audit logging for all model registry changes

## Tasks / Subtasks

- [x] **Task 1: Database Schema and Migration** (AC: 1, 2, 3, 4, 5, 6, 7, 9, 10) ✅ DONE
  - [x] 1.1 Create model_type enum (embedding, generation, ner)
  - [x] 1.2 Create model_provider enum (ollama, openai, azure, gemini, anthropic, cohere)
  - [x] 1.3 Create llm_models table with all parameter columns
  - [x] 1.4 Add encrypted api_key storage using Fernet encryption
  - [x] 1.5 Add is_default boolean for default model designation
  - [x] 1.6 Create Alembic migration with proper indexes
  - [x] 1.7 Write unit tests for model schema validation

- [x] **Task 2: Model Registry API Endpoints** (AC: 1, 2, 8, 9, 10, 11) ✅ DONE
  - [x] 2.1 Create LLMModel SQLAlchemy model in app/models/
  - [x] 2.2 Create schemas for model CRUD operations
  - [x] 2.3 Implement POST /api/v1/admin/models endpoint
  - [x] 2.4 Implement GET /api/v1/admin/models with filtering by type/provider
  - [x] 2.5 Implement GET /api/v1/admin/models/{id} endpoint
  - [x] 2.6 Implement PUT /api/v1/admin/models/{id} endpoint
  - [x] 2.7 Implement DELETE /api/v1/admin/models/{id} with KB dependency check
  - [x] 2.8 Implement PATCH /api/v1/admin/models/{id}/default endpoint
  - [x] 2.9 Write integration tests for all CRUD operations

- [x] **Task 3: Model Connection Testing** (AC: 8) ✅ DONE
  - [x] 3.1 Implement POST /api/v1/admin/models/{id}/test endpoint
  - [x] 3.2 Create provider-specific connection testers (Ollama, OpenAI, etc.)
  - [x] 3.3 Validate embedding models with test embedding call
  - [x] 3.4 Validate generation models with test completion call
  - [x] 3.5 Return detailed error messages on connection failure
  - [x] 3.6 Write integration tests for connection testing

- [x] **Task 4: Model Registry Admin UI** (AC: 1, 2, 3, 4, 5, 6, 7, 9, 10, 11) ✅ DONE
  - [x] 4.1 Create /admin/models page with model list table
  - [x] 4.2 Implement model type tabs (All, Embedding, Generation)
  - [x] 4.3 Create AddModelModal with type selector
  - [x] 4.4 Implement provider-specific form fields with conditional rendering
  - [x] 4.5 Add embedding parameter fields (dimensions, max_tokens, etc.)
  - [x] 4.6 Add generation parameter fields (context_window, temperature, etc.)
  - [x] 4.7 Implement "Test Connection" button with loading state
  - [x] 4.8 Create EditModelModal with pre-populated fields
  - [x] 4.9 Implement delete confirmation with KB dependency warning
  - [x] 4.10 Add status toggle and default model designation
  - [x] 4.11 Write component tests for model registry UI

- [x] **Task 5: Public Model List Endpoints** (AC: 1) ✅ DONE
  - [x] 5.1 Implement GET /api/v1/models/embedding (active models only)
  - [x] 5.2 Implement GET /api/v1/models/generation (active models only)
  - [x] 5.3 Filter out sensitive fields (api_key) for non-admin users
  - [x] 5.4 Write tests for public model list endpoints

- [x] **Task 6: Audit Logging Integration** (AC: 12) ✅ DONE
  - [x] 6.1 Log model creation events with full configuration
  - [x] 6.2 Log model update events with changed fields
  - [x] 6.3 Log model deletion events with KB impact
  - [x] 6.4 Log connection test attempts and results
  - [x] 6.5 Write tests for audit logging

- [x] **Task 7: Tests** ✅ DONE
  - [x] 7.1 Backend unit tests (32 passed)
  - [x] 7.2 Backend integration tests (26 passed)
  - [x] 7.3 Frontend hook tests (21 passed)
  - [x] 7.4 Frontend component tests (18 passed)

## Dev Notes

### Architecture Patterns

- **Provider Abstraction**: LiteLLM handles multi-provider complexity
- **DB-to-Proxy Sync**: Models auto-registered with LiteLLM proxy on CRUD operations
- **Encrypted Storage**: API keys encrypted at rest using Fernet encryption
- **Admin-Only Access**: Model registry endpoints require admin role
- **Public Model Lists**: Regular users see active models without sensitive data

### LiteLLM Proxy Integration (DB-to-Proxy Sync)

Models created via the Admin UI are automatically registered with the LiteLLM proxy:

1. **On Create/Update**: `litellm_proxy_service.register_model_with_proxy()` calls `/model/new`
2. **On Delete**: `litellm_proxy_service.unregister_model_from_proxy()` looks up `model_info.id`, then calls `/model/delete`
3. **On Startup**: `sync_all_models_to_proxy()` clears existing `db-*` models (using `model_info.id`), then re-registers all DB models

**Proxy Alias Pattern**: `db-{uuid}` uniquely identifies DB models in the proxy

**Connection Testing**: Uses `openai/db-{uuid}` format through LiteLLM proxy for all providers

**LiteLLM API Deletion Requirement**:

LiteLLM's `/model/delete` endpoint requires the internal `model_info.id` (a hash), **not** the `model_name` alias. The sync service handles this by:
- Looking up `model_info.id` from `/model/info` response before deletion
- Using `{"id": "<model_info_id>"}` in delete requests

```python
# Connection test flow
model_path = f"openai/db-{model.id}"  # Universal routing
response = await aembedding(
    model=model_path,
    api_base=settings.litellm_url,  # LiteLLM proxy
    api_key=settings.litellm_api_key,
)
```

### Source Tree Components

```
backend/
├── alembic/versions/
│   └── xxxx_create_llm_models_table.py  # New migration
├── app/models/
│   └── llm_model.py                      # New model
├── app/schemas/
│   └── llm_model.py                      # New schemas
├── app/services/
│   └── model_registry_service.py         # New service
├── app/api/v1/
│   ├── admin.py                          # Add model endpoints
│   └── models.py                         # New public endpoints
└── tests/
    ├── unit/
    │   └── test_model_registry_service.py
    └── integration/
        └── test_model_registry_api.py

frontend/
├── src/app/(protected)/admin/models/
│   └── page.tsx                          # New page
├── src/components/admin/
│   ├── model-list-table.tsx              # New component
│   ├── add-model-modal.tsx               # New component
│   ├── edit-model-modal.tsx              # New component
│   └── model-connection-test.tsx         # New component
└── src/hooks/
    └── useModelRegistry.ts               # New hook
```

### Supported Providers

| Provider | Embedding | Generation | Notes |
|----------|-----------|------------|-------|
| Ollama | ✅ | ✅ | Self-hosted, requires endpoint |
| OpenAI | ✅ | ✅ | API key required |
| Azure OpenAI | ✅ | ✅ | API key + endpoint required |
| Gemini | ✅ | ✅ | API key required |
| Anthropic | ❌ | ✅ | Generation only |
| Cohere | ✅ | ✅ | API key required |

### Testing Standards

- **Unit Tests**: Model validation, provider detection, encryption
- **Integration Tests**: CRUD operations, connection testing, audit logging
- **E2E Tests**: Full model registration and KB selection flow

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Story 7-9: LLM Model Registry]
- [Source: backend/app/integrations/litellm_client.py]
- [Depends On: Story 7-2 (Centralized LLM Configuration)]

## Dev Agent Record

### Context Reference

- [7-9-llm-model-registry.context.xml](./7-9-llm-model-registry.context.xml)

### Agent Model Used

Claude claude-opus-4-5-20251101 (Scrum Master Agent)

### Debug Log References

### Completion Notes List

**Completed: 2025-12-08**

All 12 ACs satisfied:
- AC-7.9.1: ✅ Admin page lists all models with type, provider, status
- AC-7.9.2: ✅ Add model form with type selection (Embedding/Generation)
- AC-7.9.3: ✅ Type selection shows relevant parameter fields
- AC-7.9.4: ✅ Provider selection (6 providers) with dynamic fields
- AC-7.9.5: ✅ Embedding parameters (dimensions, max_tokens, normalize, distance_metric, batch_size)
- AC-7.9.6: ✅ Generation parameters (context_window, max_output_tokens, temperature, top_p, top_k)
- AC-7.9.7: ✅ API endpoint and API key fields based on provider
- AC-7.9.8: ✅ Connection test validates model accessibility
- AC-7.9.9: ✅ Model status (active/inactive/deprecated) displayed
- AC-7.9.10: ✅ Default model designation per type with star indicator
- AC-7.9.11: ✅ Edit/delete actions with KB dependency check
- AC-7.9.12: ✅ Audit logging for all model registry changes

**Test Results:**
- Backend unit tests: 32 passed
- Backend integration tests: 26 passed
- Frontend hook tests: 21 passed
- Frontend component tests: 18 passed
- **Total: 97 tests passing**

### File List

**Backend:**
- `backend/alembic/versions/664fb5501195_add_llm_models_table.py` - Migration
- `backend/app/models/llm_model.py` - SQLAlchemy model
- `backend/app/schemas/llm_model.py` - Pydantic schemas
- `backend/app/services/model_registry_service.py` - CRUD service
- `backend/app/services/model_connection_tester.py` - Connection testing
- `backend/app/services/litellm_proxy_service.py` - DB-to-Proxy sync service
- `backend/app/api/v1/models.py` - API endpoints
- `backend/tests/unit/test_model_registry_service.py` - Unit tests
- `backend/tests/integration/test_models_api.py` - Integration tests

**Frontend:**
- `frontend/src/types/llm-model.ts` - TypeScript types
- `frontend/src/hooks/useModelRegistry.ts` - React Query hooks
- `frontend/src/components/admin/models/model-table.tsx` - Table component
- `frontend/src/components/admin/models/model-form-modal.tsx` - Form modal
- `frontend/src/app/(protected)/admin/models/page.tsx` - Admin page
- `frontend/src/hooks/__tests__/useModelRegistry.test.tsx` - Hook tests
- `frontend/src/components/admin/models/__tests__/model-table.test.tsx` - Component tests
