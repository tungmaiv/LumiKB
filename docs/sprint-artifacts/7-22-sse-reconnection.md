# Story 7-22: SSE Reconnection

| Field | Value |
|-------|-------|
| **Story ID** | 7-22 |
| **Epic** | Epic 7 - Tech Debt Sprint (Pre-Epic 8) |
| **Priority** | MEDIUM |
| **Effort** | 3 hours |
| **Resolves** | TD-4.2-1 |
| **Status** | Done |
| **Context** | [7-22-sse-reconnection.context.xml](7-22-sse-reconnection.context.xml) |

## User Story

**As a** user viewing streaming content
**I want** the connection to automatically reconnect if it drops
**So that** I don't lose my streaming session due to temporary network issues

## Background

Story 4-2 (Chat Streaming UI) implemented SSE streaming but the reconnection logic was deferred. Currently, if the EventSource connection drops, the user sees an error and must manually refresh. This story adds automatic reconnection with exponential backoff and a polling fallback.

## Acceptance Criteria

### AC-7.22.1: Automatic Reconnection on Disconnect
- **Given** an active SSE stream
- **When** the connection drops unexpectedly
- **Then** the client attempts to reconnect automatically
- **And** shows a "Reconnecting..." indicator

### AC-7.22.2: Exponential Backoff
- **Given** reconnection attempts are in progress
- **When** each attempt fails
- **Then** the delay doubles: 1s → 2s → 4s → 8s → max 30s
- **And** attempt count is shown to user

### AC-7.22.3: Reconnection Success Recovery
- **Given** a reconnection attempt succeeds
- **When** the stream resumes
- **Then** the "Reconnecting" indicator is hidden
- **And** streaming continues from last received position (using `Last-Event-ID`)

### AC-7.22.4: Max Retry Limit
- **Given** reconnection attempts exceed 5 failures
- **When** the 5th attempt fails
- **Then** show an error message: "Connection lost. Please refresh."
- **And** provide a manual "Retry" button

### AC-7.22.5: Polling Fallback
- **Given** SSE is not supported or consistently failing
- **When** reconnection exhausts retries
- **Then** offer polling fallback option
- **And** poll every 2 seconds if enabled

### AC-7.22.6: Unit Test Coverage
- **Given** the implementation is complete
- **When** unit tests run
- **Then** reconnection logic has ≥80% coverage

## Tasks

### Task 1: Create useSSEReconnection Hook
- [ ] 1.1 Create hook with reconnection state management
- [ ] 1.2 Implement exponential backoff timer
- [ ] 1.3 Track attempt count and max retries
- [ ] 1.4 Handle `Last-Event-ID` for resume

### Task 2: Update SSE Stream Hook
- [ ] 2.1 Integrate reconnection hook into existing SSE logic
- [ ] 2.2 Handle `onerror` event with reconnection trigger
- [ ] 2.3 Reset retry count on successful connection
- [ ] 2.4 Pass `Last-Event-ID` header on reconnect

### Task 3: Reconnection UI Indicators
- [ ] 3.1 Add "Reconnecting... (attempt X/5)" message
- [ ] 3.2 Add progress indicator during reconnection
- [ ] 3.3 Add "Connection lost" error state
- [ ] 3.4 Add manual "Retry" button

### Task 4: Polling Fallback
- [ ] 4.1 Implement polling alternative using `setInterval`
- [ ] 4.2 Add "Use polling" option in error state
- [ ] 4.3 Poll endpoint for message updates
- [ ] 4.4 Merge polled data with existing messages

### Task 5: Testing
- [ ] 5.1 Unit test exponential backoff timing
- [ ] 5.2 Unit test retry count limiting
- [ ] 5.3 Unit test Last-Event-ID handling
- [ ] 5.4 Unit test polling fallback

## Dev Notes

### Implementation Pattern
```tsx
// useSSEReconnection.ts
interface ReconnectionState {
  isReconnecting: boolean;
  attemptCount: number;
  lastEventId: string | null;
  error: string | null;
}

export function useSSEReconnection(maxRetries = 5) {
  const [state, setState] = useState<ReconnectionState>({
    isReconnecting: false,
    attemptCount: 0,
    lastEventId: null,
    error: null
  });

  const getBackoffDelay = (attempt: number) =>
    Math.min(1000 * Math.pow(2, attempt), 30000);

  const scheduleReconnect = useCallback((onReconnect: () => void) => {
    if (state.attemptCount >= maxRetries) {
      setState(s => ({ ...s, error: 'Connection lost. Please refresh.' }));
      return;
    }

    setState(s => ({ ...s, isReconnecting: true, attemptCount: s.attemptCount + 1 }));

    const delay = getBackoffDelay(state.attemptCount);
    setTimeout(() => {
      onReconnect();
    }, delay);
  }, [state.attemptCount, maxRetries]);

  const onSuccess = useCallback(() => {
    setState({ isReconnecting: false, attemptCount: 0, lastEventId: null, error: null });
  }, []);

  const setLastEventId = useCallback((id: string) => {
    setState(s => ({ ...s, lastEventId: id }));
  }, []);

  return { ...state, scheduleReconnect, onSuccess, setLastEventId };
}
```

```tsx
// Integration in useChatStream.ts
const { isReconnecting, attemptCount, scheduleReconnect, onSuccess, setLastEventId } =
  useSSEReconnection();

const connect = useCallback(() => {
  const eventSource = new EventSource(url, {
    headers: lastEventId ? { 'Last-Event-ID': lastEventId } : undefined
  });

  eventSource.onmessage = (event) => {
    setLastEventId(event.lastEventId);
    // handle message...
  };

  eventSource.onerror = () => {
    eventSource.close();
    scheduleReconnect(connect);
  };

  eventSource.onopen = () => {
    onSuccess();
  };
}, [lastEventId, scheduleReconnect, onSuccess]);
```

### Key Files
- `frontend/src/hooks/useSSEReconnection.ts` - New reconnection hook
- `frontend/src/hooks/useChatManagement.ts` - Integrate reconnection
- `frontend/src/hooks/useGenerationStream.ts` - Integrate reconnection
- `frontend/src/components/chat/reconnection-indicator.tsx` - New UI component

### Dependencies
- useChatManagement (Story 4-1) - COMPLETED
- useGenerationStream (Story 4-5) - COMPLETED

## Testing Strategy

### Unit Tests
- Mock timers for backoff testing
- Test state transitions
- Test retry count limiting
- Test Last-Event-ID tracking

## Definition of Done
- [x] All ACs pass
- [x] Unit tests ≥80% coverage on modified files
- [x] No eslint errors
- [x] Code reviewed

## Dev Agent Record

### Completion Summary (2025-12-10)

**Code Review:** APPROVED (see [code-review-stories-7-21-7-22-7-23.md](code-review-stories-7-21-7-22-7-23.md))

**Test Results:**
- 40/40 tests passing (22 hook tests + 18 component tests)

**Files Implemented:**
- `frontend/src/hooks/useSSEReconnection.ts` - Reconnection logic (~200 lines)
- `frontend/src/components/chat/reconnection-indicator.tsx` - UI components (~150 lines)
- `frontend/src/hooks/__tests__/useSSEReconnection.test.ts` - Hook tests (~250 lines)
- `frontend/src/components/chat/__tests__/reconnection-indicator.test.tsx` - Component tests (~200 lines)

**Key Features:**
- Automatic reconnection on disconnect (AC-7.22.1)
- Exponential backoff: 1s → 2s → 4s → 8s → max 30s (AC-7.22.2)
- Last-Event-ID tracking for resume (AC-7.22.3)
- Max 5 retry limit with error state (AC-7.22.4)
- Polling fallback at 2s interval (AC-7.22.5)
- ReconnectionIndicator and ReconnectionIndicatorInline components (AC-7.22.6)

**Tech Debt Resolved:** TD-4.2-1
