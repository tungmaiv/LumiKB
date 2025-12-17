/**
 * Component Tests: QueueStatusCard (Story 5-4, AC-5.4.2)
 *
 * Test Coverage:
 * - Rendering with queue metrics
 * - Badge display (Healthy, High Load, No Workers)
 * - Worker status display (online/offline count)
 * - Click handling for card
 * - Unavailable status display
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueueStatusCard } from '../queue-status-card';
import type { QueueStatus } from '@/types/queue';

describe('QueueStatusCard Component (Story 5-4)', () => {
  const mockQueue: QueueStatus = {
    queue_name: 'document_processing',
    pending_tasks: 10,
    active_tasks: 3,
    workers: [
      {
        worker_id: 'worker-1',
        status: 'online' as const,
        active_tasks: 2,
      },
      {
        worker_id: 'worker-2',
        status: 'online' as const,
        active_tasks: 1,
      },
    ],
    status: 'available' as const,
  };

  describe('[P1] Basic Rendering - AC-5.4.1', () => {
    it('should render queue name', () => {
      render(<QueueStatusCard queue={mockQueue} />);

      expect(screen.getByText('document_processing')).toBeInTheDocument();
    });

    it('should render pending tasks count', () => {
      render(<QueueStatusCard queue={mockQueue} />);

      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });

    it('should render active tasks count', () => {
      render(<QueueStatusCard queue={mockQueue} />);

      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('should render workers online count', () => {
      render(<QueueStatusCard queue={mockQueue} />);

      expect(screen.getByText('2 online')).toBeInTheDocument();
    });

    it('should render Healthy badge when queue is normal', () => {
      render(<QueueStatusCard queue={mockQueue} />);

      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });
  });

  describe('[P1] Badge Display - AC-5.4.2', () => {
    it('should display High Load badge when pending > 100', () => {
      const highLoadQueue: QueueStatus = {
        ...mockQueue,
        pending_tasks: 150,
      };

      render(<QueueStatusCard queue={highLoadQueue} />);

      expect(screen.getByText('High Load')).toBeInTheDocument();
    });

    it('should display Healthy badge when pending <= 100', () => {
      const normalQueue: QueueStatus = {
        ...mockQueue,
        pending_tasks: 50,
      };

      render(<QueueStatusCard queue={normalQueue} />);

      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });

    it('should display No Workers badge when workers array is empty', () => {
      const noWorkersQueue: QueueStatus = {
        ...mockQueue,
        workers: [],
      };

      render(<QueueStatusCard queue={noWorkersQueue} />);

      expect(screen.getByText('No Workers')).toBeInTheDocument();
      // Also shows "No workers" text in the worker count area
      expect(screen.getByText('No workers')).toBeInTheDocument();
    });

    it('should display offline workers count when some workers offline', () => {
      const offlineWorkersQueue: QueueStatus = {
        ...mockQueue,
        workers: [
          {
            worker_id: 'worker-1',
            status: 'online' as const,
            active_tasks: 2,
          },
          {
            worker_id: 'worker-2',
            status: 'offline' as const,
            active_tasks: 0,
          },
        ],
      };

      render(<QueueStatusCard queue={offlineWorkersQueue} />);

      expect(screen.getByText('1 online')).toBeInTheDocument();
      expect(screen.getByText('1 offline')).toBeInTheDocument();
    });

    it('should not display offline count when all workers online', () => {
      render(<QueueStatusCard queue={mockQueue} />);

      expect(screen.queryByText(/offline/)).not.toBeInTheDocument();
    });
  });

  describe('[P1] Click Handling', () => {
    it('should call onClick when card is clicked', () => {
      const handleClick = vi.fn();

      render(<QueueStatusCard queue={mockQueue} onClick={handleClick} />);

      // Click on the card itself (queue name is a good target)
      const queueName = screen.getByText('document_processing');
      fireEvent.click(queueName);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should not throw when clicked without onClick handler', () => {
      render(<QueueStatusCard queue={mockQueue} />);

      const queueName = screen.getByText('document_processing');
      // Should not throw
      expect(() => fireEvent.click(queueName)).not.toThrow();
    });
  });

  describe('[P0] Unavailable Status - AC-5.4.5', () => {
    it('should display Unavailable when status is unavailable', () => {
      const unavailableQueue: QueueStatus = {
        ...mockQueue,
        pending_tasks: 0,
        active_tasks: 0,
        workers: [],
        status: 'unavailable' as const,
      };

      render(<QueueStatusCard queue={unavailableQueue} />);

      expect(screen.getByText('Unavailable')).toBeInTheDocument();
    });

    it('should apply destructive border when status is unavailable', () => {
      const unavailableQueue: QueueStatus = {
        ...mockQueue,
        status: 'unavailable' as const,
      };

      const { container } = render(<QueueStatusCard queue={unavailableQueue} />);

      // Should have destructive border class
      const card = container.querySelector('.border-destructive');
      expect(card).toBeInTheDocument();
    });

    it('should not display pending/active counts when unavailable', () => {
      const unavailableQueue: QueueStatus = {
        ...mockQueue,
        pending_tasks: 10,
        active_tasks: 5,
        status: 'unavailable' as const,
      };

      render(<QueueStatusCard queue={unavailableQueue} />);

      // When unavailable, the content section changes
      expect(screen.getByText('Unavailable')).toBeInTheDocument();
      // Pending/Active text labels should not appear
      expect(screen.queryByText('Pending')).not.toBeInTheDocument();
      expect(screen.queryByText('Active')).not.toBeInTheDocument();
    });
  });

  describe('[P2] Edge Cases', () => {
    it('should handle zero pending tasks', () => {
      const zeroQueue: QueueStatus = {
        ...mockQueue,
        pending_tasks: 0,
      };

      render(<QueueStatusCard queue={zeroQueue} />);

      // Find the pending count (there's a "0" displayed)
      const pendingSection = screen.getByText('Pending');
      const container = pendingSection.parentElement;
      expect(container).toHaveTextContent('0');
    });

    it('should handle zero active tasks', () => {
      const zeroQueue: QueueStatus = {
        ...mockQueue,
        active_tasks: 0,
      };

      render(<QueueStatusCard queue={zeroQueue} />);

      // Find the active count
      const activeSection = screen.getByText('Active');
      const container = activeSection.parentElement;
      expect(container).toHaveTextContent('0');
    });

    it('should handle very long queue names', () => {
      const longNameQueue: QueueStatus = {
        ...mockQueue,
        queue_name: 'very_long_queue_name_that_might_wrap_to_multiple_lines',
      };

      render(<QueueStatusCard queue={longNameQueue} />);

      expect(
        screen.getByText('very_long_queue_name_that_might_wrap_to_multiple_lines')
      ).toBeInTheDocument();
    });

    it('should apply cursor-pointer class for clickable card', () => {
      const { container } = render(<QueueStatusCard queue={mockQueue} />);

      const card = container.firstChild;
      expect(card).toHaveClass('cursor-pointer');
    });
  });
});
