# Story 5-19: Group Management

## Story

**As an** administrator,
**I want** to create user groups and assign users to groups,
**So that** I can manage KB access permissions at the group level rather than individually per user.

## Status

| Field          | Value                                           |
| -------------- | ----------------------------------------------- |
| **Priority**   | MEDIUM                                          |
| **Points**     | 8                                               |
| **Sprint**     | Epic 5 - Administration & Polish               |
| **Owner**      | Amelia (Dev)                                    |
| **Support**    | Winston (Architect)                             |
| **Created**    | 2025-12-05                                      |
| **Status**     | done                                            |

## Context

Currently KB permissions are only assignable at the user level through the `kb_permissions` table (Story 2.2). This approach doesn't scale for enterprise deployments with many users who need similar access patterns.

Groups enable bulk permission management:
1. Create a group (e.g., "Engineering Team", "Marketing")
2. Assign KB access permissions to the group
3. Add/remove users from the group to manage access

This story focuses on group management (CRUD + membership). Story 5.20 will add the KB permission assignment UI for groups.

**Existing Infrastructure:**
- User model: `backend/app/models/user.py` - UUID-based users
- KB Permissions: `backend/app/models/knowledge_base.py` - `kb_permissions` table
- Admin endpoints pattern: `backend/app/api/v1/admin.py` - Established patterns from Story 1.6, 5.18
- Frontend admin pages: `frontend/src/app/(protected)/admin/users/page.tsx` - Reference for UI patterns

## Prerequisites

| Dependency    | Description                              | Status |
| ------------- | ---------------------------------------- | ------ |
| Story 5.18    | User Management UI                       | DONE   |
| Story 2.2     | Knowledge Base Permissions Backend       | DONE   |

## Acceptance Criteria

### AC-5.19.1: Group Model and API Created

**Given** the backend needs group management
**When** the migration is applied
**Then** a `groups` table exists with columns:
- id (UUID, PK)
- name (VARCHAR(255), unique, NOT NULL)
- description (TEXT, nullable)
- is_active (BOOLEAN, default true) - for soft delete
- created_at, updated_at timestamps

**And** a `user_groups` junction table exists:
- user_id (UUID, FK to users.id, ON DELETE CASCADE)
- group_id (UUID, FK to groups.id, ON DELETE CASCADE)
- created_at timestamp
- Primary key: (user_id, group_id)

**And** API endpoints exist:
- `GET /api/v1/admin/groups` - List all groups with pagination
- `POST /api/v1/admin/groups` - Create group
- `GET /api/v1/admin/groups/{id}` - Get group details with members
- `PATCH /api/v1/admin/groups/{id}` - Update group (name, description, is_active)
- `DELETE /api/v1/admin/groups/{id}` - Soft delete (sets is_active=false)
- `POST /api/v1/admin/groups/{id}/members` - Add users to group
- `DELETE /api/v1/admin/groups/{id}/members/{user_id}` - Remove user from group

**Technical Notes:**
- Use existing admin endpoint patterns from `backend/app/api/v1/admin.py`
- Endpoints require `current_superuser` dependency (admin-only)
- Paginated list response using `PaginatedResponse` schema
- Audit logging for all mutations (create, update, delete, member changes)

### AC-5.19.2: Group List Page Created

**Given** I am logged in as an admin (is_superuser=true)
**When** I navigate to /admin/groups
**Then** I see a table of all groups with columns:
- Name
- Description (truncated to 50 chars)
- Member count
- Status (Active/Inactive badge)
- Created date (formatted)

**And** I can search by group name (debounced, 300ms)
**And** clicking a row expands to show member list inline
**And** pagination shows 20 groups per page with navigation controls
**And** empty state shows "No groups found" message

**Technical Notes:**
- Use expandable row pattern (similar to command palette)
- Member count fetched from API (computed field)
- Follow existing table patterns from `user-table.tsx`

### AC-5.19.3: Create/Edit Group Modal Implemented

**Given** I am on the /admin/groups page
**When** I click "Create Group" button or edit action on a row
**Then** a modal appears with:
- Name field (required, max 255 chars)
- Description field (optional textarea)

**And** validation prevents:
- Empty name
- Duplicate group name (409 Conflict from API)
- Name exceeding 255 characters

**And** success shows toast notification and refreshes group list
**And** error displays validation message inline

**Technical Notes:**
- Use react-hook-form + zod validation
- Follow existing modal patterns from `create-user-modal.tsx`
- Handle 409 Conflict for duplicate names

### AC-5.19.4: Group Membership Management Implemented

**Given** I am viewing a group's expanded details (or dedicated management view)
**When** I click "Manage Members" button
**Then** I see a modal with:
- Current members list with email and "Remove" action per row
- "Add Members" button/section opening user picker

**And** the user picker allows:
- Search users by email (debounced)
- Multi-select users to add
- Only shows users not already in the group

**And** adding users:
- Calls `POST /api/v1/admin/groups/{id}/members` with user IDs
- Shows success toast with count added
- Refreshes member list immediately

**And** removing users:
- Calls `DELETE /api/v1/admin/groups/{id}/members/{user_id}`
- Shows confirmation dialog
- Refreshes member list immediately

**And** all membership changes are logged to audit.events with:
- event_type: "group.member_added" or "group.member_removed"
- event_data: { group_id, group_name, user_id, user_email }

**Technical Notes:**
- Use existing user search from `useUsers` hook
- Implement optimistic updates with rollback
- Fire-and-forget audit logging pattern

### AC-5.19.5: Admin Navigation Updated

**Given** I am an admin user (is_superuser=true)
**When** I view the admin navigation menu
**Then** I see a "Groups" link in the admin section
**And** clicking it navigates to /admin/groups
**And** the link shows active state when on groups page

**Technical Notes:**
- Add to existing admin tools section in `/admin/page.tsx`
- Add to MainNav admin section (extend Story 5.17 pattern)
- Use Users icon from lucide-react (or UserGroup if available)

### AC-5.19.6: Access Control Enforced

**Given** I am NOT an admin (is_superuser=false)
**When** I attempt to access /admin/groups directly
**Then** I am redirected to /dashboard with an error message
**And** API calls return 403 Forbidden

**Technical Notes:**
- Leverage existing AdminGuard from Story 5.18
- Backend uses `current_superuser` dependency

## Tasks

### Task 1: Create Group Model and Migration (AC: #1)

- [ ] 1.1 Create `backend/app/models/group.py` with Group and UserGroup models
- [ ] 1.2 Add Group to `backend/app/models/__init__.py` exports
- [ ] 1.3 Create alembic migration for groups and user_groups tables
- [ ] 1.4 Add appropriate indexes (groups.name, user_groups composite)
- [ ] **Testing:** Verify migration runs cleanly up and down

### Task 2: Create Group Schemas (AC: #1)

- [ ] 2.1 Create `backend/app/schemas/group.py` with:
  - GroupBase, GroupCreate, GroupUpdate, GroupRead
  - GroupMemberAdd (user_ids: list[UUID])
  - GroupWithMembers (includes member count and user list)
- [ ] 2.2 Add schemas to module exports
- [ ] **Testing:** Schema validation unit tests

### Task 3: Create GroupService (AC: #1, #4)

- [ ] 3.1 Create `backend/app/services/group_service.py` with:
  - list_groups(skip, limit, search) -> paginated
  - get_group(id) -> GroupWithMembers
  - create_group(data) -> Group
  - update_group(id, data) -> Group
  - delete_group(id) -> soft delete (is_active=false)
  - add_members(group_id, user_ids) -> count added
  - remove_member(group_id, user_id) -> bool
  - get_group_members(group_id) -> list[User]
- [ ] 3.2 Implement audit logging for all mutations
- [ ] 3.3 Handle duplicate name constraint (IntegrityError -> 409)
- [ ] **Testing:** Write 10-12 unit tests for GroupService

### Task 4: Create Group API Endpoints (AC: #1, #6)

- [ ] 4.1 Create `backend/app/api/v1/groups.py` with admin endpoints
- [ ] 4.2 Register router in `backend/app/main.py`
- [ ] 4.3 Implement all 7 endpoints with proper error handling
- [ ] 4.4 Add OpenAPI documentation (tags, descriptions)
- [ ] **Testing:** Write 8-10 integration tests for API endpoints

### Task 5: Create useGroups Hook (AC: #2, #3, #4)

- [ ] 5.1 Create `frontend/src/hooks/useGroups.ts` with React Query
- [ ] 5.2 Implement:
  - useGroups(page, search) -> paginated groups
  - useGroup(id) -> single group with members
  - createGroup mutation
  - updateGroup mutation
  - deleteGroup mutation
  - addMembers mutation
  - removeMember mutation
- [ ] 5.3 Implement optimistic updates for mutations
- [ ] **Testing:** Write 8-10 unit tests for useGroups hook

### Task 6: Create Group Types (AC: #2)

- [ ] 6.1 Create `frontend/src/types/group.ts` with TypeScript interfaces:
  - Group, GroupCreate, GroupUpdate, GroupWithMembers
  - GroupMember, GroupMemberAdd
- [ ] **Testing:** Type-checked via TypeScript strict mode

### Task 7: Create GroupTable Component (AC: #2)

- [ ] 7.1 Create `frontend/src/components/admin/group-table.tsx`
- [ ] 7.2 Implement columns: Name, Description, Member Count, Status, Created, Actions
- [ ] 7.3 Add expandable row with member list preview
- [ ] 7.4 Add search input with debounce (300ms)
- [ ] 7.5 Add pagination controls (20 per page)
- [ ] 7.6 Add empty state
- [ ] **Testing:** Write 6-8 component tests

### Task 8: Create CreateGroupModal Component (AC: #3)

- [ ] 8.1 Create `frontend/src/components/admin/create-group-modal.tsx`
- [ ] 8.2 Implement form with react-hook-form + zod
- [ ] 8.3 Add name validation (required, max 255)
- [ ] 8.4 Add description textarea (optional)
- [ ] 8.5 Handle 409 Conflict for duplicate name
- [ ] 8.6 Show toast on success
- [ ] **Testing:** Write 4-6 component tests

### Task 9: Create EditGroupModal Component (AC: #3)

- [ ] 9.1 Create `frontend/src/components/admin/edit-group-modal.tsx`
- [ ] 9.2 Pre-populate form with existing group data
- [ ] 9.3 Add status toggle (Active/Inactive) for soft delete
- [ ] 9.4 Handle validation and API errors
- [ ] **Testing:** Write 4-6 component tests

### Task 10: Create GroupMembershipModal Component (AC: #4)

- [ ] 10.1 Create `frontend/src/components/admin/group-membership-modal.tsx`
- [ ] 10.2 Display current members with email and remove action
- [ ] 10.3 Add user picker with search (uses useUsers hook)
- [ ] 10.4 Filter out users already in group
- [ ] 10.5 Support multi-select for bulk add
- [ ] 10.6 Add confirmation dialog for remove action
- [ ] 10.7 Implement optimistic updates
- [ ] **Testing:** Write 6-8 component tests

### Task 11: Create Groups Page (AC: #2, #5)

- [ ] 11.1 Create `frontend/src/app/(protected)/admin/groups/page.tsx`
- [ ] 11.2 Integrate GroupTable, CreateGroupModal, EditGroupModal, GroupMembershipModal
- [ ] 11.3 Add "Create Group" button
- [ ] 11.4 Wrap in DashboardLayout
- [ ] 11.5 Add URL state for search/page params
- [ ] **Testing:** Page tested via E2E

### Task 12: Update Admin Navigation (AC: #5)

- [ ] 12.1 Add "Groups" link to admin tools section in `/admin/page.tsx`
- [ ] 12.2 Add Groups icon (Users or UserGroup from lucide-react)
- [ ] 12.3 Update MainNav admin section with Groups link
- [ ] **Testing:** Navigation links verified manually + E2E

### Task 13: Write E2E Tests (AC: All)

- [ ] 13.1 Create `frontend/e2e/tests/admin/group-management.spec.ts`
- [ ] 13.2 Test: Admin can list groups
- [ ] 13.3 Test: Admin can create group
- [ ] 13.4 Test: Admin can edit group
- [ ] 13.5 Test: Admin can manage group members
- [ ] 13.6 Test: Non-admin redirected to dashboard

## Technical Implementation

### Architecture

```
backend/
├── app/models/
│   ├── group.py              # Group, UserGroup models
│   └── __init__.py           # Add exports
├── app/schemas/
│   └── group.py              # Group schemas
├── app/services/
│   └── group_service.py      # GroupService
├── app/api/v1/
│   └── groups.py             # Admin group endpoints
├── alembic/versions/
│   └── xxx_add_groups.py     # Migration
└── tests/
    ├── unit/test_group_service.py
    └── integration/test_groups_api.py

frontend/
├── src/app/(protected)/admin/groups/
│   ├── page.tsx              # Groups list page
│   └── __tests__/page.test.tsx
├── src/components/admin/
│   ├── group-table.tsx
│   ├── create-group-modal.tsx
│   ├── edit-group-modal.tsx
│   ├── group-membership-modal.tsx
│   └── __tests__/
│       ├── group-table.test.tsx
│       ├── create-group-modal.test.tsx
│       ├── edit-group-modal.test.tsx
│       └── group-membership-modal.test.tsx
├── src/hooks/
│   ├── useGroups.ts
│   └── __tests__/useGroups.test.tsx
├── src/types/
│   └── group.ts
└── e2e/tests/admin/
    └── group-management.spec.ts
```

### Database Schema

```sql
-- Groups table
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_groups_name ON groups(name);
CREATE INDEX idx_groups_is_active ON groups(is_active);

-- User-Groups junction table
CREATE TABLE user_groups (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, group_id)
);

CREATE INDEX idx_user_groups_group_id ON user_groups(group_id);
```

### API Contracts

```typescript
// GET /api/v1/admin/groups?page=1&per_page=20&search=eng
interface GroupsResponse {
  data: GroupRead[];
  meta: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  };
}

interface GroupRead {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  member_count: number;
  created_at: string;
  updated_at: string;
}

// POST /api/v1/admin/groups
interface GroupCreate {
  name: string;
  description?: string;
}

// PATCH /api/v1/admin/groups/{id}
interface GroupUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

// GET /api/v1/admin/groups/{id}
interface GroupWithMembers extends GroupRead {
  members: UserRead[];
}

// POST /api/v1/admin/groups/{id}/members
interface GroupMemberAdd {
  user_ids: string[];
}
// Response: { added_count: number }

// DELETE /api/v1/admin/groups/{id}/members/{user_id}
// Response: 204 No Content
```

### Component Specifications

**GroupTable Component:**
- Columns: Name, Description (truncated), Member Count, Status, Created, Actions
- Status badge: Green "Active" / Red "Inactive"
- Actions: Edit, Manage Members, Delete (if active)
- Expandable row: Shows first 5 members with "View all" link
- Search: Debounced name filter (300ms)
- Pagination: 20 per page

**CreateGroupModal Component:**
- Form validation with react-hook-form + zod
- Name: required, max 255 chars
- Description: optional textarea
- Loading state during submission
- Error display for 409 duplicate name

**GroupMembershipModal Component:**
- Current members section with remove buttons
- User picker with search (email)
- Multi-select for bulk add
- Confirmation dialog for remove
- Optimistic UI updates

## Testing Requirements

### Unit Tests

| Test Case | Component | Coverage |
| --------- | --------- | -------- |
| list_groups returns paginated results | GroupService | AC-5.19.1 |
| create_group validates unique name | GroupService | AC-5.19.1 |
| delete_group soft deletes | GroupService | AC-5.19.1 |
| add_members adds users | GroupService | AC-5.19.4 |
| remove_member removes user | GroupService | AC-5.19.4 |
| Renders group table with data | GroupTable | AC-5.19.2 |
| Expands row to show members | GroupTable | AC-5.19.2 |
| Filters by name search | GroupTable | AC-5.19.2 |
| Opens create modal | CreateGroupModal | AC-5.19.3 |
| Validates required name | CreateGroupModal | AC-5.19.3 |
| Handles duplicate name error | CreateGroupModal | AC-5.19.3 |
| Opens membership modal | GroupMembershipModal | AC-5.19.4 |
| Adds members | GroupMembershipModal | AC-5.19.4 |
| Removes member with confirm | GroupMembershipModal | AC-5.19.4 |

### Integration Tests

| Test Case | Scope | Coverage |
| --------- | ----- | -------- |
| GET /admin/groups returns list | API | AC-5.19.1 |
| POST /admin/groups creates group | API | AC-5.19.1 |
| POST /admin/groups 409 on duplicate | API | AC-5.19.1 |
| PATCH /admin/groups updates group | API | AC-5.19.1 |
| DELETE /admin/groups soft deletes | API | AC-5.19.1 |
| POST /admin/groups/{id}/members adds | API | AC-5.19.4 |
| DELETE /admin/groups/{id}/members removes | API | AC-5.19.4 |
| Non-admin gets 403 | API | AC-5.19.6 |

### E2E Tests

| Test Case | Coverage |
| --------- | -------- |
| Admin can list groups | AC-5.19.2 |
| Admin can create group | AC-5.19.3 |
| Admin can edit group | AC-5.19.3 |
| Admin can add members | AC-5.19.4 |
| Admin can remove member | AC-5.19.4 |
| Non-admin redirected | AC-5.19.6 |
| Navigation link works | AC-5.19.5 |

### Test Commands

```bash
# Backend unit tests
pytest backend/tests/unit/test_group_service.py -v

# Backend integration tests
pytest backend/tests/integration/test_groups_api.py -v

# Frontend unit tests
npm run test:run -- frontend/src/components/admin/__tests__/group-table.test.tsx
npm run test:run -- frontend/src/components/admin/__tests__/create-group-modal.test.tsx
npm run test:run -- frontend/src/components/admin/__tests__/group-membership-modal.test.tsx
npm run test:run -- frontend/src/hooks/__tests__/useGroups.test.tsx

# E2E tests
npx playwright test frontend/e2e/tests/admin/group-management.spec.ts
```

## Dev Notes

### Learnings from Previous Story (Story 5.18)

Story 5.18 (User Management UI) established key patterns this story should follow:

**Files Created in Story 5.18:**
- `frontend/src/hooks/useUsers.ts` - React Query hook pattern for admin data
- `frontend/src/components/admin/user-table.tsx` - Admin table component pattern
- `frontend/src/components/admin/create-user-modal.tsx` - Create modal pattern
- `frontend/src/components/admin/edit-user-modal.tsx` - Edit modal pattern
- `frontend/src/components/auth/admin-guard.tsx` - Route protection

**Patterns to Reuse:**
- React Query (SWR-like) for data fetching with optimistic updates
- Zod validation schemas for forms
- Admin route protection via AdminGuard wrapper
- Toast notifications for success/error feedback
- URL state for search/page params
- Self-modification prevention pattern (can't delete own membership)

**Integration Points:**
- Add "Groups" link alongside "Users" in MainNav admin section
- Follow same icon + label pattern
- Extend existing admin tools section in `/admin/page.tsx`

[Source: docs/sprint-artifacts/5-18-user-management-ui.md]

### Patterns to Follow

1. **Use existing admin page patterns** - Reference `/admin/users/page.tsx` for consistent layout
2. **React Query for data fetching** - Follow `useUsers.ts` hook pattern
3. **Shadcn UI components** - Table, Dialog, Form, Button, Badge, Input, Textarea
4. **Toast notifications** - Use existing toast utility
5. **DashboardLayout wrapper** - Consistent navigation

### Key Implementation Details

1. **Soft delete pattern**: Set `is_active=false` instead of hard delete to preserve audit history
2. **Member count**: Computed field via COUNT(*) in query, not stored
3. **Expandable rows**: Use collapsible component or accordion pattern
4. **User picker filtering**: Filter out users already in group on frontend
5. **Audit logging**: Fire-and-forget pattern for all membership changes
6. **Unique constraint**: Handle IntegrityError -> return 409 Conflict

### Security Considerations

1. **Admin-only access**: All endpoints require `current_superuser` dependency
2. **Input validation**: Sanitize group names, prevent SQL injection
3. **Audit trail**: Log all group operations for compliance
4. **Cascade delete**: Removing user from system removes from all groups

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-5.md - Story 5.19 ACs, Data Models, Traceability Matrix]
- [Source: docs/epics.md - Story 5.19 Acceptance Criteria]
- [Source: docs/architecture.md - Database patterns, API conventions]
- [Source: docs/coding-standards.md - TypeScript conventions, testing standards]
- [Source: docs/sprint-artifacts/5-18-user-management-ui.md - UI patterns]
- [Source: backend/app/api/v1/admin.py - Admin endpoint patterns]
- [Source: backend/app/models/knowledge_base.py - kb_permissions pattern]
- [Source: frontend/src/hooks/useUsers.ts - React Query hook pattern]

### Dependencies

```json
{
  "dependencies": {
    "react-hook-form": "^7.x",    // Already installed
    "@hookform/resolvers": "^3.x", // Already installed
    "zod": "^3.x",                 // Already installed
    "@tanstack/react-query": "^5.x" // Already installed
  }
}
```

### Future Enhancements (Out of Scope)

- LDAP/SSO group sync
- Group hierarchy (parent/child groups)
- Group-level KB permissions UI (Story 5.20)
- Bulk user import to groups
- Group activity dashboard

## Risks & Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Large group membership lists | Medium | Paginate member display, lazy load |
| Concurrent membership updates | Low | Use optimistic updates with proper rollback |
| Orphaned group permissions | Medium | Cascade delete on user removal |
| Duplicate group names race | Low | Database unique constraint + 409 handling |

## Definition of Done

- [ ] All acceptance criteria implemented and verified
- [ ] Backend unit tests written and passing (>80% coverage)
- [ ] Backend integration tests written and passing
- [ ] Frontend unit tests written and passing
- [ ] E2E tests written and passing
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] No ruff errors in backend
- [ ] Code reviewed
- [ ] Accessible (keyboard nav, screen reader labels)
- [ ] Responsive design (mobile-friendly)
- [ ] Documentation updated (if needed)

## Dev Agent Record

### Context Reference
- Story file: `docs/sprint-artifacts/5-19-group-management.md`
- Story context: `docs/sprint-artifacts/5-19-group-management.context.xml`
- Previous story: `docs/sprint-artifacts/5-18-user-management-ui.md`
- Epic tech spec: `docs/sprint-artifacts/tech-spec-epic-5.md`

### Agent Model Used
- Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References
- Automation summary: `docs/sprint-artifacts/automation-summary-story-5-19.md`
- Code review report: `docs/sprint-artifacts/code-review-story-5-19.md`

### Completion Notes
**Completed:** 2025-12-05
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

**Implementation Summary:**
- Backend: Group model, UserGroup junction table, GroupService, 7 admin API endpoints
- Frontend: useGroups/useGroup hooks, GroupTable, CreateGroupModal, EditGroupModal, GroupMembershipModal, Groups page
- Tests: 40+ tests (22 backend unit, 18 hook tests, 20+ component tests)
- Code Review: APPROVED with 100% AC satisfaction
- Navigation: Groups link added to MainNav admin section

### File List
| File | Status | Notes |
| ---- | ------ | ----- |
| `backend/app/models/group.py` | To create | Group, UserGroup models |
| `backend/app/schemas/group.py` | To create | Group schemas |
| `backend/app/services/group_service.py` | To create | GroupService |
| `backend/app/api/v1/groups.py` | To create | Admin endpoints |
| `backend/alembic/versions/xxx_add_groups.py` | To create | Migration |
| `backend/tests/unit/test_group_service.py` | To create | Unit tests |
| `backend/tests/integration/test_groups_api.py` | To create | Integration tests |
| `frontend/src/types/group.ts` | To create | TypeScript interfaces |
| `frontend/src/hooks/useGroups.ts` | To create | React Query hook |
| `frontend/src/components/admin/group-table.tsx` | To create | Table component |
| `frontend/src/components/admin/create-group-modal.tsx` | To create | Create modal |
| `frontend/src/components/admin/edit-group-modal.tsx` | To create | Edit modal |
| `frontend/src/components/admin/group-membership-modal.tsx` | To create | Membership modal |
| `frontend/src/app/(protected)/admin/groups/page.tsx` | To create | Groups page |
| `frontend/e2e/tests/admin/group-management.spec.ts` | To create | E2E tests |

## Changelog

| Date       | Author | Change |
| ---------- | ------ | ------ |
| 2025-12-05 | Bob (SM) | Initial story creation via YOLO workflow |
| 2025-12-05 | Bob (SM) | Validation pass - added coding-standards.md citation |
| 2025-12-05 | Bob (SM) | Re-validation - added tech-spec-epic-5.md citation after tech spec updated |
| 2025-12-05 | Bob (SM) | Story context generated, status changed to ready-for-dev |
