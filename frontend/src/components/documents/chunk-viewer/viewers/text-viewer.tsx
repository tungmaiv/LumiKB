/**
 * TextViewer Component (Story 5-26)
 *
 * Renders plain text documents with line numbers and highlighting.
 * AC-5.26.4: Content pane renders document based on type (Text)
 * AC-5.26.6: Click chunk scrolls to position in document
 */

'use client';

import { useEffect, useRef, useMemo } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TextViewerProps {
  /** Plain text content */
  content: string | null;
  /** Character range to highlight */
  highlightRange?: { start: number; end: number } | null;
  /** Show line numbers */
  showLineNumbers?: boolean;
  /** Loading state */
  isLoading?: boolean;
  /** Error message */
  error?: string | null;
}

interface HighlightedLine {
  lineNumber: number;
  content: string;
  isHighlighted: boolean;
  highlightStart?: number;
  highlightEnd?: number;
}

/**
 * Plain text document viewer.
 *
 * Features:
 * - Line numbers (optional)
 * - Character range highlighting
 * - Scroll to highlight position
 * - Monospace font for code-like viewing
 */
export function TextViewer({
  content,
  highlightRange,
  showLineNumbers = true,
  isLoading = false,
  error,
}: TextViewerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const highlightRef = useRef<HTMLSpanElement>(null);

  // Process content into lines with highlight info
  const processedLines = useMemo((): HighlightedLine[] => {
    if (!content) return [];

    const lines = content.split('\n');
    let charIndex = 0;

    return lines.map((line, index) => {
      const lineStart = charIndex;
      const lineEnd = charIndex + line.length;
      charIndex = lineEnd + 1; // +1 for newline

      let isHighlighted = false;
      let highlightStart: number | undefined;
      let highlightEnd: number | undefined;

      if (highlightRange) {
        // Check if this line overlaps with highlight range
        if (lineStart < highlightRange.end && lineEnd > highlightRange.start) {
          isHighlighted = true;
          highlightStart = Math.max(0, highlightRange.start - lineStart);
          highlightEnd = Math.min(line.length, highlightRange.end - lineStart);
        }
      }

      return {
        lineNumber: index + 1,
        content: line,
        isHighlighted,
        highlightStart,
        highlightEnd,
      };
    });
  }, [content, highlightRange]);

  // Scroll to highlighted section
  useEffect(() => {
    if (highlightRef.current) {
      highlightRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [highlightRange]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full" data-testid="text-viewer-loading">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex flex-col items-center justify-center h-full text-center p-4"
        data-testid="text-viewer-error"
      >
        <div className="text-destructive mb-2">Failed to load document</div>
        <div className="text-sm text-muted-foreground">{error}</div>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        No content available
      </div>
    );
  }

  // Calculate line number width based on total lines
  const lineNumberWidth = Math.max(3, String(processedLines.length).length);

  return (
    <div
      className="h-full overflow-y-auto overflow-x-hidden"
      ref={scrollRef}
      style={{ overscrollBehavior: 'contain' }}
      data-testid="text-viewer"
      data-scroll-container
    >
      <div className="p-4 min-h-full">
        <div className="bg-card shadow-lg rounded-lg overflow-hidden text-card-foreground">
          <div className="font-mono text-sm leading-relaxed">
            {processedLines.map((line) => (
              <div
                key={line.lineNumber}
                className={cn(
                  'flex hover:bg-muted/30',
                  line.isHighlighted && 'bg-yellow-100 dark:bg-yellow-900/30'
                )}
              >
                {/* Line number */}
                {showLineNumbers && (
                  <span
                    className="select-none text-muted-foreground text-right pr-4 pl-2 py-0.5 bg-muted/20 border-r"
                    style={{ minWidth: `${lineNumberWidth + 2}ch` }}
                  >
                    {line.lineNumber}
                  </span>
                )}

                {/* Line content */}
                <span className="flex-1 px-4 py-0.5 whitespace-pre-wrap break-all">
                  {line.isHighlighted && line.highlightStart !== undefined ? (
                    <>
                      {line.content.slice(0, line.highlightStart)}
                      <span
                        ref={
                          line.lineNumber ===
                          processedLines.find((l) => l.isHighlighted)?.lineNumber
                            ? highlightRef
                            : undefined
                        }
                        className="bg-yellow-300 dark:bg-yellow-600 rounded px-0.5"
                      >
                        {line.content.slice(line.highlightStart, line.highlightEnd)}
                      </span>
                      {line.content.slice(line.highlightEnd)}
                    </>
                  ) : (
                    line.content || '\u00A0' // Non-breaking space for empty lines
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
