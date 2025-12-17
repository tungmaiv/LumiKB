/**
 * useSSEReconnection Hook Tests - Epic 7, Story 7-22
 * Tests for reconnection logic, exponential backoff, and polling fallback
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useSSEReconnection } from '../useSSEReconnection';

describe('useSSEReconnection', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe('initial state', () => {
    it('returns correct initial state', () => {
      const { result } = renderHook(() => useSSEReconnection());

      expect(result.current.isReconnecting).toBe(false);
      expect(result.current.attemptCount).toBe(0);
      expect(result.current.lastEventId).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.maxRetriesExceeded).toBe(false);
      expect(result.current.isPolling).toBe(false);
      expect(result.current.nextRetryIn).toBe(0);
    });
  });

  describe('exponential backoff (AC-7.22.2)', () => {
    it('calculates correct backoff delays: 1s -> 2s -> 4s -> 8s', () => {
      const { result } = renderHook(() => useSSEReconnection());

      expect(result.current.getBackoffDelay(0)).toBe(1000); // 1s
      expect(result.current.getBackoffDelay(1)).toBe(2000); // 2s
      expect(result.current.getBackoffDelay(2)).toBe(4000); // 4s
      expect(result.current.getBackoffDelay(3)).toBe(8000); // 8s
      expect(result.current.getBackoffDelay(4)).toBe(16000); // 16s
    });

    it('caps backoff at maxDelay (30s)', () => {
      const { result } = renderHook(() => useSSEReconnection({ maxDelay: 30000 }));

      // 2^6 * 1000 = 64000, but should be capped at 30000
      expect(result.current.getBackoffDelay(6)).toBe(30000);
      expect(result.current.getBackoffDelay(10)).toBe(30000);
    });

    it('uses custom initial delay', () => {
      const { result } = renderHook(() => useSSEReconnection({ initialDelay: 500 }));

      expect(result.current.getBackoffDelay(0)).toBe(500); // 0.5s
      expect(result.current.getBackoffDelay(1)).toBe(1000); // 1s
      expect(result.current.getBackoffDelay(2)).toBe(2000); // 2s
    });
  });

  describe('scheduleReconnect', () => {
    it('sets isReconnecting to true and increments attemptCount', () => {
      const { result } = renderHook(() => useSSEReconnection());
      const reconnectFn = vi.fn();

      act(() => {
        result.current.scheduleReconnect(reconnectFn);
      });

      expect(result.current.isReconnecting).toBe(true);
      expect(result.current.attemptCount).toBe(1);
    });

    it('calls reconnect callback after backoff delay', () => {
      const { result } = renderHook(() => useSSEReconnection());
      const reconnectFn = vi.fn();

      act(() => {
        result.current.scheduleReconnect(reconnectFn);
      });

      expect(reconnectFn).not.toHaveBeenCalled();

      // Fast-forward past first backoff (1s)
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      expect(reconnectFn).toHaveBeenCalledTimes(1);
    });

    it('increases delay on subsequent attempts', () => {
      const { result } = renderHook(() => useSSEReconnection());
      const reconnectFn = vi.fn();

      // First attempt
      act(() => {
        result.current.scheduleReconnect(reconnectFn);
        vi.advanceTimersByTime(1000); // 1s delay
      });

      expect(reconnectFn).toHaveBeenCalledTimes(1);
      expect(result.current.attemptCount).toBe(1);

      // Second attempt (should have 2s delay)
      act(() => {
        result.current.scheduleReconnect(reconnectFn);
      });

      expect(result.current.attemptCount).toBe(2);

      // Only 1s passed - should not have called yet
      act(() => {
        vi.advanceTimersByTime(1000);
      });
      expect(reconnectFn).toHaveBeenCalledTimes(1);

      // Another 1s (total 2s) - now it should call
      act(() => {
        vi.advanceTimersByTime(1000);
      });
      expect(reconnectFn).toHaveBeenCalledTimes(2);
    });

    it('fires onReconnectAttempt callback', () => {
      const onReconnectAttempt = vi.fn();
      const { result } = renderHook(() => useSSEReconnection({ onReconnectAttempt }));

      act(() => {
        result.current.scheduleReconnect(() => {});
      });

      expect(onReconnectAttempt).toHaveBeenCalledWith(1);
    });
  });

  describe('max retry limit (AC-7.22.4)', () => {
    it('sets maxRetriesExceeded after reaching limit', () => {
      const { result } = renderHook(() => useSSEReconnection({ maxRetries: 3 }));
      const reconnectFn = vi.fn();

      // Attempt 1
      act(() => {
        result.current.scheduleReconnect(reconnectFn);
        vi.advanceTimersByTime(1000);
      });

      // Attempt 2
      act(() => {
        result.current.scheduleReconnect(reconnectFn);
        vi.advanceTimersByTime(2000);
      });

      // Attempt 3
      act(() => {
        result.current.scheduleReconnect(reconnectFn);
        vi.advanceTimersByTime(4000);
      });

      expect(result.current.attemptCount).toBe(3);
      expect(result.current.maxRetriesExceeded).toBe(false);

      // Attempt 4 - should exceed max
      act(() => {
        result.current.scheduleReconnect(reconnectFn);
      });

      expect(result.current.maxRetriesExceeded).toBe(true);
      expect(result.current.error).toBe('Connection lost. Please refresh.');
      expect(result.current.isReconnecting).toBe(false);
    });

    it('fires onMaxRetriesExceeded callback', () => {
      const onMaxRetriesExceeded = vi.fn();
      const { result } = renderHook(() =>
        useSSEReconnection({ maxRetries: 1, onMaxRetriesExceeded })
      );

      // First attempt
      act(() => {
        result.current.scheduleReconnect(() => {});
        vi.advanceTimersByTime(1000);
      });

      // Second attempt - should exceed
      act(() => {
        result.current.scheduleReconnect(() => {});
      });

      expect(onMaxRetriesExceeded).toHaveBeenCalledTimes(1);
    });
  });

  describe('onConnectionSuccess (AC-7.22.3)', () => {
    it('resets state on successful connection', () => {
      const { result } = renderHook(() => useSSEReconnection());

      // Simulate some reconnection attempts
      act(() => {
        result.current.scheduleReconnect(() => {});
      });

      expect(result.current.isReconnecting).toBe(true);
      expect(result.current.attemptCount).toBe(1);

      // Connection succeeds
      act(() => {
        result.current.onConnectionSuccess();
      });

      expect(result.current.isReconnecting).toBe(false);
      expect(result.current.attemptCount).toBe(0);
      expect(result.current.error).toBeNull();
      expect(result.current.maxRetriesExceeded).toBe(false);
    });

    it('fires onReconnectSuccess callback', () => {
      const onReconnectSuccess = vi.fn();
      const { result } = renderHook(() => useSSEReconnection({ onReconnectSuccess }));

      act(() => {
        result.current.scheduleReconnect(() => {});
      });

      act(() => {
        result.current.onConnectionSuccess();
      });

      expect(onReconnectSuccess).toHaveBeenCalledTimes(1);
    });

    it('clears pending reconnect timeout', () => {
      const { result } = renderHook(() => useSSEReconnection());
      const reconnectFn = vi.fn();

      act(() => {
        result.current.scheduleReconnect(reconnectFn);
      });

      // Connection succeeds before timeout
      act(() => {
        result.current.onConnectionSuccess();
      });

      // Advance past the original timeout
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      // reconnectFn should NOT have been called because we cleared it
      expect(reconnectFn).not.toHaveBeenCalled();
    });
  });

  describe('Last-Event-ID tracking (AC-7.22.3)', () => {
    it('tracks last event ID', () => {
      const { result } = renderHook(() => useSSEReconnection());

      expect(result.current.lastEventId).toBeNull();

      act(() => {
        result.current.setLastEventId('event-123');
      });

      expect(result.current.lastEventId).toBe('event-123');
    });

    it('preserves lastEventId through reconnection', () => {
      const { result } = renderHook(() => useSSEReconnection());

      act(() => {
        result.current.setLastEventId('event-456');
      });

      act(() => {
        result.current.scheduleReconnect(() => {});
      });

      expect(result.current.lastEventId).toBe('event-456');
    });
  });

  describe('manualRetry', () => {
    it('resets attempt count and schedules reconnect', () => {
      const { result } = renderHook(() => useSSEReconnection({ maxRetries: 2 }));
      const reconnectFn = vi.fn();

      // Exhaust retries
      act(() => {
        result.current.scheduleReconnect(reconnectFn);
        vi.advanceTimersByTime(1000);
      });
      act(() => {
        result.current.scheduleReconnect(reconnectFn);
        vi.advanceTimersByTime(2000);
      });
      act(() => {
        result.current.scheduleReconnect(reconnectFn);
      });

      expect(result.current.maxRetriesExceeded).toBe(true);

      // Manual retry
      act(() => {
        result.current.manualRetry(reconnectFn);
      });

      expect(result.current.maxRetriesExceeded).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.attemptCount).toBe(1); // Reset and started new attempt
      expect(result.current.isReconnecting).toBe(true);
    });
  });

  describe('resetState', () => {
    it('resets all state to initial values', () => {
      const { result } = renderHook(() => useSSEReconnection());

      // Set some state
      act(() => {
        result.current.setLastEventId('event-789');
        result.current.scheduleReconnect(() => {});
      });

      expect(result.current.isReconnecting).toBe(true);
      expect(result.current.lastEventId).toBe('event-789');

      // Reset
      act(() => {
        result.current.resetState();
      });

      expect(result.current.isReconnecting).toBe(false);
      expect(result.current.attemptCount).toBe(0);
      expect(result.current.lastEventId).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.maxRetriesExceeded).toBe(false);
      expect(result.current.isPolling).toBe(false);
    });
  });

  describe('polling fallback (AC-7.22.5)', () => {
    it('enables polling mode', async () => {
      const { result } = renderHook(() => useSSEReconnection());
      const pollFn = vi.fn().mockResolvedValue(undefined);

      await act(async () => {
        result.current.enablePolling(pollFn);
      });

      expect(result.current.isPolling).toBe(true);
      expect(result.current.isReconnecting).toBe(false);
      expect(pollFn).toHaveBeenCalledTimes(1); // Called immediately
    });

    it('polls at configured interval', async () => {
      const { result } = renderHook(() => useSSEReconnection({ pollingInterval: 2000 }));
      const pollFn = vi.fn().mockResolvedValue(undefined);

      await act(async () => {
        result.current.enablePolling(pollFn);
      });

      expect(pollFn).toHaveBeenCalledTimes(1);

      // Advance 2 seconds
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(pollFn).toHaveBeenCalledTimes(2);

      // Advance another 2 seconds
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(pollFn).toHaveBeenCalledTimes(3);
    });

    it('disables polling mode', async () => {
      const { result } = renderHook(() => useSSEReconnection());
      const pollFn = vi.fn().mockResolvedValue(undefined);

      await act(async () => {
        result.current.enablePolling(pollFn);
      });

      expect(result.current.isPolling).toBe(true);

      act(() => {
        result.current.disablePolling();
      });

      expect(result.current.isPolling).toBe(false);

      // Polling should stop
      const callCountBefore = pollFn.mock.calls.length;

      await act(async () => {
        vi.advanceTimersByTime(5000);
      });

      expect(pollFn).toHaveBeenCalledTimes(callCountBefore);
    });

    it('handles polling errors gracefully', async () => {
      const { result } = renderHook(() => useSSEReconnection());
      const pollFn = vi.fn().mockRejectedValue(new Error('Poll failed'));
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await act(async () => {
        result.current.enablePolling(pollFn);
      });

      // Should still be polling despite error
      expect(result.current.isPolling).toBe(true);

      consoleSpy.mockRestore();
    });
  });

  describe('nextRetryIn countdown', () => {
    it('tracks time until next retry', () => {
      const { result } = renderHook(() => useSSEReconnection());

      act(() => {
        result.current.scheduleReconnect(() => {});
      });

      // Initial nextRetryIn should be set to backoff delay
      expect(result.current.nextRetryIn).toBe(1000);

      // After some time, countdown should decrease
      act(() => {
        vi.advanceTimersByTime(500);
      });

      // Should be around 500ms remaining (accounting for interval timing)
      expect(result.current.nextRetryIn).toBeLessThan(1000);
    });
  });
});
