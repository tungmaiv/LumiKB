/**
 * MarkdownViewer Component (Story 5-26)
 *
 * Renders Markdown documents with syntax highlighting.
 * AC-5.26.4: Content pane renders document based on type (Markdown)
 * AC-5.26.6: Click chunk scrolls to position in document
 */

'use client';

import { useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { Loader2 } from 'lucide-react';

interface MarkdownViewerProps {
  /** Markdown content */
  content: string | null;
  /** Character range to scroll to */
  highlightRange?: { start: number; end: number } | null;
  /** Loading state */
  isLoading?: boolean;
  /** Error message */
  error?: string | null;
}

/**
 * Markdown document viewer with styled rendering.
 *
 * Features:
 * - Full Markdown support (headers, lists, code, tables)
 * - Styled prose output
 * - Scroll to highlight range
 * - Code block styling
 */
export function MarkdownViewer({
  content,
  highlightRange,
  isLoading = false,
  error,
}: MarkdownViewerProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  // Scroll to highlighted section when range changes
  useEffect(() => {
    if (highlightRange && contentRef.current && content) {
      const totalHeight = contentRef.current.scrollHeight;
      const totalChars = content.length;
      const ratio = highlightRange.start / totalChars;
      const scrollPosition = ratio * totalHeight;

      contentRef.current.scrollTo({
        top: Math.max(0, scrollPosition - 100),
        behavior: 'smooth',
      });
    }
  }, [highlightRange, content]);

  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center h-full"
        data-testid="markdown-viewer-loading"
      >
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex flex-col items-center justify-center h-full text-center p-4"
        data-testid="markdown-viewer-error"
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

  return (
    <div
      className="h-full overflow-y-auto overflow-x-hidden"
      ref={contentRef}
      style={{ overscrollBehavior: 'contain' }}
      data-testid="markdown-viewer"
      data-scroll-container
    >
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-card shadow-lg rounded-lg p-8 min-h-[600px] prose prose-sm max-w-none text-card-foreground">
          <ReactMarkdown
            components={{
              // Custom heading styles
              h1: ({ children }) => (
                <h1 className="text-2xl font-bold mt-6 mb-4 pb-2 border-b">{children}</h1>
              ),
              h2: ({ children }) => <h2 className="text-xl font-semibold mt-5 mb-3">{children}</h2>,
              h3: ({ children }) => <h3 className="text-lg font-semibold mt-4 mb-2">{children}</h3>,
              // Code blocks
              code: ({ className, children, ...props }) => {
                const isInline = !className;
                if (isInline) {
                  return (
                    <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
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
                <pre className="bg-muted rounded-lg overflow-x-auto my-4">{children}</pre>
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
              ul: ({ children }) => <ul className="list-disc pl-6 my-3 space-y-1">{children}</ul>,
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
              td: ({ children }) => <td className="border border-border px-3 py-2">{children}</td>,
              // Horizontal rule
              hr: () => <hr className="my-6 border-border" />,
              // Images
              img: ({ src, alt }) => (
                <img src={src} alt={alt || ''} className="max-w-full h-auto rounded-lg my-4" />
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
