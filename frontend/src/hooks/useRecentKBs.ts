import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Recent KB type returned by the API.
 */
export interface RecentKB {
  kb_id: string;
  kb_name: string;
  description: string;
  last_accessed: string;
  document_count: number;
}

/**
 * Hook to fetch user's recently accessed knowledge bases.
 *
 * Returns up to 5 recently accessed KBs sorted by last access time.
 * Uses 5-minute stale time for efficient caching.
 */
export function useRecentKBs() {
  return useQuery({
    queryKey: ['users', 'me', 'recent-kbs'],
    queryFn: async (): Promise<RecentKB[]> => {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE_URL}/api/v1/users/me/recent-kbs`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        if (res.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error('Failed to fetch recent KBs');
      }

      return res.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}
