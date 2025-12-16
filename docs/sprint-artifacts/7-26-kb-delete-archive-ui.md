# Story 7-26: KB Delete/Archive UI

| Field | Value |
|-------|-------|
| **Story ID** | 7-26 |
| **Epic** | Epic 7 - Infrastructure & DevOps |
| **Priority** | HIGH |
| **Effort** | 3 story points |
| **Added** | 2025-12-10 (Correct-Course: KB Delete/Archive Feature) |
| **Status** | IN PROGRESS |
| **Context** | [7-26-kb-delete-archive-ui.context.xml](7-26-kb-delete-archive-ui.context.xml) |

## User Story

**As an** administrator
**I want** UI controls for KB delete, archive, and restore
**So that** I can manage KB lifecycle without API calls

## Background

This story implements the frontend UI for KB lifecycle management, building on Stories 7.24 (Archive) and 7.25 (Restore). The UI provides:

1. Archive/Delete options in KB settings menu
2. Delete only enabled for empty KBs
3. Confirmation dialogs with appropriate warnings
4. Archived KB filter in KB list
5. Restore action for archived KBs

## Acceptance Criteria

### AC-7.26.1: KB actions menu
- **Given** I have ADMIN permission on an active KB
- **When** I view KB settings/actions menu
- **Then** I see "Archive KB" option
- **And** I see "Delete KB" option (enabled only if document_count = 0)

### AC-7.26.2: Delete disabled for non-empty KB
- **Given** KB has documents
- **When** I hover over disabled "Delete KB" button
- **Then** tooltip shows: "Remove all documents before deleting"

### AC-7.26.3: Archive confirmation
- **Given** I click "Archive KB"
- **When** confirmation dialog appears
- **Then** it warns: "This will archive X documents. Archived KBs are hidden from search."
- **And** I can confirm or cancel

### AC-7.26.4: Delete confirmation
- **Given** I click "Delete KB" on empty KB
- **When** confirmation dialog appears
- **Then** it warns: "This will permanently delete the KB. This cannot be undone."
- **And** I must type KB name to confirm

### AC-7.26.5: Archived KB list filter
- **Given** I view KB list
- **When** I toggle "Show Archived" filter
- **Then** archived KBs appear with visual indicator (grayed out, archive icon)

### AC-7.26.6: Restore from list
- **Given** I view archived KBs list
- **When** I click "Restore" on an archived KB
- **Then** confirmation dialog appears
- **And** KB is restored on confirmation

### AC-7.26.7: Delete empty KB only
- **Given** I have ADMIN permission on an empty KB (0 documents)
- **When** I call DELETE /api/v1/knowledge-bases/{id}
- **Then** the KB is permanently deleted from database
- **And** the Qdrant collection is deleted
- **And** the action is logged to audit.events

### AC-7.26.8: Delete non-empty KB blocked
- **Given** I have ADMIN permission on a KB with 1+ documents
- **When** I call DELETE /api/v1/knowledge-bases/{id}
- **Then** I receive 400 Bad Request
- **And** error message states: "Cannot delete KB with documents. Archive or remove documents first."

## Tasks

### Task 1: Backend - Update DELETE Endpoint
- [ ] 1.1 Modify DELETE /api/v1/knowledge-bases/{id} to check document count
- [ ] 1.2 Return 400 if document_count > 0
- [ ] 1.3 Perform hard delete if empty (remove from DB)
- [ ] 1.4 Delete Qdrant collection
- [ ] 1.5 Audit log: kb.deleted

### Task 2: KB Actions Menu Component
- [x] 2.1 Create `KBActionsMenu` component in KB settings
- [x] 2.2 Show "Archive KB" option for active KBs
- [x] 2.3 Show "Delete KB" option (disabled if has documents)
- [x] 2.4 Add tooltip on disabled delete: "Remove all documents before deleting"
- [x] 2.5 Show "Restore" option for archived KBs
- [x] 2.6 **Added**: KB Actions Menu integrated into dashboard header (after Settings icon)

### Task 3: Archive Confirmation Dialog
- [ ] 3.1 Create `ArchiveKBDialog` component
- [ ] 3.2 Display document count in warning
- [ ] 3.3 Explain consequences: "Archived KBs are hidden from search"
- [ ] 3.4 Confirm/Cancel buttons
- [ ] 3.5 Call POST /api/v1/knowledge-bases/{id}/archive on confirm

### Task 4: Delete Confirmation Dialog
- [ ] 4.1 Create `DeleteKBDialog` component
- [ ] 4.2 Require typing KB name to confirm
- [ ] 4.3 Display permanent deletion warning
- [ ] 4.4 Disable confirm until name matches
- [ ] 4.5 Call DELETE /api/v1/knowledge-bases/{id} on confirm

### Task 5: Restore Confirmation Dialog
- [ ] 5.1 Create `RestoreKBDialog` component
- [ ] 5.2 Display document count being restored
- [ ] 5.3 Confirm/Cancel buttons
- [ ] 5.4 Call POST /api/v1/knowledge-bases/{id}/restore on confirm

### Task 6: KB List Filter - Show Archived
- [x] 6.1 Add "Show Archived" toggle to KB list header
- [x] 6.2 Pass include_archived=true query param when toggled
- [x] 6.3 Style archived KBs differently (grayed out, archive icon)
- [x] 6.4 Show "Archived" badge on archived KBs

### Task 7: Success/Error Handling
- [ ] 7.1 Show success toast on archive/restore/delete
- [ ] 7.2 Show error toast on failure
- [ ] 7.3 Refresh KB list after action
- [ ] 7.4 Close dialogs on success

### Task 8: Testing
- [ ] 8.1 Unit tests for dialog components
- [ ] 8.2 Unit tests for KB actions menu
- [ ] 8.3 Integration tests for archive flow
- [ ] 8.4 Integration tests for delete flow
- [ ] 8.5 E2E tests for complete user flows

## Dev Notes

### Key Files to Create/Modify

**Frontend Components:**
- `frontend/src/components/kb/kb-actions-menu.tsx` - Actions dropdown
- `frontend/src/components/kb/dialogs/archive-kb-dialog.tsx` - Archive confirmation
- `frontend/src/components/kb/dialogs/delete-kb-dialog.tsx` - Delete confirmation
- `frontend/src/components/kb/dialogs/restore-kb-dialog.tsx` - Restore confirmation
- `frontend/src/components/kb/kb-sidebar.tsx` - Add archived filter toggle
- `frontend/src/components/kb/kb-list-item.tsx` - Archived KB styling

**Backend:**
- `backend/app/api/v1/knowledge_bases.py` - Update DELETE endpoint

### Component Structure

```tsx
// KBActionsMenu
export function KBActionsMenu({ kb, onArchive, onDelete, onRestore }: Props) {
  const isArchived = kb.archived_at !== null;
  const hasDocuments = kb.document_count > 0;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <MoreVertical className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        {!isArchived && (
          <>
            <DropdownMenuItem onClick={onArchive}>
              <Archive className="mr-2 h-4 w-4" />
              Archive KB
            </DropdownMenuItem>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span>
                    <DropdownMenuItem
                      onClick={onDelete}
                      disabled={hasDocuments}
                    >
                      <Trash className="mr-2 h-4 w-4" />
                      Delete KB
                    </DropdownMenuItem>
                  </span>
                </TooltipTrigger>
                {hasDocuments && (
                  <TooltipContent>
                    Remove all documents before deleting
                  </TooltipContent>
                )}
              </Tooltip>
            </TooltipProvider>
          </>
        )}
        {isArchived && (
          <DropdownMenuItem onClick={onRestore}>
            <ArchiveRestore className="mr-2 h-4 w-4" />
            Restore KB
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

### Delete Confirmation with Name Input

```tsx
// DeleteKBDialog
export function DeleteKBDialog({ kb, open, onOpenChange, onConfirm }: Props) {
  const [confirmName, setConfirmName] = useState("");
  const canDelete = confirmName === kb.name;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Knowledge Base</AlertDialogTitle>
          <AlertDialogDescription>
            This will permanently delete <strong>{kb.name}</strong>.
            This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="py-4">
          <Label>Type "{kb.name}" to confirm:</Label>
          <Input
            value={confirmName}
            onChange={(e) => setConfirmName(e.target.value)}
            placeholder={kb.name}
          />
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={!canDelete}
            className="bg-destructive text-destructive-foreground"
          >
            Delete Permanently
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

### Archived KB Styling

```tsx
// In KBListItem or KBSelectorItem
<div className={cn(
  "flex items-center gap-2 p-2 rounded-md",
  kb.archived_at && "opacity-60 bg-muted"
)}>
  {kb.archived_at && (
    <Badge variant="secondary" className="text-xs">
      <Archive className="h-3 w-3 mr-1" />
      Archived
    </Badge>
  )}
  <span>{kb.name}</span>
</div>
```

### API Hooks

```typescript
// useKBActions hook
export function useKBActions() {
  const queryClient = useQueryClient();

  const archiveMutation = useMutation({
    mutationFn: (kbId: string) =>
      api.post(`/knowledge-bases/${kbId}/archive`),
    onSuccess: () => {
      queryClient.invalidateQueries(['knowledge-bases']);
      toast.success('Knowledge Base archived');
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (kbId: string) =>
      api.post(`/knowledge-bases/${kbId}/restore`),
    onSuccess: () => {
      queryClient.invalidateQueries(['knowledge-bases']);
      toast.success('Knowledge Base restored');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (kbId: string) =>
      api.delete(`/knowledge-bases/${kbId}`),
    onSuccess: () => {
      queryClient.invalidateQueries(['knowledge-bases']);
      toast.success('Knowledge Base deleted');
    },
  });

  return { archiveMutation, restoreMutation, deleteMutation };
}
```

### Dependencies
- Story 7.24 (KB Archive Backend)
- Story 7.25 (KB Restore Backend)
- Story 2.3 (KB List and Selection Frontend)

## Testing Strategy

### Unit Tests
- Test KBActionsMenu renders correct options
- Test delete button disabled when has documents
- Test confirmation dialogs render correctly
- Test name confirmation validation in delete dialog
- Test archived KB styling

### Integration Tests
- Test archive flow end-to-end
- Test restore flow end-to-end
- Test delete flow for empty KB
- Test delete blocked for non-empty KB
- Test archived filter toggle

### E2E Tests
```typescript
test.describe('KB Lifecycle Management', () => {
  test('archive KB with documents', async ({ page }) => {
    // Navigate to KB with documents
    // Click Archive in actions menu
    // Verify confirmation dialog shows document count
    // Confirm archive
    // Verify KB is now in archived list
  });

  test('delete empty KB', async ({ page }) => {
    // Create empty KB
    // Click Delete in actions menu
    // Type KB name to confirm
    // Verify KB is removed from list
  });

  test('cannot delete KB with documents', async ({ page }) => {
    // Navigate to KB with documents
    // Verify Delete button is disabled
    // Verify tooltip shows reason
  });
});
```

## Implementation Notes (2025-12-10)

### KB Actions Menu Placement
The `KBActionsMenu` component has been integrated into the KB dashboard header, appearing after the Settings (gear) icon when the user has ADMIN permission on the active KB. This provides easy access to Archive/Delete/Restore actions without navigating to a separate settings page.

**Location**: `frontend/src/app/(protected)/dashboard/page.tsx`
```tsx
{isAdmin && (
  <>
    <Button variant="ghost" size="icon" aria-label="Edit tags" onClick={() => setIsEditTagsModalOpen(true)}>
      <Pencil className="h-3 w-3" />
    </Button>
    <Button variant="ghost" size="icon" aria-label="KB Settings" onClick={() => setIsSettingsModalOpen(true)}>
      <Settings className="h-3 w-3" />
    </Button>
    {/* KB Actions Menu (archive/delete) */}
    <KBActionsMenu
      kb={activeKb}
      onSettingsClick={() => setIsSettingsModalOpen(true)}
    />
  </>
)}
```

### Tags Overflow Display
KB dashboard header now displays a maximum of 3 tags, with additional tags shown in a "+X more" badge that displays a tooltip on hover with the remaining tags.

**Implementation**:
```tsx
{activeKb.tags.slice(0, 3).map((tag) => (
  <span key={tag} className="inline-block rounded-md bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
    {tag}
  </span>
))}
{activeKb.tags.length > 3 && (
  <Tooltip>
    <TooltipTrigger asChild>
      <span className="inline-block rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground cursor-default">
        +{activeKb.tags.length - 3} more
      </span>
    </TooltipTrigger>
    <TooltipContent>
      <p>{activeKb.tags.slice(3).join(', ')}</p>
    </TooltipContent>
  </Tooltip>
)}
```

### KB Sidebar Actions Menu Visibility
The KB sidebar actions menu (ellipsis/three-dot) now has improved visibility:
- Changed from `opacity-0 group-hover:opacity-100` to `opacity-50 group-hover:opacity-100`
- Always partially visible, becomes fully visible on hover

**Location**: `frontend/src/components/kb/kb-selector-item.tsx`

## Definition of Done
- [ ] All ACs implemented and passing
- [ ] Unit tests for all new components
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] No TypeScript errors
- [ ] No ESLint errors
- [ ] Code reviewed
- [ ] UI matches design system

## References
- [Sprint Change Proposal](sprint-change-proposal-kb-archive-delete-2025-12-10.md)
- [Story 7-24: KB Archive Backend](7-24-kb-archive-backend.md)
- [Story 7-25: KB Restore Backend](7-25-kb-restore-backend.md)
- [shadcn/ui Dialog](https://ui.shadcn.com/docs/components/dialog)
- [shadcn/ui Dropdown Menu](https://ui.shadcn.com/docs/components/dropdown-menu)
