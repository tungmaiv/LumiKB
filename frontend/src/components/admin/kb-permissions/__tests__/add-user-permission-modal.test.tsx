/**
 * Unit tests for AddUserPermissionModal component
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.2)
 *
 * Test Coverage:
 * - [P1] Rendering: Modal displays with user list
 * - [P1] User selection: Click to select user
 * - [P1] Search: Filter users by email
 * - [P1] Submit: Grant permission with selected user and level
 * - [P2] Validation: Error when no user selected
 * - [P2] Loading state: Shows loading indicator
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Component testing patterns
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AddUserPermissionModal } from '../add-user-permission-modal';
import type { UserRead, PermissionLevel } from '@/types/user';

// Test data
const mockUsers: UserRead[] = [
  {
    id: 'user-1',
    email: 'alice@example.com',
    is_active: true,
    is_superuser: false,
    is_verified: true,
    permission_level: 1 as PermissionLevel, // User
    created_at: '2025-01-01T00:00:00Z',
    onboarding_completed: true,
    last_active: '2025-01-01T00:00:00Z',
  },
  {
    id: 'user-2',
    email: 'bob@example.com',
    is_active: true,
    is_superuser: true,
    is_verified: true,
    permission_level: 3 as PermissionLevel, // Administrator
    created_at: '2025-01-01T00:00:00Z',
    onboarding_completed: true,
    last_active: '2025-01-01T00:00:00Z',
  },
  {
    id: 'user-3',
    email: 'charlie@example.com',
    is_active: true,
    is_superuser: false,
    is_verified: true,
    permission_level: 1 as PermissionLevel, // User
    created_at: '2025-01-01T00:00:00Z',
    onboarding_completed: true,
    last_active: '2025-01-01T00:00:00Z',
  },
];

describe('AddUserPermissionModal', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    onGrantPermission: vi.fn().mockResolvedValue(undefined),
    isGranting: false,
    users: mockUsers,
    usersLoading: false,
    existingUserIds: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('[P1] should render modal with title and description', () => {
      /**
       * GIVEN: Modal is open
       * WHEN: Component renders
       * THEN: Title and description are displayed
       */
      render(<AddUserPermissionModal {...defaultProps} />);

      expect(screen.getByText('Add User Permission')).toBeInTheDocument();
      expect(screen.getByText(/Grant a user access to this Knowledge Base/)).toBeInTheDocument();
    });

    it('[P1] should render all available users in list', () => {
      /**
       * GIVEN: Users array provided
       * WHEN: Modal renders
       * THEN: All users are displayed
       */
      render(<AddUserPermissionModal {...defaultProps} />);

      expect(screen.getByText('alice@example.com')).toBeInTheDocument();
      expect(screen.getByText('bob@example.com')).toBeInTheDocument();
      expect(screen.getByText('charlie@example.com')).toBeInTheDocument();
    });

    it('[P1] should exclude users with existing permissions', () => {
      /**
       * GIVEN: Some users already have permissions
       * WHEN: Modal renders
       * THEN: Those users are not shown
       */
      render(<AddUserPermissionModal {...defaultProps} existingUserIds={['user-1', 'user-3']} />);

      expect(screen.queryByText('alice@example.com')).not.toBeInTheDocument();
      expect(screen.getByText('bob@example.com')).toBeInTheDocument();
      expect(screen.queryByText('charlie@example.com')).not.toBeInTheDocument();
    });
  });

  describe('loading state', () => {
    it('[P2] should show loading indicator when loading users', () => {
      /**
       * GIVEN: Users are being loaded
       * WHEN: Modal renders
       * THEN: Loading message is displayed
       */
      render(<AddUserPermissionModal {...defaultProps} usersLoading={true} />);

      expect(screen.getByText('Loading users...')).toBeInTheDocument();
    });
  });

  describe('user selection', () => {
    it('[P1] should select user when clicked', async () => {
      /**
       * GIVEN: User list displayed
       * WHEN: User clicks on a user
       * THEN: User is selected and shown in selection text
       */
      const user = userEvent.setup();
      render(<AddUserPermissionModal {...defaultProps} />);

      const aliceButton = screen.getByText('alice@example.com').closest('button');
      await user.click(aliceButton!);

      // Check that selection is shown
      expect(screen.getByText(/Selected:/)).toBeInTheDocument();
    });
  });

  describe('search', () => {
    it('[P1] should filter users by search query', async () => {
      /**
       * GIVEN: Users displayed
       * WHEN: User types in search
       * THEN: Only matching users are shown
       */
      const user = userEvent.setup();
      render(<AddUserPermissionModal {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText('Search by email...');
      await user.type(searchInput, 'alice');

      expect(screen.getByText('alice@example.com')).toBeInTheDocument();
      expect(screen.queryByText('bob@example.com')).not.toBeInTheDocument();
      expect(screen.queryByText('charlie@example.com')).not.toBeInTheDocument();
    });

    it('[P2] should show no results message when search finds nothing', async () => {
      /**
       * GIVEN: Users displayed
       * WHEN: User searches for non-existent email
       * THEN: No results message shown
       */
      const user = userEvent.setup();
      render(<AddUserPermissionModal {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText('Search by email...');
      await user.type(searchInput, 'nonexistent');

      expect(screen.getByText('No users found matching your search')).toBeInTheDocument();
    });
  });

  describe('form submission', () => {
    it('[P1] should call onGrantPermission with selected user and level', async () => {
      /**
       * GIVEN: User selected and permission level set
       * WHEN: Form is submitted
       * THEN: onGrantPermission is called with correct data
       */
      const user = userEvent.setup();
      const onGrantPermission = vi.fn().mockResolvedValue(undefined);
      render(<AddUserPermissionModal {...defaultProps} onGrantPermission={onGrantPermission} />);

      // Select a user
      const aliceButton = screen.getByText('alice@example.com').closest('button');
      await user.click(aliceButton!);

      // Submit form
      const submitButton = screen.getByText('Grant Permission');
      await user.click(submitButton);

      await waitFor(() => {
        expect(onGrantPermission).toHaveBeenCalledWith({
          user_id: 'user-1',
          permission_level: 'READ', // default
        });
      });
    });

    it('[P2] should show error when submitting without user selection', async () => {
      /**
       * GIVEN: No user selected
       * WHEN: Form is submitted
       * THEN: Error message is shown
       */
      const user = userEvent.setup();
      render(<AddUserPermissionModal {...defaultProps} />);

      // Submit button should be disabled when no user selected
      const submitButton = screen.getByText('Grant Permission');
      expect(submitButton).toBeDisabled();
    });

    it('[P1] should close modal on successful submission', async () => {
      /**
       * GIVEN: Valid user selection
       * WHEN: Form is submitted successfully
       * THEN: Modal closes
       */
      const user = userEvent.setup();
      const onOpenChange = vi.fn();
      render(<AddUserPermissionModal {...defaultProps} onOpenChange={onOpenChange} />);

      // Select a user
      const aliceButton = screen.getByText('alice@example.com').closest('button');
      await user.click(aliceButton!);

      // Submit form
      const submitButton = screen.getByText('Grant Permission');
      await user.click(submitButton);

      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(false);
      });
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
      render(<AddUserPermissionModal {...defaultProps} onOpenChange={onOpenChange} />);

      const cancelButton = screen.getByText('Cancel');
      await user.click(cancelButton);

      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });
});
