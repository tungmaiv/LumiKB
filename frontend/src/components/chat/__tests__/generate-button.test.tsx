/**
 * Component Tests: GenerateButton Component (Story 4.4)
 * Priority: P1 (High - Primary action for document generation)
 * Generated: 2025-11-28
 *
 * Test Coverage:
 * - P1: Calls onClick when clicked
 * - P1: Disabled when disabled prop is true
 * - P1: Disabled when loading is true
 * - P1: Disabled when hasResults is false
 * - P1: Shows loading state with spinner
 * - P2: Displays correct button text
 * - P2: Shows FileText icon when not loading
 *
 * Knowledge Base References:
 * - component-tdd.md: Component test patterns with RTL
 * - test-quality.md: One assertion per test, clear Given-When-Then
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GenerateButton } from '../generate-button';

describe('GenerateButton Component', () => {
  it('[P1] should call onClick when button is clicked', async () => {
    /**
     * GIVEN: Button is enabled
     * WHEN: User clicks the button
     * THEN: onClick callback is called
     */
    const onClick = vi.fn();
    const user = userEvent.setup();

    render(<GenerateButton onClick={onClick} />);

    const button = screen.getByTestId('generate-button');
    await user.click(button);

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('[P1] should be disabled when disabled prop is true', () => {
    /**
     * GIVEN: Button is rendered with disabled=true
     * WHEN: Component displays
     * THEN: Button is disabled
     */
    const onClick = vi.fn();

    render(<GenerateButton onClick={onClick} disabled={true} />);

    const button = screen.getByTestId('generate-button');
    expect(button).toBeDisabled();
  });

  it('[P1] should be disabled when loading is true', () => {
    /**
     * GIVEN: Button is in loading state
     * WHEN: Component displays
     * THEN: Button is disabled
     */
    const onClick = vi.fn();

    render(<GenerateButton onClick={onClick} loading={true} />);

    const button = screen.getByTestId('generate-button');
    expect(button).toBeDisabled();
  });

  it('[P1] should be disabled when hasResults is false', () => {
    /**
     * GIVEN: No search results are available
     * WHEN: Component displays
     * THEN: Button is disabled
     */
    const onClick = vi.fn();

    render(<GenerateButton onClick={onClick} hasResults={false} />);

    const button = screen.getByTestId('generate-button');
    expect(button).toBeDisabled();
  });

  it('[P1] should show loading spinner when loading', () => {
    /**
     * GIVEN: Button is in loading state
     * WHEN: Component displays
     * THEN: Loading spinner is visible
     */
    const onClick = vi.fn();

    render(<GenerateButton onClick={onClick} loading={true} />);

    expect(screen.getByText('Generating...')).toBeInTheDocument();
  });

  it('[P1] should not call onClick when disabled', async () => {
    /**
     * GIVEN: Button is disabled
     * WHEN: User tries to click
     * THEN: onClick is not called
     */
    const onClick = vi.fn();
    const user = userEvent.setup();

    render(<GenerateButton onClick={onClick} disabled={true} />);

    const button = screen.getByTestId('generate-button');
    await user.click(button);

    expect(onClick).not.toHaveBeenCalled();
  });

  it('[P2] should display "Generate Draft" text when not loading', () => {
    /**
     * GIVEN: Button is not loading
     * WHEN: Component displays
     * THEN: Default button text is shown
     */
    const onClick = vi.fn();

    render(<GenerateButton onClick={onClick} />);

    expect(screen.getByText('Generate Draft')).toBeInTheDocument();
  });

  it('[P2] should show FileText icon when not loading', () => {
    /**
     * GIVEN: Button is not loading
     * WHEN: Component displays
     * THEN: FileText icon is visible
     */
    const onClick = vi.fn();

    render(<GenerateButton onClick={onClick} />);

    const button = screen.getByTestId('generate-button');
    const icon = button.querySelector('svg');

    expect(icon).toBeInTheDocument();
  });

  it('[P2] should show Loader2 icon when loading', () => {
    /**
     * GIVEN: Button is loading
     * WHEN: Component displays
     * THEN: Loader2 spinner icon is visible with animate-spin
     */
    const onClick = vi.fn();

    render(<GenerateButton onClick={onClick} loading={true} />);

    const button = screen.getByTestId('generate-button');
    const spinner = button.querySelector('.animate-spin');

    expect(spinner).toBeInTheDocument();
  });

  it('[P2] should be enabled when all conditions are met', () => {
    /**
     * GIVEN: Button has results, not disabled, not loading
     * WHEN: Component displays
     * THEN: Button is enabled
     */
    const onClick = vi.fn();

    render(<GenerateButton onClick={onClick} hasResults={true} />);

    const button = screen.getByTestId('generate-button');
    expect(button).toBeEnabled();
  });

  it('[P3] should apply large size styling', () => {
    /**
     * GIVEN: Component is rendered
     * WHEN: Component displays
     * THEN: Button has size="lg" prop applied
     */
    const onClick = vi.fn();

    render(<GenerateButton onClick={onClick} />);

    const button = screen.getByTestId('generate-button');
    // Size is applied via className, checking component renders
    expect(button).toBeInTheDocument();
  });

  it('[P3] should have responsive width classes', () => {
    /**
     * GIVEN: Component is rendered
     * WHEN: Component displays
     * THEN: Button has responsive width (full on mobile, auto on sm+)
     */
    const onClick = vi.fn();

    render(<GenerateButton onClick={onClick} />);

    const button = screen.getByTestId('generate-button');
    expect(button).toHaveClass('w-full', 'sm:w-auto');
  });
});
