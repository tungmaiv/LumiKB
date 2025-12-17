'use client';

import { InfoIcon, Loader2Icon } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';

export interface DuplicateInfo {
  exists: boolean;
  document_id?: string | null;
  uploaded_at?: string | null;
  file_size?: number | null;
  /** Status of the existing document: completed or archived */
  existing_status?: 'completed' | 'archived' | null;
}

interface DuplicateDialogProps {
  /** Whether the dialog is open */
  isOpen: boolean;
  /** Callback when dialog is closed without action */
  onCancel: () => void;
  /** Callback when user chooses to replace */
  onReplace: () => void;
  /** Callback when user chooses to skip */
  onSkip: () => void;
  /** Filename of the duplicate */
  filename: string;
  /** Information about the existing document */
  duplicateInfo: DuplicateInfo | null;
  /** Whether replace operation is in progress */
  isReplacing?: boolean;
  /** Error message from replace operation */
  error?: string | null;
}

/**
 * DuplicateDialog prompts user when a file with the same name already exists.
 *
 * Offers options to:
 * - Replace: Re-upload and replace existing document
 * - Skip: Don't upload this file
 *
 * @example
 * <DuplicateDialog
 *   isOpen={showDuplicateDialog}
 *   onCancel={() => setShowDuplicateDialog(false)}
 *   onReplace={handleReplace}
 *   onSkip={handleSkip}
 *   filename="report.pdf"
 *   duplicateInfo={{ exists: true, uploaded_at: '2024-01-01' }}
 * />
 */
export function DuplicateDialog({
  isOpen,
  onCancel,
  onReplace,
  onSkip,
  filename,
  duplicateInfo,
  isReplacing = false,
  error = null,
}: DuplicateDialogProps) {
  const uploadedAgo = duplicateInfo?.uploaded_at
    ? formatDistanceToNow(new Date(duplicateInfo.uploaded_at), { addSuffix: true })
    : null;

  const isArchived = duplicateInfo?.existing_status === 'archived';

  const formatFileSize = (bytes?: number | null): string => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <AlertDialog
      open={isOpen}
      onOpenChange={(open: boolean) => !open && !isReplacing && onCancel()}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Document Already Exists</AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-3">
              <p>
                A document named <span className="font-medium">{filename}</span> already exists in
                this knowledge base.
              </p>

              {/* Status badge */}
              <div className="rounded-md bg-muted p-3">
                <p className="text-sm flex items-center gap-2">
                  Status:{' '}
                  <Badge variant={isArchived ? 'secondary' : 'default'}>
                    {duplicateInfo?.existing_status || 'completed'}
                  </Badge>
                </p>
                {uploadedAgo && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Uploaded {uploadedAgo}
                    {duplicateInfo?.file_size && ` (${formatFileSize(duplicateInfo.file_size)})`}
                  </p>
                )}
              </div>

              {/* AC-6.9.7: Archived document restore note */}
              {isArchived && (
                <Alert>
                  <InfoIcon className="h-4 w-4" />
                  <AlertDescription>
                    Replacing will restore this document to active status.
                  </AlertDescription>
                </Alert>
              )}

              {/* Error message */}
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <p>Would you like to replace the existing document or cancel the upload?</p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onSkip} disabled={isReplacing}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction onClick={onReplace} disabled={isReplacing}>
            {isReplacing ? (
              <>
                <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                Replacing...
              </>
            ) : (
              'Replace Existing'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
