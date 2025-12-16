/**
 * Document Timeline Hook
 *
 * Story 9-10: Document Timeline UI
 * AC9: Responsive design with polling for in-progress documents
 *
 * Uses TanStack Query with conditional refetchInterval for real-time updates.
 */
import { useQuery } from '@tanstack/react-query';

import type { DocumentEventItem } from '@/components/admin/documents/timeline-step';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface DocumentTimelineResponse {
  document_id: string;
  events: DocumentEventItem[];
  total_duration_ms: number | null;
}

async function fetchDocumentTimeline(documentId: string): Promise<DocumentTimelineResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/observability/documents/${documentId}/timeline`, {
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('No processing events found for this document');
    }
    throw new Error(`Failed to fetch document timeline: ${response.statusText}`);
  }

  return response.json();
}

function isProcessing(events: DocumentEventItem[]): boolean {
  if (events.length === 0) return false;
  const lastEvent = events[events.length - 1];
  return lastEvent?.status === 'started' || lastEvent?.status === 'in_progress';
}

export function useDocumentTimeline(documentId: string | null, enabled = true) {
  return useQuery({
    queryKey: ['document-timeline', documentId],
    queryFn: () => fetchDocumentTimeline(documentId!),
    enabled: enabled && !!documentId,
    staleTime: 5000, // Consider data stale after 5 seconds
    refetchInterval: (query) => {
      // Poll every 2 seconds if still processing
      const events = query.state.data?.events || [];
      return isProcessing(events) ? 2000 : false;
    },
  });
}
