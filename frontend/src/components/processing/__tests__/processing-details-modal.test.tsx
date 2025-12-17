/**
 * Unit tests for ProcessingDetailsModal component
 * Story 5-23 (AC-5.23.3): Step-by-step processing details with timing
 *
 * Tests modal rendering, step timeline, error display, and loading states.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { ProcessingDetailsModal } from '../processing-details-modal';

// Mock fetch
global.fetch = vi.fn();

// Create wrapper with QueryClientProvider
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// Mock processing details data
const mockProcessingDetails = {
  id: 'doc-123',
  original_filename: 'test-document.pdf',
  file_type: 'pdf',
  file_size: 2048000,
  status: 'processing',
  current_step: 'embed',
  chunk_count: null,
  total_duration_ms: null,
  steps: [
    {
      step: 'upload',
      status: 'done',
      started_at: '2025-12-06T10:00:00Z',
      completed_at: '2025-12-06T10:00:02Z',
      duration_ms: 2000,
      error: null,
    },
    {
      step: 'parse',
      status: 'done',
      started_at: '2025-12-06T10:00:02Z',
      completed_at: '2025-12-06T10:00:05Z',
      duration_ms: 3000,
      error: null,
    },
    {
      step: 'chunk',
      status: 'done',
      started_at: '2025-12-06T10:00:05Z',
      completed_at: '2025-12-06T10:00:07Z',
      duration_ms: 2000,
      error: null,
    },
    {
      step: 'embed',
      status: 'in_progress',
      started_at: '2025-12-06T10:00:07Z',
      completed_at: null,
      duration_ms: null,
      error: null,
    },
    {
      step: 'index',
      status: 'pending',
      started_at: null,
      completed_at: null,
      duration_ms: null,
      error: null,
    },
    {
      step: 'complete',
      status: 'pending',
      started_at: null,
      completed_at: null,
      duration_ms: null,
      error: null,
    },
  ],
  created_at: '2025-12-06T09:59:55Z',
  processing_started_at: '2025-12-06T10:00:00Z',
  processing_completed_at: null,
};

const mockFailedDetails = {
  ...mockProcessingDetails,
  status: 'failed',
  current_step: 'embed',
  steps: [
    ...mockProcessingDetails.steps.slice(0, 3),
    {
      step: 'embed',
      status: 'error',
      started_at: '2025-12-06T10:00:07Z',
      completed_at: '2025-12-06T10:00:08Z',
      duration_ms: 1000,
      error: 'Embedding service unavailable: connection timeout',
    },
    {
      step: 'index',
      status: 'skipped',
      started_at: null,
      completed_at: null,
      duration_ms: null,
      error: null,
    },
    {
      step: 'complete',
      status: 'skipped',
      started_at: null,
      completed_at: null,
      duration_ms: null,
      error: null,
    },
  ],
};

describe('ProcessingDetailsModal', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] should render modal title when open - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert
    expect(screen.getByText('Processing Details')).toBeInTheDocument();
  });

  it('[P0] should show loading state while fetching - AC-5.23.3', () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert - should show spinner
    expect(screen.getByText('Processing Details')).toBeInTheDocument();
    // Loading spinner should be visible (check for animation)
    const spinners = document.querySelectorAll('.animate-spin');
    expect(spinners.length).toBeGreaterThan(0);
  });

  it('[P0] should display document filename and type - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => {
      expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    });
    expect(screen.getByText('PDF')).toBeInTheDocument();
  });

  it('[P0] should display processing steps timeline - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert - step labels should be visible
    await waitFor(() => {
      expect(screen.getByText('Processing Steps')).toBeInTheDocument();
    });
    expect(screen.getByText('Upload')).toBeInTheDocument();
    expect(screen.getByText('Parse')).toBeInTheDocument();
    expect(screen.getByText('Chunk')).toBeInTheDocument();
    expect(screen.getByText('Embed')).toBeInTheDocument();
    expect(screen.getByText('Index')).toBeInTheDocument();
    expect(screen.getByText('Complete')).toBeInTheDocument();
  });

  it('[P0] should display step status badges - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert - status badges
    await waitFor(() => {
      // Done steps
      const doneBadges = screen.getAllByText('done');
      expect(doneBadges.length).toBe(3); // upload, parse, chunk
    });
    expect(screen.getByText('in_progress')).toBeInTheDocument();
    const pendingBadges = screen.getAllByText('pending');
    expect(pendingBadges.length).toBe(2); // index, complete
  });

  it('[P0] should display step duration for completed steps - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert - durations should be visible (use getAllByText since 2.0s appears twice)
    await waitFor(() => {
      const durations = screen.getAllByText(/Duration:/);
      expect(durations.length).toBeGreaterThanOrEqual(2);
    });
    expect(screen.getByText('Duration: 3.0s')).toBeInTheDocument();
  });

  it('[P0] should display error message for failed steps - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockFailedDetails,
    });

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert - error message should be visible
    await waitFor(() => {
      expect(
        screen.getByText(/Embedding service unavailable: connection timeout/)
      ).toBeInTheDocument();
    });
  });

  it('[P0] should display overall progress percentage - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert - progress should be shown (3 done + 0.5 in_progress = 58%)
    await waitFor(() => {
      expect(screen.getByText('Overall Progress')).toBeInTheDocument();
    });
    expect(screen.getByText('58%')).toBeInTheDocument();
  });

  it('[P0] should not render content when closed', () => {
    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={false} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert - modal should not be visible
    expect(screen.queryByText('Processing Details')).not.toBeInTheDocument();
  });

  it('[P1] should show error state when fetch fails - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => {
      expect(screen.getByText('Error loading details')).toBeInTheDocument();
    });
  });

  it('[P1] should display timestamps section - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert
    await waitFor(() => {
      expect(screen.getByText('Timestamps')).toBeInTheDocument();
    });
    expect(screen.getByText('Created:')).toBeInTheDocument();
  });

  it('[P1] should call onClose when dialog is closed', async () => {
    // Arrange
    const user = userEvent.setup();
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    });

    // Act - press Escape key
    await user.keyboard('{Escape}');

    // Assert
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('[P2] should display file size formatted correctly - AC-5.23.3', async () => {
    // Arrange
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProcessingDetails,
    });

    // Act
    render(
      <ProcessingDetailsModal kbId="kb-123" docId="doc-123" isOpen={true} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Assert - 2048000 bytes = 2.0 MB
    await waitFor(() => {
      expect(screen.getByText('2.0 MB')).toBeInTheDocument();
    });
  });
});
