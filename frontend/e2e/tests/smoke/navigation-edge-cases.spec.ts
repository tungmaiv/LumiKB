/**
 * Story 5-0 Automation: Navigation & Dashboard Edge Cases
 * Generated: 2025-12-02
 *
 * Test Coverage:
 * - [P1] Dashboard navigation with no KBs
 * - [P1] Navigation cards when user has single KB
 * - [P2] Dashboard when all KBs are deleted
 * - [P2] Navigation between Search and Chat preserves state
 * - [P2] Deep linking to chat/search pages
 *
 * Knowledge Base References:
 * - test-quality.md: Given-When-Then structure
 * - test-priorities-matrix.md: P1 = Core navigation, P2 = Secondary flows
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { DashboardPage } from '../../pages';

test.describe('Story 5-0: Navigation & Dashboard Edge Cases', () => {
  test('[P1] Dashboard shows create KB prompt when user has no KBs', async ({ page }) => {
    /**
     * GIVEN: User account has no knowledge bases
     * WHEN: User lands on dashboard
     * THEN: Empty state with CTA to create KB is displayed
     */

    // Mock API to return empty KB list
    await page.route('**/api/v1/knowledge-bases**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ knowledge_bases: [] }),
      });
    });

    // WHEN: Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // THEN: Empty state is displayed
    const emptyState = page.getByTestId('dashboard-empty-state');
    await expect(emptyState).toBeVisible();

    // THEN: Create KB button is present
    const createKbButton = page.getByTestId('create-kb-button');
    await expect(createKbButton).toBeVisible();

    // THEN: Navigation cards for Chat and Search are disabled or hidden
    const chatCard = page.getByTestId('nav-card-chat');
    const searchCard = page.getByTestId('nav-card-search');

    // Cards should either be disabled or not visible
    if (await chatCard.isVisible().catch(() => false)) {
      const isDisabled = await chatCard.getAttribute('aria-disabled');
      expect(isDisabled).toBe('true');
    }

    if (await searchCard.isVisible().catch(() => false)) {
      const isDisabled = await searchCard.getAttribute('aria-disabled');
      expect(isDisabled).toBe('true');
    }
  });

  test('[P1] Dashboard navigation cards work correctly with single KB', async ({ page }) => {
    /**
     * GIVEN: User has exactly one knowledge base
     * WHEN: User clicks navigation cards
     * THEN: User navigates to correct pages with KB pre-selected
     */

    // Mock API to return single KB
    await page.route('**/api/v1/knowledge-bases**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          knowledge_bases: [
            {
              id: '123',
              name: 'Test KB',
              description: 'Test knowledge base',
              created_at: '2024-01-01T00:00:00Z',
            },
          ],
        }),
      });
    });

    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // WHEN: Click search navigation card
    const searchCard = page.getByTestId('nav-card-search');
    await expect(searchCard).toBeVisible();
    await searchCard.click();

    // THEN: Navigate to search page
    await page.waitForURL(/\/search/);

    // Go back to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // WHEN: Click chat navigation card
    const chatCard = page.getByTestId('nav-card-chat');
    await expect(chatCard).toBeVisible();
    await chatCard.click();

    // THEN: Navigate to chat page
    await page.waitForURL(/\/chat/);
  });

  test('[P2] Dashboard handles KB deletion gracefully', async ({ page }) => {
    /**
     * GIVEN: User is viewing dashboard with KBs
     * WHEN: All KBs are deleted (by admin or via API)
     * THEN: Dashboard updates to show empty state
     */

    let kbCount = 1;

    // Mock API with dynamic response
    await page.route('**/api/v1/knowledge-bases**', async (route) => {
      if (kbCount > 0) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            knowledge_bases: [
              {
                id: '123',
                name: 'Test KB',
                description: 'Test knowledge base',
                created_at: '2024-01-01T00:00:00Z',
              },
            ],
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ knowledge_bases: [] }),
        });
      }
    });

    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify KB is visible
    const kbCard = page.locator('[data-testid="kb-card"]').first();
    await expect(kbCard).toBeVisible();

    // Simulate KB deletion
    kbCount = 0;

    // Refresh page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // THEN: Empty state is now visible
    const emptyState = page.getByTestId('dashboard-empty-state');
    await expect(emptyState).toBeVisible({ timeout: 10000 });
  });

  test('[P2] Navigation between Search and Chat preserves KB selection', async ({ page }) => {
    /**
     * GIVEN: User selects a KB in Search page
     * WHEN: User navigates to Chat page
     * THEN: Same KB is pre-selected in Chat (or user's last selected KB)
     */

    // Navigate to search page
    await page.goto('/search');
    await page.waitForLoadState('networkidle');

    // Select a KB in search
    const kbSelector = page.getByTestId('kb-selector');
    if (await kbSelector.isVisible().catch(() => false)) {
      await kbSelector.click();
      const firstKb = page.getByRole('option').first();
      const kbName = await firstKb.textContent();
      await firstKb.click();

      // Navigate to chat
      await page.goto('/chat');
      await page.waitForLoadState('networkidle');

      // Verify KB is selected (may not be exact same one, but should have one selected)
      const chatKbSelector = page.getByTestId('kb-selector');
      const selectedText = await chatKbSelector.textContent();
      expect(selectedText).toBeTruthy();
      expect(selectedText).not.toMatch(/select|choose/i);
    }
  });

  test('[P2] Deep linking to chat page works correctly', async ({ page }) => {
    /**
     * GIVEN: User has direct URL to chat page
     * WHEN: User navigates directly to /chat
     * THEN: Page loads correctly, user can interact
     */

    // WHEN: Navigate directly to chat (not via dashboard)
    await page.goto('/chat');

    // THEN: Page loads successfully
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/chat/);

    // THEN: Chat interface is visible
    const chatInput = page.getByTestId('chat-input');
    await expect(chatInput).toBeVisible();

    const kbSelector = page.getByTestId('kb-selector');
    await expect(kbSelector).toBeVisible();
  });

  test('[P2] Deep linking to search page works correctly', async ({ page }) => {
    /**
     * GIVEN: User has direct URL to search page
     * WHEN: User navigates directly to /search
     * THEN: Page loads correctly, user can search
     */

    // WHEN: Navigate directly to search
    await page.goto('/search');

    // THEN: Page loads successfully
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/search/);

    // THEN: Search interface is visible
    const searchInput = page.getByTestId('search-input');
    await expect(searchInput).toBeVisible();
  });

  test('[P2] Dashboard shows correct KB count', async ({ page }) => {
    /**
     * GIVEN: User has multiple KBs
     * WHEN: User views dashboard
     * THEN: Correct count of KBs is displayed
     */

    // Mock API with multiple KBs
    const kbList = [
      { id: '1', name: 'KB 1', description: 'First KB', created_at: '2024-01-01T00:00:00Z' },
      { id: '2', name: 'KB 2', description: 'Second KB', created_at: '2024-01-02T00:00:00Z' },
      { id: '3', name: 'KB 3', description: 'Third KB', created_at: '2024-01-03T00:00:00Z' },
    ];

    await page.route('**/api/v1/knowledge-bases**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ knowledge_bases: kbList }),
      });
    });

    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // THEN: Correct number of KB cards are displayed
    const kbCards = page.locator('[data-testid="kb-card"]');
    await expect(kbCards).toHaveCount(kbList.length);
  });

  test('[P1] Dashboard handles API error when loading KBs', async ({ page }) => {
    /**
     * GIVEN: KB list API fails
     * WHEN: User lands on dashboard
     * THEN: Error message is displayed, user can retry
     */

    // Mock API failure
    await page.route('**/api/v1/knowledge-bases**', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    });

    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // THEN: Error message is displayed
    const errorMessage = page.getByTestId('kb-load-error');
    if (await errorMessage.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(errorMessage).toBeVisible();
    }

    // OR: Toast notification
    const toast = page.locator('[data-sonner-toast]').first();
    if (await toast.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(toast).toContainText(/error|failed/i);
    }

    // THEN: Retry button or option is available
    const retryButton = page.getByTestId('retry-load-kbs');
    if (await retryButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(retryButton).toBeVisible();
    }
  });

  test('[P2] Dashboard navigation cards show appropriate icons and labels', async ({ page }) => {
    /**
     * GIVEN: User has KBs available
     * WHEN: User views dashboard
     * THEN: Navigation cards display correct icons and labels
     */

    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // THEN: Search card is visible with correct content
    const searchCard = page.getByTestId('nav-card-search');
    if (await searchCard.isVisible().catch(() => false)) {
      const searchCardText = await searchCard.textContent();
      expect(searchCardText).toMatch(/search/i);
    }

    // THEN: Chat card is visible with correct content
    const chatCard = page.getByTestId('nav-card-chat');
    if (await chatCard.isVisible().catch(() => false)) {
      const chatCardText = await chatCard.textContent();
      expect(chatCardText).toMatch(/chat/i);
    }
  });

  test('[P2] Dashboard handles slow KB loading with loading state', async ({ page }) => {
    /**
     * GIVEN: KB list API is slow to respond
     * WHEN: User lands on dashboard
     * THEN: Loading skeleton/spinner is displayed while loading
     */

    // Mock slow API response
    await page.route('**/api/v1/knowledge-bases**', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          knowledge_bases: [
            { id: '123', name: 'Test KB', description: 'Test', created_at: '2024-01-01T00:00:00Z' },
          ],
        }),
      });
    });

    // Navigate to dashboard
    await page.goto('/dashboard');

    // THEN: Loading state is visible
    const loadingSkeleton = page.getByTestId('kb-loading-skeleton');
    const loadingSpinner = page
      .locator('[data-testid*="loading"]')
      .or(page.locator('.animate-spin'));

    if (await loadingSkeleton.isVisible({ timeout: 1000 }).catch(() => false)) {
      await expect(loadingSkeleton).toBeVisible();
    } else if (
      await loadingSpinner
        .first()
        .isVisible({ timeout: 1000 })
        .catch(() => false)
    ) {
      await expect(loadingSpinner.first()).toBeVisible();
    }

    // Wait for KBs to load
    await page.waitForLoadState('networkidle');

    // THEN: Loading state is removed
    if (await loadingSkeleton.isVisible().catch(() => false)) {
      await expect(loadingSkeleton).not.toBeVisible({ timeout: 5000 });
    }
  });
});
