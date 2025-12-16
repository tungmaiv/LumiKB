/**
 * Draft Selection Panel (Story 3.8, AC4)
 *
 * Floating summary panel showing count of selected search results.
 * Persists across page refreshes via localStorage.
 * Updated in Epic 4 Story 4.4 to trigger GenerationModal.
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { GenerationModal } from '@/components/chat/generation-modal';
import { useDraftStore } from '@/lib/stores/draft-store';
import { generateDocument } from '@/lib/api/generation';
import { Bookmark } from 'lucide-react';
import { toast } from 'sonner';

interface DraftSelectionPanelProps {
  kbId: string;
}

export function DraftSelectionPanel({ kbId }: DraftSelectionPanelProps) {
  const { selectedResults, clearAll } = useDraftStore();
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Hide panel when no selections (AC4)
  if (selectedResults.length === 0) {
    return null;
  }

  const handleStartDraft = () => {
    // Open generation modal (Story 4.4)
    setIsModalOpen(true);
  };

  const handleClearAll = () => {
    clearAll();
    toast.success('Draft selections cleared', {
      duration: 2000,
    });
  };

  const handleGenerate = async (data: { mode: string; additionalPrompt: string }) => {
    try {
      const chunkIds = selectedResults.map((r) => r.chunkId);

      const response = await generateDocument({
        kbId,
        mode: data.mode as
          | 'rfp_response'
          | 'technical_checklist'
          | 'requirements_summary'
          | 'custom',
        additionalPrompt: data.additionalPrompt,
        selectedChunkIds: chunkIds,
      });

      toast.success('Document generated successfully!', {
        duration: 4000,
        description: `Generated ${response.mode} with ${response.sourcesUsed} sources (confidence: ${Math.round(response.confidence * 100)}%)`,
      });

      // TODO: Navigate to document view or download
      console.log('Generated document:', response);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to generate document';
      toast.error('Generation failed', {
        duration: 5000,
        description: message,
      });
      throw error; // Re-throw for modal error handling
    }
  };

  return (
    <>
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

      {/* Generation Modal */}
      <GenerationModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        kbId={kbId}
        onSubmit={handleGenerate}
      />
    </>
  );
}
