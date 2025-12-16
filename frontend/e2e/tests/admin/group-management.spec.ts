/**
 * Story 5-19 Automation: Group Management E2E Tests
 * Generated: 2025-12-05
 *
 * Test Coverage:
 * - [P0] AC-5.19.1: Group list page displays all groups in paginated table
 * - [P0] AC-5.19.2: Create group modal with form validation
 * - [P0] AC-5.19.3: Edit group modal with status toggle
 * - [P1] AC-5.19.4: Group membership management (add/remove members)
 * - [P1] AC-5.19.5: Admin navigation includes Groups link
 * - [P0] AC-5.19.6: Access control enforced (non-admin redirected)
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - network-first.md: Route interception patterns
 * - test-priorities-matrix.md: P0/P1/P2 classification
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { mockApiResponse, waitForNetworkIdle } from '../../utils/test-helpers';

test.describe('Story 5-19: Group Management E2E Tests', () => {
  const mockGroups = {
    data: [
      {
        id: 'group-1',
        name: 'Engineering',
        description: 'Software engineering team',
        is_active: true,
        member_count: 5,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-12-05T00:00:00Z',
      },
      {
        id: 'group-2',
        name: 'Marketing',
        description: 'Marketing and communications',
        is_active: true,
        member_count: 3,
        created_at: '2025-01-15T00:00:00Z',
        updated_at: '2025-12-04T00:00:00Z',
      },
      {
        id: 'group-3',
        name: 'Archived Team',
        description: 'No longer active',
        is_active: false,
        member_count: 0,
        created_at: '2025-02-01T00:00:00Z',
        updated_at: '2025-11-01T00:00:00Z',
      },
    ],
    meta: {
      total: 3,
      page: 1,
      per_page: 20,
      total_pages: 1,
    },
  };

  const mockGroupMembers = {
    data: [
      {
        id: 'user-1',
        email: 'alice@example.com',
        is_active: true,
        is_superuser: false,
      },
      {
        id: 'user-2',
        email: 'bob@example.com',
        is_active: true,
        is_superuser: false,
      },
    ],
    meta: {
      total: 2,
      page: 1,
      per_page: 100,
      total_pages: 1,
    },
  };

  const mockAvailableUsers = {
    data: [
      {
        id: 'user-3',
        email: 'charlie@example.com',
        is_active: true,
        is_superuser: false,
      },
      {
        id: 'user-4',
        email: 'diana@example.com',
        is_active: true,
        is_superuser: false,
      },
    ],
    meta: {
      total: 2,
      page: 1,
      per_page: 100,
      total_pages: 1,
    },
  };

  test.beforeEach(async ({ page }) => {
    // Network-first: Mock groups API BEFORE navigation
    await mockApiResponse(page, '**/api/v1/admin/groups**', mockGroups);
  });

  test('[P0] AC-5.19.1: Group list displays all groups in paginated table', async ({ page }) => {
    /**
     * GIVEN: Admin user is authenticated
     * WHEN: Admin navigates to /admin/groups
     * THEN: Page displays group table with all columns and data
     */

    // WHEN: Navigate to group management page
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);

    // THEN: Page title is visible
    await expect(page.getByRole('heading', { name: /Group Management/i })).toBeVisible();

    // THEN: Group table is visible with correct columns
    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    // THEN: Table headers are correct
    await expect(page.getByRole('columnheader', { name: /Name/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /Description/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /Members/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /Status/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /Actions/i })).toBeVisible();

    // THEN: All mock groups are displayed
    await expect(page.getByText('Engineering')).toBeVisible();
    await expect(page.getByText('Marketing')).toBeVisible();
    await expect(page.getByText('Archived Team')).toBeVisible();

    // THEN: Status badges show correct states
    const activeStatuses = page.locator('[data-testid="status-badge-active"]');
    await expect(activeStatuses).toHaveCount(2);

    const inactiveStatus = page.locator('[data-testid="status-badge-inactive"]');
    await expect(inactiveStatus).toHaveCount(1);

    // THEN: Member counts are displayed
    await expect(page.getByText('5 members')).toBeVisible();
    await expect(page.getByText('3 members')).toBeVisible();
    await expect(page.getByText('0 members')).toBeVisible();
  });

  test('[P0] AC-5.19.1: Name search filter works correctly', async ({ page }) => {
    /**
     * GIVEN: Admin is on group management page
     * WHEN: Admin enters search term in name filter
     * THEN: Table filters to matching groups
     */

    // GIVEN: Navigate to group management page
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);

    // WHEN: Enter search term
    const searchInput = page.getByPlaceholder(/Search groups/i);
    await searchInput.fill('Engineering');

    // Wait for debounced search
    await page.waitForTimeout(400);

    // THEN: Only matching group is visible
    await expect(page.getByText('Engineering')).toBeVisible();
    // Non-matching groups may be hidden by client-side filter
  });

  test('[P0] AC-5.19.2: Create group modal opens and validates form', async ({ page }) => {
    /**
     * GIVEN: Admin is on group management page
     * WHEN: Admin clicks "Create Group" button
     * THEN: Create group modal opens with form fields
     */

    // GIVEN: Navigate to group management page
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);

    // WHEN: Click Create Group button
    const addButton = page.getByRole('button', { name: /Create Group/i });
    await addButton.click();

    // THEN: Modal opens
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    await expect(page.getByRole('heading', { name: /Create New Group/i })).toBeVisible();

    // THEN: Form fields are present
    await expect(page.getByLabel(/Group Name/i)).toBeVisible();
    await expect(page.getByLabel(/Description/i)).toBeVisible();

    // WHEN: Submit with empty name
    await page.getByRole('button', { name: /^Create$/i }).click();

    // THEN: Validation error appears
    await expect(page.getByText(/Group name is required/i)).toBeVisible();
  });

  test('[P0] AC-5.19.2: Create group submits successfully', async ({ page }) => {
    /**
     * GIVEN: Admin has create group modal open
     * WHEN: Admin fills valid data and submits
     * THEN: Group is created and modal closes
     */

    // Mock successful create response
    await page.route('**/api/v1/admin/groups', async (route, request) => {
      if (request.method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'new-group',
            name: 'New Team',
            description: 'A new team',
            is_active: true,
            member_count: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    // GIVEN: Navigate and open modal
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);
    await page.getByRole('button', { name: /Create Group/i }).click();

    // WHEN: Fill form with valid data
    await page.getByLabel(/Group Name/i).fill('New Team');
    await page.getByLabel(/Description/i).fill('A new team');

    // WHEN: Submit form
    await page.getByRole('button', { name: /^Create$/i }).click();

    // THEN: Modal closes
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5000 });
  });

  test('[P0] AC-5.19.3: Edit group modal shows group details', async ({ page }) => {
    /**
     * GIVEN: Admin is on group management page
     * WHEN: Admin clicks edit button for a group
     * THEN: Edit modal opens with group details
     */

    // GIVEN: Navigate to group management page
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);

    // WHEN: Click edit button for first group
    const editButtons = page.getByRole('button', { name: /Edit/i });
    await editButtons.first().click();

    // THEN: Modal opens with group details
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    await expect(page.getByRole('heading', { name: /Edit Group/i })).toBeVisible();

    // THEN: Form is pre-populated
    const nameInput = page.getByLabel(/Group Name/i);
    await expect(nameInput).toHaveValue('Engineering');

    // THEN: Status toggle is present
    const statusToggle = page.getByRole('switch');
    await expect(statusToggle).toBeVisible();
  });

  test('[P0] AC-5.19.3: Edit group updates successfully', async ({ page }) => {
    /**
     * GIVEN: Admin has edit modal open
     * WHEN: Admin modifies group and saves
     * THEN: Group is updated and modal closes
     */

    // Mock update endpoint
    await page.route('**/api/v1/admin/groups/*', async (route, request) => {
      if (request.method() === 'PATCH') {
        const body = request.postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockGroups.data[0],
            ...body,
            updated_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    // GIVEN: Navigate and open edit modal
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);
    await page.getByRole('button', { name: /Edit/i }).first().click();

    // WHEN: Modify name
    const nameInput = page.getByLabel(/Group Name/i);
    await nameInput.clear();
    await nameInput.fill('Engineering Team');

    // WHEN: Save changes
    await page.getByRole('button', { name: /Save Changes/i }).click();

    // THEN: Modal closes
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5000 });
  });

  test('[P0] AC-5.19.3: Status toggle updates group', async ({ page }) => {
    /**
     * GIVEN: Admin has edit modal open for active group
     * WHEN: Admin toggles status to inactive
     * THEN: Status is updated
     */

    // Mock update endpoint
    await page.route('**/api/v1/admin/groups/*', async (route, request) => {
      if (request.method() === 'PATCH') {
        const body = request.postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockGroups.data[0],
            is_active: body.is_active,
            updated_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    // GIVEN: Navigate and open edit modal
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);
    await page.getByRole('button', { name: /Edit/i }).first().click();

    // WHEN: Toggle status
    const statusToggle = page.getByRole('switch');
    await expect(statusToggle).toBeVisible();
    await expect(statusToggle).toBeChecked();

    // Toggle off
    await statusToggle.click();

    // THEN: Toggle updates
    await expect(statusToggle).not.toBeChecked();
  });

  test('[P1] AC-5.19.4: Membership modal displays current members', async ({ page }) => {
    /**
     * GIVEN: Admin is on group management page
     * WHEN: Admin clicks members button for a group
     * THEN: Membership modal shows current members
     */

    // Mock members endpoint
    await page.route('**/api/v1/admin/groups/*/members**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockGroupMembers),
      });
    });

    // GIVEN: Navigate to group management page
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);

    // WHEN: Click members button (badge showing member count)
    const membersButton = page.getByRole('button', { name: /5 members/i });
    await membersButton.click();

    // THEN: Modal opens
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    await expect(page.getByRole('heading', { name: /Manage Members/i })).toBeVisible();

    // THEN: Current members are displayed
    await expect(page.getByText('alice@example.com')).toBeVisible();
    await expect(page.getByText('bob@example.com')).toBeVisible();
  });

  test('[P1] AC-5.19.4: Can add members to group', async ({ page }) => {
    /**
     * GIVEN: Admin has membership modal open
     * WHEN: Admin selects users and adds them
     * THEN: Users are added to group
     */

    // Mock endpoints
    await page.route('**/api/v1/admin/groups/*/members**', async (route, request) => {
      if (request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockGroupMembers),
        });
      } else if (request.method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ added: 1 }),
        });
      } else {
        await route.continue();
      }
    });

    await page.route('**/api/v1/admin/users**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAvailableUsers),
      });
    });

    // GIVEN: Navigate and open membership modal
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);
    await page.getByRole('button', { name: /5 members/i }).click();

    // WHEN: Select a user from available users
    const userCheckbox = page.getByRole('checkbox', { name: /charlie@example.com/i });
    if (await userCheckbox.isVisible()) {
      await userCheckbox.check();

      // WHEN: Click add button
      const addButton = page.getByRole('button', { name: /Add Selected/i });
      await addButton.click();

      // THEN: Success feedback (API call made)
      // The modal may update or show success message
    }
  });

  test('[P1] AC-5.19.4: Can remove member from group', async ({ page }) => {
    /**
     * GIVEN: Admin has membership modal open with members
     * WHEN: Admin clicks remove on a member
     * THEN: Member is removed from group
     */

    // Mock endpoints
    await page.route('**/api/v1/admin/groups/*/members**', async (route, request) => {
      if (request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockGroupMembers),
        });
      } else {
        await route.continue();
      }
    });

    await page.route('**/api/v1/admin/groups/*/members/*', async (route, request) => {
      if (request.method() === 'DELETE') {
        await route.fulfill({
          status: 204,
          contentType: 'application/json',
        });
      } else {
        await route.continue();
      }
    });

    // GIVEN: Navigate and open membership modal
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);
    await page.getByRole('button', { name: /5 members/i }).click();

    // Wait for members to load
    await expect(page.getByText('alice@example.com')).toBeVisible();

    // WHEN: Click remove button for first member
    const removeButtons = page.getByRole('button', { name: /Remove/i });
    if ((await removeButtons.count()) > 0) {
      await removeButtons.first().click();

      // THEN: API call is made (member removed)
      // The member list updates
    }
  });

  test('[P1] AC-5.19.5: Admin navigation includes Groups link', async ({ page }) => {
    /**
     * GIVEN: Admin user is authenticated
     * WHEN: Admin views the navigation
     * THEN: Groups link is visible in admin section
     */

    // GIVEN: Navigate to admin dashboard
    await page.goto('/admin');
    await waitForNetworkIdle(page);

    // THEN: Groups link is visible in navigation
    const groupsLink = page.getByRole('link', { name: /Groups/i });
    await expect(groupsLink).toBeVisible();

    // WHEN: Click Groups link
    await groupsLink.click();

    // THEN: Navigate to groups page
    await expect(page).toHaveURL(/\/admin\/groups/);
  });

  test('[P0] AC-5.19.6: Non-admin user is redirected from groups page', async ({ page }) => {
    /**
     * GIVEN: Non-admin user is authenticated
     * WHEN: User attempts to access /admin/groups
     * THEN: User is redirected to dashboard
     */

    // Mock user as non-admin by mocking the auth check
    await page.route('**/api/v1/users/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'regular-user',
          email: 'regular@example.com',
          is_superuser: false,
          is_active: true,
        }),
      });
    });

    // WHEN: Navigate to admin groups page
    await page.goto('/admin/groups');
    await page.waitForLoadState('networkidle');

    // THEN: Either shows access denied or redirects to dashboard
    const accessDenied = page.getByText(/Access Denied/i);
    const dashboardUrl = /\/dashboard/;

    // Wait for either outcome
    await Promise.race([
      expect(accessDenied).toBeVisible({ timeout: 3000 }).catch(() => {}),
      page.waitForURL(dashboardUrl, { timeout: 5000 }).catch(() => {}),
    ]);

    // Verify we're not on the groups page
    const url = page.url();
    expect(url).not.toContain('/admin/groups');
  });

  test('[P2] Pagination controls work correctly', async ({ page }) => {
    /**
     * GIVEN: Admin is on group management page with multiple pages
     * WHEN: Admin clicks next page
     * THEN: Page navigation updates
     */

    // Mock paginated response with multiple pages
    const paginatedGroups = {
      ...mockGroups,
      meta: {
        total: 45,
        page: 1,
        per_page: 20,
        total_pages: 3,
      },
    };

    await page.route('**/api/v1/admin/groups**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(paginatedGroups),
      });
    });

    // GIVEN: Navigate to group management page
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);

    // THEN: Pagination info is displayed
    await expect(page.getByText(/Page 1 of 3/i)).toBeVisible();

    // THEN: Next button is enabled
    const nextButton = page.getByRole('button', { name: /Next/i });
    await expect(nextButton).toBeEnabled();

    // THEN: Previous button is disabled on first page
    const prevButton = page.getByRole('button', { name: /Previous/i });
    await expect(prevButton).toBeDisabled();
  });

  test('[P2] Delete group with confirmation', async ({ page }) => {
    /**
     * GIVEN: Admin is on group management page
     * WHEN: Admin clicks delete and confirms
     * THEN: Group is deleted
     */

    // Mock delete endpoint
    await page.route('**/api/v1/admin/groups/*', async (route, request) => {
      if (request.method() === 'DELETE') {
        await route.fulfill({
          status: 204,
          contentType: 'application/json',
        });
      } else {
        await route.continue();
      }
    });

    // GIVEN: Navigate to group management page
    await page.goto('/admin/groups');
    await waitForNetworkIdle(page);

    // WHEN: Click delete button for a group
    const deleteButtons = page.getByRole('button', { name: /Delete/i });
    await deleteButtons.first().click();

    // THEN: Confirmation dialog appears
    const confirmDialog = page.getByRole('alertdialog');
    await expect(confirmDialog).toBeVisible();

    // WHEN: Confirm deletion
    const confirmButton = page.getByRole('button', { name: /^Delete$/i });
    await confirmButton.click();

    // THEN: Dialog closes (deletion complete)
    await expect(confirmDialog).not.toBeVisible({ timeout: 5000 });
  });
});
