# Story 5-16: Docker E2E Testing Infrastructure

**Epic:** Epic 5 - Administration & Polish
**Story ID:** 5-16
**Priority:** HIGH
**Estimated Effort:** 2-3 days
**Owner:** Murat (TEA)
**Support:** Winston (Architect), Amelia (Dev)
**Status:** TODO

---

## Overview

Epic 4 retrospective revealed that while component and integration tests provide excellent coverage (220+ tests), the test pyramid is incomplete without E2E testing. This story establishes a Docker-based E2E testing infrastructure that validates complete user journeys in a production-like environment.

**Gap Identified:**
- ✅ Unit tests: Excellent coverage (29 backend, 51 frontend component, 34 frontend hook)
- ✅ Integration tests: Good coverage (74 backend API tests)
- ❌ E2E tests: Written but not executed (8 E2E tests exist but no infrastructure to run them)

**Solution:** Create `docker-compose.e2e.yml` with all services (frontend, backend, Celery, PostgreSQL, Redis, Qdrant, MinIO, LiteLLM) and configure Playwright for full-stack testing.

---

## Acceptance Criteria

### AC1: Docker Compose E2E Environment Created
**Given** the application requires multiple services for E2E testing
**When** `docker-compose -f docker-compose.e2e.yml up` is executed
**Then** all required services start successfully:
- ✅ Frontend (Next.js production build on port 3000)
- ✅ Backend (FastAPI on port 8000)
- ✅ Celery Worker (background task processing)
- ✅ PostgreSQL (test database)
- ✅ Redis (session and chat storage)
- ✅ Qdrant (vector search)
- ✅ MinIO (document storage)
- ✅ LiteLLM Proxy (LLM API)
**And** all services are accessible from the Playwright container
**And** environment variables are configured for E2E testing

**Technical Requirements:**
- Create `docker-compose.e2e.yml` in project root
- Configure service dependencies (depends_on with health checks)
- Set environment variables for E2E mode (test database, API URLs)
- Ensure frontend uses `NEXT_PUBLIC_API_URL=http://backend:8000`
- Ensure backend connects to correct service URLs (Qdrant, Redis, MinIO, etc.)

### AC2: Playwright E2E Test Execution Configured
**Given** Playwright tests exist in `frontend/e2e/tests/`
**When** E2E tests are executed with `npm run test:e2e` (or equivalent)
**Then** Playwright runs tests against the Docker environment
**And** tests can navigate to `http://frontend:3000` (or localhost:3000)
**And** tests can interact with all services through the frontend
**And** test results are reported with pass/fail status

**Technical Requirements:**
- Configure Playwright to use Docker environment URLs
- Add `playwright.config.e2e.ts` or extend existing config
- Create npm script: `npm run test:e2e`
- Ensure Playwright can access frontend service (network configuration)
- Add test database seeding for consistent test data

### AC3: E2E Test Database Seeding Implemented
**Given** E2E tests require consistent test data
**When** the E2E environment starts
**Then** the test database is seeded with:
- ✅ Test users (admin, regular user)
- ✅ Test knowledge bases with permissions
- ✅ Indexed test documents (for search/chat tests)
- ✅ Redis conversation data (if needed)
**And** seeding is idempotent (can run multiple times without errors)

**Technical Requirements:**
- Create `scripts/seed-e2e-db.sh` or `backend/seed_e2e.py`
- Run seeding as part of docker-compose startup (depends_on or init script)
- Use Alembic migrations + seed data script
- Ensure Qdrant collections are created and populated
- Ensure MinIO buckets are created with test documents

### AC4: GitHub Actions CI Integration Configured
**Given** E2E tests should run in CI/CD pipeline
**When** a pull request is created or pushed to main
**Then** GitHub Actions workflow runs E2E tests
**And** workflow uses `docker-compose.e2e.yml` to spin up environment
**And** workflow reports test results and uploads artifacts (screenshots, videos)
**And** workflow fails if any E2E tests fail

**Technical Requirements:**
- Create `.github/workflows/e2e-tests.yml` workflow file
- Configure workflow to:
  - Build Docker images for frontend and backend
  - Run `docker-compose -f docker-compose.e2e.yml up -d`
  - Wait for services to be healthy
  - Execute Playwright E2E tests
  - Upload test artifacts (screenshots, videos, HTML report)
  - Tear down Docker environment
- Set reasonable timeout (15-20 minutes for full E2E suite)

### AC5: E2E Test Suite for Epic 3 & 4 Features Executed
**Given** Epic 3 & 4 features are now accessible (Story 5.0 completed)
**When** E2E tests run in Docker environment
**Then** the following test suites execute successfully:

**Epic 3 Tests (Search & Citations):**
- Search returns results with citations
- Citation panel displays source excerpts
- Confidence scoring works
- Command palette search works

**Epic 4 Tests (Chat & Generation):**
- Chat conversation with multi-turn context (Journey 3)
- Chat streaming displays real-time tokens
- Document generation with template selection (Journey 4)
- Draft editing and export to DOCX/PDF/MD
- Feedback and recovery flow

**Technical Requirements:**
- Execute existing E2E tests in `frontend/e2e/tests/`
- Add missing E2E tests for uncovered user journeys
- Aim for 15-20 E2E tests covering critical paths
- Document any test failures and create follow-up issues

---

## Technical Notes

### Docker Compose E2E Architecture

**File:** `docker-compose.e2e.yml`

```yaml
# Placeholder structure for Murat/Winston to expand

version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.e2e
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NODE_ENV=production
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - e2e-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://test_user:test_pass@postgres:5432/test_lumikb
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - MINIO_ENDPOINT=minio:9000
      - LITELLM_BASE_URL=http://litellm:4000
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_started
      minio:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - e2e-network

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://test_user:test_pass@postgres:5432/test_lumikb
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - MINIO_ENDPOINT=minio:9000
    depends_on:
      - postgres
      - redis
      - qdrant
      - minio
    networks:
      - e2e-network

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=test_user
      - POSTGRES_PASSWORD=test_pass
      - POSTGRES_DB=test_lumikb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - e2e-network

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - e2e-network

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    networks:
      - e2e-network

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=test_minio
      - MINIO_ROOT_PASSWORD=test_minio_pass
    networks:
      - e2e-network

  litellm:
    image: ghcr.io/berriai/litellm:latest
    environment:
      - LITELLM_MASTER_KEY=test_litellm_key
    networks:
      - e2e-network

  playwright:
    build:
      context: ./frontend
      dockerfile: Dockerfile.playwright
    command: npm run test:e2e
    depends_on:
      - frontend
      - backend
    environment:
      - E2E_BASE_URL=http://frontend:3000
      - E2E_API_URL=http://backend:8000
    volumes:
      - ./frontend/e2e:/app/e2e
      - ./frontend/playwright-report:/app/playwright-report
      - ./frontend/test-results:/app/test-results
    networks:
      - e2e-network

networks:
  e2e-network:
    driver: bridge
```

### Playwright Configuration

**File:** `frontend/playwright.config.e2e.ts` (or extend `playwright.config.ts`)

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false, // Run serially for E2E stability
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 1, // Single worker for E2E
  reporter: 'html',
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
  webServer: {
    command: 'npm run dev', // Not needed for Docker E2E
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Database Seeding Strategy

**File:** `backend/seed_e2e.py`

```python
# Placeholder structure for Murat to expand

from app.db.session import SessionLocal
from app.models import User, KnowledgeBase, Document
from app.services.search_service import SearchService

def seed_e2e_database():
    db = SessionLocal()
    try:
        # Create test users
        admin_user = User(email="admin@test.com", role="ADMIN", hashed_password="...")
        regular_user = User(email="user@test.com", role="USER", hashed_password="...")
        db.add_all([admin_user, regular_user])
        db.commit()

        # Create test knowledge bases
        kb1 = KnowledgeBase(name="Test KB 1", owner_id=admin_user.id)
        kb2 = KnowledgeBase(name="Test KB 2", owner_id=regular_user.id)
        db.add_all([kb1, kb2])
        db.commit()

        # Create test documents with indexed content
        doc1 = Document(
            kb_id=kb1.id,
            filename="test_doc1.pdf",
            status="COMPLETED",
            # ... metadata
        )
        db.add(doc1)
        db.commit()

        # Index documents in Qdrant
        search_service = SearchService()
        search_service.index_document(doc1.id)

        print("E2E database seeded successfully")
    finally:
        db.close()

if __name__ == "__main__":
    seed_e2e_database()
```

**Execution:** Run as init container or startup script in docker-compose

### GitHub Actions Workflow

**File:** `.github/workflows/e2e-tests.yml`

```yaml
name: E2E Tests

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Build Docker images
        run: docker-compose -f docker-compose.e2e.yml build

      - name: Start E2E environment
        run: docker-compose -f docker-compose.e2e.yml up -d

      - name: Wait for services
        run: |
          docker-compose -f docker-compose.e2e.yml exec -T backend curl -f http://localhost:8000/health
          docker-compose -f docker-compose.e2e.yml exec -T frontend curl -f http://localhost:3000

      - name: Seed E2E database
        run: docker-compose -f docker-compose.e2e.yml exec -T backend python seed_e2e.py

      - name: Run Playwright E2E tests
        run: docker-compose -f docker-compose.e2e.yml run playwright npm run test:e2e

      - name: Upload test artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/

      - name: Tear down environment
        if: always()
        run: docker-compose -f docker-compose.e2e.yml down -v
```

---

## Prerequisites and Dependencies

**Prerequisites:**
- Story 5.0 completed (Epic 3 & 4 features accessible)
- Docker and Docker Compose installed
- Playwright dependencies installed (`npx playwright install --with-deps`)

**Dependencies:**
- Epic 3 & 4 features must be accessible through UI (Story 5.0)
- Backend services must be containerized (Docker images built)
- Frontend must have production build configuration

**Blockers:**
- Story 5.0 must complete first (no point testing features not accessible)

---

## Definition of Done

- ✅ `docker-compose.e2e.yml` created with all services
- ✅ All services start successfully and are healthy
- ✅ Playwright configured to run tests against Docker environment
- ✅ Database seeding script created and functional
- ✅ E2E test suite executes successfully (15-20 tests)
- ✅ GitHub Actions workflow created and passing
- ✅ Test artifacts (screenshots, videos, HTML report) generated
- ✅ Documentation created: E2E Testing Guide

---

## Estimated Effort

**2-3 days** (12-18 hours of focused work)

**Breakdown:**
- Docker Compose E2E file creation: 4-6 hours
- Playwright configuration: 2-3 hours
- Database seeding implementation: 3-4 hours
- GitHub Actions workflow: 2-3 hours
- E2E test execution and debugging: 3-4 hours
- Documentation: 1-2 hours

**Risk Factors:**
- Service networking issues in Docker may require debugging
- Playwright flakiness may require retries and stability improvements
- Database seeding complexity depends on data requirements
- CI/CD integration may require multiple iterations

---

## E2E Test Coverage

### Epic 3 Tests (Search & Citations)

**File:** `frontend/e2e/tests/search/search-flow.spec.ts`

```typescript
test('User can search and view citations', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('text=Search Knowledge Base'); // Navigate to search
  await page.fill('[placeholder="Search..."]', 'test query');
  await page.click('button:has-text("Search")');

  // Verify streaming answer appears
  await expect(page.locator('.search-answer')).toBeVisible();

  // Verify citations display
  await expect(page.locator('.citation-marker')).toHaveCount(2); // [1], [2]

  // Verify citation panel
  await page.click('[data-citation-id="1"]');
  await expect(page.locator('.citation-panel')).toContainText('Source excerpt');
});
```

### Epic 4 Tests (Chat & Generation)

**File:** `frontend/e2e/tests/chat/chat-conversation.spec.ts`

```typescript
test('User can have multi-turn chat conversation', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('text=Chat'); // Navigate to chat

  // Send first message
  await page.fill('[placeholder="Type a message..."]', 'What is LumiKB?');
  await page.click('button:has-text("Send")');

  // Verify streaming response
  await expect(page.locator('.chat-message.assistant')).toBeVisible();

  // Send follow-up message
  await page.fill('[placeholder="Type a message..."]', 'Tell me more');
  await page.click('button:has-text("Send")');

  // Verify second response uses context from first message
  await expect(page.locator('.chat-message.assistant')).toHaveCount(2);
});
```

**File:** `frontend/e2e/tests/generation/template-selection.spec.ts` (already exists)

- 9 existing tests for template selection, preview, context input, generation

### Additional E2E Tests to Create

1. **Document Upload → Processing → Search** (Journey 1)
2. **Search → Citation Display** (Journey 2)
3. **Chat → New Chat → Clear Chat → Undo** (Conversation management)
4. **Generation → Feedback → Alternative Suggestions** (Feedback flow)
5. **Draft Editing → Export → Download** (Export flow)

---

## Success Criteria

**Story 5.16 is complete when:**

1. Docker E2E environment runs successfully with all services
2. Playwright executes E2E tests against Docker environment
3. Database seeding provides consistent test data
4. GitHub Actions CI runs E2E tests on every PR
5. 15-20 E2E tests pass covering Epic 3 & 4 user journeys
6. E2E Testing Guide documentation created

**Impact:** This story completes the test pyramid and enables confident deployment of Epic 3 & 4 features. All future epics will benefit from E2E testing infrastructure.

---

## Notes for Alice/Winston/Murat

**Murat (TEA):**
- This is your primary story to execute
- Start with docker-compose.e2e.yml structure
- Lean on Winston for service configuration guidance
- Document any challenges with Docker networking or service dependencies
- Create E2E Testing Guide for future reference

**Winston (Architect):**
- Review docker-compose.e2e.yml architecture
- Provide guidance on service health checks and dependencies
- Ensure environment variables are correctly configured
- Review database seeding strategy

**Amelia (Dev):**
- Assist with frontend Dockerfile.e2e if needed
- Help debug Playwright test failures
- Provide context on user journeys from Story 5.0 smoke testing

**Alice (PO):**
- Review E2E test coverage - do we have the right user journeys?
- Add any missing critical paths that should be tested end-to-end
- Prioritize E2E test execution order (critical paths first)

---

## Benefits

- ✅ Full-stack integration testing (not just mocks)
- ✅ Consistent environment across dev/CI (Docker)
- ✅ Test against real services (PostgreSQL, Redis, Qdrant, MinIO, LiteLLM)
- ✅ Catch integration issues before production
- ✅ Validate complete user journeys
- ✅ Confidence in deployment readiness
- ✅ Regression prevention for future epics

---

## References

**Related Retrospective:**
- [Epic 4 Retrospective](./epic-4-retrospective-2025-11-30.md) - Identified E2E testing gap

**Related Stories:**
- Story 5.0: Epic 3 & 4 Integration Completion (prerequisite)
- Story 5.15: Epic 4 ATDD Transition to GREEN (integration tests)

**Related Documentation:**
- [Epic 5 Tech Debt](./epic-5-tech-debt.md) - E2E test items
- [Test Design Epic 4](../test-design-epic-4.md) - Test strategy

**Playwright Documentation:**
- https://playwright.dev/docs/docker
- https://playwright.dev/docs/ci

**Docker Compose Documentation:**
- https://docs.docker.com/compose/compose-file/
- https://docs.docker.com/compose/networking/

---

**Created:** 2025-11-30
**Last Updated:** 2025-11-30
**Previous Story:** Story 5.0 (Epic Integration Completion)
**Next Story:** Story 5.15 (Epic 4 ATDD Transition to GREEN)
