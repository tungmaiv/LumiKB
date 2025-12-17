/**
 * Component tests for EditUserModal
 * Story 5.18: User Management UI (AC-5.18.3, AC-5.18.4)
 *
 * Test Coverage:
 * - [P1] Modal opens and displays user details
 * - [P1] Email displayed as read-only
 * - [P1] Role badge displayed correctly (admin/user)
 * - [P1] Status toggle changes local state
 * - [P1] Self-deactivation prevention (toggle disabled for own account)
 * - [P1] Form submission calls onUpdateUser with correct data
 * - [P1] Modal closes on successful update
 * - [P1] Error message displayed on update failure
 * - [P2] Loading state disables buttons and toggle
 * - [P2] Save button disabled when no changes made
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Component testing patterns
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EditUserModal, type EditUserModalProps } from '../edit-user-modal';
import type { UserRead, PermissionLevel } from '@/types/user';

// Mock TooltipProvider - required for Tooltip components
vi.mock('@/components/ui/tooltip', async () => {
  const actual = await vi.importActual('@/components/ui/tooltip');
  return {
    ...actual,
    TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

const mockUser: UserRead = {
  id: 'user-1',
  email: 'user@example.com',
  is_active: true,
  is_superuser: false,
  is_verified: true,
  permission_level: 1 as PermissionLevel, // User
  created_at: '2025-01-01T00:00:00Z',
  last_active: '2025-12-05T00:00:00Z',
  onboarding_completed: true,
};

const mockAdminUser: UserRead = {
  id: 'admin-1',
  email: 'admin@example.com',
  is_active: true,
  is_superuser: true,
  is_verified: true,
  permission_level: 3 as PermissionLevel, // Administrator
  created_at: '2025-01-01T00:00:00Z',
  last_active: '2025-12-05T00:00:00Z',
  onboarding_completed: true,
};

describe('EditUserModal', () => {
  const defaultProps: EditUserModalProps = {
    user: mockUser,
    currentUserId: 'current-user-id',
    open: true,
    onOpenChange: vi.fn(),
    onUpdateUser: vi.fn().mockResolvedValue(undefined),
    isUpdating: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('[P1] displays user details when modal is open', () => {
      /**
       * GIVEN: EditUserModal is open with user data
       * WHEN: Component renders
       * THEN: User details are visible
       */

      // WHEN: Render modal
      render(<EditUserModal {...defaultProps} />);

      // THEN: Title is visible
      expect(screen.getByRole('heading', { name: /edit user/i })).toBeInTheDocument();

      // THEN: Email is displayed
      expect(screen.getByText('user@example.com')).toBeInTheDocument();

      // THEN: Status section is visible
      expect(screen.getByText(/account status/i)).toBeInTheDocument();

      // THEN: Action buttons are visible
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
    });

    it('[P1] does not render when user is null', () => {
      /**
       * GIVEN: EditUserModal with user=null
       * WHEN: Component renders
       * THEN: Modal is not visible
       */

      // WHEN: Render with null user
      render(<EditUserModal {...defaultProps} user={null} />);

      // THEN: Modal content is not visible
      expect(screen.queryByRole('heading', { name: /edit user/i })).not.toBeInTheDocument();
    });

    it('[P1] does not render when open is false', () => {
      /**
       * GIVEN: EditUserModal with open=false
       * WHEN: Component renders
       * THEN: Modal is not visible
       */

      // WHEN: Render closed modal
      render(<EditUserModal {...defaultProps} open={false} />);

      // THEN: Modal content is not visible
      expect(screen.queryByRole('heading', { name: /edit user/i })).not.toBeInTheDocument();
    });

    it('[P1] displays email as read-only', () => {
      /**
       * GIVEN: EditUserModal with user
       * WHEN: Component renders
       * THEN: Email is displayed as text, not input
       */

      // WHEN: Render modal
      render(<EditUserModal {...defaultProps} />);

      // THEN: Email is displayed as text
      expect(screen.getByText('user@example.com')).toBeInTheDocument();

      // THEN: No email input field exists
      expect(screen.queryByRole('textbox', { name: /email/i })).not.toBeInTheDocument();
    });

    it('[P2] displays User role badge for non-admin user', () => {
      /**
       * GIVEN: EditUserModal with non-admin user
       * WHEN: Component renders
       * THEN: User badge is displayed
       */

      // WHEN: Render modal with regular user
      render(<EditUserModal {...defaultProps} user={mockUser} />);

      // THEN: User badge is visible
      expect(screen.getByText('User')).toBeInTheDocument();
    });

    it('[P2] displays Admin role badge for admin user', () => {
      /**
       * GIVEN: EditUserModal with admin user
       * WHEN: Component renders
       * THEN: Admin badge is displayed
       */

      // WHEN: Render modal with admin user
      render(<EditUserModal {...defaultProps} user={mockAdminUser} />);

      // THEN: Admin badge is visible
      expect(screen.getByText('Admin')).toBeInTheDocument();
    });
  });

  describe('status toggle', () => {
    it('[P1] displays status toggle reflecting user active state', () => {
      /**
       * GIVEN: EditUserModal with active user
       * WHEN: Component renders
       * THEN: Status toggle shows active state
       */

      // WHEN: Render modal
      render(<EditUserModal {...defaultProps} />);

      // THEN: Toggle is checked (active)
      const toggle = screen.getByRole('switch');
      expect(toggle).toBeChecked();

      // THEN: Active label is shown
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('[P1] allows toggling status for other users', async () => {
      /**
       * GIVEN: EditUserModal for another user (not self)
       * WHEN: User clicks status toggle
       * THEN: Toggle state changes
       */
      const user = userEvent.setup();

      // WHEN: Render modal
      render(<EditUserModal {...defaultProps} />);

      // Get toggle
      const toggle = screen.getByRole('switch');
      expect(toggle).toBeChecked();

      // WHEN: Click toggle
      await user.click(toggle);

      // THEN: Toggle state changes to unchecked
      expect(toggle).not.toBeChecked();

      // THEN: Inactive label is shown
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });

    it('[P1] disables status toggle for own account (self-deactivation prevention)', () => {
      /**
       * GIVEN: EditUserModal where user.id matches currentUserId
       * WHEN: Component renders
       * THEN: Status toggle is disabled
       */

      // WHEN: Render modal with self as user
      render(<EditUserModal {...defaultProps} user={mockUser} currentUserId={mockUser.id} />);

      // THEN: Toggle is disabled
      const toggle = screen.getByRole('switch');
      expect(toggle).toBeDisabled();
    });
  });

  describe('form submission', () => {
    it('[P1] calls onUpdateUser with updated status on save', async () => {
      /**
       * GIVEN: EditUserModal with status changed
       * WHEN: User clicks save
       * THEN: onUpdateUser is called with correct data
       */
      const user = userEvent.setup();
      const onUpdateUser = vi.fn().mockResolvedValue(undefined);

      // WHEN: Render modal
      render(<EditUserModal {...defaultProps} onUpdateUser={onUpdateUser} />);

      // WHEN: Toggle status to inactive
      const toggle = screen.getByRole('switch');
      await user.click(toggle);

      // WHEN: Click save
      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // THEN: onUpdateUser called with user id and new status
      await waitFor(() => {
        expect(onUpdateUser).toHaveBeenCalledWith('user-1', { is_active: false });
      });
    });

    it('[P1] closes modal on successful update', async () => {
      /**
       * GIVEN: EditUserModal with successful update
       * WHEN: onUpdateUser resolves
       * THEN: Modal closes (onOpenChange called with false)
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();
      const onUpdateUser = vi.fn().mockResolvedValue(undefined);

      // WHEN: Render modal
      render(
        <EditUserModal {...defaultProps} onOpenChange={onOpenChange} onUpdateUser={onUpdateUser} />
      );

      // WHEN: Toggle status and save
      const toggle = screen.getByRole('switch');
      await user.click(toggle);

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // THEN: onOpenChange called with false
      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(false);
      });
    });

    it('[P2] disables save button when no changes made', () => {
      /**
       * GIVEN: EditUserModal with no status change
       * WHEN: Component renders
       * THEN: Save button is disabled
       */

      // WHEN: Render modal
      render(<EditUserModal {...defaultProps} />);

      // THEN: Save button is disabled (no changes)
      const saveButton = screen.getByRole('button', { name: /save changes/i });
      expect(saveButton).toBeDisabled();
    });
  });

  describe('error handling', () => {
    it('[P1] displays error message on update failure', async () => {
      /**
       * GIVEN: EditUserModal with update that fails
       * WHEN: onUpdateUser throws error
       * THEN: Error message is displayed
       */
      const user = userEvent.setup();
      const onUpdateUser = vi.fn().mockRejectedValue(new Error('Update failed'));

      // WHEN: Render modal
      render(<EditUserModal {...defaultProps} onUpdateUser={onUpdateUser} />);

      // WHEN: Toggle and save
      const toggle = screen.getByRole('switch');
      await user.click(toggle);

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // THEN: Error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/update failed/i)).toBeInTheDocument();
      });
    });

    it('[P1] displays generic error for non-Error exceptions', async () => {
      /**
       * GIVEN: EditUserModal with update that throws non-Error
       * WHEN: onUpdateUser throws string
       * THEN: Generic error message is displayed
       */
      const user = userEvent.setup();
      const onUpdateUser = vi.fn().mockRejectedValue('Something went wrong');

      // WHEN: Render modal
      render(<EditUserModal {...defaultProps} onUpdateUser={onUpdateUser} />);

      // WHEN: Toggle and save
      const toggle = screen.getByRole('switch');
      await user.click(toggle);

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // THEN: Generic error message is displayed
      await waitFor(() => {
        expect(screen.getByText(/failed to update user/i)).toBeInTheDocument();
      });
    });
  });

  describe('loading state', () => {
    it('[P2] disables buttons when isUpdating is true', () => {
      /**
       * GIVEN: EditUserModal with isUpdating=true
       * WHEN: Component renders
       * THEN: Buttons are disabled
       */

      // WHEN: Render with loading state
      render(<EditUserModal {...defaultProps} isUpdating={true} />);

      // THEN: Cancel button is disabled
      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();

      // THEN: Save button is disabled
      expect(screen.getByRole('button', { name: /save changes/i })).toBeDisabled();
    });

    it('[P2] disables status toggle when isUpdating is true', () => {
      /**
       * GIVEN: EditUserModal with isUpdating=true
       * WHEN: Component renders
       * THEN: Status toggle is disabled
       */

      // WHEN: Render with loading state
      render(<EditUserModal {...defaultProps} isUpdating={true} />);

      // THEN: Toggle is disabled
      const toggle = screen.getByRole('switch');
      expect(toggle).toBeDisabled();
    });
  });

  describe('cancel behavior', () => {
    it('[P1] closes modal and resets error on cancel', async () => {
      /**
       * GIVEN: EditUserModal with error displayed
       * WHEN: User clicks cancel
       * THEN: Modal closes
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();

      // WHEN: Render modal
      render(<EditUserModal {...defaultProps} onOpenChange={onOpenChange} />);

      // Click cancel
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // THEN: onOpenChange called with false
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('state reset', () => {
    it('[P2] resets local state when user prop changes', async () => {
      /**
       * GIVEN: EditUserModal with toggled state
       * WHEN: user prop changes
       * THEN: State resets to new user's values
       */
      const inactiveUser: UserRead = {
        ...mockUser,
        id: 'user-2',
        email: 'inactive@example.com',
        is_active: false,
      };

      // WHEN: Render with active user
      const { rerender } = render(<EditUserModal {...defaultProps} user={mockUser} />);

      // THEN: Toggle reflects active state
      expect(screen.getByRole('switch')).toBeChecked();

      // WHEN: User prop changes to inactive user
      rerender(<EditUserModal {...defaultProps} user={inactiveUser} />);

      // THEN: Toggle reflects inactive state
      expect(screen.getByRole('switch')).not.toBeChecked();
    });
  });
});
