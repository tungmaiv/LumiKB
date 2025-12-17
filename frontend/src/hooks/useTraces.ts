/**
 * Custom hooks for trace data fetching
 *
 * Story 9-8: Trace Viewer UI Component
 */
import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types matching backend schema
export interface TraceListItem {
  trace_id: string;
  name: string;
  status: string;
  user_id: string | null;
  kb_id: string | null;
  document_id: string | null;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  span_count: number;
}

export interface TraceListResponse {
  items: TraceListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface SpanDetail {
  span_id: string;
  parent_span_id: string | null;
  name: string;
  span_type: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  model: string | null;
  error_message: string | null;
  metadata: Record<string, unknown> | null;
}

export interface TraceDetailResponse {
  trace_id: string;
  name: string;
  status: string;
  user_id: string | null;
  kb_id: string | null;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  metadata: Record<string, unknown> | null;
  spans: SpanDetail[];
}

export interface UseTracesOptions {
  operation_type?: string;
  status?: string;
  user_id?: string;
  kb_id?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

/**
 * Fetch list of traces with filters and pagination
 */
export function useTraces(options: UseTracesOptions = {}) {
  return useQuery({
    queryKey: ['traces', options],
    queryFn: async (): Promise<TraceListResponse> => {
      const params = new URLSearchParams();

      if (options.operation_type) params.set('operation_type', options.operation_type);
      if (options.status) params.set('status', options.status);
      if (options.user_id) params.set('user_id', options.user_id);
      if (options.kb_id) params.set('kb_id', options.kb_id);
      if (options.start_date) params.set('start_date', options.start_date);
      if (options.end_date) params.set('end_date', options.end_date);
      if (options.search) params.set('search', options.search);
      if (options.skip !== undefined) params.set('skip', options.skip.toString());
      if (options.limit !== undefined) params.set('limit', options.limit.toString());

      const res = await fetch(`${API_BASE_URL}/api/v1/observability/traces?${params.toString()}`, {
        credentials: 'include',
      });

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('Unauthorized: Admin access required');
        }
        if (res.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error('Failed to fetch traces');
      }

      return res.json();
    },
    staleTime: 30_000, // 30 seconds
    refetchInterval: 30_000, // Auto-refresh every 30 seconds
    retry: 1,
  });
}

/**
 * Fetch detailed trace with all spans
 */
export function useTraceDetail(traceId: string | null) {
  return useQuery({
    queryKey: ['trace', traceId],
    queryFn: async (): Promise<TraceDetailResponse> => {
      if (!traceId) throw new Error('Trace ID required');

      const res = await fetch(`${API_BASE_URL}/api/v1/observability/traces/${traceId}`, {
        credentials: 'include',
      });

      if (!res.ok) {
        if (res.status === 404) {
          throw new Error('Trace not found');
        }
        if (res.status === 403) {
          throw new Error('Unauthorized: Admin access required');
        }
        if (res.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error('Failed to fetch trace detail');
      }

      return res.json();
    },
    enabled: !!traceId,
    staleTime: 60_000, // 1 minute
    retry: 1,
  });
}
