/**
 * Component tests for GroupTable
 * Story 5.19: Group Management (AC-5.19.1)
 *
 * Test Coverage:
 * - [P1] Table renders with group data and correct columns
 * - [P1] Client-side sorting by column click
 * - [P1] Name search/filter with debounce
 * - [P1] Pagination controls work correctly
 * - [P1] Empty state displays when no groups
 * - [P1] Loading state displays spinner
 * - [P2] Status badges show correct colors
 * - [P2] Member count displays correctly
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - component-tdd.md: Component testing patterns
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GroupTable, type GroupTableProps } from '../group-table';
import type { Group, GroupMember } from '@/types/group';
import { PermissionLevel } from '@/types/user';

// Mock group data
const mockGroups: Group[] = [
  {
    id: 'group-1',
    name: 'Engineering',
    description: 'Software engineering team',
    is_active: true,
    permission_level: PermissionLevel.USER,
    is_system: false,
    member_count: 5,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-12-05T00:00:00Z',
  },
  {
    id: 'group-2',
    name: 'Marketing',
    description: 'Marketing and communications',
    is_active: true,
    permission_level: PermissionLevel.OPERATOR,
    is_system: false,
    member_count: 3,
    created_at: '2025-01-15T00:00:00Z',
    updated_at: '2025-12-04T00:00:00Z',
  },
  {
    id: 'group-3',
    name: 'Archived Team',
    description: 'No longer active',
    is_active: false,
    permission_level: PermissionLevel.USER,
    is_system: false,
    member_count: 0,
    created_at: '2025-02-01T00:00:00Z',
    updated_at: '2025-11-01T00:00:00Z',
  },
];

const mockExpandedMembers: GroupMember[] = [
  { id: 'user-1', email: 'alice@example.com', is_active: true, joined_at: '2025-01-01T00:00:00Z' },
  { id: 'user-2', email: 'bob@example.com', is_active: true, joined_at: '2025-01-02T00:00:00Z' },
];

describe('GroupTable', () => {
  const defaultProps: GroupTableProps = {
    groups: mockGroups,
    total: 3,
    page: 1,
    totalPages: 1,
    isLoading: false,
    onPageChange: vi.fn(),
    onEditGroup: vi.fn(),
    onDeleteGroup: vi.fn(),
    onManageMembers: vi.fn(),
    searchValue: '',
    onSearchChange: vi.fn(),
    expandedGroup: null,
    onExpandGroup: vi.fn(),
    expandedMembers: [],
    isLoadingMembers: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('[P1] renders table with all groups and correct columns', () => {
      /**
       * GIVEN: GroupTable component with group data
       * WHEN: Component renders
       * THEN: All groups are displayed with correct columns
       */

      // WHEN: Render component
      render(<GroupTable {...defaultProps} />);

      // THEN: Table headers are visible
      expect(screen.getByRole('columnheader', { name: /name/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /description/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /members/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /status/i })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: /actions/i })).toBeInTheDocument();

      // THEN: All groups are displayed
      expect(screen.getByText('Engineering')).toBeInTheDocument();
      expect(screen.getByText('Marketing')).toBeInTheDocument();
      expect(screen.getByText('Archived Team')).toBeInTheDocument();
    });

    it('[P1] displays loading state with spinner', () => {
      /**
       * GIVEN: GroupTable with isLoading=true
       * WHEN: Component renders
       * THEN: Loading spinner is displayed
       */

      // WHEN: Render with loading state
      render(<GroupTable {...defaultProps} isLoading={true} />);

      // THEN: Loading message is visible
      expect(screen.getByText(/loading groups/i)).toBeInTheDocument();

      // THEN: Table is not visible
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('[P1] displays empty state when no groups', () => {
      /**
       * GIVEN: GroupTable with empty groups array
       * WHEN: Component renders
       * THEN: Empty state message is displayed
       */

      // WHEN: Render with no groups
      render(<GroupTable {...defaultProps} groups={[]} />);

      // THEN: Empty state message is visible
      expect(screen.getByText(/no groups found/i)).toBeInTheDocument();

      // THEN: Table is not visible
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('[P2] displays correct status badges for active/inactive groups', () => {
      /**
       * GIVEN: GroupTable with active and inactive groups
       * WHEN: Component renders
       * THEN: Status badges show correct colors
       */

      // WHEN: Render component
      render(<GroupTable {...defaultProps} />);

      // THEN: Active badges are present (2 active groups)
      const activeBadges = screen.getAllByTestId('status-badge-active');
      expect(activeBadges).toHaveLength(2);

      // THEN: Inactive badge is present (1 inactive group)
      const inactiveBadges = screen.getAllByTestId('status-badge-inactive');
      expect(inactiveBadges).toHaveLength(1);
    });

    it('[P2] displays member counts correctly', () => {
      /**
       * GIVEN: GroupTable with groups having different member counts
       * WHEN: Component renders
       * THEN: Member counts are displayed in each row
       */

      // WHEN: Render component
      render(<GroupTable {...defaultProps} />);

      // THEN: Member counts are displayed
      // Default sort is by created_at desc, so order is: Archived, Marketing, Engineering
      const rows = screen.getAllByRole('row');
      // Skip header row (index 0), check data rows
      const archivedRow = rows[1]; // created Feb 1 - most recent
      const marketingRow = rows[2]; // created Jan 15
      const engineeringRow = rows[3]; // created Jan 1 - oldest

      expect(within(archivedRow).getByText('0')).toBeInTheDocument();
      expect(within(marketingRow).getByText('3')).toBeInTheDocument();
      expect(within(engineeringRow).getByText('5')).toBeInTheDocument();
    });
  });

  describe('sorting', () => {
    it('[P1] sorts by name column when clicked', async () => {
      /**
       * GIVEN: GroupTable with multiple groups
       * WHEN: User clicks name column header
       * THEN: Table sorts by name
       */
      const user = userEvent.setup();

      // WHEN: Render component
      render(<GroupTable {...defaultProps} />);

      // WHEN: Click name header to sort ascending
      const nameHeader = screen.getByRole('columnheader', { name: /name/i });
      await user.click(nameHeader);

      // THEN: Rows should be reordered by name ascending
      const sortedRows = screen.getAllByRole('row');
      const firstDataRow = sortedRows[1]; // Skip header row
      expect(within(firstDataRow).getByText('Archived Team')).toBeInTheDocument();
    });

    it('[P1] toggles sort direction on repeated click', async () => {
      /**
       * GIVEN: GroupTable sorted by name ascending
       * WHEN: User clicks name column header again
       * THEN: Sort direction toggles to descending
       */
      const user = userEvent.setup();

      // WHEN: Render component
      render(<GroupTable {...defaultProps} />);

      const nameHeader = screen.getByRole('columnheader', { name: /name/i });

      // Click once for ascending
      await user.click(nameHeader);

      // Click again for descending
      await user.click(nameHeader);

      // THEN: Verify by checking the order - 'Marketing' should come before 'Engineering'
      const rows = screen.getAllByRole('row');
      const firstDataRow = rows[1];
      expect(within(firstDataRow).getByText('Marketing')).toBeInTheDocument();
    });
  });

  describe('filtering', () => {
    it('[P1] calls onSearchChange when typing in search input', async () => {
      /**
       * GIVEN: GroupTable with search functionality
       * WHEN: User enters search term
       * THEN: onSearchChange is called with input value
       */
      const user = userEvent.setup();
      const onSearchChange = vi.fn();

      // WHEN: Render component
      render(<GroupTable {...defaultProps} onSearchChange={onSearchChange} />);

      // WHEN: Type in search input
      const searchInput = screen.getByLabelText(/search groups by name/i);
      await user.type(searchInput, 'E');

      // THEN: onSearchChange is called
      expect(onSearchChange).toHaveBeenCalled();
      expect(onSearchChange).toHaveBeenCalledWith('E');
    });
  });

  describe('pagination', () => {
    it('[P1] displays pagination info correctly', () => {
      /**
       * GIVEN: GroupTable with pagination data
       * WHEN: Component renders
       * THEN: Pagination info shows correct counts
       */

      // WHEN: Render component
      render(<GroupTable {...defaultProps} />);

      // THEN: Pagination info is displayed
      expect(screen.getByText(/showing/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
    });

    it('[P1] disables previous button on first page', () => {
      /**
       * GIVEN: GroupTable on first page
       * WHEN: Component renders
       * THEN: Previous button is disabled
       */

      // WHEN: Render on first page
      render(<GroupTable {...defaultProps} />);

      // THEN: Previous button is disabled
      const prevButton = screen.getByRole('button', { name: /previous/i });
      expect(prevButton).toBeDisabled();
    });

    it('[P1] enables next button when more pages exist', () => {
      /**
       * GIVEN: GroupTable with multiple pages
       * WHEN: Component renders
       * THEN: Next button is enabled
       */

      // WHEN: Render with multiple pages
      render(<GroupTable {...defaultProps} totalPages={3} />);

      // THEN: Next button is enabled
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeEnabled();
    });

    it('[P1] calls onPageChange when next is clicked', async () => {
      /**
       * GIVEN: GroupTable with multiple pages
       * WHEN: User clicks next button
       * THEN: onPageChange is called with next page number
       */
      const user = userEvent.setup();
      const onPageChange = vi.fn();

      // WHEN: Render and click next
      render(<GroupTable {...defaultProps} totalPages={3} onPageChange={onPageChange} />);

      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      // THEN: onPageChange called with page 2
      expect(onPageChange).toHaveBeenCalledWith(2);
    });
  });

  describe('actions', () => {
    it('[P1] calls onEditGroup when edit button is clicked', async () => {
      /**
       * GIVEN: GroupTable with edit buttons
       * WHEN: User clicks edit button for a group
       * THEN: onEditGroup is called with that group
       */
      const user = userEvent.setup();
      const onEditGroup = vi.fn();

      // WHEN: Render component
      render(<GroupTable {...defaultProps} onEditGroup={onEditGroup} />);

      // Find the row with Engineering and click its edit button
      const groupRow = screen.getByText('Engineering').closest('tr');
      const editButton = within(groupRow!).getByRole('button', { name: /edit engineering/i });
      await user.click(editButton);

      // THEN: onEditGroup called with Engineering group
      expect(onEditGroup).toHaveBeenCalledWith(mockGroups[0]);
    });

    it('[P1] calls onDeleteGroup when delete button is clicked', async () => {
      /**
       * GIVEN: GroupTable with delete buttons
       * WHEN: User clicks delete button for a group
       * THEN: onDeleteGroup is called with that group
       */
      const user = userEvent.setup();
      const onDeleteGroup = vi.fn();

      // WHEN: Render component
      render(<GroupTable {...defaultProps} onDeleteGroup={onDeleteGroup} />);

      // Find the row with Engineering and click its delete button
      const groupRow = screen.getByText('Engineering').closest('tr');
      const deleteButton = within(groupRow!).getByRole('button', { name: /delete engineering/i });
      await user.click(deleteButton);

      // THEN: onDeleteGroup called with Engineering group
      expect(onDeleteGroup).toHaveBeenCalledWith(mockGroups[0]);
    });

    it('[P1] calls onManageMembers when members button is clicked', async () => {
      /**
       * GIVEN: GroupTable with member management
       * WHEN: User clicks members button
       * THEN: onManageMembers is called with that group
       */
      const user = userEvent.setup();
      const onManageMembers = vi.fn();

      // WHEN: Render component
      render(<GroupTable {...defaultProps} onManageMembers={onManageMembers} />);

      // Find member button for first group
      const groupRow = screen.getByText('Engineering').closest('tr');
      const membersButton = within(groupRow!).getByRole('button', {
        name: /manage members of engineering/i,
      });
      await user.click(membersButton);

      // THEN: onManageMembers called with Engineering group
      expect(onManageMembers).toHaveBeenCalledWith(mockGroups[0]);
    });
  });

  describe('expandable rows', () => {
    it('[P1] calls onExpandGroup when expand button is clicked', async () => {
      /**
       * GIVEN: GroupTable with expandable rows
       * WHEN: User clicks expand button
       * THEN: onExpandGroup is called
       */
      const user = userEvent.setup();
      const onExpandGroup = vi.fn();

      // WHEN: Render component
      render(<GroupTable {...defaultProps} onExpandGroup={onExpandGroup} />);

      // Find expand button for first group
      const groupRow = screen.getByText('Engineering').closest('tr');
      const expandButton = within(groupRow!).getByRole('button', { name: /expand members/i });
      await user.click(expandButton);

      // THEN: onExpandGroup called with group id
      expect(onExpandGroup).toHaveBeenCalledWith('group-1');
    });

    it('[P1] shows members when group is expanded', () => {
      /**
       * GIVEN: GroupTable with expanded group
       * WHEN: Component renders
       * THEN: Members are displayed
       */

      // WHEN: Render with expanded group
      render(
        <GroupTable
          {...defaultProps}
          expandedGroup="group-1"
          expandedMembers={mockExpandedMembers}
        />
      );

      // THEN: Members are displayed
      expect(screen.getByText('alice@example.com')).toBeInTheDocument();
      expect(screen.getByText('bob@example.com')).toBeInTheDocument();
    });

    it('[P1] shows loading state when loading members', () => {
      /**
       * GIVEN: GroupTable loading members
       * WHEN: Component renders
       * THEN: Loading indicator is shown
       */

      // WHEN: Render with loading members
      render(<GroupTable {...defaultProps} expandedGroup="group-1" isLoadingMembers={true} />);

      // THEN: Loading message is shown
      expect(screen.getByText(/loading members/i)).toBeInTheDocument();
    });

    it('[P1] shows empty state when no members', () => {
      /**
       * GIVEN: GroupTable with expanded group having no members
       * WHEN: Component renders
       * THEN: Empty state is shown
       */

      // WHEN: Render with no members
      render(<GroupTable {...defaultProps} expandedGroup="group-1" expandedMembers={[]} />);

      // THEN: Empty state is shown
      expect(screen.getByText(/no members in this group/i)).toBeInTheDocument();
    });
  });

  describe('RBAC features (AC-7.11.8-10)', () => {
    const systemGroup: Group = {
      id: 'system-group-1',
      name: 'Administrators',
      description: 'System administrators',
      is_active: true,
      permission_level: PermissionLevel.ADMINISTRATOR,
      is_system: true,
      member_count: 2,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-12-05T00:00:00Z',
    };

    it('[P1] displays System badge for system groups (AC-7.11.8)', () => {
      /**
       * GIVEN: GroupTable with a system group
       * WHEN: Component renders
       * THEN: System badge is displayed for the system group
       */

      // WHEN: Render with system group
      render(<GroupTable {...defaultProps} groups={[systemGroup, ...mockGroups]} />);

      // THEN: System badge is visible
      expect(screen.getByTestId('system-badge')).toBeInTheDocument();
      expect(screen.getByText('System')).toBeInTheDocument();
    });

    it('[P1] displays permission level badges (AC-7.11.9)', () => {
      /**
       * GIVEN: GroupTable with groups having different permission levels
       * WHEN: Component renders
       * THEN: Permission level badges are displayed
       */

      // WHEN: Render with groups
      render(<GroupTable {...defaultProps} groups={[systemGroup, ...mockGroups]} />);

      // THEN: Permission level badges are visible
      const badges = screen.getAllByTestId('permission-level-badge');
      expect(badges.length).toBeGreaterThan(0);

      // THEN: Badge labels are displayed (Admin for ADMINISTRATOR level)
      expect(screen.getByText('Admin')).toBeInTheDocument();
    });

    it('[P1] disables edit button for system groups (AC-7.11.10)', () => {
      /**
       * GIVEN: GroupTable with a system group
       * WHEN: Component renders
       * THEN: Edit button is disabled for system groups
       */

      // WHEN: Render with system group
      render(<GroupTable {...defaultProps} groups={[systemGroup]} />);

      // THEN: Edit button is disabled
      const editButton = screen.getByRole('button', { name: /cannot edit system group/i });
      expect(editButton).toBeDisabled();
    });

    it('[P1] disables delete button for system groups (AC-7.11.10)', () => {
      /**
       * GIVEN: GroupTable with a system group
       * WHEN: Component renders
       * THEN: Delete button is disabled for system groups
       */

      // WHEN: Render with system group
      render(<GroupTable {...defaultProps} groups={[systemGroup]} />);

      // THEN: Delete button is disabled
      const deleteButton = screen.getByRole('button', { name: /cannot delete system group/i });
      expect(deleteButton).toBeDisabled();
    });

    it('[P1] does not call onEditGroup when clicking disabled edit button', async () => {
      /**
       * GIVEN: GroupTable with system group and disabled edit button
       * WHEN: User attempts to click edit
       * THEN: onEditGroup is not called
       */
      const user = userEvent.setup();
      const onEditGroup = vi.fn();

      // WHEN: Render with system group
      render(<GroupTable {...defaultProps} groups={[systemGroup]} onEditGroup={onEditGroup} />);

      // Attempt to click disabled edit button
      const editButton = screen.getByRole('button', { name: /cannot edit system group/i });
      await user.click(editButton);

      // THEN: onEditGroup is not called
      expect(onEditGroup).not.toHaveBeenCalled();
    });

    it('[P1] does not call onDeleteGroup when clicking disabled delete button', async () => {
      /**
       * GIVEN: GroupTable with system group and disabled delete button
       * WHEN: User attempts to click delete
       * THEN: onDeleteGroup is not called
       */
      const user = userEvent.setup();
      const onDeleteGroup = vi.fn();

      // WHEN: Render with system group
      render(<GroupTable {...defaultProps} groups={[systemGroup]} onDeleteGroup={onDeleteGroup} />);

      // Attempt to click disabled delete button
      const deleteButton = screen.getByRole('button', { name: /cannot delete system group/i });
      await user.click(deleteButton);

      // THEN: onDeleteGroup is not called
      expect(onDeleteGroup).not.toHaveBeenCalled();
    });

    it('[P1] allows edit for non-system groups', async () => {
      /**
       * GIVEN: GroupTable with regular (non-system) groups
       * WHEN: User clicks edit button
       * THEN: onEditGroup is called
       */
      const user = userEvent.setup();
      const onEditGroup = vi.fn();

      // WHEN: Render with regular groups
      render(<GroupTable {...defaultProps} onEditGroup={onEditGroup} />);

      // Find Engineering edit button (non-system group)
      const groupRow = screen.getByText('Engineering').closest('tr');
      const editButton = within(groupRow!).getByRole('button', { name: /edit engineering/i });
      await user.click(editButton);

      // THEN: onEditGroup is called
      expect(onEditGroup).toHaveBeenCalledWith(mockGroups[0]);
    });
  });
});
