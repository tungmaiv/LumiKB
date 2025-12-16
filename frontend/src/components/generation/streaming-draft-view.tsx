/**
 * StreamingDraftView Component - Epic 4, Story 4.5, AC2
 * Real-time draft generation view with 3-panel layout
 */

'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { X, Loader2 } from 'lucide-react';
import type { Citation } from '@/types/citation';

interface StreamingDraftViewProps {
  /** Draft content (accumulated tokens) */
  content: string;
  /** Discovered citations */
  citations: Citation[];
  /** Current status message */
  status: string | null;
  /** Overall confidence score (0-1) */
  confidence: number | null;
  /** Whether generation is in progress */
  isGenerating: boolean;
  /** Error message if generation failed */
  error: string | null;
  /** Callback to cancel generation */
  onCancel: () => void;
  /** Callback to close view */
  onClose: () => void;
}

/**
 * Renders streaming draft generation with 3-panel layout:
 * - Left: Draft content with inline citation markers
 * - Right: Citations panel
 * - Top: Status bar with progress and controls
 *
 * @example
 * <StreamingDraftView
 *   content={draftContent}
 *   citations={citationsList}
 *   status="Generating..."
 *   isGenerating={true}
 *   onCancel={handleCancel}
 *   onClose={handleClose}
 * />
 */
export function StreamingDraftView({
  content,
  citations,
  status,
  confidence,
  isGenerating,
  error,
  onCancel,
  onClose,
}: StreamingDraftViewProps) {
  const renderConfidenceBadge = () => {
    if (confidence === null) return null;

    const percentage = Math.round(confidence * 100);
    let variant: 'default' | 'destructive' | 'secondary' = 'default';
    let label = 'High';

    if (percentage < 50) {
      variant = 'destructive';
      label = 'Low';
    } else if (percentage < 80) {
      variant = 'secondary';
      label = 'Medium';
    }

    return (
      <Badge variant={variant} className="ml-auto">
        {label} Confidence ({percentage}%)
      </Badge>
    );
  };

  return (
    <div className="fixed inset-0 z-50 bg-background" data-testid="streaming-draft-view">
      {/* Header Bar */}
      <div className="border-b p-4 flex items-center gap-4">
        <div className="flex-1">
          <h2 className="text-lg font-semibold">Draft Generation</h2>
          {status && (
            <p className="text-sm text-muted-foreground flex items-center gap-2">
              {isGenerating && <Loader2 className="h-3 w-3 animate-spin" />}
              {status}
            </p>
          )}
        </div>

        {renderConfidenceBadge()}

        <div className="flex gap-2">
          {isGenerating && (
            <Button
              variant="outline"
              size="sm"
              onClick={onCancel}
              data-testid="cancel-button"
            >
              Cancel
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            data-testid="close-button"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-destructive/10 text-destructive p-4 border-b">
          <p className="text-sm font-medium">Error: {error}</p>
        </div>
      )}

      {/* 3-Panel Layout */}
      <div className="flex h-[calc(100vh-120px)]">
        {/* Left Panel: Draft Content */}
        <div className="flex-1 border-r">
          <ScrollArea className="h-full">
            <div className="p-6 prose prose-sm max-w-none" data-testid="draft-content">
              {content ? (
                <div className="whitespace-pre-wrap">{content}</div>
              ) : (
                <p className="text-muted-foreground italic">
                  Waiting for draft generation to begin...
                </p>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Right Panel: Citations */}
        <div className="w-80 border-l bg-muted/30">
          <div className="p-4 border-b">
            <h3 className="font-semibold text-sm">
              Citations ({citations.length})
            </h3>
          </div>
          <ScrollArea className="h-[calc(100%-60px)]">
            <div className="p-4 space-y-3" data-testid="citations-panel">
              {citations.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">
                  No citations yet
                </p>
              ) : (
                citations.map((citation) => (
                  <Card
                    key={citation.number}
                    className="bg-background"
                    data-testid={`citation-${citation.number}`}
                  >
                    <CardHeader className="p-3">
                      <CardTitle className="text-xs font-medium flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          [{citation.number}]
                        </Badge>
                        {citation.document_name}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-3 pt-0">
                      <div className="space-y-1">
                        {citation.page_number && (
                          <p className="text-xs text-muted-foreground">
                            Page {citation.page_number}
                          </p>
                        )}
                        {citation.section_header && (
                          <p className="text-xs text-muted-foreground">
                            {citation.section_header}
                          </p>
                        )}
                        <p className="text-xs leading-relaxed">
                          {citation.excerpt}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* Footer Progress */}
      {isGenerating && (
        <div className="border-t p-4">
          <Progress value={undefined} className="w-full" />
        </div>
      )}
    </div>
  );
}
