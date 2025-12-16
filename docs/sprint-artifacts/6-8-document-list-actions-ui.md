# Story 6-8: Document List Archive/Clear Actions UI

## Story Information
- **Epic:** 6 - Document Lifecycle Management
- **Story ID:** 6-8
- **Story Points:** 3
- **Priority:** MEDIUM
- **Status:** ready-for-dev

## User Story
**As a** KB owner or admin
**I want** to archive completed documents and clear failed documents directly from the document list
**So that** I can manage document lifecycle without navigating away from the KB view

## Context
This story extends the existing document list UI with lifecycle actions. The document actions menu (three-dot menu) gains Archive, Clear, and Cancel Processing options based on document status. Archive is available for completed documents, Clear is available for failed documents, and Cancel Processing is available for pending/processing documents.

## Acceptance Criteria

### AC-6.8.1: Archive action visible for completed documents
**Given** I am viewing a KB document list as owner or admin
**And** a document has status "completed"
**When** I click the document actions menu (three-dot)
**Then** I see an "Archive" option

### AC-6.8.2: Archive action triggers confirmation
**Given** I click Archive on a completed document
**When** the confirmation dialog appears
**Then** I see message explaining document will be removed from search
**And** I can confirm or cancel the action

### AC-6.8.3: Archive success updates UI
**Given** I confirm archiving a document
**When** the operation succeeds
**Then** a success toast is shown
**And** the document disappears from the active document list
**And** the document count updates

### AC-6.8.4: Clear action visible for failed documents
**Given** I am viewing a KB document list as owner or admin
**And** a document has status "failed"
**When** I click the document actions menu
**Then** I see a "Clear" option

### AC-6.8.5: Clear action triggers confirmation
**Given** I click Clear on a failed document
**When** the confirmation dialog appears
**Then** I see message explaining document will be permanently removed
**And** I can confirm or cancel the action

### AC-6.8.6: Clear success updates UI
**Given** I confirm clearing a failed document
**When** the operation succeeds
**Then** a success toast is shown
**And** the document disappears from the document list
**And** the document count updates

### AC-6.8.7: Actions hidden for non-owners/non-admins
**Given** I am a regular user (not owner or admin)
**When** I view the document actions menu
**Then** I do not see Archive or Clear options

### AC-6.8.8: Cancel Processing visible for pending/processing documents
**Given** a document has status "pending" or "processing"
**When** I view the document actions menu
**Then** I see a "Cancel Processing" option

### AC-6.8.9: Cancel Processing moves document to failed status
**Given** I click Cancel Processing on a pending/processing document
**When** the operation succeeds
**Then** the document status changes to "failed"
**And** a toast notification confirms cancellation
**And** I can now retry or delete the document

### AC-6.8.10: Delete disabled for pending/processing documents
**Given** a document has status "pending" or "processing"
**When** I view the document actions menu
**Then** the Delete option is disabled
**And** Cancel Processing is the recommended action

## Technical Notes

### Files to Modify/Create
```
frontend/src/components/documents/document-actions-menu.tsx  (modify)
frontend/src/components/documents/archive-confirmation-modal.tsx  (new)
frontend/src/components/documents/clear-confirmation-modal.tsx  (new)
frontend/src/hooks/useDocumentLifecycle.ts  (new)
```

### useDocumentLifecycle Hook
```typescript
export function useDocumentLifecycle(kbId: string) {
  const queryClient = useQueryClient();

  const archiveDocument = useMutation({
    mutationFn: (docId: string) =>
      fetch(`/api/v1/knowledge-bases/${kbId}/documents/${docId}/archive`, {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries(['documents', kbId]);
      toast.success('Document archived');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to archive document');
    },
  });

  const clearDocument = useMutation({
    mutationFn: (docId: string) =>
      fetch(`/api/v1/knowledge-bases/${kbId}/documents/${docId}/clear`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries(['documents', kbId]);
      toast.success('Failed document cleared');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to clear document');
    },
  });

  return { archiveDocument, clearDocument };
}
```

### Document Actions Menu Update
```tsx
// Add to existing menu items
{canArchive && (
  <DropdownMenuItem onClick={onArchive}>
    <ArchiveIcon className="mr-2 h-4 w-4" />
    Archive
  </DropdownMenuItem>
)}
{canClear && (
  <DropdownMenuItem onClick={onClear} className="text-destructive">
    <TrashIcon className="mr-2 h-4 w-4" />
    Clear
  </DropdownMenuItem>
)}
{canCancel && (
  <DropdownMenuItem onClick={handleCancel} disabled={isCancelling} className="text-destructive">
    <XCircleIcon className="mr-2 h-4 w-4" />
    {isCancelling ? 'Cancelling...' : 'Cancel Processing'}
  </DropdownMenuItem>
)}
// Delete button disabled for PROCESSING/PENDING
<DropdownMenuItem
  onClick={onDelete}
  disabled={status === 'PROCESSING' || status === 'PENDING'}
  className="text-destructive"
>
  <TrashIcon className="mr-2 h-4 w-4" />
  Delete
</DropdownMenuItem>
```

### Permission & Status Logic
```typescript
const canArchive =
  document.status === 'completed' &&
  (user.is_admin || kb.owner_id === user.id);

const canClear =
  document.status === 'failed' &&
  (user.is_admin || kb.owner_id === user.id);

const canCancel =
  document.status === 'PROCESSING' || document.status === 'PENDING';
```

## Dependencies
- Story 6-1: Archive Document Backend (provides POST /archive endpoint)
- Story 6-4: Clear Failed Document Backend (provides DELETE /clear endpoint)
- Existing Documents Panel Component

## Test Cases

### Component Tests
1. Archive option visible for completed documents when owner
2. Archive option hidden for non-completed documents
3. Archive option hidden for non-owners
4. Clear option visible for failed documents when owner
5. Clear option hidden for non-failed documents
6. Clear option hidden for non-owners
7. Archive confirmation modal displays correctly
8. Clear confirmation modal displays correctly
9. Cancel Processing option visible for PROCESSING documents
10. Cancel Processing option visible for PENDING documents
11. Cancel Processing calls correct API endpoint
12. Delete button disabled for PROCESSING/PENDING documents

### E2E Tests
1. Archive completed document from document list
2. Clear failed document from document list
3. Verify archived document removed from list
4. Verify cleared document removed from list
5. Cancel processing document moves to failed status
6. Cancelled document can be retried
7. Cancel Processing option visible for PROCESSING documents
8. Cancel Processing option visible for PENDING documents
9. Delete disabled for PROCESSING documents
10. Delete disabled for PENDING documents

## Definition of Done
- [x] Document actions menu extended with Archive/Clear/Cancel options
- [x] Permission-based visibility implemented
- [x] Status-based visibility implemented
- [x] Archive confirmation modal implemented
- [x] Clear confirmation modal implemented
- [x] Cancel Processing action implemented (no confirmation needed)
- [x] useDocumentLifecycle hook implemented
- [x] Optimistic UI updates implemented
- [x] Toast notifications implemented
- [x] Component tests passing (12+)
- [x] E2E tests passing (10+)
- [ ] Code review approved

## Implementation Notes (2025-12-10)

**Cancel Processing Feature Added:**
- Backend endpoint: `POST /api/v1/knowledge-bases/{kb_id}/documents/{doc_id}/cancel`
- Service method: `DocumentService.cancel()` in `document_service.py`
- Frontend: Cancel Processing menu item in document-list.tsx dropdown
- Toast notification: "Processing cancelled for '{name}'" with description

**Files Modified:**
- `backend/app/services/document_service.py` - Added `cancel()` method
- `backend/app/schemas/document.py` - Added `CancelResponse` schema
- `backend/app/api/v1/documents.py` - Added `/cancel` endpoint
- `frontend/src/components/documents/document-list.tsx` - Added Cancel menu item
- `frontend/src/lib/utils/document-toast.ts` - Added 'cancel' toast type
- `frontend/src/components/documents/__tests__/document-list-delete.test.tsx` - Added tests

**E2E Tests Added (2025-12-10):**
- `frontend/e2e/tests/documents/document-list-actions.spec.ts` - Added Cancel Processing tests
- `frontend/e2e/fixtures/document-actions.factory.ts` - Added `createPendingDocument`, `createSuccessfulCancelOperation`, `cancelProcessing` route
