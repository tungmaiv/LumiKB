# Story 5.21: Theme System

## Story

**As a** user,
**I want** to choose from multiple color themes for the application,
**So that** I can personalize my experience and reduce eye strain.

## Status

| Field          | Value                                           |
| -------------- | ----------------------------------------------- |
| **Priority**   | LOW                                             |
| **Points**     | 1                                               |
| **Sprint**     | Epic 5 - Administration & Polish               |
| **Owner**      | Amelia (Dev)                                    |
| **Created**    | 2025-12-05                                      |
| **Status**     | DONE                                            |
| **Completed**  | 2025-12-05                                      |

## Context

Users requested additional theme options beyond the default light/dark toggle. This story adds two new themes (Light Blue, Dark Navy) and converts the simple toggle to a theme selector submenu in the user menu.

**Existing Infrastructure:**
- Theme store: `frontend/src/lib/stores/theme-store.ts` (Zustand with persist)
- User menu: `frontend/src/components/layout/user-menu.tsx`
- Global CSS: `frontend/src/app/globals.css`

## Prerequisites

| Dependency | Description | Status |
| ---------- | ----------- | ------ |
| None       | Uses existing theme infrastructure | N/A |

## Acceptance Criteria

### AC-5.21.1: Five Theme Options Available

**Given** users want theme variety
**When** I open the theme selector
**Then** I see 5 theme options:
- Light (default light theme - Trust Blue)
- Dark (default dark theme)
- Light Blue (soft sky blue tones)
- Dark Navy (deep professional navy)
- System (follow OS preference)

**And** each theme has consistent CSS variables for all UI components

**Verification:** ✅ PASSED
- `THEMES` constant in [theme-store.ts:6-12](frontend/src/lib/stores/theme-store.ts#L6-L12) defines all 5 options
- CSS variables defined in [globals.css:157-265](frontend/src/app/globals.css#L157-L265)

### AC-5.21.2: Theme Selector Submenu Implemented

**Given** theme selection was previously a simple toggle
**When** I click on my user avatar and open the dropdown
**Then** I see a "Theme" submenu with a palette icon
**And** hovering/clicking shows all 5 theme options
**And** current theme shows a checkmark indicator
**And** selecting a theme immediately applies it

**Verification:** ✅ PASSED
- Theme submenu in [user-menu.tsx:69-91](frontend/src/components/layout/user-menu.tsx#L69-L91)
- Palette icon imported at line 4
- Checkmark indicator at lines 81-85
- Immediate application via `setTheme(t.value)` at line 79

### AC-5.21.3: Theme Persistence Works

**Given** I select a theme
**When** I refresh the page or return later
**Then** my selected theme is preserved
**And** theme preference is stored in localStorage via Zustand persist

**Verification:** ✅ PASSED
- Zustand persist middleware in [theme-store.ts:40-67](frontend/src/lib/stores/theme-store.ts#L40-L67)
- localStorage key: `lumikb-theme` (line 59)
- `onRehydrateStorage` callback reapplies theme on page load (lines 60-64)

### AC-5.21.4: All UI Components Theme-Consistent

**Given** a theme is selected
**When** I navigate through the application
**Then** all components (cards, tables, modals, popovers, sidebar) use theme colors
**And** there are no white/mismatched boxes on colored backgrounds
**And** text remains readable with appropriate contrast

**Verification:** ✅ PASSED
- CSS variables cover all UI primitives: `--background`, `--foreground`, `--card`, `--primary`, `--secondary`, `--muted`, `--accent`, `--border`, `--input`, `--ring`
- All shadcn/ui components use CSS variable system
- Contrast ratios verified for WCAG 2.1 AA compliance

## Tasks

### Task 1: Define Theme Types and Constants (AC: #1)

- [x] 1.1 Extend Theme type: `'light' | 'dark' | 'light-blue' | 'dark-navy' | 'system'`
- [x] 1.2 Create THEMES constant with value, label, description for each theme
- [x] 1.3 Export THEMES for UI consumption
- **Verification:** [theme-store.ts:4-12](frontend/src/lib/stores/theme-store.ts#L4-L12)

### Task 2: Add CSS Variables for New Themes (AC: #1, #4)

- [x] 2.1 Add `.light-blue` class with sky blue CSS variables
- [x] 2.2 Add `.dark-navy` class with deep navy CSS variables
- [x] 2.3 Ensure all existing CSS variables are defined for both themes
- [x] 2.4 Verify contrast ratios for accessibility
- **Verification:** [globals.css:157-265](frontend/src/app/globals.css#L157-L265)

### Task 3: Update Theme Application Logic (AC: #1, #3)

- [x] 3.1 Modify `applyTheme()` to handle all 5 theme values
- [x] 3.2 Handle 'system' theme by detecting OS preference
- [x] 3.3 Remove old theme classes before applying new one
- **Verification:** [theme-store.ts:30-38](frontend/src/lib/stores/theme-store.ts#L30-L38)

### Task 4: Create Theme Selector Submenu (AC: #2)

- [x] 4.1 Import DropdownMenuSub components from shadcn/ui
- [x] 4.2 Add Palette icon from lucide-react
- [x] 4.3 Create submenu with all 5 theme options
- [x] 4.4 Add checkmark indicator for current theme
- [x] 4.5 Wire up onClick to setTheme
- **Verification:** [user-menu.tsx:69-91](frontend/src/components/layout/user-menu.tsx#L69-L91)

### Task 5: Verify Persistence (AC: #3)

- [x] 5.1 Confirm Zustand persist middleware is configured
- [x] 5.2 Test localStorage key `lumikb-theme`
- [x] 5.3 Verify onRehydrateStorage applies theme on load
- **Verification:** Manual testing confirmed

## Technical Implementation

### Architecture

```
frontend/
├── src/lib/stores/
│   └── theme-store.ts          # MODIFIED: Extended Theme type, THEMES constant
├── src/components/layout/
│   └── user-menu.tsx           # MODIFIED: Theme selector submenu
└── src/app/
    └── globals.css             # MODIFIED: .light-blue, .dark-navy CSS classes
```

### Theme Store Implementation

```typescript
// frontend/src/lib/stores/theme-store.ts
type Theme = 'light' | 'dark' | 'light-blue' | 'dark-navy' | 'system';

export const THEMES = [
  { value: 'light', label: 'Light', description: 'Default light theme' },
  { value: 'dark', label: 'Dark', description: 'Default dark theme' },
  { value: 'light-blue', label: 'Light Blue', description: 'Soft sky blue theme' },
  { value: 'dark-navy', label: 'Dark Navy', description: 'Deep professional navy' },
  { value: 'system', label: 'System', description: 'Follow system preference' },
] as const;

// Zustand store with persist middleware
export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      theme: 'system',
      setTheme: (theme: Theme) => {
        set({ theme });
        applyTheme(theme);
      },
      // ...
    }),
    { name: 'lumikb-theme' }
  )
);
```

### CSS Variables (Light Blue Theme)

```css
/* frontend/src/app/globals.css */
.light-blue {
  --background: #e0f2fe;
  --foreground: #0c4a6e;
  --card: #f0f9ff;
  --primary: #0284c7;
  --secondary: #7dd3fc;
  --muted: #bae6fd;
  --accent: #38bdf8;
  --border: #7dd3fc;
  /* ... */
}
```

### CSS Variables (Dark Navy Theme)

```css
/* frontend/src/app/globals.css */
.dark-navy {
  --background: #0a1628;
  --foreground: #e2e8f0;
  --card: #111d32;
  --primary: #3b82f6;
  --secondary: #1e3a5f;
  --muted: #1e293b;
  --accent: #60a5fa;
  --border: #1e3a5f;
  /* ... */
}
```

## Testing Requirements

### Manual Testing

| Test Case | Status |
| --------- | ------ |
| Select Light theme → UI updates immediately | ✅ |
| Select Dark theme → UI updates immediately | ✅ |
| Select Light Blue theme → UI updates with sky blue colors | ✅ |
| Select Dark Navy theme → UI updates with navy colors | ✅ |
| Select System theme → Follows OS preference | ✅ |
| Refresh page → Theme persists | ✅ |
| Open new tab → Theme persists | ✅ |
| All components use theme colors (no white boxes) | ✅ |
| Text contrast is readable in all themes | ✅ |

### Automated Testing

No automated tests required for this UX polish story. Theme functionality verified via manual testing.

## Dev Notes

### Design Decisions

1. **5 themes chosen**: Light, Dark, Light Blue, Dark Navy, System covers most user preferences without overwhelming options
2. **CSS variables approach**: Enables consistent theming across all shadcn/ui components without individual component updates
3. **Zustand persist**: Simple, reliable localStorage persistence without server roundtrips
4. **System theme**: Respects OS preference for accessibility

### Implementation Notes

- `applyTheme()` removes all theme classes before adding new one to prevent conflicts
- `getSystemTheme()` uses `window.matchMedia('(prefers-color-scheme: dark)')` for OS detection
- `onRehydrateStorage` ensures theme is applied on initial page load before hydration

### Files Modified

| File | Changes |
| ---- | ------- |
| [frontend/src/lib/stores/theme-store.ts](frontend/src/lib/stores/theme-store.ts) | Extended Theme type, added THEMES constant, updated applyTheme() |
| [frontend/src/components/layout/user-menu.tsx](frontend/src/components/layout/user-menu.tsx) | Added theme selector submenu with DropdownMenuSub |
| [frontend/src/app/globals.css](frontend/src/app/globals.css) | Added .light-blue and .dark-navy CSS classes |

## Definition of Done

- [x] All acceptance criteria implemented and verified
- [x] Theme selector submenu functional in user menu
- [x] All 5 themes apply correctly
- [x] Theme persists across page refresh
- [x] All UI components use theme colors consistently
- [x] No TypeScript errors
- [x] No ESLint warnings
- [x] Accessible (keyboard navigation works)
- [x] Code reviewed

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/5-21-theme-system.context.xml`

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes

Story 5.21 was implemented on 2025-12-05 as a UX polish feature. All 4 acceptance criteria satisfied. Implementation followed existing patterns in the codebase. No backend changes required.

### File List

| File | Status | Notes |
| ---- | ------ | ----- |
| `frontend/src/lib/stores/theme-store.ts` | Modified | Extended Theme type, THEMES constant |
| `frontend/src/components/layout/user-menu.tsx` | Modified | Theme selector submenu |
| `frontend/src/app/globals.css` | Modified | .light-blue, .dark-navy classes |

## Changelog

| Date       | Author | Change |
| ---------- | ------ | ------ |
| 2025-12-05 | Amelia (Dev) | Story implemented and completed |
| 2025-12-06 | Bob (SM) | Story file created retroactively for documentation completeness |
