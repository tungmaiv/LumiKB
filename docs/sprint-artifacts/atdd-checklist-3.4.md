# ATDD Checklist: Story 3.4 - Citation Display and Navigation (Frontend)

**Date:** 2025-11-25
**Story ID:** 3.4
**Status:** RED Phase (Tests Failing - Implementation Pending)

---

## Story Summary

**Epic**: 3 - Semantic Search & Citations
**Story**: 3.4 - Citation Display and Navigation (Frontend)

**Description:**
Implement citation UI in the search results page. Users see clickable citation markers `[1]`, `[2]` in the answer text, with a sidebar panel showing citation metadata. Clicking a marker highlights the corresponding citation and allows navigation to the source document.

**Risk Level:** LOW
- UI implementation, no critical backend risks
- Depends on Story 3.2 (citation data from backend)

---

## Acceptance Criteria Breakdown

| AC ID | Requirement | Test Level | Test File | Status |
|-------|------------|------------|-----------|--------|
| AC-3.4.1 | Citation markers clickable badges | Component | `search-results.test.tsx::should render citation markers as clickable badges` | ❌ RED |
| AC-3.4.1 | Markers inline in answer text | Component | `search-results.test.tsx::should render answer text with markers inline` | ❌ RED |
| AC-3.4.2 | Click marker highlights citation | Component | `search-results.test.tsx::should highlight citation in sidebar when marker clicked` | ❌ RED |
| AC-3.4.2 | Scroll to highlighted citation | Component | `search-results.test.tsx::should scroll citation panel to highlighted citation` | ❌ RED |
| AC-3.4.3 | Citation metadata display | Component | `search-results.test.tsx::should display citation metadata in sidebar` | ❌ RED |
| AC-3.4.3 | Confidence indicator | Component | `search-results.test.tsx::should display confidence indicator` | ❌ RED |
| AC-3.4.3 | Low confidence warning | Component | `search-results.test.tsx::should display low confidence warning when score < 50` | ❌ RED |
| AC-3.4.4 | Open document navigation | Component | `search-results.test.tsx::should navigate to document when Open button clicked` | ❌ RED |
| AC-3.4.4 | Citation hover tooltip | Component | `search-results.test.tsx::should preview citation excerpt in tooltip on hover` | ❌ RED |

**Component Tests:**
- `CitationMarker` component: 3 tests
- `CitationCard` component: 3 tests

**Total Tests**: 15 component tests

---

## Test Files Created

### Component Tests

**File**: `frontend/src/components/search/__tests__/search-results.test.tsx`

**Tests (15 component tests):**

**SearchResults Component (9 tests):**
1. ✅ Citation markers as clickable badges (AC-3.4.1)
2. ✅ Answer text with inline markers (AC-3.4.1)
3. ✅ Marker click highlights citation (AC-3.4.2)
4. ✅ Scroll to highlighted citation (AC-3.4.2)
5. ✅ Citation metadata display (AC-3.4.3)
6. ✅ Confidence indicator (AC-3.4.3)
7. ✅ Low confidence warning (AC-3.4.3)
8. ✅ Open document navigation (AC-3.4.4)
9. ✅ Citation hover tooltip (AC-3.4.4)

**CitationMarker Component (3 tests):**
10. ✅ Render marker with number
11. ✅ onClick callback
12. ✅ Accessible label

**CitationCard Component (3 tests):**
13. ✅ Render all metadata
14. ✅ Highlighted class
15. ✅ onOpen callback

---

## Supporting Infrastructure

### Component Structure

```
frontend/src/components/search/
├── search-results.tsx          # Main search results component
├── citation-marker.tsx         # Inline [n] badge component
├── citation-card.tsx           # Citation metadata card
├── citation-panel.tsx          # Sidebar with all citations
├── confidence-indicator.tsx    # Confidence score display
└── __tests__/
    └── search-results.test.tsx # Component tests
```

### Required shadcn/ui Components

```bash
npx shadcn@latest add badge      # For citation markers
npx shadcn@latest add card       # For citation cards
npx shadcn@latest add tooltip    # For citation preview
npx shadcn@latest add scroll-area # For citation panel
```

---

## Implementation Checklist

### RED Phase (Complete ✅)

- [x] All 15 component tests written and failing
- [x] Test fixtures with mock citation data
- [x] Component structure planned

### GREEN Phase (DEV Team - Implementation Tasks)

#### Task 1: Create CitationMarker Component

- [ ] Create `frontend/src/components/search/citation-marker.tsx`
- [ ] Implement inline badge component:
  ```tsx
  interface CitationMarkerProps {
    number: number;
    onClick: (number: number) => void;
  }

  export function CitationMarker({ number, onClick }: CitationMarkerProps) {
    return (
      <button
        data-testid={`citation-marker-${number}`}
        className="citation-marker"
        aria-label={`Citation ${number}`}
        onClick={() => onClick(number)}
      >
        [{number}]
      </button>
    );
  }
  ```
- [ ] Style with Tailwind (small badge, blue color, hover effect)
- [ ] Run test: `should render marker with correct number`
- [ ] ✅ Test passes

#### Task 2: Create CitationCard Component

- [ ] Create `frontend/src/components/search/citation-card.tsx`
- [ ] Implement citation metadata card:
  ```tsx
  interface CitationCardProps {
    citation: Citation;
    highlighted: boolean;
    onOpen: (citation: Citation) => void;
  }

  export function CitationCard({ citation, highlighted, onOpen }: CitationCardProps) {
    return (
      <div
        data-testid={`citation-card-${citation.number}`}
        className={cn("citation-card", highlighted && "highlighted")}
      >
        <div className="citation-header">
          <span className="citation-number">[{citation.number}]</span>
          <h4>{citation.documentName}</h4>
        </div>

        <div className="citation-metadata">
          {citation.pageNumber && <span>Page {citation.pageNumber}</span>}
          <span>{citation.sectionHeader}</span>
        </div>

        <p className="citation-excerpt">{citation.excerpt}</p>

        <button
          data-testid={`open-doc-button-${citation.number}`}
          onClick={() => onOpen(citation)}
        >
          Open Document
        </button>
      </div>
    );
  }
  ```
- [ ] Run test: `should render all citation metadata`
- [ ] ✅ Test passes

#### Task 3: Create ConfidenceIndicator Component

- [ ] Create `frontend/src/components/search/confidence-indicator.tsx`
- [ ] Implement confidence score display with color coding:
  ```tsx
  interface ConfidenceIndicatorProps {
    score: number;
  }

  export function ConfidenceIndicator({ score }: ConfidenceIndicatorProps) {
    const level = score >= 70 ? 'high' : score >= 50 ? 'medium' : 'low';

    return (
      <div
        data-testid="confidence-indicator"
        className={`confidence-indicator confidence-${level}`}
      >
        <span>{score}%</span>
        {level === 'low' && <span>Low confidence - verify sources</span>}
      </div>
    );
  }
  ```
- [ ] Run test: `should display confidence indicator`
- [ ] ✅ Test passes

#### Task 4: Implement Answer Text Parsing with Citation Markers

- [ ] In `search-results.tsx`, parse answer text for `[n]` markers
- [ ] Replace markers with `<CitationMarker>` components:
  ```tsx
  function parseAnswerWithCitations(answer: string, onMarkerClick: (n: number) => void) {
    const parts = [];
    const regex = /\[(\d+)\]/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(answer)) !== null) {
      // Text before marker
      if (match.index > lastIndex) {
        parts.push(answer.substring(lastIndex, match.index));
      }

      // Citation marker
      const number = parseInt(match[1]);
      parts.push(<CitationMarker key={`marker-${number}`} number={number} onClick={onMarkerClick} />);

      lastIndex = regex.lastIndex;
    }

    // Remaining text
    if (lastIndex < answer.length) {
      parts.push(answer.substring(lastIndex));
    }

    return parts;
  }
  ```
- [ ] Run test: `should render answer text with markers inline`
- [ ] ✅ Test passes

#### Task 5: Implement Citation Highlighting on Click

- [ ] Add state for highlighted citation:
  ```tsx
  const [highlightedCitation, setHighlightedCitation] = useState<number | null>(null);

  const handleMarkerClick = (number: number) => {
    setHighlightedCitation(number);

    // Scroll to citation card
    const card = document.querySelector(`[data-testid="citation-card-${number}"]`);
    card?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  };
  ```
- [ ] Pass `highlighted` prop to `CitationCard`:
  ```tsx
  {citations.map(citation => (
    <CitationCard
      key={citation.number}
      citation={citation}
      highlighted={citation.number === highlightedCitation}
      onOpen={handleOpenDocument}
    />
  ))}
  ```
- [ ] Run test: `should highlight citation in sidebar when marker clicked`
- [ ] ✅ Test passes

#### Task 6: Implement Document Navigation

- [ ] Add navigation handler in `search-results.tsx`:
  ```tsx
  const navigate = useNavigate();

  const handleOpenDocument = (citation: Citation) => {
    navigate(`/documents/${citation.documentId}`, {
      state: {
        charStart: citation.charStart,
        charEnd: citation.charEnd,
      },
    });
  };
  ```
- [ ] Run test: `should navigate to document when Open button clicked`
- [ ] ✅ Test passes

#### Task 7: Add Citation Hover Tooltip

- [ ] Wrap `CitationMarker` with `Tooltip` from shadcn/ui:
  ```tsx
  <Tooltip>
    <TooltipTrigger asChild>
      <CitationMarker number={number} onClick={onClick} />
    </TooltipTrigger>
    <TooltipContent>
      <p>{citation.excerpt}</p>
      <p className="text-xs text-gray-500">{citation.documentName}</p>
    </TooltipContent>
  </Tooltip>
  ```
- [ ] Run test: `should preview citation excerpt in tooltip on hover`
- [ ] ✅ Test passes

#### Task 8: Styling and Polish

- [ ] Add Tailwind classes for citation UI
- [ ] Ensure responsive layout (sidebar on desktop, bottom sheet on mobile)
- [ ] Add transitions for highlight effect
- [ ] Test accessibility (keyboard navigation, screen reader labels)
- [ ] Run all tests to verify polish
- [ ] ✅ All tests pass (GREEN phase)

---

## RED-GREEN-REFACTOR Workflow

### RED Phase (Complete ✅)

- ✅ All 15 component tests written and failing
- ✅ Tests define citation UI expectations
- ✅ Failures due to missing components

### GREEN Phase (DEV Team - Current)

**Suggested order**:
1. Task 1 (CitationMarker) - Foundation
2. Task 2 (CitationCard) - Metadata display
3. Task 3 (ConfidenceIndicator) - Trust signal
4. Task 4 (Answer parsing) - Inline markers
5. Task 5 (Click highlighting) - Interaction
6. Task 6 (Document navigation) - Navigation
7. Task 7 (Hover tooltip) - UX polish
8. Task 8 (Styling) - Visual polish

### REFACTOR Phase (After all tests green)

1. Extract citation parsing to custom hook (`useCitationParsing`)
2. Memoize parsed answer (avoid re-parsing on re-renders)
3. Add loading skeleton for citation panel
4. Add error boundary for citation rendering failures
5. Optimize scroll performance (virtual scrolling for many citations)
6. Code review with senior frontend dev
7. Commit: "feat: implement citation UI (Story 3.4)"

---

## Running Tests

### Run All Component Tests

```bash
cd frontend
npm run test src/components/search/__tests__/search-results.test.tsx

# Expected: All 15 tests FAIL (RED phase)
```

### Run Specific Test

```bash
# Test citation marker rendering
npm run test -- --grep "should render citation markers as clickable badges"

# Test highlighting interaction
npm run test -- --grep "should highlight citation in sidebar"
```

### Run After Implementation

```bash
# Run full Story 3.4 test suite
npm run test src/components/search/

# Expected: All 15 tests PASS (GREEN phase)
```

---

## UI/UX Design Notes

### Citation Marker Styling

```css
.citation-marker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  margin: 0 2px;
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6; /* Blue */
  background: #dbeafe; /* Light blue */
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.citation-marker:hover {
  background: #3b82f6;
  color: white;
}
```

### Citation Card Highlighting

```css
.citation-card {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.3s;
}

.citation-card.highlighted {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
```

### Confidence Indicator

```css
.confidence-indicator.confidence-high {
  color: #10b981; /* Green */
}

.confidence-indicator.confidence-medium {
  color: #f59e0b; /* Amber */
}

.confidence-indicator.confidence-low {
  color: #ef4444; /* Red */
}
```

---

## Accessibility Requirements

### Citation Markers

- [ ] Keyboard accessible (tab navigation)
- [ ] ARIA label: "Citation 1", "Citation 2", etc.
- [ ] Focus visible (outline on keyboard focus)
- [ ] Screen reader announces: "Citation 1, button"

### Citation Cards

- [ ] Semantic HTML (heading, paragraph, button)
- [ ] ARIA live region for highlighting (announces to screen reader)
- [ ] Keyboard navigation within citation panel

### Tooltips

- [ ] ARIA describedby on marker
- [ ] ESC key closes tooltip
- [ ] Focus trap within tooltip

---

## Next Steps for DEV Team

### Immediate Actions

1. **Install shadcn/ui components**:
   ```bash
   npx shadcn@latest add badge card tooltip scroll-area
   ```
2. **Run failing tests** to confirm RED phase
3. **Start GREEN phase** with Task 1 (CitationMarker component)
4. **Review design notes** (styling, accessibility)

### Definition of Done

- [ ] All 15 component tests pass
- [ ] Citation markers clickable and styled
- [ ] Citation panel displays metadata
- [ ] Highlighting works on marker click
- [ ] Document navigation functional
- [ ] Accessibility validated (keyboard, screen reader)
- [ ] Responsive design (desktop + mobile)
- [ ] Code reviewed by senior frontend dev
- [ ] Merged to main branch

---

## Known Issues / TODOs

### Long Answer Text Performance

**Issue**: Parsing answer with 50+ citations could be slow

**Solution**:
- Memoize parsed answer using `useMemo()`
- Only re-parse when answer changes

### Mobile UX

**Issue**: Citation panel sidebar takes space on mobile

**Solution**:
- Use bottom sheet UI pattern on mobile (<768px width)
- Show citations as modal overlay
- Use shadcn/ui Sheet component

---

## Output Summary

### ATDD Complete - Tests in RED Phase ✅

**Story**: 3.4 - Citation Display and Navigation (Frontend)
**Primary Test Level**: Component

**Failing Tests Created**:
- Component tests: 15 tests in `frontend/src/components/search/__tests__/search-results.test.tsx`

**Components to Implement**:
- CitationMarker (inline badge)
- CitationCard (metadata display)
- ConfidenceIndicator (trust signal)
- SearchResults (main component with answer parsing)

**Implementation Checklist**:
- Total tasks: 8 tasks
- Estimated effort: 10-14 hours

**Dependencies**:
- Story 3.2 (citation data from backend)
- shadcn/ui components (badge, card, tooltip, scroll-area)

**Next Steps for DEV Team**:
1. Install shadcn/ui components
2. Run failing tests: `npm run test src/components/search/`
3. Implement Task 1 (CitationMarker)
4. Follow RED → GREEN → REFACTOR cycle

**Output File**: `docs/atdd-checklist-3.4.md`

---

**Generated by**: Murat (TEA Agent - Test Architect Module)
**Workflow**: `.bmad/bmm/workflows/testarch/atdd`
**Date**: 2025-11-25
