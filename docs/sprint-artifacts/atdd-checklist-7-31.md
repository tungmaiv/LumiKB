# ATDD Checklist: Story 7-31 - View Mode Toggle for Chunk Viewer

## Story Overview
**Story ID:** 7-31
**Title:** View Mode Toggle for Chunk Viewer
**Epic:** 7 - Production Readiness & Configuration
**ATDD Status:** ✅ COMPLETE
**Date:** 2025-12-11

## Test Coverage Summary

| Test Type | Count | Status |
|-----------|-------|--------|
| Unit Tests (Hook) | 10 | ✅ Scaffolded |
| Unit Tests (Component) | 12 | ✅ Scaffolded |
| E2E Tests | 12 | ✅ Scaffolded |
| **Total** | **34** | ✅ |

## Acceptance Criteria Traceability

### AC-7.31.1: Toggle Component
**Requirement:** ViewModeToggle component renders with Original and Markdown options

| Test ID | Test Description | Type | Priority | File |
|---------|------------------|------|----------|------|
| VMT-U-01 | Render toggle with both Original and Markdown options | Unit | P0 | view-mode-toggle.test.tsx |
| VMT-U-02 | Render with FileText icon for Original option | Unit | P0 | view-mode-toggle.test.tsx |
| VMT-U-03 | Render with Code icon for Markdown option | Unit | P0 | view-mode-toggle.test.tsx |
| VMT-E-01 | View mode toggle shows both Original and Markdown options | E2E | P0 | document-chunk-viewer.spec.ts |

### AC-7.31.2: Default Mode
**Requirement:** Default to markdown when available, original when not

| Test ID | Test Description | Type | Priority | File |
|---------|------------------|------|----------|------|
| VMP-U-01 | Default to markdown when markdown is available | Unit | P0 | useViewModePreference.test.ts |
| VMP-U-02 | Default to original when markdown is not available | Unit | P0 | useViewModePreference.test.ts |
| VMP-U-03 | Respect stored "original" preference when markdown available | Unit | P0 | useViewModePreference.test.ts |
| VMP-U-04 | Force original when stored "markdown" but markdown unavailable | Unit | P0 | useViewModePreference.test.ts |
| VMT-E-02 | Default to markdown mode when markdown content available | E2E | P0 | document-chunk-viewer.spec.ts |
| VMT-E-03 | Fall back to original mode when markdown unavailable | E2E | P0 | document-chunk-viewer.spec.ts |

### AC-7.31.3: Disabled When Unavailable
**Requirement:** Markdown option disabled with tooltip when not available

| Test ID | Test Description | Type | Priority | File |
|---------|------------------|------|----------|------|
| VMT-U-04 | Disable Markdown option when markdown not available | Unit | P1 | view-mode-toggle.test.tsx |
| VMT-U-05 | Not disable Original option regardless of markdown availability | Unit | P1 | view-mode-toggle.test.tsx |
| VMT-U-06 | Show tooltip when Markdown disabled | Unit | P1 | view-mode-toggle.test.tsx |
| VMT-U-07 | Not call onChange when clicking disabled Markdown | Unit | P1 | view-mode-toggle.test.tsx |
| VMT-E-04 | Markdown option disabled when content unavailable | E2E | P1 | document-chunk-viewer.spec.ts |
| VMT-E-05 | Show tooltip explaining why markdown is disabled | E2E | P1 | document-chunk-viewer.spec.ts |

### AC-7.31.4: Preference Persistence
**Requirement:** User preference persists across sessions via localStorage

| Test ID | Test Description | Type | Priority | File |
|---------|------------------|------|----------|------|
| VMP-U-05 | Save preference to localStorage when mode changes | Unit | P1 | useViewModePreference.test.ts |
| VMP-U-06 | Load preference from localStorage on mount | Unit | P1 | useViewModePreference.test.ts |
| VMP-U-07 | Persist across mode switches | Unit | P1 | useViewModePreference.test.ts |
| VMP-U-08 | Handle invalid stored values gracefully | Unit | P1 | useViewModePreference.test.ts |
| VMT-E-06 | Persist preference across page reloads | E2E | P1 | document-chunk-viewer.spec.ts |

### AC-7.31.5: Visual Indication
**Requirement:** Selected mode clearly indicated visually

| Test ID | Test Description | Type | Priority | File |
|---------|------------------|------|----------|------|
| VMT-U-08 | Show Markdown as selected when value is markdown | Unit | P1 | view-mode-toggle.test.tsx |
| VMT-U-09 | Show Original as selected when value is original | Unit | P2 | view-mode-toggle.test.tsx |
| VMT-E-07 | Show clear visual indication of selected mode | E2E | P1 | document-chunk-viewer.spec.ts |

### AC-7.31.6: Unit Tests
**Requirement:** Unit tests for mode switching, persistence, disabled state

| Test ID | Test Description | Type | Priority | File |
|---------|------------------|------|----------|------|
| VMT-U-10 | Call onChange when Original is clicked | Unit | P0 | view-mode-toggle.test.tsx |
| VMT-U-11 | Call onChange when Markdown is clicked | Unit | P0 | view-mode-toggle.test.tsx |
| VMT-U-12 | Have accessible labels for screen readers | Unit | P2 | view-mode-toggle.test.tsx |
| VMP-U-09 | Update mode when markdownAvailable changes to false | Unit | P2 | useViewModePreference.test.ts |
| VMP-U-10 | Handle localStorage not being available | Unit | P2 | useViewModePreference.test.ts |
| VMT-E-08 | Switch from markdown to original view | E2E | P0 | document-chunk-viewer.spec.ts |
| VMT-E-09 | Switch from original to markdown view | E2E | P0 | document-chunk-viewer.spec.ts |

## Test Files

### Unit Tests
1. **Hook Tests:** `frontend/src/hooks/__tests__/useViewModePreference.test.ts`
   - 10 tests covering default mode, preference persistence, edge cases
   - Priority breakdown: P0 (4), P1 (4), P2 (2)

2. **Component Tests:** `frontend/src/components/documents/chunk-viewer/__tests__/view-mode-toggle.test.tsx`
   - 12 tests covering rendering, mode switching, disabled state, visual indication
   - Priority breakdown: P0 (5), P1 (5), P2 (2)

### E2E Tests
3. **E2E Tests:** `frontend/e2e/tests/documents/document-chunk-viewer.spec.ts`
   - Added `Story 7-31: View Mode Toggle` test.describe block
   - 12 tests covering all acceptance criteria
   - Priority breakdown: P0 (5), P1 (5), P2 (2)

## Implementation Files Required

The following files need to be implemented to make tests pass:

1. **Hook:** `frontend/src/hooks/useViewModePreference.ts`
   - Manages view mode state with localStorage persistence
   - Returns `{ viewMode, setViewMode }`
   - localStorage key: `lumikb-chunk-viewer-mode`

2. **Component:** `frontend/src/components/documents/chunk-viewer/view-mode-toggle.tsx`
   - Uses shadcn/ui ToggleGroup pattern
   - Props: `markdownAvailable`, `value`, `onChange`
   - Icons: FileText (Original), Code (Markdown)

3. **Integration:** Update chunk viewer page to include toggle

## Test Execution Commands

```bash
# Run unit tests
npm run test:run -- src/hooks/__tests__/useViewModePreference.test.ts
npm run test:run -- src/components/documents/chunk-viewer/__tests__/view-mode-toggle.test.tsx

# Run E2E tests
npx playwright test document-chunk-viewer.spec.ts --grep "Story 7-31"

# Run all Story 7-31 tests
npm run test:run -- --grep "7-31"
```

## Priority Legend
- **P0 (Critical):** Core functionality, must pass for story acceptance
- **P1 (High):** Important edge cases and error handling
- **P2 (Medium):** Nice-to-have coverage, accessibility

## Notes
- All tests are currently scaffolded (expect to fail until implementation)
- Tests follow existing codebase patterns from useMarkdownContent.test.ts
- E2E tests use mock API responses for markdown-content endpoint
- Component uses controlled pattern (value/onChange props)
