# Story 5.1: Admin Dashboard Overview

Status: ready-for-dev

## Story

As an **administrator**,
I want **to see system-wide statistics at a glance**,
so that **I can monitor system health and usage**.

## Acceptance Criteria

**AC1: Dashboard Statistics Display**
**Given** I am logged in as an admin
**When** I navigate to /admin
**Then** I see a dashboard with:
- Total users (active/inactive counts)
- Total Knowledge Bases
- Total documents (by processing status: ready, pending, processing, failed)
- Storage usage (total bytes with human-readable format)
- Search queries (last 24h, 7d, 30d)
- Generation requests (last 24h, 7d, 30d)

**AC2: Trend Visualization**
**Given** I am viewing the admin dashboard
**When** the statistics load
**Then** key metrics have sparkline charts showing trends over the last 30 days
**And** charts visually indicate growth (green), decline (red), or stability (blue)

**AC3: Drill-Down Navigation**
**Given** I am viewing the admin dashboard
**When** I click any metric card
**Then** I navigate to a detailed view for that metric
**And** the detailed view provides filtering and sorting capabilities

**AC4: Performance and Caching**
**Given** the dashboard aggregates data from multiple sources
**When** I load the admin dashboard
**Then** the page loads within 2 seconds
**And** statistics are cached for 5 minutes to reduce database load
**And** a "Last updated" timestamp is displayed

**AC5: Authorization Enforcement**
**Given** I am logged in as a non-admin user
**When** I attempt to access /admin
**Then** I receive a 403 Forbidden response
**And** I am redirected to the dashboard with an error message

**AC6: Real-Time Updates (Optional)**
**Given** I am viewing the admin dashboard
**When** I click "Refresh Statistics"
**Then** the dashboard re-fetches current data
**And** the "Last updated" timestamp updates
**And** any changes are highlighted briefly (fade-in animation)

## Tasks / Subtasks

### Task 1: Create AdminStatsService (Backend) - AC1, AC4
**Objective:** Implement service to aggregate system-wide statistics

**Subtasks:**
- [ ] 1.1 Create `backend/app/services/admin_stats_service.py`
- [ ] 1.2 Implement `get_dashboard_stats()` method with aggregation queries:
  - [ ] 1.2.1 Query users table: total count, active (last_active > NOW() - 30 days), inactive
  - [ ] 1.2.2 Query knowledge_bases table: total count, group by status
  - [ ] 1.2.3 Query documents table: total count, group by processing_status
  - [ ] 1.2.4 Query audit.events for search count (action='search.query', last 24h/7d/30d)
  - [ ] 1.2.5 Query audit.events for generation count (action='generation.request', last 24h/7d/30d)
  - [ ] 1.2.6 Calculate storage usage: SUM(file_size) from documents table
- [ ] 1.3 Implement `get_trend_data()` method for 30-day sparklines (search and generation counts per day)
- [ ] 1.4 Add Redis caching decorator (5-minute TTL) to reduce database load
- [ ] 1.5 Add error handling for missing audit data (graceful fallback to 0 counts)

### Task 2: Create Admin Stats API Endpoint (Backend) - AC1, AC4, AC5
**Objective:** Expose admin statistics via REST API

**Subtasks:**
- [ ] 2.1 Create `GET /api/v1/admin/stats` endpoint in `backend/app/api/v1/admin.py`
- [ ] 2.2 Add admin role authorization check (require `is_superuser=True`)
- [ ] 2.3 Call AdminStatsService.get_dashboard_stats()
- [ ] 2.4 Return JSON response matching AdminStats schema
- [ ] 2.5 Add OpenAPI documentation with example response
- [ ] 2.6 Handle 403 Forbidden for non-admin users

### Task 3: Create Pydantic Schema for Admin Stats - AC1, AC2
**Objective:** Define type-safe response schema

**Subtasks:**
- [ ] 3.1 Create `backend/app/schemas/admin.py`
- [ ] 3.2 Define `AdminStats` schema with nested models:
  - [ ] 3.2.1 UserStats (total, active, inactive)
  - [ ] 3.2.2 KnowledgeBaseStats (total, byStatus)
  - [ ] 3.2.3 DocumentStats (total, byStatus)
  - [ ] 3.2.4 StorageStats (totalBytes, avgDocSizeBytes)
  - [ ] 3.2.5 ActivityStats (searches, generations with 24h/7d/30d breakdowns)
  - [ ] 3.2.6 TrendData (searches, generations as arrays of 30 daily counts)
- [ ] 3.3 Add validation and example values for OpenAPI docs

### Task 4: Create Admin Dashboard Page (Frontend) - AC1, AC2, AC3
**Objective:** Build admin dashboard UI with statistics display

**Subtasks:**
- [ ] 4.1 Create `frontend/src/app/(protected)/admin/page.tsx`
- [ ] 4.2 Create `frontend/src/components/admin/stats-overview.tsx` component
- [ ] 4.3 Create `frontend/src/components/admin/stat-card.tsx` reusable card component
- [ ] 4.4 Implement statistics layout using shadcn/ui Card components (4-column grid on desktop)
- [ ] 4.5 Add sparkline charts using a lightweight chart library (e.g., Recharts mini charts)
- [ ] 4.6 Implement click handlers for drill-down navigation (AC3)
- [ ] 4.7 Display "Last updated" timestamp with human-readable format (e.g., "Updated 2 minutes ago")
- [ ] 4.8 Add loading skeleton while fetching data

### Task 5: Create useAdminStats Hook (Frontend) - AC4, AC6
**Objective:** Manage admin statistics state and API calls

**Subtasks:**
- [ ] 5.1 Create `frontend/src/hooks/useAdminStats.ts`
- [ ] 5.2 Implement data fetching with `fetch('/api/v1/admin/stats')`
- [ ] 5.3 Add loading, error, and data states
- [ ] 5.4 Implement manual refresh function for AC6
- [ ] 5.5 Add error handling with user-friendly messages
- [ ] 5.6 Cache response data in component state (respects backend 5-min cache)

### Task 6: Implement Authorization and Navigation - AC3, AC5
**Objective:** Enforce admin access control and enable drill-down

**Subtasks:**
- [ ] 6.1 Add admin route protection middleware in Next.js
- [ ] 6.2 Create `/admin/audit`, `/admin/queue`, `/admin/config` placeholder pages (link from stat cards)
- [ ] 6.3 Implement 403 redirect to dashboard with error toast
- [ ] 6.4 Update main navigation to show "Admin" link only for admin users
- [ ] 6.5 Test unauthorized access scenarios

### Task 7: Write Unit Tests (Backend) - AC1, AC4, AC5
**Objective:** Ensure service and API correctness

**Subtasks:**
- [ ] 7.1 Create `backend/tests/unit/test_admin_stats_service.py`
- [ ] 7.2 Test `get_dashboard_stats()` with mocked database queries
- [ ] 7.3 Test `get_trend_data()` returns 30-day arrays
- [ ] 7.4 Test caching behavior (verify cache hit/miss)
- [ ] 7.5 Test graceful handling of empty audit data
- [ ] 7.6 Create `backend/tests/integration/test_admin_api.py`
- [ ] 7.7 Test GET /api/v1/admin/stats with admin user (200 OK)
- [ ] 7.8 Test GET /api/v1/admin/stats with non-admin user (403 Forbidden)

### Task 8: Write Frontend Tests - AC1, AC2, AC6
**Objective:** Validate UI behavior and interactions

**Subtasks:**
- [ ] 8.1 Create `frontend/src/hooks/__tests__/useAdminStats.test.ts`
- [ ] 8.2 Test successful data fetch
- [ ] 8.3 Test error handling
- [ ] 8.4 Test manual refresh function
- [ ] 8.5 Create `frontend/src/components/admin/__tests__/stats-overview.test.tsx`
- [ ] 8.6 Test statistics display with mock data
- [ ] 8.7 Test loading state renders skeleton
- [ ] 8.8 Test error state displays message

## Dev Notes

### Architecture Patterns

**Backend Service Layer:**
- Follows existing service pattern from Epic 1-4 (single-responsibility services)
- AdminStatsService aggregates data from multiple sources (users, KBs, docs, audit)
- Uses dependency injection pattern for database session
- Implements caching to avoid expensive aggregation queries on every request

**API Design:**
- RESTful endpoint: GET /api/v1/admin/stats
- Returns comprehensive statistics object (no pagination needed for dashboard summary)
- Follows existing admin API pattern from Story 1.6 (admin.py module)
- Authorization via existing FastAPI-Users admin check (`current_active_superuser` dependency)

**Frontend Components:**
- Page route: `/app/(protected)/admin/page.tsx`
- Reusable StatCard component for consistent metric display
- Custom hook pattern (useAdminStats) for state management
- Follows shadcn/ui component patterns from Epic 1-4

**Performance Considerations:**
- Backend caching (5 minutes) prevents database overload
- Frontend displays cached "Last updated" timestamp for transparency
- Sparkline charts use lightweight Recharts library (already used in Epic 3 for relevance scores)
- Database queries optimized with COUNT aggregations (no full table scans)

### Project Structure Notes

**Files to Create:**

Backend:
- `backend/app/services/admin_stats_service.py` - Core statistics aggregation service
- `backend/app/schemas/admin.py` - Pydantic response schemas
- `backend/tests/unit/test_admin_stats_service.py` - Unit tests for service
- `backend/tests/integration/test_admin_stats_api.py` - Integration tests for API endpoint

Frontend:
- `frontend/src/app/(protected)/admin/page.tsx` - Admin dashboard page route
- `frontend/src/components/admin/stats-overview.tsx` - Main statistics display component
- `frontend/src/components/admin/stat-card.tsx` - Reusable metric card component
- `frontend/src/hooks/useAdminStats.ts` - Statistics state management hook
- `frontend/src/hooks/__tests__/useAdminStats.test.ts` - Hook unit tests
- `frontend/src/components/admin/__tests__/stats-overview.test.tsx` - Component tests

**Files to Modify:**
- `backend/app/api/v1/admin.py` - Add GET /api/v1/admin/stats endpoint (extends existing admin routes from Story 1.6)

**Database Queries:**
- All queries use existing tables (users, knowledge_bases, documents, audit.events)
- No schema migrations required
- Queries should be SELECT COUNT aggregations for performance

### Testing Standards

**Backend Testing:**
- Unit tests: Mock database session and test service logic
- Integration tests: Use test database and verify full API flow
- Authorization tests: Verify admin-only access enforcement
- Performance tests: Ensure queries complete within 2-second target

**Frontend Testing:**
- Hook tests: Test data fetching, loading states, error handling
- Component tests: Test rendering with mock data, skeleton loading, drill-down clicks
- Accessibility tests: Verify ARIA labels for screen readers
- Visual regression: Snapshot test for dashboard layout

### Learnings from Previous Story

**From Story 5-0 (Epic Integration Completion - Status: done):**

**New Services Created:**
- None (Story 5-0 was UI integration only)

**Architectural Changes:**
- Chat page route pattern: `/app/(protected)/chat/page.tsx` with inline component implementation
- Dashboard navigation cards pattern: Quick Access section with conditional rendering based on `activeKb` state
- Environment-based API URL configuration: `NEXT_PUBLIC_API_URL` for deployment flexibility

**Files Created:**
- `frontend/src/app/(protected)/chat/page.tsx` (NEW - 237 lines, SSE streaming chat)
- Pattern to follow: Page-level component with hooks, no separate container component

**Files Modified:**
- `frontend/src/app/(protected)/dashboard/page.tsx` (Added Quick Access cards lines 36-63)
- Pattern: Conditional rendering based on state (`{activeKb && <QuickAccessCards />}`)

**Technical Patterns to Reuse:**
1. **API URL Configuration:** Use `const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';`
2. **Loading States:** Use `isLoading` state with shadcn/ui Skeleton components
3. **Error Handling:** Display user-friendly error messages with toast notifications
4. **Authorization Checks:** Backend uses `current_active_superuser` dependency (already established in Story 1.6)
5. **Responsive Grid:** Use `grid gap-4 md:grid-cols-2 lg:grid-cols-4` for statistics cards

**Issues to Avoid:**
1. **Unused Refs:** Story 5-0 had unused `eventSourceRef` - remove any unused code immediately
2. **Generic Error Messages:** Provide specific error messages for different failure scenarios (401, 403, 500)
3. **Navigation Card Visibility:** Ensure admin navigation shows when appropriate (not hidden in edge cases)

**Quality Standards from Story 5-0:**
- Code quality score: 95/100
- Clean SSE streaming implementation
- Proper state management with hooks
- Environment-based configuration
- Citation-first architecture preserved
- KISS/DRY/YAGNI principles followed

**Pending Review Items from Story 5-0:**
- None (all review items resolved)

**Technical Debt from Story 5-0:**
- AC4 (smoke tests) deferred to Story 5.16 (Docker E2E Infrastructure)
- This story should also defer E2E smoke tests to 5.16 and focus on unit/integration tests

### References

**Architecture References:**
- [Source: ../architecture.md, lines 1036-1062] - Admin API patterns
- [Source: ../architecture.md, lines 1088-1159] - Security Architecture
- [Source: ./tech-spec-epic-5.md, lines 113-141] - AdminStats schema
- [Source: ./tech-spec-epic-5.md, lines 194-226] - API design
- [Source: ../epics.md, lines 1803-1829] - Acceptance criteria and prerequisites (Story 5.1)

**Related Components:**
- Story 1.6: Admin User Management Backend (establishes admin API pattern)
- Story 1.7: Audit Logging Infrastructure (audit.events table for activity metrics)
- Story 5-0: Epic Integration Completion (dashboard navigation card pattern)

**Existing Services to Extend:**
- `backend/app/api/v1/admin.py` - Add new `/stats` endpoint
- `backend/app/services/audit_service.py` - Reference for audit query patterns

**Frontend Patterns:**
- `frontend/src/app/(protected)/dashboard/page.tsx` - Dashboard layout pattern
- `frontend/src/components/ui/card.tsx` - shadcn/ui Card component (already used)
- `frontend/src/hooks/useActiveKb.ts` - Custom hook pattern to follow

## Dev Agent Record

### Context Reference

**Story Context XML:** [5-1-admin-dashboard-overview.context.xml](./5-1-admin-dashboard-overview.context.xml)

**Validation Report:** [validation-report-context-5-1-20251202.md](./validation-report-context-5-1-20251202.md)

**Validation Status:** ✅ APPROVED (10/10 checklist items passed - 100%)

**Context Summary:**
- Strategic alignment with FR47 (Admin dashboard with system-wide statistics)
- 5 Acceptance Criteria with test strategies
- API contract: GET /api/v1/admin/stats → AdminStats schema (22 fields)
- 25 implementation tasks across 5 phases
- 11 existing code artifacts referenced
- 4 code patterns with full implementations (~163 lines)
- 19 tests defined (unit/integration/E2E)
- 5 edge cases with mitigation strategies
- Quality gates: tests, performance (<500ms cache hit), security (403 for non-admin), acceptance
- Observability: 5 Prometheus metrics, 4 log events, 3 alerts

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
