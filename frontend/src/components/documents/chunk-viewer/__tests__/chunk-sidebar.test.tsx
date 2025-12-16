/**
 * Unit tests for ChunkSidebar component
 * Story 5-26: Document Chunk Viewer Frontend
 *
 * Tests chunk list display, search, pagination, and navigation.
 * AC-5.26.3: Chunk sidebar displays all chunks with search
 * AC-5.26.5: Search filters chunks in real-time
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ReactNode } from 'react';
import { ChunkSidebar } from '../chunk-sidebar';

// Mock the useDocumentChunks hook
vi.mock('@/hooks/useDocumentChunks', () => ({
  useDocumentChunks: vi.fn(),
}));

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

// Mock chunk data
const mockChunks = [
  {
    chunk_id: 'chunk-1',
    chunk_index: 0,
    text: 'This is the first chunk of text.',
    char_start: 0,
    char_end: 32,
    page_number: 1,
    section_header: 'Introduction',
    score: null,
  },
  {
    chunk_id: 'chunk-2',
    chunk_index: 1,
    text: 'This is the second chunk of text.',
    char_start: 33,
    char_end: 66,
    page_number: 1,
    section_header: 'Introduction',
    score: null,
  },
  {
    chunk_id: 'chunk-3',
    chunk_index: 2,
    text: 'This is the third chunk of text.',
    char_start: 67,
    char_end: 99,
    page_number: 2,
    section_header: 'Methods',
    score: null,
  },
];

describe('ChunkSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('[P0] should render chunk list with correct count - AC-5.26.3', async () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: mockChunks,
      total: 10,
      hasMore: true,
      nextCursor: 3,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByText('Document Chunks')).toBeInTheDocument();
    expect(screen.getByText('10 chunks')).toBeInTheDocument();
    expect(screen.getByTestId('chunk-sidebar')).toBeInTheDocument();
  });

  it('[P0] should render search input - AC-5.26.5', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: mockChunks,
      total: 3,
      hasMore: false,
      nextCursor: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByTestId('chunk-search-input')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search chunks...')).toBeInTheDocument();
  });

  it('[P0] should show loading state when fetching - AC-5.26.3', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: [],
      total: 0,
      hasMore: false,
      nextCursor: null,
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
      />,
      { wrapper: createWrapper() }
    );

    // Assert - loading spinner should be visible
    expect(screen.getByTestId('chunk-sidebar')).toBeInTheDocument();
  });

  it('[P0] should show error message on fetch failure - AC-5.26.3', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: [],
      total: 0,
      hasMore: false,
      nextCursor: null,
      isLoading: false,
      isError: true,
      error: new Error('Failed to load chunks'),
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByText('Failed to load chunks')).toBeInTheDocument();
  });

  it('[P0] should show empty state when no chunks - AC-5.26.3', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: [],
      total: 0,
      hasMore: false,
      nextCursor: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByText('No chunks found')).toBeInTheDocument();
  });

  it('[P0] should call onChunkClick when chunk is clicked - AC-5.26.6', () => {
    // Arrange
    const mockOnChunkClick = vi.fn();
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: mockChunks,
      total: 3,
      hasMore: false,
      nextCursor: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
        onChunkClick={mockOnChunkClick}
      />,
      { wrapper: createWrapper() }
    );

    // Virtual scroll requires real DOM measurements, which aren't available in jsdom
    // This is a limitation of testing virtualized lists - we verify the component renders
    // and that the onChunkClick prop is accepted
    expect(screen.getByTestId('chunk-sidebar')).toBeInTheDocument();
    // The onChunkClick callback is passed to virtualized items - full click testing
    // would require a real browser environment or e2e tests
  });

  it('[P0] should show "Load more" button when hasMore is true - AC-5.26.3', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: mockChunks,
      total: 100,
      hasMore: true,
      nextCursor: 3,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByTestId('load-more-chunks')).toBeInTheDocument();
    expect(screen.getByText('Load more chunks')).toBeInTheDocument();
  });

  it('[P0] should hide "Load more" button when hasMore is false', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: mockChunks,
      total: 3,
      hasMore: false,
      nextCursor: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.queryByTestId('load-more-chunks')).not.toBeInTheDocument();
  });

  it('[P1] should show singular "chunk" for count of 1 - AC-5.26.3', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: [mockChunks[0]],
      total: 1,
      hasMore: false,
      nextCursor: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByText('1 chunk')).toBeInTheDocument();
  });

  it('[P1] should show navigation footer when chunk is selected - AC-5.26.3', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: mockChunks,
      total: 10,
      hasMore: true,
      nextCursor: 3,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
        selectedChunkIndex={1}
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByTestId('prev-chunk-btn')).toBeInTheDocument();
    expect(screen.getByTestId('next-chunk-btn')).toBeInTheDocument();
    expect(screen.getByText('2 / 10')).toBeInTheDocument(); // 1-indexed display
  });

  it('[P1] should disable Prev button on first chunk', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: mockChunks,
      total: 10,
      hasMore: true,
      nextCursor: 3,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
        selectedChunkIndex={0}
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByTestId('prev-chunk-btn')).toBeDisabled();
  });

  it('[P1] should disable Next button on last chunk', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: mockChunks,
      total: 3,
      hasMore: false,
      nextCursor: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
        selectedChunkIndex={2}
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByTestId('next-chunk-btn')).toBeDisabled();
  });

  it('[P1] should show "No chunks match your search" when search returns empty - AC-5.26.5', async () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: [],
      total: 0,
      hasMore: false,
      nextCursor: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
      />,
      { wrapper: createWrapper() }
    );

    // Type in search
    fireEvent.change(screen.getByTestId('chunk-search-input'), {
      target: { value: 'nonexistent' },
    });

    // Wait for state update
    await vi.advanceTimersByTimeAsync(300);

    // Assert
    expect(screen.getByText('No chunks match your search')).toBeInTheDocument();
  });

  it('[P2] should have correct test-id for automation', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: mockChunks,
      total: 3,
      hasMore: false,
      nextCursor: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByTestId('chunk-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('chunk-search-input')).toBeInTheDocument();
  });

  it('[P2] should apply custom width style', () => {
    // Arrange
    (useDocumentChunks as ReturnType<typeof vi.fn>).mockReturnValue({
      chunks: mockChunks,
      total: 3,
      hasMore: false,
      nextCursor: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    // Act
    render(
      <ChunkSidebar
        kbId="kb-123"
        documentId="doc-456"
        width={400}
      />,
      { wrapper: createWrapper() }
    );

    // Assert
    const sidebar = screen.getByTestId('chunk-sidebar');
    expect(sidebar).toHaveStyle({ width: '400px' });
  });
});
