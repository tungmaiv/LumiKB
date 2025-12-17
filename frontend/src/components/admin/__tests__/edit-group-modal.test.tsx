/**
 * Component tests for EditGroupModal
 * Story 5.19: Group Management (AC-5.19.3)
 *
 * Test Coverage:
 * - [P1] Modal renders with pre-populated form
 * - [P1] Status toggle updates is_active
 * - [P1] onUpdateGroup called with changed fields only
 * - [P1] Modal closes after successful update
 * - [P2] Error handling displays error message
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Component testing patterns
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EditGroupModal, type EditGroupModalProps } from '../edit-group-modal';
import type { Group } from '@/types/group';
import { PermissionLevel } from '@/types/user';

const mockGroup: Group = {
  id: 'group-1',
  name: 'Engineering',
  description: 'Software engineering team',
  is_active: true,
  permission_level: PermissionLevel.USER,
  is_system: false,
  member_count: 5,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-12-05T00:00:00Z',
};

describe('EditGroupModal', () => {
  const defaultProps: EditGroupModalProps = {
    group: mockGroup,
    open: true,
    onOpenChange: vi.fn(),
    onUpdateGroup: vi.fn().mockResolvedValue(undefined),
    isUpdating: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('[P1] renders modal with pre-populated form', () => {
      /**
       * GIVEN: EditGroupModal with group data
       * WHEN: Component renders
       * THEN: Form fields are pre-populated
       */

      // WHEN: Render component
      render(<EditGroupModal {...defaultProps} />);

      // THEN: Modal title is visible
      expect(screen.getByRole('heading', { name: /Edit Group/i })).toBeInTheDocument();

      // THEN: Form fields are pre-populated
      expect(screen.getByLabelText(/Group Name/i)).toHaveValue('Engineering');
      expect(screen.getByLabelText(/Description/i)).toHaveValue('Software engineering team');

      // THEN: Status toggle shows active
      const statusToggle = screen.getByRole('switch');
      expect(statusToggle).toBeChecked();
    });

    it('[P1] does not render when group is null', () => {
      /**
       * GIVEN: EditGroupModal with group=null
       * WHEN: Component renders
       * THEN: Modal is not visible
       */

      // WHEN: Render with null group
      render(<EditGroupModal {...defaultProps} group={null} />);

      // THEN: Modal content is not visible
      expect(screen.queryByRole('heading', { name: /Edit Group/i })).not.toBeInTheDocument();
    });

    it('[P2] displays member count and created date', () => {
      /**
       * GIVEN: EditGroupModal with group data
       * WHEN: Component renders
       * THEN: Group metadata is displayed
       */

      // WHEN: Render component
      render(<EditGroupModal {...defaultProps} />);

      // THEN: Metadata is displayed
      expect(screen.getByText(/Members: 5/i)).toBeInTheDocument();
    });

    it('[P2] shows loading state when isUpdating=true', () => {
      /**
       * GIVEN: EditGroupModal during update
       * WHEN: Component renders
       * THEN: Save button shows loading state
       */

      // WHEN: Render with isUpdating=true
      render(<EditGroupModal {...defaultProps} isUpdating={true} />);

      // THEN: Save button is disabled
      const saveButton = screen.getByRole('button', { name: /Save Changes/i });
      expect(saveButton).toBeDisabled();
    });
  });

  describe('status toggle', () => {
    it('[P1] toggles status when switch is clicked', async () => {
      /**
       * GIVEN: EditGroupModal with active group
       * WHEN: User clicks status toggle
       * THEN: Toggle switches to inactive
       */
      const user = userEvent.setup();

      // WHEN: Render and toggle
      render(<EditGroupModal {...defaultProps} />);
      const statusToggle = screen.getByRole('switch');
      await user.click(statusToggle);

      // THEN: Toggle is now unchecked
      expect(statusToggle).not.toBeChecked();
    });

    it('[P1] updates status label when toggled', async () => {
      /**
       * GIVEN: EditGroupModal with active group
       * WHEN: User toggles status
       * THEN: Status label updates
       */
      const user = userEvent.setup();

      // WHEN: Render and toggle
      render(<EditGroupModal {...defaultProps} />);

      // Initially shows Active
      expect(screen.getByText('Active')).toBeInTheDocument();

      await user.click(screen.getByRole('switch'));

      // THEN: Shows Inactive
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });
  });

  describe('form submission', () => {
    it('[P1] calls onUpdateGroup with only changed fields', async () => {
      /**
       * GIVEN: EditGroupModal with form
       * WHEN: User changes only the name
       * THEN: onUpdateGroup is called with only name field
       */
      const user = userEvent.setup();
      const onUpdateGroup = vi.fn().mockResolvedValue(undefined);

      // WHEN: Render and change name
      render(<EditGroupModal {...defaultProps} onUpdateGroup={onUpdateGroup} />);
      const nameInput = screen.getByLabelText(/Group Name/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Engineering Team');
      await user.click(screen.getByRole('button', { name: /Save Changes/i }));

      // THEN: onUpdateGroup called with only name
      await waitFor(() => {
        expect(onUpdateGroup).toHaveBeenCalledWith('group-1', {
          name: 'Engineering Team',
        });
      });
    });

    it('[P1] calls onUpdateGroup with status change', async () => {
      /**
       * GIVEN: EditGroupModal with active group
       * WHEN: User toggles status
       * THEN: onUpdateGroup includes is_active change
       */
      const user = userEvent.setup();
      const onUpdateGroup = vi.fn().mockResolvedValue(undefined);

      // WHEN: Render and toggle status
      render(<EditGroupModal {...defaultProps} onUpdateGroup={onUpdateGroup} />);
      await user.click(screen.getByRole('switch'));
      await user.click(screen.getByRole('button', { name: /Save Changes/i }));

      // THEN: onUpdateGroup called with is_active
      await waitFor(() => {
        expect(onUpdateGroup).toHaveBeenCalledWith('group-1', {
          is_active: false,
        });
      });
    });

    it('[P1] disables Save button when nothing changed', () => {
      /**
       * GIVEN: EditGroupModal without changes
       * WHEN: Component renders
       * THEN: Save button is disabled
       */
      const onUpdateGroup = vi.fn().mockResolvedValue(undefined);
      const onOpenChange = vi.fn();

      // WHEN: Render without making changes
      render(
        <EditGroupModal
          {...defaultProps}
          onUpdateGroup={onUpdateGroup}
          onOpenChange={onOpenChange}
        />
      );

      // THEN: Save button is disabled (isDirty is false)
      const saveButton = screen.getByRole('button', { name: /Save Changes/i });
      expect(saveButton).toBeDisabled();
    });

    it('[P1] closes modal after successful update', async () => {
      /**
       * GIVEN: EditGroupModal with changes
       * WHEN: User saves changes
       * THEN: Modal closes
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();
      const onUpdateGroup = vi.fn().mockResolvedValue(undefined);

      // WHEN: Render and make changes
      render(
        <EditGroupModal
          {...defaultProps}
          onOpenChange={onOpenChange}
          onUpdateGroup={onUpdateGroup}
        />
      );
      await user.click(screen.getByRole('switch'));
      await user.click(screen.getByRole('button', { name: /Save Changes/i }));

      // THEN: Modal closes
      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(false);
      });
    });
  });

  describe('validation', () => {
    it('[P1] shows error when name is cleared', async () => {
      /**
       * GIVEN: EditGroupModal with form
       * WHEN: User clears name field
       * THEN: Validation error is displayed
       */
      const user = userEvent.setup();

      // WHEN: Render and clear name
      render(<EditGroupModal {...defaultProps} />);
      const nameInput = screen.getByLabelText(/Group Name/i);
      await user.clear(nameInput);
      await user.click(screen.getByRole('button', { name: /Save Changes/i }));

      // THEN: Error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/Group name is required/i)).toBeInTheDocument();
      });
    });
  });

  describe('error handling', () => {
    it('[P2] displays error message when update fails', async () => {
      /**
       * GIVEN: EditGroupModal where update will fail
       * WHEN: User saves changes
       * THEN: Error message is displayed
       */
      const user = userEvent.setup();
      const onUpdateGroup = vi
        .fn()
        .mockRejectedValue(new Error('A group with this name already exists'));

      // WHEN: Render and try to update
      render(<EditGroupModal {...defaultProps} onUpdateGroup={onUpdateGroup} />);
      const nameInput = screen.getByLabelText(/Group Name/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Existing Group');
      await user.click(screen.getByRole('button', { name: /Save Changes/i }));

      // THEN: Error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/already exists/i)).toBeInTheDocument();
      });
    });
  });

  describe('cancel behavior', () => {
    it('[P1] closes modal when cancel is clicked', async () => {
      /**
       * GIVEN: EditGroupModal is open
       * WHEN: User clicks Cancel
       * THEN: Modal closes
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      // WHEN: Render and click Cancel
      render(<EditGroupModal {...defaultProps} onOpenChange={onOpenChange} />);
      await user.click(screen.getByRole('button', { name: /Cancel/i }));

      // THEN: Modal closes
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });
});
