# Bugfix Session: Admin Panel Authentication & Audit Log Filters

**Date:** 2025-12-05
**Story:** 5.17 - Main Application Navigation Menu (Continuation)
**Session Focus:** Admin panel authentication errors and audit log filter functionality

---

## Summary

This session addressed two main issues in the admin panel:
1. Authentication errors (401 "Authentication required") on admin pages
2. Audit log filters appearing to not work

---

## Issue 1: Admin Panel Authentication Errors

### Problem Description
Admin pages (Admin Dashboard, Audit Logs, KB Stats, System Config, Queue Status) were showing "Authentication required" errors despite users being logged in.

### Root Cause
Admin hooks were using Bearer token authentication (`localStorage.getItem('token')`) while the application uses cookie-based authentication. Additionally, some hooks used relative URLs that hit the Next.js server instead of the backend API.

### Files Modified

#### 1. `frontend/src/hooks/useAdminStats.ts`
**Change:** Switched from Bearer token to cookie-based auth
```typescript
// Before
const res = await fetch('/api/v1/admin/stats', {
  headers: {
    Authorization: `Bearer ${localStorage.getItem('token')}`,
  },
});

// After
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const res = await fetch(`${API_BASE_URL}/api/v1/admin/stats`, {
  credentials: 'include',
});
```

#### 2. `frontend/src/hooks/useAuditLogs.ts`
**Change:** Switched from Bearer token to cookie-based auth
```typescript
// Before
headers: {
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('token')}`,
},

// After
headers: {
  'Content-Type': 'application/json',
},
credentials: 'include',
```

#### 3. `frontend/src/hooks/useKBStats.ts`
**Change:** Switched from Bearer token to cookie-based auth
```typescript
// Before
const res = await fetch(url, {
  headers: {
    Authorization: `Bearer ${localStorage.getItem('token')}`,
  },
});

// After
const res = await fetch(url, {
  credentials: 'include',
});
```

#### 4. `frontend/src/hooks/useSystemConfig.ts`
**Change:** Added `API_BASE_URL` constant (already used `credentials: 'include'`)
```typescript
// Added at top of file
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Updated fetch calls to use absolute URL
const response = await fetch(`${API_BASE_URL}/api/v1/admin/config`, {
  credentials: "include",
});
```

#### 5. `frontend/src/hooks/useQueueStatus.ts`
**Change:** Added `API_BASE_URL` constant
```typescript
// Added
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Updated fetch
const response = await fetch(`${API_BASE_URL}/api/v1/admin/queue/status`, {
  credentials: "include",
});
```

#### 6. `frontend/src/hooks/useQueueTasks.ts`
**Change:** Added `API_BASE_URL` constant
```typescript
// Added
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Updated fetch
const response = await fetch(`${API_BASE_URL}/api/v1/admin/queue/${queueName}/tasks?type=${taskType}`, {
  credentials: "include",
});
```

---

## Issue 2: KB Stats Page "knowledgeBases.map is not a function" Error

### Problem Description
The KB Stats page crashed with a TypeError when trying to render the knowledge base selector dropdown.

### Root Cause
The API returns a paginated response `{ data: [...], total, page, limit }` but the code treated the response as a direct array.

### File Modified

#### `frontend/src/app/(protected)/admin/kb-stats/page.tsx`
**Change:** Extract `data` from paginated API response
```typescript
// Before
if (res.ok) {
  const data = await res.json();
  setKnowledgeBases(data);
}

// After
if (res.ok) {
  const response = await res.json();
  // API returns { data: [...], total, page, limit }
  setKnowledgeBases(Array.isArray(response) ? response : response.data || []);
}
```

Also added `credentials: 'include'` to the fetch call:
```typescript
const res = await fetch(`${API_BASE_URL}/api/v1/knowledge-bases/`, {
  credentials: 'include',
});
```

---

## Issue 3: Audit Log Filters Not Working

### Problem Description
Users reported that audit log filters "don't work" - selecting a filter and clicking "Apply Filters" appeared to have no effect.

### Root Cause
The filters were actually working correctly, but the frontend `EVENT_TYPES` array was missing several event types that actually exist in the database:

| Event Type | Description |
|------------|-------------|
| `kb.created` | Logged when knowledge bases are created |
| `user.login` | Logged when users log in |
| `user.logout` | Logged when users log out |
| `user.login_failed` | Logged when login attempts fail |

When users selected event types like "search" or "generation.request" from the dropdown, there were no matching records in the database, resulting in empty results.

### Files Modified

#### 1. `backend/app/schemas/admin.py`
**Change:** Added missing event types to `AuditEventType` enum
```python
class AuditEventType(str, Enum):
    # ... existing types ...

    # Knowledge base operations
    KB_CREATED = "kb.created"  # NEW
    KB_UPDATED = "kb.updated"
    KB_ARCHIVED = "kb.archived"
    KB_PERMISSION_GRANTED = "kb.permission_granted"
    KB_PERMISSION_REVOKED = "kb.permission_revoked"

    # User operations (NEW SECTION)
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"

    # ... rest of types ...
```

#### 2. `frontend/src/types/audit.ts`
**Change:** Added matching event types to `EVENT_TYPES` array
```typescript
export const EVENT_TYPES = [
  'search',
  'generation.request',
  'generation.complete',
  'generation.failed',
  'generation.feedback',
  'document.uploaded',
  'document.retry',
  'document.deleted',
  'document.replaced',
  'document.export',
  'kb.created',        // NEW
  'kb.updated',
  'kb.archived',
  'kb.permission_granted',
  'kb.permission_revoked',
  'user.login',        // NEW
  'user.logout',       // NEW
  'user.login_failed', // NEW
  'change_search',
  'add_context',
  'new_draft',
  'select_template',
  'regenerate_with_structure',
  'regenerate_detailed',
  'add_sections',
  'search_better_sources',
  'review_citations',
  'regenerate_with_feedback',
  'adjust_parameters',
] as const;
```

---

## Verification

### API Tests Performed

1. **Audit logs without filter:**
   ```bash
   curl -s http://localhost:8000/api/v1/admin/audit/logs -X POST \
     -H "Content-Type: application/json" \
     -H "Cookie: lumikb_auth=..." \
     -d '{"page": 1, "page_size": 5}'
   # Result: 16 total events returned
   ```

2. **Audit logs with `user.login` filter:**
   ```bash
   curl -s http://localhost:8000/api/v1/admin/audit/logs -X POST \
     -H "Content-Type: application/json" \
     -H "Cookie: lumikb_auth=..." \
     -d '{"page": 1, "page_size": 5, "event_type": "user.login"}'
   # Result: 10 total events matching filter
   ```

3. **Audit logs with `document.uploaded` filter:**
   ```bash
   curl -s http://localhost:8000/api/v1/admin/audit/logs -X POST \
     -H "Content-Type: application/json" \
     -H "Cookie: lumikb_auth=..." \
     -d '{"page": 1, "page_size": 5, "event_type": "document.uploaded"}'
   # Result: 4 total events matching filter
   ```

4. **Audit logs with `resource_type: document` filter:**
   ```bash
   curl -s http://localhost:8000/api/v1/admin/audit/logs -X POST \
     -H "Content-Type: application/json" \
     -H "Cookie: lumikb_auth=..." \
     -d '{"page": 1, "page_size": 5, "resource_type": "document"}'
   # Result: 4 total events matching filter
   ```

### Linting Verification

- Backend: `ruff check app/schemas/admin.py` - All checks passed
- Frontend: `npm run lint` - No new errors introduced (pre-existing warnings only)

---

## Key Learnings

1. **Authentication Consistency:** Always use the same authentication method (cookie-based with `credentials: 'include'`) across all API hooks in the frontend.

2. **API Base URL:** Always use absolute URLs with `API_BASE_URL` for backend API calls to avoid hitting the Next.js server.

3. **Paginated Responses:** Handle paginated API responses correctly by extracting the `data` array from the response object.

4. **Enum Synchronization:** Keep frontend type definitions synchronized with backend enum values to ensure filters work correctly.

---

## Issue 4: Audit Log Export "Not Found" Error

### Problem Description
Clicking "Download CSV" or "Download JSON" in the Export Audit Logs modal resulted in "Export failed: Not Found" error.

### Root Cause
The export modal was using a relative URL `/api/v1/admin/audit/export` which hit the Next.js server instead of the backend API.

### File Modified

#### `frontend/src/components/admin/export-audit-logs-modal.tsx`
**Change:** Added `API_BASE_URL` and updated fetch URL
```typescript
// Added at top of file
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Before
const response = await fetch("/api/v1/admin/audit/export", {

// After
const response = await fetch(`${API_BASE_URL}/api/v1/admin/audit/export`, {
```

---

## Issue 5: UI Container Width Inconsistency

### Problem Description
The audit log page inner content extended to the full width of the outer frame (no horizontal padding). The config page was also missing the container class entirely.

### Root Cause
Inconsistent container/padding classes across admin pages:
- Audit page used `py-6` (vertical only) instead of `p-6`
- Config page used `p-8` without `container mx-auto`

### Files Modified

#### 1. `frontend/src/app/(protected)/admin/audit/page.tsx`
**Change:** Added horizontal padding
```typescript
// Before
<div className="container mx-auto space-y-6 py-6">

// After
<div className="container mx-auto space-y-6 p-6">
```

#### 2. `frontend/src/app/(protected)/admin/config/page.tsx`
**Change:** Added container class and standardized padding
```typescript
// Before
<div className="p-8">

// After
<div className="container mx-auto p-6">
```

---

## Issue 6: Admin Page Title Icons Missing

### Problem Description
Admin pages were missing icons before their page titles.

### Files Modified
Added icons to all admin page titles:

| Page | Icon Added |
|------|------------|
| Admin Dashboard | `Activity` |
| Audit Logs | `FileSearch` |
| Queue Status | `Server` |
| System Configuration | `Settings` |
| KB Statistics | `Database` |

Files updated:
- `frontend/src/app/(protected)/admin/page.tsx`
- `frontend/src/app/(protected)/admin/audit/page.tsx`
- `frontend/src/app/(protected)/admin/queue/page.tsx`
- `frontend/src/app/(protected)/admin/config/page.tsx`
- `frontend/src/app/(protected)/admin/kb-stats/page.tsx`

---

## Issue 7: Navigation Menu Icons Inconsistent with Page Title Icons

### Problem Description
The icons in the main navigation menu and mobile navigation did not match the icons used on the corresponding page titles.

### Root Cause
Navigation components used different icons than page titles:

| Page | Nav Icon (Before) | Page Title Icon |
|------|-------------------|-----------------|
| Admin Dashboard | `LayoutDashboard` | `Activity` |
| Audit Logs | `ScrollText` | `FileSearch` |
| Queue Status | `Activity` | `Server` |
| KB Statistics | `BarChart` | `Database` |

### Files Modified

#### 1. `frontend/src/components/layout/main-nav.tsx`
**Change:** Updated admin link icons to match page titles
```typescript
// Before
const adminLinks = [
  { href: '/admin', icon: LayoutDashboard, label: 'Admin Dashboard' },
  { href: '/admin/audit', icon: ScrollText, label: 'Audit Logs' },
  { href: '/admin/queue', icon: Activity, label: 'Queue Status' },
  { href: '/admin/config', icon: Settings, label: 'System Config' },
  { href: '/admin/kb-stats', icon: BarChart, label: 'KB Statistics' },
];

// After
const adminLinks = [
  { href: '/admin', icon: Activity, label: 'Admin Dashboard' },
  { href: '/admin/audit', icon: FileSearch, label: 'Audit Logs' },
  { href: '/admin/queue', icon: Server, label: 'Queue Status' },
  { href: '/admin/config', icon: Settings, label: 'System Config' },
  { href: '/admin/kb-stats', icon: Database, label: 'KB Statistics' },
];
```

#### 2. `frontend/src/components/layout/mobile-nav.tsx`
**Change:** Updated admin link icons and admin toggle button icon
```typescript
// Updated adminLinks array (same as main-nav.tsx)
// Updated admin toggle button icon from LayoutDashboard to Activity
```

---

## Related Files Changed (Complete List)

| File | Type of Change |
|------|----------------|
| `frontend/src/hooks/useAdminStats.ts` | Auth fix |
| `frontend/src/hooks/useAuditLogs.ts` | Auth fix |
| `frontend/src/hooks/useKBStats.ts` | Auth fix |
| `frontend/src/hooks/useSystemConfig.ts` | API URL fix |
| `frontend/src/hooks/useQueueStatus.ts` | API URL fix |
| `frontend/src/hooks/useQueueTasks.ts` | API URL fix |
| `frontend/src/app/(protected)/admin/kb-stats/page.tsx` | Paginated response fix + auth fix + icon |
| `frontend/src/types/audit.ts` | Added missing event types |
| `backend/app/schemas/admin.py` | Added missing event types to enum |
| `frontend/src/components/admin/export-audit-logs-modal.tsx` | API URL fix for export |
| `frontend/src/app/(protected)/admin/audit/page.tsx` | Container padding fix + icon |
| `frontend/src/app/(protected)/admin/config/page.tsx` | Container class fix + icon |
| `frontend/src/app/(protected)/admin/page.tsx` | Icon added |
| `frontend/src/app/(protected)/admin/queue/page.tsx` | Icon added |
| `frontend/src/components/layout/main-nav.tsx` | Icon consistency fix |
| `frontend/src/components/layout/mobile-nav.tsx` | Icon consistency fix |

---

## Issue 8: Audit Logs Dark Mode Inconsistency

### Problem Description
The Audit Logs page had white backgrounds on the filters panel, table, and modals while the rest of the application used dark mode theming.

### Root Cause
The audit log components used hardcoded light mode Tailwind classes (e.g., `bg-white`, `text-gray-900`, `border-gray-200`) instead of theme-aware semantic classes.

### Files Modified

#### 1. `frontend/src/components/admin/audit-log-table.tsx`
**Changes:**
- Table container: `border-gray-200 bg-white` → `border`
- Table dividers: `divide-gray-200` → `divide-border`
- Header background: `bg-gray-50` → `bg-muted`
- Header text: `text-gray-500` → `text-muted-foreground`
- Body dividers: `divide-gray-200 bg-white` → `divide-border`
- Row hover: `hover:bg-gray-50` → `hover:bg-muted/50`
- Cell text: `text-gray-900`, `text-gray-500` → removed / `text-muted-foreground`
- Button: `text-blue-600 hover:text-blue-900` → `text-primary hover:text-primary/80`
- Pagination text: `text-gray-700` → `text-muted-foreground`
- Status badges: `bg-green-100 text-green-800` → `bg-green-500/20 text-green-500`
- Loading spinner: `border-gray-300 border-t-blue-600` → `border-muted border-t-primary`

#### 2. `frontend/src/components/admin/audit-event-details-modal.tsx`
**Changes:**
- Labels: `text-gray-700` → `text-muted-foreground`
- Values: `text-gray-900` → removed (uses default)
- Details box: `border-gray-200 bg-gray-50` → `border bg-muted`
- Notes: `text-gray-500` → `text-muted-foreground`

#### 3. `frontend/src/components/admin/export-audit-logs-modal.tsx`
**Changes:**
- Modal background: `bg-white` → `bg-background`
- Close button: `text-gray-400 hover:text-gray-600` → `text-muted-foreground hover:text-foreground`
- Info box: `bg-blue-50 border-blue-200 text-blue-800` → `bg-primary/10 border-primary/20 text-primary`
- Filter text: `text-gray-600`, `text-gray-400` → `text-muted-foreground`, `text-muted-foreground/50`
- Error box: `bg-red-50 border-red-200 text-red-800` → `bg-destructive/10 border-destructive/20 text-destructive`
- Cancel button: hardcoded colors → `border hover:bg-muted`
- Export button: `bg-blue-600 hover:bg-blue-700` → `bg-primary hover:bg-primary/90`

---

## Issue 9: Page Title Size Inconsistency

### Problem Description
Admin pages used `text-3xl font-bold` for titles while other pages used `text-2xl font-bold`, causing visual inconsistency.

### Files Modified
All admin pages and settings page were standardized to use `text-2xl font-bold` with `h-8 w-8` icons:

| File | Change |
|------|--------|
| `frontend/src/app/(protected)/admin/page.tsx` | `text-3xl` → `text-2xl` |
| `frontend/src/app/(protected)/admin/audit/page.tsx` | `text-3xl` → `text-2xl` |
| `frontend/src/app/(protected)/admin/queue/page.tsx` | `text-3xl` → `text-2xl` |
| `frontend/src/app/(protected)/admin/config/page.tsx` | `text-3xl` → `text-2xl` |
| `frontend/src/app/(protected)/admin/kb-stats/page.tsx` | `text-3xl` → `text-2xl` |
| `frontend/src/app/(protected)/settings/page.tsx` | Icon `h-6 w-6` → `h-8 w-8` |
| `frontend/src/app/(protected)/chat/page.tsx` | Added `text-2xl font-bold` to CardTitle |

---

## Updated Related Files Changed (Complete List)

| File | Type of Change |
|------|----------------|
| `frontend/src/hooks/useAdminStats.ts` | Auth fix |
| `frontend/src/hooks/useAuditLogs.ts` | Auth fix |
| `frontend/src/hooks/useKBStats.ts` | Auth fix |
| `frontend/src/hooks/useSystemConfig.ts` | API URL fix |
| `frontend/src/hooks/useQueueStatus.ts` | API URL fix |
| `frontend/src/hooks/useQueueTasks.ts` | API URL fix |
| `frontend/src/app/(protected)/admin/kb-stats/page.tsx` | Paginated response fix + auth fix + icon + title size |
| `frontend/src/types/audit.ts` | Added missing event types |
| `backend/app/schemas/admin.py` | Added missing event types to enum |
| `frontend/src/components/admin/export-audit-logs-modal.tsx` | API URL fix + dark mode fix |
| `frontend/src/components/admin/audit-log-table.tsx` | Dark mode fix |
| `frontend/src/components/admin/audit-event-details-modal.tsx` | Dark mode fix |
| `frontend/src/app/(protected)/admin/audit/page.tsx` | Container padding fix + icon + title size |
| `frontend/src/app/(protected)/admin/config/page.tsx` | Container class fix + icon + title size |
| `frontend/src/app/(protected)/admin/page.tsx` | Icon added + title size |
| `frontend/src/app/(protected)/admin/queue/page.tsx` | Icon added + title size |
| `frontend/src/app/(protected)/settings/page.tsx` | Icon size fix |
| `frontend/src/app/(protected)/chat/page.tsx` | Title size fix |
| `frontend/src/components/layout/main-nav.tsx` | Icon consistency fix |
| `frontend/src/components/layout/mobile-nav.tsx` | Icon consistency fix |

---

## Issue 10: Audit Log Pagination UX Improvements

### Problem Description
The audit log table had pagination controls at the bottom of the table, and users couldn't change the page size (number of results per page).

### Changes Made

#### 1. `frontend/src/components/admin/audit-log-table.tsx`
**Changes:**
- Added `onPageSizeChange` optional prop to allow page size changes
- Added `PAGE_SIZE_OPTIONS` constant with options: 10, 25, 50, 100
- Moved pagination bar to the top of the table
- Combined pagination info, page size selector, and Previous/Next buttons into a single bar
- Added "Page X of Y" display showing total pages
- Used shadcn/ui Select component for page size selector
- Applied dark mode compatible styling (`bg-muted/30`)
- Removed duplicate pagination controls at bottom

```typescript
// New interface
export interface AuditLogTableProps {
  events: AuditEvent[];
  totalCount: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;  // NEW
  onViewDetails: (event: AuditEvent) => void;
  isLoading?: boolean;
}
```

#### 2. `frontend/src/app/(protected)/admin/audit/page.tsx`
**Changes:**
- Changed `pageSize` from `const` to `useState` to allow dynamic changes
- Added `handlePageSizeChange` handler that resets to page 1 when page size changes
- Passed `onPageSizeChange` prop to `AuditLogTable`
- Fixed dark mode styling on error state container

```typescript
// Before
const [pageSize] = useState(50);

// After
const [pageSize, setPageSize] = useState(50);

const handlePageSizeChange = (newPageSize: number) => {
  setPageSize(newPageSize);
  setPage(1); // Reset to page 1 when page size changes
};

// Updated AuditLogTable usage
<AuditLogTable
  ...
  onPageSizeChange={handlePageSizeChange}
/>
```

### UI/UX Result
- Pagination bar is now at the top, making it immediately visible
- Users can select how many results to display per page (10, 25, 50, or 100)
- Total page count is displayed ("Page 1 of 5")
- More compact and intuitive pagination experience

---

## Issue 11: Admin Navigation Menu Cramped/Tight Spacing

### Problem Description
The admin navigation menu in the header was too cramped, with labels being too long and insufficient spacing between items.

### Changes Made

#### 1. `frontend/src/components/layout/main-nav.tsx`
**Changes:**
- Shortened admin link labels to reduce crowding:
  - "Admin Dashboard" → "Overview"
  - "Audit Logs" → "Audit"
  - "Queue Status" → "Queue"
  - "System Config" → "Config"
  - "KB Statistics" → "KB Stats"
- Increased nav gap from `gap-1` to `gap-2` for better spacing

#### 2. `frontend/src/components/layout/mobile-nav.tsx`
**Changes:**
- Updated admin link labels to match main nav for consistency
- Updated "Dashboard" label to "Home" for mobile nav

---

## Issue 12: Collapsible Admin Menu Implementation

### Problem Description
User requested the ability to toggle between core navigation (Dashboard, Search, Chat) and admin navigation, rather than showing both simultaneously which takes up too much space.

### Behavior Requested
- Core navigation links (Dashboard, Search, Chat) visible by default
- Admin links hidden by default
- Clicking "Admin" button collapses core links and shows admin menu
- Clicking "Admin" button again returns to core navigation

### Changes Made

#### `frontend/src/components/layout/main-nav.tsx`
**Changes:**
1. Added `useState` for `showAdminMenu` toggle state (default: `false`)
2. Added new icons: `ChevronLeft`, `ChevronRight`, `Shield`
3. Added `Button` component import for admin toggle
4. Removed `Separator` component (no longer needed)
5. Implemented toggle button with:
   - Shield icon + "Admin" label
   - Chevron indicator (right when collapsed, left when expanded)
   - Highlight when on admin route or menu is open
   - Proper ARIA attributes (`aria-expanded`, `aria-label`)
6. Conditional rendering:
   - Core links shown when `!showAdminMenu`
   - Admin links shown when `showAdminMenu`

```typescript
// State
const [showAdminMenu, setShowAdminMenu] = useState(false);

// Admin toggle button
<Button
  variant="ghost"
  onClick={() => setShowAdminMenu(!showAdminMenu)}
  aria-expanded={showAdminMenu}
  aria-label={showAdminMenu ? 'Show main menu' : 'Show admin menu'}
>
  <Shield className="h-4 w-4" />
  <span>Admin</span>
  {showAdminMenu ? <ChevronLeft /> : <ChevronRight />}
</Button>

// Conditional rendering
{!showAdminMenu && <CoreLinks />}
{showAdminMenu && <AdminLinks />}
```

### UI/UX Result
- Cleaner navigation with less horizontal space usage
- Admin users can easily toggle between main app and admin sections
- Visual indicator (chevron) shows toggle state
- Active route highlighting works correctly for both modes
- Tooltip support maintained for accessibility
