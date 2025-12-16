/**
 * Export Dialog Component Tests
 *
 * Story 9-9: Chat History Viewer UI
 * AC10: Unit tests for component rendering and user interactions
 * AC8: Export conversation as JSON/CSV
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { ExportDialog } from '../export-dialog';
import type { ChatMessageItem } from '@/hooks/useChatHistory';

const mockMessages: ChatMessageItem[] = [
  {
    id: 'msg-1',
    trace_id: 'trace-1',
    session_id: 'session-1',
    role: 'user',
    content: 'Test question',
    user_id: 'user-1',
    kb_id: 'kb-1',
    created_at: '2024-01-15T10:00:00.000Z',
    citations: null,
    token_count: null,
    response_time_ms: null,
    debug_info: null,
  },
  {
    id: 'msg-2',
    trace_id: 'trace-2',
    session_id: 'session-1',
    role: 'assistant',
    content: 'Test answer with "quotes" and, commas',
    user_id: null,
    kb_id: 'kb-1',
    created_at: '2024-01-15T10:00:01.000Z',
    citations: [
      {
        index: 1,
        document_id: 'doc-1',
        document_name: 'Test Doc',
        chunk_id: 'chunk-1',
        relevance_score: 0.9,
      },
    ],
    token_count: 50,
    response_time_ms: 500,
    debug_info: null,
  },
];

describe('ExportDialog', () => {
  beforeEach(() => {
    // Mock URL.createObjectURL and revokeObjectURL
    URL.createObjectURL = vi.fn(() => 'blob:test-url');
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders export trigger button', () => {
    render(<ExportDialog messages={mockMessages} sessionId="session-123" />);

    // The trigger button should be visible
    expect(screen.getByTestId('export-button')).toBeInTheDocument();
    expect(screen.getByText('Export')).toBeInTheDocument();
  });

  it('opens dialog when trigger is clicked', async () => {
    render(<ExportDialog messages={mockMessages} sessionId="session-123" />);

    // Click the trigger button
    const triggerButton = screen.getByTestId('export-button');
    fireEvent.click(triggerButton);

    // Dialog should open
    await waitFor(() => {
      expect(screen.getByText('Export Conversation')).toBeInTheDocument();
    });

    // Format options should be visible
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText('CSV')).toBeInTheDocument();
  });

  it('exports as JSON when JSON option is selected and export clicked (AC8)', async () => {
    render(<ExportDialog messages={mockMessages} sessionId="session-123" />);

    // Open dialog
    const triggerButton = screen.getByTestId('export-button');
    fireEvent.click(triggerButton);

    await waitFor(() => {
      expect(screen.getByText('Export Conversation')).toBeInTheDocument();
    });

    // JSON should be default, click export button
    const exportButton = screen.getByTestId('confirm-export');
    fireEvent.click(exportButton);

    // Check that createObjectURL was called (download was triggered)
    expect(URL.createObjectURL).toHaveBeenCalled();
  });

  it('exports as CSV when CSV option is selected (AC8)', async () => {
    render(<ExportDialog messages={mockMessages} sessionId="session-123" />);

    // Open dialog
    const triggerButton = screen.getByTestId('export-button');
    fireEvent.click(triggerButton);

    await waitFor(() => {
      expect(screen.getByText('Export Conversation')).toBeInTheDocument();
    });

    // Select CSV format using radio button
    const csvRadio = screen.getByRole('radio', { name: /csv/i });
    fireEvent.click(csvRadio);

    // Click export button
    const exportButton = screen.getByTestId('confirm-export');
    fireEvent.click(exportButton);

    // Check that createObjectURL was called (download was triggered)
    expect(URL.createObjectURL).toHaveBeenCalled();
  });

  it('closes dialog when cancel is clicked', async () => {
    render(<ExportDialog messages={mockMessages} sessionId="session-123" />);

    // Open dialog
    const triggerButton = screen.getByTestId('export-button');
    fireEvent.click(triggerButton);

    await waitFor(() => {
      expect(screen.getByText('Export Conversation')).toBeInTheDocument();
    });

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    // Dialog should close
    await waitFor(() => {
      expect(screen.queryByText('Export Conversation')).not.toBeInTheDocument();
    });
  });

  it('shows message count in dialog description', async () => {
    render(<ExportDialog messages={mockMessages} sessionId="session-123" />);

    // Open dialog
    const triggerButton = screen.getByTestId('export-button');
    fireEvent.click(triggerButton);

    await waitFor(() => {
      expect(screen.getByText(/Export 2 messages/)).toBeInTheDocument();
    });
  });

  it('renders with custom trigger element', () => {
    render(
      <ExportDialog
        messages={mockMessages}
        sessionId="session-123"
        trigger={<button data-testid="custom-trigger">Custom Export</button>}
      />
    );

    expect(screen.getByTestId('custom-trigger')).toBeInTheDocument();
    expect(screen.getByText('Custom Export')).toBeInTheDocument();
  });
});
