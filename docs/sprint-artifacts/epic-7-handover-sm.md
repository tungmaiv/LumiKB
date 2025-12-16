# Epic 7 Creation Handover - SM Agent

> **STATUS: COMPLETED** - 2025-12-08
>
> All items in this handover have been processed by the SM Agent (Bob).
> This document is now historical reference only.
>
> **Actions Completed:**
> - Epic 7 added to `docs/epics.md` with 10 stories (7-1 through 7-10)
> - Epic 7 added to `docs/sprint-artifacts/sprint-status.yaml`
> - Story 5-16 renamed to 7-1 (`7-1-docker-e2e-infrastructure.md`)
> - Story files created for 7-2 through 7-10
> - Tech debt migrated from `epic-5-tech-debt.md` (TD-5.15-1, TD-5.26-1, TD-scroll-1)
> - **Additional stories added:** 7-9 (LLM Model Registry) and 7-10 (KB Model Configuration)

**Date:** 2025-12-08
**From:** Development Team
**To:** SM Agent (Bob)
**Purpose:** Create Epic 7 and migrate stories from Epic 5

---

## Summary

Epic 5 (Administration & Polish) has grown to 26 stories and is too large for effective management. This handover requests the creation of **Epic 7: Infrastructure & DevOps** to properly scope infrastructure-focused work.

Additionally, a comprehensive scan of all pending technical debt has been completed and is included below for consolidation into Epic 7.

---

## Requested Actions

### 1. Create Epic 7: Infrastructure & DevOps

**Epic Theme:** DevOps infrastructure, testing automation, centralized configuration, and deployment tooling.

**Epic Description:**
Infrastructure and DevOps improvements that support the application but are not user-facing features. This includes testing infrastructure, configuration management, CI/CD pipelines, and deployment automation.

---

### 2. Stories to Move from Epic 5 to Epic 7

| Current ID | Story Title | Status | Rename To |
|------------|-------------|--------|-----------|
| 5-16 | Docker E2E Testing Infrastructure | backlog | 7-1 |

---

### 3. New Stories to Add to Epic 7

| New ID | Story Title | Description | Priority |
|--------|-------------|-------------|----------|
| 7-2 | Centralized LLM Configuration | Document and formalize the centralized model configuration pattern implemented for LiteLLM. Create admin UI for model switching. | MEDIUM |
| 7-3 | CI/CD Pipeline Setup | GitHub Actions workflow for automated testing, linting, and deployment | HIGH |
| 7-4 | Production Deployment Configuration | Kubernetes manifests, Helm charts, or production docker-compose | MEDIUM |
| 7-5 | Monitoring & Observability | Prometheus metrics, Grafana dashboards, alerting | LOW |
| 7-6 | Backend Unit Test Fixes (TD-5.15-1) | Fix 26 failing unit tests due to service constructor DI changes | HIGH |
| 7-7 | Async Qdrant Client Migration (TD-5.26-1) | Migrate to async Qdrant client to fix event loop blocking | MEDIUM-HIGH |
| 7-8 | UI Scroll Isolation Fix | Fix split-pane scroll isolation in Document Chunk Viewer | MEDIUM |

---

## Context for Story 7-2: Centralized LLM Configuration

### Current Implementation

The centralized LLM configuration pattern was recently implemented:

**Files Modified:**
1. `backend/app/core/config.py` - Settings for `llm_model` and `embedding_model`
2. `infrastructure/docker/litellm_config.yaml` - Model aliases (default, embedding, ollama-embedding)
3. `infrastructure/docker/Dockerfile.litellm` - Bakes config into Docker image
4. `infrastructure/docker/docker-compose.yml` - Uses build instead of pre-built image

**Current Default Models:**
- Generation: `ollama/gemma3:4b` (local Ollama)
- Embedding: `nomic-embed-text` via `ollama-embedding` alias (768 dimensions)

**Documentation Already Updated:**
- `docs/architecture.md` - LLM Model Configuration section (lines 282-405)
- `docs/prd.md` - Integration Requirements table
- `docs/00-index.md` - Technical Stack section

**Story 7-2 Should Cover:**
- Admin UI for switching between model providers
- API endpoint for updating model configuration
- Validation of model compatibility (embedding dimensions)
- Hot-reload capability without service restart

---

## Context for Story 7-1: Docker E2E Testing Infrastructure

This story already has a complete specification at:
`docs/sprint-artifacts/5-16-docker-e2e-infrastructure.md`

Key requirements:
- `docker-compose.e2e.yml` with all services
- Playwright configuration for full-stack testing
- Database seeding for E2E tests
- GitHub Actions CI integration
- 15-20 E2E tests for Epic 3 & 4 features

---

## Files to Update

After Epic 7 creation:

1. **`docs/sprint-artifacts/sprint-status.yaml`**
   - Add Epic 7 section
   - Move 5-16 to 7-1
   - Add new stories 7-2 through 7-5

2. **`docs/epics.md`**
   - Add Epic 7: Infrastructure & DevOps

3. **`docs/sprint-artifacts/5-16-docker-e2e-infrastructure.md`**
   - Rename to `7-1-docker-e2e-infrastructure.md`
   - Update Epic reference in header

4. **Create `docs/sprint-artifacts/tech-spec-epic-7.md`**
   - Technical specification for Epic 7

---

## Suggested Epic 7 Structure

```yaml
# Epic 7: Infrastructure & DevOps (5 stories)
epic-7: backlog
7-1-docker-e2e-infrastructure: backlog  # Moved from 5-16
7-2-centralized-llm-configuration: backlog
7-3-ci-cd-pipeline-setup: backlog
7-4-production-deployment-configuration: backlog
7-5-monitoring-and-observability: backlog
epic-7-retrospective: optional
```

---

## Notes

- Epic 5 will decrease from 26 stories to 25 stories after moving 5-16
- Epic 6 (Document Lifecycle Management) is already complete with 9 stories
- Epic 7 focuses on non-user-facing infrastructure
- Stories 7-3 through 7-5 are suggestions; SM should validate with stakeholders

---

## Approval Required

Please confirm:
1. Epic 7 creation with proposed name and scope
2. Story migration (5-16 -> 7-1)
3. New stories to include in Epic 7

---

---

## Comprehensive Technical Debt Inventory

A full scan of all tech debt files was completed on 2025-12-08. Below is the consolidated inventory.

### Source Files Scanned

| File | Status |
|------|--------|
| `docs/sprint-artifacts/epic-3-tech-debt.md` | 3 items (mostly resolved in 5.11) |
| `docs/sprint-artifacts/epic-4-tech-debt.md` | 19 items (most resolved in 5.15) |
| `docs/sprint-artifacts/epic-5-tech-debt.md` | 2 items (pending) |
| `docs/sprint-artifacts/tech-debt-backend-unit-tests.md` | 1 item (pending) |
| `docs/sprint-artifacts/tech-debt-document-processing.md` | ✅ RESOLVED |
| `docs/sprint-artifacts/tech-debt-scroll-isolation.md` | 1 item (pending) |

---

### HIGH Priority Items (Must Fix)

| ID | Description | Effort | Source |
|----|-------------|--------|--------|
| **TD-5.15-1** | 26 backend unit tests failing due to service constructor DI changes. Affects: `test_draft_service.py` (12), `test_search_service.py` (8), `test_generation_service.py` (5), `test_explanation_service.py` (1) | 8h | Epic 5 |
| **TD-4.2-1** | SSE reconnection for streaming (EventSource retry on disconnect) | 4h | Epic 4 |

---

### MEDIUM-HIGH Priority Items

| ID | Description | Effort | Source |
|----|-------------|--------|--------|
| **TD-5.26-1** | Sync Qdrant client blocking async event loop. Need to migrate to `AsyncQdrantClient`. Causes 100-500ms blocking during vector operations. | 16h | Epic 5 |

---

### MEDIUM Priority Items

| ID | Description | Effort | Source |
|----|-------------|--------|--------|
| **TD-scroll-1** | Split-pane scroll isolation in Document Chunk Viewer. Scrolling one panel affects the other. Multiple solutions attempted without success. | 8h | Scroll Isolation |
| **TD-4.5-1** | Confidence scoring for search results (based on vector similarity thresholds) | 8h | Epic 4 |
| **TD-4.7-5** | PDF export quality (fonts, images, layout) | 8h | Epic 4 |
| **TD-4.6-7** | Draft auto-save with debouncing | 4h | Epic 4 |
| **TD-4.8-2** | Feedback analytics dashboard for admins | 8h | Epic 4 |
| **TD-4.9-3** | Template versioning and migration | 8h | Epic 4 |
| **TD-3.8-5** | Citation hover preview cards | 4h | Epic 3 |
| **TD-3.10-1** | Enhanced similarity search filters (file type, date range) | 6h | Epic 3 |

---

### LOW Priority Items (Nice to Have)

| ID | Description | Effort | Source |
|----|-------------|--------|--------|
| **TD-4.3-3** | Conversation export (save chat history) | 4h | Epic 4 |
| **TD-4.4-3** | Generation progress estimation (time remaining) | 4h | Epic 4 |
| **TD-4.5-4** | Custom confidence thresholds per KB | 4h | Epic 4 |
| **TD-4.6-8** | Collaborative editing indicators | 8h | Epic 4 |
| **TD-4.7-6** | LaTeX/Math rendering in exports | 6h | Epic 4 |
| **TD-4.8-3** | Feedback ML model training pipeline | 16h | Epic 4 |
| **TD-4.9-4** | User-created custom templates | 8h | Epic 4 |
| **TD-4.10-3** | Audit log retention policies | 4h | Epic 4 |
| **TD-3.8-4** | Search result clustering/grouping | 8h | Epic 3 |

---

### Resolved Items (For Reference)

| ID | Resolution | Date |
|----|------------|------|
| TD-document-processing-1 | PostgreSQL connection pool fixed | Story 5.12 |
| TD-document-processing-2 | Duplicate document handling resolved | Story 5.12 |
| TD-document-processing-3 | Stuck processing status fixed | Story 5.12 |
| TD-4.1-1 through TD-4.1-4 | Resolved in Story 5.15 | Nov 2025 |
| TD-4.3-1, TD-4.3-2 | Resolved in Story 5.15 | Nov 2025 |
| TD-3.8-1, TD-3.8-2, TD-3.8-3 | Resolved in Story 5.11 | Nov 2025 |

---

### Summary Metrics

| Category | Count | Est. Hours |
|----------|-------|------------|
| HIGH Priority | 2 | 12h |
| MEDIUM-HIGH Priority | 1 | 16h |
| MEDIUM Priority | 9 | ~62h |
| LOW Priority | 9 | ~62h |
| **TOTAL PENDING** | **21** | **~152h** |

---

### Recommended Story Assignments

| Story | Tech Debt IDs | Priority |
|-------|---------------|----------|
| 7-6 | TD-5.15-1 | HIGH - Required for test reliability |
| 7-7 | TD-5.26-1 | MEDIUM-HIGH - Performance improvement |
| 7-8 | TD-scroll-1 | MEDIUM - UX improvement |
| Future | TD-4.5-1, TD-4.7-5, TD-4.8-2 | MEDIUM - Feature enhancements |
| Future | All LOW items | LOW - Nice-to-have improvements |

---

## Updated Epic 7 Structure

```yaml
# Epic 7: Infrastructure & DevOps (8 stories)
epic-7: backlog
7-1-docker-e2e-infrastructure: backlog  # Moved from 5-16
7-2-centralized-llm-configuration: backlog
7-3-ci-cd-pipeline-setup: backlog
7-4-production-deployment-configuration: backlog
7-5-monitoring-and-observability: backlog
7-6-backend-unit-test-fixes: backlog  # TD-5.15-1
7-7-async-qdrant-migration: backlog   # TD-5.26-1
7-8-ui-scroll-isolation-fix: backlog  # TD-scroll-1
epic-7-retrospective: optional
```

---

*Generated by Development Team for SM handover*
