# Epic Technical Specification: Administration & Polish

Date: 2025-12-05
Author: Tung Vu
Epic ID: epic-5
Status: Draft (Updated)

---

## Overview

Epic 5 completes the LumiKB MVP by delivering critical administration capabilities, system polish, and resolving a major integration gap discovered during Epic 4 retrospective. This epic has three distinct focus areas:

1. **Integration Completion (Story 5.0)**: Make Epic 3 & 4 features accessible to users through UI navigation (CRITICAL)
2. **Administration Dashboard**: Provide administrators with system management, audit logging, and monitoring capabilities (FR47-52, FR58)
3. **User & Group Management**: Admin UI for managing users, groups, and KB permissions (Stories 5.18-5.20)
4. **Technical Debt & Infrastructure**: Docker E2E testing infrastructure, ATDD test hardening, and polish items
5. **User Experience Polish**: Theme system, onboarding wizard, smart KB suggestions (Stories 5.7-5.9, 5.21)

The epic addresses a critical discovery: while Epic 3 (Semantic Search) and Epic 4 (Chat & Generation) are fully implemented with high code quality and comprehensive test coverage, users cannot access these features through normal UI navigation. Story 5.0 resolves this immediately, followed by Docker-based E2E testing infrastructure (Story 5.16) to prevent similar issues in the future.

## Objectives and Scope

### In Scope

**Integration & Accessibility (CRITICAL)**
- Create `/chat` page route and wire chat components into UI
- Add dashboard navigation cards for Search and Chat features
- Remove "Coming in Epic 3/4" placeholders
- Verify all backend services (FastAPI, Celery, Qdrant, Redis, MinIO, LiteLLM) are healthy
- Smoke test complete user journeys: Document Upload → Search, Chat Conversation, Document Generation

**Administration Features (FR47-52, FR58)**
- Admin dashboard with system-wide statistics (users, KBs, documents, search/generation metrics)
- Audit log viewer with filtering and pagination (FR48)
- Audit log export for compliance reporting (FR49, FR58)
- Processing queue status monitoring (FR51)
- System configuration management (FR52)
- KB statistics admin view (FR50)

**User Experience Polish (FR8a-c, FR12b-d)**
- Onboarding wizard for first-time users (FR8a-c)
- Smart KB suggestions based on usage patterns (FR12b)
- Recent KBs list and UX refinements (FR12c-d)
- Theme system with multiple color themes (Story 5.21)

**User & Group Management (FR5, FR6, FR7)**
- User management UI for admin CRUD operations (Story 5.18)
- Group management with membership administration (Story 5.19)
- Role and KB permission management UI for users/groups (Story 5.20)

**Technical Debt & Infrastructure**
- Docker E2E testing infrastructure with all services (HIGH)
- ATDD test transition to GREEN (78 tests from Epic 3 & 4)
- Command palette test coverage improvement (Story 3.7 debt)
- Epic 3 search hardening (unit tests, accessibility)
- Celery Beat filesystem fix
- Search audit logging (moved from Epic 3 Story 3.11)

### Out of Scope

- Multi-language support (deferred to future)
- Advanced workflow engine features (Vision - MVP 3)
- Graph RAG capabilities (MVP 2)
- Cloud sync integration (MVP 2)
- Performance optimization beyond current baselines (future)

## System Architecture Alignment

Epic 5 builds on the established architecture with no new infrastructure components. Key architectural alignments:

**Backend Services (FastAPI)**
- Extends existing AuditService (Story 1.7) for admin audit viewer and export
- Extends existing admin API routes (`/api/v1/admin`) for dashboard, queue status, config
- Reuses ConversationService, GenerationService, SearchService patterns from Epic 3 & 4

**Frontend (Next.js 15 App Router)**
- Creates new `/app/(protected)/chat/page.tsx` route (Story 5.0)
- Extends dashboard page with navigation cards (Story 5.0)
- Creates new `/app/(protected)/admin` pages for admin features (Stories 5.1-5.6)
- Integrates onboarding wizard using existing shadcn/ui components (Story 5.7)

**Data Layer**
- PostgreSQL: Extends audit.events table usage for admin viewer/export (no schema changes)
- Redis: Celery task monitoring for queue status (Story 5.4)
- Existing services: No new datastores required

**Testing Infrastructure (NEW)**
- Docker Compose E2E environment with all services (Story 5.16)
- Playwright test execution against containerized stack
- Database seeding for E2E test fixtures
- GitHub Actions CI integration for automated E2E testing

**Citation-First Architecture Preserved**
- All admin features maintain citation traceability for generated content
- Audit logging captures source documents for compliance
- No deviation from established patterns

## Detailed Design

### Services and Modules

| Service/Module | Responsibilities | Inputs | Outputs | Owner |
|----------------|------------------|--------|---------|-------|
| **AdminStatsService** | Aggregate system-wide statistics for dashboard | User count, KB count, document count, search/generation metrics | Dashboard statistics JSON | Story 5.1 |
| **AuditService (Extended)** | Query, filter, and export audit logs | Date range, user filter, action filter, resource filter | Paginated audit events, CSV/JSON export | Stories 5.2, 5.3 |
| **QueueMonitorService** | Monitor Celery task queues and workers | Queue names, worker IDs | Queue depth, task states, worker health | Story 5.4 |
| **ConfigService** | Manage system configuration | Config key-value pairs | System settings, validation results | Story 5.5 |
| **OnboardingService** | Track onboarding wizard progress | User ID, step completion | Wizard state, next step | Story 5.7 |
| **RecommendationService** | Suggest KBs based on usage patterns | User ID, search history, KB access patterns | Recommended KB list with scores | Story 5.8 |
| **ChatPageComponent** | Wire chat UI into accessible route | User input, conversation state | Chat interface with streaming responses | Story 5.0 |
| **DashboardNavComponent** | Navigation cards for Search/Chat | Feature availability flags | Navigation cards with routes | Story 5.0 |
| **DockerE2EInfrastructure** | Full-stack E2E testing environment | docker-compose.e2e.yml, test fixtures | Containerized test environment | Story 5.16 |
| **UserManagementPage** | Admin UI for user CRUD operations | User list, create/edit forms | Paginated user table, modals | Story 5.18 |
| **useUsers** | React Query hook for user data | API calls, pagination state | User list, mutations | Story 5.18 |
| **GroupService** | Group CRUD operations, membership management | Group data, user assignments | Group entities, member lists | Story 5.19 |
| **GroupManagementPage** | Admin UI for group management | Group list, membership | Paginated group table, member modals | Story 5.19 |
| **useGroups** | React Query hook for group data | API calls, pagination state | Group list, mutations | Story 5.19 |
| **KBPermissionService (Extended)** | KB permissions for users AND groups | User/group IDs, KB IDs, permission levels | Permission assignments, effective permissions | Story 5.20 |
| **KBPermissionsTab** | UI component for KB permission management | User/group permissions | Permission tables, add/edit modals | Story 5.20 |
| **ThemeStore (Extended)** | Zustand store for theme management | Theme selection | Applied theme class, persisted preference | Story 5.21 |
| **ThemeSelector** | User menu submenu for theme selection | Current theme, available themes | Theme list with checkmark indicator | Story 5.21 |

### Data Models and Contracts

**New Database Schema (Stories 5.19, 5.20)**

Epic 5 introduces new database tables for group management and extends KB permissions:

**Groups Table (Story 5.19)**
```sql
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_groups (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, group_id)
);
```

**KB Group Permissions Table (Story 5.20)**
```sql
CREATE TABLE kb_group_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL, -- 'read', 'write', 'admin'
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    UNIQUE (knowledge_base_id, group_id)
);
```

**Existing Models Extended**
- `User`: Existing model (from Story 1.6), no changes
- `KnowledgeBase`: Existing model, no changes
- `KBPermission`: Existing model, extended to work with groups

**Key Data Structures:**

**Admin Statistics Response**
```typescript
interface AdminStats {
  users: {
    total: number;
    active: number;  // Active in last 30 days
    inactive: number;
  };
  knowledgeBases: {
    total: number;
    byStatus: { active: number; archived: number; };
  };
  documents: {
    total: number;
    byStatus: { processed: number; queued: number; failed: number; };
  };
  storage: {
    totalBytes: number;
    avgDocSizeBytes: number;
  };
  activity: {
    searches: { last24h: number; last7d: number; last30d: number; };
    generations: { last24h: number; last7d: number; last30d: number; };
  };
  trends: {
    searches: number[];  // Sparkline data (last 30 days)
    generations: number[];
  };
}
```

**Audit Log Filter Request**
```python
class AuditLogFilter(BaseModel):
    start_date: datetime | None
    end_date: datetime | None
    user_email: str | None
    action_type: str | None  # search, generation, document_upload, etc.
    resource_type: str | None  # knowledge_base, document, user, etc.
    page: int = 1
    page_size: int = 50
```

**Queue Status Response**
```python
class QueueStatus(BaseModel):
    queue_name: str
    depth: int  # Tasks waiting
    active_tasks: int
    scheduled_tasks: int
    workers: list[WorkerInfo]

class WorkerInfo(BaseModel):
    worker_id: str
    status: str  # online, offline
    active_tasks: int
    processed_count: int
```

**Onboarding Wizard State**
```typescript
interface OnboardingState {
  userId: string;
  currentStep: number;
  completedSteps: number[];
  totalSteps: number;
  isCompleted: boolean;
  skipped: boolean;
}
```

**Existing Models Extended**
- `User`: Add `onboarding_completed: bool`, `last_active: datetime` (migration)
- `KnowledgeBase`: Existing model, no changes
- `Document`: Existing model, no changes
- `AuditEvent`: Existing model from Story 1.7, no changes

**Group Model (Story 5.19)**
```python
class Group(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    member_count: int
    created_at: datetime
    updated_at: datetime

class GroupCreate(BaseModel):
    name: str
    description: str | None = None

class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None

class GroupMember(BaseModel):
    user_id: UUID
    email: str
    is_active: bool
    joined_at: datetime
```

**KB Permission Models (Story 5.20 - Extended)**
```python
class KBPermissionResponse(BaseModel):
    user_permissions: list[UserKBPermission]
    group_permissions: list[GroupKBPermission]

class UserKBPermission(BaseModel):
    user_id: UUID
    email: str
    permission_level: str  # 'read', 'write', 'admin'
    is_direct: bool  # True if direct assignment, False if via group

class GroupKBPermission(BaseModel):
    group_id: UUID
    group_name: str
    permission_level: str

class AddKBPermissionRequest(BaseModel):
    user_id: UUID | None = None  # Mutually exclusive with group_id
    group_id: UUID | None = None
    permission_level: str  # 'read', 'write', 'admin'
```

**Theme Type (Story 5.21)**
```typescript
type Theme = 'light' | 'dark' | 'light-blue' | 'dark-navy' | 'system';

const THEMES = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'light-blue', label: 'Light Blue', icon: Sun },
  { value: 'dark-navy', label: 'Dark Navy', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
];
```

### APIs and Interfaces

**New Admin Endpoints** (all require admin role)

```python
# Story 5.1 - Admin Dashboard
GET /api/v1/admin/stats
Response: AdminStats

# Story 5.2 - Audit Log Viewer
POST /api/v1/admin/audit/logs
Body: AuditLogFilter
Response: PaginatedResponse[AuditEvent]

# Story 5.3 - Audit Log Export
POST /api/v1/admin/audit/export
Body: AuditLogFilter
Response: StreamingResponse (CSV or JSON)

# Story 5.4 - Processing Queue Status
GET /api/v1/admin/queue/status
Response: list[QueueStatus]

GET /api/v1/admin/queue/{queue_name}/tasks
Response: list[TaskInfo]

# Story 5.5 - System Configuration
GET /api/v1/admin/config
Response: dict[str, ConfigValue]

PUT /api/v1/admin/config/{key}
Body: { value: Any }
Response: ConfigValue

# Story 5.6 - KB Statistics (Admin View)
GET /api/v1/admin/knowledge-bases/{kb_id}/stats
Response: KBDetailedStats

# Story 5.18 - User Management (uses existing endpoints from Story 1.6)
GET /api/v1/admin/users
Query: page, page_size, search, sort_by, sort_order
Response: PaginatedResponse[User]

POST /api/v1/admin/users
Body: { email: str, password: str, is_superuser: bool }
Response: User

PATCH /api/v1/admin/users/{user_id}
Body: { is_active: bool, is_superuser: bool }
Response: User

# Story 5.19 - Group Management
GET /api/v1/admin/groups
Query: page, page_size, search
Response: PaginatedResponse[Group]

POST /api/v1/admin/groups
Body: GroupCreate
Response: Group

PATCH /api/v1/admin/groups/{group_id}
Body: GroupUpdate
Response: Group

DELETE /api/v1/admin/groups/{group_id}
Response: { success: bool }

GET /api/v1/admin/groups/{group_id}/members
Response: list[GroupMember]

POST /api/v1/admin/groups/{group_id}/members
Body: { user_ids: list[UUID] }
Response: { added: int }

DELETE /api/v1/admin/groups/{group_id}/members/{user_id}
Response: { success: bool }

# Story 5.20 - KB Permission Management (Extended)
GET /api/v1/knowledge-bases/{kb_id}/permissions
Response: KBPermissionResponse

POST /api/v1/knowledge-bases/{kb_id}/permissions
Body: AddKBPermissionRequest
Response: { success: bool }

PATCH /api/v1/knowledge-bases/{kb_id}/permissions/{permission_id}
Body: { permission_level: str }
Response: { success: bool }

DELETE /api/v1/knowledge-bases/{kb_id}/permissions/{permission_id}
Response: { success: bool }
```

**New User Endpoints**

```python
# Story 5.7 - Onboarding Wizard
GET /api/v1/users/me/onboarding
Response: OnboardingState

POST /api/v1/users/me/onboarding/step/{step_number}
Response: OnboardingState

POST /api/v1/users/me/onboarding/skip
Response: OnboardingState

# Story 5.8 - Smart KB Suggestions
GET /api/v1/users/me/kb-recommendations
Response: list[KBRecommendation]

# Story 5.9 - Recent KBs
GET /api/v1/users/me/recent-kbs
Response: list[KnowledgeBase]
```

**New Frontend Routes**

```typescript
// Story 5.0 - Chat Page Route
/app/(protected)/chat -> ChatPage component
  Uses: ChatContainer, ChatInput, useChatStream from Epic 4

// Stories 5.1-5.6 - Admin Pages
/app/(protected)/admin -> AdminDashboard (overview)
/app/(protected)/admin/audit -> AuditLogViewer
/app/(protected)/admin/queue -> QueueMonitor
/app/(protected)/admin/config -> SystemConfig
/app/(protected)/admin/kb/{id}/stats -> KBStatsDetail

// Story 5.18 - User Management
/app/(protected)/admin/users -> UserManagementPage
  Uses: UserTable, CreateUserModal, EditUserModal, useUsers hook

// Story 5.19 - Group Management
/app/(protected)/admin/groups -> GroupManagementPage
  Uses: GroupTable, GroupModal, GroupMembershipModal, useGroups hook

// Story 5.20 - KB Permissions
/app/(protected)/kb/{id}/permissions -> KBPermissionsTab (tab within KB detail)
  Uses: PermissionTable, AddPermissionModal, useKBPermissions hook
```

### Workflows and Sequencing

**Story 5.0: Integration Completion Workflow**
```
1. Dev verifies backend services running
   - Check FastAPI health endpoint
   - Check Celery workers (celery -A app.workers.celery_app inspect active)
   - Check Qdrant, Redis, MinIO, LiteLLM connectivity

2. Create chat page route
   - Create /app/(protected)/chat/page.tsx
   - Import ChatContainer from Epic 4 components
   - Wire up useChatStream, useChatManagement hooks

3. Update dashboard with navigation cards
   - Edit /app/(protected)/dashboard/page.tsx
   - Add "Search Knowledge Base" card → /search
   - Add "Chat" card → /chat
   - Remove "Coming in Epic 3/4" placeholders

4. Smoke test user journeys
   - Journey 1: Login → Upload document → Wait for processing → Search
   - Journey 2: Login → Navigate to Search → Query → View citations
   - Journey 3: Login → Navigate to Chat → Send message → Receive streaming response
   - Journey 4: Login → Search → Generate document → Edit → Export
```

**Story 5.1: Admin Dashboard Stats Workflow**
```
1. AdminStatsService.get_dashboard_stats()
   - Query users table (COUNT(*), COUNT WHERE last_active > NOW() - 30 days)
   - Query knowledge_bases table (COUNT(*), GROUP BY status)
   - Query documents table (COUNT(*), GROUP BY processing_status)
   - Query audit.events for search/generation counts (last 24h, 7d, 30d)
   - Query storage usage (SUM(file_size))
   - Generate sparkline data (GROUP BY date for last 30 days)
   - Cache result in Redis (TTL: 5 minutes)

2. Return aggregated stats to frontend

3. Frontend renders dashboard cards with charts
   - Use recharts for sparklines
   - Click metric → navigate to detail view
```

**Story 5.2/5.3: Audit Log Viewer/Export Workflow**
```
1. User applies filters (date range, user, action, resource)

2. POST /api/v1/admin/audit/logs
   - AuditService.query_audit_logs(filter)
   - SELECT FROM audit.events WHERE ... ORDER BY timestamp DESC
   - Use indexed columns (timestamp, user_id, action_type, resource_type)
   - LIMIT/OFFSET for pagination

3. Viewer: Render paginated table with sort/filter controls

4. Export: POST /api/v1/admin/audit/export
   - Same query, no pagination
   - Stream CSV or JSON response
   - Set Content-Disposition header for download
```

**Story 5.4: Queue Monitoring Workflow**
```
1. GET /api/v1/admin/queue/status

2. QueueMonitorService.get_queue_status()
   - Connect to Celery via Redis backend
   - celery.control.inspect().active() → active tasks
   - celery.control.inspect().scheduled() → scheduled tasks
   - celery.control.inspect().stats() → worker info
   - Query queue depths from Redis

3. Return queue metrics

4. Frontend renders queue dashboard
   - Queue cards with depth/worker count
   - Worker status indicators
   - Task list with expand/collapse details
```

**Story 5.16: Docker E2E Infrastructure Setup**
```
1. Create docker-compose.e2e.yml
   - Services: frontend, backend, postgres, redis, qdrant, minio, celery-worker, playwright
   - Networks: isolated test network
   - Volumes: test data persistence

2. Configure Playwright for Docker
   - playwright.config.ts with Docker-specific baseURL
   - Wait-for-services healthcheck script

3. Implement database seeding
   - fixtures/seed.sql or Python seed script
   - Create test users, KBs, documents

4. Create E2E test suite
   - tests/e2e/epic3-search.spec.ts (15+ tests)
   - tests/e2e/epic4-chat-generation.spec.ts (15+ tests)

5. GitHub Actions workflow
   - .github/workflows/e2e-tests.yml
   - docker-compose up → seed → playwright test → docker-compose down
```

**Story 5.18: User Management Workflow**
```
1. Admin navigates to /admin/users
   - AdminGuard verifies is_superuser=true
   - useUsers hook fetches paginated user list

2. User List Display
   - UserTable renders with columns: Email, Status, Role, Created, Last Active
   - Pagination controls (20 per page)
   - Search/filter by email
   - Sort by any column

3. Create User Flow
   - Click "Add User" → CreateUserModal opens
   - Form: Email, Password, Confirm Password, Is Admin
   - Submit → POST /api/v1/admin/users
   - Success → Toast + refresh list
   - Error → Inline validation messages

4. Edit User Flow
   - Click edit action on row → EditUserModal opens
   - Display: Email (read-only), Status toggle, Role dropdown
   - Submit → PATCH /api/v1/admin/users/{user_id}
   - Prevent self-deactivation (warning if own account)
   - All changes logged to audit.events
```

**Story 5.19: Group Management Workflow**
```
1. Admin navigates to /admin/groups
   - AdminGuard verifies is_superuser=true
   - useGroups hook fetches paginated group list

2. Group List Display
   - GroupTable renders with: Name, Description, Member Count, Created
   - Search by group name
   - Click row → Expand to show member list

3. Create/Edit Group Flow
   - Click "Create Group" or edit action → GroupModal opens
   - Form: Name (required, unique), Description (optional)
   - Submit → POST or PATCH /api/v1/admin/groups
   - Validation prevents duplicate group names

4. Manage Members Flow
   - Click "Manage Members" on group → GroupMembershipModal opens
   - Display current members with remove action
   - "Add Members" → User picker with search
   - Add/remove → POST/DELETE /api/v1/admin/groups/{id}/members
   - All changes logged to audit.events
```

**Story 5.20: KB Permission Management Workflow**
```
1. Admin navigates to KB detail → Permissions tab
   - useKBPermissions hook fetches permissions
   - Displays User Permissions and Group Permissions sections

2. View Effective Permissions
   - User permissions: Direct assignments
   - Group permissions: Inherited via group membership
   - Display "via [Group Name]" for inherited permissions

3. Add Permission Flow
   - Click "Add User/Group Permission" → AddPermissionModal opens
   - Entity picker: User email autocomplete OR Group dropdown
   - Permission level dropdown: Read, Write, Admin
   - Validation prevents duplicate assignments
   - Submit → POST /api/v1/knowledge-bases/{kb_id}/permissions

4. Edit/Remove Permission Flow
   - Click edit on row → Change permission level
   - Click remove → Delete permission
   - Warning if removing last Admin permission
   - All changes logged to audit.events
```

**Story 5.21: Theme System Workflow**
```
1. User opens user menu (avatar dropdown)
   - Theme submenu displays with palette icon

2. View Theme Options
   - 5 options: Light, Dark, Light Blue, Dark Navy, System
   - Current theme shows checkmark indicator

3. Select Theme
   - Click theme option → Immediately applies
   - ThemeStore updates state, applies CSS class to html element
   - Preference persisted to localStorage via Zustand persist

4. Theme Persistence
   - On page load, ThemeStore hydrates from localStorage
   - System theme follows OS preference (prefers-color-scheme)
   - All UI components use theme CSS variables for consistency
```

## Non-Functional Requirements

### Performance

**Admin Dashboard (Story 5.1)**
- Stats endpoint response time: < 500ms (with Redis caching)
- Redis cache TTL: 5 minutes for dashboard stats
- Sparkline data aggregation: < 200ms (indexed queries on audit.events)
- Target: Support 100+ concurrent admin users viewing dashboard

**Audit Log Viewer (Story 5.2)**
- Query response time: < 1s for 50 results per page
- Filtering latency: < 300ms with indexed columns (timestamp, user_id, action_type, resource_type)
- Pagination: Efficient LIMIT/OFFSET queries on audit.events table
- Export generation (Story 5.3): Stream CSV/JSON without loading entire result set into memory

**Queue Monitoring (Story 5.4)**
- Queue status refresh: < 2s (Celery inspect API calls)
- Real-time task updates: Poll interval 5-10 seconds
- Worker health checks: < 500ms per worker

**E2E Test Suite (Story 5.16)**
- Full E2E test run: < 10 minutes (30+ tests across Epic 3 & 4)
- Database seeding: < 30 seconds
- Docker compose startup: < 60 seconds (all services healthy)

**User Experience Polish (Stories 5.7-5.9)**
- Onboarding wizard: Instant step transitions (< 100ms)
- KB recommendations: < 300ms (pre-computed scores, cached)
- Recent KBs: < 100ms (simple query with LIMIT 5)

**User Management (Story 5.18)**
- User list query: < 200ms (indexed on email, is_active, created_at)
- Create/edit user: < 300ms (single table write)
- Pagination: 20 users per page, efficient LIMIT/OFFSET

**Group Management (Story 5.19)**
- Group list query: < 200ms (with member count aggregation)
- Membership operations: < 100ms (junction table operations)
- Member search: < 200ms (autocomplete via indexed email)

**KB Permission Management (Story 5.20)**
- Permission list query: < 300ms (joins user and group tables)
- Permission check (authorization): < 50ms (cached effective permissions)
- Add/remove permission: < 100ms (single table operations)

**Theme System (Story 5.21)**
- Theme switch: < 16ms (single DOM class change, CSS variable swap)
- Theme persistence: < 10ms (localStorage write)
- Theme hydration: < 50ms (on page load)

### Security

**Admin Access Control**
- All `/api/v1/admin/*` endpoints require `is_superuser=True` check (FastAPI dependency)
- Admin role verification before exposing sensitive data (queue status, audit logs, system config)
- Audit log export includes user authentication in download logs

**Audit Log Protection**
- Audit events table: INSERT-only (no UPDATE/DELETE except by scheduled archival job)
- Admin audit viewer: No PII exposure in default view (GDPR compliance)
- Export format: Sanitize PII fields unless admin has explicit "export_pii" permission

**System Configuration (Story 5.5)**
- Config changes logged to audit.events
- Sensitive config values (API keys, secrets) stored encrypted in database
- Config API validates input types/ranges before persisting

**Onboarding Data (Story 5.7)**
- User onboarding state stored in users table (no separate sensitive data)
- No tracking of user behavior beyond completion status

**E2E Test Environment (Story 5.16)**
- Isolated test database (never touches production data)
- Test fixtures use synthetic data (no real user information)
- Docker network isolation prevents accidental external access

**User Management Security (Story 5.18)**
- All user management endpoints require `is_superuser=True`
- Password hashing via bcrypt (existing infrastructure)
- Cannot deactivate own admin account (prevented in UI and API)
- User creation/modification logged to audit.events

**Group Management Security (Story 5.19)**
- All group management endpoints require `is_superuser=True`
- Group membership changes logged to audit.events
- Soft delete for groups (preserve audit trail)

**KB Permission Security (Story 5.20)**
- Permission changes require KB admin role OR is_superuser
- Group-based permissions inherit to all group members
- Direct user permissions override group permissions
- Cannot remove last admin permission (safety check)
- All permission changes logged to audit.events

**Theme System Security (Story 5.21)**
- No security implications (client-side only, localStorage)
- Theme preference not synced to server (no PII)

**Existing Security Maintained**
- TLS 1.3 for all API communication (from Epic 1)
- JWT-based authentication (from Epic 1)
- KB-level access control enforced (from Epic 2)
- Citation security verified (from Epic 3)

### Reliability/Availability

**Admin Dashboard High Availability**
- Redis cache: If Redis unavailable, fall back to direct database queries (degraded performance)
- Stats calculation: Graceful degradation if any metric query fails (return partial stats)
- No single point of failure for read-only admin operations

**Audit Log Durability**
- PostgreSQL audit.events table: ACID guarantees, replicated if configured
- Export operations: Stream data to avoid OOM on large exports
- Pagination prevents query timeouts on large result sets

**Queue Monitoring Resilience**
- Celery inspect failures: Display "unavailable" status rather than error
- Worker offline detection: Mark workers as "offline" if no heartbeat in 60s
- Queue depth queries: Fall back to Redis key count if Celery inspect fails

**E2E Testing Reliability**
- Docker compose health checks: Ensure all services ready before tests run
- Test isolation: Each test run uses fresh database (seed → test → teardown)
- Retry logic: Playwright retries flaky assertions (network timeouts, animation delays)
- CI pipeline: Fail fast if E2E environment cannot start

**Onboarding Wizard Fault Tolerance**
- Skip option always available (never blocks user from using the app)
- Wizard state persisted to database (survives session refresh)
- If wizard component fails to load, user proceeds to dashboard

### Observability

**Admin Dashboard Metrics**
- Prometheus metrics: `admin_stats_requests_total`, `admin_stats_cache_hits`, `admin_stats_cache_misses`
- Latency histogram: `admin_stats_duration_seconds`
- Error rate: `admin_stats_errors_total` (by error type)

**Audit Log Operations**
- Query performance metrics: `audit_query_duration_seconds`, `audit_export_duration_seconds`
- Export volume tracking: `audit_export_rows_total` (by format: CSV, JSON)
- Filter usage metrics: Track which filters are most commonly used

**Queue Monitoring Observability**
- Queue depth metrics: `celery_queue_depth{queue_name}` (gauge)
- Worker status: `celery_workers_online`, `celery_workers_offline`
- Task processing rate: `celery_tasks_processed_total` (counter)

**E2E Test Monitoring**
- CI metrics: E2E test pass/fail rate, duration, flakiness detection
- Docker startup metrics: Time to healthy state for each service
- Test coverage: Track which E2E scenarios are covered vs. missing

**Structured Logging (All Stories)**
- Admin operations: `{"event": "admin_stats_request", "user_id": "...", "cache_hit": true, "duration_ms": 45}`
- Audit exports: `{"event": "audit_export", "user_id": "...", "format": "csv", "row_count": 1523, "duration_ms": 2341}`
- Queue monitoring: `{"event": "queue_status_check", "workers_online": 3, "queue_depths": {"default": 12, "document_processing": 5}}`
- E2E tests: `{"event": "e2e_test_run", "suite": "epic3-search", "passed": 15, "failed": 0, "duration_ms": 45000}`

**Alerts and Dashboards**
- Grafana dashboard: Admin usage metrics, queue health, E2E test trends
- Alerts: Queue depth > 100 for > 5 minutes, Worker count = 0, E2E test failure rate > 10%

## Dependencies and Integrations

**No New External Dependencies Required**

Epic 5 reuses all existing infrastructure and libraries from Epics 1-4. All required capabilities are already in place.

### Backend Dependencies (Existing - From Epic 1-4)

| Dependency | Version | Purpose | Stories Using |
|------------|---------|---------|---------------|
| **FastAPI** | ≥0.115.0 | Web framework, admin API endpoints | All admin stories (5.1-5.6) |
| **SQLAlchemy 2.0** | 2.0.44 | Database ORM, audit log queries | 5.1, 5.2, 5.3, 5.7, 5.8, 5.9 |
| **asyncpg** | 0.30.0 | Async PostgreSQL driver | All database queries |
| **Redis / redis-py** | ≥7.1.0 | Caching (stats), Celery backend | 5.1, 5.4 |
| **Celery** | 5.5.x | Background jobs, queue monitoring | 5.4, 5.13 |
| **Pydantic** | ≥2.0 | Request/response schemas | All API endpoints |
| **structlog** | ≥25.5.0 | Structured logging | All stories |

**Admin-Specific Libraries (May Need)**
- `pandas` (optional): CSV export generation for audit logs (Story 5.3)
- `openpyxl` (optional): Excel export format for audit logs (Story 5.3)

### Frontend Dependencies (Existing - From Epic 1-4)

| Dependency | Version | Purpose | Stories Using |
|------------|---------|---------|---------------|
| **Next.js** | 16.0.3 | App framework, routing | 5.0 (chat route), 5.1-5.6 (admin pages) |
| **React** | 19.2.0 | UI library | All frontend stories |
| **shadcn/ui + Radix** | Latest | UI components | 5.1-5.9 (admin tables, wizards, cards) |
| **react-hook-form** | ^7.66.1 | Form handling | 5.5 (config forms), 5.7 (wizard) |
| **zod** | ^4.1.12 | Schema validation | All forms |
| **cmdk** | ^1.1.1 | Command palette | 5.10 (test coverage) |
| **lucide-react** | ^0.554.0 | Icons | All UI components |
| **recharts** | (need to add) | Sparkline charts for admin dashboard | 5.1 |
| **date-fns** | ^4.1.0 | Date formatting for audit logs | 5.2, 5.3 |

**New Frontend Dependencies Needed**
```bash
npm install recharts  # For Story 5.1 sparkline charts
```

### Testing Infrastructure (Story 5.16 - New)

| Dependency | Version | Purpose |
|------------|---------|---------|
| **Docker** | ≥20.10 | Container runtime |
| **Docker Compose** | ≥2.0 | Multi-service orchestration |
| **Playwright** | ≥1.40 | E2E testing framework (already installed) |
| **PostgreSQL** | 16 | Test database (Docker image) |
| **Redis** | 7 | Test cache (Docker image) |
| **Qdrant** | ≥1.10.0 | Test vector DB (Docker image) |
| **MinIO** | Latest | Test object storage (Docker image) |

**docker-compose.e2e.yml Services**
- `postgres:16-alpine`
- `redis:7-alpine`
- `qdrant/qdrant:latest`
- `minio/minio:latest`
- `mcr.microsoft.com/playwright:latest`

### Integration Points

**Story 5.0: Integration Completion**
- **Frontend → Backend**: Reuses existing `/api/v1/chat/stream` endpoint (Epic 4)
- **Frontend → Frontend**: Imports ChatContainer, ChatInput from `src/components/chat/` (Epic 4)
- **Dashboard Navigation**: Adds cards linking to `/search` (Epic 3) and `/chat` (Story 5.0)

**Story 5.1: Admin Dashboard**
- **AdminStatsService → PostgreSQL**: Aggregate queries on users, knowledge_bases, documents tables
- **AdminStatsService → Redis**: Cache dashboard stats (5-minute TTL)
- **AdminStatsService → AuditService**: Query audit.events for search/generation activity metrics

**Story 5.2/5.3: Audit Log Viewer/Export**
- **AuditService → PostgreSQL**: Query audit.events table with filters and pagination
- **Export → StreamingResponse**: Stream CSV/JSON without loading full result set into memory

**Story 5.4: Queue Monitoring**
- **QueueMonitorService → Celery**: Use `celery.control.inspect()` API for queue/worker status
- **QueueMonitorService → Redis**: Query queue depths directly from Redis backend

**Story 5.5: System Configuration**
- **ConfigService → PostgreSQL**: Store/retrieve config in dedicated `system_config` table (or JSON column in settings)
- **ConfigService → AuditService**: Log all config changes to audit.events

**Story 5.7: Onboarding Wizard**
- **OnboardingService → PostgreSQL**: Update `users.onboarding_completed`, `users.last_active`
- **Frontend Wizard → Backend API**: POST requests to track wizard progress

**Story 5.8: Smart KB Suggestions**
- **RecommendationService → PostgreSQL**: Query audit.events for user's search/access patterns
- **RecommendationService → Redis**: Cache recommendations per user (1-hour TTL)

**Story 5.9: Recent KBs**
- **Frontend → Backend**: GET `/api/v1/users/me/recent-kbs` (query last_accessed timestamps)

**Story 5.16: Docker E2E Infrastructure**
- **Playwright → Frontend**: HTTP requests to `http://frontend:3000`
- **Frontend → Backend**: HTTP requests to `http://backend:8000`
- **Backend → All Services**: PostgreSQL, Redis, Qdrant, MinIO, LiteLLM connections
- **GitHub Actions → Docker Compose**: CI pipeline triggers E2E test runs

### Technical Debt Stories Dependencies

**Story 5.10: Command Palette Test Coverage**
- Existing: `cmdk`, `@testing-library/react`, `vitest`

**Story 5.11: Epic 3 Search Hardening**
- Existing: `vitest`, `@testing-library/react`, `axe-core` (accessibility testing)

**Story 5.12/5.15: ATDD Test Transition**
- Existing: `pytest`, `pytest-asyncio`, `httpx` (backend integration tests)
- Existing: `vitest`, `@testing-library/react` (frontend component tests)
- Existing: `playwright` (E2E tests)

**Story 5.13: Celery Beat Filesystem Fix**
- Existing: `celery[beat]`, `redis-py`
- Fix: Update `celerybeat-schedule` file path to writable directory

**Story 5.14: Search Audit Logging**
- Existing: `AuditService` (from Story 1.7), `SearchService` (from Epic 3)
- Integration: Call `audit_service.log_event()` from search endpoints

**Story 5.18: User Management UI**
- Existing: Backend user endpoints from Story 1.6 (`GET/POST/PATCH /api/v1/admin/users`)
- Frontend: React Query, shadcn/ui, Zod validation, AdminGuard component
- Depends on: Story 5.17 (Main Navigation)

**Story 5.19: Group Management**
- Backend: New migration for `groups` and `user_groups` tables
- Backend: GroupService, group API endpoints
- Frontend: React Query, shadcn/ui components
- Depends on: Story 5.18 (User Management UI)

**Story 5.20: KB Permission Management UI**
- Backend: New migration for `kb_group_permissions` table
- Backend: Extend KBPermissionService for group support
- Frontend: KBPermissionsTab, AddPermissionModal components
- Depends on: Story 5.19 (Group Management), Story 2.2 (KB Permissions Backend)

**Story 5.21: Theme System**
- Frontend: CSS variables in globals.css, ThemeStore (Zustand)
- Frontend: user-menu.tsx DropdownMenuSub for theme selector
- No backend dependencies

## Acceptance Criteria (Authoritative)

### Story 5.0: Epic 3 & 4 Integration Completion (CRITICAL)

**AC-5.0.1**: User can navigate to `/chat` route from dashboard navigation card without encountering 404 errors.

**AC-5.0.2**: All Epic 3 search features (semantic search, citations, cross-KB search, quick search) are accessible from dashboard navigation and function correctly.

**AC-5.0.3**: Chat interface streams LLM responses using SSE protocol from `/api/v1/chat/stream` endpoint with real-time citation extraction.

**AC-5.0.4**: Document generation workflow is accessible: Search → Generate → Edit → Export completes without errors.

**AC-5.0.5**: Backend services (FastAPI, Celery workers, Redis, Qdrant, MinIO, LiteLLM) connectivity verified via smoke tests.

**AC-5.0.6**: Manual smoke test covers 4 user journeys: (1) Document upload → Search, (2) Navigate to Search → View citations, (3) Navigate to Chat → Streaming response, (4) Search → Generate → Edit → Export.

---

### Story 5.1: Admin Dashboard Overview

**AC-5.1.1**: Admin user sees system statistics: total users, active users (30-day), total KBs, total documents.

**AC-5.1.2**: Dashboard displays activity metrics: searches and generations for last 24h, 7d, 30d.

**AC-5.1.3**: Sparkline charts render trends for searches and generations over last 30 days using recharts library.

**AC-5.1.4**: Statistics data refreshes every 5 minutes via Redis cache; cache miss triggers fresh database aggregation.

**AC-5.1.5**: Non-admin users receive 403 Forbidden when accessing `/api/v1/admin/stats`.

---

### Story 5.2: Audit Log Viewer

**AC-5.2.1**: Admin can view paginated audit logs with filters: event_type, user_id, date_range, resource_type.

**AC-5.2.2**: Audit log table displays: timestamp, event_type, user_email, resource_type, resource_id, status, duration_ms.

**AC-5.2.3**: PII fields are redacted in default view; admin must have `export_pii` permission to view full data.

**AC-5.2.4**: Pagination supports up to 10,000 records per request; query timeout set to 30s.

**AC-5.2.5**: Filtering by date_range returns results sorted by timestamp DESC.

---

### Story 5.3: Audit Log Export

**AC-5.3.1**: Admin can export filtered audit logs in CSV or JSON format via streaming response.

**AC-5.3.2**: Export operation logs to audit.events with action_type="audit_export".

**AC-5.3.3**: Export streams data incrementally (no full result set loaded into memory).

**AC-5.3.4**: CSV export includes header row with column names matching AuditEvent model fields.

**AC-5.3.5**: Export respects same PII redaction rules as viewer (AC-5.2.3).

---

### Story 5.4: Processing Queue Status

**AC-5.4.1**: Admin sees queue status for all Celery queues: document_processing, embedding_generation, export_generation.

**AC-5.4.2**: Each queue displays: pending tasks, active tasks, worker count, workers online/offline.

**AC-5.4.3**: Task details include: task_id, task_name, status, started_at, estimated_duration.

**AC-5.4.4**: Workers marked "offline" if no heartbeat received in 60s.

**AC-5.4.5**: Queue monitoring gracefully handles Celery inspect failures by displaying "unavailable" status.

---

### Story 5.5: System Configuration

**AC-5.5.1**: Admin can view all system configuration keys via GET `/api/v1/admin/config`.

**AC-5.5.2**: Admin can update config values via PUT `/api/v1/admin/config/{key}` with input validation.

**AC-5.5.3**: Config changes are logged to audit.events with old_value and new_value.

**AC-5.5.4**: Sensitive config values (API keys, secrets) are encrypted at rest and redacted in GET responses.

**AC-5.5.5**: Invalid config values are rejected with 400 Bad Request and validation error details.

---

### Story 5.6: KB Statistics (Admin View)

**AC-5.6.1**: Admin can view detailed KB statistics: document count, total chunks, total embeddings, storage size.

**AC-5.6.2**: KB stats include usage metrics: searches (30d), generations (30d), unique users (30d).

**AC-5.6.3**: Stats display top 5 most accessed documents within the KB.

**AC-5.6.4**: Stats refresh on-demand (no caching); query timeout set to 15s.

**AC-5.6.5**: Non-admin users with KB access receive 403 Forbidden for admin-only stats endpoint.

---

### Story 5.7: Onboarding Wizard

**AC-5.7.1**: New users see onboarding wizard on first login with 3 steps: Welcome, Create First KB, Upload Document.

**AC-5.7.2**: Users can skip wizard via "Skip Onboarding" button; onboarding_completed flag set to true.

**AC-5.7.3**: Wizard progress persists across sessions via `users.onboarding_state` JSON column.

**AC-5.7.4**: Completing wizard creates a "My First KB" and uploads a sample document.

**AC-5.7.5**: Wizard never shown to users with `onboarding_completed=true`.

---

### Story 5.8: Smart KB Suggestions

**AC-5.8.1**: Users see personalized KB recommendations based on search history and access patterns.

**AC-5.8.2**: Recommendation algorithm scores KBs by: recent_access_count (30d), search_relevance, shared_access.

**AC-5.8.3**: Recommendations cached per user for 1 hour via Redis.

**AC-5.8.4**: GET `/api/v1/users/me/kb-recommendations` returns max 5 recommendations with scores.

**AC-5.8.5**: Cold start (new users): Recommendations default to most popular public KBs.

---

### Story 5.9: Recent KBs and Polish Items

**AC-5.9.1**: Dashboard displays "Recent KBs" section showing last 5 accessed KBs with timestamps.

**AC-5.9.2**: Recent KBs query completes in < 100ms via indexed `last_accessed` column.

**AC-5.9.3**: Empty state message displays for users with no KB access history.

**AC-5.9.4**: Clicking recent KB card navigates to KB-specific search page.

**AC-5.9.5**: Dashboard includes tooltip help text for new users.

---

### Story 5.10: Command Palette Test Coverage Improvement

**AC-5.10.1**: Unit tests cover keyboard shortcuts (Cmd+K, Cmd+P, Escape) with ≥90% coverage.

**AC-5.10.2**: Tests verify quick search navigation, KB switching, and command execution.

**AC-5.10.3**: Accessibility tests verify ARIA labels and keyboard navigation (axe-core).

**AC-5.10.4**: Integration tests verify command palette opens/closes without React errors.

**AC-5.10.5**: All tests pass in CI/CD pipeline; no regressions from Epic 3.

---

### Story 5.11: Epic 3 Search Hardening

**AC-5.11.1**: Unit tests for search results components (SearchResultCard, CitationPreview) achieve ≥90% coverage.

**AC-5.11.2**: Accessibility tests verify WCAG 2.1 AA compliance for search UI (color contrast, ARIA, keyboard nav).

**AC-5.11.3**: Error handling tests verify graceful degradation on API failures (500, network timeout).

**AC-5.11.4**: Cross-KB search tests verify multi-KB result aggregation and deduplication.

**AC-5.11.5**: All 15 unit tests pass; no skipped tests remain.

---

### Story 5.12: ATDD Integration Tests Transition to Green

**AC-5.12.1**: All 31 Epic 3 integration tests pass without skips or xfails.

**AC-5.12.2**: Tests use real Qdrant, LiteLLM, PostgreSQL services (not mocks).

**AC-5.12.3**: Test fixtures seed database with realistic data (users, KBs, documents, embeddings).

**AC-5.12.4**: Tests clean up resources after execution (no database pollution).

**AC-5.12.5**: Integration tests run in CI/CD pipeline with < 5-minute execution time.

---

### Story 5.13: Celery Beat Filesystem Fix

**AC-5.13.1**: Celery Beat scheduler writes `celerybeat-schedule` to writable directory (`/app/celery-data/` in Docker).

**AC-5.13.2**: Scheduled tasks (reconciliation, archival) execute without filesystem permission errors.

**AC-5.13.3**: Docker volume mounts persist `celerybeat-schedule` across container restarts.

**AC-5.13.4**: Logs confirm Beat scheduler initializes successfully on container startup.

**AC-5.13.5**: No root-owned files created in working directory.

---

### Story 5.14: Search Audit Logging

**AC-5.14.1**: All search API calls log to audit.events with event_type="search".

**AC-5.14.2**: Audit logs capture: user_id, query_text (PII sanitized), kb_id, result_count, duration_ms.

**AC-5.14.3**: Logging uses fire-and-forget pattern (no impact on search latency).

**AC-5.14.4**: Failed searches log with status="failed" and error_message field.

**AC-5.14.5**: Search audit logs queryable via Story 5.2 audit log viewer.

---

### Story 5.15: Epic 4 ATDD Tests Transition to Green

**AC-5.15.1**: All 47 Epic 4 integration tests (chat, generation, streaming) pass without skips or xfails.

**AC-5.15.2**: Tests use real LiteLLM API (not mocks) for generation/streaming tests.

**AC-5.15.3**: SSE streaming tests verify progressive citation extraction and AbortController cancellation.

**AC-5.15.4**: Frontend E2E tests verify chat UI, generation modal, draft editor, export dialog.

**AC-5.15.5**: Tests execute in CI/CD with < 10-minute total runtime.

---

### Story 5.16: Docker E2E Infrastructure

**AC-5.16.1**: `docker-compose.e2e.yml` orchestrates all services: backend, frontend, postgres, redis, qdrant, minio, litellm.

**AC-5.16.2**: Database seeding script populates test data: 3 users, 5 KBs, 20 documents, 100 embeddings.

**AC-5.16.3**: Playwright tests execute against frontend service at `http://frontend:3000`.

**AC-5.16.4**: 15-20 E2E tests cover: login, upload, search, citations, chat, generation, export workflows.

**AC-5.16.5**: GitHub Actions CI pipeline runs E2E tests on every PR; failures block merge.

---

### Story 5.18: User Management UI

**AC-5.18.1**: Admin navigates to `/admin/users` and sees paginated table with columns: Email, Status (badge), Role, Created date, Last active date. Supports sort/filter by email, 20 users per page.

**AC-5.18.2**: "Add User" button opens modal with Email, Password, Confirm Password, Is Admin checkbox. POST to `/api/v1/admin/users` on submit. Success shows toast and refreshes list. Error shows inline validation.

**AC-5.18.3**: Edit action on user row opens modal with Email (read-only), Status toggle, Role dropdown. PATCH to `/api/v1/admin/users/{user_id}` on save. Cannot deactivate own account (warning displayed).

**AC-5.18.4**: Status toggle updates badge immediately (optimistic UI). API updates `is_active` field. Deactivated users cannot login. Action logged to audit.events.

**AC-5.18.5**: Admin navigation shows "Users" link in admin section. Active state shown when on users page.

**AC-5.18.6**: Non-admin users redirected to `/dashboard` with error message when accessing `/admin/users`. API returns 403 Forbidden.

---

### Story 5.19: Group Management

**AC-5.19.1**: Migration creates `groups` table (id, name, description, is_active, created_at, updated_at) and `user_groups` junction table (user_id, group_id, created_at). API endpoints exist for CRUD and membership management.

**AC-5.19.2**: Admin navigates to `/admin/groups` and sees table with: Name, Description, Member count, Created date. Search by group name. Click row expands to show member list.

**AC-5.19.3**: Create/Edit modal has Name (required, unique) and Description (optional). Validation prevents duplicate group names. Success refreshes list.

**AC-5.19.4**: "Manage Members" shows current members with remove action. "Add Members" opens user picker with email search. Add/remove updates immediately. Changes logged to audit.events.

**AC-5.19.5**: Admin navigation shows "Groups" link. Clicking navigates to `/admin/groups`.

**AC-5.19.6**: Non-admin users receive 403 Forbidden when accessing group endpoints.

---

### Story 5.20: Role & KB Permission Management UI

**AC-5.20.1**: KB detail page has "Permissions" tab showing two sections: User Permissions table and Group Permissions table. Each row shows Entity (email/group name) and Permission Level (Read/Write/Admin).

**AC-5.20.2**: "Add User/Group Permission" opens modal with entity picker (user email autocomplete OR group dropdown) and permission level dropdown. Validation prevents duplicates. Success adds row to table.

**AC-5.20.3**: Edit on permission row allows changing level. Remove button deletes permission. Warning if removing last Admin permission. Changes saved via API and logged to audit.

**AC-5.20.4**: User's effective permissions show both direct and inherited (via group) permissions. Inherited permissions display "via [Group Name]" indicator. Direct permissions override group permissions.

**AC-5.20.5**: POST `/api/v1/knowledge-bases/{kb_id}/permissions` accepts `user_id` OR `group_id` (mutually exclusive). GET returns both user and group permissions. Permission checks consider group membership.

**AC-5.20.6**: "Permissions" tab visible in KB detail admin navigation.

---

### Story 5.21: Theme System

**AC-5.21.1**: User menu shows 5 theme options: Light (default), Dark, Light Blue (sky blue tones), Dark Navy (deep navy), System (OS preference). Each theme has consistent CSS variables for all UI components.

**AC-5.21.2**: User avatar dropdown contains "Theme" submenu with palette icon. Shows all 5 options. Current theme has checkmark indicator. Selecting theme applies immediately.

**AC-5.21.3**: Selected theme persisted in localStorage via Zustand persist. Preserved on page refresh and return visits.

**AC-5.21.4**: All components (cards, tables, modals, popovers, sidebar) use theme colors. No white/mismatched boxes on colored backgrounds. Text maintains readable contrast.

---

### Stories 5.22-5.24: Late-Added Requirements (2025-12-06)

The following stories were added to Epic 5 via the correct-course workflow. Full technical specifications are maintained in their respective story files:

| Story | Title | Story File | Key Technical Notes |
|-------|-------|------------|---------------------|
| **5.22** | Document Tags | [5-22-document-tags.md](./5-22-document-tags.md) | Tags stored in `documents.metadata.tags` JSONB array (no migration). PATCH `/documents/{id}/tags` endpoint. Reuses KB tags UI pattern. |
| **5.23** | Document Processing Progress | [5-23-document-processing-progress.md](./5-23-document-processing-progress.md) | New `processing_steps` JSONB column (migration required). New "Processing" tab in dashboard (ADMIN/WRITE only). 10-second auto-refresh via React Query. |
| **5.24** | KB Dashboard Filtering & Pagination | [5-24-kb-dashboard-filtering.md](./5-24-kb-dashboard-filtering.md) | Filter bar with search/type/status/tags/date. Filter state in URL query params. Default 50 items/page. Follows Story 5-2 audit log patterns. |

**Dependencies:**
- Story 5-22 blocks Story 5-24 (tag filtering requires tags feature)
- Story 5-23 is prioritized first (most valuable for debugging uploads)

---

### Stories 5.25-5.26: Document Chunk Viewer (2025-12-07)

The Document Chunk Viewer feature enables users to verify AI citations by viewing original documents alongside extracted text chunks. Full technical specifications are maintained in their respective story files:

| Story | Title | Story File | Key Technical Notes |
|-------|-------|------------|---------------------|
| **5.25** | Document Chunk Viewer - Backend API | [5-25-document-chunk-viewer-backend.md](./5-25-document-chunk-viewer-backend.md) | New ChunkService queries Qdrant for chunks with `char_start`, `char_end`, `page_number` metadata. GET `/documents/{id}/chunks` with search/pagination. GET `/documents/{id}/content` streams files from MinIO. Optional DOCX→HTML via mammoth. |
| **5.26** | Document Chunk Viewer - Frontend UI | [5-26-document-chunk-viewer-frontend.md](./5-26-document-chunk-viewer-frontend.md) | Split-pane viewer with react-resizable-panels. Format-specific viewers: react-pdf (PDF), docx-preview (DOCX), react-markdown (MD), pre (TXT). Virtual scroll via @tanstack/react-virtual for 1000+ chunks. Debounced search (300ms). |

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Document Detail Modal                               │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  [Details Tab]    [View & Chunks Tab] ← NEW                         ││
│  └─────────────────────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────┬──────────────────────────────────────┐│
│  │      Document Viewer         │         Chunk Sidebar               ││
│  │      (60% width)             │         (40% width)                 ││
│  │                              │  ┌─────────────────────────────────┐││
│  │  ┌────────────────────────┐  │  │ 🔍 Search chunks...             │││
│  │  │ PDF/DOCX/MD/TXT Viewer │  │  └─────────────────────────────────┘││
│  │  │                        │  │  📊 42 chunks found                 ││
│  │  │ ████████████████████   │  │                                     ││
│  │  │ ████ HIGHLIGHTED ████  │  │  ┌─────────────────────────────────┐││
│  │  │ ████████████████████   │  │  │ Chunk 1        char 0-512  [▼] │││
│  │  │                        │  │  │ Lorem ipsum dolor sit amet...  │││
│  │  │                        │  │  └─────────────────────────────────┘││
│  │  │                        │  │  ┌─────────────────────────────────┐││
│  │  │                        │  │  │ Chunk 2 ★     char 513-1024    │││
│  │  │                        │  │  │ Full chunk text displayed      │││
│  │  │                        │  │  │ when expanded with highlight   │││
│  │  └────────────────────────┘  │  │                     [↑ less]   │││
│  │                              │  └─────────────────────────────────┘││
│  └──────────────────────────────┴──────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

**New Backend Components:**

| Component | Path | Description |
|-----------|------|-------------|
| ChunkService | `backend/app/services/chunk_service.py` | Queries Qdrant for document chunks with search and pagination |
| Chunk Schemas | `backend/app/schemas/chunk.py` | `DocumentChunk`, `DocumentChunksResponse` Pydantic models |

**New Frontend Components:**

| Component | Path | Description |
|-----------|------|-------------|
| DocumentChunkViewer | `frontend/src/components/documents/document-chunk-viewer/index.tsx` | Main split-pane container |
| ChunkSidebar | `frontend/src/components/documents/document-chunk-viewer/chunk-sidebar.tsx` | Search box, count, virtual-scroll list |
| ChunkItem | `frontend/src/components/documents/document-chunk-viewer/chunk-item.tsx` | Expandable chunk preview |
| PDFViewer | `frontend/src/components/documents/document-chunk-viewer/viewers/pdf-viewer.tsx` | react-pdf with text layer highlighting |
| DOCXViewer | `frontend/src/components/documents/document-chunk-viewer/viewers/docx-viewer.tsx` | docx-preview with paragraph highlighting |
| MarkdownViewer | `frontend/src/components/documents/document-chunk-viewer/viewers/markdown-viewer.tsx` | react-markdown with character highlighting |
| TextViewer | `frontend/src/components/documents/document-chunk-viewer/viewers/text-viewer.tsx` | Pre-formatted text with character highlighting |
| useDocumentChunks | `frontend/src/hooks/useDocumentChunks.ts` | React Query hook for chunks |
| useDocumentContent | `frontend/src/hooks/useDocumentContent.ts` | React Query hook for document blob |

**New API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/documents/{document_id}/chunks` | Retrieve chunks with optional search and pagination |
| GET | `/api/v1/documents/{document_id}/content` | Stream original document from MinIO |

**New Dependencies:**

| Package | Version | Purpose |
|---------|---------|---------|
| react-pdf | ^9.1.0 | PDF rendering with text layer |
| pdfjs-dist | ^4.0.0 | PDF.js worker for react-pdf |
| docx-preview | ^0.3.2 | Client-side DOCX rendering |
| react-markdown | ^9.0.0 | Markdown rendering |
| react-resizable-panels | ^2.0.0 | Split-pane layout |
| @tanstack/react-virtual | ^3.0.0 | Virtual scroll for chunk list |
| mammoth | >=1.6.0 | DOCX to HTML conversion (backend, optional) |

**Dependencies:**
- Story 5-25 blocks Story 5-26 (backend API required for frontend)
- No database migrations required (existing Qdrant payloads have all metadata)

---

### Cross-Cutting Acceptance Criteria

**AC-X.1**: All admin endpoints require `is_superuser=True`; non-admin users receive 403 Forbidden.

**AC-X.2**: All new features maintain Epic 3 citation-first architecture (no regressions).

**AC-X.3**: All API responses follow existing schema conventions (PaginatedResponse, ErrorResponse).

**AC-X.4**: All frontend components use shadcn/ui and match existing design system (Tailwind theme).

**AC-X.5**: All database migrations are reversible (up/down scripts tested).

## Traceability Mapping

This table traces each Acceptance Criterion back to PRD Functional Requirements, Technical Specification sections, implementing components/APIs, and corresponding test strategies.

| AC ID | PRD FR | Spec Section(s) | Component(s) / API(s) | Test Idea |
|-------|--------|----------------|----------------------|-----------|
| **Story 5.0: Epic 3 & 4 Integration Completion** |
| AC-5.0.1 | FR8a, FR12b | Detailed Design → Workflows (Story 5.0) | ChatPageComponent, `/app/(protected)/chat/page.tsx` | E2E: Navigate from dashboard → `/chat` → verify 200 status |
| AC-5.0.2 | FR8a-c | Detailed Design → Frontend Routes | Dashboard navigation cards, SearchPageComponent | E2E: Click "Search KB" card → verify search UI loads |
| AC-5.0.3 | FR12b | Detailed Design → APIs (Chat Endpoints) | `/api/v1/chat/stream`, ChatContainer, useChatStream | Integration: POST `/chat/stream` → verify SSE events, citations |
| AC-5.0.4 | FR12c-d | Detailed Design → Workflows (Story 5.0) | SearchPage → GenerationModal → DraftEditor → ExportModal | E2E: Full workflow smoke test (4 steps) |
| AC-5.0.5 | FR8a, FR12b | Detailed Design → Workflows (Story 5.0, step 1) | FastAPI health endpoint, Celery inspect, service connectivity | Integration: GET `/health` → verify all services "ok" |
| AC-5.0.6 | FR8a-c, FR12b-d | Detailed Design → Workflows (Story 5.0, step 4) | All Epic 3 & 4 user journeys | Manual: Execute 4 smoke test scenarios, document results |
| **Story 5.1: Admin Dashboard Overview** |
| AC-5.1.1 | FR47 | Detailed Design → Data Models (AdminStats) | AdminStatsService, GET `/api/v1/admin/stats` | Unit: Mock DB queries, verify stats aggregation logic |
| AC-5.1.2 | FR47 | Detailed Design → Data Models (AdminStats.activity) | AdminStatsService.get_activity_metrics(), AuditService | Unit: Mock audit.events queries → verify 24h/7d/30d counts |
| AC-5.1.3 | FR47 | Detailed Design → Services (AdminStatsService) | AdminDashboardPage (recharts Sparkline component) | E2E: Load admin dashboard → verify sparkline SVG rendered |
| AC-5.1.4 | FR47 | NFR Performance, Detailed Design (Redis cache) | AdminStatsService._get_cached_stats(), Redis | Integration: First call → DB hit, second call → cache hit |
| AC-5.1.5 | FR47 | NFR Security (Admin Access Control) | Admin API dependency (`require_admin`), FastAPI security | Integration: Non-admin user GET `/admin/stats` → 403 Forbidden |
| **Story 5.2: Audit Log Viewer** |
| AC-5.2.1 | FR48 | Detailed Design → APIs (Admin Endpoints) | POST `/api/v1/admin/audit/logs`, AuditLogFilter schema | Integration: POST with filters → verify paginated results |
| AC-5.2.2 | FR48 | Detailed Design → Data Models (AuditEvent) | AuditLogViewer component, AuditEvent model | Unit: Render table with mock data → verify columns displayed |
| AC-5.2.3 | FR48 | NFR Security (Audit Log Protection) | AuditService.redact_pii(), `export_pii` permission check | Unit: Call redact_pii() → verify email masked, IP anonymized |
| AC-5.2.4 | FR48 | NFR Performance | POST `/api/v1/admin/audit/logs` query timeout, pagination | Integration: Request 10,000 records → verify < 30s timeout |
| AC-5.2.5 | FR48 | Detailed Design → APIs (Admin Endpoints) | SQLAlchemy query: `order_by(AuditEvent.timestamp.desc())` | Integration: Filter by date_range → verify results DESC sorted |
| **Story 5.3: Audit Log Export** |
| AC-5.3.1 | FR49 | Detailed Design → APIs (Admin Endpoints) | POST `/api/v1/admin/audit/export`, StreamingResponse | Integration: POST export request → verify CSV/JSON streamed |
| AC-5.3.2 | FR49 | NFR Observability | AuditService.log_event(action_type="audit_export") | Unit: Call export API → verify audit event created |
| AC-5.3.3 | FR49 | NFR Reliability (Audit Log Durability) | ExportService._stream_audit_logs() generator | Unit: Mock 100k records → verify memory usage < 100MB |
| AC-5.3.4 | FR49 | Detailed Design → APIs (Story 5.3) | CSV export formatter with header row | Integration: Export CSV → verify header matches AuditEvent fields |
| AC-5.3.5 | FR49 | NFR Security (Audit Log Protection) | ExportService inherits redact_pii() from AC-5.2.3 | Unit: Export with non-PII user → verify PII redacted in output |
| **Story 5.4: Processing Queue Status** |
| AC-5.4.1 | FR50 | Detailed Design → APIs (Admin Endpoints) | GET `/api/v1/admin/queue/status`, QueueMonitorService | Integration: GET queue status → verify 3 queues returned |
| AC-5.4.2 | FR50 | Detailed Design → Data Models (QueueStatus) | QueueMonitorService.get_queue_metrics(), Celery inspect API | Unit: Mock Celery inspect → verify pending/active/worker counts |
| AC-5.4.3 | FR50 | Detailed Design → APIs (Admin Endpoints) | GET `/api/v1/admin/queue/{queue_name}/tasks`, TaskInfo | Integration: GET tasks for queue → verify task_id, status returned |
| AC-5.4.4 | FR50 | NFR Reliability (Queue Monitoring Resilience) | QueueMonitorService._detect_offline_workers() | Unit: Mock no heartbeat 60s → verify worker marked "offline" |
| AC-5.4.5 | FR50 | NFR Reliability (Queue Monitoring Resilience) | QueueMonitorService error handling, try/except on inspect() | Integration: Stop Celery → GET queue status → verify "unavailable" |
| **Story 5.5: System Configuration** |
| AC-5.5.1 | FR51 | Detailed Design → APIs (Admin Endpoints) | GET `/api/v1/admin/config`, ConfigService | Integration: GET config → verify all keys returned |
| AC-5.5.2 | FR51 | Detailed Design → APIs (Admin Endpoints) | PUT `/api/v1/admin/config/{key}`, ConfigService.validate_value() | Integration: PUT valid value → verify updated, invalid → 400 |
| AC-5.5.3 | FR51 | NFR Security (System Configuration) | ConfigService.update_config() → AuditService.log_event() | Unit: Update config → verify audit event with old/new values |
| AC-5.5.4 | FR51 | NFR Security (System Configuration) | ConfigService._encrypt_sensitive(), redact in GET response | Unit: Store API key → verify encrypted at rest, redacted in response |
| AC-5.5.5 | FR51 | Detailed Design → APIs (Admin Endpoints) | Pydantic validation in PUT `/admin/config/{key}` | Integration: PUT invalid value → verify 400 with validation errors |
| **Story 5.6: KB Statistics (Admin View)** |
| AC-5.6.1 | FR52 | Detailed Design → APIs (Admin Endpoints) | GET `/api/v1/admin/knowledge-bases/{kb_id}/stats`, KBStatsService | Integration: GET KB stats → verify document count, chunks, embeddings |
| AC-5.6.2 | FR52 | Detailed Design → Data Models (KBDetailedStats) | KBStatsService.get_usage_metrics(), audit.events queries | Unit: Mock audit queries → verify searches/generations/users counts |
| AC-5.6.3 | FR52 | Detailed Design → APIs (Admin Endpoints) | KBStatsService.get_top_documents() | Integration: GET KB stats → verify top 5 docs with access counts |
| AC-5.6.4 | FR52 | NFR Performance | GET `/admin/kb/{id}/stats` query timeout 15s, no caching | Integration: Request stats → verify < 15s response time |
| AC-5.6.5 | FR52 | NFR Security (Admin Access Control) | Admin-only endpoint, 403 for non-admin KB members | Integration: Non-admin user GET KB stats → verify 403 Forbidden |
| **Story 5.7: Onboarding Wizard** |
| AC-5.7.1 | FR58 | Detailed Design → APIs (User Endpoints) | GET `/api/v1/users/me/onboarding`, OnboardingWizard component | E2E: New user login → verify wizard displays 3 steps |
| AC-5.7.2 | FR58 | Detailed Design → APIs (User Endpoints) | POST `/api/v1/users/me/onboarding/skip`, users.onboarding_completed | Integration: POST skip → verify onboarding_completed=true |
| AC-5.7.3 | FR58 | Detailed Design → Data Models (users.onboarding_state) | OnboardingService.save_progress(), users.onboarding_state JSON | Integration: Complete step 1 → logout → login → verify step 2 shown |
| AC-5.7.4 | FR58 | Detailed Design → Workflows (Story 5.7) | OnboardingService.complete_wizard() creates KB & document | E2E: Complete wizard → verify "My First KB" created with sample doc |
| AC-5.7.5 | FR58 | Detailed Design → APIs (User Endpoints) | GET `/onboarding` conditional logic on onboarding_completed | Integration: User with onboarding_completed=true → verify no wizard |
| **Story 5.8: Smart KB Suggestions** |
| AC-5.8.1 | FR58 | Detailed Design → Services (RecommendationService) | GET `/api/v1/users/me/kb-recommendations`, RecommendationService | Integration: GET recommendations → verify personalized results |
| AC-5.8.2 | FR58 | Detailed Design → Services (RecommendationService) | RecommendationService._score_kb() algorithm | Unit: Mock user history → verify scoring: recent_access > search_relevance |
| AC-5.8.3 | FR58 | NFR Performance | RecommendationService Redis cache (1-hour TTL) | Integration: First call → DB hit, second call → cache hit (1h) |
| AC-5.8.4 | FR58 | Detailed Design → APIs (User Endpoints) | GET `/kb-recommendations` response schema, LIMIT 5 | Integration: User with 10 KBs → verify max 5 returned with scores |
| AC-5.8.5 | FR58 | Detailed Design → Services (RecommendationService) | RecommendationService._cold_start_recommendations() | Unit: New user → verify popular public KBs returned |
| **Story 5.9: Recent KBs and Polish** |
| AC-5.9.1 | FR58 | Detailed Design → APIs (User Endpoints) | GET `/api/v1/users/me/recent-kbs`, DashboardPage component | E2E: Load dashboard → verify "Recent KBs" section with 5 items |
| AC-5.9.2 | FR58 | NFR Performance | SQLAlchemy query: indexed last_accessed column, LIMIT 5 | Integration: GET recent KBs → verify < 100ms response time |
| AC-5.9.3 | FR58 | Detailed Design → Frontend Routes | DashboardPage empty state logic | E2E: New user with no KBs → verify empty state message |
| AC-5.9.4 | FR58 | Detailed Design → Frontend Routes | Recent KB card onClick → navigate(`/kb/${kb.id}/search`) | E2E: Click recent KB card → verify navigation to KB search page |
| AC-5.9.5 | FR58 | Detailed Design → Frontend Routes | DashboardPage tooltip components | E2E: Hover tooltip icon → verify help text displayed |
| **Story 5.10: Command Palette Test Coverage** |
| AC-5.10.1 | N/A (Tech Debt) | Test Strategy → Epic 3 Test Debt | useCommandPalette.test.ts, keyboard event simulation | Unit: Simulate Cmd+K → verify palette opens, test coverage ≥90% |
| AC-5.10.2 | N/A (Tech Debt) | Test Strategy → Epic 3 Test Debt | CommandPalette.test.tsx, mock router navigation | Unit: Execute "Search" command → verify navigation to `/search` |
| AC-5.10.3 | N/A (Tech Debt) | NFR Performance (Accessibility) | CommandPalette accessibility tests with axe-core | Unit: Run axe on CommandPalette → verify no violations |
| AC-5.10.4 | N/A (Tech Debt) | Test Strategy → Epic 3 Test Debt | CommandPalette integration tests with React Testing Library | Integration: Open/close palette → verify no console errors |
| AC-5.10.5 | N/A (Tech Debt) | Test Strategy → CI/CD | GitHub Actions workflow, vitest run | CI: Run tests on PR → verify all pass, coverage uploaded |
| **Story 5.11: Epic 3 Search Hardening** |
| AC-5.11.1 | N/A (Tech Debt) | Test Strategy → Epic 3 Test Debt | SearchResultCard.test.tsx, CitationPreview.test.tsx | Unit: Test all props/interactions → verify ≥90% coverage |
| AC-5.11.2 | N/A (Tech Debt) | NFR Performance (Accessibility) | Search UI accessibility tests with axe-core, WCAG 2.1 AA | Unit: Run axe on search pages → verify AA compliance |
| AC-5.11.3 | N/A (Tech Debt) | Test Strategy → Epic 3 Test Debt | SearchPage error handling tests, mock API failures | Unit: Mock 500 error → verify error boundary, graceful message |
| AC-5.11.4 | N/A (Tech Debt) | Detailed Design → Workflows (Cross-KB Search from Epic 3) | Cross-KB search tests, deduplication logic | Integration: Search 2 KBs → verify results aggregated, no duplicates |
| AC-5.11.5 | N/A (Tech Debt) | Test Strategy → CI/CD | GitHub Actions workflow, all Epic 3 tests green | CI: Run Epic 3 tests → verify 0 skipped tests |
| **Story 5.12: ATDD Integration Tests (Epic 3)** |
| AC-5.12.1 | N/A (Tech Debt) | Test Strategy → Epic 3 Test Debt | All 31 integration tests in `backend/tests/integration/test_*` | Integration: Run pytest → verify 31 passed, 0 skipped/xfail |
| AC-5.12.2 | N/A (Tech Debt) | Test Strategy → Epic 3 Test Debt | Test fixtures use real Qdrant, LiteLLM services | Integration: Tests connect to docker services, no mocks |
| AC-5.12.3 | N/A (Tech Debt) | Test Strategy → Test Fixtures | conftest.py factories: UserFactory, KBFactory, DocumentFactory | Integration: Tests seed data → verify realistic embeddings created |
| AC-5.12.4 | N/A (Tech Debt) | Test Strategy → Test Fixtures | Test teardown: cleanup_database() fixture | Integration: Run test → verify no data pollution in next test |
| AC-5.12.5 | N/A (Tech Debt) | Test Strategy → CI/CD | GitHub Actions workflow, integration test job | CI: Run integration tests → verify < 5-minute execution |
| **Story 5.13: Celery Beat Filesystem Fix** |
| AC-5.13.1 | N/A (Tech Debt) | Detailed Design → Services (CeleryBeat config) | docker-compose.yml volume mount, celerybeat command args | Integration: Start celerybeat → verify schedule file in `/app/celery-data/` |
| AC-5.13.2 | N/A (Tech Debt) | Detailed Design → Services (CeleryBeat scheduled tasks) | Celery periodic tasks: reconciliation, archival | Integration: Wait for scheduled task → verify executed, no errors |
| AC-5.13.3 | N/A (Tech Debt) | Dependencies → Docker Compose | docker-compose.yml celerybeat service volume | Manual: Restart celerybeat → verify schedule file persists |
| AC-5.13.4 | N/A (Tech Debt) | NFR Observability | Celerybeat container logs, structlog output | Manual: docker logs celerybeat → verify "Beat scheduler initialized" |
| AC-5.13.5 | N/A (Tech Debt) | Detailed Design → Services (CeleryBeat config) | Dockerfile USER directive, correct file ownership | Manual: docker exec → ls -l celery-data → verify non-root owner |
| **Story 5.14: Search Audit Logging** |
| AC-5.14.1 | N/A (moved from Epic 3) | Detailed Design → APIs (Search Endpoints from Epic 3) | POST `/api/v1/search` → AuditService.log_event() | Integration: POST search → verify audit event created |
| AC-5.14.2 | N/A (moved from Epic 3) | Detailed Design → Data Models (AuditEvent) | AuditService.log_search_event() with PII sanitization | Unit: Log search → verify query_text sanitized, kb_id captured |
| AC-5.14.3 | N/A (moved from Epic 3) | NFR Performance | Fire-and-forget async logging, no await in request path | Integration: POST search → verify < 200ms latency (no degradation) |
| AC-5.14.4 | N/A (moved from Epic 3) | Detailed Design → APIs (Search Endpoints) | AuditService.log_search_event(status="failed", error_message) | Integration: POST invalid search → verify audit log with failure |
| AC-5.14.5 | N/A (moved from Epic 3) | Detailed Design → APIs (Admin Endpoints from Story 5.2) | POST `/admin/audit/logs` with event_type="search" filter | Integration: Query audit logs → verify search events returned |
| **Story 5.15: ATDD Tests (Epic 4)** |
| AC-5.15.1 | N/A (Tech Debt) | Test Strategy → Epic 4 Test Debt | All 47 integration tests in `backend/tests/integration/test_chat_*`, `test_generation_*` | Integration: Run pytest → verify 47 passed, 0 skipped/xfail |
| AC-5.15.2 | N/A (Tech Debt) | Test Strategy → Epic 4 Test Debt | Integration tests use real LiteLLM API for streaming tests | Integration: Tests call LiteLLM, no mocks for generation |
| AC-5.15.3 | N/A (Tech Debt) | Detailed Design → APIs (Chat/Generation Streaming from Epic 4) | SSE streaming tests, AbortController cancellation | Integration: POST `/chat/stream` → verify SSE events, test abort |
| AC-5.15.4 | N/A (Tech Debt) | Test Strategy → Epic 4 Test Debt | E2E tests in `frontend/e2e/tests/chat/`, `generation/` | E2E: Test chat UI, generation modal, draft editor, export |
| AC-5.15.5 | N/A (Tech Debt) | Test Strategy → CI/CD | GitHub Actions workflow, Epic 4 test job | CI: Run Epic 4 tests → verify < 10-minute execution |
| **Story 5.16: Docker E2E Infrastructure** |
| AC-5.16.1 | N/A (Tech Debt) | Dependencies → Docker Compose | docker-compose.e2e.yml with 7 services | Manual: docker-compose -f e2e.yml up → verify all services healthy |
| AC-5.16.2 | N/A (Tech Debt) | Test Strategy → Test Fixtures | seed-e2e-data.sh script | Manual: Run seed script → verify 3 users, 5 KBs, 20 docs created |
| AC-5.16.3 | N/A (Tech Debt) | Test Strategy → E2E Tests | playwright.config.ts baseURL=`http://frontend:3000` | E2E: Run Playwright → verify tests connect to frontend service |
| AC-5.16.4 | N/A (Tech Debt) | Test Strategy → E2E Tests | 15-20 E2E tests covering Epic 3 & 4 user journeys | E2E: Run all E2E tests → verify login, upload, search, chat, export |
| AC-5.16.5 | N/A (Tech Debt) | Test Strategy → CI/CD | GitHub Actions workflow, E2E test job with docker-compose | CI: Run E2E on PR → verify failures block merge |
| **Story 5.18: User Management UI** |
| AC-5.18.1 | FR5 | Detailed Design → Frontend Routes (Story 5.18) | UserManagementPage, UserTable, useUsers hook | Integration: GET `/admin/users` → verify paginated user list |
| AC-5.18.2 | FR5 | Detailed Design → APIs (Story 5.18) | CreateUserModal, POST `/api/v1/admin/users` | Unit: Submit form → verify API call, toast notification |
| AC-5.18.3 | FR5 | Detailed Design → APIs (Story 5.18) | EditUserModal, PATCH `/api/v1/admin/users/{id}` | Unit: Edit user → verify API call, self-deactivation warning |
| AC-5.18.4 | FR5, FR56 | NFR Security (User Management) | UserTable status toggle, AuditService | Integration: Toggle status → verify `is_active` updated, audit logged |
| AC-5.18.5 | FR5 | Detailed Design → Frontend Routes (Story 5.18) | main-nav.tsx with "Users" link | E2E: Click Users nav → verify `/admin/users` route |
| AC-5.18.6 | FR5 | NFR Security (Admin Access Control) | AdminGuard, require_admin dependency | Integration: Non-admin → verify 403 Forbidden |
| **Story 5.19: Group Management** |
| AC-5.19.1 | FR6 | Detailed Design → Data Models (Groups) | Group, user_groups tables, alembic migration | Integration: Run migration → verify tables created, API endpoints work |
| AC-5.19.2 | FR6 | Detailed Design → Frontend Routes (Story 5.19) | GroupManagementPage, GroupTable, useGroups hook | Integration: GET `/admin/groups` → verify list with member counts |
| AC-5.19.3 | FR6 | Detailed Design → APIs (Story 5.19) | GroupModal, POST/PATCH `/api/v1/admin/groups` | Unit: Create/edit group → verify unique name validation |
| AC-5.19.4 | FR6, FR56 | Detailed Design → APIs (Story 5.19) | GroupMembershipModal, POST/DELETE membership endpoints | Integration: Add/remove member → verify member list updated, audit logged |
| AC-5.19.5 | FR6 | Detailed Design → Frontend Routes (Story 5.19) | main-nav.tsx with "Groups" link | E2E: Click Groups nav → verify `/admin/groups` route |
| AC-5.19.6 | FR6 | NFR Security (Admin Access Control) | require_admin dependency on all group endpoints | Integration: Non-admin → verify 403 Forbidden |
| **Story 5.20: KB Permission Management** |
| AC-5.20.1 | FR6, FR7 | Detailed Design → Frontend Routes (Story 5.20) | KBPermissionsTab, PermissionTable components | E2E: View KB → click Permissions tab → verify user/group tables |
| AC-5.20.2 | FR6, FR7 | Detailed Design → APIs (Story 5.20) | AddPermissionModal, POST `/kb/{id}/permissions` | Unit: Add permission → verify entity picker, level dropdown |
| AC-5.20.3 | FR6, FR7, FR56 | Detailed Design → APIs (Story 5.20) | Permission edit/delete, AuditService | Integration: Edit/remove permission → verify changes, audit logged |
| AC-5.20.4 | FR6, FR7 | Detailed Design → Services (KBPermissionService) | Effective permissions display, group inheritance | Integration: User in group with KB access → verify "via [Group]" indicator |
| AC-5.20.5 | FR6, FR7 | Detailed Design → APIs (Story 5.20) | POST endpoint accepts user_id XOR group_id | Integration: POST with both → verify 400, POST with one → verify success |
| AC-5.20.6 | FR6, FR7 | Detailed Design → Frontend Routes (Story 5.20) | KB detail navigation includes Permissions tab | E2E: View KB detail → verify Permissions tab visible to admins |
| **Story 5.21: Theme System** |
| AC-5.21.1 | N/A (UX Polish) | Detailed Design → Data Models (Theme Type) | globals.css with 5 theme classes, CSS variables | Manual: Apply each theme → verify consistent styling |
| AC-5.21.2 | N/A (UX Polish) | Detailed Design → Frontend Routes | ThemeSelector in user-menu.tsx, DropdownMenuSub | Unit: Open user menu → verify theme submenu with 5 options |
| AC-5.21.3 | N/A (UX Polish) | Detailed Design → Services (ThemeStore) | Zustand store with persist middleware | Unit: Select theme → refresh page → verify theme preserved |
| AC-5.21.4 | N/A (UX Polish) | NFR Performance (Theme System) | All shadcn/ui components using CSS variables | E2E: Apply each theme → verify no mismatched colors in UI |
| **Story 5.25: Document Chunk Viewer - Backend API** |
| AC-5.25.1 | FR8c (Citations) | Detailed Design → Services (ChunkService) | ChunkService.get_document_chunks(), GET `/documents/{id}/chunks` | Integration: Upload doc → process → GET chunks → verify metadata (chunk_index, char_start, char_end, page_number) |
| AC-5.25.2 | FR8c (Citations) | Detailed Design → APIs (Documents) | ChunkService search filtering, case-insensitive | Integration: GET chunks?search=keyword → verify only matching chunks returned |
| AC-5.25.3 | FR8c (Citations) | Detailed Design → APIs (Documents) | ChunkService pagination, skip/limit params | Integration: GET chunks?skip=0&limit=50 → verify pagination with 500+ chunks |
| AC-5.25.4 | FR8c (Citations) | Detailed Design → APIs (Documents) | GET `/documents/{id}/content`, MinIO streaming | Integration: GET content → verify binary integrity, correct Content-Type |
| AC-5.25.5 | FR8c (Citations) | Detailed Design → Services (DocumentService) | mammoth DOCX→HTML conversion | Integration: GET content?format=html → verify valid HTML structure |
| AC-5.25.6 | FR7 (Permissions) | NFR Security (KB Permissions) | KB READ permission check on chunk/content endpoints | Integration: Non-member GET chunks → verify 403; missing doc → 404 |
| **Story 5.26: Document Chunk Viewer - Frontend UI** |
| AC-5.26.1 | FR8c (Citations) | Detailed Design → Frontend Routes (Story 5.26) | DocumentDetailModal tabs, "View & Chunks" tab | E2E: Open document → click "View & Chunks" tab → verify viewer loads |
| AC-5.26.2 | FR8c (Citations) | Detailed Design → Frontend Routes (Story 5.26) | react-resizable-panels, DocumentChunkViewer | Unit: Render viewer → verify 60/40 split-pane, resize handle |
| AC-5.26.3 | FR8c (Citations) | Detailed Design → Frontend Routes (Story 5.26) | ChunkSidebar with search, count, virtual scroll | Unit: Render sidebar → verify search box, count, scrollable list |
| AC-5.26.4 | FR8c (Citations) | Detailed Design → Frontend Routes (Story 5.26) | ChunkItem expand/collapse behavior | Unit: Click chunk → verify full text; click collapse → verify 3-line preview |
| AC-5.26.5 | FR8c (Citations) | Detailed Design → Frontend Routes (Story 5.26) | useDebounce for search input, 300ms delay | Unit: Type in search → verify 300ms debounce before filter |
| AC-5.26.6 | FR8c (Citations) | Detailed Design → Frontend Routes (Story 5.26) | PDFViewer with react-pdf, page navigation, text layer | E2E: View PDF → select chunk → verify page scroll and highlight |
| AC-5.26.7 | FR8c (Citations) | Detailed Design → Frontend Routes (Story 5.26) | DOCXViewer with docx-preview, paragraph highlighting | E2E: View DOCX → select chunk → verify paragraph highlight |
| AC-5.26.8 | FR8c (Citations) | Detailed Design → Frontend Routes (Story 5.26) | MarkdownViewer with react-markdown, char highlighting | E2E: View MD → select chunk → verify character range highlight |
| AC-5.26.9 | FR8c (Citations) | Detailed Design → Frontend Routes (Story 5.26) | TextViewer with pre-formatted display, char highlighting | E2E: View TXT → select chunk → verify character range highlight |
| AC-5.26.10 | FR8c (Citations) | Detailed Design → Frontend Routes (Story 5.26) | Loading skeletons, error states, empty states | Unit: Test loading/error/empty states → verify appropriate UI |
| **Cross-Cutting Criteria** |
| AC-X.1 | FR47-52 | NFR Security (Admin Access Control) | All `/api/v1/admin/*` endpoints, `require_admin` dependency | Integration: Non-admin GET any admin endpoint → verify 403 |
| AC-X.2 | FR8a-c | System Architecture Alignment | All Epic 5 features inherit citation-first architecture | E2E: Search → Generate → verify citations in draft |
| AC-X.3 | N/A (Architecture) | Detailed Design → APIs (Response schemas) | All API responses use PaginatedResponse, ErrorResponse | Unit: Call any Epic 5 endpoint → verify schema matches conventions |
| AC-X.4 | N/A (Architecture) | Detailed Design → Frontend Routes | All frontend components use shadcn/ui, Tailwind theme | E2E: Load any Epic 5 page → verify design system consistency |
| AC-X.5 | N/A (Architecture) | Detailed Design → Data Models | All Alembic migrations have upgrade/downgrade | Manual: alembic upgrade → downgrade → verify reversibility |

**Notes on Traceability:**
- **PRD FR References**: FR47-52 (Admin features), FR58 (User polish features), FR8a-c (Search from Epic 3), FR12b-d (Chat/Generation from Epic 4)
- **Tech Debt Stories**: No direct PRD FRs; trace to original Epic 3/4 stories and quality goals
- **Story 5.0**: Critical integration story traces to multiple Epic 3 & 4 FRs (FR8a-c, FR12b-d)
- **Test Strategy**: Integration tests verify backend behavior, E2E tests verify user workflows, unit tests verify component logic

## Risks, Assumptions, Open Questions

### Risks

**RISK-5.1: Story 5.0 Integration Gap May Reveal Additional Missing Wiring**
- **Description**: While Epic 3 & 4 backend implementations are complete, there may be additional UI navigation or state management gaps beyond the identified chat route issue.
- **Likelihood**: Medium
- **Impact**: Medium (could delay Story 5.0 completion)
- **Mitigation**:
  - Perform comprehensive smoke testing of all Epic 3 & 4 user journeys during Story 5.0
  - Document any additional gaps as sub-tasks
  - Budget 1-2 days for unexpected integration work

**RISK-5.2: ATDD Test Transition May Uncover Real Bugs**
- **Description**: Transitioning 78 integration tests (31 Epic 3 + 47 Epic 4) from skipped/xfail to passing may reveal actual bugs in Epic 3 & 4 implementations.
- **Likelihood**: Medium-High
- **Impact**: High (could require bug fixes in "done" stories)
- **Mitigation**:
  - Treat Stories 5.12 and 5.15 as hardening stories, not just test cleanup
  - Budget time for bug fixes discovered during test transition
  - Document bugs as technical debt items with clear Epic traceability
  - Consider creating hotfix stories if bugs are critical

**RISK-5.3: Docker E2E Infrastructure May Have Environment-Specific Issues**
- **Description**: E2E tests passing locally may fail in CI/CD due to Docker networking, timing, or resource constraints.
- **Likelihood**: Medium
- **Impact**: Medium (could delay Story 5.16)
- **Mitigation**:
  - Test docker-compose.e2e.yml locally before CI integration
  - Use health checks and wait-for scripts to handle service startup timing
  - Implement retry logic in Playwright for transient failures
  - Run E2E tests in CI early and often to catch issues

**RISK-5.4: Admin Dashboard Stats Queries May Impact Database Performance**
- **Description**: Aggregating system-wide statistics (users, KBs, documents, search/generation metrics) may create expensive queries on large datasets.
- **Likelihood**: Low (MVP scale unlikely to hit limits)
- **Impact**: Medium (could slow down admin dashboard)
- **Mitigation**:
  - Implement 5-minute Redis caching (AC-5.1.4)
  - Use indexed columns for all aggregate queries
  - Monitor query performance in observability dashboards
  - Consider materialized views for Stats if performance degrades at scale

**RISK-5.5: Celery Beat Filesystem Fix May Require Container Rebuild**
- **Description**: Fixing celerybeat-schedule file permissions may require Dockerfile changes and container rebuilds.
- **Likelihood**: Low
- **Impact**: Low (Story 5.13 is small in scope)
- **Mitigation**:
  - Test fix in local Docker environment first
  - Document rollback procedure if volume mount causes issues
  - Verify no impact on other Celery services (worker, beat)

**RISK-5.6: Onboarding Wizard May Interrupt Power Users**
- **Description**: Wizard shown to all new users may annoy experienced users who don't need onboarding.
- **Likelihood**: Low
- **Impact**: Low (UX friction)
- **Mitigation**:
  - Provide prominent "Skip Onboarding" button (AC-5.7.2)
  - Never show wizard to users with `onboarding_completed=true`
  - Consider user feedback for future iterations

**RISK-5.7: Group Permission Inheritance May Create Complex Authorization Scenarios**
- **Description**: When users belong to multiple groups with different permission levels for the same KB, determining effective permission may be complex.
- **Likelihood**: Medium
- **Impact**: Medium (could lead to unexpected access or denial)
- **Mitigation**:
  - Implement "highest permission wins" rule for group inheritance
  - Direct user permissions always override group permissions
  - Display "via [Group Name]" indicator for inherited permissions (AC-5.20.4)
  - Log all permission checks for debugging

**RISK-5.8: User Management Self-Deactivation Prevention May Be Bypassed**
- **Description**: Admin could attempt to deactivate their own account through API directly, bypassing UI protection.
- **Likelihood**: Low
- **Impact**: Medium (admin locked out)
- **Mitigation**:
  - Implement server-side check preventing self-deactivation
  - Return 400 error with clear message if attempted
  - UI also prevents this action (AC-5.18.3)

**RISK-5.9: Theme CSS Variables May Not Cover All Components**
- **Description**: Some third-party or custom components may not use CSS variables, causing color mismatches with theme changes.
- **Likelihood**: Low
- **Impact**: Low (visual inconsistency)
- **Mitigation**:
  - Audit all components during Story 5.21 implementation
  - Document any components requiring manual theming
  - Test all themes against all pages before marking complete

### Assumptions

**ASSUMPTION-5.1: Epic 3 & 4 Backend Services Are Production-Ready**
- Epic 3 (Semantic Search) and Epic 4 (Chat & Generation) backend implementations are assumed to be fully functional and production-ready.
- Validation: Story 5.0 smoke tests will verify this assumption.
- Fallback: If major issues found, create hotfix stories in Epic 5.

**ASSUMPTION-5.2: Recharts Library Is Sufficient for Dashboard Sparklines**
- Recharts is assumed to support the sparkline visualizations needed for admin dashboard trends (searches/generations over 30 days).
- Validation: Prototype sparkline during Story 5.1 implementation.
- Fallback: Use lightweight alternative (chart.js, victory) if recharts is too heavy.

**ASSUMPTION-5.3: PostgreSQL Audit Table Can Handle High Write Volume**
- The `audit.events` table is assumed to handle high write throughput for search audit logging (Story 5.14) without impacting query performance.
- Validation: Monitor table size and query performance during Story 5.14.
- Fallback: Implement table partitioning by date if performance degrades.

**ASSUMPTION-5.4: Celery Inspect API Provides Sufficient Queue Monitoring**
- Celery's `control.inspect()` API is assumed to provide real-time queue depth, task status, and worker health metrics.
- Validation: Test Celery inspect API during Story 5.4 implementation.
- Fallback: Query Redis directly for queue depths if inspect API is unreliable.

**ASSUMPTION-5.5: LiteLLM API Is Stable for E2E Tests**
- E2E tests (Story 5.16) assume LiteLLM API is available and stable for real streaming tests.
- Validation: Test LiteLLM connectivity in docker-compose.e2e.yml.
- Fallback: Use mock LLM responses for E2E tests if LiteLLM is unavailable in CI.

**ASSUMPTION-5.6: Users Have Docker Installed for E2E Testing**
- Developers are assumed to have Docker and Docker Compose installed locally for running E2E tests.
- Validation: Document E2E setup requirements in README.
- Fallback: Provide cloud-based E2E test environment (future enhancement).

**ASSUMPTION-5.7: KB Recommendation Algorithm Is Simple Heuristic**
- Smart KB suggestions (Story 5.8) use simple scoring (recent_access_count, search_relevance, shared_access) rather than ML-based recommendations.
- Validation: User feedback on recommendation quality.
- Fallback: Enhance algorithm in future epic if recommendations are poor.

**ASSUMPTION-5.8: Backend User Management Endpoints Already Exist**
- Story 5.18 assumes backend user management endpoints (GET/POST/PATCH `/api/v1/admin/users`) were implemented in Story 1.6.
- Validation: Verify endpoints exist and match expected request/response schemas.
- Fallback: Create missing endpoints as sub-tasks of Story 5.18.

**ASSUMPTION-5.9: Group-Based Permissions Use Highest Permission Wins**
- When a user belongs to multiple groups with different KB permissions, the highest permission level applies.
- Validation: Test multi-group scenarios during Story 5.20.
- Fallback: Document behavior clearly; refine if user feedback indicates confusion.

**ASSUMPTION-5.10: Theme System Uses Client-Side Only Storage**
- Theme preferences stored in localStorage (not synced to server).
- Validation: Verify theme persists across sessions.
- Fallback: Add server-side user preference storage if cross-device sync is needed.

**ASSUMPTION-5.11: Story 5.21 Theme System Is Already Complete**
- Story 5.21 is marked DONE in epics.md, indicating implementation is complete.
- Validation: Verify all ACs are satisfied by existing code.
- Impact: If not complete, add remaining work to sprint backlog.

### Open Questions

**QUESTION-5.1: Should Admin Dashboard Include Real-Time Metrics?**
- **Context**: Current design uses 5-minute Redis cache for stats. Should admin dashboard include real-time metrics (e.g., live queue depth, active users)?
- **Impact**: Medium (affects Story 5.1 implementation)
- **Decision Needed By**: Story 5.1 implementation start
- **Options**:
  - Option A: Keep 5-minute cache (simpler, less load)
  - Option B: Add real-time metrics via WebSocket (more complex, better UX)
- **Recommendation**: Option A for MVP, revisit in future based on admin feedback.

**QUESTION-5.2: How Many E2E Tests Are Sufficient for Story 5.16?**
- **Context**: AC-5.16.4 specifies "15-20 E2E tests". Should we prioritize coverage (more tests) or depth (fewer, more comprehensive tests)?
- **Impact**: Medium (affects Story 5.16 scope)
- **Decision Needed By**: Story 5.16 planning
- **Options**:
  - Option A: 15 shallow tests covering all Epic 3 & 4 features
  - Option B: 20 deeper tests with edge cases and error scenarios
- **Recommendation**: Option A for MVP (breadth over depth), add deeper tests in future.

**QUESTION-5.3: Should Audit Log Export Include Excel Format?**
- **Context**: Story 5.3 specifies CSV and JSON export. Should we also support Excel (XLSX) for business users?
- **Impact**: Low (nice-to-have feature)
- **Decision Needed By**: Story 5.3 implementation
- **Options**:
  - Option A: CSV/JSON only (simpler, meets AC)
  - Option B: Add Excel export (requires openpyxl dependency)
- **Recommendation**: Option A for MVP, add Excel in future based on user requests.

**QUESTION-5.4: Should Onboarding Wizard Be Skippable Per-Step?**
- **Context**: Current design allows skipping entire wizard. Should users be able to skip individual steps?
- **Impact**: Low (UX refinement)
- **Decision Needed By**: Story 5.7 implementation
- **Options**:
  - Option A: Skip entire wizard only (simpler)
  - Option B: Skip individual steps (more flexible)
- **Recommendation**: Option A for MVP, revisit based on user feedback.

**QUESTION-5.5: Should Search Audit Logging Be Retroactive?**
- **Context**: Story 5.14 adds search audit logging. Should we backfill audit logs for past searches (if stored)?
- **Impact**: Low (historical data nice-to-have)
- **Decision Needed By**: Story 5.14 planning
- **Options**:
  - Option A: Log only new searches going forward (simpler)
  - Option B: Backfill audit logs from search history (if available)
- **Recommendation**: Option A. No historical search data is stored, so backfill is not applicable.

**QUESTION-5.6: Should E2E Tests Run on Every Commit or Only on PR?**
- **Context**: AC-5.16.5 specifies E2E tests run on PR. Should they also run on every commit to main?
- **Impact**: Medium (affects CI cost and feedback speed)
- **Decision Needed By**: Story 5.16 GitHub Actions setup
- **Options**:
  - Option A: PR only (faster feedback, lower cost)
  - Option B: PR + every commit to main (higher confidence, higher cost)
- **Recommendation**: Option A for MVP (PR only), revisit if main branch becomes unstable.

**QUESTION-5.7: What Is the Retention Policy for Audit Logs?**
- **Context**: Audit logs will grow over time. Should there be an automated archival/deletion policy?
- **Impact**: Low (future scalability concern)
- **Decision Needed By**: Before production deployment
- **Options**:
  - Option A: No retention policy (keep all logs)
  - Option B: Archive logs older than 90 days to cold storage
  - Option C: Delete logs older than 1 year
- **Recommendation**: Defer to future epic. Document in admin documentation that logs are retained indefinitely for MVP.

**QUESTION-5.8: Should Group Management Support Nested Groups?**
- **Context**: Story 5.19 creates flat groups. Should groups be nestable (group can contain groups)?
- **Impact**: High (significantly increases complexity)
- **Decision Needed By**: Story 5.19 planning
- **Options**:
  - Option A: Flat groups only (simpler, covers 80% use cases)
  - Option B: Nested groups with inheritance
- **Recommendation**: Option A for MVP. Nested groups add significant complexity; revisit in future if enterprise customers require it.

**QUESTION-5.9: Should KB Permissions Support Time-Based Expiration?**
- **Context**: Story 5.20 creates persistent KB permissions. Should permissions support expiration dates (e.g., contractor access)?
- **Impact**: Medium (adds UI and backend complexity)
- **Decision Needed By**: Story 5.20 planning
- **Options**:
  - Option A: No expiration (simpler, admin manually revokes)
  - Option B: Optional expiration date field
- **Recommendation**: Option A for MVP. Document that admin must manually revoke temporary access.

**QUESTION-5.10: How Many Themes Are Sufficient for Story 5.21?**
- **Context**: Story 5.21 adds Light Blue and Dark Navy themes. Should more themes be added?
- **Impact**: Low (UX polish)
- **Decision Needed By**: Story 5.21 implementation
- **Options**:
  - Option A: 5 themes (Light, Dark, Light Blue, Dark Navy, System) as specified
  - Option B: Allow user-customizable themes (advanced feature)
- **Recommendation**: Option A. 5 themes provide variety without overwhelming users. User-customizable themes deferred to future.

## Test Strategy Summary

Epic 5 employs a comprehensive testing strategy across unit, integration, and E2E test levels. The strategy emphasizes transitioning existing ATDD tests to green (Stories 5.12, 5.15), establishing Docker-based E2E infrastructure (Story 5.16), and ensuring new admin/user features have adequate test coverage.

### Test Levels and Coverage Targets

| Test Level | Framework | Target Coverage | Stories |
|------------|-----------|----------------|---------|
| **Unit Tests** | pytest (backend), vitest (frontend) | ≥90% for new code | 5.1-5.11, 5.18-5.21 |
| **Integration Tests** | pytest + httpx (backend), vitest + RTL (frontend) | 100% of ACs covered | 5.1-5.9, 5.12, 5.14, 5.15, 5.18-5.20 |
| **E2E Tests** | Playwright + Docker Compose | 15-20 critical user journeys | 5.0, 5.16, 5.18-5.20 |
| **Manual Tests** | Smoke tests, exploratory testing | Story 5.0 smoke tests (4 journeys), theme verification | 5.0, 5.21 |

---

### Story-Specific Test Strategies

#### **Story 5.0: Epic 3 & 4 Integration Completion (CRITICAL)**

**Test Approach**: Manual smoke testing + exploratory testing

**Manual Smoke Tests** (AC-5.0.6):
1. **Journey 1**: Login → Upload document → Wait for processing → Navigate to Search → Query → Verify results with citations
2. **Journey 2**: Login → Click "Search KB" card from dashboard → Perform search → Click citation → Verify preview modal
3. **Journey 3**: Login → Click "Chat" card from dashboard → Send message → Verify streaming response with citations
4. **Journey 4**: Login → Search → Click "Generate Document" → Select template → Verify streaming draft → Edit → Export to DOCX

**Service Connectivity Tests**:
- Integration test: GET `/health` endpoint → verify all services return "ok" status
- Manual verification: Check Celery workers, Qdrant, Redis, MinIO, LiteLLM connectivity via logs

**Acceptance**:
- All 4 smoke test journeys complete without errors
- No 404 errors when navigating to `/chat`, `/search`
- Dashboard navigation cards visible and functional

---

#### **Story 5.1: Admin Dashboard Overview**

**Unit Tests** (Backend):
- `test_admin_stats_service.py`:
  - `test_get_dashboard_stats()` → Mock DB queries, verify aggregation logic
  - `test_get_activity_metrics()` → Mock audit.events queries, verify 24h/7d/30d counts
  - `test_cache_stats()` → Verify Redis caching with 5-minute TTL
  - `test_non_admin_forbidden()` → Verify 403 for non-admin users

**Unit Tests** (Frontend):
- `admin-dashboard.test.tsx`:
  - Render dashboard with mock stats data
  - Verify sparkline charts render (recharts)
  - Verify metric cards display correct values
  - Verify loading/error states

**Integration Tests**:
- `test_admin_dashboard_api.py`:
  - GET `/api/v1/admin/stats` → Verify response schema matches AdminStats
  - First call → DB hit, second call → cache hit (verify Redis TTL)
  - Non-admin user → 403 Forbidden

**E2E Tests**:
- `admin-dashboard.spec.ts`:
  - Login as admin → Navigate to `/admin` → Verify dashboard loads
  - Verify sparkline SVG elements rendered
  - Verify stats update after 5 minutes (cache expiry)

**Coverage Target**: ≥90% unit test coverage for AdminStatsService

---

#### **Story 5.2/5.3: Audit Log Viewer/Export**

**Unit Tests** (Backend):
- `test_audit_service.py`:
  - `test_query_audit_logs()` → Verify filtering by date_range, user_id, action_type, resource_type
  - `test_redact_pii()` → Verify email masked, IP anonymized
  - `test_export_audit_logs()` → Verify CSV/JSON streaming without OOM

**Integration Tests**:
- `test_audit_log_api.py`:
  - POST `/api/v1/admin/audit/logs` with filters → Verify paginated results
  - POST `/api/v1/admin/audit/export` → Verify CSV/JSON format, streaming response
  - Query 10,000 records → Verify < 30s timeout
  - Filter by date_range → Verify results sorted DESC

**E2E Tests**:
- `audit-log-viewer.spec.ts`:
  - Login as admin → Navigate to `/admin/audit`
  - Apply filters (date range, event type) → Verify filtered results
  - Click "Export CSV" → Verify file download with correct headers
  - Verify PII redaction in default view

**Coverage Target**: ≥90% unit test coverage for AuditService export methods

---

#### **Story 5.4: Processing Queue Status**

**Unit Tests** (Backend):
- `test_queue_monitor_service.py`:
  - `test_get_queue_status()` → Mock Celery inspect, verify queue depths
  - `test_detect_offline_workers()` → Mock no heartbeat 60s, verify "offline" status
  - `test_celery_inspect_failure()` → Verify graceful degradation to "unavailable"

**Integration Tests**:
- `test_queue_status_api.py`:
  - GET `/api/v1/admin/queue/status` → Verify 3 queues returned (document_processing, embedding_generation, export_generation)
  - GET `/api/v1/admin/queue/{queue_name}/tasks` → Verify task details
  - Stop Celery worker → Verify worker marked "offline"

**Coverage Target**: ≥85% unit test coverage for QueueMonitorService

---

#### **Story 5.5/5.6: System Configuration & KB Statistics**

**Unit Tests** (Backend):
- `test_config_service.py`:
  - `test_get_config()` → Verify all keys returned
  - `test_update_config()` → Verify validation, audit logging
  - `test_encrypt_sensitive()` → Verify secrets encrypted at rest
  - `test_redact_sensitive()` → Verify secrets redacted in GET response

**Integration Tests**:
- `test_config_api.py`:
  - PUT `/api/v1/admin/config/{key}` with valid value → Verify updated
  - PUT with invalid value → Verify 400 with validation errors
  - Verify audit event created with old/new values

**Coverage Target**: ≥90% unit test coverage for ConfigService, KBStatsService

---

#### **Story 5.7-5.9: User Experience Polish**

**Unit Tests** (Frontend):
- `onboarding-wizard.test.tsx`:
  - Render wizard for new user → Verify 3 steps displayed
  - Click "Skip" → Verify onboarding_completed=true
  - Complete wizard → Verify "My First KB" created
- `kb-recommendations.test.tsx`:
  - Render recommendations → Verify max 5 displayed
  - New user (cold start) → Verify popular KBs shown
- `recent-kbs.test.tsx`:
  - Render recent KBs → Verify last 5 displayed
  - Empty state → Verify message shown

**Integration Tests**:
- `test_onboarding_api.py`:
  - POST `/api/v1/users/me/onboarding/skip` → Verify onboarding_completed=true
  - Complete step 1 → logout → login → Verify step 2 shown
- `test_recommendations_api.py`:
  - GET `/api/v1/users/me/kb-recommendations` → Verify personalized results
  - First call → DB hit, second call → cache hit (1-hour TTL)

**Coverage Target**: ≥85% unit test coverage for user experience components

---

#### **Story 5.10: Command Palette Test Coverage Improvement**

**Test Approach**: Increase test coverage from current state to ≥90%

**Unit Tests** (Frontend):
- `use-command-palette.test.ts`:
  - Simulate Cmd+K → Verify palette opens
  - Simulate Escape → Verify palette closes
  - Execute "Search" command → Verify navigation to `/search`
  - Execute "Switch KB" command → Verify KB switched
- `command-palette.test.tsx`:
  - Render palette → Verify ARIA labels
  - Test keyboard navigation (arrow keys, Enter)
  - Run axe-core → Verify no accessibility violations

**Integration Tests**:
- `command-palette-integration.test.tsx`:
  - Open/close palette → Verify no React errors in console
  - Execute commands → Verify state updates correctly

**Acceptance**:
- Test coverage ≥90% for command palette components
- All accessibility tests pass (WCAG 2.1 AA)
- All tests pass in CI/CD pipeline

---

#### **Story 5.11: Epic 3 Search Hardening**

**Test Approach**: Add missing unit tests and accessibility tests for Epic 3 search components

**Unit Tests** (Frontend):
- `search-result-card.test.tsx`:
  - Render with mock data → Verify all props displayed
  - Click card → Verify navigation
  - Hover citation → Verify preview shown
- `citation-preview.test.tsx`:
  - Render preview modal → Verify citation text, source metadata
  - Close modal → Verify modal dismissed
- `search-page.test.tsx`:
  - Mock 500 error → Verify error boundary shows graceful message
  - Mock network timeout → Verify loading state, retry button

**Accessibility Tests**:
- Run axe-core on all search pages → Verify WCAG 2.1 AA compliance
- Test color contrast, ARIA labels, keyboard navigation

**Acceptance**:
- 15 unit tests pass (0 skipped)
- Test coverage ≥90% for search components
- All accessibility tests pass

---

#### **Story 5.12: ATDD Integration Tests Transition to Green (Epic 3)**

**Test Approach**: Transition 31 Epic 3 integration tests from skipped/xfail to passing

**Integration Tests** (Backend):
- `test_semantic_search.py`: 8 tests (semantic search API, embeddings, ranking)
- `test_cross_kb_search.py`: 6 tests (multi-KB search, deduplication)
- `test_llm_synthesis.py`: 7 tests (answer synthesis, citation extraction)
- `test_sse_streaming.py`: 5 tests (SSE streaming, progressive responses)
- `test_citation_security.py`: 5 tests (citation verification, access control)

**Test Fixtures**:
- Use real Qdrant, LiteLLM, PostgreSQL services (no mocks)
- Seed database with realistic data: 3 users, 5 KBs, 20 documents, 100 embeddings
- Cleanup after each test (no pollution)

**Acceptance**:
- All 31 tests pass without skips or xfails
- Tests run in CI/CD with < 5-minute execution time
- If bugs found, document as technical debt items

---

#### **Story 5.13: Celery Beat Filesystem Fix**

**Test Approach**: Integration testing + manual verification

**Integration Tests**:
- `test_celery_beat_scheduler.py`:
  - Start celerybeat → Verify schedule file created in `/app/celery-data/`
  - Wait for scheduled task → Verify task executed without errors
  - Restart celerybeat → Verify schedule file persists

**Manual Verification**:
- `docker logs celerybeat` → Verify "Beat scheduler initialized" message
- `docker exec celerybeat ls -l /app/celery-data/` → Verify non-root file ownership

**Acceptance**:
- No filesystem permission errors in logs
- Scheduled tasks execute successfully

---

#### **Story 5.14: Search Audit Logging**

**Test Approach**: Unit + integration testing for audit logging

**Unit Tests** (Backend):
- `test_audit_logging.py`:
  - `test_log_search_event()` → Verify query_text sanitized, kb_id captured
  - `test_log_failed_search()` → Verify status="failed", error_message logged
  - `test_fire_and_forget()` → Verify async logging, no await in request path

**Integration Tests**:
- `test_search_audit_api.py`:
  - POST `/api/v1/search` → Verify audit event created
  - POST invalid search → Verify audit log with failure
  - POST `/api/v1/admin/audit/logs` with event_type="search" → Verify search events returned
  - Measure search latency → Verify < 200ms (no degradation from logging)

**Acceptance**:
- All search API calls logged to audit.events
- Logging has no impact on search latency (< 200ms)

---

#### **Story 5.15: Epic 4 ATDD Tests Transition to Green**

**Test Approach**: Transition 47 Epic 4 integration tests from skipped/xfail to passing

**Integration Tests** (Backend):
- `test_chat_api.py`: 10 tests (chat conversation, multi-turn RAG)
- `test_chat_streaming.py`: 8 tests (SSE streaming, real-time citations)
- `test_conversation_management.py`: 7 tests (clear, undo, persistence)
- `test_generation_api.py`: 8 tests (document generation, templates)
- `test_generation_streaming.py`: 6 tests (progressive draft streaming, AbortController)
- `test_draft_editing.py`: 8 tests (draft editing, citation preservation)

**Test Fixtures**:
- Use real LiteLLM API for streaming tests (no mocks)
- Seed database with conversations, drafts, generation templates
- Cleanup after each test

**E2E Tests** (Frontend):
- `chat.spec.ts`: 5 tests (chat UI, streaming, citations)
- `generation.spec.ts`: 5 tests (generation modal, draft editor, export)

**Acceptance**:
- All 47 integration tests pass without skips or xfails
- E2E tests verify chat UI, generation modal, draft editor
- Tests run in CI/CD with < 10-minute execution time

---

#### **Story 5.16: Docker E2E Infrastructure**

**Test Approach**: Establish Docker-based E2E testing infrastructure

**Infrastructure Setup**:
- `docker-compose.e2e.yml`: 7 services (frontend, backend, postgres, redis, qdrant, minio, litellm)
- Database seeding: `seed-e2e-data.sh` (3 users, 5 KBs, 20 documents, 100 embeddings)
- Health checks: Wait-for-services script ensures all services ready before tests

**E2E Tests** (15-20 tests):
- **Epic 3 Tests** (`epic3-search.spec.ts`):
  - Login → Upload document → Search → Verify results with citations (AC-5.0.6)
  - Cross-KB search → Verify results from multiple KBs
  - Citation preview → Verify source document displayed
  - Quick search (Cmd+K) → Verify command palette opens, search executes
  - Relevance explanation → Verify explanation modal
- **Epic 4 Tests** (`epic4-chat-generation.spec.ts`):
  - Chat conversation → Verify streaming responses with citations (AC-5.0.6)
  - Multi-turn chat → Verify conversation persistence
  - Document generation → Verify generation modal, template selection
  - Draft editing → Verify editor loads, citation preservation
  - Document export → Verify DOCX export dialog, file download

**GitHub Actions CI**:
- `.github/workflows/e2e-tests.yml`:
  - Trigger: On PR to main
  - Steps: docker-compose up → seed → playwright test → docker-compose down
  - Failure handling: Block merge if E2E tests fail

**Acceptance**:
- All 15-20 E2E tests pass locally and in CI
- Tests execute in < 10 minutes
- Docker environment stable across local and CI

---

#### **Story 5.18: User Management UI**

**Test Approach**: Unit + Integration + E2E testing

**Unit Tests** (Backend):
- `test_user_management.py`:
  - `test_list_users_paginated()` → Verify pagination, sorting, filtering
  - `test_create_user_validation()` → Verify email, password validation
  - `test_prevent_self_deactivation()` → Verify 400 error for self-deactivation
  - `test_admin_only_access()` → Verify 403 for non-admin users

**Unit Tests** (Frontend):
- `user-table.test.tsx`:
  - Render with mock users → Verify columns, sorting, filtering
  - Click edit → Verify modal opens with user data
- `create-user-modal.test.tsx`:
  - Submit valid form → Verify API call, success toast
  - Submit invalid form → Verify inline validation errors
- `edit-user-modal.test.tsx`:
  - Toggle status → Verify API call, optimistic UI update
  - Edit own account → Verify deactivation warning

**Integration Tests**:
- `test_user_management_api.py`:
  - POST `/api/v1/admin/users` with valid data → Verify 201, user created
  - PATCH `/api/v1/admin/users/{id}` → Verify status/role updated
  - Non-admin user → Verify 403 Forbidden

**E2E Tests**:
- `admin-users.spec.ts`:
  - Login as admin → Navigate to `/admin/users` → Verify user list
  - Create new user → Verify appears in list
  - Edit user status → Verify toggle works

**Acceptance**:
- All unit tests pass (≥90% coverage)
- Integration tests cover all ACs
- E2E tests verify happy path

---

#### **Story 5.19: Group Management**

**Test Approach**: Unit + Integration + E2E testing

**Unit Tests** (Backend):
- `test_group_service.py`:
  - `test_create_group()` → Verify group created, member count initialized
  - `test_update_group()` → Verify name/description update
  - `test_unique_group_name()` → Verify 400 for duplicate names
  - `test_add_remove_members()` → Verify membership operations
  - `test_soft_delete_group()` → Verify is_active=false, not hard deleted

**Unit Tests** (Frontend):
- `group-table.test.tsx`:
  - Render with mock groups → Verify columns, member count
  - Click row → Verify member list expands
- `group-modal.test.tsx`:
  - Submit valid form → Verify API call
  - Duplicate name → Verify validation error
- `group-membership-modal.test.tsx`:
  - Add member → Verify user added to list
  - Remove member → Verify user removed from list

**Integration Tests**:
- `test_group_api.py`:
  - POST `/api/v1/admin/groups` → Verify 201, group created
  - POST `/api/v1/admin/groups/{id}/members` → Verify members added
  - DELETE `/api/v1/admin/groups/{id}/members/{user_id}` → Verify member removed
  - Non-admin user → Verify 403 Forbidden

**E2E Tests**:
- `admin-groups.spec.ts`:
  - Login as admin → Navigate to `/admin/groups` → Verify group list
  - Create group → Add members → Verify member count updates

**Acceptance**:
- All unit tests pass (≥90% coverage)
- Migration creates tables correctly
- All ACs covered by tests

---

#### **Story 5.20: KB Permission Management UI**

**Test Approach**: Unit + Integration + E2E testing

**Unit Tests** (Backend):
- `test_kb_permission_service.py`:
  - `test_add_user_permission()` → Verify direct permission created
  - `test_add_group_permission()` → Verify group permission created
  - `test_effective_permissions()` → Verify group inheritance logic
  - `test_highest_permission_wins()` → Verify multi-group resolution
  - `test_direct_overrides_group()` → Verify direct permissions take precedence
  - `test_prevent_duplicate()` → Verify 400 for duplicate permission

**Unit Tests** (Frontend):
- `kb-permissions-tab.test.tsx`:
  - Render with mock permissions → Verify user/group tables
  - Verify "via [Group Name]" indicator for inherited permissions
- `add-permission-modal.test.tsx`:
  - Select user → Verify user picker works
  - Select group → Verify group dropdown works
  - Duplicate permission → Verify validation error

**Integration Tests**:
- `test_kb_permission_api.py`:
  - POST `/kb/{id}/permissions` with user_id → Verify user permission created
  - POST `/kb/{id}/permissions` with group_id → Verify group permission created
  - POST with both user_id and group_id → Verify 400 error
  - GET permissions → Verify both user and group permissions returned
  - Permission check for user in group → Verify access granted

**E2E Tests**:
- `kb-permissions.spec.ts`:
  - Admin views KB → Clicks Permissions tab → Verifies tables
  - Add user permission → Verify appears in table
  - Add group permission → Verify appears in table

**Acceptance**:
- All unit tests pass (≥90% coverage)
- Group permission inheritance works correctly
- All ACs covered by tests

---

#### **Story 5.21: Theme System**

**Test Approach**: Unit + Manual testing

**Unit Tests** (Frontend):
- `theme-selector.test.tsx`:
  - Render submenu → Verify 5 theme options
  - Click theme → Verify theme applied immediately
  - Verify checkmark on current theme
- `theme-store.test.ts`:
  - Select theme → Verify localStorage persisted
  - Refresh page → Verify theme hydrated from localStorage
  - System theme → Verify follows OS preference

**Manual Tests**:
- Apply each theme → Verify all components styled correctly
- Check all pages → Verify no white/mismatched boxes
- Test contrast → Verify text readable on all backgrounds

**Accessibility Tests**:
- Run axe-core on each theme → Verify WCAG color contrast requirements met

**Acceptance**:
- All unit tests pass
- Manual verification of all 5 themes
- No color contrast violations

---

#### **Story 5.25: Document Chunk Viewer - Backend API**

**Test Approach**: Unit + Integration testing

**Unit Tests** (Backend):
- `test_chunk_service.py`:
  - `test_get_document_chunks()` → Query Qdrant, verify chunk structure
  - `test_search_filter()` → Verify case-insensitive text filtering
  - `test_pagination()` → Verify skip/limit logic with large datasets
  - `test_sort_by_chunk_index()` → Verify chunks sorted correctly
- `test_chunk_schemas.py`:
  - Validate `DocumentChunk` schema with all fields
  - Validate `DocumentChunksResponse` schema

**Integration Tests**:
- `test_document_chunks_api.py`:
  - GET `/documents/{id}/chunks` → Verify chunk metadata returned
  - GET with `?search=keyword` → Verify filtering works
  - GET with `?skip=0&limit=50` → Verify pagination
  - Non-member user → Verify 403 Forbidden
  - Missing document → Verify 404 Not Found
- `test_document_content_api.py`:
  - GET `/documents/{id}/content` for PDF → Verify binary streaming
  - GET `/documents/{id}/content` for DOCX → Verify binary streaming
  - GET `/documents/{id}/content` for MD/TXT → Verify text streaming
  - GET with `?format=html` for DOCX → Verify HTML conversion

**Acceptance**:
- All 5 unit tests pass
- All 9 integration tests pass
- No Ruff linting errors

---

#### **Story 5.26: Document Chunk Viewer - Frontend UI**

**Test Approach**: Unit + E2E testing

**Unit Tests** (Frontend):
- `document-chunk-viewer.test.tsx`:
  - Render split-pane layout → Verify 60/40 panels
  - Resize panels → Verify resize handle works
  - Test responsive stacking on mobile viewport
- `chunk-sidebar.test.tsx`:
  - Render search box → Verify input accepts text
  - Render chunk count → Verify correct count displayed
  - Test virtual scroll → Verify smooth scroll with 1000 items
- `chunk-item.test.tsx`:
  - Collapsed state → Verify 3-line preview with ellipsis
  - Expanded state → Verify full text displayed
  - Click expand/collapse → Verify toggle behavior
  - Accordion behavior → Verify only one expanded at a time
- `search-debounce.test.tsx`:
  - Type in search → Verify 300ms debounce delay
- `pdf-viewer.test.tsx`:
  - Render PDF document → Verify react-pdf canvas
  - Page navigation → Verify prev/next buttons
  - Highlight on chunk select → Verify text layer highlight
- `docx-viewer.test.tsx`:
  - Render DOCX document → Verify docx-preview output
  - Highlight paragraph on chunk select
- `markdown-viewer.test.tsx`:
  - Render Markdown → Verify react-markdown output
  - Highlight character range on chunk select
- `text-viewer.test.tsx`:
  - Render plain text → Verify pre-formatted display
  - Highlight character range on chunk select
- `use-document-chunks.test.tsx`:
  - Hook fetches chunks → Verify React Query behavior
  - Hook filters by search → Verify filtering logic
- `use-document-content.test.tsx`:
  - Hook fetches blob → Verify blob URL created
  - Hook cleans up → Verify blob URL revoked on unmount
- `loading-error-empty-states.test.tsx`:
  - Loading state → Verify skeleton displayed
  - Error state → Verify error message with retry button
  - Empty state → Verify "no chunks" message

**E2E Tests**:
- `document-chunk-viewer.spec.ts`:
  - Upload PDF → View chunks → Click chunk → Verify page highlight
  - Upload DOCX → View chunks → Click chunk → Verify paragraph highlight
  - Open viewer → Search chunks → Verify filtered results
  - Click chunk → Expand → Click collapse → Verify toggle

**Acceptance**:
- All 28 unit tests pass (≥90% coverage)
- All 4 E2E tests pass
- Virtual scroll performs smoothly with 1000+ chunks

---

### Test Execution Plan

#### **Phase 1: New Feature Tests (Stories 5.1-5.9)**
- **Duration**: Parallel with story implementation
- **Approach**: Write tests alongside feature development (TDD where applicable)
- **Acceptance**: All unit tests pass, integration tests pass, ≥90% coverage

#### **Phase 2: Test Coverage Improvement (Stories 5.10-5.11)**
- **Duration**: 1-2 days per story
- **Approach**: Identify coverage gaps, write missing tests, run coverage reports
- **Acceptance**: Coverage ≥90%, all accessibility tests pass

#### **Phase 3: ATDD Test Transition (Stories 5.12, 5.15)**
- **Duration**: 3-5 days per story (may uncover bugs)
- **Approach**: Fix test fixtures, transition tests to green, fix bugs if found
- **Acceptance**: 0 skipped/xfail tests, all 78 tests pass

#### **Phase 4: E2E Infrastructure (Story 5.16)**
- **Duration**: 3-4 days
- **Approach**: Build docker-compose.e2e.yml, seed data, write E2E tests, integrate with CI
- **Acceptance**: 15-20 E2E tests pass in CI, tests run on every PR

#### **Phase 5: User & Group Management Tests (Stories 5.18-5.20)**
- **Duration**: Parallel with story implementation (2-4 days per story)
- **Approach**: TDD for backend services, component tests for frontend
- **Acceptance**: All ACs covered by tests, group permission inheritance verified

#### **Phase 6: Theme System Verification (Story 5.21)**
- **Duration**: 0.5 days (already DONE, verification only)
- **Approach**: Verify existing implementation, add missing unit tests if needed
- **Acceptance**: Theme selector works, localStorage persistence works, no color mismatches

#### **Phase 7: Document Chunk Viewer (Stories 5.25-5.26)**
- **Duration**: 3-4 days (Story 5.25: 1 day, Story 5.26: 2-3 days)
- **Approach**: Backend-first development, then frontend implementation
- **Acceptance**: All 14 backend tests pass, all 32 frontend tests pass, E2E viewer workflows functional

---

### Test Automation and CI/CD Integration

**CI Pipeline** (`.github/workflows/epic5-tests.yml`):
```yaml
name: Epic 5 Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run backend unit tests
        run: pytest backend/tests/unit/ --cov=backend/app --cov-report=xml
      - name: Run backend integration tests
        run: pytest backend/tests/integration/ -v

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run frontend unit tests
        run: npm run test:unit -- --coverage
      - name: Run frontend integration tests
        run: npm run test:integration

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Start E2E environment
        run: docker-compose -f docker-compose.e2e.yml up -d
      - name: Wait for services
        run: ./scripts/wait-for-services.sh
      - name: Seed test data
        run: ./scripts/seed-e2e-data.sh
      - name: Run E2E tests
        run: npm run test:e2e
      - name: Teardown
        run: docker-compose -f docker-compose.e2e.yml down -v
```

**Test Metrics Tracked**:
- Test pass rate (target: 100%)
- Test coverage (target: ≥90% for new code)
- Test execution time (target: < 10 minutes for full suite)
- Flakiness rate (target: < 1% for E2E tests)

---

### Success Criteria

**Epic 5 Test Strategy Success** requires:
1. ✅ All 109 acceptance criteria have corresponding tests (unit, integration, or E2E) — updated from 93 with Stories 5.25-5.26
2. ✅ All 78 ATDD tests (31 Epic 3 + 47 Epic 4) transition to green (0 skipped/xfail)
3. ✅ 15-20 E2E tests pass in Docker-based CI/CD environment
4. ✅ Test coverage ≥90% for all new Epic 5 code
5. ✅ All accessibility tests pass (WCAG 2.1 AA compliance)
6. ✅ CI/CD pipeline runs all tests on every PR, blocks merge on failure
7. ✅ No critical bugs found during test transition (or bugs documented as hotfixes)
8. ✅ Document Chunk Viewer: 14 backend tests + 32 frontend tests pass (Stories 5.25-5.26)
