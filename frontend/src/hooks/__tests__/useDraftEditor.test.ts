/**
 * Unit tests for useDraftEditor hook
 * Updated: 2025-12-04 (Story 5.15 - ATDD Transition to GREEN)
 *
 * Tests auto-save, content updates, citation management.
 *
 * Coverage Target: 80%+
 */

import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useDraftEditor } from '../useDraftEditor';
import * as draftsApi from '../../lib/api/drafts';
import type { Citation } from '@/types/citation';

// Mock the drafts API
vi.mock('../../lib/api/drafts', () => ({
  updateDraft: vi.fn(),
  calculateWordCount: vi.fn((content: string) => content.split(/\s+/).filter(Boolean).length),
}));

describe('useDraftEditor', () => {
  const mockCitation: Citation = {
    number: 1,
    document_id: 'doc-1',
    document_name: 'auth.pdf',
    page_number: 10,
    excerpt: 'OAuth 2.0 provides...',
    char_start: 0,
    char_end: 50,
    confidence: 0.95,
  };

  const defaultOptions = {
    draftId: 'draft-123',
    initialContent: 'OAuth 2.0 [1] is secure',
    initialCitations: [mockCitation],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    (draftsApi.updateDraft as ReturnType<typeof vi.fn>).mockResolvedValue({});
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  describe('[P1] Content Updates', () => {
    it('should update content when setContent is called', () => {
      // GIVEN: useDraftEditor with initial options
      const { result } = renderHook(() => useDraftEditor(defaultOptions));

      // WHEN: Updating content
      act(() => {
        result.current.setContent('Updated OAuth 2.0 [1] content');
      });

      // THEN: Content updated in state
      expect(result.current.content).toBe('Updated OAuth 2.0 [1] content');
    });

    it('should mark content as dirty when changed', () => {
      // GIVEN: useDraftEditor
      const { result } = renderHook(() => useDraftEditor(defaultOptions));

      expect(result.current.isDirty).toBe(false);

      // WHEN: Updating content
      act(() => {
        result.current.setContent('New content');
      });

      // THEN: isDirty becomes true
      expect(result.current.isDirty).toBe(true);
    });

    it('should preserve citations when content updated', () => {
      // GIVEN: useDraftEditor with citations
      const { result } = renderHook(() => useDraftEditor(defaultOptions));

      const initialCitations = result.current.citations;
      expect(initialCitations).toHaveLength(1);

      // WHEN: Updating content
      act(() => {
        result.current.setContent('Modified content [1]');
      });

      // THEN: Citations preserved
      expect(result.current.citations).toEqual(initialCitations);
      expect(result.current.citations).toHaveLength(1);
    });
  });

  describe('[P1] Auto-Save', () => {
    it('should trigger auto-save 5 seconds after content change', async () => {
      // GIVEN: useDraftEditor
      const { result } = renderHook(() => useDraftEditor(defaultOptions));

      // WHEN: Updating content
      act(() => {
        result.current.setContent('Auto-save test');
      });

      // THEN: Auto-save not called immediately
      expect(draftsApi.updateDraft).not.toHaveBeenCalled();

      // WHEN: 5 seconds pass (debounce timer)
      await act(async () => {
        vi.advanceTimersByTime(5000);
        // Allow microtasks to flush
        await Promise.resolve();
      });

      // THEN: Auto-save triggered
      expect(draftsApi.updateDraft).toHaveBeenCalledWith(
        'draft-123',
        expect.objectContaining({
          content: 'Auto-save test',
        })
      );
    });

    it('should debounce multiple content changes within 5 seconds', async () => {
      // GIVEN: useDraftEditor
      const { result } = renderHook(() => useDraftEditor(defaultOptions));

      // WHEN: Multiple content changes within 5 seconds
      act(() => {
        result.current.setContent('Change 1');
      });

      act(() => {
        vi.advanceTimersByTime(2000);
      });

      act(() => {
        result.current.setContent('Change 2');
      });

      act(() => {
        vi.advanceTimersByTime(2000);
      });

      act(() => {
        result.current.setContent('Change 3');
      });

      // Clear any previous calls
      (draftsApi.updateDraft as ReturnType<typeof vi.fn>).mockClear();

      // THEN: Only last change saved (after 5s from last edit)
      await act(async () => {
        vi.advanceTimersByTime(5000);
        await Promise.resolve();
      });

      expect(draftsApi.updateDraft).toHaveBeenCalledWith(
        'draft-123',
        expect.objectContaining({
          content: 'Change 3',
        })
      );
    });

    it('should update lastSaved after successful save', async () => {
      // GIVEN: useDraftEditor
      const { result } = renderHook(() => useDraftEditor(defaultOptions));

      expect(result.current.lastSaved).toBeNull();

      // WHEN: Content changes and auto-save triggers
      act(() => {
        result.current.setContent('Save status test');
      });

      await act(async () => {
        vi.advanceTimersByTime(5000);
        await Promise.resolve();
      });

      // THEN: lastSaved is updated
      expect(result.current.lastSaved).not.toBeNull();
    });
  });

  describe('[P2] Manual Save', () => {
    it('should allow manual save before auto-save timer', async () => {
      // GIVEN: useDraftEditor with changed content
      const { result } = renderHook(() => useDraftEditor(defaultOptions));

      act(() => {
        result.current.setContent('Manual save test');
      });

      // WHEN: Manually saving (simulate Ctrl+S)
      await act(async () => {
        await result.current.saveNow();
      });

      // THEN: Save triggered immediately
      expect(draftsApi.updateDraft).toHaveBeenCalledWith(
        'draft-123',
        expect.objectContaining({
          content: 'Manual save test',
        })
      );
    });
  });

  describe('[P1] Citation Management', () => {
    it('should update citations when setCitations called', () => {
      // GIVEN: useDraftEditor
      const { result } = renderHook(() => useDraftEditor(defaultOptions));

      const newCitation: Citation = {
        number: 2,
        document_id: 'doc-2',
        document_name: 'security.pdf',
        page_number: 20,
        excerpt: 'Security best practices...',
        char_start: 100,
        char_end: 150,
        confidence: 0.88,
      };

      // WHEN: Adding new citation
      act(() => {
        result.current.setCitations([...result.current.citations, newCitation]);
      });

      // THEN: Citations updated
      expect(result.current.citations).toHaveLength(2);
      expect(result.current.citations[1]).toEqual(newCitation);
    });

    it('should remove citation by filtering setCitations', () => {
      // GIVEN: useDraftEditor with 2 citations
      const citation2: Citation = {
        number: 2,
        document_id: 'doc-2',
        document_name: 'test.pdf',
        page_number: 5,
        excerpt: 'Test snippet',
        char_start: 200,
        char_end: 250,
        confidence: 0.9,
      };

      const { result } = renderHook(() =>
        useDraftEditor({
          ...defaultOptions,
          initialCitations: [mockCitation, citation2],
        })
      );

      expect(result.current.citations).toHaveLength(2);

      // WHEN: Removing citation 1 via setCitations filter
      act(() => {
        result.current.setCitations(result.current.citations.filter((c) => c.number !== 1));
      });

      // THEN: Citation removed
      expect(result.current.citations).toHaveLength(1);
      expect(result.current.citations[0].number).toBe(2);
    });
  });

  describe('[P2] Saving State', () => {
    it('should track isSaving during save operation', async () => {
      // GIVEN: useDraftEditor with pending save
      let resolveUpdate: () => void;
      (draftsApi.updateDraft as ReturnType<typeof vi.fn>).mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveUpdate = resolve as () => void;
          })
      );

      const { result } = renderHook(() => useDraftEditor(defaultOptions));

      // WHEN: Trigger save by changing content and advancing timer
      act(() => {
        result.current.setContent('Saving state test');
      });

      // Advance timer to trigger debounce, but don't await the promise yet
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      // Flush microtasks so the save starts
      await act(async () => {
        await Promise.resolve();
      });

      // THEN: isSaving is true during save
      expect(result.current.isSaving).toBe(true);

      // WHEN: Save completes
      await act(async () => {
        resolveUpdate!();
        await Promise.resolve();
      });

      // THEN: isSaving becomes false
      expect(result.current.isSaving).toBe(false);
    });
  });
});
