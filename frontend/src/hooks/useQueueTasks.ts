/**
 * React Query hook for fetching task details for a specific queue.
 *
 * Used in TaskListModal to display active tasks.
 * Story 7-27: Extended with document_status filter support.
 */

import { useQuery } from '@tanstack/react-query';
import type { TaskInfo, TaskInfoWithSteps, DocumentStatusFilter } from '@/types/queue';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Fetch task details for a specific queue.
 *
 * @param queueName - Queue name (e.g., "document_processing")
 * @param documentStatus - Filter by document status (Story 7-27)
 */
async function fetchQueueTasks(
  queueName: string,
  documentStatus: DocumentStatusFilter = 'all'
): Promise<TaskInfoWithSteps[]> {
  const params = new URLSearchParams();
  if (documentStatus !== 'all') {
    params.append('document_status', documentStatus);
  }

  const url = `${API_BASE_URL}/api/v1/admin/queue/${queueName}/tasks${params.toString() ? `?${params}` : ''}`;
  const response = await fetch(url, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch queue tasks: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Hook for fetching task details for a specific queue.
 *
 * @param queueName - Queue name to fetch tasks for
 * @param documentStatus - Filter by document status (Story 7-27)
 * @param enabled - Whether to enable the query (default: true)
 * @returns React Query result with task data
 */
export function useQueueTasks(
  queueName: string,
  documentStatus: DocumentStatusFilter = 'all',
  enabled = true
) {
  return useQuery({
    queryKey: ['admin', 'queue', queueName, 'tasks', documentStatus],
    queryFn: () => fetchQueueTasks(queueName, documentStatus),
    enabled,
    staleTime: 5000, // Consider data stale after 5s
    refetchInterval: 10000, // Refresh every 10s when enabled
  });
}

/**
 * Legacy hook for backward compatibility
 * @deprecated Use useQueueTasks with documentStatus filter instead
 */
export function useQueueTasksLegacy(
  queueName: string,
  taskType: 'active' | 'pending' = 'active',
  enabled = true
) {
  const documentStatus: DocumentStatusFilter = taskType === 'active' ? 'PROCESSING' : 'PENDING';
  return useQueueTasks(queueName, documentStatus, enabled);
}
