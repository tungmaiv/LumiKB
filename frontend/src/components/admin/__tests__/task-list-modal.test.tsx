/**
 * Component Tests: TaskListModal (Story 5-4, AC-5.4.3)
 *
 * Test Coverage:
 * - Rendering task table with all required columns
 * - Task details display (truncated ID, simplified name)
 * - Started time formatting (relative time)
 * - Duration display
 * - Modal open/close behavior
 * - Loading and error states
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TaskListModal } from '../task-list-modal';

// Mock the useQueueTasks hook
vi.mock('@/hooks/useQueueTasks', () => ({
  useQueueTasks: vi.fn(),
}));

import { useQueueTasks } from '@/hooks/useQueueTasks';

const mockUseQueueTasks = vi.mocked(useQueueTasks);

// Wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('TaskListModal Component (Story 5-4, AC-5.4.3)', () => {
  const mockActiveTasks = [
    {
      task_id: 'task-12345678-1234-1234-1234-123456789012',
      task_name: 'app.workers.document_tasks.process_document',
      status: 'active' as const,
      started_at: new Date('2025-12-02T10:00:00Z').toISOString(),
      estimated_duration: 3500,
    },
    {
      task_id: 'task-87654321-4321-4321-4321-210987654321',
      task_name: 'app.workers.embedding_tasks.generate_embeddings',
      status: 'active' as const,
      started_at: new Date('2025-12-02T10:05:00Z').toISOString(),
      estimated_duration: 65000,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock - return tasks
    mockUseQueueTasks.mockReturnValue({
      data: mockActiveTasks,
      isLoading: false,
      error: null,
      isError: false,
      isPending: false,
      isSuccess: true,
      status: 'success',
      fetchStatus: 'idle',
      refetch: vi.fn(),
      // Add other required QueryResult fields
    } as unknown as ReturnType<typeof useQueueTasks>);
  });

  describe('[P1] Table Structure - AC-5.4.3', () => {
    it('should render all required column headers', () => {
      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      // Verify all 5 required columns
      expect(screen.getByText('Task ID')).toBeInTheDocument();
      expect(screen.getByText('Task Name')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Started')).toBeInTheDocument();
      expect(screen.getByText('Duration')).toBeInTheDocument();
    });

    it('should render task rows with truncated IDs', () => {
      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      // Task ID should be truncated to first 8 chars + "..."
      expect(screen.getByText('task-123...')).toBeInTheDocument();
      expect(screen.getByText('task-876...')).toBeInTheDocument();
    });

    it('should render task name simplified (last segment only)', () => {
      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      // Task name shows only the function name after the last dot
      expect(screen.getByText('process_document')).toBeInTheDocument();
      expect(screen.getByText('generate_embeddings')).toBeInTheDocument();
    });

    it('should display queue name in modal title', () => {
      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/Active Tasks.*document_processing/i)).toBeInTheDocument();
    });
  });

  describe('[P1] Modal Behavior', () => {
    it('should not render content when open is false', () => {
      render(<TaskListModal open={false} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      // Modal content should not be visible
      expect(screen.queryByText('Task ID')).not.toBeInTheDocument();
    });

    it('should call onClose when dialog is closed', () => {
      const handleClose = vi.fn();

      render(<TaskListModal open={true} onClose={handleClose} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      // Shadcn Dialog uses onOpenChange which triggers onClose
      // The close button should be accessible
      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      expect(handleClose).toHaveBeenCalled();
    });

    it('should display description about sorting', () => {
      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/sorted by newest first/i)).toBeInTheDocument();
    });
  });

  describe('[P1] Loading and Error States', () => {
    it('should display loading state', () => {
      mockUseQueueTasks.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        isError: false,
        isPending: true,
        isSuccess: false,
        status: 'pending',
        fetchStatus: 'fetching',
        refetch: vi.fn(),
      } as unknown as ReturnType<typeof useQueueTasks>);

      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/loading tasks/i)).toBeInTheDocument();
    });

    it('should display error state', () => {
      mockUseQueueTasks.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
        isError: true,
        isPending: false,
        isSuccess: false,
        status: 'error',
        fetchStatus: 'idle',
        refetch: vi.fn(),
      } as unknown as ReturnType<typeof useQueueTasks>);

      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/failed to load tasks/i)).toBeInTheDocument();
    });

    it('should render empty state when no tasks', () => {
      mockUseQueueTasks.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        isError: false,
        isPending: false,
        isSuccess: true,
        status: 'success',
        fetchStatus: 'idle',
        refetch: vi.fn(),
      } as unknown as ReturnType<typeof useQueueTasks>);

      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/no active tasks/i)).toBeInTheDocument();
    });
  });

  describe('[P2] Duration Formatting', () => {
    it('should display duration in seconds for short durations', () => {
      mockUseQueueTasks.mockReturnValue({
        data: [
          {
            ...mockActiveTasks[0],
            estimated_duration: 5000, // 5 seconds
          },
        ],
        isLoading: false,
        error: null,
        isError: false,
        isPending: false,
        isSuccess: true,
        status: 'success',
        fetchStatus: 'idle',
        refetch: vi.fn(),
      } as unknown as ReturnType<typeof useQueueTasks>);

      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('5s')).toBeInTheDocument();
    });

    it('should display duration in minutes and seconds for longer durations', () => {
      mockUseQueueTasks.mockReturnValue({
        data: [
          {
            ...mockActiveTasks[0],
            estimated_duration: 125000, // 2m 5s
          },
        ],
        isLoading: false,
        error: null,
        isError: false,
        isPending: false,
        isSuccess: true,
        status: 'success',
        fetchStatus: 'idle',
        refetch: vi.fn(),
      } as unknown as ReturnType<typeof useQueueTasks>);

      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('2m 5s')).toBeInTheDocument();
    });

    it('should display N/A for null duration', () => {
      mockUseQueueTasks.mockReturnValue({
        data: [
          {
            ...mockActiveTasks[0],
            estimated_duration: null,
          },
        ],
        isLoading: false,
        error: null,
        isError: false,
        isPending: false,
        isSuccess: true,
        status: 'success',
        fetchStatus: 'idle',
        refetch: vi.fn(),
      } as unknown as ReturnType<typeof useQueueTasks>);

      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });

  describe('[P2] Hook Integration', () => {
    it('should pass correct parameters to useQueueTasks', () => {
      render(<TaskListModal open={true} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      expect(mockUseQueueTasks).toHaveBeenCalledWith('document_processing', 'active', true);
    });

    it('should disable query when modal is closed', () => {
      render(<TaskListModal open={false} onClose={vi.fn()} queueName="document_processing" />, {
        wrapper: createWrapper(),
      });

      expect(mockUseQueueTasks).toHaveBeenCalledWith('document_processing', 'active', false);
    });
  });
});
