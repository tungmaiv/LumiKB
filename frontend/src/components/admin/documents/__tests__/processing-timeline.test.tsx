/**
 * Processing Timeline Component Tests
 *
 * Story 9-10: Document Timeline UI
 * AC10: Unit tests for timeline rendering and interactions
 * AC2: Timeline visualization shows all processing steps
 * AC8: Total processing time summarized at top
 */
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { ProcessingTimeline, TimelineSkeleton } from '../processing-timeline';
import type { DocumentTimelineResponse } from '@/hooks/useDocumentTimeline';

// Mock the useDocumentTimeline hook
vi.mock('@/hooks/useDocumentTimeline', () => ({
  useDocumentTimeline: vi.fn(),
}));

import { useDocumentTimeline } from '@/hooks/useDocumentTimeline';

const mockUseDocumentTimeline = vi.mocked(useDocumentTimeline);

const mockTimelineResponse: DocumentTimelineResponse = {
  document_id: 'doc-123',
  events: [
    {
      id: 'event-1',
      trace_id: 'trace-1',
      step_name: 'upload',
      status: 'completed',
      started_at: '2024-01-15T10:00:00Z',
      ended_at: '2024-01-15T10:00:01Z',
      duration_ms: 1000,
      metrics: { file_size: 1048576, mime_type: 'application/pdf' },
      error_message: null,
    },
    {
      id: 'event-2',
      trace_id: 'trace-1',
      step_name: 'parse',
      status: 'completed',
      started_at: '2024-01-15T10:00:01Z',
      ended_at: '2024-01-15T10:00:03Z',
      duration_ms: 2000,
      metrics: { pages_extracted: 5, text_length: 10000, parser_used: 'PyPDF2' },
      error_message: null,
    },
    {
      id: 'event-3',
      trace_id: 'trace-1',
      step_name: 'chunk',
      status: 'completed',
      started_at: '2024-01-15T10:00:03Z',
      ended_at: '2024-01-15T10:00:04Z',
      duration_ms: 1000,
      metrics: { chunks_created: 25, avg_chunk_size: 400 },
      error_message: null,
    },
    {
      id: 'event-4',
      trace_id: 'trace-1',
      step_name: 'embed',
      status: 'completed',
      started_at: '2024-01-15T10:00:04Z',
      ended_at: '2024-01-15T10:00:06Z',
      duration_ms: 2000,
      metrics: { vectors_generated: 25, embedding_model: 'text-embedding-3-small' },
      error_message: null,
    },
    {
      id: 'event-5',
      trace_id: 'trace-1',
      step_name: 'index',
      status: 'completed',
      started_at: '2024-01-15T10:00:06Z',
      ended_at: '2024-01-15T10:00:07Z',
      duration_ms: 1000,
      metrics: { points_indexed: 25, collection_name: 'kb_docs' },
      error_message: null,
    },
  ],
  total_duration_ms: 7000,
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('ProcessingTimeline', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all processing steps (AC2)', () => {
    mockUseDocumentTimeline.mockReturnValue({
      data: mockTimelineResponse,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDocumentTimeline>);

    render(<ProcessingTimeline documentId="doc-123" />, { wrapper: createWrapper() });

    expect(screen.getByTestId('processing-timeline')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-step-upload')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-step-parse')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-step-chunk')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-step-embed')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-step-index')).toBeInTheDocument();
  });

  it('displays total duration at top (AC8)', () => {
    mockUseDocumentTimeline.mockReturnValue({
      data: mockTimelineResponse,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDocumentTimeline>);

    render(<ProcessingTimeline documentId="doc-123" />, { wrapper: createWrapper() });

    const totalDuration = screen.getByTestId('total-duration');
    expect(totalDuration).toBeInTheDocument();
    expect(totalDuration).toHaveTextContent('Total: 7.0s');
  });

  it('renders loading skeleton while loading', () => {
    mockUseDocumentTimeline.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as ReturnType<typeof useDocumentTimeline>);

    render(<ProcessingTimeline documentId="doc-123" />, { wrapper: createWrapper() });

    expect(screen.getByTestId('timeline-skeleton')).toBeInTheDocument();
  });

  it('renders error state on error', () => {
    mockUseDocumentTimeline.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Failed to fetch timeline'),
    } as ReturnType<typeof useDocumentTimeline>);

    render(<ProcessingTimeline documentId="doc-123" />, { wrapper: createWrapper() });

    expect(screen.getByTestId('timeline-error')).toBeInTheDocument();
    expect(screen.getByText('Failed to load timeline')).toBeInTheDocument();
    expect(screen.getByText('Failed to fetch timeline')).toBeInTheDocument();
  });

  it('renders empty state when no events', () => {
    const emptyResponse: DocumentTimelineResponse = {
      document_id: 'doc-123',
      events: [],
      total_duration_ms: null,
    };
    mockUseDocumentTimeline.mockReturnValue({
      data: emptyResponse,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDocumentTimeline>);

    render(<ProcessingTimeline documentId="doc-123" />, { wrapper: createWrapper() });

    expect(screen.getByTestId('timeline-empty')).toBeInTheDocument();
    expect(screen.getByText('No processing events found for this document')).toBeInTheDocument();
  });

  it('shows Processing Timeline header', () => {
    mockUseDocumentTimeline.mockReturnValue({
      data: mockTimelineResponse,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDocumentTimeline>);

    render(<ProcessingTimeline documentId="doc-123" />, { wrapper: createWrapper() });

    expect(screen.getByText('Processing Timeline')).toBeInTheDocument();
  });

  it('renders step labels correctly', () => {
    mockUseDocumentTimeline.mockReturnValue({
      data: mockTimelineResponse,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useDocumentTimeline>);

    render(<ProcessingTimeline documentId="doc-123" />, { wrapper: createWrapper() });

    expect(screen.getByText('Upload')).toBeInTheDocument();
    expect(screen.getByText('Parse')).toBeInTheDocument();
    expect(screen.getByText('Chunk')).toBeInTheDocument();
    expect(screen.getByText('Embed')).toBeInTheDocument();
    expect(screen.getByText('Index')).toBeInTheDocument();
  });
});

describe('TimelineSkeleton', () => {
  it('renders loading skeleton', () => {
    render(<TimelineSkeleton />);

    expect(screen.getByTestId('timeline-skeleton')).toBeInTheDocument();
  });
});
