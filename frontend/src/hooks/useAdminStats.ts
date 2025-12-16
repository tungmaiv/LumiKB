import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface PeriodStats {
  last_24h: number;
  last_7d: number;
  last_30d: number;
}

export interface AdminStats {
  users: {
    total: number;
    active: number;
    inactive: number;
  };
  knowledge_bases: {
    total: number;
    by_status: Record<string, number>;
  };
  documents: {
    total: number;
    by_status: Record<string, number>;
  };
  storage: {
    total_bytes: number;
    avg_doc_size_bytes: number;
  };
  activity: {
    searches: PeriodStats;
    generations: PeriodStats;
  };
  trends: {
    searches: number[];
    generations: number[];
  };
}

export function useAdminStats() {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: async (): Promise<AdminStats> => {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE_URL}/api/v1/admin/stats`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('Unauthorized: Admin access required');
        }
        if (res.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error('Failed to fetch admin statistics');
      }

      return res.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // Auto-refetch every 5 minutes
    retry: 1,
  });
}
