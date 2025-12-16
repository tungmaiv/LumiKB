/**
 * useDraftUndo Hook - Epic 4, Story 4.6, AC5
 * Manages undo/redo history for draft editing with 10-action buffer
 */

import { useReducer, useCallback } from 'react';
import type { Citation } from '@/types/citation';

export interface DraftSnapshot {
  content: string;
  citations: Citation[];
  timestamp: number;
}

interface UndoState {
  past: DraftSnapshot[];
  present: DraftSnapshot;
  future: DraftSnapshot[];
}

type UndoAction =
  | { type: 'SET'; snapshot: DraftSnapshot }
  | { type: 'UNDO' }
  | { type: 'REDO' }
  | { type: 'CLEAR_FUTURE' };

const MAX_HISTORY = 10;

function undoReducer(state: UndoState, action: UndoAction): UndoState {
  switch (action.type) {
    case 'SET': {
      // Add current state to past, update present
      const newPast = [...state.past, state.present].slice(-MAX_HISTORY);
      return {
        past: newPast,
        present: action.snapshot,
        future: [], // Clear future on new action
      };
    }

    case 'UNDO': {
      if (state.past.length === 0) return state;

      const previous = state.past[state.past.length - 1];
      const newPast = state.past.slice(0, -1);

      return {
        past: newPast,
        present: previous,
        future: [state.present, ...state.future].slice(0, MAX_HISTORY),
      };
    }

    case 'REDO': {
      if (state.future.length === 0) return state;

      const next = state.future[0];
      const newFuture = state.future.slice(1);

      return {
        past: [...state.past, state.present].slice(-MAX_HISTORY),
        present: next,
        future: newFuture,
      };
    }

    case 'CLEAR_FUTURE': {
      return {
        ...state,
        future: [],
      };
    }

    default:
      return state;
  }
}

export interface UseDraftUndoReturn {
  /** Current snapshot */
  snapshot: DraftSnapshot;
  /** Whether undo is available */
  canUndo: boolean;
  /** Whether redo is available */
  canRedo: boolean;
  /** Perform undo (Ctrl+Z) */
  undo: () => void;
  /** Perform redo (Ctrl+Y) */
  redo: () => void;
  /** Record new snapshot */
  recordSnapshot: (content: string, citations: Citation[]) => void;
}

/**
 * Hook for managing undo/redo history in draft editor.
 *
 * Features:
 * - 10-action history buffer (AC5)
 * - Undo with Ctrl+Z
 * - Redo with Ctrl+Y
 * - Automatic history management
 *
 * @example
 * const { snapshot, canUndo, undo, recordSnapshot } = useDraftUndo(
 *   initialContent,
 *   initialCitations
 * );
 */
export function useDraftUndo(
  initialContent: string,
  initialCitations: Citation[]
): UseDraftUndoReturn {
  const [state, dispatch] = useReducer(undoReducer, {
    past: [],
    present: {
      content: initialContent,
      citations: initialCitations,
      timestamp: Date.now(),
    },
    future: [],
  });

  const undo = useCallback(() => {
    dispatch({ type: 'UNDO' });
  }, []);

  const redo = useCallback(() => {
    dispatch({ type: 'REDO' });
  }, []);

  const recordSnapshot = useCallback((content: string, citations: Citation[]) => {
    dispatch({
      type: 'SET',
      snapshot: {
        content,
        citations,
        timestamp: Date.now(),
      },
    });
  }, []);

  return {
    snapshot: state.present,
    canUndo: state.past.length > 0,
    canRedo: state.future.length > 0,
    undo,
    redo,
    recordSnapshot,
  };
}
