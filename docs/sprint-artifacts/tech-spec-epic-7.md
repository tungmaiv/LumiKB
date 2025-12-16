# Epic Technical Specification: Infrastructure & DevOps

Date: 2025-12-08
Author: Tung Vu
Epic ID: 7
Status: Draft

---

## Overview

Epic 7 establishes production-grade DevOps infrastructure, centralized LLM model management, CI/CD pipelines, monitoring, and operational tooling for the LumiKB platform. This epic transforms the development environment into a production-ready deployment with comprehensive testing automation, multi-provider LLM support, and observability capabilities.

The epic addresses critical infrastructure gaps by providing Docker-based E2E testing, GitHub Actions CI/CD, Prometheus/Grafana monitoring, and a sophisticated LLM Model Registry that enables per-KB model configuration with automatic Qdrant collection management.

## Objectives and Scope

### In Scope

- Docker-based E2E testing infrastructure with Playwright (Story 7-1)
- Centralized LLM configuration with hot-reload capability (Story 7-2)
- GitHub Actions CI/CD pipelines with parallel testing (Story 7-3)
- Production deployment configuration (docker-compose.prod.yml, optional K8s) (Story 7-4)
- Prometheus/Grafana monitoring and alerting stack (Story 7-5)
- Backend unit test fixes for dependency injection patterns (Story 7-6)
- Async Qdrant client migration for improved concurrency (Story 7-7)
- UI scroll isolation fix for split-pane components (Story 7-8)
- LLM Model Registry with multi-provider support (Story 7-9)
- Per-KB model configuration with automatic collection creation (Story 7-10)

### Out of Scope

- Kubernetes auto-scaling (future phase)
- Multi-region deployment
- Cost optimization tooling
- Custom model fine-tuning
- GraphRAG infrastructure (Epic 8)

## System Architecture Alignment

This epic aligns with the LumiKB architecture through:

- **LiteLLM Proxy Integration (ADR-006)**: Model Registry leverages LiteLLM for unified multi-provider API access
- **Infrastructure Layer**: Extends docker-compose with monitoring services, E2E test containers
- **Backend Services**: Introduces ModelRegistryService, ConfigService enhancements
- **Qdrant Integration**: AsyncQdrantClient with per-KB collection auto-creation based on embedding model dimensions
- **Celery Workers**: Updated to read KB-specific model configurations

Referenced Architecture Components:
- `infrastructure/docker/docker-compose.yml` - Service orchestration
- `infrastructure/docker/litellm_config.yaml` - LLM proxy configuration
- `backend/app/integrations/qdrant_client.py` - Vector database client
- `backend/app/core/config.py` - Centralized configuration

## Detailed Design

### Services and Modules

| Module | Responsibility | Key Interfaces |
|--------|---------------|----------------|
| ModelRegistryService | CRUD operations for LLM models, connection testing, default management | `register_model()`, `test_connection()`, `set_default()` |
| LiteLLMProxySyncService | DB-to-Proxy model synchronization, automatic proxy registration | `register_model_with_proxy()`, `unregister_model_from_proxy()`, `sync_all_models_to_proxy()` |
| ConfigService (enhanced) | Runtime config hot-reload, LLM settings management | `get_llm_config()`, `update_llm_config()`, `hot_reload()` |
| AsyncQdrantClient | Non-blocking vector operations | `async create_collection()`, `async search()`, `async upsert()` |
| PrometheusMetrics | FastAPI instrumentation, custom metrics | `/metrics` endpoint |
| E2ETestRunner | Playwright test orchestration | `docker-compose.e2e.yml` |

### Data Models and Contracts

#### LLM Models Table

```sql
CREATE TABLE llm_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL,  -- 'embedding' | 'generation'
    provider VARCHAR(50) NOT NULL,  -- 'ollama' | 'openai' | 'anthropic' | 'azure' | 'cohere' | 'google' | 'custom'
    name VARCHAR(255) NOT NULL,
    model_id VARCHAR(255) NOT NULL,  -- provider-specific model identifier
    config JSONB NOT NULL DEFAULT '{}',  -- provider-specific configuration
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active' | 'inactive' | 'deprecated'
    is_default BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_llm_models_default ON llm_models (type) WHERE is_default = true;
```

#### Embedding Model Config Schema

```python
class EmbeddingModelConfig(BaseModel):
    dimensions: int  # Vector dimensions (768, 1536, 3072)
    max_tokens: int  # Max input tokens
    normalize: bool = True  # Normalize vectors
    distance_metric: Literal["cosine", "dot", "euclidean"] = "cosine"
    batch_size: int = 32
    tags: list[str] = []
```

#### Generation Model Config Schema

```python
class GenerationModelConfig(BaseModel):
    context_window: int
    max_output_tokens: int
    supports_streaming: bool = True
    supports_json_mode: bool = False
    supports_vision: bool = False
    temperature_default: float = 0.7
    temperature_range: tuple[float, float] = (0.0, 2.0)
    top_p_default: float = 1.0
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    tags: list[str] = []
```

#### KB Model Configuration Extension

```sql
ALTER TABLE knowledge_bases
ADD COLUMN embedding_model_id UUID REFERENCES llm_models(id),
ADD COLUMN generation_model_id UUID REFERENCES llm_models(id),
ADD COLUMN config_overrides JSONB DEFAULT '{}';
```

### APIs and Interfaces

#### Model Registry Endpoints

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| GET | `/api/v1/admin/models` | List all models | `?type=embedding&status=active` | `LLMModelList` |
| POST | `/api/v1/admin/models` | Register model | `LLMModelCreate` | `LLMModel` |
| GET | `/api/v1/admin/models/{id}` | Get model details | - | `LLMModel` |
| PUT | `/api/v1/admin/models/{id}` | Update model | `LLMModelUpdate` | `LLMModel` |
| DELETE | `/api/v1/admin/models/{id}` | Delete model | - | `204 No Content` |
| POST | `/api/v1/admin/models/{id}/test` | Test connection | - | `ConnectionTestResult` |
| POST | `/api/v1/admin/models/{id}/set-default` | Set as default | - | `LLMModel` |

#### KB Model Selection Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/models/available` | List active models for KB selection |
| GET | `/api/v1/knowledge-bases/{id}/model-config` | Get KB model configuration |
| PUT | `/api/v1/knowledge-bases/{id}/model-config` | Update KB model configuration |

### Workflows and Sequencing

#### KB Creation with Model Selection Flow

```
1. User submits KB creation form with:
   - name, description
   - embedding_model_id (required)
   - generation_model_id (required)
   - config_overrides (optional)

2. Backend validates model selections:
   - Verify models exist and are active
   - Load embedding model config for Qdrant collection

3. Create Qdrant collection:
   qdrant.create_collection(
       name=f"kb_{kb_id}",
       vectors_config={
           "size": embedding_model.config.dimensions,
           "distance": embedding_model.config.distance_metric
       }
   )

4. Create KB record with model references

5. Return KB with model info
```

#### Document Processing with KB Models

```
1. Document upload triggers processing
2. Worker loads KB configuration:
   - embedding_model_id → get model config (including provider)
   - config_overrides → apply chunk_size, chunk_overlap

3. Chunking uses KB-specific settings
4. Embedding uses KB's embedding model with provider-based routing:
   - Local providers (Ollama, LM Studio): Direct API call with provider prefix
   - Cloud providers: Route through LiteLLM proxy
5. Vectors stored in kb_{kb_id} collection
```

#### Provider-Based Routing for Embedding

The embedding worker uses **provider-based routing** to correctly handle different model providers:

```python
# EmbeddingConfig includes provider for routing decisions
EmbeddingConfig(
    model_id="mxbai-embed-large:latest",
    dimensions=1024,
    api_endpoint="http://localhost:11434",
    provider="ollama"  # Determines routing
)

# LiteLLMEmbeddingClient routing logic
DIRECT_CALL_PROVIDERS = {"ollama", "lmstudio"}

if provider in DIRECT_CALL_PROVIDERS:
    # Direct call: model = "ollama/mxbai-embed-large:latest"
    aembedding(model=f"{provider}/{model_id}", api_base=api_endpoint)
else:
    # LiteLLM proxy: model = "text-embedding-3-small"
    aembedding(model=model_id, api_base=litellm_proxy_url, custom_llm_provider="openai")
```

#### DB-to-Proxy Sync for Model Registration

Models created via the Admin UI are automatically synchronized with the LiteLLM proxy using the `LiteLLMProxySyncService`:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DB-to-Proxy Sync Flow                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Admin UI ────> Backend ────> PostgreSQL (llm_models)                   │
│                    │                                                     │
│                    │  POST /model/new                                    │
│                    └───────────────────> LiteLLM Proxy                  │
│                                            │                             │
│                                            ▼                             │
│                                      Model Available                     │
│                                      for Connection Test                 │
│                                                                          │
│  Key Pattern:                                                            │
│    - Proxy Alias: db-{uuid}                                             │
│    - Connection Test: openai/db-{uuid} → Routes through proxy           │
│    - Environment URL: ollama_url_for_proxy for Docker networking        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Sync Lifecycle:**

1. **On Model Create/Update**: `register_model_with_proxy()` → POST `/model/new`
2. **On Model Delete**: `unregister_model_from_proxy()` → Lookup `model_info.id`, then POST `/model/delete`
3. **On Backend Startup**: `sync_all_models_to_proxy()` clears `db-*` models (using `model_info.id`), then re-registers all

**LiteLLM API Deletion Note:**

LiteLLM's `/model/delete` endpoint requires the internal `model_info.id` (a hash), **not** the `model_name` alias. The sync service looks up `model_info.id` from `/model/info` before calling `/model/delete` with `{"id": "<model_info_id>"}`.

**Docker Configuration:**

```yaml
# docker-compose.yml - LiteLLM service
litellm:
  environment:
    STORE_MODEL_IN_DB: "True"  # Enable runtime model registration
```

**Environment Settings:**

```python
# config.py
ollama_url_for_proxy: str = "http://host.docker.internal:11434"
# Used when registering Ollama models with proxy running in Docker
```

## Non-Functional Requirements

### Performance

- **Model Registry API**: < 100ms for CRUD operations
- **Model Connection Test**: < 5s timeout per test
- **Qdrant Collection Creation**: < 2s for standard dimensions
- **Async Qdrant Operations**: No event loop blocking under 100 concurrent requests
- **CI Pipeline**: Total time < 10 minutes with parallel test execution
- **E2E Test Suite**: Complete in < 5 minutes

### Security

- **API Key Storage**: LLM API keys encrypted at rest in database (pgcrypto)
- **Admin-Only Access**: Model Registry restricted to admin role
- **Environment Secrets**: Production credentials via environment variables or secrets manager
- **No Hardcoded Credentials**: Validation in CI to prevent credential commits
- **Audit Logging**: All model registry changes logged with user, timestamp, old/new values

### Reliability/Availability

- **Model Fallback**: If configured model unavailable, use system default
- **Graceful Degradation**: Model connection failures don't block KB operations
- **Health Endpoints**: `/health` and `/ready` for orchestrator probes
- **Restart Resilience**: All configuration survives service restarts

### Observability

- **Prometheus Metrics**:
  - `lumikb_api_request_latency_seconds` - Request duration histogram
  - `lumikb_api_error_total` - Error counter by endpoint
  - `lumikb_model_request_total` - LLM request counter by model
  - `lumikb_model_latency_seconds` - LLM response latency
  - `lumikb_queue_depth` - Celery queue size
  - `lumikb_db_connections_active` - Database pool usage

- **Grafana Dashboards**:
  - API Performance Dashboard
  - LLM Usage Dashboard
  - Queue & Worker Dashboard
  - Error Rate Dashboard

- **Alerting Rules**:
  - Error rate > 5% → Critical alert
  - API latency p99 > 2s → Warning alert
  - Queue depth > 100 → Warning alert

## Dependencies and Integrations

### Backend Dependencies (pyproject.toml)

| Package | Version | Purpose |
|---------|---------|---------|
| prometheus-fastapi-instrumentator | ^6.1.0 | FastAPI metrics instrumentation |
| qdrant-client[async] | ^1.7.0 | Async vector database client |
| cryptography | ^41.0.0 | API key encryption |

### Frontend Dependencies (package.json)

| Package | Version | Purpose |
|---------|---------|---------|
| @playwright/test | ^1.40.0 | E2E testing framework |

### Infrastructure Dependencies

| Component | Version | Purpose |
|-----------|---------|---------|
| Prometheus | 2.47+ | Metrics collection |
| Grafana | 10.0+ | Metrics visualization |
| AlertManager | 0.26+ | Alert routing |

### External Integrations

| Provider | Integration Method | Configuration |
|----------|-------------------|---------------|
| Ollama | LiteLLM proxy | Base URL, Model Name |
| OpenAI | LiteLLM proxy | API Key, Model Name, Org ID |
| Anthropic | LiteLLM proxy | API Key, Model Name |
| Azure OpenAI | LiteLLM proxy | API Key, Endpoint, Deployment, API Version |
| Google Gemini | LiteLLM proxy | API Key, Model Name, Project ID |
| Cohere | LiteLLM proxy | API Key, Model Name |

## Acceptance Criteria (Authoritative)

### Story 7-1: Docker E2E Infrastructure
1. AC-7.1.1: docker-compose.e2e.yml starts all services with test configuration
2. AC-7.1.2: Playwright tests execute against containerized stack
3. AC-7.1.3: Database is seeded with test data before E2E runs
4. AC-7.1.4: GitHub Actions integrates E2E tests in CI pipeline
5. AC-7.1.5: 15-20 E2E tests cover Epic 3 & 4 features

### Story 7-2: Centralized LLM Configuration
1. AC-7.2.1: Admin UI displays LLM model settings
2. AC-7.2.2: Model switching applies without service restart (hot-reload)
3. AC-7.2.3: Embedding dimension mismatch triggers warning
4. AC-7.2.4: Health status shown for each configured model

### Story 7-3: CI/CD Pipeline
1. AC-7.3.1: PR triggers lint, type-check, unit tests, build
2. AC-7.3.2: Main merge builds and pushes Docker images
3. AC-7.3.3: Coverage report posted as PR comment
4. AC-7.3.4: Frontend and backend tests run in parallel, total < 10 min

### Story 7-4: Production Deployment
1. AC-7.4.1: docker-compose.prod.yml starts with production settings
2. AC-7.4.2: Optional Kubernetes manifests deploy workloads
3. AC-7.4.3: All secrets from environment variables
4. AC-7.4.4: /health and /ready endpoints available

### Story 7-5: Monitoring & Observability
1. AC-7.5.1: /metrics endpoint exposes Prometheus metrics
2. AC-7.5.2: Grafana dashboards show latency, errors, queue depth
3. AC-7.5.3: AlertManager triggers on 5% error rate threshold
4. AC-7.5.4: Logs in structured JSON format

### Story 7-6: Backend Unit Test Fixes
1. AC-7.6.1-5: All unit tests pass for draft, search, generation, explanation services
2. AC-7.6.5: DI mock pattern documented

### Story 7-7: Async Qdrant Migration
1. AC-7.7.1: AsyncQdrantClient replaces sync client
2. AC-7.7.2-3: ChunkService and SearchService use native async calls
3. AC-7.7.4: 100 concurrent requests show consistent response times

### Story 7-8: UI Scroll Isolation
1. AC-7.8.1-2: Document and chunk panels scroll independently
2. AC-7.8.3: Scroll isolation maintained after resize

### Story 7-9: LLM Model Registry
1. AC-7.9.1: Admin Model Registry page lists all registered models
2. AC-7.9.2-3: Add model form with type selection (Embedding/Generation)
3. AC-7.9.4: Provider selection shows dynamic fields
4. AC-7.9.5-7: Complete parameter sets for embedding and generation models
5. AC-7.9.8: Connection test validates model accessibility
6. AC-7.9.9-10: Status management and default designation
7. AC-7.9.11: Edit/delete with KB dependency warnings
8. AC-7.9.12: Audit logging for all changes

### Story 7-10: KB Model Configuration
1. AC-7.10.1-2: Model selection during KB creation with active models only
2. AC-7.10.3: Model info display on selection
3. AC-7.10.4: Qdrant collection auto-created with correct dimensions/metric
4. AC-7.10.5: KB-level parameter overrides supported
5. AC-7.10.6: Embedding model lock warning after first document
6. AC-7.10.7: Generation model changeable without reprocessing
7. AC-7.10.8-10: Processing and search use KB-configured models

### Story 7-11: Navigation Restructure with RBAC Default Groups
1. AC-7.11.1-3: Navigation visibility based on permission level (Admin sees both menus, Operator sees Operations only, User sees neither)
2. AC-7.11.4-5: Operations dropdown (Dashboard, Audit, Queue, KB Stats) and Admin dropdown (Dashboard, Users, Groups, KB Perms, Config, Models)
3. AC-7.11.6: Hub dashboards with card-based navigation and live stats
4. AC-7.11.7-10: Default groups (Users=1, Operators=2, Administrators=3), protected from deletion, auto-assign new users
5. AC-7.11.11-15: Cumulative permission hierarchy (higher inherits lower), User/Operator/Admin capability restrictions
6. AC-7.11.16-18: Route protection (/operations/* requires Operator, /admin/* requires Admin)
7. AC-7.11.19-20: Safety guards (last admin protection, MAX permission aggregation for multi-group users)

## Traceability Mapping

| AC | Spec Section | Component/API | Test Idea |
|----|--------------|---------------|-----------|
| AC-7.1.1 | Workflows | docker-compose.e2e.yml | E2E: All containers start |
| AC-7.2.2 | Services | ConfigService.hot_reload() | Integration: Config change applies |
| AC-7.3.1 | Workflows | .github/workflows/ci.yml | CI: PR triggers checks |
| AC-7.5.1 | NFR Observability | /metrics endpoint | Integration: Metrics scrape works |
| AC-7.7.1 | Services | AsyncQdrantClient | Unit: Async methods used |
| AC-7.9.1 | APIs | GET /api/v1/admin/models | Integration: List returns models |
| AC-7.9.8 | APIs | POST /models/{id}/test | Integration: Connection test works |
| AC-7.10.4 | Workflows | KB creation flow | Integration: Collection created |

## Risks, Assumptions, Open Questions

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LiteLLM provider compatibility issues | Medium | Test each provider during Story 7-9, maintain compatibility matrix |
| Async Qdrant migration breaks existing code | High | Comprehensive test coverage before migration, staged rollout |
| CI pipeline time exceeds 10 min | Low | Optimize test parallelization, cache dependencies |

### Assumptions

- LiteLLM proxy remains stable and supports all listed providers
- Qdrant async client API is stable
- GitHub Actions has sufficient free minutes for CI/CD
- Prometheus/Grafana stack fits within resource constraints

### Open Questions

1. **Q**: Should model API keys be stored encrypted or use external secrets manager?
   **A**: Start with encrypted storage (pgcrypto), support external manager in future

2. **Q**: How to handle embedding dimension changes for existing KBs?
   **A**: Warning + optional batch re-embedding (separate story if needed)

3. **Q**: Should E2E tests run on every PR or only on main merge?
   **A**: Run on PR for critical paths, full suite on main merge

## Test Strategy Summary

### Test Levels

| Level | Framework | Coverage Focus |
|-------|-----------|----------------|
| Unit | pytest | ModelRegistryService, ConfigService, AsyncQdrantClient |
| Integration | pytest + testcontainers | API endpoints, LiteLLM integration, Qdrant operations |
| E2E | Playwright | KB creation with models, search with configured models |

### Key Test Scenarios

1. **Model Registry CRUD**: Create, list, update, delete models
2. **Connection Testing**: Validate each provider type
3. **KB Model Selection**: Create KB with models, verify collection creation
4. **Hot Reload**: Change config, verify no restart needed
5. **Async Performance**: Concurrent Qdrant operations
6. **CI Pipeline**: Full workflow on PR and merge

### Coverage Targets

- Unit: 80% for new services
- Integration: All API endpoints exercised
- E2E: 15-20 tests covering Epic 3 & 4 critical paths

---

## Story 7-27: Queue Monitoring Enhancement

**Added:** 2025-12-10 (Correct-Course: Queue Monitoring Enhancement)

### Technical Design

#### New Endpoint: Bulk Retry Failed Documents

```python
# POST /api/v1/admin/queue/retry-failed
class BulkRetryRequest(BaseModel):
    document_ids: list[UUID] | None = None  # Selective retry
    retry_all_failed: bool = False  # Retry all FAILED documents
    kb_id: UUID | None = None  # Scope to specific KB (optional)

class BulkRetryResponse(BaseModel):
    queued: int
    failed: int
    errors: list[dict]  # [{"document_id": "uuid", "error": "reason"}]
```

#### Extended TaskInfo Schema

```python
class TaskInfo(BaseModel):
    task_id: str
    task_name: str
    status: str
    started_at: datetime | None
    estimated_duration: int | None  # milliseconds
    # New fields for Story 7-27
    processing_steps: dict | None  # From Document.processing_steps JSONB
    current_step: str | None  # From Document.current_step
    step_errors: dict | None  # From Document.step_errors JSONB
```

#### Operator Permission Dependency

```python
# backend/app/core/auth.py
async def get_current_operator_or_admin(
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Require user with operator (level 2) or admin (level 3) permissions."""
    # Check is_superuser first (backward compat)
    if current_user.is_superuser:
        return current_user

    # Check group permission_level >= 2
    user_max_level = await get_user_max_permission_level(db, current_user.id)
    if user_max_level >= 2:
        return current_user

    raise HTTPException(status_code=403, detail="Operator access required")
```

#### Frontend Components

```typescript
// StepBreakdown - Expandable row showing processing step details
interface StepBreakdownProps {
  steps: Record<string, StepInfo>;
  currentStep: string;
  stepErrors: Record<string, string>;
}

interface StepInfo {
  status: 'pending' | 'in_progress' | 'done' | 'error' | 'skipped';
  started_at: string | null;
  completed_at: string | null;
}

// StepStatusBadge - Color-coded status with error tooltip
interface StepStatusBadgeProps {
  status: StepInfo['status'];
  errorMessage?: string;
}
```

### Files to Modify

| File | Changes |
|------|---------|
| `backend/app/schemas/admin.py` | Extend TaskInfo, add BulkRetryRequest/Response |
| `backend/app/services/queue_monitor_service.py` | Add processing_steps, bulk_retry, status filter |
| `backend/app/api/v1/admin.py` | New bulk retry endpoint, operator dependency |
| `backend/app/core/auth.py` | Add `get_current_operator_or_admin()` |
| `backend/app/services/permission_service.py` | Add `get_user_max_permission_level()` |
| `frontend/src/components/admin/task-list-modal.tsx` | Expandable rows, tabs, checkboxes |
| `frontend/src/components/layout/kb-sidebar.tsx` | Conditional Queue Status link |

### Existing Assets to Leverage

| Component | Location | Reuse |
|-----------|----------|-------|
| ProcessingStep enum | `backend/app/models/document.py:29-47` | 100% |
| processing_steps JSONB | `backend/app/models/document.py:133-147` | 100% |
| QueueMonitorService | `backend/app/services/queue_monitor_service.py` | Extend |
| TaskListModal | `frontend/src/components/admin/task-list-modal.tsx` | Extend |
| Document retry API | `backend/app/api/v1/documents.py:574` | 100% |

### Test Scenarios

1. **Bulk Retry**: Verify document_ids selective retry, retry_all_failed, kb_id scoping
2. **Permission Check**: Operator (level 2) granted, User (level 1) denied, Admin (is_superuser) granted
3. **Status Filter**: Filter tasks by PENDING, PROCESSING, READY, FAILED
4. **Step Visibility**: Expand row shows step breakdown with timing
5. **Error Tooltip**: Hover on error badge shows full error message
