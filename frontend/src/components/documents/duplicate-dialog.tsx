'use client';

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
import { formatDistanceToNow } from 'date-fns';

export interface DuplicateInfo {
  exists: boolean;
  document_id?: string | null;
  uploaded_at?: string | null;
  file_size?: number | null;
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
}: DuplicateDialogProps) {
  const uploadedAgo = duplicateInfo?.uploaded_at
    ? formatDistanceToNow(new Date(duplicateInfo.uploaded_at), { addSuffix: true })
    : null;

  const formatFileSize = (bytes?: number | null): string => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={(open: boolean) => !open && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>File Already Exists</AlertDialogTitle>
          <AlertDialogDescription className="space-y-2">
            <p>
              A document named <span className="font-medium">{filename}</span> already exists in
              this knowledge base.
            </p>
            {uploadedAgo && (
              <p className="text-sm text-muted-foreground">
                Uploaded {uploadedAgo}
                {duplicateInfo?.file_size && ` (${formatFileSize(duplicateInfo.file_size)})`}
              </p>
            )}
            <p className="mt-4">
              Would you like to replace the existing document or skip this file?
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onSkip}>Skip</AlertDialogCancel>
          <AlertDialogAction onClick={onReplace}>Replace</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
