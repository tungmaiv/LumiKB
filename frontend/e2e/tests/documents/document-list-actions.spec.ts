import { test, expect, type Page } from '@playwright/test';
import {
  createActiveDocument,
  createFailedDocument,
  createProcessingDocument,
  createPendingDocument,
  createMockDocument,
  createSuccessfulArchiveOperation,
  createSuccessfulClearOperation,
  createSuccessfulCancelOperation,
  getDocumentActionRoutes,
  type ArchivedDocument,
  type DocumentStatus,
} from '../../fixtures/document-actions.factory';

/**
 * E2E tests for Story 6-8: Document List Archive/Clear Actions UI
 *
 * Tests the document actions menu (three-dot menu) with:
 * - Archive action for completed documents
 * - Clear action for failed documents
 * - Permission-based visibility (owner/admin only)
 * - Status-based visibility
 * - Confirmation dialogs
 * - UI updates after operations
 *
 * Priority: P0 (core document lifecycle functionality)
 */

// Test constants
const TEST_KB_ID = 'kb-actions-test-001';
const TEST_DOC_ID = 'doc-test-001';

test.describe('Story 6-8: Document List Archive/Clear Actions UI', () => {
  test.describe('AC-6.8.1: Archive action visible for completed documents', () => {
    test('shows Archive option in menu for completed document when owner', async ({ page }) => {
      const completedDoc = createActiveDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'completed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: false, isKbOwner: true });
      await setupDocumentList(page, TEST_KB_ID, [completedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Archive option should be visible
      await expect(page.getByRole('menuitem', { name: /archive/i })).toBeVisible();
    });

    test('shows Archive option in menu for completed document when admin', async ({ page }) => {
      const completedDoc = createActiveDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'completed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true, isKbOwner: false });
      await setupDocumentList(page, TEST_KB_ID, [completedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Archive option should be visible for admin
      await expect(page.getByRole('menuitem', { name: /archive/i })).toBeVisible();
    });
  });

  test.describe('AC-6.8.2: Archive action triggers confirmation', () => {
    test('clicking Archive shows confirmation dialog with explanation', async ({ page }) => {
      const completedDoc = createActiveDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-archive.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [completedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open menu and click Archive
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /archive/i }).click();

      // Confirmation dialog should appear
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText(/removed from search/i)).toBeVisible();

      // Should have confirm and cancel buttons
      await expect(page.getByRole('button', { name: /confirm|archive/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
    });

    test('cancel button closes dialog without archiving', async ({ page }) => {
      const completedDoc = createActiveDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-archive.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [completedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open menu and click Archive
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /archive/i }).click();

      // Click cancel
      await page.getByRole('button', { name: /cancel/i }).click();

      // Dialog should close
      await expect(page.getByRole('dialog')).not.toBeVisible();

      // Document should still be visible
      await expect(page.getByText('to-archive.pdf')).toBeVisible();
    });
  });

  test.describe('AC-6.8.3: Archive success updates UI', () => {
    test('successful archive shows toast and removes document from list', async ({ page }) => {
      const completedDoc = createActiveDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-archive.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [completedDoc]);
      await setupArchiveEndpoint(page, TEST_KB_ID, TEST_DOC_ID, true);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open menu and archive
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /archive/i }).click();

      // Confirm archive
      await page.getByRole('dialog').getByRole('button', { name: /confirm|archive/i }).click();

      // Success toast should appear
      await expect(page.getByText(/document archived/i)).toBeVisible({ timeout: 5000 });

      // Document should be removed from list
      await expect(page.getByText('to-archive.pdf')).not.toBeVisible();
    });

    test('document count updates after archive', async ({ page }) => {
      const documents = [
        createActiveDocument({ id: 'doc-1', kb_id: TEST_KB_ID, name: 'doc-1.pdf' }),
        createActiveDocument({ id: 'doc-2', kb_id: TEST_KB_ID, name: 'doc-2.pdf' }),
        createActiveDocument({ id: 'doc-3', kb_id: TEST_KB_ID, name: 'doc-3.pdf' }),
      ];

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentListWithCount(page, TEST_KB_ID, documents);
      await setupArchiveEndpoint(page, TEST_KB_ID, 'doc-1', true);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Initially shows 3 documents
      await expect(page.getByText(/3 documents/i)).toBeVisible();

      // Archive first document
      await page.locator('[data-testid="document-row-doc-1"]').getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /archive/i }).click();
      await page.getByRole('dialog').getByRole('button', { name: /confirm|archive/i }).click();

      // Count should update to 2
      await expect(page.getByText(/2 documents/i)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('AC-6.8.4: Clear action visible for failed documents', () => {
    test('shows Clear option in menu for failed document when owner', async ({ page }) => {
      const failedDoc = createFailedDocument('Parsing error', {
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'failed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: false, isKbOwner: true });
      await setupDocumentList(page, TEST_KB_ID, [failedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Clear option should be visible
      await expect(page.getByRole('menuitem', { name: /clear/i })).toBeVisible();
    });

    test('shows Clear option in menu for failed document when admin', async ({ page }) => {
      const failedDoc = createFailedDocument('Processing timeout', {
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'failed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true, isKbOwner: false });
      await setupDocumentList(page, TEST_KB_ID, [failedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Clear option should be visible
      await expect(page.getByRole('menuitem', { name: /clear/i })).toBeVisible();
    });
  });

  test.describe('AC-6.8.5: Clear action triggers confirmation', () => {
    test('clicking Clear shows confirmation dialog with permanent removal warning', async ({
      page,
    }) => {
      const failedDoc = createFailedDocument('Corrupted file', {
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-clear.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [failedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open menu and click Clear
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /clear/i }).click();

      // Confirmation dialog should appear
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText(/permanently removed/i)).toBeVisible();

      // Should have confirm and cancel buttons
      await expect(page.getByRole('button', { name: /confirm|clear/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
    });
  });

  test.describe('AC-6.8.6: Clear success updates UI', () => {
    test('successful clear shows toast and removes document from list', async ({ page }) => {
      const failedDoc = createFailedDocument('Parsing error', {
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-clear.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [failedDoc]);
      await setupClearEndpoint(page, TEST_KB_ID, TEST_DOC_ID, true);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open menu and clear
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /clear/i }).click();

      // Confirm clear
      await page.getByRole('dialog').getByRole('button', { name: /confirm|clear/i }).click();

      // Success toast should appear
      await expect(page.getByText(/failed document cleared/i)).toBeVisible({ timeout: 5000 });

      // Document should be removed from list
      await expect(page.getByText('to-clear.pdf')).not.toBeVisible();
    });

    test('document count updates after clear', async ({ page }) => {
      const documents = [
        createActiveDocument({ id: 'doc-1', kb_id: TEST_KB_ID, name: 'active.pdf' }),
        createFailedDocument('Error', { id: 'doc-2', kb_id: TEST_KB_ID, name: 'failed-1.pdf' }),
        createFailedDocument('Error', { id: 'doc-3', kb_id: TEST_KB_ID, name: 'failed-2.pdf' }),
      ];

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentListWithCount(page, TEST_KB_ID, documents);
      await setupClearEndpoint(page, TEST_KB_ID, 'doc-2', true);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Initially shows 3 documents
      await expect(page.getByText(/3 documents/i)).toBeVisible();

      // Clear first failed document
      await page.locator('[data-testid="document-row-doc-2"]').getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /clear/i }).click();
      await page.getByRole('dialog').getByRole('button', { name: /confirm|clear/i }).click();

      // Count should update to 2
      await expect(page.getByText(/2 documents/i)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('AC-6.8.7: Actions hidden for non-owners/non-admins', () => {
    test('Archive option hidden for regular users (not owner)', async ({ page }) => {
      const completedDoc = createActiveDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'completed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: false, isKbOwner: false });
      await setupDocumentList(page, TEST_KB_ID, [completedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Archive option should NOT be visible
      await expect(page.getByRole('menuitem', { name: /archive/i })).not.toBeVisible();
    });

    test('Clear option hidden for regular users (not owner)', async ({ page }) => {
      const failedDoc = createFailedDocument('Error', {
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'failed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: false, isKbOwner: false });
      await setupDocumentList(page, TEST_KB_ID, [failedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Clear option should NOT be visible
      await expect(page.getByRole('menuitem', { name: /clear/i })).not.toBeVisible();
    });
  });

  test.describe('AC-6.8.8: Actions hidden for inappropriate statuses', () => {
    test('Archive option hidden for pending documents', async ({ page }) => {
      const pendingDoc = createMockDocument('pending', {
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'pending-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [pendingDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Archive option should NOT be visible
      await expect(page.getByRole('menuitem', { name: /archive/i })).not.toBeVisible();
    });

    test('Archive option hidden for processing documents', async ({ page }) => {
      const processingDoc = createProcessingDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'processing-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [processingDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Archive option should NOT be visible
      await expect(page.getByRole('menuitem', { name: /archive/i })).not.toBeVisible();
    });

    test('Clear option hidden for completed documents', async ({ page }) => {
      const completedDoc = createActiveDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'completed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [completedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Clear option should NOT be visible
      await expect(page.getByRole('menuitem', { name: /clear/i })).not.toBeVisible();
    });

    test('Clear option hidden for processing documents', async ({ page }) => {
      const processingDoc = createProcessingDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'processing-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [processingDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Clear option should NOT be visible
      await expect(page.getByRole('menuitem', { name: /clear/i })).not.toBeVisible();
    });
  });

  test.describe('AC-6.8.8: Cancel Processing visible for pending/processing documents', () => {
    test('shows Cancel Processing option for PROCESSING documents', async ({ page }) => {
      const processingDoc = createProcessingDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'processing-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [processingDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Cancel Processing option should be visible
      await expect(page.getByRole('menuitem', { name: /cancel processing/i })).toBeVisible();
    });

    test('shows Cancel Processing option for PENDING documents', async ({ page }) => {
      const pendingDoc = createPendingDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'pending-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [pendingDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Cancel Processing option should be visible
      await expect(page.getByRole('menuitem', { name: /cancel processing/i })).toBeVisible();
    });

    test('Cancel Processing option hidden for completed documents', async ({ page }) => {
      const completedDoc = createActiveDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'completed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [completedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Cancel Processing option should NOT be visible
      await expect(page.getByRole('menuitem', { name: /cancel processing/i })).not.toBeVisible();
    });

    test('Cancel Processing option hidden for failed documents', async ({ page }) => {
      const failedDoc = createFailedDocument('Processing error', {
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'failed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [failedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Cancel Processing option should NOT be visible
      await expect(page.getByRole('menuitem', { name: /cancel processing/i })).not.toBeVisible();
    });
  });

  test.describe('AC-6.8.9: Cancel Processing moves document to failed status', () => {
    test('clicking Cancel Processing changes document status to failed', async ({ page }) => {
      const processingDoc = createProcessingDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'processing-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [processingDoc]);
      await setupCancelEndpoint(page, TEST_KB_ID, TEST_DOC_ID, true);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open menu and click Cancel Processing
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /cancel processing/i }).click();

      // Success toast should appear
      await expect(page.getByText(/processing cancelled/i)).toBeVisible({ timeout: 5000 });
    });

    test('cancelled document shows Retry option after cancellation', async ({ page }) => {
      // First show processing doc, then after cancel it becomes failed
      const processingDoc = createProcessingDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-cancel.pdf',
      });
      const failedDoc = createFailedDocument('Processing cancelled by user', {
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-cancel.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });

      // Setup document list that returns processing first, then failed after cancel
      let cancelled = false;
      await page.route(`**/api/v1/knowledge-bases/${TEST_KB_ID}/documents**`, async (route) => {
        const docs = cancelled ? [failedDoc] : [processingDoc];
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: docs,
            total: docs.length,
            page: 1,
            limit: 20,
          }),
        });
      });

      // Setup cancel endpoint
      await page.route(`**/api/v1/knowledge-bases/${TEST_KB_ID}/documents/${TEST_DOC_ID}/cancel`, async (route) => {
        cancelled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createSuccessfulCancelOperation(TEST_DOC_ID)),
        });
      });

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Cancel the processing document
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /cancel processing/i }).click();

      // Wait for list to refresh and re-open menu
      await page.waitForTimeout(1000);
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Now Clear option should be visible (for failed documents)
      await expect(page.getByRole('menuitem', { name: /clear/i })).toBeVisible();
    });
  });

  test.describe('AC-6.8.10: Delete disabled for pending/processing documents', () => {
    test('Delete option is disabled for PROCESSING documents', async ({ page }) => {
      const processingDoc = createProcessingDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'processing-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [processingDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Delete option should be disabled
      const deleteItem = page.getByRole('menuitem', { name: /delete/i });
      await expect(deleteItem).toBeVisible();
      await expect(deleteItem).toBeDisabled();
    });

    test('Delete option is disabled for PENDING documents', async ({ page }) => {
      const pendingDoc = createPendingDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'pending-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [pendingDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Delete option should be disabled
      const deleteItem = page.getByRole('menuitem', { name: /delete/i });
      await expect(deleteItem).toBeVisible();
      await expect(deleteItem).toBeDisabled();
    });

    test('Delete option is enabled for COMPLETED documents', async ({ page }) => {
      const completedDoc = createActiveDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'completed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [completedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Delete option should be enabled
      const deleteItem = page.getByRole('menuitem', { name: /delete/i });
      await expect(deleteItem).toBeVisible();
      await expect(deleteItem).not.toBeDisabled();
    });

    test('Delete option is enabled for FAILED documents', async ({ page }) => {
      const failedDoc = createFailedDocument('Processing error', {
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'failed-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [failedDoc]);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Open document actions menu
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();

      // Delete option should be enabled
      const deleteItem = page.getByRole('menuitem', { name: /delete/i });
      await expect(deleteItem).toBeVisible();
      await expect(deleteItem).not.toBeDisabled();
    });
  });

  test.describe('Error Handling', () => {
    test('shows error toast when archive fails', async ({ page }) => {
      const completedDoc = createActiveDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-archive.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [completedDoc]);
      await setupArchiveEndpoint(page, TEST_KB_ID, TEST_DOC_ID, false);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Try to archive
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /archive/i }).click();
      await page.getByRole('dialog').getByRole('button', { name: /confirm|archive/i }).click();

      // Error toast should appear
      await expect(page.getByText(/failed to archive/i)).toBeVisible({ timeout: 5000 });

      // Document should still be visible
      await expect(page.getByText('to-archive.pdf')).toBeVisible();
    });

    test('shows error toast when clear fails', async ({ page }) => {
      const failedDoc = createFailedDocument('Error', {
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-clear.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, [failedDoc]);
      await setupClearEndpoint(page, TEST_KB_ID, TEST_DOC_ID, false);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Try to clear
      await page.locator(`[data-testid="document-row-${TEST_DOC_ID}"]`).getByRole('button', { name: /more|actions/i }).click();
      await page.getByRole('menuitem', { name: /clear/i }).click();
      await page.getByRole('dialog').getByRole('button', { name: /confirm|clear/i }).click();

      // Error toast should appear
      await expect(page.getByText(/failed to clear/i)).toBeVisible({ timeout: 5000 });

      // Document should still be visible
      await expect(page.getByText('to-clear.pdf')).toBeVisible();
    });
  });

  test.describe('Edge Cases', () => {
    test('mixed document list shows correct actions for each status', async ({ page }) => {
      const documents = [
        createActiveDocument({ id: 'completed-doc', kb_id: TEST_KB_ID, name: 'completed.pdf' }),
        createFailedDocument('Error', { id: 'failed-doc', kb_id: TEST_KB_ID, name: 'failed.pdf' }),
        createProcessingDocument({ id: 'processing-doc', kb_id: TEST_KB_ID, name: 'processing.pdf' }),
      ];

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupDocumentList(page, TEST_KB_ID, documents);

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Check completed document - should have Archive
      await page.locator('[data-testid="document-row-completed-doc"]').getByRole('button', { name: /more|actions/i }).click();
      await expect(page.getByRole('menuitem', { name: /archive/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /clear/i })).not.toBeVisible();
      await page.keyboard.press('Escape');

      // Check failed document - should have Clear
      await page.locator('[data-testid="document-row-failed-doc"]').getByRole('button', { name: /more|actions/i }).click();
      await expect(page.getByRole('menuitem', { name: /clear/i })).toBeVisible();
      await expect(page.getByRole('menuitem', { name: /archive/i })).not.toBeVisible();
      await page.keyboard.press('Escape');

      // Check processing document - should have Cancel Processing only
      await page.locator('[data-testid="document-row-processing-doc"]').getByRole('button', { name: /more|actions/i }).click();
      await expect(page.getByRole('menuitem', { name: /archive/i })).not.toBeVisible();
      await expect(page.getByRole('menuitem', { name: /clear/i })).not.toBeVisible();
      await expect(page.getByRole('menuitem', { name: /cancel processing/i })).toBeVisible();
    });
  });
});

// ============================================================
// Helper Functions
// ============================================================

async function setupAuthenticatedUser(
  page: Page,
  options: { is_admin: boolean; isKbOwner?: boolean }
) {
  const userId = 'user-test-001';
  const kbOwnerId = options.isKbOwner ? userId : 'other-user-999';

  await page.route('**/api/v1/users/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: userId,
        email: 'test@example.com',
        is_admin: options.is_admin,
        is_active: true,
      }),
    });
  });

  // Mock KB endpoint to control ownership
  await page.route(`**/api/v1/knowledge-bases/${TEST_KB_ID}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: TEST_KB_ID,
        name: 'Test Knowledge Base',
        owner_id: kbOwnerId,
      }),
    });
  });
}

async function setupDocumentList(page: Page, kbId: string, docs: ArchivedDocument[]) {
  await page.route(`**/api/v1/knowledge-bases/${kbId}/documents**`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: docs,
        total: docs.length,
        page: 1,
        limit: 20,
      }),
    });
  });
}

async function setupDocumentListWithCount(page: Page, kbId: string, docs: ArchivedDocument[]) {
  let currentDocs = [...docs];

  await page.route(`**/api/v1/knowledge-bases/${kbId}/documents**`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: currentDocs,
        total: currentDocs.length,
        page: 1,
        limit: 20,
      }),
    });
  });
}

async function setupArchiveEndpoint(page: Page, kbId: string, docId: string, success: boolean) {
  await page.route(`**/api/v1/knowledge-bases/${kbId}/documents/${docId}/archive`, async (route) => {
    if (success) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSuccessfulArchiveOperation(docId)),
      });
    } else {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Failed to archive document' }),
      });
    }
  });
}

async function setupClearEndpoint(page: Page, kbId: string, docId: string, success: boolean) {
  await page.route(`**/api/v1/knowledge-bases/${kbId}/documents/${docId}/clear`, async (route) => {
    if (success) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSuccessfulClearOperation(docId)),
      });
    } else {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Failed to clear document' }),
      });
    }
  });
}

async function setupCancelEndpoint(page: Page, kbId: string, docId: string, success: boolean) {
  await page.route(`**/api/v1/knowledge-bases/${kbId}/documents/${docId}/cancel`, async (route) => {
    if (success) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSuccessfulCancelOperation(docId)),
      });
    } else {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Only PROCESSING or PENDING documents can be cancelled' }),
      });
    }
  });
}
