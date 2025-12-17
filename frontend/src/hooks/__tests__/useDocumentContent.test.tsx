/**
 * Unit tests for useDocumentContent hook
 * Story 5-26: Document Chunk Viewer Frontend
 *
 * Tests document content fetching for rendering in viewers.
 * AC-5.26.4: Content pane renders document based on type
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ReactNode } from 'react';
import { useDocumentContent } from '../useDocumentContent';

// Mock fetch
global.fetch = vi.fn();

// API base URL used by the hook (matches what hook uses when NEXT_PUBLIC_API_URL is not set)
const API_BASE_URL = 'http://localhost:8000';

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

// Mock content responses for different file types
const mockTextContentResponse = {
  text: 'This is plain text document content.\nLine 2.\nLine 3.',
  mime_type: 'text/plain',
  html: null,
};

const mockMarkdownContentResponse = {
  text: '# Heading\n\nThis is **markdown** content.\n\n- Item 1\n- Item 2',
  mime_type: 'text/markdown',
  html: null,
};

const mockDocxContentResponse = {
  text: 'This is the extracted text from DOCX document.',
  mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  html: '<p>This is the <strong>HTML</strong> content from DOCX.</p>',
};

const mockPdfContentResponse = {
  text: 'This is the extracted text from PDF document.',
  mime_type: 'application/pdf',
  html: null,
};

describe('useDocumentContent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] should fetch text document content successfully - AC-5.26.4', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockTextContentResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
          kbId: 'kb-123',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.text).toBe(mockTextContentResponse.text);
    expect(result.current.mimeType).toBe('text/plain');
    expect(result.current.html).toBeNull();
    expect(global.fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/api/v1/knowledge-bases/kb-123/documents/doc-456/full-content`,
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('[P0] should fetch markdown document content successfully - AC-5.26.4', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockMarkdownContentResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
          kbId: 'kb-123',
          documentId: 'doc-md',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.text).toContain('# Heading');
    expect(result.current.mimeType).toBe('text/markdown');
    expect(result.current.html).toBeNull();
  });

  it('[P0] should fetch DOCX document content with HTML - AC-5.26.4', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockDocxContentResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
          kbId: 'kb-123',
          documentId: 'doc-docx',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.text).toBe(mockDocxContentResponse.text);
    expect(result.current.mimeType).toContain('wordprocessingml');
    expect(result.current.html).toContain('<strong>HTML</strong>');
  });

  it('[P0] should fetch PDF document content - AC-5.26.4', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPdfContentResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
          kbId: 'kb-123',
          documentId: 'doc-pdf',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.text).toBe(mockPdfContentResponse.text);
    expect(result.current.mimeType).toBe('application/pdf');
    expect(result.current.html).toBeNull();
  });

  it('[P1] should not fetch when kbId is empty', async () => {
    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
          kbId: '',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    expect(result.current.isLoading).toBe(false);
    expect(result.current.text).toBeNull();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('[P1] should not fetch when documentId is empty', async () => {
    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
          kbId: 'kb-123',
          documentId: '',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    expect(result.current.isLoading).toBe(false);
    expect(result.current.text).toBeNull();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('[P1] should not fetch when enabled is false', async () => {
    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
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
        useDocumentContent({
          kbId: 'kb-123',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain('Failed to fetch content');
    expect(result.current.text).toBeNull();
  });

  it('[P1] should handle 403 Forbidden for unauthorized users', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
          kbId: 'kb-123',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain('Forbidden');
  });

  it('[P2] should handle network errors gracefully', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('Network error'));

    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
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
      json: async () => mockTextContentResponse,
    });

    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
          kbId: 'kb-123',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Manual refetch
    result.current.refetch();

    // Assert
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  it('[P2] should return null values before data is loaded', () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    // Act
    const { result } = renderHook(
      () =>
        useDocumentContent({
          kbId: 'kb-123',
          documentId: 'doc-456',
        }),
      { wrapper: createWrapper() }
    );

    // Assert - initial state
    expect(result.current.isLoading).toBe(true);
    expect(result.current.text).toBeNull();
    expect(result.current.mimeType).toBeNull();
    expect(result.current.html).toBeNull();
    expect(result.current.isError).toBe(false);
    expect(result.current.error).toBeNull();
  });
});
