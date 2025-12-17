'use client';

import { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';

interface VerificationDialogProps {
  open: boolean;
  citationCount: number;
  documentCount: number;
  draftId: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function VerificationDialog({
  open,
  citationCount,
  documentCount,
  draftId,
  onConfirm,
  onCancel,
}: VerificationDialogProps) {
  // Initialize state from session storage
  // draftId is stable for each dialog instance, so we don't need useEffect
  const [verified, setVerified] = useState(() => {
    if (typeof window === 'undefined') return false;
    const storageKey = `draft_export_verified_${draftId}`;
    return sessionStorage.getItem(storageKey) === 'true';
  });

  const handleConfirm = () => {
    // Save verification state to session storage
    const storageKey = `draft_export_verified_${draftId}`;
    if (verified) {
      sessionStorage.setItem(storageKey, 'true');
    }
    onConfirm();
  };

  return (
    <Dialog open={open} onOpenChange={onCancel}>
      <DialogContent className="sm:max-w-[500px]" data-testid="verification-dialog">
        <DialogHeader>
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <DialogTitle>Verify Your Sources</DialogTitle>
          </div>
          <DialogDescription data-testid="verification-message">
            Have you verified the sources before exporting?
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <p className="text-sm text-muted-foreground">Before exporting, we recommend:</p>
          <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground">
            <li>Review all [{citationCount}] citations in the draft</li>
            <li>Check cited documents for accuracy</li>
            <li>Verify claims match source content</li>
          </ul>

          <div className="rounded-lg border p-4 bg-muted/50">
            <p className="text-sm font-medium">
              Sources:{' '}
              <span data-testid="document-count">
                {documentCount} {documentCount === 1 ? 'document' : 'documents'}
              </span>
              ,{' '}
              <span data-testid="citation-count">
                {citationCount} {citationCount === 1 ? 'citation' : 'citations'}
              </span>
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="verified"
              checked={verified}
              onCheckedChange={(checked) => setVerified(checked as boolean)}
              data-testid="verification-checkbox"
            />
            <Label
              htmlFor="verified"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
            >
              I have verified the sources
            </Label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel} data-testid="go-back-button">
            Go Back
          </Button>
          <Button onClick={handleConfirm} data-testid="export-anyway-button">
            Export Anyway
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
