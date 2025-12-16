# Story 6-7: Archive Management UI

## Story Information
- **Epic:** 6 - Document Lifecycle Management
- **Story ID:** 6-7
- **Story Points:** 5
- **Priority:** HIGH
- **Status:** ready-for-dev

## User Story
**As a** KB owner or admin
**I want** to view and manage all archived documents in a dedicated interface
**So that** I can restore or permanently delete archived documents as needed

## Context
The Archive Management page provides a centralized interface for viewing all archived documents across the user's accessible KBs. It supports filtering by KB, searching by document name, pagination, and actions to restore or purge archived documents.

## Acceptance Criteria

### AC-6.7.1: Archive page accessible via navigation
**Given** I am authenticated as KB owner or admin
**When** I click "Archive" in the sidebar navigation
**Then** I am navigated to /archive page
**And** I see a list of archived documents I have access to

### AC-6.7.2: Archive list displays document metadata
**Given** I am viewing the archive page
**When** the page loads
**Then** I see a table with columns: Name, KB Name, Archived Date, Original Completion Date, File Size, Actions
**And** documents are sorted by archived date (most recent first) by default

### AC-6.7.3: Filter by Knowledge Base
**Given** I am viewing the archive page
**When** I select a KB from the filter dropdown
**Then** only archived documents from that KB are displayed

### AC-6.7.4: Search archived documents
**Given** I am viewing the archive page
**When** I type in the search box
**Then** documents are filtered by name (case-insensitive partial match)

### AC-6.7.5: Pagination support
**Given** there are more than 20 archived documents
**When** I view the archive page
**Then** I see pagination controls
**And** I can navigate between pages

### AC-6.7.6: Restore action from archive page
**Given** I am viewing an archived document in the list
**When** I click the Restore button
**Then** a confirmation dialog appears
**And** on confirm, the document is restored
**And** the document disappears from the archive list
**And** a success toast notification is shown

### AC-6.7.7: Purge action from archive page
**Given** I am viewing an archived document in the list
**When** I click the Purge button
**Then** a two-step confirmation dialog appears (warning about permanent deletion)
**And** on confirm, the document is permanently deleted
**And** the document disappears from the archive list
**And** a success toast notification is shown

### AC-6.7.8: Bulk purge selection
**Given** I am viewing the archive page
**When** I select multiple documents using checkboxes
**Then** I see a "Purge Selected" button
**And** clicking it shows a confirmation with count of selected documents
**And** on confirm, all selected documents are purged

### AC-6.7.9: Handle restore name collision
**Given** I attempt to restore a document
**And** a document with the same name exists in that KB
**When** the restore fails with 409
**Then** an error message is shown: "Cannot restore: a document with this name already exists"

### AC-6.7.10: Empty state display
**Given** there are no archived documents
**When** I view the archive page
**Then** I see an empty state message: "No archived documents"

## Technical Notes

### New Files to Create
```
frontend/src/app/(protected)/archive/page.tsx
frontend/src/hooks/useArchive.ts
frontend/src/components/archive/archive-table.tsx
frontend/src/components/archive/purge-confirmation-modal.tsx
frontend/src/components/archive/restore-confirmation-modal.tsx
```

### API Integration
```typescript
// GET /api/v1/documents/archived
interface ArchivedDocumentsResponse {
  items: ArchivedDocument[];
  total: number;
  page: number;
  limit: number;
}

interface ArchivedDocument {
  id: string;
  name: string;
  kb_id: string;
  kb_name: string;
  status: 'archived';
  archived_at: string;
  completed_at: string;
  file_size: number;
}
```

### useArchive Hook
```typescript
export function useArchive(params: ArchiveParams) {
  // Query for archived documents
  const query = useQuery({
    queryKey: ['archived-documents', params],
    queryFn: () => fetchArchivedDocuments(params),
  });

  // Mutations
  const restoreMutation = useMutation({
    mutationFn: (docId: string) => restoreDocument(docId),
    onSuccess: () => {
      queryClient.invalidateQueries(['archived-documents']);
      toast.success('Document restored');
    },
  });

  const purgeMutation = useMutation({
    mutationFn: (docId: string) => purgeDocument(docId),
    onSuccess: () => {
      queryClient.invalidateQueries(['archived-documents']);
      toast.success('Document permanently deleted');
    },
  });

  const bulkPurgeMutation = useMutation({
    mutationFn: (docIds: string[]) => bulkPurgeDocuments(docIds),
    onSuccess: (result) => {
      queryClient.invalidateQueries(['archived-documents']);
      toast.success(`${result.purged} documents purged`);
    },
  });

  return { query, restoreMutation, purgeMutation, bulkPurgeMutation };
}
```

### Navigation Update
Add Archive link to sidebar navigation for owners/admins:
```tsx
// frontend/src/components/layout/kb-sidebar.tsx
{(isOwner || isAdmin) && (
  <Link href="/archive" className="...">
    <ArchiveIcon className="h-4 w-4" />
    Archive
  </Link>
)}
```

## Dependencies
- Story 6-1: Archive Document Backend (provides archived status)
- Story 6-2: Restore Document Backend (provides restore API)
- Story 6-3: Purge Document Backend (provides purge and bulk purge APIs)

## Test Cases

### Component Tests
1. ArchivePage renders empty state when no documents
2. ArchivePage displays documents in table
3. KB filter updates document list
4. Search filters documents by name
5. Pagination controls work correctly
6. Restore button triggers confirmation and API call
7. Purge button triggers two-step confirmation
8. Bulk selection enables bulk purge button

### E2E Tests
1. Navigate to archive page from sidebar
2. Filter archived documents by KB
3. Search archived documents
4. Restore document from archive
5. Purge single document with confirmation
6. Bulk purge multiple documents

## Definition of Done
- [ ] /archive page created with table layout
- [ ] useArchive hook implemented with React Query
- [ ] KB filter dropdown implemented
- [ ] Search functionality implemented
- [ ] Pagination implemented
- [ ] Restore confirmation modal implemented
- [ ] Purge two-step confirmation modal implemented
- [ ] Bulk selection and purge implemented
- [ ] Error handling for name collision
- [ ] Empty state implemented
- [ ] Navigation link added to sidebar
- [ ] Component tests passing (8+)
- [ ] E2E tests passing (6+)
- [ ] Code review approved
