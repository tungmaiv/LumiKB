/**
 * GenerateButton Component - Epic 4, Story 4.4
 * Primary action button for triggering document generation
 */

import { Button } from '@/components/ui/button';
import { FileText, Loader2 } from 'lucide-react';

export interface GenerateButtonProps {
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  hasResults?: boolean;
}

/**
 * Primary button for initiating document generation
 * Shows loading state and is disabled when no search results
 */
export function GenerateButton({
  onClick,
  disabled = false,
  loading = false,
  hasResults = true,
}: GenerateButtonProps) {
  const isDisabled = disabled || loading || !hasResults;

  return (
    <Button
      data-testid="generate-button"
      onClick={onClick}
      disabled={isDisabled}
      className="w-full sm:w-auto"
      size="lg"
    >
      {loading ? (
        <>
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          Generating...
        </>
      ) : (
        <>
          <FileText className="w-4 h-4 mr-2" />
          Generate Draft
        </>
      )}
    </Button>
  );
}
