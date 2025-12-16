# Story 7-1: Docker E2E Infrastructure

**Epic:** Epic 7 - Infrastructure & DevOps
**Story ID:** 7-1
**Priority:** HIGH
**Estimated Effort:** 1-1.5 days
**Owner:** Murat (TEA)
**Support:** Winston (Architect), Amelia (Dev)
**Status:** done

---

## Overview

This story establishes the Docker infrastructure foundation for E2E testing. It creates `docker-compose.e2e.yml` with all services and implements database seeding for consistent test data.

**Note:** This story was split from the original scope. E2E test automation (Playwright Docker config, GitHub Actions, test execution) has been moved to **Story 8-16: E2E Test Automation** at the end of Epic 8.

**Scope:**
- ✅ Docker Compose E2E environment with all 8 services
- ✅ Service health checks and dependencies
- ✅ E2E database seeding script
- ✅ Basic infrastructure verification

**Deferred to Story 8-16:**
- Playwright Docker configuration
- GitHub Actions E2E workflow
- E2E test execution (Epic 3-8 features)

**Gap Identified:**
- ✅ Unit tests: Excellent coverage (29 backend, 51 frontend component, 34 frontend hook)
- ✅ Integration tests: Good coverage (74 backend API tests)
- ✅ E2E tests: 62 tests written, awaiting Docker infrastructure

**Solution:** Create `docker-compose.e2e.yml` with all services (frontend, backend, Celery, PostgreSQL, Redis, Qdrant, MinIO, LiteLLM) and implement idempotent database seeding.

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

### AC2: E2E Test Database Seeding Implemented
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

### AC3: Infrastructure Verification
**Given** docker-compose.e2e.yml is configured
**When** `docker-compose -f docker-compose.e2e.yml up -d` is executed
**Then** all services start and reach healthy status within 90 seconds
**And** services can communicate across the e2e-network
**And** frontend can reach backend API at http://backend:8000
**And** backend can connect to all dependent services (postgres, redis, qdrant, minio)

**Technical Requirements:**
- All 8 services must have healthchecks defined
- Frontend builds and serves production Next.js app
- Backend API responds to /health endpoint
- Service connectivity can be verified via curl commands

### AC4: Local Developer Experience
**Given** a developer wants to run E2E tests locally
**When** they execute `docker-compose -f docker-compose.e2e.yml up -d`
**Then** the environment starts without manual configuration
**And** environment variables are pre-configured for E2E mode
**And** seeding can be run via `docker-compose exec backend python seed_e2e.py`

**Note:** Playwright Docker configuration, GitHub Actions workflow, and E2E test execution have been moved to Story 8-16: E2E Test Automation.

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

- ✅ `docker-compose.e2e.yml` created with all 8 services
- ✅ All services start successfully and reach healthy status
- ✅ Service healthchecks configured (depends_on with condition)
- ✅ e2e-network bridge enables inter-service communication
- ✅ Database seeding script created and idempotent
- ✅ Test users, KBs, documents seeded in PostgreSQL, Qdrant, MinIO
- ✅ Environment variables pre-configured for E2E mode
- ✅ Documentation: E2E Infrastructure Setup Guide

**Deferred to Story 8-16:**
- Playwright Docker configuration
- GitHub Actions E2E workflow
- E2E test execution and artifacts

---

## Estimated Effort

**1-1.5 days** (6-10 hours of focused work)

**Breakdown:**
- Docker Compose E2E file creation: 3-4 hours
- Database seeding implementation: 2-3 hours
- Infrastructure verification: 1-2 hours
- Documentation: 1 hour

**Risk Factors:**
- Service networking issues in Docker may require debugging
- Database seeding complexity depends on data requirements
- Health check timing may need tuning

---

## E2E Test Coverage

**Note:** E2E test execution is deferred to Story 8-16. This story focuses only on infrastructure.

62 E2E tests already exist in `frontend/e2e/tests/` covering:
- Epic 3: Search, citations, command palette
- Epic 4: Chat, streaming, generation, templates, export
- Epic 5: Admin dashboard, onboarding
- Epic 6: Document lifecycle, archive management

These tests will be executed against the Docker infrastructure in Story 8-16.

---

## Success Criteria

**Story 7-1 is complete when:**

1. Docker E2E environment runs successfully with all 8 services
2. All services reach healthy status within 90 seconds
3. Database seeding provides consistent test data
4. Services can communicate across e2e-network
5. E2E Infrastructure Setup Guide documentation created

**Impact:** This story provides the Docker foundation for E2E testing. Story 8-16 will build on this infrastructure to execute tests across all epics.

**Related Story:** Story 8-16: E2E Test Automation (depends on this story)

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
- Story 5-0: Epic 3 & 4 Integration Completion (prerequisite)
- Story 5-15: Epic 4 ATDD Transition to GREEN (integration tests)

**Related Documentation:**
- [Epic 5 Tech Debt](./epic-5-tech-debt.md) - E2E test items
- [Test Design Epic 4](test-design-epic-4.md) - Test strategy

**Playwright Documentation:**
- https://playwright.dev/docs/docker
- https://playwright.dev/docs/ci

**Docker Compose Documentation:**
- https://docs.docker.com/compose/compose-file/
- https://docs.docker.com/compose/networking/

---

**Created:** 2025-11-30
**Last Updated:** 2025-12-08
**Migrated From:** Story 5-16 (Epic 5)
**Split:** Original Story 7-1 split into 7-1 (Docker infra) + 8-16 (E2E automation)
**Previous Story:** Story 5-0 (Epic Integration Completion) - Prerequisite
**Next Story:** Story 7-2 (Centralized LLM Configuration)
**Related Story:** Story 8-16 (E2E Test Automation) - Uses infrastructure from this story

---

## Dev Agent Record

### Context Reference

- [7-1-docker-e2e-infrastructure.context.xml](./7-1-docker-e2e-infrastructure.context.xml)

### Agent Model Used

Claude claude-opus-4-5-20251101 (Scrum Master Agent)

### Debug Log References

### Completion Notes List

1. **AC1: Docker Compose E2E Environment Created** - COMPLETED
   - Created `docker-compose.e2e.yml` with all 8 services
   - Services: frontend, backend, celery-worker, postgres, redis, qdrant, minio, litellm
   - All services have health checks defined
   - Service dependencies configured with `depends_on` conditions
   - E2E-specific ports to avoid conflicts with dev environment (5433, 6380, 6334, 9002/9003, 4001)
   - No volumes for ephemeral test data
   - **Ollama Configuration (2025-12-10):** Ollama runs on host machine with GPU support (Docker Desktop doesn't support GPU passthrough). LiteLLM connects via `host.docker.internal:host-gateway`. Start Ollama on host before running E2E tests: `ollama serve`

2. **AC2: E2E Test Database Seeding Implemented** - COMPLETED
   - Created `backend/seed_e2e.py` with idempotent seeding
   - Test users: admin@e2e-test.com (admin), user@e2e-test.com, user2@e2e-test.com
   - Test KBs: 3 knowledge bases for document, search, and permission testing
   - Test documents: 3 markdown documents with architecture, user guide, and API reference content
   - Permissions: Various permission levels (READ, WRITE, ADMIN) across users and KBs
   - Qdrant collections created with mock vectors for search testing
   - MinIO buckets created with test documents

3. **AC3: Infrastructure Verification** - COMPLETED
   - All services configured with health checks
   - Service startup order managed via depends_on conditions
   - Network: e2e-network bridge for inter-service communication
   - Environment variables pre-configured for E2E mode

4. **AC4: Local Developer Experience** - COMPLETED
   - Simple startup: `docker-compose -f docker-compose.e2e.yml up -d`
   - Seeding: `docker-compose -f docker-compose.e2e.yml exec backend python seed_e2e.py`
   - No manual configuration required
   - Test credentials documented in seed script output

### File List

- `docker-compose.e2e.yml` - E2E Docker Compose configuration
- `frontend/Dockerfile.e2e` - Frontend production build Dockerfile
- `frontend/next.config.ts` - Modified to add `output: 'standalone'`
- `backend/seed_e2e.py` - E2E database seeding script

### Ollama Configuration Update (2025-12-10)

**Issue:** Docker Desktop on Linux does not support GPU passthrough, causing Ollama container to fail with:
```
could not select device driver "nvidia" with capabilities: [[gpu]]
```

**Solution:** Run Ollama on host machine and configure Docker containers to access it via `host.docker.internal`:

1. **Development (`infrastructure/docker/docker-compose.yml`):**
   - Removed Ollama Docker service
   - Added `extra_hosts: ["host.docker.internal:host-gateway"]` to LiteLLM
   - Changed `OLLAMA_API_BASE` from `http://ollama:11434` to `http://host.docker.internal:11434`

2. **E2E (`docker-compose.e2e.yml`):**
   - Same configuration as development
   - LiteLLM connects to host Ollama via `host.docker.internal`

3. **Production (`infrastructure/docker/docker-compose.prod.yml`):**
   - **Retained Ollama Docker service with GPU support** - Production servers use standard Docker (not Docker Desktop) with nvidia-container-toolkit which supports GPU passthrough
   - LiteLLM uses `http://ollama:11434` (container-to-container)

**Prerequisites for Development/E2E:**
```bash
# Start Ollama on host
ollama serve

# Pull required models
ollama pull nomic-embed-text  # For embeddings
ollama pull gemma3:4b         # Default generation model
```
