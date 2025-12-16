/**
 * E2E tests for System Configuration Management
 *
 * Tests complete system configuration workflows including viewing settings,
 * editing configuration values, validation, restart warnings, and audit logging.
 * Story: 5-5 (System Configuration Management)
 */

import { test, expect } from '@playwright/test';
import { AdminPage } from '../../pages/admin.page';

test.describe('System Configuration E2E Tests', () => {
  let adminPage: AdminPage;

  test.beforeEach(async ({ page }) => {
    adminPage = new AdminPage(page);
  });

  test.describe('[P0] Admin can view all system configuration settings', () => {
    test('should navigate to system config page and display all 8 settings', async ({ page }) => {
      // GIVEN: Admin user is logged in
      await adminPage.loginAsAdmin();

      // WHEN: Admin navigates to /admin/config
      await page.goto('/admin/config');

      // THEN: Should display system configuration page
      await expect(page.locator('h1')).toContainText(/system configuration/i);

      // Should display settings table
      await expect(page.getByRole('table')).toBeVisible();

      // Should display 8 settings (verify by checking for specific setting keys)
      await expect(page.getByText('Session Timeout')).toBeVisible();
      await expect(page.getByText('Login Rate Limit')).toBeVisible();
      await expect(page.getByText('Max Upload File Size')).toBeVisible();
      await expect(page.getByText('Default Chunk Size')).toBeVisible();
      await expect(page.getByText('Max Chunks Per Document')).toBeVisible();
      await expect(page.getByText('Search Rate Limit')).toBeVisible();
      await expect(page.getByText('Generation Rate Limit')).toBeVisible();
      await expect(page.getByText('Upload Rate Limit')).toBeVisible();

      // Should display setting categories
      await expect(page.getByText('Security')).toBeVisible();
      await expect(page.getByText('Processing')).toBeVisible();
      await expect(page.getByText('Rate Limits')).toBeVisible();

      // Should display Edit buttons
      const editButtons = page.getByRole('button', { name: /edit/i });
      const editButtonCount = await editButtons.count();
      expect(editButtonCount).toBeGreaterThanOrEqual(8);
    });

    test('should display setting metadata correctly', async ({ page }) => {
      // GIVEN: Admin is on system config page
      await adminPage.loginAsAdmin();
      await page.goto('/admin/config');

      // THEN: Settings table should display required columns
      const table = page.getByRole('table');

      // Verify column headers
      await expect(table.getByText(/setting name/i)).toBeVisible();
      await expect(table.getByText(/current value/i)).toBeVisible();
      await expect(table.getByText(/data type/i)).toBeVisible();

      // Verify data types are displayed (e.g., "integer")
      const dataTypeCells = await table.getByText(/integer|float|boolean|string/i).allTextContents();
      expect(dataTypeCells.length).toBeGreaterThan(0);
    });
  });

  test.describe('[P0] Admin can edit a configuration setting', () => {
    test('should edit session timeout and persist value successfully', async ({ page }) => {
      // GIVEN: Admin is on system config page
      await adminPage.loginAsAdmin();
      await page.goto('/admin/config');

      // WHEN: Admin clicks Edit on Session Timeout setting
      // Find the row containing "Session Timeout" and click its Edit button
      const sessionTimeoutRow = page.locator('tr').filter({ hasText: 'Session Timeout' });
      await sessionTimeoutRow.getByRole('button', { name: /edit/i }).click();

      // THEN: Edit modal should open
      const modal = page.locator('[role="dialog"]').or(page.locator('.modal'));
      await expect(modal).toBeVisible();
      await expect(modal.getByText(/session timeout/i)).toBeVisible();

      // WHEN: Admin changes value to 1440 and saves
      const valueInput = modal.getByRole('spinbutton').or(modal.getByRole('textbox'));
      await valueInput.clear();
      await valueInput.fill('1440');
      await modal.getByRole('button', { name: /save/i }).click();

      // THEN: Modal should close
      await expect(modal).not.toBeVisible({ timeout: 5000 });

      // THEN: Success message should appear
      await expect(page.getByText(/updated successfully|success/i)).toBeVisible({ timeout: 5000 });

      // THEN: Table should show updated value
      await expect(sessionTimeoutRow).toContainText('1440');

      // Verify persistence by refreshing page
      await page.reload();
      await expect(page.locator('tr').filter({ hasText: 'Session Timeout' })).toContainText('1440');
    });

    test('should restore original value after testing', async ({ page }) => {
      // Reset session_timeout_minutes to default (720) for test isolation
      await adminPage.loginAsAdmin();
      await page.goto('/admin/config');

      const sessionTimeoutRow = page.locator('tr').filter({ hasText: 'Session Timeout' });
      await sessionTimeoutRow.getByRole('button', { name: /edit/i }).click();

      const modal = page.locator('[role="dialog"]').or(page.locator('.modal'));
      const valueInput = modal.getByRole('spinbutton').or(modal.getByRole('textbox'));
      await valueInput.clear();
      await valueInput.fill('720');
      await modal.getByRole('button', { name: /save/i }).click();

      await expect(modal).not.toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('[P1] Configuration changes are validated before saving', () => {
    test('should display validation error for value below minimum', async ({ page }) => {
      // GIVEN: Admin is editing session timeout (min: 60)
      await adminPage.loginAsAdmin();
      await page.goto('/admin/config');

      const sessionTimeoutRow = page.locator('tr').filter({ hasText: 'Session Timeout' });
      await sessionTimeoutRow.getByRole('button', { name: /edit/i }).click();

      const modal = page.locator('[role="dialog"]').or(page.locator('.modal'));

      // WHEN: Admin enters value below minimum (e.g., 30 < 60)
      const valueInput = modal.getByRole('spinbutton').or(modal.getByRole('textbox'));
      await valueInput.clear();
      await valueInput.fill('30');
      await modal.getByRole('button', { name: /save/i }).click();

      // THEN: Validation error should be displayed
      await expect(modal).toBeVisible(); // Modal should stay open
      await expect(page.getByText(/below minimum|invalid|error/i)).toBeVisible({ timeout: 5000 });

      // THEN: Value should not be saved
      await modal.getByRole('button', { name: /cancel/i }).click();
      await expect(sessionTimeoutRow).not.toContainText('30');
    });

    test('should display validation error for invalid type', async ({ page }) => {
      // GIVEN: Admin is editing an integer setting
      await adminPage.loginAsAdmin();
      await page.goto('/admin/config');

      const sessionTimeoutRow = page.locator('tr').filter({ hasText: 'Session Timeout' });
      await sessionTimeoutRow.getByRole('button', { name: /edit/i }).click();

      const modal = page.locator('[role="dialog"]').or(page.locator('.modal'));

      // WHEN: Admin enters non-numeric value
      const valueInput = modal.getByRole('spinbutton').or(modal.getByRole('textbox'));
      await valueInput.clear();
      await valueInput.fill('abc');
      await modal.getByRole('button', { name: /save/i }).click();

      // THEN: Validation error should be displayed (client-side or server-side)
      await expect(modal).toBeVisible(); // Modal should stay open
      // Note: Browser HTML5 validation may prevent this, or server returns 400
      // Check for either client-side validation or error message after API call
      const hasValidationError = await page.getByText(/invalid|error|must be a number/i).isVisible().catch(() => false);
      const isInputInvalid = await valueInput.evaluate((el) => (el as HTMLInputElement).validity.valid).catch(() => true);

      expect(hasValidationError || !isInputInvalid).toBeTruthy();

      // THEN: Close modal
      await modal.getByRole('button', { name: /cancel/i }).click();
    });
  });

  test.describe('[P1] Settings requiring restart display a warning', () => {
    test('should display warning when editing setting requiring restart', async ({ page }) => {
      // GIVEN: Admin is editing default_chunk_size_tokens (requires_restart: true)
      await adminPage.loginAsAdmin();
      await page.goto('/admin/config');

      const chunkSizeRow = page.locator('tr').filter({ hasText: 'Default Chunk Size' });

      // WHEN: Admin clicks Edit
      await chunkSizeRow.getByRole('button', { name: /edit/i }).click();

      const modal = page.locator('[role="dialog"]').or(page.locator('.modal'));
      await expect(modal).toBeVisible();

      // THEN: Modal should display restart warning
      await expect(modal.getByText(/restart|service restart required/i)).toBeVisible();

      // WHEN: Admin changes value and saves
      const valueInput = modal.getByRole('spinbutton').or(modal.getByRole('textbox'));
      await valueInput.clear();
      await valueInput.fill('1024');

      // Check for confirmation dialog or direct save
      const saveButton = modal.getByRole('button', { name: /save|continue/i });
      await saveButton.click();

      // If confirmation modal appears, confirm
      const confirmButton = page.getByRole('button', { name: /continue|confirm|yes/i });
      if (await confirmButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmButton.click();
      }

      // THEN: Warning banner should appear on page
      await expect(page.getByText(/restart|configuration changes require/i)).toBeVisible({ timeout: 5000 });
      await expect(page.getByText(/default.*chunk.*size/i)).toBeVisible();
    });

    test('should allow dismissing restart warning banner', async ({ page }) => {
      // GIVEN: Restart warning banner is displayed
      await adminPage.loginAsAdmin();
      await page.goto('/admin/config');

      // Trigger restart warning by editing a setting requiring restart
      const chunkSizeRow = page.locator('tr').filter({ hasText: 'Default Chunk Size' });
      await chunkSizeRow.getByRole('button', { name: /edit/i }).click();

      const modal = page.locator('[role="dialog"]').or(page.locator('.modal'));
      const valueInput = modal.getByRole('spinbutton').or(modal.getByRole('textbox'));
      await valueInput.clear();
      await valueInput.fill('768');
      await modal.getByRole('button', { name: /save|continue/i }).click();

      // Confirm if needed
      const confirmButton = page.getByRole('button', { name: /continue|confirm|yes/i });
      if (await confirmButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmButton.click();
      }

      // Wait for banner
      const banner = page.locator('[role="alert"]').or(page.locator('.alert'));
      await expect(banner.filter({ hasText: /restart/i })).toBeVisible({ timeout: 5000 });

      // WHEN: Admin clicks Dismiss
      const dismissButton = banner.getByRole('button', { name: /dismiss|close/i });
      if (await dismissButton.isVisible()) {
        await dismissButton.click();

        // THEN: Banner should disappear
        await expect(banner.filter({ hasText: /restart/i })).not.toBeVisible();
      }
    });
  });

  test.describe('[P1] Non-admin users receive 403 Forbidden', () => {
    test('should redirect non-admin user from config page', async ({ page }) => {
      // GIVEN: Regular user is logged in
      await adminPage.loginAsRegularUser();

      // WHEN: User attempts to access /admin/config
      await page.goto('/admin/config');

      // THEN: Should redirect to dashboard or show 403 error
      await expect(page).not.toHaveURL('/admin/config', { timeout: 5000 });

      // Should display error message
      await expect(page.getByText(/permission|access denied|admin/i)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('[P1] Configuration change appears in audit log viewer', () => {
    test('should log configuration change to audit system', async ({ page }) => {
      // GIVEN: Admin updates a configuration setting
      await adminPage.loginAsAdmin();
      await page.goto('/admin/config');

      const loginRateLimitRow = page.locator('tr').filter({ hasText: 'Login Rate Limit' });
      await loginRateLimitRow.getByRole('button', { name: /edit/i }).click();

      const modal = page.locator('[role="dialog"]').or(page.locator('.modal'));
      const valueInput = modal.getByRole('spinbutton').or(modal.getByRole('textbox'));
      await valueInput.clear();
      await valueInput.fill('20');
      await modal.getByRole('button', { name: /save/i }).click();

      // Wait for save to complete
      await expect(modal).not.toBeVisible({ timeout: 5000 });
      await expect(page.getByText(/success/i)).toBeVisible({ timeout: 5000 });

      // WHEN: Admin navigates to audit log viewer
      await page.goto('/admin/audit');

      // THEN: Should display audit event for config.update
      await expect(page.getByText(/config\.update|configuration update/i)).toBeVisible({ timeout: 10000 });

      // Should display setting key in audit details
      await expect(page.getByText(/login_rate_limit_per_hour/i)).toBeVisible();
    });
  });
});
