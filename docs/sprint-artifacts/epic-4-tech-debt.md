# Epic 4 Technical Debt Tracking

**Epic:** Epic 4 - Chat & Document Generation
**Created:** 2025-11-26
**Status:** ARCHIVED - Migrated to Epic 7 Tech Debt

---

## Migration Notice

> **IMPORTANT:** This file is archived. All active tech debt has been consolidated into:
> **[epic-7-tech-debt.md](./epic-7-tech-debt.md)**
>
> **Migration Date:** 2025-12-10
> **Reason:** Single-source-of-truth for all project tech debt

---

## Original Purpose (Historical)

Track deferred technical work from Epic 4 stories that:
- Doesn't block production deployment
- Improves quality/maintainability/security
- Should be addressed in Epic 5 (Story 5.15)

---

## Tech Debt Items

### TD-4.0-1: ATDD Test Suite Transition to GREEN Phase

**Source:** Epic 4 - All Stories (4.1-4.10)
**Priority:** HIGH
**Effort:** 16-20 hours

**Description:**
61 ATDD tests were written in RED phase before implementation (following TDD best practices). Tests currently FAIL as expected and need infrastructure setup + transition to GREEN in Epic 5.

**Test Breakdown:**
- Backend API (pytest): 22 tests
- Frontend E2E (Playwright): 16 tests
- Component (Vitest): 9 tests
- **Total**: 47 active tests (61 scenarios documented)

**Missing Test Infrastructure:**
- [ ] Conversation factory with multi-turn fixtures
- [ ] Generation request factory (template-based)
- [ ] Citation factory (complex patterns)
- [ ] Draft factory with confidence scores
- [ ] Redis test fixtures (fakeredis integration)
- [ ] LiteLLM mock for streaming responses
- [ ] Export validation helpers (python-docx, PyPDF2)

**Current State:**
- ✅ All 61 test scenarios written and documented
- ✅ Test files created in proper locations
- ✅ data-testid attributes documented
- ✅ Mock requirements specified
- ❌ Test fixtures not implemented (0/7)
- ❌ Tests in RED phase (expected - pre-implementation)

**Why Deferred:**
Following Epic 3 pattern of ATDD-first development with deferred GREEN transition. Tests document requirements and guide implementation, but full test infrastructure setup deferred to Epic 5 hardening phase.

**Proposed Resolution:**
- Epic 5, Story 5.15: "Epic 4 ATDD Transition to GREEN"
- Implement all 7 test fixtures
- Transition all 47 tests to passing (GREEN)
- Validate risk mitigations (R-001, R-002, R-004, R-005)

**Reference Documents:**
- [docs/sprint-artifacts/atdd-checklist-epic-4.md](atdd-checklist-epic-4.md) - Implementation guide
- [docs/sprint-artifacts/test-design-epic-4.md](test-design-epic-4.md) - Risk assessment

---

### TD-4.2-1: SSE Streaming Reconnection Logic

**Source:** Story 4.2 (Chat Streaming UI)
**Priority:** Medium
**Effort:** 3 hours

**Description:**
SSE (Server-Sent Events) streaming for chat lacks automatic reconnection on connection drop.

**Missing Functionality:**
- Automatic retry on connection loss (exponential backoff)
- User notification of connection issues
- Graceful degradation to polling (fallback)

**Current State:**
- ✅ SSE streaming works for happy path
- ✅ Time-to-first-token <2s (performance target met)
- ❌ No retry logic on network interruption
- ❌ User sees "loading..." indefinitely on failure

**Why Deferred:**
MVP pilot operates on stable network. Reconnection logic improves UX but not blocking for controlled pilot environment.

**Proposed Resolution:**
Add SSE reconnection middleware in Epic 5 or based on pilot feedback.

---

### TD-4.5-1: Confidence Scoring Algorithm Validation

**Source:** Story 4.5 (Draft Generation Streaming)
**Priority:** High
**Effort:** 4 hours

**Description:**
Confidence scoring formula needs empirical validation against pilot user feedback.

**Current Formula:**
```python
confidence = (
    avg_retrieval_score * 0.5 +
    source_coverage * 0.3 +
    semantic_coherence * 0.2
)
```

**Questions Requiring Pilot Data:**
- Are 80/50% thresholds appropriate for high/low classification?
- Does formula correlate with perceived draft quality?
- Should formula weight retrieval_score higher?
- Do users trust amber (medium) confidence sections?

**Current State:**
- ✅ Confidence calculated per section
- ✅ Thresholds implemented (80% high, 50% low)
- ✅ UI highlights sections (green/amber/red)
- ❌ Formula not validated with real users
- ❌ Thresholds are educated guesses

**Why Deferred:**
Initial formula based on industry best practices (weighted retrieval + coverage). Requires pilot feedback to tune. Not blocking MVP deployment.

**Proposed Resolution:**
- Collect pilot feedback on confidence accuracy (Story 5.x or post-MVP)
- Analyze false positives (high confidence but bad content)
- Analyze false negatives (low confidence but good content)
- Adjust formula weights and thresholds based on data

---

### TD-4.5-2: Draft Generation Integration Tests and Performance Validation

**Source:** Story 4.5 (Draft Generation Streaming)
**Priority:** Medium
**Effort:** 3 hours

**Description:**
Story 4.5 implements SSE-based draft generation streaming with progressive citation extraction. Integration tests and performance validation require LiteLLM mock fixtures and real LLM integration for accurate performance measurement.

**Current State:**
- ✅ Backend: SSE streaming endpoint `/api/v1/generate/stream` implemented
- ✅ Backend: Progressive citation extraction during streaming (regex-based)
- ✅ Frontend: StreamingDraftView 3-panel layout component
- ✅ Frontend: useGenerationStream hook with AbortController
- ✅ Backend unit tests: 6/6 passing (generation_service.py)
- ✅ Frontend tests: 27/27 passing (9 hook tests + 18 component tests)
- ❌ Integration tests: 8 tests created but skipped (require LiteLLM mocks)
- ❌ AC5 Performance validation: Cannot measure <3s first-token latency without real LLM
- ❌ AC6 Draft persistence: Deferred to Story 4.6 (architectural decision)

**Required Test Infrastructure:**
1. **LiteLLM Mock for Streaming** (`mock_litellm_stream` fixture):
   - Mock `LiteLLMClient.chat_completion()` async generator
   - Return realistic token chunks with citation markers [1], [2]
   - Simulate streaming rate (50-100 tokens/second)
   - Support cancellation via AbortController

2. **Performance Validation** (requires real LLM):
   - Measure time to first SSE event (target: <2s)
   - Measure time to first content chunk (target: <3s)
   - Measure streaming rate (target: 50-100 tokens/second)
   - Measure citation event latency (target: <500ms after marker)

**Blocked Tests:**
- `backend/tests/integration/test_generation_streaming.py` - 8 integration tests (all skipped)
  - SSE connection and headers
  - Event order (sources_retrieved → generation_start → content_chunk → citation → done)
  - Citation detection and emission
  - Error handling (LLM errors, insufficient sources)
  - Permission enforcement
  - Cancellation (client disconnect)

**Production Impact:**
None - core implementation is production-ready:
- SSE streaming with proper event schemas (StatusEvent, TokenEvent, CitationEvent, DoneEvent)
- Progressive citation extraction using regex `\[(\d+)\]`
- AbortController cancellation support
- Mock data strategy for Story 4.5 (real Qdrant retrieval deferred to Story 5.15)
- All unit tests passing

**Why Deferred:**
Story 4.5 focused on streaming infrastructure implementation. Integration testing and performance validation require the same LiteLLM mock infrastructure as Stories 4.1 and 4.2. Story 5.15 consolidates all Epic 4 ATDD test hardening.

**Proposed Resolution:**
- Epic 5, Story 5.15: "Epic 4 ATDD Transition to GREEN"
- Implement LiteLLM streaming mock fixture (extends TD-4.1-1 fixture)
- Transition 8 generation streaming integration tests to GREEN
- Add performance measurement tests with real LLM
- Validate AC1 (SSE event sequence), AC3 (citation accumulation), AC4 (cancellation), AC5 (performance targets)
- Note: AC6 (draft persistence) resolved in Story 4.6, not Story 5.15

**Reference:**
- [backend/tests/integration/test_generation_streaming.py](../../backend/tests/integration/test_generation_streaming.py) - Test implementation (8 tests skipped)
- [backend/app/api/v1/generate_stream.py](../../backend/app/api/v1/generate_stream.py) - SSE endpoint
- [backend/app/services/generation_service.py:160-349](../../backend/app/services/generation_service.py#L160-L349) - generate_document_stream method
- [docs/sprint-artifacts/4-5-draft-generation-streaming.md](./4-5-draft-generation-streaming.md) - Story details

---

### TD-4.7-1: Frontend Component Test Imports and Execution

**Source:** Story 4.7 (Document Export) - Test Automation
**Priority:** High
**Effort:** 2 hours
**Status:** ⏳ Pending - Tests generated, need import fixes

**Description:**
Story 4.7 test automation generated 10 comprehensive frontend component tests (ExportModal, VerificationDialog, useExport hook). Tests are well-structured with proper data-testid queries but fail due to component import/export mismatches.

**Current State:**
- ✅ All data-testid attributes added to components (export-modal, verification-dialog, draft-editor)
- ✅ radio-group UI component installed via shadcn/ui
- ✅ 10 component tests generated with proper GWT format and priority tags
- ❌ Tests fail: Import errors (default vs named imports)
- ❌ Component export declarations need verification

**Test Files Created:**
1. `frontend/src/components/generation/__tests__/export-modal.test.tsx` (2 tests)
2. `frontend/src/components/generation/__tests__/verification-dialog.test.tsx` (5 tests)
3. `frontend/src/hooks/__tests__/useExport.test.ts` (6 tests)

**Required Fixes:**
1. Verify ExportModal exports as named export: `export function ExportModal`
2. Verify VerificationDialog exports as named export: `export function VerificationDialog`
3. Update test imports if components use default exports:
   ```typescript
   // If component uses: export default function ExportModal
   import ExportModal from '../export-modal';

   // If component uses: export function ExportModal
   import { ExportModal } from '../export-modal';
   ```

**Why High Priority:**
Component tests validate critical AC1 (format selection) and AC2 (verification prompt). Frontend test coverage essential for release confidence.

**Proposed Resolution:**
- Epic 5, Story 5.15: "Epic 4 ATDD Transition to GREEN"
- Fix component import/export declarations (30 min)
- Run tests to verify GREEN status (30 min)
- Add to CI/CD pipeline (1 hour)

**Reference:**
- [docs/sprint-artifacts/automation-summary-story-4-7.md](./automation-summary-story-4-7.md) - Complete automation summary
- Test files: All generated and ready, just need import fixes

---

### TD-4.7-2: Backend Integration Test Execution

**Source:** Story 4.7 (Document Export) - Test Automation
**Priority:** High
**Effort:** 1 hour
**Status:** ⏳ Pending - Tests ready, need database + fixtures

**Description:**
7 backend integration tests exist for export API (DOCX, PDF, Markdown) covering AC1-AC5. Tests are properly structured but require test database and fixtures to run.

**Current State:**
- ✅ 7 integration tests created with proper structure
- ✅ Test coverage: DOCX export, PDF export, Markdown export, permissions, validation, error handling
- ✅ Tests follow pytest best practices
- ❌ Tests not executed yet (require database + fixtures)
- ❌ httpx dependency missing in test environment

**Test File:**
- `backend/tests/integration/test_export_api.py` (7 tests)

**Prerequisites:**
1. Test database running: `docker-compose up -d postgres`
2. Test fixtures configured: `authenticated_user`, `kb_with_permission`, `draft_factory`
3. Install httpx: Already in pyproject.toml

**Expected Result:** 7/7 tests passing

**Why High Priority:**
Integration tests validate end-to-end export API functionality including permission checks, format validation, and file generation. Critical for AC coverage.

**Proposed Resolution:**
- Epic 5, Story 5.15: "Epic 4 ATDD Transition to GREEN"
- Ensure test database is running (15 min)
- Run integration tests: `pytest tests/integration/test_export_api.py -v` (15 min)
- Debug any failures and achieve GREEN status (30 min)

**Reference:**
- [backend/tests/integration/test_export_api.py](../../backend/tests/integration/test_export_api.py) - Test implementation

---

### TD-4.7-3: E2E Test Execution and Validation

**Source:** Story 4.7 (Document Export) - Test Automation
**Priority:** Medium
**Effort:** 2 hours
**Status:** ⏳ Pending - Tests ready, need full stack

**Description:**
6 E2E Playwright tests cover complete export workflow from UI interaction to file download. All data-testid attributes are in place. Tests require full stack (backend + frontend) running.

**Current State:**
- ✅ 6 E2E tests generated with comprehensive scenarios
- ✅ All data-testid attributes added to components
- ✅ Tests cover: DOCX export (P0), PDF export, Markdown export, verification flow, cancellation, session storage
- ❌ Tests not executed yet (require full stack)
- ❌ Playwright browsers may need installation

**Test File:**
- `frontend/e2e/tests/export/document-export.spec.ts` (6 tests)

**Prerequisites:**
1. Backend running: `make dev` (port 8000)
2. Frontend running: `npm run dev` (port 3000)
3. Database seeded with demo data
4. Playwright browsers: `npx playwright install`

**Test Coverage:**
- P0: DOCX export happy path (critical)
- P1: PDF export, Markdown export, verification workflow, cancellation
- P2: Session storage persistence

**Why Medium Priority:**
E2E tests provide highest confidence but are slowest to run. Integration tests cover API layer. E2E validates full user journey including UI interaction.

**Proposed Resolution:**
- Epic 5, Story 5.15: "Epic 4 ATDD Transition to GREEN"
- Set up full stack locally or in CI (30 min)
- Run E2E tests: `npx playwright test tests/export/` (30 min)
- Debug failures and achieve GREEN status (1 hour)

**Reference:**
- [frontend/e2e/tests/export/document-export.spec.ts](../../frontend/e2e/tests/export/document-export.spec.ts) - Test implementation
- [docs/sprint-artifacts/automation-summary-story-4-7.md](./automation-summary-story-4-7.md) - Detailed test plan

---

### TD-4.7-4: AC6 Export Audit Logging Implementation

**Source:** Story 4.7 (Document Export) - Acceptance Criteria
**Priority:** Medium
**Effort:** 2 hours
**Status:** ⏳ Pending - Code exists (commented), needs audit service

**Description:**
AC6 (Export Audit Logging) implementation is complete but commented out in export API endpoint. Waiting for audit service infrastructure from Epic 5.

**Current State:**
- ✅ Audit logging code written and documented (lines 445-459 in drafts.py)
- ✅ Audit event schema defined (user_id, action, resource_type, details)
- ✅ Privacy constraints respected (no content logged, only metadata)
- ❌ Code commented out (TODO comment)
- ❌ Audit service not yet available
- ❌ 8th integration test for audit logging not added

**Commented Code Location:**
- `backend/app/api/v1/drafts.py:445-459` - Audit logging implementation

**Why Deferred:**
AC6 depends on audit service infrastructure planned for Epic 5 (Story 5.14: Search Audit Logging). Export functionality is complete without audit logging. Logging is observability enhancement, not blocking MVP.

**Proposed Resolution:**
- Epic 5, Story 5.14: "Search Audit Logging"
- Implement audit service infrastructure
- Uncomment audit logging code in export endpoint
- Add 8th integration test: `test_export_audit_logging`
- Validate audit event fields and privacy constraints

**Reference:**
- [backend/app/api/v1/drafts.py](../../backend/app/api/v1/drafts.py) - Export endpoint with TODO
- [docs/sprint-artifacts/4-7-document-export.md](./4-7-document-export.md) - AC6 requirements

---

### TD-4.7-5: PDF Export Citation Formatting Quality

**Source:** Story 4.7 (Document Export)
**Priority:** Low
**Effort:** 4 hours

**Description:**
PDF export uses basic text-based citation rendering. Footnotes may not render cleanly for complex documents.

**Current Implementation:**
- Citations rendered as inline text: "... OAuth [1] ..."
- Footnote section added at document end
- Uses reportlab

**Potential Issues:**
- Page breaks may split footnotes awkwardly
- Multi-column layouts not supported
- Custom fonts/styling limited

**Current State:**
- ✅ PDF export functional (basic)
- ✅ Citations preserved (text-based)
- ❌ Footnote formatting not production-polished
- ❌ No visual regression testing

**Why Deferred:**
DOCX export is primary format for MVP (better editing). PDF is convenience export. Basic PDF sufficient for pilot, can enhance based on feedback.

**Proposed Resolution:**
- Gather pilot feedback on PDF quality
- If needed, upgrade to professional PDF library (e.g., WeasyPrint with CSS)
- Add visual regression tests for PDF output (Playwright PDF snapshots)

---

### TD-4.7-6: Export Rate Limiting

**Source:** Story 4.7 (Document Export)
**Priority:** Low
**Effort:** 2 hours

**Description:**
No rate limiting on export endpoint. User could spam export requests.

**Missing Protection:**
- Per-user rate limit (e.g., 10 exports/minute)
- Abuse detection/alerting
- Export queue management for large documents

**Current State:**
- ✅ Export works synchronously
- ✅ Verification prompt reduces accidental spam
- ❌ No technical rate limiting
- ❌ Large exports could block server

**Why Deferred:**
Pilot has limited users (<10). Abuse unlikely. Performance not concern for MVP scale.

**Proposed Resolution:**
Add rate limiting in Epic 5 or when scaling beyond pilot (e.g., with Redis-based limiter).

---

### TD-4.8-1: Generation Feedback Audit Logging (AC6)

**Source:** Story 4.8 (Generation Feedback & Recovery)
**Priority:** Medium
**Effort:** 2 hours
**Status:** ⏳ Pending - Code exists (commented), needs audit service

**Description:**
AC6 (Feedback Audit Logging) implementation is complete but commented out in feedback API endpoint. Waiting for audit service infrastructure from Epic 5.

**Current State:**
- ✅ Audit logging code written and documented (lines 535-549 in drafts.py)
- ✅ Audit event schema defined (user_id, action, resource_type, details)
- ✅ Privacy constraints respected (no content logged, only metadata)
- ❌ Code commented out (TODO comment)
- ❌ Audit service not yet available

**Commented Code Location:**
- `backend/app/api/v1/drafts.py:535-549` - Audit logging implementation

**Why Deferred:**
AC6 depends on audit service infrastructure planned for Epic 5 (Story 5.14: Search Audit Logging). Feedback functionality is complete without audit logging. Logging is observability enhancement, not blocking MVP.

**Proposed Resolution:**
- Epic 5, Story 5.14: "Search Audit Logging"
- Implement audit service infrastructure
- Uncomment audit logging code in feedback endpoint
- Validate audit event fields and privacy constraints

**Reference:**
- [backend/app/api/v1/drafts.py](../../backend/app/api/v1/drafts.py) - Feedback endpoint with TODO
- [docs/sprint-artifacts/4-8-generation-feedback-recovery.md](./4-8-generation-feedback-recovery.md) - AC6 requirements

---

### TD-4.8-2: Frontend Feedback Button Integration

**Source:** Story 4.8 (Generation Feedback & Recovery)
**Priority:** Medium
**Effort:** 3 hours
**Status:** ⏳ Pending - Components ready, DraftEditor integration deferred

**Description:**
AC1 "This doesn't look right" button integration with DraftEditor deferred. All UI components (FeedbackModal, RecoveryModal, ErrorRecoveryDialog) and useFeedback hook implemented and ready for integration.

**Current State:**
- ✅ FeedbackModal component created (5 feedback types, radio buttons, "Other" text area)
- ✅ RecoveryModal component created (alternative suggestions display)
- ✅ ErrorRecoveryDialog component created (error recovery UI)
- ✅ useFeedback hook implemented (POST /api/v1/drafts/{id}/feedback)
- ✅ Backend API endpoint functional (3 alternatives per feedback type)
- ❌ DraftEditor button not added (AC1 incomplete)
- ❌ Regeneration flow not wired up (AC4 partial)

**Missing Integration:**
1. Add "This doesn't look right" button to DraftEditor toolbar (left of Export button)
2. Wire button click → FeedbackModal open
3. Wire FeedbackModal submit → useFeedback.handleSubmit
4. Wire alternative selection → regeneration flow
5. Show ErrorRecoveryDialog on generation failures

**Why Deferred:**
Core feedback infrastructure complete and tested (15 unit tests passing, zero linting errors). DraftEditor integration requires UI/UX coordination with existing draft editing flow (Story 4.6). Following Epic 4 pattern of infrastructure-first, integration-second.

**Proposed Resolution:**
- Epic 5, Story 5.15: "Epic 4 ATDD Transition to GREEN"
- Add feedback button to DraftEditor toolbar
- Wire up regeneration flow with feedback context
- Add 6 E2E tests for full feedback workflow
- Validate AC1 (button visibility), AC2 (modal UX), AC3 (alternatives), AC4 (regeneration)

**Reference:**
- [frontend/src/components/generation/feedback-modal.tsx](../../frontend/src/components/generation/feedback-modal.tsx) - Modal implementation
- [frontend/src/hooks/useFeedback.ts](../../frontend/src/hooks/useFeedback.ts) - Hook implementation
- [docs/sprint-artifacts/4-8-generation-feedback-recovery.md](./4-8-generation-feedback-recovery.md) - Story details

---

### TD-4.8-3: Feedback and Error Recovery Test Coverage

**Source:** Story 4.8 (Generation Feedback & Recovery)
**Priority:** Medium
**Effort:** 2 hours (reduced from 5h - frontend unit tests completed)
**Status:** ✅ **Partially Complete** - Frontend unit tests PASSING (32/32), integration/E2E deferred

**Description:**
Frontend unit test coverage for feedback and error recovery completed 2025-11-29. Integration and E2E tests deferred to Epic 5. Core implementation complete with 15 backend unit tests + 32 frontend unit tests passing.

**Test Coverage Breakdown:**

**Completed Tests (2025-11-29):**
- ✅ Backend unit: 15/15 passing (FeedbackService - all feedback types, context builder, alternatives)
- ✅ **Frontend unit: 32/32 passing (all Story 4-8 components + hooks)** ← **COMPLETED 2025-11-29**
  - ✅ FeedbackModal component (6 tests): category selection, "Other" text area, submit validation, character limits
  - ✅ RecoveryModal component (7 tests): alternative display, action selection, keyboard accessibility
  - ✅ ErrorRecoveryDialog component (11 tests): recovery options, error display, empty state handling
  - ✅ useFeedback hook (8 tests): API call, loading states, error handling, async state management
- ✅ Linting: Zero errors (ruff clean)

**Deferred Tests (14 tests remaining):**
1. **Frontend Unit Tests:** ~~14 tests~~ → **0 tests** (✅ All completed 2025-11-29)

2. **Backend Integration Tests (8 tests):**
   - POST /api/v1/drafts/{id}/feedback (3 tests): valid feedback, invalid type, permission denied
   - Feedback-enhanced regeneration (3 tests): context appended, source retrieval strategies
   - Error recovery (2 tests): timeout error → recovery options, rate limit error → retry

3. **E2E Tests (6 tests):**
   - Full feedback workflow: button click → modal → submit → alternatives → regenerate
   - Error recovery workflow: generation failure → error dialog → retry
   - AC validation: button visibility, modal UX, alternative suggestions

**Why Deferred (Integration/E2E only):**
Frontend unit tests completed 2025-11-29 (32/32 passing). Integration/E2E tests better suited for Epic 5 hardening phase when full stack is stable and LLM regeneration flow is fully implemented.

**Proposed Resolution:**
- ~~Epic 5, Story 5.15: Add 14 frontend unit tests (Vitest)~~ ← **✅ COMPLETED 2025-11-29**
- Epic 5, Story 5.15: Add 8 backend integration tests (pytest)
- Epic 5, Story 5.15: Add 6 E2E tests (Playwright)
- Validate all ACs (AC1-AC6)

**Reference:**
- [backend/tests/unit/test_feedback_service.py](../../backend/tests/unit/test_feedback_service.py) - Existing 15 unit tests
- [docs/sprint-artifacts/4-8-generation-feedback-recovery.md](./4-8-generation-feedback-recovery.md) - Test requirements

---

### TD-4.6-1: Draft Editing Validation Warnings and Advanced Features

**Source:** Story 4.6 (Draft Editing)
**Priority:** Medium
**Effort:** 4 hours
**Status:** ✅ **Critical bugs fixed 2025-11-28** - Production-ready, polish deferred to Epic 5

**Description:**
Story 4.6 implements core draft editing functionality (AC1-AC5) with all critical bugs resolved. Validation warnings (AC6) and comprehensive test coverage deferred to Epic 5 hardening.

**Implemented Features (Production-Ready):**
- ✅ AC1: DraftEditor with contentEditable
- ✅ AC2: Citation preservation (HTML-based, XSS-protected) - **FIXED 2025-11-28**
- ✅ AC3: Section regeneration endpoint (stub - LLM integration TODO)
- ✅ AC4: Auto-save (5s debounce) + manual save (Ctrl+S)
- ✅ AC5: Undo/redo (10-action buffer, Ctrl+Z/Y, optimized) - **FIXED 2025-11-28**

**Critical Bugs Fixed (2025-11-28):**
- 🔴 **Fixed:** Citation markers destroyed on edit (refactored to HTML-based approach)
- 🔴 **Fixed:** XSS vulnerability (added DOMPurify sanitization)
- 🟡 **Fixed:** Undo/redo performance issues (deep equality checks)
- 🟡 **Fixed:** Keyboard handler memory leak (ref-based approach)

**Quality Metrics:**
- Before fixes: 72/100 (conditional pass with critical bugs)
- After fixes: **92/100** (production-ready)
- Frontend quality: 60/100 → **90/100** (+30 points)
- Security: 75/100 → **95/100** (+20 points)

**Deferred Features (Not Blocking Production):**
- ❌ AC6: Validation warnings for broken citations
- ❌ Section regeneration UI (endpoint exists but frontend deferred)
- ❌ Comprehensive test coverage (smoke tests created, 40+ tests deferred)

**Missing Functionality (AC6):**
1. **Real-time validation warnings:**
   - Detect orphaned citations (markers without citation data)
   - Detect unused citations (citations without markers)
   - Detect invalid marker numbers (e.g., [999] when only 3 citations exist)
   - Warning badge in status bar showing count

2. **Auto-fix options:**
   - Button to remove orphaned markers
   - Button to remove unused citations
   - Renumber citations sequentially

3. **Visual indicators:**
   - Yellow highlight on invalid markers
   - Warning icon in citations panel

**Current State (2025-11-28):**
- ✅ Backend: Draft model, CRUD endpoints, permission checks (production-ready)
- ✅ Frontend: DraftEditor with HTML-based citations, XSS protection (production-ready)
- ✅ API: POST/GET/PATCH/DELETE /api/v1/drafts + regenerate stub
- ✅ Performance: Optimized undo/redo, no memory leaks
- ✅ Security: DOMPurify XSS sanitization active
- ❌ AC6 validation: Not implemented (deferred to Epic 5)
- ❌ Regeneration UI: Not implemented (deferred to Epic 5)
- ⚠️ Tests: Smoke test structure created, 40+ comprehensive tests deferred

**Why Production-Ready Now:**
- All Priority 1 (MUST FIX) issues resolved: Citation preservation works, XSS protected
- All Priority 2 (SHOULD FIX) issues resolved: Performance optimized, memory safe
- Code quality: ESLint clean, TypeScript error-free
- Architecture: Refactored to stable HTML-based approach
- Following Epic 3/4 pattern: Core functionality complete, polish/tests in Epic 5

**Why AC6 + Tests Still Deferred:**
- Validation warnings improve UX but not required for MVP pilot
- Basic citation validation exists server-side (prevents corrupted state)
- Smoke test structure in place for future implementation
- Comprehensive testing better suited for Epic 5 ATDD hardening phase

**Proposed Resolution:**
- Epic 5, Story 5.15: "Epic 4 ATDD Transition to GREEN"
  - Implement AC6 validation warnings with auto-fix
  - Implement section regeneration UI (connect to existing endpoint)
  - Add 40+ comprehensive tests:
    - Backend: 12 unit tests (DraftService, status transitions)
    - Backend: 8 integration tests (API endpoints, permissions)
    - Frontend: 15 unit tests (useDraftEditor, useDraftUndo, HTML citation rendering)
    - E2E: 5 Playwright tests (editing flow, undo/redo, auto-save, citation persistence)

**Reference:**
- [docs/sprint-artifacts/4-6-draft-editing.md](./4-6-draft-editing.md) - Story details with code review
- [docs/sprint-artifacts/story-4-6-priority-fixes-summary.md](./story-4-6-priority-fixes-summary.md) - Priority 1 & 2 fixes summary
- [backend/app/api/v1/drafts.py](../../backend/app/api/v1/drafts.py) - Draft API endpoints
- [frontend/src/components/generation/draft-editor.tsx](../../frontend/src/components/generation/draft-editor.tsx) - Refactored draft editor (HTML-based, XSS-protected)
- [frontend/e2e/tests/draft-editing.spec.ts](../../frontend/e2e/tests/draft-editing.spec.ts) - E2E smoke test structure

---

### TD-4.9-1: Custom Template Support

**Source:** Story 4.9 (Generation Templates)
**Priority:** Low
**Effort:** 8 hours

**Description:**
Only 3 built-in templates (RFP, Checklist, Gap Analysis). No user-defined custom templates.

**Missing Functionality:**
- Admin UI to create/edit templates
- Template storage (database vs. filesystem)
- Template versioning
- Template sharing across organization

**Current State:**
- ✅ 3 templates hardcoded
- ✅ Templates produce correct structure
- ❌ No custom template support
- ❌ Template editing requires code changes

**Why Deferred:**
3 templates cover MVP pilot use cases. Custom templates are "nice-to-have" for productization but not blocking.

**Proposed Resolution:**
Add to MVP 2 backlog or based on pilot feedback requesting specific templates.

---

### TD-4.10-1: Audit Log Query Performance

**Source:** Story 4.10 (Generation Audit Logging)
**Priority:** Low
**Effort:** 2 hours

**Description:**
Audit log query endpoint lacks pagination and indexing for large datasets.

**Performance Concerns:**
- Full table scan on `audit.events` table
- No pagination (returns all results)
- No date range filtering
- No indexes on common query fields (user_id, timestamp, event_type)

**Current State:**
- ✅ All generation events logged
- ✅ Audit table structure correct
- ❌ Query performance not optimized
- ❌ No pagination implemented

**Why Deferred:**
Pilot will generate <1000 audit events. Query performance acceptable for MVP scale. Indexing and pagination needed at production scale.

**Proposed Resolution:**
- Add database indexes on audit.events (user_id, timestamp, event_type)
- Implement pagination (limit/offset or cursor-based)
- Add to Epic 5 or when audit log exceeds 10K events

---

### TD-4.1-1: Chat API Integration Test External Service Mocks

**Source:** Story 4.1 (Chat Conversation Backend)
**Priority:** Medium
**Effort:** 4 hours

**Description:**
Integration tests for Chat API require mocks for external services (Qdrant vector search and LiteLLM response generation). Tests currently fail with 500 errors due to missing service mocks.

**Current State:**
- ✅ 8 integration tests created for all 7 ACs
- ✅ Test fixtures complete (authenticated_headers, demo_kb_with_indexed_docs, empty_kb_factory)
- ✅ Unit tests: 9/9 passing (ConversationService)
- ❌ Integration tests fail: 8/8 with 500 Internal Server Error
- ❌ Missing: Qdrant mock fixture for vector search
- ❌ Missing: LiteLLM mock fixture for response generation

**Test Files:**
- `backend/tests/integration/test_chat_api.py` - 8 tests (all blocked by missing mocks)

**Required Mocks:**
1. **Qdrant Mock** (`mock_qdrant_search` fixture):
   - Mock `SearchService.search()` to return sample SearchResultSchema chunks
   - Provide realistic vector search results with scores, excerpts, metadata
   - Handle both populated KB and empty KB scenarios

2. **LiteLLM Mock** (`mock_litellm_generate` fixture):
   - Mock `LiteLLMClient.generate()` to return citation-formatted responses
   - Simulate streaming response behavior (for future Story 4.2)
   - Return realistic answers with inline [1], [2] citation markers

**Why Deferred:**
Core implementation is production-ready (all 7 ACs implemented, unit tests passing). Integration tests validate end-to-end API behavior but require complex external service mocking. Test infrastructure setup deferred to reduce Story 4.1 scope and follow Epic 3 pattern of unit-first testing.

**Proposed Resolution:**
- Epic 5, Story 5.15: "Epic 4 ATDD Transition to GREEN"
- Implement Qdrant and LiteLLM mock fixtures in `tests/integration/conftest.py`
- Transition 8 chat API integration tests to GREEN
- Validate AC coverage: AC1 (single-turn), AC2 (multi-turn), AC4 (Redis storage), AC5 (permission enforcement), AC6 (error handling), AC7 (audit logging)

**Reference:**
- [backend/tests/integration/test_chat_api.py](../../backend/tests/integration/test_chat_api.py) - Test implementation
- [docs/sprint-artifacts/4-1-chat-conversation-backend.md](./4-1-chat-conversation-backend.md) - Story details

---

### TD-4.ALL-1: Integration Test Coverage Gaps

**Source:** Epic 4 - All Stories
**Priority:** Medium
**Effort:** 8 hours

**Description:**
While 47 ATDD tests exist, some edge cases and error paths lack integration test coverage.

**Missing Test Scenarios:**

**Story 4.1 (Chat Conversation):**
- Conversation expiry after 24h (Redis TTL)
- Concurrent conversation access (race conditions)
- Conversation with corrupted Redis data

**Story 4.5 (Draft Generation):**
- Generation timeout handling (LLM takes >30s)
- Partial generation failure (streaming interrupted)
- Invalid template data structure

**Story 4.7 (Export):**
- Export with missing citations (data integrity issue)
- Export with invalid file format request
- Export file size limits (>10MB documents)

**Current Coverage:**
- ✅ Happy paths covered (47 tests)
- ✅ Security scenarios covered (R-002)
- ✅ Performance scenarios covered (R-003)
- ⚠️ Error paths partially covered
- ❌ Edge cases undercovered

**Why Deferred:**
Core functionality and high-risk scenarios (R-001 through R-005) are well-tested. Edge case coverage improves robustness but not blocking MVP.

**Proposed Resolution:**
Add edge case tests in Epic 5 hardening (Story 5.15) or based on pilot bug reports.

---

### TD-4.ALL-2: Component Test Coverage for Draft Editor

**Source:** Story 4.6 (Draft Editing)
**Priority:** Medium
**Effort:** 4 hours

**Description:**
Draft editor component lacks dedicated unit tests. Only E2E tests exist.

**Missing Component Tests:**
- Citation marker preservation during edit
- Undo/redo functionality
- Auto-save trigger timing
- Section regeneration UI
- Keyboard shortcuts

**Current Coverage:**
- ✅ E2E test: `test_draft_editing_preserves_citation_markers`
- ❌ Component unit tests: 0/5

**Why Deferred:**
E2E test validates critical citation preservation (R-008). Component tests improve refactoring safety but not blocking.

**Proposed Resolution:**
Add component tests to Epic 5 hardening (Story 5.11 or 5.15).

---

## Summary

**Total Tech Debt Items**: 19 (3 from Story 4.8: feedback audit logging, DraftEditor integration, test coverage)
**Priority Breakdown**:
- High: 4 items (ATDD transition, Confidence validation, Story 4.7 frontend tests, Story 4.7 integration tests)
- Medium: 13 items (includes Chat API mocks, Draft Generation tests, Story 4.7/4.8 E2E tests, audit logging, feedback integration)
- Low: 2 items (PDF formatting, rate limiting)

**Effort Estimate**: ~77 hours total (reduced from 80h - Story 4.8 frontend tests completed)
**Epic 5 Story 5.15 Allocation**: ~39 hours (ATDD transition + Chat API mocks + Draft Generation tests + Story 4.7/4.8 integration/E2E tests + feedback integration)
**Remaining for Future Sprints**: ~38 hours

**Story 4.8 Frontend Tests Completed (2025-11-29):**
- ✅ 32/32 frontend unit tests passing (FeedbackModal, RecoveryModal, ErrorRecoveryDialog, useFeedback)
- ✅ All test API mismatches fixed (label text, prop structures, callback signatures)
- ✅ MSW dependency installed for API mocking
- ✅ Async state handling corrected (waitFor, proper awaits)

---

## Epic 5 Story 5.15 Scope

**Story Title**: Epic 4 ATDD Transition to GREEN + Test Hardening

**Scope (39 hours - reduced from 42h):**
1. TD-4.0-1: ATDD Test Suite Transition (16-20h) ← PRIMARY FOCUS
   - Implement 7 test fixtures
   - Transition 47 tests to GREEN
   - Validate all 4 high-risk mitigations

2. TD-4.1-1: Chat API Integration Test Mocks (4h)
   - Implement Qdrant mock fixture (mock_qdrant_search)
   - Implement LiteLLM mock fixture (mock_litellm_generate)
   - Transition 8 chat API integration tests to GREEN
   - Validate AC1-AC7 coverage

3. TD-4.5-2: Draft Generation Integration Tests (3h)
   - Implement LiteLLM streaming mock fixture (extends TD-4.1-1 fixture)
   - Transition 8 generation streaming integration tests to GREEN
   - Add performance measurement tests with real LLM
   - Validate AC1, AC3, AC4, AC5 coverage

4. TD-4.7-1: Story 4.7 Frontend Component Tests (2h)
   - Fix component import/export declarations
   - Transition 10 component tests to GREEN (ExportModal, VerificationDialog, useExport)
   - Validate AC1-AC2 coverage

5. TD-4.7-2: Story 4.7 Backend Integration Tests (1h)
   - Ensure test database running
   - Transition 7 integration tests to GREEN (export API)
   - Validate AC1-AC5 coverage

6. TD-4.7-3: Story 4.7 E2E Tests (2h)
   - Set up full stack for E2E testing
   - Transition 6 E2E tests to GREEN (export workflow)
   - Validate P0 critical path (DOCX export)

7. TD-4.8-2: Story 4.8 Feedback Button Integration (3h) ← NEW
   - Add "This doesn't look right" button to DraftEditor
   - Wire up feedback modals and regeneration flow
   - Validate AC1 (button visibility), AC4 (regeneration with feedback)

8. TD-4.8-3: Story 4.8 Test Coverage (2h - reduced from 5h) ← PARTIALLY COMPLETE
   - ~~Add 14 frontend unit tests~~ ← **✅ COMPLETED 2025-11-29 (32/32 tests passing)**
   - Add 8 backend integration tests (feedback API, regeneration)
   - Add 6 E2E tests (full feedback workflow)
   - Validate AC1-AC5 coverage

**Deferred to Story 5.14 (Audit Infrastructure)**:
9. TD-4.7-4: AC6 Export Audit Logging (2h) - Requires audit service
10. TD-4.8-1: AC6 Feedback Audit Logging (2h) - Requires audit service

**Deferred to Later Stories/Sprints**:
11. TD-4.5-1: Confidence Algorithm Validation (4h) - Requires pilot feedback
12. TD-4.7-5: PDF Export Quality (4h) - Based on pilot feedback
13. TD-4.ALL-1: Integration Test Coverage Gaps (8h) - Epic 5.11 or post-pilot
14. TD-4.ALL-2: Component Test Coverage (4h) - Epic 5.11
15. TD-4.2-1, TD-4.7-6, TD-4.9-1, TD-4.10-1: MVP 2 backlog

---

## Tracking

| Item ID | Priority | Status | Assigned To | Target Sprint | Effort |
|---------|----------|--------|-------------|---------------|--------|
| TD-4.0-1 | HIGH | Planned | QA | Epic 5 (Story 5.15) | 16-20h |
| TD-4.1-1 | MEDIUM | Planned | QA/Dev | Epic 5 (Story 5.15) | 4h |
| TD-4.5-1 | HIGH | Deferred | PM/Dev | Post-Pilot | 4h |
| TD-4.5-2 | MEDIUM | Planned | QA/Dev | Epic 5 (Story 5.15) | 3h |
| TD-4.7-1 | **HIGH** | **Planned** | **QA** | **Epic 5 (Story 5.15)** | **2h** |
| TD-4.7-2 | **HIGH** | **Planned** | **QA** | **Epic 5 (Story 5.15)** | **1h** |
| TD-4.7-3 | **MEDIUM** | **Planned** | **QA** | **Epic 5 (Story 5.15)** | **2h** |
| TD-4.7-4 | MEDIUM | Planned | Dev | Epic 5 (Story 5.14) | 2h |
| TD-4.7-5 | LOW | Deferred | Dev | Based on feedback | 4h |
| TD-4.7-6 | LOW | Deferred | Dev | MVP 2 | 2h |
| TD-4.2-1 | MEDIUM | Deferred | Dev | Epic 5 or MVP 2 | 3h |
| TD-4.6-1 | MEDIUM | Deferred | Dev | Epic 5.15 | 4h |
| **TD-4.8-1** | **MEDIUM** | **Planned** | **Dev** | **Epic 5 (Story 5.14)** | **2h** |
| **TD-4.8-2** | **MEDIUM** | **Planned** | **Dev** | **Epic 5 (Story 5.15)** | **3h** |
| **TD-4.8-3** | **MEDIUM** | **✅ Partial** | **QA** | **Epic 5 (Story 5.15)** | **2h** (was 5h) |
| TD-4.9-1 | LOW | Deferred | PM/Dev | MVP 2 | 8h |
| TD-4.10-1 | LOW | Deferred | Dev | At scale | 2h |
| TD-4.ALL-1 | MEDIUM | Deferred | QA | Epic 5.11 | 8h |
| TD-4.ALL-2 | MEDIUM | Deferred | QA | Epic 5.11 | 4h |

**Story 4.7 Test Automation Summary:**
- ✅ 24 tests generated (6 E2E, 10 Component, 7 Integration, 10 Unit)
- ✅ All data-testid attributes added to components
- ✅ Backend unit tests: 10/10 PASSING
- ⏳ Frontend component tests: Need import fixes (TD-4.7-1)
- ⏳ Backend integration tests: Need database setup (TD-4.7-2)
- ⏳ E2E tests: Need full stack (TD-4.7-3)
- ⏳ Audit logging: Need audit service (TD-4.7-4)

**Story 4.8 Implementation Summary:**
- ✅ Backend: FeedbackService + API endpoint + GenerationService enhancement complete
- ✅ Frontend: FeedbackModal, RecoveryModal, ErrorRecoveryDialog, useFeedback hook complete
- ✅ Backend unit tests: 15/15 PASSING (FeedbackService)
- ✅ **Frontend unit tests: 32/32 PASSING** ← **COMPLETED 2025-11-29**
  - ✅ FeedbackModal: 6/6 tests passing
  - ✅ RecoveryModal: 7/7 tests passing
  - ✅ ErrorRecoveryDialog: 11/11 tests passing
  - ✅ useFeedback hook: 8/8 tests passing
- ✅ Linting: Zero errors (ruff clean)
- ⏳ DraftEditor integration: Deferred to Epic 5 (TD-4.8-2)
- ~~⏳ Frontend unit tests: 14 tests deferred~~ ← **✅ COMPLETED (32 tests)**
- ⏳ Backend integration tests: 8 tests deferred (TD-4.8-3)
- ⏳ E2E tests: 6 tests deferred (TD-4.8-3)
- ⏳ Audit logging: Need audit service (TD-4.8-1)

---

**Document Owner**: Tung Vu
**Last Updated**: 2025-12-10 (ARCHIVED - Migrated to epic-7-tech-debt.md)
**Next Review**: N/A - See [epic-7-tech-debt.md](./epic-7-tech-debt.md) for active tracking
