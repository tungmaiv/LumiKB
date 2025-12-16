/**
 * Generation streaming hook for real-time draft generation via SSE.
 * Epic 4, Story 4.5, AC1-AC4
 * Updated in Story 7-22 to add reconnection support with exponential backoff.
 */

import { useState, useRef, useCallback } from 'react';
import type { Citation } from '@/types/citation';
import { useSSEReconnection } from './useSSEReconnection';
import type { ReconnectionState } from './useSSEReconnection';

export type GenerationMode =
  | 'rfp_response'
  | 'technical_checklist'
  | 'requirements_summary'
  | 'custom';

interface GenerationStreamRequest {
  kbId: string;
  mode: GenerationMode;
  additionalPrompt: string;
  selectedChunkIds: string[];
}

interface StatusEvent {
  type: 'status';
  content: string;
}

interface TokenEvent {
  type: 'token';
  content: string;
}

interface CitationEvent {
  type: 'citation';
  number: number;
  data: Citation;
}

interface DoneEvent {
  type: 'done';
  generation_id: string;
  confidence: number;
  sources_used: number;
}

interface ErrorEvent {
  type: 'error';
  message: string;
}

type StreamEvent = StatusEvent | TokenEvent | CitationEvent | DoneEvent | ErrorEvent;

export interface GenerationStreamState {
  /** Current generation status message */
  status: string | null;
  /** Accumulated draft content */
  content: string;
  /** Discovered citations */
  citations: Citation[];
  /** Overall confidence score (0-1) */
  confidence: number | null;
  /** Unique generation ID */
  generationId: string | null;
  /** Number of sources used */
  sourcesUsed: number | null;
  /** Whether generation is in progress */
  isGenerating: boolean;
  /** Error message if generation failed */
  error: string | null;
}

export interface GenerationStreamResult extends GenerationStreamState {
  /** Start streaming generation */
  startGeneration: (request: GenerationStreamRequest) => Promise<void>;
  /** Cancel active generation stream */
  cancelGeneration: () => void;
  /** Reset state for new generation */
  reset: () => void;
  /** Reconnection state (Story 7-22) */
  reconnection: ReconnectionState;
  /** Manually retry connection after max retries exceeded */
  retryConnection: () => void;
  /** Enable polling fallback */
  enablePollingFallback: () => void;
  /** Disable polling fallback */
  disablePollingFallback: () => void;
}

const INITIAL_STATE: GenerationStreamState = {
  status: null,
  content: '',
  citations: [],
  confidence: null,
  generationId: null,
  sourcesUsed: null,
  isGenerating: false,
  error: null,
};

/**
 * Hook for streaming document generation from backend.
 *
 * Handles SSE event stream with progressive content and citation accumulation.
 * Supports cancellation via AbortController (AC4).
 * Story 7-22: Added reconnection with exponential backoff.
 *
 * @example
 * const { startGeneration, cancelGeneration, content, citations, isGenerating, reconnection } =
 *   useGenerationStream();
 *
 * await startGeneration({
 *   kbId: 'kb-123',
 *   mode: 'rfp_response',
 *   additionalPrompt: 'Focus on security',
 *   selectedChunkIds: ['chunk-1', 'chunk-2'],
 * });
 *
 * // Handle reconnection UI
 * if (reconnection.isReconnecting) {
 *   showReconnectingIndicator(reconnection.attemptCount);
 * }
 */
export function useGenerationStream(): GenerationStreamResult {
  const [state, setState] = useState<GenerationStreamState>(INITIAL_STATE);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastRequestRef = useRef<GenerationStreamRequest | null>(null);

  // SSE reconnection hook (Story 7-22)
  const reconnection = useSSEReconnection({
    maxRetries: 5,
    onReconnectSuccess: () => {
      setState((prev) => ({
        ...prev,
        status: 'Connected',
      }));
    },
    onMaxRetriesExceeded: () => {
      setState((prev) => ({
        ...prev,
        error: 'Connection lost after multiple attempts. Please retry.',
        isGenerating: false,
      }));
    },
  });

  const reset = useCallback(() => {
    setState(INITIAL_STATE);
    reconnection.resetState();
    lastRequestRef.current = null;
  }, [reconnection]);

  const cancelGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    reconnection.resetState();
    setState((prev) => ({
      ...prev,
      isGenerating: false,
      status: 'Cancelled',
    }));
  }, [reconnection]);

  const processStream = useCallback(
    async (request: GenerationStreamRequest, isRetry = false): Promise<void> => {
      // Store request for potential retry
      lastRequestRef.current = request;

      // Only reset state for new generation, not retries
      if (!isRetry) {
        setState((prev) => ({
          ...prev,
          status: null,
          error: null,
          isGenerating: true,
        }));
      }

      // Create abort controller for cancellation
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      try {
        const response = await fetch('/api/v1/generate/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            // Include Last-Event-ID if resuming (Story 7-22 AC-7.22.3)
            ...(reconnection.lastEventId
              ? { 'Last-Event-ID': reconnection.lastEventId }
              : {}),
          },
          credentials: 'include',
          signal: abortController.signal,
          body: JSON.stringify({
            kb_id: request.kbId,
            mode: request.mode,
            additional_prompt: request.additionalPrompt,
            selected_chunk_ids: request.selectedChunkIds,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Generation failed');
        }

        if (!response.body) {
          throw new Error('Response body is null');
        }

        // Connection successful - reset reconnection state (AC-7.22.3)
        reconnection.onConnectionSuccess();

        // Process SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.trim() || !line.startsWith('data: ')) continue;

            const data = line.slice(6); // Remove 'data: ' prefix

            // Track event ID if present (AC-7.22.3)
            const idMatch = line.match(/^id:\s*(.+)$/);
            if (idMatch) {
              reconnection.setLastEventId(idMatch[1]);
            }

            const event: StreamEvent = JSON.parse(data);

            switch (event.type) {
              case 'status':
                setState((prev) => ({
                  ...prev,
                  status: event.content,
                }));
                break;

              case 'token':
                setState((prev) => ({
                  ...prev,
                  content: prev.content + event.content,
                }));
                break;

              case 'citation':
                setState((prev) => ({
                  ...prev,
                  citations: [...prev.citations, event.data],
                }));
                break;

              case 'done':
                setState((prev) => ({
                  ...prev,
                  generationId: event.generation_id,
                  confidence: event.confidence,
                  sourcesUsed: event.sources_used,
                  isGenerating: false,
                  status: 'Complete',
                }));
                break;

              case 'error':
                setState((prev) => ({
                  ...prev,
                  error: event.message,
                  isGenerating: false,
                  status: null,
                }));
                break;
            }
          }
        }
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          // Cancellation is handled by cancelGeneration()
          return;
        }

        // Check if this is a network error that warrants reconnection (AC-7.22.1)
        const isNetworkError =
          err instanceof TypeError ||
          (err instanceof Error && err.message.includes('network')) ||
          (err instanceof Error && err.message.includes('fetch'));

        if (isNetworkError && !reconnection.maxRetriesExceeded) {
          // Schedule reconnection with exponential backoff (AC-7.22.2)
          reconnection.scheduleReconnect(() => {
            processStream(request, true);
          });
          return;
        }

        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setState((prev) => ({
          ...prev,
          error: errorMessage,
          isGenerating: false,
          status: null,
        }));
      } finally {
        abortControllerRef.current = null;
      }
    },
    [reconnection]
  );

  const startGeneration = useCallback(
    async (request: GenerationStreamRequest): Promise<void> => {
      // Reset state for new generation
      reset();
      setState(INITIAL_STATE);
      setState((prev) => ({
        ...prev,
        isGenerating: true,
        error: null,
      }));
      await processStream(request, false);
    },
    [reset, processStream]
  );

  // Manual retry after max retries exceeded (AC-7.22.4)
  const retryConnection = useCallback(() => {
    if (lastRequestRef.current) {
      reconnection.manualRetry(() => {
        if (lastRequestRef.current) {
          processStream(lastRequestRef.current, true);
        }
      });
    }
  }, [reconnection, processStream]);

  // Polling fallback (AC-7.22.5)
  const enablePollingFallback = useCallback(() => {
    if (!lastRequestRef.current) return;

    reconnection.enablePolling(async () => {
      // Poll for status - this would need a corresponding API endpoint
      try {
        const response = await fetch(
          `/api/v1/generate/status/${state.generationId}`,
          {
            credentials: 'include',
          }
        );
        if (response.ok) {
          const data = await response.json();
          setState((prev) => ({
            ...prev,
            content: data.content || prev.content,
            citations: data.citations || prev.citations,
            status: data.status || prev.status,
            isGenerating: data.status !== 'Complete' && data.status !== 'Error',
          }));
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    });
  }, [reconnection, state.generationId]);

  const disablePollingFallback = useCallback(() => {
    reconnection.disablePolling();
  }, [reconnection]);

  return {
    ...state,
    startGeneration,
    cancelGeneration,
    reset,
    reconnection: {
      isReconnecting: reconnection.isReconnecting,
      attemptCount: reconnection.attemptCount,
      lastEventId: reconnection.lastEventId,
      error: reconnection.error,
      maxRetriesExceeded: reconnection.maxRetriesExceeded,
      isPolling: reconnection.isPolling,
      nextRetryIn: reconnection.nextRetryIn,
    },
    retryConnection,
    enablePollingFallback,
    disablePollingFallback,
  };
}
