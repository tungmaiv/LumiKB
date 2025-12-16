# Story 9-12: Observability Dashboard Widgets

Status: ready-for-dev

## Story

As an **Admin user**,
I want observability widgets integrated into the admin dashboard,
so that I can monitor LLM usage, processing pipeline health, and chat activity at a glance.

## Acceptance Criteria

1. **AC1:** "LLM Usage" widget displays total tokens, cost, breakdown by model
2. **AC2:** "Processing Pipeline" widget shows documents processed, avg time, error rate
3. **AC3:** "Chat Activity" widget shows messages today, active sessions, avg response time
4. **AC4:** "System Health" widget shows trace success rate, p95 latency
5. **AC5:** Time period selector (hour/day/week/month) for all widgets
6. **AC6:** Auto-refresh every 30 seconds (configurable)
7. **AC7:** Sparkline charts for trends
8. **AC8:** Click widget to navigate to detailed view
9. **AC9:** Widgets load independently (parallel fetching)
10. **AC10:** Unit tests for widget components

## Tasks / Subtasks

- [ ] Task 1: Create LLM Usage Widget (AC: 1, 7, 8)
  - [ ] Create `frontend/src/components/admin/widgets/llm-usage-widget.tsx`
  - [ ] Display total tokens (prompt + completion)
  - [ ] Display total cost in USD
  - [ ] Show breakdown by model (table or chart)
  - [ ] Add sparkline for token trend
  - [ ] Link to detailed trace view on click

- [ ] Task 2: Create Processing Pipeline Widget (AC: 2, 7, 8)
  - [ ] Create `frontend/src/components/admin/widgets/processing-widget.tsx`
  - [ ] Display documents processed count
  - [ ] Display average processing time
  - [ ] Display error rate percentage
  - [ ] Add sparkline for processing volume
  - [ ] Link to document timeline on click

- [ ] Task 3: Create Chat Activity Widget (AC: 3, 7, 8)
  - [ ] Create `frontend/src/components/admin/widgets/chat-activity-widget.tsx`
  - [ ] Display message count for period
  - [ ] Display active session count
  - [ ] Display average response time
  - [ ] Add sparkline for message trend
  - [ ] Link to chat history viewer on click

- [ ] Task 4: Create System Health Widget (AC: 4, 7, 8)
  - [ ] Create `frontend/src/components/admin/widgets/system-health-widget.tsx`
  - [ ] Display trace success rate percentage
  - [ ] Display p95 latency
  - [ ] Display error count
  - [ ] Add sparkline for success rate trend
  - [ ] Link to trace viewer on click

- [ ] Task 5: Implement time period selector (AC: 5)
  - [ ] Create shared time period selector component
  - [ ] Support hour/day/week/month options
  - [ ] Persist selection in URL params or localStorage
  - [ ] Pass selected period to all widgets

- [ ] Task 6: Implement auto-refresh (AC: 6)
  - [ ] Add refresh interval configuration (default 30s)
  - [ ] Implement polling with React Query or SWR
  - [ ] Add manual refresh button
  - [ ] Show last updated timestamp

- [ ] Task 7: Implement parallel data fetching (AC: 9)
  - [ ] Create custom hooks for each widget data
  - [ ] Use React Query for parallel fetching
  - [ ] Implement independent loading states
  - [ ] Handle individual widget errors gracefully

- [ ] Task 8: Create widget grid layout
  - [ ] Create `frontend/src/components/admin/observability-dashboard.tsx`
  - [ ] Responsive grid layout (2x2 desktop, 1 column mobile)
  - [ ] Consistent widget card styling
  - [ ] Hover effects and interactions

- [ ] Task 9: Create sparkline chart component
  - [ ] Create reusable sparkline component
  - [ ] Use lightweight chart library (e.g., recharts mini)
  - [ ] Support trend data format
  - [ ] Configurable colors for up/down trends

- [ ] Task 10: Write tests (AC: 10)
  - [ ] Unit tests for each widget component
  - [ ] Test time period selector functionality
  - [ ] Test auto-refresh behavior
  - [ ] Test loading and error states
  - [ ] Test navigation on click

## Dev Notes

### Learnings from Previous Story

**Story 9-10 (Document Timeline UI)** established key patterns:
- **React Query Polling:** `refetchInterval` callback pattern for conditional auto-refresh - reuse for widget refresh
- **Component Composition:** Nested component structure (Timeline → Step → Detail) - similar pattern for widgets
- **Status Visualization:** Color-coded status icons (gray/blue/green/red) - apply to health indicators
- **Human-Readable Formatting:** `formatDuration()` utility - reuse for latency display
- **Source:** [stories/9-10-document-timeline-ui.md#Custom Hook with Polling]

### Dependencies

- **Story 9-7 (Observability Admin API):** `GET /api/v1/observability/stats` endpoint must be implemented - widgets consume this data
- **Story 9-1 (Observability Schema):** TimescaleDB schema must exist for stats aggregation queries

### Architecture Patterns

- **Widget Pattern:** Self-contained components with independent data fetching
- **React Query/SWR:** For parallel fetching and caching
- **Composition:** Reusable sparkline and card components
- **Responsive Design:** Mobile-first with breakpoint-based layouts

### Widget Data Structure

```typescript
interface LLMUsageData {
  totalTokens: number;
  promptTokens: number;
  completionTokens: number;
  totalCostUsd: number;
  byModel: Array<{
    model: string;
    tokens: number;
    cost: number;
  }>;
  trend: Array<{ timestamp: string; value: number }>;
}

interface ProcessingPipelineData {
  documentsProcessed: number;
  avgProcessingTimeMs: number;
  errorRate: number;
  trend: Array<{ timestamp: string; value: number }>;
}

interface ChatActivityData {
  messageCount: number;
  activeSessionCount: number;
  avgResponseTimeMs: number;
  trend: Array<{ timestamp: string; value: number }>;
}

interface SystemHealthData {
  traceSuccessRate: number;
  p95LatencyMs: number;
  errorCount: number;
  trend: Array<{ timestamp: string; value: number }>;
}
```

### API Endpoints Used

- `GET /api/v1/observability/stats?period={period}` - Main stats endpoint
- Widgets derive data from the unified stats response

### Sparkline Implementation

```tsx
// Using recharts for lightweight sparklines
import { Sparklines, SparklinesLine } from 'react-sparklines';

<Sparklines data={trend.map(t => t.value)} width={100} height={20}>
  <SparklinesLine color="#10B981" />
</Sparklines>
```

### Source Tree Components

- `frontend/src/components/admin/widgets/` - Widget components directory
- `frontend/src/components/admin/observability-dashboard.tsx` - Dashboard container
- `frontend/src/hooks/useObservabilityStats.ts` - Data fetching hook
- `frontend/src/app/(protected)/admin/observability/page.tsx` - Route page
- `frontend/src/components/admin/widgets/__tests__/` - Widget tests

### Dependencies

- React Query or SWR for data fetching
- Sparkline library (react-sparklines or recharts)
- Shadcn/ui Card component (existing)

### Testing Standards

- Use React Testing Library
- Mock API responses for unit tests
- Test loading, success, and error states
- Verify navigation behavior
- Test responsive behavior

### Project Structure Notes

- Follows existing admin component patterns
- Uses existing Shadcn/ui design system
- Aligns with frontend/src structure conventions

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-9-observability.md#Phase 4: Advanced Features - Story 9-12 Observability Dashboard Widgets]
- [Source: docs/epics/epic-9-observability.md#Phase 4: Advanced Features (18 points)]
- [Source: docs/architecture.md#monitoring] - Architecture monitoring stack documentation
- [Source: docs/testing-guideline.md] - React Testing Library patterns for component tests
- [Source: frontend/src/components/admin/stat-card.tsx] - Existing stat card pattern to follow

## Dev Agent Record

### Context Reference

- [9-12-observability-dashboard-widgets.context.xml](./9-12-observability-dashboard-widgets.context.xml)

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

### File List
