# Story 5.9: Recent KBs and Polish Items

Status: done

## Story

As a **user**,
I want **quick access to recently used KBs and a polished UI**,
so that **my daily workflow is efficient**.

## Acceptance Criteria

**AC-5.9.1: Recent KBs Section in Sidebar**
**Given** I am a logged-in user
**When** I open the KB sidebar
**Then** a "Recent" section displays my last 5 accessed KBs
**And** they are ordered by most recent first

**Validation:**
- Sidebar shows "Recent" section above the full KB list
- Maximum 5 KBs displayed in Recent section
- Most recently accessed KB appears first
- Clicking a recent KB sets it as active

**AC-5.9.2: Recent KB Query Performance**
**Given** the system queries recent KBs
**When** GET `/api/v1/users/me/recent-kbs` is called
**Then** the response completes in < 100ms
**And** uses indexed `last_accessed` column for efficient lookup

**Validation:**
- Response time measured via performance logging
- Query uses index on `kb_access_log.accessed_at`
- Response returns max 5 KBs with timestamps

**AC-5.9.3: Empty State for No Recent KBs**
**Given** a user has no KB access history
**When** the Recent section is rendered
**Then** a helpful empty state message is displayed
**And** the message suggests selecting a KB from the list below

**Validation:**
- New users see empty state with helpful message
- Message includes call-to-action to explore KBs
- Empty state matches design system patterns

**AC-5.9.4: Click Recent KB Navigates to KB Search**
**Given** I see a recent KB in the sidebar
**When** I click on the recent KB card
**Then** the KB is set as active
**And** I can navigate to search within that KB context

**Validation:**
- Clicking recent KB calls `setActiveKb(kb)`
- Active KB state updates in global store
- Search page uses active KB for queries

**AC-5.9.5: Dashboard Tooltip Help for New Users**
**Given** I am viewing the dashboard
**When** I hover over icon-only buttons
**Then** tooltips display with helpful descriptions

**Validation:**
- All icon-only buttons have `aria-label` and tooltip
- Tooltips appear on hover with 200ms delay
- Tooltip content is concise and actionable

**AC-5.9.6: KB Recommendations Integration (from Story 5.8)**
**Given** the KB recommendations API is available (Story 5.8)
**When** I view the KB selector
**Then** I can see personalized KB recommendations
**And** recommendations display reason and score

**Validation:**
- `useKBRecommendations` hook fetches from `/api/v1/users/me/kb-recommendations`
- Recommendations section shows in sidebar below Recent
- Each recommendation shows kb_name, reason, and visual score indicator

**AC-5.9.7: Loading Skeletons on Data-Fetching Views**
**Given** data is being fetched from the API
**When** the loading state is active
**Then** skeleton loaders display instead of empty content

**Validation:**
- Dashboard cards show skeleton during load
- KB sidebar shows skeleton during load
- Skeletons match actual component dimensions

**AC-5.9.8: Error Boundaries with Recovery Options**
**Given** an error occurs during rendering or data fetch
**When** the error boundary catches the error
**Then** a friendly error message displays with recovery options
**And** the user can retry or navigate away

**Validation:**
- Error boundaries wrap major components
- Error UI shows retry button
- Errors are logged to console/monitoring

**AC-5.9.9: Keyboard Navigation Throughout**
**Given** I am navigating the application
**When** I use Tab, Enter, and Escape keys
**Then** focus moves logically through interactive elements
**And** I can activate buttons/links with Enter

**Validation:**
- Tab order follows visual layout
- Focus indicators visible (ring styling)
- Escape closes modals/dropdowns
- Enter activates focused elements

## Tasks / Subtasks

### Task 1: Create Recent KBs Backend Endpoint (AC-5.9.1, AC-5.9.2)

**Objective:** Implement API endpoint to retrieve user's recently accessed KBs

**Subtasks:**
- [ ] 1.1 Create `GET /api/v1/users/me/recent-kbs` endpoint in `backend/app/api/v1/users.py`
  - [ ] 1.1.1 Query `kb_access_log` table for user's recent KB accesses
  - [ ] 1.1.2 Group by kb_id and get most recent access per KB
  - [ ] 1.1.3 Join with `knowledge_bases` table for KB details
  - [ ] 1.1.4 Limit to 5 most recent, ordered by accessed_at DESC
- [ ] 1.2 Create Pydantic schema: `RecentKB` in `backend/app/schemas/kb_recommendation.py`
  - [ ] 1.2.1 Fields: kb_id (UUID), kb_name (str), description (str), last_accessed (datetime), document_count (int)
- [ ] 1.3 Ensure query uses indexed columns for < 100ms response
  - [ ] 1.3.1 Verify index exists on `kb_access_log(user_id, accessed_at)`
  - [ ] 1.3.2 Add performance logging to endpoint
- [ ] 1.4 Add OpenAPI documentation
- [ ] 1.5 Require authentication (`current_active_user` dependency)

### Task 2: Create Recent KBs Frontend Hook (AC-5.9.1)

**Objective:** Create React hook to fetch and cache recent KBs

**Subtasks:**
- [ ] 2.1 Create `frontend/src/hooks/useRecentKBs.ts`
  - [ ] 2.1.1 Implement `useRecentKBs()` hook with SWR or React Query pattern
  - [ ] 2.1.2 Return: `{ recentKBs, isLoading, error, refetch }`
  - [ ] 2.1.3 Cache results with 5-minute stale time
- [ ] 2.2 Add TypeScript types for RecentKB
  - [ ] 2.2.1 Match backend schema: kb_id, kb_name, description, last_accessed, document_count
- [ ] 2.3 Handle loading and error states

### Task 3: Update KB Sidebar with Recent Section (AC-5.9.1, AC-5.9.3, AC-5.9.4)

**Objective:** Add Recent KBs section to the KB sidebar

**Subtasks:**
- [ ] 3.1 Update `frontend/src/components/layout/kb-sidebar.tsx`
  - [ ] 3.1.1 Import `useRecentKBs` hook
  - [ ] 3.1.2 Add "Recent" section header with Clock icon
  - [ ] 3.1.3 Display up to 5 recent KBs above the full list
  - [ ] 3.1.4 Add Separator between Recent and All KBs sections
- [ ] 3.2 Create `RecentKBItem` component variant
  - [ ] 3.2.1 Show KB name and relative time (e.g., "2h ago")
  - [ ] 3.2.2 Compact styling to differentiate from full KB items
  - [ ] 3.2.3 onClick sets active KB via `setActiveKb()`
- [ ] 3.3 Implement empty state for no recent KBs
  - [ ] 3.3.1 Show message: "No recent activity"
  - [ ] 3.3.2 Show subtext: "Select a KB below to get started"
- [ ] 3.4 Add loading skeleton for Recent section

### Task 4: Integrate KB Recommendations UI (AC-5.9.6)

**Objective:** Display personalized KB recommendations from Story 5.8

**Subtasks:**
- [ ] 4.1 Create `frontend/src/hooks/useKBRecommendations.ts` (from Story 5.8 Task 5.1)
  - [ ] 4.1.1 Fetch from `GET /api/v1/users/me/kb-recommendations`
  - [ ] 4.1.2 Return: `{ recommendations, isLoading, error, isColdStart }`
- [ ] 4.2 Create `KBRecommendationItem` component
  - [ ] 4.2.1 Show kb_name, reason, and score indicator
  - [ ] 4.2.2 Visual score indicator (progress bar or star rating)
  - [ ] 4.2.3 onClick sets active KB
- [ ] 4.3 Add "Recommended" section to sidebar (below Recent)
  - [ ] 4.3.1 Show max 3 recommendations in sidebar
  - [ ] 4.3.2 "See more" link if > 3 recommendations
  - [ ] 4.3.3 Cold start indicator for new users

### Task 5: Add Dashboard Tooltips (AC-5.9.5)

**Objective:** Add tooltips to icon-only buttons throughout the app

**Subtasks:**
- [ ] 5.1 Install/verify Tooltip component from shadcn/ui
  - [ ] 5.1.1 Run `npx shadcn@latest add tooltip` if not present
- [ ] 5.2 Update `frontend/src/components/layout/header.tsx`
  - [ ] 5.2.1 Wrap icon buttons with Tooltip
  - [ ] 5.2.2 Add tooltips: "Search (Cmd+K)", "Notifications", "Settings"
- [ ] 5.3 Update `frontend/src/components/layout/kb-sidebar.tsx`
  - [ ] 5.3.1 Add tooltip to "Create Knowledge Base" button
- [ ] 5.4 Update `frontend/src/app/(protected)/dashboard/page.tsx`
  - [ ] 5.4.1 Add tooltips to quick action cards
- [ ] 5.5 Ensure all tooltips have consistent delay (200ms)

### Task 6: Implement Loading Skeletons (AC-5.9.7)

**Objective:** Add loading skeletons to data-fetching views

**Subtasks:**
- [ ] 6.1 Create `DashboardSkeleton` component
  - [ ] 6.1.1 Skeleton for header/welcome section
  - [ ] 6.1.2 Skeleton for quick access cards (4 cards)
  - [ ] 6.1.3 Skeleton for documents panel
- [ ] 6.2 Update dashboard page to show skeleton during load
  - [ ] 6.2.1 Add loading state check from stores
  - [ ] 6.2.2 Conditionally render skeleton vs content
- [ ] 6.3 Verify KB sidebar skeleton already implemented
  - [ ] 6.3.1 Review `KbSelectorSkeleton` in kb-sidebar.tsx
  - [ ] 6.3.2 Add skeleton for Recent section

### Task 7: Add Error Boundaries (AC-5.9.8)

**Objective:** Wrap major components with error boundaries

**Subtasks:**
- [ ] 7.1 Create `frontend/src/components/ui/error-boundary.tsx`
  - [ ] 7.1.1 Implement React ErrorBoundary class component
  - [ ] 7.1.2 Display friendly error message
  - [ ] 7.1.3 Add "Try Again" button that resets state
  - [ ] 7.1.4 Add "Go Home" button as fallback
- [ ] 7.2 Wrap dashboard page with error boundary
- [ ] 7.3 Wrap KB sidebar with error boundary
- [ ] 7.4 Wrap documents panel with error boundary
- [ ] 7.5 Log errors to console with stack trace

### Task 8: Verify Keyboard Navigation (AC-5.9.9)

**Objective:** Ensure keyboard accessibility throughout the app

**Subtasks:**
- [ ] 8.1 Audit tab order in dashboard
  - [ ] 8.1.1 Verify logical tab order through cards
  - [ ] 8.1.2 Add `tabIndex` where needed
- [ ] 8.2 Audit tab order in KB sidebar
  - [ ] 8.2.1 Tab through KB list items
  - [ ] 8.2.2 Verify Enter activates KB selection
- [ ] 8.3 Verify focus indicators
  - [ ] 8.3.1 Check ring styling on all interactive elements
  - [ ] 8.3.2 Ensure sufficient contrast for focus ring
- [ ] 8.4 Verify Escape behavior
  - [ ] 8.4.1 Escape closes modals (KB create, etc.)
  - [ ] 8.4.2 Escape closes command palette
- [ ] 8.5 Manual accessibility audit
  - [ ] 8.5.1 Test with keyboard only
  - [ ] 8.5.2 Verify no focus traps

### Task 9: Write Backend Unit Tests

**Objective:** Test recent KBs endpoint logic

**Subtasks:**
- [ ] 9.1 Create `backend/tests/unit/test_recent_kbs.py`
- [ ] 9.2 Test endpoint logic
  - [ ] 9.2.1 `test_recent_kbs_returns_max_5()` - verify limit
  - [ ] 9.2.2 `test_recent_kbs_ordered_by_accessed_at()` - most recent first
  - [ ] 9.2.3 `test_recent_kbs_groups_by_kb()` - no duplicate KBs
- [ ] 9.3 Test edge cases
  - [ ] 9.3.1 `test_recent_kbs_empty_for_new_user()` - returns empty list
  - [ ] 9.3.2 `test_recent_kbs_only_accessible_kbs()` - permission check

### Task 10: Write Backend Integration Tests

**Objective:** Test API endpoint with authentication

**Subtasks:**
- [ ] 10.1 Create `backend/tests/integration/test_recent_kbs_api.py`
- [ ] 10.2 Test API endpoint
  - [ ] 10.2.1 `test_get_recent_kbs_authenticated_returns_200()` - 200 OK
  - [ ] 10.2.2 `test_get_recent_kbs_unauthenticated_returns_401()` - 401 Unauthorized
  - [ ] 10.2.3 `test_recent_kbs_response_schema_valid()` - validate schema
- [ ] 10.3 Test performance
  - [ ] 10.3.1 `test_recent_kbs_response_under_100ms()` - verify < 100ms

### Task 11: Write Frontend Unit Tests

**Objective:** Test React hooks and components

**Subtasks:**
- [ ] 11.1 Create `frontend/src/hooks/__tests__/useRecentKBs.test.ts`
  - [ ] 11.1.1 Test fetch success scenario
  - [ ] 11.1.2 Test loading state
  - [ ] 11.1.3 Test error handling
- [ ] 11.2 Create `frontend/src/hooks/__tests__/useKBRecommendations.test.ts`
  - [ ] 11.2.1 Test fetch success scenario
  - [ ] 11.2.2 Test cold start handling
- [ ] 11.3 Create `frontend/src/components/layout/__tests__/kb-sidebar-recent.test.tsx`
  - [ ] 11.3.1 Test Recent section renders
  - [ ] 11.3.2 Test empty state renders
  - [ ] 11.3.3 Test click sets active KB
- [ ] 11.4 Create `frontend/src/components/ui/__tests__/error-boundary.test.tsx`
  - [ ] 11.4.1 Test error rendering
  - [ ] 11.4.2 Test retry functionality

### Task 12: E2E Tests (Deferred to Story 5.16)

**Note:** E2E tests deferred to Story 5.16 (Docker E2E Infrastructure)

**Subtasks:**
- [ ] 12.1 Create `frontend/e2e/tests/recent-kbs.spec.ts`
- [ ] 12.2 Test recent KB workflow
  - [ ] 12.2.1 Login → Access KB → Verify appears in Recent
  - [ ] 12.2.2 Click recent KB → Verify sets active

## Dependencies

**Prerequisites (from epics.md):**
- Story 2.3: KB Management (DONE)
- Story 5.8: Smart KB Suggestions (DONE) - provides KB recommendations backend

**Backend Dependencies (existing):**
- `kb_access_log` table (from Story 5.8)
- `KBRecommendationService` (from Story 5.8)
- FastAPI-Users authentication

**Frontend Dependencies (existing):**
- shadcn/ui components (Button, Card, Skeleton, Tooltip, ScrollArea)
- Zustand stores (auth-store, kb-store)
- date-fns for relative time formatting

**New Dependencies:**
- None required (all dependencies already installed)

## Technical Notes

1. **Recent KBs Storage**: The `kb_access_log` table (created in Story 5.8) tracks KB access patterns. Query this table to get recent KBs.

2. **Performance**: Query must use indexed columns for < 100ms response. Index exists on `(user_id, kb_id, accessed_at)`.

3. **Frontend State**: Recent KBs should update when user accesses a KB. Consider calling `useRecentKBs().refetch()` after KB selection.

4. **Recommendations Integration**: Story 5.8 deferred UI tasks (5.1-5.3) to this story. Implement the `useKBRecommendations` hook and UI components.

5. **Polish Scope**: Keep polish items focused on core UX patterns:
   - Loading skeletons (data feedback)
   - Error boundaries (graceful failure)
   - Tooltips (discoverability)
   - Keyboard navigation (accessibility)

6. **Reference**: FR12d (Recent KBs), UX spec Section 7 - Pattern Decisions

## Definition of Done

- [ ] All acceptance criteria validated
- [ ] Backend unit tests pass (5 tests)
- [ ] Backend integration tests pass (4 tests)
- [ ] Frontend unit tests pass (12 tests)
- [ ] Code review completed
- [ ] No linting errors (ruff, ESLint)
- [ ] No TypeScript errors
- [ ] Manual testing completed:
  - [ ] Recent KBs display correctly in sidebar
  - [ ] Empty state shows for new users
  - [ ] KB recommendations display with reasons
  - [ ] Tooltips appear on hover
  - [ ] Keyboard navigation works throughout
  - [ ] Error boundaries display friendly messages
  - [ ] Loading skeletons show during data fetch

## Traceability

| AC ID | PRD FR | Tech Spec Section | Test Coverage |
|-------|--------|-------------------|---------------|
| AC-5.9.1 | FR12d | Tech Spec AC-5.9.1 | Task 9, 10, 11 |
| AC-5.9.2 | FR12d | NFR Performance | Task 10.3 |
| AC-5.9.3 | FR12d | Tech Spec AC-5.9.3 | Task 11.3 |
| AC-5.9.4 | FR12d | Tech Spec AC-5.9.4 | Task 11.3 |
| AC-5.9.5 | FR58 | Tech Spec AC-5.9.5 | Manual testing |
| AC-5.9.6 | FR12c | Story 5.8 (deferred) | Task 11.2 |
| AC-5.9.7 | UX Spec | Pattern Decisions | Task 11 |
| AC-5.9.8 | UX Spec | Pattern Decisions | Task 11.4 |
| AC-5.9.9 | WCAG 2.1 AA | Accessibility | Task 8 |
