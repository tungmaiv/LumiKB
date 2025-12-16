/**
 * Waterfall Timeline Component Tests
 *
 * Story 9-8: Trace Viewer UI Component
 * AC10: Unit tests for component rendering and user interactions
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { WaterfallTimeline } from '../waterfall-timeline';
import type { SpanDetail } from '@/hooks/useTraces';

const baseTime = new Date('2024-01-15T10:00:00.000Z');

const mockSpans: SpanDetail[] = [
  {
    span_id: 'span1',
    parent_span_id: null,
    name: 'root_operation',
    span_type: 'internal',
    status: 'completed',
    started_at: baseTime.toISOString(),
    ended_at: new Date(baseTime.getTime() + 1000).toISOString(),
    duration_ms: 1000,
    input_tokens: null,
    output_tokens: null,
    model: null,
    error_message: null,
    metadata: null,
  },
  {
    span_id: 'span2',
    parent_span_id: 'span1',
    name: 'llm_call',
    span_type: 'llm',
    status: 'completed',
    started_at: new Date(baseTime.getTime() + 100).toISOString(),
    ended_at: new Date(baseTime.getTime() + 600).toISOString(),
    duration_ms: 500,
    input_tokens: 100,
    output_tokens: 200,
    model: 'gpt-4',
    error_message: null,
    metadata: { cost_usd: 0.05 },
  },
  {
    span_id: 'span3',
    parent_span_id: 'span1',
    name: 'db_query',
    span_type: 'db',
    status: 'failed',
    started_at: new Date(baseTime.getTime() + 700).toISOString(),
    ended_at: new Date(baseTime.getTime() + 900).toISOString(),
    duration_ms: 200,
    input_tokens: null,
    output_tokens: null,
    model: null,
    error_message: 'Connection timeout',
    metadata: { query: 'SELECT * FROM users' },
  },
];

describe('WaterfallTimeline', () => {
  it('renders all spans correctly', () => {
    const onSelectSpan = vi.fn();

    render(
      <WaterfallTimeline
        spans={mockSpans}
        totalDuration={1000}
        selectedSpanId={null}
        onSelectSpan={onSelectSpan}
      />
    );

    // Check span names are displayed
    expect(screen.getByText('root_operation')).toBeInTheDocument();
    expect(screen.getByText('llm_call')).toBeInTheDocument();
    expect(screen.getByText('db_query')).toBeInTheDocument();
  });

  it('displays time scale header', () => {
    const onSelectSpan = vi.fn();

    render(
      <WaterfallTimeline
        spans={mockSpans}
        totalDuration={1000}
        selectedSpanId={null}
        onSelectSpan={onSelectSpan}
      />
    );

    // Check time scale markers are present (formatTimeLabel uses "1.0s" for 1000ms)
    // Some values appear both in header and span rows, so use getAllByText
    expect(screen.getByText('0ms')).toBeInTheDocument();
    expect(screen.getByText('250ms')).toBeInTheDocument();
    expect(screen.getAllByText('500ms').length).toBeGreaterThan(0); // header + llm_call row
    expect(screen.getByText('750ms')).toBeInTheDocument();
    expect(screen.getAllByText('1.0s').length).toBeGreaterThan(0); // header + root row
  });

  it('calls onSelectSpan when span row is clicked', () => {
    const onSelectSpan = vi.fn();

    render(
      <WaterfallTimeline
        spans={mockSpans}
        totalDuration={1000}
        selectedSpanId={null}
        onSelectSpan={onSelectSpan}
      />
    );

    const spanRow = screen.getByTestId('span-row-span2');
    fireEvent.click(spanRow);

    expect(onSelectSpan).toHaveBeenCalledWith('span2');
  });

  it('highlights selected span row', () => {
    const onSelectSpan = vi.fn();

    render(
      <WaterfallTimeline
        spans={mockSpans}
        totalDuration={1000}
        selectedSpanId="span2"
        onSelectSpan={onSelectSpan}
      />
    );

    const selectedRow = screen.getByTestId('span-row-span2');
    expect(selectedRow).toHaveClass('bg-muted');
  });

  it('displays empty state when no spans', () => {
    const onSelectSpan = vi.fn();

    render(
      <WaterfallTimeline
        spans={[]}
        totalDuration={1000}
        selectedSpanId={null}
        onSelectSpan={onSelectSpan}
      />
    );

    expect(screen.getByText('No spans found for this trace')).toBeInTheDocument();
  });

  it('shows duration labels for each span', () => {
    const onSelectSpan = vi.fn();

    render(
      <WaterfallTimeline
        spans={mockSpans}
        totalDuration={1000}
        selectedSpanId={null}
        onSelectSpan={onSelectSpan}
      />
    );

    // Check duration labels (formatTimeLabel uses "1.0s" for 1000ms)
    // Some values appear both in header and span row, so use getAllByText
    const oneSecLabels = screen.getAllByText('1.0s');
    expect(oneSecLabels.length).toBeGreaterThan(0); // root_operation + header
    const fiveHundredMsLabels = screen.getAllByText('500ms');
    expect(fiveHundredMsLabels.length).toBeGreaterThan(0); // llm_call + header
    expect(screen.getByText('200ms')).toBeInTheDocument(); // db_query
  });

  it('handles keyboard navigation', () => {
    const onSelectSpan = vi.fn();

    render(
      <WaterfallTimeline
        spans={mockSpans}
        totalDuration={1000}
        selectedSpanId={null}
        onSelectSpan={onSelectSpan}
      />
    );

    const spanRow = screen.getByTestId('span-row-span1');
    fireEvent.keyDown(spanRow, { key: 'Enter' });

    expect(onSelectSpan).toHaveBeenCalledWith('span1');
  });
});
