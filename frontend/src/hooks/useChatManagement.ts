/**
 * Chat management hook for conversation lifecycle operations.
 *
 * Provides new chat, clear chat, and undo functionality per AC-1 and AC-2.
 */

import { useState, useEffect, useRef } from 'react';

interface ChatManagementCallbacks {
  /** Called when messages should be cleared */
  onMessagesClear?: () => void;
  /** Called when messages should be restored */
  onMessagesRestore?: () => void;
  /** Called when SSE stream should be aborted */
  onAbortStream?: () => void;
}

interface ChatManagementResult {
  /** Start a new conversation (clears history) */
  startNewChat: (kbId: string) => Promise<void>;
  /** Clear current conversation (30s undo window) */
  clearChat: (kbId: string) => Promise<void>;
  /** Undo the last clear operation (must be within 30s) */
  undoClear: (kbId: string) => Promise<void>;
  /** Whether undo is currently available */
  undoAvailable: boolean;
  /** Loading state for management operations */
  isLoading: boolean;
  /** Error from last operation */
  error: string | null;
  /** Remaining seconds in undo window (0 if not available) */
  undoSecondsRemaining: number;
}

/**
 * Hook for managing conversation lifecycle.
 *
 * @example
 * const { startNewChat, clearChat, undoClear, undoAvailable } = useChatManagement({
 *   onMessagesClear: () => setMessages([]),
 *   onMessagesRestore: () => { ... },
 * });
 *
 * // Start fresh conversation
 * await startNewChat(kbId);
 *
 * // Clear with undo
 * await clearChat(kbId);
 * if (undoAvailable) {
 *   await undoClear(kbId);
 * }
 */
export function useChatManagement(callbacks?: ChatManagementCallbacks): ChatManagementResult {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize undo state from localStorage (Option A fix from code review)
  const [undoAvailable, setUndoAvailable] = useState(() => {
    if (typeof window === 'undefined') return false;
    const stored = localStorage.getItem('chat-undo-available');
    const expires = Number(localStorage.getItem('chat-undo-expires'));
    return stored === 'true' && Date.now() < expires;
  });

  const [undoSecondsRemaining, setUndoSecondsRemaining] = useState(() => {
    if (typeof window === 'undefined') return 0;
    const expires = Number(localStorage.getItem('chat-undo-expires'));
    if (!expires || Date.now() >= expires) return 0;
    return Math.ceil((expires - Date.now()) / 1000);
  });

  const undoTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const undoIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (undoTimeoutRef.current) clearTimeout(undoTimeoutRef.current);
      if (undoIntervalRef.current) clearInterval(undoIntervalRef.current);
    };
  }, []);

  // Monitor localStorage for expired undo state (Option A fix)
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const checkExpiration = () => {
      const expires = Number(localStorage.getItem('chat-undo-expires'));
      if (expires && Date.now() >= expires) {
        localStorage.removeItem('chat-undo-available');
        localStorage.removeItem('chat-undo-kb-id');
        localStorage.removeItem('chat-undo-expires');
        setUndoAvailable(false);
        setUndoSecondsRemaining(0);
      }
    };

    const interval = setInterval(checkExpiration, 1000);
    return () => clearInterval(interval);
  }, []);

  const startNewChat = async (kbId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    setUndoAvailable(false);

    // Clear undo timers
    if (undoTimeoutRef.current) clearTimeout(undoTimeoutRef.current);
    if (undoIntervalRef.current) clearInterval(undoIntervalRef.current);
    setUndoSecondsRemaining(0);

    // Clear localStorage undo state
    localStorage.removeItem('chat-undo-available');
    localStorage.removeItem('chat-undo-kb-id');
    localStorage.removeItem('chat-undo-expires');

    try {
      const response = await fetch(`/api/v1/chat/new?kb_id=${kbId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start new chat');
      }

      // Clear messages via callback instead of page reload
      callbacks?.onMessagesClear?.();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = async (kbId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    // Abort any active SSE stream
    callbacks?.onAbortStream?.();

    try {
      const response = await fetch(`/api/v1/chat/clear?kb_id=${kbId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to clear chat');
      }

      const data = await response.json();
      setUndoAvailable(data.undo_available);

      // Persist undo state to localStorage (Option A fix from code review)
      if (data.undo_available) {
        const expiresAt = Date.now() + 30000;
        localStorage.setItem('chat-undo-available', 'true');
        localStorage.setItem('chat-undo-kb-id', kbId);
        localStorage.setItem('chat-undo-expires', String(expiresAt));
      }

      // Clear messages via callback instead of page reload
      callbacks?.onMessagesClear?.();

      // Start 30-second undo countdown
      if (data.undo_available) {
        setUndoSecondsRemaining(30);

        // Countdown interval (updates every second)
        undoIntervalRef.current = setInterval(() => {
          setUndoSecondsRemaining((prev) => {
            if (prev <= 1) {
              if (undoIntervalRef.current) clearInterval(undoIntervalRef.current);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);

        // Timeout to disable undo after 30s
        undoTimeoutRef.current = setTimeout(() => {
          setUndoAvailable(false);
          setUndoSecondsRemaining(0);
          if (undoIntervalRef.current) clearInterval(undoIntervalRef.current);
          // Clear localStorage when undo expires
          localStorage.removeItem('chat-undo-available');
          localStorage.removeItem('chat-undo-kb-id');
          localStorage.removeItem('chat-undo-expires');
        }, 30000);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const undoClear = async (kbId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    // Clear undo timers
    if (undoTimeoutRef.current) clearTimeout(undoTimeoutRef.current);
    if (undoIntervalRef.current) clearInterval(undoIntervalRef.current);

    try {
      const response = await fetch(`/api/v1/chat/undo-clear?kb_id=${kbId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 410) {
          throw new Error('Undo window expired (30 seconds)');
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to undo clear');
      }

      setUndoAvailable(false);
      setUndoSecondsRemaining(0);

      // Clear localStorage undo state
      localStorage.removeItem('chat-undo-available');
      localStorage.removeItem('chat-undo-kb-id');
      localStorage.removeItem('chat-undo-expires');

      // Restore messages via callback instead of page reload
      callbacks?.onMessagesRestore?.();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    startNewChat,
    clearChat,
    undoClear,
    undoAvailable,
    undoSecondsRemaining,
    isLoading,
    error,
  };
}
