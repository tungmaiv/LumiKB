'use client';

import { AlertCircle, RotateCw, Search, FileText } from 'lucide-react';

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

export interface RecoveryOption {
  type: string;
  description: string;
  action: string;
}

interface ErrorRecoveryDialogProps {
  isOpen: boolean;
  onClose: () => void;
  errorMessage: string;
  errorType?: string;
  recoveryOptions?: RecoveryOption[];
  onActionSelect: (action: string) => void;
}

const ACTION_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  retry: RotateCw,
  select_template: FileText,
  search: Search,
};

export function ErrorRecoveryDialog({
  isOpen,
  onClose,
  errorMessage,
  errorType,
  recoveryOptions = [],
  onActionSelect,
}: ErrorRecoveryDialogProps) {
  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent className="sm:max-w-[500px]">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Generation Failed
          </AlertDialogTitle>
          <AlertDialogDescription>
            Something went wrong while generating your draft. Here&apos;s what you can do:
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-4 py-4">
          {/* Recovery options */}
          {recoveryOptions.length > 0 && (
            <div className="space-y-2">
              {recoveryOptions.map((option) => {
                const Icon = ACTION_ICONS[option.action] || RotateCw;
                return (
                  <button
                    key={option.action}
                    onClick={() => {
                      onActionSelect(option.action);
                      onClose();
                    }}
                    className="w-full flex items-start gap-3 rounded-lg border p-3 text-left hover:bg-muted transition-colors"
                  >
                    <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-sm">{option.description}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Error details */}
          <div className="rounded-md bg-muted p-3 text-sm">
            <p className="font-medium mb-1">Error details:</p>
            <p className="text-muted-foreground">{errorMessage}</p>
            {errorType && <p className="text-xs text-muted-foreground mt-1">Type: {errorType}</p>}
          </div>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel>Dismiss</AlertDialogCancel>
          {recoveryOptions.length === 0 && (
            <AlertDialogAction onClick={onClose}>Contact Support</AlertDialogAction>
          )}
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
