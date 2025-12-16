/**
 * CitationWarningBanner Component - Epic 7, Story 7-21
 * Displays validation warnings for orphaned or unused citations
 * Per AC-7.21.4 and AC-7.21.5: Shows as dismissable warning with auto-fix option
 */

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertTriangle, X, Wrench } from 'lucide-react';
import type { ValidationWarning, ValidationWarningType } from '@/hooks/useCitationValidation';

interface CitationWarningBannerProps {
  /** List of validation warnings to display */
  warnings: ValidationWarning[];
  /** Callback when user dismisses a warning (AC-7.21.5) */
  onDismiss: (type: ValidationWarningType) => void;
  /** Callback when user clicks auto-fix for unused citations */
  onAutoFix?: (numbersToRemove: number[]) => void;
  /** Whether auto-fix is available */
  showAutoFix?: boolean;
}

/**
 * Warning banner for citation validation issues.
 *
 * Displays:
 * - Orphaned citations: [n] markers without matching sources
 * - Unused citations: Sources defined but not referenced
 *
 * Features:
 * - Dismissable warnings (AC-7.21.5)
 * - Auto-fix button for unused citations
 * - Warning reappears if issue recurs after edit
 */
export function CitationWarningBanner({
  warnings,
  onDismiss,
  onAutoFix,
  showAutoFix = true,
}: CitationWarningBannerProps) {
  if (warnings.length === 0) return null;

  return (
    <div className="space-y-2 mb-4" data-testid="citation-warning-banner">
      {warnings.map((warning) => (
        <Alert
          key={warning.type}
          variant="default"
          className="bg-amber-50 border-amber-200 dark:bg-amber-950/20 dark:border-amber-800"
        >
          <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-500" />
          <AlertTitle className="text-amber-900 dark:text-amber-100">
            {warning.type === 'orphaned_citation'
              ? 'Missing Citation Source'
              : 'Unused Citation Source'}
          </AlertTitle>
          <AlertDescription className="text-amber-800 dark:text-amber-200">
            <p>{warning.message}</p>

            {/* Auto-fix button for unused citations */}
            {showAutoFix && warning.type === 'unused_citation' && onAutoFix && (
              <Button
                variant="outline"
                size="sm"
                className="mt-2 text-amber-700 border-amber-300 hover:bg-amber-100 dark:text-amber-300 dark:border-amber-700 dark:hover:bg-amber-900/30"
                onClick={() => onAutoFix(warning.citationNumbers)}
                data-testid="auto-fix-button"
              >
                <Wrench className="h-3 w-3 mr-1" />
                Remove unused {warning.citationNumbers.length === 1 ? 'source' : 'sources'}
              </Button>
            )}
          </AlertDescription>

          {/* Dismiss button (AC-7.21.5) */}
          <Button
            variant="ghost"
            size="sm"
            className="absolute top-2 right-2 h-6 w-6 p-0 text-amber-600 hover:text-amber-900 hover:bg-amber-100 dark:text-amber-400 dark:hover:text-amber-100 dark:hover:bg-amber-900/30"
            onClick={() => onDismiss(warning.type)}
            aria-label={`Dismiss ${warning.type === 'orphaned_citation' ? 'missing source' : 'unused source'} warning`}
            data-testid={`dismiss-${warning.type}`}
          >
            <X className="h-4 w-4" />
          </Button>
        </Alert>
      ))}
    </div>
  );
}

/**
 * Compact version of the warning banner for inline display
 */
export function CitationWarningInline({
  warnings,
  onDismiss,
}: Pick<CitationWarningBannerProps, 'warnings' | 'onDismiss'>) {
  if (warnings.length === 0) return null;

  const totalIssues = warnings.reduce(
    (sum, w) => sum + w.citationNumbers.length,
    0
  );

  return (
    <div
      className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400"
      data-testid="citation-warning-inline"
    >
      <AlertTriangle className="h-4 w-4" />
      <span>
        {totalIssues} citation {totalIssues === 1 ? 'issue' : 'issues'} detected
      </span>
      <Button
        variant="ghost"
        size="sm"
        className="h-5 px-1 text-amber-600 hover:text-amber-900 dark:text-amber-400 dark:hover:text-amber-100"
        onClick={() => warnings.forEach((w) => onDismiss(w.type))}
        aria-label="Dismiss all warnings"
      >
        <X className="h-3 w-3" />
      </Button>
    </div>
  );
}
