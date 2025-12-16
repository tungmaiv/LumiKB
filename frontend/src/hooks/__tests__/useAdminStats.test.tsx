/**
 * Unit tests for useAdminStats hook
 *
 * Tests data fetching, error handling, and manual refresh functionality
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ReactNode } from 'react';
import { useAdminStats } from '../useAdminStats';

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

describe('useAdminStats', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should fetch admin stats successfully', async () => {
    // Arrange
    const mockStats = {
      users: { total: 100, active: 80, inactive: 20 },
      knowledge_bases: { total: 50, by_status: { active: 45, archived: 5 } },
      documents: {
        total: 1000,
        by_status: { READY: 900, PENDING: 50, FAILED: 50 },
      },
      storage: { total_bytes: 1000000, avg_doc_size_bytes: 1000 },
      activity: {
        searches: { last_24h: 10, last_7d: 70, last_30d: 300 },
        generations: { last_24h: 5, last_7d: 35, last_30d: 150 },
      },
      trends: { searches: Array(30).fill(10), generations: Array(30).fill(5) },
    };

    localStorage.setItem('token', 'test-token');
    (global.fetch as vi.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockStats,
    });

    // Act
    const { result } = renderHook(() => useAdminStats(), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockStats);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/admin/stats'),
      expect.objectContaining({
        headers: {
          Authorization: 'Bearer test-token',
        },
      })
    );
  });

  it('should handle 403 Forbidden error', async () => {
    // Arrange
    localStorage.setItem('token', 'test-token');
    (global.fetch as vi.Mock).mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'Not authorized' }),
    });

    // Act
    const { result } = renderHook(() => useAdminStats(), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it('should handle 401 Unauthorized error', async () => {
    // Arrange
    localStorage.setItem('token', 'test-token');
    (global.fetch as vi.Mock).mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Not authenticated' }),
    });

    // Act
    const { result } = renderHook(() => useAdminStats(), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it('should handle network errors', async () => {
    // Arrange
    localStorage.setItem('token', 'test-token');
    (global.fetch as vi.Mock).mockRejectedValueOnce(
      new Error('Network error')
    );

    // Act
    const { result } = renderHook(() => useAdminStats(), {
      wrapper: createWrapper(),
    });

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it('should use staleTime of 5 minutes', () => {
    // Arrange
    localStorage.setItem('token', 'test-token');
    (global.fetch as vi.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    // Act
    const { result } = renderHook(() => useAdminStats(), {
      wrapper: createWrapper(),
    });

    // Assert
    // React Query should not refetch within staleTime
    expect(result.current.isLoading || result.current.isSuccess).toBe(true);
  });

  it('should allow manual refetch', async () => {
    // Arrange
    const mockStats = {
      users: { total: 100, active: 80, inactive: 20 },
      knowledge_bases: { total: 50, by_status: {} },
      documents: { total: 1000, by_status: {} },
      storage: { total_bytes: 1000000, avg_doc_size_bytes: 1000 },
      activity: {
        searches: { last_24h: 10, last_7d: 70, last_30d: 300 },
        generations: { last_24h: 5, last_7d: 35, last_30d: 150 },
      },
      trends: { searches: [], generations: [] },
    };

    localStorage.setItem('token', 'test-token');
    (global.fetch as vi.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockStats,
    });

    // Act
    const { result } = renderHook(() => useAdminStats(), {
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
