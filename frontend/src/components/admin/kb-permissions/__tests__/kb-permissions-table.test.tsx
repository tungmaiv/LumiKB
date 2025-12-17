/**
 * Unit tests for KBPermissionsTable component
 * Story 5.20: Role & KB Permission Management UI (AC-5.20.1)
 *
 * Test Coverage:
 * - [P1] Rendering: Displays permissions table with columns
 * - [P1] Sorting: Click column headers to sort
 * - [P1] Search: Filter by name or type
 * - [P1] Pagination: Navigate between pages
 * - [P1] Actions: Edit and delete button callbacks
 * - [P2] Empty state: No permissions message
 * - [P2] Loading state: Shows loading indicator
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Component testing patterns
 */

import { render, screen, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { KBPermissionsTable } from '../kb-permissions-table';
import type { PermissionExtended } from '@/types/permission';

// Test data
const mockPermissions: PermissionExtended[] = [
  {
    id: 'perm-1',
    entity_type: 'user',
    entity_id: 'user-1',
    entity_name: 'alice@example.com',
    kb_id: 'kb-1',
    permission_level: 'READ',
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 'perm-2',
    entity_type: 'group',
    entity_id: 'group-1',
    entity_name: 'Engineering',
    kb_id: 'kb-1',
    permission_level: 'WRITE',
    created_at: '2025-01-15T00:00:00Z',
  },
  {
    id: 'perm-3',
    entity_type: 'user',
    entity_id: 'user-2',
    entity_name: 'bob@example.com',
    kb_id: 'kb-1',
    permission_level: 'ADMIN',
    created_at: '2025-01-20T00:00:00Z',
  },
];

describe('KBPermissionsTable', () => {
  const defaultProps = {
    permissions: mockPermissions,
    total: 3,
    page: 1,
    limit: 20,
    isLoading: false,
    onPageChange: vi.fn(),
    onLimitChange: vi.fn(),
    onEditPermission: vi.fn(),
    onDeletePermission: vi.fn(),
    searchValue: '',
    onSearchChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('[P1] should render table with all permission rows', () => {
      /**
       * GIVEN: Permissions data
       * WHEN: Component renders
       * THEN: All permissions are displayed in rows
       */
      render(<KBPermissionsTable {...defaultProps} />);

      expect(screen.getByText('alice@example.com')).toBeInTheDocument();
      expect(screen.getByText('Engineering')).toBeInTheDocument();
      expect(screen.getByText('bob@example.com')).toBeInTheDocument();
    });

    it('[P1] should render correct column headers', () => {
      /**
       * GIVEN: Table component
       * WHEN: Component renders
       * THEN: All column headers are visible
       */
      render(<KBPermissionsTable {...defaultProps} />);

      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Permission')).toBeInTheDocument();
      expect(screen.getByText('Granted')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('[P1] should display permission levels with badges', () => {
      /**
       * GIVEN: Permissions with different levels
       * WHEN: Component renders
       * THEN: Each level has a colored badge
       */
      render(<KBPermissionsTable {...defaultProps} />);

      expect(screen.getByText('READ')).toBeInTheDocument();
      expect(screen.getByText('WRITE')).toBeInTheDocument();
      expect(screen.getByText('ADMIN')).toBeInTheDocument();
    });

    it('[P1] should display user and group icons correctly', () => {
      /**
       * GIVEN: Mix of user and group permissions
       * WHEN: Component renders
       * THEN: User rows show "User" and group rows show "Group"
       */
      render(<KBPermissionsTable {...defaultProps} />);

      // Check for user and group labels
      const userLabels = screen.getAllByText('User');
      const groupLabels = screen.getAllByText('Group');

      expect(userLabels).toHaveLength(2); // alice and bob
      expect(groupLabels).toHaveLength(1); // Engineering
    });
  });

  describe('loading state', () => {
    it('[P2] should show loading indicator when loading', () => {
      /**
       * GIVEN: isLoading is true
       * WHEN: Component renders
       * THEN: Loading message is displayed
       */
      render(<KBPermissionsTable {...defaultProps} isLoading={true} />);

      expect(screen.getByText('Loading permissions...')).toBeInTheDocument();
    });
  });

  describe('empty state', () => {
    it('[P2] should show empty message when no permissions', () => {
      /**
       * GIVEN: Empty permissions array
       * WHEN: Component renders
       * THEN: No permissions message is displayed
       */
      render(<KBPermissionsTable {...defaultProps} permissions={[]} total={0} />);

      expect(screen.getByText('No permissions found')).toBeInTheDocument();
      expect(screen.getByText('Add users or groups to grant access')).toBeInTheDocument();
    });

    it('[P2] should show search suggestion when filtered to empty', () => {
      /**
       * GIVEN: Search term that filters out all results
       * WHEN: Component renders with search value
       * THEN: Suggests adjusting search term
       */
      render(
        <KBPermissionsTable
          {...defaultProps}
          permissions={[]}
          total={0}
          searchValue="nonexistent"
        />
      );

      expect(screen.getByText('No permissions found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search term')).toBeInTheDocument();
    });
  });

  describe('sorting', () => {
    it('[P1] should sort by name when clicking Name header', async () => {
      /**
       * GIVEN: Unsorted permissions table
       * WHEN: Name column header is clicked
       * THEN: Rows are sorted alphabetically by name
       */
      const user = userEvent.setup();
      render(<KBPermissionsTable {...defaultProps} />);

      const nameHeader = screen.getByText('Name');
      await user.click(nameHeader);

      // After sorting by name ascending, alice should be first
      const rows = screen.getAllByRole('row').slice(1); // Skip header row
      expect(within(rows[0]).getByText('alice@example.com')).toBeInTheDocument();
    });

    it('[P1] should toggle sort direction on second click', async () => {
      /**
       * GIVEN: Table sorted ascending by Name
       * WHEN: Name header is clicked again
       * THEN: Sort direction toggles to descending
       */
      const user = userEvent.setup();
      render(<KBPermissionsTable {...defaultProps} />);

      const nameHeader = screen.getByText('Name');

      // First click - ascending (alice, bob, Engineering)
      await user.click(nameHeader);
      let rows = screen.getAllByRole('row').slice(1);
      expect(within(rows[0]).getByText('alice@example.com')).toBeInTheDocument();

      // Second click - descending (Engineering, bob, alice)
      await user.click(nameHeader);
      rows = screen.getAllByRole('row').slice(1);
      expect(within(rows[0]).getByText('Engineering')).toBeInTheDocument();
    });
  });

  describe('search', () => {
    it('[P1] should call onSearchChange when typing in search', async () => {
      /**
       * GIVEN: Search input in table
       * WHEN: User types in search field
       * THEN: onSearchChange is called with value
       */
      const user = userEvent.setup();
      const onSearchChange = vi.fn();
      render(<KBPermissionsTable {...defaultProps} onSearchChange={onSearchChange} />);

      const searchInput = screen.getByPlaceholderText('Search by name or type...');
      await user.type(searchInput, 'alice');

      // onSearchChange is called for each character
      expect(onSearchChange).toHaveBeenCalled();
    });

    it('[P1] should filter permissions by search value', () => {
      /**
       * GIVEN: Search value is set
       * WHEN: Component renders
       * THEN: Only matching permissions are displayed
       */
      render(<KBPermissionsTable {...defaultProps} searchValue="alice" />);

      expect(screen.getByText('alice@example.com')).toBeInTheDocument();
      expect(screen.queryByText('bob@example.com')).not.toBeInTheDocument();
      expect(screen.queryByText('Engineering')).not.toBeInTheDocument();
    });
  });

  describe('pagination', () => {
    it('[P1] should display pagination info', () => {
      /**
       * GIVEN: Paginated permissions
       * WHEN: Component renders
       * THEN: Page info is displayed
       */
      render(<KBPermissionsTable {...defaultProps} />);

      // Check for Previous and Next buttons which are part of pagination
      expect(screen.getByText('Previous')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();
    });

    it('[P1] should call onPageChange when clicking Next', async () => {
      /**
       * GIVEN: Table on page 1 with more pages
       * WHEN: Next button is clicked
       * THEN: onPageChange is called with page 2
       */
      const user = userEvent.setup();
      const onPageChange = vi.fn();
      render(
        <KBPermissionsTable {...defaultProps} onPageChange={onPageChange} total={50} limit={20} />
      );

      const nextButton = screen.getByText('Next');
      await user.click(nextButton);

      expect(onPageChange).toHaveBeenCalledWith(2);
    });

    it('[P1] should call onPageChange when clicking Previous', async () => {
      /**
       * GIVEN: Table on page 2
       * WHEN: Previous button is clicked
       * THEN: onPageChange is called with page 1
       */
      const user = userEvent.setup();
      const onPageChange = vi.fn();
      render(
        <KBPermissionsTable {...defaultProps} onPageChange={onPageChange} page={2} total={50} />
      );

      const prevButton = screen.getByText('Previous');
      await user.click(prevButton);

      expect(onPageChange).toHaveBeenCalledWith(1);
    });

    it('[P1] should disable Previous on first page', () => {
      /**
       * GIVEN: Table on page 1
       * WHEN: Component renders
       * THEN: Previous button is disabled
       */
      render(<KBPermissionsTable {...defaultProps} page={1} />);

      const prevButton = screen.getByText('Previous');
      expect(prevButton).toBeDisabled();
    });

    it('[P1] should disable Next on last page', () => {
      /**
       * GIVEN: Table on last page
       * WHEN: Component renders
       * THEN: Next button is disabled
       */
      render(<KBPermissionsTable {...defaultProps} page={1} total={3} limit={20} />);

      const nextButton = screen.getByText('Next');
      expect(nextButton).toBeDisabled();
    });
  });

  describe('actions', () => {
    it('[P1] should call onEditPermission when edit button clicked', async () => {
      /**
       * GIVEN: Permission row with edit button
       * WHEN: Edit button is clicked
       * THEN: onEditPermission is called with permission
       */
      const user = userEvent.setup();
      const onEditPermission = vi.fn();
      render(<KBPermissionsTable {...defaultProps} onEditPermission={onEditPermission} />);

      const editButton = screen.getByLabelText('Edit permission for alice@example.com');
      await user.click(editButton);

      expect(onEditPermission).toHaveBeenCalledWith(mockPermissions[0]);
    });

    it('[P1] should call onDeletePermission when delete button clicked', async () => {
      /**
       * GIVEN: Permission row with delete button
       * WHEN: Delete button is clicked
       * THEN: onDeletePermission is called with permission
       */
      const user = userEvent.setup();
      const onDeletePermission = vi.fn();
      render(<KBPermissionsTable {...defaultProps} onDeletePermission={onDeletePermission} />);

      const deleteButton = screen.getByLabelText('Remove permission for alice@example.com');
      await user.click(deleteButton);

      expect(onDeletePermission).toHaveBeenCalledWith(mockPermissions[0]);
    });
  });

  describe('page size', () => {
    it('[P1] should render page size selector with current value', () => {
      /**
       * GIVEN: Page size selector
       * WHEN: Component renders
       * THEN: Current limit is displayed
       */
      const onLimitChange = vi.fn();
      render(<KBPermissionsTable {...defaultProps} limit={20} onLimitChange={onLimitChange} />);

      // Check that the page size label is present
      expect(screen.getByText('Show')).toBeInTheDocument();
      expect(screen.getByText('per page')).toBeInTheDocument();
    });
  });
});
