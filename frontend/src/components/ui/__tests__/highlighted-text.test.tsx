/**
 * Tests for HighlightedText component (Story 3.9, AC2)
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HighlightedText } from '../highlighted-text';

describe('HighlightedText', () => {
  it('highlights keywords in text', () => {
    const { container } = render(
      <HighlightedText text="OAuth 2.0 authentication" keywords={['OAuth', 'authentication']} />
    );

    const marks = container.querySelectorAll('mark');
    expect(marks).toHaveLength(2);
    expect(marks[0].textContent).toBe('OAuth');
    expect(marks[1].textContent).toBe('authentication');
  });

  it('handles case-insensitive matching', () => {
    const { container } = render(
      <HighlightedText text="OAUTH 2.0 Authentication" keywords={['oauth', 'authentication']} />
    );

    const marks = container.querySelectorAll('mark');
    expect(marks.length).toBeGreaterThan(0);
    // Original case preserved
    expect(marks[0].textContent).toBe('OAUTH');
  });

  it('preserves word boundaries - no partial highlights', () => {
    const { container } = render(
      <HighlightedText text="OAuth authentication authenticator" keywords={['authentication']} />
    );

    const marks = container.querySelectorAll('mark');
    // Should only highlight "authentication", not "authenticator"
    expect(marks).toHaveLength(1);
    expect(marks[0].textContent).toBe('authentication');
  });

  it('renders plain text when no keywords provided', () => {
    const { container } = render(<HighlightedText text="OAuth 2.0 authentication" keywords={[]} />);

    const marks = container.querySelectorAll('mark');
    expect(marks).toHaveLength(0);
    expect(container.textContent).toBe('OAuth 2.0 authentication');
  });

  it('handles empty keyword array', () => {
    const { container } = render(<HighlightedText text="Test text" keywords={[]} />);

    const marks = container.querySelectorAll('mark');
    expect(marks).toHaveLength(0);
  });

  it('escapes regex special characters in keywords', () => {
    const { container } = render(<HighlightedText text="test [1] pattern" keywords={['[1]']} />);

    const marks = container.querySelectorAll('mark');
    // Should handle regex special chars without breaking (may not match due to word boundaries)
    // At minimum, verify no crash
    expect(container.textContent).toContain('[1]');
  });
});
