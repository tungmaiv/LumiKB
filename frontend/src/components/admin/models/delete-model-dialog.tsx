/**
 * Dialog for confirming model deletion
 * Story 7-9: LLM Model Registry (AC-7.9.6)
 */

'use client';

import { AlertTriangle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { LLMModelSummary } from '@/types/llm-model';
import { PROVIDER_INFO, MODEL_TYPE_INFO } from '@/types/llm-model';

interface DeleteModelDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  model: LLMModelSummary | null;
  onConfirm: () => void;
  isDeleting: boolean;
}

export function DeleteModelDialog({
  open,
  onOpenChange,
  model,
  onConfirm,
  isDeleting,
}: DeleteModelDialogProps) {
  if (!model) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            Delete Model
          </DialogTitle>
          <DialogDescription>
            Are you sure you want to delete this model? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <div className="bg-muted p-4 rounded-lg space-y-2">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Name</span>
            <span className="font-medium">{model.name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Type</span>
            <span>{MODEL_TYPE_INFO[model.type]?.name || model.type}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Provider</span>
            <span>
              {PROVIDER_INFO[model.provider]?.icon}{' '}
              {PROVIDER_INFO[model.provider]?.name || model.provider}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Model ID</span>
            <code className="text-xs bg-background px-1 py-0.5 rounded">{model.model_id}</code>
          </div>
        </div>

        {model.is_default && (
          <div className="bg-amber-50 border border-amber-200 p-3 rounded-lg text-sm text-amber-800">
            This model is set as the default {model.type} model. You cannot delete it until you set
            another model as the default.
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isDeleting}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={isDeleting || model.is_default}
          >
            {isDeleting ? 'Deleting...' : 'Delete Model'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
