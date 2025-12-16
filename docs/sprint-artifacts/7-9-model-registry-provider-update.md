# Story 7-9: LLM Model Registry - Provider Update

Status: done
Date: 2025-12-09 (Updated)

## Summary

Post-completion update to Story 7-9 adding 4 new LLM providers with SVG logos and reorganizing the model form layout.

**Update 2025-12-09**: Fixed Qwen (DashScope) provider routing and added NER model type validation support.

## Requirements

1. **Layout Change**: Provider dropdown moved below Display Name, with Model ID + Type fields below Provider
2. **New Providers**: Added DeepSeek, Qwen, Mistral, LM Studio with actual SVG logos (replacing emoji icons)

## Changes Made

### Frontend

#### 1. Type Definitions (`frontend/src/types/llm-model.ts`)
- Extended `ModelProvider` type to include 4 new providers:
  ```typescript
  export type ModelProvider = 'ollama' | 'openai' | 'azure' | 'gemini' | 'anthropic' | 'cohere' | 'deepseek' | 'qwen' | 'mistral' | 'lmstudio';
  ```
- Updated `PROVIDER_INFO` with metadata for all 10 providers

#### 2. Provider Logo Component (`frontend/src/components/admin/models/provider-logo.tsx`) - NEW
- Created SVG logo component for all 10 providers
- Includes `PROVIDER_COLORS` for provider-specific styling:
  | Provider | Color |
  |----------|-------|
  | OpenAI | Green (#10a37f) |
  | Anthropic | Orange (#d97706) |
  | Azure | Blue (#0078d4) |
  | Gemini | Google Blue (#4285f4) |
  | Mistral | Red (#f54e42) |
  | DeepSeek | Purple (#5865f2) |
  | Qwen | Orange (#ff6a00) |
  | Cohere | Teal (#39594d) |
  | Ollama | Gray (dark mode aware) |
  | LM Studio | Violet (#7c3aed) |

#### 3. Model Form Modal (`frontend/src/components/admin/models/model-form-modal.tsx`)
- Reorganized form layout:
  1. Display Name (full width)
  2. Provider (full width with logo in dropdown)
  3. Model ID + Type (side by side)
- Added `ProviderLogo` integration in Select dropdown
- Updated `MODEL_PROVIDERS` array with logical ordering

#### 4. Model Table (`frontend/src/components/admin/models/model-table.tsx`)
- Replaced emoji icons with `ProviderLogo` component
- Added provider-specific colors

### Backend

#### 1. Model Enum (`backend/app/models/llm_model.py`)
- Added 4 new providers to `ModelProvider` enum:
  ```python
  DEEPSEEK = "deepseek"
  QWEN = "qwen"
  MISTRAL = "mistral"
  LMSTUDIO = "lmstudio"
  ```

#### 2. Schema (`backend/app/schemas/llm_model.py`)
- Updated `ModelProviderLiteral` to include new providers:
  ```python
  ModelProviderLiteral = Literal["ollama", "openai", "azure", "gemini", "anthropic", "cohere", "deepseek", "qwen", "mistral", "lmstudio"]
  ```

#### 3. Connection Tester (`backend/app/services/model_connection_tester.py`)
- Added LiteLLM prefixes for new providers:
  ```python
  "deepseek": "deepseek/",
  "qwen": "dashscope/",  # Qwen uses DashScope API (not qwen/ prefix)
  "mistral": "mistral/",
  "lmstudio": "openai/",  # LM Studio uses OpenAI-compatible API
  ```

#### 4. Model Registry Service (`backend/app/services/model_registry_service.py`)
- Added `NERModelConfig` import to support NER model type validation
- Updated `validate_model_config()` function to handle NER models

## Update 2025-12-09: Bug Fixes

### Issue 1: Qwen Provider "LLM Provider NOT provided" Error

**Problem**: Creating a Qwen model and testing connection failed with:
```
litellm.BadRequestError: LLM Provider NOT provided. Pass in the LLM provider you are trying to call. You passed model=qwen/qwen-plus-2025-09-11
```

**Root Cause**: LiteLLM does not recognize the `qwen/` prefix. Qwen models use Alibaba's DashScope API, which requires the `dashscope/` prefix.

**Fix** (`model_connection_tester.py`):
1. Changed provider prefix from `"qwen": "qwen/"` to `"qwen": "dashscope/"`
2. Added `DIRECT_API_PROVIDERS` set for providers that use direct API calls:
   ```python
   DIRECT_API_PROVIDERS = {"qwen", "deepseek", "anthropic", "gemini", "cohere", "mistral"}
   ```
3. Created `_configure_api_access()` helper function to handle API endpoint and authentication configuration consistently across all test functions (embedding, generation, NER)

### Issue 2: NER Model Type Validation Error

**Problem**: Creating an NER model failed with:
```
Invalid configuration for ner: Invalid model type: ner
```

**Root Cause**: The `validate_model_config()` function in `model_registry_service.py` only handled `embedding` and `generation` model types, but not `ner`.

**Fix** (`model_registry_service.py`):
1. Added `NERModelConfig` import:
   ```python
   from app.schemas.llm_model import (
       EmbeddingModelConfig,
       GenerationModelConfig,
       LLMModelCreate,
       LLMModelUpdate,
       NERModelConfig,
   )
   ```
2. Added NER handling in `validate_model_config()`:
   ```python
   elif model_type == ModelType.NER.value:
       validated = NERModelConfig(**config)
       return validated.model_dump()
   ```

## Test Results

- Frontend tests: 39 passed (21 hook + 18 component)
- Backend unit tests: 32 passed
- Backend integration tests: 26 passed
- TypeScript compilation: No errors
- **Total: 97 tests passing**

## Files Modified

| File | Change Type |
|------|-------------|
| `frontend/src/types/llm-model.ts` | Modified |
| `frontend/src/components/admin/models/provider-logo.tsx` | **New** |
| `frontend/src/components/admin/models/model-form-modal.tsx` | Modified |
| `frontend/src/components/admin/models/model-table.tsx` | Modified |
| `backend/app/models/llm_model.py` | Modified |
| `backend/app/schemas/llm_model.py` | Modified |
| `backend/app/services/model_connection_tester.py` | Modified (2025-12-09: Qwen prefix + DIRECT_API_PROVIDERS) |
| `backend/app/services/model_registry_service.py` | Modified (2025-12-09: NER validation) |

## Provider Support Matrix

All providers route through the LiteLLM proxy using the **DB-to-Proxy Sync** architecture:

| Provider | Logo | LiteLLM Prefix | API Type | Proxy Routing |
|----------|------|----------------|----------|---------------|
| OpenAI | ✅ SVG | `openai/` | OpenAI | `openai/db-{uuid}` |
| Anthropic | ✅ SVG | `anthropic/` | Anthropic | `openai/db-{uuid}` |
| Azure | ✅ SVG | `azure/` | Azure OpenAI | `openai/db-{uuid}` |
| Gemini | ✅ SVG | `gemini/` | Google AI | `openai/db-{uuid}` |
| Mistral | ✅ SVG | `mistral/` | Mistral AI | `openai/db-{uuid}` |
| DeepSeek | ✅ SVG | `deepseek/` | DeepSeek | `openai/db-{uuid}` |
| Qwen | ✅ SVG | `dashscope/` | Alibaba DashScope | `openai/db-{uuid}` |
| Cohere | ✅ SVG | `cohere/` | Cohere | `openai/db-{uuid}` |
| Ollama | ✅ SVG | `ollama/` | Local | `openai/db-{uuid}` |
| LM Studio | ✅ SVG | `openai/` | OpenAI-compatible | `openai/db-{uuid}` |

### DB-to-Proxy Sync Architecture

When models are created via Admin UI, they are automatically registered with the LiteLLM proxy:

1. **Alias Pattern**: `db-{uuid}` uniquely identifies DB models in proxy
2. **Connection Test**: Uses `openai/db-{uuid}` format - the `openai/` prefix routes through proxy
3. **Environment URL**: `ollama_url_for_proxy` setting handles Docker networking for Ollama
4. **Startup Sync**: `sync_all_models_to_proxy()` clears existing `db-*` models (using `model_info.id`), then re-registers all DB models

**LiteLLM API Deletion Note:**

LiteLLM's `/model/delete` endpoint requires the internal `model_info.id` (a hash), **not** the `model_name` alias. The sync service handles this by:
- Looking up `model_info.id` from `/model/info` response before deletion
- Using `{"id": "<model_info_id>"}` in delete requests

See [ADR-006](../architecture/09-adrs.md#adr-006-litellm-proxy-for-model-abstraction-epic-7) for full implementation details.

## Model Type Support

| Model Type | Config Schema | Validation | Connection Test |
|------------|--------------|------------|-----------------|
| Embedding | `EmbeddingModelConfig` | ✅ | ✅ (dimensions check) |
| Generation | `GenerationModelConfig` | ✅ | ✅ (completion test) |
| NER | `NERModelConfig` | ✅ (2025-12-09) | ✅ (JSON extraction test) |

## Notes

- LM Studio uses OpenAI-compatible API, so it uses `openai/` prefix in LiteLLM
- All SVG logos are properly sized (default 20px) and use `currentColor` for theming support
- Provider dropdown now shows logo + name + description for better UX
- **Qwen uses `dashscope/` prefix** (not `qwen/`) - this is Alibaba's DashScope API
- Direct API providers use their own API keys directly instead of routing through LiteLLM proxy
- NER models are specialized generation models for entity extraction (Epic 8 GraphRAG)
