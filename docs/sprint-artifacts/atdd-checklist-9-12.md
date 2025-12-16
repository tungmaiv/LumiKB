# ATDD Checklist - Epic 9, Story 12: Observability Dashboard Widgets

**Date:** 2025-12-15
**Author:** Tung Vu
**Primary Test Level:** Component/Unit (Frontend React)

---

## Story Summary

Create observability widgets for the admin dashboard showing LLM usage, processing pipeline health, chat activity, and system health metrics with sparkline trends and auto-refresh.

**As an** Admin user
**I want** observability widgets integrated into the admin dashboard
**So that** I can monitor LLM usage, processing pipeline health, and chat activity at a glance

---

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

---

## Failing Tests Created (RED Phase)

### Component Tests (15 tests)

**File:** `frontend/src/components/admin/widgets/__tests__/llm-usage-widget.test.tsx`

- [ ] **Test:** `renders_total_tokens_and_cost`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC1 - Displays total tokens and cost

- [ ] **Test:** `renders_model_breakdown_table`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC1 - Shows breakdown by model

- [ ] **Test:** `renders_sparkline_for_trend`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC7 - Sparkline chart displayed

- [ ] **Test:** `navigates_to_trace_view_on_click`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC8 - Click navigation works

**File:** `frontend/src/components/admin/widgets/__tests__/processing-widget.test.tsx`

- [ ] **Test:** `renders_documents_processed_count`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC2 - Documents processed displayed

- [ ] **Test:** `renders_avg_processing_time`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC2 - Average time displayed

- [ ] **Test:** `renders_error_rate_percentage`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC2 - Error rate displayed

- [ ] **Test:** `navigates_to_document_timeline_on_click`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC8 - Click navigation works

**File:** `frontend/src/components/admin/widgets/__tests__/chat-activity-widget.test.tsx`

- [ ] **Test:** `renders_message_count`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC3 - Message count displayed

- [ ] **Test:** `renders_active_sessions`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC3 - Active sessions displayed

- [ ] **Test:** `renders_avg_response_time`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC3 - Response time displayed

**File:** `frontend/src/components/admin/widgets/__tests__/system-health-widget.test.tsx`

- [ ] **Test:** `renders_trace_success_rate`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC4 - Success rate displayed

- [ ] **Test:** `renders_p95_latency`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC4 - P95 latency displayed

**File:** `frontend/src/components/admin/widgets/__tests__/time-period-selector.test.tsx`

- [ ] **Test:** `renders_all_period_options`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC5 - Hour/day/week/month options

- [ ] **Test:** `calls_onChange_when_period_selected`
  - **Status:** RED - Component does not exist
  - **Verifies:** AC5 - Selection callback works

### Hook Tests (6 tests)

**File:** `frontend/src/hooks/__tests__/useObservabilityStats.test.tsx`

- [ ] **Test:** `fetches_stats_for_selected_period`
  - **Status:** RED - Hook does not exist
  - **Verifies:** AC5 - Period parameter passed to API

- [ ] **Test:** `auto_refreshes_at_configured_interval`
  - **Status:** RED - Hook does not exist
  - **Verifies:** AC6 - Auto-refresh every 30s

- [ ] **Test:** `handles_parallel_widget_fetching`
  - **Status:** RED - Hook does not exist
  - **Verifies:** AC9 - Independent loading states

- [ ] **Test:** `handles_individual_widget_errors`
  - **Status:** RED - Hook does not exist
  - **Verifies:** AC9 - Graceful error handling

- [ ] **Test:** `provides_loading_state_per_widget`
  - **Status:** RED - Hook does not exist
  - **Verifies:** AC9 - Independent loading indicators

- [ ] **Test:** `manual_refresh_triggers_refetch`
  - **Status:** RED - Hook does not exist
  - **Verifies:** AC6 - Manual refresh button works

### E2E Tests (3 tests)

**File:** `frontend/e2e/tests/admin/observability-dashboard.spec.ts`

- [ ] **Test:** `displays_all_four_widgets`
  - **Status:** RED - Dashboard page not implemented
  - **Verifies:** AC1-4 - All widgets render

- [ ] **Test:** `time_period_selector_updates_all_widgets`
  - **Status:** RED - Dashboard page not implemented
  - **Verifies:** AC5 - Period selection updates data

- [ ] **Test:** `widget_click_navigates_to_detail_view`
  - **Status:** RED - Dashboard page not implemented
  - **Verifies:** AC8 - Navigation works

---

## Data Factories Created

### Widget Data Factories

**File:** `frontend/src/test/factories/observability-widget-factories.ts`

**Exports:**

- `createLLMUsageData(overrides?)` - Create LLM usage widget data
- `createProcessingPipelineData(overrides?)` - Create processing widget data
- `createChatActivityData(overrides?)` - Create chat activity widget data
- `createSystemHealthData(overrides?)` - Create system health widget data
- `createTrendData(count?)` - Create sparkline trend data points

**Example Usage:**

```typescript
import { createLLMUsageData, createTrendData } from '@/test/factories/observability-widget-factories';

// Default LLM usage data
const llmData = createLLMUsageData();

// Custom with overrides
const customData = createLLMUsageData({
  totalTokens: 100000,
  totalCostUsd: 5.50,
  byModel: [
    { model: 'gpt-4', tokens: 80000, cost: 4.00 },
    { model: 'gpt-3.5-turbo', tokens: 20000, cost: 1.50 },
  ],
});

// Generate trend data
const trend = createTrendData(24); // 24 data points
```

**Factory Implementations:**

```typescript
import { faker } from '@faker-js/faker';

export function createLLMUsageData(overrides?: Partial<LLMUsageData>): LLMUsageData {
  const promptTokens = faker.number.int({ min: 10000, max: 100000 });
  const completionTokens = faker.number.int({ min: 5000, max: 50000 });
  return {
    totalTokens: promptTokens + completionTokens,
    promptTokens,
    completionTokens,
    totalCostUsd: faker.number.float({ min: 0.5, max: 50, fractionDigits: 2 }),
    byModel: [
      { model: 'gpt-4', tokens: faker.number.int({ min: 1000, max: 50000 }), cost: faker.number.float({ min: 0.1, max: 25 }) },
      { model: 'gpt-3.5-turbo', tokens: faker.number.int({ min: 1000, max: 50000 }), cost: faker.number.float({ min: 0.1, max: 10 }) },
    ],
    trend: createTrendData(24),
    ...overrides,
  };
}

export function createProcessingPipelineData(overrides?: Partial<ProcessingPipelineData>): ProcessingPipelineData {
  return {
    documentsProcessed: faker.number.int({ min: 10, max: 500 }),
    avgProcessingTimeMs: faker.number.int({ min: 500, max: 30000 }),
    errorRate: faker.number.float({ min: 0, max: 15, fractionDigits: 1 }),
    trend: createTrendData(24),
    ...overrides,
  };
}

export function createChatActivityData(overrides?: Partial<ChatActivityData>): ChatActivityData {
  return {
    messageCount: faker.number.int({ min: 50, max: 1000 }),
    activeSessionCount: faker.number.int({ min: 5, max: 100 }),
    avgResponseTimeMs: faker.number.int({ min: 100, max: 5000 }),
    trend: createTrendData(24),
    ...overrides,
  };
}

export function createSystemHealthData(overrides?: Partial<SystemHealthData>): SystemHealthData {
  return {
    traceSuccessRate: faker.number.float({ min: 90, max: 100, fractionDigits: 1 }),
    p95LatencyMs: faker.number.int({ min: 100, max: 2000 }),
    errorCount: faker.number.int({ min: 0, max: 50 }),
    trend: createTrendData(24),
    ...overrides,
  };
}

export function createTrendData(count: number = 24): Array<{ timestamp: string; value: number }> {
  const now = new Date();
  return Array.from({ length: count }, (_, i) => ({
    timestamp: new Date(now.getTime() - (count - i) * 3600000).toISOString(),
    value: faker.number.int({ min: 10, max: 100 }),
  }));
}
```

---

## Fixtures Created

### Widget Test Fixtures

**File:** `frontend/src/test/fixtures/observability-widget-fixtures.tsx`

**Fixtures:**

- `renderWithProviders` - Render component with React Query provider
  - **Setup:** Creates QueryClient with test config
  - **Provides:** Wrapped component with providers
  - **Cleanup:** Clear query cache

- `mockObservabilityApi` - MSW handlers for observability API
  - **Setup:** Register MSW handlers
  - **Provides:** Mock API responses
  - **Cleanup:** Reset handlers

**Example Usage:**

```typescript
import { renderWithProviders, mockObservabilityApi } from '@/test/fixtures/observability-widget-fixtures';
import { LLMUsageWidget } from '@/components/admin/widgets/llm-usage-widget';

describe('LLMUsageWidget', () => {
  beforeEach(() => {
    mockObservabilityApi();
  });

  it('renders_total_tokens_and_cost', async () => {
    const { getByTestId } = renderWithProviders(
      <LLMUsageWidget period="day" />
    );

    await waitFor(() => {
      expect(getByTestId('llm-total-tokens')).toBeInTheDocument();
      expect(getByTestId('llm-total-cost')).toBeInTheDocument();
    });
  });
});
```

---

## Mock Requirements

### Observability Stats API Mock

**Endpoint:** `GET /api/v1/observability/stats?period={period}`

**Success Response:**

```json
{
  "llmUsage": {
    "totalTokens": 125000,
    "promptTokens": 100000,
    "completionTokens": 25000,
    "totalCostUsd": 5.75,
    "byModel": [
      { "model": "gpt-4", "tokens": 80000, "cost": 4.00 },
      { "model": "gpt-3.5-turbo", "tokens": 45000, "cost": 1.75 }
    ],
    "trend": [
      { "timestamp": "2025-12-15T00:00:00Z", "value": 5000 },
      { "timestamp": "2025-12-15T01:00:00Z", "value": 5500 }
    ]
  },
  "processingPipeline": {
    "documentsProcessed": 127,
    "avgProcessingTimeMs": 8500,
    "errorRate": 2.3,
    "trend": [...]
  },
  "chatActivity": {
    "messageCount": 423,
    "activeSessionCount": 45,
    "avgResponseTimeMs": 850,
    "trend": [...]
  },
  "systemHealth": {
    "traceSuccessRate": 98.5,
    "p95LatencyMs": 450,
    "errorCount": 12,
    "trend": [...]
  }
}
```

**Error Response:**

```json
{
  "detail": "Failed to fetch observability stats"
}
```

**MSW Handler:**

```typescript
import { rest } from 'msw';
import { createLLMUsageData, createProcessingPipelineData, createChatActivityData, createSystemHealthData } from '../factories/observability-widget-factories';

export const observabilityHandlers = [
  rest.get('/api/v1/observability/stats', (req, res, ctx) => {
    const period = req.url.searchParams.get('period') || 'day';
    return res(
      ctx.json({
        llmUsage: createLLMUsageData(),
        processingPipeline: createProcessingPipelineData(),
        chatActivity: createChatActivityData(),
        systemHealth: createSystemHealthData(),
      })
    );
  }),
];
```

---

## Required data-testid Attributes

### LLM Usage Widget

- `llm-usage-widget` - Widget container
- `llm-total-tokens` - Total tokens display
- `llm-total-cost` - Total cost display
- `llm-model-breakdown` - Model breakdown table
- `llm-sparkline` - Trend sparkline chart

### Processing Pipeline Widget

- `processing-widget` - Widget container
- `processing-docs-count` - Documents processed count
- `processing-avg-time` - Average processing time
- `processing-error-rate` - Error rate percentage
- `processing-sparkline` - Trend sparkline chart

### Chat Activity Widget

- `chat-activity-widget` - Widget container
- `chat-message-count` - Message count display
- `chat-active-sessions` - Active sessions count
- `chat-avg-response-time` - Average response time
- `chat-sparkline` - Trend sparkline chart

### System Health Widget

- `system-health-widget` - Widget container
- `health-success-rate` - Trace success rate
- `health-p95-latency` - P95 latency display
- `health-error-count` - Error count display
- `health-sparkline` - Trend sparkline chart

### Time Period Selector

- `time-period-selector` - Selector container
- `period-option-hour` - Hour option
- `period-option-day` - Day option
- `period-option-week` - Week option
- `period-option-month` - Month option

### Dashboard

- `observability-dashboard` - Dashboard container
- `refresh-button` - Manual refresh button
- `last-updated` - Last updated timestamp

**Implementation Example:**

```tsx
<div data-testid="llm-usage-widget" className="widget-card" onClick={handleNavigate}>
  <h3>LLM Usage</h3>
  <div data-testid="llm-total-tokens">{formatNumber(data.totalTokens)} tokens</div>
  <div data-testid="llm-total-cost">${data.totalCostUsd.toFixed(2)}</div>
  <div data-testid="llm-sparkline">
    <Sparkline data={data.trend} />
  </div>
</div>
```

---

## Implementation Checklist

### Test: `renders_total_tokens_and_cost`

**File:** `frontend/src/components/admin/widgets/__tests__/llm-usage-widget.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/widgets/llm-usage-widget.tsx`
- [ ] Define `LLMUsageWidget` component accepting `data` prop
- [ ] Display `totalTokens` with formatting
- [ ] Display `totalCostUsd` with currency formatting
- [ ] Add `data-testid="llm-total-tokens"` attribute
- [ ] Add `data-testid="llm-total-cost"` attribute
- [ ] Run test: `npm run test:run frontend/src/components/admin/widgets/__tests__/llm-usage-widget.test.tsx`
- [ ] Test passes (green phase)

---

### Test: `renders_sparkline_for_trend`

**File:** `frontend/src/components/admin/widgets/__tests__/llm-usage-widget.test.tsx`

**Tasks to make this test pass:**

- [ ] Install sparkline library: `npm install react-sparklines`
- [ ] Create `frontend/src/components/admin/widgets/sparkline.tsx` wrapper
- [ ] Import and use `Sparkline` component in widget
- [ ] Pass `trend` data to sparkline
- [ ] Add `data-testid="llm-sparkline"` attribute
- [ ] Run test: `npm run test:run -- --grep "renders_sparkline"`
- [ ] Test passes (green phase)

---

### Test: `auto_refreshes_at_configured_interval`

**File:** `frontend/src/hooks/__tests__/useObservabilityStats.test.tsx`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/hooks/useObservabilityStats.ts`
- [ ] Use React Query with `refetchInterval: 30000`
- [ ] Accept `period` parameter
- [ ] Accept `refreshInterval` parameter (default 30000)
- [ ] Return data, loading, error states
- [ ] Run test: `npm run test:run frontend/src/hooks/__tests__/useObservabilityStats.test.tsx`
- [ ] Test passes (green phase)

---

### Test: `handles_parallel_widget_fetching`

**File:** `frontend/src/hooks/__tests__/useObservabilityStats.test.tsx`

**Tasks to make this test pass:**

- [ ] Use separate query keys per widget type
- [ ] Implement individual hooks or use useQueries
- [ ] Ensure independent loading states
- [ ] Handle individual errors gracefully
- [ ] Run test: `npm run test:run -- --grep "parallel"`
- [ ] Test passes (green phase)

---

### Test: `time_period_selector_updates_all_widgets`

**File:** `frontend/e2e/tests/admin/observability-dashboard.spec.ts`

**Tasks to make this test pass:**

- [ ] Create `frontend/src/components/admin/widgets/time-period-selector.tsx`
- [ ] Implement period options (hour/day/week/month)
- [ ] Lift state to dashboard level
- [ ] Pass period to all widget hooks
- [ ] Run test: `npx playwright test observability-dashboard.spec.ts`
- [ ] Test passes (green phase)

---

## Running Tests

```bash
# Run all component tests for widgets
npm run test:run frontend/src/components/admin/widgets/__tests__/*.test.tsx

# Run hook tests
npm run test:run frontend/src/hooks/__tests__/useObservabilityStats.test.tsx

# Run with coverage
npm run test:run -- --coverage frontend/src/components/admin/widgets

# Run E2E tests
npx playwright test frontend/e2e/tests/admin/observability-dashboard.spec.ts

# Run specific test
npm run test:run -- --grep "renders_total_tokens"

# Run in watch mode
npm run test -- --watch frontend/src/components/admin/widgets
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete)

**TEA Agent Responsibilities:**

-  All tests written and failing
-  Fixtures and factories created
-  Mock requirements documented
-  data-testid requirements listed
-  Implementation checklist created

---

### GREEN Phase (DEV Team - Next Steps)

**Recommended Implementation Order:**

1. Create base widget card component
2. Implement LLMUsageWidget (AC1)
3. Implement useObservabilityStats hook
4. Implement ProcessingWidget (AC2)
5. Implement ChatActivityWidget (AC3)
6. Implement SystemHealthWidget (AC4)
7. Implement TimePeriodSelector (AC5)
8. Add auto-refresh logic (AC6)
9. Add sparkline component (AC7)
10. Add navigation handlers (AC8)
11. Verify parallel fetching (AC9)

---

## Knowledge Base References Applied

- **component-tdd.md** - React component testing with RTL
- **data-factories.md** - Factory patterns with faker
- **network-first.md** - MSW for API mocking
- **fixture-architecture.md** - Test setup/teardown

---

## Notes

- Use existing `Card` component from Shadcn/ui
- Follow existing admin component patterns in `frontend/src/components/admin/`
- Sparkline library options: `react-sparklines`, `recharts`, or `visx`
- Consider using `react-query` for data fetching and caching
- Mobile responsive: 1-column layout on small screens

---

**Generated by BMad TEA Agent** - 2025-12-15
