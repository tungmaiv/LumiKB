/**
 * Hook Tests: useMarkdownContent
 *
 * Story: 7-30 Enhanced Markdown Viewer
 * Coverage: Fetch markdown content, 404 handling, loading states, error handling
 *
 * Test Count: 6 tests
 * Priority: P1 (4), P2 (2)
 *
 * Test Framework: Vitest
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { useMarkdownContent } from '../useMarkdownContent';

// Mock fetch globally
global.fetch = vi.fn();

// Create wrapper with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('useMarkdownContent Hook', () => {
  const mockKbId = 'kb-test-123';
  const mockDocumentId = 'doc-test-456';

  const mockMarkdownResponse = {
    document_id: mockDocumentId,
    markdown_content: '# Test Document\n\nThis is markdown content.',
    generated_at: '2025-12-11T10:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('[P1] should fetch markdown content successfully', async () => {
    // GIVEN: API returns successful markdown response
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockMarkdownResponse),
    });

    // WHEN: Hook is rendered with valid parameters
    const { result } = renderHook(
      () => useMarkdownContent({ kbId: mockKbId, documentId: mockDocumentId }),
      { wrapper: createWrapper() }
    );

    // THEN: Initially loading
    expect(result.current.isLoading).toBe(true);

    // THEN: After fetch completes, data is available
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockMarkdownResponse);
    expect(result.current.isError).toBe(false);

    // THEN: Correct endpoint was called
    expect(global.fetch).toHaveBeenCalledWith(
      `http://localhost:8000/api/v1/knowledge-bases/${mockKbId}/documents/${mockDocumentId}/markdown-content`,
      { credentials: 'include' }
    );
  });

  it('[P1] should handle 404 gracefully by returning null', async () => {
    // GIVEN: API returns 404 (markdown not available)
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    // WHEN: Hook is rendered
    const { result } = renderHook(
      () => useMarkdownContent({ kbId: mockKbId, documentId: mockDocumentId }),
      { wrapper: createWrapper() }
    );

    // THEN: After fetch completes, data is null (not an error)
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBeNull();
    expect(result.current.isError).toBe(false);
  });

  it('[P1] should handle API errors (non-404) as errors', async () => {
    // GIVEN: API returns 500 error
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });

    // WHEN: Hook is rendered
    const { result } = renderHook(
      () => useMarkdownContent({ kbId: mockKbId, documentId: mockDocumentId }),
      { wrapper: createWrapper() }
    );

    // THEN: After fetch completes, error state is set
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isError).toBe(true);
    expect(result.current.error).toBeInstanceOf(Error);
    expect((result.current.error as Error).message).toContain('Failed to fetch markdown content');
  });

  it('[P1] should not fetch when disabled', async () => {
    // GIVEN: Hook is rendered with enabled=false
    const { result } = renderHook(
      () =>
        useMarkdownContent({
          kbId: mockKbId,
          documentId: mockDocumentId,
          enabled: false,
        }),
      { wrapper: createWrapper() }
    );

    // THEN: Fetch is not called
    expect(global.fetch).not.toHaveBeenCalled();

    // THEN: Data is undefined (not fetched)
    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });

  it('[P2] should not fetch when kbId is empty', async () => {
    // GIVEN: Hook is rendered with empty kbId
    const { result } = renderHook(
      () =>
        useMarkdownContent({
          kbId: '',
          documentId: mockDocumentId,
        }),
      { wrapper: createWrapper() }
    );

    // THEN: Fetch is not called
    expect(global.fetch).not.toHaveBeenCalled();
    expect(result.current.isLoading).toBe(false);
  });

  it('[P2] should not fetch when documentId is empty', async () => {
    // GIVEN: Hook is rendered with empty documentId
    const { result } = renderHook(
      () =>
        useMarkdownContent({
          kbId: mockKbId,
          documentId: '',
        }),
      { wrapper: createWrapper() }
    );

    // THEN: Fetch is not called
    expect(global.fetch).not.toHaveBeenCalled();
    expect(result.current.isLoading).toBe(false);
  });

  it('[P2] should handle network errors gracefully', async () => {
    // GIVEN: Network error occurs
    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Network error')
    );

    // WHEN: Hook is rendered
    const { result } = renderHook(
      () => useMarkdownContent({ kbId: mockKbId, documentId: mockDocumentId }),
      { wrapper: createWrapper() }
    );

    // THEN: After fetch fails, error state is set
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isError).toBe(true);
    expect(result.current.error).toBeInstanceOf(Error);
  });
});
