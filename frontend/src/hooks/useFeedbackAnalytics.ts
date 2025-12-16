/**
 * Feedback Analytics Hook - Story 7-23
 * Fetches feedback analytics data for admin dashboard visualization.
 *
 * AC-7.23.6: API endpoint GET /api/v1/admin/feedback/analytics
 */

import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/** Feedback count by type for pie chart (AC-7.23.2) */
export interface FeedbackTypeCount {
  type: string;
  count: number;
}

/** Daily feedback count for trend chart (AC-7.23.3) */
export interface FeedbackDayCount {
  date: string;
  count: number;
}

/** Recent feedback item with user context (AC-7.23.4) */
export interface RecentFeedbackItem {
  id: string;
  timestamp: string | null;
  user_id: string | null;
  user_email: string | null;
  draft_id: string | null;
  feedback_type: string | null;
  feedback_comments: string | null;
  related_request_id: string | null;
}

/** Comprehensive feedback analytics response (AC-7.23.6) */
export interface FeedbackAnalytics {
  by_type: FeedbackTypeCount[];
  by_day: FeedbackDayCount[];
  recent: RecentFeedbackItem[];
  total_count: number;
}

/**
 * Hook for fetching feedback analytics from admin API.
 *
 * @example
 * const { data, isLoading, error } = useFeedbackAnalytics();
 * if (data) {
 *   // Render pie chart with data.by_type
 *   // Render trend chart with data.by_day
 *   // Render table with data.recent
 * }
 */
export function useFeedbackAnalytics() {
  return useQuery({
    queryKey: ['admin', 'feedback', 'analytics'],
    queryFn: async (): Promise<FeedbackAnalytics> => {
      const res = await fetch(`${API_BASE_URL}/api/v1/admin/feedback/analytics`, {
        credentials: 'include',
      });

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('Unauthorized: Admin access required');
        }
        if (res.status === 401) {
          throw new Error('Authentication required');
        }
        throw new Error('Failed to fetch feedback analytics');
      }

      return res.json();
    },
    staleTime: 2 * 60 * 1000, // 2 minutes - feedback data changes more frequently
    refetchInterval: 2 * 60 * 1000, // Auto-refetch every 2 minutes
    retry: 1,
  });
}
