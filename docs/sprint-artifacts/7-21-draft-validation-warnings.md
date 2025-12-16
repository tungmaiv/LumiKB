# Story 7-21: Draft Validation Warnings

| Field | Value |
|-------|-------|
| **Story ID** | 7-21 |
| **Epic** | Epic 7 - Tech Debt Sprint (Pre-Epic 8) |
| **Priority** | MEDIUM |
| **Effort** | 4 hours |
| **Resolves** | TD-4.6-1 |
| **Status** | Done |
| **Context** | [7-21-draft-validation-warnings.context.xml](7-21-draft-validation-warnings.context.xml) |

## User Story

**As a** document author
**I want** to see warnings when my draft has citation issues
**So that** I can fix orphaned or unused citations before exporting

## Background

Story 4-6 (Draft Editing) implemented the draft editor but deferred citation validation warnings. When a user edits a draft, citations may become orphaned (referenced but not in source list) or unused (in source list but never referenced). This story adds real-time validation and auto-fix suggestions.

## Acceptance Criteria

### AC-7.21.1: Orphaned Citation Detection
- **Given** a draft contains a citation reference `[1]`
- **When** citation `[1]` is not in the sources list
- **Then** a warning banner shows: "Citation [1] references a missing source"

### AC-7.21.2: Unused Citation Detection
- **Given** a draft has source `[2]` in the citations list
- **When** `[2]` is not referenced anywhere in the draft content
- **Then** a warning shows: "Source [2] is defined but never used"

### AC-7.21.3: Real-time Validation
- **Given** the user is editing the draft
- **When** they add or remove a citation reference
- **Then** validation runs within 500ms (debounced)
- **And** warnings update accordingly

### AC-7.21.4: Auto-fix for Unused Citations
- **Given** an unused citation warning is shown
- **When** the user clicks "Remove unused"
- **Then** the citation is removed from the sources list
- **And** remaining citations are renumbered

### AC-7.21.5: Warning Dismissal
- **Given** a validation warning is shown
- **When** the user clicks "Dismiss"
- **Then** the warning is hidden for this editing session
- **And** reappears if the issue recurs after edit

### AC-7.21.6: Unit Test Coverage
- **Given** the implementation is complete
- **When** unit tests run
- **Then** validation logic has ≥80% coverage

## Tasks

### Task 1: Create Validation Logic
- [ ] 1.1 Create `useCitationValidation` hook
- [ ] 1.2 Implement orphaned citation detection (regex scan for `[n]`)
- [ ] 1.3 Implement unused citation detection
- [ ] 1.4 Add debouncing (500ms) for real-time validation

### Task 2: Warning Banner Component
- [ ] 2.1 Create `CitationWarningBanner` component
- [ ] 2.2 Style with warning colors (amber/yellow)
- [ ] 2.3 Add dismiss button
- [ ] 2.4 Add auto-fix action button

### Task 3: Integrate into DraftEditor
- [ ] 3.1 Add validation hook to DraftEditor
- [ ] 3.2 Display warning banner above editor
- [ ] 3.3 Handle dismiss state
- [ ] 3.4 Handle auto-fix action

### Task 4: Citation Renumbering
- [ ] 4.1 Implement citation renumbering utility
- [ ] 4.2 Update content references when citation removed
- [ ] 4.3 Update sources list order

### Task 5: Testing
- [ ] 5.1 Unit test orphaned detection
- [ ] 5.2 Unit test unused detection
- [ ] 5.3 Unit test debouncing
- [ ] 5.4 Unit test auto-fix renumbering

## Dev Notes

### Implementation Pattern
```tsx
// useCitationValidation.ts
import { useDebounce } from '@/hooks/useDebounce';

interface ValidationResult {
  orphanedCitations: number[];  // [1, 3] = citations referenced but not defined
  unusedCitations: number[];    // [2] = citations defined but not used
}

export function useCitationValidation(content: string, citations: Citation[]) {
  const debouncedContent = useDebounce(content, 500);

  const validation = useMemo<ValidationResult>(() => {
    // Find all [n] references in content
    const referenced = new Set(
      [...debouncedContent.matchAll(/\[(\d+)\]/g)].map(m => parseInt(m[1]))
    );

    // Find all defined citation numbers
    const defined = new Set(citations.map((_, i) => i + 1));

    return {
      orphanedCitations: [...referenced].filter(n => !defined.has(n)),
      unusedCitations: [...defined].filter(n => !referenced.has(n))
    };
  }, [debouncedContent, citations]);

  return validation;
}
```

```tsx
// CitationWarningBanner.tsx
export function CitationWarningBanner({
  orphaned,
  unused,
  onRemoveUnused,
  onDismiss
}: Props) {
  if (orphaned.length === 0 && unused.length === 0) return null;

  return (
    <Alert variant="warning">
      {orphaned.length > 0 && (
        <p>Citations {orphaned.join(', ')} reference missing sources</p>
      )}
      {unused.length > 0 && (
        <div>
          <p>Sources {unused.join(', ')} are never referenced</p>
          <Button size="sm" onClick={onRemoveUnused}>Remove unused</Button>
        </div>
      )}
      <Button variant="ghost" size="sm" onClick={onDismiss}>Dismiss</Button>
    </Alert>
  );
}
```

### Key Files
- `frontend/src/hooks/useCitationValidation.ts` - New validation hook
- `frontend/src/components/generation/citation-warning-banner.tsx` - New component
- `frontend/src/components/generation/draft-editor.tsx` - Integration
- `frontend/src/hooks/useDebounce.ts` - Existing utility

### Dependencies
- DraftEditor (Story 4-6) - COMPLETED
- useDebounce hook - EXISTS

## Testing Strategy

### Unit Tests
- Test orphaned detection with various content patterns
- Test unused detection with citation list
- Test debounce timing
- Test renumbering logic

## Definition of Done
- [x] All ACs pass
- [x] Unit tests ≥80% coverage on modified files
- [x] No eslint errors
- [x] Code reviewed

## Dev Agent Record

### Completion Summary (2025-12-10)

**Code Review:** APPROVED (see [code-review-stories-7-21-7-22-7-23.md](code-review-stories-7-21-7-22-7-23.md))

**Test Results:**
- 39/39 tests passing (19 hook tests + 20 component tests)
- Fixed: Test timing issue with fake timers (`vi.useFakeTimers()` / `vi.advanceTimersByTime()`)

**Files Implemented:**
- `frontend/src/hooks/useCitationValidation.ts` - Validation hook with debounce (283 lines)
- `frontend/src/hooks/useDebounce.ts` - Debounce utility (34 lines)
- `frontend/src/components/generation/citation-warning-banner.tsx` - Warning UI component (~150 lines)
- `frontend/src/hooks/__tests__/useCitationValidation.test.ts` - Hook tests (319 lines)
- `frontend/src/components/generation/__tests__/citation-warning-banner.test.tsx` - Component tests (~300 lines)

**Key Features:**
- Orphaned citation detection (AC-7.21.1)
- Unused citation detection (AC-7.21.2)
- Debounced validation at 500ms (AC-7.21.3)
- Auto-fix with renumbering (AC-7.21.4, AC-7.21.6)
- Dismissable warnings with recurrence (AC-7.21.5)

**Tech Debt Resolved:** TD-4.6-1
