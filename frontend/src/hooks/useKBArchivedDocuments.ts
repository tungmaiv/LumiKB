/**
 * Hook for fetching KB-specific archived documents
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ArchivedDocumentItem {
  id: string;
  name: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  chunk_count: number;
  archived_at: string;
  created_at: string;
  tags: string[];
  uploader_email: string | null;
}

export interface PaginatedArchivedDocumentsResponse {
  data: ArchivedDocumentItem[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface UseKBArchivedDocumentsOptions {
  kbId: string;
  search?: string;
  page?: number;
  pageSize?: number;
  enabled?: boolean;
}

/**
 * Extract error message from API response detail field.
 */
function extractErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') {
    return detail;
  }
  if (detail && typeof detail === 'object') {
    const errorObj = detail as { error?: { message?: string }; message?: string };
    if (errorObj.error?.message) {
      return errorObj.error.message;
    }
    if (errorObj.message) {
      return errorObj.message;
    }
  }
  return fallback;
}

/**
 * Fetch archived documents for a specific KB
 */
export function useKBArchivedDocuments({
  kbId,
  search,
  page = 1,
  pageSize = 20,
  enabled = true,
}: UseKBArchivedDocumentsOptions) {
  return useQuery({
    queryKey: ['kb-archived-documents', kbId, { search, page, pageSize }],
    queryFn: async (): Promise<PaginatedArchivedDocumentsResponse> => {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      params.set('page', String(page));
      params.set('page_size', String(pageSize));

      const url = `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/archived?${params.toString()}`;

      const res = await fetch(url, {
        method: 'GET',
        credentials: 'include',
      });

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('Permission denied: WRITE access required');
        }
        throw new Error(`Failed to fetch archived documents: ${res.statusText}`);
      }

      return res.json();
    },
    enabled: enabled && !!kbId,
    staleTime: 30 * 1000,
  });
}

/**
 * Restore an archived document
 */
export function useRestoreArchivedDocument(kbId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId: string) => {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/restore`,
        {
          method: 'POST',
          credentials: 'include',
        }
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(extractErrorMessage(errorData.detail, 'Failed to restore document'));
      }

      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb-archived-documents', kbId] });
      queryClient.invalidateQueries({ queryKey: ['documents', kbId] });
      toast.success('Document restored');
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

/**
 * Permanently delete (purge) an archived document
 */
export function usePurgeArchivedDocument(kbId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId: string) => {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/purge`,
        {
          method: 'DELETE',
          credentials: 'include',
        }
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(extractErrorMessage(errorData.detail, 'Failed to purge document'));
      }

      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb-archived-documents', kbId] });
      toast.success('Document permanently deleted');
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
