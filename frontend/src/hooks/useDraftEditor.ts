/**
 * useDraftEditor Hook - Epic 4, Story 4.6, AC1-AC4
 * Manages draft editing state, auto-save, and citation preservation
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { Citation } from '@/types/citation';
import { calculateWordCount, updateDraft } from '@/lib/api/drafts';
import { useDebounce } from './useDebounce';

export interface UseDraftEditorOptions {
  /** Draft ID for persistence */
  draftId: string;
  /** Initial content (markdown with [n] markers) */
  initialContent: string;
  /** Initial citations */
  initialCitations: Citation[];
  /** Auto-save interval in ms (default: 5000) */
  autoSaveInterval?: number;
  /** Callback when save succeeds */
  onSaveSuccess?: () => void;
  /** Callback when save fails */
  onSaveError?: (error: Error) => void;
}

export interface UseDraftEditorReturn {
  /** Current content */
  content: string;
  /** Update content (called from contentEditable onChange) */
  setContent: (value: string) => void;
  /** Current citations */
  citations: Citation[];
  /** Update citations */
  setCitations: (value: Citation[]) => void;
  /** Whether auto-save is in progress */
  isSaving: boolean;
  /** Last save timestamp */
  lastSaved: Date | null;
  /** Manually trigger save (Ctrl+S) */
  saveNow: () => Promise<void>;
  /** Whether content has unsaved changes */
  isDirty: boolean;
}

/**
 * Hook for managing draft editor state with auto-save.
 *
 * Features:
 * - Auto-save every 5s (debounced)
 * - Manual save via saveNow() (Ctrl+S)
 * - Citation preservation during edits
 * - Word count calculation
 *
 * @example
 * const editor = useDraftEditor({
 *   draftId: '123',
 *   initialContent: 'Draft text [1]',
 *   initialCitations: [citation1],
 *   onSaveSuccess: () => toast('Saved'),
 * });
 */
export function useDraftEditor({
  draftId,
  initialContent,
  initialCitations,
  autoSaveInterval = 5000,
  onSaveSuccess,
  onSaveError,
}: UseDraftEditorOptions): UseDraftEditorReturn {
  const [content, setContent] = useState(initialContent);
  const [citations, setCitations] = useState<Citation[]>(initialCitations);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  // Track initial values to detect changes
  const initialContentRef = useRef(initialContent);
  const initialCitationsRef = useRef(initialCitations);

  // Debounced content for auto-save
  const debouncedContent = useDebounce(content, autoSaveInterval);

  // Save function
  const save = useCallback(async () => {
    if (!isDirty) return; // Skip if no changes

    setIsSaving(true);

    try {
      const wordCount = calculateWordCount(content);

      await updateDraft(draftId, {
        content,
        citations,
        status: 'editing',
        word_count: wordCount,
      });

      setLastSaved(new Date());
      setIsDirty(false);
      onSaveSuccess?.();
    } catch (error) {
      console.error('Draft save failed:', error);
      onSaveError?.(error as Error);
    } finally {
      setIsSaving(false);
    }
  }, [content, citations, draftId, isDirty, onSaveSuccess, onSaveError]);

  // Auto-save when debounced content changes
  useEffect(() => {
    if (debouncedContent !== initialContentRef.current) {
      void save();
    }
  }, [debouncedContent, save]);

  // Mark as dirty when content or citations change
  useEffect(() => {
    const contentChanged = content !== initialContentRef.current;
    const citationsChanged =
      JSON.stringify(citations) !== JSON.stringify(initialCitationsRef.current);

    setIsDirty(contentChanged || citationsChanged);
  }, [content, citations]);

  // Manual save function for Ctrl+S
  const saveNow = useCallback(async () => {
    await save();
  }, [save]);

  return {
    content,
    setContent,
    citations,
    setCitations,
    isSaving,
    lastSaved,
    saveNow,
    isDirty,
  };
}
