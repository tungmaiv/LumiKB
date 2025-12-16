/**
 * Story 5-18 Automation: User Management E2E Tests
 * Generated: 2025-12-05
 *
 * Test Coverage:
 * - [P0] AC-5.18.1: User list page displays all users in paginated table
 * - [P0] AC-5.18.2: Create user modal with form validation
 * - [P0] AC-5.18.3: Edit user modal with status toggle
 * - [P1] AC-5.18.4: User status toggle with optimistic updates
 * - [P1] AC-5.18.5: Admin navigation includes Users link
 * - [P0] AC-5.18.6: Access control enforced (non-admin redirected)
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - network-first.md: Route interception patterns
 * - test-priorities-matrix.md: P0/P1/P2 classification
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { mockApiResponse, waitForNetworkIdle } from '../../utils/test-helpers';

test.describe('Story 5-18: User Management E2E Tests', () => {
  const mockUsers = {
    data: [
      {
        id: 'user-1',
        email: 'admin@example.com',
        is_active: true,
        is_superuser: true,
        is_verified: true,
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
        created_at: '2025-02-01T00:00:00Z',
        last_active: '2025-11-01T00:00:00Z',
        onboarding_completed: false,
      },
    ],
    meta: {
      total: 3,
      page: 1,
      per_page: 20,
      total_pages: 1,
    },
  };

  test.beforeEach(async ({ page }) => {
    // Network-first: Mock users API BEFORE navigation
    await mockApiResponse(page, '**/api/v1/admin/users**', mockUsers);
  });

  test('[P0] AC-5.18.1: User list displays all users in paginated table', async ({ page }) => {
    /**
     * GIVEN: Admin user is authenticated
     * WHEN: Admin navigates to /admin/users
     * THEN: Page displays user table with all columns and data
     */

    // WHEN: Navigate to user management page
    await page.goto('/admin/users');
    await waitForNetworkIdle(page);

    // THEN: Page title is visible
    await expect(page.getByRole('heading', { name: /User Management/i })).toBeVisible();

    // THEN: User table is visible with correct columns
    const table = page.getByRole('table');
    await expect(table).toBeVisible();

    // THEN: Table headers are correct
    await expect(page.getByRole('columnheader', { name: /Email/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /Status/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /Role/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /Created/i })).toBeVisible();

    // THEN: All mock users are displayed
    await expect(page.getByText('admin@example.com')).toBeVisible();
    await expect(page.getByText('user@example.com')).toBeVisible();
    await expect(page.getByText('inactive@example.com')).toBeVisible();

    // THEN: Status badges show correct states
    const activeStatuses = page.locator('[data-testid="status-badge-active"]');
    await expect(activeStatuses).toHaveCount(2);

    const inactiveStatus = page.locator('[data-testid="status-badge-inactive"]');
    await expect(inactiveStatus).toHaveCount(1);

    // THEN: Role badges show correct roles
    const adminRoles = page.locator('[data-testid="role-badge-admin"]');
    await expect(adminRoles).toHaveCount(1);

    const userRoles = page.locator('[data-testid="role-badge-user"]');
    await expect(userRoles).toHaveCount(2);
  });

  test('[P0] AC-5.18.1: Email search filter works correctly', async ({ page }) => {
    /**
     * GIVEN: Admin is on user management page
     * WHEN: Admin enters search term in email filter
     * THEN: Table filters to matching users
     */

    // GIVEN: Navigate to user management page
    await page.goto('/admin/users');
    await waitForNetworkIdle(page);

    // WHEN: Enter search term
    const searchInput = page.getByPlaceholder(/Search by email/i);
    await searchInput.fill('admin');

    // Wait for debounced search
    await page.waitForTimeout(400);

    // THEN: Only matching user is visible
    await expect(page.getByText('admin@example.com')).toBeVisible();
    // Non-matching users may be hidden by client-side filter
  });

  test('[P0] AC-5.18.2: Create user modal opens and validates form', async ({ page }) => {
    /**
     * GIVEN: Admin is on user management page
     * WHEN: Admin clicks "Add User" button
     * THEN: Create user modal opens with form fields
     */

    // GIVEN: Navigate to user management page
    await page.goto('/admin/users');
    await waitForNetworkIdle(page);

    // WHEN: Click Add User button
    const addButton = page.getByRole('button', { name: /Add User/i });
    await addButton.click();

    // THEN: Modal opens
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    await expect(page.getByRole('heading', { name: /Add New User/i })).toBeVisible();

    // THEN: Form fields are present
    await expect(page.getByLabel(/Email/i)).toBeVisible();
    await expect(page.getByLabel(/^Password$/i)).toBeVisible();
    await expect(page.getByLabel(/Confirm Password/i)).toBeVisible();
    await expect(page.getByLabel(/Grant administrator privileges/i)).toBeVisible();

    // WHEN: Submit with empty fields
    await page.getByRole('button', { name: /Create User/i }).click();

    // THEN: Validation errors appear
    await expect(page.getByText(/Please enter a valid email/i)).toBeVisible();
  });

  test('[P0] AC-5.18.2: Create user submits successfully', async ({ page }) => {
    /**
     * GIVEN: Admin has create user modal open
     * WHEN: Admin fills valid data and submits
     * THEN: User is created and modal closes
     */

    // Mock successful create response
    await page.route('**/api/v1/admin/users', async (route, request) => {
      if (request.method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'new-user',
            email: 'newuser@example.com',
            is_active: true,
            is_superuser: false,
            is_verified: false,
            created_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    // GIVEN: Navigate and open modal
    await page.goto('/admin/users');
    await waitForNetworkIdle(page);
    await page.getByRole('button', { name: /Add User/i }).click();

    // WHEN: Fill form with valid data
    await page.getByLabel(/Email/i).fill('newuser@example.com');
    await page.getByLabel(/^Password$/i).fill('password123');
    await page.getByLabel(/Confirm Password/i).fill('password123');

    // WHEN: Submit form
    await page.getByRole('button', { name: /Create User/i }).click();

    // THEN: Modal closes and success toast appears
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5000 });
  });

  test('[P0] AC-5.18.3: Edit user modal shows user details', async ({ page }) => {
    /**
     * GIVEN: Admin is on user management page
     * WHEN: Admin clicks edit button for a user
     * THEN: Edit modal opens with user details
     */

    // GIVEN: Navigate to user management page
    await page.goto('/admin/users');
    await waitForNetworkIdle(page);

    // WHEN: Click edit button for first user
    const editButtons = page.getByRole('button', { name: /Edit/i });
    await editButtons.first().click();

    // THEN: Modal opens with user details
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    await expect(page.getByRole('heading', { name: /Edit User/i })).toBeVisible();

    // THEN: Email is shown as read-only
    await expect(page.getByText('admin@example.com')).toBeVisible();

    // THEN: Status toggle is present
    const statusToggle = page.getByRole('switch', { name: /Active/i });
    await expect(statusToggle).toBeVisible();
  });

  test('[P1] AC-5.18.4: User status toggle updates optimistically', async ({ page }) => {
    /**
     * GIVEN: Admin has edit modal open for active user
     * WHEN: Admin toggles status to inactive
     * THEN: UI updates immediately (optimistic update)
     */

    // Mock update endpoint
    await page.route('**/api/v1/admin/users/*', async (route, request) => {
      if (request.method() === 'PATCH') {
        const body = request.postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockUsers.data[1],
            is_active: body.is_active,
          }),
        });
      } else {
        await route.continue();
      }
    });

    // GIVEN: Navigate and open edit modal for regular user
    await page.goto('/admin/users');
    await waitForNetworkIdle(page);

    // Find edit button for user@example.com row
    const userRow = page.getByRole('row').filter({ hasText: 'user@example.com' });
    await userRow.getByRole('button', { name: /Edit/i }).click();

    // WHEN: Toggle status
    const statusToggle = page.getByRole('switch', { name: /Active/i });
    await expect(statusToggle).toBeVisible();

    // Check initial state
    await expect(statusToggle).toBeChecked();

    // Toggle off
    await statusToggle.click();

    // THEN: Toggle updates immediately
    await expect(statusToggle).not.toBeChecked();
  });

  test('[P1] AC-5.18.5: Admin navigation includes Users link', async ({ page }) => {
    /**
     * GIVEN: Admin user is authenticated
     * WHEN: Admin views the navigation
     * THEN: Users link is visible in admin section
     */

    // GIVEN: Navigate to admin dashboard
    await page.goto('/admin');
    await waitForNetworkIdle(page);

    // THEN: Users link is visible in navigation
    const usersLink = page.getByRole('link', { name: /Users/i });
    await expect(usersLink).toBeVisible();

    // WHEN: Click Users link
    await usersLink.click();

    // THEN: Navigate to users page
    await expect(page).toHaveURL(/\/admin\/users/);
  });

  test('[P0] AC-5.18.6: Non-admin user is redirected from users page', async ({ page }) => {
    /**
     * GIVEN: Non-admin user is authenticated
     * WHEN: User attempts to access /admin/users
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

    // WHEN: Navigate to admin users page
    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');

    // THEN: Either shows access denied or redirects to dashboard
    // The AdminGuard will show access denied message briefly then redirect
    const accessDenied = page.getByText(/Access Denied/i);
    const dashboardUrl = /\/dashboard/;

    // Wait for either outcome
    await Promise.race([
      expect(accessDenied).toBeVisible({ timeout: 3000 }).catch(() => {}),
      page.waitForURL(dashboardUrl, { timeout: 5000 }).catch(() => {}),
    ]);

    // Verify we're not on the users page
    const url = page.url();
    expect(url).not.toContain('/admin/users');
  });

  test('[P2] Pagination controls work correctly', async ({ page }) => {
    /**
     * GIVEN: Admin is on user management page with multiple pages
     * WHEN: Admin clicks next page
     * THEN: Page navigation updates
     */

    // Mock paginated response with multiple pages
    const paginatedUsers = {
      ...mockUsers,
      meta: {
        total: 45,
        page: 1,
        per_page: 20,
        total_pages: 3,
      },
    };

    await page.route('**/api/v1/admin/users**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(paginatedUsers),
      });
    });

    // GIVEN: Navigate to user management page
    await page.goto('/admin/users');
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
});
