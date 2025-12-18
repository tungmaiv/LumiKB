/**
 * Tests for SessionSelector component (Story 8-0: Chat Session Persistence)
 *
 * Note: Radix UI DropdownMenu has complex portal/focus behaviors that don't render
 * dropdown content in jsdom reliably. These tests focus on the trigger behavior
 * and hook integration. Full dropdown interactions are better tested via E2E.
 */

import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { SessionSelector } from '../session-selector';

// Mock useChatSessions hook
vi.mock('@/hooks/useChatSessions', () => ({
  useChatSessions: vi.fn(() => ({
    sessions: [],
    total: 0,
    maxSessions: 10,
    isLoading: false,
    error: null,
    refresh: vi.fn(),
    loadSession: vi.fn(),
    isLoadingSession: false,
  })),
}));

describe('SessionSelector', () => {
  const mockOnSessionSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders history button with trigger', () => {
    render(<SessionSelector kbId="test-kb" onSessionSelect={mockOnSessionSelect} />);

    expect(screen.getByTestId('session-selector-trigger')).toBeInTheDocument();
    expect(screen.getByText('History')).toBeInTheDocument();
  });

  it('shows session count in badge when sessions exist', async () => {
    const { useChatSessions } = await import('@/hooks/useChatSessions');

    vi.mocked(useChatSessions).mockReturnValue({
      sessions: [
        {
          conversation_id: 'conv-1',
          kb_id: 'test-kb',
          message_count: 4,
          first_message_preview: 'What is TOGAF?',
          last_message_at: new Date().toISOString(),
          first_message_at: new Date().toISOString(),
        },
        {
          conversation_id: 'conv-2',
          kb_id: 'test-kb',
          message_count: 6,
          first_message_preview: 'Explain architecture',
          last_message_at: new Date(Date.now() - 86400000).toISOString(),
          first_message_at: new Date(Date.now() - 86400000).toISOString(),
        },
      ],
      total: 2,
      maxSessions: 10,
      isLoading: false,
      error: null,
      refresh: vi.fn(),
      loadSession: vi.fn(),
      isLoadingSession: false,
    });

    render(<SessionSelector kbId="test-kb" onSessionSelect={mockOnSessionSelect} />);

    expect(screen.getByText('(2)')).toBeInTheDocument();
  });

  it('disables trigger when disabled prop is true', () => {
    render(
      <SessionSelector kbId="test-kb" onSessionSelect={mockOnSessionSelect} disabled={true} />
    );

    expect(screen.getByTestId('session-selector-trigger')).toBeDisabled();
  });

  it('disables trigger when session is loading', async () => {
    const { useChatSessions } = await import('@/hooks/useChatSessions');

    vi.mocked(useChatSessions).mockReturnValue({
      sessions: [],
      total: 0,
      maxSessions: 10,
      isLoading: false,
      error: null,
      refresh: vi.fn(),
      loadSession: vi.fn(),
      isLoadingSession: true, // Loading a session
    });

    render(<SessionSelector kbId="test-kb" onSessionSelect={mockOnSessionSelect} />);

    expect(screen.getByTestId('session-selector-trigger')).toBeDisabled();
  });

  it('shows loading spinner when isLoadingSession is true', async () => {
    const { useChatSessions } = await import('@/hooks/useChatSessions');

    vi.mocked(useChatSessions).mockReturnValue({
      sessions: [],
      total: 0,
      maxSessions: 10,
      isLoading: false,
      error: null,
      refresh: vi.fn(),
      loadSession: vi.fn(),
      isLoadingSession: true,
    });

    render(<SessionSelector kbId="test-kb" onSessionSelect={mockOnSessionSelect} />);

    // Should have the loader icon (lucide-loader-2)
    const trigger = screen.getByTestId('session-selector-trigger');
    const spinner = trigger.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('hides badge when total is 0', async () => {
    const { useChatSessions } = await import('@/hooks/useChatSessions');

    vi.mocked(useChatSessions).mockReturnValue({
      sessions: [],
      total: 0,
      maxSessions: 10,
      isLoading: false,
      error: null,
      refresh: vi.fn(),
      loadSession: vi.fn(),
      isLoadingSession: false,
    });

    render(<SessionSelector kbId="test-kb" onSessionSelect={mockOnSessionSelect} />);

    // Should not have a count badge
    expect(screen.queryByText('(0)')).not.toBeInTheDocument();
  });

  it('calls useChatSessions with correct kbId', async () => {
    const { useChatSessions } = await import('@/hooks/useChatSessions');

    render(<SessionSelector kbId="my-test-kb-123" onSessionSelect={mockOnSessionSelect} />);

    expect(useChatSessions).toHaveBeenCalledWith({ kbId: 'my-test-kb-123' });
  });
});
