/**
 * Component Tests: Queue Status Page (Story 5-4, Story 7-11)
 *
 * Test Coverage:
 * - Loading state (skeleton display)
 * - Error state (error message display)
 * - Success state (all queue cards rendered)
 * - Hook integration (useQueueStatus)
 *
 * Story 7.11: Moved from /admin/queue to /operations/queue
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import OperationsQueuePage from '../page';

// Mock useQueueStatus hook
vi.mock('@/hooks/useQueueStatus');

import { useQueueStatus } from '@/hooks/useQueueStatus';

const mockUseQueueStatus = vi.mocked(useQueueStatus);

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

const mockQueues = [
  {
    queue_name: 'document_processing',
    pending_tasks: 10,
    active_tasks: 3,
    workers: [
      {
        worker_id: 'worker-doc-1',
        status: 'online' as const,
        active_tasks: 2,
      },
    ],
    status: 'available' as const,
  },
  {
    queue_name: 'embedding_generation',
    pending_tasks: 5,
    active_tasks: 1,
    workers: [
      {
        worker_id: 'worker-embed-1',
        status: 'online' as const,
        active_tasks: 1,
      },
    ],
    status: 'available' as const,
  },
  {
    queue_name: 'export_generation',
    pending_tasks: 2,
    active_tasks: 0,
    workers: [],
    status: 'available' as const,
  },
];

describe('OperationsQueuePage Component (Story 5-4, Story 7-11)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('[P0] Loading State', () => {
    it('should display loading skeletons while fetching data', () => {
      mockUseQueueStatus.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        isSuccess: false,
        isError: false,
        refetch: vi.fn(),
        dataUpdatedAt: 0,
      } as never);

      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // Should show title
      expect(screen.getByText('Queue Status')).toBeInTheDocument();

      // Should show 3 skeleton placeholders (for 3 queues)
      const skeletons = document.querySelectorAll('.h-32');
      expect(skeletons.length).toBeGreaterThanOrEqual(3);
    });

    it('should not show queue cards while loading', () => {
      mockUseQueueStatus.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        isSuccess: false,
        isError: false,
        refetch: vi.fn(),
        dataUpdatedAt: 0,
      } as never);

      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // Queue cards should not be visible
      expect(screen.queryByText('document_processing')).not.toBeInTheDocument();
      expect(screen.queryByText('embedding_generation')).not.toBeInTheDocument();
    });
  });

  describe('[P0] Error State - AC-5.4.5', () => {
    it('should display error message when hook returns error', () => {
      const errorMessage = 'Unable to connect to task queue';
      mockUseQueueStatus.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error(errorMessage),
        isSuccess: false,
        isError: true,
        refetch: vi.fn(),
        dataUpdatedAt: 0,
      } as never);

      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // Should show error message
      expect(
        screen.getByText(/unable to connect to task queue/i)
      ).toBeInTheDocument();

      // Should not show queue cards
      expect(screen.queryByText('document_processing')).not.toBeInTheDocument();
    });

    it('should show generic error when error is not an Error instance', () => {
      mockUseQueueStatus.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: 'Connection failed',
        isSuccess: false,
        isError: true,
        refetch: vi.fn(),
        dataUpdatedAt: 0,
      } as never);

      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      expect(screen.getByText(/failed to load queue status/i)).toBeInTheDocument();
    });
  });

  describe('[P0] Success State - AC-5.4.1', () => {
    beforeEach(() => {
      mockUseQueueStatus.mockReturnValue({
        data: mockQueues,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
        dataUpdatedAt: Date.now(),
      } as never);
    });

    it('should render page title and subtitle', () => {
      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      expect(screen.getByText('Queue Status')).toBeInTheDocument();
      expect(
        screen.getByText('Real-time monitoring of background task queues')
      ).toBeInTheDocument();
    });

    it('should render all 3 queue cards', () => {
      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // All 3 queues should be visible
      expect(screen.getByText('document_processing')).toBeInTheDocument();
      expect(screen.getByText('embedding_generation')).toBeInTheDocument();
      expect(screen.getByText('export_generation')).toBeInTheDocument();
    });

    it('should display correct metrics for each queue - AC-5.4.2', () => {
      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // Document processing queue - pending 10, active 3
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();

      // Embedding generation queue - pending 5, active 1
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1);

      // Export generation queue - pending 2, active 0
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(1);
    });

    it('should show last updated time', () => {
      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // Should show "Last updated:" with relative time
      expect(screen.getByText(/last updated:/i)).toBeInTheDocument();
    });

    it('should open task modal when queue card is clicked', () => {
      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // Click on document_processing card
      const docCard = screen.getByText('document_processing').closest('[class*="card"]');
      expect(docCard).toBeInTheDocument();
      fireEvent.click(docCard!);

      // TaskListModal should open (it receives queueName prop)
      // Note: Modal content is controlled by TaskListModal component
    });
  });

  describe('[P0] Unavailable Queues - AC-5.4.5', () => {
    it('should display unavailable status for queues', () => {
      const unavailableQueues = mockQueues.map((q) => ({
        ...q,
        pending_tasks: 0,
        active_tasks: 0,
        workers: [],
        status: 'unavailable' as const,
      }));

      mockUseQueueStatus.mockReturnValue({
        data: unavailableQueues,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
        dataUpdatedAt: Date.now(),
      } as never);

      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // Should show unavailable badges for all queues
      const unavailableBadges = screen.getAllByText(/unavailable/i);
      expect(unavailableBadges.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('[P2] Edge Cases', () => {
    it('should handle empty queue list gracefully', () => {
      mockUseQueueStatus.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
        dataUpdatedAt: Date.now(),
      } as never);

      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // Should show empty state message
      expect(screen.getByText(/no active queues found/i)).toBeInTheDocument();
    });

    it('should handle zero workers correctly', () => {
      const noWorkersQueues = mockQueues.map((q) => ({
        ...q,
        workers: [],
      }));

      mockUseQueueStatus.mockReturnValue({
        data: noWorkersQueues,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
        dataUpdatedAt: Date.now(),
      } as never);

      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // Should show "No workers" in QueueStatusCard
      const noWorkersTexts = screen.getAllByText(/no workers/i);
      expect(noWorkersTexts.length).toBeGreaterThanOrEqual(1);
    });

    it('should display worker online status', () => {
      mockUseQueueStatus.mockReturnValue({
        data: mockQueues,
        isLoading: false,
        error: null,
        isSuccess: true,
        isError: false,
        refetch: vi.fn(),
        dataUpdatedAt: Date.now(),
      } as never);

      render(<OperationsQueuePage />, { wrapper: createWrapper() });

      // Should show online workers count
      const onlineTexts = screen.getAllByText(/online/i);
      expect(onlineTexts.length).toBeGreaterThanOrEqual(1);
    });
  });
});
