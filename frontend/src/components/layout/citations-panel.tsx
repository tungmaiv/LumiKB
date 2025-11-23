'use client';

import { ChevronLeft, ChevronRight, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

interface CitationsPanelProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
}

export function CitationsPanel({
  isCollapsed = false,
  onToggle,
}: CitationsPanelProps): React.ReactElement {
  if (isCollapsed) {
    return (
      <div className="flex h-full w-12 flex-col items-center border-l bg-muted/30 py-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className="h-8 w-8"
          aria-label="Expand citations panel"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Separator className="my-4 w-6" />
        <FileText className="h-5 w-5 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex h-full w-[320px] flex-col border-l bg-muted/30">
      {/* Header */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          <h2 className="font-semibold">Citations</h2>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className="h-8 w-8"
          aria-label="Collapse citations panel"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      <Separator />

      {/* Empty State */}
      <ScrollArea className="flex-1">
        <div className="flex h-full flex-col items-center justify-center p-6 text-center">
          <FileText className="mb-4 h-12 w-12 text-muted-foreground/50" />
          <p className="text-sm font-medium text-muted-foreground">Citations will appear here</p>
          <p className="mt-1 text-xs text-muted-foreground/70">Search to see source references</p>
          <p className="mt-1 text-xs text-muted-foreground/50">Coming in Epic 3</p>
        </div>
      </ScrollArea>
    </div>
  );
}
