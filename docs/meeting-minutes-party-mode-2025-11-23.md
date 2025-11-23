# Party Mode Meeting Minutes

**Project:** LumiKB
**Date:** 2025-11-23
**Facilitator:** John (Product Manager)
**Scribe:** Paige (Technical Writer)

---

## Attendees

| Agent | Role | Participation |
|-------|------|---------------|
| Murat | Master Test Architect | Primary contributor |
| Winston | System Architect | Technical advisor |
| Amelia | Developer Agent | Implementation details |
| John | Product Manager | Process guidance |
| Tung Vu | Project Owner | Decision maker |

---

## Agenda

1. Review Epic 1 completion status and identified gaps
2. Discuss test infrastructure strategy before Epic 2
3. Decide on test database approach
4. Determine next steps and story creation

---

## Discussion Summary

### 1. Epic 1 Status Review

**Finding:** Epic 1 (10 stories) is complete, but docker-compose.yml is missing `backend` and `frontend` service containers. Currently only infrastructure services (PostgreSQL, Redis, MinIO, Qdrant, LiteLLM) are containerized.

**Context:** Story 1.3 focused on infrastructure services only. Backend and frontend were designed to run outside Docker during development for faster iteration.

**Gap Identified:** This creates friction for:
- New developer onboarding
- Running full stack with single command
- Production-like local testing

**Decision:** Address this gap - options presented were:
- Option A: Development Profile (docker compose --profile dev)
- Option B: Always include in main compose

*Status: Deferred pending test infrastructure discussion*

---

### 2. Test Infrastructure Strategy

**Presenter:** Murat (Master Test Architect)

#### Test Pyramid for LumiKB (RAG System)

```
         E2E (Playwright)
        - Critical user journeys only
        - Login -> Search -> Citations flow

      Integration (pytest + testcontainers)
      - API contracts
      - DB + Qdrant + MinIO interactions

    Unit Tests (pytest + vitest)
    - Business logic
    - Citation parsing, chunking
```

#### Recommended Test Stack

| Layer | Backend (Python) | Frontend (Next.js) | Priority |
|-------|------------------|-------------------|----------|
| Unit | pytest + pytest-asyncio | Vitest + React Testing Library | HIGH |
| Integration | testcontainers-python | MSW (Mock Service Worker) | HIGH |
| E2E | - | Playwright | MEDIUM |
| API Contract | pytest + httpx | - | HIGH |

#### High-Risk Areas Requiring Heavy Coverage

1. **Citation extraction/mapping** - THE product differentiator
2. **Document processing pipeline** - async, multi-service coordination
3. **Permission enforcement** - security critical
4. **Audit logging** - compliance requirement

---

### 3. Test Database Strategy

**Key Question from Tung Vu:** Should we implement test database infrastructure? If yes, how?

#### Options Evaluated

| Strategy | Isolation | Speed | CI/CD Ready | Verdict |
|----------|-----------|-------|-------------|---------|
| Testcontainers | Perfect | Medium | Excellent | **RECOMMENDED** |
| Shared Docker Compose DB | Poor | Fast | Tricky | Dev-only |
| SQLite in-memory | Good | Fastest | Good | NO - async incompatible |
| Separate test DB in Postgres | Medium | Fast | Needs setup | Fallback |

#### Approved Approach: Hybrid Strategy

**Unit Tests (pytest.mark.unit)**
- NO database at all
- Mock repositories, test pure business logic
- Target runtime: < 10 seconds

**Integration Tests (pytest.mark.integration)**
- Testcontainers (PostgreSQL, Redis, Qdrant, MinIO)
- Fresh container per test session
- Target runtime: 1-2 minutes

**E2E Tests (Playwright)**
- Docker Compose full stack
- Seeded test data
- Target runtime: 3-5 minutes

---

### 4. Implementation Plan

#### Phase 1: Pytest Infrastructure (Before Epic 2)

**Task 1.1:** Install testcontainers
```bash
pip install testcontainers[postgres,redis]
```

**Task 1.2:** Create test fixture hierarchy
```
backend/tests/
├── conftest.py              # Shared fixtures
├── unit/
│   └── conftest.py          # Unit-specific (no DB)
├── integration/
│   └── conftest.py          # Testcontainers fixtures
└── e2e/
    └── conftest.py          # Docker Compose fixtures
```

**Task 1.3:** Pytest markers configuration
```ini
[pytest]
markers =
    unit: Fast tests without external dependencies
    integration: Tests requiring testcontainers
    e2e: Full stack tests requiring docker-compose
```

**Task 1.4:** Database transaction rollback pattern for test isolation

#### Phase 2: Makefile Commands
- `make test-unit` - Fast, no Docker
- `make test-integration` - Requires testcontainers
- `make test-all` - Complete suite

#### Phase 3: CI Pipeline (GitHub Actions)
- Unit tests: No Docker needed
- Integration tests: Testcontainers auto-provision

---

### 5. Scope Decision

**IN SCOPE for Test Infrastructure Story:**
- Testcontainers setup for PostgreSQL, Redis
- Pytest markers and configuration
- Basic Makefile commands
- One example integration test using new pattern

**OUT OF SCOPE (deferred):**
- Qdrant testcontainer (defer to Story 2.6)
- MinIO testcontainer (defer to Story 2.4)
- E2E/Playwright setup (defer to before Epic 3)
- Full coverage thresholds

---

## Decisions Made

| # | Decision | Rationale | Owner |
|---|----------|-----------|-------|
| 1 | Implement test infrastructure BEFORE Epic 2 | Prevents 2-3x tech debt accumulation | Murat |
| 2 | Use testcontainers for integration tests | Perfect isolation, CI/CD ready | Winston |
| 3 | Hybrid test strategy (unit/integration/e2e) | Balances speed and coverage | Murat |
| 4 | Create formal story (Option A) | Proper tracking and visibility | John |
| 5 | Estimate: 2-4 hours focused work | Foundational, not comprehensive | Amelia |

---

## Action Items

| # | Action | Owner | Due | Status |
|---|--------|-------|-----|--------|
| 1 | Draft Test Infrastructure Story with tasks and ACs | Murat | 2025-11-23 | Pending |
| 2 | Review and approve story | Tung Vu | 2025-11-23 | Pending |
| 3 | Add story to sprint backlog | Bob (SM) | After approval | Pending |
| 4 | Address Docker Compose backend/frontend gap | TBD | After test infra | Pending |

---

## Key Quotes

> "Testing infrastructure BEFORE implementation is exactly the risk-based approach I champion." - Murat

> "Do we want tests to run against Docker Compose services or testcontainers? My recommendation: Both." - Winston

> "Each test session gets fresh containers... Container automatically destroyed." - Amelia

> "Is this a full story or a tech spike? Make it a Story 0 or Tech Enablement Story - tracked but lighter weight." - John

---

## Next Meeting

**Topic:** Test Infrastructure Story Review & Sprint Planning
**When:** After story draft completion
**Attendees:** SM (Bob), TEA (Murat), Dev (Amelia), Tung Vu

---

## Appendix: Technical References

### Testcontainers Pattern Example

```python
@pytest.fixture(scope="session")
def postgres_url():
    with PostgresContainer("postgres:16") as pg:
        yield pg.get_connection_url()

@pytest.fixture
async def db_session(postgres_url):
    """Each test gets isolated transaction that rolls back"""
    engine = create_async_engine(postgres_url)
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
            await session.rollback()
```

### Current Test State (from Epic 1)

```
backend/tests/
├── conftest.py                    # Async fixtures exist
├── integration/
│   └── test_service_connectivity.py  # 7 tests (Docker Compose dependent)
└── unit/                          # NOT YET CREATED
```

---

*Meeting concluded. Party Mode deactivated.*

*Minutes prepared by Paige (Technical Writer) on behalf of the BMad team.*
