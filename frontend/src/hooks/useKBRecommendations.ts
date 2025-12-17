import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * KB Recommendation type returned by the API.
 */
export interface KBRecommendation {
  kb_id: string;
  kb_name: string;
  description: string;
  score: number;
  reason: string;
  last_accessed: string | null;
  is_cold_start: boolean;
}

/**
 * Hook to fetch personalized KB recommendations.
 *
 * Returns up to 5 KB recommendations based on:
 * - Recent access patterns (40% weight)
 * - Search relevance (35% weight)
 * - Global popularity (25% weight)
 *
 * New users receive cold start recommendations based on popular public KBs.
 * Results are cached for 1 hour.
 */
export function useKBRecommendations() {
  return useQuery({
    queryKey: ['users', 'me', 'kb-recommendations'],
    queryFn: async (): Promise<KBRecommendation[]> => {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE_URL}/api/v1/users/me/kb-recommendations`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        if (res.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error('Failed to fetch KB recommendations');
      }

      return res.json();
    },
    staleTime: 60 * 60 * 1000, // 1 hour (matches backend cache)
    retry: 1,
  });
}
