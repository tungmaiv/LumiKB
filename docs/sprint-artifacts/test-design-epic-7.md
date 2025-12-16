# Test Design: Epic 7 - Infrastructure & DevOps

**Date:** 2025-12-08
**Author:** Murat (Master Test Architect)
**Status:** Draft
**Epic ID:** epic-7

---

## Executive Summary

**Scope:** Full test design for Epic 7 (Infrastructure & DevOps) covering Docker E2E infrastructure, CI/CD pipelines, LLM model registry, KB model configuration, monitoring/observability, and technical debt fixes.

**Risk Summary:**

- Total risks identified: 14
- High-priority risks (≥6): 6
- Critical categories: TECH, SEC, OPS, PERF, DATA

**Coverage Summary:**

- P0 scenarios: 28 (56 hours)
- P1 scenarios: 42 (42 hours)
- P2/P3 scenarios: 35 (17 hours)
- **Total effort**: 115 hours (~14 days)

**Epic 7 Stories (10 total):**

| Story | Title | Priority | Tests |
|-------|-------|----------|-------|
| 7-1 | Docker E2E Testing Infrastructure | HIGH | 18 |
| 7-2 | Centralized LLM Configuration | HIGH | 12 |
| 7-3 | CI/CD Pipeline Setup | HIGH | 16 |
| 7-4 | Production Deployment Configuration | HIGH | 10 |
| 7-5 | Monitoring and Observability | MEDIUM | 14 |
| 7-6 | Backend Unit Test Fixes | MEDIUM | 8 |
| 7-7 | Async Qdrant Migration | MEDIUM | 10 |
| 7-8 | UI Scroll Isolation Fix | LOW | 6 |
| 7-9 | LLM Model Registry | HIGH | 18 |
| 7-10 | KB Model Configuration | HIGH | 16 |

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
|---------|----------|-------------|-------------|--------|-------|------------|-------|----------|
| R-001 | TECH | Docker E2E services fail to start in CI environment | 3 | 3 | 9 | Health checks, service dependencies, timeout configuration | Dev | Story 7-1 |
| R-002 | SEC | API keys for LLM providers exposed in logs or config | 2 | 3 | 6 | Encryption at rest, redaction in logs, secret management | Dev | Story 7-9 |
| R-003 | OPS | CI/CD pipeline fails due to test flakiness | 3 | 2 | 6 | Test retries, parallelization, container caching | QA | Story 7-3 |
| R-004 | TECH | Qdrant async migration breaks existing search | 2 | 3 | 6 | Feature flag, gradual rollout, rollback plan | Dev | Story 7-7 |
| R-005 | DATA | KB model change causes embedding dimension mismatch | 2 | 3 | 6 | Validation, re-indexing workflow, migration warnings | Dev | Story 7-10 |
| R-006 | PERF | Model registry API slow with many registered models | 2 | 2 | 4 | Pagination, caching, indexed queries | Dev | Story 7-9 |

### Medium-Priority Risks (Score 3-5)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|----------|-------------|-------------|--------|-------|------------|-------|
| R-007 | OPS | Production deployment config differs from dev | 2 | 2 | 4 | Environment parity checks, config validation | Dev |
| R-008 | TECH | Monitoring metrics cardinality explosion | 2 | 2 | 4 | Metric naming conventions, cardinality limits | Dev |
| R-009 | PERF | Distributed tracing overhead impacts latency | 2 | 2 | 4 | Sampling strategy, async span export | Dev |
| R-010 | TECH | Unit test fixes break previously passing tests | 2 | 2 | 4 | Regression testing, incremental fixes | QA |
| R-011 | UX | UI scroll isolation causes side effects | 2 | 1 | 2 | Component isolation testing, visual regression | Dev |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
|---------|----------|-------------|-------------|--------|-------|--------|
| R-012 | OPS | Container registry authentication issues | 1 | 2 | 2 | Document setup, test in CI |
| R-013 | TECH | LiteLLM proxy configuration complexity | 1 | 2 | 2 | Configuration templates |
| R-014 | DOC | Monitoring dashboards missing key metrics | 1 | 1 | 1 | Dashboard review checklist |

### Risk Category Legend

- **TECH**: Technical/Architecture (service integration, migrations, async operations)
- **SEC**: Security (API keys, secrets, credentials exposure)
- **PERF**: Performance (latency, throughput, resource usage)
- **DATA**: Data Integrity (embedding consistency, model configuration)
- **OPS**: Operations (CI/CD, deployment, container orchestration)
- **UX**: User Experience (UI behavior, visual consistency)
- **DOC**: Documentation (missing or outdated docs)

---

## Test Coverage Plan

### P0 (Critical) - Run on every commit

**Criteria**: Blocks deployment + High risk (≥6) + Critical infrastructure

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
|-------------|------------|-----------|------------|-------|-------|
| Story 7-1: Docker E2E services healthy | Integration | R-001 | 5 | QA | All 8 services start, health checks pass |
| Story 7-1: E2E test execution | E2E | R-001 | 3 | QA | Playwright runs against Docker stack |
| Story 7-3: CI pipeline unit tests | Integration | R-003 | 3 | Dev | Backend + frontend tests execute |
| Story 7-3: CI pipeline integration tests | Integration | R-003 | 3 | Dev | Test containers spin up |
| Story 7-7: Async Qdrant search functional | Integration | R-004 | 4 | QA | Search returns results, no timeouts |
| Story 7-9: Model API key encryption | Integration | R-002 | 3 | QA | Keys encrypted at rest, redacted in GET |
| Story 7-10: Qdrant collection creation | Integration | R-005 | 4 | QA | Correct dimensions, distance metric |
| Story 7-10: Model change validation | API | R-005 | 3 | QA | Re-indexing warning displayed |

**Total P0**: 28 tests, 56 hours (2h each for complex infrastructure tests)

### P1 (High) - Run on PR to main

**Criteria**: Important infrastructure features + Medium risk (3-5)

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
|-------------|------------|-----------|------------|-------|-------|
| Story 7-1: Database seeding works | Integration | - | 3 | QA | Test users, KBs, documents created |
| Story 7-1: GitHub Actions workflow | Integration | - | 2 | Dev | Workflow executes, artifacts uploaded |
| Story 7-2: LiteLLM config centralized | API | - | 3 | QA | Config CRUD, validation |
| Story 7-2: Embedding model config | API | - | 3 | QA | Model parameters stored |
| Story 7-3: Linting passes | Integration | - | 2 | Dev | Ruff, ESLint, tsc |
| Story 7-3: Security scanning | Integration | - | 2 | Dev | Dependency vulnerabilities detected |
| Story 7-4: Production config validation | Integration | R-007 | 3 | Dev | Environment variables complete |
| Story 7-5: Application metrics exposed | API | R-008 | 4 | QA | /metrics endpoint, latency, errors |
| Story 7-5: Health check endpoints | API | - | 3 | QA | Detailed health, dependencies |
| Story 7-9: Model CRUD operations | API | - | 5 | QA | Create, read, update, delete, test |
| Story 7-9: Model validation | API | - | 3 | QA | Connectivity test, API key validation |
| Story 7-10: Embedding model selection | E2E | - | 3 | QA | KB creation with model |
| Story 7-10: RAG parameter overrides | API | - | 3 | QA | KB-level settings applied |

**Total P1**: 42 tests, 42 hours (1h average)

### P2 (Medium) - Run nightly/weekly

**Criteria**: Secondary features + Low risk (1-2) + Edge cases

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
|-------------|------------|-----------|------------|-------|-------|
| Story 7-1: Service dependency ordering | Integration | - | 2 | Dev | postgres → redis → backend |
| Story 7-1: E2E test artifacts | Integration | - | 2 | QA | Screenshots, videos uploaded |
| Story 7-3: Container image tagging | Integration | - | 2 | Dev | Version + commit SHA tags |
| Story 7-4: Docker Compose production | Integration | - | 3 | Dev | Production config starts |
| Story 7-5: Distributed tracing | Integration | R-009 | 3 | QA | Traces span services |
| Story 7-5: Alerting rules | Integration | - | 2 | Dev | Thresholds trigger alerts |
| Story 7-6: Unit test regression | Unit | R-010 | 4 | QA | Previously passing tests still pass |
| Story 7-6: Test coverage maintained | Unit | - | 2 | Dev | Coverage ≥80% |
| Story 7-7: Async performance improvement | Performance | - | 3 | QA | Latency reduction measured |
| Story 7-8: Scroll isolation visual | Component | R-011 | 3 | Dev | No side effects on other panels |
| Story 7-9: NER model parameters | API | - | 3 | QA | Entity types, confidence threshold |
| Story 7-9: Admin UI model management | E2E | - | 3 | QA | Add, edit, delete, test models |
| Story 7-10: Generation model selection | E2E | - | 2 | QA | Context window displayed |

**Total P2**: 35 tests, 17 hours (0.5h average)

### P3 (Low) - Run on-demand

**Criteria**: Nice-to-have + Exploratory + Performance benchmarks

| Requirement | Test Level | Test Count | Owner | Notes |
|-------------|------------|------------|-------|-------|
| Story 7-1: E2E full suite performance | Performance | 2 | QA | Suite < 10 minutes |
| Story 7-5: Dashboard visualization | Manual | 2 | Dev | Grafana dashboards review |
| Story 7-9: Model registry pagination | Performance | 2 | QA | 100+ models paginated |

**Total P3**: 6 tests, 1.5 hours

---

## Execution Order

### Smoke Tests (<5 min)

**Purpose**: Fast feedback, catch infrastructure-breaking issues

- [ ] Docker E2E services start successfully (Story 7-1, 3min)
- [ ] Backend health check passes (Story 7-1, 1min)
- [ ] Model registry API accessible (Story 7-9, 1min)

**Total**: 3 scenarios

### P0 Tests (<60 min)

**Purpose**: Critical path validation for infrastructure deployment

- [ ] Story 7-1: Docker Compose E2E up (Integration, 8min)
- [ ] Story 7-1: All services healthy (Integration, 5min)
- [ ] Story 7-1: Playwright E2E execution (E2E, 15min)
- [ ] Story 7-3: CI unit tests execute (Integration, 8min)
- [ ] Story 7-3: CI integration tests execute (Integration, 10min)
- [ ] Story 7-7: Async Qdrant search works (Integration, 5min)
- [ ] Story 7-9: API key encryption verified (Integration, 5min)
- [ ] Story 7-10: Qdrant collection auto-creation (Integration, 5min)

**Total**: 28 scenarios (~60 min execution)

### P1 Tests (<45 min)

**Purpose**: Important infrastructure feature coverage

- [ ] Story 7-1: Database seeding (Integration, 3min)
- [ ] Story 7-2: LLM config CRUD (API, 4min)
- [ ] Story 7-5: Metrics endpoint (API, 3min)
- [ ] Story 7-9: Model CRUD operations (API, 5min)
- [ ] Story 7-10: KB model selection (E2E, 5min)
- [+ 37 more P1 tests...]

**Total**: 42 scenarios (~45 min execution)

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
|----------|-------|------------|-------------|-------|
| P0 | 28 | 2.0 | 56 | Complex infrastructure, Docker, CI/CD tests |
| P1 | 42 | 1.0 | 42 | Standard API/integration coverage |
| P2 | 35 | 0.5 | 17 | Component tests, edge cases |
| P3 | 6 | 0.25 | 1.5 | Exploratory, performance benchmarks |
| **Buffer (10%)** | - | - | **11.6** | **Unknown unknowns** |
| **Total** | **111** | **-** | **128** | **~16 days** |

### Prerequisites

**Test Data:**

- `llmModelFactory()` - Embedding, generation, NER models
- `kbWithModelFactory()` - KBs with specific model configurations
- `dockerServiceFactory()` - Docker service health fixtures
- `ciPipelineFactory()` - CI/CD workflow test scenarios

**Tooling:**

- **Docker Compose** for E2E infrastructure (docker-compose.e2e.yml)
- **Playwright** for E2E tests (navigation, model selection)
- **pytest** for API tests (model registry, configuration endpoints)
- **GitHub Actions** for CI/CD testing
- **Vitest** for component tests (scroll isolation)

**Environment:**

- Docker Desktop or Docker Engine with Compose v2
- GitHub Actions runner access
- LiteLLM proxy with test API keys
- Prometheus/Grafana for monitoring tests

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Infrastructure paths** (Docker E2E, CI/CD): ≥90%
- **Security scenarios** (API key encryption, secrets): 100%
- **Model registry CRUD**: 100%
- **KB model configuration**: ≥90%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Docker E2E environment starts reliably
- [ ] API key encryption verified
- [ ] Qdrant collection creation with correct dimensions

---

## Mitigation Plans

### R-001: Docker E2E Services Fail in CI (Score: 9 - CRITICAL)

**Mitigation Strategy:**
1. Implement proper health checks for all 8 services
2. Configure service dependencies with `depends_on: condition: service_healthy`
3. Add startup timeout configuration (60-90 seconds)
4. Use Docker Compose wait scripts
5. Test on multiple CI environments (Ubuntu, self-hosted)

**Owner:** Dev (Winston/Murat)
**Timeline:** Story 7-1
**Verification:**
- All services healthy within 60 seconds
- E2E tests execute successfully
- CI workflow passes reliably

---

### R-002: API Keys Exposed in Logs or Config (Score: 6)

**Mitigation Strategy:**
1. Encrypt API keys at rest in database (AES-256 or Fernet)
2. Redact keys in API GET responses (show only last 4 chars)
3. Filter secrets from application logs
4. Use environment variable secrets in CI/CD
5. Security audit of configuration endpoints

**Owner:** Dev + Security
**Timeline:** Story 7-9
**Verification:**
- API keys never appear in logs (grep verification)
- GET /models returns redacted keys
- Encryption verified with database inspection

---

### R-003: CI/CD Pipeline Fails Due to Test Flakiness (Score: 6)

**Mitigation Strategy:**
1. Configure test retries (2-3 retries for flaky tests)
2. Use test parallelization carefully (avoid resource contention)
3. Implement container caching for faster builds
4. Add test isolation (each test cleans up)
5. Monitor test execution times, flag slow tests

**Owner:** QA
**Timeline:** Story 7-3
**Verification:**
- CI pipeline passes 95%+ on first run
- Retry mechanism catches transient failures
- Build time < 15 minutes

---

### R-004: Async Qdrant Migration Breaks Search (Score: 6)

**Mitigation Strategy:**
1. Implement feature flag for async Qdrant client
2. Run both sync and async in parallel during migration
3. Create rollback plan to sync client
4. Test with production-like data volumes
5. Monitor search latency during rollout

**Owner:** Dev (Amelia)
**Timeline:** Story 7-7
**Verification:**
- Search returns identical results (sync vs async)
- No timeout errors under load
- Latency improvement measured (target: 20% reduction)

---

### R-005: KB Model Change Causes Embedding Mismatch (Score: 6)

**Mitigation Strategy:**
1. Validate embedding model dimensions before KB creation
2. Display re-indexing warning when changing embedding model
3. Implement background re-indexing job
4. Track embedding model version per KB
5. Prevent model change without re-indexing confirmation

**Owner:** Dev
**Timeline:** Story 7-10
**Verification:**
- KB creation fails with invalid dimensions
- Warning displayed on model change
- Re-indexing job queued successfully
- Documents searchable after re-indexing

---

## Test Scenario Details

### Story 7-1: Docker E2E Testing Infrastructure

**P0 Scenarios (8):**

1. **Docker Compose services start**
   - Test Level: Integration
   - Risk: R-001
   - Steps:
     1. Run `docker-compose -f docker-compose.e2e.yml up -d`
     2. Wait for all services
   - Validation: All 8 services (frontend, backend, celery, postgres, redis, qdrant, minio, litellm) healthy

2. **Backend health check passes**
   - Test Level: Integration
   - Risk: R-001
   - Steps:
     1. Call `GET /health` on backend
   - Validation: 200 OK with healthy dependencies

3. **Frontend accessible**
   - Test Level: Integration
   - Risk: R-001
   - Steps:
     1. Navigate to http://localhost:3000
   - Validation: Page loads, no errors

4. **Playwright E2E tests execute**
   - Test Level: E2E
   - Risk: R-001
   - Steps:
     1. Run `npm run test:e2e`
   - Validation: Tests pass, report generated

5. **Database seeding works**
   - Test Level: Integration
   - Steps:
     1. Run seed script
     2. Query users, KBs, documents
   - Validation: Test data created

**P1 Scenarios (5):**

6. **Service dependency ordering**
   - Test Level: Integration
   - Validation: postgres → redis → backend → celery order

7. **Test artifacts uploaded**
   - Test Level: Integration
   - Validation: Screenshots, videos in playwright-report/

8. **GitHub Actions workflow executes**
   - Test Level: Integration
   - Validation: E2E job runs, passes

9. **Network isolation**
   - Test Level: Integration
   - Validation: Services communicate on e2e-network

10. **Environment variables configured**
    - Test Level: Integration
    - Validation: All required env vars present

---

### Story 7-9: LLM Model Registry

**P0 Scenarios (6):**

11. **Model registration API**
    - Test Level: API
    - Steps:
      1. POST `/api/v1/admin/models` with embedding model config
    - Validation: Model created, ID returned

12. **API key encryption at rest**
    - Test Level: Integration
    - Risk: R-002
    - Steps:
      1. Register model with API key
      2. Query database directly
    - Validation: api_key_encrypted column is encrypted bytes

13. **API key redacted in GET**
    - Test Level: API
    - Risk: R-002
    - Steps:
      1. GET `/api/v1/admin/models/{id}`
    - Validation: api_key shows only last 4 chars

14. **Model validation connectivity**
    - Test Level: API
    - Steps:
      1. POST `/api/v1/admin/models/{id}/test`
    - Validation: Connectivity test passes/fails appropriately

**P1 Scenarios (9):**

15. **Embedding model parameters**
    - Test Level: API
    - Validation: dimensions, max_tokens, distance_metric stored

16. **Generation model parameters**
    - Test Level: API
    - Validation: context_window, max_output_tokens, temperature stored

17. **NER model parameters**
    - Test Level: API
    - Validation: entity_types, confidence_threshold stored

18. **Model list endpoint**
    - Test Level: API
    - Validation: All models returned, filtered by type

19. **Model update endpoint**
    - Test Level: API
    - Validation: Parameters updated, audit logged

20. **Model delete endpoint**
    - Test Level: API
    - Validation: Model deleted, cannot be referenced

21. **Admin-only access**
    - Test Level: API
    - Validation: Non-admin gets 403

22. **Model tags**
    - Test Level: API
    - Validation: Tags stored and searchable

23. **RAG default parameters**
    - Test Level: API
    - Validation: similarity_threshold, top_k, rerank settings

---

### Story 7-10: KB Model Configuration

**P0 Scenarios (7):**

24. **Qdrant collection auto-creation**
    - Test Level: Integration
    - Risk: R-005
    - Steps:
      1. Create KB with embedding model
    - Validation: Qdrant collection created with correct dimensions

25. **Collection dimension matches model**
    - Test Level: Integration
    - Risk: R-005
    - Steps:
      1. Create KB with 1536-dim model
      2. Query Qdrant collection config
    - Validation: vector_size = 1536

26. **Distance metric from model**
    - Test Level: Integration
    - Risk: R-005
    - Validation: distance = COSINE (or model config)

27. **Model change warning**
    - Test Level: API
    - Risk: R-005
    - Steps:
      1. Create KB with model A
      2. Attempt to change to model B
    - Validation: Warning about re-indexing returned

**P1 Scenarios (6):**

28. **Embedding model selection UI**
    - Test Level: E2E
    - Validation: Dropdown shows available models

29. **Generation model selection UI**
    - Test Level: E2E
    - Validation: Dropdown shows available models

30. **RAG parameter overrides**
    - Test Level: API
    - Validation: KB-level overrides applied to search

31. **Model details in KB response**
    - Test Level: API
    - Validation: embedding_model, generation_model objects included

32. **Re-indexing job queued**
    - Test Level: Integration
    - Validation: Celery task created on model change

33. **Default model pre-selection**
    - Test Level: E2E
    - Validation: System default model selected on new KB

---

### Story 7-2: Centralized LLM Configuration

**Story Summary**: Admin UI to configure LLM model settings with hot-reload capability

**Risk Assessment (Story-Specific)**:

| ID | Category | Risk Description | Prob | Impact | Score | Mitigation |
|----|----------|------------------|------|--------|-------|------------|
| R-7.2-1 | TECH | Hot-reload mechanism fails silently, config changes not applied | 2 | 3 | **6** | Integration tests verify config propagation end-to-end |
| R-7.2-2 | DATA | Embedding dimension mismatch corrupts KB search results | 2 | 3 | **6** | Dimension validation before allowing model switch |
| R-7.2-3 | SEC | Non-admin users access LLM config endpoints | 1 | 3 | 3 | Unit tests verify is_superuser guard on all endpoints |
| R-7.2-4 | PERF | Config polling causes excessive Redis load | 2 | 2 | 4 | Monitor Redis ops, use 30s polling interval |
| R-7.2-5 | OPS | LiteLLM proxy doesn't support hot-reload signal | 2 | 2 | 4 | Document polling fallback, test both mechanisms |
| R-7.2-6 | TECH | Model connection test timeout causes UI freeze | 2 | 2 | 4 | 5s timeout with async loading state |

**P0 Scenarios (3) - Critical Path**:

| Test ID | AC | Level | Scenario | Expected Result | Risk |
|---------|-----|-------|----------|-----------------|------|
| 7.2-P0-01 | AC-7.2.2 | Integration | Update LLM config via PUT endpoint, verify new config returned by GET | Config persists and reflects changes | R-7.2-1 |
| 7.2-P0-02 | AC-7.2.2 | Integration | Update config, verify hot-reload propagates within 30s | Services use new config without restart | R-7.2-1 |
| 7.2-P0-03 | AC-7.2.3 | Unit | Select embedding model with different dimensions than existing KB | Warning returned with affected KB list | R-7.2-2 |

**P1 Scenarios (5) - Core Functionality**:

| Test ID | AC | Level | Scenario | Expected Result |
|---------|-----|-------|----------|-----------------|
| 7.2-P1-01 | AC-7.2.1 | Integration | GET /api/v1/admin/config/llm returns all required fields | Response includes provider, model, base_url, temperature, max_tokens |
| 7.2-P1-02 | AC-7.2.4 | Integration | POST /api/v1/admin/config/llm/test with valid model | Returns health status success |
| 7.2-P1-03 | AC-7.2.4 | Integration | POST /api/v1/admin/config/llm/test with invalid model | Returns health status failure with error message |
| 7.2-P1-04 | AC-7.2.1 | Unit | ConfigService.get_llm_config() returns current settings | Settings match database/defaults |
| 7.2-P1-05 | AC-7.2.2 | Unit | ConfigService.update_llm_config() invalidates Redis cache | Cache key deleted, audit logged |

**P2 Scenarios (5) - UI Components**:

| Test ID | AC | Level | Scenario | Expected Result |
|---------|-----|-------|----------|-----------------|
| 7.2-P2-01 | AC-7.2.1 | Component | LLMConfigForm renders with current values | Form fields populated correctly |
| 7.2-P2-02 | AC-7.2.4 | Component | ModelHealthIndicator shows connection status | Green/red indicator based on test result |
| 7.2-P2-03 | AC-7.2.2 | Component | Apply Changes button shows loading state | Spinner during update, success toast after |
| 7.2-P2-04 | AC-7.2.3 | Component | Dimension mismatch warning dialog displays | Lists affected KBs, requires confirmation |
| 7.2-P2-05 | AC-7.2.1 | E2E | Admin navigates to /admin/config/llm | Page loads with current config |

**P3 Scenarios (4) - Edge Cases & Security**:

| Test ID | AC | Level | Scenario | Expected Result |
|---------|-----|-------|----------|-----------------|
| 7.2-P3-01 | SEC | Integration | Non-admin user calls PUT /api/v1/admin/config/llm | 403 Forbidden |
| 7.2-P3-02 | SEC | Integration | Non-admin user calls POST /api/v1/admin/config/llm/test | 403 Forbidden |
| 7.2-P3-03 | AC-7.2.1 | Unit | useLLMConfig hook returns loading/error/data states | Correct state transitions |
| 7.2-P3-04 | PERF | Integration | Redis polling interval respects 30s minimum | No excessive Redis operations |

**Test File Locations**:

```
backend/tests/unit/test_config_service.py          # ConfigService LLM methods
backend/tests/integration/test_llm_config_api.py   # API endpoint tests
frontend/src/hooks/__tests__/useLLMConfig.test.ts  # Hook tests
frontend/src/components/admin/__tests__/llm-config-form.test.tsx  # Component tests
```

**Resource Estimate**:

| Test Level | Count | Est. Time | Automation |
|------------|-------|-----------|------------|
| Unit | 5 | 2h | pytest, vitest |
| Integration | 8 | 4h | pytest + httpx |
| Component | 4 | 3h | vitest + RTL |
| E2E | 1 | 1h | playwright |
| **Total** | **18** | **10h** | |

**Quality Gate Criteria**:

- [ ] Unit test coverage ≥80% for ConfigService LLM methods
- [ ] All P0 tests passing
- [ ] All P1 tests passing
- [ ] Integration tests use mocked LiteLLM (no external dependencies)
- [ ] Manual verification: hot-reload works without service restart

---

### Story 7-3: CI/CD Pipeline Setup

**P0 Scenarios (6):**

34. **Backend unit tests execute**
    - Test Level: Integration
    - Risk: R-003
    - Steps:
      1. Push to PR
      2. Check CI workflow
    - Validation: pytest runs, results reported

35. **Frontend unit tests execute**
    - Test Level: Integration
    - Risk: R-003
    - Validation: vitest runs, results reported

36. **Integration tests with containers**
    - Test Level: Integration
    - Risk: R-003
    - Validation: testcontainers spin up PostgreSQL, Redis

**P1 Scenarios (10):**

37. **Python linting (ruff)**
    - Test Level: Integration
    - Validation: No linting errors

38. **TypeScript linting (ESLint)**
    - Test Level: Integration
    - Validation: No linting errors

39. **Type checking passes**
    - Test Level: Integration
    - Validation: mypy/tsc pass

40. **Security scanning**
    - Test Level: Integration
    - Validation: Dependency vulnerabilities detected

41. **Container image building**
    - Test Level: Integration
    - Validation: Docker images built

42. **Image tagging**
    - Test Level: Integration
    - Validation: version + commit SHA tags

43. **Coverage report generated**
    - Test Level: Integration
    - Validation: Coverage metrics available

44. **Test retries on failure**
    - Test Level: Integration
    - Validation: Flaky tests retried

45. **Artifact caching**
    - Test Level: Integration
    - Validation: Faster subsequent builds

46. **Branch protection**
    - Test Level: Manual
    - Validation: PR blocked on failing checks

---

### Story 7-5: Monitoring and Observability

**P1 Scenarios (7):**

47. **Metrics endpoint exposed**
    - Test Level: API
    - Risk: R-008
    - Steps:
      1. GET `/metrics`
    - Validation: Prometheus format metrics

48. **API latency metrics**
    - Test Level: API
    - Validation: http_request_duration_seconds present

49. **Error rate metrics**
    - Test Level: API
    - Validation: http_request_errors_total present

50. **Health check detailed**
    - Test Level: API
    - Validation: Database, Redis, Qdrant status included

51. **Queue depth metrics**
    - Test Level: API
    - Validation: celery_queue_length present

**P2 Scenarios (7):**

52. **Distributed tracing**
    - Test Level: Integration
    - Risk: R-009
    - Validation: Traces span backend → Celery

53. **Alerting rules fire**
    - Test Level: Integration
    - Validation: High error rate triggers alert

54. **Dashboard visualization**
    - Test Level: Manual
    - Validation: Grafana dashboards render

55. **Infrastructure metrics**
    - Test Level: API
    - Validation: CPU, memory, connections

56. **Trace sampling**
    - Test Level: Integration
    - Validation: Sampling rate configurable

57. **Alert history**
    - Test Level: Integration
    - Validation: Past alerts queryable

58. **Service dependency map**
    - Test Level: Manual
    - Validation: Dependencies visualized

---

## Assumptions and Dependencies

### Assumptions

1. Docker Desktop or Engine available on dev/CI environments
2. GitHub Actions runner has Docker access
3. LiteLLM proxy available for model connectivity testing
4. Qdrant async client API compatible with sync usage
5. Model registry is admin-only feature

### Dependencies

1. **Epic 5 completion** - Story 5-0 (Epic Integration) prerequisite for E2E
2. **Docker Compose ≥2.0** - Required for health check syntax
3. **Playwright ≥1.40** - Already installed
4. **pytest-asyncio** - For async Qdrant tests
5. **Prometheus client library** - For metrics exposure

### Risks to Plan

- **Risk**: CI runner resource limits prevent Docker E2E
  - **Impact**: E2E tests cannot run in CI
  - **Contingency**: Use self-hosted runners or scheduled E2E runs

- **Risk**: LiteLLM proxy unavailable for model testing
  - **Impact**: Model validation tests fail
  - **Contingency**: Mock LiteLLM responses for unit tests

- **Risk**: Async Qdrant migration more complex than estimated
  - **Impact**: Story 7-7 extends timeline
  - **Contingency**: Feature flag allows gradual rollout

---

## Validation Checklist

After completing all steps, verify:

- [x] Risk assessment complete with all categories
- [x] All risks scored (probability × impact)
- [x] High-priority risks (≥6) flagged with mitigation plans
- [x] Coverage matrix maps requirements to test levels
- [x] Priority levels assigned (P0-P3)
- [x] Execution order defined
- [x] Resource estimates provided
- [x] Quality gate criteria defined
- [x] Test scenarios detailed for P0 stories
- [x] Output file created and formatted correctly

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: __________ Date: __________
- [ ] Tech Lead: __________ Date: __________
- [ ] QA Lead: __________ Date: __________

**Comments:**

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework (6 categories, scoring, gates)
- `probability-impact.md` - Risk scoring methodology (1-9 scale, thresholds)
- `test-levels-framework.md` - Test level selection (E2E, API, Component, Unit)
- `test-priorities-matrix.md` - P0-P3 prioritization (risk-based mapping)

### Related Documents

- **PRD**: [docs/prd.md](./prd.md) - FR78-FR86 (Epic 7)
- **Epic**: [docs/epics.md](./epics.md) - Epic 7 section
- **Architecture**: [docs/architecture.md](./architecture.md) - LiteLLM, Model Registry
- **Sprint Status**: [docs/sprint-artifacts/sprint-status.yaml](sprint-artifacts/sprint-status.yaml)

### Story References

- [Story 7-1](sprint-artifacts/7-1-docker-e2e-infrastructure.md) - Docker E2E
- [Story 7-2](sprint-artifacts/7-2-centralized-llm-configuration.md) - LLM Config
- [Story 7-3](sprint-artifacts/7-3-ci-cd-pipeline-setup.md) - CI/CD
- [Story 7-9](sprint-artifacts/7-9-llm-model-registry.md) - Model Registry
- [Story 7-10](sprint-artifacts/7-10-kb-model-configuration.md) - KB Model Config

---

**Generated by**: Murat (TEA - Master Test Architect)
**Workflow**: `.bmad/bmm/workflows/testarch/test-design`
**Version**: 1.0 (BMad v6)
**Date**: 2025-12-08
