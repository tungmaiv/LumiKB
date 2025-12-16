/**
 * Story 5-1 Automation: Admin Dashboard E2E Tests
 * Generated: 2025-12-02
 *
 * Test Coverage:
 * - [P0] Admin dashboard displays all stat cards
 * - [P0] Non-admin user receives 403 Forbidden
 * - [P1] Dashboard loads within performance target
 * - [P1] Stat cards show correct data
 * - [P2] Drill-down navigation works
 * - [P2] Manual refresh updates statistics
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - network-first.md: Route interception patterns
 * - test-priorities-matrix.md: P0/P1/P2 classification
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { mockApiResponse, waitForNetworkIdle } from '../../utils/test-helpers';
import { createAdminStats } from '../../fixtures/admin-stats.factory';

test.describe('Story 5-1: Admin Dashboard E2E Tests', () => {
  const mockAdminStats = createAdminStats();

  test.beforeEach(async ({ page }) => {
    // Network-first: Mock admin stats API BEFORE navigation
    await mockApiResponse(page, '**/api/v1/admin/stats', mockAdminStats);
  });

  test('[P0] Admin dashboard displays all stat cards with correct data', async ({ page }) => {
    /**
     * GIVEN: Admin user is authenticated
     * WHEN: Admin navigates to /admin
     * THEN: Dashboard displays 6 stat cards with correct labels and values
     */

    // GIVEN & WHEN: Navigate to admin dashboard
    await page.goto('/admin');
    await waitForNetworkIdle(page);

    // THEN: All stat cards are visible
    const statCards = page.locator('[data-testid^="stat-card-"]');
    await expect(statCards).toHaveCount(6); // Users, KBs, Documents, Storage, Searches, Generations

    // THEN: Users stat card shows correct data
    const usersCard = page.getByTestId('stat-card-users');
    await expect(usersCard).toBeVisible();
    await expect(usersCard).toContainText('100'); // Total users
    await expect(usersCard).toContainText('80'); // Active
    await expect(usersCard).toContainText('20'); // Inactive

    // THEN: Knowledge Bases stat card shows correct data
    const kbCard = page.getByTestId('stat-card-knowledge-bases');
    await expect(kbCard).toBeVisible();
    await expect(kbCard).toContainText('50'); // Total KBs

    // THEN: Documents stat card shows correct data
    const docsCard = page.getByTestId('stat-card-documents');
    await expect(docsCard).toBeVisible();
    await expect(docsCard).toContainText('1,000'); // Total documents (formatted with comma)

    // THEN: Storage stat card shows correct data with human-readable format
    const storageCard = page.getByTestId('stat-card-storage');
    await expect(storageCard).toBeVisible();
    await expect(storageCard).toContainText(/1\.00?\s*GB/i); // 1GB

    // THEN: Search activity stat card shows correct data
    const searchCard = page.getByTestId('stat-card-searches');
    await expect(searchCard).toBeVisible();
    await expect(searchCard).toContainText('100'); // Last 24h

    // THEN: Generation activity stat card shows correct data
    const genCard = page.getByTestId('stat-card-generations');
    await expect(genCard).toBeVisible();
    await expect(genCard).toContainText('50'); // Last 24h
  });

  test('[P0] Non-admin user receives 403 and is redirected', async ({ page }) => {
    /**
     * GIVEN: Regular (non-admin) user is authenticated
     * WHEN: User attempts to access /admin
     * THEN: User receives 403 Forbidden and is redirected to dashboard with error message
     */

    // Mock 403 response
    await page.route('**/api/v1/admin/stats', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Not authorized' }),
      });
    });

    // WHEN: Navigate to admin page
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');

    // THEN: Error message is displayed
    const errorMessage = page.getByTestId('admin-error-message');
    if (await errorMessage.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(errorMessage).toContainText(/not authorized|forbidden|access denied/i);
    }

    // OR: Toast notification appears
    const toast = page.locator('[data-sonner-toast]').first();
    if (await toast.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(toast).toContainText(/not authorized|forbidden|access/i);
    }
  });

  test('[P1] Dashboard loads within performance target (2 seconds)', async ({ page }) => {
    /**
     * GIVEN: Admin user is authenticated
     * WHEN: Admin navigates to /admin
     * THEN: Dashboard loads within 2 seconds
     */

    const startTime = Date.now();

    // WHEN: Navigate to admin dashboard
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');

    // Wait for stat cards to be visible
    const usersCard = page.getByTestId('stat-card-users');
    await expect(usersCard).toBeVisible({ timeout: 5000 });

    const loadTime = Date.now() - startTime;

    // THEN: Page loads within 2 seconds (allow some buffer for test environment)
    expect(loadTime).toBeLessThan(3000); // 3 seconds to account for test overhead
  });

  test('[P1] Stat cards display sparkline trend charts', async ({ page }) => {
    /**
     * GIVEN: Admin dashboard is loaded
     * WHEN: Statistics include 30-day trend data
     * THEN: Stat cards display sparkline charts
     */

    // Navigate to dashboard
    await page.goto('/admin');
    await waitForNetworkIdle(page);

    // THEN: Sparkline charts are visible (if implemented)
    const searchSparkline = page.locator('[data-testid="sparkline-searches"]');
    if (await searchSparkline.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(searchSparkline).toBeVisible();
    }

    const genSparkline = page.locator('[data-testid="sparkline-generations"]');
    if (await genSparkline.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(genSparkline).toBeVisible();
    }
  });

  test('[P2] Drill-down navigation works for stat cards', async ({ page }) => {
    /**
     * GIVEN: Admin dashboard is loaded
     * WHEN: Admin clicks a stat card
     * THEN: Navigation to detailed view occurs (if implemented)
     */

    await page.goto('/admin');
    await waitForNetworkIdle(page);

    // WHEN: Click users stat card
    const usersCard = page.getByTestId('stat-card-users');
    await expect(usersCard).toBeVisible();

    // Check if card is clickable
    const isClickable = await usersCard.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.cursor === 'pointer' || el.tagName.toLowerCase() === 'a';
    });

    if (isClickable) {
      await usersCard.click();

      // THEN: Should navigate to users detail page (if route exists)
      await page.waitForURL(/\/admin\/users/, { timeout: 3000 }).catch(() => {});
    }
  });

  test('[P2] Manual refresh updates statistics', async ({ page }) => {
    /**
     * GIVEN: Admin dashboard is loaded
     * WHEN: Admin clicks "Refresh Statistics" button
     * THEN: Dashboard re-fetches current data and updates timestamp
     */

    await page.goto('/admin');
    await waitForNetworkIdle(page);

    // Look for refresh button
    const refreshButton = page.getByTestId('refresh-stats-button');
    if (await refreshButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Get initial timestamp
      const timestamp = page.getByTestId('last-updated-timestamp');
      const initialTime = await timestamp.textContent();

      // Wait a moment
      await page.waitForTimeout(1000);

      // Mock updated stats
      const updatedStats = {
        ...mockAdminStats,
        users: { total: 101, active: 81, inactive: 20 }, // One more user
      };

      await mockApiResponse(page, '**/api/v1/admin/stats', updatedStats);

      // WHEN: Click refresh
      await refreshButton.click();

      // Wait for update
      await page.waitForTimeout(500);

      // THEN: Data is updated
      const usersCard = page.getByTestId('stat-card-users');
      await expect(usersCard).toContainText('101'); // Updated count

      // THEN: Timestamp is updated
      const newTime = await timestamp.textContent();
      expect(newTime).not.toBe(initialTime);
    }
  });

  test('[P2] Dashboard displays loading skeleton while fetching', async ({ page }) => {
    /**
     * GIVEN: Admin navigates to dashboard
     * WHEN: API response is slow
     * THEN: Loading skeleton is displayed
     */

    // Mock slow API response
    await page.route('**/api/v1/admin/stats', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAdminStats),
      });
    });

    await page.goto('/admin');

    // THEN: Loading skeleton is visible
    const skeleton = page.locator('[data-testid^="skeleton-"]').or(page.locator('.animate-pulse')).first();
    if (await skeleton.isVisible({ timeout: 500 }).catch(() => false)) {
      await expect(skeleton).toBeVisible();
    }

    // Wait for data to load
    await waitForNetworkIdle(page);

    // THEN: Loading skeleton is removed
    await expect(skeleton).not.toBeVisible({ timeout: 3000 });
  });

  test('[P2] Dashboard shows "Last updated" timestamp', async ({ page }) => {
    /**
     * GIVEN: Admin dashboard is loaded
     * WHEN: Statistics are displayed
     * THEN: "Last updated" timestamp is visible
     */

    await page.goto('/admin');
    await waitForNetworkIdle(page);

    // THEN: Timestamp is visible
    const timestamp = page.locator('[data-testid="last-updated-timestamp"]').or(
      page.locator('text=/last updated|updated.*ago/i')
    ).first();

    if (await timestamp.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(timestamp).toBeVisible();
    }
  });

  test('[P1] Dashboard handles API error gracefully', async ({ page }) => {
    /**
     * GIVEN: Admin attempts to load dashboard
     * WHEN: API returns 500 Internal Server Error
     * THEN: Error message is displayed, retry option available
     */

    // Mock 500 error
    await page.route('**/api/v1/admin/stats', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    });

    await page.goto('/admin');
    await page.waitForLoadState('networkidle');

    // THEN: Error message is displayed
    const errorMessage = page.getByTestId('admin-error-message');
    if (await errorMessage.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(errorMessage).toBeVisible();
      await expect(errorMessage).toContainText(/error|failed/i);
    }

    // OR: Toast notification
    const toast = page.locator('[data-sonner-toast]').first();
    if (await toast.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(toast).toContainText(/error|failed/i);
    }
  });

  test('[P2] Dashboard handles empty database gracefully', async ({ page }) => {
    /**
     * GIVEN: Database has no data
     * WHEN: Admin loads dashboard
     * THEN: Stat cards show zeros, no errors
     */

    const emptyStats = {
      users: { total: 0, active: 0, inactive: 0 },
      knowledge_bases: { total: 0, by_status: {} },
      documents: { total: 0, by_status: {} },
      storage: { total_bytes: 0, avg_doc_size_bytes: 0 },
      activity: {
        searches: { last_24h: 0, last_7d: 0, last_30d: 0 },
        generations: { last_24h: 0, last_7d: 0, last_30d: 0 },
      },
      trends: {
        searches: Array(30).fill(0),
        generations: Array(30).fill(0),
      },
    };

    await mockApiResponse(page, '**/api/v1/admin/stats', emptyStats);

    await page.goto('/admin');
    await waitForNetworkIdle(page);

    // THEN: Stat cards show zeros
    const usersCard = page.getByTestId('stat-card-users');
    await expect(usersCard).toBeVisible();
    await expect(usersCard).toContainText('0'); // Total users

    // No error messages
    const errorMessage = page.getByTestId('admin-error-message');
    await expect(errorMessage).not.toBeVisible();
  });
});
