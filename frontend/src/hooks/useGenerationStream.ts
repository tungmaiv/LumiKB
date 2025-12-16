/**
 * Generation streaming hook for real-time draft generation via SSE.
 * Epic 4, Story 4.5, AC1-AC4
 */

import { useState, useRef, useCallback } from 'react';
import type { Citation } from '@/types/citation';

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
 *
 * @example
 * const { startGeneration, cancelGeneration, content, citations, isGenerating } =
 *   useGenerationStream();
 *
 * await startGeneration({
 *   kbId: 'kb-123',
 *   mode: 'rfp_response',
 *   additionalPrompt: 'Focus on security',
 *   selectedChunkIds: ['chunk-1', 'chunk-2'],
 * });
 */
export function useGenerationStream(): GenerationStreamResult {
  const [state, setState] = useState<GenerationStreamState>(INITIAL_STATE);
  const abortControllerRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  const cancelGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState((prev) => ({
      ...prev,
      isGenerating: false,
      status: 'Cancelled',
    }));
  }, []);

  const startGeneration = useCallback(
    async (request: GenerationStreamRequest): Promise<void> => {
      // Reset state for new generation
      reset();

      // Create abort controller for cancellation
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      setState((prev) => ({
        ...prev,
        isGenerating: true,
        error: null,
      }));

      try {
        const response = await fetch('/api/v1/generate/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
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
    [reset]
  );

  return {
    ...state,
    startGeneration,
    cancelGeneration,
    reset,
  };
}
