/**
 * Hook for managing chat session history (Story 8-0: Chat Session Persistence)
 *
 * Fetches user's past chat sessions for a KB and handles session switching.
 */

import { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// Types (matching backend schemas)
// =============================================================================

export interface ChatSessionItem {
  conversation_id: string;
  kb_id: string;
  message_count: number;
  first_message_preview: string;
  last_message_at: string;
  first_message_at: string;
}

export interface ChatSessionsResponse {
  sessions: ChatSessionItem[];
  total: number;
  max_sessions: number;
}

export interface ChatSessionMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations: Array<{
    number: number;
    document_id: string;
    document_name: string;
    page_number?: number;
    section_header?: string;
    excerpt: string;
    confidence?: number;
  }>;
  confidence: number | null;
}

export interface ChatSessionMessagesResponse {
  conversation_id: string;
  kb_id: string;
  messages: ChatSessionMessage[];
  message_count: number;
}

// =============================================================================
// Hook
// =============================================================================

interface UseChatSessionsOptions {
  kbId: string;
  /** Whether to auto-fetch sessions on mount */
  autoFetch?: boolean;
}

interface UseChatSessionsReturn {
  /** List of user's sessions for this KB */
  sessions: ChatSessionItem[];
  /** Total count of sessions */
  total: number;
  /** Maximum sessions allowed (from KB settings) */
  maxSessions: number;
  /** Whether sessions are being fetched */
  isLoading: boolean;
  /** Error message if fetch failed */
  error: string | null;
  /** Refresh the sessions list */
  refresh: () => Promise<void>;
  /** Load messages for a specific session */
  loadSession: (conversationId: string) => Promise<ChatSessionMessagesResponse | null>;
  /** Whether a session is being loaded */
  isLoadingSession: boolean;
}

/**
 * Hook for fetching and managing chat session history.
 *
 * @example
 * const { sessions, isLoading, refresh, loadSession } = useChatSessions({ kbId });
 *
 * // Load an old session
 * const messages = await loadSession('conv-abc123');
 */
export function useChatSessions({
  kbId,
  autoFetch = true,
}: UseChatSessionsOptions): UseChatSessionsReturn {
  const [sessions, setSessions] = useState<ChatSessionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [maxSessions, setMaxSessions] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    if (!kbId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/sessions?kb_id=${kbId}`, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        if (response.status === 404) {
          // KB not found or no permission - show actual backend message
          setError(errorData.detail || 'Knowledge Base not found');
          return;
        }
        throw new Error(errorData.detail || 'Failed to fetch sessions');
      }

      const data: ChatSessionsResponse = await response.json();
      setSessions(data.sessions);
      setTotal(data.total);
      setMaxSessions(data.max_sessions);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [kbId]);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      void fetchSessions();
    }
  }, [autoFetch, fetchSessions]);

  const loadSession = useCallback(
    async (conversationId: string): Promise<ChatSessionMessagesResponse | null> => {
      if (!kbId || !conversationId) return null;

      setIsLoadingSession(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/chat/sessions/${conversationId}/messages?kb_id=${kbId}`,
          {
            method: 'GET',
            credentials: 'include',
          }
        );

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Session not found');
          }
          if (response.status === 400) {
            throw new Error('Invalid session ID');
          }
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to load session');
        }

        const data: ChatSessionMessagesResponse = await response.json();
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return null;
      } finally {
        setIsLoadingSession(false);
      }
    },
    [kbId]
  );

  return {
    sessions,
    total,
    maxSessions,
    isLoading,
    error,
    refresh: fetchSessions,
    loadSession,
    isLoadingSession,
  };
}
