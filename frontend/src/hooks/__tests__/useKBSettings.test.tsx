/**
 * Story 7-14 ATDD: useKBSettings Hook Tests
 * Generated: 2025-12-09
 *
 * Tests AC-7.14.6 & AC-7.14.8:
 * - GET /api/v1/knowledge-bases/{id}/settings query
 * - PUT /api/v1/knowledge-bases/{id}/settings mutation
 * - React Query caching (5min stale time)
 * - Optimistic updates with rollback
 *
 * Implementation: frontend/src/hooks/useKBSettings.ts
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useKBSettings } from '../useKBSettings';
import type { ReactNode } from 'react';
import type { KBSettings } from '@/types/kb-settings';
import { DEFAULT_KB_SETTINGS } from '@/types/kb-settings';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockSettings: KBSettings = { ...DEFAULT_KB_SETTINGS };

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('useKBSettings', () => {
  const kbId = 'test-kb-uuid';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('[P0] AC-7.14.8: GET /settings Query', () => {
    it('fetches settings for a KB', async () => {
      /**
       * GIVEN: Valid KB ID
       * WHEN: Hook mounts
       * THEN: GET request is made to /settings endpoint
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/v1/knowledge-bases/${kbId}/settings`),
        expect.objectContaining({ method: 'GET' })
      );
    });

    it('returns settings data on success', async () => {
      /**
       * GIVEN: API returns settings
       * WHEN: Query completes
       * THEN: Hook returns settings data
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.settings).toBeDefined();
      });

      expect(result.current.settings).toEqual(mockSettings);
      expect(result.current.error).toBeNull();
    });

    it('returns error on API failure', async () => {
      /**
       * GIVEN: API returns error
       * WHEN: Query fails
       * THEN: Hook returns error state
       *
       * Note: Hook has retry: 1, so we mock 2 error responses
       */
      const errorResponse = {
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ detail: 'Internal server error' }),
      };
      // Initial request + 1 retry
      mockFetch.mockResolvedValueOnce(errorResponse);
      mockFetch.mockResolvedValueOnce(errorResponse);

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(
        () => {
          expect(result.current.error).not.toBeNull();
        },
        { timeout: 3000 }
      );

      expect(result.current.error).toBeDefined();
      expect(result.current.settings).toBeUndefined();
    });

    it('starts in loading state', () => {
      /**
       * GIVEN: Hook is mounted
       * WHEN: Initial render
       * THEN: isLoading is true
       */
      mockFetch.mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => mockSettings,
                }),
              100
            )
          )
      );

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.settings).toBeUndefined();
    });
  });

  describe('[P0] AC-7.14.6: PUT /settings Mutation', () => {
    it('updates settings via PUT request', async () => {
      /**
       * GIVEN: Hook has fetched settings
       * WHEN: updateSettings is called
       * THEN: PUT request is made with new settings
       */
      // Initial fetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.settings).toBeDefined();
      });

      // Update settings
      const updatedSettings = {
        ...mockSettings,
        chunking: { ...mockSettings.chunking, chunk_size: 1024 },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedSettings,
      });

      // Refetch after invalidation
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedSettings,
      });

      await act(async () => {
        await result.current.updateSettings(updatedSettings);
      });

      // Verify PUT was called with correct data
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/v1/knowledge-bases/${kbId}/settings`),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updatedSettings),
        })
      );
    });

    it('returns updated settings on mutation success', async () => {
      /**
       * GIVEN: updateSettings is called
       * WHEN: API returns success
       * THEN: Hook returns new settings (via optimistic update)
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.settings).toBeDefined();
      });

      const updatedSettings = {
        ...mockSettings,
        generation: { ...mockSettings.generation, temperature: 1.2 },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedSettings,
      });

      // Refetch after invalidation
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedSettings,
      });

      await act(async () => {
        await result.current.updateSettings(updatedSettings);
      });

      await waitFor(() => {
        expect(result.current.settings?.generation.temperature).toBe(1.2);
      });
    });

    it('handles mutation error', async () => {
      /**
       * GIVEN: updateSettings is called
       * WHEN: API returns error
       * THEN: Error is thrown and rolled back
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.settings).toBeDefined();
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: 'Validation error' }),
      });

      await act(async () => {
        try {
          await result.current.updateSettings(mockSettings);
        } catch {
          // Expected error - updateSettings throws on failure
        }
      });

      // Settings should be rolled back to original
      expect(result.current.settings?.chunking.chunk_size).toBe(512);
    });
  });

  describe('[P1] Optimistic Updates', () => {
    it('applies optimistic update immediately', async () => {
      /**
       * GIVEN: Settings are loaded
       * WHEN: updateSettings is called
       * THEN: UI shows new value before API responds
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.settings).toBeDefined();
      });

      const updatedSettings = {
        ...mockSettings,
        chunking: { ...mockSettings.chunking, chunk_size: 1024 },
      };

      // Slow API response
      let resolveUpdate: (value: unknown) => void;
      mockFetch.mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveUpdate = resolve;
          })
      );

      // Start the update
      act(() => {
        result.current.updateSettings(updatedSettings);
      });

      // Optimistic update should be applied immediately
      await waitFor(() => {
        expect(result.current.settings?.chunking.chunk_size).toBe(1024);
      });

      // Complete the update
      await act(async () => {
        resolveUpdate!({
          ok: true,
          json: async () => updatedSettings,
        });
      });
    });

    it('rolls back on mutation failure', async () => {
      /**
       * GIVEN: Optimistic update was applied
       * WHEN: API returns error
       * THEN: Settings are rolled back to previous value
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.settings).toBeDefined();
      });

      const updatedSettings = {
        ...mockSettings,
        chunking: { ...mockSettings.chunking, chunk_size: 1024 },
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: 'Validation error' }),
      });

      await act(async () => {
        try {
          await result.current.updateSettings(updatedSettings);
        } catch {
          // Expected error
        }
      });

      // Should rollback to original
      await waitFor(() => {
        expect(result.current.settings?.chunking.chunk_size).toBe(512);
      });
    });
  });

  describe('[P1] Caching', () => {
    it('uses cached data within stale time', async () => {
      /**
       * GIVEN: Settings were fetched
       * WHEN: Hook remounts within 5min
       * THEN: No new API call is made (uses cache)
       */
      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false, staleTime: 5 * 60 * 1000 },
        },
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      function Wrapper({ children }: { children: ReactNode }) {
        return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
      }

      // First render
      const { result, unmount } = renderHook(() => useKBSettings(kbId), {
        wrapper: Wrapper,
      });

      await waitFor(() => {
        expect(result.current.settings).toBeDefined();
      });

      unmount();

      // Second render - should use cache
      const { result: result2 } = renderHook(() => useKBSettings(kbId), {
        wrapper: Wrapper,
      });

      await waitFor(() => {
        expect(result2.current.settings).toBeDefined();
      });

      // Only one fetch should have been made
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('[P1] Cache Invalidation', () => {
    it('invalidates cache after successful update', async () => {
      /**
       * GIVEN: Settings were updated
       * WHEN: Cache is checked
       * THEN: Cache reflects new values
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.settings).toBeDefined();
      });

      const updatedSettings = {
        ...mockSettings,
        generation: { ...mockSettings.generation, temperature: 1.5 },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedSettings,
      });

      // Refetch after invalidation
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedSettings,
      });

      await act(async () => {
        await result.current.updateSettings(updatedSettings);
      });

      await waitFor(() => {
        expect(result.current.settings?.generation.temperature).toBe(1.5);
      });
    });
  });

  describe('[P2] Loading States', () => {
    it('returns isSaving while mutation is in progress', async () => {
      /**
       * GIVEN: Settings are loaded
       * WHEN: updateSettings is called
       * THEN: isSaving is true until complete
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.settings).toBeDefined();
      });

      // Slow API response
      let resolveUpdate: (value: unknown) => void;
      mockFetch.mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveUpdate = resolve;
          })
      );

      // Start the mutation (don't await - we want to check isSaving mid-flight)
      act(() => {
        result.current.updateSettings(mockSettings);
      });

      // isSaving should become true after React processes the state update
      await waitFor(() => {
        expect(result.current.isSaving).toBe(true);
      });

      // Mock the refetch that happens after onSettled
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      // Complete the update
      await act(async () => {
        resolveUpdate!({
          ok: true,
          json: async () => mockSettings,
        });
      });

      await waitFor(() => {
        expect(result.current.isSaving).toBe(false);
      });
    });
  });

  describe('[P2] Refetch', () => {
    it('provides refetch function to manually refresh', async () => {
      /**
       * GIVEN: Settings are loaded
       * WHEN: refetch is called
       * THEN: Settings are re-fetched from server
       */
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSettings,
      });

      const { result } = renderHook(() => useKBSettings(kbId), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.settings).toBeDefined();
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Setup for refetch - provide multiple responses in case of background refetches
      const updatedSettings = {
        ...mockSettings,
        chunking: { ...mockSettings.chunking, chunk_size: 2000 },
      };
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => updatedSettings,
      });

      // Trigger refetch
      await act(async () => {
        result.current.refetch();
      });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
      });
    });
  });
});
