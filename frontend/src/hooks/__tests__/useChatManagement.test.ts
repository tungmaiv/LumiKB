/**
 * Tests for useChatManagement hook - localStorage persistence (Story 4-3, Option A fix)
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useChatManagement } from '../useChatManagement';

// Mock fetch
global.fetch = vi.fn();

describe('useChatManagement - localStorage persistence', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    localStorage.clear();
  });

  describe('Undo state persistence (Option A fix)', () => {
    it('[P0] persists undo state to localStorage when clearing chat', async () => {
      // GIVEN: Mock clearChat API response
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ undo_available: true }),
      } as Response);

      const { result } = renderHook(() => useChatManagement());

      // WHEN: Clear chat
      await act(async () => {
        await result.current.clearChat('test-kb-id');
      });

      // THEN: localStorage contains undo state
      expect(localStorage.getItem('chat-undo-available')).toBe('true');
      expect(localStorage.getItem('chat-undo-kb-id')).toBe('test-kb-id');
      expect(localStorage.getItem('chat-undo-expires')).toBeTruthy();

      const expires = Number(localStorage.getItem('chat-undo-expires'));
      expect(expires).toBeGreaterThan(Date.now());
      expect(expires).toBeLessThanOrEqual(Date.now() + 30000);
    });

    it('[P0] initializes undo state from localStorage on mount', async () => {
      // GIVEN: localStorage has valid undo state
      const expiresAt = Date.now() + 15000; // 15s remaining
      localStorage.setItem('chat-undo-available', 'true');
      localStorage.setItem('chat-undo-kb-id', 'test-kb-id');
      localStorage.setItem('chat-undo-expires', String(expiresAt));

      // WHEN: Hook mounts
      const { result } = renderHook(() => useChatManagement());

      // THEN: Undo state restored from localStorage
      expect(result.current.undoAvailable).toBe(true);
      expect(result.current.undoSecondsRemaining).toBeGreaterThan(0);
      expect(result.current.undoSecondsRemaining).toBeLessThanOrEqual(15);
    });

    it('[P0] undo state survives page reload within 30s window', async () => {
      // GIVEN: Clear chat and populate localStorage
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ undo_available: true }),
      } as Response);

      const { result: firstRender } = renderHook(() => useChatManagement());

      await act(async () => {
        await firstRender.current.clearChat('test-kb-id');
      });

      expect(firstRender.current.undoAvailable).toBe(true);

      // WHEN: Simulate page reload (unmount and remount hook)
      const { result: secondRender } = renderHook(() => useChatManagement());

      // THEN: Undo state persists after "reload"
      expect(secondRender.current.undoAvailable).toBe(true);
      expect(secondRender.current.undoSecondsRemaining).toBeGreaterThan(0);
    });

    it('[P0] expired undo state is not restored on mount', async () => {
      // GIVEN: localStorage has expired undo state
      const expiresAt = Date.now() - 1000; // Expired 1s ago
      localStorage.setItem('chat-undo-available', 'true');
      localStorage.setItem('chat-undo-kb-id', 'test-kb-id');
      localStorage.setItem('chat-undo-expires', String(expiresAt));

      // WHEN: Hook mounts
      const { result } = renderHook(() => useChatManagement());

      // THEN: Undo not available (expired)
      expect(result.current.undoAvailable).toBe(false);
      expect(result.current.undoSecondsRemaining).toBe(0);
    });

    it('[P0] clears localStorage when undo timer expires', async () => {
      // GIVEN: Mock clearChat API
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ undo_available: true }),
      } as Response);

      const { result } = renderHook(() => useChatManagement());

      await act(async () => {
        await result.current.clearChat('test-kb-id');
      });

      expect(localStorage.getItem('chat-undo-available')).toBe('true');

      // WHEN: 30 seconds elapse
      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      // THEN: localStorage cleared
      expect(localStorage.getItem('chat-undo-available')).toBeNull();
      expect(localStorage.getItem('chat-undo-kb-id')).toBeNull();
      expect(localStorage.getItem('chat-undo-expires')).toBeNull();
      expect(result.current.undoAvailable).toBe(false);
    });

    it('[P0] clears localStorage when undo is executed', async () => {
      // GIVEN: Undo state in localStorage
      localStorage.setItem('chat-undo-available', 'true');
      localStorage.setItem('chat-undo-kb-id', 'test-kb-id');
      localStorage.setItem('chat-undo-expires', String(Date.now() + 30000));

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      } as Response);

      const { result } = renderHook(() => useChatManagement());

      // WHEN: Execute undo
      await act(async () => {
        await result.current.undoClear('test-kb-id');
      });

      // THEN: localStorage cleared
      expect(localStorage.getItem('chat-undo-available')).toBeNull();
      expect(localStorage.getItem('chat-undo-kb-id')).toBeNull();
      expect(localStorage.getItem('chat-undo-expires')).toBeNull();
    });

    it('[P0] clears localStorage when starting new chat', async () => {
      // GIVEN: Undo state in localStorage
      localStorage.setItem('chat-undo-available', 'true');
      localStorage.setItem('chat-undo-kb-id', 'test-kb-id');
      localStorage.setItem('chat-undo-expires', String(Date.now() + 30000));

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      } as Response);

      const { result } = renderHook(() => useChatManagement());

      // WHEN: Start new chat
      await act(async () => {
        await result.current.startNewChat('test-kb-id');
      });

      // THEN: localStorage cleared
      expect(localStorage.getItem('chat-undo-available')).toBeNull();
      expect(localStorage.getItem('chat-undo-kb-id')).toBeNull();
      expect(localStorage.getItem('chat-undo-expires')).toBeNull();
    });
  });

  describe('Undo countdown timer', () => {
    it('[P0] undoSecondsRemaining decrements every second', async () => {
      // GIVEN: Clear chat initiated
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ undo_available: true }),
      } as Response);

      const { result } = renderHook(() => useChatManagement());

      await act(async () => {
        await result.current.clearChat('test-kb-id');
      });

      expect(result.current.undoSecondsRemaining).toBe(30);

      // WHEN: 5 seconds elapse
      await act(async () => {
        vi.advanceTimersByTime(5000);
      });

      // THEN: Countdown decrements
      expect(result.current.undoSecondsRemaining).toBe(25);

      // WHEN: Another 10 seconds
      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      // THEN: Countdown continues
      expect(result.current.undoSecondsRemaining).toBe(15);
    });

    it('[P1] undoAvailable becomes false after 30s timeout', async () => {
      // GIVEN: Clear chat initiated
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ undo_available: true }),
      } as Response);

      const { result } = renderHook(() => useChatManagement());

      await act(async () => {
        await result.current.clearChat('test-kb-id');
      });

      expect(result.current.undoAvailable).toBe(true);

      // WHEN: 30 seconds elapse
      await act(async () => {
        vi.advanceTimersByTime(30000);
      });

      // THEN: Undo no longer available
      expect(result.current.undoAvailable).toBe(false);
      expect(result.current.undoSecondsRemaining).toBe(0);
    });
  });

  describe('Error handling', () => {
    it('[P1] handles 410 error when undo window expired', async () => {
      // GIVEN: Expired undo attempt
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 410,
        json: async () => ({ detail: 'Undo window expired' }),
      } as Response);

      const { result } = renderHook(() => useChatManagement());

      // WHEN: Attempt undo (error is caught internally)
      let thrownError: Error | null = null;
      await act(async () => {
        try {
          await result.current.undoClear('test-kb-id');
        } catch (err) {
          thrownError = err as Error;
        }
      });

      // THEN: Error was thrown and is set in state
      expect(thrownError).toBeTruthy();
      if (thrownError) {
        expect((thrownError as Error).message).toBe('Undo window expired (30 seconds)');
      }
      expect(result.current.error).toBe('Undo window expired (30 seconds)');
    });

    it('[P2] handles malformed localStorage data gracefully', async () => {
      // GIVEN: Corrupted localStorage data
      localStorage.setItem('chat-undo-available', 'not-a-boolean');
      localStorage.setItem('chat-undo-expires', 'not-a-number');

      // WHEN: Hook mounts
      const { result } = renderHook(() => useChatManagement());

      // THEN: Does not crash, defaults to unavailable
      expect(result.current.undoAvailable).toBe(false);
      expect(result.current.undoSecondsRemaining).toBe(0);
    });
  });
});
