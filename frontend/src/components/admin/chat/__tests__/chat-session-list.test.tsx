/**
 * Chat Session List Component Tests
 *
 * Story 9-9: Chat History Viewer UI
 * AC10: Unit tests for component rendering and user interactions
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ChatSessionList, ChatSessionListSkeleton } from '../chat-session-list';
import type { ChatSession } from '@/hooks/useChatHistory';

const mockSessions: ChatSession[] = [
  {
    session_id: 'session-1',
    user_id: 'user-1',
    user_name: 'alice@example.com',
    kb_id: 'kb-1',
    kb_name: 'Technical Docs',
    message_count: 15,
    last_message_at: new Date().toISOString(),
    first_message_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    session_id: 'session-2',
    user_id: 'user-2',
    user_name: 'bob@example.com',
    kb_id: 'kb-2',
    kb_name: 'HR Policies',
    message_count: 8,
    last_message_at: new Date(Date.now() - 7200000).toISOString(),
    first_message_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    session_id: 'session-3',
    user_id: null,
    user_name: null,
    kb_id: 'kb-3',
    kb_name: 'Public FAQ',
    message_count: 3,
    last_message_at: new Date(Date.now() - 1800000).toISOString(),
    first_message_at: new Date(Date.now() - 1800000).toISOString(),
  },
];

describe('ChatSessionList', () => {
  it('renders session list with all columns (AC1)', () => {
    const onSelectSession = vi.fn();

    render(
      <ChatSessionList
        sessions={mockSessions}
        selectedSessionId={null}
        onSelectSession={onSelectSession}
        isLoading={false}
      />
    );

    // Check table headers
    expect(screen.getByText('User')).toBeInTheDocument();
    expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
    expect(screen.getByText('Messages')).toBeInTheDocument();
    expect(screen.getByText('Last Active')).toBeInTheDocument();

    // Check session data displayed
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    expect(screen.getByText('bob@example.com')).toBeInTheDocument();
    expect(screen.getByText('Technical Docs')).toBeInTheDocument();
    expect(screen.getByText('HR Policies')).toBeInTheDocument();
    expect(screen.getByText('Public FAQ')).toBeInTheDocument();

    // Check message counts
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('handles anonymous user sessions', () => {
    const onSelectSession = vi.fn();

    render(
      <ChatSessionList
        sessions={mockSessions}
        selectedSessionId={null}
        onSelectSession={onSelectSession}
        isLoading={false}
      />
    );

    // Session with null user should show "Unknown"
    expect(screen.getByText('Unknown')).toBeInTheDocument();
  });

  it('calls onSelectSession when row is clicked', () => {
    const onSelectSession = vi.fn();

    render(
      <ChatSessionList
        sessions={mockSessions}
        selectedSessionId={null}
        onSelectSession={onSelectSession}
        isLoading={false}
      />
    );

    const row = screen.getByTestId('session-row-session-1');
    fireEvent.click(row);

    expect(onSelectSession).toHaveBeenCalledWith('session-1');
  });

  it('highlights selected session row', () => {
    const onSelectSession = vi.fn();

    render(
      <ChatSessionList
        sessions={mockSessions}
        selectedSessionId="session-2"
        onSelectSession={onSelectSession}
        isLoading={false}
      />
    );

    const selectedRow = screen.getByTestId('session-row-session-2');
    expect(selectedRow).toHaveClass('bg-muted');

    const unselectedRow = screen.getByTestId('session-row-session-1');
    expect(unselectedRow).not.toHaveClass('bg-muted');
  });

  it('displays empty state when no sessions', () => {
    const onSelectSession = vi.fn();

    render(
      <ChatSessionList
        sessions={[]}
        selectedSessionId={null}
        onSelectSession={onSelectSession}
        isLoading={false}
      />
    );

    expect(screen.getByText('No chat sessions found')).toBeInTheDocument();
  });

  it('shows loading skeleton when isLoading is true', () => {
    const onSelectSession = vi.fn();

    const { container } = render(
      <ChatSessionList
        sessions={[]}
        selectedSessionId={null}
        onSelectSession={onSelectSession}
        isLoading={true}
      />
    );

    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });
});

describe('ChatSessionListSkeleton', () => {
  it('renders loading skeleton', () => {
    const { container } = render(<ChatSessionListSkeleton />);

    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
