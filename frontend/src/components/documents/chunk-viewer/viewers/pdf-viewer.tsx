/**
 * PDFViewer Component (Story 5-26)
 *
 * Renders PDF documents with page navigation and chunk highlighting.
 * AC-5.26.4: Content pane renders document based on type (PDF)
 * AC-5.26.6: Click chunk scrolls to position in document
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Loader2, ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-react';

// PDF Document proxy type - matches react-pdf's internal type
interface PDFDocument {
  numPages: number;
}
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

// Define options outside component to ensure stable reference
const DOCUMENT_OPTIONS = {
  withCredentials: true,
};

interface PDFViewerProps {
  /** URL to PDF file */
  url: string;
  /** Page number to scroll to (1-indexed) */
  targetPage?: number | null;
  /** Character range to highlight */
  highlightRange?: { start: number; end: number } | null;
  /** Callback when PDF loads */
  onLoad?: (numPages: number) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

/**
 * PDF document viewer with navigation and highlighting.
 *
 * Features:
 * - Multi-page rendering with lazy loading
 * - Page navigation controls
 * - Zoom controls
 * - Scroll to target page (from chunk selection)
 * - Text selection support
 */
export function PDFViewer({
  url,
  targetPage,
  highlightRange: _highlightRange, // Reserved for future text highlighting feature
  onLoad,
  onError,
}: PDFViewerProps) {
  void _highlightRange; // Suppress unused variable warning
  const [numPages, setNumPages] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  // Track the PDF document proxy to ensure pages only render when it's ready
  const [pdfDocument, setPdfDocument] = useState<PDFDocument | null>(null);
  // Use ref to store file data to prevent re-renders causing Document remount
  const fileDataRef = useRef<{ data: Uint8Array } | null>(null);
  // Track when file is ready for Document to render
  const [fileReady, setFileReady] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  // Fetch PDF with credentials since react-pdf options.withCredentials doesn't work reliably
  useEffect(() => {
    let cancelled = false;

    const fetchPdf = async () => {
      try {
        const response = await fetch(url, {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch PDF: ${response.status} ${response.statusText}`);
        }

        const arrayBuffer = await response.arrayBuffer();
        // Convert to Uint8Array to avoid ArrayBuffer detachment issues
        const uint8Array = new Uint8Array(arrayBuffer);

        if (!cancelled) {
          // Store in ref to avoid re-renders
          fileDataRef.current = { data: uint8Array };
          setFileReady(true);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error('Failed to fetch PDF'));
          setLoading(false);
          onError?.(err instanceof Error ? err : new Error('Failed to fetch PDF'));
        }
      }
    };

    // Reset state when URL changes
    fileDataRef.current = null;
    setFileReady(false);
    setError(null);
    setLoading(true);
    setPdfDocument(null);
    setNumPages(0);

    if (url) {
      fetchPdf();
    }

    return () => {
      cancelled = true;
    };
  }, [url, onError]);

  // Handle PDF load success - receives the actual PDF document proxy
  const onDocumentLoadSuccess = useCallback(
    (pdf: PDFDocument) => {
      setNumPages(pdf.numPages);
      setLoading(false);
      // Store the PDF document proxy - pages can now safely render
      setPdfDocument(pdf);
      onLoad?.(pdf.numPages);
    },
    [onLoad]
  );

  // Handle PDF load error
  const onDocumentLoadError = useCallback(
    (err: Error) => {
      setError(err);
      setLoading(false);
      onError?.(err);
    },
    [onError]
  );

  // Navigate to target page when chunk is selected
  useEffect(() => {
    if (targetPage && targetPage >= 1 && targetPage <= numPages) {
      setCurrentPage(targetPage);
      const pageElement = pageRefs.current.get(targetPage);
      if (pageElement) {
        pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, [targetPage, numPages]);

  // Zoom controls
  const zoomIn = () => setScale((s) => Math.min(s + 0.25, 3.0));
  const zoomOut = () => setScale((s) => Math.max(s - 0.25, 0.5));

  // Page navigation
  const goToPage = (page: number) => {
    const validPage = Math.max(1, Math.min(page, numPages));
    setCurrentPage(validPage);
    const pageElement = pageRefs.current.get(validPage);
    if (pageElement) {
      pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-4">
        <div className="text-destructive mb-2">Failed to load PDF</div>
        <div className="text-sm text-muted-foreground">{error.message}</div>
      </div>
    );
  }

  // Check if document is ready for rendering pages
  const canRenderPages = pdfDocument !== null && numPages > 0;

  return (
    <div className="flex flex-col h-full" data-testid="pdf-viewer">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 border-b bg-muted/30">
        {/* Zoom controls */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={zoomOut}
            disabled={scale <= 0.5}
            title="Zoom out"
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="text-sm w-14 text-center">
            {Math.round(scale * 100)}%
          </span>
          <Button
            variant="ghost"
            size="icon"
            onClick={zoomIn}
            disabled={scale >= 3.0}
            title="Zoom in"
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
        </div>

        {/* Page navigation */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => goToPage(currentPage - 1)}
            disabled={currentPage <= 1}
            title="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-1">
            <Input
              type="number"
              min={1}
              max={numPages}
              value={currentPage}
              onChange={(e) => goToPage(parseInt(e.target.value) || 1)}
              className="w-14 h-8 text-center"
            />
            <span className="text-sm text-muted-foreground">/ {numPages}</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => goToPage(currentPage + 1)}
            disabled={currentPage >= numPages}
            title="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        {/* Spacer for alignment */}
        <div className="w-24" />
      </div>

      {/* PDF content */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto overflow-x-hidden"
        style={{ overscrollBehavior: 'contain' }}
        data-testid="pdf-scroll-container"
        data-scroll-container
      >
        <div className="flex flex-col items-center p-4 min-h-full">
          {(loading || !fileReady || !canRenderPages) && !error && (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {fileReady && fileDataRef.current && (
            <Document
              key={url}
              file={fileDataRef.current}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={null}
              className="flex flex-col items-center gap-4"
              options={DOCUMENT_OPTIONS}
            >
              {/* Only render pages after PDF document proxy is ready */}
              {canRenderPages && Array.from({ length: numPages }, (_, index) => (
                <div
                  key={`page_${index + 1}`}
                  ref={(el) => {
                    if (el) pageRefs.current.set(index + 1, el);
                  }}
                  className="shadow-lg"
                >
                  <Page
                    pageNumber={index + 1}
                    scale={scale}
                    renderTextLayer={true}
                    renderAnnotationLayer={true}
                    className="[&_.react-pdf__Page__canvas]:bg-white dark:[&_.react-pdf__Page__canvas]:bg-gray-100"
                  />
                </div>
              ))}
            </Document>
          )}
        </div>
      </div>
    </div>
  );
}
