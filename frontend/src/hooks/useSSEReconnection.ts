/**
 * SSE Reconnection Hook - Epic 7, Story 7-22
 * Automatic reconnection with exponential backoff for SSE streams.
 *
 * Features:
 * - Exponential backoff: 1s → 2s → 4s → 8s → max 30s (AC-7.22.2)
 * - Max retry limit of 5 attempts (AC-7.22.4)
 * - Last-Event-ID tracking for resume (AC-7.22.3)
 * - Polling fallback option (AC-7.22.5)
 */

import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Reconnection state exposed by the hook
 */
export interface ReconnectionState {
  /** Whether reconnection is currently in progress */
  isReconnecting: boolean;
  /** Number of reconnection attempts made */
  attemptCount: number;
  /** Last event ID for resume capability */
  lastEventId: string | null;
  /** Error message if reconnection failed */
  error: string | null;
  /** Whether max retries exceeded */
  maxRetriesExceeded: boolean;
  /** Whether polling fallback is active */
  isPolling: boolean;
  /** Time until next retry attempt (ms) */
  nextRetryIn: number;
}

/**
 * Options for the SSE reconnection hook
 */
export interface UseSSEReconnectionOptions {
  /** Maximum number of retry attempts (default: 5) */
  maxRetries?: number;
  /** Initial backoff delay in ms (default: 1000) */
  initialDelay?: number;
  /** Maximum backoff delay in ms (default: 30000) */
  maxDelay?: number;
  /** Polling interval in ms (default: 2000) */
  pollingInterval?: number;
  /** Callback when reconnection succeeds */
  onReconnectSuccess?: () => void;
  /** Callback when max retries exceeded */
  onMaxRetriesExceeded?: () => void;
  /** Callback for each reconnection attempt */
  onReconnectAttempt?: (attemptCount: number) => void;
}

/**
 * Result type for the SSE reconnection hook
 */
export interface UseSSEReconnectionResult extends ReconnectionState {
  /** Schedule a reconnection attempt with the given callback */
  scheduleReconnect: (onReconnect: () => void) => void;
  /** Call when connection is successfully established */
  onConnectionSuccess: () => void;
  /** Set the last event ID for resume capability */
  setLastEventId: (id: string) => void;
  /** Manually trigger a retry */
  manualRetry: (onReconnect: () => void) => void;
  /** Reset all reconnection state */
  resetState: () => void;
  /** Enable polling fallback mode */
  enablePolling: (pollCallback: () => Promise<void>) => void;
  /** Disable polling fallback mode */
  disablePolling: () => void;
  /** Calculate backoff delay for a given attempt */
  getBackoffDelay: (attempt: number) => number;
}

const INITIAL_STATE: ReconnectionState = {
  isReconnecting: false,
  attemptCount: 0,
  lastEventId: null,
  error: null,
  maxRetriesExceeded: false,
  isPolling: false,
  nextRetryIn: 0,
};

/**
 * Hook for managing SSE reconnection with exponential backoff.
 *
 * Provides automatic reconnection logic for SSE streams that:
 * - Retries with exponential backoff (1s → 2s → 4s → 8s → max 30s)
 * - Limits retries to 5 attempts by default
 * - Tracks Last-Event-ID for seamless resume
 * - Offers polling fallback when SSE fails
 *
 * @param options Configuration options
 * @returns Reconnection state and control functions
 *
 * @example
 * const { scheduleReconnect, onConnectionSuccess, isReconnecting, attemptCount } =
 *   useSSEReconnection({
 *     maxRetries: 5,
 *     onMaxRetriesExceeded: () => showError('Connection lost'),
 *   });
 *
 * // In SSE error handler:
 * eventSource.onerror = () => {
 *   scheduleReconnect(() => connectToStream());
 * };
 *
 * // In SSE open handler:
 * eventSource.onopen = () => {
 *   onConnectionSuccess();
 * };
 */
export function useSSEReconnection(
  options: UseSSEReconnectionOptions = {}
): UseSSEReconnectionResult {
  const {
    maxRetries = 5,
    initialDelay = 1000,
    maxDelay = 30000,
    pollingInterval = 2000,
    onReconnectSuccess,
    onMaxRetriesExceeded,
    onReconnectAttempt,
  } = options;

  const [state, setState] = useState<ReconnectionState>(INITIAL_STATE);

  // Refs for timers and callbacks
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pendingReconnectRef = useRef<(() => void) | null>(null);
  const pollingCallbackRef = useRef<(() => Promise<void>) | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }
    };
  }, []);

  /**
   * Calculate exponential backoff delay.
   * Follows pattern: 1s → 2s → 4s → 8s → ... → max 30s
   */
  const getBackoffDelay = useCallback(
    (attempt: number): number => {
      const delay = initialDelay * Math.pow(2, attempt);
      return Math.min(delay, maxDelay);
    },
    [initialDelay, maxDelay]
  );

  /**
   * Schedule a reconnection attempt with exponential backoff.
   * Calls onReconnect callback after the backoff delay.
   */
  const scheduleReconnect = useCallback(
    (onReconnect: () => void) => {
      // Clear any existing timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }

      // Check if max retries exceeded (AC-7.22.4)
      setState((prev) => {
        if (prev.attemptCount >= maxRetries) {
          onMaxRetriesExceeded?.();
          return {
            ...prev,
            isReconnecting: false,
            maxRetriesExceeded: true,
            error: 'Connection lost. Please refresh.',
            nextRetryIn: 0,
          };
        }

        const newAttemptCount = prev.attemptCount + 1;
        const delay = getBackoffDelay(prev.attemptCount);

        // Fire attempt callback
        onReconnectAttempt?.(newAttemptCount);

        // Store pending reconnect callback
        pendingReconnectRef.current = onReconnect;

        // Schedule the reconnection
        reconnectTimeoutRef.current = setTimeout(() => {
          pendingReconnectRef.current?.();
          setState((s) => ({ ...s, nextRetryIn: 0 }));
        }, delay);

        // Start countdown for UI
        const startTime = Date.now();
        countdownIntervalRef.current = setInterval(() => {
          const elapsed = Date.now() - startTime;
          const remaining = Math.max(0, delay - elapsed);
          setState((s) => ({ ...s, nextRetryIn: remaining }));
          if (remaining === 0 && countdownIntervalRef.current) {
            clearInterval(countdownIntervalRef.current);
          }
        }, 100);

        return {
          ...prev,
          isReconnecting: true,
          attemptCount: newAttemptCount,
          error: null,
          maxRetriesExceeded: false,
          nextRetryIn: delay,
        };
      });
    },
    [maxRetries, getBackoffDelay, onMaxRetriesExceeded, onReconnectAttempt]
  );

  /**
   * Call when connection is successfully established (AC-7.22.3).
   * Resets retry count and clears reconnecting state.
   */
  const onConnectionSuccess = useCallback(() => {
    // Clear timers
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = null;
    }

    pendingReconnectRef.current = null;
    onReconnectSuccess?.();

    setState((prev) => ({
      ...prev,
      isReconnecting: false,
      attemptCount: 0,
      error: null,
      maxRetriesExceeded: false,
      nextRetryIn: 0,
    }));
  }, [onReconnectSuccess]);

  /**
   * Set the last event ID for resuming streams (AC-7.22.3).
   */
  const setLastEventId = useCallback((id: string) => {
    setState((prev) => ({ ...prev, lastEventId: id }));
  }, []);

  /**
   * Manually trigger a retry (for "Retry" button in UI).
   * Resets attempt count before retrying.
   */
  const manualRetry = useCallback(
    (onReconnect: () => void) => {
      setState((prev) => ({
        ...prev,
        attemptCount: 0,
        error: null,
        maxRetriesExceeded: false,
      }));

      // Schedule reconnect will increment attempt count
      scheduleReconnect(onReconnect);
    },
    [scheduleReconnect]
  );

  /**
   * Reset all reconnection state.
   */
  const resetState = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = null;
    }

    pendingReconnectRef.current = null;
    pollingCallbackRef.current = null;

    setState(INITIAL_STATE);
  }, []);

  /**
   * Enable polling fallback mode (AC-7.22.5).
   * Starts polling at the configured interval.
   */
  const enablePolling = useCallback(
    (pollCallback: () => Promise<void>) => {
      // Clear any existing polling
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }

      pollingCallbackRef.current = pollCallback;

      setState((prev) => ({
        ...prev,
        isPolling: true,
        isReconnecting: false,
        error: null,
      }));

      // Start polling at configured interval (default 2s per AC-7.22.5)
      pollingIntervalRef.current = setInterval(async () => {
        try {
          await pollingCallbackRef.current?.();
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, pollingInterval);

      // Execute immediately as well
      pollCallback().catch(console.error);
    },
    [pollingInterval]
  );

  /**
   * Disable polling fallback mode.
   */
  const disablePolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    pollingCallbackRef.current = null;

    setState((prev) => ({
      ...prev,
      isPolling: false,
    }));
  }, []);

  return {
    ...state,
    scheduleReconnect,
    onConnectionSuccess,
    setLastEventId,
    manualRetry,
    resetState,
    enablePolling,
    disablePolling,
    getBackoffDelay,
  };
}
