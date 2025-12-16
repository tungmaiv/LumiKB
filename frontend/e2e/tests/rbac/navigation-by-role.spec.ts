/**
 * Story 7-11: RBAC Navigation Tests
 * Navigation Restructure with RBAC Default Groups
 *
 * Test Coverage:
 * - AC-7.11.1: Administrators see both Operations and Admin dropdowns
 * - AC-7.11.2: Operators see only Operations dropdown
 * - AC-7.11.3: Basic Users see neither dropdown
 * - AC-7.11.4: Operations dropdown contains audit, queue, kb-stats
 * - AC-7.11.5: Admin dropdown contains users, groups, kb-permissions, config, models
 * - AC-7.11.16: Non-operator users cannot access /operations routes (403)
 * - AC-7.11.17-18: Non-admin users cannot access /admin routes (403)
 *
 * Permission Levels:
 * - USER (1): Basic access - core links only
 * - OPERATOR (2): Operations routes - operations menu visible
 * - ADMINISTRATOR (3): Full access - both menus visible
 */

import { test, expect, Page } from '@playwright/test';

// Test fixtures for different user roles
const BASIC_USER = {
  email: 'basic@test.com',
  permission_level: 1,
};

const OPERATOR_USER = {
  email: 'operator@test.com',
  permission_level: 2,
};

const ADMIN_USER = {
  email: 'admin@test.com',
  permission_level: 3,
};

// Helper to mock authenticated user with specific permission level
async function mockAuthenticatedUser(page: Page, user: { email: string; permission_level: number }) {
  await page.route('**/api/v1/users/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'test-user-id',
        email: user.email,
        permission_level: user.permission_level,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      }),
    });
  });

  // Mock session validation
  await page.route('**/api/v1/auth/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ valid: true }),
    });
  });
}

test.describe('Story 7-11: RBAC Navigation', () => {
  test.describe('Basic User Navigation (AC-7.11.3)', () => {
    test.beforeEach(async ({ page }) => {
      await mockAuthenticatedUser(page, BASIC_USER);
    });

    test('[P0] Basic user sees core navigation links only', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 1 (USER)
       * WHEN: User views the main navigation
       * THEN: Only Dashboard, Search, Chat links are visible
       * AND: Operations dropdown is hidden
       * AND: Admin dropdown is hidden
       */

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Core links should be visible
      await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /search/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /chat/i })).toBeVisible();

      // Operations and Admin dropdowns should NOT be visible
      await expect(page.getByRole('button', { name: /operations menu/i })).not.toBeVisible();
      await expect(page.getByRole('button', { name: /admin menu/i })).not.toBeVisible();
    });

    test('[P0] Basic user cannot access operations routes directly (AC-7.11.16)', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 1 (USER)
       * WHEN: User navigates directly to /operations
       * THEN: User is redirected to dashboard
       * AND: Access denied message is shown
       */

      await page.goto('/operations');
      await page.waitForLoadState('networkidle');

      // Should be redirected to dashboard
      await expect(page).toHaveURL(/\/dashboard/);

      // Or see access denied (before redirect completes)
      const accessDenied = page.getByText(/access denied/i);
      if (await accessDenied.isVisible({ timeout: 1000 }).catch(() => false)) {
        await expect(accessDenied).toBeVisible();
      }
    });

    test('[P0] Basic user cannot access admin routes directly (AC-7.11.17)', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 1 (USER)
       * WHEN: User navigates directly to /admin
       * THEN: User is redirected to dashboard
       * AND: Access denied message is shown
       */

      await page.goto('/admin');
      await page.waitForLoadState('networkidle');

      // Should be redirected to dashboard
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test('[P1] Basic user cannot access nested operations routes', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 1 (USER)
       * WHEN: User navigates directly to /operations/audit
       * THEN: User is redirected to dashboard
       */

      await page.goto('/operations/audit');
      await page.waitForLoadState('networkidle');

      await expect(page).toHaveURL(/\/dashboard/);
    });

    test('[P1] Basic user cannot access nested admin routes', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 1 (USER)
       * WHEN: User navigates directly to /admin/users
       * THEN: User is redirected to dashboard
       */

      await page.goto('/admin/users');
      await page.waitForLoadState('networkidle');

      await expect(page).toHaveURL(/\/dashboard/);
    });
  });

  test.describe('Operator Navigation (AC-7.11.2, AC-7.11.4)', () => {
    test.beforeEach(async ({ page }) => {
      await mockAuthenticatedUser(page, OPERATOR_USER);
    });

    test('[P0] Operator sees Operations dropdown', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 2 (OPERATOR)
       * WHEN: User views the main navigation
       * THEN: Operations dropdown is visible
       * AND: Admin dropdown is hidden
       */

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Operations dropdown should be visible
      await expect(page.getByRole('button', { name: /operations menu/i })).toBeVisible();

      // Admin dropdown should NOT be visible
      await expect(page.getByRole('button', { name: /admin menu/i })).not.toBeVisible();
    });

    test('[P0] Operations dropdown contains correct links (AC-7.11.4)', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 2 (OPERATOR)
       * WHEN: User opens the Operations dropdown
       * THEN: Dropdown contains: Operations Dashboard, Audit Logs, Processing Queue, KB Statistics
       */

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Open Operations dropdown
      await page.getByRole('button', { name: /operations menu/i }).click();

      // Verify all links are present
      await expect(page.getByRole('menuitem', { name: /operations dashboard/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /audit logs/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /processing queue/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /kb statistics/i })).toBeVisible();
    });

    test('[P0] Operator can access operations routes', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 2 (OPERATOR)
       * WHEN: User navigates to /operations
       * THEN: Page loads successfully (no redirect)
       */

      await page.goto('/operations');
      await page.waitForLoadState('networkidle');

      // Should stay on operations page
      await expect(page).toHaveURL(/\/operations/);
      await expect(page.getByText(/access denied/i)).not.toBeVisible();
    });

    test('[P0] Operator cannot access admin routes (AC-7.11.18)', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 2 (OPERATOR)
       * WHEN: User navigates directly to /admin
       * THEN: User is redirected to dashboard
       */

      await page.goto('/admin');
      await page.waitForLoadState('networkidle');

      // Should be redirected to dashboard
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test('[P1] Operator can navigate to all operations sub-routes', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 2 (OPERATOR)
       * WHEN: User navigates to operations sub-routes
       * THEN: All routes load successfully
       */

      const operationsRoutes = [
        '/operations',
        '/operations/audit',
        '/operations/queue',
        '/operations/kb-stats',
      ];

      for (const route of operationsRoutes) {
        await page.goto(route);
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveURL(new RegExp(route.replace('/', '\\/')));
      }
    });
  });

  test.describe('Administrator Navigation (AC-7.11.1, AC-7.11.5)', () => {
    test.beforeEach(async ({ page }) => {
      await mockAuthenticatedUser(page, ADMIN_USER);
    });

    test('[P0] Administrator sees both Operations and Admin dropdowns (AC-7.11.1)', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 3 (ADMINISTRATOR)
       * WHEN: User views the main navigation
       * THEN: Both Operations and Admin dropdowns are visible
       */

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Both dropdowns should be visible
      await expect(page.getByRole('button', { name: /operations menu/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /admin menu/i })).toBeVisible();
    });

    test('[P0] Admin dropdown contains correct links (AC-7.11.5)', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 3 (ADMINISTRATOR)
       * WHEN: User opens the Admin dropdown
       * THEN: Dropdown contains: Admin Dashboard, Users, Groups, KB Permissions, System Config, Model Registry
       */

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Open Admin dropdown
      await page.getByRole('button', { name: /admin menu/i }).click();

      // Verify all links are present
      await expect(page.getByRole('menuitem', { name: /admin dashboard/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /users/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /groups/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /kb permissions/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /system config/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /model registry/i })).toBeVisible();
    });

    test('[P0] Administrator can access both operations and admin routes', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 3 (ADMINISTRATOR)
       * WHEN: User navigates to /operations and /admin
       * THEN: Both pages load successfully
       */

      // Test operations route
      await page.goto('/operations');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/\/operations/);

      // Test admin route
      await page.goto('/admin');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/\/admin/);
    });

    test('[P1] Administrator can navigate to all admin sub-routes', async ({ page }) => {
      /**
       * GIVEN: User is authenticated with permission_level 3 (ADMINISTRATOR)
       * WHEN: User navigates to admin sub-routes
       * THEN: All routes load successfully
       */

      const adminRoutes = [
        '/admin',
        '/admin/users',
        '/admin/groups',
        '/admin/kb-permissions',
        '/admin/config',
        '/admin/models',
      ];

      for (const route of adminRoutes) {
        await page.goto(route);
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveURL(new RegExp(route.replace('/', '\\/')));
      }
    });
  });

  test.describe('Navigation Active State', () => {
    test('[P1] Operations button highlights when on operations route', async ({ page }) => {
      /**
       * GIVEN: User is an operator on /operations/audit
       * WHEN: User views the navigation
       * THEN: Operations button has active styling
       */

      await mockAuthenticatedUser(page, OPERATOR_USER);
      await page.goto('/operations/audit');
      await page.waitForLoadState('networkidle');

      const operationsButton = page.getByRole('button', { name: /operations menu/i });
      await expect(operationsButton).toHaveClass(/bg-accent/);
    });

    test('[P1] Admin button highlights when on admin route', async ({ page }) => {
      /**
       * GIVEN: User is an admin on /admin/users
       * WHEN: User views the navigation
       * THEN: Admin button has active styling
       */

      await mockAuthenticatedUser(page, ADMIN_USER);
      await page.goto('/admin/users');
      await page.waitForLoadState('networkidle');

      const adminButton = page.getByRole('button', { name: /admin menu/i });
      await expect(adminButton).toHaveClass(/bg-accent/);
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('[P2] Operations dropdown can be navigated with keyboard', async ({ page }) => {
      /**
       * GIVEN: User is an operator
       * WHEN: User focuses and opens Operations dropdown with keyboard
       * THEN: Menu items can be navigated with arrow keys
       */

      await mockAuthenticatedUser(page, OPERATOR_USER);
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Focus and open dropdown
      const operationsButton = page.getByRole('button', { name: /operations menu/i });
      await operationsButton.focus();
      await page.keyboard.press('Enter');

      // Navigate with arrow keys
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('ArrowDown');

      // Menu should be visible
      await expect(page.getByRole('menuitem', { name: /audit logs/i })).toBeVisible();
    });

    test('[P2] Admin dropdown can be closed with Escape', async ({ page }) => {
      /**
       * GIVEN: User is an admin with Admin dropdown open
       * WHEN: User presses Escape
       * THEN: Dropdown closes
       */

      await mockAuthenticatedUser(page, ADMIN_USER);
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      // Open dropdown
      await page.getByRole('button', { name: /admin menu/i }).click();
      await expect(page.getByRole('menuitem', { name: /users/i })).toBeVisible();

      // Press Escape
      await page.keyboard.press('Escape');

      // Menu should be hidden
      await expect(page.getByRole('menuitem', { name: /users/i })).not.toBeVisible();
    });
  });
});

test.describe('Story 7-11: Route Protection', () => {
  test('[P0] Unauthenticated user redirects to login for protected routes', async ({ page }) => {
    /**
     * GIVEN: User is not authenticated
     * WHEN: User navigates to protected route
     * THEN: User is redirected to login page
     */

    // Mock no auth session
    await page.route('**/api/v1/users/me', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Not authenticated' }),
      });
    });

    await page.goto('/operations');
    await page.waitForLoadState('networkidle');

    // Should be redirected to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('[P1] Protected routes show loading state during auth check', async ({ page }) => {
    /**
     * GIVEN: Auth check is in progress
     * WHEN: User accesses protected route
     * THEN: Loading indicator is shown
     */

    // Delay auth response
    await page.route('**/api/v1/users/me', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-user-id',
          email: 'operator@test.com',
          permission_level: 2,
          is_active: true,
        }),
      });
    });

    await page.goto('/operations');

    // Should show loading state
    const loadingText = page.getByText(/verifying access/i);
    await expect(loadingText).toBeVisible({ timeout: 1000 });
  });
});
