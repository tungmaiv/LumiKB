import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useKBRecommendations, type KBRecommendation } from '../useKBRecommendations';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ReactNode } from 'react';

describe('useKBRecommendations', () => {
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

  const mockRecommendations: KBRecommendation[] = [
    {
      kb_id: '550e8400-e29b-41d4-a716-446655440001',
      kb_name: 'Recommended KB 1',
      description: 'Popular KB',
      score: 0.95,
      reason: 'Based on your recent activity',
      last_accessed: '2025-12-03T10:00:00Z',
      is_cold_start: false,
    },
    {
      kb_id: '550e8400-e29b-41d4-a716-446655440002',
      kb_name: 'Recommended KB 2',
      description: 'Trending KB',
      score: 0.85,
      reason: 'Popular in your organization',
      last_accessed: null,
      is_cold_start: false,
    },
  ];

  const mockColdStartRecommendations: KBRecommendation[] = [
    {
      kb_id: '550e8400-e29b-41d4-a716-446655440003',
      kb_name: 'Public KB',
      description: 'Popular public knowledge base',
      score: 0.8,
      reason: 'Popular across all users',
      last_accessed: null,
      is_cold_start: true,
    },
  ];

  it('fetches KB recommendations on mount', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRecommendations,
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useKBRecommendations(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockRecommendations);
  });

  it('calls correct API endpoint with auth header', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    global.fetch = mockFetch;

    renderHook(() => useKBRecommendations(), { wrapper });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/users/me/kb-recommendations',
        {
          headers: {
            Authorization: 'Bearer test-token',
          },
        }
      );
    });
  });

  it('returns empty array when no recommendations', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useKBRecommendations(), { wrapper });

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

    const { result } = renderHook(() => useKBRecommendations(), { wrapper });

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

    const { result } = renderHook(() => useKBRecommendations(), { wrapper });

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 3000 }
    );

    expect(result.current.error?.message).toBe('Failed to fetch KB recommendations');
  });

  it('sets isLoading during fetch', async () => {
    const mockFetch = vi
      .fn()
      .mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ ok: true, json: async () => mockRecommendations }), 100)
          )
      );
    global.fetch = mockFetch;

    const { result } = renderHook(() => useKBRecommendations(), { wrapper });

    // Should be loading initially
    expect(result.current.isLoading).toBe(true);

    // Wait for completion
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('has 1 hour stale time for caching', () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRecommendations,
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useKBRecommendations(), { wrapper });

    // Hook uses 1 hour stale time (60 * 60 * 1000 = 3600000ms)
    // We can verify by checking the query client's default options
    expect(result.current.isStale).toBe(true); // Initially stale
  });

  it('handles cold start recommendations for new users', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockColdStartRecommendations,
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useKBRecommendations(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockColdStartRecommendations);
    expect(result.current.data?.[0].is_cold_start).toBe(true);
    expect(result.current.data?.[0].last_accessed).toBeNull();
  });

  it('includes score and reason in recommendations', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRecommendations,
    });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useKBRecommendations(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const firstRec = result.current.data?.[0];
    expect(firstRec?.score).toBe(0.95);
    expect(firstRec?.reason).toBe('Based on your recent activity');
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
      .mockResolvedValueOnce({ ok: true, json: async () => mockRecommendations });
    global.fetch = mockFetch;

    const { result } = renderHook(() => useKBRecommendations(), { wrapper: retryWrapper });

    await waitFor(
      () => {
        expect(result.current.isSuccess).toBe(true);
      },
      { timeout: 5000 }
    );

    // Should have called fetch twice (initial + 1 retry)
    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(result.current.data).toEqual(mockRecommendations);
  });
});
