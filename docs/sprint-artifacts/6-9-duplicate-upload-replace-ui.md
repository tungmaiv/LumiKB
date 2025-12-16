# Story 6-9: Duplicate Upload & Replace UI

## Story Information
- **Epic:** 6 - Document Lifecycle Management
- **Story ID:** 6-9
- **Story Points:** 3
- **Priority:** MEDIUM
- **Status:** ready-for-dev

## User Story
**As a** KB owner or admin
**I want** to handle duplicate document uploads with clear options
**So that** I can choose to replace existing documents or cancel the upload

## Context
When uploading a document with a name that already exists in the KB (completed or archived), the user is presented with a modal explaining the conflict. They can choose to replace the existing document (triggering the replace flow) or cancel the upload. Failed documents with the same name are auto-cleared with a notification.

## Acceptance Criteria

### AC-6.9.1: Duplicate detection modal appears on 409
**Given** I upload a document
**And** a document with the same name exists (completed or archived)
**When** the upload returns 409 duplicate error
**Then** a duplicate detection modal appears
**And** it shows the name of the existing document
**And** it shows the status of the existing document (completed/archived)

### AC-6.9.2: Replace option in duplicate modal
**Given** I see the duplicate detection modal
**When** I click "Replace Existing"
**Then** the replace API is called with the new file
**And** on success, the modal closes
**And** a success toast shows "Document replaced and queued for processing"
**And** the document list refreshes

### AC-6.9.3: Cancel option in duplicate modal
**Given** I see the duplicate detection modal
**When** I click "Cancel"
**Then** the modal closes
**And** no upload or replace operation occurs

### AC-6.9.4: Auto-clear notification for failed duplicates
**Given** I upload a document
**And** a failed document with the same name existed
**When** the upload succeeds with auto_cleared_document_id in response
**Then** a toast notification shows "Previous failed upload was automatically cleared"
**And** the new document appears in the list

### AC-6.9.5: Replace shows processing status
**Given** I confirm replacing a document
**When** the replace operation is in progress
**Then** the modal shows a loading state
**And** the Replace button is disabled

### AC-6.9.6: Replace error handling
**Given** I confirm replacing a document
**And** the replace API fails (e.g., document now processing)
**When** the error response is received
**Then** an error message is shown in the modal
**And** I can retry or cancel

### AC-6.9.7: Archived document replace shows restore note
**Given** I see the duplicate detection modal
**And** the existing document is archived
**When** I view the modal content
**Then** I see a note that replacing will restore the document to active status

## Technical Notes

### Files to Modify/Create
```
frontend/src/components/documents/duplicate-document-modal.tsx  (new)
frontend/src/components/documents/document-upload.tsx  (modify)
frontend/src/hooks/useDocumentUpload.ts  (modify)
frontend/src/hooks/useDocumentLifecycle.ts  (modify - add replace)
```

### DuplicateDocumentModal Component
```tsx
interface DuplicateDocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReplace: () => void;
  duplicateInfo: {
    existingDocumentId: string;
    existingStatus: 'completed' | 'archived';
    documentName: string;
  };
  file: File;
  isReplacing: boolean;
  error: string | null;
}

export function DuplicateDocumentModal({
  isOpen,
  onClose,
  onReplace,
  duplicateInfo,
  file,
  isReplacing,
  error,
}: DuplicateDocumentModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Document Already Exists</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <p>
            A document named <strong>{duplicateInfo.documentName}</strong> already
            exists in this knowledge base.
          </p>

          <div className="rounded-md bg-muted p-3">
            <p className="text-sm">
              Status: <Badge>{duplicateInfo.existingStatus}</Badge>
            </p>
          </div>

          {duplicateInfo.existingStatus === 'archived' && (
            <Alert>
              <InfoIcon className="h-4 w-4" />
              <AlertDescription>
                Replacing will restore this document to active status.
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isReplacing}>
            Cancel
          </Button>
          <Button onClick={onReplace} disabled={isReplacing}>
            {isReplacing ? <Spinner /> : 'Replace Existing'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### Upload Hook 409 Handling
```typescript
// In useDocumentUpload.ts
const uploadMutation = useMutation({
  mutationFn: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`/api/v1/knowledge-bases/${kbId}/documents`, {
      method: 'POST',
      body: formData,
    });

    if (response.status === 409) {
      const data = await response.json();
      if (data.error === 'duplicate_document') {
        // Return duplicate info for UI handling
        return {
          isDuplicate: true,
          duplicateInfo: {
            existingDocumentId: data.existing_document_id,
            existingStatus: data.existing_status,
            documentName: file.name,
          },
          file,
        };
      }
    }

    if (!response.ok) {
      throw new Error('Upload failed');
    }

    const result = await response.json();

    // Check for auto-clear notification
    if (result.auto_cleared_document_id) {
      toast.info('Previous failed upload was automatically cleared');
    }

    return result;
  },
});
```

### Replace Mutation
```typescript
// Add to useDocumentLifecycle.ts
const replaceDocument = useMutation({
  mutationFn: async ({ docId, file }: { docId: string; file: File }) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(
      `/api/v1/knowledge-bases/${kbId}/documents/${docId}/replace`,
      {
        method: 'POST',
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Replace failed');
    }

    return response.json();
  },
  onSuccess: () => {
    queryClient.invalidateQueries(['documents', kbId]);
    toast.success('Document replaced and queued for processing');
  },
});
```

## Dependencies
- Story 6-5: Duplicate Detection Backend (provides 409 response with duplicate info)
- Story 6-6: Replace Document Backend (provides POST /replace endpoint)
- Existing Document Upload Component

## Test Cases

### Component Tests
1. DuplicateDocumentModal renders with correct info
2. Replace button triggers onReplace callback
3. Cancel button closes modal
4. Loading state shown during replace
5. Error message displayed on replace failure
6. Archived status shows restore note
7. Auto-clear notification shown on upload success

### E2E Tests
1. Upload duplicate shows modal
2. Replace from duplicate modal succeeds
3. Cancel duplicate upload works
4. Auto-clear failed document on re-upload
5. Replace archived document restores to active

## Definition of Done
- [ ] DuplicateDocumentModal component implemented
- [ ] Upload hook handles 409 duplicate response
- [ ] Replace mutation added to useDocumentLifecycle
- [ ] Auto-clear notification implemented
- [ ] Loading states implemented
- [ ] Error handling implemented
- [ ] Archived document restore note displayed
- [ ] Component tests passing (7+)
- [ ] E2E tests passing (5+)
- [ ] Code review approved
