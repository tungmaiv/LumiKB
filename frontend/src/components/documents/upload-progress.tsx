'use client';

import { XIcon, RotateCwIcon, CheckIcon, AlertCircleIcon, FileWarningIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { UploadFile, UploadStatus } from '@/lib/hooks/use-file-upload';

/**
 * Format bytes to human-readable size.
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

interface UploadProgressItemProps {
  file: UploadFile;
  onCancel?: (fileId: string) => void;
  onRetry?: (fileId: string) => void;
}

/**
 * Single upload progress item showing file name, size, progress bar, and status.
 */
function UploadProgressItem({ file, onCancel, onRetry }: UploadProgressItemProps) {
  const statusIcon: Record<UploadStatus, React.ReactNode> = {
    pending: null,
    uploading: null,
    completed: <CheckIcon className="size-4 text-green-500" />,
    failed: <AlertCircleIcon className="size-4 text-destructive" />,
    duplicate: <FileWarningIcon className="size-4 text-amber-500" />,
  };

  const statusText: Record<UploadStatus, string> = {
    pending: 'Waiting...',
    uploading: `${file.progress}%`,
    completed: 'Complete',
    failed: file.error || 'Failed',
    duplicate: 'Duplicate detected',
  };

  return (
    <div
      className={cn(
        'flex items-center gap-3 p-3 rounded-md border',
        file.status === 'completed' &&
          'bg-green-50/50 border-green-200 dark:bg-green-950/20 dark:border-green-900',
        file.status === 'failed' && 'bg-destructive/10 border-destructive/30',
        file.status === 'duplicate' &&
          'bg-amber-50/50 border-amber-200 dark:bg-amber-950/20 dark:border-amber-900'
      )}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="font-medium truncate text-sm">{file.file.name}</span>
          <span className="text-xs text-muted-foreground shrink-0">
            {formatBytes(file.file.size)}
          </span>
        </div>

        {(file.status === 'uploading' || file.status === 'pending') && (
          <Progress value={file.progress} className="h-1.5 mt-2" />
        )}

        {file.status === 'failed' && file.error && (
          <p className="text-xs text-destructive mt-1 truncate" title={file.error}>
            {file.error}
          </p>
        )}
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {statusIcon[file.status]}
        <span
          className={cn(
            'text-xs',
            file.status === 'completed' && 'text-green-600 dark:text-green-400',
            file.status === 'failed' && 'text-destructive',
            file.status === 'duplicate' && 'text-amber-600 dark:text-amber-400',
            (file.status === 'pending' || file.status === 'uploading') && 'text-muted-foreground'
          )}
        >
          {statusText[file.status]}
        </span>

        {file.status === 'pending' && onCancel && (
          <Button
            variant="ghost"
            size="icon"
            className="size-6"
            onClick={() => onCancel(file.id)}
            title="Cancel upload"
          >
            <XIcon className="size-3.5" />
          </Button>
        )}

        {file.status === 'failed' && onRetry && (
          <Button
            variant="outline"
            size="sm"
            className="h-6 px-2 text-xs gap-1"
            onClick={() => onRetry(file.id)}
          >
            <RotateCwIcon className="size-3" />
            Retry
          </Button>
        )}
      </div>
    </div>
  );
}

interface UploadProgressProps {
  /** Files in the upload queue */
  files: UploadFile[];
  /** Cancel a pending upload */
  onCancel?: (fileId: string) => void;
  /** Retry a failed upload */
  onRetry?: (fileId: string) => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * UploadProgress displays a list of files being uploaded with progress bars.
 *
 * Features:
 * - Shows file name, size, and upload percentage for each file
 * - Progress bar for uploads in progress
 * - Cancel button for pending files (not in-progress)
 * - Retry button for failed files
 * - Success/error states per file
 *
 * @example
 * <UploadProgress
 *   files={uploadFiles}
 *   onCancel={(fileId) => cancelUpload(fileId)}
 *   onRetry={(fileId) => retryUpload(fileId)}
 * />
 */
export function UploadProgress({ files, onCancel, onRetry, className }: UploadProgressProps) {
  if (files.length === 0) {
    return null;
  }

  return (
    <div className={cn('space-y-2', className)}>
      {files.map((file) => (
        <UploadProgressItem key={file.id} file={file} onCancel={onCancel} onRetry={onRetry} />
      ))}
    </div>
  );
}
