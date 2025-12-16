# Test Design: Epic 5 - Administration & Polish

**Date:** 2025-12-02
**Author:** Murat (Master Test Architect)
**Status:** Draft
**Epic ID:** epic-5

---

## Executive Summary

**Scope:** Full test design for Epic 5 (Administration & Polish + Integration Completion + Technical Debt)

**Risk Summary:**

- Total risks identified: 12
- High-priority risks (≥6): 5
- Critical categories: TECH, SEC, OPS, DATA, BUS

**Coverage Summary:**

- P0 scenarios: 22 (44 hours)
- P1 scenarios: 28 (28 hours)
- P2/P3 scenarios: 35 (13 hours)
- **Total effort**: 85 hours (~11 days)

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

### Medium-Priority Risks (Score 3-5)

| Risk ID | Category | Description                                                 | Probability | Impact | Score | Mitigation                                                              | Owner |
| ------- | -------- | ----------------------------------------------------------- | ----------- | ------ | ----- | ----------------------------------------------------------------------- | ----- |
| R-006   | PERF     | Admin dashboard stats query timeout (>5s)                   | 2           | 2      | 4     | Redis caching (5-min TTL), indexed queries, aggregation optimization    | Dev   |
| R-007   | BUS      | Onboarding wizard breaks, users cannot access app           | 2           | 2      | 4     | Skip button always functional, wizard load failure fallback             | QA    |
| R-008   | TECH     | Celery Beat continues failing after fix attempt             | 2           | 2      | 4     | Verify writable volume mount, test across container restarts            | Dev   |
| R-009   | SEC      | PII exposure in audit log export                            | 2           | 2      | 4     | PII redaction tests, export permission validation                       | QA    |
| R-010   | PERF     | Queue monitoring inspect() calls timeout (>10s)             | 2           | 2      | 4     | Timeout configuration, fallback to Redis queries                        | Dev   |

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

**Total P0**: 22 tests, 44 hours (2h each for complex E2E)

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

**Total P1**: 28 tests, 28 hours (1h average)

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

**Total P2**: 35 tests, 17.5 hours (0.5h average)

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
| P0 | 22 | 2.0 | 44 | Complex E2E, critical infrastructure tests |
| P1 | 28 | 1.0 | 28 | Standard API/integration coverage |
| P2 | 35 | 0.5 | 17.5 | Component tests, edge cases |
| P3 | 9 | 0.25 | 2.25 | Exploratory, performance benchmarks |
| **Buffer (10%)** | - | - | **9.2** | **Unknown unknowns** |
| **Total** | **94** | **-** | **101** | **~13 days** |

### Prerequisites

**Test Data:**

- `adminUserFactory()` - Admin users with is_superuser=True
- `auditEventFactory()` - Audit log fixtures (1K, 10K record sets)
- `queueTaskFactory()` - Celery task fixtures for queue monitoring
- `knowledgeBaseFactory()` - KB statistics scenarios
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
**Version**: 6.0 (BMad v6)
**Date**: 2025-12-02
