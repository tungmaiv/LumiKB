# Epic 5: Administration & Polish

**Goal:** Provide administrators with system management capabilities and polish the user experience with onboarding and refinements.

**User Value:** "Administrators can fully manage the system, and new users have a delightful onboarding experience."

**FRs Covered:** FR47-52, FR58, FR8a-c, FR12b, FR12c-d

**Technical Foundation:**
- Admin dashboard
- Audit log viewer
- Onboarding wizard
- UX polish items
- **Epic 3 & 4 Integration Completion (NEW - Story 5.0)**
- **Main Application Navigation Menu (NEW - Story 5.17)**
- **Docker E2E Testing Infrastructure (NEW - Story 5.16)**

**Epic 5 Scope Changes:**
- **2025-11-30:** Added Story 5.0: Epic 3 & 4 Integration Completion (CRITICAL)
- **2025-11-30:** Added Story 5.16: Docker E2E Testing Infrastructure (HIGH)
- **2025-12-03:** Added Story 5.17: Main Application Navigation Menu (HIGH)
- **2025-12-05:** Added Stories 5.18-5.20: User/Group/Role Management UI
- **2025-12-05:** Added Story 5.21: Theme System (DONE)
- **2025-12-06:** Added Stories 5.22-5.24: Document Tags, Processing Progress, Dashboard Filtering
- **2025-12-07:** Added Stories 5.25-5.26: Document Chunk Viewer (Backend API + Frontend UI)
- Total stories: 26

---

## Story 5.0: Epic 3 & 4 Integration Completion (CRITICAL - NEW)

As an **administrator and user**,
I want **Epic 3 & 4 features to be accessible through normal UI navigation**,
So that **users can actually use search, chat, and generation features**.

**Priority:** CRITICAL
**Estimated Effort:** 1-2 days
**Owner:** Amelia (Dev) with Winston (Architect) support

**Context:** Epic 4 retrospective (2025-11-30) revealed that while Epic 3 & 4 features are fully implemented with high code quality (95-100/100) and comprehensive test coverage (220+ tests), they are not accessible to users through the UI. This story makes features discoverable and accessible.

**Acceptance Criteria:**

**AC1: Chat Page Route Created**
**Given** chat components exist in `frontend/src/components/chat/`
**When** user navigates to `/app/(protected)/chat`
**Then** a functional chat page renders with ChatContainer component
**And** user can start new conversations, send messages, receive streaming responses

**AC2: Navigation Links Added to Dashboard**
**Given** search and chat features are implemented
**When** user views the dashboard at `/app/(protected)/dashboard`
**Then** navigation cards/buttons for "Search Knowledge Base" and "Chat" are visible
**And** clicking these links navigates to `/search` and `/chat` respectively
**And** "Coming in Epic 3" and "Coming in Epic 4" placeholders are removed

**AC3: Backend Services Verified and Healthy**
**Given** the application depends on multiple backend services
**When** the backend is started
**Then** all required services are running and healthy:
- FastAPI backend, PostgreSQL, Redis, Celery worker, Qdrant, MinIO, LiteLLM

**AC4: Complete User Journeys Smoke Tested**
**Given** all Epic 3 & 4 features are wired into UI
**When** smoke testing is performed
**Then** the following user journeys work end-to-end:
1. Document Upload → Processing → Search
2. Search → Citation Display
3. Chat Conversation (multi-turn)
4. Document Generation (template → draft → export)

**AC5: Navigation Discoverability Validated**
**Given** users should discover features through normal UI flow
**When** a new user logs in for the first time
**Then** Search and Chat features are clearly discoverable from dashboard and command palette

**Prerequisites:** Epic 3 & 4 stories completed (components built, tests passing)

**Technical Notes:**
- Create `/app/(protected)/chat/page.tsx` route
- Update `dashboard/page.tsx` to add Search and Chat navigation cards
- Verify backend services (Celery workers, Qdrant, Redis) are running correctly
- Document service startup process
- **Reference:** [docs/sprint-artifacts/5-0-epic-integration-completion.md](sprint-artifacts/5-0-epic-integration-completion.md)

---

## Story 5.1: Admin Dashboard Overview

As an **administrator**,
I want **to see system-wide statistics at a glance**,
So that **I can monitor system health and usage**.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I navigate to /admin
**Then** I see a dashboard with:
- Total users (active/inactive)
- Total Knowledge Bases
- Total documents (by status)
- Storage usage
- Search queries (last 24h, 7d, 30d)
- Generation requests (last 24h, 7d, 30d)

**And** key metrics have sparkline charts showing trends
**And** I can click any metric to see details

**Prerequisites:** Story 1.6

**Technical Notes:**
- Aggregate queries with caching (refresh every 5 min)
- Reference: FR47

---

## Story 5.2: Audit Log Viewer

As an **administrator**,
I want **to view and filter audit logs**,
So that **I can investigate issues and demonstrate compliance**.

**Acceptance Criteria:**

**Given** I am on the admin audit page
**When** I view the audit log table
**Then** I see events with:
- Timestamp
- User (email)
- Action
- Resource type/ID
- IP address

**And** I can filter by:
- Date range (picker)
- User (autocomplete)
- Action type (dropdown)
- Resource type (dropdown)

**And** results are paginated (50 per page)
**And** I can sort by timestamp (default: newest first)

**Prerequisites:** Story 5.1, Story 1.7

**Technical Notes:**
- Use indexed queries on audit.events
- Reference: FR48

---

## Story 5.3: Audit Log Export

As an **administrator**,
I want **to export audit logs for compliance reporting**,
So that **I can provide evidence to auditors**.

**Acceptance Criteria:**

**Given** I have filtered audit logs
**When** I click "Export"
**Then** I can choose format: CSV or JSON

**Given** I select CSV
**When** export completes
**Then** a CSV file downloads with all filtered records
**And** columns match the table display

**Given** I select JSON
**When** export completes
**Then** a JSON file downloads with full audit event details
**And** includes nested details object

**And** export is limited to 10,000 records (paginate for more)
**And** export action is itself logged to audit

**Prerequisites:** Story 5.2

**Technical Notes:**
- Stream large exports to avoid memory issues
- Reference: FR49

---

## Story 5.4: Processing Queue Status

As an **administrator**,
I want **to monitor the document processing queue**,
So that **I can identify and resolve bottlenecks**.

**Acceptance Criteria:**

**Given** I am on the admin page
**When** I view the queue status section
**Then** I see:
- Queue depth (pending events)
- Currently processing count
- Failed events (last 24h)
- Average processing time

**And** I can see list of failed events with error details
**And** I can manually retry failed events
**And** I can purge completed events older than X days

**Prerequisites:** Story 5.1, Story 2.11

**Technical Notes:**
- Query outbox table for metrics
- Use Celery inspection for worker status
- Reference: FR52

---

## Story 5.5: System Configuration

As an **administrator**,
I want **to configure system-wide settings**,
So that **I can tune the system for our needs**.

**Acceptance Criteria:**

**Given** I am on the admin settings page
**When** I view configuration options
**Then** I can configure:
- Default session timeout
- Maximum upload file size
- Default chunk size for processing
- Rate limits

**Given** I save configuration changes
**When** the save completes
**Then** settings are persisted
**And** affected services pick up new values
**And** the change is logged to audit

**Prerequisites:** Story 5.1

**Technical Notes:**
- Store in database, cache in Redis
- Require service restart for some settings (document)
- Reference: FR50, FR51

---

## Story 5.6: KB Statistics (Admin View)

As an **administrator**,
I want **detailed statistics for each Knowledge Base**,
So that **I can optimize storage and identify issues**.

**Acceptance Criteria:**

**Given** I am viewing a KB as admin
**When** I click "Statistics"
**Then** I see detailed metrics:
- Document count by status
- Total storage size (files + vectors)
- Vector count
- Average chunk size
- Search queries (last 30d)
- Top searchers (users)
- Processing success rate

**And** I can see trends over time (chart)

**Prerequisites:** Story 5.1, Story 2.1

**Technical Notes:**
- Aggregate from PostgreSQL + Qdrant + MinIO
- Reference: FR12b

---

## Story 5.7: Onboarding Wizard

As a **first-time user**,
I want **a guided introduction to LumiKB**,
So that **I understand the value and how to use it**.

**Acceptance Criteria:**

**Given** I login for the first time
**When** the dashboard loads
**Then** the onboarding wizard modal appears

**And** the wizard has steps:
1. "Welcome to LumiKB!" - value proposition
2. "Explore the Sample KB" - guided tour of demo KB
3. "Try a Search" - search the demo KB with suggested query
4. "See the Magic" - highlight citations in results
5. "You're Ready!" - next steps and close

**Given** I complete a step
**When** I click "Next"
**Then** I progress to the next step
**And** progress dots show my position

**Given** I want to skip
**When** I click "Skip Tutorial"
**Then** the wizard closes
**And** my preference is saved (don't show again)

**Prerequisites:** Story 1.10, Story 3.4

**Technical Notes:**
- Use Dialog with step state
- Store onboarding_complete flag on user
- Reference: FR8a, FR8b

---

## Story 5.8: Smart KB Suggestions

As a **user**,
I want **the system to suggest relevant KBs based on my content**,
So that **I can quickly find where to search**.

**Acceptance Criteria:**

**Given** I paste text into the search bar
**When** the system analyzes the content
**Then** it suggests 1-3 most relevant KBs
**And** shows why each is suggested (matching keywords)

**Given** I select a suggested KB
**When** I press Enter
**Then** search runs against that KB

**Given** no strong match exists
**When** analysis completes
**Then** suggestion shows "Search all KBs" as default

**Prerequisites:** Story 3.6

**Technical Notes:**
- Analyze pasted content against KB descriptions + sample docs
- Use lightweight embedding comparison
- Reference: FR12c

---

## Story 5.9: Recent KBs and Polish Items

As a **user**,
I want **quick access to recently used KBs and a polished UI**,
So that **my daily workflow is efficient**.

**Acceptance Criteria:**

**Given** I open the KB sidebar
**When** I view the list
**Then** "Recent" section shows my last 5 accessed KBs
**And** they're ordered by most recent first

**And** additional polish items:
- Loading skeletons on all data-fetching views
- Empty states with helpful messages and CTAs
- Error boundaries with friendly recovery options
- Keyboard navigation throughout (Tab, Enter, Escape)
- Tooltips on icon-only buttons

**Prerequisites:** Story 2.3

**Technical Notes:**
- Track recent KBs in localStorage
- Reference: FR12d
- Reference: UX spec Section 7 - Pattern Decisions

---

## Story 5.10: Command Palette Test Coverage Improvement (Technical Debt)

As a **developer**,
I want **to achieve 100% test coverage for the command palette component**,
So that **we have comprehensive test validation for the quick search feature**.

**Acceptance Criteria:**

**Given** the command palette tests currently have 70% pass rate (7/10)
**When** I investigate the test failures
**Then** I identify the root cause (Command component filtering with mocked data)

**And When** I implement a fix
**Then** all 10 command palette tests pass consistently
**And** tests properly validate:
- Result fetching after debounce
- Result display with metadata
- Error state handling on API failure

**And** I document the chosen approach in test file comments

**Prerequisites:** Story 3.7 (completed)

**Technical Notes:**
- **Current Status:** 7/10 tests passing, 3 tests timeout due to shadcn/ui Command component's internal filtering not working with mocked fetch responses
- **Production Impact:** None - production code is verified correct through passing tests and manual validation
- **Priority:** Low - polish item, not blocking
- **Effort:** 1-2 hours
- **Possible Solutions:**
  1. Mock at component level rather than fetch level
  2. Use real Command component behavior with test data
  3. Convert to E2E tests instead of unit tests
  4. Investigate Command/cmdk library test utilities
- **Reference:** Story 3.7 code review, validation-report-3-7-2025-11-26.md
- **Type:** Technical Debt - Test Infrastructure

---

## Story 5.11: Epic 3 Search Hardening (Technical Debt)

As a **developer**,
I want **to complete deferred test coverage and accessibility work from Epic 3**,
So that **search features have comprehensive test coverage and full WCAG 2.1 AA compliance**.

**Acceptance Criteria:**

**Given** Epic 3 deferred work tracked in epic-3-tech-debt.md
**When** I implement the hardening tasks
**Then** all deferred items are completed:

1. **Backend Unit Tests (TD-3.8-1):**
   - Add `test_similar_search_uses_chunk_embedding()` to test_search_service.py
   - Add `test_similar_search_excludes_original()` to test_search_service.py
   - Add `test_similar_search_checks_permissions()` to test_search_service.py
   - All 3 tests pass

2. **Hook Unit Tests (TD-3.8-2):**
   - Create `frontend/src/lib/stores/__tests__/draft-store.test.ts`
   - Add `test_addToDraft__adds_result_to_store()`
   - Add `test_removeFromDraft__removes_by_id()`
   - Add `test_clearAll__empties_selections()`
   - Add `test_isInDraft__returns_true_when_exists()`
   - Add `test_persistence__survives_page_reload()`
   - All 5 tests pass

3. **Screen Reader Verification (TD-3.8-3):**
   - Manually test with NVDA or JAWS screen reader
   - Verify action buttons announce labels correctly
   - Verify draft selection panel announces count changes
   - Verify similar search flow is navigable
   - Document findings in validation-report-3-8-accessibility.md

4. **Command Palette Dialog Accessibility (TD-3.7-1) - NEW:**
   - Add DialogTitle to command-palette.tsx (wrap with VisuallyHidden)
   - Add DialogDescription with "Search across your knowledge bases"
   - Verify Radix UI accessibility warnings eliminated
   - Test with screen reader to confirm announcements

5. **Command Palette Test Fixes (TD-3.7-2) - OPTIONAL:**
   - Debug and fix 3 failing tests (debounce, metadata, error state)
   - Investigate msw mock handler registration
   - Verify React Query cache state in tests
   - All command palette tests passing (10/10)

6. **Desktop Hover Reveal (TD-3.8-4) - OPTIONAL:**
   - Implement hover reveal for action buttons on desktop (≥1024px)
   - Buttons hidden by default, appear on card hover
   - Mobile/tablet behavior unchanged (always visible)

7. **TODO Cleanup (TD-3.8-5):**
   - Scan search components for TODO comments
   - Resolve or convert to tracked issues
   - Verify 0 TODO comments in search/ directory

**And** all existing tests continue to pass (regression protection)

**Prerequisites:** Story 3.8, 3.7, 3.10 (completed)

**Technical Notes:**
- **Source:** Stories 3-7, 3-8, 3-10 code review deferred items
- **Priority:** Medium (improves quality, not blocking production)
- **Effort:** ~6-7 hours (original 4.5h + 0.5h dialog a11y + 1-2h optional tests)
- **Test Pyramid Goal:** Unit tests strengthen isolation, reduce integration test dependency
- **Accessibility Goal:** WCAG 2.1 AA compliance verification (manual + automated)
- **Reference:** docs/sprint-artifacts/epic-3-tech-debt.md
- **Type:** Technical Debt - Test Coverage & Accessibility
- **Updated:** 2025-11-26 (added TD-3.7-1, TD-3.7-2)

**Task Breakdown:**
- Task 1: Backend unit tests (2h)
- Task 2: Hook unit tests (1.5h)
- Task 3: Screen reader testing (1h)
- Task 4: Dialog accessibility (0.5h) - **NEW**
- Task 5: Command palette tests (1-2h) - OPTIONAL
- Task 6: Desktop hover reveal (0.5h) - OPTIONAL
- Task 7: TODO cleanup (0.5h)

**Note:** TD-3.10-1 (VerifyAllButton test harness issue) deferred to Epic 6 due to low priority (test-only issue, component works in production).

---

## Story 5.12: ATDD Integration Tests Transition to GREEN (Technical Debt)

As a **developer**,
I want **to transition 31 ATDD integration tests from RED phase to GREEN**,
So that **search feature integration tests validate against real indexed data in Qdrant**.

**Acceptance Criteria:**

**Given** 31 integration tests are in ATDD RED phase (intentionally failing)
**When** I implement the test infrastructure improvements
**Then** all 31 tests transition to GREEN:

1. **Test Fixture Helper:**
   - Create `backend/tests/helpers/indexing.py`
   - Implement `wait_for_document_indexed(doc_id, timeout=30)` helper
   - Helper polls Qdrant until document chunks indexed
   - Raises TimeoutError if indexing not complete within timeout

2. **Update Test Fixtures:**
   - Update `test_cross_kb_search.py` (9 tests) - use wait_for_document_indexed()
   - Update `test_llm_synthesis.py` (6 tests) - use wait_for_document_indexed()
   - Update `test_quick_search.py` (5 tests) - use wait_for_document_indexed()
   - Update `test_sse_streaming.py` (6 tests) - use wait_for_document_indexed()
   - Update `test_similar_search.py` (5 tests) - use wait_for_document_indexed()

3. **Test Execution:**
   - Run `make test-backend` - 0 failures, 0 errors
   - All 31 previously RED tests now GREEN
   - Existing 496 passing tests still pass (no regressions)

4. **Documentation:**
   - Update epic-3-tech-debt.md TD-ATDD section with RESOLVED status
   - Document wait_for_document_indexed() usage in testing-framework-guideline.md

**And** tests validate against real Qdrant/LiteLLM integration (not mocks)

**Prerequisites:**
- Epic 2 complete (document processing pipeline functional)
- Story 3.10 complete (all search features implemented)

**Technical Notes:**
- **Source:** TD-ATDD in epic-3-tech-debt.md (lines 186-285)
- **Root Cause:** Tests written before implementation (ATDD), expect indexed documents
- **Current Status:** 26 failed + 5 errors = 31 tests in RED phase
- **Error Pattern:** `assert 500 == 200` (empty Qdrant collections → 500 errors)
- **Priority:** Medium (blocks test confidence, not production)
- **Effort:** 3-4 hours
- **Type:** Technical Debt - Test Infrastructure

**Implementation Strategy:**
1. Create polling helper that checks Qdrant for chunk count > 0
2. Use helper in test setup after document upload
3. Ensure tests use same document fixtures consistently
4. Consider adding test-specific Qdrant collection cleanup

**Affected Tests by Story:**
- Story 3.6 (Cross-KB Search): 9 tests
- Story 3.2 (LLM Synthesis): 6 tests
- Story 3.7 (Quick Search): 5 tests
- Story 3.3 (SSE Streaming): 6 tests
- Story 3.8 (Similar Search): 5 tests

**Validation:**
```bash
make test-backend
# Expected: 527 passed, 9 skipped, 0 failed, 0 errors
```

**Reference:**
- docs/sprint-artifacts/epic-3-tech-debt.md (TD-ATDD section)
- Test design checklist: docs/sprint-artifacts/atdd-checklist-3.*.md

**Note:** This resolves the ATDD RED phase deliberately created during Epic 3 story implementation.

---

## Story 5.13: Celery Beat Filesystem Fix (Technical Debt)

As a **developer**,
I want **to fix the celery-beat read-only filesystem error**,
So that **scheduled tasks (like outbox reconciliation) run reliably**.

**Acceptance Criteria:**

**Given** celery-beat service is restarting with error:
```
OSError: [Errno 30] Read-only file system: 'celerybeat-schedule'
```

**When** I investigate the issue
**Then** I identify the root cause (celerybeat-schedule file location)

**And When** I implement the fix
**Then** celery-beat service runs without restarts:
- `docker compose ps` shows lumikb-celery-beat status as "Up" (not "Restarting")
- No OSError in `docker compose logs celery-beat --tail 50`
- Scheduled tasks execute correctly (verify via logs)

**And** the fix persists across:
- Container restarts
- `docker compose down && docker compose up`
- Full environment rebuild

**Acceptance Validation:**
1. Start services: `docker compose up -d`
2. Wait 2 minutes
3. Check status: `docker compose ps celery-beat` → STATUS = "Up"
4. Check logs: `docker compose logs celery-beat --tail 50` → No "Read-only file system" errors
5. Verify scheduled tasks: Check for outbox processing task executions in logs

**Prerequisites:** Epic 2 complete (celery workers functional)

**Technical Notes:**
- **Root Cause:** celerybeat-schedule file written to read-only container path
- **Current Impact:** Scheduled tasks (e.g., outbox reconciliation every 5 min) may not run
- **Priority:** Medium (doesn't block features, but affects background jobs)
- **Effort:** 1 hour
- **Type:** Technical Debt - Infrastructure

**Possible Solutions:**
1. Configure CELERY_BEAT_SCHEDULE_FILENAME to writable volume
2. Mount /app/celerybeat-schedule as Docker volume
3. Set celery beat to use persistent database backend (Django DB scheduler)
4. Write schedule file to /tmp (ephemeral but functional)

**Recommended Approach:**
Option 1 - Configure persistent volume in docker-compose.yml:
```yaml
celery-beat:
  volumes:
    - celery-beat-schedule:/app/celery-schedule
volumes:
  celery-beat-schedule:
```

**And** update celery config:
```python
# backend/app/workers/celery_app.py
app.conf.beat_schedule_filename = '/app/celery-schedule/celerybeat-schedule'
```

**Validation Files:**
- infrastructure/docker/docker-compose.yml (volume mount)
- backend/app/workers/celery_app.py (config change)

**Reference:**
- Discovered during Epic 3 test analysis (2025-11-26)
- Related to Story 2.11 (outbox reconciliation scheduling)

**Note:** While this doesn't block MVP, it should be fixed before production to ensure reliable background job execution.

---

## Story 5.14: Search Audit Logging (moved from Epic 3)

As a **compliance officer**,
I want **all search queries logged**,
So that **we can audit information access**.

**Acceptance Criteria:**

**Given** a user performs a search
**When** results are returned
**Then** an audit event is logged with:
- user_id
- query text
- kb_ids searched
- result_count
- timestamp
- response_time_ms

**Given** audit logs exist
**When** an admin queries them
**Then** they can filter by user, date, and KB

**And** audit write is async (doesn't block search response)

**Prerequisites:**
- Story 3.1 (Semantic Search Backend) - ✅ Complete
- Story 1.7 (Audit Logging Infrastructure) - ✅ Complete
- Story 5.2 (Audit Log Viewer) - Provides UI to view these logs

**Technical Notes:**
- Reuse audit infrastructure from Story 1.7
- Log to `audit.events` table with action_type = 'search'
- Include search metadata in details JSON column
- Async write via background task (don't block search response)
- **Reference:** FR54
- **Type:** Feature - Compliance & Audit
- **Effort:** 1-2 hours
- **Originally:** Story 3.11 in Epic 3, moved to Epic 5 for thematic fit

**Story Relationship:**
- Provides search audit data that Story 5.2 (Audit Log Viewer) will display
- Complements Story 4.10 (Generation Audit Logging) for complete audit coverage
- Together with Stories 5.2 and 5.3, completes the full audit workflow:
  1. Log search queries (5.14)
  2. Log generation requests (4.10)
  3. View all audit logs (5.2)
  4. Export audit logs (5.3)

---

## Story 5.15: Epic 4 ATDD Transition to GREEN + Test Hardening (Technical Debt)

As a **developer**,
I want **to transition 47 ATDD tests from Epic 4 (Chat & Generation) from RED phase to GREEN**,
So that **chat and generation features have comprehensive test coverage with validated risk mitigations**.

**Acceptance Criteria:**

**Given** 47 ATDD tests are in RED phase (written before implementation)
**When** I implement the test infrastructure and transition tests
**Then** all high-priority tests transition to GREEN:

1. **Test Fixtures & Factories (7 items):**
   - Create `backend/tests/factories/conversation.py`:
     - `create_conversation()` - Basic conversation factory
     - `create_multi_turn_conversation(turns=5)` - Multi-turn conversations
   - Create `backend/tests/factories/generation.py`:
     - `create_generation_request()` - Generation request factory
     - `create_draft()` - Generated draft with citations and confidence
   - Create `backend/tests/factories/citation.py`:
     - `create_citation(number=1)` - Single citation factory
     - `create_complex_citations(count=10)` - Multiple citations with varying scores
   - Update `conftest.py`:
     - Add `redis_client` fixture (using fakeredis)
   - All factories follow faker pattern with override support

2. **Backend API Tests (22 tests):**
   - `test_chat_conversation.py` (5 tests) - ✅ All pass
   - `test_citation_security.py` (5 tests) - ✅ All pass (SECURITY CRITICAL)
   - `test_document_export.py` (7 tests) - ✅ All pass
   - `test_confidence_scoring.py` (5 tests) - ✅ All pass

3. **Frontend E2E Tests (16 tests):**
   - `chat-conversation.spec.ts` (7 tests) - ✅ All pass
   - `document-generation.spec.ts` (9 tests) - ✅ All pass

4. **Component Tests (9 tests):**
   - `chat-message.test.tsx` (9 tests) - ✅ All pass

5. **Export Validation Helpers:**
   - Install: `python-docx`, `PyPDF2`, `reportlab`
   - Create `backend/tests/helpers/export_validation.py`:
     - `validate_docx_citations(docx_bytes, expected_citations)` - Parse DOCX XML
     - `validate_pdf_citations(pdf_bytes, expected_citations)` - Extract PDF text
   - Use helpers in export tests

6. **Risk Mitigation Validation:**
   - R-001 (Token Limit): 3 tests GREEN ✅
   - R-002 (Citation Injection): 5 tests GREEN ✅ (SECURITY)
   - R-003 (Streaming Latency): 2 tests GREEN ✅
   - R-004 (Export Citations): 5 tests GREEN ✅
   - R-005 (Low Confidence): 6 tests GREEN ✅

7. **Documentation:**
   - Update `docs/sprint-artifacts/epic-4-tech-debt.md` TD-4.0-1 → RESOLVED
   - Add test execution guide to README or testing-framework-guideline.md

**And** all existing tests continue to pass (no regressions)
**And** run `make test-backend` → 0 failures (all Epic 4 tests GREEN)
**And** run `npm run test:e2e -- e2e/tests/chat/` → 0 failures
**And** run `npm run test` → all component tests pass

**Prerequisites:**
- Epic 4 complete (Stories 4.1-4.10 implemented)
- Story 5.12 complete (Epic 3 ATDD transition - similar pattern)

**Technical Notes:**
- **Source:** TD-4.0-1 in epic-4-tech-debt.md
- **Root Cause:** ATDD tests written before implementation (RED phase)
- **Current Status:** 47 tests in RED phase (intentional)
- **Priority:** HIGH (validates 4 high-risk mitigations)
- **Effort:** 16-20 hours
- **Type:** Technical Debt - Test Infrastructure + Security Validation

**Implementation Strategy:**
1. Start with factories (conversation, generation, citation)
2. Add Redis fixture with fakeredis
3. Implement export validation helpers
4. Run backend tests → debug failures → GREEN
5. Run E2E tests → add missing data-testid attributes → GREEN
6. Run component tests → GREEN
7. Validate all 4 risk mitigations covered

**Affected Tests by Story:**
- Story 4.1 (Chat Conversation): 5 backend + 3 E2E tests
- Story 4.2 (Chat Streaming UI): 2 backend + 4 E2E + 9 component tests
- Story 4.5 (Confidence Scoring): 5 backend + 2 E2E tests
- Story 4.7 (Document Export): 7 backend + 3 E2E tests
- Story 4.3, 4.4, 4.6, 4.8, 4.9, 4.10: Covered by above tests

**Security Focus:**
- Citation injection tests (R-002) are **CRITICAL** - must pass 100%
- Adversarial prompt suite validates system resilience
- Citation validation prevents fake source injection

**Test Execution Commands:**
```bash
# Backend tests
cd backend
pytest tests/integration/test_chat*.py -v
pytest tests/integration/test_citation_security.py -v  # SECURITY
pytest tests/integration/test_document_export.py -v
pytest tests/integration/test_confidence_scoring.py -v

# Frontend E2E
cd frontend
npm run test:e2e -- e2e/tests/chat/

# Component tests
npm run test -- src/components/chat/__tests__/

# All Epic 4 tests
make test-epic-4  # Add this target to Makefile
```

**Validation Checklist:**
- [ ] All 7 factories created and tested
- [ ] Redis fixture working with fakeredis
- [ ] Export validation helpers functional
- [ ] 22 backend API tests GREEN
- [ ] 16 E2E tests GREEN
- [ ] 9 component tests GREEN
- [ ] R-002 (Security) tests passing 100%
- [ ] No regressions in existing tests
- [ ] epic-4-tech-debt.md updated

**Reference:**
- docs/sprint-artifacts/epic-4-tech-debt.md (TD-4.0-1)
- docs/sprint-artifacts/atdd-checklist-epic-4.md (implementation guide)
- docs/sprint-artifacts/test-design-epic-4.md (risk assessment)

**Note:** This resolves the ATDD RED phase deliberately created during Epic 4 story implementation. Follows same pattern as Story 5.12 (Epic 3 ATDD transition).

---

## Story 5.16: Docker E2E Testing Infrastructure (HIGH - NEW)

As a **developer and QA engineer**,
I want **a Docker-based E2E testing infrastructure that validates complete user journeys**,
So that **we can test the full stack in a production-like environment and catch integration issues before deployment**.

**Priority:** HIGH
**Estimated Effort:** 2-3 days
**Owner:** Murat (TEA)
**Support:** Winston (Architect), Amelia (Dev)

**Context:** Epic 4 retrospective (2025-11-30) revealed that the test pyramid is incomplete. While unit tests (✅ 114 total) and integration tests (✅ 74 backend) provide excellent coverage, E2E tests are missing. This story establishes Docker-based E2E testing infrastructure to validate complete user journeys.

**Test Pyramid Gap:**
- ✅ Unit tests: Excellent coverage (29 backend, 51 frontend component, 34 frontend hook)
- ✅ Integration tests: Good coverage (74 backend API tests)
- ❌ E2E tests: Written but not executed (8 E2E tests exist, no infrastructure to run them)

**Acceptance Criteria:**

**AC1: Docker Compose E2E Environment Created**
**Given** the application requires multiple services for E2E testing
**When** `docker-compose -f docker-compose.e2e.yml up` is executed
**Then** all required services start successfully:
- Frontend (Next.js production build on port 3000)
- Backend (FastAPI on port 8000)
- Celery Worker, PostgreSQL, Redis, Qdrant, MinIO, LiteLLM
**And** all services are accessible from the Playwright container
**And** environment variables are configured for E2E testing

**AC2: Playwright E2E Test Execution Configured**
**Given** Playwright tests exist in `frontend/e2e/tests/`
**When** E2E tests are executed with `npm run test:e2e`
**Then** Playwright runs tests against the Docker environment
**And** tests can navigate to frontend and interact with all services
**And** test results are reported with pass/fail status

**AC3: E2E Test Database Seeding Implemented**
**Given** E2E tests require consistent test data
**When** the E2E environment starts
**Then** the test database is seeded with:
- Test users (admin, regular user)
- Test knowledge bases with permissions
- Indexed test documents (for search/chat tests)
**And** seeding is idempotent (can run multiple times without errors)

**AC4: GitHub Actions CI Integration Configured**
**Given** E2E tests should run in CI/CD pipeline
**When** a pull request is created or pushed to main
**Then** GitHub Actions workflow runs E2E tests
**And** workflow uses `docker-compose.e2e.yml` to spin up environment
**And** workflow reports test results and uploads artifacts (screenshots, videos)
**And** workflow fails if any E2E tests fail

**AC5: E2E Test Suite for Epic 3 & 4 Features Executed**
**Given** Epic 3 & 4 features are now accessible (Story 5.0 completed)
**When** E2E tests run in Docker environment
**Then** the following test suites execute successfully:
- **Epic 3:** Search with citations, citation panel, confidence scoring, command palette
- **Epic 4:** Chat conversation (multi-turn), chat streaming, document generation, draft editing, export, feedback
**And** 15-20 E2E tests pass covering critical paths

**Prerequisites:**
- Story 5.0 completed (Epic 3 & 4 features accessible through UI)
- Docker and Docker Compose installed
- Playwright dependencies installed

**Technical Notes:**
- Create `docker-compose.e2e.yml` with all 8 services (frontend, backend, celery, postgres, redis, qdrant, minio, litellm, playwright)
- Configure Playwright to use Docker environment URLs (`E2E_BASE_URL=http://frontend:3000`)
- Create database seeding script (`backend/seed_e2e.py`)
- Create GitHub Actions workflow (`.github/workflows/e2e-tests.yml`)
- Execute existing E2E tests and add missing ones (target: 15-20 total)
- **Reference:** [docs/sprint-artifacts/5-16-docker-e2e-infrastructure.md](sprint-artifacts/5-16-docker-e2e-infrastructure.md)
- **Type:** Test Infrastructure - E2E Testing

**Benefits:**
- Full-stack integration testing (not just mocked components)
- Consistent environment across dev and CI
- Test against real services (PostgreSQL, Redis, Qdrant, MinIO, LiteLLM)
- Catch integration issues before production deployment
- Validate complete user journeys end-to-end
- Framework for all future E2E testing

**User Journeys to Test:**
1. Document Upload → Processing → Search
2. Search → Citation Display
3. Chat Conversation (multi-turn with history)
4. Document Generation (template → draft → export)

---

## Story 5.17: Main Application Navigation Menu (HIGH - NEW)

As a **user and administrator**,
I want **a persistent main navigation menu on all protected routes**,
So that **I can easily discover and access all application features including admin tools**.

**Priority:** HIGH
**Estimated Effort:** 1-2 days
**Owner:** Amelia (Dev)

**Context:** Stories 5-1 through 5-6 implemented comprehensive admin features (dashboard overview, audit logs, queue monitoring, system configuration, KB statistics) but these features are not accessible via UI navigation. Users cannot discover or navigate to `/admin`, `/admin/audit`, `/admin/queue`, `/admin/config`, or `/admin/kb-stats` routes. This story adds persistent main navigation to make all features discoverable.

**Problem Statement:** Admin features (Stories 5-1 through 5-6) are built and functional but not accessible via UI navigation. The application currently only has:
- KB sidebar (left side) - for knowledge base selection
- Header with search bar and user menu (top)
- Mobile bottom nav with placeholder buttons (mobile only)

Users cannot access admin routes without manually typing URLs. This is the same pattern identified in Epic 4 retrospective where features were built but not accessible.

**Solution:** Add a persistent main navigation component with:
- Core application links: Dashboard, Search, Chat
- Admin section (permission-gated): Admin Dashboard, Audit Logs, Queue Status, System Config, KB Statistics
- Active route highlighting
- Mobile-responsive design
- Full accessibility compliance (WCAG 2.1 AA)

**Acceptance Criteria:**

**AC-5.17.1: Navigation Structure and Layout**
**Given** a user is logged into any protected route
**When** the page loads
**Then** a persistent main navigation menu is visible
**And** navigation is positioned consistently across all routes
**And** navigation contains two sections: "Core Links" and "Admin" (admin-only)
**And** navigation is responsive (desktop sidebar, mobile bottom nav)
**And** navigation does not interfere with existing three-panel layout (KB sidebar, main content, citations panel)

**Validation:**
- Navigation component renders on all routes: `/dashboard`, `/search`, `/chat`, `/admin/*`
- Desktop breakpoint (≥1024px): Navigation is a vertical sidebar
- Mobile/tablet breakpoint (<1024px): Navigation is a bottom bar with icons
- Layout maintains existing KB sidebar and citations panel

**AC-5.17.2: Core Application Links**
**Given** the main navigation is visible
**When** I view the "Core Links" section
**Then** I see three links: "Dashboard", "Search", "Chat"
**And** each link has an appropriate icon (Home, Search, MessageSquare)
**And** clicking each link navigates to `/dashboard`, `/search`, `/chat` respectively
**And** the active route is highlighted visually

**Validation:**
- All 3 core links present with icons
- Navigation works correctly (Next.js routing)
- Active route has distinct visual styling (background color, bold text)
- Icons match design system (Lucide React icons)

**AC-5.17.3: Admin Section (Permission-Gated)**
**Given** I am logged in as an admin user
**When** I view the main navigation
**Then** I see an "Admin" section below core links
**And** the admin section contains 5 links: "Admin Dashboard", "Audit Logs", "Queue Status", "System Config", "KB Statistics"
**And** each admin link has an appropriate icon
**And** clicking each link navigates to the respective admin route

**Given** I am logged in as a regular (non-admin) user
**When** I view the main navigation
**Then** the "Admin" section is not visible

**Validation:**
- Admin section only visible to users with `role === 'admin'`
- All 5 admin links present with correct routes: `/admin`, `/admin/audit`, `/admin/queue`, `/admin/config`, `/admin/kb-stats`
- Permission check uses `useAuthStore` hook
- Non-admin users cannot see admin navigation (verified via frontend logic)

**AC-5.17.4: User Menu Integration**
**Given** the main navigation includes user controls
**When** I view the navigation on desktop
**Then** the existing user menu (Settings, Logout) is integrated into navigation
**And** user menu positioning is consistent with design system

**Validation:**
- User menu component reused from existing header
- Desktop: User menu at bottom of navigation sidebar
- Mobile: User menu in header (existing behavior preserved)

**AC-5.17.5: Mobile Navigation Behavior**
**Given** I am using a mobile device (width < 1024px)
**When** I view the application
**Then** the main navigation is a bottom bar with icon-only buttons
**And** active route is highlighted
**And** tapping a navigation item navigates to that route
**And** touch targets are at least 44x44px (WCAG 2.1 AA)

**Validation:**
- Mobile breakpoint uses bottom navigation bar
- Icons only (no text labels on mobile)
- Active state visually distinct
- Touch target size compliant

**AC-5.17.6: Accessibility Compliance**
**Given** the main navigation must be accessible
**When** I interact with navigation using keyboard or screen reader
**Then** all navigation items are keyboard accessible (Tab, Enter)
**And** active route is announced to screen readers
**And** navigation has proper ARIA labels and roles
**And** focus indicators are visible
**And** navigation complies with WCAG 2.1 AA standards

**Validation:**
- All links keyboard navigable
- ARIA attributes: `role="navigation"`, `aria-label="Main navigation"`, `aria-current="page"` for active route
- Focus visible on keyboard navigation
- Screen reader testing confirms proper announcements

**Prerequisites:**
- Stories 5-1 through 5-6 completed (admin routes exist)
- Story 5.0 completed (dashboard navigation cards exist as pattern reference)

**Technical Notes:**
- Create `MainNav` component in `frontend/src/components/layout/`
- Integrate into `DashboardLayout` component
- Use `usePathname()` hook for active route detection
- Use `useAuthStore()` for permission checks
- Reuse existing header user menu component
- Follow existing three-panel layout pattern (Story 1.9)
- **Reference:** [docs/sprint-artifacts/5-17-main-navigation.md](sprint-artifacts/5-17-main-navigation.md)
- **Pattern Source:** Story 5.0 Quick Access cards, Epic 4 retrospective learning about integration stories

**Benefits:**
- Admin features (Stories 5-1 to 5-6) become discoverable and accessible
- Consistent navigation across entire application
- Improved user experience with clear feature discovery
- Prevents feature abandonment (Epic 4 retrospective learning applied)

---

## Story 5.18: User Management UI (NEW)

As an **administrator**,
I want **to view, create, edit, and manage user accounts through the admin UI**,
So that **I can onboard new team members, update user information, and control account status without direct database access**.

**Priority:** HIGH
**Estimated Effort:** 2-3 days
**Owner:** Amelia (Dev)
**Support:** Winston (Architect)

**Context:** The backend API endpoints for user management exist (GET/POST/PATCH /api/v1/admin/users from Story 1.6), but there is no frontend UI to access these features. Administrators currently have no way to manage users through the application interface.

**Prerequisites:**
- Story 1.6: Admin User Management Backend (DONE)
- Story 5.17: Main Application Navigation Menu (provides admin navigation)

**Acceptance Criteria:**

**AC-5.18.1: User List Page Created**
**Given** I am logged in as an admin (is_superuser=true)
**When** I navigate to /admin/users
**Then** I see a paginated table of all users with columns:
- Email
- Status (Active/Inactive badge)
- Role (Admin/User)
- Created date
- Last active date
**And** I can sort by any column
**And** I can search/filter by email
**And** pagination shows 20 users per page with navigation controls

**AC-5.18.2: Create User Modal Implemented**
**Given** I am on the /admin/users page
**When** I click "Add User" button
**Then** a modal appears with form fields:
- Email (required, validated)
- Password (required, min 8 chars)
- Confirm Password (must match)
- Is Admin checkbox (default unchecked)
**And** clicking "Create" calls POST /api/v1/admin/users
**And** success shows toast notification and refreshes user list
**And** error displays validation message inline

**AC-5.18.3: Edit User Functionality Implemented**
**Given** I am viewing the user list
**When** I click the edit action on a user row
**Then** a modal appears with:
- Email (read-only, displayed for context)
- Status toggle (Active/Inactive)
- Role dropdown (User/Admin)
**And** changes are saved via PATCH /api/v1/admin/users/{user_id}
**And** success shows confirmation and updates table row
**And** I cannot deactivate my own account (prevented with warning)

**AC-5.18.4: User Status Toggle Works**
**Given** I am viewing the user list
**When** I toggle a user's status from Active to Inactive
**Then** the status badge updates immediately (optimistic UI)
**And** the API call updates is_active field
**And** deactivated users cannot log in until reactivated
**And** action is logged to audit.events

**AC-5.18.5: Admin Navigation Updated**
**Given** I am an admin user
**When** I view the admin navigation menu
**Then** I see a "Users" link in the admin section
**And** clicking it navigates to /admin/users
**And** the link shows active state when on users page

**AC-5.18.6: Access Control Enforced**
**Given** I am NOT an admin (is_superuser=false)
**When** I attempt to access /admin/users directly
**Then** I am redirected to /dashboard with an error message
**And** API calls return 403 Forbidden

**Technical Notes:**
- Frontend: Create `/admin/users/page.tsx`, `useUsers` hook, `UserTable`, `CreateUserModal`, `EditUserModal` components
- Use existing backend endpoints: GET/POST/PATCH /api/v1/admin/users
- Add DELETE endpoint to backend if needed (soft delete via is_active=false preferred)
- Reference: FR5, FR56 (audit logging)

**Tasks:**
- Task 1: Create useUsers React Query hook with pagination
- Task 2: Create UserTable component with sorting/filtering
- Task 3: Create CreateUserModal with form validation
- Task 4: Create EditUserModal with status toggle
- Task 5: Create /admin/users/page.tsx
- Task 6: Update main-nav.tsx with Users link
- Task 7: Write unit tests for components
- Task 8: Write integration tests for API calls

---

## Story 5.19: Group Management (NEW)

As an **administrator**,
I want **to create user groups and assign users to groups**,
So that **I can manage KB access permissions at the group level rather than individually per user**.

**Priority:** MEDIUM
**Estimated Effort:** 3-4 days
**Owner:** Amelia (Dev)
**Support:** Winston (Architect)

**Context:** Currently KB permissions are only assignable at the user level. Groups enable bulk permission management - assign KB access to a group, then add/remove users from the group. This is essential for enterprise deployments with many users.

**Prerequisites:**
- Story 5.18: User Management UI
- Story 2.2: Knowledge Base Permissions Backend (DONE)

**Acceptance Criteria:**

**AC-5.19.1: Group Model and API Created**
**Given** the backend needs group management
**When** the migration is applied
**Then** a `groups` table exists with columns:
- id (UUID, PK)
- name (VARCHAR, unique)
- description (TEXT, nullable)
- created_at, updated_at timestamps
**And** a `user_groups` junction table exists (user_id, group_id)
**And** API endpoints exist:
- GET /api/v1/admin/groups (list all)
- POST /api/v1/admin/groups (create)
- PATCH /api/v1/admin/groups/{id} (update)
- DELETE /api/v1/admin/groups/{id} (soft delete)
- POST /api/v1/admin/groups/{id}/members (add users)
- DELETE /api/v1/admin/groups/{id}/members/{user_id} (remove user)

**AC-5.19.2: Group List Page Created**
**Given** I am logged in as an admin
**When** I navigate to /admin/groups
**Then** I see a table of all groups with:
- Name
- Description
- Member count
- Created date
**And** I can search by group name
**And** clicking a row expands to show member list

**AC-5.19.3: Create/Edit Group Modal Implemented**
**Given** I am on the /admin/groups page
**When** I click "Create Group" or edit action
**Then** a modal appears with:
- Name (required, unique)
- Description (optional)
**And** validation prevents duplicate group names
**And** success refreshes group list

**AC-5.19.4: Group Membership Management Implemented**
**Given** I am viewing a group's details
**When** I click "Manage Members"
**Then** I see:
- Current members list with remove action
- "Add Members" button opening user picker
**And** I can search users by email in the picker
**And** adding/removing users updates immediately
**And** changes are logged to audit.events

**AC-5.19.5: Admin Navigation Updated**
**Given** I am an admin user
**When** I view the admin navigation
**Then** I see a "Groups" link
**And** clicking it navigates to /admin/groups

**Technical Notes:**
- Create alembic migration for groups and user_groups tables
- GroupService for business logic
- Consider LDAP/SSO group sync for future (out of scope for MVP)
- Reference: FR6, FR56

**Tasks:**
- Task 1: Create groups and user_groups database models
- Task 2: Create alembic migration
- Task 3: Create GroupService with CRUD operations
- Task 4: Create group API endpoints
- Task 5: Create useGroups React Query hook
- Task 6: Create GroupTable and GroupMembershipModal components
- Task 7: Create /admin/groups/page.tsx
- Task 8: Update navigation
- Task 9: Write backend unit tests
- Task 10: Write frontend tests

---

## Story 5.20: Role & KB Permission Management UI (NEW)

As an **administrator**,
I want **to assign Knowledge Base permissions to users and groups through the UI**,
So that **I can control who can access which Knowledge Bases without SQL queries**.

**Priority:** MEDIUM
**Estimated Effort:** 2-3 days
**Owner:** Amelia (Dev)
**Support:** Winston (Architect)

**Context:** KB permissions backend exists (Story 2.2), but there's no UI to manage permissions. Admins need to assign Read/Write/Admin permissions to users or groups for each KB.

**Prerequisites:**
- Story 5.18: User Management UI
- Story 5.19: Group Management
- Story 2.2: Knowledge Base Permissions Backend (DONE)

**Acceptance Criteria:**

**AC-5.20.1: KB Permission Tab Added**
**Given** I am an admin viewing KB details
**When** I click the "Permissions" tab
**Then** I see two sections:
- User Permissions (table of user-KB-permission assignments)
- Group Permissions (table of group-KB-permission assignments)
**And** each row shows: Entity (user email/group name), Permission Level (Read/Write/Admin)

**AC-5.20.2: Add Permission Modal Implemented**
**Given** I am on the KB Permissions tab
**When** I click "Add User Permission" or "Add Group Permission"
**Then** a modal appears with:
- Entity picker (user email autocomplete or group dropdown)
- Permission level dropdown (Read, Write, Admin)
**And** validation prevents duplicate assignments
**And** success adds row to permissions table

**AC-5.20.3: Edit/Remove Permission Works**
**Given** I am viewing KB permissions
**When** I click edit on a permission row
**Then** I can change the permission level
**And** I can remove the permission entirely
**And** removing the last Admin permission shows warning
**And** changes are saved via API and logged to audit

**AC-5.20.4: Group Permission Inheritance Displayed**
**Given** a user belongs to a group with KB access
**When** I view that user's effective permissions
**Then** I see both direct and inherited (via group) permissions
**And** inherited permissions show "via [Group Name]" indicator
**And** direct permissions override group permissions

**AC-5.20.5: Backend API Extended for Groups**
**Given** groups can now have KB permissions
**When** POST /api/v1/knowledge-bases/{kb_id}/permissions is called
**Then** it accepts both user_id and group_id (mutually exclusive)
**And** GET endpoint returns both user and group permissions
**And** permission checks consider group membership

**AC-5.20.6: Admin Navigation Updated**
**Given** the existing KB management exists
**When** admin views a KB
**Then** "Permissions" is a visible tab option

**Technical Notes:**
- Extend kb_permissions table or create kb_group_permissions
- Update KBPermissionService to check group membership
- Consider permission caching for performance
- Reference: FR6, FR7, FR56

**Tasks:**
- Task 1: Create kb_group_permissions table and migration
- Task 2: Extend KBPermissionService for group support
- Task 3: Update permission check logic to include groups
- Task 4: Create KBPermissionsTab component
- Task 5: Create AddPermissionModal (user/group variants)
- Task 6: Update KB detail page with Permissions tab
- Task 7: Create useKBPermissions hook
- Task 8: Write backend tests for group permissions
- Task 9: Write frontend component tests

---

## Story 5.21: Theme System (NEW)

As a **user**,
I want **to choose from multiple color themes for the application**,
So that **I can personalize my experience and reduce eye strain**.

**Priority:** LOW
**Estimated Effort:** 0.5 days
**Owner:** Amelia (Dev)
**Status:** DONE

**Context:** Users requested additional theme options beyond the default light/dark toggle. This story adds two new themes (Light Blue, Dark Navy) and converts the simple toggle to a theme selector submenu in the user menu.

**Acceptance Criteria:**

**AC-5.21.1: Two New Themes Added**
**Given** users want theme variety
**When** I open the theme selector
**Then** I see 5 theme options:
- Light (default light theme - Trust Blue)
- Dark (default dark theme)
- Light Blue (soft sky blue tones)
- Dark Navy (deep professional navy)
- System (follow OS preference)
**And** each theme has consistent CSS variables for all UI components

**AC-5.21.2: Theme Selector Submenu Implemented**
**Given** theme selection was previously a simple toggle
**When** I click on my user avatar and open the dropdown
**Then** I see a "Theme" submenu with a palette icon
**And** hovering/clicking shows all 5 theme options
**And** current theme shows a checkmark indicator
**And** selecting a theme immediately applies it

**AC-5.21.3: Theme Persistence Works**
**Given** I select a theme
**When** I refresh the page or return later
**Then** my selected theme is preserved
**And** theme preference is stored in localStorage via Zustand persist

**AC-5.21.4: All UI Components Theme-Consistent**
**Given** a theme is selected
**When** I navigate through the application
**Then** all components (cards, tables, modals, popovers, sidebar) use theme colors
**And** there are no white/mismatched boxes on colored backgrounds
**And** text remains readable with appropriate contrast

**Prerequisites:**
- None (uses existing theme infrastructure)

**Technical Notes:**
- CSS variables in `globals.css` for `.light-blue` and `.dark-navy` classes
- Theme store extended: `type Theme = 'light' | 'dark' | 'light-blue' | 'dark-navy' | 'system'`
- THEMES constant exported for UI display
- User menu updated with DropdownMenuSub for theme selection
- Reference: UX spec, accessibility guidelines (WCAG color contrast)

**Files Modified:**
- `frontend/src/app/globals.css` - Added two new theme classes
- `frontend/src/lib/stores/theme-store.ts` - Extended Theme type, added THEMES constant
- `frontend/src/components/layout/user-menu.tsx` - Added theme selector submenu

---

## Story 5.22: Document Tags (NEW)

As a **knowledge base user with ADMIN or WRITE permission**,
I want **to add tags to documents**,
So that **I can categorize, organize, and filter documents more effectively**.

**Priority:** MEDIUM
**Estimated Effort:** 1-2 days
**Story Points:** 3
**Owner:** Dev
**Status:** DRAFTED

**Context:** LumiKB has a robust tagging system for Knowledge Bases. This story extends the same pattern to documents, enabling document organization, enhanced filtering, and improved search. Tags are stored in the existing `documents.metadata` JSONB column (no migration required).

**Acceptance Criteria:**

**AC-5.22.1: Users can add tags during document upload**
**Given** I am a user with ADMIN or WRITE permission on a KB
**When** I upload a document
**Then** I see an optional "Tags" input field
**And** I can enter tags (comma or Enter to add)
**And** a maximum of 10 tags per document, 50 chars each
**And** tags are saved to document metadata on upload

**AC-5.22.2: Tags are displayed in document list**
**Given** I am viewing the KB dashboard document list
**When** documents have tags
**Then** tags display as badges next to each document
**And** truncated if >3 tags (show "+N more")

**AC-5.22.3: Users with ADMIN/WRITE can edit document tags**
**Given** I have ADMIN or WRITE permission
**When** I click the "Edit tags" button on a document
**Then** a modal opens to add/remove tags
**And** changes save on "Save" click

**AC-5.22.4: Users with READ permission cannot edit tags**
**Given** I have only READ permission
**When** I view documents
**Then** I see tags (read-only)
**And** I do NOT see an "Edit tags" button

**AC-5.22.5: Tags are searchable in document filtering**
**Given** I am on the KB dashboard
**When** I filter by tag name
**Then** matching documents are shown (case-insensitive)

**Prerequisites:**
- None (builds on existing document infrastructure)

**Technical Notes:**
- Tags stored in `documents.metadata.tags` JSONB array
- Follows KB tags pattern (kb-tags-feature-implementation.md)
- PATCH `/documents/{id}/tags` endpoint with permission check
- DocumentTagInput, DocumentEditTagsModal components
- See: docs/sprint-artifacts/5-22-document-tags.md

---

## Story 5.23: Document Processing Progress Screen (NEW)

As a **knowledge base user with ADMIN or WRITE permission**,
I want **to view detailed document processing status**,
So that **I can monitor progress, identify failures, and troubleshoot issues**.

**Priority:** HIGH (PRIORITY)
**Estimated Effort:** 2-3 days
**Story Points:** 8
**Owner:** Dev
**Status:** DRAFTED

**Context:** The current document list shows only basic status (pending/processing/processed/failed). This story provides a detailed processing view showing per-step status (Upload → Parse → Chunk → Embed → Index), errors, and chunk counts. Accessible as a new tab in the KB dashboard.

**Acceptance Criteria:**

**AC-5.23.1: Processing tab visible to ADMIN/WRITE users**
**Given** I am viewing the KB dashboard
**And** I have ADMIN or WRITE permission
**When** the page loads
**Then** I see a "Processing" tab alongside existing tabs
**And** clicking it shows the processing status view

**AC-5.23.2: Processing table with comprehensive filters**
**Given** I am on the Processing tab
**When** the page loads
**Then** I see a filter bar with:
- Document name (text search)
- File type (dropdown)
- Date range (date picker)
- Status (pending/processing/processed/failed)
- Current step (upload/parse/chunk/embed/index)
**And** filters apply immediately (no "Apply" button)

**AC-5.23.3: Per-document step status displayed**
**Given** I view the processing table
**When** documents are listed
**Then** each row shows:
- Document name, file type, upload date
- Overall status (color-coded)
- Current/completed step
- Step progress indicator (5-step pipeline)
- Chunk count (if available)
- "View Details" button

**AC-5.23.4: Processing details modal with step-level info**
**Given** I click "View Details" on a document
**When** the modal opens
**Then** I see detailed step-by-step status:
- Each step: pending/in_progress/completed/failed
- Timestamp for each step
- Error message if step failed
- Retry button for failed steps (if applicable)

**AC-5.23.5: Auto-refresh with 10-second interval**
**Given** I am on the Processing tab
**When** documents are processing
**Then** the table auto-refreshes every 10 seconds
**And** I see a "Last updated" timestamp
**And** I can manually refresh with a button

**AC-5.23.6: READ users cannot access Processing tab**
**Given** I have only READ permission on the KB
**When** I view the dashboard
**Then** I do NOT see the "Processing" tab

**Prerequisites:**
- None (extends existing document infrastructure)

**Technical Notes:**
- Database: Add `processing_steps`, `current_step`, `step_errors` JSONB columns to documents table
- API: GET `/knowledge-bases/{kb_id}/documents/processing`, GET `/documents/{doc_id}/processing-details`
- Frontend: ProcessingTab, DocumentProcessingTable, ProcessingFilterBar, ProcessingDetailsModal
- Auto-refresh: React Query with 10s refetchInterval
- See: docs/sprint-artifacts/5-23-document-processing-progress.md

---

## Story 5.24: KB Dashboard Document Filtering & Pagination (NEW)

As a **knowledge base user**,
I want **to filter and paginate the document list in the KB dashboard**,
So that **I can quickly find specific documents in large knowledge bases**.

**Priority:** MEDIUM
**Estimated Effort:** 1-2 days
**Story Points:** 3
**Owner:** Dev
**Status:** DRAFTED

**Context:** As KBs grow, the document list becomes difficult to navigate. This story applies the same filtering/pagination patterns from Story 5-2 (Audit Log Viewer) to the KB dashboard document list.

**Acceptance Criteria:**

**AC-5.24.1: Document list displays filter bar**
**Given** I am viewing the KB dashboard with an active KB
**When** the page loads
**Then** I see a filter bar with:
- Search (text input for document name)
- Type (dropdown: PDF, DOCX, TXT, etc.)
- Status (dropdown: processed, processing, failed, pending)
- Tags (multi-select, from Story 5-22)
- Date Range (date picker)
- Clear Filters button

**AC-5.24.2: Filters update document list in real-time**
**Given** I have applied filters
**When** I change a filter value
**Then** the document list updates automatically
**And** loading indicator shows during refresh
**And** empty state message if no matches

**AC-5.24.3: Document list is paginated**
**Given** the KB has more than 50 documents
**When** I view the document list
**Then** I see pagination controls:
- Current page indicator (e.g., "Page 1 of 5")
- Previous/Next buttons
- Page size selector (25, 50, 100)
- Total document count

**AC-5.24.4: Filter state persists in URL**
**Given** I have applied filters
**When** I refresh the page or share the URL
**Then** the same filters are applied
**URL format:** `/dashboard?kb=<id>&status=failed&type=pdf&page=2`

**AC-5.24.5: Filter by tags shows matching documents**
**Given** documents have tags (from Story 5-22)
**When** I select tags in the filter
**Then** only documents with ALL selected tags are shown

**Prerequisites:**
- Story 5-22 (Document Tags) - tag filter requires tags

**Technical Notes:**
- Follows Story 5-2 (Audit Log Viewer) filtering/pagination pattern
- URL param sync via useDocumentFilters hook
- Debounced search (300ms) to prevent excessive API calls
- Default 50 items per page
- See: docs/sprint-artifacts/5-24-kb-dashboard-filtering.md

---

## Story 5.25: Document Chunk Viewer - Backend API (NEW)

As a **user or admin**,
I want **API endpoints to retrieve document chunks and stream original document content**,
So that **the frontend can display a split-pane viewer for citation verification**.

**Priority:** HIGH
**Estimated Effort:** 1 day
**Story Points:** 3
**Owner:** Dev
**Status:** TODO

**Context:** Users need to verify that AI-generated citations actually come from source documents. Admins need to inspect document processing quality. This story provides the backend API foundation for the Document Chunk Viewer feature.

**Key Discovery:** The existing architecture already stores:
- Original files in MinIO (PDF, DOCX, MD, TXT preserved)
- Chunk metadata in Qdrant with `char_start`, `char_end`, `page_number`
- Full `chunk_text` in vector payloads

This means minimal backend changes are needed - primarily new endpoints to expose existing data.

**Acceptance Criteria:**

**AC-5.25.1: Chunk retrieval endpoint returns chunks with metadata**
**Given** a document has been processed and indexed
**When** I call `GET /api/v1/documents/{id}/chunks`
**Then** I receive a JSON response containing:
- `chunks`: Array of chunk objects
- `total`: Total number of chunks
- `document_id`: The document UUID
**And** each chunk object contains:
- `chunk_index`: Position in sequence (0-indexed)
- `chunk_text`: Full text content
- `char_start`: Starting character offset in source
- `char_end`: Ending character offset in source
- `page_number`: Page number (PDF only, null for others)
- `paragraph_index`: Paragraph index (DOCX/MD)

**AC-5.25.2: Chunk search filters by text content**
**Given** a document has multiple chunks
**When** I call `GET /api/v1/documents/{id}/chunks?search=authentication`
**Then** only chunks containing "authentication" (case-insensitive) are returned
**And** the `total` reflects the filtered count

**AC-5.25.3: Chunk pagination supports large documents**
**Given** a document has 500+ chunks
**When** I call `GET /api/v1/documents/{id}/chunks?skip=0&limit=50`
**Then** I receive exactly 50 chunks (or fewer if near end)
**And** `total` shows the full count

**AC-5.25.4: Document content endpoint streams original file**
**Given** a document exists in MinIO
**When** I call `GET /api/v1/documents/{id}/content`
**Then** the original file is streamed with correct headers:
- `Content-Type`: Matches original MIME type
- `Content-Disposition`: `inline; filename="original_name.pdf"`
- `Content-Length`: File size in bytes

**AC-5.25.5: DOCX content can be converted to HTML (optional)**
**Given** a DOCX document exists
**When** I call `GET /api/v1/documents/{id}/content?format=html`
**Then** the DOCX is converted to semantic HTML using mammoth
**And** the response `Content-Type` is `text/html`

**AC-5.25.6: Endpoints enforce document access permissions**
**Given** I do not have READ access to a KB
**When** I call chunk or content endpoints
**Then** I receive 403 Forbidden
**Given** the document does not exist
**Then** I receive 404 Not Found

**Prerequisites:**
- Epic 2 complete (document processing pipeline functional)

**Technical Notes:**
- Create ChunkService to query Qdrant for document chunks
- Stream files from MinIO using existing download_file_stream()
- Optional: Add mammoth dependency for DOCX→HTML conversion
- See: docs/sprint-artifacts/5-25-document-chunk-viewer-backend.md

---

## Story 5.26: Document Chunk Viewer - Frontend UI (NEW)

As a **user or admin**,
I want **a split-pane document viewer showing original documents alongside extracted text chunks**,
So that **I can verify AI citations and inspect document processing quality**.

**Priority:** HIGH
**Estimated Effort:** 2-3 days
**Story Points:** 8
**Owner:** Dev
**Status:** TODO

**Context:** This is the frontend implementation for the Document Chunk Viewer feature. It displays original documents (PDF, DOCX, Markdown, Text) alongside extracted chunks with highlighting support.

**Acceptance Criteria:**

**AC-5.26.1: Document detail modal has "View & Chunks" tab**
**Given** I open a document detail modal
**When** the modal renders
**Then** I see tab navigation with "Details" and "View & Chunks" tabs
**And** clicking "View & Chunks" shows the split-pane viewer

**AC-5.26.2: Split-pane layout with resizable panels**
**Given** I am on the "View & Chunks" tab
**When** the viewer loads
**Then** I see a split-pane layout:
- Left panel (60%): Document viewer
- Right panel (40%): Chunk sidebar
**And** I can drag the divider to resize panels
**And** on mobile (<1024px), panels stack vertically

**AC-5.26.3: Chunk sidebar with search and list**
**Given** the chunk sidebar is visible
**When** chunks are loaded
**Then** I see:
- Search box at top
- Chunk count indicator (e.g., "42 chunks")
- Scrollable list of chunk previews

**AC-5.26.4: Chunks expand to full text**
**Given** I see a collapsed chunk
**When** I click on it
**Then** it expands to show full text
**And** other chunks collapse (accordion behavior)
**And** I see a collapse button at bottom-right

**AC-5.26.5: Search filters chunks in real-time**
**Given** I type in the search box
**When** I pause typing (300ms debounce)
**Then** the chunk list filters to show only matching chunks
**And** the chunk count updates

**AC-5.26.6: PDF viewer with page navigation and highlighting**
**Given** I view a PDF document
**When** I click a chunk
**Then** the PDF scrolls to the relevant page
**And** the text is highlighted (yellow overlay)
**And** I can navigate pages with prev/next buttons

**AC-5.26.7: DOCX viewer with paragraph highlighting**
**Given** I view a DOCX document
**When** I click a chunk
**Then** the viewer scrolls to the paragraph
**And** the paragraph is highlighted (yellow background)

**AC-5.26.8: Markdown viewer with character highlighting**
**Given** I view a Markdown document
**When** I click a chunk
**Then** the viewer scrolls to the position
**And** the character range is highlighted

**AC-5.26.9: Text viewer with character highlighting**
**Given** I view a plain text document
**When** I click a chunk
**Then** the viewer scrolls to the line
**And** the character range is highlighted

**AC-5.26.10: Loading, error, and empty states handled**
**Given** the viewer is loading
**Then** I see skeleton placeholders
**Given** an error occurs
**Then** I see an error message with retry button
**Given** a document has no chunks
**Then** I see an empty state message

**Prerequisites:**
- Story 5-25: Document Chunk Viewer - Backend API

**Technical Notes:**
- Dependencies: react-pdf, pdfjs-dist, docx-preview, react-markdown, react-resizable-panels, @tanstack/react-virtual
- PDF.js worker must be configured (CDN or public folder)
- Virtual scroll required for performance with 1000+ chunks
- Blob URLs must be revoked on unmount to prevent memory leaks
- See: docs/sprint-artifacts/5-26-document-chunk-viewer-frontend.md

---

## Summary

Epic 5 establishes the administration and polish features for LumiKB:

| Story | Points | Key Deliverable |
|-------|--------|-----------------|
| 5.0 | - | Epic 3 & 4 Integration Completion (CRITICAL) |
| 5.1 | - | Admin dashboard overview |
| 5.2 | - | Audit log viewer |
| 5.3 | - | Audit log export |
| 5.4 | - | Processing queue status |
| 5.5 | - | System configuration |
| 5.6 | - | KB statistics (admin view) |
| 5.7 | - | Onboarding wizard |
| 5.8 | - | Smart KB suggestions |
| 5.9 | - | Recent KBs and polish items |
| 5.10 | - | Command palette test coverage (Tech Debt) |
| 5.11 | - | Epic 3 search hardening (Tech Debt) |
| 5.12 | - | ATDD integration tests transition (Tech Debt) |
| 5.13 | - | Celery beat filesystem fix (Tech Debt) |
| 5.14 | - | Search audit logging |
| 5.15 | - | Epic 4 ATDD transition (Tech Debt) |
| 5.16 | - | Docker E2E testing infrastructure |
| 5.17 | - | Main application navigation menu |
| 5.18 | - | User management UI |
| 5.19 | - | Group management |
| 5.20 | - | Role & KB permission management UI |
| 5.21 | - | Theme system (DONE) |
| 5.22 | - | Document tags |
| 5.23 | - | Document processing progress |
| 5.24 | - | KB dashboard filtering & pagination |
| 5.25 | - | Document chunk viewer - Backend API |
| 5.26 | - | Document chunk viewer - Frontend UI |

**Total Stories:** 26

---

_For implementation: Use the `dev-story` workflow to execute individual stories from this breakdown._
