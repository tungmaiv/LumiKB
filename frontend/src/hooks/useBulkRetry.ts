/**
 * React Query hook for bulk retry operations (Story 7-27).
 *
 * Provides mutation for retrying failed documents in bulk.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { BulkRetryRequest, BulkRetryResponse } from '@/types/queue';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Bulk retry failed documents.
 *
 * @param request - Bulk retry request with document_ids or retry_all_failed flag
 */
async function bulkRetryFailed(request: BulkRetryRequest): Promise<BulkRetryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/queue/retry-failed`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to retry documents: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Hook for bulk retry operations.
 *
 * @returns React Query mutation for bulk retry
 */
export function useBulkRetry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: bulkRetryFailed,
    onSuccess: () => {
      // Invalidate queue-related queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['admin', 'queue'] });
    },
  });
}
