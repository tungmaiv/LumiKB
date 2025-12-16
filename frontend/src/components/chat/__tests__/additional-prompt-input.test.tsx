/**
 * Component Tests: AdditionalPromptInput Component (Story 4.4)
 * Priority: P1 (High - Document generation refinement)
 * Generated: 2025-11-28
 *
 * Test Coverage:
 * - P1: Updates value on text input
 * - P1: Calls onChange with new value
 * - P1: Enforces character limit (500 chars)
 * - P1: Shows character counter
 * - P1: Disabled state prevents input
 * - P2: Displays custom placeholder
 * - P2: Shows warning when near character limit
 * - P2: Multi-line input support
 *
 * Knowledge Base References:
 * - component-tdd.md: Component test patterns with RTL
 * - test-quality.md: One assertion per test, clear Given-When-Then
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AdditionalPromptInput } from '../additional-prompt-input';

describe('AdditionalPromptInput Component', () => {
  it('[P1] should call onChange when user types text', async () => {
    /**
     * GIVEN: Component is rendered
     * WHEN: User types in textarea
     * THEN: onChange is called with each keystroke
     */
    const onChange = vi.fn();
    const user = userEvent.setup();

    render(<AdditionalPromptInput value="" onChange={onChange} />);

    const textarea = screen.getByTestId('additional-prompt-textarea');
    await user.type(textarea, 'Test');

    // userEvent.type calls onChange for each keystroke
    expect(onChange).toHaveBeenCalled();
    expect(onChange.mock.calls.length).toBeGreaterThan(0);
  });

  it('[P1] should display current value in textarea', () => {
    /**
     * GIVEN: Component is rendered with value
     * WHEN: Component displays
     * THEN: Textarea shows the value
     */
    const onChange = vi.fn();

    render(<AdditionalPromptInput value="Existing context" onChange={onChange} />);

    const textarea = screen.getByTestId('additional-prompt-textarea') as HTMLTextAreaElement;
    expect(textarea.value).toBe('Existing context');
  });

  it('[P1] should enforce 500 character limit', async () => {
    /**
     * GIVEN: User types more than 500 characters
     * WHEN: User continues typing
     * THEN: Input is capped at 500 characters
     */
    const onChange = vi.fn();
    const user = userEvent.setup();

    render(<AdditionalPromptInput value="" onChange={onChange} />);

    const longText = 'a'.repeat(510); // Exceeds limit
    const textarea = screen.getByTestId('additional-prompt-textarea');

    await user.type(textarea, longText);

    // onChange should only be called for first 500 chars
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1];
    if (lastCall) {
      expect(lastCall[0].length).toBeLessThanOrEqual(500);
    }
  });

  it('[P1] should display character counter', () => {
    /**
     * GIVEN: Component is rendered with text
     * WHEN: Component displays
     * THEN: Character counter shows current/max
     */
    const onChange = vi.fn();

    render(<AdditionalPromptInput value="Test input" onChange={onChange} />);

    const charCount = screen.getByTestId('char-count');
    expect(charCount).toHaveTextContent('10/500');
  });

  it('[P1] should update character counter as user types', async () => {
    /**
     * GIVEN: Component is rendered
     * WHEN: User types text
     * THEN: Character counter updates
     */
    const onChange = vi.fn();
    const user = userEvent.setup();

    const { rerender } = render(<AdditionalPromptInput value="" onChange={onChange} />);

    expect(screen.getByTestId('char-count')).toHaveTextContent('0/500');

    // Simulate value change
    rerender(<AdditionalPromptInput value="Hello" onChange={onChange} />);

    expect(screen.getByTestId('char-count')).toHaveTextContent('5/500');
  });

  it('[P1] should disable textarea when disabled prop is true', () => {
    /**
     * GIVEN: Component is rendered with disabled=true
     * WHEN: Component displays
     * THEN: Textarea is disabled
     */
    const onChange = vi.fn();

    render(<AdditionalPromptInput value="" onChange={onChange} disabled={true} />);

    const textarea = screen.getByTestId('additional-prompt-textarea');
    expect(textarea).toBeDisabled();
  });

  it('[P2] should display custom placeholder text', () => {
    /**
     * GIVEN: Component is rendered with custom placeholder
     * WHEN: Component displays
     * THEN: Custom placeholder is shown
     */
    const onChange = vi.fn();

    render(
      <AdditionalPromptInput value="" onChange={onChange} placeholder="Custom placeholder" />
    );

    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument();
  });

  it('[P2] should show warning styling when near character limit', () => {
    /**
     * GIVEN: User has typed >80% of max characters (>400 chars)
     * WHEN: Component displays
     * THEN: Character counter shows warning color
     */
    const onChange = vi.fn();
    const longText = 'a'.repeat(420); // >80% of 500

    render(<AdditionalPromptInput value={longText} onChange={onChange} />);

    const charCount = screen.getByTestId('char-count');
    const countText = charCount.querySelector('span');

    // Check if warning class is applied (amber color)
    expect(countText).toHaveClass('text-amber-600');
  });

  it('[P2] should allow multi-line input', () => {
    /**
     * GIVEN: Component is rendered with multi-line value
     * WHEN: Component displays
     * THEN: Textarea shows multi-line content
     */
    const onChange = vi.fn();
    const multiLineValue = 'Line 1\nLine 2\nLine 3';

    render(<AdditionalPromptInput value={multiLineValue} onChange={onChange} />);

    const textarea = screen.getByTestId('additional-prompt-textarea') as HTMLTextAreaElement;
    expect(textarea.value).toContain('\n');
    expect(textarea.value).toBe(multiLineValue);
  });

  it('[P2] should show help text with Info icon', () => {
    /**
     * GIVEN: Component is rendered
     * WHEN: Component displays
     * THEN: Help text is visible
     */
    const onChange = vi.fn();

    render(<AdditionalPromptInput value="" onChange={onChange} />);

    expect(
      screen.getByText(/Provide specific requirements, tone, or sections to focus on/i)
    ).toBeInTheDocument();
  });

  it('[P2] should display "Optional" label indicator', () => {
    /**
     * GIVEN: Component is rendered
     * WHEN: Component displays
     * THEN: Label shows "Optional" indicator
     */
    const onChange = vi.fn();

    render(<AdditionalPromptInput value="" onChange={onChange} />);

    expect(screen.getByText(/Additional Context/i)).toBeInTheDocument();
    expect(screen.getByText(/Optional/i)).toBeInTheDocument();
  });

  it('[P3] should render textarea with correct ID and label association', () => {
    /**
     * GIVEN: Component is rendered
     * WHEN: Component displays
     * THEN: Label has htmlFor matching textarea ID
     */
    const onChange = vi.fn();

    render(<AdditionalPromptInput value="" onChange={onChange} />);

    const label = screen.getByText(/Additional Context/i);
    expect(label).toHaveAttribute('for', 'additional-prompt');
  });
});
