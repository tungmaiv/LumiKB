/**
 * useDocumentContent Hook (Story 5-26)
 *
 * Fetches full document content from the backend API for rendering.
 * AC-5.26.4: Content pane renders document based on type
 */

import { useQuery } from '@tanstack/react-query';
import type { DocumentContentResponse } from '@/types/chunk';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UseDocumentContentOptions {
  /** Knowledge Base ID */
  kbId: string;
  /** Document ID */
  documentId: string;
  /** Enabled state */
  enabled?: boolean;
}

interface UseDocumentContentReturn {
  /** Document text content */
  text: string | null;
  /** MIME type of document */
  mimeType: string | null;
  /** HTML content for DOCX files */
  html: string | null;
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
 * Fetch full document content for rendering.
 *
 * Features:
 * - Returns text, mime_type, and optional HTML (for DOCX)
 * - Uses staleTime: Infinity (document content doesn't change)
 * - Caches results with React Query
 *
 * @example
 * ```tsx
 * const { text, mimeType, html, isLoading } = useDocumentContent({
 *   kbId: 'uuid',
 *   documentId: 'uuid',
 * });
 * ```
 */
export function useDocumentContent({
  kbId,
  documentId,
  enabled = true,
}: UseDocumentContentOptions): UseDocumentContentReturn {
  const query = useQuery<DocumentContentResponse>({
    queryKey: ['document-content', kbId, documentId],
    queryFn: async () => {
      const url = `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/full-content`;

      const response = await fetch(url, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch content: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: enabled && !!kbId && !!documentId,
    staleTime: Infinity, // Document content doesn't change
    gcTime: 1000 * 60 * 30, // Keep in cache for 30 minutes
  });

  return {
    text: query.data?.text ?? null,
    mimeType: query.data?.mime_type ?? null,
    html: query.data?.html ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
