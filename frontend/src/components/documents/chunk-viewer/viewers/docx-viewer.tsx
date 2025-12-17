/**
 * DOCXViewer Component (Story 5-26)
 *
 * Renders DOCX documents using HTML conversion from backend.
 * AC-5.26.4: Content pane renders document based on type (DOCX)
 * AC-5.26.6: Click chunk scrolls to position in document
 */

'use client';

import { useEffect, useRef } from 'react';
import DOMPurify from 'dompurify';
import { Loader2 } from 'lucide-react';

interface DOCXViewerProps {
  /** HTML content from mammoth conversion */
  html: string | null;
  /** Plain text content (fallback) */
  text?: string | null;
  /** Character range to scroll to */
  highlightRange?: { start: number; end: number } | null;
  /** Loading state */
  isLoading?: boolean;
  /** Error message */
  error?: string | null;
}

/**
 * DOCX document viewer using sanitized HTML.
 *
 * Features:
 * - Renders mammoth-converted HTML
 * - Sanitizes HTML with DOMPurify
 * - Falls back to plain text if no HTML
 * - Scroll to highlight range
 * - Styled with document-like appearance
 */
export function DOCXViewer({
  html,
  text,
  highlightRange,
  isLoading = false,
  error,
}: DOCXViewerProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  // Scroll to highlighted section when range changes
  useEffect(() => {
    if (highlightRange && contentRef.current && text) {
      // For DOCX, we estimate position based on text length
      // This is approximate since HTML adds formatting
      const totalHeight = contentRef.current.scrollHeight;
      const totalChars = text.length;
      const ratio = highlightRange.start / totalChars;
      const scrollPosition = ratio * totalHeight;

      contentRef.current.scrollTo({
        top: Math.max(0, scrollPosition - 100),
        behavior: 'smooth',
      });
    }
  }, [highlightRange, text]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full" data-testid="docx-viewer-loading">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex flex-col items-center justify-center h-full text-center p-4"
        data-testid="docx-viewer-error"
      >
        <div className="text-destructive mb-2">Failed to load document</div>
        <div className="text-sm text-muted-foreground">{error}</div>
      </div>
    );
  }

  // Sanitize HTML content
  const sanitizedHtml = html
    ? DOMPurify.sanitize(html, {
        ALLOWED_TAGS: [
          'p',
          'br',
          'strong',
          'b',
          'em',
          'i',
          'u',
          'h1',
          'h2',
          'h3',
          'h4',
          'h5',
          'h6',
          'ul',
          'ol',
          'li',
          'table',
          'thead',
          'tbody',
          'tr',
          'th',
          'td',
          'a',
          'span',
          'div',
          'img',
        ],
        ALLOWED_ATTR: ['href', 'src', 'alt', 'class', 'style'],
      })
    : null;

  return (
    <div
      className="h-full overflow-y-auto overflow-x-hidden"
      ref={contentRef}
      style={{ overscrollBehavior: 'contain' }}
      data-testid="docx-viewer"
      data-scroll-container
    >
      <div className="p-6 max-w-4xl mx-auto">
        {/* Document-like container */}
        <div className="bg-card shadow-lg rounded-lg p-8 min-h-[600px] text-card-foreground">
          {sanitizedHtml ? (
            <div
              className="docx-content prose prose-sm prose-gray dark:prose-invert max-w-none"
              dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
            />
          ) : text ? (
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-card-foreground">
              {text}
            </pre>
          ) : (
            <div className="text-muted-foreground text-center">No content available</div>
          )}
        </div>
      </div>

      {/* DOCX-specific styles using CSS variables for theme support */}
      <style jsx global>{`
        .docx-content {
          font-family: 'Calibri', 'Arial', sans-serif;
          line-height: 1.6;
          color: inherit;
        }
        .docx-content h1 {
          font-size: 1.5rem;
          font-weight: 600;
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
          color: inherit;
        }
        .docx-content h2 {
          font-size: 1.25rem;
          font-weight: 600;
          margin-top: 1.25rem;
          margin-bottom: 0.5rem;
          color: inherit;
        }
        .docx-content h3,
        .docx-content h4,
        .docx-content h5,
        .docx-content h6 {
          color: inherit;
        }
        .docx-content p {
          margin-bottom: 0.75rem;
          color: inherit;
        }
        .docx-content table {
          border-collapse: collapse;
          width: 100%;
          margin: 1rem 0;
        }
        .docx-content th,
        .docx-content td {
          border: 1px solid var(--border);
          padding: 0.5rem;
          text-align: left;
        }
        .docx-content th {
          background-color: var(--muted);
          font-weight: 600;
        }
        .docx-content ul,
        .docx-content ol {
          padding-left: 1.5rem;
          margin-bottom: 0.75rem;
        }
        .docx-content li {
          margin-bottom: 0.25rem;
        }
        .docx-content img {
          max-width: 100%;
          height: auto;
        }
        .docx-content a {
          color: var(--primary);
        }
      `}</style>
    </div>
  );
}
