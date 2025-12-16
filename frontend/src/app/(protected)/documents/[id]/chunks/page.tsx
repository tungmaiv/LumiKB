'use client';

import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import {
  GripVertical,
  FileText,
  Loader2,
  ArrowLeft,
  Layers,
  ChevronUp,
  ChevronDown,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Header } from '@/components/layout/header';
import { useDocumentContent } from '@/hooks/useDocumentContent';
import { ChunkSidebar } from '@/components/documents/chunk-viewer/chunk-sidebar';
import {
  PDFViewer,
  DOCXViewer,
  MarkdownViewer,
  TextViewer,
  EnhancedMarkdownViewer,
} from '@/components/documents/chunk-viewer/viewers';
import { ViewModeToggle } from '@/components/documents/chunk-viewer/view-mode-toggle';
import { useMarkdownContent } from '@/hooks/useMarkdownContent';
import { useViewModePreference } from '@/hooks/useViewModePreference';
import type { DocumentChunk } from '@/types/chunk';
import { cn } from '@/lib/utils';
import { getMimeType, getViewerType } from '@/lib/file-utils';

/**
 * IsolatedScrollPanel - A wrapper that captures wheel events and prevents
 * them from propagating to parent elements or sibling panels.
 */
function IsolatedScrollPanel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Capture wheel events at this container level and stop propagation
    const handleWheel = (e: WheelEvent) => {
      // Find the scrollable element within this panel
      const scrollable = container.querySelector('[data-scroll-container]') as HTMLElement;
      if (!scrollable) return;

      const { scrollTop, scrollHeight, clientHeight } = scrollable;
      const isAtTop = scrollTop <= 0;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 1;
      const isScrollingUp = e.deltaY < 0;
      const isScrollingDown = e.deltaY > 0;

      // If at boundary and trying to scroll past it, prevent default
      if ((isAtTop && isScrollingUp) || (isAtBottom && isScrollingDown)) {
        e.preventDefault();
      }

      // Always stop propagation to prevent affecting other panels
      e.stopPropagation();
    };

    // Use capture phase to intercept before it reaches other handlers
    container.addEventListener('wheel', handleWheel, { passive: false, capture: true });

    return () => {
      container.removeEventListener('wheel', handleWheel, { capture: true });
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className={cn('h-full w-full overflow-hidden', className)}
      style={{ isolation: 'isolate' }}
    >
      {children}
    </div>
  );
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Breakpoint for responsive behavior (768px = md)
const MOBILE_BREAKPOINT = 768;

/**
 * Custom hook for responsive breakpoint detection
 */
function useIsMobile(breakpoint: number = MOBILE_BREAKPOINT) {
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < breakpoint;
  });

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < breakpoint;
      setIsMobile((prev) => (prev !== mobile ? mobile : prev));
    };

    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [breakpoint]);

  return isMobile;
}

interface DocumentInfo {
  id: string;
  name: string;
  original_filename: string;
  mime_type: string;
  chunk_count: number;
}

/**
 * Document Chunks Page
 *
 * Displays a split-pane view with:
 * - Left: Original document viewer (PDF/DOCX/Markdown/Text)
 * - Right: Chunk list with search and selection
 *
 * When a chunk is selected, it highlights in the original document.
 */
export default function DocumentChunksPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const documentId = params.id as string;
  const kbId = searchParams.get('kb');

  const [documentInfo, setDocumentInfo] = useState<DocumentInfo | null>(null);
  const [isLoadingInfo, setIsLoadingInfo] = useState(true);
  const [infoError, setInfoError] = useState<string | null>(null);
  const [selectedChunk, setSelectedChunk] = useState<DocumentChunk | null>(null);
  const [selectedChunkIndex, setSelectedChunkIndex] = useState<number | null>(null);
  const [mobileChunksExpanded, setMobileChunksExpanded] = useState(false);

  const isMobile = useIsMobile();

  // Fetch document info
  useEffect(() => {
    if (!kbId || !documentId) return;

    const fetchDocumentInfo = async () => {
      setIsLoadingInfo(true);
      setInfoError(null);
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}`,
          { credentials: 'include' }
        );
        if (!response.ok) {
          throw new Error(`Failed to load document: ${response.statusText}`);
        }
        const data = await response.json();
        setDocumentInfo(data);
      } catch (err) {
        setInfoError(err instanceof Error ? err.message : 'Failed to load document');
      } finally {
        setIsLoadingInfo(false);
      }
    };

    fetchDocumentInfo();
  }, [kbId, documentId]);

  // Fetch document content
  const {
    text,
    mimeType: contentMimeType,
    html,
    isLoading: isLoadingContent,
    isError: isContentError,
    error: contentError,
  } = useDocumentContent({
    kbId: kbId || '',
    documentId,
    enabled: !!kbId && !!documentId,
  });

  // Fetch markdown content for enhanced highlighting (Story 7-30)
  // AC-7.30.1: Fetch markdown from /markdown-content endpoint
  const {
    data: markdownData,
    isLoading: isLoadingMarkdown,
    isError: isMarkdownError,
  } = useMarkdownContent({
    kbId: kbId || '',
    documentId,
    enabled: !!kbId && !!documentId,
  });

  // Story 7-31: View mode toggle state
  // AC-7.31.2: Default to markdown when available
  // AC-7.31.4: Persist preference in localStorage
  const markdownAvailable = !!markdownData?.markdown_content;
  const { viewMode, setViewMode } = useViewModePreference(markdownAvailable);

  // Determine MIME type
  const effectiveMimeType = useMemo(
    () =>
      documentInfo?.mime_type ||
      contentMimeType ||
      (documentInfo?.original_filename
        ? getMimeType(documentInfo.original_filename)
        : 'text/plain'),
    [documentInfo?.mime_type, contentMimeType, documentInfo?.original_filename]
  );

  const viewerType = getViewerType(effectiveMimeType);

  // Handle chunk click
  const handleChunkClick = useCallback((chunk: DocumentChunk) => {
    setSelectedChunk(chunk);
    setSelectedChunkIndex(chunk.chunk_index);
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

  // Handle back navigation to KB dashboard
  const handleBackToKB = () => {
    if (kbId) {
      router.push(`/dashboard?kb=${kbId}`);
    } else {
      router.push('/dashboard');
    }
  };

  // Render the appropriate viewer
  const renderViewer = () => {
    // Story 7-30: Check if markdown content is available for enhanced highlighting
    // AC-7.30.5: Show loading skeleton while fetching markdown
    if (isLoadingMarkdown) {
      return (
        <div className="flex items-center justify-center h-full bg-muted/10">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      );
    }

    // Story 7-31: Use viewMode toggle to decide which viewer to show
    // AC-7.31.2, AC-7.31.3: Show EnhancedMarkdownViewer only when markdown mode selected AND available
    if (viewMode === 'markdown' && markdownAvailable) {
      return (
        <EnhancedMarkdownViewer
          content={markdownData!.markdown_content}
          highlightRange={highlightRange}
          showFallbackMessage={viewerType === 'pdf' || viewerType === 'docx'}
        />
      );
    }

    // AC-7.30.4: Fallback to original viewers when markdown not available
    // For PDF files, render directly from download URL (don't need text content)
    // PDF.js handles the rendering from the binary file
    // Render immediately without waiting for full-content endpoint
    if (viewerType === 'pdf') {
      return (
        <>
          {/* AC-7.30.4: Show subtle message when precise highlighting not available */}
          <div className="absolute top-2 left-2 z-10 px-3 py-1.5 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded text-xs text-amber-700 dark:text-amber-300">
            Precise highlighting not available for this document
          </div>
          <PDFViewer
            url={`${API_BASE_URL}/api/v1/knowledge-bases/${kbId}/documents/${documentId}/download`}
            targetPage={selectedChunk?.page_number}
            highlightRange={highlightRange}
          />
        </>
      );
    }

    // For non-PDF files, show loading state while fetching content
    if (isLoadingContent) {
      return (
        <div className="flex items-center justify-center h-full bg-muted/10">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      );
    }

    if (isContentError) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-center p-4 bg-muted/10">
          <FileText className="h-12 w-12 text-muted-foreground mb-4" />
          <div className="text-destructive mb-2">Failed to load document content</div>
          <div className="text-sm text-muted-foreground">
            {contentError?.message || 'Unknown error'}
          </div>
        </div>
      );
    }

    // Check if content is empty/null after loading completes (for non-PDF files)
    if (!text && !html) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-center p-4 bg-muted/10">
          <FileText className="h-12 w-12 text-muted-foreground mb-4" />
          <div className="text-muted-foreground mb-2">No document content available</div>
          <div className="text-sm text-muted-foreground">
            The document content could not be loaded. This may happen if the document is still processing or the content format is not supported.
          </div>
        </div>
      );
    }

    switch (viewerType) {
      case 'docx':
        return (
          <>
            {/* AC-7.30.4: Show subtle message when precise highlighting not available */}
            <div className="absolute top-2 left-2 z-10 px-3 py-1.5 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded text-xs text-amber-700 dark:text-amber-300">
              Precise highlighting not available for this document
            </div>
            <DOCXViewer
              html={html}
              text={text}
              highlightRange={highlightRange}
              isLoading={isLoadingContent}
              error={isContentError ? (contentError?.message || 'Failed to load content') : undefined}
            />
          </>
        );

      case 'markdown':
        return (
          <MarkdownViewer content={text} highlightRange={highlightRange} />
        );

      case 'text':
      default:
        return (
          <TextViewer
            content={text}
            highlightRange={highlightRange}
            showLineNumbers={true}
          />
        );
    }
  };

  // Error states
  if (!kbId) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <FileText className="h-12 w-12 text-muted-foreground mb-4" />
        <h2 className="text-lg font-semibold mb-2">Missing Knowledge Base</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Knowledge base ID is required to view document chunks.
        </p>
        <Button onClick={handleBackToKB}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Go Back
        </Button>
      </div>
    );
  }

  if (isLoadingInfo) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (infoError) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <FileText className="h-12 w-12 text-muted-foreground mb-4" />
        <h2 className="text-lg font-semibold mb-2">Error Loading Document</h2>
        <p className="text-sm text-muted-foreground mb-4">{infoError}</p>
        <Button onClick={handleBackToKB}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Go Back
        </Button>
      </div>
    );
  }

  // Mobile layout: vertical split with collapsible bottom sheet
  if (isMobile) {
    return (
      <div className="h-screen w-full flex flex-col" data-testid="document-chunks-page">
        {/* App Header */}
        <Header />

        {/* Document sub-header with back button and view mode toggle */}
        <div className="flex items-center gap-2 px-4 py-3 border-b bg-background">
          <Button variant="outline" size="sm" onClick={handleBackToKB}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to KB
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-semibold truncate">{documentInfo?.name}</h1>
            <p className="text-xs text-muted-foreground">
              {documentInfo?.chunk_count} chunks
            </p>
          </div>
          {/* Story 7-31: View mode toggle - AC-7.31.1 */}
          <ViewModeToggle
            markdownAvailable={markdownAvailable}
            value={viewMode}
            onChange={setViewMode}
          />
        </div>

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
    <div className="h-screen w-full flex flex-col" data-testid="document-chunks-page">
      {/* App Header */}
      <Header />

      {/* Document sub-header with back button and view mode toggle */}
      <div className="flex items-center gap-3 px-4 py-3 border-b bg-background shrink-0">
        <Button variant="outline" size="sm" onClick={handleBackToKB}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to KB
        </Button>
        <div className="flex-1 min-w-0">
          <h1 className="text-lg font-semibold truncate">{documentInfo?.name}</h1>
          <p className="text-sm text-muted-foreground">
            {documentInfo?.chunk_count} chunks | {documentInfo?.original_filename}
          </p>
        </div>
        {/* Story 7-31: View mode toggle - AC-7.31.1 */}
        <ViewModeToggle
          markdownAvailable={markdownAvailable}
          value={viewMode}
          onChange={setViewMode}
        />
      </div>

      {/* Split-pane content */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <PanelGroup direction="horizontal" className="h-full">
          {/* Document content pane (left side) - IsolatedScrollPanel captures wheel events */}
          <Panel defaultSize={65} minSize={30} className="overflow-hidden">
            <IsolatedScrollPanel>
              {renderViewer()}
            </IsolatedScrollPanel>
          </Panel>

          {/* Resize handle */}
          <PanelResizeHandle className="w-2 bg-border hover:bg-primary/20 transition-colors flex items-center justify-center group">
            <GripVertical className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
          </PanelResizeHandle>

          {/* Chunk sidebar pane (right side) - IsolatedScrollPanel captures wheel events */}
          <Panel defaultSize={35} minSize={20} maxSize={50} className="overflow-hidden">
            <IsolatedScrollPanel>
              <ChunkSidebar
                kbId={kbId}
                documentId={documentId}
                selectedChunkIndex={selectedChunkIndex}
                onChunkClick={handleChunkClick}
                width="100%"
              />
            </IsolatedScrollPanel>
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
}
