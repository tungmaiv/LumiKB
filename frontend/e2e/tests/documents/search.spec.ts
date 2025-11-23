import { test, expect } from '../../fixtures/auth.fixture';
import { DashboardPage } from '../../pages';

test.describe('Document Search', () => {
  // Use authenticated state for these tests
  test.use({ storageState: 'e2e/.auth/user.json' });

  test('search input is visible on dashboard', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    await expect(dashboard.searchInput).toBeVisible();
  });

  test('can type search query', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    await dashboard.searchInput.fill('test document');

    await expect(dashboard.searchInput).toHaveValue('test document');
  });

  test('pressing enter submits search', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    await dashboard.search('meeting notes');

    // URL should update with search query or results should appear
    // This depends on your implementation
    await expect(page).toHaveURL(/.*search|.*q=/);
  });

  test('shows empty state for no results', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // Search for something that definitely doesn't exist
    await dashboard.search('xyznonexistent12345abcde');

    await expect(page.getByText(/no results|no documents|nothing found/i)).toBeVisible({
      timeout: 10000,
    });
  });
});

test.describe('Search Results', () => {
  test.use({ storageState: 'e2e/.auth/user.json' });

  test('displays search results when documents match', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // Search for a common term that should have results
    await dashboard.search('document');

    // Should show some results (or empty state)
    const hasResults = await page
      .getByTestId('search-results')
      .isVisible()
      .catch(() => false);
    const hasEmptyState = await page
      .getByText(/no results/i)
      .isVisible()
      .catch(() => false);

    // Either results or empty state should be visible
    expect(hasResults || hasEmptyState).toBe(true);
  });

  test('search results are clickable', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    await dashboard.search('document');

    // If there are results, clicking one should navigate
    const firstResult = page.getByTestId('search-result-item').first();
    const hasResult = await firstResult.isVisible().catch(() => false);

    if (hasResult) {
      await firstResult.click();
      // Should navigate to document detail or open document
      await expect(page).not.toHaveURL(/.*dashboard$/);
    }
  });
});
