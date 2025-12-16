/**
 * Unit tests for useDraftUndo hook
 *
 * Tests undo/redo functionality, history buffer, and snapshot management.
 *
 * Coverage Target: 80%+
 * Test Count: 7
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { useDraftUndo } from '../useDraftUndo';

describe('useDraftUndo', () => {
  const initialSnapshot = {
    content: 'Initial content',
    citations: [],
  };

  describe('[P1] Undo Functionality', () => {
    it('should undo last change', () => {
      // GIVEN: Hook with initial snapshot
      const { result } = renderHook(() => useDraftUndo(initialSnapshot));

      // WHEN: Recording new snapshot then undoing
      act(() => {
        result.current.recordSnapshot({
          content: 'Changed content',
          citations: [],
        });
      });

      expect(result.current.snapshot.content).toBe('Changed content');

      act(() => {
        result.current.undo();
      });

      // THEN: Reverted to initial
      expect(result.current.snapshot.content).toBe('Initial content');
    });

    it('should undo multiple changes in reverse order', () => {
      // GIVEN: Hook with 3 snapshots
      const { result } = renderHook(() => useDraftUndo(initialSnapshot));

      act(() => {
        result.current.recordSnapshot({ content: 'Change 1', citations: [] });
        result.current.recordSnapshot({ content: 'Change 2', citations: [] });
        result.current.recordSnapshot({ content: 'Change 3', citations: [] });
      });

      expect(result.current.snapshot.content).toBe('Change 3');

      // WHEN: Undoing 3 times
      act(() => {
        result.current.undo(); // Back to Change 2
      });
      expect(result.current.snapshot.content).toBe('Change 2');

      act(() => {
        result.current.undo(); // Back to Change 1
      });
      expect(result.current.snapshot.content).toBe('Change 1');

      act(() => {
        result.current.undo(); // Back to Initial
      });
      expect(result.current.snapshot.content).toBe('Initial content');
    });

    it('should disable undo when at beginning of history', () => {
      // GIVEN: Hook at initial state
      const { result } = renderHook(() => useDraftUndo(initialSnapshot));

      // THEN: canUndo is false
      expect(result.current.canUndo).toBe(false);

      // WHEN: Recording snapshot
      act(() => {
        result.current.recordSnapshot({ content: 'Change', citations: [] });
      });

      // THEN: canUndo is true
      expect(result.current.canUndo).toBe(true);
    });
  });

  describe('[P1] Redo Functionality', () => {
    it('should redo undone change', () => {
      // GIVEN: Hook with snapshot that's been undone
      const { result } = renderHook(() => useDraftUndo(initialSnapshot));

      act(() => {
        result.current.recordSnapshot({ content: 'Changed', citations: [] });
      });

      act(() => {
        result.current.undo();
      });

      expect(result.current.snapshot.content).toBe('Initial content');

      // WHEN: Redoing
      act(() => {
        result.current.redo();
      });

      // THEN: Change restored
      expect(result.current.snapshot.content).toBe('Changed');
    });

    it('should redo multiple changes in forward order', () => {
      // GIVEN: Hook with 3 changes, all undone
      const { result } = renderHook(() => useDraftUndo(initialSnapshot));

      act(() => {
        result.current.recordSnapshot({ content: 'Change 1', citations: [] });
        result.current.recordSnapshot({ content: 'Change 2', citations: [] });
        result.current.recordSnapshot({ content: 'Change 3', citations: [] });

        result.current.undo();
        result.current.undo();
        result.current.undo();
      });

      expect(result.current.snapshot.content).toBe('Initial content');

      // WHEN: Redoing 3 times
      act(() => {
        result.current.redo();
      });
      expect(result.current.snapshot.content).toBe('Change 1');

      act(() => {
        result.current.redo();
      });
      expect(result.current.snapshot.content).toBe('Change 2');

      act(() => {
        result.current.redo();
      });
      expect(result.current.snapshot.content).toBe('Change 3');
    });

    it('should disable redo when at end of history', () => {
      // GIVEN: Hook at latest state
      const { result } = renderHook(() => useDraftUndo(initialSnapshot));

      // THEN: canRedo is false
      expect(result.current.canRedo).toBe(false);

      // WHEN: Recording and undoing
      act(() => {
        result.current.recordSnapshot({ content: 'Change', citations: [] });
        result.current.undo();
      });

      // THEN: canRedo is true
      expect(result.current.canRedo).toBe(true);
    });

    it('should clear redo history when new snapshot recorded', () => {
      // GIVEN: Hook with undone changes
      const { result } = renderHook(() => useDraftUndo(initialSnapshot));

      act(() => {
        result.current.recordSnapshot({ content: 'Change 1', citations: [] });
        result.current.recordSnapshot({ content: 'Change 2', citations: [] });
        result.current.undo(); // Now can redo
      });

      expect(result.current.canRedo).toBe(true);

      // WHEN: Recording new snapshot from middle of history
      act(() => {
        result.current.recordSnapshot({ content: 'New branch', citations: [] });
      });

      // THEN: Redo disabled (history forked)
      expect(result.current.canRedo).toBe(false);
      expect(result.current.snapshot.content).toBe('New branch');
    });
  });

  describe('[P2] History Buffer Limit', () => {
    it('should maintain maximum 10 snapshots in history', () => {
      // GIVEN: Hook with initial snapshot
      const { result } = renderHook(() => useDraftUndo(initialSnapshot));

      // WHEN: Recording 15 snapshots (exceeds 10 buffer)
      act(() => {
        for (let i = 1; i <= 15; i++) {
          result.current.recordSnapshot({
            content: `Change ${i}`,
            citations: [],
          });
        }
      });

      // THEN: Current is Change 15
      expect(result.current.snapshot.content).toBe('Change 15');

      // WHEN: Undoing 10 times (max buffer)
      act(() => {
        for (let i = 0; i < 10; i++) {
          result.current.undo();
        }
      });

      // THEN: Stops at Change 6 (15 - 9, oldest in 10-buffer is Change 6)
      expect(result.current.snapshot.content).toBe('Change 6');
      expect(result.current.canUndo).toBe(false);
    });
  });

  describe('[P2] Citation Preservation in Undo/Redo', () => {
    it('should preserve citations when undoing', () => {
      // GIVEN: Snapshots with different citations
      const { result } = renderHook(() => useDraftUndo(initialSnapshot));

      const citation1 = {
        number: 1,
        document_id: 'doc-1',
        document_name: 'test.pdf',
        page: 5,
        chunk_index: 2,
        confidence_score: 0.9,
        snippet: 'Test',
      };

      const citation2 = {
        number: 2,
        document_id: 'doc-2',
        document_name: 'auth.pdf',
        page: 10,
        chunk_index: 5,
        confidence_score: 0.95,
        snippet: 'Auth',
      };

      act(() => {
        result.current.recordSnapshot({
          content: 'Content with [1]',
          citations: [citation1],
        });
        result.current.recordSnapshot({
          content: 'Content with [1] and [2]',
          citations: [citation1, citation2],
        });
      });

      expect(result.current.snapshot.citations).toHaveLength(2);

      // WHEN: Undoing
      act(() => {
        result.current.undo();
      });

      // THEN: Citations from previous snapshot restored
      expect(result.current.snapshot.citations).toHaveLength(1);
      expect(result.current.snapshot.citations[0]).toEqual(citation1);
    });
  });
});
