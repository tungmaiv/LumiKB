# Story 7-30: Enhanced Markdown Viewer with Highlighting (Frontend)

**Epic:** 7 - Infrastructure & DevOps
**Story Points:** 3
**Status:** done
**Created:** 2025-12-11

---

## User Story

**As a** user viewing document chunks,
**I want** precise chunk highlighting in the markdown viewer,
**So that** I can see exactly which text corresponds to each chunk.

---

## Background

Currently, the chunk viewer has position accuracy issues with PDF and DOCX documents:
- PDF: Page-level navigation only
- DOCX: Scroll position estimation (imprecise ratio calculation)

Stories 7-28 and 7-29 provide markdown content for all documents. This story implements the frontend viewer that consumes that markdown and applies accurate character-based highlighting using `char_start` and `char_end` positions.

**Reference Implementation:** The existing `TextViewer` component (`frontend/src/components/documents/chunk-viewer/viewers/text-viewer.tsx`) already has line-based highlighting logic that can be adapted.

---

## Acceptance Criteria

### AC-7.30.1: Fetch Markdown Content
**Given** I open Document Chunk Viewer for a document
**When** markdown content is available
**Then** the viewer fetches markdown from `/markdown-content` endpoint

**Implementation Notes:**
- Create `useMarkdownContent` hook for data fetching
- Handle loading, error, and success states
- Return fallback indicator when markdown unavailable

### AC-7.30.2: Precise Highlighting
**Given** I select a chunk in the chunk list
**When** the chunk has `char_start` and `char_end` positions
**Then** exactly those characters are highlighted in the markdown view

**Implementation Notes:**
- Use character offset positions from chunk metadata
- Split markdown content into highlighted/non-highlighted spans
- Handle edge cases: overlapping chunks, empty chunks

### AC-7.30.3: Highlight Styling
**Given** a chunk is highlighted
**Then** highlight uses visible background color (e.g., `bg-yellow-200`)
**And** view auto-scrolls to bring highlighted text into viewport

**Implementation Notes:**
- Use Tailwind `bg-yellow-200` or similar for highlight
- Add `dark:bg-yellow-800` for dark mode support
- Use `scrollIntoView({ behavior: 'smooth', block: 'center' })` for scrolling

### AC-7.30.4: Graceful Fallback
**Given** markdown content is not available (404)
**Then** viewer shows original format viewer (PDF/DOCX)
**And** user sees subtle message "Precise highlighting not available"

**Implementation Notes:**
- Check `useMarkdownContent` hook response
- Fall back to existing viewer components
- Show non-intrusive info message

### AC-7.30.5: Loading State
**Given** markdown content is being fetched
**Then** viewer shows loading spinner/skeleton

**Implementation Notes:**
- Use existing Skeleton component from shadcn/ui
- Match loading state styling with other viewers

### AC-7.30.6: Unit Tests
**Given** highlighting logic tests exist
**Then** tests cover: highlight positioning, scroll behavior, fallback scenarios

---

## Technical Design

### New Hook: useMarkdownContent

```typescript
// frontend/src/hooks/useMarkdownContent.ts

import { useQuery } from '@tanstack/react-query';

interface MarkdownContentResponse {
  document_id: string;
  markdown_content: string;
  generated_at: string;
}

interface UseMarkdownContentOptions {
  kbId: string;
  documentId: string;
  enabled?: boolean;
}

export function useMarkdownContent({ kbId, documentId, enabled = true }: UseMarkdownContentOptions) {
  return useQuery<MarkdownContentResponse>({
    queryKey: ['markdown-content', kbId, documentId],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/knowledge-bases/${kbId}/documents/${documentId}/markdown-content`,
        { credentials: 'include' }
      );

      if (response.status === 404) {
        return null; // Markdown not available
      }

      if (!response.ok) {
        throw new Error('Failed to fetch markdown content');
      }

      return response.json();
    },
    enabled,
    staleTime: Infinity, // Markdown content is immutable
    retry: false, // Don't retry 404s
  });
}
```

### Enhanced Markdown Viewer Component

```typescript
// frontend/src/components/documents/chunk-viewer/viewers/enhanced-markdown-viewer.tsx

import { useRef, useEffect, useMemo } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import ReactMarkdown from 'react-markdown';

interface EnhancedMarkdownViewerProps {
  content: string;
  highlightRange?: {
    start: number;
    end: number;
  };
}

export function EnhancedMarkdownViewer({ content, highlightRange }: EnhancedMarkdownViewerProps) {
  const highlightRef = useRef<HTMLSpanElement>(null);

  // Scroll highlighted text into view
  useEffect(() => {
    if (highlightRange && highlightRef.current) {
      highlightRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [highlightRange]);

  // Split content into segments with highlight
  const segments = useMemo(() => {
    if (!highlightRange) {
      return [{ text: content, highlighted: false }];
    }

    const { start, end } = highlightRange;
    const segments = [];

    if (start > 0) {
      segments.push({ text: content.slice(0, start), highlighted: false });
    }

    segments.push({ text: content.slice(start, end), highlighted: true });

    if (end < content.length) {
      segments.push({ text: content.slice(end), highlighted: false });
    }

    return segments;
  }, [content, highlightRange]);

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none p-4 overflow-auto">
      {segments.map((segment, index) =>
        segment.highlighted ? (
          <span
            key={index}
            ref={highlightRef}
            className="bg-yellow-200 dark:bg-yellow-800 rounded px-0.5"
          >
            {segment.text}
          </span>
        ) : (
          <ReactMarkdown key={index}>{segment.text}</ReactMarkdown>
        )
      )}
    </div>
  );
}
```

### Files to Create/Modify

| File | Changes |
|------|---------|
| `frontend/src/hooks/useMarkdownContent.ts` | New hook for fetching markdown |
| `frontend/src/components/documents/chunk-viewer/viewers/enhanced-markdown-viewer.tsx` | New enhanced viewer component |
| `frontend/src/app/(protected)/documents/[id]/chunks/page.tsx` | Integrate enhanced viewer |
| `frontend/src/components/documents/chunk-viewer/index.tsx` | Add viewer selection logic |
| `frontend/src/hooks/__tests__/useMarkdownContent.test.ts` | Unit tests for hook |
| `frontend/src/components/documents/chunk-viewer/viewers/__tests__/enhanced-markdown-viewer.test.tsx` | Component tests |

### Integration with Chunk Viewer Page

```typescript
// In chunks/page.tsx

const { data: markdownData, isLoading: markdownLoading, isError } = useMarkdownContent({
  kbId,
  documentId,
  enabled: !!documentId,
});

// In render:
{markdownLoading && <Skeleton className="h-full w-full" />}

{markdownData ? (
  <EnhancedMarkdownViewer
    content={markdownData.markdown_content}
    highlightRange={selectedChunk ? {
      start: selectedChunk.char_start,
      end: selectedChunk.char_end,
    } : undefined}
  />
) : (
  // Fallback to original viewer
  <DocumentViewer document={document} />
)}
```

---

## Dependencies

### Prerequisites
- Story 7-29 (Markdown Content API Endpoint)

### Blocked By
- Story 7-29 must be completed for API to exist

### Blocks
- Story 7-31 (View Mode Toggle for Chunk Viewer)

---

## Test Plan

### Unit Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_useMarkdownContent_success` | Successful fetch | Returns markdown data |
| `test_useMarkdownContent_404` | Markdown not available | Returns null |
| `test_useMarkdownContent_error` | API error | Throws error |
| `test_highlight_positioning` | Highlight range applied | Correct spans created |
| `test_highlight_scroll` | Auto-scroll on highlight | scrollIntoView called |
| `test_fallback_display` | No markdown available | Original viewer shown |

### E2E Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_chunk_viewer_markdown_mode` | Open viewer with markdown doc | Markdown rendered with highlight |
| `test_chunk_selection_highlighting` | Select chunk in list | Text highlighted in viewer |
| `test_fallback_to_original` | Open viewer with old doc | Original viewer shown with message |

---

## Definition of Done

- [x] `useMarkdownContent` hook implemented and tested
- [x] `EnhancedMarkdownViewer` component implemented
- [x] Character-based highlighting working with char_start/char_end
- [x] Auto-scroll to highlighted text working
- [x] Graceful fallback to original viewer for older documents
- [x] Loading skeleton displayed during fetch
- [x] Dark mode support for highlight styling
- [x] Unit tests pass with coverage >= 80%
- [x] Code review approved
- [x] ESLint/TypeScript checks pass

---

## Story Context References

- [Sprint Change Proposal](sprint-change-proposal-markdown-first-processing.md) - Feature rationale
- [Story 7-29](7-29-markdown-content-api.md) - Prerequisite: API endpoint
- [Epic 7: Infrastructure](../epics/epic-7-infrastructure.md) - Story 7.30
- [text-viewer.tsx](../../frontend/src/components/documents/chunk-viewer/viewers/text-viewer.tsx) - Reference implementation for highlighting
- [chunk-viewer/index.tsx](../../frontend/src/components/documents/chunk-viewer/index.tsx) - Integration point

---

## Notes

- Reuse highlighting logic from existing TextViewer component
- ReactMarkdown rendering may need adjustment for inline highlights
- Consider code syntax highlighting with `react-syntax-highlighter` (optional)
- The viewer should handle very large documents efficiently (virtualization if needed)
- Story 7-31 will add the toggle between Original/Markdown views

---

## Senior Developer Review (AI)

**Reviewer:** Claude (AI Code Reviewer)
**Date:** 2025-12-11
**Review Type:** Comprehensive Code Review per BMAD Workflow

---

### Review Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| **Acceptance Criteria** | ✅ ALL PASS | 6/6 ACs validated with evidence |
| **Definition of Done** | ✅ 9/10 PASS | Only "Code review approved" pending |
| **Tests** | ✅ 34/34 PASS | 7 hook tests + 27 component tests |
| **TypeScript** | ✅ PASS | No errors in Story 7-30 files |
| **ESLint** | ⚠️ 1 WARNING | `<img>` vs `<Image>` - acceptable for markdown |
| **Security** | ✅ PASS | No vulnerabilities detected |

**OUTCOME: ✅ APPROVED**

---

### Acceptance Criteria Validation

#### AC-7.30.1: Fetch Markdown Content ✅
- **Evidence:** [useMarkdownContent.ts:36-60](frontend/src/hooks/useMarkdownContent.ts#L36-L60)
- **Implementation:** React Query hook fetches from `/api/v1/knowledge-bases/{kbId}/documents/{documentId}/markdown-content`
- **Test Coverage:** `useMarkdownContent.test.ts` - 7 tests covering success, 404, errors, disabled states

#### AC-7.30.2: Precise Highlighting ✅
- **Evidence:** [enhanced-markdown-viewer.tsx:82-103](frontend/src/components/documents/chunk-viewer/viewers/enhanced-markdown-viewer.tsx#L82-L103)
- **Implementation:** Character-based segmentation using `char_start`/`char_end` with safe bounds checking
- **Test Coverage:** Tests for highlight positioning, edge cases (start/middle/end), boundary conditions

#### AC-7.30.3: Highlight Styling ✅
- **Evidence:** [enhanced-markdown-viewer.tsx:189-191](frontend/src/components/documents/chunk-viewer/viewers/enhanced-markdown-viewer.tsx#L189-L191)
- **Implementation:** `bg-yellow-200 dark:bg-yellow-800` with `scrollIntoView({ behavior: 'smooth', block: 'center' })`
- **Test Coverage:** Tests verify className application and scrollIntoView invocation

#### AC-7.30.4: Graceful Fallback ✅
- **Evidence:** [chunks/page.tsx:263-280](frontend/src/app/(protected)/documents/[id]/chunks/page.tsx#L263-L280)
- **Implementation:** Falls back to PDF/DOCX viewers when markdown unavailable, shows "Precise highlighting not available" message
- **Test Coverage:** Component tests for fallback message display

#### AC-7.30.5: Loading State ✅
- **Evidence:** [enhanced-markdown-viewer.tsx:122-134](frontend/src/components/documents/chunk-viewer/viewers/enhanced-markdown-viewer.tsx#L122-L134)
- **Implementation:** Skeleton loading states matching existing viewer patterns
- **Test Coverage:** Tests for isLoading state rendering

#### AC-7.30.6: Unit Tests ✅
- **Evidence:** 34 tests total (7 hook + 27 component)
- **Coverage:** Highlight positioning, scroll behavior, fallback scenarios, loading/error states, edge cases
- **Result:** All 34 tests pass

---

### Code Quality Assessment

#### Strengths
1. **Clean Architecture:** Hook separates data fetching from presentation
2. **Type Safety:** Full TypeScript coverage with explicit interfaces
3. **Error Handling:** Graceful 404 handling returns null (not error)
4. **Performance:** `staleTime: Infinity` prevents unnecessary refetches
5. **Accessibility:** Semantic markdown rendering with proper heading hierarchy
6. **Dark Mode:** Full theme support for highlighting

#### Minor Issues (Non-blocking)

| Issue | Location | Severity | Recommendation |
|-------|----------|----------|----------------|
| ESLint `<img>` warning | Line 256 | Low | Acceptable - external markdown images can't use Next.js Image optimization |

---

### Test Results

```
✓ src/hooks/__tests__/useMarkdownContent.test.ts (7 tests) 235ms
✓ src/components/documents/chunk-viewer/viewers/__tests__/enhanced-markdown-viewer.test.tsx (27 tests) 274ms

Test Files  2 passed (2)
Tests       34 passed (34)
Duration    842ms
```

---

### Security Review

- **XSS Prevention:** ReactMarkdown with default sanitization
- **API Security:** Credentials included for auth, proper error handling
- **Input Validation:** Safe bounds checking on character ranges

---

### Files Reviewed

| File | Lines | Status |
|------|-------|--------|
| `frontend/src/hooks/useMarkdownContent.ts` | 78 | ✅ Clean |
| `frontend/src/components/documents/chunk-viewer/viewers/enhanced-markdown-viewer.tsx` | 274 | ✅ Clean |
| `frontend/src/app/(protected)/documents/[id]/chunks/page.tsx` | 516 | ✅ Integration correct |
| `frontend/src/hooks/__tests__/useMarkdownContent.test.ts` | 209 | ✅ Comprehensive |
| `frontend/src/components/documents/chunk-viewer/viewers/__tests__/enhanced-markdown-viewer.test.tsx` | 431 | ✅ Comprehensive |
| `frontend/src/components/documents/chunk-viewer/viewers/index.ts` | - | ✅ Export added |

---

### Final Verdict

**✅ APPROVED** - Story 7-30 meets all acceptance criteria and Definition of Done items. Implementation is clean, well-tested, and follows project patterns. The single ESLint warning is acceptable given the markdown rendering context.

**Ready to move to DONE status.**
