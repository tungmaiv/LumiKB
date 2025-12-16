# Test Design: Epic 5 - Administration & Polish

**Date:** 2025-12-07 (Updated)
**Author:** Murat (Master Test Architect)
**Status:** Draft
**Epic ID:** epic-5

---

## Executive Summary

**Scope:** Full test design for Epic 5 (Administration & Polish + Integration Completion + Technical Debt + Document Management + Document Chunk Viewer)

**Risk Summary:**

- Total risks identified: 17
- High-priority risks (≥6): 8
- Critical categories: TECH, SEC, OPS, DATA, BUS, PERF

**Coverage Summary:**

- P0 scenarios: 40 (80 hours)
- P1 scenarios: 60 (60 hours)
- P2/P3 scenarios: 75 (28 hours)
- **Total effort**: 168 hours (~21 days)

**New Stories Added (2025-12-07):**
- **Story 5.25**: Document Chunk Viewer - Backend API (18 tests) - HIGH PRIORITY
- **Story 5.26**: Document Chunk Viewer - Frontend UI (20 tests) - HIGH PRIORITY

**Previously Added (2025-12-06):**
- **Story 5-22**: Document Tags (24 tests)
- **Story 5-23**: Document Processing Progress (61 tests) - HIGH PRIORITY
- **Story 5-24**: KB Dashboard Filtering & Pagination (26 tests)

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description                                                        | Probability | Impact | Score | Mitigation                                                                 | Owner | Timeline     |
| ------- | -------- | ------------------------------------------------------------------ | ----------- | ------ | ----- | -------------------------------------------------------------------------- | ----- | ------------ |
| R-001   | TECH     | Story 5.0 not completed blocks all Epic 3 & 4 features from users | 3           | 3      | 9     | CRITICAL - Must complete first, comprehensive smoke testing                | Dev   | Before 5.1   |
| R-002   | SEC      | Admin endpoints exposed without authorization checks               | 2           | 3      | 6     | Comprehensive auth tests, role-based access validation                     | Dev   | Before 5.1   |
| R-003   | DATA     | Audit log corruption during export streaming                       | 2           | 3      | 6     | Test large exports (10K+ records), validate data integrity                 | QA    | Before 5.3   |
| R-004   | OPS      | Docker E2E infrastructure misconfigured, tests fail randomly       | 3           | 2      | 6     | Health checks, service dependencies, network isolation                     | Dev   | Before 5.16  |
| R-005   | TECH     | 78 ATDD tests remain red, blocking test confidence                 | 3           | 2      | 6     | Implement wait-for-indexed helper, systematic test fixture updates         | QA    | During 5.12  |
| R-013   | DATA     | Processing step state lost during pipeline failures                | 2           | 3      | 6     | JSONB column for step tracking, error state preservation                   | Dev   | Before 5.23  |
| R-014   | PERF     | Document list slow with 1000+ documents and complex filters        | 3           | 2      | 6     | Indexed queries, pagination, filter combination optimization               | Dev   | Before 5-24  |

### Medium-Priority Risks (Score 3-5)

| Risk ID | Category | Description                                                 | Probability | Impact | Score | Mitigation                                                              | Owner |
| ------- | -------- | ----------------------------------------------------------- | ----------- | ------ | ----- | ----------------------------------------------------------------------- | ----- |
| R-006   | PERF     | Admin dashboard stats query timeout (>5s)                   | 2           | 2      | 4     | Redis caching (5-min TTL), indexed queries, aggregation optimization    | Dev   |
| R-007   | BUS      | Onboarding wizard breaks, users cannot access app           | 2           | 2      | 4     | Skip button always functional, wizard load failure fallback             | QA    |
| R-008   | TECH     | Celery Beat continues failing after fix attempt             | 2           | 2      | 4     | Verify writable volume mount, test across container restarts            | Dev   |
| R-009   | SEC      | PII exposure in audit log export                            | 2           | 2      | 4     | PII redaction tests, export permission validation                       | QA    |
| R-010   | PERF     | Queue monitoring inspect() calls timeout (>10s)             | 2           | 2      | 4     | Timeout configuration, fallback to Redis queries                        | Dev   |
| R-015   | UX       | Tag autocomplete slow with large tag corpus                 | 2           | 1      | 2     | Limit autocomplete to 20 results, debounce input                        | Dev   |
| R-016   | DATA     | Tag validation inconsistent (case sensitivity, whitespace)  | 2           | 2      | 4     | Normalize tags on save (lowercase, trimmed)                             | Dev   |
| R-017   | UX       | Processing progress not updating in real-time               | 2           | 2      | 4     | 10-second auto-refresh, React Query polling                             | Dev   |
| R-018   | TECH     | Chunk viewer fails to highlight text in non-PDF documents   | 2           | 2      | 4     | Format-specific highlighting strategies (char offset vs page-based)     | Dev   |
| R-019   | PERF     | Large document streaming causes browser memory issues        | 2           | 2      | 4     | Lazy loading, chunk pagination, streaming with range requests           | Dev   |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description                                              | Probability | Impact | Score | Action  |
| ------- | -------- | -------------------------------------------------------- | ----------- | ------ | ----- | ------- |
| R-011   | UX       | Sparkline charts don't render on old browsers            | 1           | 1      | 1     | Monitor |
| R-012   | OPS      | Config changes require service restart (not documented)  | 1           | 1      | 1     | Document |

### Risk Category Legend

- **TECH**: Technical/Architecture (integration failures, test infrastructure, service dependencies)
- **SEC**: Security (authorization, PII exposure, admin access control)
- **PERF**: Performance (dashboard queries, export streaming, queue monitoring)
- **DATA**: Data Integrity (audit log corruption, export accuracy)
- **BUS**: Business Impact (onboarding wizard blocking users, feature discoverability)
- **OPS**: Operations (Docker E2E infrastructure, Celery workers, service health)

---

## Test Coverage Plan

### P0 (Critical) - Run on every commit

**Criteria**: Blocks MVP delivery + High risk (≥6) + Critical infrastructure

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Story 5.0: Chat route accessible | E2E | R-001 | 3 | QA | Navigation, SSE streaming, conversation flow |
| Story 5.0: Dashboard nav cards working | E2E | R-001 | 2 | QA | Search/Chat navigation functional |
| Story 5.0: Backend services healthy | API | R-001 | 5 | QA | FastAPI, Celery, Qdrant, Redis, MinIO health checks |
| Story 5.1: Admin auth checks | API | R-002 | 4 | QA | Role-based access control, 403 on non-admin |
| Story 5.3: Audit export integrity | API | R-003 | 3 | QA | Large export (10K records), data accuracy validation |
| Story 5.16: Docker E2E setup | Integration | R-004 | 3 | QA | Service startup, health checks, network isolation |
| Story 5.12: ATDD tests green | Integration | R-005 | 2 | QA | All 78 tests passing, fixture validation |
| Story 5.23: Processing pipeline tracking | API | R-013 | 6 | QA | Step state persistence, error handling |
| Story 5.24: Document list performance | API | R-014 | 4 | QA | Large dataset filtering, pagination |
| Story 5.25: Chunk retrieval endpoint | API | - | 3 | QA | Chunks with metadata, pagination |
| Story 5.25: Document content streaming | API | R-019 | 3 | QA | MinIO streaming, range requests |

**Total P0**: 40 tests, 80 hours (2h each for complex E2E)

### P1 (High) - Run on PR to main

**Criteria**: Important admin features + Medium risk (3-5) + Common workflows

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Story 5.1: Dashboard stats display | API | R-006 | 3 | QA | User/KB/doc counts, search/generation metrics |
| Story 5.1: Redis caching works | Integration | R-006 | 2 | QA | Cache hit/miss, TTL expiry |
| Story 5.2: Audit log filtering | API | - | 4 | QA | Date range, user, action, resource filters |
| Story 5.2: Pagination works | API | - | 2 | QA | 50 per page, offset queries |
| Story 5.3: CSV/JSON export formats | API | R-009 | 3 | QA | Format validation, PII redaction |
| Story 5.4: Queue status monitoring | API | R-010 | 3 | QA | Queue depth, worker status, task details |
| Story 5.5: System configuration | API | - | 3 | QA | Config CRUD, validation, audit logging |
| Story 5.7: Onboarding wizard flow | E2E | R-007 | 4 | QA | Step progression, skip functionality, wizard state |
| Story 5.13: Celery Beat fix | Integration | R-008 | 2 | DEV | No filesystem errors, scheduled tasks execute |
| Story 5.14: Search audit logging | API | - | 2 | QA | Audit events logged, async write |
| Story 5.22: Tag CRUD operations | API | R-016 | 5 | QA | Add, edit, delete, bulk operations |
| Story 5.22: Tag autocomplete | API | R-015 | 3 | QA | Search, limit results, debounce |
| Story 5.23: Processing status display | E2E | R-017 | 4 | QA | Status columns, progress indicators |
| Story 5.23: Step details modal | E2E | - | 3 | QA | Error expansion, step timing |
| Story 5.24: Filter controls | E2E | - | 4 | QA | Search, type, status, tags, date range |
| Story 5.24: URL state persistence | Integration | - | 3 | QA | Filters preserved in URL |
| Story 5.25: Chunk search filtering | API | - | 2 | QA | Text search within chunks |
| Story 5.25: Chunk pagination | API | - | 2 | QA | Page through large chunk sets |
| Story 5.26: Split-pane layout | E2E | - | 2 | QA | Resizable panels, mobile stacking |
| Story 5.26: Chunk selection highlighting | E2E | R-018 | 3 | QA | Click chunk, highlight in document |
| Story 5.26: Document viewer format support | E2E | R-018 | 3 | QA | PDF, HTML, text rendering |

**Total P1**: 60 tests, 60 hours (1h average)

### P2 (Medium) - Run nightly/weekly

**Criteria**: Secondary admin features + Low risk (1-2) + Edge cases

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Story 5.1: Sparkline charts render | Component | - | 2 | DEV | Chart data transformation, responsive design |
| Story 5.2: Audit log export large datasets | Performance | - | 2 | QA | 10K+ records streaming performance |
| Story 5.4: Worker offline detection | Integration | - | 2 | DEV | 60s heartbeat timeout |
| Story 5.5: Sensitive config encryption | Integration | - | 2 | QA | API keys encrypted, redacted in GET |
| Story 5.6: KB detailed stats | API | - | 3 | QA | Document/chunk/embedding counts, storage size |
| Story 5.7: Wizard state persistence | Component | - | 2 | DEV | Survives session refresh |
| Story 5.8: Smart KB suggestions | API | - | 3 | QA | Recommendation algorithm, caching |
| Story 5.9: Recent KBs list | API | - | 2 | QA | Last 5 accessed, ordering |
| Story 5.9: UX polish items | Component | - | 3 | DEV | Loading skeletons, empty states, tooltips |
| Story 5.10: Command palette test fixes | Unit | - | 3 | DEV | All 10 tests passing |
| Story 5.11: Search hardening tests | Unit | - | 6 | DEV | Backend unit, hook tests, screen reader |
| Story 5.15: Epic 4 ATDD tests | Integration | - | 5 | QA | 47 ATDD tests green |
| Story 5.22: Tag display on cards | Component | - | 4 | DEV | Max 10 tags, overflow handling |
| Story 5.22: Bulk tag operations | Integration | - | 4 | QA | Multi-select, apply to batch |
| Story 5.23: Auto-refresh polling | Component | R-017 | 3 | DEV | 10-second interval, pause on modal |
| Story 5.23: Pagination controls | Component | - | 3 | DEV | 25/50/100 page sizes |
| Story 5.24: Real-time filter updates | Component | - | 4 | DEV | No Apply button, debounced search |
| Story 5.24: Tag AND filtering | Integration | - | 3 | QA | Multiple tags filter with AND logic |
| Story 5.25: Permission check on chunks | API | - | 2 | QA | Only KB members can view |
| Story 5.25: Empty chunk handling | API | - | 1 | QA | Document with 0 chunks |
| Story 5.26: Chunk detail panel | Component | - | 2 | DEV | Metadata display, copy text |
| Story 5.26: Mobile responsive | E2E | - | 2 | QA | Stacked panels <1024px |
| Story 5.26: Keyboard navigation | Component | - | 2 | DEV | Arrow keys through chunks |
| Story 5.26: Search within chunks | Component | - | 2 | DEV | Highlight search matches |

**Total P2**: 75 tests, 37.5 hours (0.5h average)

### P3 (Low) - Run on-demand

**Criteria**: Nice-to-have + Exploratory + Performance benchmarks

| Requirement | Test Level | Test Count | Owner | Notes |
| ----------- | ---------- | ---------- | ----- | ----- |
| Story 5.1: Admin dashboard UI theme consistency | Component | 2 | DEV | Dark/light mode |
| Story 5.6: KB stats trends over time | Component | 2 | DEV | Chart rendering |
| Story 5.8: Cold start recommendations | API | 2 | QA | New users get popular KBs |
| Story 5.16: E2E test execution performance | Performance | 3 | QA | Full suite < 10 minutes |

**Total P3**: 9 tests, 2 hours (0.25h average)

---

## Execution Order

### Smoke Tests (<5 min)

**Purpose**: Fast feedback, catch integration-breaking issues

- [ ] Chat page loads and streams responses (Story 5.0, 2min)
- [ ] Admin dashboard displays stats (Story 5.1, 1min)
- [ ] Backend services health check (Story 5.0, 2min)

**Total**: 3 scenarios

### P0 Tests (<45 min)

**Purpose**: Critical path validation for MVP delivery

- [ ] Story 5.0: Chat route navigation (E2E, 5min)
- [ ] Story 5.0: SSE streaming chat response (E2E, 5min)
- [ ] Story 5.0: Dashboard navigation cards (E2E, 3min)
- [ ] Story 5.0: Backend services connectivity (API, 5min)
- [ ] Story 5.1: Admin-only access enforced (API, 3min)
- [ ] Story 5.3: Audit export data integrity (API, 8min)
- [ ] Story 5.16: Docker E2E environment startup (Integration, 8min)
- [ ] Story 5.12: All 78 ATDD tests passing (Integration, 8min)

**Total**: 22 scenarios (~45 min execution)

### P1 Tests (<60 min)

**Purpose**: Important admin feature coverage

- [ ] Story 5.1: Dashboard stats accuracy (API, 3min)
- [ ] Story 5.2: Audit log filtering (API, 5min)
- [ ] Story 5.3: CSV/JSON export formats (API, 4min)
- [ ] Story 5.4: Queue monitoring (API, 4min)
- [ ] Story 5.7: Onboarding wizard flow (E2E, 8min)
- [+ 23 more P1 tests...]

**Total**: 28 scenarios (~60 min execution)

### P2/P3 Tests (<90 min)

**Purpose**: Full regression coverage

- [ ] Story 5.1: Sparkline chart rendering (Component, 2min)
- [ ] Story 5.2: Large dataset export performance (Performance, 10min)
- [ ] Story 5.11: Search hardening tests (Unit, 8min)
- [+ 31 more P2/P3 tests...]

**Total**: 44 scenarios (~90 min execution)

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 34 | 2.0 | 68 | Complex E2E, critical infrastructure tests |
| P1 | 52 | 1.0 | 52 | Standard API/integration coverage |
| P2 | 62 | 0.5 | 31 | Component tests, edge cases |
| P3 | 9 | 0.25 | 2.25 | Exploratory, performance benchmarks |
| **Buffer (10%)** | - | - | **15.3** | **Unknown unknowns** |
| **Total** | **157** | **-** | **168** | **~21 days** |

### Prerequisites

**Test Data:**

- `adminUserFactory()` - Admin users with is_superuser=True
- `auditEventFactory()` - Audit log fixtures (1K, 10K record sets)
- `queueTaskFactory()` - Celery task fixtures for queue monitoring
- `knowledgeBaseFactory()` - KB statistics scenarios
- `documentTagsFactory()` - Document with tags (valid, invalid, max tags scenarios)
- `processingProgressFactory()` - Multi-step processing states, error scenarios
- `largeDocumentListFactory()` - 100+ documents for pagination testing
- Docker seed script: Create test users, KBs, documents for E2E tests

**Tooling:**

- **Playwright** for E2E (dashboard navigation, chat page, onboarding wizard)
- **Vitest** for component tests (sparkline charts, wizard components)
- **pytest** for API tests (admin endpoints, audit log, queue monitoring)
- **Docker Compose** for E2E infrastructure (docker-compose.e2e.yml)
- **recharts** for chart component testing (Story 5.1)

**Environment:**

- PostgreSQL with audit.events table populated (test data)
- Redis with cached stats (cache hit/miss scenarios)
- Celery workers running (queue monitoring tests)
- Docker Compose E2E environment (all services healthy)

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths** (Story 5.0 integration, admin dashboard): ≥90%
- **Security scenarios** (admin auth, PII redaction): 100%
- **E2E infrastructure** (Docker setup, service health): 100%
- **Technical debt** (ATDD tests green): 100%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Story 5.0 smoke tests pass (users can access Epic 3 & 4 features)
- [ ] Admin authorization tests pass 100%
- [ ] Docker E2E infrastructure functional

---

## Mitigation Plans

### R-001: Story 5.0 Not Completed Blocks All Features (Score: 9 - CRITICAL)

**Mitigation Strategy:**
1. **Immediate priority** - Must be first story in Epic 5
2. Create `/app/(protected)/chat/page.tsx` route with ChatContainer
3. Update dashboard with Search and Chat navigation cards
4. Comprehensive smoke testing of 4 user journeys:
   - Document Upload → Processing → Search
   - Search → Citation Display
   - Chat Conversation (multi-turn)
   - Document Generation (template → draft → export)
5. Backend service health verification script

**Owner:** Dev (Amelia)
**Timeline:** BEFORE any other Story 5 work
**Status:** CRITICAL BLOCKER
**Verification:**
- Smoke test suite passes 100%
- Users can navigate to /search and /chat from dashboard
- All Epic 3 & 4 features accessible and functional

---

### R-002: Admin Endpoints Exposed Without Auth (Score: 6)

**Mitigation Strategy:**
1. All `/api/v1/admin/*` endpoints require `is_superuser=True` dependency
2. Comprehensive authorization tests:
   - Admin user can access admin endpoints
   - Non-admin user receives 403 Forbidden
   - Unauthenticated request receives 401 Unauthorized
3. Security review before Story 5.1 completion
4. Test with adversarial requests (role escalation attempts)

**Owner:** Dev + QA
**Timeline:** Before Story 5.1 completion
**Status:** Planned
**Verification:**
- All admin endpoint tests include auth validation
- Security test suite (20 scenarios) passes
- Penetration test review signoff

---

### R-003: Audit Log Corruption During Export (Score: 6)

**Mitigation Strategy:**
1. Test large exports (10K+ records) with streaming validation
2. Validate CSV/JSON data integrity:
   - Row count matches query result
   - Field values preserved (no truncation)
   - Timestamp formats consistent
3. Use StreamingResponse to avoid memory exhaustion
4. Test export with concurrent audit writes
5. Data integrity checksum validation

**Owner:** QA
**Timeline:** Before Story 5.3 completion
**Status:** Planned
**Verification:**
- Large export test suite (5 scenarios) passes
- Streaming performance < 30s for 10K records
- Data integrity validation 100% accuracy

---

### R-004: Docker E2E Infrastructure Misconfigured (Score: 6)

**Mitigation Strategy:**
1. Comprehensive health checks for all services:
   - PostgreSQL: `SELECT 1` query succeeds
   - Redis: `PING` succeeds
   - Qdrant: `GET /health` returns 200
   - MinIO: `GET /minio/health/live` returns 200
   - Backend: `GET /health` returns 200
2. Service dependency ordering in docker-compose.e2e.yml
3. Network isolation validation (services cannot access external network)
4. Database seeding verification (test users, KBs, documents created)
5. Test E2E suite execution in CI/CD pipeline

**Owner:** Dev
**Timeline:** Before Story 5.16 completion
**Status:** Planned
**Verification:**
- All health checks pass < 60s from `docker-compose up`
- E2E test suite passes in CI/CD
- Service startup idempotent (restart tests)

---

### R-005: 78 ATDD Tests Remain Red (Score: 6)

**Mitigation Strategy:**
1. Implement `wait_for_document_indexed(doc_id, timeout=30)` helper
2. Systematic test fixture updates across 5 test files:
   - `test_cross_kb_search.py` (9 tests)
   - `test_llm_synthesis.py` (6 tests)
   - `test_quick_search.py` (5 tests)
   - `test_sse_streaming.py` (6 tests)
   - `test_similar_search.py` (5 tests)
   - Epic 4 ATDD tests (47 tests)
3. Verify tests use real Qdrant/LiteLLM integration (not mocks)
4. Test execution validation: `make test-backend` 0 failures

**Owner:** QA
**Timeline:** During Story 5.12 and 5.15
**Status:** Planned
**Verification:**
- All 78 tests transition to GREEN
- No test failures, no errors
- Existing 496 tests still pass (no regressions)

---

## Assumptions and Dependencies

### Assumptions

1. **Story 5.0 is first priority** - Must complete before other admin features to unblock users
2. Epic 3 & 4 backend services are stable (FastAPI, Celery, Qdrant, Redis working correctly)
3. Docker Compose infrastructure available on dev/CI environments
4. Admin users exist in database (seeded during Epic 1)
5. Audit logging infrastructure from Epic 1 is functional

### Dependencies

1. **Epic 3 & 4 completion** - Required for Story 5.0 smoke testing
2. **recharts library** - Install before Story 5.1 (sparkline charts)
3. **Docker Compose ≥2.0** - Required for Story 5.16 E2E infrastructure
4. **Playwright ≥1.40** - Already installed, verify version
5. **PostgreSQL audit.events table** - Populated with test data for Story 5.2/5.3

### Risks to Plan

- **Risk**: Story 5.0 reveals Epic 3/4 integration bugs
  - **Impact**: Delays Epic 5 start, requires Epic 3/4 fixes
  - **Contingency**: Buffer 2-3 days for integration fixes, prioritize critical paths

- **Risk**: Docker E2E infrastructure too complex, consumes excessive CI time
  - **Impact**: CI/CD pipeline timeouts, slow feedback
  - **Contingency**: Optimize test parallelization, selective E2E execution

- **Risk**: ATDD test fixtures fail after updates (R-005 mitigation)
  - **Impact**: Test churn, unstable test suite
  - **Contingency**: Incremental fixture updates, validate one test file at a time

---

## Test Scenario Details

### Story 5.0: Epic 3 & 4 Integration Completion (CRITICAL)

**P0 Scenarios (5):**

1. **Chat page route navigation**
   - Test Level: E2E
   - Risk: R-001
   - Steps:
     1. Login as authenticated user
     2. Click "Chat" card on dashboard
     3. Verify navigation to `/app/(protected)/chat`
   - Validation: Chat page renders, no 404 errors

2. **SSE streaming chat response**
   - Test Level: E2E
   - Risk: R-001
   - Steps:
     1. Navigate to /chat
     2. Send message "What is OAuth?"
     3. Monitor SSE events from `/api/v1/chat/stream`
   - Validation: Tokens stream word-by-word, citations appear inline

3. **Dashboard navigation cards functional**
   - Test Level: E2E
   - Risk: R-001
   - Steps:
     1. Login and view dashboard
     2. Verify "Search Knowledge Base" card visible
     3. Verify "Chat" card visible
     4. Click each card
   - Validation: Navigate to /search and /chat respectively

4. **Backend services health checks**
   - Test Level: API
   - Risk: R-001
   - Steps:
     1. Query FastAPI `/health` endpoint
     2. Verify Celery workers active (inspect API)
     3. Verify Qdrant `/health` returns 200
     4. Verify Redis PING succeeds
     5. Verify MinIO `/minio/health/live` returns 200
   - Validation: All services healthy

5. **End-to-end smoke test journeys**
   - Test Level: E2E
   - Risk: R-001
   - Steps:
     1. Journey 1: Upload document → Processing → Search
     2. Journey 2: Search → View citations
     3. Journey 3: Chat → Streaming response
     4. Journey 4: Search → Generate → Edit → Export
   - Validation: All 4 journeys complete without errors

---

### Story 5.1: Admin Dashboard Overview

**P0 Scenarios (4):**

6. **Admin-only access enforced**
   - Test Level: API
   - Risk: R-002
   - Steps:
     1. Login as non-admin user
     2. Call GET `/api/v1/admin/stats`
   - Validation: Response 403 Forbidden

7. **Admin user sees dashboard stats**
   - Test Level: API
   - Risk: R-002
   - Steps:
     1. Login as admin user
     2. Call GET `/api/v1/admin/stats`
   - Validation: Returns user counts, KB counts, document counts, search/generation metrics

8. **Redis caching works**
   - Test Level: Integration
   - Risk: R-006
   - Steps:
     1. Call `/api/v1/admin/stats` (cache miss)
     2. Verify query to PostgreSQL
     3. Call again within 5 minutes (cache hit)
   - Validation: Second request served from Redis, faster response

9. **Sparkline data accurate**
   - Test Level: API
   - Risk: R-006
   - Steps:
     1. Seed audit.events with search/generation events (30 days)
     2. Call `/api/v1/admin/stats`
     3. Verify trends array length = 30
   - Validation: Sparkline data matches daily aggregation

**P1 Scenarios (3):**

10. **Dashboard stats breakdown**
    - Test Level: API
    - Validation: Active/inactive users, KBs by status, docs by processing status

11. **Stats refresh on cache expiry**
    - Test Level: Integration
    - Validation: After 5 minutes, cache miss triggers fresh query

12. **Unauthenticated request blocked**
    - Test Level: API
    - Validation: 401 Unauthorized without JWT

---

### Story 5.2: Audit Log Viewer

**P1 Scenarios (4):**

13. **Audit log filtering by date range**
    - Test Level: API
    - Steps:
      1. POST `/api/v1/admin/audit/logs` with start_date, end_date
    - Validation: Results within date range, sorted by timestamp DESC

14. **Audit log filtering by user**
    - Test Level: API
    - Steps:
      1. POST `/api/v1/admin/audit/logs` with user_email filter
    - Validation: All events belong to specified user

15. **Pagination works correctly**
    - Test Level: API
    - Steps:
      1. POST with page=1, page_size=50
      2. POST with page=2, page_size=50
    - Validation: No duplicate records, correct offset

16. **PII redaction in default view**
    - Test Level: API
    - Risk: R-009
    - Steps:
      1. Login as admin without export_pii permission
      2. Call audit logs endpoint
    - Validation: Sensitive fields redacted (email partially masked)

---

### Story 5.3: Audit Log Export

**P0 Scenarios (3):**

17. **Large dataset export integrity**
    - Test Level: API
    - Risk: R-003
    - Steps:
      1. Seed 10,000 audit events
      2. POST `/api/v1/admin/audit/export` format=csv
      3. Download CSV file
      4. Verify row count = 10,000
    - Validation: All rows present, no data corruption

18. **CSV export format validation**
    - Test Level: API
    - Steps:
      1. Export audit logs as CSV
      2. Parse CSV headers
    - Validation: Headers match AuditEvent model fields

19. **JSON export format validation**
    - Test Level: API
    - Steps:
      1. Export audit logs as JSON
      2. Parse JSON array
    - Validation: Each object has all AuditEvent fields

**P1 Scenarios (3):**

20. **Export respects PII redaction**
    - Test Level: API
    - Risk: R-009
    - Validation: Exported data redacts PII unless export_pii permission

21. **Export action logged to audit**
    - Test Level: API
    - Steps:
      1. Export audit logs
      2. Query audit.events for action_type="audit_export"
    - Validation: Export event logged with user, timestamp, row count

22. **Streaming export performance**
    - Test Level: Performance
    - Steps:
      1. Export 10K records
      2. Measure time to first byte, total time
    - Validation: First byte < 2s, total time < 30s

---

### Story 5.4: Processing Queue Status

**P1 Scenarios (3):**

23. **Queue status displays correctly**
    - Test Level: API
    - Steps:
      1. GET `/api/v1/admin/queue/status`
    - Validation: Returns queues: document_processing, embedding_generation, export_generation

24. **Worker online/offline detection**
    - Test Level: Integration
    - Risk: R-010
    - Steps:
      1. Stop Celery worker
      2. Wait 60 seconds
      3. Call queue status endpoint
    - Validation: Worker marked "offline"

25. **Queue depth accuracy**
    - Test Level: Integration
    - Steps:
      1. Submit 10 tasks to queue
      2. Call queue status
    - Validation: Pending tasks = 10

---

### Story 5.5: System Configuration

**P1 Scenarios (3):**

26. **Config CRUD operations**
    - Test Level: API
    - Steps:
      1. GET `/api/v1/admin/config`
      2. PUT `/api/v1/admin/config/max_upload_size` value=100MB
      3. Verify config updated
    - Validation: Config change persisted

27. **Config validation**
    - Test Level: API
    - Steps:
      1. PUT invalid config value (negative number)
    - Validation: 400 Bad Request with validation error

28. **Config changes audited**
    - Test Level: API
    - Steps:
      1. Update config
      2. Query audit.events
    - Validation: Config change logged with old_value and new_value

**P2 Scenarios (2):**

29. **Sensitive config encryption**
    - Test Level: Integration
    - Validation: API keys encrypted at rest, redacted in GET responses

30. **Config change effect immediate**
    - Test Level: Integration
    - Validation: New config value used without service restart (where applicable)

---

### Story 5.6: KB Statistics (Admin View)

**P2 Scenarios (3):**

31. **KB stats accuracy**
    - Test Level: API
    - Steps:
      1. Seed KB with 100 documents, 1000 chunks, 1000 embeddings
      2. GET `/api/v1/admin/knowledge-bases/{kb_id}/stats`
    - Validation: Counts match seeded data

32. **KB usage metrics**
    - Test Level: API
    - Steps:
      1. Seed audit.events with searches (30d)
      2. Call KB stats endpoint
    - Validation: Search count accurate, unique users count accurate

33. **Top accessed documents**
    - Test Level: API
    - Validation: Top 5 documents sorted by access count

---

### Story 5.7: Onboarding Wizard

**P1 Scenarios (4):**

34. **Wizard displays on first login**
    - Test Level: E2E
    - Risk: R-007
    - Steps:
      1. Create new user with onboarding_completed=false
      2. Login
    - Validation: Wizard modal appears

35. **Wizard step progression**
    - Test Level: E2E
    - Steps:
      1. Click "Next" on Step 1
      2. Verify Step 2 displayed
    - Validation: Progress dots update

36. **Wizard skip functionality**
    - Test Level: E2E
    - Risk: R-007
    - Steps:
      1. Click "Skip Onboarding"
      2. Verify wizard closes
      3. Re-login
    - Validation: Wizard not shown again (onboarding_completed=true)

37. **Wizard state persistence**
    - Test Level: Component
    - Steps:
      1. Complete Step 1, refresh page
      2. Verify wizard resumes at Step 2
    - Validation: State persisted in database

---

### Story 5.8: Smart KB Suggestions

**P2 Scenarios (3):**

38. **Recommendation algorithm**
    - Test Level: API
    - Steps:
      1. Seed user search history (KB A: 10 searches, KB B: 2 searches)
      2. GET `/api/v1/users/me/kb-recommendations`
    - Validation: KB A ranked higher than KB B

39. **Recommendations cached**
    - Test Level: Integration
    - Steps:
      1. Call recommendations endpoint (cache miss)
      2. Call again within 1 hour (cache hit)
    - Validation: Second request served from Redis

40. **Cold start recommendations**
    - Test Level: API
    - Steps:
      1. Call recommendations for new user with no history
    - Validation: Returns most popular public KBs

---

### Story 5.9: Recent KBs and Polish Items

**P2 Scenarios (5):**

41. **Recent KBs list**
    - Test Level: API
    - Steps:
      1. Access KB A, KB B, KB C (in order)
      2. GET `/api/v1/users/me/recent-kbs`
    - Validation: Returns [C, B, A] (most recent first), max 5

42. **Empty state message**
    - Test Level: Component
    - Validation: "No recent KBs" message for users with no access history

43. **Loading skeletons display**
    - Test Level: Component
    - Validation: Skeleton components shown during data fetch

44. **Empty states with CTAs**
    - Test Level: Component
    - Validation: Empty states have helpful messages and action buttons

45. **Keyboard navigation**
    - Test Level: E2E
    - Validation: Tab, Enter, Escape work throughout UI

---

### Story 5.10: Command Palette Test Coverage Improvement

**P2 Scenarios (3):**

46. **All 10 command palette tests pass**
    - Test Level: Unit
    - Steps:
      1. Run `npm test command-palette`
    - Validation: 10/10 tests passing

47. **Result fetching after debounce**
    - Test Level: Unit
    - Validation: Results fetched after debounce delay

48. **Error state handling**
    - Test Level: Unit
    - Validation: Error message displayed on API failure

---

### Story 5.11: Epic 3 Search Hardening

**P2 Scenarios (6):**

49. **Backend unit tests - similar search**
    - Test Level: Unit
    - Steps:
      1. Add 3 unit tests to test_search_service.py
    - Validation: All tests pass

50. **Hook unit tests - draft store**
    - Test Level: Unit
    - Steps:
      1. Create draft-store.test.ts with 5 tests
    - Validation: All tests pass

51. **Screen reader verification**
    - Test Level: Manual
    - Steps:
      1. Test with NVDA/JAWS
      2. Verify action buttons announce labels
    - Validation: Accessibility compliance documented

52. **Command palette dialog accessibility**
    - Test Level: Unit
    - Steps:
      1. Add DialogTitle and DialogDescription
      2. Verify Radix UI warnings eliminated
    - Validation: No accessibility warnings

53. **Desktop hover reveal**
    - Test Level: Component
    - Validation: Action buttons hidden by default, appear on hover (≥1024px)

54. **TODO cleanup**
    - Test Level: Manual
    - Validation: 0 TODO comments in search/ directory

---

### Story 5.12: ATDD Integration Tests Transition to Green (Epic 3)

**P0 Scenarios (2):**

55. **All 31 Epic 3 ATDD tests pass**
    - Test Level: Integration
    - Risk: R-005
    - Steps:
      1. Implement wait_for_document_indexed() helper
      2. Update 5 test files
      3. Run `make test-backend`
    - Validation: 0 failures, 0 errors

56. **Test fixtures validate correctly**
    - Test Level: Integration
    - Risk: R-005
    - Steps:
      1. Verify documents indexed in Qdrant
      2. Verify embeddings created
    - Validation: Test data ready before assertions

---

### Story 5.13: Celery Beat Filesystem Fix

**P1 Scenarios (2):**

57. **Celery Beat runs without errors**
    - Test Level: Integration
    - Risk: R-008
    - Steps:
      1. Start Docker Compose
      2. Wait 2 minutes
      3. Check `docker compose ps celery-beat`
    - Validation: STATUS = "Up" (not "Restarting")

58. **Scheduled tasks execute**
    - Test Level: Integration
    - Steps:
      1. Verify celery-beat logs show scheduled task execution
    - Validation: Outbox reconciliation task runs every 5 minutes

---

### Story 5.14: Search Audit Logging

**P1 Scenarios (2):**

59. **Search queries logged to audit**
    - Test Level: API
    - Steps:
      1. Perform search query
      2. Query audit.events for action_type="search"
    - Validation: Audit event logged with query text, kb_ids, result_count

60. **Audit write is async**
    - Test Level: Integration
    - Steps:
      1. Perform search
      2. Measure response time
    - Validation: Audit write doesn't block search response

---

### Story 5.15: Epic 4 ATDD Transition to Green

**P2 Scenarios (5):**

61. **All 47 Epic 4 ATDD tests pass**
    - Test Level: Integration
    - Risk: R-005
    - Steps:
      1. Update test fixtures for chat, generation, export
      2. Run `make test-backend`
    - Validation: 0 failures, 0 errors

62-65. **Story-specific ATDD test groups**
    - Test Level: Integration
    - Validation: Chat (15 tests), Generation (12 tests), Draft editing (10 tests), Export (10 tests) all pass

---

### Story 5.16: Docker E2E Testing Infrastructure

**P0 Scenarios (3):**

66. **Docker E2E environment startup**
    - Test Level: Integration
    - Risk: R-004
    - Steps:
      1. Run `docker-compose -f docker-compose.e2e.yml up -d`
      2. Verify all services healthy < 60s
    - Validation: Health checks pass for all services

67. **E2E test execution**
    - Test Level: E2E
    - Risk: R-004
    - Steps:
      1. Run Playwright test suite against Docker environment
      2. Verify 30+ tests execute successfully
    - Validation: E2E tests pass against containerized stack

68. **Database seeding works**
    - Test Level: Integration
    - Risk: R-004
    - Steps:
      1. Run seed script
      2. Verify test users, KBs, documents created
    - Validation: E2E tests can use seeded data

**P2 Scenarios (3):**

69. **Service dependencies ordered**
    - Test Level: Integration
    - Validation: Services start in correct order (postgres → redis → backend)

70. **Network isolation validated**
    - Test Level: Integration
    - Validation: Test network cannot access external resources

71. **CI/CD integration**
    - Test Level: Integration
    - Validation: GitHub Actions workflow executes E2E tests successfully

---

### Story 5-22: Document Tags

**P1 Scenarios (8):**

72. **Add tags to document**
    - Test Level: API
    - Risk: R-016
    - Steps:
      1. POST `/api/v1/documents/{doc_id}/tags` with ["policy", "hr"]
      2. GET document
    - Validation: Tags saved and returned

73. **Tag validation - max 10 tags**
    - Test Level: API
    - Risk: R-016
    - Steps:
      1. Try to add 11 tags to document
    - Validation: 400 Bad Request, max 10 tags error

74. **Tag validation - 50 char limit**
    - Test Level: API
    - Risk: R-016
    - Steps:
      1. Try to add tag with 51 characters
    - Validation: 400 Bad Request, tag too long error

75. **Tag normalization**
    - Test Level: API
    - Risk: R-016
    - Steps:
      1. Add tag "  Policy  " (with spaces)
      2. GET document tags
    - Validation: Tag normalized to "policy" (lowercase, trimmed)

76. **Tag autocomplete**
    - Test Level: API
    - Risk: R-015
    - Steps:
      1. GET `/api/v1/knowledge-bases/{kb_id}/tags?q=pol`
    - Validation: Returns matching tags, max 20 results

77. **Bulk tag update**
    - Test Level: API
    - Steps:
      1. POST `/api/v1/documents/bulk-tags` with doc_ids and tags
    - Validation: All documents updated with new tags

78. **Remove tags from document**
    - Test Level: API
    - Steps:
      1. DELETE `/api/v1/documents/{doc_id}/tags/policy`
    - Validation: Tag removed, other tags preserved

79. **Tag display on document card**
    - Test Level: E2E
    - Steps:
      1. Navigate to KB dashboard
      2. View document with 5 tags
    - Validation: Tags displayed as badges

**P2 Scenarios (4):**

80. **Overflow tags hidden**
    - Test Level: Component
    - Validation: Max 10 tags displayed, "+N more" indicator

81. **Tag filter in document list**
    - Test Level: E2E
    - Validation: Selecting tag filters document list

82. **Edit tags modal**
    - Test Level: E2E
    - Validation: Modal opens, tags editable, save works

83. **Tags persist across sessions**
    - Test Level: Integration
    - Validation: Tags survive document re-processing

---

### Story 5-23: Document Processing Progress

**P0 Scenarios (6):**

84. **Processing screen access**
    - Test Level: API
    - Risk: R-013
    - Steps:
      1. GET `/api/v1/admin/processing-status`
    - Validation: Returns list of documents with processing status

85. **Processing step tracking**
    - Test Level: API
    - Risk: R-013
    - Steps:
      1. Upload document
      2. Poll processing status
    - Validation: Steps tracked: upload → parse → chunk → embed → index

86. **Step error preservation**
    - Test Level: API
    - Risk: R-013
    - Steps:
      1. Upload malformed document
      2. Check processing status
    - Validation: Error captured in step_errors JSONB, processing halted

87. **Progress percentage calculation**
    - Test Level: Unit
    - Risk: R-013
    - Steps:
      1. Mock document at step 3/5
    - Validation: Progress = 60%

88. **Failed status filtering**
    - Test Level: API
    - Steps:
      1. GET `/api/v1/admin/processing-status?status=failed`
    - Validation: Only failed documents returned

89. **Admin-only access**
    - Test Level: API
    - Steps:
      1. Non-admin calls processing endpoint
    - Validation: 403 Forbidden

**P1 Scenarios (7):**

90. **Document list columns**
    - Test Level: E2E
    - Risk: R-017
    - Steps:
      1. Navigate to /admin/processing
    - Validation: Columns: name, status, progress, current_step, updated_at

91. **Status badge display**
    - Test Level: E2E
    - Validation: Color-coded badges (green=completed, yellow=processing, red=failed)

92. **Step details modal**
    - Test Level: E2E
    - Steps:
      1. Click document row
      2. View modal
    - Validation: All steps displayed with timing, errors expandable

93. **Pagination controls**
    - Test Level: E2E
    - Steps:
      1. With 100 documents, click "Next"
    - Validation: Page 2 loads, URL updated

94. **Page size selector**
    - Test Level: E2E
    - Steps:
      1. Select 100 from dropdown
    - Validation: 100 documents displayed

95. **Auto-refresh toggle**
    - Test Level: E2E
    - Risk: R-017
    - Steps:
      1. Enable auto-refresh
      2. Wait 10 seconds
    - Validation: List refreshes without user action

96. **Retry failed document**
    - Test Level: E2E
    - Steps:
      1. Click "Retry" on failed document
    - Validation: Document re-queued, status changes to "pending"

**P2 Scenarios (8):**

97. **Processing timeline view**
    - Test Level: Component
    - Validation: Steps shown as timeline with duration

98. **Error message copy**
    - Test Level: E2E
    - Validation: Copy button copies error to clipboard

99. **Bulk retry failed**
    - Test Level: E2E
    - Validation: Multi-select and retry all failed

100. **Filter by KB**
     - Test Level: E2E
     - Validation: Dropdown filters by knowledge base

101. **Sort by columns**
     - Test Level: E2E
     - Validation: Click column header to sort

102. **Processing metrics summary**
     - Test Level: Component
     - Validation: Cards showing total, processing, failed, completed counts

103. **Export processing report**
     - Test Level: API
     - Validation: CSV export of processing status

104. **Celery task correlation**
     - Test Level: Integration
     - Validation: Processing status matches Celery task state

---

### Story 5-24: KB Dashboard Document Filtering & Pagination

**P0 Scenarios (4):**

105. **Filter bar renders**
     - Test Level: E2E
     - Risk: R-014
     - Steps:
       1. Navigate to KB dashboard
     - Validation: Filter bar visible with all controls

106. **Pagination with large dataset**
     - Test Level: API
     - Risk: R-014
     - Steps:
       1. KB with 500 documents
       2. GET documents?page=5&limit=50
     - Validation: Correct 50 documents returned, total=500

107. **Filter by status**
     - Test Level: API
     - Steps:
       1. GET documents?status=failed
     - Validation: Only failed documents returned

108. **URL state preservation**
     - Test Level: E2E
     - Steps:
       1. Apply filters (status=failed, type=pdf)
       2. Copy URL, open in new tab
     - Validation: Same filters applied

**P1 Scenarios (6):**

109. **Search by document name**
     - Test Level: E2E
     - Steps:
       1. Type "policy" in search
       2. Wait for debounce
     - Validation: Documents with "policy" in name shown

110. **Filter by type**
     - Test Level: E2E
     - Steps:
       1. Select "PDF" from type dropdown
     - Validation: Only PDF documents shown

111. **Filter by tags (AND logic)**
     - Test Level: API
     - Steps:
       1. GET documents?tags=policy&tags=hr
     - Validation: Only documents with BOTH tags returned

112. **Date range filter**
     - Test Level: E2E
     - Steps:
       1. Set start date to 7 days ago
       2. Set end date to today
     - Validation: Documents uploaded in range shown

113. **Clear filters button**
     - Test Level: E2E
     - Steps:
       1. Apply multiple filters
       2. Click "Clear Filters"
     - Validation: All filters reset, full list shown

114. **Page size selector**
     - Test Level: E2E
     - Steps:
       1. Select 100 from dropdown
     - Validation: 100 documents per page

**P2 Scenarios (8):**

115. **Empty state message**
     - Test Level: Component
     - Validation: "No documents match filters" when empty

116. **Loading indicator**
     - Test Level: Component
     - Validation: Spinner shown during filter change

117. **Combined filters**
     - Test Level: Integration
     - Validation: Multiple filters work together (AND logic)

118. **Filter persistence across navigation**
     - Test Level: E2E
     - Validation: Filters preserved when leaving and returning

119. **Total count display**
     - Test Level: Component
     - Validation: "234 documents" shown in pagination

120. **Previous/Next buttons**
     - Test Level: E2E
     - Validation: Navigate between pages correctly

121. **Tag autocomplete in filter**
     - Test Level: E2E
     - Validation: Tags from KB shown in dropdown

122. **Debounced search input**
     - Test Level: Component
     - Validation: API called after 300ms debounce

---

### Story 5.25: Document Chunk Viewer - Backend API (NEW)

**P0 Scenarios (6):**

123. **Chunk retrieval returns chunks with metadata**
    - Test Level: API
    - Steps:
      1. Process document with multiple chunks
      2. GET `/api/v1/documents/{id}/chunks`
    - Validation: Response contains chunks array with chunk_index, chunk_text, char_start, char_end, page_number

124. **Chunk retrieval pagination**
    - Test Level: API
    - Steps:
      1. Document with 100 chunks
      2. GET `/api/v1/documents/{id}/chunks?page=2&limit=20`
    - Validation: Returns 20 chunks, offset=20, has_next=true

125. **Document content streaming from MinIO**
    - Test Level: API
    - Risk: R-019
    - Steps:
      1. GET `/api/v1/documents/{id}/content`
    - Validation: Streams original file with correct Content-Type header

126. **Range requests supported**
    - Test Level: API
    - Risk: R-019
    - Steps:
      1. GET `/api/v1/documents/{id}/content` with Range header
    - Validation: 206 Partial Content response

127. **Permission check on chunk endpoint**
    - Test Level: API
    - Steps:
      1. Non-member tries to access document chunks
    - Validation: 403 Forbidden

128. **Chunk retrieval for unprocessed document**
    - Test Level: API
    - Steps:
      1. GET chunks for document still processing
    - Validation: 400 Bad Request or empty chunks array with message

**P1 Scenarios (6):**

129. **Chunk search filters by text content**
    - Test Level: API
    - Steps:
      1. GET `/api/v1/documents/{id}/chunks?search=authentication`
    - Validation: Only chunks containing "authentication" returned

130. **Chunk search highlights matches**
    - Test Level: API
    - Steps:
      1. Search chunks
    - Validation: Response includes highlight positions

131. **Get single chunk by index**
    - Test Level: API
    - Steps:
      1. GET `/api/v1/documents/{id}/chunks/5`
    - Validation: Returns chunk at index 5 with full metadata

132. **Content-Type detection**
    - Test Level: API
    - Steps:
      1. Request content for PDF, DOCX, TXT documents
    - Validation: Correct Content-Type headers for each

133. **Chunk count in response**
    - Test Level: API
    - Steps:
      1. GET chunks endpoint
    - Validation: `total` field matches actual chunk count

134. **Empty document chunks**
    - Test Level: API
    - Steps:
      1. Document with no extractable text
    - Validation: Empty chunks array, helpful message

**P2 Scenarios (6):**

135. **Chunk metadata accuracy**
    - Test Level: Integration
    - Validation: char_start/char_end map correctly to source

136. **Page number accuracy for PDFs**
    - Test Level: Integration
    - Validation: Chunk page_number matches PDF page

137. **Paragraph index for DOCX**
    - Test Level: Integration
    - Validation: paragraph_index populated for DOCX files

138. **Large file streaming performance**
    - Test Level: Performance
    - Risk: R-019
    - Validation: 50MB file streams without timeout

139. **Chunk ordering consistency**
    - Test Level: API
    - Validation: Chunks always returned in chunk_index order

140. **Concurrent chunk requests**
    - Test Level: Performance
    - Validation: Multiple requests don't interfere

---

### Story 5.26: Document Chunk Viewer - Frontend UI (NEW)

**P1 Scenarios (8):**

141. **Split-pane layout renders**
    - Test Level: E2E
    - Steps:
      1. Open document detail modal
      2. Click "View & Chunks" tab
    - Validation: Left pane (document), right pane (chunks) visible

142. **Resizable panels**
    - Test Level: E2E
    - Steps:
      1. Drag divider between panels
    - Validation: Panels resize, minimum widths enforced

143. **Chunk list displays**
    - Test Level: E2E
    - Steps:
      1. View chunk sidebar
    - Validation: Chunk count, scrollable list of chunk previews

144. **Click chunk highlights in document**
    - Test Level: E2E
    - Risk: R-018
    - Steps:
      1. Click chunk in sidebar
    - Validation: Document scrolls to chunk, text highlighted

145. **Chunk search filters list**
    - Test Level: E2E
    - Steps:
      1. Type in chunk search box
    - Validation: List filters to matching chunks

146. **PDF viewer displays**
    - Test Level: E2E
    - Risk: R-018
    - Steps:
      1. Open PDF document
    - Validation: PDF renders in left pane

147. **Text viewer displays**
    - Test Level: E2E
    - Risk: R-018
    - Steps:
      1. Open TXT/MD document
    - Validation: Text renders with line numbers

148. **HTML viewer displays**
    - Test Level: E2E
    - Steps:
      1. Open HTML document
    - Validation: HTML renders sanitized

**P2 Scenarios (6):**

149. **Mobile layout stacks panels**
    - Test Level: E2E
    - Steps:
      1. View on <1024px viewport
    - Validation: Panels stack vertically

150. **Chunk detail panel**
    - Test Level: Component
    - Steps:
      1. Click "View Details" on chunk
    - Validation: Panel shows char_start, char_end, page_number, full text

151. **Copy chunk text button**
    - Test Level: E2E
    - Steps:
      1. Click copy button on chunk
    - Validation: Text copied to clipboard, toast shown

152. **Download original document**
    - Test Level: E2E
    - Steps:
      1. Click "Download Original"
    - Validation: File downloads with correct name

153. **Keyboard navigation**
    - Test Level: Component
    - Validation: Arrow keys move through chunks, Enter selects

154. **Loading state**
    - Test Level: Component
    - Validation: Skeleton shown while chunks load

**P3 Scenarios (6):**

155. **Chunk viewer with 500+ chunks**
    - Test Level: Performance
    - Validation: Virtualized list, smooth scrolling

156. **Highlight persistence across searches**
    - Test Level: E2E
    - Validation: Selected chunk stays highlighted during search

157. **Error state display**
    - Test Level: Component
    - Validation: Error message with retry button

158. **Empty state display**
    - Test Level: Component
    - Validation: Helpful message when no chunks

159. **Browser back/forward**
    - Test Level: E2E
    - Validation: Tab state preserved in URL

160. **Print document view**
    - Test Level: E2E
    - Validation: Print-friendly CSS applied

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

- **PRD**: [docs/prd.md](./prd.md)
- **Epic**: [docs/epics.md](./epics.md) - Epic 5 (lines 1722-2400)
- **Tech Spec**: [docs/sprint-artifacts/tech-spec-epic-5.md](sprint-artifacts/tech-spec-epic-5.md)
- **Architecture**: [docs/architecture.md](./architecture.md)
- **Sprint Status**: [docs/sprint-artifacts/sprint-status.yaml](sprint-artifacts/sprint-status.yaml)

---

**Generated by**: Murat (TEA - Master Test Architect)
**Workflow**: `.bmad/bmm/workflows/testarch/test-design`
**Version**: 6.2 (BMad v6) - Updated with Stories 5.25, 5.26 (Document Chunk Viewer)
**Date**: 2025-12-07
