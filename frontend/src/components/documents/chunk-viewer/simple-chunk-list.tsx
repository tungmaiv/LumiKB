/**
 * SimpleChunkList Component
 *
 * Simple expandable list of document chunks for the modal view.
 * Each chunk shows a preview (first 3 lines) and expands to full content on click.
 */

'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { useDocumentChunks } from '@/hooks/useDocumentChunks';
import { cn } from '@/lib/utils';
import type { DocumentChunk } from '@/types/chunk';

interface SimpleChunkListProps {
  /** Knowledge Base ID */
  kbId: string;
  /** Document ID */
  documentId: string;
}

const PREVIEW_LINES = 3;
const PREVIEW_CHAR_LIMIT = 200;

/**
 * Truncate text to preview length (first N lines or char limit).
 */
function getPreviewText(text: string): string {
  const lines = text.split('\n').slice(0, PREVIEW_LINES);
  const preview = lines.join('\n');
  if (preview.length > PREVIEW_CHAR_LIMIT) {
    return preview.slice(0, PREVIEW_CHAR_LIMIT) + '...';
  }
  if (text.split('\n').length > PREVIEW_LINES || text.length > preview.length) {
    return preview + '...';
  }
  return preview;
}

/**
 * Single expandable chunk item.
 */
function ExpandableChunkItem({ chunk }: { chunk: DocumentChunk }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const previewText = getPreviewText(chunk.text);
  const hasMoreContent = chunk.text.length > previewText.length - 3; // Account for "..."

  return (
    <div className="border rounded-lg bg-card" data-testid={`chunk-item-${chunk.chunk_index}`}>
      <button
        type="button"
        onClick={() => hasMoreContent && setIsExpanded(!isExpanded)}
        className={cn(
          'w-full text-left p-3 flex items-start gap-2',
          hasMoreContent && 'cursor-pointer hover:bg-muted/50',
          !hasMoreContent && 'cursor-default'
        )}
        disabled={!hasMoreContent}
      >
        {/* Expand/collapse icon */}
        <span className="mt-0.5 text-muted-foreground">
          {hasMoreContent ? (
            isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )
          ) : (
            <span className="w-4" />
          )}
        </span>

        <div className="flex-1 min-w-0">
          {/* Header with chunk number and metadata */}
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-muted-foreground">
              Chunk #{chunk.chunk_index + 1}
            </span>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {chunk.page_number && <span>Page {chunk.page_number}</span>}
              {chunk.section_header && (
                <span className="truncate max-w-[120px]" title={chunk.section_header}>
                  {chunk.section_header}
                </span>
              )}
            </div>
          </div>

          {/* Content - preview or full */}
          <p className="text-sm whitespace-pre-wrap break-words">
            {isExpanded ? chunk.text : previewText}
          </p>
        </div>
      </button>
    </div>
  );
}

/**
 * Simple chunk list with expandable items.
 * No search, no virtual scrolling - just a simple list for modal view.
 */
export function SimpleChunkList({ kbId, documentId }: SimpleChunkListProps) {
  const [cursor, setCursor] = useState(0);
  const [allChunks, setAllChunks] = useState<DocumentChunk[]>([]);
  const [loadedDataKey, setLoadedDataKey] = useState('');

  const { chunks, total, hasMore, isLoading, isError, error } = useDocumentChunks({
    kbId,
    documentId,
    cursor,
    limit: 50,
  });

  // Stable data key to detect changes
  const dataKey = chunks.map((c) => c.chunk_id).join(',');

  // Accumulate chunks when data changes
  if (chunks.length > 0 && dataKey !== loadedDataKey) {
    setLoadedDataKey(dataKey);
    if (cursor === 0) {
      setAllChunks(chunks);
    } else {
      const existingIds = new Set(allChunks.map((c) => c.chunk_id));
      const newChunks = chunks.filter((c) => !existingIds.has(c.chunk_id));
      if (newChunks.length > 0) {
        setAllChunks((prev) => [...prev, ...newChunks]);
      }
    }
  }

  const handleLoadMore = () => {
    if (hasMore && !isLoading) {
      setCursor((prev) => prev + 50);
    }
  };

  if (isLoading && allChunks.length === 0) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4 text-center text-sm text-destructive">
        {error?.message || 'Failed to load chunks'}
      </div>
    );
  }

  if (allChunks.length === 0) {
    return <div className="p-4 text-center text-sm text-muted-foreground">No chunks found</div>;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-1 py-2 text-xs text-muted-foreground">
        {total} {total === 1 ? 'chunk' : 'chunks'}
      </div>

      {/* Chunk list */}
      <ScrollArea className="flex-1">
        <div className="space-y-2 pr-4">
          {allChunks.map((chunk) => (
            <ExpandableChunkItem key={chunk.chunk_id} chunk={chunk} />
          ))}

          {/* Load more button */}
          {hasMore && (
            <div className="py-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={handleLoadMore}
                disabled={isLoading}
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <ChevronDown className="h-4 w-4 mr-2" />
                )}
                Load more chunks
              </Button>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
