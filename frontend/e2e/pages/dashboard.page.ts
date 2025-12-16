import { Page, expect } from '@playwright/test';
import { BasePage } from './base.page';
import { LoginPage } from './login.page';

export class DashboardPage extends BasePage {
  private loginPage: LoginPage;

  // Locators
  readonly welcomeMessage = this.page.getByRole('heading', {
    name: /welcome|dashboard/i,
  });
  readonly searchInput = this.page.getByPlaceholder(/search/i);
  readonly uploadButton = this.page.getByRole('button', { name: /upload/i });
  readonly userMenu = this.page.getByTestId('user-menu');
  readonly sidebar = this.page.getByTestId('sidebar');

  constructor(page: Page) {
    super(page);
    this.loginPage = new LoginPage(page);
  }

  /**
   * Login as a regular user
   */
  async loginAsUser() {
    await this.loginPage.goto();
    const userEmail = process.env.USER_EMAIL || 'user@example.com';
    const userPassword = process.env.USER_PASSWORD || 'userpassword';
    await this.loginPage.login(userEmail, userPassword);
  }

  async goto() {
    await super.goto('/dashboard');
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
  }

  async openUserMenu() {
    await this.userMenu.click();
  }

  async logout() {
    await this.openUserMenu();
    await this.page.getByRole('menuitem', { name: /logout|sign out/i }).click();
  }

  async expectDashboardVisible() {
    await expect(this.page).toHaveURL(/.*dashboard/);
  }

  async navigateTo(section: 'documents' | 'settings' | 'profile') {
    const linkName = {
      documents: /documents/i,
      settings: /settings/i,
      profile: /profile/i,
    };
    await this.page.getByRole('link', { name: linkName[section] }).click();
  }

  // ============================================================
  // Story 5-24: KB Dashboard Filtering & Pagination Methods
  // ============================================================

  /**
   * Navigate to KB dashboard with specific knowledge base
   */
  async gotoWithKB(kbId: string) {
    await super.goto(`/dashboard?kb=${kbId}`);
  }

  /**
   * Search documents by name
   */
  async searchDocuments(query: string) {
    const searchInput = this.page.getByPlaceholder(/search documents/i);
    await searchInput.fill(query);
    // Wait for debounce
    await this.page.waitForTimeout(400);
  }

  /**
   * Filter documents by file type
   */
  async filterByType(type: 'pdf' | 'docx' | 'txt' | 'md' | 'all') {
    const typeDropdown = this.page.getByRole('combobox', { name: /type/i });
    await typeDropdown.click();
    await this.page.getByRole('option', { name: new RegExp(type, 'i') }).click();
  }

  /**
   * Filter documents by processing status
   */
  async filterByStatus(status: 'processed' | 'processing' | 'failed' | 'pending' | 'all') {
    const statusDropdown = this.page.getByRole('combobox', { name: /status/i });
    await statusDropdown.click();
    await this.page.getByRole('option', { name: new RegExp(status, 'i') }).click();
  }

  /**
   * Filter documents by tags (multi-select)
   */
  async filterByTags(tags: string[]) {
    const tagSelect = this.page.locator('[data-testid="tag-filter"]');
    await tagSelect.click();
    for (const tag of tags) {
      await this.page.getByRole('option', { name: tag }).click();
    }
    // Close dropdown by clicking outside
    await this.page.keyboard.press('Escape');
  }

  /**
   * Filter documents by date range
   */
  async filterByDateRange(startDate: string, endDate: string) {
    const datePicker = this.page.locator('[data-testid="date-range-picker"]');
    await datePicker.click();

    // Fill start date
    const startInput = this.page.getByLabel(/start date/i);
    await startInput.fill(startDate);

    // Fill end date
    const endInput = this.page.getByLabel(/end date/i);
    await endInput.fill(endDate);

    // Apply date range
    await this.page.getByRole('button', { name: /apply/i }).click();
  }

  /**
   * Clear all active filters
   */
  async clearFilters() {
    await this.page.getByRole('button', { name: /clear filters/i }).click();
  }

  /**
   * Check if filter bar is visible
   */
  async isFilterBarVisible(): Promise<boolean> {
    const filterBar = this.page.locator('[data-testid="document-filter-bar"]');
    return await filterBar.isVisible();
  }

  /**
   * Get current active filters from URL
   */
  async getActiveFilters(): Promise<{
    search?: string;
    type?: string;
    status?: string;
    tags?: string[];
    startDate?: string;
    endDate?: string;
    page?: number;
  }> {
    const url = new URL(this.page.url());
    return {
      search: url.searchParams.get('search') || undefined,
      type: url.searchParams.get('type') || undefined,
      status: url.searchParams.get('status') || undefined,
      tags: url.searchParams.getAll('tags'),
      startDate: url.searchParams.get('startDate') || undefined,
      endDate: url.searchParams.get('endDate') || undefined,
      page: url.searchParams.get('page') ? Number(url.searchParams.get('page')) : undefined,
    };
  }

  // ============================================================
  // Pagination Methods
  // ============================================================

  /**
   * Go to next page
   */
  async goToNextPage() {
    await this.page.getByRole('button', { name: /next/i }).click();
  }

  /**
   * Go to previous page
   */
  async goToPreviousPage() {
    await this.page.getByRole('button', { name: /previous/i }).click();
  }

  /**
   * Change page size
   */
  async setPageSize(size: 25 | 50 | 100) {
    const pageSizeSelect = this.page.locator('[data-testid="page-size-select"]');
    await pageSizeSelect.click();
    await this.page.getByRole('option', { name: String(size) }).click();
  }

  /**
   * Get current pagination state
   */
  async getPaginationInfo(): Promise<{
    currentPage: number;
    totalPages: number;
    totalDocuments: number;
    pageSize: number;
  }> {
    // Parse "Page X of Y"
    const pageText = await this.page.locator('[data-testid="pagination-info"]').textContent();
    const pageMatch = pageText?.match(/Page (\d+) of (\d+)/i);

    // Parse "N documents"
    const totalText = await this.page.locator('[data-testid="total-documents"]').textContent();
    const totalMatch = totalText?.match(/(\d+) documents?/i);

    // Get page size from select
    const pageSizeText = await this.page.locator('[data-testid="page-size-select"]').textContent();
    const pageSizeMatch = pageSizeText?.match(/(\d+)/);

    return {
      currentPage: pageMatch ? parseInt(pageMatch[1]) : 1,
      totalPages: pageMatch ? parseInt(pageMatch[2]) : 1,
      totalDocuments: totalMatch ? parseInt(totalMatch[1]) : 0,
      pageSize: pageSizeMatch ? parseInt(pageSizeMatch[1]) : 50,
    };
  }

  /**
   * Check if next page button is enabled
   */
  async isNextPageEnabled(): Promise<boolean> {
    const nextButton = this.page.getByRole('button', { name: /next/i });
    return await nextButton.isEnabled();
  }

  /**
   * Check if previous page button is enabled
   */
  async isPreviousPageEnabled(): Promise<boolean> {
    const prevButton = this.page.getByRole('button', { name: /previous/i });
    return await prevButton.isEnabled();
  }

  /**
   * Get visible document rows count
   */
  async getDocumentRowCount(): Promise<number> {
    const rows = this.page.locator('[data-testid="document-row"]');
    return await rows.count();
  }

  /**
   * Get list of visible document names
   */
  async getDocumentNames(): Promise<string[]> {
    const nameElements = this.page.locator('[data-testid="document-name"]');
    const count = await nameElements.count();
    const names: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await nameElements.nth(i).textContent();
      if (text) names.push(text.trim());
    }
    return names;
  }

  /**
   * Check if empty state message is visible
   */
  async isEmptyStateVisible(): Promise<boolean> {
    const emptyState = this.page.locator('[data-testid="empty-document-list"]');
    return await emptyState.isVisible();
  }

  /**
   * Check if loading indicator is visible
   */
  async isLoadingVisible(): Promise<boolean> {
    const loading = this.page.locator('[data-testid="document-list-loading"]');
    return await loading.isVisible();
  }
}
