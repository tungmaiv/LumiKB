'use client';

import * as React from 'react';

import { cn } from '@/lib/utils';

interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

/**
 * Native CSS ScrollArea component - replacement for Radix ScrollArea
 * that is compatible with React 19.
 *
 * Uses native CSS overflow-auto with custom scrollbar styling.
 */
function ScrollArea({ className, children, ...props }: ScrollAreaProps) {
  return (
    <div
      data-slot="scroll-area"
      className={cn(
        'relative overflow-auto',
        // Custom scrollbar styling
        '[&::-webkit-scrollbar]:w-2.5',
        '[&::-webkit-scrollbar-track]:bg-transparent',
        '[&::-webkit-scrollbar-thumb]:rounded-full',
        '[&::-webkit-scrollbar-thumb]:bg-border',
        '[&::-webkit-scrollbar-thumb:hover]:bg-border/80',
        // Firefox scrollbar
        'scrollbar-thin scrollbar-track-transparent scrollbar-thumb-border',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

interface ScrollBarProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: 'vertical' | 'horizontal';
}

/**
 * ScrollBar component - kept for API compatibility but not rendered
 * since native scrollbars are styled via CSS.
 */
function ScrollBar({ orientation = 'vertical', ...props }: ScrollBarProps) {
  // Native scrollbars are styled via CSS on the ScrollArea
  // This component is kept for API compatibility
  return null;
}

export { ScrollArea, ScrollBar };
