# Epic 7: Infrastructure & DevOps

**Goal:** Establish DevOps infrastructure, testing automation, centralized configuration, model management, and deployment tooling to support production operations.

**User Value:** Development team has reliable CI/CD pipelines, comprehensive E2E testing, centralized model management, and production-ready deployment infrastructure. Users can leverage multiple LLM providers with per-KB configuration.

**FRs Covered:** Infrastructure-focused (no direct FR mapping - supports all FRs operationally)

**Technical Foundation:**
- Docker-based E2E testing with Playwright
- GitHub Actions CI/CD pipelines
- Kubernetes/Helm production deployment
- Prometheus/Grafana observability stack
- LLM Model Registry with multi-provider support
- Per-KB model configuration with Qdrant collection auto-creation

---

## Story 7.1: Docker E2E Infrastructure

**Description:** As a developer, I want Docker-based E2E testing infrastructure so I can run comprehensive integration tests against the full stack.

**Story Points:** 5

**Migrated From:** Story 5-16 (scope reduced - E2E automation moved to Story 8.16)

**Acceptance Criteria:**
(See specification at docs/sprint-artifacts/7-1-docker-e2e-infrastructure.md)

**Prerequisites:** None

**Technical Notes:**
- docker-compose.e2e.yml with all 8 services
- Service health checks and dependencies
- Database seeding for E2E tests (idempotent)
- Infrastructure verification

**Deferred to Story 8.16:**
- Playwright Docker configuration
- GitHub Actions E2E workflow
- E2E test execution

---

## Story 7.2: Centralized LLM Configuration

**Description:** As an admin, I want centralized LLM configuration management so I can switch between model providers without code changes.

**Story Points:** 5

**Acceptance Criteria:**

**AC-7.2.1: Admin UI for model configuration**
**Given** I am logged in as admin
**When** I navigate to Admin > System Config
**Then** I see LLM model settings with current values

**AC-7.2.2: Model switching without restart**
**Given** I update the LLM model configuration
**When** I save changes
**Then** new requests use the updated model
**And** no service restart is required (hot-reload)

**AC-7.2.3: Embedding model dimension validation**
**Given** I switch to a different embedding model
**When** the dimensions differ from existing vectors
**Then** I see a warning: "Dimension mismatch - existing vectors may need re-embedding"

**AC-7.2.4: Model health check**
**Given** I am on the LLM config page
**Then** I see health status for each configured model
**And** last successful request timestamp

**Prerequisites:** Story 5.5 (System Configuration)

**Technical Notes:**
- LiteLLM proxy handles model routing
- Config stored in system_config table
- Existing implementation: backend/app/core/config.py, infrastructure/docker/litellm_config.yaml

---

## Story 7.3: CI/CD Pipeline Setup

**Description:** As a developer, I want automated CI/CD pipelines so code changes are automatically tested and deployable.

**Story Points:** 5

**Acceptance Criteria:**

**AC-7.3.1: Pull request checks**
**Given** I create a pull request
**Then** GitHub Actions runs: lint, type-check, unit tests, build

**AC-7.3.2: Main branch deployment**
**Given** a PR is merged to main
**Then** Docker images are built and pushed to registry
**And** staging environment is updated

**AC-7.3.3: Test coverage reporting**
**Given** CI runs on a PR
**Then** coverage report is posted as PR comment
**And** coverage badge is updated

**AC-7.3.4: Parallel test execution**
**Given** CI runs tests
**Then** frontend and backend tests run in parallel
**And** total CI time is under 10 minutes

**Prerequisites:** Story 7.1 (Docker E2E Infrastructure)

**Technical Notes:**
- GitHub Actions workflow files in .github/workflows/
- Docker Hub or GitHub Container Registry
- Coverage via pytest-cov and vitest coverage

---

## Story 7.4: Production Deployment Configuration

**Description:** As a DevOps engineer, I want production deployment configuration so the application can be deployed to production infrastructure.

**Story Points:** 5

**Acceptance Criteria:**

**AC-7.4.1: Production docker-compose**
**Given** I have a production server
**When** I run docker compose -f docker-compose.prod.yml up
**Then** all services start with production settings

**AC-7.4.2: Kubernetes manifests (optional)**
**Given** I have a K8s cluster
**When** I apply the manifests
**Then** all workloads are deployed with proper resources

**AC-7.4.3: Environment configuration**
**Given** production deployment
**Then** all secrets are loaded from environment/secrets manager
**And** no hardcoded credentials exist

**AC-7.4.4: Health check endpoints**
**Given** production deployment
**Then** /health and /ready endpoints are available
**And** orchestrator can verify service health

**Prerequisites:** None

**Technical Notes:**
- docker-compose.prod.yml with production overrides
- Optional: Kubernetes manifests or Helm charts
- Secret management via environment variables

---

## Story 7.5: Monitoring & Observability

**Description:** As a DevOps engineer, I want monitoring and observability so I can track system health and diagnose issues.

**Story Points:** 5

**Acceptance Criteria:**

**AC-7.5.1: Prometheus metrics endpoint**
**Given** the backend is running
**Then** /metrics endpoint exposes Prometheus metrics
**And** includes request latency, error rates, active connections

**AC-7.5.2: Grafana dashboards**
**Given** Prometheus is scraping metrics
**Then** Grafana dashboards show: API latency, error rates, queue depth, DB connections

**AC-7.5.3: Alerting rules**
**Given** error rate exceeds threshold (5%)
**Then** alert is triggered
**And** notification sent (email/Slack)

**AC-7.5.4: Log aggregation**
**Given** services are running
**Then** logs are aggregated in structured JSON format
**And** queryable via log viewer

**Prerequisites:** Story 7.4 (Production Deployment)

**Technical Notes:**
- prometheus-fastapi-instrumentator for metrics
- Grafana with pre-built dashboards
- AlertManager for notifications

---

## Story 7.6: Backend Unit Test Fixes

**Description:** As a developer, I want all backend unit tests passing so I have confidence in test coverage.

**Story Points:** 3

**Tech Debt Reference:** TD-5.15-1

**Acceptance Criteria:**

**AC-7.6.1: Draft service tests passing**
**Given** I run pytest tests/unit/test_draft_service.py
**Then** all 12 tests pass

**AC-7.6.2: Search service tests passing**
**Given** I run pytest tests/unit/test_search_service.py
**Then** all 8 tests pass

**AC-7.6.3: Generation service tests passing**
**Given** I run pytest tests/unit/test_generation_service.py
**Then** all 5 tests pass

**AC-7.6.4: Explanation service tests passing**
**Given** I run pytest tests/unit/test_explanation_service.py
**Then** all tests pass

**AC-7.6.5: DI pattern documented**
**Given** tests are fixed
**Then** a comment or doc explains the DI mock pattern for future tests

**Prerequisites:** None

**Technical Notes:**
- Root cause: Service constructor DI changes not reflected in test mocks
- Update test fixtures to match current DI patterns

---

## Story 7.7: Async Qdrant Client Migration

**Description:** As a developer, I want async Qdrant client so vector operations don't block the event loop.

**Story Points:** 5

**Tech Debt Reference:** TD-5.26-1

**Acceptance Criteria:**

**AC-7.7.1: AsyncQdrantClient used**
**Given** I inspect backend/app/integrations/qdrant_client.py
**Then** it uses AsyncQdrantClient instead of sync QdrantClient

**AC-7.7.2: ChunkService fully async**
**Given** I inspect chunk_service.py
**Then** all Qdrant calls are native async (no asyncio.to_thread)

**AC-7.7.3: SearchService fully async**
**Given** I inspect search_service.py
**Then** all Qdrant calls are native async

**AC-7.7.4: Load test validates concurrency**
**Given** I run concurrent requests (100 simultaneous)
**Then** response times remain consistent
**And** no event loop blocking observed

**Prerequisites:** None

**Technical Notes:**
- Replace QdrantClient with AsyncQdrantClient
- Update all service methods to use async calls
- Remove asyncio.to_thread workarounds

---

## Story 7.8: UI Scroll Isolation Fix

**Description:** As a user, I want split-pane scroll isolation so scrolling one panel doesn't affect the other.

**Story Points:** 3

**Tech Debt Reference:** TD-scroll-1

**Acceptance Criteria:**

**AC-7.8.1: Document viewer scroll isolated**
**Given** I am viewing the Document Chunk Viewer
**When** I scroll in the document panel
**Then** the chunk list panel does not scroll

**AC-7.8.2: Chunk list scroll isolated**
**Given** I am viewing the Document Chunk Viewer
**When** I scroll in the chunk list panel
**Then** the document panel does not scroll

**AC-7.8.3: Resize maintains isolation**
**Given** I resize the split panes
**Then** scroll isolation is maintained

**Prerequisites:** Story 5.26 (Document Chunk Viewer Frontend)

**Technical Notes:**
- Multiple solutions attempted without success
- May require CSS overflow:hidden + custom scroll containers
- Test with various document sizes

---

## Story 7.9: LLM Model Registry

**Description:** As an admin, I want to register and manage LLM models so users can select appropriate models for their Knowledge Bases.

**Story Points:** 8

**Acceptance Criteria:**

**AC-7.9.1: Model registration page**
**Given** I am logged in as admin
**When** I navigate to Admin > Model Registry
**Then** I see a list of registered models with their configurations

**AC-7.9.2: Register new model**
**Given** I am on Model Registry
**When** I click "Add Model"
**Then** I see a form with fields based on model type

**AC-7.9.3: Model type selection**
**Given** I am registering a new model
**When** I select model type
**Then** I can choose: "Embedding" or "Generation"

**AC-7.9.4: Provider selection with dynamic fields**
**Given** I am registering a model
**When** I select provider
**Then** appropriate fields are shown:

| Provider | Required Fields |
|----------|-----------------|
| Ollama (Local) | Base URL, Model Name |
| OpenAI | API Key, Model Name, Organization ID (optional) |
| Google Gemini | API Key, Model Name, Project ID (optional) |
| Azure OpenAI | API Key, Endpoint URL, Deployment Name, API Version |
| Anthropic | API Key, Model Name |
| Cohere | API Key, Model Name |
| Custom/OpenAI-compatible | Base URL, API Key (optional), Model Name |

**AC-7.9.5: Embedding model parameters**
**Given** I am registering an Embedding model
**Then** I must provide:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | string | Display name | "Nomic Embed Text" |
| `provider` | enum | Provider type | ollama, openai, cohere |
| `model_id` | string | Model identifier | "nomic-embed-text" |
| `dimensions` | int | Vector dimensions | 768, 1536, 3072 |
| `max_tokens` | int | Max input tokens | 8192 |
| `normalize` | bool | Normalize vectors | true |
| `distance_metric` | enum | Similarity metric | cosine, dot, euclidean |
| `batch_size` | int | Batch size for bulk embedding | 32 |
| `tags` | string[] | Searchable tags | ["local", "fast", "multilingual"] |

**AC-7.9.6: Generation model parameters**
**Given** I am registering a Generation model
**Then** I must provide:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | string | Display name | "GPT-4o" |
| `provider` | enum | Provider type | openai, anthropic, ollama |
| `model_id` | string | Model identifier | "gpt-4o" |
| `context_window` | int | Max context tokens | 128000 |
| `max_output_tokens` | int | Max response tokens | 16384 |
| `supports_streaming` | bool | SSE streaming support | true |
| `supports_json_mode` | bool | Structured output | true |
| `supports_vision` | bool | Image input support | true |
| `temperature_default` | float | Default temperature | 0.7 |
| `temperature_range` | [float, float] | Valid range | [0.0, 2.0] |
| `top_p_default` | float | Default nucleus sampling | 1.0 |
| `top_k_default` | int | Default top-k (if supported) | 40 |
| `frequency_penalty_default` | float | Repetition penalty | 0.0 |
| `presence_penalty_default` | float | Topic novelty penalty | 0.0 |
| `cost_per_1k_input` | float | Cost tracking (USD) | 0.0025 |
| `cost_per_1k_output` | float | Cost tracking (USD) | 0.01 |
| `tags` | string[] | Searchable tags | ["cloud", "fast", "reasoning"] |

**AC-7.9.7: RAG/Search parameters (shared)**
**Given** I am configuring search defaults for a model
**Then** I can set:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `similarity_threshold` | float | Min similarity score | 0.7 |
| `top_k` | int | Number of chunks to retrieve | 10 |
| `rerank_enabled` | bool | Enable reranking | true |
| `rerank_model` | string | Rerank model (if enabled) | "cohere-rerank-v3" |
| `hybrid_search` | bool | Combine vector + keyword | false |
| `mmr_enabled` | bool | Maximal Marginal Relevance | true |
| `mmr_lambda` | float | MMR diversity factor | 0.5 |

**AC-7.9.8: Connection test**
**Given** I have filled in model configuration
**When** I click "Test Connection"
**Then** system validates connectivity and returns:
- For embedding: sample text embedded, dimensions verified
- For generation: simple prompt completed, streaming verified

**AC-7.9.9: Model status management**
**Given** a model is registered
**Then** I can set status: Active, Inactive, Deprecated
**And** only Active models appear in KB configuration

**AC-7.9.10: Default model designation**
**Given** I have multiple models of same type
**When** I mark one as "System Default"
**Then** new KBs use this model unless overridden

**AC-7.9.11: Model edit and delete**
**Given** a model is registered
**When** I edit or delete it
**Then** I see warning if any KBs are using this model
**And** deletion is blocked if KBs depend on it

**AC-7.9.12: Audit logging**
**Given** any model registry change occurs
**Then** audit log captures: action, user, timestamp, old/new values

**Prerequisites:** Story 5.5 (System Configuration)

**Technical Notes:**
- New table: `llm_models` (id, type, provider, name, config JSONB, status, is_default, created_at, updated_at)
- LiteLLM proxy integration for unified API
- Secure storage for API keys (encrypted at rest)
- Migration to add model registry schema

---

## Story 7.10: KB Model Configuration

**Description:** As a KB creator, I want to select embedding and generation models for my Knowledge Base so documents are processed with appropriate models.

**Story Points:** 5

**Acceptance Criteria:**

**AC-7.10.1: Model selection during KB creation**
**Given** I am creating a new Knowledge Base
**When** I fill in the creation form
**Then** I see model selection section with:
- Embedding Model dropdown (required)
- Generation Model dropdown (required)

**AC-7.10.2: Only active models shown**
**Given** I am selecting models for a KB
**Then** only models with status "Active" appear in dropdowns
**And** system default is pre-selected

**AC-7.10.3: Model info display**
**Given** I select a model
**Then** I see key parameters:
- For embedding: dimensions, provider, tags
- For generation: context window, provider, streaming support

**AC-7.10.4: Qdrant collection auto-creation**
**Given** I create a KB with embedding model
**When** KB is created
**Then** Qdrant collection is created with:
- Collection name: `kb_{kb_id}`
- Vector size: from embedding model dimensions
- Distance metric: from embedding model config (cosine/dot/euclidean)
- Optimizers config based on expected document count

**AC-7.10.5: KB-level parameter overrides**
**Given** I am configuring a KB
**Then** I can override default search parameters:

| Parameter | Description | Inherits From |
|-----------|-------------|---------------|
| `similarity_threshold` | Min relevance score | Model default |
| `top_k` | Chunks to retrieve | Model default |
| `chunk_size` | Document chunk size | System default (512) |
| `chunk_overlap` | Overlap between chunks | System default (50) |
| `temperature` | Generation temperature | Model default |
| `max_response_tokens` | Max generation length | Model default |

**AC-7.10.6: Model lock after first document**
**Given** a KB has documents uploaded
**When** I try to change the embedding model
**Then** I see warning: "Changing embedding model requires re-processing all documents"
**And** I must confirm to proceed

**AC-7.10.7: Generation model changeable**
**Given** a KB exists with documents
**When** I change the generation model
**Then** change applies immediately (no reprocessing needed)

**AC-7.10.8: KB settings page shows model info**
**Given** I view KB settings
**Then** I see current model assignments
**And** link to model details in admin registry

**AC-7.10.9: Document processing uses KB models**
**Given** a document is uploaded to a KB
**When** processing starts
**Then** embedding uses KB's configured embedding model
**And** vectors are stored with correct dimensions

**AC-7.10.10: Search/chat uses KB models**
**Given** I search or chat in a KB
**Then** retrieval uses KB's embedding model
**And** generation uses KB's generation model
**And** parameters respect KB-level overrides

**Prerequisites:**
- Story 7.9 (LLM Model Registry)
- Story 2.1 (Knowledge Base CRUD)

**Technical Notes:**
- Add to `knowledge_bases` table: `embedding_model_id`, `generation_model_id`, `config_overrides JSONB`
- Qdrant collection creation: `qdrant_client.create_collection(name, vectors_config)`
- Update document processing worker to read KB model config
- Update search/chat services to use KB-specific models

---

## Story 7.11: Navigation Restructure with RBAC Default Groups

**Description:** As an administrator, I want a restructured navigation with separate Operations and Admin menus, and three default user groups (Users, Operators, Administrators) with cumulative permissions, so that users see appropriate UI elements based on their role, and permission management is simplified through a clear hierarchical group system.

**Story Points:** 8

**Acceptance Criteria:**

**Navigation Restructure:**

**AC-7.11.1: Admin sees dual menus**
**Given** an Administrator views the application header
**Then** they see two dropdown menus: "Operations" and "Admin"

**AC-7.11.2: Operator sees Operations only**
**Given** an Operator user views the header
**Then** they see only the "Operations" dropdown (no "Admin" menu)

**AC-7.11.3: Basic User sees neither menu**
**Given** a basic User views the header
**Then** they see neither Operations nor Admin menus (only Search)

**AC-7.11.4: Operations menu items**
**Given** the Operations dropdown is opened
**Then** it displays: Operations Dashboard (hub), Audit Logs, Processing Queue, KB Statistics

**AC-7.11.5: Admin menu items**
**Given** the Admin dropdown is opened
**Then** it displays: Admin Dashboard (hub), Users, Groups, KB Permissions, System Config, Model Registry

**AC-7.11.6: Hub dashboards**
**Given** clicking "Operations Dashboard" or "Admin Dashboard"
**When** the page loads
**Then** it shows a card-based hub with links to all sub-sections

**Default Groups:**

**AC-7.11.7: System groups seeded**
**Given** a fresh installation
**When** the database is seeded
**Then** three system groups exist: "Users" (level 1), "Operators" (level 2), "Administrators" (level 3)

**AC-7.11.8: System groups protected**
**Given** system default groups
**When** an admin attempts to delete them
**Then** the operation is blocked with error "Cannot delete system groups"

**AC-7.11.9: System group membership editable**
**Given** system default groups
**When** an admin edits membership
**Then** members can be added/removed normally

**AC-7.11.10: Auto-assign new users**
**Given** a new user registration
**When** the account is created
**Then** the user is automatically added to the "Users" group

**Permission Hierarchy (Cumulative):**

**AC-7.11.11: Cumulative permissions**
**Given** permission levels (User=1, Operator=2, Admin=3)
**When** checking permissions
**Then** higher levels inherit all lower-level permissions

**AC-7.11.12: User upload restriction**
**Given** a User (level 1)
**When** they try to upload documents
**Then** the upload button is hidden and API returns 403

**AC-7.11.13: Operator capabilities**
**Given** an Operator (level 2)
**When** they access the application
**Then** they can upload/delete documents, create KBs, and view Operations menu

**AC-7.11.14: Operator KB deletion restriction**
**Given** an Operator (level 2)
**When** they try to delete a Knowledge Base
**Then** the operation is blocked (Admin only)

**AC-7.11.15: Administrator full access**
**Given** an Administrator (level 3)
**When** they access the application
**Then** they have full access including KB deletion and Admin menu

**Route Protection:**

**AC-7.11.16: User route block**
**Given** a User accessing `/operations/*` routes
**When** the page loads
**Then** they are redirected with 403 Forbidden

**AC-7.11.17: Operator admin route block**
**Given** an Operator accessing `/admin/*` routes
**When** the page loads
**Then** they are redirected with 403 Forbidden

**AC-7.11.18: Admin unrestricted access**
**Given** an Administrator
**When** accessing any route
**Then** access is granted

**Safety Guards:**

**AC-7.11.19: Last admin protection**
**Given** the last Administrator in the system
**When** attempting to remove themselves from Administrators group
**Then** the operation is blocked with error "Cannot remove the last administrator"

**AC-7.11.20: Max permission level**
**Given** a user in multiple groups
**When** checking their permission level
**Then** the MAX permission_level across all groups is used

**Prerequisites:**
- Story 5.17 (Main Navigation) - navigation structure to extend
- Story 5.19 (Group Management) - group CRUD to extend
- Story 7.9 (LLM Model Registry) - admin route pattern reference

**Technical Notes:**
- Add `permission_level` (integer 1-3) and `is_system` (boolean) columns to groups table
- Create `PermissionService` with `get_user_permission_level(user)` method
- Create `@require_permission(level)` decorator for endpoints
- Cumulative permission check: `user_max_level >= required_level`
- Frontend: `OperationsDropdown`, `AdminDropdown` components, `usePermissionLevel()` hook
- Route guards: `OperatorGuard`, `AdminGuard` HOCs
- Auto-add new users to "Users" group in registration flow

---

## Story 7.12: KB Settings Schema & Pydantic Models

**Description:** As a developer, I want typed Pydantic schemas for KB-level configuration so settings are validated and type-safe.

**Story Points:** 5

**Added:** 2025-12-09 (Correct-Course: KB-Level Configuration)

**Acceptance Criteria:**

**AC-7.12.1: ChunkingConfig schema**
**Given** I import ChunkingConfig from app.schemas.kb_settings
**Then** it includes: strategy (fixed/recursive/semantic), chunk_size (100-2000), chunk_overlap (0-500), separators (list[str])

**AC-7.12.2: RetrievalConfig schema**
**Given** I import RetrievalConfig from app.schemas.kb_settings
**Then** it includes: top_k (1-100), similarity_threshold (0.0-1.0), method (vector/hybrid/hyde), mmr_enabled, mmr_lambda, hybrid_alpha

**AC-7.12.3: RerankingConfig schema**
**Given** I import RerankingConfig from app.schemas.kb_settings
**Then** it includes: enabled (bool), model (str), top_n (1-50)

**AC-7.12.4: GenerationConfig schema**
**Given** I import GenerationConfig from app.schemas.kb_settings
**Then** it includes: temperature (0.0-2.0), top_p (0.0-1.0), top_k (1-100), max_tokens (100-16000), frequency_penalty (-2.0-2.0), presence_penalty (-2.0-2.0), stop_sequences (list[str])

**AC-7.12.5: NERConfig schema**
**Given** I import NERConfig from app.schemas.kb_settings
**Then** it includes: enabled (bool), confidence_threshold (0.0-1.0), entity_types (list[str]), batch_size (1-100)

**AC-7.12.6: DocumentProcessingConfig schema**
**Given** I import DocumentProcessingConfig from app.schemas.kb_settings
**Then** it includes: ocr_enabled (bool), language_detection (bool), table_extraction (bool), image_extraction (bool)

**AC-7.12.7: KBPromptConfig schema**
**Given** I import KBPromptConfig from app.schemas.kb_settings
**Then** it includes: system_prompt (str, max 4000 chars), context_template (str), citation_style (inline/footnote/none), uncertainty_handling (acknowledge/refuse/best_effort), response_language (str)

**AC-7.12.8: EmbeddingConfig schema**
**Given** I import EmbeddingConfig from app.schemas.kb_settings
**Then** it includes: model_id (UUID, optional), batch_size (1-100), normalize (bool), truncation (start/end/none), max_length (128-16384), prefix_document (str, max 100 chars), prefix_query (str, max 100 chars), pooling_strategy (mean/cls/max/last)

**AC-7.12.9: KBSettings composite schema**
**Given** I import KBSettings from app.schemas.kb_settings
**Then** it aggregates all sub-configs (including EmbeddingConfig) with default factories
**And** includes preset field for quick configuration

**AC-7.12.10: Backwards compatibility**
**Given** existing KBs have empty {} settings
**When** I parse with KBSettings
**Then** all defaults are applied without errors

**AC-7.12.11: Re-indexing trigger detection**
**Given** EmbeddingConfig changes (model_id, normalize, prefix_*, pooling_strategy)
**When** KB settings are updated
**Then** system flags that re-indexing is required
**And** returns warning to user before applying

**Prerequisites:** Story 7.10 (KB Model Configuration) - DONE

**Technical Notes:**
- Create `backend/app/schemas/kb_settings.py`
- Use Pydantic v2 with Field validators
- Export from `backend/app/schemas/__init__.py`
- Unit tests for validation edge cases

---

## Story 7.13: KBConfigResolver Service

**Description:** As a developer, I want a configuration resolver service so request/KB/system configs are merged with proper precedence.

**Story Points:** 5

**Added:** 2025-12-09 (Correct-Course: KB-Level Configuration)

**Acceptance Criteria:**

**AC-7.13.1: Resolve single parameter**
**Given** I call resolve_param("temperature", request_value=0.5, kb_settings, system_default=0.7)
**Then** it returns 0.5 (request wins)

**AC-7.13.2: Fallback to KB setting**
**Given** I call resolve_param("temperature", request_value=None, kb_settings={temperature: 0.3}, system_default=0.7)
**Then** it returns 0.3 (KB wins)

**AC-7.13.3: Fallback to system default**
**Given** I call resolve_param("temperature", request_value=None, kb_settings={}, system_default=0.7)
**Then** it returns 0.7 (system default)

**AC-7.13.4: Resolve full generation config**
**Given** I call resolve_generation_config(kb_id, request_overrides)
**Then** it returns merged GenerationConfig with correct precedence

**AC-7.13.5: Resolve full retrieval config**
**Given** I call resolve_retrieval_config(kb_id, request_overrides)
**Then** it returns merged RetrievalConfig with correct precedence

**AC-7.13.6: Resolve chunking config**
**Given** I call resolve_chunking_config(kb_id)
**Then** it returns ChunkingConfig from KB or system defaults

**AC-7.13.7: Get KB system prompt**
**Given** I call get_kb_system_prompt(kb_id)
**When** KB has custom system_prompt in prompts config
**Then** it returns the KB's system_prompt
**Else** it returns system default prompt

**AC-7.13.8: Cache KB settings**
**Given** multiple requests for same KB
**Then** KB settings are cached (Redis, 5min TTL)
**And** cache invalidated on KB settings update

**Prerequisites:** Story 7.12

**Technical Notes:**
- Create `backend/app/services/kb_config_resolver.py`
- Inject ConfigService and KBService as dependencies
- Use Redis for caching with pub/sub invalidation
- Unit tests for all precedence scenarios

---

## Story 7.14: KB Settings UI - General Panel

**Description:** As a KB owner, I want a settings UI to configure chunking, retrieval, and generation parameters for my Knowledge Base.

**Story Points:** 5

**Added:** 2025-12-09 (Correct-Course: KB-Level Configuration)

**Acceptance Criteria:**

**AC-7.14.1: Settings tab in KB modal**
**Given** I open KB settings modal
**Then** I see tabs: General, Models, Advanced, Prompts

**AC-7.14.2: Chunking section**
**Given** I view General tab
**Then** I see Chunking section with:
- Strategy dropdown (Fixed, Recursive, Semantic)
- Chunk size slider (100-2000, default 512)
- Chunk overlap slider (0-500, default 50)

**AC-7.14.3: Retrieval section**
**Given** I view General tab
**Then** I see Retrieval section with:
- Top K slider (1-100, default 10)
- Similarity threshold slider (0.0-1.0, default 0.7)
- Method dropdown (Vector, Hybrid, HyDE)
- MMR toggle with lambda slider

**AC-7.14.4: Generation section**
**Given** I view General tab
**Then** I see Generation section with:
- Temperature slider (0.0-2.0, default 0.7)
- Top P slider (0.0-1.0, default 1.0)
- Max tokens input (100-16000)

**AC-7.14.5: Reset to defaults button**
**Given** I have modified settings
**When** I click "Reset to Defaults"
**Then** all General settings revert to system defaults
**And** confirmation dialog shown first

**AC-7.14.6: Save settings**
**Given** I modify settings
**When** I click Save
**Then** settings are saved to KB.settings JSONB
**And** success toast shown

**AC-7.14.7: Validation feedback**
**Given** I enter invalid value (e.g., temperature > 2.0)
**Then** field shows error styling
**And** Save is disabled

**AC-7.14.8: Settings API endpoint**
**Given** I call PUT /api/v1/knowledge-bases/{id}/settings
**Then** settings JSONB is updated
**And** audit log entry created

**Prerequisites:** Story 7.12, 7.13

**Technical Notes:**
- Extend `frontend/src/components/kb/kb-settings-modal.tsx`
- Create `frontend/src/components/kb/settings/` folder
- Use shadcn/ui Slider, Select, Switch components
- React Hook Form for validation

---

## Story 7.15: KB Settings UI - Prompts Panel

**Description:** As a KB owner, I want to configure custom system prompts and citation styles for my Knowledge Base.

**Story Points:** 3

**Added:** 2025-12-09 (Correct-Course: KB-Level Configuration)

**Acceptance Criteria:**

**AC-7.15.1: Prompts tab**
**Given** I open KB settings modal
**When** I click Prompts tab
**Then** I see System Prompt section

**AC-7.15.2: System prompt editor**
**Given** I view Prompts tab
**Then** I see textarea for system prompt (max 4000 chars)
**And** character count indicator
**And** placeholder with example prompt

**AC-7.15.3: Prompt variables help**
**Given** I view system prompt editor
**Then** I see help text explaining available variables:
- {context} - Retrieved document chunks
- {query} - User's question
- {kb_name} - Knowledge Base name

**AC-7.15.4: Citation style selector**
**Given** I view Prompts tab
**Then** I see Citation Style dropdown:
- Inline [1], [2] (default)
- Footnote
- None

**AC-7.15.5: Uncertainty handling selector**
**Given** I view Prompts tab
**Then** I see "When uncertain, the AI should:" dropdown:
- Acknowledge uncertainty (default)
- Refuse to answer
- Give best effort answer

**AC-7.15.6: Response language**
**Given** I view Prompts tab
**Then** I see Response Language dropdown with options:
- English (default)
- Tiếng Việt
**And** when I change the language, system prompt auto-switches to matching language version (if using a template)

**AC-7.15.7: Preview prompt**
**Given** I have entered a system prompt
**When** I click "Preview"
**Then** I see rendered prompt with sample values for {kb_name}, {context}, {query}

**AC-7.15.8: Prompt templates**
**Given** I view Prompts tab
**Then** I see "Load Template" dropdown with bilingual options:
- English: Default RAG, Strict Citations, Conversational, Technical Documentation
- Vietnamese: RAG Mặc định, Trích dẫn nghiêm ngặt, Hội thoại, Tài liệu kỹ thuật
**And** all templates include {kb_name}, {context}, {query} variables

**Prerequisites:** Story 7.14

**Technical Notes:**
- Create `frontend/src/components/kb/settings/prompts-panel.tsx`
- Textarea with character count (max 4000)
- Template loading from `frontend/src/lib/prompt-templates.ts` with bilingual support
- Response language dropdown with EN/VI options
- Auto-switch prompt to selected language using `detectTemplateFromPrompt()` function
- Fuzzy template matching supports exact match + key phrase detection

---

## Story 7.16: KB Settings Presets

**Description:** As a KB owner, I want preset configurations so I can quickly optimize my KB for common use cases.

**Story Points:** 3

**Added:** 2025-12-09 (Correct-Course: KB-Level Configuration)

**Acceptance Criteria:**

**AC-7.16.1: Preset selector in settings**
**Given** I open KB settings modal
**Then** I see "Quick Preset" dropdown at top with options:
- Custom (current)
- Legal
- Technical
- Creative
- Code
- General

**AC-7.16.2: Legal preset**
**Given** I select "Legal" preset
**Then** settings are populated with:
- temperature: 0.3
- chunk_size: 1000
- chunk_overlap: 200
- citation_style: footnote
- uncertainty_handling: acknowledge
- System prompt emphasizes accuracy and citations

**AC-7.16.3: Technical preset**
**Given** I select "Technical" preset
**Then** settings are populated with:
- temperature: 0.5
- chunk_size: 800
- chunk_overlap: 100
- citation_style: inline
- System prompt emphasizes precision and code examples

**AC-7.16.4: Creative preset**
**Given** I select "Creative" preset
**Then** settings are populated with:
- temperature: 0.9
- top_p: 0.95
- chunk_size: 500
- uncertainty_handling: best_effort
- System prompt allows creative interpretation

**AC-7.16.5: Code preset**
**Given** I select "Code" preset
**Then** settings are populated with:
- temperature: 0.2
- chunk_size: 600
- chunk_overlap: 50
- System prompt emphasizes code accuracy and syntax

**AC-7.16.6: General preset**
**Given** I select "General" preset
**Then** settings are populated with system defaults

**AC-7.16.7: Preset confirmation**
**Given** I have custom settings
**When** I select a preset
**Then** confirmation dialog warns about overwriting
**And** I can cancel or proceed

**AC-7.16.8: Preset indicator**
**Given** settings match a preset exactly
**Then** that preset is shown as selected
**When** I modify any setting
**Then** preset shows as "Custom"

**Prerequisites:** Story 7.14, 7.15

**Technical Notes:**
- Create `backend/app/core/kb_presets.py` with preset definitions
- Create `frontend/src/lib/kb-presets.ts` mirror
- API endpoint GET /api/v1/kb-presets

---

## Story 7.17: Service Integration

**Description:** As a system, I want search and generation services to use KB-level configuration so each KB behaves according to its settings.

**Story Points:** 2

**Added:** 2025-12-09 (Correct-Course: KB-Level Configuration)

**Acceptance Criteria:**

**AC-7.17.1: SearchService uses KB retrieval config**
**Given** I search in a KB with custom retrieval settings
**When** search executes
**Then** top_k, similarity_threshold, method from KB settings are used

**AC-7.17.2: GenerationService uses KB generation config**
**Given** I generate response in a KB with custom generation settings
**When** LLM call executes
**Then** temperature, top_p, max_tokens from KB settings are used

**AC-7.17.3: GenerationService uses KB system prompt**
**Given** KB has custom system_prompt
**When** I generate response
**Then** KB's system_prompt is used instead of default

**AC-7.17.4: Document worker uses KB chunking config**
**Given** I upload document to KB with custom chunking settings
**When** document is processed
**Then** chunk_size, chunk_overlap, strategy from KB settings are used

**AC-7.17.5: Request overrides still work**
**Given** KB has temperature: 0.5
**When** request includes temperature: 0.8
**Then** 0.8 is used (request wins)

**AC-7.17.6: Audit logging**
**Given** generation uses KB settings
**Then** audit log includes effective_config snapshot

**Prerequisites:** Story 7.13

**Technical Notes:**
- Modify `backend/app/services/search_service.py`
- Modify `backend/app/services/generation_service.py`
- Modify `backend/app/services/chunk_service.py` (Extended 2025-12-17: KB-aware embedding for chunk search)
- Modify `backend/app/workers/parsing.py` and `embedding.py`
- Inject KBConfigResolver as dependency

**Implementation Update (2025-12-17):**
- ChunkService extended to use KB's configured embedding model for chunk search
- `_search_chunks()` now resolves embedding model via `KBConfigResolver.get_kb_embedding_model()`
- Ensures query embedding dimensions match stored vectors when KB has custom embedding model
- Fixed qdrant-client 1.16+ API compatibility (search → query_points)

---

## Story 7.18: Document Worker KB Config Integration

**Description:** As a system, I want document processing workers to use KB-level chunking configuration so documents are chunked according to KB settings.

**Story Points:** 2

**Added:** 2025-12-10 (Tech Debt Resolution from Story 7-17)

**Type:** Technical Debt Resolution

**Acceptance Criteria:**

**AC-7.18.1: Worker fetches KB config**
**Given** a document is uploaded to a KB with custom chunking settings
**When** the document processing worker starts
**Then** it fetches the KB's chunking config via `KBConfigResolver.resolve(kb_id)`

**AC-7.18.2: Chunking uses KB settings**
**Given** KB has custom chunking config (chunk_size=1000, overlap=150, strategy=recursive)
**When** the document is chunked
**Then** the chunking uses these KB-specific values, not system defaults

**AC-7.18.3: Fallback to system defaults**
**Given** KB has no custom chunking config
**When** the document is chunked
**Then** system defaults are used (chunk_size=500, overlap=50)

**AC-7.18.4: Unit tests pass**
**Given** document worker integration tests exist
**When** tests execute
**Then** all tests pass verifying KB config is respected

**Technical Notes:**
- Add `get_kb_chunking_config()` helper to `document_tasks.py`
- Pass config to `process_document_task`
- Update `parsing.py` to accept chunking parameters
- See: [7-18-document-worker-kb-config.md](../sprint-artifacts/7-18-document-worker-kb-config.md)

---

## Story 7.19: Export Audit Logging

**Description:** As an admin, I want document exports to be logged in the audit trail so I can track data exports for compliance.

**Story Points:** 1

**Added:** 2025-12-10 (Tech Debt Resolution from Story 4-7)

**Type:** Technical Debt Resolution

**Acceptance Criteria:**

**AC-7.19.1: Export events logged**
**Given** a user exports a draft to DOCX/PDF/Markdown
**When** the export completes successfully
**Then** an audit event is logged with event_type, user_id, draft_id, format, timestamp

**AC-7.19.2: Failed exports logged**
**Given** a user attempts to export but it fails
**When** the export fails
**Then** an audit event is logged with event_type=draft.export_failed, error, status=error

**AC-7.19.3: Audit events visible**
**Given** export audit events are logged
**When** admin views audit log with filter event_type=draft.exported
**Then** export events appear with correct metadata

**AC-7.19.4: PII not logged**
**Given** export audit logging is enabled
**When** events are logged
**Then** draft content is NOT included (only metadata)

**Technical Notes:**
- Uncomment/add audit logging call in export endpoint
- Use existing AuditService infrastructure from Story 5.14
- See: [7-19-export-audit-logging.md](../sprint-artifacts/7-19-export-audit-logging.md)

---

## Story 7.20: Feedback Button DraftEditor Integration

**Description:** As a user, I want to click "This doesn't look right" on generated drafts so I can provide feedback and get better alternatives.

**Story Points:** 2

**Added:** 2025-12-10 (Tech Debt Resolution from Story 4-8)

**Type:** Technical Debt Resolution

**Acceptance Criteria:**

**AC-7.20.1: Feedback button visible**
**Given** user is viewing a generated draft in DraftEditor
**When** the draft is displayed
**Then** "This doesn't look right" button appears in toolbar

**AC-7.20.2: Button opens feedback modal**
**Given** user clicks "This doesn't look right" button
**When** button is clicked
**Then** FeedbackModal opens with 5 feedback type options

**AC-7.20.3: Feedback submission works**
**Given** user selects a feedback type and submits
**When** submission completes
**Then** feedback is sent to backend and RecoveryModal opens with 3 alternatives

**AC-7.20.4: Alternative selection triggers regeneration**
**Given** user selects an alternative from RecoveryModal
**When** alternative is selected
**Then** draft regenerates using the selected suggestion

**AC-7.20.5: Error recovery dialog shows on failure**
**Given** draft generation fails
**When** error occurs
**Then** ErrorRecoveryDialog appears with retry/cancel options

**Technical Notes:**
- Components exist (FeedbackModal, RecoveryModal, ErrorRecoveryDialog, useFeedback)
- Wire components into DraftEditor toolbar
- See: [7-20-feedback-button-integration.md](../sprint-artifacts/7-20-feedback-button-integration.md)

---

## Story 7.21: Draft Validation Warnings

**Description:** As a user editing a draft, I want to see warnings when citations are broken so I can fix them before saving.

**Story Points:** 2

**Added:** 2025-12-10 (Tech Debt Resolution from Story 4-6)

**Type:** Technical Debt Resolution

**Acceptance Criteria:**

**AC-7.21.1: Orphaned citation detection**
**Given** user edits draft and removes text containing citation markers
**When** save is attempted
**Then** warning shows "X citations have no matching markers"

**AC-7.21.2: Unused citation detection**
**Given** user edits draft and citation data exists without markers
**When** save is attempted
**Then** warning shows "X citation sources are not referenced"

**AC-7.21.3: Invalid marker detection**
**Given** user manually types [99] when only 5 citations exist
**When** draft is validated
**Then** warning shows "Citation [99] references non-existent source"

**AC-7.21.4: Warning badge in status bar**
**Given** validation issues exist
**When** draft is displayed
**Then** status bar shows warning badge with issue count

**AC-7.21.5: Auto-fix options**
**Given** validation warnings are shown
**When** user clicks "Auto-fix"
**Then** orphaned/unused citations are removed, invalid markers highlighted

**Technical Notes:**
- Create `useCitationValidator` hook
- Create `CitationValidationWarning` component
- Add warning badge to DraftEditor status bar
- See: [7-21-draft-validation-warnings.md](../sprint-artifacts/7-21-draft-validation-warnings.md)

---

## Story 7.22: SSE Reconnection Logic

**Description:** As a user, I want chat streaming to automatically reconnect on connection drop so I don't lose my work.

**Story Points:** 1

**Added:** 2025-12-10 (Tech Debt Resolution from Story 4-2)

**Type:** Technical Debt Resolution

**Acceptance Criteria:**

**AC-7.22.1: Automatic reconnection**
**Given** SSE connection drops during streaming
**When** network becomes available again
**Then** connection automatically retries with exponential backoff (1s, 2s, 4s, max 30s)

**AC-7.22.2: User notification**
**Given** SSE connection fails and is retrying
**When** retry is in progress
**Then** user sees "Connection lost. Reconnecting..." message

**AC-7.22.3: Max retry limit**
**Given** SSE connection fails repeatedly
**When** 5 retries fail
**Then** user sees "Connection failed. Click to retry" with manual retry button

**AC-7.22.4: Graceful recovery**
**Given** SSE reconnection succeeds
**When** connection is restored
**Then** streaming resumes cleanly

**Technical Notes:**
- Create `useSSEReconnection` hook with exponential backoff
- Integrate into chat streaming flow
- Add connection status UI component
- See: [7-22-sse-reconnection.md](../sprint-artifacts/7-22-sse-reconnection.md)

---

## Story 7.23: Feedback Analytics Dashboard

**Description:** As an admin, I want to see feedback patterns and regeneration success rates so I can identify systemic issues.

**Story Points:** 2

**Added:** 2025-12-10 (Tech Debt Resolution from Story 4-8)

**Type:** Technical Debt Resolution / Future Enhancement

**Acceptance Criteria:**

**AC-7.23.1: Feedback type distribution**
**Given** admin accesses analytics dashboard
**When** viewing feedback section
**Then** pie/bar chart shows distribution of feedback types over selected time range

**AC-7.23.2: Feedback by knowledge base**
**Given** admin views KB-specific analytics
**When** selecting a KB
**Then** breakdown of feedback types for that KB is displayed

**AC-7.23.3: Regeneration success rate**
**Given** admin views regeneration metrics
**When** viewing the regeneration section
**Then** success rate is shown over time

**AC-7.23.4: Trend analysis**
**Given** admin views feedback trends
**When** selecting date range
**Then** line chart shows feedback volume over time with trend indicator

**AC-7.23.5: Top issues summary**
**Given** admin views dashboard overview
**When** dashboard loads
**Then** top 3 most common feedback types are highlighted with counts

**Technical Notes:**
- Create FeedbackAnalyticsService with aggregation queries
- Add analytics endpoints to admin API
- Create chart components using shadcn/recharts
- See: [7-23-feedback-analytics.md](../sprint-artifacts/7-23-feedback-analytics.md)

---

## Story 7.24: KB Archive Backend

**Description:** As an administrator, I want to archive a Knowledge Base and all its documents so content is preserved but hidden from normal operations.

**Story Points:** 5

**Added:** 2025-12-10 (Correct-Course: KB Delete/Archive Feature)

**Acceptance Criteria:**

**AC-7.24.1: Archive endpoint**
**Given** I have ADMIN permission on a KB
**When** I call POST /api/v1/knowledge-bases/{id}/archive
**Then** the KB status is set to ARCHIVED
**And** KB.archived_at is set to current timestamp

**AC-7.24.2: Cascade to documents**
**Given** a KB is being archived
**When** the archive operation executes
**Then** all documents in KB have archived_at set to current timestamp
**And** an outbox event is created for Qdrant payload updates

**AC-7.24.3: Qdrant payload updates**
**Given** a KB archive outbox event is processed
**When** the outbox worker runs
**Then** all Qdrant points for KB documents have payload updated to is_archived: true
**And** archived points are excluded from search queries

**AC-7.24.4: Archived KB hidden from listings**
**Given** a KB is archived
**When** I call GET /api/v1/knowledge-bases
**Then** the archived KB does not appear in default listing
**And** it appears when include_archived=true query param is set

**AC-7.24.5: Upload blocked on archived KB**
**Given** a KB is archived
**When** I try to upload documents to it
**Then** I receive 400 Bad Request
**And** error message states: "Cannot upload to archived KB"

**AC-7.24.6: Audit logging**
**Given** a KB is archived
**When** the operation completes
**Then** the action is logged to audit.events with event_type=kb.archived

**Prerequisites:**
- Story 2.1 (KB CRUD Backend)
- Story 6.1 (Archive Document Backend - pattern reference)

**Technical Notes:**
- Add `archived_at TIMESTAMP` column to `knowledge_bases` table
- Reuse Epic 6 document archive pattern for cascade
- Batch Qdrant payload updates (100 points per batch)
- Use transactional outbox for consistency
- Index: `CREATE INDEX idx_kb_archived ON knowledge_bases(archived_at) WHERE archived_at IS NOT NULL`
- See: [sprint-change-proposal-kb-archive-delete-2025-12-10.md](../sprint-artifacts/sprint-change-proposal-kb-archive-delete-2025-12-10.md)

---

## Story 7.25: KB Restore Backend

**Description:** As an administrator, I want to restore an archived Knowledge Base so it becomes active and searchable again.

**Story Points:** 3

**Added:** 2025-12-10 (Correct-Course: KB Delete/Archive Feature)

**Acceptance Criteria:**

**AC-7.25.1: Restore endpoint**
**Given** I have ADMIN permission on an archived KB
**When** I call POST /api/v1/knowledge-bases/{id}/restore
**Then** the KB status is set to ACTIVE
**And** KB.archived_at is set to null

**AC-7.25.2: Cascade restore to documents**
**Given** a KB is being restored
**When** the restore operation executes
**Then** all documents in KB have archived_at set to null
**And** an outbox event is created for Qdrant payload updates

**AC-7.25.3: Qdrant payload updates**
**Given** a KB restore outbox event is processed
**When** the outbox worker runs
**Then** all Qdrant points for KB documents have payload updated to is_archived: false
**And** restored points are included in search queries

**AC-7.25.4: Restored KB visible in listings**
**Given** a KB is restored
**When** I call GET /api/v1/knowledge-bases
**Then** the KB appears in default listing
**And** document upload is permitted again

**AC-7.25.5: Audit logging**
**Given** a KB is restored
**When** the operation completes
**Then** the action is logged to audit.events with event_type=kb.restored

**Prerequisites:**
- Story 7.24 (KB Archive Backend)

**Technical Notes:**
- Mirror archive logic with inverse operation
- Batch Qdrant payload updates
- Use transactional outbox for consistency
- See: [sprint-change-proposal-kb-archive-delete-2025-12-10.md](../sprint-artifacts/sprint-change-proposal-kb-archive-delete-2025-12-10.md)

---

## Story 7.26: KB Delete/Archive UI

**Description:** As an administrator, I want UI controls for KB delete, archive, and restore so I can manage KB lifecycle without API calls.

**Story Points:** 3

**Added:** 2025-12-10 (Correct-Course: KB Delete/Archive Feature)

**Acceptance Criteria:**

**AC-7.26.1: KB actions menu**
**Given** I have ADMIN permission on an active KB
**When** I view KB settings/actions menu
**Then** I see "Archive KB" option
**And** I see "Delete KB" option (enabled only if document_count = 0)

**AC-7.26.2: Delete disabled for non-empty KB**
**Given** KB has documents
**When** I hover over disabled "Delete KB" button
**Then** tooltip shows: "Remove all documents before deleting"

**AC-7.26.3: Archive confirmation**
**Given** I click "Archive KB"
**When** confirmation dialog appears
**Then** it warns: "This will archive X documents. Archived KBs are hidden from search."
**And** I can confirm or cancel

**AC-7.26.4: Delete confirmation**
**Given** I click "Delete KB" on empty KB
**When** confirmation dialog appears
**Then** it warns: "This will permanently delete the KB. This cannot be undone."
**And** I must type KB name to confirm

**AC-7.26.5: Archived KB list filter**
**Given** I view KB list
**When** I toggle "Show Archived" filter
**Then** archived KBs appear with visual indicator (grayed out, archive icon)

**AC-7.26.6: Restore from list**
**Given** I view archived KBs list
**When** I click "Restore" on an archived KB
**Then** confirmation dialog appears
**And** KB is restored on confirmation

**AC-7.26.7: Delete empty KB only**
**Given** I have ADMIN permission on an empty KB (0 documents)
**When** I call DELETE /api/v1/knowledge-bases/{id}
**Then** the KB is permanently deleted from database
**And** the Qdrant collection is deleted
**And** the action is logged to audit.events

**AC-7.26.8: Delete non-empty KB blocked**
**Given** I have ADMIN permission on a KB with 1+ documents
**When** I call DELETE /api/v1/knowledge-bases/{id}
**Then** I receive 400 Bad Request
**And** error message states: "Cannot delete KB with documents. Archive or remove documents first."

**Prerequisites:**
- Story 7.24 (KB Archive Backend)
- Story 7.25 (KB Restore Backend)

**Technical Notes:**
- Add "Archived" filter toggle to KB list
- Destructive actions require explicit confirmation
- Show document count in archive warning
- Extend existing KB settings modal with archive/delete actions
- See: [sprint-change-proposal-kb-archive-delete-2025-12-10.md](../sprint-artifacts/sprint-change-proposal-kb-archive-delete-2025-12-10.md)

---

## Story 7.27: Queue Monitoring Enhancement with Operator Access

**Description:** As an operator or administrator, I want enhanced queue monitoring with per-step timing, error visibility, bulk retry capabilities, and filtering so that I can diagnose processing failures quickly, understand bottlenecks, and recover failed documents efficiently.

**Story Points:** 3

**Added:** 2025-12-10 (Correct-Course: Queue Monitoring Enhancement)

**Acceptance Criteria:**

**AC-7.27.1: Expandable task row with step breakdown**
**Given** I am viewing the TaskListModal
**When** I click a task row
**Then** it expands to show a step breakdown table with columns: Step, Status, Started, Completed, Duration

**AC-7.27.2: Live elapsed time for in-progress steps**
**Given** a processing step is in_progress
**Then** the Duration column shows live elapsed time counter

**AC-7.27.3: Color-coded status badges**
**Given** I view the step breakdown table
**Then** step statuses are displayed with color-coded badges (done=green, in_progress=blue, pending=gray, error=red)

**AC-7.27.4: Error tooltip on failed steps**
**Given** a step has status "error"
**When** I hover over the red error badge
**Then** a tooltip shows the full error message from step_errors

**AC-7.27.5: Bulk retry button visible**
**Given** failed tasks exist in the queue
**When** I view TaskListModal
**Then** "Retry All Failed" button is visible in the header

**AC-7.27.6: Selective retry with checkboxes**
**Given** I view tasks in TaskListModal
**Then** each task row has a checkbox for selection
**And** I can select multiple tasks for bulk retry

**AC-7.27.7: Bulk retry confirmation and feedback**
**Given** I confirm bulk retry
**When** retry completes
**Then** success toast shows "X documents queued for retry"

**AC-7.27.8: Filter tabs for task status**
**Given** I view TaskListModal
**Then** I see filter tabs: All, Active, Pending, Failed
**And** Failed tab shows count badge

**AC-7.27.9: Operator permission access**
**Given** a user is in a group with permission_level >= 2
**When** they access queue monitoring endpoints
**Then** access is granted (200 OK)

**AC-7.27.10: Regular user denied access**
**Given** a user has only permission_level = 1
**When** they access queue monitoring endpoints
**Then** access is denied (403 Forbidden)

**AC-7.27.11: Queue Status sidebar visibility**
**Given** a user has permission_level >= 2
**When** they view the application sidebar
**Then** "Queue Status" link is visible under Operations

**Prerequisites:**
- Story 5.4 (Processing Queue Status)
- Story 7.11 (Navigation Restructure with RBAC)

**Technical Notes:**
- Extend TaskInfo schema with processing_steps, current_step, step_errors
- New endpoint: POST /api/v1/admin/queue/retry-failed
- Create get_current_operator_or_admin() auth dependency
- Reuse existing ProcessingStep enum and processing_steps JSONB from Document model
- See: [7-27-queue-monitoring-enhancement.md](../sprint-artifacts/7-27-queue-monitoring-enhancement.md)
- See: [sprint-change-proposal-queue-monitoring-enhancement.md](../sprint-artifacts/sprint-change-proposal-queue-monitoring-enhancement.md)

---

## Story 7.28: Markdown Generation from DOCX/PDF (Backend)

**Description:** As a developer, I want to convert PDF/DOCX documents to Markdown during parsing so that chunk positions can be accurately highlighted in the document viewer.

**Story Points:** 3

**Added:** 2025-12-11 (Correct-Course: Markdown-First Document Processing)

**Type:** Enhancement (Document Chunk Viewer Position Accuracy)

**Acceptance Criteria:**

**AC-7.28.1: markdownify dependency**
**Given** I check backend/pyproject.toml
**Then** `markdownify>=0.11.0` is listed as a dependency

**AC-7.28.2: elements_to_markdown function**
**Given** I import elements_to_markdown from app.workers.parsing
**Then** function accepts list[Element] and returns string with markdown

**AC-7.28.3: ParsedContent markdown field**
**Given** I inspect ParsedContent dataclass
**Then** it has optional `markdown_content: str | None` field

**AC-7.28.4: Markdown stored in MinIO**
**Given** a PDF/DOCX document is processed
**When** parsing completes
**Then** `.parsed.json` includes `markdown_content` field with converted markdown

**AC-7.28.5: DOCX markdown quality**
**Given** a DOCX with headings, lists, and tables
**When** converted to markdown
**Then** output preserves heading levels (#, ##, ###), list formatting (-, 1.), and table structure (|)

**AC-7.28.6: Unit test coverage**
**Given** markdown generation tests exist
**Then** coverage is ≥80% for elements_to_markdown function

**Prerequisites:** None

**Technical Notes:**
- Use `markdownify` library for HTML-to-Markdown conversion
- `unstructured` elements have `.metadata.text_as_html` for tables
- Preserve element order and spacing
- Handle edge cases: empty elements, nested structures
- See: [sprint-change-proposal-markdown-first-processing.md](../sprint-artifacts/sprint-change-proposal-markdown-first-processing.md)

---

## Story 7.29: Markdown Content API Endpoint (Backend)

**Description:** As a frontend developer, I want an API endpoint to retrieve the markdown content of a document so I can render it in the chunk viewer.

**Story Points:** 2

**Added:** 2025-12-11 (Correct-Course: Markdown-First Document Processing)

**Type:** Enhancement (Document Chunk Viewer Position Accuracy)

**Acceptance Criteria:**

**AC-7.29.1: Endpoint implemented**
**Given** a document has markdown_content in parsed.json
**When** I call GET /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/markdown-content
**Then** I receive 200 with JSON body containing `markdown_content` and `generated_at`

**AC-7.29.2: 404 for older documents**
**Given** a document was processed before markdown generation was added
**When** I call the endpoint
**Then** I receive 404 with message "Markdown content not available for this document"

**AC-7.29.3: 400 for processing documents**
**Given** a document has status PROCESSING or PENDING
**When** I call the endpoint
**Then** I receive 400 with message "Document is still processing"

**AC-7.29.4: Response schema**
**Given** markdown content is available
**Then** response includes:
- `markdown_content: string` (the markdown text)
- `generated_at: datetime` (when markdown was generated)
- `document_id: UUID`

**AC-7.29.5: Permission check**
**Given** user does not have read access to the KB
**When** they call the endpoint
**Then** they receive 403 Forbidden

**AC-7.29.6: Integration tests**
**Given** integration tests for the endpoint exist
**Then** all success and error scenarios are covered

**Prerequisites:** Story 7.28

**Technical Notes:**
- Reuse existing document permission checks
- Read from MinIO `.parsed.json` file
- Cache-friendly (markdown content is immutable once generated)
- See: [sprint-change-proposal-markdown-first-processing.md](../sprint-artifacts/sprint-change-proposal-markdown-first-processing.md)

---

## Story 7.30: Enhanced Markdown Viewer with Highlighting (Frontend)

**Description:** As a user viewing document chunks, I want precise chunk highlighting in the markdown viewer so I can see exactly which text corresponds to each chunk.

**Story Points:** 3

**Added:** 2025-12-11 (Correct-Course: Markdown-First Document Processing)

**Type:** Enhancement (Document Chunk Viewer Position Accuracy)

**Acceptance Criteria:**

**AC-7.30.1: Fetch markdown content**
**Given** I open Document Chunk Viewer for a document
**When** markdown content is available
**Then** the viewer fetches markdown from /markdown-content endpoint

**AC-7.30.2: Precise highlighting**
**Given** I select a chunk in the chunk list
**When** the chunk has char_start and char_end positions
**Then** exactly those characters are highlighted in the markdown view

**AC-7.30.3: Highlight styling**
**Given** a chunk is highlighted
**Then** highlight uses visible background color (e.g., yellow-200)
**And** view auto-scrolls to bring highlighted text into viewport

**AC-7.30.4: Graceful fallback**
**Given** markdown content is not available (404)
**Then** viewer shows original format viewer (PDF/DOCX)
**And** user sees subtle message "Precise highlighting not available"

**AC-7.30.5: Loading state**
**Given** markdown content is being fetched
**Then** viewer shows loading spinner/skeleton

**AC-7.30.6: Unit tests**
**Given** highlighting logic tests exist
**Then** tests cover: highlight positioning, scroll behavior, fallback scenarios

**Prerequisites:** Story 7.29

**Technical Notes:**
- Create `useMarkdownContent` hook for data fetching
- Use `char_start` and `char_end` from chunk metadata
- Consider using React refs for scroll-into-view
- Syntax highlighting for code blocks (optional)
- See: [sprint-change-proposal-markdown-first-processing.md](../sprint-artifacts/sprint-change-proposal-markdown-first-processing.md)

---

## Story 7.31: View Mode Toggle for Chunk Viewer (Frontend)

**Description:** As a user, I want to toggle between Original and Markdown view modes so I can choose the viewing experience that works best for me.

**Story Points:** 2

**Added:** 2025-12-11 (Correct-Course: Markdown-First Document Processing)

**Type:** Enhancement (Document Chunk Viewer UX)

**Acceptance Criteria:**

**AC-7.31.1: Toggle component**
**Given** I open Document Chunk Viewer
**Then** I see a view mode toggle in the viewer header area
**And** toggle has options: "Original" | "Markdown"

**AC-7.31.2: Default mode**
**Given** markdown content is available for the document
**Then** Markdown view is selected by default

**AC-7.31.3: Disabled when unavailable**
**Given** markdown content is not available (older document)
**Then** toggle is disabled with Markdown option grayed out
**And** Original view is shown

**AC-7.31.4: Preference persistence**
**Given** I change view mode preference
**Then** preference is saved in localStorage
**And** persists across page refreshes

**AC-7.31.5: Visual indication**
**Given** toggle is displayed
**Then** current mode has clear visual indication (selected state)

**AC-7.31.6: Unit tests**
**Given** toggle component tests exist
**Then** tests cover: mode switching, preference persistence, disabled state

**Prerequisites:** Story 7.30

**Technical Notes:**
- Use shadcn/ui ToggleGroup component
- Store preference in localStorage key `lumikb-chunk-viewer-mode`
- Consider keyboard accessibility (arrow keys for toggle)
- See: [sprint-change-proposal-markdown-first-processing.md](../sprint-artifacts/sprint-change-proposal-markdown-first-processing.md)

---

## Story 7.32: Docling Document Parser Integration

**Description:** As an admin/KB owner, I want to select Docling as an alternative document parser backend so I can get better table extraction, layout analysis, and support for additional document formats.

**Story Points:** 2

**Added:** 2025-12-16 (Correct-Course: Docling Parser Integration)

**Type:** Feature Enhancement (Feature-Flagged)

**Acceptance Criteria:**

**AC-7.32.1: System-level feature flag**
**Given** I check backend environment configuration
**Then** `LUMIKB_PARSER_DOCLING_ENABLED` env var exists (default: false)
**And** when false, all documents use Unstructured regardless of KB settings

**AC-7.32.2: KB setting for parser backend**
**Given** I view KB settings schema
**Then** `processing.parser_backend` field exists in `DocumentProcessingConfig`
**With** options: `unstructured` (default), `docling`, `auto`
**And** setting applies to ALL document types (PDF, DOCX, MD, and future formats)

**AC-7.32.3: KB Settings UI integration**
**Given** I open KB Settings modal > Processing tab
**Then** I see "Document Parser" dropdown with options:
- Unstructured (default) - "Standard parser for PDF, DOCX, Markdown"
- Docling - "Advanced parser with better tables and layout"
- Auto - "Try Docling first, fallback to Unstructured"

**AC-7.32.4: Default behavior unchanged**
**Given** system has `LUMIKB_PARSER_DOCLING_ENABLED=false` (default)
**When** documents are processed
**Then** Unstructured is used for all formats (existing behavior)

**AC-7.32.5: ParsedContent interface preserved**
**Given** Docling parser is used
**When** document is parsed
**Then** output conforms to existing `ParsedContent` dataclass

**AC-7.32.6: Strategy pattern implementation**
**Given** I inspect `backend/app/workers/parsing.py`
**Then** `parse_document()` function accepts optional `parser_backend` parameter

**AC-7.32.7: Auto mode fallback**
**Given** KB has `parser_backend: auto`
**When** Docling parsing fails for a document
**Then** system automatically retries with Unstructured

**AC-7.32.8: Unit tests with mocked Docling**
**Given** unit tests for Docling parser exist
**Then** tests mock Docling library and test all scenarios

**Prerequisites:** None (self-contained feature)

**Technical Notes:**
- Add `DocumentParserBackend` enum to `kb_settings.py`
- Add `parser_backend` field to `DocumentProcessingConfig`
- Create `backend/app/workers/docling_parser.py`
- Optional dependency: `docling>=2.0.0`
- See: [7-32-docling-parser-integration.md](../sprint-artifacts/7-32-docling-parser-integration.md)

---

## Summary

Epic 7 establishes the infrastructure and DevOps foundation for LumiKB:

| Story | Points | Key Deliverable |
|-------|--------|-----------------|
| 7.1 | 5 | Docker E2E infrastructure |
| 7.2 | 5 | Centralized LLM configuration |
| 7.3 | 5 | CI/CD pipeline setup |
| 7.4 | 5 | Production deployment configuration |
| 7.5 | 5 | Monitoring & observability |
| 7.6 | 3 | Backend unit test fixes |
| 7.7 | 5 | Async Qdrant client migration |
| 7.8 | 3 | UI scroll isolation fix |
| 7.9 | 8 | LLM Model Registry |
| 7.10 | 5 | KB Model Configuration |
| 7.11 | 8 | Navigation restructure with RBAC |
| 7.12 | 5 | KB Settings Schema & Pydantic Models |
| 7.13 | 5 | KBConfigResolver Service |
| 7.14 | 5 | KB Settings UI - General Panel |
| 7.15 | 3 | KB Settings UI - Prompts Panel |
| 7.16 | 3 | KB Settings Presets |
| 7.17 | 2 | Service Integration |
| 7.18 | 2 | Document Worker KB Config (Tech Debt) |
| 7.19 | 1 | Export Audit Logging (Tech Debt) |
| 7.20 | 2 | Feedback Button Integration (Tech Debt) |
| 7.21 | 2 | Draft Validation Warnings (Tech Debt) |
| 7.22 | 1 | SSE Reconnection Logic (Tech Debt) |
| 7.23 | 2 | Feedback Analytics Dashboard (Tech Debt) |
| 7.24 | 5 | KB Archive Backend |
| 7.25 | 3 | KB Restore Backend |
| 7.26 | 3 | KB Delete/Archive UI |
| 7.27 | 3 | Queue Monitoring Enhancement |
| 7.28 | 3 | Markdown Generation from DOCX/PDF |
| 7.29 | 2 | Markdown Content API Endpoint |
| 7.30 | 3 | Enhanced Markdown Viewer with Highlighting |
| 7.31 | 2 | View Mode Toggle for Chunk Viewer |
| 7.32 | 2 | Docling Document Parser Integration |

**Total Stories:** 32
**Total Story Points:** 116

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._
