/**
 * Unit tests for TextViewer component
 * Story 5-26: Document Chunk Viewer Frontend
 *
 * Tests text document rendering with line numbers and highlighting.
 * AC-5.26.4: Content pane renders document based on type (Text)
 * AC-5.26.6: Click chunk scrolls to position in document
 */

import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { TextViewer } from '../viewers/text-viewer';

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

describe('TextViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P0] should render text content with line numbers - AC-5.26.4', () => {
    // Arrange
    const content = 'Line 1\nLine 2\nLine 3';

    // Act
    render(<TextViewer content={content} showLineNumbers={true} />);

    // Assert
    expect(screen.getByTestId('text-viewer')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Line 1')).toBeInTheDocument();
    expect(screen.getByText('Line 2')).toBeInTheDocument();
    expect(screen.getByText('Line 3')).toBeInTheDocument();
  });

  it('[P0] should render without line numbers when disabled - AC-5.26.4', () => {
    // Arrange
    const content = 'Line 1\nLine 2';

    // Act
    render(<TextViewer content={content} showLineNumbers={false} />);

    // Assert
    expect(screen.getByText('Line 1')).toBeInTheDocument();
    // Line numbers should not be in the document as separate elements
    // (they would be within the line number column)
    const textViewer = screen.getByTestId('text-viewer');
    expect(textViewer.querySelector('.text-muted-foreground.text-right')).not.toBeInTheDocument();
  });

  it('[P0] should highlight specified character range - AC-5.26.6', () => {
    // Arrange
    const content = 'Hello World';
    const highlightRange = { start: 0, end: 5 }; // "Hello"

    // Act
    render(<TextViewer content={content} highlightRange={highlightRange} />);

    // Assert - the highlight class should be applied
    const highlightedSpan = screen.getByText('Hello');
    expect(highlightedSpan).toHaveClass('bg-yellow-300');
  });

  it('[P0] should call scrollIntoView for highlighted section - AC-5.26.6', () => {
    // Arrange
    const content = 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5';
    const highlightRange = { start: 14, end: 20 }; // Part of "Line 3"

    // Act
    render(<TextViewer content={content} highlightRange={highlightRange} />);

    // Assert
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'center',
    });
  });

  it('[P0] should show loading state - AC-5.26.4', () => {
    // Act
    render(<TextViewer content={null} isLoading={true} />);

    // Assert
    expect(screen.getByTestId('text-viewer-loading')).toBeInTheDocument();
  });

  it('[P0] should show error state - AC-5.26.4', () => {
    // Act
    render(<TextViewer content={null} error="Network timeout error" />);

    // Assert
    expect(screen.getByTestId('text-viewer-error')).toBeInTheDocument();
    expect(screen.getByText('Network timeout error')).toBeInTheDocument();
    expect(screen.getByText('Failed to load document')).toBeInTheDocument(); // Title
  });

  it('[P0] should show empty state when content is null - AC-5.26.4', () => {
    // Act
    render(<TextViewer content={null} />);

    // Assert
    expect(screen.getByText('No content available')).toBeInTheDocument();
  });

  it('[P1] should handle multi-line highlight range - AC-5.26.6', () => {
    // Arrange
    const content = 'Line 1\nLine 2\nLine 3';
    const highlightRange = { start: 7, end: 20 }; // "Line 2\nLine 3"

    // Act
    render(<TextViewer content={content} highlightRange={highlightRange} />);

    // Assert - both lines should have highlighting
    const textViewer = screen.getByTestId('text-viewer');
    const highlightedRows = textViewer.querySelectorAll('.bg-yellow-100');
    expect(highlightedRows.length).toBeGreaterThanOrEqual(2);
  });

  it('[P1] should handle empty content', () => {
    // Act
    render(<TextViewer content="" />);

    // Assert
    expect(screen.getByText('No content available')).toBeInTheDocument();
  });

  it('[P1] should preserve whitespace in content - AC-5.26.4', () => {
    // Arrange
    const content = 'Line with    spaces\n  Indented line';

    // Act
    render(<TextViewer content={content} />);

    // Assert - content should be in pre-wrap
    const textViewer = screen.getByTestId('text-viewer');
    const contentSpan = textViewer.querySelector('.whitespace-pre-wrap');
    expect(contentSpan).toBeInTheDocument();
  });

  it('[P2] should handle very long content gracefully - AC-5.26.3', () => {
    // Arrange
    const lines = Array.from({ length: 1000 }, (_, i) => `Line ${i + 1}`);
    const content = lines.join('\n');

    // Act
    render(<TextViewer content={content} />);

    // Assert
    expect(screen.getByTestId('text-viewer')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('1000')).toBeInTheDocument();
  });

  it('[P2] should handle highlight at end of content', () => {
    // Arrange
    const content = 'Hello World';
    const highlightRange = { start: 6, end: 11 }; // "World"

    // Act
    render(<TextViewer content={content} highlightRange={highlightRange} />);

    // Assert
    expect(screen.getByText('World')).toHaveClass('bg-yellow-300');
  });

  it('[P2] should calculate line number width correctly', () => {
    // Arrange - 1000 lines need 4-character width
    const lines = Array.from({ length: 1000 }, (_, i) => `Line ${i + 1}`);
    const content = lines.join('\n');

    // Act
    render(<TextViewer content={content} />);

    // Assert - line number width should accommodate 4 digits (1000)
    const textViewer = screen.getByTestId('text-viewer');
    const lineNumberElement = textViewer.querySelector('.text-muted-foreground.text-right');
    expect(lineNumberElement).toHaveStyle({ minWidth: '6ch' }); // 4 + 2 padding
  });

  it('[P2] should handle null highlightRange', () => {
    // Arrange
    const content = 'Hello World';

    // Act
    render(<TextViewer content={content} highlightRange={null} />);

    // Assert
    expect(screen.getByText('Hello World')).toBeInTheDocument();
    expect(Element.prototype.scrollIntoView).not.toHaveBeenCalled();
  });
});
