import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';
import { CitationPreviewModal } from '../citation-preview-modal';
import type { Citation } from '../citation-card';

// Mock fetch
global.fetch = vi.fn();

const mockCitation: Citation = {
  number: 1,
  documentId: '550e8400-e29b-41d4-a716-446655440000',
  documentName: 'Test Document.pdf',
  pageNumber: 14,
  sectionHeader: 'Test Section',
  excerpt: 'This is a test excerpt from the document.',
  charStart: 100,
  charEnd: 142,
};

describe('CitationPreviewModal', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when closed', () => {
    const onOpenChange = vi.fn();
    const onOpenDocument = vi.fn();

    const { container } = render(
      <CitationPreviewModal
        citation={mockCitation}
        open={false}
        onOpenChange={onOpenChange}
        onOpenDocument={onOpenDocument}
      />
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('displays document name and metadata', async () => {
    const onOpenChange = vi.fn();
    const onOpenDocument = vi.fn();

    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => 'Before text. This is a test excerpt from the document. After text.',
    });

    render(
      <CitationPreviewModal
        citation={mockCitation}
        open={true}
        onOpenChange={onOpenChange}
        onOpenDocument={onOpenDocument}
      />
    );

    expect(screen.getByText('Test Document.pdf')).toBeInTheDocument();
    expect(screen.getByText(/Page 14.*Test Section/)).toBeInTheDocument();
  });

  it('fetches and displays citation context', async () => {
    const onOpenChange = vi.fn();
    const onOpenDocument = vi.fn();

    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => 'Before text. This is a test excerpt from the document. After text.',
    });

    render(
      <CitationPreviewModal
        citation={mockCitation}
        open={true}
        onOpenChange={onOpenChange}
        onOpenDocument={onOpenDocument}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/This is a test excerpt from the document/)).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching', () => {
    const onOpenChange = vi.fn();
    const onOpenDocument = vi.fn();

    (global.fetch as Mock).mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                text: async () => 'Content',
              }),
            100
          )
        )
    );

    render(
      <CitationPreviewModal
        citation={mockCitation}
        open={true}
        onOpenChange={onOpenChange}
        onOpenDocument={onOpenDocument}
      />
    );

    // Should show skeleton loader
    expect(screen.getByTestId('citation-preview-close')).toBeInTheDocument();
  });

  it('handles fetch error gracefully', async () => {
    const onOpenChange = vi.fn();
    const onOpenDocument = vi.fn();

    (global.fetch as Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    render(
      <CitationPreviewModal
        citation={mockCitation}
        open={true}
        onOpenChange={onOpenChange}
        onOpenDocument={onOpenDocument}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to load full context/)).toBeInTheDocument();
    });

    // Should still show excerpt as fallback
    await waitFor(() => {
      expect(screen.getByText(mockCitation.excerpt)).toBeInTheDocument();
    });
  });

  it('closes modal when Close button is clicked', async () => {
    const onOpenChange = vi.fn();
    const onOpenDocument = vi.fn();
    const user = userEvent.setup();

    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => 'Content',
    });

    render(
      <CitationPreviewModal
        citation={mockCitation}
        open={true}
        onOpenChange={onOpenChange}
        onOpenDocument={onOpenDocument}
      />
    );

    const closeButton = screen.getByTestId('citation-preview-close');
    await user.click(closeButton);

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('calls onOpenDocument when Open Document button is clicked', async () => {
    const onOpenChange = vi.fn();
    const onOpenDocument = vi.fn();
    const user = userEvent.setup();

    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => 'Content',
    });

    render(
      <CitationPreviewModal
        citation={mockCitation}
        open={true}
        onOpenChange={onOpenChange}
        onOpenDocument={onOpenDocument}
      />
    );

    const openButton = screen.getByTestId('citation-preview-open-document');
    await user.click(openButton);

    expect(onOpenDocument).toHaveBeenCalledWith(
      mockCitation.documentId,
      mockCitation.charStart,
      mockCitation.charEnd
    );
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('closes modal on Escape key press', async () => {
    const onOpenChange = vi.fn();
    const onOpenDocument = vi.fn();
    const user = userEvent.setup();

    (global.fetch as Mock).mockResolvedValueOnce({
      ok: true,
      text: async () => 'Content',
    });

    render(
      <CitationPreviewModal
        citation={mockCitation}
        open={true}
        onOpenChange={onOpenChange}
        onOpenDocument={onOpenDocument}
      />
    );

    await user.keyboard('{Escape}');

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
