/**
 * Chat History Data Hooks
 *
 * Story 9-9: Chat History Viewer UI
 * AC9: Pagination for long histories with infinite scroll or page controls
 */

import { useInfiniteQuery, useQuery } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export interface Citation {
  index: number;
  document_id: string;
  document_name: string | null;
  chunk_id: string | null;
  relevance_score: number | null;
}

/**
 * Debug info for chat history (from observability storage)
 * Stored when KB has debug_mode enabled
 */
export interface ChatHistoryDebugInfo {
  kb_params?: {
    system_prompt_preview: string;
    citation_style: string;
    response_language: string;
    uncertainty_handling: string;
  };
  chunks_retrieved?: Array<{
    document_id: string;
    chunk_index: number;
    relevance_score: number;
    document_name?: string;
    preview?: string;
  }>;
  timing?: {
    retrieval_ms: number;
    context_assembly_ms: number;
  };
}

export interface ChatMessageItem {
  id: string;
  trace_id: string;
  session_id: string | null;
  role: 'user' | 'assistant';
  content: string;
  user_id: string | null;
  kb_id: string | null;
  created_at: string;
  token_count: number | null;
  response_time_ms: number | null;
  citations: Citation[] | null;
  /** Debug info when KB has debug_mode enabled (Story 9-15) */
  debug_info: ChatHistoryDebugInfo | null;
}

export interface ChatHistoryResponse {
  items: ChatMessageItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface ChatSession {
  session_id: string;
  user_id: string | null;
  user_name: string | null;
  kb_id: string | null;
  kb_name: string | null;
  message_count: number;
  last_message_at: string;
  first_message_at: string;
}

export interface ChatSessionsResponse {
  items: ChatSession[];
  total: number;
  skip: number;
  limit: number;
}

export interface ChatHistoryFilters {
  userId?: string;
  kbId?: string;
  sessionId?: string;
  searchQuery?: string;
  startDate?: string;
  endDate?: string;
}

// ============================================================================
// API Functions
// ============================================================================

async function fetchChatHistory(
  filters: ChatHistoryFilters,
  skip: number = 0,
  limit: number = 50
): Promise<ChatHistoryResponse> {
  const params = new URLSearchParams();

  if (filters.userId) params.append('user_id', filters.userId);
  if (filters.kbId) params.append('kb_id', filters.kbId);
  if (filters.sessionId) params.append('session_id', filters.sessionId);
  if (filters.searchQuery) params.append('search_query', filters.searchQuery);
  if (filters.startDate) params.append('start_date', filters.startDate);
  if (filters.endDate) params.append('end_date', filters.endDate);
  params.append('skip', String(skip));
  params.append('limit', String(limit));

  const response = await fetch(`${API_BASE_URL}/api/v1/observability/chat-history?${params}`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch chat history: ${response.statusText}`);
  }

  return response.json();
}

async function fetchChatSessions(
  filters: ChatHistoryFilters,
  skip: number = 0,
  limit: number = 20
): Promise<ChatSessionsResponse> {
  const params = new URLSearchParams();

  if (filters.userId) params.append('user_id', filters.userId);
  if (filters.kbId) params.append('kb_id', filters.kbId);
  if (filters.searchQuery) params.append('search_query', filters.searchQuery);
  if (filters.startDate) params.append('start_date', filters.startDate);
  if (filters.endDate) params.append('end_date', filters.endDate);
  params.append('skip', String(skip));
  params.append('limit', String(limit));

  const response = await fetch(`${API_BASE_URL}/api/v1/observability/chat-sessions?${params}`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch chat sessions: ${response.statusText}`);
  }

  return response.json();
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * Hook for fetching paginated chat sessions list
 * AC1: Session list displays user, KB name, message count, and last active timestamp
 */
export function useChatSessions(filters: ChatHistoryFilters = {}) {
  return useQuery({
    queryKey: ['chat-sessions', filters],
    queryFn: () => fetchChatSessions(filters),
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}

/**
 * Hook for fetching chat messages with infinite scroll support
 * AC9: Pagination for long histories
 */
export function useChatMessages(sessionId: string | null) {
  return useInfiniteQuery({
    queryKey: ['chat-messages', sessionId],
    queryFn: ({ pageParam = 0 }) =>
      fetchChatHistory({ sessionId: sessionId || undefined }, pageParam, 50),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => {
      const nextSkip = lastPage.skip + lastPage.limit;
      return nextSkip < lastPage.total ? nextSkip : undefined;
    },
    enabled: !!sessionId,
    staleTime: 60_000,
  });
}

/**
 * Hook for searching chat history with filters
 * AC6, AC7: Search within chat history, filter by user/KB/date
 */
export function useChatHistorySearch(filters: ChatHistoryFilters = {}) {
  return useQuery({
    queryKey: ['chat-history-search', filters],
    queryFn: () => fetchChatHistory(filters, 0, 100),
    staleTime: 30_000,
    enabled: Object.keys(filters).length > 0,
  });
}
