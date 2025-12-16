# Tech Debt: Scroll Isolation in Document Chunk Viewer

## Issue Summary

**Status**: ACCEPTED LIMITATION ⚠️
**Priority**: Low (P3)
**Component**: Document Chunk Viewer (`/documents/[id]/chunks`)
**Reported**: 2025-12-08

---

## Migration Notice

> **CONSOLIDATED:** This tech debt is tracked in the consolidated tracker.
> See: **[epic-7-tech-debt.md](./epic-7-tech-debt.md)**
>
> **Current Status:** Accepted as Known Limitation
> - `react-resizable-panels` propagates scroll events internally
> - 9 solutions attempted, none fully successful
> - Workaround applied: `overscroll-behavior: contain`
> - Linked scrolling persists as minor UX issue

---

## Problem Description

The document chunk viewer page uses a split-pane layout with:
- **Left panel**: Document viewer (PDF, DOCX, Markdown, Text)
- **Right panel**: Chunk sidebar with scrollable list

**Expected behavior**: Each panel should scroll independently - scrolling in the PDF viewer should NOT scroll the chunk sidebar, and vice versa.

**Actual behavior**: Scrolling in one panel causes both panels to scroll together (linked scrolling).

## Affected Files

- `/frontend/src/app/(protected)/documents/[id]/chunks/page.tsx` - Main page with PanelGroup
- `/frontend/src/components/documents/chunk-viewer/viewers/pdf-viewer.tsx`
- `/frontend/src/components/documents/chunk-viewer/viewers/text-viewer.tsx`
- `/frontend/src/components/documents/chunk-viewer/viewers/docx-viewer.tsx`
- `/frontend/src/components/documents/chunk-viewer/viewers/markdown-viewer.tsx`
- `/frontend/src/components/documents/chunk-viewer/chunk-sidebar.tsx`

## Technical Context

### Current Implementation

The page uses `react-resizable-panels` library for the split-pane layout:

```tsx
<PanelGroup direction="horizontal" className="h-full">
  <Panel defaultSize={65} minSize={30}>
    {/* Document viewer */}
  </Panel>
  <PanelResizeHandle />
  <Panel defaultSize={35} minSize={20} maxSize={50}>
    {/* Chunk sidebar */}
  </Panel>
</PanelGroup>
```

Each viewer component has:
- `overflow-y-auto` for scrolling
- `overscrollBehavior: 'contain'` CSS property
- Native wheel event listener with `e.stopPropagation()`

### Attempted Solutions (All Failed)

1. **CSS `overscroll-behavior: contain`** - Did not prevent scroll propagation between panels

2. **React `onWheel` with `stopPropagation()`** - React's wheel events are passive by default, `preventDefault()` doesn't work

3. **Native wheel event listeners** with `{ passive: false }`:
   ```tsx
   useEffect(() => {
     const handleWheel = (e: WheelEvent) => {
       // Check boundaries
       if ((atTop && isScrollingUp) || (atBottom && isScrollingDown)) {
         e.preventDefault();
       }
       e.stopPropagation();
     };
     container.addEventListener('wheel', handleWheel, { passive: false });
   }, []);
   ```
   - Applied in each viewer component
   - Did not prevent linked scrolling

4. **Panel wrapper level event capture**:
   ```tsx
   container.addEventListener('wheel', handleWheel, { passive: false, capture: true });
   ```
   - Attempted to intercept events at the panel wrapper level
   - Did not work

5. **CSS containment properties**:
   ```css
   isolation: isolate;
   contain: layout style paint;
   ```
   - Caused layout to break (blank page, no scroll)
   - Had to revert

6. **Global CSS targeting panels**:
   ```css
   [data-panel] {
     isolation: isolate;
     contain: layout style paint;
     overflow: hidden;
   }
   ```
   - Also caused layout issues

7. **ScrollArea component wrapper** (radix-ui/react-scroll-area):
   ```tsx
   <Panel>
     <ScrollArea className="h-full">
       {/* viewer content */}
     </ScrollArea>
   </Panel>
   ```
   - Wrapped each panel's content in a ScrollArea component
   - Did not prevent linked scrolling

8. **Panel `overflow: hidden` with isolation wrapper**:
   ```tsx
   <Panel className="overflow-hidden">
     <div style={{ isolation: 'isolate' }} className="h-full w-full overflow-hidden">
       {/* viewer content with overscrollBehavior: contain */}
     </div>
   </Panel>
   ```
   - Added `overflow: hidden` to Panel components
   - Wrapped content in div with `isolation: isolate`
   - Each viewer has `overscrollBehavior: contain`
   - Did not prevent linked scrolling

9. **Custom IsolatedScrollPanel with capture-phase wheel events**:
   ```tsx
   function IsolatedScrollPanel({ children }) {
     const containerRef = useRef<HTMLDivElement>(null);

     useEffect(() => {
       const container = containerRef.current;
       if (!container) return;

       const handleWheel = (e: WheelEvent) => {
         const scrollable = container.querySelector('[data-scroll-container]');
         if (!scrollable) return;

         const { scrollTop, scrollHeight, clientHeight } = scrollable;
         const isAtTop = scrollTop <= 0;
         const isAtBottom = scrollTop + clientHeight >= scrollHeight - 1;

         // Prevent default at boundaries
         if ((isAtTop && e.deltaY < 0) || (isAtBottom && e.deltaY > 0)) {
           e.preventDefault();
         }
         // Always stop propagation
         e.stopPropagation();
       };

       container.addEventListener('wheel', handleWheel, { passive: false, capture: true });
       return () => container.removeEventListener('wheel', handleWheel, { capture: true });
     }, []);

     return (
       <div ref={containerRef} style={{ isolation: 'isolate' }}>
         {children}
       </div>
     );
   }
   ```
   - Created custom component to capture wheel events in capture phase
   - Added `data-scroll-container` attribute to all scrollable elements
   - Applied `{ passive: false, capture: true }` to intercept events early
   - Called both `preventDefault()` and `stopPropagation()`
   - Did not prevent linked scrolling

## Root Cause Analysis

The `react-resizable-panels` library may be propagating scroll events internally through its panel containers. The scroll events might be:

1. Bubbling through the PanelGroup component
2. Being handled at a level above individual panel contents
3. Affected by the library's internal event handling for resize functionality

## Potential Solutions to Investigate

1. **Replace `react-resizable-panels`** with a simpler CSS-based split layout using:
   - CSS Grid with resize handle
   - Flexbox with custom resize logic
   - Different library (e.g., `react-split-pane`, `allotment`)

2. **Iframe isolation** - Render each panel content in an iframe (heavy-handed but guarantees isolation)

3. **Portal-based rendering** - Render scroll containers in React portals outside the panel hierarchy

4. **Custom PanelGroup wrapper** - Create a wrapper that intercepts all wheel events before they reach the library

5. **Library configuration** - Check if `react-resizable-panels` has options to disable scroll event handling

6. **Browser-specific investigation** - Test if the issue is browser-specific (Chrome, Firefox, Safari)

## Reproduction Steps

1. Navigate to any document's chunk viewer: `/documents/[id]/chunks?kb=[kb-id]`
2. Position mouse over the PDF viewer (left panel)
3. Scroll with mouse wheel
4. Observe that the chunk sidebar (right panel) also scrolls

## Impact

- **User Experience**: Users cannot independently browse document content while keeping their place in the chunk list
- **Functionality**: Reduces usefulness of the split-pane view for chunk navigation

## Related Issues

- Story 5-26: Document Chunk Viewer (Frontend)
- AC-5.26.3: Chunk sidebar displays all chunks
- AC-5.26.6: Click chunk scrolls to position in document

## References

- react-resizable-panels: https://github.com/bvaughn/react-resizable-panels
- MDN overscroll-behavior: https://developer.mozilla.org/en-US/docs/Web/CSS/overscroll-behavior
- MDN CSS contain: https://developer.mozilla.org/en-US/docs/Web/CSS/contain
