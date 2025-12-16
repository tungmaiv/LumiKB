/**
 * Unit tests for EnhancedMarkdownViewer component
 * Story 7-30: Enhanced Markdown Viewer with Highlighting
 *
 * Tests markdown rendering with character-based highlighting.
 * AC-7.30.2: Precise highlighting using char_start/char_end positions
 * AC-7.30.3: Highlight styling with dark mode support and auto-scroll
 * AC-7.30.5: Loading states
 * AC-7.30.6: Unit tests for highlight positioning, scroll behavior, fallback
 */

import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { EnhancedMarkdownViewer } from '../enhanced-markdown-viewer';

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

describe('EnhancedMarkdownViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ============================================================================
  // Content Rendering Tests - AC-7.30.2
  // ============================================================================

  it('[P0] should render markdown content - AC-7.30.2', () => {
    // Arrange
    const content = '# Heading\n\nParagraph text';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert
    expect(screen.getByTestId('enhanced-markdown-viewer')).toBeInTheDocument();
    expect(screen.getByText('Heading')).toBeInTheDocument();
    expect(screen.getByText('Paragraph text')).toBeInTheDocument();
  });

  it('[P0] should render markdown with proper styling - AC-7.30.2', () => {
    // Arrange
    const content = '# Main Title\n\n## Subtitle\n\nRegular paragraph';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert
    const h1 = screen.getByRole('heading', { level: 1 });
    expect(h1).toHaveTextContent('Main Title');
    expect(h1).toHaveClass('text-2xl', 'font-bold');

    const h2 = screen.getByRole('heading', { level: 2 });
    expect(h2).toHaveTextContent('Subtitle');
    expect(h2).toHaveClass('text-xl', 'font-semibold');
  });

  // ============================================================================
  // Highlight Positioning Tests - AC-7.30.2
  // ============================================================================

  it('[P0] should highlight specified character range - AC-7.30.2', () => {
    // Arrange
    const content = 'Hello World Test';
    const highlightRange = { start: 6, end: 11 }; // "World"

    // Act
    render(
      <EnhancedMarkdownViewer content={content} highlightRange={highlightRange} />
    );

    // Assert
    const highlightSegment = screen.getByTestId('highlight-segment');
    expect(highlightSegment).toBeInTheDocument();
    expect(highlightSegment).toHaveTextContent('World');
  });

  it('[P0] should apply correct highlight styling - AC-7.30.3', () => {
    // Arrange
    const content = 'Hello World Test';
    const highlightRange = { start: 0, end: 5 }; // "Hello"

    // Act
    render(
      <EnhancedMarkdownViewer content={content} highlightRange={highlightRange} />
    );

    // Assert - should have yellow background with dark mode variant
    const highlightSegment = screen.getByTestId('highlight-segment');
    expect(highlightSegment).toHaveClass('bg-yellow-200', 'dark:bg-yellow-800');
  });

  it('[P0] should split content correctly for highlight at beginning - AC-7.30.2', () => {
    // Arrange
    const content = 'StartMiddleEnd';
    const highlightRange = { start: 0, end: 5 }; // "Start"

    // Act
    render(
      <EnhancedMarkdownViewer content={content} highlightRange={highlightRange} />
    );

    // Assert
    const highlightSegment = screen.getByTestId('highlight-segment');
    expect(highlightSegment).toHaveTextContent('Start');
    expect(screen.getByText(/MiddleEnd/)).toBeInTheDocument();
  });

  it('[P0] should split content correctly for highlight in middle - AC-7.30.2', () => {
    // Arrange
    const content = 'StartMiddleEnd';
    const highlightRange = { start: 5, end: 11 }; // "Middle"

    // Act
    render(
      <EnhancedMarkdownViewer content={content} highlightRange={highlightRange} />
    );

    // Assert
    const highlightSegment = screen.getByTestId('highlight-segment');
    expect(highlightSegment).toHaveTextContent('Middle');
  });

  it('[P0] should split content correctly for highlight at end - AC-7.30.2', () => {
    // Arrange
    const content = 'StartMiddleEnd';
    const highlightRange = { start: 11, end: 14 }; // "End"

    // Act
    render(
      <EnhancedMarkdownViewer content={content} highlightRange={highlightRange} />
    );

    // Assert
    const highlightSegment = screen.getByTestId('highlight-segment');
    expect(highlightSegment).toHaveTextContent('End');
  });

  it('[P1] should handle out-of-bounds highlight range gracefully - AC-7.30.6', () => {
    // Arrange
    const content = 'Short text';
    const highlightRange = { start: 5, end: 100 }; // end exceeds content length

    // Act
    render(
      <EnhancedMarkdownViewer content={content} highlightRange={highlightRange} />
    );

    // Assert - should clamp to valid range
    // "Short text" - start=5 is 't', end=100 clamped to 10
    const highlightSegment = screen.getByTestId('highlight-segment');
    expect(highlightSegment).toHaveTextContent('text');
  });

  it('[P1] should handle negative highlight range start - AC-7.30.6', () => {
    // Arrange
    const content = 'Test content';
    const highlightRange = { start: -5, end: 4 };

    // Act
    render(
      <EnhancedMarkdownViewer content={content} highlightRange={highlightRange} />
    );

    // Assert - should clamp start to 0
    const highlightSegment = screen.getByTestId('highlight-segment');
    expect(highlightSegment).toHaveTextContent('Test');
  });

  // ============================================================================
  // Scroll Behavior Tests - AC-7.30.3
  // ============================================================================

  it('[P0] should scroll highlighted section into view - AC-7.30.3', async () => {
    // Arrange
    const content = 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5';
    const highlightRange = { start: 14, end: 20 };

    // Act
    render(
      <EnhancedMarkdownViewer content={content} highlightRange={highlightRange} />
    );

    // Fast-forward timer for the scroll delay
    vi.advanceTimersByTime(150);

    // Assert
    expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'center',
    });
  });

  it('[P1] should not scroll when no highlight range - AC-7.30.3', () => {
    // Arrange
    const content = 'Line 1\nLine 2\nLine 3';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);
    vi.advanceTimersByTime(150);

    // Assert
    expect(Element.prototype.scrollIntoView).not.toHaveBeenCalled();
  });

  it('[P1] should not scroll when highlight range is null - AC-7.30.3', () => {
    // Arrange
    const content = 'Some content';

    // Act
    render(<EnhancedMarkdownViewer content={content} highlightRange={null} />);
    vi.advanceTimersByTime(150);

    // Assert
    expect(Element.prototype.scrollIntoView).not.toHaveBeenCalled();
  });

  // ============================================================================
  // Loading State Tests - AC-7.30.5
  // ============================================================================

  it('[P0] should show loading state - AC-7.30.5', () => {
    // Act
    render(<EnhancedMarkdownViewer content="" isLoading={true} />);

    // Assert
    expect(screen.getByTestId('enhanced-markdown-viewer-loading')).toBeInTheDocument();
  });

  // ============================================================================
  // Error State Tests - AC-7.30.5
  // ============================================================================

  it('[P0] should show error state - AC-7.30.5', () => {
    // Act
    render(<EnhancedMarkdownViewer content="" error="Network timeout error" />);

    // Assert
    expect(screen.getByTestId('enhanced-markdown-viewer-error')).toBeInTheDocument();
    expect(screen.getByText('Network timeout error')).toBeInTheDocument();
    expect(screen.getByText('Failed to load markdown content')).toBeInTheDocument();
  });

  // ============================================================================
  // Empty/Fallback State Tests - AC-7.30.4
  // ============================================================================

  it('[P0] should show empty state when content is empty - AC-7.30.4', () => {
    // Act
    render(<EnhancedMarkdownViewer content="" />);

    // Assert
    expect(screen.getByTestId('enhanced-markdown-viewer-empty')).toBeInTheDocument();
    expect(screen.getByText('No content available')).toBeInTheDocument();
  });

  it('[P1] should show fallback message when enabled - AC-7.30.4', () => {
    // Arrange
    const content = '# Test';

    // Act
    render(
      <EnhancedMarkdownViewer content={content} showFallbackMessage={true} />
    );

    // Assert
    expect(screen.getByText('Enhanced view:')).toBeInTheDocument();
    expect(screen.getByText('Precise chunk highlighting enabled')).toBeInTheDocument();
  });

  it('[P1] should not show fallback message when disabled - AC-7.30.4', () => {
    // Arrange
    const content = '# Test';

    // Act
    render(
      <EnhancedMarkdownViewer content={content} showFallbackMessage={false} />
    );

    // Assert
    expect(screen.queryByText('Enhanced view:')).not.toBeInTheDocument();
  });

  // ============================================================================
  // Markdown Element Rendering Tests - AC-7.30.2
  // ============================================================================

  it('[P1] should render code blocks correctly', () => {
    // Arrange
    const content = '```\nconst x = 1;\n```';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert
    const codeBlock = screen.getByText('const x = 1;');
    expect(codeBlock).toBeInTheDocument();
    expect(codeBlock).toHaveClass('font-mono');
  });

  it('[P1] should render inline code correctly', () => {
    // Arrange
    const content = 'Use `console.log` for debugging';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert
    const inlineCode = screen.getByText('console.log');
    expect(inlineCode).toHaveClass('bg-muted');
  });

  it('[P1] should render links with target="_blank"', () => {
    // Arrange
    const content = '[Link](https://example.com)';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert
    const link = screen.getByRole('link', { name: 'Link' });
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('[P1] should render unordered lists', () => {
    // Arrange
    const content = '- Item 1\n- Item 2\n- Item 3';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
    expect(screen.getByText('Item 3')).toBeInTheDocument();
    const list = screen.getByRole('list');
    expect(list).toHaveClass('list-disc');
  });

  it('[P1] should render ordered lists', () => {
    // Arrange
    const content = '1. First\n2. Second\n3. Third';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert
    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
    expect(screen.getByText('Third')).toBeInTheDocument();
    const list = screen.getByRole('list');
    expect(list).toHaveClass('list-decimal');
  });

  it('[P1] should render blockquotes', () => {
    // Arrange
    const content = '> This is a quote';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert
    const blockquote = screen.getByRole('blockquote');
    expect(blockquote).toBeInTheDocument();
    expect(blockquote).toHaveClass('border-l-4');
  });

  // ============================================================================
  // Edge Cases - AC-7.30.6
  // ============================================================================

  it('[P2] should handle empty highlight range (start equals end)', () => {
    // Arrange
    const content = 'Test content';
    const highlightRange = { start: 5, end: 5 };

    // Act
    render(
      <EnhancedMarkdownViewer content={content} highlightRange={highlightRange} />
    );

    // Assert - no highlight segment should be rendered
    expect(screen.queryByTestId('highlight-segment')).not.toBeInTheDocument();
  });

  it('[P2] should handle very long content', () => {
    // Arrange
    const lines = Array.from({ length: 100 }, (_, i) => `# Heading ${i + 1}\n\nParagraph ${i + 1}`);
    const content = lines.join('\n\n');

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert
    expect(screen.getByTestId('enhanced-markdown-viewer')).toBeInTheDocument();
    expect(screen.getByText('Heading 1')).toBeInTheDocument();
    expect(screen.getByText('Heading 100')).toBeInTheDocument();
  });

  it('[P2] should handle content with special characters', () => {
    // Arrange
    const content = '# Test & Demo <script>alert("xss")</script>';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert - script tag should not execute (rendered as text)
    const viewer = screen.getByTestId('enhanced-markdown-viewer');
    expect(viewer).toBeInTheDocument();
  });

  it('[P2] should have scroll container attribute for scroll isolation', () => {
    // Arrange
    const content = '# Test';

    // Act
    render(<EnhancedMarkdownViewer content={content} />);

    // Assert
    const viewer = screen.getByTestId('enhanced-markdown-viewer');
    expect(viewer).toHaveAttribute('data-scroll-container');
    expect(viewer).toHaveStyle({ overscrollBehavior: 'contain' });
  });
});
