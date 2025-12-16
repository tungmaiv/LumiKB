/**
 * Unit tests for StreamingDraftView component (Story 4.5, AC2)
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { StreamingDraftView } from '../streaming-draft-view';
import type { Citation } from '@/types/citation';

describe('StreamingDraftView', () => {
  const mockCitations: Citation[] = [
    {
      number: 1,
      document_id: 'doc-123',
      document_name: 'Security_Architecture.pdf',
      page_number: 14,
      section_header: 'Authentication',
      excerpt: 'OAuth 2.0 with PKCE flow ensures secure authentication...',
      char_start: 1234,
      char_end: 1456,
      confidence: 0.92,
    },
    {
      number: 2,
      document_id: 'doc-456',
      document_name: 'Design_Patterns.pdf',
      page_number: 7,
      section_header: 'Singleton Pattern',
      excerpt: 'The Singleton pattern ensures only one instance...',
      char_start: 500,
      char_end: 650,
      confidence: 0.88,
    },
  ];

  const defaultProps = {
    content: '',
    citations: [],
    status: null,
    confidence: null,
    isGenerating: false,
    error: null,
    onCancel: vi.fn(),
    onClose: vi.fn(),
  };

  it('should render with empty state', () => {
    render(<StreamingDraftView {...defaultProps} />);

    expect(screen.getByTestId('streaming-draft-view')).toBeInTheDocument();
    expect(screen.getByText('Draft Generation')).toBeInTheDocument();
    expect(screen.getByText(/Waiting for draft generation/i)).toBeInTheDocument();
    expect(screen.getByText('Citations (0)')).toBeInTheDocument();
  });

  it('should display status message when generating', () => {
    render(
      <StreamingDraftView
        {...defaultProps}
        status="Preparing sources..."
        isGenerating={true}
      />
    );

    expect(screen.getByText('Preparing sources...')).toBeInTheDocument();
  });

  it('should display accumulated draft content', () => {
    const content = 'Our solution implements OAuth 2.0 [1] for secure authentication.';
    render(<StreamingDraftView {...defaultProps} content={content} />);

    expect(screen.getByTestId('draft-content')).toHaveTextContent(content);
  });

  it('should render citations in the panel', () => {
    render(<StreamingDraftView {...defaultProps} citations={mockCitations} />);

    expect(screen.getByText('Citations (2)')).toBeInTheDocument();
    expect(screen.getByTestId('citation-1')).toBeInTheDocument();
    expect(screen.getByTestId('citation-2')).toBeInTheDocument();
    expect(screen.getByText('Security_Architecture.pdf')).toBeInTheDocument();
    expect(screen.getByText('Design_Patterns.pdf')).toBeInTheDocument();
  });

  it('should display citation details', () => {
    render(<StreamingDraftView {...defaultProps} citations={mockCitations} />);

    expect(screen.getByText('Page 14')).toBeInTheDocument();
    expect(screen.getByText('Authentication')).toBeInTheDocument();
    expect(
      screen.getByText(/OAuth 2.0 with PKCE flow ensures secure authentication/i)
    ).toBeInTheDocument();
  });

  it('should show cancel button when generating', () => {
    render(<StreamingDraftView {...defaultProps} isGenerating={true} />);

    const cancelButton = screen.getByTestId('cancel-button');
    expect(cancelButton).toBeInTheDocument();
  });

  it('should call onCancel when cancel button clicked', () => {
    const onCancel = vi.fn();
    render(<StreamingDraftView {...defaultProps} isGenerating={true} onCancel={onCancel} />);

    const cancelButton = screen.getByTestId('cancel-button');
    fireEvent.click(cancelButton);

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when close button clicked', () => {
    const onClose = vi.fn();
    render(<StreamingDraftView {...defaultProps} onClose={onClose} />);

    const closeButton = screen.getByTestId('close-button');
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should display error message', () => {
    render(<StreamingDraftView {...defaultProps} error="Insufficient sources provided" />);

    expect(screen.getByText(/Error: Insufficient sources/i)).toBeInTheDocument();
  });

  it('should display confidence badge when available', () => {
    render(<StreamingDraftView {...defaultProps} confidence={0.85} />);

    // 85% >= 80% threshold, so it's "High Confidence"
    expect(screen.getByText(/High Confidence \(85%\)/i)).toBeInTheDocument();
  });

  it('should show high confidence badge for score >= 0.8', () => {
    render(<StreamingDraftView {...defaultProps} confidence={0.92} />);

    expect(screen.getByText(/High Confidence \(92%\)/i)).toBeInTheDocument();
  });

  it('should show low confidence badge for score < 0.5', () => {
    render(<StreamingDraftView {...defaultProps} confidence={0.45} />);

    expect(screen.getByText(/Low Confidence \(45%\)/i)).toBeInTheDocument();
  });

  it('should display loading spinner when generating', () => {
    render(
      <StreamingDraftView
        {...defaultProps}
        isGenerating={true}
        status="Generating draft..."
      />
    );

    // Spinner should be present (via Loader2 icon)
    const statusText = screen.getByText('Generating draft...');
    expect(statusText).toBeInTheDocument();
  });

  it('should not show cancel button when not generating', () => {
    render(<StreamingDraftView {...defaultProps} isGenerating={false} />);

    expect(screen.queryByTestId('cancel-button')).not.toBeInTheDocument();
  });

  it('should show "No citations yet" when citations array is empty', () => {
    render(<StreamingDraftView {...defaultProps} citations={[]} />);

    expect(screen.getByText('No citations yet')).toBeInTheDocument();
  });

  it('should display citation numbers as badges', () => {
    render(<StreamingDraftView {...defaultProps} citations={mockCitations} />);

    expect(screen.getByText('[1]')).toBeInTheDocument();
    expect(screen.getByText('[2]')).toBeInTheDocument();
  });

  it('should handle citations without page numbers', () => {
    const citationWithoutPage: Citation = {
      ...mockCitations[0],
      page_number: null,
    };

    render(<StreamingDraftView {...defaultProps} citations={[citationWithoutPage]} />);

    expect(screen.queryByText(/Page/)).not.toBeInTheDocument();
  });

  it('should handle citations without section headers', () => {
    const citationWithoutSection: Citation = {
      ...mockCitations[0],
      section_header: null,
    };

    render(<StreamingDraftView {...defaultProps} citations={[citationWithoutSection]} />);

    // Should still render document name and excerpt
    expect(screen.getByText('Security_Architecture.pdf')).toBeInTheDocument();
    expect(
      screen.getByText(/OAuth 2.0 with PKCE flow ensures secure authentication/i)
    ).toBeInTheDocument();
  });
});
