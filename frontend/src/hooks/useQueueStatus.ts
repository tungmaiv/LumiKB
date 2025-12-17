/**
 * React Query hook for fetching queue status.
 *
 * Provides auto-refresh every 10 seconds for real-time monitoring.
 * Uses React Query for caching and background refetch.
 */

import { useQuery } from '@tanstack/react-query';
import type { QueueStatus } from '@/types/queue';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const REFETCH_INTERVAL = 10000; // 10 seconds

/**
 * Fetch all queue statuses from API.
 */
async function fetchQueueStatus(): Promise<QueueStatus[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/queue/status`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch queue status: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Hook for fetching queue status with auto-refresh.
 *
 * @returns React Query result with queue status data
 */
export function useQueueStatus() {
  return useQuery({
    queryKey: ['admin', 'queue', 'status'],
    queryFn: fetchQueueStatus,
    refetchInterval: REFETCH_INTERVAL,
    staleTime: 5000, // Consider data stale after 5s (backend cache is 5min)
  });
}
