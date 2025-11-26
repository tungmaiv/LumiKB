'use client';

import { CheckCircle2Icon, ClockIcon, Loader2Icon, XCircleIcon } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

/**
 * Document processing status values.
 */
export type DocumentStatus = 'PENDING' | 'PROCESSING' | 'READY' | 'FAILED';

interface DocumentStatusBadgeProps {
  /** Current status of the document */
  status: DocumentStatus;
  /** Error message for FAILED status (shown in tooltip) */
  errorMessage?: string | null;
  /** Chunk count for READY status */
  chunkCount?: number;
  /** Version number - if > 1, shows "Updating" instead of "Processing" */
  versionNumber?: number;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Status badge configuration for each document status.
 */
const STATUS_CONFIG = {
  PENDING: {
    icon: ClockIcon,
    label: 'Queued for processing',
    color: 'text-muted-foreground',
    bgColor: 'bg-muted',
  },
  PROCESSING: {
    icon: Loader2Icon,
    label: 'Processing...',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 dark:bg-blue-950',
    animate: true,
  },
  UPDATING: {
    icon: Loader2Icon,
    label: 'Updating...',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 dark:bg-amber-950',
    animate: true,
  },
  READY: {
    icon: CheckCircle2Icon,
    label: 'Ready',
    color: 'text-green-600',
    bgColor: 'bg-green-50 dark:bg-green-950',
  },
  FAILED: {
    icon: XCircleIcon,
    label: 'Failed',
    color: 'text-red-600',
    bgColor: 'bg-red-50 dark:bg-red-950',
  },
} as const;

/**
 * DocumentStatusBadge displays the processing status of a document.
 *
 * - PENDING: Gray clock icon, "Queued for processing"
 * - PROCESSING: Blue animated spinner, "Processing..."
 * - READY: Green checkmark, "Ready" with optional chunk count
 * - FAILED: Red error icon with tooltip showing error message
 *
 * @example
 * <DocumentStatusBadge status="READY" chunkCount={47} />
 * <DocumentStatusBadge status="FAILED" errorMessage="Parse error: Invalid PDF" />
 */
export function DocumentStatusBadge({
  status,
  errorMessage,
  chunkCount,
  versionNumber,
  className,
}: DocumentStatusBadgeProps) {
  // Use UPDATING config for PROCESSING status when version > 1
  const effectiveStatus =
    status === 'PROCESSING' && versionNumber !== undefined && versionNumber > 1
      ? 'UPDATING'
      : status;
  const config = STATUS_CONFIG[effectiveStatus];
  const Icon = config.icon;

  const badgeContent = (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium',
        config.bgColor,
        config.color,
        className
      )}
    >
      <Icon className={cn('size-3.5', 'animate' in config && config.animate && 'animate-spin')} />
      <span>{config.label}</span>
      {status === 'READY' && chunkCount !== undefined && chunkCount > 0 && (
        <span className="text-muted-foreground">({chunkCount} chunks)</span>
      )}
    </div>
  );

  // Show tooltip with error message for FAILED status
  if (status === 'FAILED' && errorMessage) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>{badgeContent}</TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <p className="text-sm">{errorMessage}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return badgeContent;
}
