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

## Summary

**Total Items:** 1
**High Priority:** 0
**Medium Priority:** 0
**Low Priority:** 1

**Notes:**
- All deferred items have minimal production impact
- Story 5.10 is already defined in Epic 5 to address TD-3.7-1
- No blockers for Epic 3 completion or MVP deployment
