# Story 7-31: View Mode Toggle for Chunk Viewer (Frontend)

**Epic:** 7 - Infrastructure & DevOps
**Story Points:** 2
**Status:** Done
**Created:** 2025-12-11

---

## User Story

**As a** user,
**I want to** toggle between Original and Markdown view modes,
**So that** I can choose the viewing experience that works best for me.

---

## Background

Story 7-30 implements the enhanced markdown viewer with precise highlighting. This story adds a user-facing toggle that allows switching between the original document format (PDF/DOCX) and the markdown view.

Users may prefer:
- **Markdown view**: Precise chunk highlighting, faster loading, consistent format
- **Original view**: See exact document formatting, images, layout

---

## Acceptance Criteria

### AC-7.31.1: Toggle Component
**Given** I open Document Chunk Viewer
**Then** I see a view mode toggle in the viewer header area
**And** toggle has options: "Original" | "Markdown"

**Implementation Notes:**
- Use shadcn/ui `ToggleGroup` component
- Place in viewer toolbar/header area
- Clear visual design matching existing UI

### AC-7.31.2: Default Mode
**Given** markdown content is available for the document
**Then** Markdown view is selected by default

**Implementation Notes:**
- Check markdown availability first
- If available, default to Markdown
- If not, default to Original

### AC-7.31.3: Disabled When Unavailable
**Given** markdown content is not available (older document)
**Then** toggle is disabled with Markdown option grayed out
**And** Original view is shown

**Implementation Notes:**
- Disable Markdown option when `useMarkdownContent` returns null
- Show tooltip explaining why: "Markdown not available for this document"

### AC-7.31.4: Preference Persistence
**Given** I change view mode preference
**Then** preference is saved in localStorage
**And** persists across page refreshes

**Implementation Notes:**
- localStorage key: `lumikb-chunk-viewer-mode`
- Values: `"markdown"` | `"original"`
- Check stored preference on component mount

### AC-7.31.5: Visual Indication
**Given** toggle is displayed
**Then** current mode has clear visual indication (selected state)

**Implementation Notes:**
- Use `ToggleGroupItem` with `data-state="on"` styling
- Match existing UI patterns for toggle buttons

### AC-7.31.6: Unit Tests
**Given** toggle component tests exist
**Then** tests cover: mode switching, preference persistence, disabled state

---

## Technical Design

### View Mode Toggle Component

```typescript
// frontend/src/components/documents/chunk-viewer/view-mode-toggle.tsx

'use client';

import { useEffect, useState } from 'react';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { FileText, Code } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

const STORAGE_KEY = 'lumikb-chunk-viewer-mode';

type ViewMode = 'original' | 'markdown';

interface ViewModeToggleProps {
  markdownAvailable: boolean;
  value: ViewMode;
  onChange: (mode: ViewMode) => void;
}

export function ViewModeToggle({
  markdownAvailable,
  value,
  onChange,
}: ViewModeToggleProps) {
  // Load preference from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ViewMode | null;
    if (stored && (stored === 'original' || stored === 'markdown')) {
      // Only use stored if markdown is available, otherwise force original
      if (stored === 'markdown' && !markdownAvailable) {
        onChange('original');
      } else if (stored !== value) {
        onChange(stored);
      }
    }
  }, [markdownAvailable]);

  // Save preference when changed
  const handleChange = (newValue: string) => {
    if (newValue === 'original' || newValue === 'markdown') {
      localStorage.setItem(STORAGE_KEY, newValue);
      onChange(newValue);
    }
  };

  return (
    <TooltipProvider>
      <ToggleGroup
        type="single"
        value={value}
        onValueChange={handleChange}
        className="border rounded-md"
      >
        <ToggleGroupItem
          value="original"
          aria-label="Original view"
          className="px-3 py-1.5 text-sm"
        >
          <FileText className="h-4 w-4 mr-1.5" />
          Original
        </ToggleGroupItem>

        <Tooltip>
          <TooltipTrigger asChild>
            <span>
              <ToggleGroupItem
                value="markdown"
                aria-label="Markdown view"
                disabled={!markdownAvailable}
                className="px-3 py-1.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Code className="h-4 w-4 mr-1.5" />
                Markdown
              </ToggleGroupItem>
            </span>
          </TooltipTrigger>
          {!markdownAvailable && (
            <TooltipContent>
              <p>Markdown not available for this document</p>
            </TooltipContent>
          )}
        </Tooltip>
      </ToggleGroup>
    </TooltipProvider>
  );
}
```

### Custom Hook for View Mode State

```typescript
// frontend/src/hooks/useViewModePreference.ts

import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'lumikb-chunk-viewer-mode';

type ViewMode = 'original' | 'markdown';

export function useViewModePreference(markdownAvailable: boolean) {
  const [viewMode, setViewMode] = useState<ViewMode>('original');

  // Initialize from localStorage or default based on availability
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ViewMode | null;

    if (markdownAvailable) {
      // Default to markdown if available, unless user chose original
      setViewMode(stored === 'original' ? 'original' : 'markdown');
    } else {
      // Force original if markdown unavailable
      setViewMode('original');
    }
  }, [markdownAvailable]);

  // Persist preference
  const setMode = useCallback((mode: ViewMode) => {
    localStorage.setItem(STORAGE_KEY, mode);
    setViewMode(mode);
  }, []);

  return { viewMode, setViewMode: setMode };
}
```

### Integration with Chunk Viewer Page

```typescript
// In chunks/page.tsx

import { ViewModeToggle } from '@/components/documents/chunk-viewer/view-mode-toggle';
import { useViewModePreference } from '@/hooks/useViewModePreference';
import { useMarkdownContent } from '@/hooks/useMarkdownContent';

// In component:
const { data: markdownData, isLoading: markdownLoading } = useMarkdownContent({
  kbId,
  documentId,
});

const markdownAvailable = !!markdownData?.markdown_content;
const { viewMode, setViewMode } = useViewModePreference(markdownAvailable);

// In header/toolbar area:
<ViewModeToggle
  markdownAvailable={markdownAvailable}
  value={viewMode}
  onChange={setViewMode}
/>

// In viewer area:
{viewMode === 'markdown' && markdownAvailable ? (
  <EnhancedMarkdownViewer
    content={markdownData.markdown_content}
    highlightRange={selectedChunk ? {
      start: selectedChunk.char_start,
      end: selectedChunk.char_end,
    } : undefined}
  />
) : (
  <OriginalDocumentViewer document={document} />
)}
```

### Files to Create/Modify

| File | Changes |
|------|---------|
| `frontend/src/components/documents/chunk-viewer/view-mode-toggle.tsx` | New toggle component |
| `frontend/src/hooks/useViewModePreference.ts` | New hook for preference management |
| `frontend/src/app/(protected)/documents/[id]/chunks/page.tsx` | Integrate toggle |
| `frontend/src/components/documents/chunk-viewer/index.tsx` | Update viewer selection |
| `frontend/src/components/documents/chunk-viewer/__tests__/view-mode-toggle.test.tsx` | Component tests |
| `frontend/src/hooks/__tests__/useViewModePreference.test.ts` | Hook tests |

---

## Dependencies

### Prerequisites
- Story 7-30 (Enhanced Markdown Viewer with Highlighting)

### Blocked By
- Story 7-30 must be completed for markdown viewer to exist

### Blocks
- None (final story in Markdown-First feature chain)

---

## Test Plan

### Unit Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_toggle_renders` | Component renders with both options | Original and Markdown buttons visible |
| `test_toggle_default_markdown` | Default when markdown available | Markdown selected |
| `test_toggle_default_original` | Default when markdown unavailable | Original selected |
| `test_toggle_markdown_disabled` | Markdown unavailable | Markdown button disabled with tooltip |
| `test_toggle_onChange` | User clicks toggle | onChange called with new value |
| `test_preference_save` | Mode changed | localStorage updated |
| `test_preference_load` | Component mounts | Reads from localStorage |
| `test_preference_fallback` | Stored markdown but unavailable | Falls back to original |

### E2E Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_toggle_visible_in_viewer` | Open chunk viewer | Toggle visible in header |
| `test_toggle_switch_modes` | Click toggle options | View switches between modes |
| `test_toggle_persists` | Change mode, refresh | Same mode after refresh |
| `test_toggle_disabled_old_doc` | Open old document | Markdown toggle disabled |

---

## Definition of Done

- [x] `ViewModeToggle` component implemented
- [x] `useViewModePreference` hook implemented
- [x] Toggle renders in chunk viewer header
- [x] Original/Markdown modes switch correctly
- [x] Markdown disabled when unavailable (with tooltip)
- [x] Preference persisted in localStorage
- [x] Preference loaded on page refresh
- [x] Unit tests pass with coverage >= 80%
- [ ] E2E tests pass (scaffolded, deferred to Story 8-16)
- [x] Code review approved
- [x] ESLint/TypeScript checks pass

---

## Story Context References

- [Sprint Change Proposal](sprint-change-proposal-markdown-first-processing.md) - Feature rationale
- [Story 7-30](7-30-enhanced-markdown-viewer.md) - Prerequisite: markdown viewer
- [Epic 7: Infrastructure](../epics/epic-7-infrastructure.md) - Story 7.31
- [shadcn/ui ToggleGroup](https://ui.shadcn.com/docs/components/toggle-group) - Component reference

---

## Notes

- Use shadcn/ui `ToggleGroup` for consistent styling
- localStorage key follows existing app conventions
- Consider adding analytics event when mode changed (optional)
- Icon choices: `FileText` for Original, `Code` for Markdown
- Tooltip explains why Markdown is disabled for clarity
- This is the final story in the Markdown-First Document Processing feature chain

---

## Dev Agent Record

### Completion Notes
**Completed:** 2025-12-11
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

**Implementation Summary:**
- All 6 ACs satisfied (AC-7.31.1 through AC-7.31.6)
- `useViewModePreference` hook: localStorage persistence, SSR handling, markdown fallback
- `ViewModeToggle` component: shadcn ToggleGroup, disabled state with tooltip
- Integration verified in `chunks/page.tsx` (mobile + desktop layouts)
- 22/22 unit tests passing (10 hook + 12 component)
- 12 E2E tests scaffolded (deferred to Story 8-16)
- TypeScript and ESLint clean
- Code review approved with 95/100 quality score

**Feature Chain Complete:**
- 7-28: Markdown Generation Backend ✅
- 7-29: Markdown Content API ✅
- 7-30: Enhanced Markdown Viewer ✅
- 7-31: View Mode Toggle ✅
