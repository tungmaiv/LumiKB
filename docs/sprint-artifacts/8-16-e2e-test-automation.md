# Story 8-16: E2E Test Automation

**Epic:** Epic 8 - GraphRAG Integration
**Story ID:** 8-16
**Priority:** HIGH
**Estimated Effort:** 1.5-2 days
**Owner:** Murat (TEA)
**Support:** Winston (Architect), Amelia (Dev)
**Status:** backlog

---

## Overview

This story implements E2E test automation on top of the Docker infrastructure established in Story 7-1. It configures Playwright for Docker execution, creates GitHub Actions workflow, and executes the comprehensive E2E test suite covering all epics (3-8).

**Origin:** Split from Story 7-1 (Docker E2E Testing Infrastructure). The infrastructure foundation (docker-compose.e2e.yml, seeding) was kept in Story 7-1, while test automation moved here to be executed at the end of Epic 8 when all features are complete.

**Dependencies:**
- Story 7-1: Docker E2E Infrastructure (provides docker-compose.e2e.yml, seeding)
- Epic 8 Stories: 8-1 through 8-15 (GraphRAG features to be tested)

**Scope:**
- ✅ Playwright Docker configuration
- ✅ `playwright.config.e2e.ts` for Docker environment
- ✅ GitHub Actions E2E workflow
- ✅ E2E test execution covering Epic 3-8 features
- ✅ 20+ E2E tests with comprehensive coverage

---

## Acceptance Criteria

### AC1: Playwright Docker Configuration
**Given** docker-compose.e2e.yml exists (from Story 7-1)
**When** Playwright is configured for Docker execution
**Then** Playwright can connect to frontend:3000 inside Docker network
**And** tests run against the containerized stack
**And** test results are collected in the playwright service

**Technical Requirements:**
- Create `playwright.config.e2e.ts` extending base config
- Configure baseURL from E2E_BASE_URL environment variable
- Add Playwright service to docker-compose.e2e.yml
- Mount volume for test results and artifacts
- Configure single worker for E2E stability

### AC2: Playwright Container Service
**Given** docker-compose.e2e.yml has all application services
**When** a Playwright service is added
**Then** `docker-compose run playwright npm run test:e2e` executes tests
**And** tests access frontend service at http://frontend:3000
**And** test artifacts (screenshots, videos, HTML report) are saved to mounted volumes

**Technical Requirements:**
- Create `frontend/Dockerfile.playwright` for test runner container
- Add npm script: `npm run test:e2e`
- Configure trace, screenshot, video on failure
- Set retries to 2 for CI stability

### AC3: GitHub Actions E2E Workflow
**Given** E2E tests can run in Docker
**When** a pull request is created or pushed to main
**Then** GitHub Actions workflow:
- Builds Docker images
- Starts docker-compose.e2e.yml
- Waits for service health
- Seeds database
- Runs Playwright E2E tests
- Uploads artifacts (screenshots, videos, HTML report)
- Tears down environment

**Technical Requirements:**
- Create `.github/workflows/e2e-tests.yml`
- Set 20-minute workflow timeout
- Upload test artifacts on both success and failure
- Report test results in PR comments (optional)

### AC4: E2E Test Suite Execution
**Given** Playwright is configured and GitHub Actions workflow exists
**When** E2E tests execute
**Then** the following test suites pass:

**Epic 3 Tests (Search & Citations):**
- Search returns results with citations
- Citation panel displays source excerpts
- Confidence scoring works
- Command palette search works

**Epic 4 Tests (Chat & Generation):**
- Chat conversation with multi-turn context
- Chat streaming displays real-time tokens
- Document generation with template selection
- Draft editing and export to DOCX/PDF/MD
- Feedback and recovery flow

**Epic 5 Tests (Administration):**
- Admin dashboard metrics
- Audit log viewer
- User management
- System configuration

**Epic 6 Tests (Document Lifecycle):**
- Archive and restore documents
- Purge archived documents
- Duplicate detection on upload

**Epic 7 Tests (Infrastructure):**
- LLM model configuration

**Epic 8 Tests (GraphRAG):**
- Domain management
- Entity extraction visualization
- Graph-augmented search results

**Technical Requirements:**
- Target 20+ E2E tests covering critical user journeys
- Use existing 62 E2E tests as baseline
- Add missing tests for Epic 7 and 8 features
- Document any test failures and create follow-up issues

### AC5: Test Coverage Documentation
**Given** E2E tests execute successfully
**When** the test suite completes
**Then** documentation includes:
- E2E Test Execution Guide
- Test coverage matrix by epic
- Instructions for running locally
- Instructions for debugging failures

---

## Technical Notes

### Playwright E2E Configuration

**File:** `frontend/playwright.config.e2e.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false, // Run serially for E2E stability
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker for E2E
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // No webServer - services run in Docker
});
```

### Playwright Dockerfile

**File:** `frontend/Dockerfile.playwright`

```dockerfile
FROM mcr.microsoft.com/playwright:v1.40.0-jammy

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy test files
COPY e2e/ ./e2e/
COPY playwright.config.e2e.ts ./

# Install Playwright browsers
RUN npx playwright install chromium

# Run tests
CMD ["npm", "run", "test:e2e"]
```

### Docker Compose Playwright Service

**Add to:** `docker-compose.e2e.yml`

```yaml
  playwright:
    build:
      context: ./frontend
      dockerfile: Dockerfile.playwright
    depends_on:
      frontend:
        condition: service_healthy
      backend:
        condition: service_healthy
    environment:
      - E2E_BASE_URL=http://frontend:3000
      - E2E_API_URL=http://backend:8000
      - TEST_USER_EMAIL=admin@test.com
      - TEST_USER_PASSWORD=test_password_123
    volumes:
      - ./frontend/playwright-report:/app/playwright-report
      - ./frontend/test-results:/app/test-results
    networks:
      - e2e-network
```

### GitHub Actions Workflow

**File:** `.github/workflows/e2e-tests.yml`

```yaml
name: E2E Tests

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker images
        run: docker-compose -f docker-compose.e2e.yml build

      - name: Start E2E environment
        run: docker-compose -f docker-compose.e2e.yml up -d

      - name: Wait for services
        run: |
          echo "Waiting for services to be healthy..."
          timeout 120 bash -c 'until docker-compose -f docker-compose.e2e.yml ps | grep -q "healthy"; do sleep 5; done'

      - name: Seed E2E database
        run: docker-compose -f docker-compose.e2e.yml exec -T backend python seed_e2e.py

      - name: Run Playwright E2E tests
        run: docker-compose -f docker-compose.e2e.yml run playwright

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-test-results
          path: frontend/test-results/
          retention-days: 30

      - name: Tear down environment
        if: always()
        run: docker-compose -f docker-compose.e2e.yml down -v
```

---

## E2E Test Coverage Matrix

| Epic | Feature Area | Test Count | Status |
|------|--------------|------------|--------|
| Epic 3 | Search & Citations | 12 | Existing |
| Epic 4 | Chat & Generation | 18 | Existing |
| Epic 5 | Administration | 15 | Existing |
| Epic 6 | Document Lifecycle | 9 | Existing |
| Epic 7 | Infrastructure | 4 | To Create |
| Epic 8 | GraphRAG | 4 | To Create |
| **Total** | | **62+** | |

### Existing E2E Tests (62)

Located in `frontend/e2e/tests/`:
- `chat/` - Chat conversation, streaming, management
- `export/` - Document export (DOCX, PDF, MD)
- `generation/` - Template selection, draft streaming
- `documents/` - Tags, processing, archive
- `admin/` - Dashboard, users, groups
- `onboarding/` - Wizard flow
- `smoke/` - Integration journeys

### New E2E Tests to Create

**Epic 7 (4 tests):**
1. LLM model configuration - Admin can add/configure models
2. LLM model health check - Status indicators work
3. Model selection per KB - KB uses selected model
4. Model hot-reload - Configuration changes apply

**Epic 8 (4 tests):**
1. Domain creation wizard - Create domain schema
2. Entity extraction visualization - View extracted entities
3. Graph-augmented search - Results include graph context
4. Domain linking to KB - Associate domain with KB

---

## Prerequisites and Dependencies

**Prerequisites:**
- Story 7-1 completed (docker-compose.e2e.yml, seeding script)
- Epic 8 Stories 8-1 through 8-15 completed (GraphRAG features)
- Docker and Docker Compose available in CI

**Dependencies:**
- `docker-compose.e2e.yml` (from Story 7-1)
- `backend/seed_e2e.py` (from Story 7-1)
- E2E network configuration (from Story 7-1)

**Blockers:**
- Cannot execute until Story 7-1 infrastructure is complete
- Epic 8 tests cannot be written until 8-1 through 8-15 are implemented

---

## Definition of Done

- ✅ `playwright.config.e2e.ts` created for Docker environment
- ✅ `frontend/Dockerfile.playwright` builds successfully
- ✅ Playwright service added to docker-compose.e2e.yml
- ✅ `npm run test:e2e` executes tests in Docker
- ✅ GitHub Actions workflow created and triggers on PR/push
- ✅ All existing 62 E2E tests pass
- ✅ 8 new E2E tests created (4 Epic 7, 4 Epic 8)
- ✅ Test artifacts uploaded on every CI run
- ✅ E2E Test Execution Guide documentation created

---

## Estimated Effort

**1.5-2 days** (10-14 hours of focused work)

**Breakdown:**
- Playwright Docker configuration: 2-3 hours
- Playwright Dockerfile: 1-2 hours
- GitHub Actions workflow: 2-3 hours
- Epic 7 E2E tests: 2 hours
- Epic 8 E2E tests: 2 hours
- Documentation: 1-2 hours

**Risk Factors:**
- Playwright flakiness may require retries and stability improvements
- CI/CD integration may require multiple iterations
- Epic 8 feature complexity may affect test creation

---

## Success Criteria

**Story 8-16 is complete when:**

1. Playwright executes E2E tests against Docker environment
2. GitHub Actions CI runs E2E tests on every PR
3. All 70+ E2E tests pass (62 existing + 8 new)
4. Test artifacts generated and uploaded
5. E2E Test Execution Guide documentation created

**Impact:** This story completes the test pyramid for all epics (3-8), enabling confident deployment with full integration testing coverage.

---

## References

**Related Stories:**
- Story 7-1: Docker E2E Infrastructure (prerequisite)
- Story 5-16: Original E2E story (migrated/split)

**Related Documentation:**
- [Epic 7 Tech Spec](./tech-spec-epic-7.md)
- [Epic 8 Tech Spec](./tech-spec-epic-8.md)
- [Epic 4 Retrospective](./epic-4-retrospective-2025-11-30.md) - Identified E2E gap

**Playwright Documentation:**
- https://playwright.dev/docs/docker
- https://playwright.dev/docs/ci-intro

---

**Created:** 2025-12-08
**Origin:** Split from Story 7-1 (Docker E2E Testing Infrastructure)
**Previous Story:** Story 8-15 (Batch Reprocessing Worker)
**Depends On:** Story 7-1 (Docker E2E Infrastructure)

---

## Dev Agent Record

### Context Reference

- Context XML to be generated when story is drafted

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
