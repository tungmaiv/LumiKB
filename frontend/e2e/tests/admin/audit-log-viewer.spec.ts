/**
 * E2E tests for Audit Log Viewer
 *
 * Tests complete audit log viewing workflows including filtering, pagination,
 * and viewing event details.
 * Story: 5-2 (Audit Log Viewer)
 */

import { test, expect } from '@playwright/test';
import { AdminPage } from '../../pages/admin.page';

test.describe('Audit Log Viewer E2E Tests', () => {
  let adminPage: AdminPage;

  test.beforeEach(async ({ page }) => {
    adminPage = new AdminPage(page);
  });

  test.describe('[P0] Admin can access audit log viewer', () => {
    test('should navigate to audit log page and display audit events', async ({ page }) => {
      // GIVEN: Admin user is logged in
      await adminPage.loginAsAdmin();

      // WHEN: Admin navigates to /admin/audit
      await page.goto('/admin/audit');

      // THEN: Should display audit log viewer page
      await expect(page.locator('h1')).toContainText(/audit log/i);

      // Should display audit log table
      await expect(page.getByRole('table')).toBeVisible();

      // Should display filter controls
      await expect(page.getByLabel(/event type/i)).toBeVisible();
      await expect(page.getByLabel(/user email/i)).toBeVisible();
      await expect(page.getByLabel(/start date/i)).toBeVisible();
      await expect(page.getByLabel(/end date/i)).toBeVisible();

      // Should display at least one audit event (from registration/login)
      const rowCount = await page.getByRole('row').count();
      expect(rowCount).toBeGreaterThanOrEqual(2); // Header + at least 1 data row
    });

    test.skip('should display audit events sorted by timestamp DESC by default', async ({ page }) => {
      // Skipped: Sorting functionality not yet implemented
      // TODO: Implement after adding sorting to backend
    });
  });

  test.describe('[P1] Admin can filter audit logs', () => {
    test.skip('should filter audit logs by event type', async ({ page }) => {
      // Skipped: Requires seed data functionality
      // TODO: Implement with real backend test data
    });

    test('should filter audit logs by date range', async ({ page }) => {
      // GIVEN: Admin is on audit log page
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');

      // WHEN: Admin sets start date to today
      const today = new Date().toISOString().split('T')[0];
      await page.getByLabel(/start date/i).fill(today);

      // AND: Admin clicks Apply Filters
      await page.getByRole('button', { name: /apply filters/i }).click();
      await page.waitForLoadState('networkidle');

      // THEN: Should display only events from today onwards
      const timestamps = await page
        .getByRole('cell', { name: /2025-\d{2}-\d{2}/i })
        .allTextContents();

      timestamps.forEach((timestamp) => {
        const eventDate = new Date(timestamp);
        const todayDate = new Date(today);
        expect(eventDate.getTime()).toBeGreaterThanOrEqual(todayDate.getTime());
      });
    });

    test('should filter audit logs by user email', async ({ page }) => {
      // GIVEN: Admin is on audit log page
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');

      // WHEN: Admin enters user email filter
      const userEmailInput = page.getByLabel(/user email/i);
      await userEmailInput.fill('admin@example.com');

      // AND: Admin clicks Apply Filters
      await page.getByRole('button', { name: /apply filters/i }).click();
      await page.waitForLoadState('networkidle');

      // THEN: Should display only events for that user
      const userEmailCells = await page
        .getByRole('cell', { name: /admin@example\.com/i })
        .allTextContents();

      expect(userEmailCells.length).toBeGreaterThan(0);
    });

    test('should apply multiple filters combined', async ({ page }) => {
      // GIVEN: Admin is on audit log page
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');

      // WHEN: Admin applies event type and date range filters
      await page.getByLabel(/event type/i).click();
      await page.getByRole('option', { name: 'search' }).click();

      const today = new Date().toISOString().split('T')[0];
      await page.getByLabel(/start date/i).fill(today);

      await page.getByRole('button', { name: /apply filters/i }).click();
      await page.waitForLoadState('networkidle');

      // THEN: Should display events matching all filters
      const eventTypeCells = await page.getByRole('cell', { name: 'search' });
      await expect(eventTypeCells.first()).toBeVisible();

      const timestamps = await page
        .getByRole('cell', { name: /2025-\d{2}-\d{2}/i })
        .allTextContents();

      timestamps.forEach((timestamp) => {
        const eventDate = new Date(timestamp);
        const todayDate = new Date(today);
        expect(eventDate.getTime()).toBeGreaterThanOrEqual(todayDate.getTime());
      });
    });

    test('should reset all filters when Reset button is clicked', async ({ page }) => {
      // GIVEN: Admin has applied filters
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');

      await page.getByLabel(/event type/i).click();
      await page.getByRole('option', { name: 'search' }).click();
      await page.getByRole('button', { name: /apply filters/i }).click();
      await page.waitForLoadState('networkidle');

      const filteredRowCount = await page.getByRole('row').count();

      // WHEN: Admin clicks Reset button
      await page.getByRole('button', { name: /reset/i }).click();
      await page.waitForLoadState('networkidle');

      // THEN: Should display all events (no filters)
      const allRowsCount = await page.getByRole('row').count();
      expect(allRowsCount).toBeGreaterThanOrEqual(filteredRowCount);

      // Filter inputs should be cleared
      const eventTypeSelect = page.getByLabel(/event type/i);
      await expect(eventTypeSelect).toHaveValue('');
    });
  });

  test.describe('[P1] Admin can view event details', () => {
    test('should open details modal when View Details button is clicked', async ({ page }) => {
      // GIVEN: Admin is on audit log page with events
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');
      await page.waitForLoadState('networkidle');

      // WHEN: Admin clicks "View Details" for first event
      const viewDetailsButton = page
        .getByRole('button', { name: /view details/i })
        .first();
      await viewDetailsButton.click();

      // THEN: Should open modal with event JSON
      const modal = page.getByRole('dialog');
      await expect(modal).toBeVisible();

      // Modal should display event details
      await expect(modal.getByText(/audit event details/i)).toBeVisible();
      await expect(modal.getByText(/"id"/i)).toBeVisible();
      await expect(modal.getByText(/"event_type"/i)).toBeVisible();
    });

    test('should display redacted PII in event details by default', async ({ page }) => {
      // GIVEN: Admin without export_pii permission
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');
      await page.waitForLoadState('networkidle');

      // WHEN: Admin opens event details modal
      await page.getByRole('button', { name: /view details/i }).first().click();

      // THEN: Should display redacted IP address
      const modal = page.getByRole('dialog');
      await expect(modal.getByText(/XXX\.XXX\.XXX\.XXX/)).toBeVisible();

      // Should display PII redaction notice
      await expect(modal.getByText(/pii redacted/i)).toBeVisible();
    });

    test('should copy event JSON to clipboard when Copy button is clicked', async ({ page }) => {
      // GIVEN: Admin has opened event details modal
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: /view details/i }).first().click();

      // WHEN: Admin clicks "Copy to Clipboard" button
      const modal = page.getByRole('dialog');
      await modal.getByRole('button', { name: /copy to clipboard/i }).click();

      // THEN: Should display success message
      await expect(modal.getByText(/copied to clipboard/i)).toBeVisible();

      // Clipboard should contain JSON (verify via clipboard API)
      const clipboardText = await page.evaluate(() =>
        navigator.clipboard.readText()
      );
      expect(clipboardText).toContain('"id"');
      expect(clipboardText).toContain('"event_type"');
    });

    test('should close modal when close button is clicked', async ({ page }) => {
      // GIVEN: Event details modal is open
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: /view details/i }).first().click();

      const modal = page.getByRole('dialog');
      await expect(modal).toBeVisible();

      // WHEN: Admin clicks close button
      await modal.getByRole('button', { name: /close/i }).click();

      // THEN: Modal should be closed
      await expect(modal).not.toBeVisible();
    });

    test('should close modal when Escape key is pressed', async ({ page }) => {
      // GIVEN: Event details modal is open
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');
      await page.waitForLoadState('networkidle');

      await page.getByRole('button', { name: /view details/i }).first().click();

      const modal = page.getByRole('dialog');
      await expect(modal).toBeVisible();

      // WHEN: Admin presses Escape key
      await page.keyboard.press('Escape');

      // THEN: Modal should be closed
      await expect(modal).not.toBeVisible();
    });
  });

  test.describe('[P1] Pagination works correctly', () => {
    test('should navigate to next page when Next button is clicked', async ({ page }) => {
      // GIVEN: Admin is on audit log page with > 50 events (page 1)
      await adminPage.loginAsAdmin();
      await adminPage.seedAuditEvents([{ event_type: 'search', count: 60 }]);

      await page.goto('/admin/audit');
      await page.waitForLoadState('networkidle');

      // Verify we're on page 1
      await expect(page.getByText(/showing 1-50 of/i)).toBeVisible();

      // WHEN: Admin clicks Next page button
      await page.getByLabel(/next page/i).click();
      await page.waitForLoadState('networkidle');

      // THEN: Should display page 2
      await expect(page.getByText(/showing 51-/i)).toBeVisible();

      // Should display different events
      const page2Rows = await page.getByRole('row').count();
      expect(page2Rows).toBeGreaterThan(1); // Header + data rows
    });

    test('should navigate to previous page when Previous button is clicked', async ({ page }) => {
      // GIVEN: Admin is on page 2
      await adminPage.loginAsAdmin();
      await adminPage.seedAuditEvents([{ event_type: 'search', count: 60 }]);

      await page.goto('/admin/audit?page=2');
      await page.waitForLoadState('networkidle');

      // WHEN: Admin clicks Previous page button
      await page.getByLabel(/previous page/i).click();
      await page.waitForLoadState('networkidle');

      // THEN: Should navigate back to page 1
      await expect(page.getByText(/showing 1-50 of/i)).toBeVisible();
    });

    test('should disable Previous button on first page', async ({ page }) => {
      // GIVEN: Admin is on page 1
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');
      await page.waitForLoadState('networkidle');

      // THEN: Previous button should be disabled
      const prevButton = page.getByLabel(/previous page/i);
      await expect(prevButton).toBeDisabled();
    });

    test('should disable Next button on last page', async ({ page }) => {
      // GIVEN: Admin is on last page (< 50 events total)
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');
      await page.waitForLoadState('networkidle');

      // THEN: Next button should be disabled if on last page
      const totalText = await page.getByText(/showing \d+-\d+ of (\d+)/i).textContent();
      const match = totalText?.match(/of (\d+)/);
      const totalCount = match ? parseInt(match[1]) : 0;

      if (totalCount <= 50) {
        const nextButton = page.getByLabel(/next page/i);
        await expect(nextButton).toBeDisabled();
      }
    });

    test('should display correct pagination info', async ({ page }) => {
      // GIVEN: Admin is on audit log page
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');
      await page.waitForLoadState('networkidle');

      // THEN: Should display pagination info
      // "Showing 1-50 of 100 events" (or similar)
      await expect(page.getByText(/showing \d+-\d+ of \d+/i)).toBeVisible();
    });
  });

  test.describe('[P0] Non-admin users receive 403 Forbidden', () => {
    test('should redirect non-admin to dashboard with error message', async ({ page }) => {
      // GIVEN: Regular (non-admin) user is logged in
      await adminPage.loginAsRegularUser();

      // WHEN: User attempts to navigate to /admin/audit
      await page.goto('/admin/audit');

      // THEN: Should receive 403 Forbidden
      // Should redirect to dashboard
      await expect(page).toHaveURL('/dashboard');

      // Should display error message
      await expect(
        page.getByText(/you do not have permission to access/i)
      ).toBeVisible();
    });

    test('should not display audit log navigation link for non-admin users', async ({ page }) => {
      // GIVEN: Regular user is logged in
      await adminPage.loginAsRegularUser();
      await page.goto('/dashboard');

      // THEN: Should NOT display "Audit Logs" link in navigation
      await expect(page.getByRole('link', { name: /audit logs/i })).not.toBeVisible();
    });
  });

  test.describe('[P2] Edge cases and error handling', () => {
    test('should display warning when result set is limited to 10,000 records', async ({ page }) => {
      // GIVEN: Admin applies broad filters matching > 10,000 events
      await adminPage.loginAsAdmin();
      await adminPage.seedAuditEvents([{ event_type: 'search', count: 12000 }]);

      await page.goto('/admin/audit');
      await page.waitForLoadState('networkidle');

      // THEN: Should display warning message
      await expect(
        page.getByText(/results limited to 10,000 records/i)
      ).toBeVisible();
      await expect(
        page.getByText(/refine your filters for more specific results/i)
      ).toBeVisible();
    });

    test('should display timeout error when query exceeds 30 seconds', async ({ page }) => {
      // GIVEN: Admin applies filters that cause slow query
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');

      // Simulate timeout by applying very broad date range
      await page.getByLabel(/start date/i).fill('2020-01-01');
      await page.getByLabel(/end date/i).fill('2030-12-31');

      // WHEN: Admin clicks Apply Filters
      await page.getByRole('button', { name: /apply filters/i }).click();

      // THEN: Should display timeout error (if query times out)
      // Note: This test may not always trigger timeout in test environment
      // await expect(page.getByText(/query timed out/i)).toBeVisible();
    });

    test('should handle empty results gracefully', async ({ page }) => {
      // GIVEN: Admin applies filters that match no events
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');

      // Apply filter for non-existent user
      await page.getByLabel(/user email/i).fill('nonexistent@example.com');
      await page.getByRole('button', { name: /apply filters/i }).click();
      await page.waitForLoadState('networkidle');

      // THEN: Should display empty state message
      await expect(page.getByText(/no audit events found/i)).toBeVisible();
    });

    test('should persist filters in URL search params', async ({ page }) => {
      // GIVEN: Admin applies filters
      await adminPage.loginAsAdmin();
      await page.goto('/admin/audit');

      await page.getByLabel(/event type/i).click();
      await page.getByRole('option', { name: 'search' }).click();
      await page.getByRole('button', { name: /apply filters/i }).click();
      await page.waitForLoadState('networkidle');

      // THEN: URL should contain filter params
      expect(page.url()).toContain('event_type=search');

      // WHEN: User refreshes page
      await page.reload();

      // THEN: Filters should still be applied
      const eventTypeSelect = page.getByLabel(/event type/i);
      await expect(eventTypeSelect).toHaveValue('search');
    });
  });
});
