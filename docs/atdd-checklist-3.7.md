# ATDD Checklist: Story 3.7 - Command Palette (⌘K) Quick Search

**Date:** 2025-11-25
**Story ID:** 3.7
**Status:** RED Phase (Tests Failing - Implementation Pending)

---

## Story Summary

**Epic**: 3 - Semantic Search & Citations
**Story**: 3.7 - Command Palette (⌘K) Quick Search

**Description:**
Implement a command palette overlay (similar to VS Code, Linear, Slack) triggered by ⌘K (Mac) or Ctrl+K (Windows/Linux). Provides instant access to quick search from anywhere in the app, returning top 5 chunk results without LLM synthesis for maximum speed.

**Priority:** P1 - High (Important UX for power users)

**User Value:**
- Instant search from anywhere (no navigation required)
- Faster results (skips LLM synthesis)
- Keyboard-driven workflow (power user efficiency)
- Muscle memory from other apps (⌘K is standard)

---

## Acceptance Criteria Breakdown

| AC ID | Requirement | Test Level | Test File | Status |
|-------|------------|------------|-----------|--------|
| AC-3.7.1 | ⌘K / Ctrl+K opens command palette | Component | `command-palette.test.tsx::test_open_command_palette_when_Cmd_K_pressed` | ❌ RED |
| AC-3.7.1 | Prevent default browser behavior | Component | `command-palette.test.tsx::test_prevent_default_browser_behavior` | ❌ RED |
| AC-3.7.2 | Quick search returns chunks only (no synthesis) | Integration | `test_quick_search.py::test_quick_search_returns_chunks_only` | ❌ RED |
| AC-3.7.2 | Debounce search input | Component | `command-palette.test.tsx::test_debounce_search_input` | ❌ RED |
| AC-3.7.3 | Results display snippet + metadata | Component | `command-palette.test.tsx::test_display_search_results_with_all_metadata` | ❌ RED |
| AC-3.7.3 | Highlight query terms in results | Component | `command-palette.test.tsx::test_highlight_query_terms_in_result_text` | ❌ RED |
| AC-3.7.4 | Click result navigates to document | Component | `command-palette.test.tsx::test_navigate_to_document_when_result_clicked` | ❌ RED |
| AC-3.7.4 | Enter key navigates to selected result | Component | `command-palette.test.tsx::test_navigate_using_Enter_key_on_selected_result` | ❌ RED |

**Total Tests**: 18 tests (5 backend integration + 13 frontend component)

---

## Test Files Created

### Backend Tests

**File**: `backend/tests/integration/test_quick_search.py`

**Tests (5 integration tests):**
1. ✅ `test_quick_search_returns_chunks_only` - No synthesis
2. ✅ `test_quick_search_includes_chunk_metadata` - Metadata completeness
3. ✅ `test_quick_search_respects_limit` - Limit enforcement (max 5)
4. ✅ `test_quick_search_performance` - Performance < 2s
5. ✅ `test_quick_search_with_no_results` - Empty results edge case

### Frontend Tests

**File**: `frontend/src/components/search/__tests__/command-palette.test.tsx`

**Tests (13 component tests):**
1. ✅ `test_open_command_palette_when_Cmd_K_pressed_on_Mac` - Keyboard shortcut (Mac)
2. ✅ `test_open_command_palette_when_Ctrl_K_pressed_on_Windows` - Keyboard shortcut (Windows/Linux)
3. ✅ `test_prevent_default_browser_behavior_for_Cmd_Ctrl_K` - Prevent browser default
4. ✅ `test_search_and_display_chunk_results_without_synthesis` - Quick search UX
5. ✅ `test_debounce_search_input_to_avoid_excessive_API_calls` - Debouncing
6. ✅ `test_display_search_results_with_all_metadata` - Metadata display
7. ✅ `test_highlight_query_terms_in_result_text` - Query highlighting
8. ✅ `test_navigate_to_document_when_result_clicked` - Click navigation
9. ✅ `test_navigate_using_Enter_key_on_selected_result` - Keyboard navigation
10. ✅ `test_navigate_results_using_arrow_keys` - Arrow key navigation
11. ✅ `test_close_palette_when_Escape_pressed` - Escape to close
12. ✅ `test_show_loading_indicator_while_searching` - Loading state
13. ✅ `test_have_proper_ARIA_attributes_for_accessibility` - Accessibility

---

## Supporting Infrastructure

### Global Keyboard Listener

The command palette must be accessible from **anywhere** in the app. This requires a global keyboard event listener.

**Implementation Pattern**:

```tsx
// In App.tsx or layout component
import { CommandPalette } from '@/components/search/command-palette';

function App() {
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check for Cmd+K (Mac) or Ctrl+K (Windows/Linux)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault(); // Prevent browser default (search)
        setIsPaletteOpen(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return (
    <>
      {/* App content */}
      <CommandPalette
        isOpen={isPaletteOpen}
        onClose={() => setIsPaletteOpen(false)}
      />
    </>
  );
}
```

### Quick Search API Signature

**Backend change**: Add `synthesize` parameter to existing `/api/v1/search` endpoint.

```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    kb_ids: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=50)
    synthesize: bool = Field(default=True)  # NEW for Story 3.7

class QuickSearchResponse(BaseModel):
    # Subset of SearchResponse (no answer/citations)
    query: str
    results: list[SearchResultSchema]  # Chunks only
```

**Logic change**:

```python
@router.post("/search")
async def search(request: SearchRequest, ...):
    # Perform vector search (same as before)
    results = await search_service.search(
        query=request.query,
        kb_ids=request.kb_ids,
        user_id=current_user.id,
        limit=request.limit
    )

    # NEW: Skip synthesis if synthesize=False
    if not request.synthesize:
        # Quick search mode (command palette)
        return {
            "query": request.query,
            "results": results
        }

    # Full search mode (existing logic)
    answer, citations = await synthesis_service.synthesize(results, request.query)
    return {
        "query": request.query,
        "answer": answer,
        "citations": citations,
        "results": results
    }
```

---

## Implementation Checklist

### RED Phase (Complete ✅)

- [x] All 18 tests written and failing (5 backend + 13 frontend)
- [x] Global keyboard listener pattern defined
- [x] Quick search API signature documented

### GREEN Phase (DEV Team - Implementation Tasks)

#### Task 1: Backend - Add `synthesize` Parameter

- [ ] Update `SearchRequest` schema in `backend/app/api/v1/search.py`:
  ```python
  synthesize: bool = Field(default=True)  # True for full search, False for quick
  ```
- [ ] Modify search endpoint logic:
  ```python
  if not request.synthesize:
      # Skip LLM synthesis
      return {"query": request.query, "results": results}

  # Existing synthesis logic...
  ```
- [ ] Run test: `test_quick_search_returns_chunks_only`
- [ ] ✅ Test passes (quick search skips synthesis)

#### Task 2: Backend - Optimize Quick Search Performance

- [ ] Ensure quick search uses cached embeddings:
  ```python
  # Already implemented in Story 3.6
  embedding = await self.embed_with_cache(query)
  ```
- [ ] Skip audit logging for quick searches (optional - reduces overhead):
  ```python
  if request.synthesize:
      # Only log full searches
      await audit_service.log_search(...)
  ```
- [ ] Run test: `test_quick_search_performance`
- [ ] ✅ Test passes (response < 2s)

#### Task 3: Frontend - Create CommandPalette Component

- [ ] Create `frontend/src/components/search/command-palette.tsx`
- [ ] Use shadcn/ui Dialog as base:
  ```bash
  npx shadcn@latest add dialog
  npx shadcn@latest add command  # Or build custom combobox
  ```
- [ ] Implement component skeleton:
  ```tsx
  interface CommandPaletteProps {
    isOpen: boolean;
    onClose: () => void;
  }

  export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [selectedIndex, setSelectedIndex] = useState(0);

    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent data-testid="command-palette">
          <input
            data-testid="command-palette-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search knowledge bases..."
          />
          {/* Results list */}
        </DialogContent>
      </Dialog>
    );
  }
  ```
- [ ] Run test: `test_open_command_palette_when_Cmd_K_pressed_on_Mac`
- [ ] ✅ Test passes (palette renders)

#### Task 4: Frontend - Add Global Keyboard Listener

- [ ] In `frontend/src/App.tsx` (or root layout):
  ```tsx
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsPaletteOpen(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <>
      {/* App routes */}
      <CommandPalette
        isOpen={isPaletteOpen}
        onClose={() => setIsPaletteOpen(false)}
      />
    </>
  );
  ```
- [ ] Run tests:
  - `test_open_command_palette_when_Cmd_K_pressed_on_Mac`
  - `test_prevent_default_browser_behavior_for_Cmd_Ctrl_K`
- [ ] ✅ Tests pass (keyboard shortcut works)

#### Task 5: Frontend - Implement Quick Search with Debouncing

- [ ] Add debounced search function:
  ```tsx
  import { useDebouncedCallback } from 'use-debounce';

  const searchQuick = useDebouncedCallback(async (query: string) => {
    if (!query) return;

    setIsLoading(true);

    const response = await fetch('/api/v1/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        synthesize: false,  // Quick search mode
        limit: 5,
      }),
    });

    const data = await response.json();
    setResults(data.results);
    setIsLoading(false);
  }, 300); // 300ms debounce

  useEffect(() => {
    searchQuick(query);
  }, [query]);
  ```
- [ ] Run tests:
  - `test_search_and_display_chunk_results_without_synthesis`
  - `test_debounce_search_input_to_avoid_excessive_API_calls`
- [ ] ✅ Tests pass (search works with debouncing)

#### Task 6: Frontend - Display Results with Metadata

- [ ] Render results list:
  ```tsx
  <div className="results-list">
    {results.map((result, index) => (
      <div
        key={result.id}
        data-testid={`quick-search-result-${index}`}
        className={cn("result-item", { selected: index === selectedIndex })}
        onClick={() => handleSelectResult(result)}
      >
        <div className="flex items-center justify-between">
          <h4 className="font-semibold">{result.document_name}</h4>
          <Badge variant="secondary">{result.kb_name}</Badge>
        </div>

        <p className="text-sm text-muted-foreground">
          {highlightQuery(result.chunk_text, query)}
        </p>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {result.page_number && <span>Page {result.page_number}</span>}
          <span>{Math.round(result.relevance_score * 100)}%</span>
        </div>
      </div>
    ))}
  </div>
  ```
- [ ] Implement query highlighting:
  ```tsx
  function highlightQuery(text: string, query: string) {
    const parts = text.split(new RegExp(`(${query})`, 'gi'));

    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={i} data-testid="highlighted-query-term" className="font-bold bg-yellow-200">
          {part}
        </mark>
      ) : (
        <span key={i}>{part}</span>
      )
    );
  }
  ```
- [ ] Run tests:
  - `test_display_search_results_with_all_metadata`
  - `test_highlight_query_terms_in_result_text`
- [ ] ✅ Tests pass (results rendered correctly)

#### Task 7: Frontend - Navigation on Click/Enter

- [ ] Implement navigation handler:
  ```tsx
  const navigate = useNavigate();

  const handleSelectResult = (result: SearchResult) => {
    navigate(`/documents/${result.document_id}`, {
      state: {
        charStart: result.char_start,
        charEnd: result.char_end,
        highlightColor: 'yellow',
      },
    });

    onClose(); // Close palette after navigation
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && results[selectedIndex]) {
      handleSelectResult(results[selectedIndex]);
    }
  };
  ```
- [ ] Run tests:
  - `test_navigate_to_document_when_result_clicked`
  - `test_navigate_using_Enter_key_on_selected_result`
- [ ] ✅ Tests pass (navigation works)

#### Task 8: Frontend - Keyboard Navigation (Arrow Keys)

- [ ] Implement arrow key navigation:
  ```tsx
  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
        break;

      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
        break;

      case 'Enter':
        e.preventDefault();
        if (results[selectedIndex]) {
          handleSelectResult(results[selectedIndex]);
        }
        break;

      case 'Escape':
        e.preventDefault();
        onClose();
        break;
    }
  };
  ```
- [ ] Run test: `test_navigate_results_using_arrow_keys`
- [ ] ✅ Test passes (arrow keys work)

#### Task 9: Frontend - Close Handlers and Focus Management

- [ ] Implement close handlers:
  ```tsx
  // Escape key already handled in handleKeyDown

  // Click outside to close
  <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
    {/* Content */}
  </Dialog>
  ```
- [ ] Restore focus on close:
  ```tsx
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement;
    } else if (previousFocusRef.current) {
      previousFocusRef.current.focus();
    }
  }, [isOpen]);
  ```
- [ ] Run tests:
  - `test_close_palette_when_Escape_pressed`
  - `test_restore_focus_to_previous_element_when_closed`
- [ ] ✅ Tests pass (close and focus management work)

#### Task 10: Frontend - Loading and Empty States

- [ ] Add loading indicator:
  ```tsx
  {isLoading && (
    <div data-testid="search-loading-spinner" className="flex items-center gap-2">
      <Spinner />
      <span>Searching...</span>
    </div>
  )}
  ```
- [ ] Add empty state:
  ```tsx
  {!isLoading && query && results.length === 0 && (
    <div data-testid="search-empty-state" className="text-center py-8">
      <p className="text-muted-foreground">No results found for "{query}"</p>
      <p className="text-sm">Try a different search term</p>
    </div>
  )}
  ```
- [ ] Run test: `test_show_loading_indicator_while_searching`
- [ ] ✅ Test passes (states rendered)

#### Task 11: Frontend - Accessibility

- [ ] Add ARIA attributes:
  ```tsx
  <Dialog
    open={isOpen}
    onOpenChange={onClose}
    aria-label="Quick search"
  >
    <DialogContent
      role="dialog"
      aria-modal="true"
      data-testid="command-palette"
    >
      <input
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={results.length > 0}
        aria-controls="search-results"
        {...}
      />

      <div id="search-results" role="listbox">
        {results.map((result, index) => (
          <div
            role="option"
            aria-selected={index === selectedIndex}
            {...}
          />
        ))}
      </div>
    </DialogContent>
  </Dialog>
  ```
- [ ] Run test: `test_have_proper_ARIA_attributes_for_accessibility`
- [ ] ✅ Test passes (accessible)

---

## RED-GREEN-REFACTOR Workflow

### RED Phase (Complete ✅)

- ✅ All 18 tests written and failing (5 backend + 13 frontend)
- ✅ Tests define command palette UX
- ✅ Failures due to missing quick search mode

### GREEN Phase (DEV Team - Current)

**Suggested order**:
1. Task 1 (Backend - synthesize parameter) - API contract
2. Task 2 (Backend - performance optimization) - Speed
3. Task 3 (Frontend - component skeleton) - Foundation
4. Task 4 (Frontend - keyboard listener) - Trigger
5. Task 5 (Frontend - search + debounce) - Core functionality
6. Task 6 (Frontend - results display) - UX
7. Task 7 (Frontend - navigation) - Primary action
8. Task 8 (Frontend - arrow keys) - Keyboard workflow
9. Task 9 (Frontend - close handlers) - Interaction
10. Task 10 (Frontend - loading/empty states) - Polish
11. Task 11 (Frontend - accessibility) - Compliance

### REFACTOR Phase (After all tests green)

1. Extract search logic to custom hook: `useQuickSearch()`
2. Extract result highlighting to utility: `highlightText()`
3. Add animation for palette open/close
4. Add keyboard shortcut hint in UI: "Press ⌘K to search"
5. Add telemetry: track palette open rate, search queries
6. Code review with senior dev
7. Commit: "feat: implement command palette quick search (Story 3.7)"

---

## Running Tests

### Run All Story 3.7 Tests

**Backend:**
```bash
cd backend
pytest tests/integration/test_quick_search.py -v

# Expected: All tests FAIL (RED phase)
```

**Frontend:**
```bash
cd frontend
npm run test command-palette.test.tsx

# Expected: All tests FAIL (RED phase)
```

### Run After Implementation

**Backend:**
```bash
pytest tests/integration/test_quick_search.py -v

# Expected: All 5 tests PASS (GREEN phase)
```

**Frontend:**
```bash
npm run test command-palette.test.tsx

# Expected: All 13 tests PASS (GREEN phase)
```

---

## UX Design Notes

### Visual Design

**Command Palette Appearance:**
- Centered modal overlay (max-width: 600px)
- Semi-transparent backdrop (bg-black/50)
- Search input at top (large, autofocused)
- Results list below (max 5 results, scrollable if needed)
- Keyboard hints at bottom: "↑↓ to navigate, ↵ to select, ESC to close"

**Result Item Layout:**
```
┌─────────────────────────────────────────────────┐
│ OAuth Security Guide.pdf        [Security KB]   │
│ OAuth 2.0 with PKCE flow ensures secure...      │
│ Page 14 • 92%                                    │
└─────────────────────────────────────────────────┘
```

### Animation

- Fade in backdrop: 150ms
- Slide down palette: 200ms ease-out
- Slide up on close: 150ms ease-in

### Keyboard Shortcuts Summary

| Key | Action |
|-----|--------|
| ⌘K / Ctrl+K | Open palette |
| ESC | Close palette |
| ↑ / ↓ | Navigate results |
| ↵ (Enter) | Select result |
| Click outside | Close palette |

---

## Known Issues / TODOs

### Issue 1: Multiple Keyboards Shortcuts Conflict

**Problem**: Some browsers use Ctrl+K for search bar

**Solution**:
- Use `e.preventDefault()` to override browser default
- Test across browsers (Chrome, Firefox, Safari, Edge)
- Document conflict in user guide (rare)

### Issue 2: Focus Trap in Nested Modals

**Problem**: If command palette opens over another modal, focus trap conflicts

**Solution**:
- Use portal for palette: `<Dialog modal={true}>`
- Z-index: palette (z-50) > other modals (z-40)
- Close palette if another modal opens (edge case)

### Issue 3: Query Too Short

**Problem**: Searching for 1-letter queries ("a", "b") is inefficient

**Solution**:
```tsx
const searchQuick = useDebouncedCallback(async (query: string) => {
  if (query.length < 2) {
    setResults([]);
    return;
  }
  // Proceed with search
}, 300);
```

---

## Performance Benchmarks

| Metric | Target | Measurement |
|--------|--------|-------------|
| Palette open time | < 100ms | Manual testing |
| Quick search API | < 1s (p95) | `test_quick_search_performance` |
| Debounce delay | 300ms | User testing (feels responsive) |

**Performance Comparison:**

| Search Mode | Time | LLM Synthesis? |
|-------------|------|----------------|
| Full Search | 2-3s | ✅ Yes (expensive) |
| Quick Search | < 1s | ❌ No (fast) |

---

## Dependencies

### Backend

- Existing `/api/v1/search` endpoint (Story 3.1)
- No new dependencies

### Frontend

**npm packages:**
```bash
npm install use-debounce  # For debounced search input
```

**shadcn/ui components:**
```bash
npx shadcn@latest add dialog badge
```

---

## Next Steps for DEV Team

### Immediate Actions

1. **Review command palette UX** in other apps (VS Code, Linear, Raycast)
2. **Run failing tests** to confirm RED phase:
   ```bash
   pytest tests/integration/test_quick_search.py -v
   npm run test command-palette.test.tsx
   ```
3. **Start GREEN phase** with Task 1 (Backend - synthesize parameter)

### Definition of Done

- [ ] All 18 tests pass (5 backend + 13 frontend)
- [ ] ⌘K / Ctrl+K opens palette from anywhere
- [ ] Quick search returns chunks in < 1s
- [ ] Results display with full metadata
- [ ] Keyboard navigation works (arrows, Enter, ESC)
- [ ] Clicking result navigates to document with highlighting
- [ ] Loading and empty states displayed
- [ ] Accessibility validated (ARIA, focus management)
- [ ] Code reviewed by senior dev
- [ ] Merged to main branch

---

## Knowledge Base References Applied

**Frameworks:**
- `test-levels-framework.md` - Component + Integration tests
- `test-quality.md` - Accessibility and keyboard navigation

**Patterns:**
- `fixture-architecture.md` - Mock search results

---

## Output Summary

### ATDD Complete - Tests in RED Phase ✅

**Story**: 3.7 - Command Palette (⌘K) Quick Search
**Primary Test Levels**: Component + Integration

**Failing Tests Created**:
- Backend integration tests: 5 tests in `backend/tests/integration/test_quick_search.py`
- Frontend component tests: 13 tests in `frontend/src/components/search/__tests__/command-palette.test.tsx`

**Supporting Infrastructure**:
- Global keyboard listener pattern
- Quick search API mode (synthesize=False)
- Debounced search input
- Keyboard navigation logic
- Focus management

**Implementation Checklist**:
- Total tasks: 11 tasks
- Estimated effort: 6-8 hours

**Dependencies**:
- Story 3.1 (Semantic Search) must be complete
- shadcn/ui Dialog component
- use-debounce npm package

**Next Steps for DEV Team**:
1. Review command palette UX patterns
2. Run failing tests: `pytest test_quick_search.py && npm run test command-palette.test.tsx`
3. Implement Task 1 (Backend - synthesize parameter)
4. Follow RED → GREEN → REFACTOR cycle

**Output File**: `docs/atdd-checklist-3.7.md`

---

**Generated by**: Murat (TEA Agent - Test Architect Module)
**Workflow**: `.bmad/bmm/workflows/testarch/atdd`
**Date**: 2025-11-25
