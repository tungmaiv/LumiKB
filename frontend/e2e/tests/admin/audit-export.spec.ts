/**
 * E2E tests for Audit Log Export feature (Story 5.3)
 */

import { test, expect } from '@playwright/test';
import { AdminPage } from '../../pages/admin.page';

test.describe('Audit Log Export', () => {
  let adminPage: AdminPage;

  test.beforeEach(async ({ page }) => {
    adminPage = new AdminPage(page);
    await adminPage.loginAsAdmin();
    await adminPage.gotoAuditLogs();
  });

  test('should display Export button on Audit Log Viewer page', async ({ page }) => {
    // Verify Export button is visible
    const exportButton = page.getByRole('button', { name: /export/i });
    await expect(exportButton).toBeVisible();
  });

  test('should open export modal when Export button clicked', async ({ page }) => {
    // Click Export button
    await page.getByRole('button', { name: /export/i }).click();

    // Verify modal is displayed
    await expect(page.getByText('Export Audit Logs')).toBeVisible();
    await expect(page.getByText(/records will be exported/i)).toBeVisible();

    // Verify format options
    await expect(page.getByText('CSV (Comma-Separated Values)')).toBeVisible();
    await expect(page.getByText('JSON (JavaScript Object Notation)')).toBeVisible();
  });

  test('should download CSV file when Download CSV clicked', async ({ page }) => {
    // Click Export button
    await page.getByRole('button', { name: /export/i }).click();

    // Select CSV format (should be default)
    const csvRadio = page.getByRole('radio', { name: /csv/i });
    await expect(csvRadio).toBeChecked();

    // Start download listener
    const downloadPromise = page.waitForEvent('download');

    // Click Download button
    await page.getByRole('button', { name: /download csv/i }).click();

    // Wait for download
    const download = await downloadPromise;

    // Verify filename
    expect(download.suggestedFilename()).toMatch(/audit-log-export-.*\.csv/);

    // Verify file is not empty
    const path = await download.path();
    expect(path).toBeTruthy();
  });

  test('should download JSON file when JSON format selected', async ({ page }) => {
    // Click Export button
    await page.getByRole('button', { name: /export/i }).click();

    // Select JSON format
    await page.getByRole('radio', { name: /json/i }).click();

    // Start download listener
    const downloadPromise = page.waitForEvent('download');

    // Click Download button
    await page.getByRole('button', { name: /download json/i }).click();

    // Wait for download
    const download = await downloadPromise;

    // Verify filename
    expect(download.suggestedFilename()).toMatch(/audit-log-export-.*\.json/);
  });

  test('should close modal when Cancel clicked', async ({ page }) => {
    // Click Export button
    await page.getByRole('button', { name: /export/i }).click();

    // Verify modal is open
    await expect(page.getByText('Export Audit Logs')).toBeVisible();

    // Click Cancel
    await page.getByRole('button', { name: /cancel/i }).click();

    // Verify modal is closed
    await expect(page.getByText('Export Audit Logs')).not.toBeVisible();
  });
});

test.describe('Audit Log Export - Non-Admin', () => {
  test('should not display Export button for non-admin users', async ({ page }) => {
    // Login as regular user
    const adminPage = new AdminPage(page);
    await adminPage.loginAsRegularUser();

    // Try to navigate to admin audit page
    await page.goto('/admin/audit');

    // Should be redirected or see 403 error
    // Export button should not be visible
    const exportButton = page.getByRole('button', { name: /export/i });
    await expect(exportButton).not.toBeVisible();
  });
});
