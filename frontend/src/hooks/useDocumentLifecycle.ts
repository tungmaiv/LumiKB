/**
 * Hook for document lifecycle operations (archive, clear, replace)
 * Story 6-8: Document List Archive/Clear Actions UI
 * Story 6-9: Duplicate Upload & Replace UI
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Extract error message from API response detail field.
 * Handles both string and nested object formats:
 * - String: "Error message"
 * - Object: { error: { code: "...", message: "...", details: {...} } }
 */
function extractErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') {
    return detail;
  }
  if (detail && typeof detail === 'object') {
    const errorObj = detail as { error?: { message?: string } };
    if (errorObj.error?.message) {
      return errorObj.error.message;
    }
  }
  return fallback;
}

export interface ArchiveDocumentResponse {
  id: string;
  message: string;
  archived_at: string;
}

export interface ClearDocumentResponse {
  id: string;
  message: string;
}

export interface ReplaceDocumentResponse {
  id: string;
  message: string;
  version_number: number;
}

/**
 * Hook for document lifecycle operations
 */
export function useDocumentLifecycle(kbId: string) {
  const queryClient = useQueryClient();

  /**
   * Archive a completed document (soft delete)
   */
  const archiveDocument = useMutation({
    mutationFn: async (documentId: string): Promise<ArchiveDocumentResponse> => {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/archive`,
        {
          method: 'POST',
          credentials: 'include',
        }
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(extractErrorMessage(errorData.detail, 'Failed to archive document'));
      }

      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', kbId] });
      queryClient.invalidateQueries({ queryKey: ['kb-archived-documents', kbId] });
      toast.success('Document archived');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to archive document');
    },
  });

  /**
   * Clear a failed document (permanent delete)
   */
  const clearDocument = useMutation({
    mutationFn: async (documentId: string): Promise<ClearDocumentResponse> => {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/clear`,
        {
          method: 'DELETE',
          credentials: 'include',
        }
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(extractErrorMessage(errorData.detail, 'Failed to clear document'));
      }

      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', kbId] });
      toast.success('Failed document cleared');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to clear document');
    },
  });

  /**
   * Replace an existing document with a new file
   */
  const replaceDocument = useMutation({
    mutationFn: async ({
      documentId,
      file,
    }: {
      documentId: string;
      file: File;
    }): Promise<ReplaceDocumentResponse> => {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(
        `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/replace`,
        {
          method: 'POST',
          credentials: 'include',
          body: formData,
        }
      );

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(extractErrorMessage(errorData.detail, 'Failed to replace document'));
      }

      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', kbId] });
      toast.success('Document replaced and queued for processing');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to replace document');
    },
  });

  return {
    archiveDocument,
    clearDocument,
    replaceDocument,
  };
}
