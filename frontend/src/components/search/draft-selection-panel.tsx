/**
 * Draft Selection Panel (Story 3.8, AC4)
 *
 * Floating summary panel showing count of selected search results.
 * Persists across page refreshes via localStorage.
 * Prepares for Epic 4 document generation workflow.
 */

'use client';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useDraftStore } from '@/lib/stores/draft-store';
import { Bookmark } from 'lucide-react';
import { toast } from 'sonner';

export function DraftSelectionPanel() {
  const { selectedResults, clearAll } = useDraftStore();

  // Hide panel when no selections (AC4)
  if (selectedResults.length === 0) {
    return null;
  }

  const handleStartDraft = () => {
    // Placeholder for Epic 4 (Story 4.4 - Document Generation Request)
    // Future: router.push('/generate?sources=' + selectedResults.map(r => r.chunkId).join(','))
    toast.info('Draft generation coming in Epic 4!', {
      duration: 4000,
      description: 'Your selected results will be available for document generation soon.',
    });
  };

  const handleClearAll = () => {
    clearAll();
    toast.success('Draft selections cleared', {
      duration: 2000,
    });
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-md" data-testid="draft-selection-panel">
      <Card className="p-4 shadow-lg border-2 border-primary/20">
        <div className="flex items-center gap-4">
          {/* Icon and count */}
          <div className="flex items-center gap-2">
            <Bookmark className="h-5 w-5 text-primary" aria-hidden="true" />
            <span className="font-medium text-sm">
              {selectedResults.length} result{selectedResults.length > 1 ? 's' : ''} selected for
              draft
            </span>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearAll}
              className="text-xs"
              aria-label="Clear all draft selections"
            >
              Clear All
            </Button>
            <Button
              size="sm"
              onClick={handleStartDraft}
              className="text-xs"
              aria-label="Start draft generation with selected results"
            >
              Start Draft
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
