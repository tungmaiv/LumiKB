# ATDD Checklist - Epic 9, Story 9-9: Chat History Viewer UI

**Date:** 2025-12-15
**Author:** Tung Vu
**Primary Test Level:** Component Tests + Selective E2E

---

## Story Summary

Create a React component for browsing persistent chat history showing all user conversations with filtering, search, and export capabilities for compliance and usage analysis.

**As a** system administrator
**I want** a chat history viewer with search and export
**So that** I can review user interactions for compliance, analyze usage patterns, and support troubleshooting

---

## Acceptance Criteria

1. Session list displays user, KB name, message count, and last active timestamp
2. Click session row to view full conversation thread in detail panel
3. User messages and assistant messages rendered with distinct styling (different backgrounds, alignment)
4. Citations displayed inline with clickable source links to documents
5. Token usage and response time shown per assistant message
6. Search within chat history by content (full-text search across messages)
7. Filter by user, KB, and date range
8. Export conversation as JSON or CSV (single session or bulk export)
9. Pagination for long histories with infinite scroll or page controls
10. Unit tests for component rendering and user interactions

---

## Failing Tests Created (RED Phase)

### Component Tests (14 tests)

**File:** `frontend/src/components/admin/chat/__tests__/chat-session-list.test.tsx` (~180 lines)

- [ ] **Test:** `renders_session_list_with_all_columns`
  - **Status:** RED - ChatSessionList component does not exist
  - **Verifies:** AC-9.9.1 - Displays user, KB name, message count, last active

- [ ] **Test:** `highlights_selected_session_row`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.9.2 - Visual indication of selected session

- [ ] **Test:** `calls_onSelectSession_when_row_clicked`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.9.2 - Click handler triggers detail panel

- [ ] **Test:** `displays_relative_time_for_last_active`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.9.1 - "2 hours ago" format

**File:** `frontend/src/components/admin/chat/__tests__/conversation-thread.test.tsx` (~200 lines)

- [ ] **Test:** `renders_user_messages_right_aligned`
  - **Status:** RED - ConversationThread component does not exist
  - **Verifies:** AC-9.9.3 - User messages styled differently

- [ ] **Test:** `renders_assistant_messages_left_aligned`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.9.3 - Assistant messages styled differently

- [ ] **Test:** `displays_token_count_on_assistant_messages`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.9.5 - Token usage shown

- [ ] **Test:** `displays_response_time_on_assistant_messages`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.9.5 - Response time shown

**File:** `frontend/src/components/admin/chat/__tests__/citation-display.test.tsx` (~120 lines)

- [ ] **Test:** `renders_citations_with_clickable_links`
  - **Status:** RED - CitationDisplay component does not exist
  - **Verifies:** AC-9.9.4 - Citations are clickable

- [ ] **Test:** `navigates_to_document_chunk_on_click`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.9.4 - Links navigate to document with chunk

**File:** `frontend/src/components/admin/chat/__tests__/chat-filters.test.tsx` (~150 lines)

- [ ] **Test:** `renders_search_input_with_debounce`
  - **Status:** RED - ChatFilters component does not exist
  - **Verifies:** AC-9.9.6 - Search input with 300ms debounce

- [ ] **Test:** `calls_onFiltersChange_with_debounced_search`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.9.6 - Debounced callback

**File:** `frontend/src/components/admin/chat/__tests__/export-dialog.test.tsx` (~180 lines)

- [ ] **Test:** `exports_conversation_as_json`
  - **Status:** RED - ExportDialog component does not exist
  - **Verifies:** AC-9.9.8 - JSON export works

- [ ] **Test:** `exports_conversation_as_csv_with_escaped_quotes`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC-9.9.8 - CSV export with proper escaping

### Hook Tests (3 tests)

**File:** `frontend/src/hooks/__tests__/useChatHistory.test.ts` (~150 lines)

- [ ] **Test:** `fetches_chat_history_with_filters`
  - **Status:** RED - useChatHistory hook does not exist
  - **Verifies:** AC-9.9.6, AC-9.9.7 - Fetches with filter params

- [ ] **Test:** `supports_infinite_scroll_pagination`
  - **Status:** RED - Hook does not exist
  - **Verifies:** AC-9.9.9 - useInfiniteQuery for pagination

- [ ] **Test:** `debounces_search_query`
  - **Status:** RED - Hook does not exist
  - **Verifies:** AC-9.9.6 - 300ms debounce on search

### E2E Tests (3 tests)

**File:** `frontend/e2e/tests/admin/chat-history.spec.ts` (~180 lines)

- [ ] **Test:** `admin_can_search_and_filter_chat_history`
  - **Status:** RED - Page does not exist
  - **Verifies:** AC-9.9.6, AC-9.9.7 - Full search/filter flow

- [ ] **Test:** `admin_can_view_conversation_with_citations`
  - **Status:** RED - Page does not exist
  - **Verifies:** AC-9.9.2, AC-9.9.4 - View conversation thread

- [ ] **Test:** `admin_can_export_conversation_as_csv`
  - **Status:** RED - Page does not exist
  - **Verifies:** AC-9.9.8 - Export flow

---

## Data Factories Created

### Chat History Factory

**File:** `frontend/src/test/factories/chat-history.factory.ts`

**Exports:**

- `createChatSession(overrides?)` - Create session summary item
- `createChatSessions(count)` - Create array of sessions
- `createChatMessage(overrides?)` - Create single chat message
- `createChatMessages(count, options?)` - Create messages for a session
- `createCitation(overrides?)` - Create citation object

**Example Usage:**

```typescript
import { createChatSession, createChatMessages, createCitation } from "@/test/factories/chat-history.factory";

const sessions = [
  createChatSession({ user_name: "John Doe", message_count: 15 }),
  createChatSession({ kb_name: "Engineering Docs", last_active: new Date() }),
];

const messages = createChatMessages(10, {
  session_id: "session-123",
  alternateRoles: true, // user, assistant, user, assistant...
  withCitations: true,
});

const assistantMessage = createChatMessage({
  role: "assistant",
  token_count: 150,
  response_time_ms: 1200,
  citations: [
    createCitation({ document_name: "API Guide", index: 1 }),
    createCitation({ document_name: "FAQ", index: 2 }),
  ],
});
```

---

## Fixtures Created

### Chat History Fixtures

**File:** `frontend/src/test/fixtures/chat-history.fixture.ts`

**Fixtures:**

- `mockChatHistoryApi` - MSW handler for GET /observability/chat-history
  - **Setup:** Registers MSW handler with mock chat data
  - **Provides:** Pre-configured API response with pagination
  - **Cleanup:** Handler automatically cleaned between tests

- `mockChatExport` - Mock for file download
  - **Setup:** Spies on URL.createObjectURL and anchor click
  - **Provides:** Assertion helpers for export validation
  - **Cleanup:** Restores original implementations

**Example Usage:**

```typescript
import { mockChatHistoryApi, mockChatExport } from "@/test/fixtures/chat-history.fixture";

beforeEach(() => {
  mockChatHistoryApi(createChatMessages(20));
});

test("exports as CSV", async () => {
  const { assertDownloaded } = mockChatExport();

  render(<ExportDialog messages={messages} />);
  await userEvent.click(screen.getByText("Export CSV"));

  assertDownloaded("chat-export.csv", "text/csv");
});
```

---

## Mock Requirements

### Chat History API Mock

**Endpoint:** `GET /api/v1/observability/chat-history`

**Success Response:**

```json
{
  "items": [
    {
      "id": "msg-uuid",
      "trace_id": "trace-abc123",
      "session_id": "session-123",
      "role": "user",
      "content": "How do I configure the API?",
      "user_id": "user-uuid",
      "kb_id": "kb-uuid",
      "created_at": "2025-12-15T10:00:00Z",
      "token_count": null,
      "response_time_ms": null,
      "citations": null
    },
    {
      "id": "msg-uuid-2",
      "trace_id": "trace-abc123",
      "session_id": "session-123",
      "role": "assistant",
      "content": "To configure the API, follow these steps [1]...",
      "user_id": "user-uuid",
      "kb_id": "kb-uuid",
      "created_at": "2025-12-15T10:00:05Z",
      "token_count": 150,
      "response_time_ms": 1200,
      "citations": [
        {
          "index": 1,
          "document_id": "doc-uuid",
          "document_name": "API Configuration Guide",
          "chunk_id": "chunk-uuid",
          "relevance_score": 0.92
        }
      ]
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

**Failure Response:**

```json
{
  "detail": "Failed to fetch chat history"
}
```

**Notes:**
- Support query params: user_id, kb_id, session_id, search_query, start_date, end_date, skip, limit
- Infinite scroll uses skip/limit for pagination

---

## Required data-testid Attributes

### Chat Session List Component

- `chat-session-list` - Main session list container
- `chat-session-row-{session_id}` - Individual session row (clickable)
- `chat-session-user-{session_id}` - User name cell
- `chat-session-kb-{session_id}` - KB name cell
- `chat-session-count-{session_id}` - Message count cell
- `chat-session-last-active-{session_id}` - Last active timestamp
- `chat-session-loading` - Loading skeleton
- `chat-session-empty` - Empty state

### Chat Filters Component

- `chat-filter-search` - Search input field
- `chat-filter-user` - User select dropdown
- `chat-filter-kb` - KB select dropdown
- `chat-filter-start-date` - Start date picker
- `chat-filter-end-date` - End date picker

### Conversation Thread Component

- `conversation-thread` - Thread container
- `chat-message-{id}` - Individual message bubble
- `chat-message-role-{id}` - Role indicator (user/assistant)
- `chat-message-content-{id}` - Message content
- `chat-message-tokens-{id}` - Token count (assistant only)
- `chat-message-time-{id}` - Response time (assistant only)

### Citation Display Component

- `citation-list` - Citations container
- `citation-link-{index}` - Clickable citation link
- `citation-score-{index}` - Relevance score badge

### Export Dialog Component

- `export-dialog` - Dialog container
- `export-format-json` - JSON radio button
- `export-format-csv` - CSV radio button
- `export-submit-btn` - Export button
- `export-cancel-btn` - Cancel button

### Session Detail Panel

- `session-detail-panel` - Slide-out panel
- `session-detail-close-btn` - Close button
- `session-detail-export-btn` - Export current session

**Implementation Example:**

```tsx
<div data-testid="conversation-thread" className="flex flex-col gap-4">
  {messages.map((msg) => (
    <div
      key={msg.id}
      data-testid={`chat-message-${msg.id}`}
      className={cn(
        "max-w-[80%] rounded-lg p-4",
        msg.role === "user" ? "ml-auto bg-primary" : "mr-auto bg-muted"
      )}
    >
      <p data-testid={`chat-message-content-${msg.id}`}>{msg.content}</p>
      {msg.role === "assistant" && (
        <div className="mt-2 text-xs">
          <span data-testid={`chat-message-tokens-${msg.id}`}>
            {msg.token_count} tokens
          </span>
          <span data-testid={`chat-message-time-${msg.id}`}>
            {msg.response_time_ms}ms
          </span>
        </div>
      )}
    </div>
  ))}
</div>
```

---

## Implementation Checklist

### Test: renders_session_list_with_all_columns

**File:** `frontend/src/components/admin/chat/__tests__/chat-session-list.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/chat/chat-session-list.tsx`
- [ ] Define ChatSessionListProps interface
- [ ] Render table with columns: User, KB, Messages, Last Active
- [ ] Format last_active as relative time ("2 hours ago")
- [ ] Add data-testid attributes
- [ ] Run test: `npm run test:run -- src/components/admin/chat/__tests__/chat-session-list.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: renders_user_messages_right_aligned

**File:** `frontend/src/components/admin/chat/__tests__/conversation-thread.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/chat/conversation-thread.tsx`
- [ ] Apply `ml-auto` class for user messages
- [ ] Use different background colors (primary vs muted)
- [ ] Add data-testid: `conversation-thread`, `chat-message-{id}`
- [ ] Run test: `npm run test:run -- src/components/admin/chat/__tests__/conversation-thread.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1 hour

---

### Test: displays_token_count_on_assistant_messages

**File:** `frontend/src/components/admin/chat/__tests__/conversation-thread.test.tsx`

**Tasks to make this test pass:**

- [ ] Conditionally render token_count for role === "assistant"
- [ ] Add data-testid: `chat-message-tokens-{id}`
- [ ] Run test: `npm run test:run -- src/components/admin/chat/__tests__/conversation-thread.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 0.5 hours

---

### Test: renders_citations_with_clickable_links

**File:** `frontend/src/components/admin/chat/__tests__/citation-display.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/chat/citation-display.tsx`
- [ ] Render citation links with document name
- [ ] Build href: `/documents/{document_id}?chunk={chunk_id}`
- [ ] Add data-testid: `citation-list`, `citation-link-{index}`
- [ ] Run test: `npm run test:run -- src/components/admin/chat/__tests__/citation-display.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1 hour

---

### Test: renders_search_input_with_debounce

**File:** `frontend/src/components/admin/chat/__tests__/chat-filters.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/chat/chat-filters.tsx`
- [ ] Use useDebounce hook with 300ms delay
- [ ] Add search Input with data-testid: `chat-filter-search`
- [ ] Call onFiltersChange with debounced value
- [ ] Run test: `npm run test:run -- src/components/admin/chat/__tests__/chat-filters.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1 hour

---

### Test: exports_conversation_as_csv_with_escaped_quotes

**File:** `frontend/src/components/admin/chat/__tests__/export-dialog.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/chat/export-dialog.tsx`
- [ ] Implement exportAsCSV function with quote escaping
- [ ] Create blob and trigger download via anchor click
- [ ] Add data-testid: `export-dialog`, `export-format-csv`, `export-submit-btn`
- [ ] Run test: `npm run test:run -- src/components/admin/chat/__tests__/export-dialog.test.tsx`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: supports_infinite_scroll_pagination

**File:** `frontend/src/hooks/__tests__/useChatHistory.test.ts`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/hooks/useChatHistory.ts`
- [ ] Use TanStack Query useInfiniteQuery
- [ ] Implement getNextPageParam based on skip + limit < total
- [ ] Expose fetchNextPage and hasNextPage
- [ ] Run test: `npm run test:run -- src/hooks/__tests__/useChatHistory.test.ts`
- [ ] Test passes (green phase)

**Estimated Effort:** 1.5 hours

---

### Test: admin_can_search_and_filter_chat_history (E2E)

**File:** `frontend/e2e/tests/admin/chat-history.spec.ts`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/app/(protected)/admin/chat-history/page.tsx`
- [ ] Compose ChatSessionList, ChatFilters, SessionDetailPanel components
- [ ] Wire up useChatHistory hook with filter state
- [ ] Add navigation link from admin dashboard
- [ ] Run test: `npx playwright test e2e/tests/admin/chat-history.spec.ts`
- [ ] Test passes (green phase)

**Estimated Effort:** 2 hours

---

## Running Tests

```bash
# Run all component tests for this story
npm run test:run -- src/components/admin/chat

# Run specific test file
npm run test:run -- src/components/admin/chat/__tests__/chat-session-list.test.tsx

# Run hook tests
npm run test:run -- src/hooks/__tests__/useChatHistory.test.ts

# Run E2E tests
npx playwright test e2e/tests/admin/chat-history.spec.ts

# Run E2E in headed mode
npx playwright test e2e/tests/admin/chat-history.spec.ts --headed

# Run with coverage
npm run test:coverage -- --testPathPattern="admin/chat"
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

- [ ] All tests written and failing
- [ ] Fixtures and factories created
- [ ] Mock requirements documented
- [ ] data-testid requirements listed
- [ ] Implementation checklist created

**Verification:**

- All tests run and fail as expected
- Failure messages are clear and actionable
- Tests fail due to missing implementation, not test bugs

---

### GREEN Phase (DEV Team - Next Steps)

**DEV Agent Responsibilities:**

1. **Pick one failing test** from implementation checklist
2. **Read the test** to understand expected behavior
3. **Implement minimal code** to make that specific test pass
4. **Run the test** to verify it now passes (green)
5. **Check off the task** in implementation checklist
6. **Move to next test** and repeat

---

### REFACTOR Phase (DEV Team - After All Tests Pass)

**DEV Agent Responsibilities:**

1. **Verify all tests pass**
2. **Review code for quality**
3. **Extract duplications** (DRY principle)
4. **Ensure tests still pass** after each refactor

---

## Next Steps

1. **Review this checklist** with team
2. **Run failing tests** to confirm RED phase
3. **Begin implementation** using checklist
4. **Work one test at a time**
5. **When all tests pass**, refactor for quality
6. **When complete**, run `bmad sm story-done`

---

## Knowledge Base References Applied

- **fixture-architecture.md** - React Testing Library fixtures
- **data-factories.md** - Factory patterns for chat data
- **component-tdd.md** - Component test strategies
- **network-first.md** - MSW handler setup
- **test-quality.md** - Test design principles

See `tea-index.csv` for complete knowledge fragment mapping.

---

## Test Execution Evidence

### Initial Test Run (RED Phase Verification)

**Command:** `npm run test:run -- src/components/admin/chat`

**Results:**

```
FAIL src/components/admin/chat/__tests__/chat-session-list.test.tsx
  Cannot find module '@/components/admin/chat/chat-session-list'

FAIL src/components/admin/chat/__tests__/conversation-thread.test.tsx
  Cannot find module '@/components/admin/chat/conversation-thread'

FAIL src/components/admin/chat/__tests__/citation-display.test.tsx
  Cannot find module '@/components/admin/chat/citation-display'

FAIL src/components/admin/chat/__tests__/chat-filters.test.tsx
  Cannot find module '@/components/admin/chat/chat-filters'

FAIL src/components/admin/chat/__tests__/export-dialog.test.tsx
  Cannot find module '@/components/admin/chat/export-dialog'
```

**Summary:**

- Total tests: 20
- Passing: 0 (expected)
- Failing: 20 (expected)
- Status: RED phase verified

---

## Notes

- 300ms debounce on search to prevent excessive API calls
- CSV export must escape quotes (replace " with "")
- Last active timestamp formatted as relative time
- Citation links navigate to document with chunk highlighted
- Consider bulk export option for selected sessions

---

**Generated by BMad TEA Agent** - 2025-12-15
