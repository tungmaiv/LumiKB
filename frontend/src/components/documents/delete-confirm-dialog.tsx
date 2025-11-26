'use client';

import { useState } from 'react';
import { AlertTriangleIcon, LoaderIcon } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DeleteConfirmDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog requests close */
  onOpenChange: (open: boolean) => void;
  /** Document name to display */
  documentName: string;
  /** Document ID to delete */
  documentId: string;
  /** Knowledge base ID */
  kbId: string;
  /** Callback when deletion is confirmed and successful */
  onDeleted?: () => void;
  /** Callback when deletion fails */
  onError?: (error: string) => void;
}

/**
 * Confirmation dialog for document deletion.
 *
 * Displays a confirmation prompt before permanently deleting a document.
 * Handles the API call internally and reports success/failure via callbacks.
 *
 * @example
 * <DeleteConfirmDialog
 *   open={showDeleteDialog}
 *   onOpenChange={setShowDeleteDialog}
 *   documentName="Report.pdf"
 *   documentId="doc-123"
 *   kbId="kb-456"
 *   onDeleted={() => refetchDocuments()}
 *   onError={(err) => console.error(err)}
 * />
 */
export function DeleteConfirmDialog({
  open,
  onOpenChange,
  documentName,
  documentId,
  kbId,
  onDeleted,
  onError,
}: DeleteConfirmDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}`,
        {
          method: 'DELETE',
          credentials: 'include',
        }
      );

      if (response.status === 204) {
        // Success - close dialog and notify parent
        onOpenChange(false);
        onDeleted?.();
        return;
      }

      // Handle error responses
      if (response.status === 400) {
        const data = await response.json();
        const errorCode = data?.detail?.error?.code;
        const errorMessage = data?.detail?.error?.message;

        if (errorCode === 'PROCESSING_IN_PROGRESS') {
          onError?.('Cannot delete while document is processing. Please wait.');
        } else if (errorCode === 'ALREADY_DELETED') {
          onError?.('Document has already been deleted.');
        } else {
          onError?.(errorMessage || 'Failed to delete document.');
        }
        return;
      }

      if (response.status === 404) {
        onError?.('Document not found.');
        return;
      }

      // Unexpected error
      onError?.('An unexpected error occurred.');
    } catch (err) {
      console.error('Delete document error:', err);
      onError?.('Network error. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCancel = () => {
    if (!isDeleting) {
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={isDeleting ? undefined : onOpenChange}>
      <DialogContent showCloseButton={!isDeleting}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangleIcon className="size-5 text-destructive" />
            Delete Document
          </DialogTitle>
          <DialogDescription>
            Are you sure you want to delete{' '}
            <span className="font-medium text-foreground">&quot;{documentName}&quot;</span>? This
            action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <div className="text-sm text-muted-foreground bg-muted/50 rounded-md p-3 border">
          <p>Deleting this document will:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Remove it from the Knowledge Base</li>
            <li>Delete all indexed chunks from search</li>
            <li>Delete the uploaded file</li>
          </ul>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel} disabled={isDeleting}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>
            {isDeleting ? (
              <>
                <LoaderIcon className="size-4 mr-2 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete Document'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
