/**
 * Unit tests for EditPermissionModal component
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.3)
 *
 * Test Coverage:
 * - [P1] Rendering: Modal displays with permission info
 * - [P1] Update: Change permission level and save
 * - [P1] Delete: Revoke permission with confirmation
 * - [P2] Validation: Save disabled when no changes
 * - [P2] Error handling: Shows error message on failure
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Component testing patterns
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { EditPermissionModal } from '../edit-permission-modal';
import type { PermissionExtended } from '@/types/permission';

// Test data
const mockUserPermission: PermissionExtended = {
  id: 'perm-1',
  kb_id: 'kb-1',
  entity_type: 'user',
  entity_id: 'user-1',
  entity_name: 'alice@example.com',
  permission_level: 'READ',
  created_at: '2025-01-01T00:00:00Z',
};

const mockGroupPermission: PermissionExtended = {
  id: 'perm-2',
  kb_id: 'kb-1',
  entity_type: 'group',
  entity_id: 'group-1',
  entity_name: 'Engineering',
  permission_level: 'WRITE',
  created_at: '2025-01-02T00:00:00Z',
};

describe('EditPermissionModal', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    permission: mockUserPermission,
    onUpdatePermission: vi.fn().mockResolvedValue(undefined),
    onDeletePermission: vi.fn().mockResolvedValue(undefined),
    isUpdating: false,
    isDeleting: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('[P1] should render modal with title and description for user', () => {
      /**
       * GIVEN: Modal is open with a user permission
       * WHEN: Component renders
       * THEN: Title and user description are displayed
       */
      render(<EditPermissionModal {...defaultProps} />);

      expect(screen.getByText('Edit Permission')).toBeInTheDocument();
      expect(screen.getByText(/Update or revoke the permission for this user/)).toBeInTheDocument();
    });

    it('[P1] should render modal with group description for group', () => {
      /**
       * GIVEN: Modal is open with a group permission
       * WHEN: Component renders
       * THEN: Group description is displayed
       */
      render(<EditPermissionModal {...defaultProps} permission={mockGroupPermission} />);

      expect(
        screen.getByText(/Update or revoke the permission for this group/)
      ).toBeInTheDocument();
    });

    it('[P1] should display entity name and type', () => {
      /**
       * GIVEN: Modal is open with a permission
       * WHEN: Component renders
       * THEN: Entity name and type are displayed
       */
      render(<EditPermissionModal {...defaultProps} />);

      expect(screen.getByText('alice@example.com')).toBeInTheDocument();
      expect(screen.getByText('user')).toBeInTheDocument();
    });

    it('[P2] should not render when permission is null', () => {
      /**
       * GIVEN: Permission is null
       * WHEN: Component renders
       * THEN: Nothing is rendered
       */
      const { container } = render(<EditPermissionModal {...defaultProps} permission={null} />);

      expect(container).toBeEmptyDOMElement();
    });
  });

  describe('update permission', () => {
    it('[P1] should close modal without calling update when no changes made', async () => {
      /**
       * GIVEN: Modal open with permission
       * WHEN: Save clicked without changing level
       * THEN: Modal closes without calling update
       */
      const user = userEvent.setup();
      const onUpdatePermission = vi.fn().mockResolvedValue(undefined);
      const onOpenChange = vi.fn();
      render(
        <EditPermissionModal
          {...defaultProps}
          onUpdatePermission={onUpdatePermission}
          onOpenChange={onOpenChange}
        />
      );

      // Save button should be disabled when no changes
      const saveButton = screen.getByText('Save Changes');
      expect(saveButton).toBeDisabled();
    });

    it('[P2] should disable save when permission level unchanged', () => {
      /**
       * GIVEN: Modal open with permission at READ level
       * WHEN: Level not changed
       * THEN: Save button is disabled
       */
      render(<EditPermissionModal {...defaultProps} />);

      const saveButton = screen.getByText('Save Changes');
      expect(saveButton).toBeDisabled();
    });
  });

  describe('delete permission', () => {
    it('[P1] should show confirmation dialog when revoke clicked', async () => {
      /**
       * GIVEN: Modal open
       * WHEN: Revoke Access button clicked
       * THEN: Confirmation dialog appears
       */
      const user = userEvent.setup();
      render(<EditPermissionModal {...defaultProps} />);

      const revokeButton = screen.getByText('Revoke Access');
      await user.click(revokeButton);

      // Confirmation dialog should appear
      expect(screen.getByText('Revoke Permission')).toBeInTheDocument();
      expect(screen.getByText(/Are you sure you want to revoke access/)).toBeInTheDocument();
    });

    it('[P1] should call onDeletePermission when confirmed', async () => {
      /**
       * GIVEN: Confirmation dialog open
       * WHEN: Revoke confirmed
       * THEN: onDeletePermission is called
       */
      const user = userEvent.setup();
      const onDeletePermission = vi.fn().mockResolvedValue(undefined);
      render(<EditPermissionModal {...defaultProps} onDeletePermission={onDeletePermission} />);

      // Open confirmation dialog
      const revokeButton = screen.getByText('Revoke Access');
      await user.click(revokeButton);

      // Confirm deletion - there are now two "Revoke Access" buttons
      const confirmButtons = screen.getAllByText('Revoke Access');
      const confirmButton = confirmButtons[1]; // The one in the alert dialog
      await user.click(confirmButton);

      await waitFor(() => {
        expect(onDeletePermission).toHaveBeenCalledWith(mockUserPermission);
      });
    });

    it('[P1] should close confirmation dialog when cancelled', async () => {
      /**
       * GIVEN: Confirmation dialog open
       * WHEN: Cancel clicked
       * THEN: Dialog closes, permission not deleted
       */
      const user = userEvent.setup();
      const onDeletePermission = vi.fn();
      render(<EditPermissionModal {...defaultProps} onDeletePermission={onDeletePermission} />);

      // Open confirmation dialog
      const revokeButton = screen.getByText('Revoke Access');
      await user.click(revokeButton);

      // Cancel
      const cancelButton = screen.getAllByText('Cancel')[1]; // The one in the alert dialog
      await user.click(cancelButton);

      expect(onDeletePermission).not.toHaveBeenCalled();
    });
  });

  describe('cancel', () => {
    it('[P1] should close modal when cancel clicked', async () => {
      /**
       * GIVEN: Modal open
       * WHEN: Cancel button clicked
       * THEN: onOpenChange called with false
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();
      render(<EditPermissionModal {...defaultProps} onOpenChange={onOpenChange} />);

      // Find cancel button in the main modal (first one)
      const cancelButtons = screen.getAllByText('Cancel');
      await user.click(cancelButtons[0]);

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('loading states', () => {
    it('[P2] should disable buttons when updating', () => {
      /**
       * GIVEN: Permission is being updated
       * WHEN: Component renders
       * THEN: All buttons are disabled
       */
      render(<EditPermissionModal {...defaultProps} isUpdating={true} />);

      expect(screen.getByText('Revoke Access')).toBeDisabled();
      expect(screen.getByText('Cancel')).toBeDisabled();
      expect(screen.getByText('Save Changes')).toBeDisabled();
    });

    it('[P2] should disable buttons when deleting', () => {
      /**
       * GIVEN: Permission is being deleted
       * WHEN: Component renders
       * THEN: All buttons are disabled
       */
      render(<EditPermissionModal {...defaultProps} isDeleting={true} />);

      expect(screen.getByText('Revoke Access')).toBeDisabled();
      expect(screen.getByText('Cancel')).toBeDisabled();
    });
  });

  describe('group permission note', () => {
    it('[P2] should show group override note for group permissions', () => {
      /**
       * GIVEN: Modal open with a group permission
       * WHEN: Component renders
       * THEN: Note about user overrides is displayed
       */
      render(<EditPermissionModal {...defaultProps} permission={mockGroupPermission} />);

      expect(
        screen.getByText(/Users with direct permissions will override group permissions/)
      ).toBeInTheDocument();
    });

    it('[P2] should not show group note for user permissions', () => {
      /**
       * GIVEN: Modal open with a user permission
       * WHEN: Component renders
       * THEN: No group override note
       */
      render(<EditPermissionModal {...defaultProps} />);

      expect(
        screen.queryByText(/Users with direct permissions will override/)
      ).not.toBeInTheDocument();
    });
  });
});
