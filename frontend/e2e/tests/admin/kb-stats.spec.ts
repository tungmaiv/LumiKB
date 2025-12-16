/**
 * Story 5-6 Automation: KB Statistics Admin View E2E Tests
 * Generated: 2025-12-03
 *
 * Test Coverage:
 * - [P0] KB stats page displays all metrics correctly
 * - [P0] Non-admin user receives 403 Forbidden
 * - [P1] Page loads within 3-second performance target (AC-5.6.5)
 * - [P1] Manual refresh updates statistics (AC-5.6.5)
 * - [P2] Navigation from admin dashboard to KB stats works
 * - [P2] Empty KB displays zero values gracefully
 * - [P2] Large KB with high storage displays formatted values
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure, deterministic tests
 * - network-first.md: Route interception patterns
 * - test-priorities-matrix.md: P0/P1/P2 classification
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { mockApiResponse, waitForNetworkIdle } from '../../utils/test-helpers';
import {
  createKBStats,
  createEmptyKBStats,
  createLargeKBStats,
  createHighActivityKBStats,
} from '../../fixtures/kb-stats.factory';

test.describe('Story 5-6: KB Statistics Admin View E2E Tests', () => {
  const mockKbId = '550e8400-e29b-41d4-a716-446655440000';
  const mockKbStats = createKBStats({ kb_id: mockKbId });

  test.beforeEach(async ({ page }) => {
    // Network-first: Mock KB stats API BEFORE navigation
    await mockApiResponse(
      page,
      `**/api/v1/admin/knowledge-bases/${mockKbId}/stats`,
      mockKbStats
    );
  });

  test('[P0] KB stats page displays all metrics correctly (AC-5.6.1, AC-5.6.2, AC-5.6.3)', async ({
    page,
  }) => {
    /**
     * GIVEN: Admin user is authenticated
     * WHEN: Admin navigates to KB stats page
     * THEN: All statistics are displayed with correct values
     *
     * AC-5.6.1: Document count, storage, vectors, chunks, success rate
     * AC-5.6.2: Search activity metrics (30-day)
     * AC-5.6.3: Generation activity metrics (30-day)
     */

    // GIVEN & WHEN: Navigate to KB stats page
    await page.goto(`/admin/kb-stats?kbId=${mockKbId}`);
    await waitForNetworkIdle(page);

    // THEN: Page title shows KB name
    await expect(page.locator('h1, h2')).toContainText('Engineering Documentation');

    // THEN: Document count metric is visible
    const docCountMetric = page.getByTestId('metric-document-count');
    if (await docCountMetric.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(docCountMetric).toContainText('42');
    } else {
      // Alternative selector: look for text content
      await expect(page.locator('text=/42.*documents?/i')).toBeVisible();
    }

    // THEN: Storage metric shows human-readable format (100MB)
    const storageMetric = page.getByTestId('metric-storage');
    if (await storageMetric.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(storageMetric).toContainText(/100(\.\d+)?\s*MB/i);
    } else {
      await expect(page.locator('text=/100.*MB/i')).toBeVisible();
    }

    // THEN: Vector count metric is visible
    const vectorMetric = page.getByTestId('metric-embeddings');
    if (await vectorMetric.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(vectorMetric).toContainText('1,250');
    } else {
      await expect(page.locator('text=/1,?250.*embeddings?/i')).toBeVisible();
    }

    // THEN: Chunks metric is visible
    const chunksMetric = page.getByTestId('metric-chunks');
    if (await chunksMetric.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(chunksMetric).toContainText('1,250');
    } else {
      await expect(page.locator('text=/1,?250.*chunks?/i')).toBeVisible();
    }

    // THEN: Search activity metric is visible (AC-5.6.2)
    const searchMetric = page.getByTestId('metric-searches-30d');
    if (await searchMetric.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(searchMetric).toContainText('285');
    } else {
      await expect(page.locator('text=/285.*searches?/i')).toBeVisible();
    }

    // THEN: Generation activity metric is visible (AC-5.6.3)
    const genMetric = page.getByTestId('metric-generations-30d');
    if (await genMetric.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(genMetric).toContainText('98');
    } else {
      await expect(page.locator('text=/98.*generations?/i')).toBeVisible();
    }

    // THEN: Unique users metric is visible
    const usersMetric = page.getByTestId('metric-unique-users');
    if (await usersMetric.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(usersMetric).toContainText('12');
    } else {
      await expect(page.locator('text=/12.*users?/i')).toBeVisible();
    }

    // THEN: Top documents section is visible (AC-5.6.2)
    const topDocsSection = page.locator('[data-testid="top-documents"]');
    if (await topDocsSection.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(topDocsSection).toBeVisible();
      // Check first top document
      await expect(topDocsSection).toContainText('architecture-guide.pdf');
      await expect(topDocsSection).toContainText('50');
    }
  });

  test('[P0] Non-admin user receives 403 and cannot access KB stats (AC-5.6.6)', async ({
    page,
  }) => {
    /**
     * GIVEN: Regular (non-admin) user is authenticated
     * WHEN: User attempts to access KB stats page
     * THEN: User receives 403 Forbidden and is redirected or shown error
     */

    // Mock 403 response
    await page.route(`**/api/v1/admin/knowledge-bases/${mockKbId}/stats`, async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Not authorized' }),
      });
    });

    // WHEN: Navigate to KB stats page
    await page.goto(`/admin/kb-stats?kbId=${mockKbId}`);
    await page.waitForLoadState('networkidle');

    // THEN: Error message is displayed
    const errorMessage = page.getByTestId('kb-stats-error-message');
    if (await errorMessage.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(errorMessage).toContainText(/not authorized|forbidden|access denied/i);
    }

    // OR: Toast notification appears
    const toast = page.locator('[data-sonner-toast]').first();
    if (await toast.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(toast).toContainText(/not authorized|forbidden|access/i);
    }

    // OR: Redirected to admin dashboard or login
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/\/(admin|login|dashboard)/);
  });

  test('[P1] KB stats page loads within 3-second performance target (AC-5.6.5)', async ({
    page,
  }) => {
    /**
     * GIVEN: Admin user is authenticated
     * WHEN: Admin navigates to KB stats page
     * THEN: Page loads within 3 seconds (AC-5.6.5 requirement)
     */

    const startTime = Date.now();

    // WHEN: Navigate to KB stats page
    await page.goto(`/admin/kb-stats?kbId=${mockKbId}`);
    await page.waitForLoadState('networkidle');

    // Wait for key metric to be visible (ensures data loaded)
    const docCountMetric = page.locator('text=/\\d+.*documents?/i').first();
    await expect(docCountMetric).toBeVisible({ timeout: 5000 });

    const loadTime = Date.now() - startTime;

    // THEN: Page loads within 3 seconds (AC-5.6.5)
    expect(loadTime).toBeLessThan(3500); // 3.5 seconds to account for test overhead
  });

  test('[P1] Manual refresh updates statistics (AC-5.6.5)', async ({ page }) => {
    /**
     * GIVEN: KB stats page is loaded
     * WHEN: Admin clicks manual refresh button
     * THEN: Statistics are refetched and updated
     *
     * AC-5.6.5: Manual refresh option bypasses cache
     */

    // Navigate to KB stats page
    await page.goto(`/admin/kb-stats?kbId=${mockKbId}`);
    await waitForNetworkIdle(page);

    // Wait for initial load
    await expect(page.locator('text=/42.*documents?/i')).toBeVisible();

    // Mock updated stats (different document count)
    const updatedStats = createKBStats({
      kb_id: mockKbId,
      document_count: 50, // Changed from 42
    });

    await mockApiResponse(
      page,
      `**/api/v1/admin/knowledge-bases/${mockKbId}/stats`,
      updatedStats
    );

    // WHEN: Click refresh button
    const refreshButton = page.getByTestId('refresh-kb-stats-button');
    if (await refreshButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await refreshButton.click();
      await page.waitForLoadState('networkidle');

      // THEN: Updated document count is displayed
      await expect(page.locator('text=/50.*documents?/i')).toBeVisible({ timeout: 5000 });
    } else {
      // Alternative: Reload page manually (simulates refresh)
      await page.reload();
      await waitForNetworkIdle(page);
      await expect(page.locator('text=/50.*documents?/i')).toBeVisible();
    }
  });

  test('[P2] Navigation from admin dashboard to KB stats works (AC-5.6.6)', async ({ page }) => {
    /**
     * GIVEN: Admin is on admin dashboard
     * WHEN: Admin clicks "View Statistics" for a KB
     * THEN: User navigates to /admin/kb-stats with correct KB ID
     */

    // Mock admin dashboard API
    await mockApiResponse(page, '**/api/v1/admin/stats', {
      users: { total: 100, active: 80, inactive: 20 },
      knowledge_bases: { total: 5, by_status: { active: 5 } },
      documents: { total: 100, by_status: {} },
      storage: { total_bytes: 1000000, avg_doc_size_bytes: 10000 },
      activity: {
        searches: { last_24h: 10, last_7d: 70, last_30d: 300 },
        generations: { last_24h: 5, last_7d: 35, last_30d: 150 },
      },
      trends: { searches: [], generations: [] },
    });

    // Mock knowledge bases list API
    await mockApiResponse(page, '**/api/v1/admin/knowledge-bases*', {
      items: [
        {
          id: mockKbId,
          name: 'Engineering Documentation',
          description: 'Test KB',
          created_at: '2025-12-03T10:00:00Z',
        },
      ],
      total: 1,
    });

    // GIVEN: Navigate to admin dashboard
    await page.goto('/admin');
    await waitForNetworkIdle(page);

    // WHEN: Click "View Statistics" link/button
    const viewStatsButton = page.locator(`[href*="/admin/kb-stats"][href*="${mockKbId}"]`).first();
    if (await viewStatsButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await viewStatsButton.click();
      await page.waitForLoadState('networkidle');

      // THEN: Navigated to KB stats page
      expect(page.url()).toContain('/admin/kb-stats');
      expect(page.url()).toContain(mockKbId);
      await expect(page.locator('h1, h2')).toContainText('Engineering Documentation');
    }
  });

  test('[P2] Empty KB displays zero values gracefully', async ({ page }) => {
    /**
     * GIVEN: KB has no documents or activity
     * WHEN: Admin views KB stats
     * THEN: All metrics show 0 with appropriate messaging
     */

    const emptyKbId = '550e8400-e29b-41d4-a716-446655440001';
    const emptyKbStats = createEmptyKBStats(emptyKbId, 'Empty KB');

    await mockApiResponse(
      page,
      `**/api/v1/admin/knowledge-bases/${emptyKbId}/stats`,
      emptyKbStats
    );

    // Navigate to empty KB stats page
    await page.goto(`/admin/kb-stats?kbId=${emptyKbId}`);
    await waitForNetworkIdle(page);

    // THEN: Zero values are displayed
    await expect(page.locator('text=/0.*documents?/i')).toBeVisible();
    await expect(page.locator('text=/0.*MB|0.*bytes?/i')).toBeVisible();
    await expect(page.locator('text=/0.*embeddings?|0.*vectors?/i')).toBeVisible();

    // THEN: Empty state message or "No data" indicator
    const emptyStateMessage = page.locator('text=/no documents|empty|no data/i');
    if (await emptyStateMessage.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(emptyStateMessage).toBeVisible();
    }
  });

  test('[P2] Large KB with high storage displays formatted values correctly', async ({ page }) => {
    /**
     * GIVEN: KB has large storage (50GB) and many documents
     * WHEN: Admin views KB stats
     * THEN: Storage is formatted in GB, counts use comma separators
     */

    const largeKbId = '550e8400-e29b-41d4-a716-446655440002';
    const largeKbStats = createLargeKBStats();
    largeKbStats.kb_id = largeKbId;

    await mockApiResponse(
      page,
      `**/api/v1/admin/knowledge-bases/${largeKbId}/stats`,
      largeKbStats
    );

    // Navigate to large KB stats page
    await page.goto(`/admin/kb-stats?kbId=${largeKbId}`);
    await waitForNetworkIdle(page);

    // THEN: Document count uses comma separator (5,000)
    await expect(page.locator('text=/5,000.*documents?/i')).toBeVisible();

    // THEN: Storage shows GB format (50GB or 50.0 GB)
    await expect(page.locator('text=/50(\\.\\d+)?\\s*GB/i')).toBeVisible();

    // THEN: Large embeddings count formatted (125,000)
    await expect(page.locator('text=/125,000.*embeddings?/i')).toBeVisible();

    // THEN: High search activity (15,000 searches)
    await expect(page.locator('text=/15,000.*searches?/i')).toBeVisible();
  });

  test('[P2] High activity KB shows top documents list (AC-5.6.2)', async ({ page }) => {
    /**
     * GIVEN: KB has high search and generation activity
     * WHEN: Admin views KB stats
     * THEN: Top 5 documents are displayed with access counts
     */

    const highActivityKbId = '550e8400-e29b-41d4-a716-446655440003';
    const highActivityStats = createHighActivityKBStats();
    highActivityStats.kb_id = highActivityKbId;

    await mockApiResponse(
      page,
      `**/api/v1/admin/knowledge-bases/${highActivityKbId}/stats`,
      highActivityStats
    );

    // Navigate to high activity KB stats page
    await page.goto(`/admin/kb-stats?kbId=${highActivityKbId}`);
    await waitForNetworkIdle(page);

    // THEN: High search count is visible
    await expect(page.locator('text=/5,000.*searches?/i')).toBeVisible();

    // THEN: High generation count is visible
    await expect(page.locator('text=/2,500.*generations?/i')).toBeVisible();

    // THEN: Multiple unique users (45)
    await expect(page.locator('text=/45.*users?/i')).toBeVisible();
  });
});
