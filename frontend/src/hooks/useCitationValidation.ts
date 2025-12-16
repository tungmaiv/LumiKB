/**
 * useCitationValidation Hook - Epic 7, Story 7-21
 * Real-time citation validation for draft editing
 * Detects orphaned citations and unused sources with debounced validation
 */

import { useMemo, useState, useCallback } from 'react';
import type { Citation } from '@/types/citation';
import { useDebounce } from './useDebounce';

/**
 * Types of validation warnings
 */
export type ValidationWarningType =
  | 'orphaned_citation'  // Citation marker [n] in content but no matching source
  | 'unused_citation';   // Source exists but marker [n] not in content

/**
 * Validation warning with details
 */
export interface ValidationWarning {
  /** Type of validation issue */
  type: ValidationWarningType;
  /** Human-readable warning message */
  message: string;
  /** Citation numbers affected */
  citationNumbers: number[];
}

/**
 * Validation result from the hook
 */
export interface CitationValidationResult {
  /** List of validation warnings */
  warnings: ValidationWarning[];
  /** Whether any warnings exist */
  hasWarnings: boolean;
  /** Orphaned citation numbers (in content but not in sources) */
  orphanedCitations: number[];
  /** Unused citation numbers (in sources but not in content) */
  unusedCitations: number[];
  /** Dismiss a specific warning type */
  dismissWarning: (type: ValidationWarningType) => void;
  /** Reset all dismissed warnings */
  resetDismissed: () => void;
  /** Whether a warning type is dismissed */
  isWarningDismissed: (type: ValidationWarningType) => boolean;
}

/**
 * Options for the citation validation hook
 */
export interface UseCitationValidationOptions {
  /** Debounce delay in ms (default: 500ms per AC-7.21.3) */
  debounceMs?: number;
}

/**
 * Extract all citation marker numbers from content.
 * Matches [n] pattern where n is one or more digits.
 */
function extractCitationMarkers(content: string): Set<number> {
  const markers = new Set<number>();
  const markerRegex = /\[(\d+)\]/g;
  let match;

  while ((match = markerRegex.exec(content)) !== null) {
    markers.add(parseInt(match[1], 10));
  }

  return markers;
}

/**
 * Hook for real-time citation validation in draft editor.
 *
 * Detects:
 * - Orphaned citations: [n] markers in content without matching source (AC-7.21.1)
 * - Unused citations: Sources defined but not referenced in content (AC-7.21.2)
 *
 * Features:
 * - Debounced validation (500ms default per AC-7.21.3)
 * - Dismissable warnings (AC-7.21.5)
 * - Warnings reappear if issue recurs after edit (AC-7.21.5)
 *
 * @param content - Draft content with [n] citation markers
 * @param citations - Array of citation objects
 * @param options - Configuration options
 * @returns Validation result with warnings and dismiss functions
 *
 * @example
 * const { warnings, hasWarnings, dismissWarning } = useCitationValidation(
 *   content,
 *   citations,
 *   { debounceMs: 500 }
 * );
 */
export function useCitationValidation(
  content: string,
  citations: Citation[],
  options: UseCitationValidationOptions = {}
): CitationValidationResult {
  const { debounceMs = 500 } = options;

  // Debounce content changes for performance (AC-7.21.3: 500ms)
  const debouncedContent = useDebounce(content, debounceMs);

  // Track dismissed warning types
  // Key: warning type, Value: set of citation numbers that were dismissed
  const [dismissedWarnings, setDismissedWarnings] = useState<
    Map<ValidationWarningType, Set<number>>
  >(new Map());

  // Calculate validation results
  const validationResult = useMemo(() => {
    // Extract markers from content
    const markersInContent = extractCitationMarkers(debouncedContent);

    // Get citation numbers from sources
    const citationNumbers = new Set(citations.map(c => c.number));

    // Find orphaned citations (in content but not in sources) - AC-7.21.1
    const orphanedCitations = [...markersInContent].filter(
      n => !citationNumbers.has(n)
    );

    // Find unused citations (in sources but not in content) - AC-7.21.2
    const unusedCitations = [...citationNumbers].filter(
      n => !markersInContent.has(n)
    );

    return { orphanedCitations, unusedCitations };
  }, [debouncedContent, citations]);

  // Build warnings list, filtering out dismissed ones
  const warnings = useMemo(() => {
    const result: ValidationWarning[] = [];
    const { orphanedCitations, unusedCitations } = validationResult;

    // Get dismissed sets for each type
    const dismissedOrphaned = dismissedWarnings.get('orphaned_citation') || new Set();
    const dismissedUnused = dismissedWarnings.get('unused_citation') || new Set();

    // Filter orphaned citations that aren't dismissed
    const activeOrphaned = orphanedCitations.filter(n => !dismissedOrphaned.has(n));
    if (activeOrphaned.length > 0) {
      result.push({
        type: 'orphaned_citation',
        message: activeOrphaned.length === 1
          ? `Citation [${activeOrphaned[0]}] references a missing source`
          : `Citations [${activeOrphaned.join('], [')}] reference missing sources`,
        citationNumbers: activeOrphaned,
      });
    }

    // Filter unused citations that aren't dismissed
    const activeUnused = unusedCitations.filter(n => !dismissedUnused.has(n));
    if (activeUnused.length > 0) {
      result.push({
        type: 'unused_citation',
        message: activeUnused.length === 1
          ? `Source [${activeUnused[0]}] is defined but never used`
          : `Sources [${activeUnused.join('], [')}] are defined but never used`,
        citationNumbers: activeUnused,
      });
    }

    return result;
  }, [validationResult, dismissedWarnings]);

  // Dismiss a warning type with current citation numbers (AC-7.21.5)
  const dismissWarning = useCallback((type: ValidationWarningType) => {
    const { orphanedCitations, unusedCitations } = validationResult;
    const numbers = type === 'orphaned_citation' ? orphanedCitations : unusedCitations;

    setDismissedWarnings(prev => {
      const next = new Map(prev);
      next.set(type, new Set(numbers));
      return next;
    });
  }, [validationResult]);

  // Reset all dismissed warnings
  const resetDismissed = useCallback(() => {
    setDismissedWarnings(new Map());
  }, []);

  // Check if a warning type is currently dismissed
  const isWarningDismissed = useCallback((type: ValidationWarningType): boolean => {
    const dismissed = dismissedWarnings.get(type);
    if (!dismissed || dismissed.size === 0) return false;

    const { orphanedCitations, unusedCitations } = validationResult;
    const currentNumbers = type === 'orphaned_citation' ? orphanedCitations : unusedCitations;

    // Warning is dismissed only if all current numbers are in dismissed set
    return currentNumbers.every(n => dismissed.has(n));
  }, [dismissedWarnings, validationResult]);

  return {
    warnings,
    hasWarnings: warnings.length > 0,
    orphanedCitations: validationResult.orphanedCitations,
    unusedCitations: validationResult.unusedCitations,
    dismissWarning,
    resetDismissed,
    isWarningDismissed,
  };
}

/**
 * Utility function to renumber citations after removing unused ones.
 * Updates both content and citations array.
 *
 * @param content - Draft content with [n] markers
 * @param citations - Current citations array
 * @param numbersToRemove - Citation numbers to remove
 * @returns Updated content and citations with sequential numbering
 */
export function renumberCitations(
  content: string,
  citations: Citation[],
  numbersToRemove: number[]
): { content: string; citations: Citation[] } {
  // Remove specified citations
  const filteredCitations = citations.filter(
    c => !numbersToRemove.includes(c.number)
  );

  // Create mapping from old numbers to new numbers
  const numberMap = new Map<number, number>();
  filteredCitations
    .sort((a, b) => a.number - b.number)
    .forEach((c, index) => {
      numberMap.set(c.number, index + 1);
    });

  // Update citation numbers
  const updatedCitations = filteredCitations.map(c => ({
    ...c,
    number: numberMap.get(c.number) || c.number,
  }));

  // Update content markers
  let updatedContent = content;

  // First, remove markers for deleted citations
  for (const num of numbersToRemove) {
    updatedContent = updatedContent.replace(
      new RegExp(`\\[${num}\\]`, 'g'),
      ''
    );
  }

  // Then, replace remaining markers with placeholders (to avoid collision)
  const sortedOldNumbers = [...numberMap.keys()].sort((a, b) => b - a);
  for (const oldNum of sortedOldNumbers) {
    const newNum = numberMap.get(oldNum);
    if (newNum !== undefined) {
      // Use a placeholder to avoid collision during renumbering
      const placeholder = `__CITATION_${oldNum}__`;
      updatedContent = updatedContent.replace(
        new RegExp(`\\[${oldNum}\\]`, 'g'),
        placeholder
      );
    }
  }

  // Finally, replace placeholders with new numbers
  for (const [oldNum, newNum] of numberMap.entries()) {
    const placeholder = `__CITATION_${oldNum}__`;
    updatedContent = updatedContent.replace(
      new RegExp(placeholder, 'g'),
      `[${newNum}]`
    );
  }

  return {
    content: updatedContent,
    citations: updatedCitations,
  };
}
