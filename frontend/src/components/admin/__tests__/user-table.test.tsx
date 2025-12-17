/**
 * Component tests for UserTable
 * Story 5.18: User Management UI (AC-5.18.1)
 *
 * Test Coverage:
 * - [P1] Table renders with user data and correct columns
 * - [P1] Client-side sorting by column click
 * - [P1] Email search/filter with debounce
 * - [P1] Pagination controls work correctly
 * - [P1] Empty state displays when no users
 * - [P1] Loading state displays spinner
 * - [P2] Status badges show correct colors
 * - [P2] Role badges show correct colors
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Component testing patterns
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserTable, type UserTableProps } from '../user-table';
import type { UserRead, PaginationMeta, PermissionLevel } from '@/types/user';

// Mock user data
const mockUsers: UserRead[] = [
  {
    id: 'user-1',
    email: 'admin@example.com',
    is_active: true,
    is_superuser: true,
    is_verified: true,
    permission_level: 3 as PermissionLevel, // Administrator
    created_at: '2025-01-01T00:00:00Z',
    last_active: '2025-12-05T00:00:00Z',
    onboarding_completed: true,
  },
  {
    id: 'user-2',
    email: 'user@example.com',
    is_active: true,
    is_superuser: false,
    is_verified: true,
    permission_level: 1 as PermissionLevel, // User
    created_at: '2025-01-15T00:00:00Z',
    last_active: '2025-12-04T00:00:00Z',
    onboarding_completed: true,
  },
  {
    id: 'user-3',
    email: 'inactive@example.com',
    is_active: false,
    is_superuser: false,
    is_verified: true,
    permission_level: 1 as PermissionLevel, // User
    created_at: '2025-02-01T00:00:00Z',
    last_active: null,
    onboarding_completed: false,
  },
];

const mockPagination: PaginationMeta = {
  total: 3,
  page: 1,
  per_page: 20,
  total_pages: 1,
};

describe('UserTable', () => {
  const defaultProps: UserTableProps = {
    users: mockUsers,
    pagination: mockPagination,
    isLoading: false,
    onPageChange: vi.fn(),
    onEditUser: vi.fn(),
    searchValue: '',
    onSearchChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('[P1] renders table with all users and correct columns', () => {
      /**
       * GIVEN: UserTable component with user data
       * WHEN: Component renders
       * THEN: All users are displayed with correct columns
       */

      // WHEN: Render component
      render(<UserTable {...defaultProps} />);

      // THEN: Table headers are visible
      expect(screen.getByRole('columnheader', { name: /email/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /status/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /role/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /created/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /last active/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /actions/i })).toBeInTheDocument();

      // THEN: All users are displayed
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
      expect(screen.getByText('user@example.com')).toBeInTheDocument();
      expect(screen.getByText('inactive@example.com')).toBeInTheDocument();
    });

    it('[P1] displays loading state with spinner', () => {
      /**
       * GIVEN: UserTable with isLoading=true
       * WHEN: Component renders
       * THEN: Loading spinner is displayed
       */

      // WHEN: Render with loading state
      render(<UserTable {...defaultProps} isLoading={true} />);

      // THEN: Loading message is visible
      expect(screen.getByText(/loading users/i)).toBeInTheDocument();

      // THEN: Table is not visible
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('[P1] displays empty state when no users', () => {
      /**
       * GIVEN: UserTable with empty users array
       * WHEN: Component renders
       * THEN: Empty state message is displayed
       */

      // WHEN: Render with no users
      render(<UserTable {...defaultProps} users={[]} />);

      // THEN: Empty state message is visible
      expect(screen.getByText(/no users found/i)).toBeInTheDocument();

      // THEN: Table is not visible
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('[P2] displays correct status badges for active/inactive users', () => {
      /**
       * GIVEN: UserTable with active and inactive users
       * WHEN: Component renders
       * THEN: Status badges show correct colors
       */

      // WHEN: Render component
      render(<UserTable {...defaultProps} />);

      // THEN: Active badges are present (2 active users)
      const activeBadges = screen.getAllByTestId('status-badge-active');
      expect(activeBadges).toHaveLength(2);

      // THEN: Inactive badge is present (1 inactive user)
      const inactiveBadges = screen.getAllByTestId('status-badge-inactive');
      expect(inactiveBadges).toHaveLength(1);
    });

    it('[P2] displays correct role badges for admin/user', () => {
      /**
       * GIVEN: UserTable with admin and regular users
       * WHEN: Component renders
       * THEN: Role badges show correct roles
       */

      // WHEN: Render component
      render(<UserTable {...defaultProps} />);

      // THEN: Admin badge is present (1 admin)
      const adminBadges = screen.getAllByTestId('role-badge-admin');
      expect(adminBadges).toHaveLength(1);

      // THEN: User badges are present (2 regular users)
      const userBadges = screen.getAllByTestId('role-badge-user');
      expect(userBadges).toHaveLength(2);
    });
  });

  describe('sorting', () => {
    it('[P1] sorts by email column when clicked', async () => {
      /**
       * GIVEN: UserTable with multiple users
       * WHEN: User clicks email column header
       * THEN: Table sorts by email
       */
      const user = userEvent.setup();

      // WHEN: Render component
      render(<UserTable {...defaultProps} />);

      // Get initial order (by created_at desc by default)
      const rows = screen.getAllByRole('row');

      // WHEN: Click email header to sort ascending
      const emailHeader = screen.getByRole('columnheader', { name: /email/i });
      await user.click(emailHeader);

      // THEN: Rows should be reordered by email ascending
      const sortedRows = screen.getAllByRole('row');
      const firstDataRow = sortedRows[1]; // Skip header row
      expect(within(firstDataRow).getByText('admin@example.com')).toBeInTheDocument();
    });

    it('[P1] toggles sort direction on repeated click', async () => {
      /**
       * GIVEN: UserTable sorted by email ascending
       * WHEN: User clicks email column header again
       * THEN: Sort direction toggles to descending
       */
      const user = userEvent.setup();

      // WHEN: Render component
      render(<UserTable {...defaultProps} />);

      const emailHeader = screen.getByRole('columnheader', { name: /email/i });

      // Click once for ascending
      await user.click(emailHeader);

      // Click again for descending
      await user.click(emailHeader);

      // THEN: Sort icon should indicate descending
      // Verify by checking the order - 'user@' should come before 'inactive@' before 'admin@' in desc
      const rows = screen.getAllByRole('row');
      const firstDataRow = rows[1];
      expect(within(firstDataRow).getByText('user@example.com')).toBeInTheDocument();
    });
  });

  describe('filtering', () => {
    it('[P1] calls onSearchChange when typing in search input', async () => {
      /**
       * GIVEN: UserTable with search functionality
       * WHEN: User enters search term
       * THEN: onSearchChange is called with input value
       */
      const user = userEvent.setup();
      const onSearchChange = vi.fn();

      // WHEN: Render component
      render(<UserTable {...defaultProps} onSearchChange={onSearchChange} />);

      // WHEN: Type in search input (type a single character)
      const searchInput = screen.getByPlaceholderText(/search by email/i);
      await user.type(searchInput, 'a');

      // THEN: onSearchChange is called
      expect(onSearchChange).toHaveBeenCalled();
      // The handler should be called with the full input value
      expect(onSearchChange).toHaveBeenCalledWith('a');
    });

    it('[P1] shows filtered results based on searchValue prop', () => {
      /**
       * GIVEN: UserTable with searchValue set
       * WHEN: Component renders
       * THEN: Only matching users are displayed
       */

      // WHEN: Render with search filter
      render(<UserTable {...defaultProps} searchValue="admin" />);

      // THEN: Only admin user is visible
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
      expect(screen.queryByText('user@example.com')).not.toBeInTheDocument();
      expect(screen.queryByText('inactive@example.com')).not.toBeInTheDocument();
    });

    it('[P1] shows empty state when search has no matches', () => {
      /**
       * GIVEN: UserTable with search term that matches no users
       * WHEN: Component renders
       * THEN: Empty state with search hint is displayed
       */

      // WHEN: Render with non-matching search
      render(<UserTable {...defaultProps} searchValue="nonexistent" />);

      // THEN: Empty state message is visible
      expect(screen.getByText(/no users found/i)).toBeInTheDocument();
      expect(screen.getByText(/try adjusting your search/i)).toBeInTheDocument();
    });
  });

  describe('pagination', () => {
    it('[P1] displays pagination info correctly', () => {
      /**
       * GIVEN: UserTable with pagination data
       * WHEN: Component renders
       * THEN: Pagination info shows correct counts
       */

      // WHEN: Render component
      render(<UserTable {...defaultProps} />);

      // THEN: Pagination info is displayed
      expect(screen.getByText(/showing/i)).toBeInTheDocument();
      // Check that pagination controls exist
      expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
    });

    it('[P1] disables previous button on first page', () => {
      /**
       * GIVEN: UserTable on first page
       * WHEN: Component renders
       * THEN: Previous button is disabled
       */

      // WHEN: Render on first page
      render(<UserTable {...defaultProps} />);

      // THEN: Previous button is disabled
      const prevButton = screen.getByRole('button', { name: /previous/i });
      expect(prevButton).toBeDisabled();
    });

    it('[P1] enables next button when more pages exist', () => {
      /**
       * GIVEN: UserTable with multiple pages
       * WHEN: Component renders
       * THEN: Next button is enabled
       */
      const multiPagePagination: PaginationMeta = {
        total: 45,
        page: 1,
        per_page: 20,
        total_pages: 3,
      };

      // WHEN: Render with multiple pages
      render(<UserTable {...defaultProps} pagination={multiPagePagination} />);

      // THEN: Next button is enabled
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeEnabled();
    });

    it('[P1] calls onPageChange when next is clicked', async () => {
      /**
       * GIVEN: UserTable with multiple pages
       * WHEN: User clicks next button
       * THEN: onPageChange is called with next page number
       */
      const user = userEvent.setup();
      const onPageChange = vi.fn();
      const multiPagePagination: PaginationMeta = {
        total: 45,
        page: 1,
        per_page: 20,
        total_pages: 3,
      };

      // WHEN: Render and click next
      render(
        <UserTable {...defaultProps} pagination={multiPagePagination} onPageChange={onPageChange} />
      );

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      // THEN: onPageChange called with page 2
      expect(onPageChange).toHaveBeenCalledWith(2);
    });
  });

  describe('actions', () => {
    it('[P1] calls onEditUser when edit button is clicked', async () => {
      /**
       * GIVEN: UserTable with edit buttons
       * WHEN: User clicks edit button for a user
       * THEN: onEditUser is called with that user
       */
      const user = userEvent.setup();
      const onEditUser = vi.fn();

      // WHEN: Render component
      render(<UserTable {...defaultProps} onEditUser={onEditUser} />);

      // Find the row with admin@example.com and click its edit button
      // Note: Default sort is created_at desc, so we click within a specific row
      const adminRow = screen.getByText('admin@example.com').closest('tr');
      const editButton = within(adminRow!).getByRole('button', { name: /edit/i });
      await user.click(editButton);

      // THEN: onEditUser called with admin user
      expect(onEditUser).toHaveBeenCalledWith(mockUsers[0]);
    });
  });

  describe('date formatting', () => {
    it('[P2] formats dates correctly', () => {
      /**
       * GIVEN: UserTable with users having dates
       * WHEN: Component renders
       * THEN: Dates are formatted correctly
       */

      // WHEN: Render component
      render(<UserTable {...defaultProps} />);

      // THEN: Dates are formatted (Jan 1, 2025 format)
      expect(screen.getByText('Jan 1, 2025')).toBeInTheDocument();
    });

    it('[P2] shows "Never" for null last_active', () => {
      /**
       * GIVEN: UserTable with user having null last_active
       * WHEN: Component renders
       * THEN: Shows "Never" for that user
       */

      // WHEN: Render component
      render(<UserTable {...defaultProps} />);

      // THEN: "Never" is displayed for inactive user
      expect(screen.getByText('Never')).toBeInTheDocument();
    });
  });
});
