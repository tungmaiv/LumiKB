/**
 * useDocumentChunks Hook (Story 5-26)
 *
 * Fetches document chunks from the backend API with search and pagination.
 * AC-5.26.3: Chunk sidebar displays all chunks with search
 * AC-5.26.5: Search filters chunks in real-time
 */

import { useQuery } from '@tanstack/react-query';
import { useDebounce } from './useDebounce';
import type { DocumentChunksResponse } from '@/types/chunk';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UseDocumentChunksOptions {
  /** Knowledge Base ID */
  kbId: string;
  /** Document ID */
  documentId: string;
  /** Search query (optional) */
  searchQuery?: string;
  /** Pagination cursor (default: 0) */
  cursor?: number;
  /** Page size limit (default: 50, max: 100) */
  limit?: number;
  /** Enabled state */
  enabled?: boolean;
}

interface UseDocumentChunksReturn {
  /** Chunk data */
  chunks: DocumentChunksResponse['chunks'];
  /** Total count of chunks */
  total: number;
  /** Whether more chunks exist */
  hasMore: boolean;
  /** Next cursor for pagination */
  nextCursor: number | null;
  /** Loading state */
  isLoading: boolean;
  /** Error state */
  isError: boolean;
  /** Error object */
  error: Error | null;
  /** Refetch function */
  refetch: () => void;
}

/**
 * Fetch document chunks with optional search and pagination.
 *
 * Features:
 * - Automatic search debouncing (300ms)
 * - Cursor-based pagination
 * - Caches results with React Query
 *
 * @example
 * ```tsx
 * const { chunks, total, isLoading } = useDocumentChunks({
 *   kbId: 'uuid',
 *   documentId: 'uuid',
 *   searchQuery: 'authentication',
 * });
 * ```
 */
export function useDocumentChunks({
  kbId,
  documentId,
  searchQuery = '',
  cursor = 0,
  limit = 50,
  enabled = true,
}: UseDocumentChunksOptions): UseDocumentChunksReturn {
  // Debounce search query by 300ms (AC-5.26.5)
  const debouncedSearch = useDebounce(searchQuery, 300);

  const query = useQuery<DocumentChunksResponse>({
    queryKey: ['document-chunks', kbId, documentId, debouncedSearch, cursor, limit],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set('cursor', cursor.toString());
      params.set('limit', limit.toString());
      if (debouncedSearch) {
        params.set('search', debouncedSearch);
      }

      const response = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/chunks?${params}`,
        {
          credentials: 'include',
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch chunks: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: enabled && !!kbId && !!documentId,
    staleTime: 30000, // Cache for 30 seconds
  });

  return {
    chunks: query.data?.chunks ?? [],
    total: query.data?.total ?? 0,
    hasMore: query.data?.has_more ?? false,
    nextCursor: query.data?.next_cursor ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
