/**
 * useViewModePreference Hook (Story 7-31)
 *
 * Manages view mode preference with localStorage persistence.
 *
 * AC-7.31.2: Default Mode - defaults to markdown when available
 * AC-7.31.4: Preference Persistence - saves to localStorage
 */

import { useState, useCallback, useMemo } from 'react';

const STORAGE_KEY = 'lumikb-chunk-viewer-mode';

export type ViewMode = 'original' | 'markdown';

/**
 * Get stored preference from localStorage (client-side only)
 */
function getStoredPreference(): ViewMode | null {
  if (typeof window === 'undefined') return null;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'original' || stored === 'markdown') {
    return stored;
  }
  return null;
}

/**
 * Compute the initial view mode based on availability and stored preference.
 * AC-7.31.2: Default to markdown when available
 */
function computeViewMode(markdownAvailable: boolean): ViewMode {
  const stored = getStoredPreference();

  if (markdownAvailable) {
    // Default to markdown if available, unless user explicitly chose original
    return stored === 'original' ? 'original' : 'markdown';
  }
  // Force original if markdown unavailable
  return 'original';
}

/**
 * Hook for managing view mode preference with localStorage persistence.
 *
 * Behavior:
 * - Defaults to 'markdown' when markdown is available
 * - Falls back to 'original' when markdown unavailable
 * - Respects stored preference if user explicitly chose 'original'
 * - Persists preference changes to localStorage
 *
 * @param markdownAvailable - Whether markdown content is available for the document
 * @returns Object with viewMode and setViewMode
 *
 * @example
 * const { viewMode, setViewMode } = useViewModePreference(markdownAvailable);
 *
 * // In toggle:
 * <ViewModeToggle value={viewMode} onChange={setViewMode} />
 */
export function useViewModePreference(markdownAvailable: boolean) {
  // Use useMemo to compute initial value based on markdownAvailable changes
  // This avoids the need for useEffect + setState pattern
  const computedMode = useMemo(() => computeViewMode(markdownAvailable), [markdownAvailable]);

  // State tracks user's explicit selection within the session
  const [userSelectedMode, setUserSelectedMode] = useState<ViewMode | null>(null);

  // Effective view mode: user selection takes precedence if valid
  const viewMode = useMemo(() => {
    // If user has made a selection this session
    if (userSelectedMode !== null) {
      // But markdown is unavailable and they selected markdown, force original
      if (userSelectedMode === 'markdown' && !markdownAvailable) {
        return 'original';
      }
      return userSelectedMode;
    }
    // Fall back to computed mode (from localStorage or default)
    return computedMode;
  }, [userSelectedMode, computedMode, markdownAvailable]);

  // Persist preference to localStorage
  // AC-7.31.4: Save preference when changed
  const setViewMode = useCallback((mode: ViewMode) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, mode);
    }
    setUserSelectedMode(mode);
  }, []);

  return {
    viewMode,
    setViewMode,
  };
}
