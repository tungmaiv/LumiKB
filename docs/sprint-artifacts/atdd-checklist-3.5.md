# ATDD Checklist: Story 3.5 - Citation Preview & Source Navigation

**Date:** 2025-11-25
**Story ID:** 3.5
**Status:** RED Phase (Tests Failing - Implementation Pending)

---

## Story Summary

**Epic**: 3 - Semantic Search & Citations
**Story**: 3.5 - Citation Preview & Source Navigation

**Description:**
Enhance citation UX by providing a preview modal that shows the full context around a cited passage. Users can see surrounding text (±200 characters) before navigating to the full document.

**Priority:** P1 - High (Important UX enhancement)

**User Value:**
- Verify citation accuracy without leaving search results
- Understand context before opening full document
- Faster citation validation workflow

---

## Acceptance Criteria Breakdown

| AC ID | Requirement | Test Level | Test File | Status |
|-------|------------|------------|-----------|--------|
| AC-3.5.1 | Preview modal opens when citation clicked | Component | `citation-preview.test.tsx::test_display_preview_modal_when_Preview_button_clicked` | ❌ RED |
| AC-3.5.2 | Preview shows surrounding text context (±200 chars) | Component | `citation-preview.test.tsx::test_display_surrounding_text_context_around_excerpt` | ❌ RED |
| AC-3.5.3 | "Open in Document" navigates with highlighting | Component | `citation-preview.test.tsx::test_navigate_to_document_when_Open_Document_button_clicked` | ❌ RED |
| AC-3.5.4 | Preview displays document metadata | Component | `citation-preview.test.tsx::test_display_document_metadata_in_preview_header` | ❌ RED |

**Total Tests**: 12 component tests (10 primary + 2 accessibility)

---

## Test Files Created

### Component Tests

**File**: `frontend/src/components/search/__tests__/citation-preview.test.tsx`

**Tests (12 component tests):**
1. ✅ `test_display_preview_modal_when_Preview_button_clicked` - Modal rendering
2. ✅ `test_not_render_modal_when_isOpen_is_false` - Conditional rendering
3. ✅ `test_display_surrounding_text_context_around_excerpt` - Context display
4. ✅ `test_highlight_the_cited_excerpt_within_context` - Excerpt highlighting
5. ✅ `test_display_document_metadata_in_preview_header` - Metadata display
6. ✅ `test_navigate_to_document_when_Open_Document_button_clicked` - Navigation
7. ✅ `test_close_modal_when_close_button_clicked` - Close button
8. ✅ `test_close_modal_when_Escape_key_pressed` - Keyboard interaction
9. ✅ `test_close_modal_when_clicking_outside_overlay` - Click outside
10. ✅ `test_show_loading_state_while_fetching_full_context` - Loading state
11. ✅ `test_have_proper_ARIA_attributes_for_accessibility` - Accessibility
12. ✅ `test_trap_focus_within_modal_when_open` - Focus management

---

## Supporting Infrastructure

### Citation Preview Data Model

The `CitationPreview` component receives extended citation data with full context:

```typescript
interface CitationWithContext {
  // Standard citation fields (from Story 3.2)
  number: number;
  documentId: string;
  documentName: string;
  pageNumber: number | null;
  sectionHeader: string | null;
  excerpt: string;
  charStart: number;
  charEnd: number;

  // Extended fields for preview
  fullContext?: string; // Full text context (±200 chars)
}
```

### Backend API Extension (Optional)

**Option A: Frontend calculates context** (Recommended for MVP)
- Frontend already has `excerpt` from Story 3.2
- Preview just displays `excerpt` (no additional backend call)
- Simpler implementation

**Option B: Backend provides full context**
- Add endpoint: `GET /api/v1/documents/{doc_id}/context?charStart={start}&charEnd={end}`
- Returns full context with ±200 chars
- Better for long excerpts or complex formatting

**Recommendation**: Use Option A (frontend-only) for MVP, add Option B if users request more context.

---

## Implementation Checklist

### RED Phase (Complete ✅)

- [x] All 12 tests written and failing
- [x] Component interface defined
- [x] Test data fixtures created

### GREEN Phase (DEV Team - Implementation Tasks)

#### Task 1: Create CitationPreview Component

- [ ] Create `frontend/src/components/search/citation-preview.tsx`
- [ ] Implement component props:
  ```typescript
  interface CitationPreviewProps {
    citation: CitationWithContext;
    isOpen: boolean;
    onClose: () => void;
    isLoading?: boolean;
  }
  ```
- [ ] Use shadcn/ui Dialog component:
  ```bash
  npx shadcn@latest add dialog
  ```
- [ ] Run test: `test_display_preview_modal_when_Preview_button_clicked`
- [ ] ✅ Test passes (modal renders)

#### Task 2: Display Full Context with Highlighting

- [ ] Render `citation.fullContext` (or `citation.excerpt` if context unavailable)
- [ ] Highlight excerpt within context:
  ```tsx
  const renderContextWithHighlight = () => {
    // Split context into: before + excerpt + after
    const before = fullContext.substring(0, excerptStartIndex);
    const highlighted = citation.excerpt;
    const after = fullContext.substring(excerptEndIndex);

    return (
      <div data-testid="citation-context">
        <span>{before}</span>
        <mark data-testid="highlighted-excerpt" className="bg-yellow-200">
          {highlighted}
        </mark>
        <span>{after}</span>
      </div>
    );
  };
  ```
- [ ] Run tests:
  - `test_display_surrounding_text_context_around_excerpt`
  - `test_highlight_the_cited_excerpt_within_context`
- [ ] ✅ Tests pass (context displayed with highlighting)

#### Task 3: Display Document Metadata

- [ ] Render preview header with metadata:
  ```tsx
  <DialogHeader>
    <div className="flex items-center gap-2">
      <Badge data-testid="citation-number-badge">[{citation.number}]</Badge>
      <DialogTitle>{citation.documentName}</DialogTitle>
    </div>
    <DialogDescription>
      {citation.pageNumber && <span>Page {citation.pageNumber}</span>}
      {citation.sectionHeader && <span> • {citation.sectionHeader}</span>}
    </DialogDescription>
  </DialogHeader>
  ```
- [ ] Run test: `test_display_document_metadata_in_preview_header`
- [ ] ✅ Test passes (metadata rendered)

#### Task 4: Implement "Open in Document" Navigation

- [ ] Add "Open in Document" button with navigation:
  ```tsx
  import { useNavigate } from 'react-router-dom';

  const navigate = useNavigate();

  const handleOpenDocument = () => {
    navigate(`/documents/${citation.documentId}`, {
      state: {
        charStart: citation.charStart,
        charEnd: citation.charEnd,
        highlightColor: 'yellow',
      },
    });
    onClose(); // Close modal after navigation
  };

  <Button
    data-testid="open-document-button"
    onClick={handleOpenDocument}
  >
    Open in Document
  </Button>
  ```
- [ ] Run test: `test_navigate_to_document_when_Open_Document_button_clicked`
- [ ] ✅ Test passes (navigation works)

#### Task 5: Modal Interaction (Close Handlers)

- [ ] Add close button:
  ```tsx
  <Button
    data-testid="close-preview-button"
    aria-label="Close preview"
    onClick={onClose}
  >
    <X className="h-4 w-4" />
  </Button>
  ```
- [ ] Enable Escape key close (shadcn Dialog handles this by default)
- [ ] Enable click-outside-to-close:
  ```tsx
  <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
    <DialogContent>
      {/* Modal content */}
    </DialogContent>
  </Dialog>
  ```
- [ ] Run tests:
  - `test_close_modal_when_close_button_clicked`
  - `test_close_modal_when_Escape_key_pressed`
  - `test_close_modal_when_clicking_outside_overlay`
- [ ] ✅ Tests pass (all close methods work)

#### Task 6: Loading State (Optional Context Fetching)

- [ ] Handle loading state if fetching context from backend:
  ```tsx
  {isLoading ? (
    <div data-testid="loading-spinner">
      <Spinner />
      <p>Loading context...</p>
    </div>
  ) : (
    renderContextWithHighlight()
  )}
  ```
- [ ] Run test: `test_show_loading_state_while_fetching_full_context`
- [ ] ✅ Test passes (loading state displayed)

#### Task 7: Accessibility & Focus Management

- [ ] Ensure Dialog has proper ARIA attributes (shadcn provides these)
- [ ] Verify focus trap (shadcn Dialog handles this)
- [ ] Test keyboard navigation:
  ```tsx
  <Dialog>
    <DialogContent aria-modal="true" aria-labelledby="preview-title">
      <DialogTitle id="preview-title">Citation Preview</DialogTitle>
      {/* Content */}
    </DialogContent>
  </Dialog>
  ```
- [ ] Run tests:
  - `test_have_proper_ARIA_attributes_for_accessibility`
  - `test_trap_focus_within_modal_when_open`
- [ ] ✅ Tests pass (accessibility validated)

#### Task 8: Integrate Preview into CitationCard

- [ ] Update `CitationCard` component to add "Preview" button:
  ```tsx
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  <Button
    data-testid={`preview-citation-button-${citation.number}`}
    onClick={() => setIsPreviewOpen(true)}
    variant="outline"
    size="sm"
  >
    Preview
  </Button>

  <CitationPreview
    citation={citation}
    isOpen={isPreviewOpen}
    onClose={() => setIsPreviewOpen(false)}
  />
  ```
- [ ] Run test: `test_open_preview_modal_when_Preview_button_on_CitationCard_clicked`
- [ ] ✅ Test passes (integration complete)

#### Task 9: Final Validation

- [ ] Run all Story 3.5 tests:
  ```bash
  npm run test src/components/search/__tests__/citation-preview.test.tsx
  ```
- [ ] All 12 tests should pass (GREEN phase)
- [ ] Manual testing: Open preview, verify highlighting, navigate to document
- [ ] ✅ All tests pass

---

## RED-GREEN-REFACTOR Workflow

### RED Phase (Complete ✅)

- ✅ All 12 tests written and failing
- ✅ Tests define expected preview UX
- ✅ Failures due to missing CitationPreview component

### GREEN Phase (DEV Team - Current)

**Suggested order**:
1. Task 1 (Component skeleton) - Foundation
2. Task 2 (Context + highlighting) - Core UX
3. Task 3 (Metadata) - Information display
4. Task 4 (Navigation) - Primary action
5. Task 5 (Close handlers) - Interaction
6. Task 6 (Loading state) - Polish
7. Task 7 (Accessibility) - Compliance
8. Task 8 (Integration) - Connect to CitationCard
9. Task 9 (Validation) - Final check

### REFACTOR Phase (After all tests green)

1. Extract highlighting logic to reusable utility function
2. Add animation/transition for modal open/close
3. Optimize rendering for long context strings (truncate after 500 chars)
4. Add telemetry: track preview open rate
5. Code review with senior dev
6. Commit: "feat: add citation preview modal (Story 3.5)"

---

## Running Tests

### Run All Story 3.5 Tests

```bash
cd frontend
npm run test src/components/search/__tests__/citation-preview.test.tsx

# Expected: All tests FAIL (RED phase)
```

### Run Specific Test

```bash
# Test modal rendering
npm run test citation-preview.test.tsx -t "should display preview modal"

# Test navigation
npm run test citation-preview.test.tsx -t "should navigate to document"
```

### Run After Implementation

```bash
# Run full Story 3.5 test suite
npm run test citation-preview.test.tsx

# Expected: All 12 tests PASS (GREEN phase)
```

---

## Component Architecture

### Component Structure

```
frontend/src/components/search/
├── citation-preview.tsx          # NEW - Preview modal component
├── citation-card.tsx             # UPDATED - Add "Preview" button
├── search-results.tsx            # NO CHANGES
└── __tests__/
    ├── citation-preview.test.tsx # NEW - 12 tests
    └── citation-card.test.tsx    # UPDATED - Add preview trigger test
```

### Component Hierarchy

```
SearchResults
  └── CitationPanel
      └── CitationCard (for each citation)
          ├── Preview button
          └── CitationPreview modal (conditional)
```

---

## UX Flow

### Happy Path

1. User sees search results with citations in right panel
2. User clicks "Preview" button on CitationCard #1
3. Modal opens showing:
   - Document name, page, section header
   - Highlighted excerpt within full context
4. User reads context and decides to verify in full document
5. User clicks "Open in Document"
6. Modal closes, navigates to document viewer with passage highlighted
7. User verifies citation accuracy

### Alternative Paths

**Quick verification:**
1. User hovers over citation marker [1] (Story 3.4 tooltip)
2. Reads quick excerpt in tooltip
3. Clicks marker → CitationCard scrolls into view
4. Clicks "Preview" for more context
5. Closes modal (citation verified without opening document)

**Multiple citation verification:**
1. User opens preview for [1]
2. Verifies, closes modal
3. Opens preview for [2]
4. Verifies, closes modal
5. Uses "Verify All" mode (Story 3.10) for systematic verification

---

## Dependencies

### shadcn/ui Components Required

```bash
npx shadcn@latest add dialog badge button
```

**Components used:**
- `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription` - Modal structure
- `Badge` - Citation number display
- `Button` - Action buttons

### Browser APIs

- `react-router-dom` - `useNavigate()` for document navigation
- `Element.scrollIntoView()` - Not needed (modal doesn't scroll)

---

## Known Issues / TODOs

### Issue 1: Long Context Truncation

**Problem**: Full context (±200 chars) might be too long for some excerpts

**Solution**:
```tsx
const MAX_CONTEXT_LENGTH = 500;
const contextToDisplay = fullContext.length > MAX_CONTEXT_LENGTH
  ? truncateContext(fullContext, citation.excerpt, MAX_CONTEXT_LENGTH)
  : fullContext;
```

### Issue 2: Context Not Available

**Problem**: Some citations might not have `fullContext` (e.g., PDFs without text extraction)

**Solution**:
```tsx
{citation.fullContext ? (
  renderContextWithHighlight()
) : (
  <div className="text-muted-foreground">
    <p>Context preview not available for this document type.</p>
    <p>Click "Open in Document" to view the full source.</p>
  </div>
)}
```

### Issue 3: Mobile Responsiveness

**Problem**: Modal might be cramped on small screens

**Solution**:
- Use shadcn Dialog's responsive sizing
- Add `className="max-w-2xl"` to DialogContent
- Test on mobile viewport (375px width)

---

## Performance Considerations

### Lazy Loading

If context is fetched from backend:

```tsx
const [context, setContext] = useState<string | null>(null);
const [isLoading, setIsLoading] = useState(false);

useEffect(() => {
  if (isOpen && !citation.fullContext) {
    setIsLoading(true);
    fetchCitationContext(citation.documentId, citation.charStart, citation.charEnd)
      .then(setContext)
      .finally(() => setIsLoading(false));
  }
}, [isOpen]);
```

### Memoization

For expensive highlighting logic:

```tsx
const highlightedContext = useMemo(() => {
  return renderContextWithHighlight();
}, [citation.fullContext, citation.excerpt]);
```

---

## Next Steps for DEV Team

### Immediate Actions

1. **Install shadcn/ui Dialog**:
   ```bash
   npx shadcn@latest add dialog badge
   ```

2. **Run failing tests** to confirm RED phase:
   ```bash
   npm run test citation-preview.test.tsx
   # Expected: All FAIL
   ```

3. **Start GREEN phase** with Task 1 (Component skeleton)

### Definition of Done

- [ ] All 12 tests pass
- [ ] Preview modal displays citation context correctly
- [ ] Highlighting works for excerpts
- [ ] Navigation to document includes highlighting params
- [ ] All close methods work (button, Escape, click-outside)
- [ ] Accessibility validated (ARIA, focus trap)
- [ ] Code reviewed by senior dev
- [ ] Merged to main branch

---

## Knowledge Base References Applied

**Frameworks:**
- `test-levels-framework.md` - Component test level
- `test-quality.md` - Accessibility testing

**Patterns:**
- `fixture-architecture.md` - Mock citation data structure

---

## Output Summary

### ATDD Complete - Tests in RED Phase ✅

**Story**: 3.5 - Citation Preview & Source Navigation
**Primary Test Level**: Component

**Failing Tests Created**:
- Component tests: 12 tests in `frontend/src/components/search/__tests__/citation-preview.test.tsx`

**Supporting Infrastructure**:
- CitationPreview component (to be implemented)
- CitationCard integration (update existing)
- shadcn/ui Dialog component

**Implementation Checklist**:
- Total tasks: 9 tasks
- Estimated effort: 6-8 hours

**Dependencies**:
- shadcn/ui Dialog, Badge components
- react-router-dom navigation
- Story 3.4 (CitationCard) must be complete

**Next Steps for DEV Team**:
1. Install shadcn/ui Dialog component
2. Run failing tests: `npm run test citation-preview.test.tsx`
3. Implement Task 1 (Component skeleton)
4. Follow RED → GREEN → REFACTOR cycle

**Output File**: `docs/atdd-checklist-3.5.md`

---

**Generated by**: Murat (TEA Agent - Test Architect Module)
**Workflow**: `.bmad/bmm/workflows/testarch/atdd`
**Date**: 2025-11-25
