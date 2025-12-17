/**
 * React Query hook for fetching document processing status.
 *
 * Story 5-23: Provides real-time visibility into document processing pipeline.
 * Auto-refreshes every 10 seconds (AC-5.23.5).
 */

import { useQuery } from '@tanstack/react-query';
import type { PaginatedDocumentProcessingResponse, ProcessingFilters } from '@/types/processing';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const REFETCH_INTERVAL = 10000; // 10 seconds (AC-5.23.5)

/**
 * Build query string from filters.
 */
function buildQueryString(filters: ProcessingFilters): string {
  const params = new URLSearchParams();

  if (filters.name) {
    params.append('name', filters.name);
  }
  if (filters.file_type) {
    params.append('file_type', filters.file_type);
  }
  if (filters.status) {
    params.append('status', filters.status);
  }
  if (filters.current_step) {
    params.append('current_step', filters.current_step);
  }
  if (filters.page !== undefined) {
    params.append('page', String(filters.page));
  }
  if (filters.page_size !== undefined) {
    params.append('page_size', String(filters.page_size));
  }
  if (filters.sort_by) {
    params.append('sort_by', filters.sort_by);
  }
  if (filters.sort_order) {
    params.append('sort_order', filters.sort_order);
  }

  return params.toString();
}

/**
 * Fetch document processing status from API.
 */
async function fetchDocumentProcessing(
  kbId: string,
  filters: ProcessingFilters
): Promise<PaginatedDocumentProcessingResponse> {
  const queryString = buildQueryString(filters);
  const url = `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/processing${
    queryString ? `?${queryString}` : ''
  }`;

  const response = await fetch(url, {
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error('WRITE permission required to view processing status');
    }
    if (response.status === 404) {
      throw new Error('Knowledge Base not found');
    }
    throw new Error(`Failed to fetch processing status: ${response.statusText}`);
  }

  return response.json();
}

export interface UseDocumentProcessingOptions {
  /** Knowledge Base ID */
  kbId: string;

  /** Filter parameters */
  filters?: ProcessingFilters;

  /** Enable auto-refresh (default: true) */
  autoRefresh?: boolean;

  /** Custom refresh interval in milliseconds (default: 10000) */
  refreshInterval?: number;

  /** Enable the query (default: true) */
  enabled?: boolean;
}

/**
 * Hook for fetching document processing status with filtering and auto-refresh.
 *
 * @param options - Hook options
 * @returns React Query result with paginated document processing status
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useDocumentProcessing({
 *   kbId: "uuid",
 *   filters: { status: "processing", page: 1, page_size: 20 },
 * });
 * ```
 */
export function useDocumentProcessing({
  kbId,
  filters = {},
  autoRefresh = true,
  refreshInterval = REFETCH_INTERVAL,
  enabled = true,
}: UseDocumentProcessingOptions) {
  return useQuery({
    queryKey: ['kb', kbId, 'processing', filters],
    queryFn: () => fetchDocumentProcessing(kbId, filters),
    refetchInterval: autoRefresh ? refreshInterval : false,
    staleTime: 5000, // Consider data stale after 5s
    enabled: enabled && !!kbId,
  });
}
