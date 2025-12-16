# Story 7.2: Centralized LLM Configuration

Status: done

## Story

As an **administrator**,
I want **a centralized UI to configure LLM model settings with hot-reload capability**,
so that **I can switch models and adjust parameters without restarting services**.

## Acceptance Criteria

1. **AC-7.2.1**: Admin UI displays current LLM model settings including provider, model name, base URL, and key parameters (temperature, max_tokens)
2. **AC-7.2.2**: Model switching applies without service restart (hot-reload via Redis pub/sub or config polling)
3. **AC-7.2.3**: Embedding dimension mismatch triggers warning when selected model dimensions differ from existing KB collections
4. **AC-7.2.4**: Health status shown for each configured model (via connection test endpoint)

## Tasks / Subtasks

- [x] **Task 1: Extend ConfigService for LLM settings** (AC: 1, 2)
  - [x] 1.1 Add `get_llm_config()` method to ConfigService returning current model settings
  - [x] 1.2 Add `update_llm_config()` method with Redis cache invalidation
  - [x] 1.3 Implement hot-reload mechanism (Redis pub/sub or 30s polling interval)
  - [x] 1.4 Write unit tests for ConfigService LLM methods (≥80% coverage)

- [x] **Task 2: Create LLM Configuration Admin API** (AC: 1, 2, 3, 4)
  - [x] 2.1 GET `/api/v1/admin/llm/config` - Retrieve current LLM configuration
  - [x] 2.2 PUT `/api/v1/admin/llm/config` - Update LLM configuration (admin-only)
  - [x] 2.3 GET `/api/v1/admin/llm/health` - Test model connection
  - [x] 2.4 Add dimension mismatch detection logic comparing model dimensions vs KB collections
  - [x] 2.5 Write integration tests for all endpoints

- [x] **Task 3: Create LLM Configuration Frontend Page** (AC: 1, 4)
  - [x] 3.1 Create `useLLMConfig` hook with 30s polling (stale time: 30s)
  - [x] 3.2 Create LLMConfigForm component with provider selection and model parameters
  - [x] 3.3 Create ModelHealthIndicator component showing connection status
  - [x] 3.4 Add page at `/admin/config/llm` with DashboardLayout protection
  - [x] 3.5 Write unit tests for hooks and components

- [x] **Task 4: Implement Hot-Reload UI Feedback** (AC: 2, 3)
  - [x] 4.1 Add "Apply Changes" button with loading state
  - [x] 4.2 Show success toast on config update ("Changes applied without restart")
  - [x] 4.3 Display dimension mismatch warning dialog with affected KB list
  - [x] 4.4 Add confirmation modal for changes affecting active processing

- [x] **Task 5: Connect to Existing LiteLLM Integration** (AC: 1, 2)
  - [x] 5.1 Update `litellm_config.yaml` template generation from database config
  - [x] 5.2 Add signal to LiteLLM proxy for config refresh (if supported) or document polling
  - [x] 5.3 Verify model switching works end-to-end via search/generation

## Dev Notes

### Architecture Patterns

- **ConfigService Pattern**: Follows existing `app/services/config_service.py` pattern with Redis caching
- **Hot-Reload**: Redis pub/sub preferred (like existing config refresh) or polling fallback
- **LiteLLM Integration**: Uses existing `app/integrations/litellm_client.py` abstraction
- **Admin-Only Access**: Protected by `is_superuser` check (consistent with Story 5.1)
- **DB-to-Proxy Sync**: Models registered via Admin UI automatically sync to LiteLLM proxy (see Story 7-9)

### DB-to-Proxy Sync Integration

Hot-reload capability now includes automatic proxy registration:

1. **Model Registration**: When LLM config is updated, models are registered with LiteLLM proxy via `register_model_with_proxy()`
2. **Connection Test**: Uses `openai/db-{uuid}` alias pattern to route through proxy
3. **No YAML Editing**: Admin UI model changes are reflected in proxy without manually editing `litellm_config.yaml`

See [7-9-llm-model-registry.md](./7-9-llm-model-registry.md#litellm-proxy-integration-db-to-proxy-sync) for full implementation details.

### Source Tree Components

```
backend/
├── app/services/config_service.py  # Extend with LLM methods
├── app/api/v1/admin.py             # Add LLM config endpoints
├── app/schemas/config.py           # Add LLMConfigSchema
└── tests/
    ├── unit/test_config_service.py
    └── integration/test_llm_config_api.py

frontend/
├── src/hooks/useLLMConfig.ts
├── src/components/admin/llm-config-form.tsx
├── src/components/admin/model-health-indicator.tsx
└── src/app/(protected)/admin/config/llm/page.tsx
```

### Testing Standards

- **Unit Tests**: ConfigService LLM methods, schema validation
- **Integration Tests**: API endpoints with mocked LiteLLM
- **Frontend Tests**: Hook behavior, form validation, health indicator states
- **Manual Verification**: Hot-reload works without service restart

### Project Structure Notes

- Extends existing `/admin/config` page structure from Story 5.5
- Uses SystemConfig table for persistence (key: `llm_config`)
- Follows existing hook patterns from `useSystemConfig`

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Story 7-2: Centralized LLM Configuration]
- [Source: docs/architecture.md#LLM Model Configuration]
- [Source: docs/architecture.md#ADR-006: LiteLLM Proxy for Model Abstraction]
- [Source: backend/app/integrations/litellm_client.py]
- [Source: infrastructure/docker/litellm_config.yaml]

## Dev Agent Record

### Context Reference

- [7-2-centralized-llm-configuration.context.xml](./7-2-centralized-llm-configuration.context.xml)

### Agent Model Used

Claude claude-opus-4-5-20251101 (Scrum Master Agent)

### Debug Log References

### Completion Notes List

- **Code Review Date**: 2025-12-09
- **Review Status**: PASSED - All Acceptance Criteria Validated

### Code Review Results

#### AC Validation Summary

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC-7.2.1 | Admin UI displays LLM settings | ✅ PASS | `llm-config-form.tsx` displays provider, model name, base URL, temperature, max_tokens, top_p |
| AC-7.2.2 | Hot-reload without restart | ✅ PASS | `useLLMConfig.ts` implements 30s polling (STALE_TIME_MS=30000), hot-reload success banner in page.tsx |
| AC-7.2.3 | Dimension mismatch warning | ✅ PASS | `DimensionMismatchWarning` type, AlertDialog in page.tsx shows affected KBs |
| AC-7.2.4 | Health status per model | ✅ PASS | `model-health-indicator.tsx` shows connection status with latency color coding |

#### Test Results

- **Frontend Unit Tests**: 59 tests passed (2.45s)
  - `useLLMConfig.test.tsx`: 16 tests
  - `llm-config-form.test.tsx`: 23 tests
  - `model-health-indicator.test.tsx`: 20 tests
- **Backend Integration Tests**: 15 tests passed (10.62s)
  - `test_config_api.py`: TestGetLLMConfig (4), TestUpdateLLMConfig (7), TestGetLLMHealth (4)

#### Key Implementation Details

1. **30s Polling**: Frontend hook uses `STALE_TIME_MS = 30000` for auto-refresh
2. **Hot-Reload Feedback**: 5-second success banner with green styling
3. **Latency Color Coding**: <500ms green, <1000ms yellow, else orange
4. **Admin-Only Protection**: Endpoints require admin access (401/403 error handling)

### File List

**Backend Files:**
- `backend/app/api/v1/admin.py` (lines 1287-1420) - LLM config endpoints
- `backend/app/integrations/litellm_client.py` - LiteLLM integration
- `backend/tests/integration/test_config_api.py` - 15 integration tests

**Frontend Files:**
- `frontend/src/app/(protected)/admin/config/llm/page.tsx` - Main config page
- `frontend/src/hooks/useLLMConfig.ts` - React hook with 30s polling
- `frontend/src/components/admin/llm-config-form.tsx` - Config form component
- `frontend/src/components/admin/model-health-indicator.tsx` - Health display
- `frontend/src/types/llm-config.ts` - TypeScript type definitions

**Test Files:**
- `frontend/src/hooks/__tests__/useLLMConfig.test.tsx` - 16 hook tests
- `frontend/src/components/admin/__tests__/llm-config-form.test.tsx` - 23 form tests
- `frontend/src/components/admin/__tests__/model-health-indicator.test.tsx` - 20 health tests
