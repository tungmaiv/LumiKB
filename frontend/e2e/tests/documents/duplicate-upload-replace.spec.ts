import { test, expect, type Page } from '@playwright/test';
import {
  createSameNameDuplicateResult,
  createSuccessfulReplaceResult,
  createFailedReplaceResult,
} from '../../fixtures/duplicate-detection.factory';

/**
 * E2E tests for Story 6-9: Duplicate Upload & Replace UI
 *
 * Tests the duplicate detection modal, replace/cancel options,
 * loading states, error handling, and archived document restore notes.
 */

// Test KB and document IDs for mocking
const TEST_KB_ID = 'kb-e2e-test-123';
const TEST_DOC_ID = 'doc-existing-456';
const TEST_FILENAME = 'test-document.pdf';

test.describe('Story 6-9: Duplicate Upload & Replace UI', () => {
  test.describe('AC-6.9.1: Duplicate Detection Modal', () => {
    test('shows duplicate dialog when uploading file with same name', async ({ page }) => {
      // Mock 409 conflict response from upload API
      await page.route(`**/api/v1/knowledge-bases/${TEST_KB_ID}/documents`, async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 409,
            contentType: 'application/json',
            body: JSON.stringify({
              detail: {
                error: {
                  code: 'DUPLICATE_DOCUMENT',
                  message: 'A document with this name already exists',
                  details: {
                    error: 'duplicate_document',
                    existing_document_id: TEST_DOC_ID,
                    existing_status: 'completed',
                  },
                },
              },
            }),
          });
        } else {
          await route.continue();
        }
      });

      // Navigate to KB documents page
      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Upload a file (trigger the dropzone)
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: TEST_FILENAME,
        mimeType: 'application/pdf',
        buffer: Buffer.from('test file content'),
      });

      // Wait for duplicate dialog to appear
      await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 5000 });
      await expect(page.getByText('Document Already Exists')).toBeVisible();
      await expect(page.getByText(TEST_FILENAME)).toBeVisible();
    });
  });

  test.describe('AC-6.9.2 & AC-6.9.3: Replace and Cancel Options', () => {
    test('shows Replace and Cancel buttons in duplicate dialog', async ({ page }) => {
      // Setup: mock duplicate detection
      await setupDuplicateDetection(page, TEST_KB_ID, TEST_DOC_ID, 'completed');

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      // Trigger duplicate detection
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: TEST_FILENAME,
        mimeType: 'application/pdf',
        buffer: Buffer.from('test content'),
      });

      // Wait for dialog
      await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 5000 });

      // Verify both buttons are present
      await expect(page.getByRole('button', { name: /replace existing/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
    });

    test('Cancel button closes dialog and removes file from queue', async ({ page }) => {
      await setupDuplicateDetection(page, TEST_KB_ID, TEST_DOC_ID, 'completed');

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: TEST_FILENAME,
        mimeType: 'application/pdf',
        buffer: Buffer.from('test content'),
      });

      await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 5000 });

      // Click Cancel
      await page.getByRole('button', { name: /cancel/i }).click();

      // Dialog should close
      await expect(page.getByRole('alertdialog')).not.toBeVisible();
    });
  });

  test.describe('AC-6.9.5: Replace Loading State', () => {
    test('shows loading state during replace operation', async ({ page }) => {
      await setupDuplicateDetection(page, TEST_KB_ID, TEST_DOC_ID, 'completed');

      // Mock slow replace endpoint
      await page.route(
        `**/api/v1/knowledge-bases/${TEST_KB_ID}/documents/${TEST_DOC_ID}/reupload`,
        async (route) => {
          // Delay to show loading state
          await new Promise((resolve) => setTimeout(resolve, 2000));
          await route.fulfill({
            status: 202,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 'new-doc-123',
              name: TEST_FILENAME,
              status: 'pending',
            }),
          });
        }
      );

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: TEST_FILENAME,
        mimeType: 'application/pdf',
        buffer: Buffer.from('test content'),
      });

      await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 5000 });

      // Click Replace
      await page.getByRole('button', { name: /replace existing/i }).click();

      // Should show loading state
      await expect(page.getByText('Replacing...')).toBeVisible();

      // Buttons should be disabled during replace
      await expect(page.getByRole('button', { name: /replacing/i })).toBeDisabled();
      await expect(page.getByRole('button', { name: /cancel/i })).toBeDisabled();
    });
  });

  test.describe('AC-6.9.6: Replace Error State', () => {
    test('shows error message when replace fails', async ({ page }) => {
      await setupDuplicateDetection(page, TEST_KB_ID, TEST_DOC_ID, 'completed');

      // Mock failed replace
      await page.route(
        `**/api/v1/knowledge-bases/${TEST_KB_ID}/documents/${TEST_DOC_ID}/reupload`,
        async (route) => {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              detail: 'File type mismatch. Expected PDF, got DOCX.',
            }),
          });
        }
      );

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: TEST_FILENAME,
        mimeType: 'application/pdf',
        buffer: Buffer.from('test content'),
      });

      await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 5000 });

      // Click Replace
      await page.getByRole('button', { name: /replace existing/i }).click();

      // Wait for error to appear
      await expect(page.getByText(/file type mismatch/i)).toBeVisible({ timeout: 5000 });

      // Buttons should be re-enabled to allow retry or cancel
      await expect(page.getByRole('button', { name: /replace existing/i })).toBeEnabled();
      await expect(page.getByRole('button', { name: /cancel/i })).toBeEnabled();
    });
  });

  test.describe('AC-6.9.7: Archived Document Restore Note', () => {
    test('shows restore note when duplicate is archived', async ({ page }) => {
      // Setup with archived status
      await setupDuplicateDetection(page, TEST_KB_ID, TEST_DOC_ID, 'archived');

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: TEST_FILENAME,
        mimeType: 'application/pdf',
        buffer: Buffer.from('test content'),
      });

      await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 5000 });

      // Should show archived badge
      await expect(page.getByText('archived')).toBeVisible();

      // Should show restore note
      await expect(
        page.getByText(/replacing will restore this document to active status/i)
      ).toBeVisible();
    });

    test('does not show restore note for completed documents', async ({ page }) => {
      await setupDuplicateDetection(page, TEST_KB_ID, TEST_DOC_ID, 'completed');

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: TEST_FILENAME,
        mimeType: 'application/pdf',
        buffer: Buffer.from('test content'),
      });

      await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 5000 });

      // Should show completed badge
      await expect(page.getByText('completed')).toBeVisible();

      // Should NOT show restore note
      await expect(
        page.getByText(/replacing will restore this document to active status/i)
      ).not.toBeVisible();
    });
  });

  test.describe('AC-6.9.4: Auto-Clear Notification', () => {
    test('shows toast when failed document is auto-cleared', async ({ page }) => {
      // Mock upload that returns auto-clear info
      await page.route(`**/api/v1/knowledge-bases/${TEST_KB_ID}/documents`, async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 202,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 'new-doc-123',
              name: TEST_FILENAME,
              original_filename: TEST_FILENAME,
              mime_type: 'application/pdf',
              file_size_bytes: 1024,
              status: 'pending',
              auto_cleared_document_id: 'old-failed-doc',
              message: 'Previous failed upload was automatically cleared',
            }),
          });
        } else {
          await route.continue();
        }
      });

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: TEST_FILENAME,
        mimeType: 'application/pdf',
        buffer: Buffer.from('test content'),
      });

      // Should show auto-clear toast notification
      await expect(page.getByText(/previous failed upload was automatically cleared/i)).toBeVisible(
        { timeout: 5000 }
      );
    });
  });

  test.describe('Successful Replace Flow', () => {
    test('closes dialog and refreshes list after successful replace', async ({ page }) => {
      await setupDuplicateDetection(page, TEST_KB_ID, TEST_DOC_ID, 'completed');

      // Mock successful replace
      await page.route(
        `**/api/v1/knowledge-bases/${TEST_KB_ID}/documents/${TEST_DOC_ID}/reupload`,
        async (route) => {
          await route.fulfill({
            status: 202,
            contentType: 'application/json',
            body: JSON.stringify({
              id: TEST_DOC_ID,
              name: TEST_FILENAME,
              original_filename: TEST_FILENAME,
              mime_type: 'application/pdf',
              file_size_bytes: 1024,
              status: 'pending',
              created_at: new Date().toISOString(),
            }),
          });
        }
      );

      await page.goto(`/dashboard?kb=${TEST_KB_ID}`);

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: TEST_FILENAME,
        mimeType: 'application/pdf',
        buffer: Buffer.from('test content'),
      });

      await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 5000 });

      // Click Replace
      await page.getByRole('button', { name: /replace existing/i }).click();

      // Dialog should close after success
      await expect(page.getByRole('alertdialog')).not.toBeVisible({ timeout: 5000 });

      // Should show success toast
      await expect(page.getByText(/uploaded successfully/i)).toBeVisible({ timeout: 5000 });
    });
  });
});

/**
 * Helper to setup duplicate detection mock
 */
async function setupDuplicateDetection(
  page: Page,
  kbId: string,
  existingDocId: string,
  existingStatus: 'completed' | 'archived'
) {
  await page.route(`**/api/v1/knowledge-bases/${kbId}/documents`, async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error: {
              code: 'DUPLICATE_DOCUMENT',
              message: 'A document with this name already exists',
              details: {
                error: 'duplicate_document',
                existing_document_id: existingDocId,
                existing_status: existingStatus,
              },
            },
          },
        }),
      });
    } else {
      await route.continue();
    }
  });
}
