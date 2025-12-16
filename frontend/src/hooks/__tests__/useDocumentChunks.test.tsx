/**
 * Unit tests for useDocumentChunks hook
 * Story 5-26: Document Chunk Viewer Frontend
 *
 * Tests data fetching, search, and pagination functionality.
 * AC-5.26.3: Chunk sidebar displays all chunks with search
 * AC-5.26.5: Search filters chunks in real-time
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ReactNode } from 'react';
import { useDocumentChunks } from '../useDocumentChunks';

// Mock the useDebounce hook to return value immediately
vi.mock('../useDebounce', () => ({
  useDebounce: vi.fn((value: string) => value),
}));

// Mock fetch
global.fetch = vi.fn();

function TestWrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

const createWrapper = () => TestWrapper;

// Mock chunk data
const mockChunksResponse = {
  chunks: [
    {
      chunk_id: 'chunk-1',
      chunk_index: 0,
      text: 'This is the first chunk of text content.',
      char_start: 0,
      char_end: 40,
      page_number: 1,
      section_header: 'Introduction',
      score: null,
    },
    {
      chunk_id: 'chunk-2',
      chunk_index: 1,
      text: 'This is the second chunk of text content.',
      char_start: 41,
      char_end: 82,
      page_number: 1,
      section_header: 'Introduction',
      score: null,
    },
    {
      chunk_id: 'chunk-3',
      chunk_index: 2,
      text: 'This is the third chunk with different content.',
      char_start: 83,
      char_end: 130,
      page_number: 2,
      section_header: 'Methods',
      score: null,
    },
  ],
  total: 10,
  has_more: true,
  next_cursor: 3,
};

const mockSearchResponse = {
  chunks: [
    {
      chunk_id: 'chunk-1',
      chunk_index: 0,
      text: 'This is the first chunk of text content.',
      char_start: 0,
      char_end: 40,
      page_number: 1,
      section_header: 'Introduction',
      score: 0.95,
    },
  ],
  total: 1,
  has_more: false,
  next_cursor: null,
};

describe('useDocumentChunks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('[P0] should fetch document chunks successfully - AC-5.26.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockChunksResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentChunks({
          kbId: 'kb-123',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    // Wait for the fetch to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Assert
    expect(result.current.chunks).toHaveLength(3);
    expect(result.current.total).toBe(10);
    expect(result.current.hasMore).toBe(true);
    expect(result.current.nextCursor).toBe(3);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/knowledge-bases/kb-123/documents/doc-456/chunks'),
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('[P0] should include pagination parameters in request - AC-5.26.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockChunksResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentChunks({
          kbId: 'kb-123',
          documentId: 'doc-456',
          cursor: 50,
          limit: 25,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Assert
    const fetchCall = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][0];
    expect(fetchCall).toContain('cursor=50');
    expect(fetchCall).toContain('limit=25');
  });

  it('[P0] should include search parameter when searchQuery provided - AC-5.26.5', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSearchResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentChunks({
          kbId: 'kb-123',
          documentId: 'doc-456',
          searchQuery: 'authentication',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Assert
    const fetchCall = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0][0];
    expect(fetchCall).toContain('search=authentication');
  });

  it('[P0] should return search results with scores - AC-5.26.5', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockSearchResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentChunks({
          kbId: 'kb-123',
          documentId: 'doc-456',
          searchQuery: 'first',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Assert
    expect(result.current.chunks).toHaveLength(1);
    expect(result.current.chunks[0].score).toBe(0.95);
    expect(result.current.total).toBe(1);
    expect(result.current.hasMore).toBe(false);
  });

  it('[P1] should not fetch when kbId is empty', async () => {
    // Act
    const { result } = renderHook(
      () =>
        useDocumentChunks({
          kbId: '',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    expect(result.current.isLoading).toBe(false);
    expect(result.current.chunks).toEqual([]);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('[P1] should not fetch when documentId is empty', async () => {
    // Act
    const { result } = renderHook(
      () =>
        useDocumentChunks({
          kbId: 'kb-123',
          documentId: '',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    expect(result.current.isLoading).toBe(false);
    expect(result.current.chunks).toEqual([]);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('[P1] should not fetch when enabled is false', async () => {
    // Act
    const { result } = renderHook(
      () =>
        useDocumentChunks({
          kbId: 'kb-123',
          documentId: 'doc-456',
          enabled: false,
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    expect(result.current.isLoading).toBe(false);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('[P1] should handle API errors', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      statusText: 'Not Found',
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentChunks({
          kbId: 'kb-123',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain('Failed to fetch chunks');
    expect(result.current.chunks).toEqual([]);
  });

  it('[P2] should handle network errors gracefully', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Network error')
    );

    // Act
    const { result } = renderHook(
      () =>
        useDocumentChunks({
          kbId: 'kb-123',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe('Network error');
  });

  it('[P2] should allow manual refetch', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => mockChunksResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentChunks({
          kbId: 'kb-123',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Manual refetch
    await act(async () => {
      result.current.refetch();
    });

    // Assert
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });
});
