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
import { ArchiveRestore, Loader2 } from 'lucide-react';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';

interface RestoreKBDialogProps {
  kb: KnowledgeBase;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isLoading?: boolean;
}

/**
 * Confirmation dialog for restoring an archived Knowledge Base.
 * Story 7-26: AC-7.26.6 - Restore confirmation with document count.
 */
export function RestoreKBDialog({
  kb,
  open,
  onOpenChange,
  onConfirm,
  isLoading = false,
}: RestoreKBDialogProps) {
  const documentCount = kb.document_count;
  const hasDocuments = documentCount > 0;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <ArchiveRestore className="h-5 w-5 text-green-500" />
            Restore Knowledge Base
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-2 text-sm text-muted-foreground">
              <span className="block">
                Are you sure you want to restore <strong>&quot;{kb.name}&quot;</strong>?
              </span>
              {hasDocuments && (
                <span className="block text-green-600 dark:text-green-400">
                  This will restore {documentCount} document{documentCount === 1 ? '' : 's'}.
                </span>
              )}
              <span className="block">
                The Knowledge Base will be returned to the active list and become searchable again.
              </span>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLoading}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              onConfirm();
            }}
            disabled={isLoading}
            className="bg-green-600 text-white hover:bg-green-700"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Restoring...
              </>
            ) : (
              <>
                <ArchiveRestore className="mr-2 h-4 w-4" />
                Restore
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
