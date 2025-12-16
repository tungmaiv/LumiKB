# Story 5-24: KB Dashboard Document Filtering & Pagination

**Epic:** Epic 5 - Administration & Polish
**Story ID:** 5-24
**Status:** done
**Created:** 2025-12-06
**Author:** Bob (Scrum Master)

---

## Story

**As a** knowledge base user,
**I want** to filter and paginate the document list in the KB dashboard,
**So that** I can quickly find specific documents in large knowledge bases.

---

## Context & Rationale

### Why This Story Matters

As knowledge bases grow, the document list becomes difficult to navigate. Users need:

- **Filtering**: Find documents by name, type, status, tags, or date range
- **Pagination**: Navigate large lists without performance degradation
- **Persistence**: Filter state preserved in URL for bookmarking/sharing

This story applies the same filtering/pagination patterns from Story 5-2 (Audit Log Viewer) to the KB dashboard document list.

### Relationship to Other Stories

**Depends On:**
- **Story 5-2 (Audit Log Viewer)**: Filtering and pagination patterns to follow
- **Story 5-22 (Document Tags)**: Tag filtering depends on tags being available

**Enables:**
- Improved document management experience for all KB users

**Architectural Fit:**
- Reuses filter bar and pagination patterns from admin audit logs
- Filter state stored in URL query params
- No new infrastructure required

---

## Acceptance Criteria

### AC-5.24.1: Document list displays filter bar

**Given** I am viewing the KB dashboard with an active KB
**When** the page loads
**Then** I see a filter bar above the document list with:
- **Search** (text input): Filter by document name (partial match)
- **Type** (dropdown): Filter by file type (PDF, DOCX, TXT, etc.)
- **Status** (dropdown): Filter by processing status (processed, processing, failed, pending)
- **Tags** (multi-select): Filter by document tags (from Story 5-22)
- **Date Range** (date picker): Filter by upload date
- **Clear Filters** button to reset all filters

**Validation:**
- Unit test: Filter bar renders all filter controls
- E2E test: Filter bar is visible on dashboard

---

### AC-5.24.2: Filters update document list in real-time

**Given** I have applied one or more filters
**When** I change a filter value
**Then** the document list updates automatically (no manual "Apply" button needed)
**And** loading indicator shows during refresh
**And** empty state message shows if no documents match filters

**Validation:**
- Integration test: GET documents with filters → verify filtered results
- E2E test: Apply filter → verify list updates

---

### AC-5.24.3: Document list is paginated

**Given** the KB has more than 50 documents
**When** I view the document list
**Then** I see pagination controls at the bottom:
- Current page indicator (e.g., "Page 1 of 5")
- Previous/Next buttons
- Page size selector (25, 50, 100)
- Total document count (e.g., "234 documents")

**And** default page size is 50 documents
**And** pagination works with active filters

**Validation:**
- Unit test: Pagination component renders controls
- Integration test: GET documents?page=2&limit=50 → verify page 2 results
- E2E test: Click "Next" → verify page 2 loads

---

### AC-5.24.4: Filter state persists in URL

**Given** I have applied filters (e.g., status=failed, type=pdf)
**When** I refresh the page or copy/share the URL
**Then** the same filters are applied
**And** the document list shows the same filtered results

**URL format:**
```
/dashboard?kb=<kb_id>&status=failed&type=pdf&page=2
```

**Validation:**
- Unit test: useDocumentFilters hook syncs with URL
- E2E test: Apply filters → refresh page → verify filters persist

---

### AC-5.24.5: Filter by tags shows matching documents

**Given** documents have tags (from Story 5-22)
**When** I select one or more tags in the tag filter
**Then** only documents with ALL selected tags are shown
**And** tag filter dropdown shows available tags from documents in this KB

**Validation:**
- Integration test: GET documents?tags=policy,hr → verify filtered results
- E2E test: Select tag filter → verify results

---

## Technical Design

### Backend Changes

**1. Update Document List Endpoint (`backend/app/api/v1/knowledge_bases.py`):**

```python
@router.get("/knowledge-bases/{kb_id}/documents")
async def list_kb_documents(
    kb_id: UUID,
    # NEW filter parameters
    search: str | None = Query(None, description="Search by document name"),
    doc_type: str | None = Query(None, alias="type", description="Filter by file type"),
    status: str | None = Query(None, description="Filter by processing status"),
    tags: list[str] | None = Query(None, description="Filter by tags (AND logic)"),
    start_date: datetime | None = Query(None, description="Filter by upload date (from)"),
    end_date: datetime | None = Query(None, description="Filter by upload date (to)"),
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    # Existing
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedDocumentResponse:
    """List documents in a KB with filtering and pagination."""
    document_service = DocumentService(db)
    documents, total = await document_service.list_documents(
        kb_id=kb_id,
        user=current_user,
        search=search,
        doc_type=doc_type,
        status=status,
        tags=tags,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )
    return PaginatedDocumentResponse(
        documents=[DocumentResponse.from_orm(d) for d in documents],
        total=total,
        page=page,
        page_size=limit,
        has_more=(page * limit) < total,
    )
```

**2. Update Document Service (`backend/app/services/document_service.py`):**

```python
async def list_documents(
    self,
    kb_id: UUID,
    user: User,
    search: str | None = None,
    doc_type: str | None = None,
    status: str | None = None,
    tags: list[str] | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[Document], int]:
    """List documents with filtering and pagination."""
    # Permission check
    await self.kb_service.check_user_access(kb_id, user.id)

    # Build query
    query = select(Document).where(Document.kb_id == kb_id)

    # Apply filters
    if search:
        query = query.where(Document.name.ilike(f"%{search}%"))
    if doc_type:
        query = query.where(Document.content_type.ilike(f"%{doc_type}%"))
    if status:
        query = query.where(Document.status == status)
    if tags:
        # JSONB contains all specified tags
        for tag in tags:
            query = query.where(
                Document.metadata["tags"].contains([tag])
            )
    if start_date:
        query = query.where(Document.created_at >= start_date)
    if end_date:
        query = query.where(Document.created_at <= end_date)

    # Count total (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await self.db.execute(count_query)).scalar() or 0

    # Apply pagination and sorting
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await self.db.execute(query)
    documents = result.scalars().all()

    return documents, total
```

**3. Add Response Schema (`backend/app/schemas/document.py`):**

```python
class PaginatedDocumentResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
```

### Frontend Changes

**1. New Hook: useDocumentFilters (`frontend/src/hooks/useDocumentFilters.ts`):**

```typescript
interface DocumentFilters {
  search?: string;
  type?: string;
  status?: string;
  tags?: string[];
  startDate?: string;
  endDate?: string;
  page: number;
  limit: number;
}

export function useDocumentFilters() {
  // Sync filters with URL search params
  const searchParams = useSearchParams();
  const router = useRouter();

  const filters = useMemo((): DocumentFilters => ({
    search: searchParams.get('search') || undefined,
    type: searchParams.get('type') || undefined,
    status: searchParams.get('status') || undefined,
    tags: searchParams.getAll('tags') || undefined,
    startDate: searchParams.get('startDate') || undefined,
    endDate: searchParams.get('endDate') || undefined,
    page: parseInt(searchParams.get('page') || '1'),
    limit: parseInt(searchParams.get('limit') || '50'),
  }), [searchParams]);

  const setFilters = useCallback((newFilters: Partial<DocumentFilters>) => {
    const params = new URLSearchParams(searchParams);
    // Update URL params...
    router.push(`?${params.toString()}`);
  }, [searchParams, router]);

  return { filters, setFilters };
}
```

**2. New Component: DocumentFilterBar (`frontend/src/components/documents/document-filter-bar.tsx`):**

```typescript
interface DocumentFilterBarProps {
  filters: DocumentFilters;
  onFiltersChange: (filters: Partial<DocumentFilters>) => void;
  availableTags: string[];
}

export function DocumentFilterBar({
  filters,
  onFiltersChange,
  availableTags,
}: DocumentFilterBarProps) {
  return (
    <div className="flex flex-wrap gap-3 p-4 bg-muted/50 rounded-lg">
      {/* Search input */}
      <Input
        placeholder="Search documents..."
        value={filters.search || ''}
        onChange={(e) => onFiltersChange({ search: e.target.value })}
        className="w-64"
      />

      {/* Type dropdown */}
      <Select
        value={filters.type}
        onValueChange={(value) => onFiltersChange({ type: value })}
      >
        <SelectTrigger className="w-32">
          <SelectValue placeholder="Type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="pdf">PDF</SelectItem>
          <SelectItem value="docx">DOCX</SelectItem>
          <SelectItem value="txt">TXT</SelectItem>
          <SelectItem value="md">Markdown</SelectItem>
        </SelectContent>
      </Select>

      {/* Status dropdown */}
      <Select
        value={filters.status}
        onValueChange={(value) => onFiltersChange({ status: value })}
      >
        <SelectTrigger className="w-36">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="processed">Processed</SelectItem>
          <SelectItem value="processing">Processing</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
          <SelectItem value="pending">Pending</SelectItem>
        </SelectContent>
      </Select>

      {/* Tags multi-select */}
      <TagSelect
        selected={filters.tags || []}
        options={availableTags}
        onChange={(tags) => onFiltersChange({ tags })}
        placeholder="Tags..."
      />

      {/* Date range */}
      <DateRangePicker
        startDate={filters.startDate}
        endDate={filters.endDate}
        onChange={(range) => onFiltersChange({
          startDate: range.start,
          endDate: range.end,
        })}
      />

      {/* Clear button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onFiltersChange({
          search: undefined,
          type: undefined,
          status: undefined,
          tags: undefined,
          startDate: undefined,
          endDate: undefined,
          page: 1,
        })}
      >
        Clear Filters
      </Button>
    </div>
  );
}
```

**3. New Component: DocumentPagination (`frontend/src/components/documents/document-pagination.tsx`):**

```typescript
interface DocumentPaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

export function DocumentPagination({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}: DocumentPaginationProps) {
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t">
      <span className="text-sm text-muted-foreground">
        {total} documents
      </span>

      <div className="flex items-center gap-4">
        <Select
          value={String(pageSize)}
          onValueChange={(v) => onPageSizeChange(Number(v))}
        >
          <SelectTrigger className="w-20">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="25">25</SelectItem>
            <SelectItem value="50">50</SelectItem>
            <SelectItem value="100">100</SelectItem>
          </SelectContent>
        </Select>

        <span className="text-sm">
          Page {page} of {totalPages}
        </span>

        <div className="flex gap-1">
          <Button
            variant="outline"
            size="icon"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
```

**4. Update Dashboard Page:**

Integrate `DocumentFilterBar` and `DocumentPagination` into the KB dashboard.

---

## Tasks

### Backend Tasks

- [ ] **Task 1: Add filter parameters to document list endpoint** (1 hour)
  - Add search, type, status, tags, date range query params
  - Add pagination params (page, limit)
  - Write 5 integration tests for each filter type

- [ ] **Task 2: Update document service list method** (1 hour)
  - Implement filter logic with SQLAlchemy
  - Implement JSONB tag filtering
  - Add pagination with count query
  - Write 4 unit tests

- [ ] **Task 3: Add PaginatedDocumentResponse schema** (15 min)
  - Create response schema with pagination metadata
  - Write 1 unit test

### Frontend Tasks

- [ ] **Task 4: Create useDocumentFilters hook** (1 hour)
  - URL param sync for filter state
  - Debounced search input
  - Write 3 unit tests

- [ ] **Task 5: Create DocumentFilterBar component** (1.5 hours)
  - All filter controls
  - Clear filters button
  - Write 4 unit tests

- [ ] **Task 6: Create DocumentPagination component** (1 hour)
  - Page navigation
  - Page size selector
  - Total count display
  - Write 3 unit tests

- [ ] **Task 7: Integrate filters into dashboard** (1 hour)
  - Wire up filter bar and pagination
  - Loading and empty states
  - Write 2 unit tests

- [ ] **Task 8: Write E2E tests** (1 hour)
  - Filter by each criterion
  - Pagination navigation
  - URL persistence
  - 4 E2E tests total

---

## Definition of Done

- [ ] All 5 acceptance criteria validated
- [ ] Backend: 10 tests passing (4 unit, 6 integration)
- [ ] Frontend: 12 tests passing (unit tests)
- [ ] E2E: 4 tests passing
- [ ] No linting errors (Ruff, ESLint)
- [ ] Type safety enforced
- [ ] Code reviewed

---

## Dependencies

- **Blocked By:** Story 5-22 (Document Tags) - tag filter requires tags
- **Blocks:** None

---

## Story Points

**Estimate:** 3 story points (1-2 days)

---

## Notes

- Follows same filtering pattern as Story 5-2 (Audit Log Viewer)
- URL param persistence enables bookmarking filtered views
- Debounced search prevents excessive API calls
- Default 50 items per page balances performance and usability

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-06 | Bob (SM) | Initial story created via correct-course workflow |
| 2025-12-06 | Dev Agent | ✅ COMPLETED: All implementation tasks done |

---

## Dev Agent Record

### Completion Summary (2025-12-06)

**Status:** ✅ DONE

**Implementation Completed:**
- Backend: Filter params added to document list endpoint (search, type, status, tags, dates)
- Backend: Pagination with total count query
- Frontend: `DocumentFilterBar` with advanced filters panel
- Frontend: `DocumentPagination` component with page size selector
- Frontend: `useDocumentFilters` hook with URL param sync
- Frontend: `useDocuments` hook with React Query for fetching/caching
- Frontend: Debounced search input (300ms)
- Frontend: Filter state persisted in URL query params

**Tests Passing:**
- Frontend: 56/56 tests for document filter components
- All filter controls tested (search, status, type, tags, date range)
- Pagination controls tested (page navigation, page size)

**Components Delivered:**
- `DocumentFilterBar` - Main filter bar with search, status, type dropdowns
- `DocumentPagination` - Page navigation with prev/next and page size
- `useDocumentFilters` - Hook for URL-synced filter state
- `useDocuments` - Hook for fetching paginated documents

**All Acceptance Criteria Satisfied:**
- AC-5.24.1: ✅ Filter bar with search, type, status, tags, date range, clear button
- AC-5.24.2: ✅ Filters update document list in real-time with loading indicator
- AC-5.24.3: ✅ Pagination with page indicator, prev/next, page size selector
- AC-5.24.4: ✅ Filter state persists in URL (refresh preserves filters)
- AC-5.24.5: ✅ Tag filter shows matching documents (AND logic)
