/**
 * BulkRetryDialog Component (Story 7-27, AC-7.27.6-9)
 *
 * Dialog for bulk retry operations:
 * - Confirmation dialog with count
 * - Loading state during API call
 * - Success/error feedback
 */

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { type BulkRetryResponse } from '@/types/queue';

interface BulkRetryDialogProps {
  open: boolean;
  onClose: () => void;
  selectedDocumentIds: string[];
  retryAll?: boolean;
  onRetrySuccess?: (response: BulkRetryResponse) => void;
  onRetryError?: (error: Error) => void;
  onConfirm?: () => Promise<BulkRetryResponse>;
}

export function BulkRetryDialog({
  open,
  onClose,
  selectedDocumentIds,
  retryAll = false,
  onRetrySuccess,
  onRetryError,
  onConfirm,
}: BulkRetryDialogProps) {
  const [isLoading, setIsLoading] = useState(false);

  const count = retryAll ? 'all failed' : selectedDocumentIds.length;

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      if (onConfirm) {
        const response = await onConfirm();
        onRetrySuccess?.(response);
      } else {
        // Default mock response for testing
        const response: BulkRetryResponse = {
          queued: selectedDocumentIds.length,
          failed: 0,
          errors: [],
        };
        onRetrySuccess?.(response);
      }
      onClose();
    } catch (error) {
      onRetryError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent data-testid="bulk-retry-dialog">
        <DialogHeader>
          <DialogTitle id="bulk-retry-title">Confirm Retry</DialogTitle>
          <DialogDescription data-testid="retry-count-message">
            Retry {typeof count === 'number' ? `${count} failed documents` : count}?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            data-testid="cancel-button"
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            data-testid="confirm-button"
            disabled={isLoading}
          >
            {isLoading ? 'Retrying...' : 'Confirm Retry'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/**
 * BulkRetryButton Component (Story 7-27, AC-7.27.6-7)
 *
 * Button controls for bulk retry operations
 */
interface BulkRetryButtonProps {
  failedCount: number;
  selectedCount: number;
  onRetryAll: () => void;
  onRetrySelected: () => void;
  disabled?: boolean;
}

export function BulkRetryButton({
  failedCount,
  selectedCount,
  onRetryAll,
  onRetrySelected,
  disabled = false,
}: BulkRetryButtonProps) {
  return (
    <div data-testid="bulk-retry-controls" className="flex gap-2">
      {failedCount > 0 && (
        <Button
          variant="outline"
          onClick={onRetryAll}
          disabled={disabled}
          data-testid="retry-all-button"
          className="text-red-600 border-red-200 hover:bg-red-50"
        >
          Retry All Failed ({failedCount})
        </Button>
      )}
      {selectedCount > 0 && (
        <Button
          variant="outline"
          onClick={onRetrySelected}
          disabled={disabled}
          data-testid="retry-selected-button"
        >
          Retry Selected ({selectedCount})
        </Button>
      )}
    </div>
  );
}
