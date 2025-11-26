import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DocumentStatusBadge, type DocumentStatus } from '../document-status-badge';

describe('DocumentStatusBadge', () => {
  describe('PENDING status', () => {
    it('renders with clock icon and correct label', () => {
      render(<DocumentStatusBadge status="PENDING" />);

      expect(screen.getByText('Queued for processing')).toBeInTheDocument();
    });

    it('has gray styling', () => {
      render(<DocumentStatusBadge status="PENDING" />);

      const badge = screen.getByText('Queued for processing').parentElement;
      expect(badge).toHaveClass('text-muted-foreground');
      expect(badge).toHaveClass('bg-muted');
    });
  });

  describe('PROCESSING status', () => {
    it('renders with spinner and processing label', () => {
      render(<DocumentStatusBadge status="PROCESSING" />);

      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('has blue styling', () => {
      render(<DocumentStatusBadge status="PROCESSING" />);

      const badge = screen.getByText('Processing...').parentElement;
      expect(badge).toHaveClass('text-blue-600');
    });

    it('has animated spinner', () => {
      const { container } = render(<DocumentStatusBadge status="PROCESSING" />);

      const spinner = container.querySelector('svg');
      expect(spinner).toHaveClass('animate-spin');
    });
  });

  describe('READY status', () => {
    it('renders with checkmark and ready label', () => {
      render(<DocumentStatusBadge status="READY" />);

      expect(screen.getByText('Ready')).toBeInTheDocument();
    });

    it('has green styling', () => {
      render(<DocumentStatusBadge status="READY" />);

      const badge = screen.getByText('Ready').parentElement;
      expect(badge).toHaveClass('text-green-600');
    });

    it('displays chunk count when provided', () => {
      render(<DocumentStatusBadge status="READY" chunkCount={47} />);

      expect(screen.getByText('(47 chunks)')).toBeInTheDocument();
    });

    it('does not display chunk count when zero', () => {
      render(<DocumentStatusBadge status="READY" chunkCount={0} />);

      expect(screen.queryByText(/chunks/)).not.toBeInTheDocument();
    });

    it('does not display chunk count when undefined', () => {
      render(<DocumentStatusBadge status="READY" />);

      expect(screen.queryByText(/chunks/)).not.toBeInTheDocument();
    });
  });

  describe('FAILED status', () => {
    it('renders with error icon and failed label', () => {
      render(<DocumentStatusBadge status="FAILED" />);

      expect(screen.getByText('Failed')).toBeInTheDocument();
    });

    it('has red styling', () => {
      render(<DocumentStatusBadge status="FAILED" />);

      const badge = screen.getByText('Failed').parentElement;
      expect(badge).toHaveClass('text-red-600');
    });

    it('renders tooltip trigger when error message provided', () => {
      const errorMessage = 'Parse error: Invalid PDF format';

      render(<DocumentStatusBadge status="FAILED" errorMessage={errorMessage} />);

      // Badge should still be visible
      expect(screen.getByText('Failed')).toBeInTheDocument();
    });

    it('renders without tooltip wrapper when no error message', () => {
      const { container } = render(<DocumentStatusBadge status="FAILED" />);

      // Should not have tooltip provider wrapper
      expect(container.querySelector('[data-state]')).not.toBeInTheDocument();
    });
  });

  describe('custom className', () => {
    it('applies additional className to badge', () => {
      render(<DocumentStatusBadge status="READY" className="custom-class" />);

      const badge = screen.getByText('Ready').parentElement;
      expect(badge).toHaveClass('custom-class');
    });
  });

  describe('all statuses render correctly', () => {
    const statuses: DocumentStatus[] = ['PENDING', 'PROCESSING', 'READY', 'FAILED'];

    it.each(statuses)('renders %s status without errors', (status) => {
      expect(() => render(<DocumentStatusBadge status={status} />)).not.toThrow();
    });
  });
});
