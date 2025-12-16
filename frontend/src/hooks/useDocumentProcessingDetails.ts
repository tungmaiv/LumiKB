/**
 * React Query hook for fetching detailed processing status for a single document.
 *
 * Story 5-23 (AC-5.23.3): Provides step-by-step processing details with timing
 * and error information.
 */

import { useQuery } from "@tanstack/react-query";
import type { DocumentProcessingDetails } from "@/types/processing";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const REFETCH_INTERVAL = 5000; // 5 seconds for active processing

/**
 * Fetch document processing details from API.
 */
async function fetchDocumentProcessingDetails(
  kbId: string,
  docId: string
): Promise<DocumentProcessingDetails> {
  const url = `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/processing/${docId}`;

  const response = await fetch(url, {
    credentials: "include",
  });

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error("WRITE permission required to view processing details");
    }
    if (response.status === 404) {
      throw new Error("Document not found");
    }
    throw new Error(
      `Failed to fetch processing details: ${response.statusText}`
    );
  }

  return response.json();
}

export interface UseDocumentProcessingDetailsOptions {
  /** Knowledge Base ID */
  kbId: string;

  /** Document ID */
  docId: string;

  /** Enable auto-refresh for active processing (default: true) */
  autoRefresh?: boolean;

  /** Custom refresh interval in milliseconds (default: 5000) */
  refreshInterval?: number;

  /** Enable the query (default: true) */
  enabled?: boolean;
}

/**
 * Hook for fetching detailed processing status for a single document.
 *
 * @param options - Hook options
 * @returns React Query result with document processing details
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useDocumentProcessingDetails({
 *   kbId: "kb-uuid",
 *   docId: "doc-uuid",
 * });
 *
 * if (data) {
 *   console.log(data.steps); // Step-by-step processing info
 *   console.log(data.total_duration_ms); // Total processing time
 * }
 * ```
 */
export function useDocumentProcessingDetails({
  kbId,
  docId,
  autoRefresh = true,
  refreshInterval = REFETCH_INTERVAL,
  enabled = true,
}: UseDocumentProcessingDetailsOptions) {
  return useQuery({
    queryKey: ["kb", kbId, "processing", docId, "details"],
    queryFn: () => fetchDocumentProcessingDetails(kbId, docId),
    refetchInterval: autoRefresh ? refreshInterval : false,
    staleTime: 2000, // Consider data stale after 2s
    enabled: enabled && !!kbId && !!docId,
  });
}
