import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CitationCard, Citation } from '../citation-card';

const mockCitation: Citation = {
  number: 1,
  documentId: 'doc-123',
  documentName: 'Test Document.pdf',
  pageNumber: 5,
  sectionHeader: 'Introduction',
  excerpt: 'This is a test excerpt from the document.',
  charStart: 100,
  charEnd: 200,
};

describe('CitationCard', () => {
  it('renders citation number badge', () => {
    render(<CitationCard citation={mockCitation} onPreview={vi.fn()} onOpenDocument={vi.fn()} />);
    expect(screen.getByText('[1]')).toBeInTheDocument();
  });

  it('renders document name', () => {
    render(<CitationCard citation={mockCitation} onPreview={vi.fn()} onOpenDocument={vi.fn()} />);
    expect(screen.getByText('Test Document.pdf')).toBeInTheDocument();
  });

  it('truncates document name when longer than 40 chars', () => {
    const longName = 'A'.repeat(50);
    const longCitation = { ...mockCitation, documentName: longName };
    render(<CitationCard citation={longCitation} onPreview={vi.fn()} onOpenDocument={vi.fn()} />);
    expect(screen.getByText(/^A{37}\.\.\./)).toBeInTheDocument();
  });

  it('renders page number and section header', () => {
    render(<CitationCard citation={mockCitation} onPreview={vi.fn()} onOpenDocument={vi.fn()} />);
    expect(screen.getByText(/Page 5/)).toBeInTheDocument();
    expect(screen.getByText(/Introduction/)).toBeInTheDocument();
  });

  it('renders excerpt', () => {
    render(<CitationCard citation={mockCitation} onPreview={vi.fn()} onOpenDocument={vi.fn()} />);
    expect(screen.getByText('This is a test excerpt from the document.')).toBeInTheDocument();
  });

  it('truncates excerpt when longer than 200 chars', () => {
    const longExcerpt = 'A'.repeat(250);
    const longCitation = { ...mockCitation, excerpt: longExcerpt };
    render(<CitationCard citation={longCitation} onPreview={vi.fn()} onOpenDocument={vi.fn()} />);
    expect(screen.getByText(/^A{197}\.\.\./)).toBeInTheDocument();
  });

  it('calls onPreview when Preview button is clicked', () => {
    const onPreview = vi.fn();
    render(<CitationCard citation={mockCitation} onPreview={onPreview} onOpenDocument={vi.fn()} />);
    fireEvent.click(screen.getByText('Preview'));
    expect(onPreview).toHaveBeenCalledWith(mockCitation);
  });

  it('calls onOpenDocument when Open Document button is clicked', () => {
    const onOpenDocument = vi.fn();
    render(
      <CitationCard citation={mockCitation} onPreview={vi.fn()} onOpenDocument={onOpenDocument} />
    );
    fireEvent.click(screen.getByText('Open Document'));
    expect(onOpenDocument).toHaveBeenCalledWith('doc-123', 100, 200);
  });

  it('has correct data-testid', () => {
    render(<CitationCard citation={mockCitation} onPreview={vi.fn()} onOpenDocument={vi.fn()} />);
    expect(screen.getByTestId('citation-card-1')).toBeInTheDocument();
  });

  it('applies highlight styles when highlighted is true', () => {
    const { container } = render(
      <CitationCard
        citation={mockCitation}
        onPreview={vi.fn()}
        onOpenDocument={vi.fn()}
        highlighted={true}
      />
    );
    const card = container.querySelector('[data-testid="citation-card-1"]');
    expect(card).toHaveClass('ring-2');
    expect(card).toHaveClass('ring-[#0066CC]');
  });

  it('does not apply highlight styles when highlighted is false', () => {
    const { container } = render(
      <CitationCard
        citation={mockCitation}
        onPreview={vi.fn()}
        onOpenDocument={vi.fn()}
        highlighted={false}
      />
    );
    const card = container.querySelector('[data-testid="citation-card-1"]');
    expect(card).not.toHaveClass('ring-2');
  });
});
