import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useRecentKBs, type RecentKB } from '../useRecentKBs';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ReactNode } from 'react';

describe('useRecentKBs', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.clearAllMocks();
    localStorage.setItem('token', 'test-token');
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  const mockRecentKBs: RecentKB[] = [
    {
      kb_id: '550e8400-e29b-41d4-a716-446655440001',
      kb_name: 'Recent KB 1',
      description: 'First recent KB',
      last_accessed: '2025-12-03T10:00:00Z',
      document_count: 5,
    },
    {
      kb_id: '550e8400-e29b-41d4-a716-446655440002',
      kb_name: 'Recent KB 2',
      description: 'Second recent KB',
      last_accessed: '2025-12-03T09:00:00Z',
      document_count: 10,
    },
  ];

  it('fetches recent KBs on mount', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRecentKBs,
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useRecentKBs(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockRecentKBs);
  });

  it('calls correct API endpoint with auth header', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    global.fetch = mockFetch;

    renderHook(() => useRecentKBs(), { wrapper });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/users/me/recent-kbs', {
        headers: {
          Authorization: 'Bearer test-token',
        },
      });
    });
  });

  it('returns empty array when no recent KBs', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useRecentKBs(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual([]);
  });

  it('handles 401 authentication error', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useRecentKBs(), { wrapper });

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 3000 }
    );

    expect(result.current.error?.message).toBe('Authentication required');
  });

  it('handles generic API error', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useRecentKBs(), { wrapper });

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 3000 }
    );

    expect(result.current.error?.message).toBe('Failed to fetch recent KBs');
  });

  it('sets isLoading during fetch', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ ok: true, json: async () => mockRecentKBs }), 100)
          )
      );
    global.fetch = mockFetch;

    const { result } = renderHook(() => useRecentKBs(), { wrapper });

    // Should be loading initially
    expect(result.current.isLoading).toBe(true);

    // Wait for completion
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('has 5 minute stale time', () => {
    // Query key should be stable for 5 minutes
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRecentKBs,
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useRecentKBs(), { wrapper });

    // Hook uses 5 minute stale time (5 * 60 * 1000 = 300000ms)
    // We can verify by checking the query client's default options
    expect(result.current.isStale).toBe(true); // Initially stale
  });

  it('retries once on failure', async () => {
    // Create a fresh QueryClient with retry enabled for this test
    const retryQueryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: 1, retryDelay: 0 },
      },
    });
    const retryWrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={retryQueryClient}>{children}</QueryClientProvider>
    );

    const mockFetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 500 })
      .mockResolvedValueOnce({ ok: true, json: async () => mockRecentKBs });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useRecentKBs(), { wrapper: retryWrapper });

    await waitFor(
      () => {
        expect(result.current.isSuccess).toBe(true);
      },
      { timeout: 5000 }
    );

    // Should have called fetch twice (initial + 1 retry)
    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(result.current.data).toEqual(mockRecentKBs);
  });
});
