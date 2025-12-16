/**
 * Unit tests for useAuditLogs hook
 * Updated: 2025-12-04 (Story 5.15 - ATDD Transition to GREEN)
 *
 * Tests audit log fetching with react-query, filtering, pagination, and error handling.
 * Story: 5-2 (Audit Log Viewer)
 */

import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAuditLogs } from '../useAuditLogs';

// Mock fetch API
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Create wrapper with QueryClientProvider
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0, // Disable garbage collection for tests
        staleTime: 0,
      },
    },
  });
  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  return { wrapper: Wrapper, queryClient };
};

describe('useAuditLogs Hook', () => {
  const mockAuditEvents = [
    {
      id: '1',
      timestamp: '2025-12-02T10:00:00Z',
      event_type: 'search',
      user_id: 'user-123',
      user_email: 'test@example.com',
      resource_type: 'knowledge_base',
      resource_id: 'kb-456',
      status: 'success',
      duration_ms: 150,
      ip_address: 'XXX.XXX.XXX.XXX',
      details: { query: 'test search' },
    },
    {
      id: '2',
      timestamp: '2025-12-02T09:00:00Z',
      event_type: 'generation',
      user_id: 'user-123',
      user_email: 'test@example.com',
      resource_type: 'draft',
      resource_id: 'draft-789',
      status: 'success',
      duration_ms: 2500,
      ip_address: 'XXX.XXX.XXX.XXX',
      details: { document_type: 'report' },
    },
  ];

  const mockPaginatedResponse = {
    events: mockAuditEvents,
    total: 100,
    page: 1,
    page_size: 50,
    has_more: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage for token
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => 'test-token'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe('[P1] useAuditLogs fetches data on mount', () => {
    it('should fetch audit logs when hook is mounted', async () => {
      // GIVEN: useAuditLogs hook with default filters
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPaginatedResponse,
      });

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered
      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 1, pageSize: 50 }),
        { wrapper }
      );

      // THEN: Should be in loading state initially
      expect(result.current.isLoading).toBe(true);

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // THEN: Should have fetched audit logs
      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/audit/logs'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      // THEN: Should have data from response
      expect(result.current.data).toBeDefined();
      expect(result.current.data?.events).toEqual(mockAuditEvents);
      expect(result.current.data?.total).toBe(100);
      expect(result.current.error).toBeNull();
    });

    it('should fetch audit logs with filters applied', async () => {
      // GIVEN: useAuditLogs hook with date and event_type filters
      const filters = {
        start_date: '2025-12-01',
        end_date: '2025-12-02',
        event_type: 'search',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockPaginatedResponse,
          events: [mockAuditEvents[0]], // Only search event
          total: 1,
        }),
      });

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered with filters
      const { result } = renderHook(
        () => useAuditLogs({ filters, page: 1, pageSize: 50 }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // THEN: Should include filters in request
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/admin/audit/logs'),
        expect.objectContaining({
          body: expect.stringContaining('search'),
        })
      );

      // THEN: Should have filtered results
      expect(result.current.data?.events).toHaveLength(1);
      expect(result.current.data?.events[0].action).toBe('search');
      expect(result.current.data?.total).toBe(1);
    });
  });

  describe('[P1] useAuditLogs handles loading state', () => {
    it('should set isLoading to true while fetching', () => {
      // GIVEN: Fetch returns a pending promise
      mockFetch.mockReturnValueOnce(
        new Promise(() => {}) // Never resolves
      );

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered
      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 1, pageSize: 50 }),
        { wrapper }
      );

      // THEN: Should be in loading state
      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBeNull();
    });

    it('should set isLoading to false after data loads', async () => {
      // GIVEN: Fetch returns successful response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPaginatedResponse,
      });

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered
      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 1, pageSize: 50 }),
        { wrapper }
      );

      // THEN: Should transition from loading to loaded
      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data?.events).toEqual(mockAuditEvents);
    });
  });

  describe('[P1] useAuditLogs handles error state', () => {
    it('should set error when API returns error response', async () => {
      // GIVEN: Fetch returns 500 error
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered
      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 1, pageSize: 50 }),
        { wrapper }
      );

      // THEN: Should have error set after query settles
      await waitFor(
        () => {
          expect(result.current.error).toBeTruthy();
        },
        { timeout: 3000 }
      );

      expect(result.current.data).toBeUndefined();
    });

    it('should set error when API returns 403 Forbidden', async () => {
      // GIVEN: Non-admin user receives 403
      mockFetch.mockResolvedValue({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
        json: async () => ({ detail: 'Admin access required' }),
      });

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered
      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 1, pageSize: 50 }),
        { wrapper }
      );

      // THEN: Should have error set
      await waitFor(
        () => {
          expect(result.current.error).toBeTruthy();
        },
        { timeout: 3000 }
      );

      expect(result.current.data).toBeUndefined();
    });

    it('should set error when network fails', async () => {
      // GIVEN: Fetch throws network error
      mockFetch.mockRejectedValue(new Error('Network error'));

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered
      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 1, pageSize: 50 }),
        { wrapper }
      );

      // THEN: Should have error set
      await waitFor(
        () => {
          expect(result.current.error).toBeTruthy();
        },
        { timeout: 3000 }
      );

      expect(result.current.error?.message).toContain('Network error');
      expect(result.current.data).toBeUndefined();
    });
  });

  describe('[P1] useAuditLogs refetches on filter change', () => {
    it('should refetch when filters change', async () => {
      // GIVEN: Initial fetch successful
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPaginatedResponse,
      });

      const { wrapper } = createWrapper();

      const { result, rerender } = renderHook(
        ({ filters }) => useAuditLogs({ filters, page: 1, pageSize: 50 }),
        {
          wrapper,
          initialProps: { filters: {} },
        }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);

      // WHEN: Filters change
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockPaginatedResponse,
          events: [mockAuditEvents[0]],
          total: 1,
        }),
      });

      rerender({ filters: { event_type: 'search' } });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
      });

      // Wait for data to be updated after refetch
      await waitFor(() => {
        expect(result.current.data?.events).toHaveLength(1);
      });
    });

    it('should refetch when page changes', async () => {
      // GIVEN: Initial fetch successful (page 1)
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPaginatedResponse,
      });

      const { wrapper } = createWrapper();

      const { result, rerender } = renderHook(
        ({ page }) => useAuditLogs({ filters: {}, page, pageSize: 50 }),
        {
          wrapper,
          initialProps: { page: 1 },
        }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);

      // WHEN: Page changes to 2
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockPaginatedResponse,
          page: 2,
          events: [mockAuditEvents[1]],
        }),
      });

      rerender({ page: 2 });

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
      });

      // Wait for data to be updated after refetch
      await waitFor(() => {
        expect(result.current.data?.page).toBe(2);
      });
    });
  });

  describe('[P2] useAuditLogs provides refetch function', () => {
    it('should refetch when refetch function is called', async () => {
      // GIVEN: Initial fetch successful
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPaginatedResponse,
      });

      const { wrapper } = createWrapper();

      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 1, pageSize: 50 }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);

      // WHEN: Refetch is called
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPaginatedResponse,
      });

      await result.current.refetch();

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2);
      });

      // THEN: Should make another API call
      expect(result.current.data?.events).toEqual(mockAuditEvents);
    });
  });

  describe('[P2] useAuditLogs handles pagination metadata', () => {
    it('should return has_more flag from paginated response', async () => {
      // GIVEN: Paginated response with has_more=true
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockPaginatedResponse,
          has_more: true,
        }),
      });

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered
      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 1, pageSize: 50 }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // THEN: Should return has_more flag
      expect(result.current.data?.has_more).toBe(true);
    });

    it('should handle last page correctly (has_more=false)', async () => {
      // GIVEN: Last page with has_more=false
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ...mockPaginatedResponse,
          page: 2,
          total: 100,
          has_more: false,
        }),
      });

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered for page 2
      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 2, pageSize: 50 }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // THEN: Should indicate no more pages
      expect(result.current.data?.has_more).toBe(false);
    });
  });

  describe('[P2] useAuditLogs handles edge cases', () => {
    it('should handle empty results gracefully', async () => {
      // GIVEN: API returns empty events array
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          events: [],
          total: 0,
          page: 1,
          page_size: 50,
          has_more: false,
        }),
      });

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered
      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 1, pageSize: 50 }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // THEN: Should handle empty state
      expect(result.current.data?.events).toEqual([]);
      expect(result.current.data?.total).toBe(0);
      expect(result.current.error).toBeNull();
    });

    it('should handle query timeout (504 Gateway Timeout)', async () => {
      // GIVEN: API returns 504 timeout error
      mockFetch.mockResolvedValue({
        ok: false,
        status: 504,
        statusText: 'Gateway Timeout',
        json: async () => ({
          detail: 'Query timed out. Please narrow your date range or add more filters.',
        }),
      });

      const { wrapper } = createWrapper();

      // WHEN: Hook is rendered
      const { result } = renderHook(
        () => useAuditLogs({ filters: {}, page: 1, pageSize: 10000 }),
        { wrapper }
      );

      // THEN: Should set timeout error (wait for error instead of isLoading)
      await waitFor(
        () => {
          expect(result.current.error).toBeTruthy();
        },
        { timeout: 3000 }
      );

      expect(result.current.data).toBeUndefined();
    });
  });
});
