# Story 9.9: Chat History Viewer UI

Status: ready-for-dev

## Story

As a **system administrator**,
I want **a React component for browsing persistent chat history showing all user conversations with filtering, search, and export capabilities**,
so that **I can review user interactions for compliance, analyze usage patterns, and support troubleshooting**.

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

## Tasks / Subtasks

- [ ] Task 1: Create chat session list component (AC: #1, #9)
  - [ ] Subtask 1.1: Create `frontend/src/components/admin/chat/chat-session-list.tsx`
  - [ ] Subtask 1.2: Implement data table with columns: User, KB, Messages, Last Active
  - [ ] Subtask 1.3: Add user avatar/initials display
  - [ ] Subtask 1.4: Show message count badge
  - [ ] Subtask 1.5: Format last active as relative time (e.g., "2 hours ago")
  - [ ] Subtask 1.6: Implement pagination with page controls

- [ ] Task 2: Create filter and search controls (AC: #6, #7)
  - [ ] Subtask 2.1: Create `frontend/src/components/admin/chat/chat-filters.tsx`
  - [ ] Subtask 2.2: Add search input for full-text search
  - [ ] Subtask 2.3: Add user dropdown with autocomplete
  - [ ] Subtask 2.4: Add KB dropdown with all knowledge bases
  - [ ] Subtask 2.5: Add date range picker
  - [ ] Subtask 2.6: Implement debounced search (300ms)

- [ ] Task 3: Create conversation thread component (AC: #2, #3, #5)
  - [ ] Subtask 3.1: Create `frontend/src/components/admin/chat/conversation-thread.tsx`
  - [ ] Subtask 3.2: Implement chat bubble layout (user right, assistant left)
  - [ ] Subtask 3.3: Style user messages with primary color background
  - [ ] Subtask 3.4: Style assistant messages with muted background
  - [ ] Subtask 3.5: Add timestamp to each message
  - [ ] Subtask 3.6: Show token count and response time for assistant messages
  - [ ] Subtask 3.7: Implement scroll-to-bottom on new messages

- [ ] Task 4: Create citation display component (AC: #4)
  - [ ] Subtask 4.1: Create `frontend/src/components/admin/chat/citation-display.tsx`
  - [ ] Subtask 4.2: Parse citations from message metadata
  - [ ] Subtask 4.3: Render citation markers inline ([1], [2], etc.)
  - [ ] Subtask 4.4: Add footnote section with source links
  - [ ] Subtask 4.5: Make source links clickable (navigate to document)

- [ ] Task 5: Create session detail panel (AC: #2)
  - [ ] Subtask 5.1: Create `frontend/src/components/admin/chat/session-detail-panel.tsx`
  - [ ] Subtask 5.2: Implement slide-out panel from right
  - [ ] Subtask 5.3: Show session header: user, KB, session_id, date range
  - [ ] Subtask 5.4: Embed ConversationThread component
  - [ ] Subtask 5.5: Add close button and keyboard shortcut (Escape)

- [ ] Task 6: Create export functionality (AC: #8)
  - [ ] Subtask 6.1: Create `frontend/src/components/admin/chat/export-dialog.tsx`
  - [ ] Subtask 6.2: Add export button to session detail panel
  - [ ] Subtask 6.3: Implement JSON export format
  - [ ] Subtask 6.4: Implement CSV export format (flattened messages)
  - [ ] Subtask 6.5: Add bulk export option from session list (export selected)
  - [ ] Subtask 6.6: Trigger browser download with appropriate filename

- [ ] Task 7: Create custom hooks for chat data (AC: #9)
  - [ ] Subtask 7.1: Create `frontend/src/hooks/useChatHistory.ts`
  - [ ] Subtask 7.2: Implement useChatSessions() hook with filters
  - [ ] Subtask 7.3: Implement useChatMessages(sessionId) hook
  - [ ] Subtask 7.4: Handle loading, error, and pagination states
  - [ ] Subtask 7.5: Use TanStack Query with infinite query for messages

- [ ] Task 8: Create main chat history page (AC: #1)
  - [ ] Subtask 8.1: Create `frontend/src/app/(protected)/admin/chat-history/page.tsx`
  - [ ] Subtask 8.2: Compose ChatFilters, ChatSessionList, SessionDetailPanel
  - [ ] Subtask 8.3: Implement responsive layout
  - [ ] Subtask 8.4: Add breadcrumb navigation
  - [ ] Subtask 8.5: Add link from admin dashboard

- [ ] Task 9: Implement loading and error states
  - [ ] Subtask 9.1: Create skeleton loader for session list
  - [ ] Subtask 9.2: Create skeleton loader for conversation thread
  - [ ] Subtask 9.3: Show empty state when no results
  - [ ] Subtask 9.4: Show toast notifications for API errors

- [ ] Task 10: Write unit tests (AC: #10)
  - [ ] Subtask 10.1: Test ChatSessionList renders sessions correctly
  - [ ] Subtask 10.2: Test ConversationThread renders messages with correct styling
  - [ ] Subtask 10.3: Test CitationDisplay renders inline citations
  - [ ] Subtask 10.4: Test ChatFilters apply filters correctly
  - [ ] Subtask 10.5: Test export generates correct JSON/CSV
  - [ ] Subtask 10.6: Test pagination and infinite scroll

## Dev Notes

### Architecture Patterns

- **Component Composition**: Small, focused components composed together
- **Custom Hooks**: Data fetching encapsulated in hooks
- **Infinite Query**: TanStack Query infinite query for message pagination
- **Export Pattern**: Client-side file generation and download

### Key Technical Decisions

- **Chat Bubble Layout**: Follows common chat UI patterns (user right, bot left)
- **Citation Parsing**: Citations stored in message metadata as JSON array
- **Search Debouncing**: 300ms debounce to avoid excessive API calls
- **Export Formats**: JSON for full fidelity, CSV for spreadsheet analysis

### Component Structure

```typescript
// frontend/src/components/admin/chat/conversation-thread.tsx

import { cn } from "@/lib/utils";
import { CitationDisplay } from "./citation-display";

interface ConversationThreadProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export function ConversationThread({ messages, isLoading }: ConversationThreadProps) {
  if (isLoading) {
    return <ConversationSkeleton />;
  }

  return (
    <div className="flex flex-col gap-4 p-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={cn(
            "max-w-[80%] rounded-lg p-4",
            message.role === "user"
              ? "ml-auto bg-primary text-primary-foreground"
              : "mr-auto bg-muted"
          )}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>

          {message.role === "assistant" && message.citations && (
            <CitationDisplay citations={message.citations} />
          )}

          <div className="mt-2 flex items-center gap-2 text-xs opacity-70">
            <span>{formatTime(message.created_at)}</span>
            {message.role === "assistant" && (
              <>
                <span>{message.token_count} tokens</span>
                <span>{message.response_time_ms}ms</span>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Citation Display Implementation

```typescript
// frontend/src/components/admin/chat/citation-display.tsx

interface Citation {
  index: number;
  document_id: string;
  document_name: string;
  chunk_id: string;
  relevance_score: number;
}

interface CitationDisplayProps {
  citations: Citation[];
}

export function CitationDisplay({ citations }: CitationDisplayProps) {
  return (
    <div className="mt-3 border-t pt-2">
      <p className="text-xs font-medium mb-1">Sources:</p>
      <div className="flex flex-wrap gap-1">
        {citations.map((citation) => (
          <a
            key={citation.index}
            href={`/documents/${citation.document_id}?chunk=${citation.chunk_id}`}
            className="text-xs px-2 py-1 bg-background rounded hover:underline"
          >
            [{citation.index}] {citation.document_name}
          </a>
        ))}
      </div>
    </div>
  );
}
```

### Export Implementation

```typescript
// frontend/src/components/admin/chat/export-dialog.tsx

function exportAsJSON(messages: ChatMessage[], filename: string) {
  const data = JSON.stringify(messages, null, 2);
  downloadFile(data, `${filename}.json`, "application/json");
}

function exportAsCSV(messages: ChatMessage[], filename: string) {
  const headers = ["id", "role", "content", "created_at", "token_count", "response_time_ms"];
  const rows = messages.map((m) => [
    m.id,
    m.role,
    `"${m.content.replace(/"/g, '""')}"`, // Escape quotes
    m.created_at,
    m.token_count || "",
    m.response_time_ms || "",
  ]);
  const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  downloadFile(csv, `${filename}.csv`, "text/csv");
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
```

### Source Tree Changes

```
frontend/src/
├── app/(protected)/admin/
│   └── chat-history/
│       └── page.tsx                    # New: Chat history page
├── components/admin/chat/
│   ├── chat-session-list.tsx           # New: Session list table
│   ├── chat-filters.tsx                # New: Filter controls
│   ├── conversation-thread.tsx         # New: Message thread
│   ├── citation-display.tsx            # New: Citation rendering
│   ├── session-detail-panel.tsx        # New: Slide-out panel
│   ├── export-dialog.tsx               # New: Export functionality
│   └── __tests__/
│       ├── chat-session-list.test.tsx  # New: Unit tests
│       ├── conversation-thread.test.tsx# New: Unit tests
│       └── export-dialog.test.tsx      # New: Unit tests
└── hooks/
    └── useChatHistory.ts               # New: Data fetching hooks
```

### Testing Standards

- Mock API responses for all test scenarios
- Test component rendering with various data states
- Test message styling for user vs assistant
- Test citation links are clickable
- Test export generates valid JSON/CSV
- Test search debouncing behavior

### Configuration Dependencies

No new configuration - uses existing admin routes and API client.

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#Story 9-10]
- [Source: docs/epics/epic-9-observability.md]
- [Source: frontend/src/components/chat/ - existing chat components]
- [Source: frontend/src/components/generation/export-modal.tsx - export pattern]

## Dev Agent Record

### Context Reference

- [9-9-chat-history-viewer-ui.context.xml](9-9-chat-history-viewer-ui.context.xml)

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Story drafted | Claude (SM Agent) |
