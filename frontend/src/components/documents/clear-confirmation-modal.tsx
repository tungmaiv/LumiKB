'use client';

import { Trash2, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ClearConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  documentName: string;
  isLoading: boolean;
}

/**
 * Confirmation modal for clearing a failed document
 * Story 6-8: Document List Archive/Clear Actions UI
 */
export function ClearConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  documentName,
  isLoading,
}: ClearConfirmationModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-destructive">
            <Trash2 className="h-5 w-5" />
            Clear Failed Document
          </DialogTitle>
          <DialogDescription>
            Are you sure you want to clear &quot;{documentName}&quot;?
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              This action is permanent. The failed document will be removed from the system and
              cannot be recovered.
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={isLoading}>
            {isLoading ? 'Clearing...' : 'Clear'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
