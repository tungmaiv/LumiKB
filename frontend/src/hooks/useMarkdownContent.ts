/**
 * useMarkdownContent Hook (Story 7-30)
 *
 * Fetches markdown content for a document from the API.
 * AC-7.30.1: Fetch markdown content from /markdown-content endpoint
 * AC-7.30.4: Handle 404 gracefully (markdown not available)
 * AC-7.30.5: Handle loading state
 */

import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface MarkdownContentResponse {
  document_id: string;
  markdown_content: string;
  generated_at: string;
}

export interface UseMarkdownContentOptions {
  kbId: string;
  documentId: string;
  enabled?: boolean;
}

/**
 * Hook to fetch markdown content for a document.
 *
 * Returns:
 * - data: MarkdownContentResponse if available, null if 404
 * - isLoading: true while fetching
 * - isError: true if fetch failed (not 404)
 * - error: Error object if fetch failed
 *
 * @example
 * const { data, isLoading, isError } = useMarkdownContent({
 *   kbId: 'kb-123',
 *   documentId: 'doc-456',
 *   enabled: true,
 * });
 *
 * if (data) {
 *   // Markdown available, render enhanced viewer
 * } else {
 *   // Fallback to original viewer
 * }
 */
export function useMarkdownContent({
  kbId,
  documentId,
  enabled = true,
}: UseMarkdownContentOptions) {
  return useQuery<MarkdownContentResponse | null>({
    queryKey: ['markdown-content', kbId, documentId],
    queryFn: async (): Promise<MarkdownContentResponse | null> => {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/markdown-content`,
        { credentials: 'include' }
      );

      // 404 means markdown not available - return null (not an error)
      if (response.status === 404) {
        return null;
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch markdown content: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: enabled && !!kbId && !!documentId,
    staleTime: Infinity, // Markdown content is immutable once generated
    gcTime: 30 * 60 * 1000, // Keep in cache for 30 minutes
    retry: false, // Don't retry 404s or errors
  });
}
