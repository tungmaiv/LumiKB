'use client';

import { useState, useEffect } from 'react';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Trash2, Loader2, AlertTriangle } from 'lucide-react';
import type { KnowledgeBase } from '@/lib/api/knowledge-bases';

interface DeleteKBDialogProps {
  kb: KnowledgeBase;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isLoading?: boolean;
}

/**
 * Confirmation dialog for permanently deleting a Knowledge Base.
 * Story 7-26: AC-7.26.4 - Delete confirmation with name input requirement.
 */
export function DeleteKBDialog({
  kb,
  open,
  onOpenChange,
  onConfirm,
  isLoading = false,
}: DeleteKBDialogProps) {
  const [confirmName, setConfirmName] = useState('');

  // Reset input when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setConfirmName('');
    }
  }, [open]);

  const canDelete = confirmName === kb.name;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            Delete Knowledge Base
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-3 text-sm text-muted-foreground">
              <span className="block">
                This will <strong>permanently delete</strong> the Knowledge Base{' '}
                <strong>&quot;{kb.name}&quot;</strong>.
              </span>
              <span className="block text-destructive font-medium">
                This action cannot be undone. All associated data will be lost.
              </span>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="py-4 space-y-2">
          <Label htmlFor="confirm-name" className="text-sm">
            Type <span className="font-mono font-semibold">{kb.name}</span> to confirm:
          </Label>
          <Input
            id="confirm-name"
            value={confirmName}
            onChange={(e) => setConfirmName(e.target.value)}
            placeholder={kb.name}
            disabled={isLoading}
            autoComplete="off"
          />
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLoading}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              if (canDelete) {
                onConfirm();
              }
            }}
            disabled={!canDelete || isLoading}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="mr-2 h-4 w-4" />
                Delete Permanently
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
