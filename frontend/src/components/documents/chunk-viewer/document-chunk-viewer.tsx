/**
 * DocumentChunkViewer Component (Story 5-26)
 *
 * Main container component that orchestrates the chunk viewer experience.
 * AC-5.26.1: Modal/panel shows chunked document with split-pane layout
 * AC-5.26.2: Left side shows rendered content, right side shows chunks
 * AC-5.26.7: Responsive - sidebar collapses to bottom sheet on mobile
 */

'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { GripVertical, FileText, Loader2, ChevronUp, ChevronDown, Layers } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useDocumentContent } from '@/hooks/useDocumentContent';
import { ChunkSidebar } from './chunk-sidebar';
import { PDFViewer, DOCXViewer, MarkdownViewer, TextViewer } from './viewers';
import type { DocumentChunk } from '@/types/chunk';
import { cn } from '@/lib/utils';
import { getMimeType, getViewerType } from '@/lib/file-utils';

// Breakpoint for responsive behavior (768px = md)
const MOBILE_BREAKPOINT = 768;

interface DocumentChunkViewerProps {
  /** Knowledge Base ID */
  kbId: string;
  /** Document ID */
  documentId: string;
  /** Document filename (for display and type detection) */
  filename: string;
  /** Document MIME type (optional, detected from filename if not provided) */
  mimeType?: string;
  /** File URL for PDF viewing */
  fileUrl?: string;
  /** Initial chunk to select */
  initialChunkIndex?: number;
  /** Callback when viewer is closed */
  onClose?: () => void;
}

/**
 * Custom hook for responsive breakpoint detection
 */
function useIsMobile(breakpoint: number = MOBILE_BREAKPOINT) {
  // Initialize to false for SSR, then check on mount
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < breakpoint;
  });

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < breakpoint;
      setIsMobile((prev) => (prev !== mobile ? mobile : prev));
    };

    // Listen for resize
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [breakpoint]);

  return isMobile;
}

/**
 * Document Chunk Viewer with split-pane layout.
 *
 * Features:
 * - Resizable split-pane (document | chunks)
 * - Auto-detects document type from filename/MIME
 * - Renders appropriate viewer for each type
 * - Syncs chunk selection with document scroll
 * - Responsive: collapses to vertical on mobile (AC-5.26.7)
 */
export function DocumentChunkViewer({
  kbId,
  documentId,
  filename,
  mimeType: providedMimeType,
  fileUrl,
  initialChunkIndex,
  onClose: _onClose, // Reserved for modal close functionality
}: DocumentChunkViewerProps) {
  void _onClose; // Suppress unused variable warning
  const [selectedChunk, setSelectedChunk] = useState<DocumentChunk | null>(null);
  const [selectedChunkIndex, setSelectedChunkIndex] = useState<number | null>(
    initialChunkIndex ?? null
  );
  const [mobileChunksExpanded, setMobileChunksExpanded] = useState(false);
  const isMobile = useIsMobile();

  // Fetch document content
  const {
    text,
    mimeType: contentMimeType,
    html,
    isLoading,
    isError,
    error,
  } = useDocumentContent({
    kbId,
    documentId,
  });

  // Determine MIME type (prefer provided, then API response, then detection)
  const effectiveMimeType = useMemo(
    () => providedMimeType || contentMimeType || getMimeType(filename),
    [providedMimeType, contentMimeType, filename]
  );

  const viewerType = getViewerType(effectiveMimeType);

  // Handle chunk click
  const handleChunkClick = useCallback((chunk: DocumentChunk) => {
    setSelectedChunk(chunk);
    setSelectedChunkIndex(chunk.chunk_index);
    // Collapse mobile sidebar after selection
    setMobileChunksExpanded(false);
  }, []);

  // Get highlight range from selected chunk
  const highlightRange = useMemo(() => {
    if (!selectedChunk) return null;
    return {
      start: selectedChunk.char_start,
      end: selectedChunk.char_end,
    };
  }, [selectedChunk]);

  // Render the appropriate viewer
  const renderViewer = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      );
    }

    if (isError) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-center p-4">
          <FileText className="h-12 w-12 text-muted-foreground mb-4" />
          <div className="text-destructive mb-2">Failed to load document</div>
          <div className="text-sm text-muted-foreground">{error?.message || 'Unknown error'}</div>
        </div>
      );
    }

    switch (viewerType) {
      case 'pdf':
        return (
          <PDFViewer
            url={fileUrl || `/api/v1/knowledge-bases/${kbId}/documents/${documentId}/download`}
            targetPage={selectedChunk?.page_number}
            highlightRange={highlightRange}
          />
        );

      case 'docx':
        return <DOCXViewer html={html} text={text} highlightRange={highlightRange} />;

      case 'markdown':
        return <MarkdownViewer content={text} highlightRange={highlightRange} />;

      case 'text':
      default:
        return <TextViewer content={text} highlightRange={highlightRange} showLineNumbers={true} />;
    }
  };

  // Mobile layout: vertical split with collapsible bottom sheet
  if (isMobile) {
    return (
      <div className="h-full w-full flex flex-col" data-testid="document-chunk-viewer">
        {/* Document content (top) */}
        <div
          className={cn(
            'flex-1 overflow-hidden transition-all duration-200',
            mobileChunksExpanded && 'flex-[0.4]'
          )}
        >
          {renderViewer()}
        </div>

        {/* Mobile chunks toggle button */}
        <Button
          variant="outline"
          className="w-full rounded-none border-x-0 gap-2 py-2"
          onClick={() => setMobileChunksExpanded(!mobileChunksExpanded)}
          data-testid="mobile-chunks-toggle"
        >
          <Layers className="h-4 w-4" />
          {mobileChunksExpanded ? 'Hide' : 'Show'} Chunks
          {selectedChunkIndex !== null && (
            <span className="text-xs text-muted-foreground">
              (#{selectedChunkIndex + 1} selected)
            </span>
          )}
          {mobileChunksExpanded ? (
            <ChevronDown className="h-4 w-4 ml-auto" />
          ) : (
            <ChevronUp className="h-4 w-4 ml-auto" />
          )}
        </Button>

        {/* Chunk sidebar (bottom sheet) */}
        <div
          className={cn(
            'overflow-hidden transition-all duration-200',
            mobileChunksExpanded ? 'flex-[0.6]' : 'h-0'
          )}
        >
          {mobileChunksExpanded && (
            <ChunkSidebar
              kbId={kbId}
              documentId={documentId}
              selectedChunkIndex={selectedChunkIndex}
              onChunkClick={handleChunkClick}
              width="100%"
            />
          )}
        </div>
      </div>
    );
  }

  // Desktop layout: horizontal split-pane
  return (
    <div className="h-full w-full" data-testid="document-chunk-viewer">
      <PanelGroup direction="horizontal" className="h-full">
        {/* Document content pane (AC-5.26.2: left side) */}
        <Panel defaultSize={65} minSize={30}>
          <div className="h-full overflow-hidden">{renderViewer()}</div>
        </Panel>

        {/* Resize handle */}
        <PanelResizeHandle className="w-2 bg-border hover:bg-primary/20 transition-colors flex items-center justify-center group">
          <GripVertical className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
        </PanelResizeHandle>

        {/* Chunk sidebar pane (AC-5.26.2: right side) */}
        <Panel defaultSize={35} minSize={20} maxSize={50}>
          <ChunkSidebar
            kbId={kbId}
            documentId={documentId}
            selectedChunkIndex={selectedChunkIndex}
            onChunkClick={handleChunkClick}
            width="100%"
          />
        </Panel>
      </PanelGroup>
    </div>
  );
}
