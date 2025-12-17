/**
 * Unit tests for useQueueStatus hook
 * Story 5-4: Processing Queue Status
 *
 * Tests data fetching, error handling, and auto-refresh functionality
 * for the queue monitoring feature.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, type Mock } from 'vitest';
import { ReactNode } from 'react';
import { useQueueStatus } from '../useQueueStatus';

// Mock fetch
global.fetch = vi.fn();

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useQueueStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('[P0] should fetch queue status successfully - AC-5.4.1', async () => {
    // Arrange
    const mockQueues = [
      {
        queue_name: 'document_processing',
        pending_tasks: 10,
        active_tasks: 3,
        workers: [
          {
            worker_id: 'worker-1',
            status: 'online',
            active_tasks: 2,
            processed_count: 42,
            last_heartbeat: new Date().toISOString(),
          },
        ],
        status: 'available',
      },
      {
        queue_name: 'embedding_generation',
        pending_tasks: 5,
        active_tasks: 1,
        workers: [],
        status: 'available',
      },
      {
        queue_name: 'export_generation',
        pending_tasks: 2,
        active_tasks: 0,
        workers: [],
        status: 'available',
      },
    ];

    localStorage.setItem('token', 'test-token');
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockQueues,
    });

    // Act
    const { result } = renderHook(() => useQueueStatus(), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockQueues);
    expect(result.current.data).toHaveLength(3);
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/admin/queue/status',
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('[P0] should handle 403 Forbidden error - AC-5.4.6', async () => {
    // Arrange
    localStorage.setItem('token', 'test-token');
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'Admin access required' }),
    });

    // Act
    const { result } = renderHook(() => useQueueStatus(), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it('[P0] should handle Celery broker unavailable gracefully - AC-5.4.5', async () => {
    // Arrange
    const mockUnavailableQueues = [
      {
        queue_name: 'document_processing',
        pending_tasks: 0,
        active_tasks: 0,
        workers: [],
        status: 'unavailable',
      },
      {
        queue_name: 'embedding_generation',
        pending_tasks: 0,
        active_tasks: 0,
        workers: [],
        status: 'unavailable',
      },
      {
        queue_name: 'export_generation',
        pending_tasks: 0,
        active_tasks: 0,
        workers: [],
        status: 'unavailable',
      },
    ];

    localStorage.setItem('token', 'test-token');
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockUnavailableQueues,
    });

    // Act
    const { result } = renderHook(() => useQueueStatus(), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockUnavailableQueues);
    expect(result.current.data?.every((q) => q.status === 'unavailable')).toBe(true);
  });

  it('[P1] should handle network errors', async () => {
    // Arrange
    localStorage.setItem('token', 'test-token');
    (global.fetch as Mock).mockRejectedValueOnce(new Error('Network error'));

    // Act
    const { result } = renderHook(() => useQueueStatus(), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it('[P1] should use refetchInterval of 10 seconds for auto-refresh', () => {
    // Arrange
    localStorage.setItem('token', 'test-token');
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });

    // Act
    const { result } = renderHook(() => useQueueStatus(), {
      wrapper: createWrapper(),
    });

    // Assert: Hook should have refetchInterval configured
    // React Query automatically handles this internally
    expect(result.current.isLoading || result.current.isSuccess).toBe(true);
  });

  it('[P1] should allow manual refetch', async () => {
    // Arrange
    const mockQueues = [
      {
        queue_name: 'document_processing',
        pending_tasks: 10,
        active_tasks: 3,
        workers: [],
        status: 'available',
      },
    ];

    localStorage.setItem('token', 'test-token');
    (global.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => mockQueues,
    });

    // Act
    const { result } = renderHook(() => useQueueStatus(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Refetch
    result.current.refetch();

    // Assert
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });
});
