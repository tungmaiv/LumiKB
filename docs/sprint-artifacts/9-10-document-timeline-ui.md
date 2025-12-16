# Story 9.10: Document Timeline UI

Status: ready-for-dev

## Story

As a **system administrator**,
I want **a React component showing the document processing timeline with step-by-step visualization of upload, parse, chunk, embed, and index stages**,
so that **I can quickly identify which processing step failed or took longer than expected for troubleshooting document ingestion issues**.

## Acceptance Criteria

1. Access via "View Processing" button in document detail modal
2. Timeline visualization shows all processing steps in vertical layout
3. Each step shows status icon (pending=gray, in-progress=blue spinner, completed=green check, failed=red X)
4. Step duration displayed in human-readable format (e.g., "2.3s", "45ms")
5. Click step to see detailed metrics (chunks created, vectors generated, etc.)
6. Error steps show error type and full error message
7. Retry count visible for failed steps that were retried
8. Total processing time summarized at top of timeline
9. Responsive design for modal display
10. Unit tests for timeline rendering and interactions

## Tasks / Subtasks

- [ ] Task 1: Create timeline container component (AC: #2, #8)
  - [ ] Subtask 1.1: Create `frontend/src/components/admin/documents/processing-timeline.tsx`
  - [ ] Subtask 1.2: Implement vertical timeline layout with connector lines
  - [ ] Subtask 1.3: Show total processing time at top
  - [ ] Subtask 1.4: Calculate and display overall status (completed, in-progress, failed)

- [ ] Task 2: Create timeline step component (AC: #3, #4, #7)
  - [ ] Subtask 2.1: Create `frontend/src/components/admin/documents/timeline-step.tsx`
  - [ ] Subtask 2.2: Implement status icon with color coding
  - [ ] Subtask 2.3: Add step name label (Upload, Parse, Chunk, Embed, Index)
  - [ ] Subtask 2.4: Display duration in human-readable format
  - [ ] Subtask 2.5: Show retry badge if retry_count > 0
  - [ ] Subtask 2.6: Make step clickable to expand details

- [ ] Task 3: Create step detail panel (AC: #5, #6)
  - [ ] Subtask 3.1: Create `frontend/src/components/admin/documents/step-detail.tsx`
  - [ ] Subtask 3.2: Show step-specific metrics based on step type
  - [ ] Subtask 3.3: Upload: file_size, mime_type
  - [ ] Subtask 3.4: Parse: pages_extracted, text_length, parser_used
  - [ ] Subtask 3.5: Chunk: chunks_created, avg_chunk_size
  - [ ] Subtask 3.6: Embed: vectors_generated, embedding_model
  - [ ] Subtask 3.7: Index: points_indexed, collection_name
  - [ ] Subtask 3.8: Display error_type and error_message for failed steps

- [ ] Task 4: Create status icon component (AC: #3)
  - [ ] Subtask 4.1: Create `frontend/src/components/admin/documents/status-icon.tsx`
  - [ ] Subtask 4.2: Pending: gray circle outline
  - [ ] Subtask 4.3: In-progress: blue spinner animation
  - [ ] Subtask 4.4: Completed: green check circle
  - [ ] Subtask 4.5: Failed: red X circle
  - [ ] Subtask 4.6: Use Lucide icons with consistent sizing

- [ ] Task 5: Create modal integration (AC: #1)
  - [ ] Subtask 5.1: Add "View Processing" button to DocumentDetailModal
  - [ ] Subtask 5.2: Create processing timeline modal/dialog
  - [ ] Subtask 5.3: Pass document_id to timeline component
  - [ ] Subtask 5.4: Handle modal open/close state

- [ ] Task 6: Create custom hook for timeline data (AC: #9)
  - [ ] Subtask 6.1: Create `frontend/src/hooks/useDocumentTimeline.ts`
  - [ ] Subtask 6.2: Fetch from `/observability/documents/{id}/timeline`
  - [ ] Subtask 6.3: Handle loading and error states
  - [ ] Subtask 6.4: Auto-refresh while document is processing (polling)

- [ ] Task 7: Implement loading and error states (AC: #9)
  - [ ] Subtask 7.1: Create skeleton loader for timeline
  - [ ] Subtask 7.2: Show empty state if no events found
  - [ ] Subtask 7.3: Show toast notifications for API errors

- [ ] Task 8: Write unit tests (AC: #10)
  - [ ] Subtask 8.1: Test ProcessingTimeline renders all steps
  - [ ] Subtask 8.2: Test TimelineStep shows correct status icons
  - [ ] Subtask 8.3: Test StepDetail shows type-specific metrics
  - [ ] Subtask 8.4: Test StatusIcon renders correct icons for each status
  - [ ] Subtask 8.5: Test click to expand step details
  - [ ] Subtask 8.6: Test retry count badge displayed

## Dev Notes

### Architecture Patterns

- **Component Composition**: Timeline composed of step components
- **Collapsible Details**: Click step to expand/collapse metrics
- **Polling Pattern**: Auto-refresh while processing is in-progress
- **Modal Integration**: Embedded in existing document detail modal

### Key Technical Decisions

- **Vertical Timeline**: Vertical layout for clear step sequence
- **Status Icons**: Lucide icons for consistency with rest of UI
- **Duration Formatting**: Human-readable (45ms, 2.3s, 1m 30s)
- **Auto-Refresh**: 2-second polling interval while status != completed/failed

### Component Structure

```typescript
// frontend/src/components/admin/documents/processing-timeline.tsx

import { TimelineStep } from "./timeline-step";
import { useDocumentTimeline } from "@/hooks/useDocumentTimeline";
import { formatDuration } from "@/lib/utils";

interface ProcessingTimelineProps {
  documentId: string;
}

export function ProcessingTimeline({ documentId }: ProcessingTimelineProps) {
  const { data, isLoading, error } = useDocumentTimeline(documentId);

  if (isLoading) {
    return <TimelineSkeleton />;
  }

  if (error) {
    return <TimelineError error={error} />;
  }

  const { events, total_duration_ms } = data;

  return (
    <div className="space-y-4">
      {/* Summary header */}
      <div className="flex items-center justify-between border-b pb-2">
        <h3 className="font-medium">Processing Timeline</h3>
        <span className="text-sm text-muted-foreground">
          Total: {formatDuration(total_duration_ms)}
        </span>
      </div>

      {/* Timeline steps */}
      <div className="relative pl-6">
        {/* Vertical connector line */}
        <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-border" />

        <div className="space-y-4">
          {events.map((event, index) => (
            <TimelineStep
              key={event.id}
              event={event}
              isLast={index === events.length - 1}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
```

### Timeline Step Implementation

```typescript
// frontend/src/components/admin/documents/timeline-step.tsx

import { useState } from "react";
import { StatusIcon } from "./status-icon";
import { StepDetail } from "./step-detail";
import { formatDuration } from "@/lib/utils";
import { ChevronDown, ChevronRight } from "lucide-react";

interface TimelineStepProps {
  event: DocumentEvent;
  isLast: boolean;
}

export function TimelineStep({ event, isLast }: TimelineStepProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="relative">
      {/* Status icon positioned on the connector line */}
      <div className="absolute -left-6 mt-1">
        <StatusIcon status={event.status} />
      </div>

      {/* Step content */}
      <div
        className="cursor-pointer rounded-lg border p-3 hover:bg-muted/50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <span className="font-medium capitalize">{event.step_name}</span>
            {event.retry_count > 0 && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-warning text-warning-foreground">
                Retry {event.retry_count}
              </span>
            )}
          </div>
          <span className="text-sm text-muted-foreground">
            {event.duration_ms ? formatDuration(event.duration_ms) : "..."}
          </span>
        </div>

        {/* Expanded detail */}
        {isExpanded && <StepDetail event={event} />}
      </div>
    </div>
  );
}
```

### Step-Specific Metrics

```typescript
// frontend/src/components/admin/documents/step-detail.tsx

interface StepDetailProps {
  event: DocumentEvent;
}

export function StepDetail({ event }: StepDetailProps) {
  const { step_name, status, metrics, error_message } = event;

  return (
    <div className="mt-3 pt-3 border-t">
      {/* Error message for failed steps */}
      {status === "failed" && error_message && (
        <div className="mb-3 p-2 rounded bg-destructive/10 text-destructive text-sm">
          <span className="font-medium">Error: </span>
          {error_message}
        </div>
      )}

      {/* Step-specific metrics */}
      <div className="grid grid-cols-2 gap-2 text-sm">
        {step_name === "upload" && (
          <>
            <MetricItem label="File Size" value={formatBytes(metrics?.file_size)} />
            <MetricItem label="MIME Type" value={metrics?.mime_type} />
          </>
        )}
        {step_name === "parse" && (
          <>
            <MetricItem label="Pages" value={metrics?.pages_extracted} />
            <MetricItem label="Text Length" value={formatNumber(metrics?.text_length)} />
            <MetricItem label="Parser" value={metrics?.parser_used} />
          </>
        )}
        {step_name === "chunk" && (
          <>
            <MetricItem label="Chunks" value={metrics?.chunks_created} />
            <MetricItem label="Avg Size" value={formatNumber(metrics?.avg_chunk_size)} />
          </>
        )}
        {step_name === "embed" && (
          <>
            <MetricItem label="Vectors" value={metrics?.vectors_generated} />
            <MetricItem label="Model" value={metrics?.embedding_model} />
          </>
        )}
        {step_name === "index" && (
          <>
            <MetricItem label="Points" value={metrics?.points_indexed} />
            <MetricItem label="Collection" value={metrics?.collection_name} />
          </>
        )}
      </div>
    </div>
  );
}
```

### Custom Hook with Polling

```typescript
// frontend/src/hooks/useDocumentTimeline.ts

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useDocumentTimeline(documentId: string) {
  return useQuery({
    queryKey: ["document-timeline", documentId],
    queryFn: () => api.get(`/observability/documents/${documentId}/timeline`),
    refetchInterval: (data) => {
      // Poll every 2 seconds if still processing
      const events = data?.events || [];
      const lastEvent = events[events.length - 1];
      const isProcessing = lastEvent?.status === "started" || lastEvent?.status === "in_progress";
      return isProcessing ? 2000 : false;
    },
  });
}
```

### Source Tree Changes

```
frontend/src/
├── components/
│   ├── admin/documents/
│   │   ├── processing-timeline.tsx     # New: Main timeline component
│   │   ├── timeline-step.tsx           # New: Individual step
│   │   ├── step-detail.tsx             # New: Step metrics
│   │   ├── status-icon.tsx             # New: Status icons
│   │   └── __tests__/
│   │       ├── processing-timeline.test.tsx  # New
│   │       ├── timeline-step.test.tsx        # New
│   │       └── step-detail.test.tsx          # New
│   └── documents/
│       └── document-detail-modal.tsx   # Modified: Add "View Processing" button
└── hooks/
    └── useDocumentTimeline.ts          # New: Data fetching hook
```

### Testing Standards

- Mock API responses for all step statuses
- Test status icon renders correctly for each status
- Test step expansion/collapse behavior
- Test metrics displayed for each step type
- Test error message display for failed steps
- Test polling behavior during processing

### Configuration Dependencies

No new configuration - uses existing document routes and observability API.

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#Story 9-11]
- [Source: docs/epics/epic-9-observability.md]
- [Source: frontend/src/components/documents/document-detail-modal.tsx - integration point]
- [Source: frontend/src/components/documents/upload-dropzone.tsx - progress pattern]

## Dev Agent Record

### Context Reference

- [9-10-document-timeline-ui.context.xml](9-10-document-timeline-ui.context.xml)

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-15 | Story drafted | Claude (SM Agent) |
