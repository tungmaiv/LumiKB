/**
 * Session Detail Panel Component Tests
 *
 * Story 9-9: Chat History Viewer UI
 * AC10: Unit tests for component rendering and user interactions
 * AC5: Click to expand conversation in side panel
 * AC6: Infinite scroll for long conversations
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

import { SessionDetailPanel } from '../session-detail-panel';

// Mock the useChatMessages hook
vi.mock('@/hooks/useChatHistory', () => ({
  useChatMessages: vi.fn(() => ({
    data: {
      pages: [
        {
          items: [
            {
              id: 'msg-1',
              trace_id: 'trace-1',
              session_id: 'session-123',
              role: 'user',
              content: 'Test question',
              user_id: 'user-1',
              kb_id: 'kb-1',
              created_at: new Date().toISOString(),
              citations: null,
              token_count: null,
              response_time_ms: null,
            },
            {
              id: 'msg-2',
              trace_id: 'trace-2',
              session_id: 'session-123',
              role: 'assistant',
              content: 'Test answer',
              user_id: null,
              kb_id: 'kb-1',
              created_at: new Date().toISOString(),
              citations: [],
              token_count: 100,
              response_time_ms: 500,
            },
          ],
          total: 2,
          has_more: false,
        },
      ],
    },
    isLoading: false,
    error: null,
    hasNextPage: false,
    fetchNextPage: vi.fn(),
    isFetchingNextPage: false,
  })),
}));

function renderWithQueryClient(component: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);
}

describe('SessionDetailPanel', () => {
  it('renders panel when sessionId is provided (AC5)', () => {
    const onClose = vi.fn();

    renderWithQueryClient(<SessionDetailPanel sessionId="session-123" onClose={onClose} />);

    // Panel should be visible with conversation
    expect(screen.getByText('Conversation')).toBeInTheDocument();
  });

  it('does not render when sessionId is null', () => {
    const onClose = vi.fn();

    renderWithQueryClient(<SessionDetailPanel sessionId={null} onClose={onClose} />);

    // Panel should not be visible
    expect(screen.queryByText('Conversation')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();

    renderWithQueryClient(<SessionDetailPanel sessionId="session-123" onClose={onClose} />);

    // Find and click close button
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalled();
  });

  it('displays messages from the conversation', () => {
    const onClose = vi.fn();

    renderWithQueryClient(<SessionDetailPanel sessionId="session-123" onClose={onClose} />);

    // Check that messages are displayed
    expect(screen.getByText('Test question')).toBeInTheDocument();
    expect(screen.getByText('Test answer')).toBeInTheDocument();
  });

  it('has export button', () => {
    const onClose = vi.fn();

    renderWithQueryClient(<SessionDetailPanel sessionId="session-123" onClose={onClose} />);

    // Check for export button
    const exportButton = screen.getByRole('button', { name: /export/i });
    expect(exportButton).toBeInTheDocument();
  });

  it('handles keyboard escape to close', () => {
    const onClose = vi.fn();

    renderWithQueryClient(<SessionDetailPanel sessionId="session-123" onClose={onClose} />);

    // Press Escape key
    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onClose).toHaveBeenCalled();
  });
});
