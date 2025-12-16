/**
 * ATDD Component Tests: Epic 4 - Chat Message Component (Story 4.2)
 * Status: RED phase - Tests written before implementation
 * Generated: 2025-11-26
 *
 * Test Coverage:
 * - P1: Chat message rendering (user/AI alignment)
 * - P1: Citation badges display inline
 * - P1: Timestamps show relative time
 * - P2: Confidence indicator styling
 *
 * Knowledge Base References:
 * - component-tdd.md: Component test patterns with RTL
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChatMessage } from '../chat-message';

describe('ChatMessage Component', () => {
  it('P1: renders user message with right alignment', () => {
    /**
     * GIVEN: User message data
     * WHEN: Component is rendered
     * THEN: Message appears right-aligned with user styling
     */
    render(
      <ChatMessage
        role="user"
        content="What is OAuth 2.0?"
        timestamp={new Date()}
        citations={[]}
      />
    );

    const message = screen.getByTestId('chat-message');
    expect(message).toBeInTheDocument();
    expect(message).toHaveAttribute('data-role', 'user');

    // User messages should be right-aligned
    expect(message).toHaveClass(/right|justify-end|ml-auto/);
  });

  it('P1: renders AI message with left alignment and citations', () => {
    /**
     * GIVEN: AI message with citations
     * WHEN: Component is rendered
     * THEN: Message left-aligned with citation badges inline
     */
    const citations = [
      { number: 1, documentName: 'OAuth Spec', excerpt: 'OAuth 2.0 is...' },
      { number: 2, documentName: 'Security Guide', excerpt: 'Security considerations...' },
    ];

    render(
      <ChatMessage
        role="assistant"
        content="OAuth 2.0 is an authorization framework [1] with security implications [2]."
        timestamp={new Date()}
        citations={citations}
      />
    );

    const message = screen.getByTestId('chat-message');
    expect(message).toHaveAttribute('data-role', 'assistant');

    // AI messages should be left-aligned
    expect(message).toHaveClass(/left|justify-start|mr-auto/);

    // Citation badges should be rendered
    const citationBadges = screen.getAllByTestId('citation-badge');
    expect(citationBadges).toHaveLength(2);

    // Verify citation numbers
    expect(citationBadges[0]).toHaveTextContent('[1]');
    expect(citationBadges[1]).toHaveTextContent('[2]');
  });

  it('P1: displays relative timestamp', () => {
    /**
     * GIVEN: Message with timestamp 2 minutes ago
     * WHEN: Component renders
     * THEN: Timestamp shows "2m ago"
     */
    const twoMinutesAgo = new Date(Date.now() - 2 * 60 * 1000);

    render(
      <ChatMessage
        role="user"
        content="Test message"
        timestamp={twoMinutesAgo}
        citations={[]}
      />
    );

    const timestamp = screen.getByTestId('message-timestamp');
    expect(timestamp).toHaveTextContent(/2m ago|2 minutes ago/);
  });

  it('P1: shows "just now" for recent messages', () => {
    /**
     * GIVEN: Message sent <30 seconds ago
     * WHEN: Component renders
     * THEN: Timestamp shows "just now"
     */
    const justNow = new Date(Date.now() - 5000); // 5 seconds ago

    render(
      <ChatMessage
        role="assistant"
        content="Response"
        timestamp={justNow}
        citations={[]}
      />
    );

    const timestamp = screen.getByTestId('message-timestamp');
    expect(timestamp).toHaveTextContent(/just now/i);
  });

  it('P2: displays confidence indicator for AI messages', () => {
    /**
     * GIVEN: AI message with medium confidence
     * WHEN: Component renders
     * THEN: Amber confidence bar shown
     */
    render(
      <ChatMessage
        role="assistant"
        content="This is a response with medium confidence"
        timestamp={new Date()}
        citations={[]}
        confidence={0.65} // 65% = medium
      />
    );

    const confidenceIndicator = screen.getByTestId('confidence-indicator');
    expect(confidenceIndicator).toBeInTheDocument();

    // Should have amber/yellow styling for medium confidence
    expect(confidenceIndicator).toHaveClass(/amber|yellow/);
  });

  it('P2: high confidence shows green indicator', () => {
    /**
     * GIVEN: AI message with high confidence (>80%)
     * WHEN: Component renders
     * THEN: Green confidence bar shown
     */
    render(
      <ChatMessage
        role="assistant"
        content="High confidence response"
        timestamp={new Date()}
        citations={[]}
        confidence={0.92} // 92% = high
      />
    );

    const confidenceIndicator = screen.getByTestId('confidence-indicator');
    expect(confidenceIndicator).toHaveClass(/green/);
  });

  it('P2: low confidence shows red indicator with warning', () => {
    /**
     * GIVEN: AI message with low confidence (<50%)
     * WHEN: Component renders
     * THEN: Red indicator with "Verify carefully" warning
     */
    render(
      <ChatMessage
        role="assistant"
        content="Low confidence response"
        timestamp={new Date()}
        citations={[]}
        confidence={0.42} // 42% = low
      />
    );

    const confidenceIndicator = screen.getByTestId('confidence-indicator');
    expect(confidenceIndicator).toHaveClass(/red/);

    // Warning text should be present
    expect(screen.getByText(/verify carefully/i)).toBeInTheDocument();
  });

  it('P2: user messages do not show confidence indicator', () => {
    /**
     * GIVEN: User message
     * WHEN: Component renders
     * THEN: No confidence indicator shown (only for AI)
     */
    render(
      <ChatMessage
        role="user"
        content="User question"
        timestamp={new Date()}
        citations={[]}
      />
    );

    const confidenceIndicator = screen.queryByTestId('confidence-indicator');
    expect(confidenceIndicator).not.toBeInTheDocument();
  });

  it('P3: citation badge click triggers preview', () => {
    /**
     * GIVEN: Message with citations
     * WHEN: User clicks citation badge
     * THEN: onCitationClick callback fired with citation data
     */
    const onCitationClick = vi.fn();
    const citations = [
      { number: 1, documentName: 'Test Doc', excerpt: 'Excerpt...' },
    ];

    render(
      <ChatMessage
        role="assistant"
        content="Content with citation [1]"
        timestamp={new Date()}
        citations={citations}
        onCitationClick={onCitationClick}
      />
    );

    const citationBadge = screen.getByTestId('citation-badge');
    citationBadge.click();

    expect(onCitationClick).toHaveBeenCalledWith(citations[0]);
  });
});
