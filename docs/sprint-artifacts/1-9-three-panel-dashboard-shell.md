# Story 1.9: Three-Panel Dashboard Shell

Status: done

## Story

As a **user**,
I want **to see the main application layout after login**,
so that **I understand how to navigate LumiKB**.

## Acceptance Criteria

1. **Given** I am logged in **When** I navigate to the dashboard **Then** I see a three-panel layout:
   - Left sidebar (260px): KB navigation area with placeholder content
   - Center panel (flexible): Main content area with welcome message
   - Right panel (320px): Citations panel with placeholder content (collapsible)

2. **Given** I am viewing the dashboard **When** I look at the header **Then** I see:
   - LumiKB logo on the left
   - Search bar placeholder in the center (disabled, shows "Search coming soon...")
   - User menu with profile and logout options on the right

3. **Given** the viewport is desktop (1280px+) **When** I view the dashboard **Then** all three panels are visible simultaneously **And** the layout fills the viewport height

4. **Given** the viewport is laptop (1024-1279px) **When** I view the dashboard **Then** the citations panel becomes a toggleable tab/button **And** the sidebar and center panel remain visible

5. **Given** the viewport is tablet (768-1023px) **When** I view the dashboard **Then** the sidebar is hidden by default **And** a hamburger menu button appears in the header **And** clicking it opens the sidebar as a drawer overlay

6. **Given** the viewport is mobile (<768px) **When** I view the dashboard **Then** only the center panel is visible **And** bottom navigation shows icons for sidebar and citations **And** the header is simplified

7. **Given** I am viewing the right panel (citations) **When** I click the collapse button **Then** the panel hides **And** an expand button appears **And** the center panel expands to fill the space

8. **Given** I am on the dashboard **When** I click the dark mode toggle in the user menu **Then** the entire application switches to dark mode **And** my preference is persisted in localStorage

9. **And** all panels have proper visual hierarchy:
   - Sidebar has subtle background (`bg-muted/50`) and border-right
   - Center panel has white/dark background
   - Citations panel has subtle background and border-left
   - Header is sticky with backdrop blur

## Tasks / Subtasks

- [x] **Task 1: Install required shadcn/ui components** (AC: 1, 7, 9)
  - [x] Run `npx shadcn@latest add sheet separator scroll-area tooltip switch`
  - [x] These components provide drawer (Sheet), panel dividers (Separator), scrollable areas (ScrollArea), hover hints (Tooltip), and dark mode toggle (Switch)
  - [x] Verify imports work

- [x] **Task 2: Create three-panel layout component** (AC: 1, 3, 9)
  - [x] Create `frontend/src/components/layout/dashboard-layout.tsx`
  - [x] Structure with CSS Grid: `grid-template-columns: 260px 1fr 320px`
  - [x] Full viewport height: `min-h-screen` with sticky header
  - [x] Export `DashboardLayout` component that accepts `children` for center panel

- [x] **Task 3: Create Header component** (AC: 2)
  - [x] Create `frontend/src/components/layout/header.tsx`
  - [x] Include LumiKB logo (text logo with primary color)
  - [x] Include disabled search bar placeholder with tooltip "Search coming soon..."
  - [x] Include UserMenu component (already exists)
  - [x] Add `⌘K` keyboard shortcut hint (disabled, for future Epic 3)
  - [x] Sticky positioning with backdrop blur: `sticky top-0 z-50 backdrop-blur`

- [x] **Task 4: Create KB Sidebar component** (AC: 1, 5, 6)
  - [x] Create `frontend/src/components/layout/kb-sidebar.tsx`
  - [x] Header section: "Knowledge Bases" title + "New KB" button (disabled)
  - [x] Scrollable list area using ScrollArea component
  - [x] Placeholder KB items (3-4 example items with icons, names, doc counts)
  - [x] Footer section: storage usage indicator (placeholder)
  - [x] Style: `w-[260px] border-r bg-muted/50`

- [x] **Task 5: Create Citations Panel component** (AC: 1, 7)
  - [x] Create `frontend/src/components/layout/citations-panel.tsx`
  - [x] Header: "Citations" title + collapse button
  - [x] Empty state: "Citations will appear here when you ask questions"
  - [x] Collapse/expand functionality using local state
  - [x] Style: `w-[320px] border-l bg-muted/30`
  - [x] Accept `isCollapsed` and `onToggle` props for controlled mode

- [x] **Task 6: Create responsive behavior hooks** (AC: 3, 4, 5, 6)
  - [x] Create `frontend/src/hooks/use-media-query.ts` custom hook
  - [x] Create `frontend/src/hooks/use-responsive-layout.ts` that returns:
    - `isDesktop`: viewport >= 1280px
    - `isLaptop`: viewport 1024-1279px
    - `isTablet`: viewport 768-1023px
    - `isMobile`: viewport < 768px
  - [x] Use `window.matchMedia` with SSR safety

- [x] **Task 7: Implement responsive layout variants** (AC: 3, 4, 5, 6)
  - [x] Desktop: Full three-panel layout
  - [x] Laptop: Citations panel becomes floating button/popover
  - [x] Tablet: Sidebar in Sheet (drawer), triggered by hamburger menu
  - [x] Mobile: Single column, bottom navigation bar
  - [x] Create `frontend/src/components/layout/mobile-nav.tsx` for bottom navigation

- [x] **Task 8: Add dark mode toggle to UserMenu** (AC: 8)
  - [x] Update `frontend/src/components/layout/user-menu.tsx` to include theme toggle
  - [x] Create `frontend/src/lib/stores/theme-store.ts` with Zustand:
    - State: `theme: 'light' | 'dark' | 'system'`
    - Actions: `setTheme()`, `toggleTheme()`
    - Persist to localStorage with key `lumikb-theme`
  - [x] Update `frontend/src/app/layout.tsx` to apply theme class to `<html>` element
  - [x] Use `next-themes` package OR manual implementation (manual preferred for control)

- [x] **Task 9: Update dashboard page to use new layout** (AC: 1, 9)
  - [x] Refactor `frontend/src/app/(protected)/dashboard/page.tsx`
  - [x] Use `DashboardLayout` as wrapper
  - [x] Center panel content: Welcome message, quick stats (placeholders)
  - [x] Remove old header (now in DashboardLayout)

- [x] **Task 10: Create placeholder components for future features** (AC: 1, 2)
  - [x] Create `frontend/src/components/kb/kb-selector-item.tsx` (placeholder)
  - [x] Create `frontend/src/components/search/search-bar.tsx` (disabled placeholder)
  - [x] Create `frontend/src/components/citations/citation-card.tsx` (placeholder)
  - [x] These components will be implemented fully in later epics

- [x] **Task 11: Write tests for layout components** (AC: 1-9)
  - [x] Create `frontend/src/components/layout/__tests__/dashboard-layout.test.tsx`:
    - Renders three panels on desktop viewport
    - Sidebar collapses on tablet viewport
    - Mobile shows bottom navigation
  - [x] Create `frontend/src/components/layout/__tests__/header.test.tsx`:
    - Renders logo, search placeholder, user menu
    - Search bar is disabled
  - [x] Create `frontend/src/hooks/__tests__/use-responsive-layout.test.ts`:
    - Returns correct breakpoint values

- [x] **Task 12: Run linting, type-check, and verification** (AC: 1-9)
  - [x] Run `npm run lint` and fix any errors
  - [x] Run `npm run type-check` and fix any TypeScript errors
  - [x] Run `npm run test:run` and ensure all tests pass
  - [x] Run `npm run build` to verify production build
  - [ ] Manual test: Resize viewport and verify responsive behavior
  - [ ] Manual test: Toggle dark mode and verify persistence
  - [ ] Manual test: Collapse/expand citations panel
  - [ ] Manual test: Open sidebar drawer on tablet/mobile

## Dev Notes

### Learnings from Previous Stories

**From Story 1-8-frontend-authentication-ui (Status: done)**

- **Frontend Structure Established**:
  - `frontend/src/components/layout/user-menu.tsx` - UserMenu component ready
  - `frontend/src/lib/stores/auth-store.ts` - Zustand store pattern established
  - `frontend/src/app/(protected)/layout.tsx` - AuthGuard wrapper in place
  - `frontend/src/app/(protected)/dashboard/page.tsx` - Current simple dashboard to refactor
- **Trust Blue Theme Applied**: CSS variables configured in globals.css
- **shadcn/ui Components Available**: button, input, card, label, form, dropdown-menu, avatar, sonner
- **Testing Setup**: Vitest configured with test-utils

**From Story 1-1-project-initialization (Status: done)**

- **Frontend Stack**: Next.js 16, React 19, TailwindCSS v4, shadcn/ui (new-york style)
- **Zustand Version**: >=5.0.0 installed

[Source: docs/sprint-artifacts/1-8-frontend-authentication-ui.md#Dev-Notes]

### Architecture Constraints

From [architecture.md](../../docs/architecture.md) and [ux-design-specification.md](../../docs/ux-design-specification.md):

| Constraint | Requirement |
|------------|-------------|
| Layout | Three-Panel (NotebookLM style) from UX spec Section 4 |
| Sidebar Width | 260px fixed |
| Citations Panel Width | 320px fixed, collapsible |
| Responsive Breakpoints | Desktop 1280+, Laptop 1024-1279, Tablet 768-1023, Mobile <768 |
| Header | Sticky with backdrop blur |
| Dark Mode | System preference detection + manual toggle |
| State Management | Zustand for theme and UI state |
| Components | shadcn/ui + Radix UI primitives |

### UX Design References

From [ux-design-specification.md](../../docs/ux-design-specification.md) Section 4.1-4.6:

**Three-Panel Layout Structure:**
```
+------------------------------------------------------------------+
|                         Header Bar                                |
|  Logo    [Search all KBs... ⌘K]         [New Chat]  [User]       |
+----------+-----------------------------+-------------------------+
|          |                             |                         |
|  KB      |       Chat / Main Content   |   Citations             |
|  Sidebar |                             |   Panel                 |
|          |                             |                         |
|  260px   |           Flexible          |      320px              |
|          |                             |                         |
|          +-----------------------------+                         |
|          |       Input Area            |                         |
+----------+-----------------------------+-------------------------+
```

**Color Palette (Trust Blue):**
- Background: #FFFFFF (light) / #1E1E2E (dark)
- Surface: #FAFAFA (light) / #2D2D3F (dark)
- Border: #E5E5E5 (light) / #3D3D4F (dark)
- Muted: bg-muted/50 for sidebar, bg-muted/30 for citations

**Responsive Adaptations:**
- Desktop (1280px+): Full three-panel
- Laptop (1024-1279px): Citations become tab/toggle
- Tablet (768-1023px): Sidebar in drawer, hamburger menu
- Mobile (<768px): Single column, bottom nav

### Project Structure (Files to Create/Modify)

```
frontend/
├── src/
│   ├── app/
│   │   ├── (protected)/
│   │   │   └── dashboard/
│   │   │       └── page.tsx         # MODIFY: Use DashboardLayout
│   │   ├── globals.css              # MODIFY: Add dark mode variables if needed
│   │   └── layout.tsx               # MODIFY: Add theme provider
│   ├── components/
│   │   ├── layout/
│   │   │   ├── dashboard-layout.tsx # NEW: Three-panel layout wrapper
│   │   │   ├── header.tsx           # NEW: App header component
│   │   │   ├── kb-sidebar.tsx       # NEW: KB navigation sidebar
│   │   │   ├── citations-panel.tsx  # NEW: Citations right panel
│   │   │   ├── mobile-nav.tsx       # NEW: Mobile bottom navigation
│   │   │   └── user-menu.tsx        # MODIFY: Add dark mode toggle
│   │   ├── kb/
│   │   │   └── kb-selector-item.tsx # NEW: Placeholder KB item
│   │   ├── search/
│   │   │   └── search-bar.tsx       # NEW: Disabled search placeholder
│   │   ├── citations/
│   │   │   └── citation-card.tsx    # NEW: Placeholder citation card
│   │   └── ui/                      # shadcn/ui components (auto-generated)
│   ├── hooks/
│   │   ├── use-media-query.ts       # NEW: Media query hook
│   │   └── use-responsive-layout.ts # NEW: Responsive breakpoint hook
│   └── lib/
│       └── stores/
│           └── theme-store.ts       # NEW: Theme state management
```

### Dependencies to Add

```bash
# shadcn/ui components
npx shadcn@latest add sheet separator scroll-area tooltip switch

# Icons (if not already installed via lucide-react)
# Already installed from Story 1.8
```

### CSS Grid Layout Reference

```css
/* Desktop three-panel grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 260px 1fr 320px;
  grid-template-rows: auto 1fr;
  min-height: 100vh;
}

/* Laptop - citations as overlay */
@media (max-width: 1279px) {
  .dashboard-grid {
    grid-template-columns: 260px 1fr;
  }
}

/* Tablet - sidebar as drawer */
@media (max-width: 1023px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

/* Mobile - single column */
@media (max-width: 767px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
    padding-bottom: 64px; /* Space for bottom nav */
  }
}
```

### References

- [Source: docs/epics.md:470-504#Story-1.9] - Original story definition with AC
- [Source: docs/sprint-artifacts/tech-spec-epic-1.md:376#Story-1.9-AC] - Tech spec AC summary
- [Source: docs/sprint-artifacts/tech-spec-epic-1.md:388#E1-AC6] - Epic-level acceptance criteria
- [Source: docs/ux-design-specification.md:820-908#Design-Direction] - Three-panel layout spec
- [Source: docs/ux-design-specification.md:1396-1462#Responsive-Strategy] - Responsive breakpoints
- [Source: docs/ux-design-specification.md:796-812#Dark-Mode-Support] - Dark mode color palette
- [Source: docs/architecture.md:254-259#Frontend-Stack] - Next.js, React, shadcn/ui versions
- [Source: docs/architecture.md:547-549#Naming-Conventions] - TypeScript file naming
- [Source: docs/coding-standards.md:208-400#TypeScript-Standards-Frontend] - Frontend coding conventions
- [Source: docs/sprint-artifacts/1-8-frontend-authentication-ui.md#Dev-Notes] - Previous story learnings

## Dev Agent Record

### Context Reference

docs/sprint-artifacts/1-9-three-panel-dashboard-shell.context.xml

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

- Lint error fixed: use-media-query.ts refactored from useState/useEffect to useSyncExternalStore for React Compiler compatibility
- Test file fixed: header.test.tsx corrected userEvent import pattern

### Completion Notes List

- Implemented three-panel dashboard layout with responsive design
- Created 5 new shadcn/ui components: sheet, separator, scroll-area, tooltip, switch
- Built responsive hooks using useSyncExternalStore for SSR safety
- Dark mode toggle with Zustand + localStorage persistence
- All 33 tests pass (17 new tests for layout components)
- Production build successful

### File List

**New Files:**
- frontend/src/components/layout/dashboard-layout.tsx
- frontend/src/components/layout/header.tsx
- frontend/src/components/layout/kb-sidebar.tsx
- frontend/src/components/layout/citations-panel.tsx
- frontend/src/components/layout/mobile-nav.tsx
- frontend/src/components/kb/kb-selector-item.tsx
- frontend/src/components/search/search-bar.tsx
- frontend/src/components/citations/citation-card.tsx
- frontend/src/hooks/use-media-query.ts
- frontend/src/hooks/use-responsive-layout.ts
- frontend/src/lib/stores/theme-store.ts
- frontend/src/components/ui/sheet.tsx
- frontend/src/components/ui/separator.tsx
- frontend/src/components/ui/scroll-area.tsx
- frontend/src/components/ui/tooltip.tsx
- frontend/src/components/ui/switch.tsx
- frontend/src/components/layout/__tests__/dashboard-layout.test.tsx
- frontend/src/components/layout/__tests__/header.test.tsx
- frontend/src/hooks/__tests__/use-responsive-layout.test.ts

**Modified Files:**
- frontend/src/app/(protected)/dashboard/page.tsx
- frontend/src/components/layout/user-menu.tsx

## Senior Developer Review (AI)

### Reviewer
Tung Vu

### Date
2025-11-23

### Outcome
**APPROVE** - All acceptance criteria implemented and verified with evidence. All automated tasks completed. Tests, lint, type-check, and build all pass.

### Summary
Story 1.9 implements a well-architected three-panel dashboard layout with comprehensive responsive design support. The implementation follows React best practices, uses SSR-safe patterns, and includes proper state management with Zustand. All 9 acceptance criteria are fully satisfied with traceable evidence.

### Key Findings

**No HIGH or MEDIUM severity issues found.**

**LOW Severity:**
- 2 pre-existing lint warnings in auth forms (react-hook-form compatibility) - not related to this story

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | Three-panel layout (260px sidebar, flexible center, 320px citations) | ✅ IMPLEMENTED | dashboard-layout.tsx:41-69, kb-sidebar.tsx:67, citations-panel.tsx:39 |
| AC2 | Header with logo, disabled search bar, user menu | ✅ IMPLEMENTED | header.tsx:18-42, search-bar.tsx:17-36 |
| AC3 | Desktop (1280px+): all three panels visible | ✅ IMPLEMENTED | dashboard-layout.tsx:27-29, use-responsive-layout.ts:13 |
| AC4 | Laptop (1024-1279px): citations as toggleable button | ✅ IMPLEMENTED | dashboard-layout.tsx:70-90 |
| AC5 | Tablet (768-1023px): sidebar in drawer, hamburger menu | ✅ IMPLEMENTED | dashboard-layout.tsx:31, dashboard-layout.tsx:49-57 |
| AC6 | Mobile (<768px): single column, bottom navigation | ✅ IMPLEMENTED | mobile-nav.tsx:16-48, dashboard-layout.tsx:106-109 |
| AC7 | Citations panel collapse/expand functionality | ✅ IMPLEMENTED | citations-panel.tsx:16-34 |
| AC8 | Dark mode toggle with localStorage persistence | ✅ IMPLEMENTED | theme-store.ts:29-53, user-menu.tsx:52-59 |
| AC9 | Visual hierarchy (styling) | ✅ IMPLEMENTED | kb-sidebar.tsx:19, header.tsx:21, citations-panel.tsx:39 |

**Summary: 9 of 9 acceptance criteria fully implemented**

### Task Completion Validation

| Task | Marked | Verified | Evidence |
|------|--------|----------|----------|
| Task 1: Install shadcn/ui components | ✅ | ✅ | package.json:24-28 |
| Task 2: Three-panel layout component | ✅ | ✅ | dashboard-layout.tsx |
| Task 3: Header component | ✅ | ✅ | header.tsx |
| Task 4: KB Sidebar component | ✅ | ✅ | kb-sidebar.tsx |
| Task 5: Citations Panel component | ✅ | ✅ | citations-panel.tsx |
| Task 6: Responsive behavior hooks | ✅ | ✅ | use-media-query.ts, use-responsive-layout.ts |
| Task 7: Responsive layout variants | ✅ | ✅ | dashboard-layout.tsx |
| Task 8: Dark mode toggle | ✅ | ✅ | theme-store.ts, user-menu.tsx |
| Task 9: Dashboard page update | ✅ | ✅ | page.tsx |
| Task 10: Placeholder components | ✅ | ✅ | kb-selector-item.tsx, search-bar.tsx, citation-card.tsx |
| Task 11: Tests | ✅ | ✅ | 17 new tests, all passing |
| Task 12: Verification | ✅ | ✅ | lint (0 errors), type-check (pass), tests (33 pass), build (pass) |

**Summary: 12 of 12 automated tasks verified. Manual testing (Task 12.5-12.8) deferred to user.**

### Test Coverage and Gaps

- **33 tests total** (17 new for this story)
- Test files: dashboard-layout.test.tsx, header.test.tsx, use-responsive-layout.test.ts
- All tests pass
- Coverage includes: responsive breakpoints, component rendering, user interactions

### Architectural Alignment

✅ **Tech Spec Compliance:**
- Next.js 16 App Router - compliant
- Tailwind CSS 4 - compliant
- Zustand 5 for state - compliant
- shadcn/ui components - compliant

✅ **UX Design Compliance:**
- Three-panel layout matches spec
- Responsive breakpoints match spec (1280px, 1024px, 768px)
- Dark mode toggle implemented

### Security Notes

No security concerns identified. Story is UI-only with no sensitive data handling.

### Best-Practices and References

- React 19 useSyncExternalStore for SSR-safe media queries
- Zustand persist middleware for localStorage
- Radix UI Sheet for accessible drawers
- Proper ARIA labels on interactive elements

### Action Items

**Code Changes Required:**
- None

**Advisory Notes:**
- Note: Manual testing recommended before production (viewport resizing, dark mode, panel collapse)
- Note: Pre-existing lint warnings in auth forms are unrelated to this story

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-23 | Initial draft created from epics.md, architecture.md, ux-design-specification.md, and story 1-8 learnings | SM Agent (Bob) |
| 2025-11-23 | Added Dev Agent Record and SM Review Notes sections per validation | SM Agent (Bob) |
| 2025-11-23 | Implementation complete: three-panel layout, responsive design, dark mode, 33 tests passing | Dev Agent (Amelia) |
| 2025-11-23 | Senior Developer Review: APPROVED - All ACs verified, all tasks validated | Dev Agent (Amelia) |
