/**
 * EnhancedMarkdownViewer Component (Story 7-30)
 *
 * Renders markdown content with precise character-based highlighting.
 * AC-7.30.2: Precise highlighting using char_start/char_end positions
 * AC-7.30.3: Highlight styling with dark mode support and auto-scroll
 */

'use client';

import { useEffect, useRef, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import { Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EnhancedMarkdownViewerProps {
  /** Markdown content */
  content: string;
  /** Character range to highlight */
  highlightRange?: {
    start: number;
    end: number;
  } | null;
  /** Loading state */
  isLoading?: boolean;
  /** Error message */
  error?: string | null;
  /** Show fallback message when no markdown */
  showFallbackMessage?: boolean;
}

interface ContentSegment {
  text: string;
  highlighted: boolean;
}

/**
 * Enhanced Markdown viewer with character-based highlighting.
 *
 * Features:
 * - Precise character offset highlighting (char_start/char_end)
 * - Auto-scroll to highlighted text
 * - Dark mode support (bg-yellow-200/dark:bg-yellow-800)
 * - Loading skeleton state
 * - Graceful error handling
 */
export function EnhancedMarkdownViewer({
  content,
  highlightRange,
  isLoading = false,
  error,
  showFallbackMessage = false,
}: EnhancedMarkdownViewerProps) {
  const highlightRef = useRef<HTMLSpanElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Scroll highlighted text into view when range changes
  useEffect(() => {
    if (highlightRange && highlightRef.current) {
      // Small delay to ensure content is rendered
      const timer = setTimeout(() => {
        highlightRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [highlightRange]);

  // Split content into segments for highlighting
  const segments = useMemo((): ContentSegment[] => {
    if (!content) {
      return [];
    }

    if (!highlightRange) {
      return [{ text: content, highlighted: false }];
    }

    const { start, end } = highlightRange;
    const result: ContentSegment[] = [];

    // Clamp values to valid range
    const safeStart = Math.max(0, Math.min(start, content.length));
    const safeEnd = Math.max(safeStart, Math.min(end, content.length));

    // Before highlight
    if (safeStart > 0) {
      result.push({ text: content.slice(0, safeStart), highlighted: false });
    }

    // Highlighted section
    if (safeEnd > safeStart) {
      result.push({ text: content.slice(safeStart, safeEnd), highlighted: true });
    }

    // After highlight
    if (safeEnd < content.length) {
      result.push({ text: content.slice(safeEnd), highlighted: false });
    }

    return result;
  }, [content, highlightRange]);

  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center h-full"
        data-testid="enhanced-markdown-viewer-loading"
      >
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex flex-col items-center justify-center h-full text-center p-4"
        data-testid="enhanced-markdown-viewer-error"
      >
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <div className="text-destructive mb-2">Failed to load markdown content</div>
        <div className="text-sm text-muted-foreground">{error}</div>
      </div>
    );
  }

  if (!content) {
    return (
      <div
        className="flex items-center justify-center h-full text-muted-foreground"
        data-testid="enhanced-markdown-viewer-empty"
      >
        No content available
      </div>
    );
  }

  return (
    <div
      className="h-full overflow-y-auto overflow-x-hidden"
      ref={containerRef}
      style={{ overscrollBehavior: 'contain' }}
      data-testid="enhanced-markdown-viewer"
      data-scroll-container
    >
      <div className="p-6 max-w-4xl mx-auto">
        {showFallbackMessage && (
          <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-700 dark:text-blue-300">
            <span className="font-medium">Enhanced view:</span> Precise chunk highlighting enabled
          </div>
        )}
        <div className="bg-card shadow-lg rounded-lg p-8 min-h-[600px] text-card-foreground">
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {segments.map((segment, index) =>
              segment.highlighted ? (
                <span
                  key={index}
                  ref={highlightRef}
                  className={cn(
                    'bg-yellow-200 dark:bg-yellow-800',
                    'rounded px-0.5',
                    'transition-colors duration-200'
                  )}
                  data-testid="highlight-segment"
                >
                  {segment.text}
                </span>
              ) : (
                <ReactMarkdown
                  key={index}
                  components={{
                    // Custom heading styles
                    h1: ({ children }) => (
                      <h1 className="text-2xl font-bold mt-6 mb-4 pb-2 border-b">
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="text-xl font-semibold mt-5 mb-3">{children}</h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-lg font-semibold mt-4 mb-2">{children}</h3>
                    ),
                    // Code blocks
                    code: ({ className, children, ...props }) => {
                      const isInline = !className;
                      if (isInline) {
                        return (
                          <code
                            className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono"
                            {...props}
                          >
                            {children}
                          </code>
                        );
                      }
                      return (
                        <code
                          className="block bg-muted p-4 rounded-lg overflow-x-auto text-sm font-mono"
                          {...props}
                        >
                          {children}
                        </code>
                      );
                    },
                    pre: ({ children }) => (
                      <pre className="bg-muted rounded-lg overflow-x-auto my-4">
                        {children}
                      </pre>
                    ),
                    // Links
                    a: ({ href, children }) => (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        {children}
                      </a>
                    ),
                    // Lists
                    ul: ({ children }) => (
                      <ul className="list-disc pl-6 my-3 space-y-1">{children}</ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal pl-6 my-3 space-y-1">{children}</ol>
                    ),
                    // Blockquotes
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-primary/30 pl-4 py-1 my-4 italic text-muted-foreground">
                        {children}
                      </blockquote>
                    ),
                    // Tables
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-4">
                        <table className="w-full border-collapse">{children}</table>
                      </div>
                    ),
                    th: ({ children }) => (
                      <th className="border border-border bg-muted px-3 py-2 text-left font-semibold">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="border border-border px-3 py-2">{children}</td>
                    ),
                    // Horizontal rule
                    hr: () => <hr className="my-6 border-border" />,
                    // Images
                    img: ({ src, alt }) => (
                      <img
                        src={src}
                        alt={alt || ''}
                        className="max-w-full h-auto rounded-lg my-4"
                      />
                    ),
                  }}
                >
                  {segment.text}
                </ReactMarkdown>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
