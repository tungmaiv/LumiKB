/**
 * StepStatusBadge Component (Story 7-27, AC-7.27.4-5)
 *
 * Color-coded status badges for processing steps:
 * - done: Green badge with checkmark
 * - in_progress: Blue badge with spinner animation
 * - pending: Gray badge
 * - error: Red badge with error icon and tooltip
 */

import { type StepStatus } from '@/types/queue';

interface StepStatusBadgeProps {
  status: StepStatus;
  errorMessage?: string | null;
}

export function StepStatusBadge({ status, errorMessage }: StepStatusBadgeProps) {
  const colorClasses: Record<StepStatus, string> = {
    done: 'bg-green-500',
    in_progress: 'bg-blue-500',
    pending: 'bg-gray-400',
    error: 'bg-red-500',
  };

  return (
    <span
      data-testid="step-status-badge"
      className={`badge ${colorClasses[status]} inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs text-white font-medium`}
      title={status === 'error' && errorMessage ? errorMessage : undefined}
      aria-label={`Status: ${status}`}
    >
      {status === 'in_progress' && (
        <span
          data-testid="spinner"
          className="animate-spin h-3 w-3 border-2 border-white border-t-transparent rounded-full"
          aria-hidden="true"
        />
      )}
      {status === 'error' && (
        <span data-testid="error-icon" aria-hidden="true">
          <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </span>
      )}
      {status}
    </span>
  );
}
