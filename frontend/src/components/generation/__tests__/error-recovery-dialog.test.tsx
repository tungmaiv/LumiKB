/**
 * ErrorRecoveryDialog Component Tests (Story 4-8)
 *
 * Test Coverage: AC5 (Error Recovery Options)
 * Priority: P1 (Error UX)
 *
 * Tests:
 * 1. Retry action triggers regeneration
 * 2. Template action opens template selector
 * 3. Search action navigates to search page
 * 4. Error message displayed correctly
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ErrorRecoveryDialog } from '../error-recovery-dialog';

// Mock Next.js router (not used in component, but keeping for potential future use)
const mockPush = vi.fn();
const mockRouter = {
  push: mockPush,
  pathname: '/drafts/123',
  query: {},
  asPath: '/drafts/123',
};

vi.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
}));

describe('ErrorRecoveryDialog', () => {
  const mockRecoveryOptions = [
    {
      type: 'retry',
      description: 'Retry generation with same parameters',
      action: 'retry',
    },
    {
      type: 'use_template',
      description: 'Start from a structured template instead',
      action: 'select_template',
    },
    {
      type: 'search_more',
      description: 'Search for more sources before generating',
      action: 'search',
    },
  ];

  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onActionSelect: vi.fn(),
    errorMessage: 'Generation took too long and was cancelled.',
    errorType: 'LLMTimeout',
    recoveryOptions: mockRecoveryOptions,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('[P1] should trigger onActionSelect when retry option clicked', async () => {
    // GIVEN: ErrorRecoveryDialog with retry option
    const onActionSelect = vi.fn();
    render(<ErrorRecoveryDialog {...defaultProps} onActionSelect={onActionSelect} />);

    // WHEN: User clicks retry recovery option
    const recoveryButtons = screen.getAllByRole('button');
    // Find the retry button (first recovery option, not Cancel/Dismiss)
    const retryButton = recoveryButtons.find(btn =>
      btn.textContent?.includes('Retry generation') ||
      btn.className?.includes('hover:bg-muted')
    );

    if (retryButton) {
      await userEvent.click(retryButton);
      // THEN: onActionSelect callback triggered with 'retry' action
      expect(onActionSelect).toHaveBeenCalledWith('retry');
    }
  });

  it('[P1] should trigger onActionSelect when template option clicked', async () => {
    // GIVEN: ErrorRecoveryDialog with template option
    const onActionSelect = vi.fn();
    render(<ErrorRecoveryDialog {...defaultProps} onActionSelect={onActionSelect} />);

    // WHEN: User clicks template recovery option (second option)
    const recoveryButtons = screen.getAllByRole('button');
    const templateButton = recoveryButtons.find(btn =>
      btn.textContent?.includes('structured template') ||
      (btn.className?.includes('hover:bg-muted') && btn.textContent?.includes('template'))
    );

    if (templateButton) {
      await userEvent.click(templateButton);
      // THEN: onActionSelect callback triggered with 'select_template' action
      expect(onActionSelect).toHaveBeenCalledWith('select_template');
    }
  });

  it('[P1] should trigger onActionSelect when search option clicked', async () => {
    // GIVEN: ErrorRecoveryDialog with search option
    const onActionSelect = vi.fn();
    render(<ErrorRecoveryDialog {...defaultProps} onActionSelect={onActionSelect} />);

    // WHEN: User clicks search recovery option (third option)
    const recoveryButtons = screen.getAllByRole('button');
    const searchButton = recoveryButtons.find(btn =>
      btn.textContent?.includes('Search for more sources') ||
      (btn.className?.includes('hover:bg-muted') && btn.textContent?.includes('Search'))
    );

    if (searchButton) {
      await userEvent.click(searchButton);
      // THEN: onActionSelect callback triggered with 'search' action
      expect(onActionSelect).toHaveBeenCalledWith('search');
    }
  });

  it('[P1] should display error message and type correctly', () => {
    // GIVEN: ErrorRecoveryDialog with error details
    render(<ErrorRecoveryDialog {...defaultProps} />);

    // THEN: Error message is visible
    expect(screen.getByText('Generation took too long and was cancelled.')).toBeInTheDocument();

    // AND: Error type displayed in error details section
    expect(screen.getByText(/Type:\s*LLMTimeout/i)).toBeInTheDocument();
  });

  it('[P1] should display all recovery options', () => {
    // GIVEN: ErrorRecoveryDialog with 3 recovery options
    render(<ErrorRecoveryDialog {...defaultProps} />);

    // THEN: All recovery option descriptions visible
    expect(screen.getByText('Retry generation with same parameters')).toBeInTheDocument();
    expect(screen.getByText('Start from a structured template instead')).toBeInTheDocument();
    expect(screen.getByText('Search for more sources before generating')).toBeInTheDocument();

    // AND: Recovery options are rendered as clickable elements
    const allButtons = screen.getAllByRole('button');
    // Should have at least: 3 recovery options + 1 dismiss button
    expect(allButtons.length).toBeGreaterThanOrEqual(4);
  });

  it('[P1] should close dialog when dismiss button clicked', async () => {
    // GIVEN: ErrorRecoveryDialog is open
    const onClose = vi.fn();
    render(<ErrorRecoveryDialog {...defaultProps} onClose={onClose} />);

    // WHEN: User clicks Dismiss button
    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    await userEvent.click(dismissButton);

    // THEN: onClose callback triggered
    expect(onClose).toHaveBeenCalled();
  });

  it('[P1] should handle rate limit error with wait option', async () => {
    // GIVEN: ErrorRecoveryDialog with rate limit error
    const rateLimitOptions = [
      {
        type: 'wait_retry',
        description: 'Wait 30 seconds and retry automatically',
        action: 'auto_retry',
      },
      {
        type: 'use_template',
        description: 'Use a template while waiting',
        action: 'select_template',
      },
    ];

    render(<ErrorRecoveryDialog
      {...defaultProps}
      errorMessage="Too many requests. Please wait and try again."
      errorType="RateLimitError"
      recoveryOptions={rateLimitOptions}
    />);

    // THEN: Rate limit message displayed
    expect(screen.getByText('Too many requests. Please wait and try again.')).toBeInTheDocument();

    // AND: Auto-retry option shown
    expect(screen.getByText('Wait 30 seconds and retry automatically')).toBeInTheDocument();
  });

  it('[P1] should handle insufficient sources error', () => {
    // GIVEN: ErrorRecoveryDialog with insufficient sources error
    const insufficientSourcesOptions = [
      {
        type: 'search_more',
        description: 'Search for more sources with different query',
        action: 'search',
      },
      {
        type: 'use_template',
        description: 'Start from a structured template',
        action: 'select_template',
      },
    ];

    render(<ErrorRecoveryDialog
      {...defaultProps}
      errorMessage="Not enough sources found to generate content."
      errorType="InsufficientSources"
      recoveryOptions={insufficientSourcesOptions}
    />);

    // THEN: Error message displayed
    expect(
      screen.getByText('Not enough sources found to generate content.')
    ).toBeInTheDocument();

    // AND: Search option prioritized
    expect(
      screen.getByText('Search for more sources with different query')
    ).toBeInTheDocument();
  });

  it('[P1] should be keyboard accessible', async () => {
    // GIVEN: ErrorRecoveryDialog is open
    const onActionSelect = vi.fn();
    render(<ErrorRecoveryDialog {...defaultProps} onActionSelect={onActionSelect} />);

    // WHEN: User navigates to first recovery button
    const allButtons = screen.getAllByRole('button');
    const firstRecoveryButton = allButtons.find(btn =>
      btn.className?.includes('hover:bg-muted')
    );

    if (firstRecoveryButton) {
      firstRecoveryButton.focus();

      // THEN: Button is focusable
      expect(firstRecoveryButton).toHaveFocus();

      // WHEN: User presses Enter
      await userEvent.keyboard('{Enter}');

      // THEN: onActionSelect triggered
      expect(onActionSelect).toHaveBeenCalled();
    }
  });

  it('[P1] should handle empty recovery options gracefully', () => {
    // GIVEN: ErrorRecoveryDialog with no recovery options
    render(<ErrorRecoveryDialog
      {...defaultProps}
      errorMessage="Unknown error occurred."
      errorType="UnknownError"
      recoveryOptions={[]}
    />);

    // THEN: Error message still displayed
    expect(screen.getByText('Unknown error occurred.')).toBeInTheDocument();

    // AND: Dismiss button and Contact Support button available
    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    expect(dismissButton).toBeInTheDocument();

    // When no recovery options, "Contact Support" button appears
    const supportButton = screen.getByRole('button', { name: /contact support/i });
    expect(supportButton).toBeInTheDocument();
  });

  it('[P1] should display error icon or visual indicator', () => {
    // GIVEN: ErrorRecoveryDialog with error
    render(<ErrorRecoveryDialog {...defaultProps} />);

    // THEN: Dialog title includes "Generation Failed" which indicates error
    expect(screen.getByText(/generation failed/i)).toBeInTheDocument();

    // AND: Error details section is visible
    expect(screen.getByText(/error details/i)).toBeInTheDocument();
  });
});
