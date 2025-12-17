import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useKBStats } from '../useKBStats';

// Mock fetch globally
global.fetch = vi.fn();

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  Wrapper.displayName = 'QueryClientWrapper';

  return Wrapper;
}

describe('useKBStats', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should not fetch when kbId is null', () => {
    const { result } = renderHook(() => useKBStats(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
    expect(fetch).not.toHaveBeenCalled();
  });

  it('should fetch KB stats successfully', async () => {
    const mockStats = {
      kb_id: 'kb-123',
      kb_name: 'Test KB',
      document_count: 42,
      storage_bytes: 104857600,
      total_chunks: 1250,
      total_embeddings: 1250,
      searches_30d: 285,
      generations_30d: 98,
      unique_users_30d: 12,
      top_documents: [],
      last_updated: '2025-12-03T10:15:00Z',
    };

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockStats,
    });

    const { result } = renderHook(() => useKBStats('kb-123'), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockStats);
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/admin/knowledge-bases/kb-123/stats',
      {
        credentials: 'include',
      }
    );
  });

  it('should handle 404 error when KB not found', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 404,
    });

    localStorage.setItem('token', 'test-token');

    const { result } = renderHook(() => useKBStats('invalid-kb-id'), {
      wrapper: createWrapper(),
    });

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 3000 }
    );

    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toBe('Knowledge base not found');
  });

  it('should handle 403 error when not admin', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 403,
    });

    localStorage.setItem('token', 'test-token');

    const { result } = renderHook(() => useKBStats('kb-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 3000 }
    );

    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toBe('Unauthorized: Admin access required');
  });

  it('should handle 401 error when not authenticated', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 401,
    });

    localStorage.setItem('token', 'test-token');

    const { result } = renderHook(() => useKBStats('kb-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 3000 }
    );

    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toBe('Authentication required');
  });

  it('should handle generic fetch error', async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 500,
    });

    localStorage.setItem('token', 'test-token');

    const { result } = renderHook(() => useKBStats('kb-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(
      () => {
        expect(result.current.isError).toBe(true);
      },
      { timeout: 3000 }
    );

    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toBe('Failed to fetch KB statistics');
  });
});
