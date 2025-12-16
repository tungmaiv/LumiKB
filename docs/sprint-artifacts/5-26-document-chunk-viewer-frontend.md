# Story 5-26: Document Chunk Viewer - Frontend UI

**Epic:** Epic 5 - Administration & Polish
**Story ID:** 5-26
**Status:** done
**Created:** 2025-12-07
**Author:** Bob (Scrum Master)

---

## Story

**As a** user or admin,
**I want** to view a document alongside its extracted text chunks in a split-pane interface,
**So that** I can verify AI citations and understand how documents were processed.

---

## Context & Rationale

### Why This Story Matters

Users need to trust AI-generated citations. Admins need to inspect document processing quality. This story delivers a rich split-pane viewer that:
- Shows the original document (PDF, DOCX, MD, TXT) on the left
- Shows extracted chunks in a searchable sidebar on the right
- Highlights the source section when a chunk is selected

### Technical Decisions (from Party Mode Discussion)

| Format | Viewer Library | Highlight Granularity |
|--------|---------------|----------------------|
| PDF | `react-pdf` | Character-level (text layer) |
| DOCX | `docx-preview` | Paragraph-level |
| Markdown | `react-markdown` | Character-level |
| Text | `<pre>` element | Character-level |

**Key Decision:** DOCX highlighting is paragraph-level (not character-level) due to conversion complexity. This was explicitly approved.

### Relationship to Other Stories

**Depends On:**
- **Story 5-25**: Backend API for chunks and content streaming

**Enables:**
- Future: Citation deep-links from chat/search results

**Architectural Fit:**
- New tab in document detail modal
- Reuses existing document metadata from documents panel
- Uses React Query for data fetching

---

## Acceptance Criteria

### AC-5.26.0: Feature Navigation (DoD Learning #5)

**Given** I am viewing a document in the KB dashboard
**When** I click on a document to open its detail modal
**Then** I can access the "View & Chunks" tab from within the modal
**And** no placeholder text remains (e.g., "Coming in Epic X")

**Navigation Path:** KB Dashboard → Document List → Click Document → Detail Modal → "View & Chunks" Tab

**Validation:**
- E2E test: Navigate from dashboard to chunk viewer
- Manual verification: Feature accessible through normal UI flow

---

### AC-5.26.1: Document detail modal has "View & Chunks" tab

**Given** I open a document's detail modal
**When** the modal loads
**Then** I see tabs: [Details] [View & Chunks] [History]
**And** clicking "View & Chunks" shows the split-pane viewer

**Validation:**
- Unit test: Tab navigation renders correctly
- E2E test: Click tab → viewer appears

---

### AC-5.26.2: Split-pane layout with resizable panels

**Given** I am on the "View & Chunks" tab
**When** the viewer loads
**Then** I see:
- Left panel: Document viewer (flexible width, min 40%)
- Right panel: Chunk sidebar (320px default, min 280px)
- Draggable divider between panels

**And** I can drag the divider to resize panels
**And** the layout is responsive:
- Desktop (1024px+): Side-by-side panels
- Tablet/Mobile (<1024px): Stacked vertically (document above, chunks below)

**Validation:**
- Unit test: Split-pane renders with correct initial widths
- E2E test: Drag divider → panels resize

---

### AC-5.26.3: Chunk sidebar displays all chunks with search

**Given** a document has been processed
**When** I view the chunks sidebar
**Then** I see:
- Search box at top with placeholder "Search chunks..."
- Chunk count display (e.g., "47 chunks")
- Scrollable list of chunk items

**And** each chunk shows:
- Chunk number (e.g., "#1", "#2")
- First 3 lines of text as preview
- Expand indicator (▼ or ►)

**And** the list uses virtual scroll for performance with 1000+ chunks

**Validation:**
- Unit test: ChunkSidebar renders search box and count
- Unit test: ChunkItem shows 3-line preview
- Performance test: 1000 chunks scroll smoothly

---

### AC-5.26.4: Chunks expand and collapse

**Given** I see a chunk in collapsed state
**When** I click on it
**Then** the chunk expands to show full text
**And** a collapse button appears at bottom-right [↑ less]

**Given** a chunk is expanded
**When** I click the collapse button
**Then** the chunk returns to 3-line preview state

**And** only one chunk can be expanded at a time (accordion behavior)

**Validation:**
- Unit test: ChunkItem expand/collapse toggle works
- Unit test: Accordion behavior - expanding one collapses others

---

### AC-5.26.5: Search filters chunks in real-time

**Given** I type in the search box
**When** I enter "authentication" and wait 300ms (debounce)
**Then** only chunks containing "authentication" are shown
**And** the chunk count updates (e.g., "12 of 47 chunks")
**And** clearing the search shows all chunks again

**Validation:**
- Unit test: useDocumentChunks hook filters correctly
- Unit test: Debounce delays API call by 300ms

---

### AC-5.26.6: PDF viewer with text layer highlighting

**Given** a PDF document is loaded
**When** I click on a chunk
**Then** the PDF viewer:
- Scrolls to the correct page (`page_number`)
- Highlights the text range (`char_start` to `char_end`)
- Uses yellow background overlay on text layer

**Validation:**
- Unit test: PDFViewer scrolls to page on chunk select
- E2E test: Click chunk → PDF highlights correct section

---

### AC-5.26.7: DOCX viewer with paragraph highlighting

**Given** a DOCX document is loaded
**When** I click on a chunk
**Then** the DOCX viewer:
- Renders the document using `docx-preview`
- Scrolls to the paragraph containing the chunk
- Highlights the entire paragraph (yellow background)

**Note:** Paragraph-level granularity is acceptable (approved in requirements).

**Validation:**
- Unit test: DOCXViewer renders document
- E2E test: Click chunk → DOCX highlights paragraph

---

### AC-5.26.8: Markdown viewer with section highlighting

**Given** a Markdown document is loaded
**When** I click on a chunk
**Then** the Markdown viewer:
- Renders markdown using `react-markdown`
- Scrolls to the character position (`char_start`)
- Highlights the text range with yellow background

**Validation:**
- Unit test: MarkdownViewer renders content
- E2E test: Click chunk → Markdown highlights section

---

### AC-5.26.9: Text viewer with character highlighting

**Given** a plain text document is loaded
**When** I click on a chunk
**Then** the Text viewer:
- Displays text in `<pre>` element with monospace font
- Scrolls to the line containing `char_start`
- Highlights the character range (`char_start` to `char_end`)

**Validation:**
- Unit test: TextViewer highlights character range
- E2E test: Click chunk → Text highlights section

---

### AC-5.26.10: Loading and error states

**Given** I open "View & Chunks" tab
**When** document content is loading
**Then** I see loading skeletons for both panels

**Given** the document fails to load
**When** an error occurs
**Then** I see a friendly error message with retry button

**Given** a document has no chunks (processing failed)
**When** I view the chunks sidebar
**Then** I see "No chunks available" message

**Validation:**
- Unit test: Loading state renders skeletons
- Unit test: Error state renders retry button
- Unit test: Empty state renders message

---

## Dev Notes

### Learnings from Previous Story

**From Story 5-25 (Backend API):** [Source: docs/sprint-artifacts/5-25-document-chunk-viewer-backend.md]
- Backend provides `GET /documents/{id}/chunks` with `search`, `skip`, `limit` params
- Backend provides `GET /documents/{id}/content` for streaming original files
- Chunk metadata includes: `chunk_index`, `chunk_text`, `char_start`, `char_end`, `page_number`, `paragraph_index`
- Optional DOCX→HTML conversion available via `?format=html`

**Applicable to This Story:**
- useDocumentChunks hook should pass `search` param with 300ms debounce
- useDocumentContent hook fetches blob and creates object URL
- Highlight logic uses `char_start`/`char_end` for text, `page_number` for PDF navigation

### Architecture Patterns and Constraints

- **Component Architecture**: Follow existing modal patterns (document-detail-modal.tsx)
- **Hook Patterns**: Use React Query with staleTime for caching (see useAuditLogs, useDocuments)
- **UI Components**: Use shadcn/ui exclusively (Input, Button, Select from existing components)
- **Split Pane**: react-resizable-panels (new dependency, follows Radix patterns)
- **Virtual Scroll**: @tanstack/react-virtual for 1000+ chunk performance

[Source: docs/architecture.md - Frontend Architecture]
[Source: docs/sprint-artifacts/tech-spec-epic-5.md - Stories 5.25-5.26 Technical Notes]

### Project Structure Notes

New files to create:
```
frontend/src/components/documents/document-chunk-viewer/
├── index.tsx                    # Main container
├── chunk-sidebar.tsx            # Search + chunk list
├── chunk-item.tsx               # Expandable chunk
└── viewers/
    ├── pdf-viewer.tsx           # react-pdf
    ├── docx-viewer.tsx          # docx-preview
    ├── markdown-viewer.tsx      # react-markdown
    └── text-viewer.tsx          # <pre> element

frontend/src/hooks/
├── useDocumentChunks.ts         # Fetch chunks with search
└── useDocumentContent.ts        # Fetch file blob
```

[Source: docs/sprint-artifacts/tech-spec-epic-5.md - Component Architecture diagram]

### References

- [Tech Spec Epic 5 - Story 5.26](./tech-spec-epic-5.md) - AC definitions, test strategy, traceability
- [Architecture](../architecture.md) - Frontend patterns, hook conventions
- [Story 5-25 Backend API](./5-25-document-chunk-viewer-backend.md) - API contract this story consumes
- [Story 5-24 Dashboard Filtering](./5-24-kb-dashboard-filtering.md) - URL sync and filter patterns

---

## Technical Design

### Component Architecture

```
frontend/src/components/documents/
├── document-detail-modal.tsx        # Extended with tabs
├── document-chunk-viewer/
│   ├── index.tsx                    # Main split-pane container
│   ├── chunk-sidebar.tsx            # Search + chunk list
│   ├── chunk-item.tsx               # Expandable chunk preview
│   └── viewers/
│       ├── pdf-viewer.tsx           # react-pdf + highlight overlay
│       ├── docx-viewer.tsx          # docx-preview + paragraph highlight
│       ├── markdown-viewer.tsx      # react-markdown + highlight
│       └── text-viewer.tsx          # <pre> + character highlight

frontend/src/hooks/
├── useDocumentChunks.ts             # Fetch & search chunks
└── useDocumentContent.ts            # Fetch original file blob
```

### New Dependencies

```json
{
  "react-pdf": "9.1.0",
  "pdfjs-dist": "4.0.0",
  "docx-preview": "0.3.2",
  "react-markdown": "9.0.0",
  "react-resizable-panels": "2.0.0",
  "@tanstack/react-virtual": "3.0.0"
}
```

**Note:** Exact versions pinned (no `^`) for reproducible builds.

### Key Components

**DocumentChunkViewer (index.tsx)**

```typescript
interface DocumentChunkViewerProps {
  document: Document;
}

export function DocumentChunkViewer({ document }: DocumentChunkViewerProps) {
  const [selectedChunk, setSelectedChunk] = useState<DocumentChunk | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const { chunks, total, isLoading, error } = useDocumentChunks(
    document.id,
    searchQuery
  );

  const { contentUrl, contentType, isLoading: contentLoading } = useDocumentContent(
    document.id
  );

  const ViewerComponent = useMemo(() => {
    switch (document.mime_type) {
      case 'application/pdf':
        return PDFViewer;
      case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return DOCXViewer;
      case 'text/markdown':
        return MarkdownViewer;
      default:
        return TextViewer;
    }
  }, [document.mime_type]);

  return (
    <ResizablePanelGroup direction="horizontal">
      <ResizablePanel defaultSize={60} minSize={40}>
        <ViewerComponent
          contentUrl={contentUrl}
          selectedChunk={selectedChunk}
          isLoading={contentLoading}
        />
      </ResizablePanel>

      <ResizableHandle />

      <ResizablePanel defaultSize={40} minSize={25}>
        <ChunkSidebar
          chunks={chunks}
          total={total}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selectedChunk={selectedChunk}
          onChunkSelect={setSelectedChunk}
          isLoading={isLoading}
        />
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
```

**ChunkSidebar**

```typescript
interface ChunkSidebarProps {
  chunks: DocumentChunk[];
  total: number;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedChunk: DocumentChunk | null;
  onChunkSelect: (chunk: DocumentChunk) => void;
  isLoading: boolean;
}

export function ChunkSidebar({
  chunks,
  total,
  searchQuery,
  onSearchChange,
  selectedChunk,
  onChunkSelect,
  isLoading,
}: ChunkSidebarProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const debouncedSearch = useDebounce(searchQuery, 300);

  const parentRef = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({
    count: chunks.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
  });

  return (
    <div className="flex flex-col h-full">
      {/* Search Box */}
      <div className="p-3 border-b">
        <Input
          placeholder="Search chunks..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground mt-1">
          {searchQuery ? `${chunks.length} of ${total} chunks` : `${total} chunks`}
        </p>
      </div>

      {/* Virtual Scroll List */}
      <div ref={parentRef} className="flex-1 overflow-auto">
        {isLoading ? (
          <ChunkListSkeleton />
        ) : chunks.length === 0 ? (
          <EmptyState message="No chunks available" />
        ) : (
          <div
            style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}
          >
            {virtualizer.getVirtualItems().map((virtualItem) => {
              const chunk = chunks[virtualItem.index];
              return (
                <ChunkItem
                  key={chunk.chunk_index}
                  chunk={chunk}
                  isExpanded={expandedIndex === virtualItem.index}
                  isSelected={selectedChunk?.chunk_index === chunk.chunk_index}
                  onExpand={() => {
                    setExpandedIndex(
                      expandedIndex === virtualItem.index ? null : virtualItem.index
                    );
                    onChunkSelect(chunk);
                  }}
                  onCollapse={() => setExpandedIndex(null)}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    transform: `translateY(${virtualItem.start}px)`,
                  }}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
```

**ChunkItem**

```typescript
interface ChunkItemProps {
  chunk: DocumentChunk;
  isExpanded: boolean;
  isSelected: boolean;
  onExpand: () => void;
  onCollapse: () => void;
  style?: React.CSSProperties;
}

export function ChunkItem({
  chunk,
  isExpanded,
  isSelected,
  onExpand,
  onCollapse,
  style,
}: ChunkItemProps) {
  // Get first 3 lines for preview
  const preview = useMemo(() => {
    const lines = chunk.chunk_text.split('\n').slice(0, 3);
    return lines.join('\n') + (chunk.chunk_text.split('\n').length > 3 ? '...' : '');
  }, [chunk.chunk_text]);

  return (
    <div
      style={style}
      className={cn(
        'p-3 border-b cursor-pointer hover:bg-muted/50 transition-colors',
        isSelected && 'bg-primary/10 border-l-2 border-l-primary'
      )}
      onClick={onExpand}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-medium text-muted-foreground">
          #{chunk.chunk_index + 1}
        </span>
        {chunk.page_number && (
          <span className="text-xs text-muted-foreground">
            (Page {chunk.page_number})
          </span>
        )}
        <span className="ml-auto">
          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </span>
      </div>

      {isExpanded ? (
        <div className="relative">
          <p className="text-sm whitespace-pre-wrap">{chunk.chunk_text}</p>
          <Button
            variant="ghost"
            size="sm"
            className="absolute bottom-0 right-0"
            onClick={(e) => {
              e.stopPropagation();
              onCollapse();
            }}
          >
            ↑ less
          </Button>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground line-clamp-3">
          {preview}
        </p>
      )}
    </div>
  );
}
```

**PDFViewer with Highlighting**

```typescript
interface PDFViewerProps {
  contentUrl: string;
  selectedChunk: DocumentChunk | null;
  isLoading: boolean;
}

export function PDFViewer({ contentUrl, selectedChunk, isLoading }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const containerRef = useRef<HTMLDivElement>(null);

  // Scroll to page when chunk selected
  useEffect(() => {
    if (selectedChunk?.page_number) {
      setCurrentPage(selectedChunk.page_number);
    }
  }, [selectedChunk]);

  if (isLoading) {
    return <ViewerSkeleton />;
  }

  return (
    <div ref={containerRef} className="h-full overflow-auto">
      <Document
        file={contentUrl}
        onLoadSuccess={({ numPages }) => setNumPages(numPages)}
      >
        <Page
          pageNumber={currentPage}
          renderTextLayer={true}
          renderAnnotationLayer={false}
          customTextRenderer={({ str, itemIndex }) => {
            // Highlight logic based on char_start/char_end
            if (selectedChunk) {
              // Apply highlight class if text overlaps with chunk
              return `<span class="chunk-highlight">${str}</span>`;
            }
            return str;
          }}
        />
      </Document>

      {/* Page Navigation */}
      <div className="sticky bottom-0 bg-background border-t p-2 flex items-center justify-center gap-4">
        <Button
          variant="outline"
          size="icon"
          disabled={currentPage <= 1}
          onClick={() => setCurrentPage((p) => p - 1)}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-sm">
          Page {currentPage} of {numPages}
        </span>
        <Button
          variant="outline"
          size="icon"
          disabled={currentPage >= numPages}
          onClick={() => setCurrentPage((p) => p + 1)}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
```

### Hooks

**useDocumentChunks**

```typescript
export function useDocumentChunks(documentId: string, searchQuery: string) {
  const debouncedSearch = useDebounce(searchQuery, 300);

  return useQuery({
    queryKey: ['document-chunks', documentId, debouncedSearch],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (debouncedSearch) params.set('search', debouncedSearch);

      const response = await fetch(
        `/api/v1/documents/${documentId}/chunks?${params}`
      );
      if (!response.ok) throw new Error('Failed to fetch chunks');
      return response.json();
    },
  });
}
```

**useDocumentContent**

```typescript
export function useDocumentContent(documentId: string) {
  return useQuery({
    queryKey: ['document-content', documentId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/documents/${documentId}/content`);
      if (!response.ok) throw new Error('Failed to fetch content');

      const blob = await response.blob();
      return {
        url: URL.createObjectURL(blob),
        type: response.headers.get('content-type'),
      };
    },
    staleTime: Infinity, // Don't refetch document content
  });
}
```

---

## Tasks

### Frontend Tasks

- [ ] **Task 1: Add new dependencies** (AC: all)
  - Install react-pdf@9.1.0, pdfjs-dist@4.0.0, docx-preview@0.3.2, react-markdown@9.0.0, react-resizable-panels@2.0.0, @tanstack/react-virtual@3.0.0
  - Configure PDF.js worker

- [ ] **Task 2: Create useDocumentChunks hook** (AC: 5.26.3, 5.26.5)
  - Implement React Query hook (AC: 5.26.3)
  - Debounced search (AC: 5.26.5)
  - Write 3 unit tests

- [ ] **Task 3: Create useDocumentContent hook** (AC: 5.26.6, 5.26.7, 5.26.8, 5.26.9)
  - Fetch and create blob URL
  - Handle cleanup on unmount
  - Write 2 unit tests

- [ ] **Task 4: Create ChunkItem component** (AC: 5.26.3, 5.26.4)
  - 3-line preview logic (AC: 5.26.3)
  - Expand/collapse animation (AC: 5.26.4)
  - Write 3 unit tests

- [ ] **Task 5: Create ChunkSidebar component** (AC: 5.26.3, 5.26.5)
  - Search box with debounce (AC: 5.26.5)
  - Virtual scroll list (AC: 5.26.3)
  - Chunk count display (AC: 5.26.3)
  - Write 4 unit tests

- [ ] **Task 6: Create PDFViewer component** (AC: 5.26.6)
  - react-pdf integration
  - Page navigation
  - Text layer highlighting
  - Write 3 unit tests

- [ ] **Task 7: Create DOCXViewer component** (AC: 5.26.7)
  - docx-preview integration
  - Paragraph highlighting
  - Write 2 unit tests

- [ ] **Task 8: Create MarkdownViewer component** (AC: 5.26.8)
  - react-markdown rendering
  - Character range highlighting
  - Write 2 unit tests

- [ ] **Task 9: Create TextViewer component** (AC: 5.26.9)
  - Pre-formatted display
  - Character highlighting
  - Write 2 unit tests

- [ ] **Task 10: Create DocumentChunkViewer container** (AC: 5.26.2)
  - Split-pane layout with react-resizable-panels
  - Format-specific viewer switching
  - Write 3 unit tests

- [ ] **Task 11: Extend document detail modal with tabs** (AC: 5.26.0, 5.26.1)
  - Add tab navigation (AC: 5.26.1)
  - Wire up View & Chunks tab (AC: 5.26.0)
  - Write 2 unit tests

- [ ] **Task 12: Add responsive behavior** (AC: 5.26.2)
  - Stack panels on mobile
  - Test breakpoints
  - Write 1 unit test

- [ ] **Task 13: Write E2E tests** (AC: 5.26.0, 5.26.6, 5.26.7, 5.26.5)
  - Navigate to chunk viewer via modal (AC: 5.26.0)
  - Upload PDF → view chunks → click chunk → verify highlight (AC: 5.26.6)
  - Upload DOCX → view chunks → verify paragraph highlight (AC: 5.26.7)
  - Search chunks → verify filtering (AC: 5.26.5)
  - Verify split-pane resize (AC: 5.26.2)
  - Write 5 E2E tests

---

## Definition of Done

- [ ] All 11 acceptance criteria validated (AC-5.26.0 through AC-5.26.10)
- [ ] Frontend: 27 unit tests passing
- [ ] E2E: 5 tests passing (includes navigation test)
- [ ] No linting errors (ESLint)
- [ ] Type safety enforced (TypeScript strict)
- [ ] Responsive design verified (desktop, tablet, mobile)
- [ ] Performance acceptable (1000 chunks scroll smoothly)
- [ ] Code reviewed

---

## Dependencies

- **Blocked By:** Story 5-25 (Backend API)
- **Blocks:** None (end-user feature)

---

## Story Points

**Estimate:** 8 story points (3-4 days)

---

## Notes

- PDF highlighting uses react-pdf's text layer - may need custom CSS
- DOCX rendering with docx-preview is client-side (no server conversion needed)
- Virtual scroll is critical for documents with 500+ chunks
- Consider lazy-loading viewers to reduce initial bundle size

---

## Wireframe Reference

```
┌─────────────────────────────────────────────────────────────────────┐
│  Document: requirements.pdf                              [✕ Close] │
├─────────────────────────────────────────────────────────────────────┤
│  [📋 Details]  [📄 View & Chunks]  [📜 History]                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────┬───────────────────────────────┐   │
│  │                             │  🔍 [Search chunks...]        │   │
│  │                             │  ───────────────────────────  │   │
│  │    PDF Viewer               │  47 chunks                    │   │
│  │    ┌───────────────────┐    │  ───────────────────────────  │   │
│  │    │                   │    │  📄 #1                        │   │
│  │    │   Page 3 of 12    │    │  "The system shall provide... │   │
│  │    │                   │    │  authentication using..."     │   │
│  │    │  ═══════════════  │    │                    [▼]        │   │
│  │    │  ║ HIGHLIGHTED ║◄─┼────│  ───────────────────────────  │   │
│  │    │  ═══════════════  │    │  📄 #2 (selected, expanded)   │   │
│  │    │                   │    │  "Vector embeddings are       │   │
│  │    │                   │    │  generated using the Gemini   │   │
│  │    └───────────────────┘    │  text-embedding-004 model     │   │
│  │    [◀] Page 3 of 12 [▶]     │  which produces 768-dim..."   │   │
│  │                             │                    [↑ less]   │   │
│  │                             │  ───────────────────────────  │   │
│  │                             │  📄 #3                        │   │
│  │                             │  "Security considerations..." │   │
│  │                             │                    [▼]        │   │
│  └─────────────────────────────┴───────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-07 | Bob (SM) | Initial story created from Party Mode discussion |
| 2025-12-07 | Bob (SM) | Added AC-5.26.0 (Navigation) per DoD Learning #5; updated test counts (11 ACs, 5 E2E) |
| 2025-12-07 | Bob (SM) | Added Dev Notes with Learnings, Architecture, Project Structure, References sections |
| 2025-12-07 | Bob (SM) | Added AC references to all tasks; Fixed Task 13 E2E count (4→5) to match DoD; Pinned exact npm versions |
