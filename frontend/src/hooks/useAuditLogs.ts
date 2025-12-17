/**
 * Hook for fetching and managing audit logs
 * Story 5.2: Audit Log Viewer
 */

import { useQuery } from '@tanstack/react-query';
import type { AuditLogFilter, PaginatedAuditResponse } from '@/types/audit';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UseAuditLogsOptions {
  filters: AuditLogFilter;
  page: number;
  pageSize: number;
}

export function useAuditLogs({ filters, page, pageSize }: UseAuditLogsOptions) {
  return useQuery({
    queryKey: ['admin', 'audit', 'logs', filters, page, pageSize],
    queryFn: async (): Promise<PaginatedAuditResponse> => {
      // Build request body
      const requestBody: AuditLogFilter = {
        page,
        page_size: pageSize,
        ...filters,
      };

      const res = await fetch(`${API_BASE_URL}/api/v1/admin/audit/logs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestBody),
      });

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('Unauthorized: Admin access required');
        }
        if (res.status === 401) {
          throw new Error('Authentication required');
        }
        if (res.status === 500) {
          throw new Error('Server error: Failed to fetch audit logs');
        }
        throw new Error(`Failed to fetch audit logs: ${res.statusText}`);
      }

      return res.json();
    },
    staleTime: 30 * 1000, // 30 seconds (audit logs change frequently)
    retry: 1, // Only retry once for failed requests
    // Don't refetch automatically - user controls via filters/pagination
    refetchOnWindowFocus: false,
  });
}
