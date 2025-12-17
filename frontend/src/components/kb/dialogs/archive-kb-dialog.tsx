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
import { Archive, Loader2 } from 'lucide-react';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';

interface ArchiveKBDialogProps {
  kb: KnowledgeBase;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isLoading?: boolean;
}

/**
 * Confirmation dialog for archiving a Knowledge Base.
 * Story 7-26: AC-7.26.3 - Archive confirmation with document count warning.
 */
export function ArchiveKBDialog({
  kb,
  open,
  onOpenChange,
  onConfirm,
  isLoading = false,
}: ArchiveKBDialogProps) {
  const documentCount = kb.document_count;
  const hasDocuments = documentCount > 0;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <Archive className="h-5 w-5 text-amber-500" />
            Archive Knowledge Base
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-2 text-sm text-muted-foreground">
              <span className="block">
                Are you sure you want to archive <strong>&quot;{kb.name}&quot;</strong>?
              </span>
              {hasDocuments && (
                <span className="block text-amber-600 dark:text-amber-400">
                  This will archive {documentCount} document{documentCount === 1 ? '' : 's'}.
                </span>
              )}
              <span className="block">
                Archived Knowledge Bases are hidden from search results and the main list. You can
                restore them later from the archive.
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
            className="bg-amber-600 text-white hover:bg-amber-700"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Archiving...
              </>
            ) : (
              <>
                <Archive className="mr-2 h-4 w-4" />
                Archive
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
