# Story 9.8: Trace Viewer UI Component

Status: ready-for-dev

## Story

As a **system administrator**,
I want **a React component for viewing distributed traces with a waterfall visualization showing all spans, their timing, and type-specific metrics**,
so that **I can debug and analyze request flows across the system to identify performance bottlenecks and errors**.

## Acceptance Criteria

1. Trace list view displays operation type, document ID, status, duration, span count, and timestamp
2. Filtering controls for operation type (document_processing, chat, search), status (completed, failed), date range, and search (trace ID or name)
3. Click trace row to view detail panel (slide-out or modal)
4. Trace detail shows timeline of spans in waterfall view with duration bars
5. Span details show type-specific metrics (LLM: model/tokens/cost, DB: query/rows, External: URL/status)
6. Error spans highlighted in red with error message displayed
7. LLM spans prominently show model name, token counts (input/output), and cost (if available)
8. Responsive design for admin dashboard integration (works on desktop and tablet)
9. Loading states (skeleton) and error handling (toast notifications)
10. Unit tests for component rendering and user interactions

## Tasks / Subtasks

- [x] Task 1: Create trace list component (AC: #1, #2)
  - [x] Subtask 1.1: Create `frontend/src/components/admin/traces/trace-list.tsx`
  - [x] Subtask 1.2: Implement data table with columns: Operation, Document, Status, Duration, Spans, Time
  - [x] Subtask 1.3: Add status badge with color coding (green=completed, red=failed, yellow=in_progress)
  - [x] Subtask 1.4: Format duration in human-readable format (ms, s, min)
  - [x] Subtask 1.5: Add click handler to select trace
  - [x] Subtask 1.6: Add document ID column with truncated display and FileText icon

- [x] Task 2: Create filter controls component (AC: #2)
  - [x] Subtask 2.1: Create `frontend/src/components/admin/traces/trace-filters.tsx`
  - [x] Subtask 2.2: Add operation type dropdown (All, Document Processing, Chat, Search, Embedding)
  - [x] Subtask 2.3: Add status dropdown (All, Completed, Failed, In Progress)
  - [x] Subtask 2.4: Add date range picker (start date, end date)
  - [x] Subtask 2.5: Implement filter state management with reactive updates
  - [x] Subtask 2.6: Add search input for trace ID or name (case-insensitive)
  - [x] Subtask 2.7: Add clear filters button

- [ ] Task 3: Create trace detail panel (AC: #3, #4)
  - [ ] Subtask 3.1: Create `frontend/src/components/admin/traces/trace-detail-panel.tsx`
  - [ ] Subtask 3.2: Implement slide-out panel from right side
  - [ ] Subtask 3.3: Show trace header: trace_id, operation_type, status, total duration
  - [ ] Subtask 3.4: Render waterfall view container for spans

- [ ] Task 4: Create waterfall timeline visualization (AC: #4)
  - [ ] Subtask 4.1: Create `frontend/src/components/admin/traces/waterfall-timeline.tsx`
  - [ ] Subtask 4.2: Calculate span positions based on relative start times
  - [ ] Subtask 4.3: Render horizontal bars proportional to duration
  - [ ] Subtask 4.4: Nest child spans under parent with indentation
  - [ ] Subtask 4.5: Add time scale header (0ms, 100ms, 200ms, etc.)

- [ ] Task 5: Create span detail component (AC: #5, #6, #7)
  - [ ] Subtask 5.1: Create `frontend/src/components/admin/traces/span-detail.tsx`
  - [ ] Subtask 5.2: Show span name, type, status, duration
  - [ ] Subtask 5.3: Render type-specific metrics based on span_type
  - [ ] Subtask 5.4: LLM spans: display model, input_tokens, output_tokens, cost_usd
  - [ ] Subtask 5.5: DB spans: display query snippet, rows_affected
  - [ ] Subtask 5.6: External spans: display URL, status_code, response_time
  - [ ] Subtask 5.7: Highlight error spans with red border/background
  - [ ] Subtask 5.8: Display error_message for failed spans

- [ ] Task 6: Create custom hooks for trace data (AC: #9)
  - [ ] Subtask 6.1: Create `frontend/src/hooks/useTraces.ts`
  - [ ] Subtask 6.2: Implement useTraces() hook with filters and pagination
  - [ ] Subtask 6.3: Implement useTraceDetail(traceId) hook
  - [ ] Subtask 6.4: Handle loading, error, and refetch states
  - [ ] Subtask 6.5: Use TanStack Query for caching and revalidation

- [ ] Task 7: Create main trace viewer page (AC: #8)
  - [ ] Subtask 7.1: Create `frontend/src/app/(protected)/admin/traces/page.tsx`
  - [ ] Subtask 7.2: Compose TraceFilters, TraceList, TraceDetailPanel
  - [ ] Subtask 7.3: Implement responsive layout (side panel on desktop, full screen on mobile)
  - [ ] Subtask 7.4: Add breadcrumb navigation

- [ ] Task 8: Implement loading and error states (AC: #9)
  - [ ] Subtask 8.1: Create skeleton loader for trace list
  - [ ] Subtask 8.2: Create skeleton loader for waterfall timeline
  - [ ] Subtask 8.3: Add error boundary for component failures
  - [ ] Subtask 8.4: Show toast notifications for API errors

- [ ] Task 9: Write unit tests (AC: #10)
  - [ ] Subtask 9.1: Test TraceList renders traces correctly
  - [ ] Subtask 9.2: Test TraceFilters apply filters correctly
  - [ ] Subtask 9.3: Test WaterfallTimeline positions spans correctly
  - [ ] Subtask 9.4: Test SpanDetail renders type-specific metrics
  - [ ] Subtask 9.5: Test error span highlighting
  - [ ] Subtask 9.6: Test loading states display correctly
  - [ ] Subtask 9.7: Test click interactions open detail panel

## Dev Notes

### Architecture Patterns

- **Component Composition**: Small, focused components composed together
- **Custom Hooks**: Data fetching encapsulated in hooks (useTraces, useTraceDetail)
- **TanStack Query**: For server state management with caching
- **Responsive Design**: Mobile-first with breakpoint-based layouts

### Key Technical Decisions

- **Waterfall Visualization**: CSS-based with percentage widths (no canvas/SVG for simplicity)
- **Panel Pattern**: Slide-out panel for detail view (consistent with existing admin UI)
- **Color Coding**: Consistent status colors across all admin components
- **Lazy Loading**: Trace detail fetched on-demand when trace selected

### Component Structure

```typescript
// frontend/src/components/admin/traces/trace-list.tsx

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Circle, Clock, FileText, XCircle } from 'lucide-react';

interface TraceListItem {
  trace_id: string;
  name: string;
  status: string;
  user_id: string | null;
  kb_id: string | null;
  document_id: string | null;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  span_count: number;
}

interface TraceListProps {
  traces: TraceListItem[];
  selectedTraceId: string | null;
  onSelectTrace: (traceId: string) => void;
}

export function TraceList({ traces, selectedTraceId, onSelectTrace }: TraceListProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Operation</TableHead>
          <TableHead>Document</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Duration</TableHead>
          <TableHead>Spans</TableHead>
          <TableHead>Time</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {traces.map((trace) => (
          <TableRow
            key={trace.trace_id}
            data-testid={`trace-row-${trace.trace_id}`}
            className={selectedTraceId === trace.trace_id ? "bg-muted cursor-pointer" : "cursor-pointer hover:bg-muted/50"}
            onClick={() => onSelectTrace(trace.trace_id)}
          >
            <TableCell>{formatOperationName(trace.name)}</TableCell>
            <TableCell>
              {trace.document_id ? (
                <span className="flex items-center gap-1 text-xs text-muted-foreground font-mono">
                  <FileText className="h-3 w-3" />
                  {trace.document_id.slice(0, 8)}...
                </span>
              ) : (
                <span className="text-xs text-muted-foreground">-</span>
              )}
            </TableCell>
            <TableCell>
              <StatusBadge status={trace.status} />
            </TableCell>
            <TableCell>{formatDuration(trace.duration_ms)}</TableCell>
            <TableCell>{trace.span_count}</TableCell>
            <TableCell>{formatRelativeTime(trace.started_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

### Waterfall Timeline Implementation

```typescript
// frontend/src/components/admin/traces/waterfall-timeline.tsx

interface WaterfallTimelineProps {
  spans: SpanDetail[];
  totalDuration: number;
}

export function WaterfallTimeline({ spans, totalDuration }: WaterfallTimelineProps) {
  // Calculate percentage positions
  const getBarStyle = (span: SpanDetail) => {
    const startPercent = (span.relative_start_ms / totalDuration) * 100;
    const widthPercent = ((span.duration_ms || 0) / totalDuration) * 100;
    return {
      left: `${startPercent}%`,
      width: `${Math.max(widthPercent, 1)}%`, // Minimum 1% width for visibility
    };
  };

  return (
    <div className="space-y-1">
      <TimeScaleHeader totalDuration={totalDuration} />
      {spans.map((span, index) => (
        <div key={span.span_id} className="flex items-center h-8">
          <div className="w-48 truncate text-sm">{span.name}</div>
          <div className="flex-1 relative h-6 bg-muted rounded">
            <div
              className={cn(
                "absolute h-full rounded",
                span.status === "failed" ? "bg-destructive" : "bg-primary"
              )}
              style={getBarStyle(span)}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Custom Hook Implementation

```typescript
// frontend/src/hooks/useTraces.ts

import { useQuery } from "@tanstack/react-query";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UseTracesOptions {
  operation_type?: string;
  status?: string;
  user_id?: string;
  kb_id?: string;
  start_date?: string;
  end_date?: string;
  search?: string;  // Search in trace ID or name (case-insensitive)
  skip?: number;
  limit?: number;
}

export function useTraces(options: UseTracesOptions = {}) {
  return useQuery({
    queryKey: ["traces", options],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (options.operation_type) params.set('operation_type', options.operation_type);
      if (options.status) params.set('status', options.status);
      if (options.user_id) params.set('user_id', options.user_id);
      if (options.kb_id) params.set('kb_id', options.kb_id);
      if (options.start_date) params.set('start_date', options.start_date);
      if (options.end_date) params.set('end_date', options.end_date);
      if (options.search) params.set('search', options.search);
      if (options.skip !== undefined) params.set('skip', options.skip.toString());
      if (options.limit !== undefined) params.set('limit', options.limit.toString());

      const res = await fetch(
        `${API_BASE_URL}/api/v1/observability/traces?${params.toString()}`,
        { credentials: 'include' }
      );
      if (!res.ok) throw new Error('Failed to fetch traces');
      return res.json();
    },
    staleTime: 30_000, // 30 seconds
    refetchInterval: 30_000, // Auto-refresh every 30 seconds
    retry: 1,
  });
}

export function useTraceDetail(traceId: string | null) {
  return useQuery({
    queryKey: ["trace", traceId],
    queryFn: async () => {
      if (!traceId) throw new Error('Trace ID required');
      const res = await fetch(
        `${API_BASE_URL}/api/v1/observability/traces/${traceId}`,
        { credentials: 'include' }
      );
      if (!res.ok) throw new Error('Failed to fetch trace detail');
      return res.json();
    },
    enabled: !!traceId,
    staleTime: 60_000, // 1 minute
    retry: 1,
  });
}
```

### Source Tree Changes

```
frontend/src/
├── app/(protected)/admin/
│   └── traces/
│       └── page.tsx                    # New: Trace viewer page
├── components/admin/traces/
│   ├── trace-list.tsx                  # New: Trace list table
│   ├── trace-filters.tsx               # New: Filter controls
│   ├── trace-detail-panel.tsx          # New: Slide-out detail panel
│   ├── waterfall-timeline.tsx          # New: Waterfall visualization
│   ├── span-detail.tsx                 # New: Span detail card
│   └── __tests__/
│       ├── trace-list.test.tsx         # New: Unit tests
│       ├── waterfall-timeline.test.tsx # New: Unit tests
│       └── span-detail.test.tsx        # New: Unit tests
└── hooks/
    └── useTraces.ts                    # New: Data fetching hooks
```

### Testing Standards

- Mock API responses for all test scenarios
- Test component rendering with various data states
- Test user interactions (clicks, filter changes)
- Test responsive behavior at different breakpoints
- Snapshot tests for visual regression

### Configuration Dependencies

No new configuration - uses existing admin routes and API client.

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#Story 9-9]
- [Source: docs/epics/epic-9-observability.md]
- [Source: frontend/src/components/admin/ - existing admin components]
- [Source: frontend/src/hooks/useAdminStats.ts - existing hook pattern]

## Dev Agent Record

### Context Reference

- [9-8-trace-viewer-ui-component.context.xml](9-8-trace-viewer-ui-component.context.xml)

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Story drafted | Claude (SM Agent) |
