/**
 * Hook for fetching observability statistics.
 *
 * Story 9-12: Observability Dashboard Widgets
 *
 * Provides React Query-based data fetching with:
 * - Configurable time period (hour, day, week, month)
 * - Auto-refresh every 30 seconds (configurable)
 * - Parallel fetching support for independent widget loading
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * LLM usage statistics from the backend.
 */
export interface LLMUsageStats {
  total_requests: number;
  total_input_tokens: number;
  total_output_tokens: number;
  avg_latency_ms: number | null;
  by_model: Record<string, { requests: number; input_tokens: number; output_tokens: number }>;
}

/**
 * Document processing metrics from the backend.
 */
export interface ProcessingMetrics {
  total_documents: number;
  total_chunks: number;
  avg_processing_time_ms: number | null;
  success_count: number;
  failure_count: number;
}

/**
 * Chat activity metrics from the backend.
 */
export interface ChatMetrics {
  total_messages: number;
  total_conversations: number;
  avg_response_time_ms: number | null;
  avg_tokens_per_response: number | null;
}

/**
 * Complete observability stats response from the backend.
 */
export interface ObservabilityStats {
  time_period: string;
  start_date: string;
  end_date: string;
  llm_usage: LLMUsageStats;
  processing_metrics: ProcessingMetrics;
  chat_metrics: ChatMetrics;
  error_rate: number;
}

/**
 * Time period options for stats filtering.
 */
export type TimePeriod = 'hour' | 'day' | 'week' | 'month';

/**
 * Hook options for customizing behavior.
 */
interface UseObservabilityStatsOptions {
  /** Time period for aggregation. Default: 'day' */
  period?: TimePeriod;
  /** Auto-refresh interval in milliseconds. Default: 30000 (30s). Set to 0 to disable. */
  refreshInterval?: number;
  /** Whether the query is enabled. Default: true */
  enabled?: boolean;
}

/**
 * Fetch observability stats from the API.
 */
async function fetchObservabilityStats(period: TimePeriod): Promise<ObservabilityStats> {
  const response = await fetch(`${API_BASE_URL}/api/v1/observability/stats?time_period=${period}`, {
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch stats' }));
    throw new Error(error.detail || 'Failed to fetch observability stats');
  }

  return response.json();
}

/**
 * Hook for fetching observability statistics.
 *
 * @example
 * ```tsx
 * const { data, isLoading, error, refetch } = useObservabilityStats({
 *   period: 'day',
 *   refreshInterval: 30000,
 * });
 * ```
 */
export function useObservabilityStats(options: UseObservabilityStatsOptions = {}) {
  const { period = 'day', refreshInterval = 30000, enabled = true } = options;

  return useQuery({
    queryKey: ['observability-stats', period],
    queryFn: () => fetchObservabilityStats(period),
    refetchInterval: refreshInterval > 0 ? refreshInterval : false,
    enabled,
    staleTime: 10000, // Consider data fresh for 10 seconds
    gcTime: 60000, // Keep in cache for 1 minute
  });
}

/**
 * Hook for manually refreshing observability stats.
 */
export function useRefreshObservabilityStats() {
  const queryClient = useQueryClient();

  return (period?: TimePeriod) => {
    if (period) {
      queryClient.invalidateQueries({ queryKey: ['observability-stats', period] });
    } else {
      queryClient.invalidateQueries({ queryKey: ['observability-stats'] });
    }
  };
}
