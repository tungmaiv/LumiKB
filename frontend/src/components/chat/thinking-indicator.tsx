/**
 * ThinkingIndicator Component - Epic 4, Story 4.2
 * Shows animated indicator while AI is processing
 */

import { cn } from '@/lib/utils';

interface ThinkingIndicatorProps {
  className?: string;
}

export function ThinkingIndicator({ className }: ThinkingIndicatorProps) {
  return (
    <div
      data-testid="thinking-indicator"
      className={cn('flex items-center gap-2 text-muted-foreground text-sm px-4 py-3', className)}
    >
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce [animation-delay:-0.3s]" />
        <span className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce [animation-delay:-0.15s]" />
        <span className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce" />
      </div>
      <span>Thinking...</span>
    </div>
  );
}
