import { test, expect, type Page } from '@playwright/test';
import {
  createArchivedDocument,
  createArchivedDocumentList,
  createArchiveStats,
  createEmptyKBStats,
  createSuccessfulRestoreOperation,
  createSuccessfulPurgeOperation,
  createBulkOperationResult,
  getDocumentActionRoutes,
  type ArchivedDocument,
} from '../../fixtures/document-actions.factory';

/**
 * E2E tests for Story 6-7: Archive Management UI
 *
 * Tests the archive management page including:
 * - Navigation and access
 * - Document list display with metadata
 * - KB filtering and search
 * - Pagination
 * - Restore and purge operations (single and bulk)
 * - Error handling
 * - Empty states
 *
 * Priority: P0 (core document lifecycle functionality)
 */

// Test constants
const TEST_KB_ID = 'kb-archive-test-001';
const TEST_KB_NAME = 'Test Knowledge Base';
const TEST_DOC_ID = 'doc-archived-001';

test.describe('Story 6-7: Archive Management UI', () => {
  test.describe('AC-6.7.1: Archive page accessible via navigation', () => {
    test('navigates to /archive from sidebar for KB owner', async ({ page }) => {
      // Setup: Mock user as KB owner
      await setupAuthenticatedUser(page, { is_admin: false, owned_kb_ids: [TEST_KB_ID] });
      await setupArchivedDocuments(page, TEST_KB_ID, createArchivedDocumentList(TEST_KB_ID, 5));

      await page.goto('/dashboard');

      // Click Archive link in sidebar
      await page.getByRole('link', { name: /archive/i }).click();

      // Should navigate to archive page
      await expect(page).toHaveURL(/\/archive/);

      // Should see archived documents list
      await expect(page.locator('[data-testid="archive-table"]')).toBeVisible();
    });

    test('navigates to /archive from sidebar for admin', async ({ page }) => {
      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, createArchivedDocumentList(TEST_KB_ID, 3));

      await page.goto('/dashboard');

      await page.getByRole('link', { name: /archive/i }).click();

      await expect(page).toHaveURL(/\/archive/);
      await expect(page.locator('[data-testid="archive-table"]')).toBeVisible();
    });

    test('archive link hidden for regular users without KB ownership', async ({ page }) => {
      await setupAuthenticatedUser(page, { is_admin: false, owned_kb_ids: [] });

      await page.goto('/dashboard');

      // Archive link should not be visible
      await expect(page.getByRole('link', { name: /archive/i })).not.toBeVisible();
    });
  });

  test.describe('AC-6.7.2: Archive list displays document metadata', () => {
    test('displays table with all required columns', async ({ page }) => {
      const archivedDocs = createArchivedDocumentList(TEST_KB_ID, 3);
      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, archivedDocs);

      await page.goto('/archive');

      // Verify table headers
      const table = page.locator('[data-testid="archive-table"]');
      await expect(table).toBeVisible();

      await expect(page.getByRole('columnheader', { name: /name/i })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: /knowledge base/i })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: /archived date/i })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: /file size/i })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: /actions/i })).toBeVisible();
    });

    test('documents sorted by archived date (most recent first)', async ({ page }) => {
      const now = new Date();
      const archivedDocs = [
        createArchivedDocument({
          kb_id: TEST_KB_ID,
          name: 'oldest.pdf',
          archived_at: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        }),
        createArchivedDocument({
          kb_id: TEST_KB_ID,
          name: 'newest.pdf',
          archived_at: now.toISOString(),
        }),
        createArchivedDocument({
          kb_id: TEST_KB_ID,
          name: 'middle.pdf',
          archived_at: new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        }),
      ];

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, archivedDocs);

      await page.goto('/archive');

      // First row should be newest document
      const firstRow = page.locator('[data-testid="archive-row"]').first();
      await expect(firstRow).toContainText('newest.pdf');
    });
  });

  test.describe('AC-6.7.3: Filter by Knowledge Base', () => {
    test('KB filter dropdown shows accessible KBs', async ({ page }) => {
      const kb1Docs = createArchivedDocumentList('kb-001', 2);
      const kb2Docs = createArchivedDocumentList('kb-002', 3);

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupMultiKBArchivedDocuments(page, [
        { kbId: 'kb-001', kbName: 'KB One', docs: kb1Docs },
        { kbId: 'kb-002', kbName: 'KB Two', docs: kb2Docs },
      ]);

      await page.goto('/archive');

      // Open KB filter dropdown
      await page.getByRole('combobox', { name: /knowledge base/i }).click();

      // Should show all KBs
      await expect(page.getByRole('option', { name: /all knowledge bases/i })).toBeVisible();
      await expect(page.getByRole('option', { name: /kb one/i })).toBeVisible();
      await expect(page.getByRole('option', { name: /kb two/i })).toBeVisible();
    });

    test('selecting KB filters document list', async ({ page }) => {
      const kb1Docs = createArchivedDocumentList('kb-001', 2).map((d) => ({
        ...d,
        name: `kb1-${d.name}`,
      }));
      const kb2Docs = createArchivedDocumentList('kb-002', 3).map((d) => ({
        ...d,
        name: `kb2-${d.name}`,
      }));

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupMultiKBArchivedDocuments(page, [
        { kbId: 'kb-001', kbName: 'KB One', docs: kb1Docs },
        { kbId: 'kb-002', kbName: 'KB Two', docs: kb2Docs },
      ]);

      await page.goto('/archive');

      // Initially shows all documents
      await expect(page.locator('[data-testid="archive-row"]')).toHaveCount(5);

      // Filter by KB One
      await page.getByRole('combobox', { name: /knowledge base/i }).click();
      await page.getByRole('option', { name: /kb one/i }).click();

      // Should show only KB One documents
      await expect(page.locator('[data-testid="archive-row"]')).toHaveCount(2);
      await expect(page.getByText('kb1-archived')).toBeVisible();
    });
  });

  test.describe('AC-6.7.4: Search archived documents', () => {
    test('search filters documents by name', async ({ page }) => {
      const archivedDocs = [
        createArchivedDocument({ kb_id: TEST_KB_ID, name: 'annual-report-2024.pdf' }),
        createArchivedDocument({ kb_id: TEST_KB_ID, name: 'quarterly-summary.pdf' }),
        createArchivedDocument({ kb_id: TEST_KB_ID, name: 'meeting-notes.pdf' }),
      ];

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, archivedDocs);

      await page.goto('/archive');

      // Search for "report"
      await page.getByPlaceholder(/search/i).fill('report');

      // Wait for debounce
      await page.waitForTimeout(500);

      // Should only show matching document
      await expect(page.locator('[data-testid="archive-row"]')).toHaveCount(1);
      await expect(page.getByText('annual-report-2024.pdf')).toBeVisible();
    });

    test('search is case-insensitive', async ({ page }) => {
      const archivedDocs = [
        createArchivedDocument({ kb_id: TEST_KB_ID, name: 'UPPERCASE-DOC.pdf' }),
        createArchivedDocument({ kb_id: TEST_KB_ID, name: 'other-file.pdf' }),
      ];

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, archivedDocs);

      await page.goto('/archive');

      // Search lowercase
      await page.getByPlaceholder(/search/i).fill('uppercase');
      await page.waitForTimeout(500);

      await expect(page.locator('[data-testid="archive-row"]')).toHaveCount(1);
      await expect(page.getByText('UPPERCASE-DOC.pdf')).toBeVisible();
    });
  });

  test.describe('AC-6.7.5: Pagination support', () => {
    test('shows pagination when more than 20 documents', async ({ page }) => {
      const archivedDocs = createArchivedDocumentList(TEST_KB_ID, 25);

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupPaginatedArchivedDocuments(page, archivedDocs, 20);

      await page.goto('/archive');

      // Should show pagination controls
      await expect(page.getByRole('button', { name: /next/i })).toBeVisible();
      await expect(page.getByText(/page 1/i)).toBeVisible();
    });

    test('navigation between pages works', async ({ page }) => {
      const archivedDocs = createArchivedDocumentList(TEST_KB_ID, 25);

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupPaginatedArchivedDocuments(page, archivedDocs, 20);

      await page.goto('/archive');

      // Go to next page
      await page.getByRole('button', { name: /next/i }).click();

      // Should show page 2
      await expect(page.getByText(/page 2/i)).toBeVisible();

      // Should have remaining documents (5)
      await expect(page.locator('[data-testid="archive-row"]')).toHaveCount(5);
    });
  });

  test.describe('AC-6.7.6: Restore action from archive page', () => {
    test('restore button triggers confirmation dialog', async ({ page }) => {
      const archivedDoc = createArchivedDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'archived-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, [archivedDoc]);

      await page.goto('/archive');

      // Click restore button
      await page.getByRole('button', { name: /restore/i }).click();

      // Confirmation dialog should appear
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText(/restore this document/i)).toBeVisible();
    });

    test('confirm restore removes document from list', async ({ page }) => {
      const archivedDoc = createArchivedDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'archived-doc.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, [archivedDoc]);
      await setupRestoreEndpoint(page, TEST_KB_ID, TEST_DOC_ID, true);

      await page.goto('/archive');

      // Click restore
      await page.getByRole('button', { name: /restore/i }).click();

      // Confirm in dialog
      await page.getByRole('dialog').getByRole('button', { name: /confirm|restore/i }).click();

      // Wait for dialog to close
      await expect(page.getByRole('dialog')).not.toBeVisible();

      // Success toast should appear
      await expect(page.getByText(/restored/i)).toBeVisible();

      // Document should be removed from list
      await expect(page.getByText('archived-doc.pdf')).not.toBeVisible();
    });
  });

  test.describe('AC-6.7.7: Purge action from archive page', () => {
    test('purge button triggers two-step confirmation', async ({ page }) => {
      const archivedDoc = createArchivedDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-purge.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, [archivedDoc]);

      await page.goto('/archive');

      // Click purge button
      await page.getByRole('button', { name: /purge|delete/i }).click();

      // First confirmation dialog
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText(/permanently delete/i)).toBeVisible();
    });

    test('confirm purge requires typing DELETE', async ({ page }) => {
      const archivedDoc = createArchivedDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'to-purge.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, [archivedDoc]);
      await setupPurgeEndpoint(page, TEST_KB_ID, TEST_DOC_ID, true);

      await page.goto('/archive');

      // Click purge
      await page.getByRole('button', { name: /purge|delete/i }).click();

      // Type confirmation text
      await page.getByPlaceholder(/type.*delete/i).fill('DELETE');

      // Confirm button should be enabled
      await page.getByRole('dialog').getByRole('button', { name: /confirm|delete/i }).click();

      // Success toast
      await expect(page.getByText(/permanently deleted/i)).toBeVisible();

      // Document removed
      await expect(page.getByText('to-purge.pdf')).not.toBeVisible();
    });
  });

  test.describe('AC-6.7.8: Bulk purge selection', () => {
    test('selecting multiple documents enables bulk purge button', async ({ page }) => {
      const archivedDocs = createArchivedDocumentList(TEST_KB_ID, 3);

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, archivedDocs);

      await page.goto('/archive');

      // Select first two documents
      await page.locator('[data-testid="archive-row"]').nth(0).getByRole('checkbox').click();
      await page.locator('[data-testid="archive-row"]').nth(1).getByRole('checkbox').click();

      // Bulk purge button should be visible
      await expect(page.getByRole('button', { name: /purge selected/i })).toBeVisible();
      await expect(page.getByText(/2 selected/i)).toBeVisible();
    });

    test('bulk purge shows confirmation with count', async ({ page }) => {
      const archivedDocs = createArchivedDocumentList(TEST_KB_ID, 3);

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, archivedDocs);

      await page.goto('/archive');

      // Select all via header checkbox
      await page.getByRole('checkbox', { name: /select all/i }).click();

      // Click bulk purge
      await page.getByRole('button', { name: /purge selected/i }).click();

      // Confirmation should show count
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText(/3 documents/i)).toBeVisible();
    });

    test('bulk purge removes all selected documents', async ({ page }) => {
      const archivedDocs = createArchivedDocumentList(TEST_KB_ID, 3);

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, archivedDocs);
      await setupBulkPurgeEndpoint(page, archivedDocs.map((d) => d.id));

      await page.goto('/archive');

      // Select all
      await page.getByRole('checkbox', { name: /select all/i }).click();

      // Click bulk purge
      await page.getByRole('button', { name: /purge selected/i }).click();

      // Type DELETE and confirm
      await page.getByPlaceholder(/type.*delete/i).fill('DELETE');
      await page.getByRole('dialog').getByRole('button', { name: /confirm|delete/i }).click();

      // All documents should be removed
      await expect(page.locator('[data-testid="archive-row"]')).toHaveCount(0);
      await expect(page.getByText(/3 documents purged/i)).toBeVisible();
    });
  });

  test.describe('AC-6.7.9: Handle restore name collision', () => {
    test('shows error when restore fails with 409', async ({ page }) => {
      const archivedDoc = createArchivedDocument({
        id: TEST_DOC_ID,
        kb_id: TEST_KB_ID,
        name: 'duplicate-name.pdf',
      });

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, [archivedDoc]);

      // Mock 409 conflict on restore
      await page.route(`**/api/v1/documents/${TEST_DOC_ID}/restore`, async (route) => {
        await route.fulfill({
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Cannot restore: a document with this name already exists',
          }),
        });
      });

      await page.goto('/archive');

      // Attempt restore
      await page.getByRole('button', { name: /restore/i }).click();
      await page.getByRole('dialog').getByRole('button', { name: /confirm|restore/i }).click();

      // Error message should be shown
      await expect(page.getByText(/document with this name already exists/i)).toBeVisible();

      // Document should still be in list (not removed)
      await expect(page.getByText('duplicate-name.pdf')).toBeVisible();
    });
  });

  test.describe('AC-6.7.10: Empty state display', () => {
    test('shows empty state when no archived documents', async ({ page }) => {
      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, []);

      await page.goto('/archive');

      // Empty state should be visible
      await expect(page.getByText(/no archived documents/i)).toBeVisible();

      // Table should not be visible
      await expect(page.locator('[data-testid="archive-table"]')).not.toBeVisible();
    });

    test('shows empty state after filtering with no results', async ({ page }) => {
      const archivedDocs = createArchivedDocumentList(TEST_KB_ID, 3);

      await setupAuthenticatedUser(page, { is_admin: true });
      await setupArchivedDocuments(page, TEST_KB_ID, archivedDocs);

      await page.goto('/archive');

      // Search for non-existent term
      await page.getByPlaceholder(/search/i).fill('nonexistent-xyz-123');
      await page.waitForTimeout(500);

      // Should show empty search results message
      await expect(page.getByText(/no documents found/i)).toBeVisible();
    });
  });

  test.describe('Edge Cases and Error Handling', () => {
    test('handles server error gracefully', async ({ page }) => {
      await setupAuthenticatedUser(page, { is_admin: true });

      // Mock server error
      await page.route('**/api/v1/documents/archived**', async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Internal server error' }),
        });
      });

      await page.goto('/archive');

      // Should show error state
      await expect(page.getByText(/error loading/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /retry/i })).toBeVisible();
    });

    test('retry button reloads data after error', async ({ page }) => {
      await setupAuthenticatedUser(page, { is_admin: true });

      let requestCount = 0;
      await page.route('**/api/v1/documents/archived**', async (route) => {
        requestCount++;
        if (requestCount === 1) {
          await route.fulfill({
            status: 500,
            body: JSON.stringify({ detail: 'Server error' }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              items: createArchivedDocumentList(TEST_KB_ID, 2),
              total: 2,
              page: 1,
              limit: 20,
            }),
          });
        }
      });

      await page.goto('/archive');

      // Should show error
      await expect(page.getByText(/error loading/i)).toBeVisible();

      // Click retry
      await page.getByRole('button', { name: /retry/i }).click();

      // Should now show documents
      await expect(page.locator('[data-testid="archive-row"]')).toHaveCount(2);
    });
  });
});

// ============================================================
// Helper Functions
// ============================================================

async function setupAuthenticatedUser(
  page: Page,
  options: { is_admin: boolean; owned_kb_ids?: string[] }
) {
  await page.route('**/api/v1/users/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'user-test-001',
        email: 'test@example.com',
        is_admin: options.is_admin,
        is_active: true,
        owned_kb_ids: options.owned_kb_ids || [],
      }),
    });
  });
}

async function setupArchivedDocuments(page: Page, kbId: string, docs: ArchivedDocument[]) {
  await page.route('**/api/v1/documents/archived**', async (route) => {
    const url = new URL(route.request().url());
    const searchQuery = url.searchParams.get('search')?.toLowerCase() || '';
    const filterKbId = url.searchParams.get('kb_id');

    let filteredDocs = docs;

    if (filterKbId) {
      filteredDocs = filteredDocs.filter((d) => d.kb_id === filterKbId);
    }

    if (searchQuery) {
      filteredDocs = filteredDocs.filter((d) => d.name.toLowerCase().includes(searchQuery));
    }

    // Sort by archived_at descending
    filteredDocs.sort(
      (a, b) => new Date(b.archived_at!).getTime() - new Date(a.archived_at!).getTime()
    );

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: filteredDocs.map((d) => ({
          ...d,
          kb_name: 'Test Knowledge Base',
        })),
        total: filteredDocs.length,
        page: 1,
        limit: 20,
      }),
    });
  });
}

async function setupMultiKBArchivedDocuments(
  page: Page,
  kbData: Array<{ kbId: string; kbName: string; docs: ArchivedDocument[] }>
) {
  const allDocs = kbData.flatMap(({ kbId, kbName, docs }) =>
    docs.map((d) => ({ ...d, kb_id: kbId, kb_name: kbName }))
  );

  await page.route('**/api/v1/documents/archived**', async (route) => {
    const url = new URL(route.request().url());
    const filterKbId = url.searchParams.get('kb_id');

    let filteredDocs = allDocs;
    if (filterKbId) {
      filteredDocs = filteredDocs.filter((d) => d.kb_id === filterKbId);
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: filteredDocs,
        total: filteredDocs.length,
        page: 1,
        limit: 20,
      }),
    });
  });

  // Mock KB list for filter dropdown
  await page.route('**/api/v1/knowledge-bases**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: kbData.map(({ kbId, kbName }) => ({
          id: kbId,
          name: kbName,
        })),
        total: kbData.length,
      }),
    });
  });
}

async function setupPaginatedArchivedDocuments(
  page: Page,
  docs: ArchivedDocument[],
  pageSize: number
) {
  await page.route('**/api/v1/documents/archived**', async (route) => {
    const url = new URL(route.request().url());
    const pageNum = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || String(pageSize));

    const start = (pageNum - 1) * limit;
    const end = start + limit;
    const pagedDocs = docs.slice(start, end);

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: pagedDocs.map((d) => ({ ...d, kb_name: 'Test KB' })),
        total: docs.length,
        page: pageNum,
        limit,
      }),
    });
  });
}

async function setupRestoreEndpoint(page: Page, kbId: string, docId: string, success: boolean) {
  await page.route(`**/api/v1/documents/${docId}/restore`, async (route) => {
    if (success) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSuccessfulRestoreOperation(docId)),
      });
    } else {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Restore failed' }),
      });
    }
  });
}

async function setupPurgeEndpoint(page: Page, kbId: string, docId: string, success: boolean) {
  await page.route(`**/api/v1/documents/${docId}/purge`, async (route) => {
    if (success) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSuccessfulPurgeOperation(docId)),
      });
    } else {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Purge failed' }),
      });
    }
  });
}

async function setupBulkPurgeEndpoint(page: Page, docIds: string[]) {
  await page.route('**/api/v1/documents/bulk-purge', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createBulkOperationResult(docIds, 'purge', 0)),
    });
  });
}
