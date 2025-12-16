# Story 5.17: Main Application Navigation Menu

Status: done

## Story

As a **user (admin or regular user)**,
I want **a persistent navigation menu to access main application sections**,
so that **I can easily navigate between Dashboard, Search, Chat, Admin, and other features**.

## Acceptance Criteria

**AC-5.17.1: Navigation Component Structure**
**Given** I am viewing any protected route in the application
**When** I look at the page layout
**Then** I see a persistent navigation component that provides access to main application sections
**And** the navigation adapts to my screen size:
- Desktop/Laptop (≥1024px): Vertical sidebar navigation OR horizontal header navigation
- Tablet (768-1023px): Collapsible navigation accessible via hamburger menu
- Mobile (<768px): Bottom navigation bar OR hamburger menu
**And** the navigation component is rendered in DashboardLayout for all protected routes
**And** the navigation uses consistent styling with shadcn/ui design system

**Validation:**
- Navigation visible on all protected routes (/dashboard, /search, /chat, /admin/*)
- Responsive behavior verified at breakpoints (mobile, tablet, laptop, desktop)
- Navigation persists when switching between routes
- Visual consistency with KB sidebar and header components

**AC-5.17.2: Core Navigation Links (All Users)**
**Given** I am any authenticated user (admin or regular)
**When** I view the navigation menu
**Then** I see the following core navigation links with icons and labels:
- **Dashboard** (/) - Home or LayoutDashboard icon
- **Search** (/search) - Search icon
- **Chat** (/chat) - MessageSquare icon
**And** the current active route is visually highlighted (different background or border)
**And** each link has a tooltip or accessible label for clarity
**And** clicking a link navigates to the corresponding route

**Validation:**
- All 3 core links visible to all authenticated users
- Active route highlighting updates on navigation
- Icons from lucide-react library (consistent with existing UI)
- Tooltips display on hover (desktop) or tap (mobile)
- Links use Next.js Link component for client-side navigation

**AC-5.17.3: Admin Navigation Section (Admin Users Only)**
**Given** I am an authenticated user
**When** I view the navigation menu
**Then** the "Admin" section is visible ONLY if I have admin role
**And** the Admin section includes the following links:
- **Admin Dashboard** (/admin) - LayoutDashboard icon
- **Audit Logs** (/admin/audit) - ScrollText or FileText icon
- **Queue Status** (/admin/queue) - ListChecks or Activity icon
- **System Config** (/admin/config) - Settings or Sliders icon
- **KB Statistics** (/admin/kb-stats) - BarChart or PieChart icon
**And** the Admin section has a visual separator or header ("Admin" label)
**And** if I am NOT an admin user, the Admin section is completely hidden

**When** a non-admin user attempts to access an admin route directly (via URL)
**Then** they receive a 403 Forbidden error
**And** they are redirected to the dashboard or shown an error message

**Validation:**
- Admin section visible only when user.role === 'admin' (check via useAuthStore)
- All 5 admin links render with correct routes and icons
- Non-admin users see no admin links in navigation
- Backend route protection verified (admin_required dependency on all admin routes)
- Integration test: non-admin user gets 403 on GET /api/v1/admin/*

**AC-5.17.4: User Menu Integration**
**Given** I am viewing the application
**When** I look at the header
**Then** I see the existing user profile menu (UserMenu component - already implemented)
**And** the user menu includes:
- User email or name display
- **Settings** link (route: /settings - placeholder for now, can be non-functional)
- **Logout** button (existing functionality)
**And** clicking Settings navigates to /settings (or shows "Coming soon" message)
**And** clicking Logout logs me out and redirects to login page

**Validation:**
- UserMenu component already exists in header.tsx
- Add Settings link to UserMenu dropdown
- Settings route can be placeholder page or "Coming soon" modal
- Logout functionality already implemented (no changes needed)

**AC-5.17.5: Mobile Navigation**
**Given** I am viewing the application on a mobile device (<768px width)
**When** I interact with the navigation
**Then** I see a mobile-optimized navigation interface:
- **Option A**: Bottom navigation bar with core links (Dashboard, Search, Chat)
- **Option B**: Hamburger menu icon in header that opens slide-out navigation
**And** core navigation links are easily accessible (Dashboard, Search, Chat)
**And** admin links are available in a collapsible "Admin" section OR separate menu item
**And** all tap targets are touch-friendly (minimum 44x44px)
**And** the mobile navigation does not overlap with content or KB sidebar sheet

**Validation:**
- Mobile navigation tested on viewport <768px
- Bottom nav OR hamburger menu functional
- Admin section accessible on mobile (collapsible or nested)
- No layout conflicts with existing mobile-nav.tsx component
- Touch targets meet accessibility guidelines (WCAG 2.5.5)

**AC-5.17.6: Accessibility & Polish**
**Given** I am using keyboard navigation or assistive technology
**When** I interact with the navigation menu
**Then** all navigation links are keyboard accessible:
- Tab key cycles through navigation links in logical order
- Enter key activates the focused link
- Focus visible styles clearly indicate current focus position
**And** all navigation links have proper ARIA labels and semantic HTML
**And** route transitions are smooth (no jarring page reloads)
**And** loading states are shown if navigation takes >200ms (optional enhancement)

**Validation:**
- Keyboard navigation tested (Tab, Shift+Tab, Enter)
- Focus visible styles applied to all interactive elements
- ARIA labels present (aria-label or aria-labelledby)
- Semantic HTML: <nav> element, <ul>/<li> for link lists
- Screen reader announces navigation links correctly
- Smooth client-side navigation (Next.js Link component)

## Tasks / Subtasks

### Task 1: Create Desktop Navigation Component (Frontend) - AC-5.17.1, AC-5.17.2

**Objective:** Build main navigation component for desktop/laptop viewports

**Subtasks:**
- [ ] 1.1 Create `frontend/src/components/layout/main-nav.tsx`
- [ ] 1.2 Implement vertical sidebar navigation layout (left side, below header)
  - [ ] 1.2.1 Width: 200-240px (consistent with KB sidebar width)
  - [ ] 1.2.2 Position: Fixed or sticky, below header
  - [ ] 1.2.3 Z-index management (below modals, above content)
- [ ] 1.3 Add core navigation links (Dashboard, Search, Chat)
  - [ ] 1.3.1 Use Next.js Link component for client-side routing
  - [ ] 1.3.2 Import icons from lucide-react (Home, Search, MessageSquare)
  - [ ] 1.3.3 Icon + label layout (icon left, label right)
- [ ] 1.4 Implement active route detection
  - [ ] 1.4.1 Use Next.js `usePathname()` hook to get current route
  - [ ] 1.4.2 Apply active styles (bg-accent, text-accent-foreground)
  - [ ] 1.4.3 Highlight exact match for routes
- [ ] 1.5 Add tooltips using shadcn/ui Tooltip component
- [ ] 1.6 Style with Tailwind CSS (consistent with existing layout components)
- [ ] 1.7 Responsive design: Hide on mobile (<768px), show on desktop (≥1024px)

**Alternative Approach:**
- If vertical sidebar conflicts with KB sidebar, consider horizontal navigation in header
- Decision: Choose based on UX review and existing layout constraints

### Task 2: Add Admin Navigation Section with Permission Gating (Frontend) - AC-5.17.3

**Objective:** Add admin-only navigation links with role-based visibility

**Subtasks:**
- [ ] 2.1 Import `useAuthStore` to access current user role
- [ ] 2.2 Add conditional rendering for admin section
  - [ ] 2.2.1 Check `user?.role === 'admin'` or equivalent permission
  - [ ] 2.2.2 Only render admin links if user is admin
- [ ] 2.3 Add visual separator for admin section
  - [ ] 2.3.1 Separator line (Separator component from shadcn/ui)
  - [ ] 2.3.2 "Admin" section header label (text-xs, text-muted-foreground)
- [ ] 2.4 Add 5 admin navigation links
  - [ ] 2.4.1 Admin Dashboard (/admin) - LayoutDashboard icon
  - [ ] 2.4.2 Audit Logs (/admin/audit) - ScrollText icon
  - [ ] 2.4.3 Queue Status (/admin/queue) - Activity icon
  - [ ] 2.4.4 System Config (/admin/config) - Settings icon
  - [ ] 2.4.5 KB Statistics (/admin/kb-stats) - BarChart icon
- [ ] 2.5 Ensure admin route protection on backend (verify existing admin_required dependency)

### Task 3: Mobile Navigation Implementation (Frontend) - AC-5.17.5

**Objective:** Adapt navigation for mobile viewports (<768px)

**Subtasks:**
- [ ] 3.1 Review existing `frontend/src/components/layout/mobile-nav.tsx`
- [ ] 3.2 Update mobile-nav.tsx with real routing links (currently has placeholder buttons)
  - [ ] 3.2.1 Dashboard link (/) - Home icon
  - [ ] 3.2.2 Search link (/search) - Search icon
  - [ ] 3.2.3 Chat link (/chat) - MessageSquare icon
  - [ ] 3.2.4 Remove or update "KBs" and "Citations" buttons (already handled by sheets)
- [ ] 3.3 Add admin section to mobile navigation
  - [ ] 3.3.1 Collapsible "Admin" menu item (Accordion or Sheet)
  - [ ] 3.3.2 Show only if user is admin
  - [ ] 3.3.3 Expand to show 5 admin links
- [ ] 3.4 Ensure touch-friendly tap targets (min 44x44px)
- [ ] 3.5 Test mobile navigation on viewport <768px
- [ ] 3.6 Fix any layout conflicts with existing mobile sheets (KB sidebar, Citations)

**Alternative:**
- If bottom nav is too crowded, implement hamburger menu in header instead
- Hamburger opens slide-out navigation sheet with all links

### Task 4: Integrate Navigation into DashboardLayout (Frontend) - AC-5.17.1

**Objective:** Add MainNav component to existing DashboardLayout

**Subtasks:**
- [ ] 4.1 Update `frontend/src/components/layout/dashboard-layout.tsx`
- [ ] 4.2 Import MainNav component
- [ ] 4.3 Add MainNav to layout structure
  - [ ] 4.3.1 Position: Between Header and main content area
  - [ ] 4.3.2 Desktop: Vertical sidebar alongside KB sidebar (two sidebars)
  - [ ] 4.3.3 Mobile: Use existing mobile-nav.tsx component
- [ ] 4.4 Adjust layout spacing to accommodate main navigation
  - [ ] 4.4.1 Ensure KB sidebar (left) and MainNav (left or center) don't overlap
  - [ ] 4.4.2 Adjust main content area width if needed
- [ ] 4.5 Test navigation persistence across route changes
- [ ] 4.6 Verify responsive behavior (desktop, tablet, mobile)

**Layout Options:**
- **Option 1**: KB Sidebar (left) | Main Nav (header horizontal) | Content | Citations (right)
- **Option 2**: KB Sidebar (left) | Main Nav Sidebar (left) | Content | Citations (right) [two left sidebars]
- **Option 3**: KB Sidebar (left) | Content with inline Main Nav | Citations (right)

**Recommendation:** Option 1 (horizontal header nav) for simplicity

### Task 5: Add Settings Link to User Menu (Frontend) - AC-5.17.4

**Objective:** Add Settings link to existing UserMenu component

**Subtasks:**
- [ ] 5.1 Update `frontend/src/components/layout/user-menu.tsx`
- [ ] 5.2 Add Settings link to dropdown menu
  - [ ] 5.2.1 Link to /settings route (placeholder page)
  - [ ] 5.2.2 Settings icon from lucide-react
- [ ] 5.3 Create placeholder settings page (optional)
  - [ ] 5.3.1 `frontend/src/app/(protected)/settings/page.tsx`
  - [ ] 5.3.2 Display "Settings coming soon" message
  - [ ] 5.3.3 Or show "Tutorial Restart" option (reference Story 5.7 AC-5.7.6)
- [ ] 5.4 Verify logout functionality still works (should already be implemented)

### Task 6: Backend Route Protection Verification - AC-5.17.3

**Objective:** Ensure admin routes have proper permission enforcement

**Subtasks:**
- [ ] 6.1 Review all admin API routes in `backend/app/api/v1/admin.py` and related files
- [ ] 6.2 Verify `admin_required` dependency is applied to all admin endpoints
  - [ ] 6.2.1 GET /api/v1/admin/stats
  - [ ] 6.2.2 GET /api/v1/admin/audit/*
  - [ ] 6.2.3 GET /api/v1/admin/queue/*
  - [ ] 6.2.4 GET /api/v1/admin/config/*
  - [ ] 6.2.5 GET /api/v1/admin/knowledge-bases/{kb_id}/stats
- [ ] 6.3 Create integration test for permission enforcement
  - [ ] 6.3.1 Test: Regular user gets 403 on admin endpoints
  - [ ] 6.3.2 Test: Admin user gets 200 on admin endpoints
  - [ ] 6.3.3 Test: Unauthenticated user gets 401 on admin endpoints

### Task 7: Frontend Component Tests - AC-5.17.2, AC-5.17.3, AC-5.17.6

**Objective:** Test navigation component rendering and behavior

**Subtasks:**
- [ ] 7.1 Create `frontend/src/components/layout/__tests__/main-nav.test.tsx`
- [ ] 7.2 Test: MainNav renders all core links for any authenticated user
- [ ] 7.3 Test: MainNav renders admin section for admin user
- [ ] 7.4 Test: MainNav hides admin section for non-admin user
- [ ] 7.5 Test: Active route highlighting applies to current route
- [ ] 7.6 Test: Clicking a link navigates to correct route (mock Next.js router)
- [ ] 7.7 Test: Mobile navigation renders correctly at <768px viewport
- [ ] 7.8 Test: Accessibility - ARIA labels present on all links
- [ ] 7.9 Test: Keyboard navigation - Tab/Enter trigger navigation

### Task 8: E2E Smoke Tests (Deferred to Story 5-16)

**Objective:** Validate end-to-end navigation functionality

**Subtasks:**
- [ ] 8.1 Create `frontend/e2e/tests/navigation/main-navigation.spec.ts`
- [ ] 8.2 Test: Navigation visible on dashboard after login
- [ ] 8.3 Test: Clicking "Search" navigates to /search page
- [ ] 8.4 Test: Clicking "Chat" navigates to /chat page
- [ ] 8.5 Test: Admin links visible only to admin users
- [ ] 8.6 Test: Non-admin user gets 403 error on /admin URL
- [ ] 8.7 Test: Mobile navigation works on mobile viewport
- [ ] 8.8 Test: Active route highlighting updates on navigation

**Note:** E2E tests will be executed as part of Story 5.16 (Docker E2E Infrastructure).

## Dev Notes

### Architecture Patterns

**Component Design:**
- **MainNav Component**: Reusable navigation sidebar/header component
- **Permission-Based Rendering**: Use `useAuthStore` to check user role and conditionally render admin links
- **Active Route Detection**: Use Next.js `usePathname()` hook for client-side route tracking
- **Responsive Design**: Hide/show navigation based on viewport width using Tailwind breakpoints

**Layout Integration:**
- MainNav integrated into DashboardLayout (alongside Header and KB Sidebar)
- Desktop: Vertical sidebar OR horizontal header navigation (decide based on layout constraints)
- Mobile: Existing mobile-nav.tsx component updated with real routing links

**Permission Enforcement:**
- Frontend: Hide admin links for non-admin users (UX)
- Backend: Enforce admin_required dependency on all admin routes (security)
- Defense in depth: Both client-side hiding AND server-side enforcement

### User Experience Considerations

**Navigation Placement:**
- **Goal**: Make core features (Dashboard, Search, Chat) always accessible
- **Challenge**: Avoid navigation clutter - KB sidebar already occupies left side
- **Solution**: Horizontal header navigation OR compact vertical sidebar

**Admin Section Design:**
- Visual separation from core links (separator + "Admin" label)
- Clear indication that these are administrative features
- Collapse/hide on mobile to reduce cognitive load for non-admin users

**Active Route Highlighting:**
- Visual feedback for current location in app
- Helps users maintain context when navigating between sections
- Use subtle background color change (bg-accent) and/or left border

### Project Structure Notes

**Files to Create:**

Frontend:
- `frontend/src/components/layout/main-nav.tsx` - Main navigation component
- `frontend/src/components/layout/__tests__/main-nav.test.tsx` - Component tests
- `frontend/src/app/(protected)/settings/page.tsx` - Placeholder settings page (optional)
- `frontend/e2e/tests/navigation/main-navigation.spec.ts` - E2E tests (deferred to 5-16)

**Files to Modify:**
- `frontend/src/components/layout/dashboard-layout.tsx` - Integrate MainNav component
- `frontend/src/components/layout/mobile-nav.tsx` - Add real routing links, admin section
- `frontend/src/components/layout/user-menu.tsx` - Add Settings link

**Existing Components to Reference:**
- `frontend/src/components/layout/header.tsx` - Header with search bar and user menu
- `frontend/src/components/layout/kb-sidebar.tsx` - KB selector sidebar (layout reference)
- `frontend/src/components/layout/mobile-nav.tsx` - Existing mobile navigation (update this)
- `frontend/src/app/(protected)/dashboard/page.tsx` - Quick Access cards (navigation pattern reference)

### Testing Standards

**Frontend Component Testing:**
- Test: Navigation renders all links for authenticated users
- Test: Admin section visible only for admin users
- Test: Active route highlighting applies correctly
- Test: Keyboard navigation works (Tab, Enter)
- Test: ARIA labels present for accessibility
- Coverage target: 80%+ for MainNav component

**Backend Integration Testing:**
- Test: Non-admin user gets 403 Forbidden on admin routes
- Test: Admin user gets 200 OK on admin routes
- Test: Unauthenticated user gets 401 Unauthorized
- Endpoints to test: /admin/stats, /admin/audit/*, /admin/queue/*, /admin/config/*, /admin/knowledge-bases/{id}/stats

**E2E Testing (Story 5-16):**
- Full user navigation journey (login → dashboard → search → chat → admin)
- Permission-based navigation (admin sees admin links, regular user doesn't)
- Mobile navigation (bottom nav or hamburger menu)
- Active route highlighting across navigation

### Learnings from Previous Stories

**From Story 5.0 (Epic Integration Completion):**
1. **Quick Access Cards Pattern**: Dashboard page shows clickable cards for Search and Chat
   - Reuse this pattern: MainNav is persistent version of Quick Access
   - Keep Quick Access cards on dashboard for discoverability
2. **Navigation Gap**: Epic 3 & 4 features were built but not accessible via navigation
   - Story 5.17 prevents this issue for Epic 5 admin features
3. **Integration Before Testing**: Navigation needed BEFORE E2E tests (Story 5-16)

**From Stories 5-1 through 5-6 (Admin Features):**
1. **Permission Enforcement**: All admin endpoints use `admin_required` dependency
   - MainNav should check user role client-side: `user?.role === 'admin'`
2. **Admin Dashboard Integration**: Story 5-1 added admin overview page
   - MainNav links to /admin route (existing page)
3. **Consistent Icons**: Stories use lucide-react icons (LayoutDashboard, ScrollText, Activity, Settings, BarChart)
   - Reuse same icons in MainNav for consistency

**From Story 1.9 (Three-Panel Dashboard Shell):**
1. **DashboardLayout Component**: Central layout component for all protected routes
   - MainNav integrates into this layout
2. **Responsive Design**: Layout adapts to desktop (3-panel), laptop (2-panel), mobile (1-panel + sheets)
   - MainNav must respect existing responsive behavior
3. **KB Sidebar**: Already occupies left side of layout
   - MainNav placement: horizontal header OR second vertical sidebar

**Quality Standards:**
- Code quality target: 90/100
- All tests must pass before marking story complete
- TypeScript strict mode (no `any` types)
- Accessibility: WCAG 2.1 AA compliance (keyboard nav, ARIA labels, focus styles)
- KISS/DRY/YAGNI principles
- [Source: docs/coding-standards.md] - Project coding standards and conventions

### Technical Debt Considerations

**Deferred to Future Stories:**
- E2E smoke tests deferred to Story 5.16 (Docker E2E Infrastructure)
- Settings page functionality (currently placeholder) - future story
- Navigation analytics tracking (which links are most used) - future enhancement
- Keyboard shortcuts for navigation (Cmd+1 for Dashboard, etc.) - future enhancement

**Potential Future Enhancements:**
- Breadcrumb navigation for deep routes (e.g., /admin/audit → Admin > Audit Logs)
- Recent pages history (quick navigation back to recently visited routes)
- Search within navigation (filter navigation links by keyword)
- Customizable navigation (users can reorder or pin favorite sections)
- Navigation collapse/expand (minimize sidebar to icons-only on desktop)

### References

**Architecture References:**
- [Source: docs/architecture.md] - Overall system architecture
- [Source: docs/ux-design-specification.md, lines 156-188] - Navigation & Layout patterns
- [Source: frontend/src/components/layout/dashboard-layout.tsx] - Existing layout structure

**PRD References:**
- [Source: docs/sprint-artifacts/tech-spec-epic-5.md] - Epic 5 technical specification
- [Source: docs/epics.md] - Epic 5 scope (Administration & Polish)
- **Problem Statement**: Admin features (Stories 5-1 through 5-6) are built but not accessible via UI navigation
- **Solution**: Add persistent main navigation menu to all protected routes
- **Story Origin**: Post-PRD integration story created 2025-12-03 based on Epic 4 retrospective learning (sprint-status.yaml:95-96) about integration stories preventing feature abandonment

**Related Stories:**
- Story 5.0: Epic 3 & 4 Integration Completion (Quick Access cards pattern)
- Story 1.9: Three-Panel Dashboard Shell (DashboardLayout component)
- Stories 5-1 to 5-6: Admin features that need navigation access
- Story 5.16: Docker E2E Infrastructure (E2E test execution)

**UI Component Library:**
- shadcn/ui Navigation Menu: https://ui.shadcn.com/docs/components/navigation-menu
- shadcn/ui Separator: https://ui.shadcn.com/docs/components/separator
- shadcn/ui Tooltip: https://ui.shadcn.com/docs/components/tooltip
- lucide-react icons: https://lucide.dev/icons/

**Next.js Documentation:**
- usePathname hook: https://nextjs.org/docs/app/api-reference/functions/use-pathname
- Link component: https://nextjs.org/docs/app/api-reference/components/link

## Dev Agent Record

### Context Reference

- [5-17-main-navigation.context.xml](5-17-main-navigation.context.xml)

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

### Completion Notes List

**Implementation Summary (2025-12-05):**

1. **MainNav Component Created (AC-5.17.1, AC-5.17.2):**
   - Created `frontend/src/components/layout/main-nav.tsx`
   - Horizontal header navigation approach (Option 1 from story)
   - Core links: Dashboard, Search, Chat with proper icons
   - Active route detection using `usePathname()`
   - Tooltips for accessibility

2. **Admin Navigation Section (AC-5.17.3):**
   - Admin section gated by `user?.is_superuser === true` check
   - 5 admin links: Admin Dashboard, Audit Logs, Queue Status, System Config, KB Statistics
   - Visual separator between core and admin sections
   - Completely hidden for non-admin users

3. **Mobile Navigation Updated (AC-5.17.5):**
   - Updated `mobile-nav.tsx` with real routing links
   - Added expandable admin section for admin users
   - Touch-friendly tap targets (min 44x44px per WCAG 2.5.5)
   - KBs and Citations buttons preserved for sheet access

4. **Navigation Integrated (AC-5.17.1):**
   - MainNav added to Header component (horizontal in header right side)
   - Hidden on mobile (`hidden md:flex`), visible on tablet/desktop
   - Responsive: icons-only on tablet, icons+labels on desktop

5. **Settings Link Added (AC-5.17.4):**
   - Settings link added to UserMenu dropdown
   - Created placeholder settings page at `/settings`

6. **Backend Route Protection (AC-5.17.3):**
   - Verified all admin endpoints use `current_superuser` dependency
   - Created comprehensive integration tests in `backend/tests/integration/test_admin_route_protection.py`
   - Tests: 401 unauthenticated, 403 non-admin, 200 admin

7. **Frontend Tests (AC-5.17.6):**
   - Created `main-nav.test.tsx` (18 tests)
   - Created `mobile-nav.test.tsx` (18 tests)
   - All 96 layout tests pass

**Key Design Decisions:**
- Used horizontal header nav instead of vertical sidebar to avoid conflicts with KB sidebar
- Admin check uses `is_superuser` boolean (not role string) based on UserRead type
- Mobile admin section uses simple toggle instead of Collapsible component

### File List

**Created:**
- `frontend/src/components/layout/main-nav.tsx` - Main horizontal navigation component
- `frontend/src/components/layout/__tests__/main-nav.test.tsx` - MainNav component tests
- `frontend/src/components/layout/__tests__/mobile-nav.test.tsx` - MobileNav component tests
- `frontend/src/app/(protected)/settings/page.tsx` - Placeholder settings page
- `backend/tests/integration/test_admin_route_protection.py` - Backend route protection tests

**Modified:**
- `frontend/src/components/layout/header.tsx` - Added MainNav integration
- `frontend/src/components/layout/mobile-nav.tsx` - Added routing links and admin section
- `frontend/src/components/layout/user-menu.tsx` - Added Settings link
- `frontend/src/components/layout/__tests__/header.test.tsx` - Updated for MainNav integration
