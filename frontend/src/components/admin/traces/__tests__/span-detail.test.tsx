/**
 * Span Detail Component Tests
 *
 * Story 9-8: Trace Viewer UI Component
 * AC10: Unit tests for component rendering and user interactions
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { SpanDetailCard } from '../span-detail';
import type { SpanDetail } from '@/hooks/useTraces';

describe('SpanDetailCard', () => {
  it('renders LLM span with model and token metrics (AC7)', () => {
    const llmSpan: SpanDetail = {
      span_id: 'span-llm-1',
      parent_span_id: null,
      name: 'generate_response',
      span_type: 'llm',
      status: 'completed',
      started_at: '2024-01-15T10:00:00.000Z',
      ended_at: '2024-01-15T10:00:01.500Z',
      duration_ms: 1500,
      input_tokens: 500,
      output_tokens: 1200,
      model: 'gpt-4-turbo',
      error_message: null,
      metadata: { cost_usd: 0.0875 },
    };

    render(<SpanDetailCard span={llmSpan} />);

    // Check span name and type
    expect(screen.getByText('generate_response')).toBeInTheDocument();
    expect(screen.getByText('llm')).toBeInTheDocument();

    // Check LLM-specific metrics (AC7)
    expect(screen.getByText('LLM Metrics')).toBeInTheDocument();
    expect(screen.getByText('gpt-4-turbo')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument(); // Input tokens
    expect(screen.getByText('1,200')).toBeInTheDocument(); // Output tokens
    expect(screen.getByText('1,700')).toBeInTheDocument(); // Total tokens
    expect(screen.getByText('$0.0875')).toBeInTheDocument(); // Cost
  });

  it('renders failed span with error message highlighted (AC6)', () => {
    const failedSpan: SpanDetail = {
      span_id: 'span-failed-1',
      parent_span_id: null,
      name: 'database_query',
      span_type: 'db',
      status: 'failed',
      started_at: '2024-01-15T10:00:00.000Z',
      ended_at: '2024-01-15T10:00:00.500Z',
      duration_ms: 500,
      input_tokens: null,
      output_tokens: null,
      model: null,
      error_message: 'Connection refused: PostgreSQL server unavailable',
      metadata: { query: 'SELECT * FROM users' },
    };

    render(<SpanDetailCard span={failedSpan} />);

    // Check error is displayed
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(
      screen.getByText('Connection refused: PostgreSQL server unavailable')
    ).toBeInTheDocument();

    // Check card has destructive border
    const card = screen.getByTestId('span-detail-card');
    expect(card).toHaveClass('border-destructive');
  });

  it('renders database span with query metrics', () => {
    const dbSpan: SpanDetail = {
      span_id: 'span-db-1',
      parent_span_id: null,
      name: 'fetch_documents',
      span_type: 'db',
      status: 'completed',
      started_at: '2024-01-15T10:00:00.000Z',
      ended_at: '2024-01-15T10:00:00.050Z',
      duration_ms: 50,
      input_tokens: null,
      output_tokens: null,
      model: null,
      error_message: null,
      metadata: {
        operation: 'SELECT',
        table: 'documents',
        rows_affected: 25,
        query: 'SELECT * FROM documents WHERE kb_id = ?',
      },
    };

    render(<SpanDetailCard span={dbSpan} />);

    // Check database metrics
    expect(screen.getByText('Database Metrics')).toBeInTheDocument();
    expect(screen.getByText('SELECT')).toBeInTheDocument();
    expect(screen.getByText('documents')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('SELECT * FROM documents WHERE kb_id = ?')).toBeInTheDocument();
  });

  it('renders external call span with URL and status', () => {
    const externalSpan: SpanDetail = {
      span_id: 'span-ext-1',
      parent_span_id: null,
      name: 'fetch_embeddings',
      span_type: 'external',
      status: 'completed',
      started_at: '2024-01-15T10:00:00.000Z',
      ended_at: '2024-01-15T10:00:00.300Z',
      duration_ms: 300,
      input_tokens: null,
      output_tokens: null,
      model: null,
      error_message: null,
      metadata: {
        url: 'https://api.openai.com/v1/embeddings',
        method: 'POST',
        status_code: 200,
      },
    };

    render(<SpanDetailCard span={externalSpan} />);

    // Check external call metrics
    expect(screen.getByText('External Call')).toBeInTheDocument();
    expect(screen.getByText('https://api.openai.com/v1/embeddings')).toBeInTheDocument();
    expect(screen.getByText('POST')).toBeInTheDocument();
    expect(screen.getByText('200')).toBeInTheDocument();
  });

  it('renders timing information correctly', () => {
    const span: SpanDetail = {
      span_id: 'span-timing-1',
      parent_span_id: null,
      name: 'process_chunk',
      span_type: 'internal',
      status: 'completed',
      started_at: '2024-01-15T10:00:00.123Z',
      ended_at: '2024-01-15T10:00:01.456Z',
      duration_ms: 1333,
      input_tokens: null,
      output_tokens: null,
      model: null,
      error_message: null,
      metadata: null,
    };

    render(<SpanDetailCard span={span} />);

    // Check timing section
    expect(screen.getByText('Timing')).toBeInTheDocument();
    // Multiple elements may show duration, use getAllByText
    const durationElements = screen.getAllByText('1333ms');
    expect(durationElements.length).toBeGreaterThan(0);
  });

  it('displays status badge with correct variant', () => {
    const completedSpan: SpanDetail = {
      span_id: 'span-status-1',
      parent_span_id: null,
      name: 'test_operation',
      span_type: 'internal',
      status: 'completed',
      started_at: '2024-01-15T10:00:00.000Z',
      ended_at: '2024-01-15T10:00:01.000Z',
      duration_ms: 1000,
      input_tokens: null,
      output_tokens: null,
      model: null,
      error_message: null,
      metadata: null,
    };

    render(<SpanDetailCard span={completedSpan} />);

    const badge = screen.getByText('completed');
    expect(badge).toHaveClass('bg-green-100');
  });

  it('shows span IDs in expandable section', () => {
    const span: SpanDetail = {
      span_id: 'abc123def456',
      parent_span_id: 'parent123456',
      name: 'child_operation',
      span_type: 'internal',
      status: 'completed',
      started_at: '2024-01-15T10:00:00.000Z',
      ended_at: '2024-01-15T10:00:01.000Z',
      duration_ms: 1000,
      input_tokens: null,
      output_tokens: null,
      model: null,
      error_message: null,
      metadata: null,
    };

    render(<SpanDetailCard span={span} />);

    // Check span IDs section exists
    expect(screen.getByText('Span IDs')).toBeInTheDocument();
    expect(screen.getByText('Span: abc123def456')).toBeInTheDocument();
    expect(screen.getByText('Parent: parent123456')).toBeInTheDocument();
  });
});
