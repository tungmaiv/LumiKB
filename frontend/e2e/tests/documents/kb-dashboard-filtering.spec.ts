/**
 * E2E Tests for KB Dashboard Document Filtering & Pagination
 * Story 5-24: KB Dashboard Document Filtering & Pagination
 *
 * Tests cover all 5 acceptance criteria:
 * - AC-5.24.1: Filter bar with search, type, status, tags, date range
 * - AC-5.24.2: Real-time filter updates
 * - AC-5.24.3: Pagination controls
 * - AC-5.24.4: URL persistence for filter state
 * - AC-5.24.5: Tag-based filtering (multi-select)
 */

import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/dashboard.page';
import {
  createMockDocumentsWithTags,
  createMockPaginatedDocuments,
} from '../../fixtures/document-tags.factory';

test.describe('KB Dashboard Filtering & Pagination - E2E', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
  });

  test.describe('AC-5.24.1: Filter bar with multiple filter options', () => {
    test('[P0] Filter bar is visible on dashboard', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(10), total: 10 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Filter bar is visible
      await expect(page.locator('[data-testid="document-filter-bar"]')).toBeVisible();

      // AND: Search input is visible
      await expect(page.getByPlaceholder(/search documents/i)).toBeVisible();

      // AND: Type filter is visible
      await expect(page.getByRole('combobox', { name: /type/i })).toBeVisible();

      // AND: Status filter is visible
      await expect(page.getByRole('combobox', { name: /status/i })).toBeVisible();
    });

    test('[P0] User can filter by search term', async ({ page }) => {
      let lastSearchTerm: string | null = null;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastSearchTerm = url.searchParams.get('search');
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User types in search
      await dashboardPage.searchDocuments('financial report');

      // THEN: API receives search parameter
      expect(lastSearchTerm).toBe('financial report');
    });

    test('[P0] User can filter by file type', async ({ page }) => {
      let lastMimeType: string | null = null;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastMimeType = url.searchParams.get('mimeType');
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User selects PDF filter
      await dashboardPage.filterByType('pdf');

      // THEN: API receives mime type filter
      await page.waitForTimeout(500);
      expect(lastMimeType).toMatch(/pdf/i);
    });

    test('[P0] User can filter by status', async ({ page }) => {
      let lastStatus: string | null = null;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastStatus = url.searchParams.get('status');
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User selects Processing status
      await dashboardPage.filterByStatus('processing');

      // THEN: API receives status filter
      await page.waitForTimeout(500);
      expect((lastStatus as string | null)?.toLowerCase()).toBe('processing');
    });

    test('[P1] User can filter by date range', async ({ page }) => {
      let lastDateFrom: string | null = null;
      let lastDateTo: string | null = null;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastDateFrom = url.searchParams.get('dateFrom');
        lastDateTo = url.searchParams.get('dateTo');
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User sets date range
      await dashboardPage.filterByDateRange('2024-01-01', '2024-12-31');

      // THEN: API receives date filters
      await page.waitForTimeout(500);
      expect(lastDateFrom).toBe('2024-01-01');
      expect(lastDateTo).toBe('2024-12-31');
    });

    test('[P1] User can combine multiple filters', async ({ page }) => {
      let lastSearch: string | null = null;
      let lastStatus: string | null = null;
      let lastMimeType: string | null = null;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastSearch = url.searchParams.get('search');
        lastStatus = url.searchParams.get('status');
        lastMimeType = url.searchParams.get('mimeType');
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(2), total: 2 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User applies multiple filters
      await dashboardPage.searchDocuments('report');
      await dashboardPage.filterByType('pdf');
      await dashboardPage.filterByStatus('processed');

      // THEN: API receives all filters
      await page.waitForTimeout(500);
      expect(lastSearch).toBe('report');
      expect(lastMimeType).toMatch(/pdf/i);
      expect((lastStatus as string | null)?.toLowerCase()).toBe('processed');
    });

    test('[P1] Clear filters button resets all filters', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(10), total: 10 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // Apply some filters
      await dashboardPage.searchDocuments('test');
      await dashboardPage.filterByStatus('failed');

      // WHEN: User clicks clear filters
      await dashboardPage.clearFilters();

      // THEN: Search input is empty
      await expect(page.getByPlaceholder(/search documents/i)).toHaveValue('');

      // AND: URL has no filter params
      const url = page.url();
      expect(url).not.toMatch(/search=/);
      expect(url).not.toMatch(/status=/);
    });
  });

  test.describe('AC-5.24.2: Real-time filter updates', () => {
    test('[P0] Document list updates when filter changes', async ({ page }) => {
      let requestCount = 0;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        requestCount++;
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      const initialCount = requestCount;

      // WHEN: User applies filter
      await dashboardPage.filterByStatus('processed');

      // THEN: API was called again
      await page.waitForTimeout(500);
      expect(requestCount).toBeGreaterThan(initialCount);
    });

    test('[P1] Search has debounce delay', async ({ page }) => {
      let requestCount = 0;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        requestCount++;
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      const initialCount = requestCount;

      // WHEN: User types quickly
      const searchInput = page.getByPlaceholder(/search documents/i);
      await searchInput.type('test query', { delay: 50 });

      // THEN: Only one additional request was made (debounced)
      await page.waitForTimeout(600);
      expect(requestCount).toBe(initialCount + 1);
    });

    test('[P1] Loading indicator shown during filter change', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        // Add delay to see loading state
        await new Promise((resolve) => setTimeout(resolve, 500));
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');
      await page.waitForTimeout(600);

      // WHEN: User applies filter
      await dashboardPage.filterByType('pdf');

      // THEN: Loading indicator appears
      const isLoading = await dashboardPage.isLoadingVisible();
      expect(isLoading).toBe(true);
    });

    test('[P2] Empty state shown when filters return no results', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      let isFiltered = false;
      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        isFiltered = url.searchParams.has('search');

        await route.fulfill({
          status: 200,
          json: isFiltered
            ? { documents: [], total: 0 }
            : { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User searches for non-existent content
      await dashboardPage.searchDocuments('xyznonexistent12345');

      // THEN: Empty state is shown
      await page.waitForTimeout(500);
      const isEmpty = await dashboardPage.isEmptyStateVisible();
      expect(isEmpty).toBe(true);
    });
  });

  test.describe('AC-5.24.3: Pagination controls', () => {
    test('[P0] Pagination controls are visible', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: createMockPaginatedDocuments(1, 50, 150),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Pagination info is visible
      await expect(page.locator('[data-testid="pagination-info"]')).toBeVisible();

      // AND: Next button is visible
      await expect(page.getByRole('button', { name: /next/i })).toBeVisible();

      // AND: Previous button is visible
      await expect(page.getByRole('button', { name: /previous/i })).toBeVisible();
    });

    test('[P0] User can navigate to next page', async ({ page }) => {
      let lastPage = 1;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastPage = parseInt(url.searchParams.get('page') || '1');
        await route.fulfill({
          status: 200,
          json: createMockPaginatedDocuments(lastPage, 50, 150),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User clicks next
      await dashboardPage.goToNextPage();

      // THEN: Page 2 is loaded
      await page.waitForTimeout(500);
      expect(lastPage).toBe(2);
    });

    test('[P0] User can navigate to previous page', async ({ page }) => {
      let lastPage = 2;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastPage = parseInt(url.searchParams.get('page') || '1');
        await route.fulfill({
          status: 200,
          json: createMockPaginatedDocuments(lastPage, 50, 150),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.gotoWithKB('kb-1');
      // Navigate to page 2 via URL
      await page.goto(page.url() + '&page=2');
      await page.waitForTimeout(500);

      // WHEN: User clicks previous
      await dashboardPage.goToPreviousPage();

      // THEN: Page 1 is loaded
      await page.waitForTimeout(500);
      expect(lastPage).toBe(1);
    });

    test('[P1] Previous is disabled on first page', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: createMockPaginatedDocuments(1, 50, 150),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Previous button is disabled
      const isPrevEnabled = await dashboardPage.isPreviousPageEnabled();
      expect(isPrevEnabled).toBe(false);
    });

    test('[P1] Next is disabled on last page', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        // Last page: 3 pages of 50 = 150 docs
        await route.fulfill({
          status: 200,
          json: createMockPaginatedDocuments(3, 50, 150),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.gotoWithKB('kb-1');
      // Navigate to last page
      await page.goto(page.url() + '&page=3');
      await page.waitForTimeout(500);

      // THEN: Next button is disabled
      const isNextEnabled = await dashboardPage.isNextPageEnabled();
      expect(isNextEnabled).toBe(false);
    });

    test('[P1] User can change page size', async ({ page }) => {
      let lastLimit = 50;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastLimit = parseInt(url.searchParams.get('limit') || '50');
        await route.fulfill({
          status: 200,
          json: createMockPaginatedDocuments(1, lastLimit, 150),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User changes page size
      await dashboardPage.setPageSize(100);

      // THEN: API receives new limit
      await page.waitForTimeout(500);
      expect(lastLimit).toBe(100);
    });

    test('[P2] Changing page size resets to page 1', async ({ page }) => {
      let lastPage = 2;

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastPage = parseInt(url.searchParams.get('page') || '1');
        await route.fulfill({
          status: 200,
          json: createMockPaginatedDocuments(lastPage, 50, 150),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.gotoWithKB('kb-1');
      // Start on page 2
      await page.goto(page.url() + '&page=2');
      await page.waitForTimeout(500);

      // WHEN: User changes page size
      await dashboardPage.setPageSize(100);

      // THEN: Page is reset to 1
      await page.waitForTimeout(500);
      expect(lastPage).toBe(1);
    });
  });

  test.describe('AC-5.24.4: URL persistence for filter state', () => {
    test('[P0] Filters are persisted in URL', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User applies filters
      await dashboardPage.searchDocuments('test');
      await dashboardPage.filterByStatus('processed');

      // THEN: URL contains filter params
      await page.waitForTimeout(500);
      const url = page.url();
      expect(url).toMatch(/search=test/);
      expect(url).toMatch(/status=processed/i);
    });

    test('[P0] Filters are restored from URL on page load', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      let receivedSearch: string | null = null;
      let receivedStatus: string | null = null;

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        receivedSearch = url.searchParams.get('search');
        receivedStatus = url.searchParams.get('status');
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();

      // WHEN: User navigates with filter params in URL
      await page.goto('/dashboard?kb=kb-1&search=report&status=READY');

      // THEN: API receives filter params
      await page.waitForTimeout(500);
      expect(receivedSearch).toBe('report');
      expect(receivedStatus).toBe('READY');

      // AND: Search input shows the value
      await expect(page.getByPlaceholder(/search documents/i)).toHaveValue('report');
    });

    test('[P1] Pagination is persisted in URL', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: createMockPaginatedDocuments(1, 50, 150),
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User navigates to page 2
      await dashboardPage.goToNextPage();

      // THEN: URL contains page param
      await page.waitForTimeout(500);
      expect(page.url()).toMatch(/page=2/);
    });

    test('[P1] Sharing URL restores exact state', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      let receivedParams: Record<string, string | null> = {};

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        receivedParams = {
          search: url.searchParams.get('search'),
          status: url.searchParams.get('status'),
          page: url.searchParams.get('page'),
          limit: url.searchParams.get('limit'),
        };
        await route.fulfill({
          status: 200,
          json: createMockPaginatedDocuments(2, 100, 250),
        });
      });

      await dashboardPage.loginAsUser();

      // WHEN: User opens shared URL with all params
      await page.goto('/dashboard?kb=kb-1&search=finance&status=PROCESSING&page=2&limit=100');

      // THEN: All params are applied
      await page.waitForTimeout(500);
      expect(receivedParams.search).toBe('finance');
      expect(receivedParams.status).toBe('PROCESSING');
      expect(receivedParams.page).toBe('2');
      expect(receivedParams.limit).toBe('100');
    });

    test('[P2] Invalid URL params are handled gracefully', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      let receivedPage: string | null = null;

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        receivedPage = url.searchParams.get('page');
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();

      // WHEN: User navigates with invalid params
      await page.goto('/dashboard?kb=kb-1&page=-5&limit=999');

      // THEN: Invalid values are normalized
      await page.waitForTimeout(500);
      // Page should be 1 (negative normalized)
      expect(receivedPage).toBe('1');
    });
  });

  test.describe('AC-5.24.5: Tag-based filtering (multi-select)', () => {
    test('[P0] Tag filter dropdown shows available tags', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(10), total: 10 },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/tags', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            tags: ['policy', 'hr', 'technical', 'legal', 'finance'],
          },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User opens tag filter
      await page.click('[data-testid="tag-filter"]');

      // THEN: Available tags are shown
      await expect(page.getByRole('option', { name: 'policy' })).toBeVisible();
      await expect(page.getByRole('option', { name: 'hr' })).toBeVisible();
      await expect(page.getByRole('option', { name: 'technical' })).toBeVisible();
    });

    test('[P0] User can select multiple tags', async ({ page }) => {
      let lastTags: string[] = [];

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastTags = url.searchParams.getAll('tags');
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/tags', async (route) => {
        await route.fulfill({
          status: 200,
          json: { tags: ['policy', 'hr', 'finance'] },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User selects multiple tags
      await dashboardPage.filterByTags(['policy', 'finance']);

      // THEN: API receives both tags
      await page.waitForTimeout(500);
      expect(lastTags).toContain('policy');
      expect(lastTags).toContain('finance');
    });

    test('[P1] Selected tags appear as chips', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/tags', async (route) => {
        await route.fulfill({
          status: 200,
          json: { tags: ['policy', 'hr', 'finance'] },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // WHEN: User selects tags
      await dashboardPage.filterByTags(['policy', 'finance']);

      // THEN: Selected tags appear as removable chips
      await expect(page.locator('[data-testid="active-filter-chip"]').filter({ hasText: 'policy' })).toBeVisible();
      await expect(page.locator('[data-testid="active-filter-chip"]').filter({ hasText: 'finance' })).toBeVisible();
    });

    test('[P1] User can remove individual tag filter', async ({ page }) => {
      let lastTags: string[] = [];

      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        const url = new URL(route.request().url());
        lastTags = url.searchParams.getAll('tags');
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/tags', async (route) => {
        await route.fulfill({
          status: 200,
          json: { tags: ['policy', 'hr', 'finance'] },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // Select multiple tags
      await dashboardPage.filterByTags(['policy', 'finance']);
      await page.waitForTimeout(500);

      // WHEN: User removes one tag
      const policyChip = page.locator('[data-testid="active-filter-chip"]').filter({ hasText: 'policy' });
      await policyChip.locator('button').click();

      // THEN: Only remaining tag is in filter
      await page.waitForTimeout(500);
      expect(lastTags).not.toContain('policy');
      expect(lastTags).toContain('finance');
    });
  });

  test.describe('Edge Cases and Error Handling', () => {
    test('[P2] Handles API error gracefully', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 500,
          json: { detail: 'Internal server error' },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Error state is shown
      await expect(page.getByText(/error|failed|something went wrong/i)).toBeVisible();
    });

    test('[P2] Handles empty KB gracefully', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [{ id: 'kb-1', name: 'Test KB', permission_level: 'READ' }],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/kb-1/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: { documents: [], total: 0 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // THEN: Empty state is shown
      const isEmpty = await dashboardPage.isEmptyStateVisible();
      expect(isEmpty).toBe(true);
    });

    test('[P2] Filters reset when switching KB', async ({ page }) => {
      await page.route('**/api/v1/knowledge-bases', async (route) => {
        await route.fulfill({
          status: 200,
          json: {
            data: [
              { id: 'kb-1', name: 'KB One', permission_level: 'READ' },
              { id: 'kb-2', name: 'KB Two', permission_level: 'READ' },
            ],
          },
        });
      });

      await page.route('**/api/v1/knowledge-bases/*/documents*', async (route) => {
        await route.fulfill({
          status: 200,
          json: { documents: createMockDocumentsWithTags(5), total: 5 },
        });
      });

      await dashboardPage.loginAsUser();
      await dashboardPage.goto();
      await page.click('[data-testid="kb-selector-kb-1"]');

      // Apply filter on KB-1
      await dashboardPage.searchDocuments('test');

      // WHEN: User switches to KB-2
      await page.click('[data-testid="kb-selector-kb-2"]');

      // THEN: Search is cleared
      await page.waitForTimeout(500);
      await expect(page.getByPlaceholder(/search documents/i)).toHaveValue('');
    });
  });
});
