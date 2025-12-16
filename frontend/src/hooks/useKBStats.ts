import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface TopDocument {
  id: string;
  filename: string;
  access_count: number;
}

export interface KBDetailedStats {
  kb_id: string;
  kb_name: string;
  document_count: number;
  storage_bytes: number;
  total_chunks: number;
  total_embeddings: number;
  searches_30d: number;
  generations_30d: number;
  unique_users_30d: number;
  top_documents: TopDocument[];
  last_updated: string;
}

export function useKBStats(kbId: string | null) {
  return useQuery({
    queryKey: ['admin', 'knowledge-bases', kbId, 'stats'],
    queryFn: async (): Promise<KBDetailedStats> => {
      if (!kbId) {
        throw new Error('KB ID is required');
      }

      const res = await fetch(
        `${API_BASE_URL}/api/v1/admin/knowledge-bases/${kbId}/stats`,
        {
          credentials: 'include',
        }
      );

      if (!res.ok) {
        if (res.status === 404) {
          throw new Error('Knowledge base not found');
        }
        if (res.status === 403) {
          throw new Error('Unauthorized: Admin access required');
        }
        if (res.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error('Failed to fetch KB statistics');
      }

      return res.json();
    },
    enabled: !!kbId, // Only fetch if kbId is provided
    staleTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 10 * 60 * 1000, // Auto-refetch every 10 minutes
    retry: 1,
  });
}
