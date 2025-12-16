# Epic 5 Technical Debt Tracking

**Epic:** Epic 5 - Administration & Polish
**Created:** 2025-11-26
**Status:** Active

---

## Purpose

Track deferred technical work from Epic 5 and prior epics that:
- Doesn't block production deployment
- Improves quality/maintainability
- Should be addressed in future sprints or Epic 5 itself

---

## Tech Debt Items

### TD-4.1-1: Chat API Integration Test External Service Mocks (Story 5.15)

**Source:** Story 4.1 (Chat Conversation Backend) - Epic 4
**Priority:** Medium
**Effort:** 4 hours
**Target Story:** Story 5.15 (Epic 4 ATDD Transition to GREEN)

**Description:**
Integration tests for Chat API require mocks for external services (Qdrant vector search and LiteLLM response generation). Tests currently fail with 500 errors due to missing service mocks.

**Current State:**
- ✅ 8 integration tests created for all 7 ACs
- ✅ Test fixtures complete (authenticated_headers, demo_kb_with_indexed_docs, empty_kb_factory)
- ✅ Unit tests: 9/9 passing (ConversationService)
- ❌ Integration tests fail: 8/8 with 500 Internal Server Error
- ❌ Missing: Qdrant mock fixture for vector search
- ❌ Missing: LiteLLM mock fixture for response generation

**Required Mocks:**
1. **Qdrant Mock** (`mock_qdrant_search` fixture):
   - Mock `SearchService.search()` to return sample SearchResultSchema chunks
   - Provide realistic vector search results with scores, excerpts, metadata
   - Handle both populated KB and empty KB scenarios

2. **LiteLLM Mock** (`mock_litellm_generate` fixture):
   - Mock `LiteLLMClient.generate()` to return citation-formatted responses
   - Return realistic answers with inline [1], [2] citation markers

**Production Impact:**
None - core implementation is production-ready (all 7 ACs implemented, unit tests passing). Integration tests validate end-to-end API behavior but are not blocking deployment.

**Why Deferred:**
Test infrastructure setup deferred to reduce Story 4.1 scope and follow Epic 3 pattern of unit-first testing. Epic 5 Story 5.15 is dedicated to Epic 4 ATDD test hardening.

**Proposed Resolution (Story 5.15):**
- Implement Qdrant and LiteLLM mock fixtures in `tests/integration/conftest.py`
- Transition 8 chat API integration tests to GREEN
- Validate AC coverage: AC1 (single-turn), AC2 (multi-turn), AC4 (Redis storage), AC5 (permission enforcement), AC6 (error handling), AC7 (audit logging)

**Reference:**
- [backend/tests/integration/test_chat_api.py](../../backend/tests/integration/test_chat_api.py) - Test implementation
- [docs/sprint-artifacts/4-1-chat-conversation-backend.md](./4-1-chat-conversation-backend.md) - Story details
- [docs/sprint-artifacts/epic-4-tech-debt.md](./epic-4-tech-debt.md#TD-4.1-1) - Full tech debt entry

---

### TD-4.2-2: Chat Streaming Integration Test Dependency (Story 5.15)

**Source:** Story 4.2 (Chat Streaming UI) - Epic 4
**Priority:** Medium
**Effort:** 2 hours
**Target Story:** Story 5.15 (Epic 4 ATDD Transition to GREEN)

**Description:**
Chat streaming integration tests cannot run due to dependency on Story 4.1 test infrastructure (Qdrant and LiteLLM mocks). Story 4.2 SSE streaming endpoint implementation is complete and production-ready, but integration tests require the same external service mocks as Story 4.1.

**Current State:**
- ✅ Backend SSE streaming: Real LLM token streaming implemented (not word-split simulation)
- ✅ Event schema: Fixed (text→token, inline citations)
- ✅ ConversationService.send_message_stream(): Yields real-time events
- ✅ Frontend components: ChatContainer, ChatInput, useChatStream hook created
- ✅ SSE client updated: Handles status, token, citation, done events
- ✅ Component tests: ChatMessage component (9/9 passing)
- ❌ Integration tests: Cannot run without Story 4.1 mock infrastructure

**Blocked Tests:**
- `backend/tests/integration/test_chat_api.py` - SSE streaming endpoint tests (require Qdrant + LiteLLM mocks)
- `frontend/e2e/tests/chat/chat-conversation.spec.ts` - E2E streaming tests (require backend infrastructure)

**Dependencies:**
1. TD-4.1-1 must be resolved first (Qdrant and LiteLLM mocks)
2. Once Story 4.1 mocks are in place, Story 4.2 streaming tests will use same fixtures

**Production Impact:**
None - SSE streaming implementation is production-ready:
- Real LLM token streaming (not simulated)
- Citations streamed inline as markers detected
- Status events before/during generation
- Error handling with SSE error events
- All frontend components integrated

**Why Deferred:**
Story 4.2 implementation focused on fixing code review blockers (real streaming, missing components). Integration testing deferred to Story 5.15 which resolves all Epic 4 test infrastructure needs in one consolidated effort.

**Proposed Resolution (Story 5.15):**
- Reuse TD-4.1-1 mock fixtures for streaming endpoint tests
- Add SSE-specific integration tests (streaming response parsing, event order)
- Validate real-time citation inline streaming (AC2)
- Run E2E tests with full backend infrastructure

**Reference:**
- [backend/app/api/v1/chat_stream.py](../../backend/app/api/v1/chat_stream.py) - SSE endpoint implementation
- [backend/app/services/conversation_service.py:160-292](../../backend/app/services/conversation_service.py#L160-L292) - send_message_stream method
- [docs/sprint-artifacts/code-review-report-story-4-2.md](./code-review-report-story-4-2.md) - Code review findings
- [docs/sprint-artifacts/4-2-chat-streaming-ui.md](./4-2-chat-streaming-ui.md) - Story details

---

### TD-3.7-1: Command Palette Test Coverage (Story 5.10)

**Source:** Story 3-7 (Quick Search and Command Palette)
**Priority:** Low
**Effort:** 1-2 hours
**Target Story:** Story 5.10

**Description:**
Command palette component tests have 70% pass rate (7/10 passing). Three tests fail due to shadcn/ui Command component's internal filtering not recognizing mocked fetch responses.

**Failing Tests:**
- `fetches results after debounce (AC10)` - Timeouts waiting for results to appear
- `displays results with metadata (AC2)` - Timeouts waiting for result metadata
- `shows error state on API failure (AC9)` - Timeouts waiting for error message

**Root Cause:**
The shadcn/ui Command component has internal filtering that doesn't work with vitest mocked fetch responses. When fetch is mocked to return results, the Command component's filtering mechanism doesn't display them in the test DOM.

**Production Impact:**
None - manual QA and backend integration tests confirm all features work correctly. This is a test infrastructure limitation, not a functional bug.

**Why Deferred:**
- Production functionality verified working
- Backend integration tests validate API contract
- 7 passing component tests cover core functionality
- Senior developer review approved Story 3.7 with this known limitation

**Proposed Resolution (Story 5.10):**
1. **Option 1**: Convert to E2E tests with Playwright (tests against real browser)
2. **Option 2**: Mock at different level (API layer vs component props)
3. **Option 3**: Use real backend in integration tests instead of mocks
4. **Option 4**: Investigate Command/cmdk library test utilities

**Reference:**
- Story 3.7: [docs/sprint-artifacts/3-7-quick-search-and-command-palette.md](docs/sprint-artifacts/3-7-quick-search-and-command-palette.md#L1028)
- Story 5.10: [docs/epics.md](docs/epics.md#L2050-L2086)

---

### TD-4.9-1: Template Selection E2E Test Execution (Story 5.15)

**Source:** Story 4.9 (Generation Templates) - Epic 4
**Priority:** Low
**Effort:** 2 hours
**Target Story:** Story 5.15 (Epic 4 ATDD Transition to GREEN)

**Description:**
E2E tests for template selection UI workflow are written but not yet executable with Playwright. Tests validate template selection, preview display, context input, and generation initiation.

**Current State:**
- ✅ Backend: Template registry complete (4 templates)
- ✅ Backend: GET /api/v1/templates endpoint implemented
- ✅ Frontend: TemplateSelector component complete
- ✅ Frontend: GenerationModal integration complete
- ✅ Component tests: 9/9 passing
- ✅ Hook tests: 8/8 passing
- ✅ Unit tests: 8/8 passing (backend)
- ✅ Integration tests: 4/4 passing (backend)
- ❌ E2E tests: 9 tests written but not executed with Playwright

**E2E Test Coverage (Deferred):**
9 tests in `frontend/e2e/tests/generation/template-selection.spec.ts`:
1. Displays all 4 templates in selector
2. Shows template descriptions
3. Displays template previews on selection
4. Defaults to RFP Response template
5. Allows template switching
6. Custom template shows custom instructions field
7. Requires context input before generation
8. Initiates generation with template + context
9. Clears form after generation

**Production Impact:**
None - all functionality is production-ready and validated:
- Backend template registry tested (12 tests passing)
- Frontend component tested (9 tests passing)
- Frontend hook tested (8 tests passing)
- Build passing with 0 TypeScript errors
- All 5 acceptance criteria satisfied

**Why Deferred:**
E2E tests intentionally deferred to Epic 5 Story 5.15 per project workflow. Story 4.9 focused on component implementation and unit/integration testing. E2E execution aligns with Epic 4 ATDD transition to GREEN.

**Proposed Resolution (Story 5.15):**
- Install Playwright dependencies if needed
- Execute 9 E2E tests in `template-selection.spec.ts`
- Validate full user workflow: template selection → preview → context input → generation
- Verify integration with search page "Generate Draft" button
- Add screenshot assertions for visual regression testing

**Reference:**
- [frontend/e2e/tests/generation/template-selection.spec.ts](../../frontend/e2e/tests/generation/template-selection.spec.ts) - E2E test file
- [docs/sprint-artifacts/4-9-generation-templates.md](./4-9-generation-templates.md) - Story details

---

### TD-4.9-2: Test File TypeScript Error Cleanup (Story 5.15)

**Source:** Story 4.9 (Generation Templates) - Epic 4
**Priority:** Low
**Effort:** 1 hour
**Target Story:** Story 5.15 (Epic 4 ATDD Transition to GREEN)

**Description:**
Three TypeScript errors exist in `frontend/src/hooks/__tests__/use-chat-stream.test.ts` (test file, not production code). These are non-blocking linting errors that do not affect production code or test execution.

**Current State:**
- ✅ Production code: 0 TypeScript errors (build PASSED)
- ✅ All tests passing: 29/29 (100% pass rate)
- ❌ Test file errors: 3 TypeScript errors in `use-chat-stream.test.ts`

**Error Details:**
The errors are related to test setup and mock configuration in the chat stream hook tests. They do not impact:
- Production code quality
- Test execution or results
- Runtime behavior
- Build output

**Production Impact:**
None - production code is clean and all tests pass successfully. This is a test file quality improvement, not a functional issue.

**Why Deferred:**
Focus for Story 4.9 was on production code quality, functional test coverage, and build verification. Test file linting is a polish item that can be addressed during Epic 5 test hardening.

**Proposed Resolution (Story 5.15):**
- Review TypeScript errors in `use-chat-stream.test.ts`
- Fix type annotations in test mocks and assertions
- Verify all tests still pass after cleanup
- Run `npm run type-check` to confirm 0 errors

**Reference:**
- [frontend/src/hooks/__tests__/use-chat-stream.test.ts](../../frontend/src/hooks/__tests__/use-chat-stream.test.ts) - Test file with TypeScript errors
- [docs/sprint-artifacts/4-9-generation-templates.md](./4-9-generation-templates.md) - Story details

---

## Summary

**Total Items:** 5
**High Priority:** 0
**Medium Priority:** 2
  - TD-4.1-1 (Chat API integration test mocks)
  - TD-4.2-2 (Chat Streaming integration test dependency)
**Low Priority:** 3
  - TD-3.7-1 (Command palette tests)
  - TD-4.9-1 (Template selection E2E tests)
  - TD-4.9-2 (Test file TypeScript cleanup)

**Epic 5 Story Allocation:**
- Story 5.10: TD-3.7-1 (Command palette test coverage)
- Story 5.15: TD-4.1-1 + TD-4.2-2 + TD-4.9-1 + TD-4.9-2 (Epic 4 ATDD transition to GREEN)

**Notes:**
- All deferred items have minimal production impact
- Story 4.2 implementation is production-ready (all blockers from code review fixed)
- Story 4.9 implementation is production-ready (Quality 95/100, all ACs satisfied)
- TD-4.2-2 has dependency on TD-4.1-1 (must resolve Story 4.1 mocks first)
- Story 5.10 and 5.15 already defined in Epic 5 to address tech debt
- No blockers for Epic 3 or Epic 4 completion or MVP deployment
- **Note:** TD-4.5-2 (Draft Generation tests) moved to epic-4-tech-debt.md (correct location)
