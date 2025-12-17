/**
 * useCitationValidation Hook Tests - Epic 7, Story 7-21
 * Tests for citation validation, dismissable warnings, and renumbering
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useCitationValidation, renumberCitations } from '../useCitationValidation';
import type { Citation } from '@/types/citation';

// Mock citations for testing
const mockCitations: Citation[] = [
  {
    number: 1,
    document_id: 'doc-1',
    document_name: 'Doc 1',
    excerpt: 'Excerpt 1',
    char_start: 0,
    char_end: 100,
    confidence: 0.95,
  },
  {
    number: 2,
    document_id: 'doc-2',
    document_name: 'Doc 2',
    excerpt: 'Excerpt 2',
    char_start: 100,
    char_end: 200,
    confidence: 0.9,
  },
  {
    number: 3,
    document_id: 'doc-3',
    document_name: 'Doc 3',
    excerpt: 'Excerpt 3',
    char_start: 200,
    char_end: 300,
    confidence: 0.85,
  },
];

describe('useCitationValidation', () => {
  // Use fake timers for debounce testing
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('orphaned citation detection (AC-7.21.1)', () => {
    it('detects orphaned citations in content', async () => {
      // Content references [4] which doesn't exist in citations
      const content = 'Text with [1] and [4] citations';

      const { result } = renderHook(() =>
        useCitationValidation(content, mockCitations, { debounceMs: 0 })
      );

      // Advance timers to allow debounce to complete
      act(() => {
        vi.advanceTimersByTime(10);
      });

      expect(result.current.orphanedCitations).toContain(4);
      expect(result.current.hasWarnings).toBe(true);
    });

    it('generates correct message for single orphaned citation', async () => {
      const content = 'Text with [5] citation';

      const { result } = renderHook(() =>
        useCitationValidation(content, mockCitations, { debounceMs: 0 })
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      const warning = result.current.warnings.find((w) => w.type === 'orphaned_citation');
      expect(warning?.message).toBe('Citation [5] references a missing source');
    });

    it('generates correct message for multiple orphaned citations', async () => {
      const content = 'Text with [5] and [6] citations';

      const { result } = renderHook(() =>
        useCitationValidation(content, mockCitations, { debounceMs: 0 })
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      const warning = result.current.warnings.find((w) => w.type === 'orphaned_citation');
      expect(warning?.message).toBe('Citations [5], [6] reference missing sources');
    });
  });

  describe('unused citation detection (AC-7.21.2)', () => {
    it('detects unused citations not referenced in content', async () => {
      // Content only references [1], but citations include 1, 2, 3
      const content = 'Text with only [1] citation';

      const { result } = renderHook(() =>
        useCitationValidation(content, mockCitations, { debounceMs: 0 })
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      expect(result.current.unusedCitations).toContain(2);
      expect(result.current.unusedCitations).toContain(3);
      expect(result.current.hasWarnings).toBe(true);
    });

    it('generates correct message for single unused citation', async () => {
      const citations: Citation[] = [
        {
          number: 1,
          document_id: 'doc-1',
          document_name: 'Doc 1',
          excerpt: 'Excerpt 1',
          char_start: 0,
          char_end: 100,
          confidence: 0.95,
        },
        {
          number: 2,
          document_id: 'doc-2',
          document_name: 'Doc 2',
          excerpt: 'Excerpt 2',
          char_start: 100,
          char_end: 200,
          confidence: 0.9,
        },
      ];
      const content = 'Text with only [1] citation';

      const { result } = renderHook(() =>
        useCitationValidation(content, citations, { debounceMs: 0 })
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      const warning = result.current.warnings.find((w) => w.type === 'unused_citation');
      expect(warning?.message).toBe('Source [2] is defined but never used');
    });
  });

  describe('debounced validation (AC-7.21.3)', () => {
    it('debounces validation by 500ms by default', async () => {
      const content = 'Text with [5] citation';

      const { result, rerender } = renderHook(
        ({ content }) => useCitationValidation(content, mockCitations),
        { initialProps: { content: '' } }
      );

      // Initially no orphaned citations (empty content)
      expect(result.current.orphanedCitations).toEqual([]);

      // Update content - should not immediately show warnings
      rerender({ content });

      // Before debounce completes
      expect(result.current.orphanedCitations).toEqual([]);

      // After 500ms debounce
      act(() => {
        vi.advanceTimersByTime(500);
      });

      expect(result.current.orphanedCitations).toContain(5);
    });

    it('uses custom debounce delay', async () => {
      const content = 'Text with [5] citation';

      const { result, rerender } = renderHook(
        ({ content }) => useCitationValidation(content, mockCitations, { debounceMs: 200 }),
        { initialProps: { content: '' } }
      );

      rerender({ content });

      // Should not show warnings before 200ms
      act(() => {
        vi.advanceTimersByTime(100);
      });
      expect(result.current.orphanedCitations).toEqual([]);

      // Should show warnings after 200ms
      act(() => {
        vi.advanceTimersByTime(100);
      });
      expect(result.current.orphanedCitations).toContain(5);
    });
  });

  describe('dismissable warnings (AC-7.21.5)', () => {
    it('allows dismissing a warning', async () => {
      const content = 'Text with [1] citation';

      const { result } = renderHook(() =>
        useCitationValidation(content, mockCitations, { debounceMs: 0 })
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      expect(result.current.hasWarnings).toBe(true);

      // Dismiss the unused citation warning
      act(() => {
        result.current.dismissWarning('unused_citation');
      });

      const unusedWarning = result.current.warnings.find((w) => w.type === 'unused_citation');
      expect(unusedWarning).toBeUndefined();
    });

    it('tracks dismissed state correctly', async () => {
      const content = 'Text with [1] citation';

      const { result } = renderHook(() =>
        useCitationValidation(content, mockCitations, { debounceMs: 0 })
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      expect(result.current.isWarningDismissed('unused_citation')).toBe(false);

      act(() => {
        result.current.dismissWarning('unused_citation');
      });

      expect(result.current.isWarningDismissed('unused_citation')).toBe(true);
    });

    it('can reset all dismissed warnings', async () => {
      const content = 'Text with [1] and [5] citations';

      const { result } = renderHook(() =>
        useCitationValidation(content, mockCitations, { debounceMs: 0 })
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      expect(result.current.hasWarnings).toBe(true);

      // Dismiss all warnings
      act(() => {
        result.current.dismissWarning('unused_citation');
        result.current.dismissWarning('orphaned_citation');
      });

      expect(result.current.hasWarnings).toBe(false);

      // Reset dismissed
      act(() => {
        result.current.resetDismissed();
      });

      expect(result.current.hasWarnings).toBe(true);
    });

    it('warning reappears if issue recurs after edit', async () => {
      const { result, rerender } = renderHook(
        ({ content }) => useCitationValidation(content, mockCitations, { debounceMs: 0 }),
        { initialProps: { content: 'Text with [1] citation' } }
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      // Dismiss unused citation warning
      act(() => {
        result.current.dismissWarning('unused_citation');
      });

      expect(result.current.hasWarnings).toBe(false);

      // Edit content to use all citations, then back to using only [1]
      rerender({ content: 'Text with [1], [2], [3]' });
      act(() => {
        vi.advanceTimersByTime(10);
      });

      rerender({ content: 'Text with [1] only' });
      act(() => {
        vi.advanceTimersByTime(10);
      });

      // Warning should reappear (different citation numbers)
      expect(result.current.unusedCitations).toContain(2);
      expect(result.current.unusedCitations).toContain(3);
    });
  });

  describe('no warnings scenario', () => {
    it('returns no warnings when all citations are valid', async () => {
      const content = 'Text with [1], [2], and [3] citations';

      const { result } = renderHook(() =>
        useCitationValidation(content, mockCitations, { debounceMs: 0 })
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      expect(result.current.hasWarnings).toBe(false);
      expect(result.current.warnings).toHaveLength(0);
      expect(result.current.orphanedCitations).toEqual([]);
      expect(result.current.unusedCitations).toEqual([]);
    });

    it('handles empty content', async () => {
      const { result } = renderHook(() =>
        useCitationValidation('', mockCitations, { debounceMs: 0 })
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      // All citations are unused
      expect(result.current.unusedCitations).toEqual([1, 2, 3]);
    });

    it('handles empty citations', async () => {
      const { result } = renderHook(() =>
        useCitationValidation('Text with [1] citation', [], { debounceMs: 0 })
      );

      act(() => {
        vi.advanceTimersByTime(10);
      });

      // Citation [1] is orphaned
      expect(result.current.orphanedCitations).toEqual([1]);
    });
  });
});

describe('renumberCitations', () => {
  it('removes specified citations and renumbers remaining', () => {
    const content = 'Text with [1] and [2] and [3] citations';
    const citations: Citation[] = [
      {
        number: 1,
        document_id: 'doc-1',
        document_name: 'Doc 1',
        excerpt: 'Excerpt 1',
        char_start: 0,
        char_end: 100,
        confidence: 0.95,
      },
      {
        number: 2,
        document_id: 'doc-2',
        document_name: 'Doc 2',
        excerpt: 'Excerpt 2',
        char_start: 100,
        char_end: 200,
        confidence: 0.9,
      },
      {
        number: 3,
        document_id: 'doc-3',
        document_name: 'Doc 3',
        excerpt: 'Excerpt 3',
        char_start: 200,
        char_end: 300,
        confidence: 0.85,
      },
    ];

    const result = renumberCitations(content, citations, [2]);

    // Citation [2] should be removed, [3] should become [2]
    expect(result.content).toBe('Text with [1] and  and [2] citations');
    expect(result.citations).toHaveLength(2);
    expect(result.citations[0].number).toBe(1);
    expect(result.citations[1].number).toBe(2);
    expect(result.citations[1].document_id).toBe('doc-3'); // Original doc-3
  });

  it('handles removing first citation', () => {
    const content = 'Start [1] middle [2] end [3]';
    const citations: Citation[] = [
      {
        number: 1,
        document_id: 'doc-1',
        document_name: 'Doc 1',
        excerpt: 'Excerpt 1',
        char_start: 0,
        char_end: 100,
        confidence: 0.95,
      },
      {
        number: 2,
        document_id: 'doc-2',
        document_name: 'Doc 2',
        excerpt: 'Excerpt 2',
        char_start: 100,
        char_end: 200,
        confidence: 0.9,
      },
      {
        number: 3,
        document_id: 'doc-3',
        document_name: 'Doc 3',
        excerpt: 'Excerpt 3',
        char_start: 200,
        char_end: 300,
        confidence: 0.85,
      },
    ];

    const result = renumberCitations(content, citations, [1]);

    expect(result.content).toBe('Start  middle [1] end [2]');
    expect(result.citations).toHaveLength(2);
    expect(result.citations[0].number).toBe(1);
    expect(result.citations[0].document_id).toBe('doc-2');
    expect(result.citations[1].number).toBe(2);
    expect(result.citations[1].document_id).toBe('doc-3');
  });

  it('handles removing multiple citations', () => {
    const content = '[1] and [2] and [3] and [4]';
    const citations: Citation[] = [
      {
        number: 1,
        document_id: 'doc-1',
        document_name: 'Doc 1',
        excerpt: 'Excerpt 1',
        char_start: 0,
        char_end: 100,
        confidence: 0.95,
      },
      {
        number: 2,
        document_id: 'doc-2',
        document_name: 'Doc 2',
        excerpt: 'Excerpt 2',
        char_start: 100,
        char_end: 200,
        confidence: 0.9,
      },
      {
        number: 3,
        document_id: 'doc-3',
        document_name: 'Doc 3',
        excerpt: 'Excerpt 3',
        char_start: 200,
        char_end: 300,
        confidence: 0.85,
      },
      {
        number: 4,
        document_id: 'doc-4',
        document_name: 'Doc 4',
        excerpt: 'Excerpt 4',
        char_start: 300,
        char_end: 400,
        confidence: 0.8,
      },
    ];

    const result = renumberCitations(content, citations, [2, 3]);

    expect(result.content).toBe('[1] and  and  and [2]');
    expect(result.citations).toHaveLength(2);
    expect(result.citations[0].number).toBe(1);
    expect(result.citations[0].document_id).toBe('doc-1');
    expect(result.citations[1].number).toBe(2);
    expect(result.citations[1].document_id).toBe('doc-4');
  });

  it('handles empty numbersToRemove', () => {
    const content = 'Text [1] and [2]';
    const citations: Citation[] = [
      {
        number: 1,
        document_id: 'doc-1',
        document_name: 'Doc 1',
        excerpt: 'Excerpt 1',
        char_start: 0,
        char_end: 100,
        confidence: 0.95,
      },
      {
        number: 2,
        document_id: 'doc-2',
        document_name: 'Doc 2',
        excerpt: 'Excerpt 2',
        char_start: 100,
        char_end: 200,
        confidence: 0.9,
      },
    ];

    const result = renumberCitations(content, citations, []);

    expect(result.content).toBe(content);
    expect(result.citations).toEqual(citations);
  });

  it('handles multiple occurrences of same citation', () => {
    const content = 'First [1] and again [1] then [2]';
    const citations: Citation[] = [
      {
        number: 1,
        document_id: 'doc-1',
        document_name: 'Doc 1',
        excerpt: 'Excerpt 1',
        char_start: 0,
        char_end: 100,
        confidence: 0.95,
      },
      {
        number: 2,
        document_id: 'doc-2',
        document_name: 'Doc 2',
        excerpt: 'Excerpt 2',
        char_start: 100,
        char_end: 200,
        confidence: 0.9,
      },
    ];

    const result = renumberCitations(content, citations, [1]);

    expect(result.content).toBe('First  and again  then [1]');
    expect(result.citations).toHaveLength(1);
    expect(result.citations[0].number).toBe(1);
    expect(result.citations[0].document_id).toBe('doc-2');
  });
});
