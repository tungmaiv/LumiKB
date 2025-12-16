/**
 * Tests for useFeedbackAnalytics hook - Story 7-23
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useFeedbackAnalytics } from '../useFeedbackAnalytics';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('useFeedbackAnalytics', () => {
  let queryClient: QueryClient;

  const mockAnalyticsResponse = {
    by_type: [
      { type: 'not_relevant', count: 10 },
      { type: 'inaccurate', count: 5 },
      { type: 'incomplete', count: 3 },
    ],
    by_day: [
      { date: '2025-12-01', count: 2 },
      { date: '2025-12-02', count: 3 },
      { date: '2025-12-03', count: 5 },
    ],
    recent: [
      {
        id: 'fb-1',
        timestamp: '2025-12-03T10:00:00Z',
        user_id: 'user-123',
        user_email: 'test@example.com',
        draft_id: 'draft-456',
        feedback_type: 'not_relevant',
        feedback_comments: 'This was not helpful',
        related_request_id: 'req-789',
      },
    ],
    total_count: 18,
  };

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    mockFetch.mockReset();
  });

  afterEach(() => {
    queryClient.clear();
  });

  it('should fetch feedback analytics successfully (AC-7.23.6)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockAnalyticsResponse),
    });

    const { result } = renderHook(() => useFeedbackAnalytics(), { wrapper });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockAnalyticsResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/admin/feedback/analytics'),
      expect.objectContaining({ credentials: 'include' })
    );
  });

  it('should return feedback by type data (AC-7.23.2)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockAnalyticsResponse),
    });

    const { result } = renderHook(() => useFeedbackAnalytics(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data?.by_type).toHaveLength(3);
    expect(result.current.data?.by_type[0]).toEqual({
      type: 'not_relevant',
      count: 10,
    });
  });

  it('should return feedback trend data (AC-7.23.3)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockAnalyticsResponse),
    });

    const { result } = renderHook(() => useFeedbackAnalytics(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data?.by_day).toHaveLength(3);
    expect(result.current.data?.by_day[0]).toEqual({
      date: '2025-12-01',
      count: 2,
    });
  });

  it('should return recent feedback items (AC-7.23.4)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockAnalyticsResponse),
    });

    const { result } = renderHook(() => useFeedbackAnalytics(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data?.recent).toHaveLength(1);
    expect(result.current.data?.recent[0].user_email).toBe('test@example.com');
    expect(result.current.data?.recent[0].feedback_type).toBe('not_relevant');
  });

  it('should handle 403 unauthorized error', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 403,
    });

    const { result } = renderHook(() => useFeedbackAnalytics(), { wrapper });

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 3000 }
    );

    expect(result.current.error?.message).toBe('Unauthorized: Admin access required');
  });

  it('should handle 401 authentication error', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
    });

    const { result } = renderHook(() => useFeedbackAnalytics(), { wrapper });

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 3000 }
    );

    expect(result.current.error?.message).toBe('Authentication required');
  });

  it('should handle generic fetch error', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
    });

    const { result } = renderHook(() => useFeedbackAnalytics(), { wrapper });

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 3000 }
    );

    expect(result.current.error?.message).toBe('Failed to fetch feedback analytics');
  });

  it('should return total feedback count', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockAnalyticsResponse),
    });

    const { result } = renderHook(() => useFeedbackAnalytics(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data?.total_count).toBe(18);
  });
});
