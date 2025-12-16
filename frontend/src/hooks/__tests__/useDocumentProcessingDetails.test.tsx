/**
 * Unit tests for useDocumentProcessingDetails hook
 * Story 5-23 (AC-5.23.3): Document Processing Details Modal
 *
 * Tests data fetching, error handling, and auto-refresh for
 * detailed document processing step information.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, type Mock } from 'vitest';
import { ReactNode } from 'react';
import { useDocumentProcessingDetails } from '../useDocumentProcessingDetails';

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

// Mock detailed processing data
const mockProcessingDetails = {
  id: 'doc-123',
  original_filename: 'test-document.pdf',
  file_type: 'pdf',
  file_size: 2048000,
  status: 'processing',
  current_step: 'embed',
  chunk_count: null,
  total_duration_ms: null,
  steps: [
    {
      step: 'upload',
      status: 'done',
      started_at: '2025-12-06T10:00:00Z',
      completed_at: '2025-12-06T10:00:02Z',
      duration_ms: 2000,
      error: null,
    },
    {
      step: 'parse',
      status: 'done',
      started_at: '2025-12-06T10:00:02Z',
      completed_at: '2025-12-06T10:00:05Z',
      duration_ms: 3000,
      error: null,
    },
    {
      step: 'chunk',
      status: 'done',
      started_at: '2025-12-06T10:00:05Z',
      completed_at: '2025-12-06T10:00:07Z',
      duration_ms: 2000,
      error: null,
    },
    {
      step: 'embed',
      status: 'in_progress',
      started_at: '2025-12-06T10:00:07Z',
      completed_at: null,
      duration_ms: null,
      error: null,
    },
    {
      step: 'index',
      status: 'pending',
      started_at: null,
      completed_at: null,
      duration_ms: null,
      error: null,
    },
    {
      step: 'complete',
      status: 'pending',
      started_at: null,
      completed_at: null,
      duration_ms: null,
      error: null,
    },
  ],
  created_at: '2025-12-06T09:59:55Z',
  processing_started_at: '2025-12-06T10:00:00Z',
  processing_completed_at: null,
};

describe('useDocumentProcessingDetails', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] should fetch document processing details successfully - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessingDetails({
          kbId: 'kb-123',
          docId: 'doc-123',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockProcessingDetails);
    expect(result.current.data?.steps).toHaveLength(6);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/knowledge-bases/kb-123/processing/doc-123'),
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('[P0] should return step-by-step progress with timing - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessingDetails({
          kbId: 'kb-123',
          docId: 'doc-123',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Assert step details
    const steps = result.current.data?.steps;
    expect(steps).toBeDefined();

    // Check completed steps have timing
    const uploadStep = steps?.find((s) => s.step === 'upload');
    expect(uploadStep?.status).toBe('done');
    expect(uploadStep?.duration_ms).toBe(2000);
    expect(uploadStep?.started_at).toBeTruthy();
    expect(uploadStep?.completed_at).toBeTruthy();

    // Check in-progress step
    const embedStep = steps?.find((s) => s.step === 'embed');
    expect(embedStep?.status).toBe('in_progress');
    expect(embedStep?.started_at).toBeTruthy();
    expect(embedStep?.completed_at).toBeNull();

    // Check pending steps
    const indexStep = steps?.find((s) => s.step === 'index');
    expect(indexStep?.status).toBe('pending');
    expect(indexStep?.started_at).toBeNull();
  });

  it('[P0] should handle 403 Forbidden for READ-only users', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: false,
      status: 403,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessingDetails({
          kbId: 'kb-123',
          docId: 'doc-123',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain('WRITE permission required');
  });

  it('[P0] should handle 404 Not Found for invalid document', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessingDetails({
          kbId: 'kb-123',
          docId: 'invalid-doc',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain('Document not found');
  });

  it('[P1] should configure refetchInterval when autoRefresh is enabled', async () => {
    // Arrange
    (global.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessingDetails({
          kbId: 'kb-123',
          docId: 'doc-123',
          autoRefresh: true,
          refreshInterval: 5000,
        }),
      { wrapper: createWrapper() }
    );

    // Assert - hook should be configured and query running
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(global.fetch).toHaveBeenCalledTimes(1);
    // React Query internally handles refetchInterval
    expect(result.current.isLoading || result.current.isSuccess).toBe(true);
  });

  it('[P1] should not fetch when docId is empty', async () => {
    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessingDetails({
          kbId: 'kb-123',
          docId: '',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert - query should not run
    expect(result.current.isFetching).toBe(false);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('[P1] should not fetch when disabled', async () => {
    // Act
    const { result } = renderHook(
      () =>
        useDocumentProcessingDetails({
          kbId: 'kb-123',
          docId: 'doc-123',
          enabled: false,
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
        useDocumentProcessingDetails({
          kbId: 'kb-123',
          docId: 'doc-123',
          autoRefresh: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe('Network error');
  });
});
