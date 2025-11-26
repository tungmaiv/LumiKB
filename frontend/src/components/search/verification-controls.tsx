'use client';

import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import { useVerificationStore } from '@/lib/hooks/use-verification';
import { type Citation } from './citation-card';
import { useEffect } from 'react';

interface VerificationControlsProps {
  citations: Citation[];
}

export function VerificationControls({ citations }: VerificationControlsProps) {
  const {
    currentCitationIndex,
    verifiedCitations,
    navigateNext,
    navigatePrevious,
    toggleVerified,
    exitVerification,
    isAllVerified,
    isVerifying,
  } = useVerificationStore();

  const currentCitation = citations[currentCitationIndex];
  const isVerified = currentCitation ? verifiedCitations.has(currentCitation.number) : false;
  const isFirst = currentCitationIndex === 0;
  const isLast = currentCitationIndex === citations.length - 1;

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isVerifying) return;

      switch (e.key) {
        case 'ArrowRight':
          if (!isLast) navigateNext();
          break;
        case 'ArrowLeft':
          if (!isFirst) navigatePrevious();
          break;
        case ' ':
        case 'Enter':
          if (currentCitation) {
            e.preventDefault();
            toggleVerified(currentCitation.number);
          }
          break;
        case 'Escape':
          exitVerification();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    currentCitationIndex,
    currentCitation,
    isFirst,
    isLast,
    isVerifying,
    navigateNext,
    navigatePrevious,
    toggleVerified,
    exitVerification,
  ]);

  if (!currentCitation) return null;

  return (
    <div className="flex items-center justify-between gap-4 p-4 bg-accent border-t border-b">
      {/* Progress */}
      <div className="text-sm font-medium">
        Citation {currentCitationIndex + 1} of {citations.length}
      </div>

      {/* Navigation */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={navigatePrevious}
          disabled={isFirst}
          aria-label="Previous citation"
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Previous
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={navigateNext}
          disabled={isLast}
          aria-label="Next citation"
        >
          Next
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>

      {/* Verification Checkbox */}
      <div className="flex items-center gap-2">
        <Checkbox
          id="verify-citation"
          checked={isVerified}
          onCheckedChange={() => toggleVerified(currentCitation.number)}
        />
        <label htmlFor="verify-citation" className="text-sm font-medium cursor-pointer">
          ✓ Verified
        </label>
      </div>

      {/* All Verified Message */}
      {isAllVerified() && (
        <div className="text-sm font-medium text-green-600 dark:text-green-400">
          All sources verified ✓
        </div>
      )}

      {/* Exit */}
      <Button
        variant="ghost"
        size="sm"
        onClick={exitVerification}
        aria-label="Exit verification mode"
      >
        <X className="h-4 w-4 mr-1" />
        Exit
      </Button>
    </div>
  );
}
