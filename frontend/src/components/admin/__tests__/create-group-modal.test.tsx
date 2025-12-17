/**
 * Component tests for CreateGroupModal
 * Story 5.19: Group Management (AC-5.19.2)
 *
 * Test Coverage:
 * - [P1] Modal renders with form fields
 * - [P1] Form validation prevents empty name
 * - [P1] onCreateGroup called with valid data
 * - [P1] Modal closes after successful creation
 * - [P2] Error handling displays error message
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Component testing patterns
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CreateGroupModal, type CreateGroupModalProps } from '../create-group-modal';

describe('CreateGroupModal', () => {
  const defaultProps: CreateGroupModalProps = {
    open: true,
    onOpenChange: vi.fn(),
    onCreateGroup: vi.fn().mockResolvedValue(undefined),
    isCreating: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('[P1] renders modal with form fields when open', () => {
      /**
       * GIVEN: CreateGroupModal with open=true
       * WHEN: Component renders
       * THEN: Modal displays with form fields
       */

      // WHEN: Render component
      render(<CreateGroupModal {...defaultProps} />);

      // THEN: Modal title is visible
      expect(screen.getByRole('heading', { name: /Create New Group/i })).toBeInTheDocument();

      // THEN: Form fields are present
      expect(screen.getByLabelText(/Group Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();

      // THEN: Action buttons are present
      expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Create Group/i })).toBeInTheDocument();
    });

    it('[P1] does not render when open=false', () => {
      /**
       * GIVEN: CreateGroupModal with open=false
       * WHEN: Component renders
       * THEN: Modal is not visible
       */

      // WHEN: Render with open=false
      render(<CreateGroupModal {...defaultProps} open={false} />);

      // THEN: Modal content is not visible
      expect(screen.queryByRole('heading', { name: /Create New Group/i })).not.toBeInTheDocument();
    });

    it('[P2] shows loading state when isCreating=true', () => {
      /**
       * GIVEN: CreateGroupModal during creation
       * WHEN: Component renders
       * THEN: Create button shows loading state
       */

      // WHEN: Render with isCreating=true
      render(<CreateGroupModal {...defaultProps} isCreating={true} />);

      // THEN: Create button is disabled
      const createButton = screen.getByRole('button', { name: /Create/i });
      expect(createButton).toBeDisabled();
    });
  });

  describe('validation', () => {
    it('[P1] shows error when submitting empty name', async () => {
      /**
       * GIVEN: CreateGroupModal with empty form
       * WHEN: User clicks Create without entering name
       * THEN: Validation error is displayed
       */
      const user = userEvent.setup();

      // WHEN: Render and submit empty form
      render(<CreateGroupModal {...defaultProps} />);
      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      // THEN: Error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/Group name is required/i)).toBeInTheDocument();
      });

      // THEN: onCreateGroup was not called
      expect(defaultProps.onCreateGroup).not.toHaveBeenCalled();
    });

    it('[P1] shows error when name exceeds max length', async () => {
      /**
       * GIVEN: CreateGroupModal with too long name
       * WHEN: User enters name over 255 characters
       * THEN: Validation error is displayed
       */
      const user = userEvent.setup();
      const longName = 'a'.repeat(256);

      // WHEN: Render and enter long name
      render(<CreateGroupModal {...defaultProps} />);
      await user.type(screen.getByLabelText(/Group Name/i), longName);
      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      // THEN: Error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/at most 255 characters/i)).toBeInTheDocument();
      });
    });
  });

  describe('form submission', () => {
    it('[P1] calls onCreateGroup with valid data', async () => {
      /**
       * GIVEN: CreateGroupModal with form fields
       * WHEN: User fills form and submits
       * THEN: onCreateGroup is called with form data
       */
      const user = userEvent.setup();
      const onCreateGroup = vi.fn().mockResolvedValue(undefined);

      // WHEN: Render and fill form
      render(<CreateGroupModal {...defaultProps} onCreateGroup={onCreateGroup} />);
      await user.type(screen.getByLabelText(/Group Name/i), 'New Team');
      await user.type(screen.getByLabelText(/Description/i), 'A new team description');
      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      // THEN: onCreateGroup called with correct data
      await waitFor(() => {
        expect(onCreateGroup).toHaveBeenCalledWith({
          name: 'New Team',
          description: 'A new team description',
        });
      });
    });

    it('[P1] calls onCreateGroup with null description when empty', async () => {
      /**
       * GIVEN: CreateGroupModal with only name filled
       * WHEN: User submits without description
       * THEN: onCreateGroup is called with null description
       */
      const user = userEvent.setup();
      const onCreateGroup = vi.fn().mockResolvedValue(undefined);

      // WHEN: Render and fill only name
      render(<CreateGroupModal {...defaultProps} onCreateGroup={onCreateGroup} />);
      await user.type(screen.getByLabelText(/Group Name/i), 'New Team');
      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      // THEN: onCreateGroup called with null description
      await waitFor(() => {
        expect(onCreateGroup).toHaveBeenCalledWith({
          name: 'New Team',
          description: null,
        });
      });
    });

    it('[P1] closes modal after successful creation', async () => {
      /**
       * GIVEN: CreateGroupModal with valid form
       * WHEN: User submits and creation succeeds
       * THEN: Modal closes (onOpenChange called with false)
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();
      const onCreateGroup = vi.fn().mockResolvedValue(undefined);

      // WHEN: Render and submit valid form
      render(
        <CreateGroupModal
          {...defaultProps}
          onOpenChange={onOpenChange}
          onCreateGroup={onCreateGroup}
        />
      );
      await user.type(screen.getByLabelText(/Group Name/i), 'New Team');
      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      // THEN: Modal closes
      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(false);
      });
    });
  });

  describe('error handling', () => {
    it('[P2] displays error message when creation fails', async () => {
      /**
       * GIVEN: CreateGroupModal where creation will fail
       * WHEN: User submits form
       * THEN: Error message is displayed
       */
      const user = userEvent.setup();
      const onCreateGroup = vi
        .fn()
        .mockRejectedValue(new Error('A group with this name already exists'));

      // WHEN: Render and submit form
      render(<CreateGroupModal {...defaultProps} onCreateGroup={onCreateGroup} />);
      await user.type(screen.getByLabelText(/Group Name/i), 'Existing Team');
      await user.click(screen.getByRole('button', { name: /Create Group/i }));

      // THEN: Error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/already exists/i)).toBeInTheDocument();
      });
    });
  });

  describe('cancel behavior', () => {
    it('[P1] closes modal when cancel is clicked', async () => {
      /**
       * GIVEN: CreateGroupModal is open
       * WHEN: User clicks Cancel
       * THEN: Modal closes
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      // WHEN: Render and click Cancel
      render(<CreateGroupModal {...defaultProps} onOpenChange={onOpenChange} />);
      await user.click(screen.getByRole('button', { name: /Cancel/i }));

      // THEN: Modal closes
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });

    it('[P1] resets form when modal closes', async () => {
      /**
       * GIVEN: CreateGroupModal with filled form
       * WHEN: User cancels and reopens modal
       * THEN: Form is reset
       */
      const user = userEvent.setup();
      const { rerender } = render(<CreateGroupModal {...defaultProps} />);

      // Fill form
      await user.type(screen.getByLabelText(/Group Name/i), 'Test Group');

      // Close modal
      await user.click(screen.getByRole('button', { name: /Cancel/i }));

      // Reopen modal
      rerender(<CreateGroupModal {...defaultProps} open={true} />);

      // THEN: Form is reset
      expect(screen.getByLabelText(/Group Name/i)).toHaveValue('');
    });
  });
});
