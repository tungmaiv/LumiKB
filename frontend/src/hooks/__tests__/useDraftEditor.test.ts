/**
 * Unit tests for useDraftEditor hook
 *
 * Tests auto-save, content updates, citation management, and status transitions.
 *
 * Coverage Target: 80%+
 * Test Count: 8
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useDraftEditor } from '../useDraftEditor';
import * as draftsApi from '../../lib/api/drafts';

// Mock the drafts API
vi.mock('../../lib/api/drafts');

describe('useDraftEditor', () => {
  const mockDraft = {
    id: 'draft-123',
    kb_id: 'kb-456',
    user_id: 'user-789',
    title: 'Test Draft',
    content: 'OAuth 2.0 [1] is secure',
    status: 'complete' as const,
    citations: [
      {
        number: 1,
        document_id: 'doc-1',
        document_name: 'auth.pdf',
        page: 10,
        chunk_index: 5,
        confidence_score: 0.95,
        snippet: 'OAuth 2.0 provides...',
      },
    ],
    word_count: 4,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('[P1] Content Updates', () => {
    it('should update content when setContent is called', () => {
      // GIVEN: useDraftEditor with initial draft
      const { result } = renderHook(() => useDraftEditor(mockDraft));

      // WHEN: Updating content
      act(() => {
        result.current.setContent('Updated OAuth 2.0 [1] content');
      });

      // THEN: Content updated in state
      expect(result.current.content).toBe('Updated OAuth 2.0 [1] content');
    });

    it('should change status to editing on first content change', () => {
      // GIVEN: Draft with status='complete'
      const { result } = renderHook(() => useDraftEditor(mockDraft));

      expect(result.current.status).toBe('complete');

      // WHEN: Updating content
      act(() => {
        result.current.setContent('New content');
      });

      // THEN: Status changes to 'editing'
      expect(result.current.status).toBe('editing');
    });

    it('should preserve citations when content updated', () => {
      // GIVEN: Draft with citations
      const { result } = renderHook(() => useDraftEditor(mockDraft));

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
      // GIVEN: useDraftEditor with mocked updateDraft API
      const mockUpdateDraft = vi.spyOn(draftsApi, 'updateDraft').mockResolvedValue(mockDraft);

      const { result } = renderHook(() => useDraftEditor(mockDraft));

      // WHEN: Updating content
      act(() => {
        result.current.setContent('Auto-save test');
      });

      // THEN: Auto-save not called immediately
      expect(mockUpdateDraft).not.toHaveBeenCalled();

      // WHEN: 5 seconds pass
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      // THEN: Auto-save triggered
      await waitFor(() => {
        expect(mockUpdateDraft).toHaveBeenCalledWith('draft-123', {
          content: 'Auto-save test',
          citations: mockDraft.citations,
          status: 'editing',
          word_count: 2,
        });
      });
    });

    it('should debounce multiple content changes within 5 seconds', async () => {
      // GIVEN: useDraftEditor
      const mockUpdateDraft = vi.spyOn(draftsApi, 'updateDraft').mockResolvedValue(mockDraft);

      const { result } = renderHook(() => useDraftEditor(mockDraft));

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

      // THEN: Only last change saved (after 5s from last edit)
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(mockUpdateDraft).toHaveBeenCalledTimes(1);
        expect(mockUpdateDraft).toHaveBeenCalledWith(
          'draft-123',
          expect.objectContaining({
            content: 'Change 3',
          })
        );
      });
    });

    it('should update save status after successful save', async () => {
      // GIVEN: useDraftEditor
      vi.spyOn(draftsApi, 'updateDraft').mockResolvedValue(mockDraft);

      const { result } = renderHook(() => useDraftEditor(mockDraft));

      // WHEN: Content changes and auto-save triggers
      act(() => {
        result.current.setContent('Save status test');
      });

      act(() => {
        vi.advanceTimersByTime(5000);
      });

      // THEN: Save status updates to 'saving' then 'saved'
      await waitFor(() => {
        expect(result.current.saveStatus).toBe('saved');
      });
    });
  });

  describe('[P2] Manual Save', () => {
    it('should allow manual save before auto-save timer', async () => {
      // GIVEN: useDraftEditor with changed content
      const mockUpdateDraft = vi.spyOn(draftsApi, 'updateDraft').mockResolvedValue(mockDraft);

      const { result } = renderHook(() => useDraftEditor(mockDraft));

      act(() => {
        result.current.setContent('Manual save test');
      });

      // WHEN: Manually saving (simulate Ctrl+S)
      await act(async () => {
        await result.current.saveNow();
      });

      // THEN: Save triggered immediately
      expect(mockUpdateDraft).toHaveBeenCalledWith(
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
      const { result } = renderHook(() => useDraftEditor(mockDraft));

      const newCitation = {
        number: 2,
        document_id: 'doc-2',
        document_name: 'security.pdf',
        page: 20,
        chunk_index: 10,
        confidence_score: 0.88,
        snippet: 'Security best practices...',
      };

      // WHEN: Adding new citation
      act(() => {
        result.current.setCitations([...result.current.citations, newCitation]);
      });

      // THEN: Citations updated
      expect(result.current.citations).toHaveLength(2);
      expect(result.current.citations[1]).toEqual(newCitation);
    });

    it('should remove citation when deleteCitation called', () => {
      // GIVEN: Draft with 2 citations
      const draftWith2Citations = {
        ...mockDraft,
        citations: [
          mockDraft.citations[0],
          {
            number: 2,
            document_id: 'doc-2',
            document_name: 'test.pdf',
            page: 5,
            chunk_index: 2,
            confidence_score: 0.9,
            snippet: 'Test snippet',
          },
        ],
      };

      const { result } = renderHook(() => useDraftEditor(draftWith2Citations));

      expect(result.current.citations).toHaveLength(2);

      // WHEN: Deleting citation 1
      act(() => {
        result.current.deleteCitation(1);
      });

      // THEN: Citation removed
      expect(result.current.citations).toHaveLength(1);
      expect(result.current.citations[0].number).toBe(2);
    });
  });

  describe('[P2] Word Count', () => {
    it('should calculate word count from content', () => {
      // GIVEN: useDraftEditor
      const { result } = renderHook(() => useDraftEditor(mockDraft));

      // WHEN: Setting content with known word count
      act(() => {
        result.current.setContent('The quick brown fox jumps over the lazy dog'); // 9 words
      });

      // THEN: Word count calculated
      expect(result.current.wordCount).toBe(9);
    });

    it('should exclude citation markers from word count', () => {
      // GIVEN: useDraftEditor
      const { result } = renderHook(() => useDraftEditor(mockDraft));

      // WHEN: Content with citation markers
      act(() => {
        result.current.setContent('OAuth 2.0 [1] is secure [2]'); // 4 words + 2 markers
      });

      // THEN: Only actual words counted (not [1] [2])
      expect(result.current.wordCount).toBe(4);
    });
  });
});
