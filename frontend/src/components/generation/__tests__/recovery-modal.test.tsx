/**
 * RecoveryModal Component Tests (Story 4-8)
 *
 * Test Coverage: AC3 (Alternative Suggestions Display)
 * Priority: P1 (Core UI functionality)
 *
 * Tests:
 * 1. Alternatives displayed with correct descriptions
 * 2. Action buttons trigger onActionSelect
 * 3. Cancel closes modal
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { RecoveryModal } from '../recovery-modal';

describe('RecoveryModal', () => {
  const mockAlternatives = [
    {
      type: 're_search',
      description: 'Search for different sources with a broader or more specific query',
      action: 'change_search',
    },
    {
      type: 'add_context',
      description: 'Provide additional context or requirements for generation',
      action: 'add_instructions',
    },
    {
      type: 'start_fresh',
      description: 'Start over with a new draft',
      action: 'create_new',
    },
  ];

  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onActionSelect: vi.fn(),
    alternatives: mockAlternatives,
  };

  it('[P1] should display alternatives with correct descriptions', () => {
    // GIVEN: RecoveryModal with 3 alternatives
    render(<RecoveryModal {...defaultProps} />);

    // THEN: All 3 alternative descriptions are visible (with numbering)
    expect(
      screen.getByText(/1\.\s*Search for different sources with a broader or more specific query/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/2\.\s*Provide additional context or requirements for generation/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/3\.\s*Start over with a new draft/i)).toBeInTheDocument();

    // AND: Each alternative has a "Try this" action button
    const actionButtons = screen.getAllByRole('button', { name: /try this/i });
    expect(actionButtons).toHaveLength(3);
  });

  it('[P1] should trigger onActionSelect when action button clicked', async () => {
    // GIVEN: RecoveryModal with alternatives
    const onActionSelect = vi.fn();
    render(<RecoveryModal {...defaultProps} onActionSelect={onActionSelect} />);

    // WHEN: User clicks first "Try this" button (re_search)
    const actionButtons = screen.getAllByRole('button', { name: /try this/i });
    await userEvent.click(actionButtons[0]);

    // THEN: onActionSelect called with first alternative's action string
    expect(onActionSelect).toHaveBeenCalledWith('change_search');

    // WHEN: User clicks second "Try this" button (add_context)
    await userEvent.click(actionButtons[1]);

    // THEN: onActionSelect called with second alternative's action string
    expect(onActionSelect).toHaveBeenCalledWith('add_instructions');
  });

  it('[P1] should close modal when cancel button clicked', async () => {
    // GIVEN: RecoveryModal is open
    const onClose = vi.fn();
    render(<RecoveryModal {...defaultProps} onClose={onClose} />);

    // WHEN: User clicks Cancel button (specifically the one in footer, not the X close button)
    const cancelButton = screen.getByRole('button', { name: /^cancel$/i });
    await userEvent.click(cancelButton);

    // THEN: onClose called
    expect(onClose).toHaveBeenCalled();
  });

  it('[P1] should display feedback type context', () => {
    // GIVEN: RecoveryModal is open
    render(<RecoveryModal {...defaultProps} />);

    // THEN: Dialog title or description provides context
    expect(
      screen.getByText(/let's try something different/i) ||
        screen.getByText(/based on your feedback/i)
    ).toBeInTheDocument();
  });

  it('[P1] should handle empty alternatives gracefully', () => {
    // GIVEN: RecoveryModal with no alternatives
    render(<RecoveryModal {...defaultProps} alternatives={[]} />);

    // THEN: No action buttons displayed
    const actionButtons = screen.queryAllByRole('button', { name: /try this/i });
    expect(actionButtons).toHaveLength(0);

    // AND: Cancel button still visible
    const cancelButton = screen.getByRole('button', { name: /^cancel$/i });
    expect(cancelButton).toBeInTheDocument();
  });

  it('[P1] should render different alternative types correctly', () => {
    // GIVEN: RecoveryModal with "wrong_format" alternatives
    const templateAlternatives = [
      {
        type: 'use_template',
        description: 'Choose a different template structure',
        action: 'select_template',
      },
      {
        type: 'regenerate_structured',
        description: 'Regenerate with better formatting',
        action: 'regenerate',
      },
    ];

    render(<RecoveryModal {...defaultProps} alternatives={templateAlternatives} />);

    // THEN: Template-related alternatives displayed (with numbering)
    expect(screen.getByText(/1\.\s*Choose a different template structure/i)).toBeInTheDocument();
    expect(screen.getByText(/2\.\s*Regenerate with better formatting/i)).toBeInTheDocument();

    // AND: 2 action buttons visible
    const actionButtons = screen.getAllByRole('button', { name: /try this/i });
    expect(actionButtons).toHaveLength(2);
  });

  it('[P1] should be keyboard accessible', async () => {
    // GIVEN: RecoveryModal is open
    render(<RecoveryModal {...defaultProps} />);

    // WHEN: User navigates with keyboard
    const firstActionButton = screen.getAllByRole('button', { name: /try this/i })[0];

    // THEN: Button is focusable
    firstActionButton.focus();
    expect(firstActionButton).toHaveFocus();

    // WHEN: User presses Enter
    await userEvent.keyboard('{Enter}');

    // THEN: onActionSelect triggered with action string
    expect(defaultProps.onActionSelect).toHaveBeenCalledWith('change_search');
  });
});
