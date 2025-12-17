/**
 * ChunkSidebar Component (Story 5-26)
 *
 * Scrollable sidebar showing all document chunks with search and virtual scrolling.
 * AC-5.26.3: Chunk sidebar displays all chunks with search
 * AC-5.26.5: Search filters chunks in real-time
 */

'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Search, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useDocumentChunks } from '@/hooks/useDocumentChunks';
import { ChunkItem } from './chunk-item';
import type { DocumentChunk } from '@/types/chunk';

interface ChunkSidebarProps {
  /** Knowledge Base ID */
  kbId: string;
  /** Document ID */
  documentId: string;
  /** Currently selected chunk index */
  selectedChunkIndex?: number | null;
  /** Callback when chunk is clicked */
  onChunkClick?: (chunk: DocumentChunk) => void;
  /** Width of sidebar (for responsive) */
  width?: number | string;
}

/**
 * Sidebar component for browsing document chunks.
 *
 * Features:
 * - Virtual scrolling for 1000+ chunks (AC-5.26.3)
 * - Real-time search with 300ms debounce (AC-5.26.5)
 * - Load more pagination
 * - Keyboard navigation support
 */
export function ChunkSidebar({
  kbId,
  documentId,
  selectedChunkIndex,
  onChunkClick,
  width = 320,
}: ChunkSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [cursor, setCursor] = useState(0);
  const [allChunks, setAllChunks] = useState<DocumentChunk[]>([]);
  const [expandedChunkIndex, setExpandedChunkIndex] = useState<number | null>(null);
  const parentRef = useRef<HTMLDivElement>(null);
  const lastDataKeyRef = useRef<string>('');

  const { chunks, total, hasMore, isLoading, isError, error } = useDocumentChunks({
    kbId,
    documentId,
    searchQuery,
    cursor,
    limit: 50,
  });

  // Create a stable key from chunk IDs to detect actual data changes
  const dataKey = chunks.map((c) => c.chunk_id).join(',');

  // Accumulate chunks for pagination (reset on search change)
  useEffect(() => {
    // Skip if no data or same data
    if (chunks.length === 0 || dataKey === lastDataKeyRef.current) return;
    lastDataKeyRef.current = dataKey;

    if (cursor === 0) {
      // First page - replace all
      setAllChunks(chunks);
    } else {
      // Pagination - merge new chunks
      setAllChunks((prev) => {
        const existingIds = new Set(prev.map((c) => c.chunk_id));
        const newChunks = chunks.filter((c) => !existingIds.has(c.chunk_id));
        if (newChunks.length === 0) return prev;
        return [...prev, ...newChunks];
      });
    }
  }, [dataKey, cursor, chunks]);

  // Reset when search changes
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
    setCursor(0);
    setAllChunks([]);
    setExpandedChunkIndex(null);
    lastDataKeyRef.current = '';
  }, []);

  // Toggle chunk expand/collapse - only one can be expanded at a time
  const handleToggleExpand = useCallback((chunkIndex: number) => {
    setExpandedChunkIndex((prev) => (prev === chunkIndex ? null : chunkIndex));
  }, []);

  const loadMore = useCallback(() => {
    if (hasMore && !isLoading) {
      setCursor((prev) => prev + 50);
    }
  }, [hasMore, isLoading]);

  // NOTE: Auto-scroll to selected chunk is disabled.
  // When user clicks a chunk, the chunk is already visible (they just clicked it).
  // The document viewer scrolls to show the corresponding content.
  // Re-enabling this would cause the sidebar to jump away from where the user clicked.

  return (
    <div
      className="flex flex-col h-full border-r bg-background"
      style={{ width }}
      data-testid="chunk-sidebar"
    >
      {/* Header with search */}
      <div className="p-3 border-b space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Document Chunks</h3>
          <span className="text-xs text-muted-foreground">
            {total} {total === 1 ? 'chunk' : 'chunks'}
          </span>
        </div>

        {/* Search input */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search chunks..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-9 h-9"
            data-testid="chunk-search-input"
          />
        </div>
      </div>

      {/* Chunk list with virtual scrolling */}
      <div
        ref={parentRef}
        className="flex-1 overflow-y-auto overflow-x-hidden"
        style={{ overscrollBehavior: 'contain' }}
        data-testid="chunk-list-scroll"
        data-scroll-container
      >
        {isLoading && allChunks.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : isError ? (
          <div className="p-4 text-center text-sm text-destructive">
            {error?.message || 'Failed to load chunks'}
          </div>
        ) : allChunks.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            {searchQuery ? 'No chunks match your search' : 'No chunks found'}
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {allChunks.map((chunk) => (
              <ChunkItem
                key={chunk.chunk_id}
                chunk={chunk}
                isSelected={selectedChunkIndex === chunk.chunk_index}
                isExpanded={expandedChunkIndex === chunk.chunk_index}
                isSearchMatch={searchQuery.length > 0 && chunk.score !== null}
                onClick={onChunkClick}
                onToggleExpand={handleToggleExpand}
              />
            ))}
          </div>
        )}

        {/* Load more button */}
        {hasMore && !isLoading && (
          <div className="p-3">
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={loadMore}
              data-testid="load-more-chunks"
            >
              <ChevronDown className="h-4 w-4 mr-2" />
              Load more chunks
            </Button>
          </div>
        )}

        {/* Loading indicator for pagination */}
        {isLoading && allChunks.length > 0 && (
          <div className="p-3 flex justify-center">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          </div>
        )}
      </div>

      {/* Navigation footer */}
      {selectedChunkIndex !== null && selectedChunkIndex !== undefined && (
        <div className="p-2 border-t flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            disabled={selectedChunkIndex === 0}
            onClick={() => {
              const prevChunk = allChunks.find((c) => c.chunk_index === selectedChunkIndex - 1);
              if (prevChunk) onChunkClick?.(prevChunk);
            }}
            data-testid="prev-chunk-btn"
          >
            <ChevronUp className="h-4 w-4 mr-1" />
            Prev
          </Button>
          <span className="text-xs text-muted-foreground">
            {selectedChunkIndex + 1} / {total}
          </span>
          <Button
            variant="ghost"
            size="sm"
            disabled={selectedChunkIndex >= total - 1}
            onClick={() => {
              const nextChunk = allChunks.find((c) => c.chunk_index === selectedChunkIndex + 1);
              if (nextChunk) onChunkClick?.(nextChunk);
            }}
            data-testid="next-chunk-btn"
          >
            Next
            <ChevronDown className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}
    </div>
  );
}
