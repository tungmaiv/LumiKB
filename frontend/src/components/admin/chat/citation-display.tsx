/**
 * Citation Display Component
 *
 * Story 9-9: Chat History Viewer UI
 * AC4: Citations displayed inline with clickable source links to documents
 */
'use client';

import { FileText } from 'lucide-react';
import Link from 'next/link';

import type { Citation } from '@/hooks/useChatHistory';

interface CitationDisplayProps {
  citations: Citation[];
}

/**
 * Format relevance score as percentage
 */
function formatScore(score: number | null): string {
  if (score === null) return '';
  return `${Math.round(score * 100)}%`;
}

export function CitationDisplay({ citations }: CitationDisplayProps) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-3 border-t pt-2">
      <p className="text-xs font-medium mb-2 text-muted-foreground flex items-center gap-1">
        <FileText className="h-3 w-3" />
        Sources ({citations.length})
      </p>
      <div className="flex flex-wrap gap-2">
        {citations.map((citation) => {
          const href = citation.chunk_id
            ? `/documents/${citation.document_id}?chunk=${citation.chunk_id}`
            : `/documents/${citation.document_id}`;

          return (
            <Link
              key={citation.index}
              href={href}
              className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-muted rounded hover:bg-muted/80 transition-colors"
              data-testid={`citation-link-${citation.index}`}
            >
              <span className="font-medium">[{citation.index}]</span>
              <span className="truncate max-w-[150px]">
                {citation.document_name || 'Document'}
              </span>
              {citation.relevance_score !== null && (
                <span className="text-muted-foreground">
                  {formatScore(citation.relevance_score)}
                </span>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Inline citation badge for message content
 */
export function InlineCitation({
  citation,
  onClick,
}: {
  citation: Citation;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      className="inline-flex items-center text-xs px-1.5 py-0.5 bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors mx-0.5"
      onClick={onClick}
      data-testid={`inline-citation-${citation.index}`}
    >
      [{citation.index}]
    </button>
  );
}
