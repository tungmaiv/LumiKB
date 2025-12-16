/**
 * Unit tests for useDraftUndo hook
 *
 * Tests undo/redo functionality, history buffer, and snapshot management.
 *
 * Coverage Target: 80%+
 * Test Count: 7
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { useDraftUndo } from '../useDraftUndo';
import type { Citation } from '@/types/citation';

describe('useDraftUndo', () => {
  const initialContent = 'Initial content';
  const initialCitations: never[] = [];

  describe('[P1] Undo Functionality', () => {
    it('should undo last change', () => {
      // GIVEN: Hook with initial snapshot
      const { result } = renderHook(() => useDraftUndo(initialContent, initialCitations));

      // WHEN: Recording new snapshot then undoing
      act(() => {
        result.current.recordSnapshot('Changed content', []);
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
      const { result } = renderHook(() => useDraftUndo(initialContent, initialCitations));

      act(() => {
        result.current.recordSnapshot('Change 1', []);
        result.current.recordSnapshot('Change 2', []);
        result.current.recordSnapshot('Change 3', []);
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
      const { result } = renderHook(() => useDraftUndo(initialContent, initialCitations));

      // THEN: canUndo is false
      expect(result.current.canUndo).toBe(false);

      // WHEN: Recording snapshot
      act(() => {
        result.current.recordSnapshot('Change', []);
      });

      // THEN: canUndo is true
      expect(result.current.canUndo).toBe(true);
    });
  });

  describe('[P1] Redo Functionality', () => {
    it('should redo undone change', () => {
      // GIVEN: Hook with snapshot that's been undone
      const { result } = renderHook(() => useDraftUndo(initialContent, initialCitations));

      act(() => {
        result.current.recordSnapshot('Changed', []);
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
      const { result } = renderHook(() => useDraftUndo(initialContent, initialCitations));

      act(() => {
        result.current.recordSnapshot('Change 1', []);
        result.current.recordSnapshot('Change 2', []);
        result.current.recordSnapshot('Change 3', []);

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
      const { result } = renderHook(() => useDraftUndo(initialContent, initialCitations));

      // THEN: canRedo is false
      expect(result.current.canRedo).toBe(false);

      // WHEN: Recording and undoing
      act(() => {
        result.current.recordSnapshot('Change', []);
        result.current.undo();
      });

      // THEN: canRedo is true
      expect(result.current.canRedo).toBe(true);
    });

    it('should clear redo history when new snapshot recorded', () => {
      // GIVEN: Hook with undone changes
      const { result } = renderHook(() => useDraftUndo(initialContent, initialCitations));

      act(() => {
        result.current.recordSnapshot('Change 1', []);
        result.current.recordSnapshot('Change 2', []);
        result.current.undo(); // Now can redo
      });

      expect(result.current.canRedo).toBe(true);

      // WHEN: Recording new snapshot from middle of history
      act(() => {
        result.current.recordSnapshot('New branch', []);
      });

      // THEN: Redo disabled (history forked)
      expect(result.current.canRedo).toBe(false);
      expect(result.current.snapshot.content).toBe('New branch');
    });
  });

  describe('[P2] History Buffer Limit', () => {
    it('should maintain maximum 10 snapshots in history', () => {
      // GIVEN: Hook with initial snapshot
      const { result } = renderHook(() => useDraftUndo(initialContent, initialCitations));

      // WHEN: Recording 15 snapshots (exceeds 10 buffer)
      act(() => {
        for (let i = 1; i <= 15; i++) {
          result.current.recordSnapshot(`Change ${i}`, []);
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

      // THEN: Stops at oldest in buffer (Change 5 since buffer holds 10 past + 1 present)
      // Buffer: [Change 5, 6, 7, 8, 9, 10, 11, 12, 13, 14] + present=Change 15
      // After 10 undos: present=Change 5, past=[]
      expect(result.current.snapshot.content).toBe('Change 5');
      expect(result.current.canUndo).toBe(false);
    });
  });

  describe('[P2] Citation Preservation in Undo/Redo', () => {
    it('should preserve citations when undoing', () => {
      // GIVEN: Snapshots with different citations
      const { result } = renderHook(() => useDraftUndo(initialContent, initialCitations));

      const citation1: Citation = {
        number: 1,
        document_id: 'doc-1',
        document_name: 'test.pdf',
        page_number: 5,
        excerpt: 'Test excerpt text',
        char_start: 0,
        char_end: 100,
        confidence: 0.9,
      };

      const citation2: Citation = {
        number: 2,
        document_id: 'doc-2',
        document_name: 'auth.pdf',
        page_number: 10,
        excerpt: 'Auth excerpt text',
        char_start: 200,
        char_end: 300,
        confidence: 0.95,
      };

      act(() => {
        result.current.recordSnapshot('Content with [1]', [citation1]);
        result.current.recordSnapshot('Content with [1] and [2]', [citation1, citation2]);
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
