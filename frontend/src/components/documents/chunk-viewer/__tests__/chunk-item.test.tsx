/**
 * Unit tests for ChunkItem component
 * Story 5-26: Document Chunk Viewer Frontend
 *
 * Tests chunk display, selection state, and click handling.
 * AC-5.26.3: Chunk sidebar displays all chunks
 * AC-5.26.6: Click chunk scrolls to position in document
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ChunkItem } from '../chunk-item';
import type { DocumentChunk } from '@/types/chunk';

// Mock chunk data
const mockChunk: DocumentChunk = {
  chunk_id: 'chunk-1',
  chunk_index: 0,
  text: 'This is the first chunk of text content for testing the ChunkItem component.',
  char_start: 0,
  char_end: 76,
  page_number: 1,
  section_header: 'Introduction',
  score: null,
};

const mockChunkWithScore: DocumentChunk = {
  ...mockChunk,
  chunk_id: 'chunk-2',
  chunk_index: 1,
  score: 0.95,
};

const mockChunkLongText: DocumentChunk = {
  ...mockChunk,
  chunk_id: 'chunk-3',
  chunk_index: 2,
  text: 'This is a very long chunk of text that should be truncated when displayed in the ChunkItem component because it exceeds 100 characters and we need to show an ellipsis at the end.',
};

const mockChunkNoMetadata: DocumentChunk = {
  chunk_id: 'chunk-4',
  chunk_index: 3,
  text: 'Chunk without page number or section header.',
  char_start: 200,
  char_end: 245,
  page_number: null,
  section_header: null,
  score: null,
};

describe('ChunkItem', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] should render chunk index and preview text - AC-5.26.3', () => {
    // Act
    render(<ChunkItem chunk={mockChunk} />);

    // Assert
    expect(screen.getByText('Chunk #1')).toBeInTheDocument();
    expect(screen.getByText(mockChunk.text)).toBeInTheDocument();
  });

  it('[P0] should display page number when available - AC-5.26.3', () => {
    // Act
    render(<ChunkItem chunk={mockChunk} />);

    // Assert
    expect(screen.getByText('Page 1')).toBeInTheDocument();
  });

  it('[P0] should display section header when available - AC-5.26.3', () => {
    // Act
    render(<ChunkItem chunk={mockChunk} />);

    // Assert
    expect(screen.getByText('Introduction')).toBeInTheDocument();
  });

  it('[P0] should display character range - AC-5.26.3', () => {
    // Act
    render(<ChunkItem chunk={mockChunk} />);

    // Assert
    expect(screen.getByText('0-76')).toBeInTheDocument();
  });

  it('[P0] should truncate long text with ellipsis - AC-5.26.3', () => {
    // Act
    render(<ChunkItem chunk={mockChunkLongText} />);

    // Assert
    const truncatedText = screen.getByText(/This is a very long chunk/);
    expect(truncatedText.textContent).toContain('...');
    expect(truncatedText.textContent?.length).toBeLessThanOrEqual(103); // 100 chars + '...'
  });

  it('[P0] should call onClick when clicked - AC-5.26.6', () => {
    // Arrange
    const mockOnClick = vi.fn();

    // Act
    render(<ChunkItem chunk={mockChunk} onClick={mockOnClick} />);
    // Click the text content button (second button, as first is the chunk index button)
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[1]); // Text content button

    // Assert
    expect(mockOnClick).toHaveBeenCalledTimes(1);
    expect(mockOnClick).toHaveBeenCalledWith(mockChunk);
  });

  it('[P0] should show selected state with proper styling - AC-5.26.3', () => {
    // Act
    render(<ChunkItem chunk={mockChunk} isSelected={true} />);

    // Assert - container div has the styling, buttons have aria-pressed
    const container = screen.getByTestId('chunk-item-0');
    expect(container).toHaveClass('bg-primary/10', 'border-primary');
    // Check that clickable buttons have aria-pressed
    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toHaveAttribute('aria-pressed', 'true'); // Chunk index button
    expect(buttons[1]).toHaveAttribute('aria-pressed', 'true'); // Text content button
  });

  it('[P0] should show unselected state with default styling - AC-5.26.3', () => {
    // Act
    render(<ChunkItem chunk={mockChunk} isSelected={false} />);

    // Assert - container div has the styling, buttons have aria-pressed
    const container = screen.getByTestId('chunk-item-0');
    expect(container).toHaveClass('bg-background', 'border-border');
    // Check that clickable buttons have aria-pressed
    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toHaveAttribute('aria-pressed', 'false'); // Chunk index button
    expect(buttons[1]).toHaveAttribute('aria-pressed', 'false'); // Text content button
  });

  it('[P1] should show score badge when chunk has search score - AC-5.26.5', () => {
    // Act
    render(<ChunkItem chunk={mockChunkWithScore} isSearchMatch={true} />);

    // Assert
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByTitle('Relevance score')).toBeInTheDocument();
  });

  it('[P1] should highlight search match with ring styling - AC-5.26.5', () => {
    // Act
    render(<ChunkItem chunk={mockChunkWithScore} isSearchMatch={true} />);

    // Assert - container div has the ring styling
    const container = screen.getByTestId('chunk-item-1');
    expect(container).toHaveClass('ring-1', 'ring-yellow-500/50');
  });

  it('[P1] should not show page number when null', () => {
    // Act
    render(<ChunkItem chunk={mockChunkNoMetadata} />);

    // Assert
    expect(screen.queryByText(/Page/)).not.toBeInTheDocument();
  });

  it('[P1] should not show section header when null', () => {
    // Act
    render(<ChunkItem chunk={mockChunkNoMetadata} />);

    // Assert
    expect(screen.queryByText('Introduction')).not.toBeInTheDocument();
  });

  it('[P2] should have accessible button roles', () => {
    // Act
    render(<ChunkItem chunk={mockChunk} />);

    // Assert - component has multiple accessible buttons
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(2); // Chunk index + text content buttons
    buttons.forEach((button) => {
      expect(button).toHaveAttribute('type', 'button');
    });
  });

  it('[P2] should have correct test-id for automation', () => {
    // Act
    render(<ChunkItem chunk={mockChunk} />);

    // Assert
    expect(screen.getByTestId('chunk-item-0')).toBeInTheDocument();
  });

  it('[P2] should handle click without onClick handler', () => {
    // Act & Assert - should not throw
    render(<ChunkItem chunk={mockChunk} />);
    const buttons = screen.getAllByRole('button');
    expect(() => fireEvent.click(buttons[1])).not.toThrow(); // Text content button
  });

  it('[P2] should format score as percentage', () => {
    // Arrange
    const chunkWithScore: DocumentChunk = {
      ...mockChunk,
      score: 0.8765,
    };

    // Act
    render(<ChunkItem chunk={chunkWithScore} isSearchMatch={true} />);

    // Assert
    expect(screen.getByText('88%')).toBeInTheDocument(); // Rounded to nearest integer
  });
});
