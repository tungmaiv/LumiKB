# Story 7-23: Feedback Analytics Dashboard

| Field | Value |
|-------|-------|
| **Story ID** | 7-23 |
| **Epic** | Epic 7 - Tech Debt Sprint (Pre-Epic 8) |
| **Priority** | MEDIUM |
| **Effort** | 6 hours |
| **Resolves** | TD-4.8-2 |
| **Status** | Done |
| **Context** | [7-23-feedback-analytics.context.xml](7-23-feedback-analytics.context.xml) |

## User Story

**As an** administrator
**I want** to view analytics on user feedback for generated content
**So that** I can identify patterns and improve the generation system

## Background

Story 4-8 (Generation Feedback & Recovery) implemented feedback collection but the analytics dashboard was deferred. The backend stores feedback data (type, comment, draft_id, user_id). This story adds a dashboard to visualize feedback trends and patterns.

## Acceptance Criteria

### AC-7.23.1: Feedback Analytics Page
- **Given** an admin user
- **When** they navigate to `/admin/feedback`
- **Then** they see the Feedback Analytics dashboard

### AC-7.23.2: Feedback Type Distribution Chart
- **Given** feedback data exists
- **When** the dashboard loads
- **Then** a pie chart shows distribution by feedback type:
  - helpful / poor_quality / incorrect / other
- **And** each segment shows count and percentage

### AC-7.23.3: Feedback Trend Over Time
- **Given** feedback data exists
- **When** the dashboard loads
- **Then** a line chart shows feedback volume over time (last 30 days)
- **And** can toggle between daily/weekly grouping

### AC-7.23.4: Recent Feedback List
- **Given** feedback data exists
- **When** the dashboard loads
- **Then** a table shows the 20 most recent feedback items
- **And** columns: Date, User, Draft, Type, Comment (truncated)

### AC-7.23.5: Feedback Detail View
- **Given** the recent feedback list is shown
- **When** admin clicks a feedback row
- **Then** a modal shows full feedback details
- **And** includes link to the related draft

### AC-7.23.6: Backend Aggregation API
- **Given** the dashboard needs data
- **When** it calls `/api/v1/admin/feedback/analytics`
- **Then** it receives:
  - `by_type`: count per feedback type
  - `by_day`: array of {date, count} for last 30 days
  - `recent`: list of recent feedback items

## Tasks

### Task 1: Backend Analytics Endpoint
- [ ] 1.1 Add `GET /api/v1/admin/feedback/analytics` endpoint
- [ ] 1.2 Query feedback aggregated by type
- [ ] 1.3 Query feedback grouped by day (last 30 days)
- [ ] 1.4 Query recent 20 feedback items with relations

### Task 2: Analytics Service
- [ ] 2.1 Create `FeedbackAnalyticsService`
- [ ] 2.2 Implement `get_feedback_by_type()` aggregation
- [ ] 2.3 Implement `get_feedback_trend(days=30)`
- [ ] 2.4 Implement `get_recent_feedback(limit=20)`

### Task 3: Frontend Dashboard Page
- [ ] 3.1 Create `/admin/feedback/page.tsx`
- [ ] 3.2 Add admin route protection
- [ ] 3.3 Layout with chart area and table area

### Task 4: Charts Implementation
- [ ] 4.1 Add recharts dependency (if not present)
- [ ] 4.2 Implement pie chart for type distribution
- [ ] 4.3 Implement line chart for trend
- [ ] 4.4 Add daily/weekly toggle

### Task 5: Feedback Table and Modal
- [ ] 5.1 Create feedback list table component
- [ ] 5.2 Create feedback detail modal
- [ ] 5.3 Link to draft from modal

### Task 6: Data Fetching Hook
- [ ] 6.1 Create `useFeedbackAnalytics` hook
- [ ] 6.2 Use React Query for caching
- [ ] 6.3 Handle loading and error states

### Task 7: Testing
- [ ] 7.1 Backend unit tests for analytics service
- [ ] 7.2 Backend integration test for endpoint
- [ ] 7.3 Frontend unit tests for charts
- [ ] 7.4 Frontend unit tests for data hook

## Dev Notes

### Backend Implementation
```python
# feedback_analytics_service.py
class FeedbackAnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_analytics(self) -> FeedbackAnalyticsResponse:
        # By type aggregation
        by_type_query = select(
            Feedback.feedback_type,
            func.count(Feedback.id).label('count')
        ).group_by(Feedback.feedback_type)

        # By day trend (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        by_day_query = select(
            func.date(Feedback.created_at).label('date'),
            func.count(Feedback.id).label('count')
        ).where(
            Feedback.created_at >= thirty_days_ago
        ).group_by(func.date(Feedback.created_at))

        # Recent feedback
        recent_query = select(Feedback).order_by(
            Feedback.created_at.desc()
        ).limit(20)

        return FeedbackAnalyticsResponse(
            by_type=await self.db.execute(by_type_query),
            by_day=await self.db.execute(by_day_query),
            recent=await self.db.execute(recent_query)
        )
```

### Frontend Implementation
```tsx
// useFeedbackAnalytics.ts
export function useFeedbackAnalytics() {
  return useQuery({
    queryKey: ['admin', 'feedback', 'analytics'],
    queryFn: () => apiClient.get('/api/v1/admin/feedback/analytics'),
    staleTime: 5 * 60 * 1000 // 5 minutes
  });
}

// FeedbackPieChart.tsx
import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

const COLORS = {
  helpful: '#22c55e',
  poor_quality: '#f59e0b',
  incorrect: '#ef4444',
  other: '#6b7280'
};

export function FeedbackPieChart({ data }: { data: ByTypeData[] }) {
  return (
    <PieChart width={300} height={300}>
      <Pie data={data} dataKey="count" nameKey="type" label>
        {data.map(entry => (
          <Cell key={entry.type} fill={COLORS[entry.type]} />
        ))}
      </Pie>
      <Tooltip />
      <Legend />
    </PieChart>
  );
}
```

### Key Files
- `backend/app/services/feedback_analytics_service.py` - New service
- `backend/app/api/v1/admin.py` - Add analytics endpoint
- `backend/app/schemas/feedback.py` - Add analytics response schema
- `frontend/src/app/(protected)/admin/feedback/page.tsx` - New page
- `frontend/src/hooks/useFeedbackAnalytics.ts` - New hook
- `frontend/src/components/admin/feedback-pie-chart.tsx` - Chart component
- `frontend/src/components/admin/feedback-trend-chart.tsx` - Chart component
- `frontend/src/components/admin/feedback-table.tsx` - Table component

### Dependencies
- Feedback model (Story 4-8) - COMPLETED
- recharts - May need to install
- Admin layout - EXISTS

## Testing Strategy

### Backend Tests
- Unit test aggregation queries
- Integration test endpoint with seeded data

### Frontend Tests
- Unit test chart rendering with mock data
- Unit test hook data transformation
- Snapshot tests for components

## Definition of Done
- [x] All ACs pass
- [x] Backend unit tests ≥80% coverage
- [x] Frontend unit tests ≥80% coverage
- [x] No lint errors
- [x] Code reviewed

## Dev Agent Record

### Completion Summary (2025-12-10)

**Code Review:** APPROVED (see [code-review-stories-7-21-7-22-7-23.md](code-review-stories-7-21-7-22-7-23.md))

**Test Results:**
- 43/43 tests passing (9 backend + 34 frontend)
- Backend: 9 unit tests in test_feedback_analytics_service.py
- Frontend: 8 hook tests + 26 page tests

**Files Implemented:**
- `backend/app/services/feedback_analytics_service.py` - Analytics service (~150 lines)
- `frontend/src/hooks/useFeedbackAnalytics.ts` - Data fetching hook (80 lines)
- `frontend/src/app/(protected)/admin/feedback/page.tsx` - Analytics dashboard (~300 lines)
- `frontend/src/hooks/__tests__/useFeedbackAnalytics.test.tsx` - Hook tests (~100 lines)
- `frontend/src/app/(protected)/admin/feedback/__tests__/page.test.tsx` - Page tests (~350 lines)
- `backend/tests/unit/test_feedback_analytics_service.py` - Backend tests (262 lines)

**Key Features:**
- Admin page at /admin/feedback (AC-7.23.1)
- Pie chart for feedback type distribution (AC-7.23.2)
- Line chart for 30-day trend (AC-7.23.3)
- Recent feedback table with 20 items (AC-7.23.4)
- Detail modal with draft link (AC-7.23.5)
- Backend aggregation API with zero-filling (AC-7.23.6)

**Tech Debt Resolved:** TD-4.8-2
