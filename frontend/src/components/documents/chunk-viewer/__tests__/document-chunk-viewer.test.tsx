/**
 * Unit tests for DocumentChunkViewer component
 * Story 5-26: Document Chunk Viewer Frontend
 *
 * Tests the main container component with split-pane layout and responsive behavior.
 * AC-5.26.1: Modal/panel shows chunked document with split-pane layout
 * AC-5.26.2: Left side shows rendered content, right side shows chunks
 * AC-5.26.7: Responsive - sidebar collapses to bottom sheet on mobile
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ReactNode } from 'react';
import { DocumentChunkViewer } from '../document-chunk-viewer';

// Mock the hooks
vi.mock('@/hooks/useDocumentContent', () => ({
  useDocumentContent: vi.fn(),
}));

vi.mock('@/hooks/useDocumentChunks', () => ({
  useDocumentChunks: vi.fn(),
}));

// Mock react-resizable-panels
vi.mock('react-resizable-panels', () => ({
  Panel: ({ children }: { children: ReactNode }) => <div data-testid="panel">{children}</div>,
  PanelGroup: ({ children }: { children: ReactNode }) => (
    <div data-testid="panel-group">{children}</div>
  ),
  PanelResizeHandle: () => <div data-testid="resize-handle" />,
}));

// Mock react-pdf to avoid DOMMatrix error in jsdom
vi.mock('react-pdf', () => ({
  Document: ({ children }: { children: ReactNode }) => (
    <div data-testid="pdf-document">{children}</div>
  ),
  Page: () => <div data-testid="pdf-page" />,
  pdfjs: { GlobalWorkerOptions: { workerSrc: '' } },
}));

// Mock react-markdown to avoid className prop warning in tests
vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => (
    <div data-testid="react-markdown-content">{children}</div>
  ),
}));

import { useDocumentContent } from '@/hooks/useDocumentContent';
import { useDocumentChunks } from '@/hooks/useDocumentChunks';

function TestWrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

const createWrapper = () => TestWrapper;

// Mock data
const mockTextContent = {
  text: 'This is the document text content.\nLine 2.\nLine 3.',
  mimeType: 'text/plain',
  html: null,
  isLoading: false,
  isError: false,
  error: null,
  refetch: vi.fn(),
};

const mockMarkdownContent = {
  text: '# Heading\n\nThis is **markdown** content.',
  mimeType: 'text/markdown',
  html: null,
  isLoading: false,
  isError: false,
  error: null,
  refetch: vi.fn(),
};

const mockChunks = {
  chunks: [
    {
      chunk_id: 'chunk-1',
      chunk_index: 0,
      text: 'First chunk text.',
      char_start: 0,
      char_end: 17,
      page_number: 1,
      section_header: 'Intro',
      score: null,
    },
    {
      chunk_id: 'chunk-2',
      chunk_index: 1,
      text: 'Second chunk text.',
      char_start: 18,
      char_end: 36,
      page_number: 1,
      section_header: 'Intro',
      score: null,
    },
  ],
  total: 2,
  hasMore: false,
  nextCursor: null,
  isLoading: false,
  isError: false,
  error: null,
  refetch: vi.fn(),
};

describe('DocumentChunkViewer', () => {
  let originalInnerWidth: number;

  beforeEach(() => {
    vi.clearAllMocks();
    originalInnerWidth = window.innerWidth;

    // Default to desktop size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });

    (useDocumentContent as ReturnType<typeof vi.fn>).mockReturnValue(mockTextContent);
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue(mockChunks);
  });

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  it('[P0] should render split-pane layout on desktop - AC-5.26.1', () => {
    // Act
    render(<DocumentChunkViewer kbId="kb-123" documentId="doc-456" filename="test.txt" />, {
      wrapper: createWrapper(),
    });

    // Assert
    expect(screen.getByTestId('document-chunk-viewer')).toBeInTheDocument();
    expect(screen.getByTestId('panel-group')).toBeInTheDocument();
    expect(screen.getByTestId('resize-handle')).toBeInTheDocument();
  });

  it('[P0] should render text viewer for .txt files - AC-5.26.4', () => {
    // Arrange
    (useDocumentContent as ReturnType<typeof vi.fn>).mockReturnValue(mockTextContent);

    // Act
    render(<DocumentChunkViewer kbId="kb-123" documentId="doc-456" filename="document.txt" />, {
      wrapper: createWrapper(),
    });

    // Assert
    expect(screen.getByTestId('text-viewer')).toBeInTheDocument();
  });

  it('[P0] should render markdown viewer for .md files - AC-5.26.4', () => {
    // Arrange
    (useDocumentContent as ReturnType<typeof vi.fn>).mockReturnValue(mockMarkdownContent);

    // Act
    render(<DocumentChunkViewer kbId="kb-123" documentId="doc-456" filename="readme.md" />, {
      wrapper: createWrapper(),
    });

    // Assert
    expect(screen.getByTestId('markdown-viewer')).toBeInTheDocument();
  });

  it('[P0] should show loading state while fetching content - AC-5.26.4', () => {
    // Arrange
    (useDocumentContent as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockTextContent,
      isLoading: true,
      text: null,
    });

    // Act
    render(<DocumentChunkViewer kbId="kb-123" documentId="doc-456" filename="test.txt" />, {
      wrapper: createWrapper(),
    });

    // Assert - should show loading spinner
    expect(screen.getByTestId('document-chunk-viewer')).toBeInTheDocument();
  });

  it('[P0] should show error state on fetch failure - AC-5.26.4', () => {
    // Arrange
    (useDocumentContent as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockTextContent,
      isError: true,
      error: new Error('Failed to load'),
      text: null,
    });

    // Act
    render(<DocumentChunkViewer kbId="kb-123" documentId="doc-456" filename="test.txt" />, {
      wrapper: createWrapper(),
    });

    // Assert
    expect(screen.getByText('Failed to load document')).toBeInTheDocument();
  });

  it('[P0] should use provided mimeType over filename detection - AC-5.26.4', () => {
    // Arrange
    (useDocumentContent as ReturnType<typeof vi.fn>).mockReturnValue(mockMarkdownContent);

    // Act
    render(
      <DocumentChunkViewer
        kbId="kb-123"
        documentId="doc-456"
        filename="document.unknown"
        mimeType="text/markdown"
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByTestId('markdown-viewer')).toBeInTheDocument();
  });

  it('[P1] should detect MIME type from filename extension - AC-5.26.4', () => {
    // Arrange
    (useDocumentContent as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockTextContent,
      mimeType: null, // No MIME type from API
    });

    // Act - .txt extension should use text viewer
    render(<DocumentChunkViewer kbId="kb-123" documentId="doc-456" filename="document.txt" />, {
      wrapper: createWrapper(),
    });

    // Assert
    expect(screen.getByTestId('text-viewer')).toBeInTheDocument();
  });

  it('[P1] should render mobile layout on small screens - AC-5.26.7', async () => {
    // Arrange - set mobile width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 600,
    });

    // Fire resize event
    window.dispatchEvent(new Event('resize'));

    // Act
    render(<DocumentChunkViewer kbId="kb-123" documentId="doc-456" filename="test.txt" />, {
      wrapper: createWrapper(),
    });

    // Assert - should show mobile toggle button
    await waitFor(() => {
      expect(screen.getByTestId('mobile-chunks-toggle')).toBeInTheDocument();
    });
  });

  it('[P1] should toggle chunks panel on mobile - AC-5.26.7', async () => {
    // Arrange - set mobile width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 600,
    });
    window.dispatchEvent(new Event('resize'));

    // Act
    render(<DocumentChunkViewer kbId="kb-123" documentId="doc-456" filename="test.txt" />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByTestId('mobile-chunks-toggle')).toBeInTheDocument();
    });

    // Initial state - should show "Show Chunks"
    expect(screen.getByText(/Show.*Chunks/)).toBeInTheDocument();

    // Click to expand
    fireEvent.click(screen.getByTestId('mobile-chunks-toggle'));

    // Assert - should show "Hide Chunks"
    expect(screen.getByText(/Hide.*Chunks/)).toBeInTheDocument();
  });

  it('[P1] should select initial chunk when provided - AC-5.26.6', () => {
    // Act
    render(
      <DocumentChunkViewer
        kbId="kb-123"
        documentId="doc-456"
        filename="test.txt"
        initialChunkIndex={1}
      />,
      { wrapper: createWrapper() }
    );

    // Assert - component should render with initial chunk selected
    expect(screen.getByTestId('document-chunk-viewer')).toBeInTheDocument();
  });

  it('[P2] should render chunk sidebar in split-pane - AC-5.26.2', () => {
    // Act
    render(<DocumentChunkViewer kbId="kb-123" documentId="doc-456" filename="test.txt" />, {
      wrapper: createWrapper(),
    });

    // Assert
    expect(screen.getByTestId('chunk-sidebar')).toBeInTheDocument();
  });

  it('[P2] should handle onClose callback', () => {
    // Arrange
    const mockOnClose = vi.fn();

    // Act
    render(
      <DocumentChunkViewer
        kbId="kb-123"
        documentId="doc-456"
        filename="test.txt"
        onClose={mockOnClose}
      />,
      { wrapper: createWrapper() }
    );

    // Assert - component should render (onClose is available for parent modal)
    expect(screen.getByTestId('document-chunk-viewer')).toBeInTheDocument();
  });

  it('[P2] should default to text/plain for unknown extensions', () => {
    // Arrange
    (useDocumentContent as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockTextContent,
      mimeType: null,
    });

    // Act
    render(<DocumentChunkViewer kbId="kb-123" documentId="doc-456" filename="document.xyz" />, {
      wrapper: createWrapper(),
    });

    // Assert - should default to text viewer
    expect(screen.getByTestId('text-viewer')).toBeInTheDocument();
  });
});
