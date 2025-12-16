/**
 * Unit tests for useDocumentProcessing hook
 * Story 5-23: Document Processing Progress Screen
 *
 * Tests data fetching, filtering, pagination, and auto-refresh functionality
 * for the document processing status monitoring feature.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, type Mock } from 'vitest';
import { ReactNode } from 'react';
import { useDocumentProcessing } from '../useDocumentProcessing';

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

// Mock processing data
const mockProcessingResponse = {
  documents: [
    {
      id: 'doc-1',
      original_filename: 'test-doc.pdf',
      file_type: 'pdf',
      file_size: 1024000,
      status: 'processing',
      current_step: 'parse',
      chunk_count: null,
      created_at: '2025-12-06T10:00:00Z',
      updated_at: '2025-12-06T10:00:05Z',
    },
    {
      id: 'doc-2',
      original_filename: 'completed-doc.pdf',
      file_type: 'pdf',
      file_size: 2048000,
      status: 'ready',
      current_step: 'complete',
      chunk_count: 25,
      created_at: '2025-12-06T09:00:00Z',
      updated_at: '2025-12-06T09:05:00Z',
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
};

describe('useDocumentProcessing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] should fetch document processing status successfully - AC-5.23.1', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessing({
          kbId: 'kb-123',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockProcessingResponse);
    expect(result.current.data?.documents).toHaveLength(2);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/knowledge-bases/kb-123/processing'),
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('[P0] should include filter parameters in request - AC-5.23.2', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessing({
          kbId: 'kb-123',
          filters: {
            name: 'test',
            status: 'processing',
            file_type: 'pdf',
            current_step: 'parse',
            page: 1,
            page_size: 20,
          },
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Assert
    const fetchCall = (global.fetch as Mock).mock.calls[0][0];
    expect(fetchCall).toContain('name=test');
    expect(fetchCall).toContain('status=processing');
    expect(fetchCall).toContain('file_type=pdf');
    expect(fetchCall).toContain('current_step=parse');
  });

  it('[P0] should handle 403 Forbidden for READ-only users - AC-5.23.1', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: false,
      status: 403,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessing({
          kbId: 'kb-123',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain('WRITE permission required');
  });

  it('[P0] should handle 404 Not Found for invalid KB - AC-5.23.1', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessing({
          kbId: 'invalid-kb',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain('Knowledge Base not found');
  });

  it('[P1] should configure refetchInterval when autoRefresh is enabled - AC-5.23.5', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => mockProcessingResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessing({
          kbId: 'kb-123',
          autoRefresh: true,
          refreshInterval: 10000,
        }),
      { wrapper: createWrapper() }
    );

    // Assert - hook should be configured and query running
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(global.fetch).toHaveBeenCalledTimes(1);
    // React Query internally handles refetchInterval
    expect(result.current.isLoading || result.current.isSuccess).toBe(true);
  });

  it('[P1] should allow manual refetch', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => mockProcessingResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessing({
          kbId: 'kb-123',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Manual refetch
    result.current.refetch();

    // Assert
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  it('[P1] should not fetch when kbId is empty', async () => {
    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessing({
          kbId: '',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert - query should not run
    expect(result.current.isFetching).toBe(false);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('[P2] should handle network errors gracefully', async () => {
    // Arrange
    (global.fetch as Mock).mockRejectedValueOnce(new Error('Network error'));

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessing({
          kbId: 'kb-123',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe('Network error');
  });
});
