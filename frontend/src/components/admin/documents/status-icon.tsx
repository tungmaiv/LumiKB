/**
 * Status Icon Component
 *
 * Story 9-10: Document Timeline UI
 * AC3: Status icons (pending=gray, in-progress=blue spinner, completed=green, failed=red)
 */
import { Circle, CheckCircle, XCircle, Loader2 } from 'lucide-react';

export type StepStatus = 'pending' | 'started' | 'in_progress' | 'completed' | 'failed';

interface StatusIconProps {
  status: StepStatus | string;
  className?: string;
}

export function StatusIcon({ status, className }: StatusIconProps) {
  switch (status) {
    case 'completed':
      return (
        <CheckCircle
          className={`h-5 w-5 text-green-500 ${className ?? ''}`}
          aria-label="Completed"
          data-testid="status-icon-completed"
        />
      );
    case 'failed':
      return (
        <XCircle
          className={`h-5 w-5 text-red-500 ${className ?? ''}`}
          aria-label="Failed"
          data-testid="status-icon-failed"
        />
      );
    case 'started':
    case 'in_progress':
      return (
        <Loader2
          className={`h-5 w-5 text-blue-500 animate-spin ${className ?? ''}`}
          aria-label="In Progress"
          data-testid="status-icon-in-progress"
        />
      );
    case 'pending':
    default:
      return (
        <Circle
          className={`h-5 w-5 text-gray-400 ${className ?? ''}`}
          aria-label="Pending"
          data-testid="status-icon-pending"
        />
      );
  }
}
