/**
 * Timeline Step Component Tests
 *
 * Story 9-10: Document Timeline UI
 * AC10: Unit tests for timeline rendering and interactions
 * AC5: Click to expand step details
 * AC7: Retry count visible for failed steps
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { TimelineStep, type DocumentEventItem } from '../timeline-step';

const mockEvent: DocumentEventItem = {
  id: 'event-1',
  trace_id: 'trace-123',
  step_name: 'parse',
  status: 'completed',
  started_at: '2024-01-15T10:00:00Z',
  ended_at: '2024-01-15T10:00:02Z',
  duration_ms: 2300,
  metrics: {
    pages_extracted: 5,
    text_length: 10000,
    parser_used: 'PyPDF2',
  },
  error_message: null,
};

describe('TimelineStep', () => {
  it('renders step with correct label and duration (AC4)', () => {
    render(<TimelineStep event={mockEvent} isLast={false} />);

    expect(screen.getByText('Parse')).toBeInTheDocument();
    expect(screen.getByText('2.3s')).toBeInTheDocument();
  });

  it('renders step with data-testid based on step name', () => {
    render(<TimelineStep event={mockEvent} isLast={false} />);

    expect(screen.getByTestId('timeline-step-parse')).toBeInTheDocument();
  });

  it('shows correct status icon for completed step (AC3)', () => {
    render(<TimelineStep event={mockEvent} isLast={false} />);

    expect(screen.getByTestId('status-icon-completed')).toBeInTheDocument();
  });

  it('shows correct status icon for failed step', () => {
    const failedEvent: DocumentEventItem = {
      ...mockEvent,
      status: 'failed',
      error_message: 'Parse error',
    };

    render(<TimelineStep event={failedEvent} isLast={false} />);

    expect(screen.getByTestId('status-icon-failed')).toBeInTheDocument();
  });

  it('shows correct status icon for in-progress step', () => {
    const inProgressEvent: DocumentEventItem = {
      ...mockEvent,
      status: 'started',
      ended_at: null,
      duration_ms: null,
    };

    render(<TimelineStep event={inProgressEvent} isLast={false} />);

    expect(screen.getByTestId('status-icon-in-progress')).toBeInTheDocument();
  });

  it('expands to show details when clicked (AC5)', () => {
    render(<TimelineStep event={mockEvent} isLast={false} />);

    // Details should not be visible initially
    expect(screen.queryByTestId('step-detail')).not.toBeInTheDocument();

    // Click to expand
    const step = screen.getByRole('button');
    fireEvent.click(step);

    // Details should now be visible
    expect(screen.getByTestId('step-detail')).toBeInTheDocument();
  });

  it('collapses details when clicked again', () => {
    render(<TimelineStep event={mockEvent} isLast={false} />);

    const step = screen.getByRole('button');

    // Click to expand
    fireEvent.click(step);
    expect(screen.getByTestId('step-detail')).toBeInTheDocument();

    // Click to collapse
    fireEvent.click(step);
    expect(screen.queryByTestId('step-detail')).not.toBeInTheDocument();
  });

  it('expands via keyboard Enter key', () => {
    render(<TimelineStep event={mockEvent} isLast={false} />);

    const step = screen.getByRole('button');
    fireEvent.keyDown(step, { key: 'Enter' });

    expect(screen.getByTestId('step-detail')).toBeInTheDocument();
  });

  it('expands via keyboard Space key', () => {
    render(<TimelineStep event={mockEvent} isLast={false} />);

    const step = screen.getByRole('button');
    fireEvent.keyDown(step, { key: ' ' });

    expect(screen.getByTestId('step-detail')).toBeInTheDocument();
  });

  it('shows retry badge when retry_count > 0 (AC7)', () => {
    const retriedEvent: DocumentEventItem = {
      ...mockEvent,
      retry_count: 2,
    };

    render(<TimelineStep event={retriedEvent} isLast={false} />);

    const retryBadge = screen.getByTestId('retry-badge');
    expect(retryBadge).toBeInTheDocument();
    expect(retryBadge).toHaveTextContent('Retry 2');
  });

  it('does not show retry badge when retry_count is 0', () => {
    const noRetryEvent: DocumentEventItem = {
      ...mockEvent,
      retry_count: 0,
    };

    render(<TimelineStep event={noRetryEvent} isLast={false} />);

    expect(screen.queryByTestId('retry-badge')).not.toBeInTheDocument();
  });

  it('does not show retry badge when retry_count is undefined', () => {
    render(<TimelineStep event={mockEvent} isLast={false} />);

    expect(screen.queryByTestId('retry-badge')).not.toBeInTheDocument();
  });

  it('shows dash for duration when duration_ms is null', () => {
    const inProgressEvent: DocumentEventItem = {
      ...mockEvent,
      duration_ms: null,
    };

    render(<TimelineStep event={inProgressEvent} isLast={false} />);

    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('formats duration in milliseconds correctly', () => {
    const fastEvent: DocumentEventItem = {
      ...mockEvent,
      duration_ms: 45,
    };

    render(<TimelineStep event={fastEvent} isLast={false} />);

    expect(screen.getByText('45ms')).toBeInTheDocument();
  });

  it('formats duration in minutes and seconds correctly', () => {
    const slowEvent: DocumentEventItem = {
      ...mockEvent,
      duration_ms: 90000, // 1m 30s
    };

    render(<TimelineStep event={slowEvent} isLast={false} />);

    expect(screen.getByText('1m 30s')).toBeInTheDocument();
  });
});
