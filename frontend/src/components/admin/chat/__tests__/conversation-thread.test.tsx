/**
 * Conversation Thread Component Tests
 *
 * Story 9-9: Chat History Viewer UI
 * AC10: Unit tests for component rendering and user interactions
 * AC3: Message bubbles with user/assistant distinction
 * AC4: Assistant responses display sources
 *
 * Story 9-15: KB Debug Mode & Prompt Integration
 * Tests for debug info display in chat history
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ConversationThread, ConversationThreadSkeleton } from '../conversation-thread';
import type { ChatMessageItem } from '@/hooks/useChatHistory';

const mockMessages: ChatMessageItem[] = [
  {
    id: 'msg-1',
    trace_id: 'trace-1',
    session_id: 'session-1',
    role: 'user',
    content: 'What is the return policy?',
    user_id: 'user-1',
    kb_id: 'kb-1',
    created_at: new Date().toISOString(),
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
    content:
      'Based on the documentation, the return policy allows returns within 30 days of purchase.',
    user_id: null,
    kb_id: 'kb-1',
    created_at: new Date().toISOString(),
    citations: [
      {
        index: 1,
        document_id: 'doc-1',
        document_name: 'Return Policy Guide',
        chunk_id: 'chunk-1',
        relevance_score: 0.95,
      },
    ],
    token_count: 150,
    response_time_ms: 1200,
    debug_info: null,
  },
  {
    id: 'msg-3',
    trace_id: 'trace-3',
    session_id: 'session-1',
    role: 'user',
    content: 'Are there any exceptions?',
    user_id: 'user-1',
    kb_id: 'kb-1',
    created_at: new Date().toISOString(),
    citations: null,
    token_count: null,
    response_time_ms: null,
    debug_info: null,
  },
  {
    id: 'msg-4',
    trace_id: 'trace-4',
    session_id: 'session-1',
    role: 'assistant',
    content: 'Yes, there are exceptions for sale items and personalized products.',
    user_id: null,
    kb_id: 'kb-1',
    created_at: new Date().toISOString(),
    citations: [
      {
        index: 1,
        document_id: 'doc-1',
        document_name: 'Return Policy Guide',
        chunk_id: 'chunk-5',
        relevance_score: 0.89,
      },
      {
        index: 2,
        document_id: 'doc-2',
        document_name: 'Sale Terms',
        chunk_id: 'chunk-1',
        relevance_score: 0.85,
      },
    ],
    token_count: 200,
    response_time_ms: 1500,
    debug_info: null,
  },
];

describe('ConversationThread', () => {
  it('renders user and assistant messages with distinct styling (AC3)', () => {
    render(<ConversationThread messages={mockMessages} />);

    // Check user messages are displayed
    expect(screen.getByText('What is the return policy?')).toBeInTheDocument();
    expect(screen.getByText('Are there any exceptions?')).toBeInTheDocument();

    // Check assistant messages are displayed
    expect(
      screen.getByText(/Based on the documentation, the return policy allows returns/)
    ).toBeInTheDocument();
    expect(screen.getByText(/Yes, there are exceptions for sale items/)).toBeInTheDocument();
  });

  it('displays citations for assistant messages (AC4)', () => {
    render(<ConversationThread messages={mockMessages} />);

    // Check citations are displayed (using getAllByText since same doc may appear in multiple messages)
    const returnPolicyCitations = screen.getAllByText('Return Policy Guide');
    expect(returnPolicyCitations.length).toBeGreaterThan(0);
    expect(screen.getByText('Sale Terms')).toBeInTheDocument();
  });

  it('shows token count for assistant messages', () => {
    render(<ConversationThread messages={mockMessages} />);

    // Check token counts are displayed
    expect(screen.getByText(/150 tokens/)).toBeInTheDocument();
    expect(screen.getByText(/200 tokens/)).toBeInTheDocument();
  });

  it('shows response time for assistant messages', () => {
    render(<ConversationThread messages={mockMessages} />);

    // Check response times are displayed
    expect(screen.getByText(/1.2s/)).toBeInTheDocument();
    expect(screen.getByText(/1.5s/)).toBeInTheDocument();
  });

  it('displays empty state when no messages', () => {
    render(<ConversationThread messages={[]} />);

    expect(screen.getByText('No messages in this conversation')).toBeInTheDocument();
  });

  it('renders message bubbles for each message', () => {
    render(<ConversationThread messages={mockMessages} />);

    // Check all 4 messages are rendered
    expect(screen.getByTestId('message-msg-1')).toBeInTheDocument();
    expect(screen.getByTestId('message-msg-2')).toBeInTheDocument();
    expect(screen.getByTestId('message-msg-3')).toBeInTheDocument();
    expect(screen.getByTestId('message-msg-4')).toBeInTheDocument();
  });
});

describe('ConversationThreadSkeleton', () => {
  it('renders loading skeleton', () => {
    const { container } = render(<ConversationThreadSkeleton />);

    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });
});

/**
 * Story 9-15: KB Debug Mode & Prompt Integration
 * Tests for debug info display in chat history viewer
 */
describe('ConversationThread - Debug Info Display (Story 9-15)', () => {
  const mockMessageWithDebugInfo: ChatMessageItem = {
    id: 'msg-debug-1',
    trace_id: 'trace-debug-1',
    session_id: 'session-debug',
    role: 'assistant',
    content: 'Response with debug info available.',
    user_id: null,
    kb_id: 'kb-1',
    created_at: new Date().toISOString(),
    citations: [
      {
        index: 1,
        document_id: 'doc-1',
        document_name: 'Test Document',
        chunk_id: 'chunk-1',
        relevance_score: 0.92,
      },
    ],
    token_count: 100,
    response_time_ms: 800,
    debug_info: {
      kb_params: {
        system_prompt_preview: 'You are a helpful assistant...',
        citation_style: 'inline',
        response_language: 'en',
        uncertainty_handling: 'acknowledge',
      },
      chunks_retrieved: [
        {
          document_id: 'doc-1',
          chunk_index: 0,
          relevance_score: 0.92,
          document_name: 'Test Document',
        },
        {
          document_id: 'doc-1',
          chunk_index: 1,
          relevance_score: 0.85,
          document_name: 'Test Document',
        },
      ],
      timing: {
        retrieval_ms: 150,
        context_assembly_ms: 50,
      },
    },
  };

  const mockMessageWithoutDebugInfo: ChatMessageItem = {
    id: 'msg-no-debug',
    trace_id: 'trace-no-debug',
    session_id: 'session-debug',
    role: 'assistant',
    content: 'Response without debug info.',
    user_id: null,
    kb_id: 'kb-1',
    created_at: new Date().toISOString(),
    citations: null,
    token_count: 50,
    response_time_ms: 400,
    debug_info: null,
  };

  it('renders debug info section when debug_info is present', () => {
    render(<ConversationThread messages={[mockMessageWithDebugInfo]} />);

    // Debug info section should be present
    expect(screen.getByTestId('chat-history-debug-info')).toBeInTheDocument();
    expect(screen.getByText('Debug Info')).toBeInTheDocument();
  });

  it('does not render debug info section when debug_info is null', () => {
    render(<ConversationThread messages={[mockMessageWithoutDebugInfo]} />);

    // Debug info section should not be present
    expect(screen.queryByTestId('chat-history-debug-info')).not.toBeInTheDocument();
    expect(screen.queryByText('Debug Info')).not.toBeInTheDocument();
  });

  it('shows chunk count badge in collapsed state', () => {
    render(<ConversationThread messages={[mockMessageWithDebugInfo]} />);

    // Chunk count should be visible in collapsed state
    expect(screen.getByText('2 chunks')).toBeInTheDocument();
  });

  it('shows total timing badge in collapsed state', () => {
    render(<ConversationThread messages={[mockMessageWithDebugInfo]} />);

    // Total timing (150ms + 50ms = 200ms) should be visible
    expect(screen.getByText('200ms')).toBeInTheDocument();
  });

  it('expands to show KB parameters when clicked', () => {
    render(<ConversationThread messages={[mockMessageWithDebugInfo]} />);

    // Click to expand
    const trigger = screen.getByText('Debug Info');
    fireEvent.click(trigger);

    // KB parameters should be visible
    expect(screen.getByTestId('debug-kb-params')).toBeInTheDocument();
    expect(screen.getByText(/Citation:/)).toBeInTheDocument();
    expect(screen.getByText(/inline/i)).toBeInTheDocument();
    expect(screen.getByText(/Language:/)).toBeInTheDocument();
    // Language value is displayed (uppercase via CSS)
    const kbParamsSection = screen.getByTestId('debug-kb-params');
    expect(kbParamsSection).toHaveTextContent(/Language:.*en/i);
  });

  it('expands to show timing breakdown when clicked', () => {
    render(<ConversationThread messages={[mockMessageWithDebugInfo]} />);

    // Click to expand
    const trigger = screen.getByText('Debug Info');
    fireEvent.click(trigger);

    // Timing section should be visible
    expect(screen.getByTestId('debug-timing')).toBeInTheDocument();
    expect(screen.getByText(/Retrieval:/)).toBeInTheDocument();
    expect(screen.getByText('150ms')).toBeInTheDocument();
    expect(screen.getByText(/Context:/)).toBeInTheDocument();
    expect(screen.getByText('50ms')).toBeInTheDocument();
  });

  it('expands to show retrieved chunks when clicked', () => {
    render(<ConversationThread messages={[mockMessageWithDebugInfo]} />);

    // Click to expand
    const trigger = screen.getByText('Debug Info');
    fireEvent.click(trigger);

    // Chunks section should be visible
    expect(screen.getByTestId('debug-chunks')).toBeInTheDocument();
    expect(screen.getByText('Retrieved Chunks (2)')).toBeInTheDocument();
    // Chunk indices
    expect(screen.getByText('#0')).toBeInTheDocument();
    expect(screen.getByText('#1')).toBeInTheDocument();
    // Relevance scores as percentages
    expect(screen.getByText('92.0%')).toBeInTheDocument();
    expect(screen.getByText('85.0%')).toBeInTheDocument();
  });

  it('does not show debug info for user messages', () => {
    const userMessageWithDebug: ChatMessageItem = {
      id: 'msg-user-debug',
      trace_id: 'trace-user',
      session_id: 'session-debug',
      role: 'user',
      content: 'User question',
      user_id: 'user-1',
      kb_id: 'kb-1',
      created_at: new Date().toISOString(),
      citations: null,
      token_count: null,
      response_time_ms: null,
      // Even if debug_info somehow exists on user message, it shouldn't render
      debug_info: {
        kb_params: {
          system_prompt_preview: 'test',
          citation_style: 'inline',
          response_language: 'en',
          uncertainty_handling: 'acknowledge',
        },
        chunks_retrieved: [],
        timing: {
          retrieval_ms: 0,
          context_assembly_ms: 0,
        },
      },
    };

    render(<ConversationThread messages={[userMessageWithDebug]} />);

    // Debug info should not be shown for user messages
    expect(screen.queryByTestId('chat-history-debug-info')).not.toBeInTheDocument();
  });
});
