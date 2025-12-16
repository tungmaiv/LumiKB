/**
 * E2E Tests for Document Processing Progress Screen
 * Story 5-23: Document Processing Progress
 *
 * Tests cover all 7 acceptance criteria:
 * - AC-5.23.1: Processing tab shows step-level progress for each document
 * - AC-5.23.2: Filter by file type, status, or processing step
 * - AC-5.23.3: Click to view step-by-step processing details
 * - AC-5.23.4: Processing tab visible only to ADMIN/WRITE permission users
 * - AC-5.23.5: Auto-refresh every 10 seconds
 * - AC-5.23.6: Handle documents without processing info gracefully
 * - AC-5.23.7: Show human-readable processing step names and timing
 */

import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/dashboard.page';
import {
  createPaginatedProcessingResponse,
  createMixedProcessingResponse,
  createEmptyProcessingResponse,
  createCompletedDocumentDetails,
  createFailedDocumentDetails,
} from '../../fixtures/processing.factory';

test.describe('Document Processing Progress - E2E', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
  });

  test.describe('AC-5.23.1: Processing tab shows step-level progress', () => {
    test('[P0] User sees Processing tab and document table with progress bars', async ({
      page,
    }) => {
      // GIVEN: Mock KB with WRITE permission and processing documents
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [
              {
                id: 'kb-1',
                name: 'Test KB',
                description: 'Test Knowledge Base',
                permission_level: 'WRITE',
              },
            ],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing*', async (route) => {
        await route.fulfill({
          status: 200,
          json: createMixedProcessingResponse(),
        });
      });

      // Login and navigate to dashboard
      await dashboardPage.loginAsUser();
      await dashboardPage.goto();

      // Select the KB
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User clicks on Processing tab
      await page.click('button:has-text("Processing")');

      // THEN: Processing table is visible with documents
      await expect(page.locator('table')).toBeVisible();
      await expect(page.getByRole('row')).toHaveCount(7); // 1 header + 6 documents

      // AND: Progress bars are visible for each document
      const progressBars = page.locator('[role="progressbar"]');
      await expect(progressBars.first()).toBeVisible();

      // AND: Status badges are displayed
      await expect(page.getByText('Ready')).toBeVisible();
      await expect(page.getByText('Processing')).toBeVisible();
      await expect(page.getByText('Failed')).toBeVisible();
      await expect(page.getByText('Pending')).toBeVisible();
    });

    test('[P1] Document table shows current step in progress column', async ({ page }) => {
      // GIVEN: Mock processing response with documents at various steps
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing*', async (route) => {
        await route.fulfill({
          status: 200,
          json: createMixedProcessingResponse(),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      // THEN: Step labels are displayed
      await expect(page.getByText('Parse')).toBeVisible();
      await expect(page.getByText('Chunk')).toBeVisible();
      await expect(page.getByText('Embed')).toBeVisible();
      await expect(page.getByText('Complete')).toBeVisible();
    });
  });

  test.describe('AC-5.23.2: Filter by file type, status, or processing step', () => {
    test('[P1] User filters documents by status', async ({ page }) => {
      // GIVEN: Mock processing endpoint that responds to status filter
      let lastFilterStatus: string | null = null;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing*', async (route) => {
        const url = new URL(route.request().url());
        lastFilterStatus = url.searchParams.get('status');

        const response =
          lastFilterStatus === 'failed'
            ? createPaginatedProcessingResponse(2, { statuses: ['failed'] })
            : createMixedProcessingResponse();

        await route.fulfill({ status: 200, json: response });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      // WHEN: User opens filters and selects "Failed" status
      await page.click('button:has-text("Filters")');
      await page.click('#status');
      await page.click('text=Failed');
      await page.click('button:has-text("Apply Filters")');

      // THEN: API was called with status filter
      await page.waitForTimeout(500);
      expect(lastFilterStatus).toBe('failed');
    });

    test('[P1] User filters documents by file type', async ({ page }) => {
      let lastFilterFileType: string | null = null;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing*', async (route) => {
        const url = new URL(route.request().url());
        lastFilterFileType = url.searchParams.get('file_type');
        await route.fulfill({ status: 200, json: createMixedProcessingResponse() });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      // WHEN: User opens filters and selects "PDF" file type
      await page.click('button:has-text("Filters")');
      await page.click('#file-type');
      await page.click('text=PDF');
      await page.click('button:has-text("Apply Filters")');

      // THEN: API was called with file_type filter
      await page.waitForTimeout(500);
      expect(lastFilterFileType).toBe('pdf');
    });

    test('[P1] User filters by processing step', async ({ page }) => {
      let lastFilterStep: string | null = null;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing*', async (route) => {
        const url = new URL(route.request().url());
        lastFilterStep = url.searchParams.get('current_step');
        await route.fulfill({ status: 200, json: createMixedProcessingResponse() });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      // WHEN: User opens filters and selects "Embed" step
      await page.click('button:has-text("Filters")');
      await page.click('#current-step');
      await page.click('text=Embed');
      await page.click('button:has-text("Apply Filters")');

      // THEN: API was called with current_step filter
      await page.waitForTimeout(500);
      expect(lastFilterStep).toBe('embed');
    });

    test('[P2] User resets filters', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing*', async (route) => {
        await route.fulfill({ status: 200, json: createMixedProcessingResponse() });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      // Set some filters
      await page.click('button:has-text("Filters")');
      await page.click('#status');
      await page.click('text=Failed');

      // WHEN: User clicks Reset
      await page.click('button:has-text("Reset")');

      // THEN: Filters are cleared
      await expect(page.locator('#status')).toContainText('All statuses');
    });
  });

  test.describe('AC-5.23.3: Click to view step-by-step processing details', () => {
    test('[P0] User clicks document to see processing details modal', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing', async (route) => {
        await route.fulfill({ status: 200, json: createMixedProcessingResponse() });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing/doc-ready', async (route) => {
        await route.fulfill({ status: 200, json: createCompletedDocumentDetails() });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      // WHEN: User clicks on a document row
      await page.click('tr:has-text("completed_doc.pdf")');

      // THEN: Processing details modal is visible
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText('Processing Details')).toBeVisible();

      // AND: Shows document info
      await expect(page.getByText('completed_document.pdf')).toBeVisible();

      // AND: Shows step-by-step timeline
      await expect(page.getByText('Processing Steps')).toBeVisible();
      await expect(page.getByText('Upload')).toBeVisible();
      await expect(page.getByText('Parse')).toBeVisible();
      await expect(page.getByText('Chunk')).toBeVisible();
      await expect(page.getByText('Embed')).toBeVisible();
      await expect(page.getByText('Index')).toBeVisible();

      // AND: Shows timing information
      await expect(page.getByText(/Duration:/)).toBeVisible();
    });

    test('[P1] Details modal shows error message for failed documents', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing', async (route) => {
        await route.fulfill({ status: 200, json: createMixedProcessingResponse() });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing/doc-failed', async (route) => {
        await route.fulfill({
          status: 200,
          json: createFailedDocumentDetails('embed', 'Embedding service unavailable'),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      // WHEN: User clicks on failed document
      await page.click('tr:has-text("failed_doc.txt")');

      // THEN: Modal shows error message
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText(/Error:/)).toBeVisible();
      await expect(page.getByText(/Embedding service unavailable/)).toBeVisible();
    });
  });

  test.describe('AC-5.23.4: Processing tab visible only to ADMIN/WRITE users', () => {
    test('[P0] Processing tab is visible for WRITE permission users', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Processing tab is visible
      await expect(page.getByRole('tab', { name: /Processing/i })).toBeVisible();
    });

    test('[P0] Processing tab is visible for ADMIN permission users', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'ADMIN' }],
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Processing tab is visible
      await expect(page.getByRole('tab', { name: /Processing/i })).toBeVisible();
    });

    test('[P0] Processing tab is hidden for READ-only users', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Processing tab is NOT visible
      await expect(page.getByRole('tab', { name: /Processing/i })).not.toBeVisible();

      // AND: Documents tab is visible
      await expect(page.getByRole('tab', { name: /Documents/i })).toBeVisible();
    });
  });

  test.describe('AC-5.23.5: Auto-refresh every 10 seconds', () => {
    test('[P1] Processing table auto-refreshes every 10 seconds', async ({ page }) => {
      let requestCount = 0;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing*', async (route) => {
        requestCount++;
        await route.fulfill({ status: 200, json: createMixedProcessingResponse() });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      const initialCount = requestCount;

      // WHEN: We wait for 10+ seconds
      await page.waitForTimeout(11000);

      // THEN: Additional API requests were made
      expect(requestCount).toBeGreaterThan(initialCount);
    });

    test('[P2] Manual refresh button works', async ({ page }) => {
      let requestCount = 0;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing*', async (route) => {
        requestCount++;
        await route.fulfill({ status: 200, json: createMixedProcessingResponse() });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      const initialCount = requestCount;

      // WHEN: User clicks refresh button
      await page.click('button:has-text("Refresh")');

      // THEN: API request is made
      await page.waitForTimeout(500);
      expect(requestCount).toBeGreaterThan(initialCount);
    });
  });

  test.describe('AC-5.23.6: Handle documents without processing info gracefully', () => {
    test('[P1] Empty state is shown when no documents exist', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing*', async (route) => {
        await route.fulfill({ status: 200, json: createEmptyProcessingResponse() });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      // THEN: Empty state message is shown
      await expect(page.getByText(/No documents found/i)).toBeVisible();
      await expect(
        page.getByText(/Try adjusting your filters or upload some documents/i)
      ).toBeVisible();
    });

    test('[P2] Loading state is shown while fetching data', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      // Delay the processing response
      await page.route('**/api/v1/knowledge-bases/kb-1/processing*', async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await route.fulfill({ status: 200, json: createMixedProcessingResponse() });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');

      // THEN: Loading indicator is shown
      await expect(page.locator('.animate-spin').first()).toBeVisible();
    });
  });

  test.describe('AC-5.23.7: Human-readable processing step names and timing', () => {
    test('[P1] Step names are human-readable', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing', async (route) => {
        await route.fulfill({ status: 200, json: createMixedProcessingResponse() });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing/doc-ready', async (route) => {
        await route.fulfill({ status: 200, json: createCompletedDocumentDetails() });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');
      await page.click('tr:has-text("completed_doc.pdf")');

      // THEN: Step names are human-readable (capitalized)
      await expect(page.getByText('Upload')).toBeVisible();
      await expect(page.getByText('Parse')).toBeVisible();
      await expect(page.getByText('Chunk')).toBeVisible();
      await expect(page.getByText('Embed')).toBeVisible();
      await expect(page.getByText('Index')).toBeVisible();
      await expect(page.getByText('Complete')).toBeVisible();
    });

    test('[P1] Timing is shown in human-readable format', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'WRITE' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing', async (route) => {
        await route.fulfill({ status: 200, json: createMixedProcessingResponse() });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/processing/doc-ready', async (route) => {
        await route.fulfill({ status: 200, json: createCompletedDocumentDetails() });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.click('button:has-text("Processing")');
      await page.click('tr:has-text("completed_doc.pdf")');

      // THEN: Duration is shown in human-readable format (e.g., "4.5s" or "1m 30s")
      await expect(page.getByText(/Duration:.*\d+(\.\d+)?s/)).toBeVisible();

      // AND: Total processing time is shown
      await expect(page.getByText(/Total processing time:/)).toBeVisible();
    });
  });
});
