/**
 * ReconnectionIndicator Component - Epic 7, Story 7-22
 * Displays reconnection status during SSE stream interruptions.
 *
 * Features:
 * - "Reconnecting..." message with attempt count (AC-7.22.1, AC-7.22.2)
 * - Progress indicator during reconnection
 * - Error state with "Connection lost" message (AC-7.22.4)
 * - Manual "Retry" button
 * - "Use polling" fallback option (AC-7.22.5)
 */

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { RefreshCw, WifiOff, Radio, Loader2 } from 'lucide-react';

interface ReconnectionIndicatorProps {
  /** Whether reconnection is in progress */
  isReconnecting: boolean;
  /** Current attempt number */
  attemptCount: number;
  /** Maximum retry attempts */
  maxRetries: number;
  /** Whether max retries have been exceeded */
  maxRetriesExceeded: boolean;
  /** Error message to display */
  error: string | null;
  /** Time until next retry in ms */
  nextRetryIn: number;
  /** Whether polling fallback is active */
  isPolling: boolean;
  /** Callback for manual retry */
  onRetry: () => void;
  /** Callback to enable polling fallback */
  onEnablePolling?: () => void;
  /** Callback to disable polling fallback */
  onDisablePolling?: () => void;
}

/**
 * Indicator component for SSE reconnection status.
 *
 * Shows different states:
 * - Reconnecting: Shows attempt count and countdown
 * - Max retries exceeded: Shows error with retry button
 * - Polling active: Shows polling indicator
 *
 * @example
 * <ReconnectionIndicator
 *   isReconnecting={true}
 *   attemptCount={2}
 *   maxRetries={5}
 *   maxRetriesExceeded={false}
 *   error={null}
 *   nextRetryIn={2000}
 *   isPolling={false}
 *   onRetry={handleRetry}
 *   onEnablePolling={handleEnablePolling}
 * />
 */
export function ReconnectionIndicator({
  isReconnecting,
  attemptCount,
  maxRetries,
  maxRetriesExceeded,
  error,
  nextRetryIn,
  isPolling,
  onRetry,
  onEnablePolling,
  onDisablePolling,
}: ReconnectionIndicatorProps) {
  // Don't render if everything is normal
  if (!isReconnecting && !maxRetriesExceeded && !isPolling) {
    return null;
  }

  // Polling active state
  if (isPolling) {
    return (
      <Alert
        className="bg-blue-50 border-blue-200 dark:bg-blue-950/20 dark:border-blue-800"
        data-testid="polling-indicator"
      >
        <Radio className="h-4 w-4 text-blue-600 dark:text-blue-400 animate-pulse" />
        <AlertTitle className="text-blue-900 dark:text-blue-100">
          Polling Mode Active
        </AlertTitle>
        <AlertDescription className="text-blue-800 dark:text-blue-200">
          <p className="mb-2">
            Using polling fallback due to connection issues. Updates may be slightly delayed.
          </p>
          {onDisablePolling && (
            <Button
              variant="outline"
              size="sm"
              onClick={onDisablePolling}
              className="text-blue-700 border-blue-300 hover:bg-blue-100 dark:text-blue-300 dark:border-blue-700 dark:hover:bg-blue-900/30"
              data-testid="disable-polling-button"
            >
              <WifiOff className="h-3 w-3 mr-1" />
              Disable Polling
            </Button>
          )}
        </AlertDescription>
      </Alert>
    );
  }

  // Max retries exceeded - show error state (AC-7.22.4)
  if (maxRetriesExceeded) {
    return (
      <Alert
        variant="destructive"
        className="bg-red-50 border-red-200 dark:bg-red-950/20 dark:border-red-800"
        data-testid="connection-lost-indicator"
      >
        <WifiOff className="h-4 w-4" />
        <AlertTitle>Connection Lost</AlertTitle>
        <AlertDescription>
          <p className="mb-2">{error || 'Connection lost. Please refresh.'}</p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="text-red-700 border-red-300 hover:bg-red-100 dark:text-red-300 dark:border-red-700 dark:hover:bg-red-900/30"
              data-testid="retry-button"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
            {onEnablePolling && (
              <Button
                variant="outline"
                size="sm"
                onClick={onEnablePolling}
                className="text-red-700 border-red-300 hover:bg-red-100 dark:text-red-300 dark:border-red-700 dark:hover:bg-red-900/30"
                data-testid="enable-polling-button"
              >
                <Radio className="h-3 w-3 mr-1" />
                Use Polling
              </Button>
            )}
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Reconnecting state (AC-7.22.1, AC-7.22.2)
  if (isReconnecting) {
    const progress = ((maxRetries - (maxRetries - attemptCount)) / maxRetries) * 100;
    const secondsRemaining = Math.ceil(nextRetryIn / 1000);

    return (
      <Alert
        className="bg-amber-50 border-amber-200 dark:bg-amber-950/20 dark:border-amber-800"
        data-testid="reconnecting-indicator"
      >
        <Loader2 className="h-4 w-4 text-amber-600 dark:text-amber-400 animate-spin" />
        <AlertTitle className="text-amber-900 dark:text-amber-100">
          Reconnecting...
        </AlertTitle>
        <AlertDescription className="text-amber-800 dark:text-amber-200">
          <p className="mb-2" data-testid="attempt-count">
            Attempt {attemptCount} of {maxRetries}
            {nextRetryIn > 0 && (
              <span className="ml-2 text-amber-600 dark:text-amber-400">
                (retrying in {secondsRemaining}s)
              </span>
            )}
          </p>
          <Progress
            value={progress}
            className="h-2 bg-amber-200 dark:bg-amber-800"
            data-testid="reconnection-progress"
          />
        </AlertDescription>
      </Alert>
    );
  }

  return null;
}

/**
 * Compact inline version of reconnection indicator for use in headers/toolbars
 */
export function ReconnectionIndicatorInline({
  isReconnecting,
  attemptCount,
  maxRetries,
  maxRetriesExceeded,
  isPolling,
  onRetry,
}: Pick<
  ReconnectionIndicatorProps,
  'isReconnecting' | 'attemptCount' | 'maxRetries' | 'maxRetriesExceeded' | 'isPolling' | 'onRetry'
>) {
  if (!isReconnecting && !maxRetriesExceeded && !isPolling) {
    return null;
  }

  if (isPolling) {
    return (
      <div
        className="flex items-center gap-1.5 text-sm text-blue-600 dark:text-blue-400"
        data-testid="polling-indicator-inline"
      >
        <Radio className="h-3 w-3 animate-pulse" />
        <span>Polling</span>
      </div>
    );
  }

  if (maxRetriesExceeded) {
    return (
      <div className="flex items-center gap-1.5" data-testid="connection-lost-inline">
        <WifiOff className="h-3 w-3 text-red-500" />
        <span className="text-sm text-red-600 dark:text-red-400">Disconnected</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={onRetry}
          className="h-6 px-2 text-red-600 hover:text-red-800 dark:text-red-400"
          data-testid="retry-button-inline"
        >
          <RefreshCw className="h-3 w-3" />
        </Button>
      </div>
    );
  }

  if (isReconnecting) {
    return (
      <div
        className="flex items-center gap-1.5 text-sm text-amber-600 dark:text-amber-400"
        data-testid="reconnecting-indicator-inline"
      >
        <Loader2 className="h-3 w-3 animate-spin" />
        <span>
          Reconnecting ({attemptCount}/{maxRetries})
        </span>
      </div>
    );
  }

  return null;
}
