/**
 * Hook for fetching and managing archived documents
 * Story 6-7: Archive Management UI
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import type {
  ArchivedDocumentsFilter,
  PaginatedArchivedDocumentsResponse,
  RestoreDocumentResponse,
  PurgeDocumentResponse,
  BulkPurgeResponse,
} from '@/types/archive';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UseArchivedDocumentsOptions {
  filters: ArchivedDocumentsFilter;
  enabled?: boolean;
}

/**
 * Fetch paginated archived documents with filtering
 */
export function useArchivedDocuments({
  filters,
  enabled = true,
}: UseArchivedDocumentsOptions) {
  return useQuery({
    queryKey: ['archived-documents', filters],
    queryFn: async (): Promise<PaginatedArchivedDocumentsResponse> => {
      const params = new URLSearchParams();

      if (filters.kb_id) {
        params.set('kb_id', filters.kb_id);
      }
      if (filters.search) {
        params.set('search', filters.search);
      }
      if (filters.page !== undefined) {
        params.set('page', String(filters.page));
      }
      if (filters.page_size !== undefined) {
        params.set('page_size', String(filters.page_size));
      }

      const url = `${API_BASE_URL}/api/v1/admin/archived-documents${params.toString() ? `?${params.toString()}` : ''}`;

      const res = await fetch(url, {
        method: 'GET',
        credentials: 'include',
      });

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('Unauthorized: Admin access required');
        }
        if (res.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error(`Failed to fetch archived documents: ${res.statusText}`);
      }

      return res.json();
    },
    enabled,
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: false,
  });
}

/**
 * Restore a single archived document
 */
export function useRestoreDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      kbId,
      documentId,
    }: {
      kbId: string;
      documentId: string;
    }): Promise<RestoreDocumentResponse> => {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/restore`,
        {
          method: 'POST',
          credentials: 'include',
        }
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));

        // Handle name collision (409)
        if (res.status === 409) {
          const error = new Error(errorData.detail || 'Document name conflict') as Error & {
            status: number;
            conflictingDocumentId?: string;
          };
          error.status = 409;
          error.conflictingDocumentId = errorData.conflicting_document_id;
          throw error;
        }

        throw new Error(errorData.detail || 'Failed to restore document');
      }

      return res.json();
    },
    onSuccess: () => {
      // Invalidate archived documents list
      queryClient.invalidateQueries({ queryKey: ['archived-documents'] });
      // Invalidate documents list as document is now active
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Document restored successfully');
    },
    onError: (error: Error & { status?: number }) => {
      if (error.status === 409) {
        // Don't show toast for name collision - let UI handle it
        return;
      }
      toast.error(error.message || 'Failed to restore document');
    },
  });
}

/**
 * Purge (permanently delete) a single archived document
 */
export function usePurgeDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      kbId,
      documentId,
    }: {
      kbId: string;
      documentId: string;
    }): Promise<PurgeDocumentResponse> => {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/purge`,
        {
          method: 'DELETE',
          credentials: 'include',
        }
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Failed to purge document');
      }

      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['archived-documents'] });
      toast.success('Document permanently deleted');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to purge document');
    },
  });
}

/**
 * Bulk purge multiple archived documents
 */
export function useBulkPurge() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      kbId,
      documentIds,
    }: {
      kbId: string;
      documentIds: string[];
    }): Promise<BulkPurgeResponse> => {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/bulk-purge`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ document_ids: documentIds }),
        }
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Failed to purge documents');
      }

      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['archived-documents'] });

      if (data.skipped_ids.length > 0) {
        toast.warning(
          `Purged ${data.purged_count} documents. ${data.skipped_ids.length} skipped (not archived).`
        );
      } else {
        toast.success(`${data.purged_count} documents permanently deleted`);
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to purge documents');
    },
  });
}
