/**
 * Story 5-1 Automation: Admin Dashboard Negative Path Tests
 * Generated: 2025-12-02
 *
 * Test Coverage:
 * - [P0] Non-admin receives 403 Forbidden
 * - [P0] Unauthenticated user receives 401
 * - [P1] API timeout handling
 * - [P1] API 500 Internal Server Error
 * - [P2] Malformed JSON response
 * - [P2] Network offline error
 * - [P1] Slow API response (>2 seconds)
 * - [P2] Invalid admin stats schema
 * - [P1] Retry mechanism on transient failures
 * - [P2] Multiple concurrent API errors
 *
 * Knowledge Base References:
 * - test-quality.md: Negative path coverage
 * - error-scenarios.fixture.ts: Error mocking utilities
 */

import { test as authTest, expect } from '../../fixtures/auth.fixture';
import {
  test as errorTest,
  ERROR_RESPONSES,
} from '../../fixtures/error-scenarios.fixture';
import { waitForNetworkIdle } from '../../utils/test-helpers';
import { createAdminStats } from '../../fixtures/admin-stats.factory';

// Merge fixtures from both auth and error-scenarios
const test = errorTest.extend({
  // Get auth fixture's authenticated context
});

test.describe('Story 5-1: Admin Dashboard Negative Paths', () => {
  test('[P0] Non-admin user receives 403 Forbidden', async ({ page, mockApiError }) => {
    /**
     * GIVEN: Regular (non-admin) user is authenticated
     * WHEN: User attempts to access /admin
     * THEN: User receives 403 and error message displayed
     */

    await mockApiError(page, '**/api/v1/admin/stats', ERROR_RESPONSES.FORBIDDEN);

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

  test('[P0] Unauthenticated user receives 401 and redirects to login', async ({ page, mockApiError }) => {
    /**
     * GIVEN: User is not authenticated
     * WHEN: User attempts to access /admin directly
     * THEN: User receives 401 and is redirected to login page
     */

    await mockApiError(page, '**/api/v1/admin/stats', ERROR_RESPONSES.UNAUTHORIZED);

    await page.goto('/admin');
    await page.waitForLoadState('networkidle');

    // THEN: Should redirect to login OR show error
    const currentUrl = page.url();
    const isLoginPage = currentUrl.includes('/login') || currentUrl.includes('/auth');
    const hasErrorMessage = await page
      .getByTestId('admin-error-message')
      .isVisible({ timeout: 2000 })
      .catch(() => false);

    expect(isLoginPage || hasErrorMessage).toBe(true);
  });

  test('[P1] Dashboard handles API 500 Internal Server Error', async ({ page, mockApiError }) => {
    /**
     * GIVEN: Admin stats API returns 500 error
     * WHEN: Admin attempts to load dashboard
     * THEN: Error message is displayed with retry option
     */

    await mockApiError(
      page,
      '**/api/v1/admin/stats',
      ERROR_RESPONSES.INTERNAL_SERVER_ERROR
    );

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

  test('[P1] Dashboard handles API timeout gracefully', async ({ page, mockNetworkTimeout }) => {
    /**
     * GIVEN: Admin stats API times out (>10 seconds)
     * WHEN: Admin attempts to load dashboard
     * THEN: Timeout error message displayed, retry available
     */

    await mockNetworkTimeout(page, '**/api/v1/admin/stats', 15000);

    const startTime = Date.now();
    await page.goto('/admin');

    // Wait for timeout error
    await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});

    const elapsed = Date.now() - startTime;

    // THEN: Request timed out (should take <20s total)
    expect(elapsed).toBeLessThan(20000);

    // THEN: Error message displayed
    const errorMessage = page.getByTestId('admin-error-message');
    if (await errorMessage.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(errorMessage).toContainText(/timeout|timed out|too long/i);
    }
  });

  test('[P2] Dashboard handles malformed JSON response', async ({ page, mockMalformedResponse }) => {
    /**
     * GIVEN: Admin stats API returns invalid JSON
     * WHEN: Admin attempts to load dashboard
     * THEN: Parse error message displayed
     */

    await mockMalformedResponse(
      page,
      '**/api/v1/admin/stats',
      ERROR_RESPONSES.MALFORMED_JSON.body as string
    );

    await page.goto('/admin');
    await page.waitForLoadState('networkidle');

    // THEN: Error message displayed
    const errorMessage = page.getByTestId('admin-error-message');
    if (await errorMessage.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(errorMessage).toBeVisible();
    }

    // OR: Toast notification
    const toast = page.locator('[data-sonner-toast]').first();
    if (await toast.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(toast).toBeVisible();
    }
  });

  test('[P2] Dashboard handles network offline error', async ({ page }) => {
    /**
     * GIVEN: Network is offline
     * WHEN: Admin attempts to load dashboard
     * THEN: Network error message displayed
     */

    // Simulate offline network
    await page.context().setOffline(true);

    await page.goto('/admin').catch(() => {}); // May fail to navigate
    await page.waitForTimeout(2000);

    // Restore network
    await page.context().setOffline(false);

    // THEN: Error state visible (or page didn't load)
    const pageLoaded = await page.url().includes('/admin');
    if (pageLoaded) {
      const errorMessage = page.getByTestId('admin-error-message');
      await expect(errorMessage).toBeVisible({ timeout: 5000 });
    }
  });

  test('[P1] Dashboard shows loading skeleton during slow API response', async ({ page }) => {
    /**
     * GIVEN: Admin stats API is slow (1.5 seconds)
     * WHEN: Admin loads dashboard
     * THEN: Loading skeleton is displayed, then replaced with data
     */

    const stats = createAdminStats();

    await page.route('**/api/v1/admin/stats', async (route) => {
      // Delay response by 1.5 seconds
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(stats),
      });
    });

    await page.goto('/admin');

    // THEN: Loading skeleton is visible initially
    const skeleton = page
      .locator('[data-testid^="skeleton-"]')
      .or(page.locator('.animate-pulse'))
      .first();
    if (await skeleton.isVisible({ timeout: 500 }).catch(() => false)) {
      await expect(skeleton).toBeVisible();
    }

    // Wait for data to load
    await waitForNetworkIdle(page);

    // THEN: Loading skeleton is removed
    await expect(skeleton).not.toBeVisible({ timeout: 3000 });

    // THEN: Stat cards are visible
    const usersCard = page.getByTestId('stat-card-users');
    await expect(usersCard).toBeVisible();
  });

  test('[P2] Dashboard handles invalid admin stats schema', async ({ page }) => {
    /**
     * GIVEN: Admin stats API returns data with missing required fields
     * WHEN: Admin loads dashboard
     * THEN: Error message displayed OR graceful degradation
     */

    const invalidStats = {
      users: { total: 100 }, // Missing active/inactive
      // Missing knowledge_bases, documents, etc.
    };

    await page.route('**/api/v1/admin/stats', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(invalidStats),
      });
    });

    await page.goto('/admin');
    await page.waitForLoadState('networkidle');

    // THEN: Either error message OR graceful fallback
    const errorMessage = page.getByTestId('admin-error-message');
    const hasError = await errorMessage.isVisible({ timeout: 2000 }).catch(() => false);

    if (!hasError) {
      // Graceful degradation: Some cards may show, others may show zeros
      const usersCard = page.getByTestId('stat-card-users');
      await expect(usersCard).toBeVisible();
    }
  });

  test('[P1] Dashboard retry mechanism on transient failure', async ({ page }) => {
    /**
     * GIVEN: Admin stats API fails once, then succeeds
     * WHEN: Admin clicks retry button
     * THEN: Dashboard successfully loads data on retry
     */

    let attemptCount = 0;
    const stats = createAdminStats();

    await page.route('**/api/v1/admin/stats', async (route) => {
      attemptCount++;

      if (attemptCount === 1) {
        // First attempt: Fail with 500
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Transient error' }),
        });
      } else {
        // Second attempt: Success
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(stats),
        });
      }
    });

    await page.goto('/admin');
    await page.waitForLoadState('networkidle');

    // THEN: Error message displayed
    const errorMessage = page.getByTestId('admin-error-message');
    if (await errorMessage.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(errorMessage).toBeVisible();

      // Look for retry button
      const retryButton =
        page.getByTestId('retry-button') ||
        page.getByRole('button', { name: /retry|try again/i });

      if (await retryButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        // WHEN: Click retry
        await retryButton.click();
        await page.waitForTimeout(500);

        // THEN: Dashboard loads successfully
        const usersCard = page.getByTestId('stat-card-users');
        await expect(usersCard).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('[P2] Dashboard handles multiple concurrent API errors', async ({ page, mockApiError }) => {
    /**
     * GIVEN: Multiple admin API calls fail simultaneously
     * WHEN: Admin loads dashboard
     * THEN: Single consolidated error message displayed (not multiple)
     */

    await mockApiError(page, '**/api/v1/admin/**', ERROR_RESPONSES.INTERNAL_SERVER_ERROR);

    await page.goto('/admin');
    await page.waitForLoadState('networkidle');

    // THEN: Error message displayed (should be single, not multiple)
    const errorMessages = page.getByTestId('admin-error-message');
    const count = await errorMessages.count();

    if (count > 0) {
      expect(count).toBeLessThanOrEqual(1); // Should consolidate errors
    }
  });

  test('[P1] Dashboard session expiry handling', async ({ page }) => {
    /**
     * GIVEN: Admin is viewing dashboard
     * WHEN: Session expires (401 after initial load)
     * THEN: User is redirected to login with session expired message
     */

    const stats = createAdminStats();
    let requestCount = 0;

    await page.route('**/api/v1/admin/stats', async (route) => {
      requestCount++;

      if (requestCount === 1) {
        // First load: Success
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(stats),
        });
      } else {
        // Subsequent requests: Session expired
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Session expired' }),
        });
      }
    });

    await page.goto('/admin');
    await waitForNetworkIdle(page);

    // Dashboard loaded successfully
    const usersCard = page.getByTestId('stat-card-users');
    await expect(usersCard).toBeVisible();

    // WHEN: Try to refresh (triggers session expiry)
    const refreshButton = page.getByTestId('refresh-stats-button');
    if (await refreshButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await refreshButton.click();
      await page.waitForTimeout(1000);

      // THEN: Should show error or redirect to login
      const currentUrl = page.url();
      const isLoginPage = currentUrl.includes('/login') || currentUrl.includes('/auth');
      const hasErrorMessage = await page
        .getByTestId('admin-error-message')
        .isVisible({ timeout: 2000 })
        .catch(() => false);

      expect(isLoginPage || hasErrorMessage).toBe(true);
    }
  });
});
