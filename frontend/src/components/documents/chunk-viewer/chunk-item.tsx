/**
 * ChunkItem Component (Story 5-26)
 *
 * Displays a single chunk in the sidebar list.
 * AC-5.26.3: Chunk sidebar displays all chunks
 * AC-5.26.6: Click chunk scrolls to position in document
 */

'use client';

import { ChevronDown, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { DocumentChunk } from '@/types/chunk';

interface ChunkItemProps {
  /** Chunk data */
  chunk: DocumentChunk;
  /** Whether this chunk is currently selected */
  isSelected?: boolean;
  /** Whether this chunk is expanded (controlled from parent) */
  isExpanded?: boolean;
  /** Whether this chunk matches search (for highlighting) */
  isSearchMatch?: boolean;
  /** Click handler */
  onClick?: (chunk: DocumentChunk) => void;
  /** Expand/collapse toggle handler */
  onToggleExpand?: (chunkIndex: number) => void;
}

/**
 * Single chunk item in the sidebar.
 *
 * Features:
 * - Shows chunk index, preview text, and optional page/section
 * - Highlights search matches with score badge
 * - Selected state styling
 * - Accessible with keyboard navigation
 */
const PREVIEW_LENGTH = 100;

export function ChunkItem({
  chunk,
  isSelected = false,
  isExpanded = false,
  isSearchMatch = false,
  onClick,
  onToggleExpand,
}: ChunkItemProps) {
  // Check if text is long enough to need expand/collapse
  const isExpandable = chunk.text.length > PREVIEW_LENGTH;

  // Truncate text for preview (max 100 chars)
  const previewText = isExpandable ? `${chunk.text.slice(0, PREVIEW_LENGTH)}...` : chunk.text;

  const handleExpandToggle = (e: React.MouseEvent) => {
    e.stopPropagation(); // Don't trigger chunk selection
    onToggleExpand?.(chunk.chunk_index);
  };

  const handleChunkClick = () => {
    onClick?.(chunk);
  };

  return (
    <div
      className={cn(
        'w-full text-left p-3 rounded-lg border transition-colors',
        'hover:bg-muted/50',
        isSelected ? 'bg-primary/10 border-primary' : 'bg-background border-border',
        isSearchMatch && 'ring-1 ring-yellow-500/50'
      )}
      data-testid={`chunk-item-${chunk.chunk_index}`}
    >
      {/* Header row with expand toggle, index and metadata */}
      <div className="flex items-center gap-2 mb-1">
        {/* Expand/Collapse toggle */}
        {isExpandable && (
          <button
            type="button"
            onClick={handleExpandToggle}
            className="p-0.5 rounded hover:bg-muted focus:outline-none focus:ring-1 focus:ring-ring"
            aria-expanded={isExpanded}
            aria-label={isExpanded ? 'Collapse chunk' : 'Expand chunk'}
            data-testid={`chunk-toggle-${chunk.chunk_index}`}
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        )}

        {/* Chunk index - clickable to select */}
        <button
          type="button"
          onClick={handleChunkClick}
          className="text-xs font-medium text-muted-foreground hover:text-foreground focus:outline-none focus:underline"
          aria-pressed={isSelected}
        >
          Chunk #{chunk.chunk_index + 1}
        </button>

        {/* Score badge for search results */}
        {chunk.score !== null && (
          <span
            className="text-xs px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200 ml-auto"
            title="Relevance score"
          >
            {(chunk.score * 100).toFixed(0)}%
          </span>
        )}
      </div>

      {/* Text content - clickable to select chunk */}
      <button
        type="button"
        onClick={handleChunkClick}
        className="w-full text-left focus:outline-none focus:ring-1 focus:ring-ring rounded"
        aria-pressed={isSelected}
      >
        <p className={cn('text-sm text-foreground', !isExpanded && 'line-clamp-3')}>
          {isExpanded ? chunk.text : previewText}
        </p>
      </button>

      {/* Metadata row */}
      <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
        {chunk.page_number && (
          <span className="flex items-center gap-1">
            <PageIcon className="w-3 h-3" />
            Page {chunk.page_number}
          </span>
        )}
        {chunk.section_header && (
          <span className="truncate max-w-[150px]" title={chunk.section_header}>
            {chunk.section_header}
          </span>
        )}
        {/* Character range for debugging/advanced users */}
        <span className="ml-auto opacity-50" title="Character range">
          {chunk.char_start}-{chunk.char_end}
        </span>
      </div>
    </div>
  );
}

// Simple page icon component
function PageIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
      <polyline points="14,2 14,8 20,8" />
    </svg>
  );
}
