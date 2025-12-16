import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchResultCard, SearchResult } from '../search-result-card';

const mockResult: SearchResult = {
  documentId: 'doc-123',
  documentName: 'Test Document.pdf',
  kbId: 'kb-1',
  kbName: 'Sales KB',
  chunkText: 'This is a test chunk of text from the document.',
  relevanceScore: 0.92,
  pageNumber: 5,
  sectionHeader: 'Introduction',
  updatedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
  citationNumbers: [1, 2],
  charStart: 0,
  charEnd: 100,
};

describe('SearchResultCard', () => {
  it('renders document name with file icon', () => {
    render(
      <SearchResultCard
        result={mockResult}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    expect(screen.getByText('📄')).toBeInTheDocument();
    expect(screen.getByText('Test Document.pdf')).toBeInTheDocument();
  });

  it('renders KB name badge', () => {
    render(
      <SearchResultCard
        result={mockResult}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    expect(screen.getByText('Sales KB')).toBeInTheDocument();
  });

  it('renders relevance score as percentage', () => {
    render(
      <SearchResultCard
        result={mockResult}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    expect(screen.getByText('92% match')).toBeInTheDocument();
  });

  it('applies green color for high relevance (≥80%)', () => {
    const { container } = render(
      <SearchResultCard
        result={{ ...mockResult, relevanceScore: 0.85 }}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    const relevanceText = screen.getByText('85% match');
    expect(relevanceText).toHaveClass('text-[#10B981]');
  });

  it('applies amber color for medium relevance (60-79%)', () => {
    const { container } = render(
      <SearchResultCard
        result={{ ...mockResult, relevanceScore: 0.7 }}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    const relevanceText = screen.getByText('70% match');
    expect(relevanceText).toHaveClass('text-[#F59E0B]');
  });

  it('applies gray color for low relevance (<60%)', () => {
    const { container } = render(
      <SearchResultCard
        result={{ ...mockResult, relevanceScore: 0.5 }}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    const relevanceText = screen.getByText('50% match');
    expect(relevanceText).toHaveClass('text-gray-600');
  });

  it('renders relative timestamp', () => {
    render(
      <SearchResultCard
        result={mockResult}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    // formatDistanceToNow should produce "7 days ago" or similar
    expect(screen.getByText(/days ago/)).toBeInTheDocument();
  });

  it('renders chunk text', () => {
    render(
      <SearchResultCard
        result={mockResult}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    expect(screen.getByText('This is a test chunk of text from the document.')).toBeInTheDocument();
  });

  it('renders citation markers when present', () => {
    render(
      <SearchResultCard
        result={mockResult}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    expect(screen.getByText('[1]')).toBeInTheDocument();
    expect(screen.getByText('[2]')).toBeInTheDocument();
  });

  it('does not render citation markers when not present', () => {
    const resultWithoutCitations = { ...mockResult, citationNumbers: undefined };
    render(
      <SearchResultCard
        result={resultWithoutCitations}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    expect(screen.queryByText('[1]')).not.toBeInTheDocument();
  });

  it('calls onUseInDraft when Use in Draft button is clicked', () => {
    const onUseInDraft = vi.fn();
    render(
      <SearchResultCard
        result={mockResult}
        query="test query"
        onUseInDraft={onUseInDraft}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    fireEvent.click(screen.getByText('Use in Draft'));
    expect(onUseInDraft).toHaveBeenCalledWith(mockResult);
  });

  it('calls onView when View button is clicked', () => {
    const onView = vi.fn();
    render(
      <SearchResultCard
        result={mockResult}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={onView}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    fireEvent.click(screen.getByText('View'));
    expect(onView).toHaveBeenCalledWith('doc-123');
  });

  it('calls onFindSimilar when Similar button is clicked', () => {
    const onFindSimilar = vi.fn();
    render(
      <SearchResultCard
        result={mockResult}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={onFindSimilar}
        index={0}
      />
    );
    fireEvent.click(screen.getByText('Similar'));
    expect(onFindSimilar).toHaveBeenCalledWith(mockResult);
  });

  it('has correct data-testid', () => {
    render(
      <SearchResultCard
        result={mockResult}
        query="test query"
        onUseInDraft={vi.fn()}
        onView={vi.fn()}
        onFindSimilar={vi.fn()}
        index={0}
      />
    );
    expect(screen.getByTestId('search-result-card-0')).toBeInTheDocument();
  });
});
