/**
 * Trace List Component Tests
 *
 * Story 9-8: Trace Viewer UI Component
 * AC10: Unit tests for component rendering and user interactions
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { TraceList, TraceListSkeleton } from '../trace-list';
import type { TraceListItem } from '@/hooks/useTraces';

const mockTraces: TraceListItem[] = [
  {
    trace_id: 'abc123def456789012345678901234ab',
    name: 'chat_completion',
    status: 'completed',
    user_id: '550e8400-e29b-41d4-a716-446655440000',
    kb_id: '550e8400-e29b-41d4-a716-446655440001',
    document_id: null,
    started_at: new Date().toISOString(),
    ended_at: new Date().toISOString(),
    duration_ms: 1234,
    span_count: 5,
  },
  {
    trace_id: 'def456789012345678901234567890cd',
    name: 'document_processing',
    status: 'failed',
    user_id: null,
    kb_id: '550e8400-e29b-41d4-a716-446655440002',
    document_id: '550e8400-e29b-41d4-a716-446655440099',
    started_at: new Date(Date.now() - 3600000).toISOString(),
    ended_at: new Date(Date.now() - 3500000).toISOString(),
    duration_ms: 100000,
    span_count: 12,
  },
  {
    trace_id: 'ghi789012345678901234567890ef12',
    name: 'embedding',
    status: 'in_progress',
    user_id: '550e8400-e29b-41d4-a716-446655440003',
    kb_id: null,
    document_id: null,
    started_at: new Date().toISOString(),
    ended_at: null,
    duration_ms: null,
    span_count: 2,
  },
];

describe('TraceList', () => {
  it('renders traces correctly with all columns', () => {
    const onSelectTrace = vi.fn();

    render(<TraceList traces={mockTraces} selectedTraceId={null} onSelectTrace={onSelectTrace} />);

    // Check table headers
    expect(screen.getByText('Operation')).toBeInTheDocument();
    expect(screen.getByText('Document')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Duration')).toBeInTheDocument();
    expect(screen.getByText('Spans')).toBeInTheDocument();
    expect(screen.getByText('Time')).toBeInTheDocument();

    // Check operation names are formatted
    expect(screen.getByText('Chat Completion')).toBeInTheDocument();
    expect(screen.getByText('Document Processing')).toBeInTheDocument();
    expect(screen.getByText('Embedding')).toBeInTheDocument();

    // Check status badges
    expect(screen.getByText('completed')).toBeInTheDocument();
    expect(screen.getByText('failed')).toBeInTheDocument();
    expect(screen.getByText('in_progress')).toBeInTheDocument();

    // Check span counts
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('calls onSelectTrace when a trace row is clicked', () => {
    const onSelectTrace = vi.fn();

    render(<TraceList traces={mockTraces} selectedTraceId={null} onSelectTrace={onSelectTrace} />);

    const traceRow = screen.getByTestId(`trace-row-${mockTraces[0].trace_id}`);
    fireEvent.click(traceRow);

    expect(onSelectTrace).toHaveBeenCalledWith(mockTraces[0].trace_id);
  });

  it('highlights selected trace row', () => {
    const onSelectTrace = vi.fn();

    render(
      <TraceList
        traces={mockTraces}
        selectedTraceId={mockTraces[0].trace_id}
        onSelectTrace={onSelectTrace}
      />
    );

    const selectedRow = screen.getByTestId(`trace-row-${mockTraces[0].trace_id}`);
    expect(selectedRow).toHaveClass('bg-muted');

    const unselectedRow = screen.getByTestId(`trace-row-${mockTraces[1].trace_id}`);
    expect(unselectedRow).not.toHaveClass('bg-muted');
  });

  it('displays empty state when no traces', () => {
    const onSelectTrace = vi.fn();

    render(<TraceList traces={[]} selectedTraceId={null} onSelectTrace={onSelectTrace} />);

    expect(screen.getByText('No traces found matching filters')).toBeInTheDocument();
  });

  it('formats duration correctly', () => {
    const onSelectTrace = vi.fn();

    render(<TraceList traces={mockTraces} selectedTraceId={null} onSelectTrace={onSelectTrace} />);

    // 1234ms should display as 1.2s
    expect(screen.getByText('1.2s')).toBeInTheDocument();

    // 100000ms should display as 1.7m
    expect(screen.getByText('1.7m')).toBeInTheDocument();

    // null duration should display as - (there might be multiple '-' from document_id column)
    const dashes = screen.getAllByText('-');
    expect(dashes.length).toBeGreaterThan(0);
  });
});

describe('TraceListSkeleton', () => {
  it('renders loading skeleton', () => {
    const { container } = render(<TraceListSkeleton />);

    // Should have skeleton elements (Skeleton component uses animate-pulse class)
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
