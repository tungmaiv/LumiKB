import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Page object for Queue Status Dashboard (/admin/queue)
 * Story 5-4: Processing Queue Status
 */
export class QueuePage extends BasePage {
  // Page elements
  readonly refreshButton: Locator;
  readonly lastUpdatedText: Locator;
  readonly errorMessage: Locator;
  readonly retryButton: Locator;

  constructor(page: Page) {
    super(page);
    this.refreshButton = page.getByRole('button', { name: /refresh/i });
    this.lastUpdatedText = page.getByText(/last updated:/i);
    this.errorMessage = page.getByText(/unable to connect to task queue/i);
    this.retryButton = page.getByRole('button', { name: /retry|refresh queue status/i });
  }

  /**
   * Navigate to queue status page
   */
  async goto() {
    await this.page.goto('/admin/queue');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get queue card by queue name
   */
  getQueueCard(queueName: string): Locator {
    return this.page.locator(`[data-testid="queue-card-${queueName}"]`);
  }

  /**
   * Get "View Active Tasks" button for a queue
   */
  getViewActiveTasksButton(queueName: string): Locator {
    return this.getQueueCard(queueName).getByRole('button', {
      name: /view active tasks/i,
    });
  }

  /**
   * Get "View Pending Tasks" button for a queue
   */
  getViewPendingTasksButton(queueName: string): Locator {
    return this.getQueueCard(queueName).getByRole('button', {
      name: /view pending tasks/i,
    });
  }

  /**
   * Check if warning badge is displayed for a queue
   */
  async hasWarningBadge(queueName: string, warningText: string): Promise<boolean> {
    const badge = this.getQueueCard(queueName).getByText(warningText);
    return badge.isVisible();
  }

  /**
   * Get pending tasks count for a queue
   */
  async getPendingTasksCount(queueName: string): Promise<number> {
    const text = await this.getQueueCard(queueName)
      .locator('[data-testid="pending-tasks"]')
      .textContent();
    return parseInt(text || '0', 10);
  }

  /**
   * Get active tasks count for a queue
   */
  async getActiveTasksCount(queueName: string): Promise<number> {
    const text = await this.getQueueCard(queueName)
      .locator('[data-testid="active-tasks"]')
      .textContent();
    return parseInt(text || '0', 10);
  }

  /**
   * Get workers online count for a queue
   */
  async getWorkersOnlineCount(queueName: string): Promise<number> {
    const text = await this.getQueueCard(queueName)
      .locator('[data-testid="workers-online"]')
      .textContent();
    return parseInt(text || '0', 10);
  }

  /**
   * Click refresh button and wait for data to update
   */
  async clickRefresh() {
    await this.refreshButton.click();
    await this.page.waitForResponse((response) =>
      response.url().includes('/api/v1/admin/queue/status')
    );
  }

  /**
   * Wait for auto-refresh (10 seconds)
   */
  async waitForAutoRefresh() {
    await this.page.waitForTimeout(10500); // 10s + buffer
    await this.page.waitForResponse((response) =>
      response.url().includes('/api/v1/admin/queue/status')
    );
  }

  /**
   * Check if task list modal is visible
   */
  async isTaskListModalVisible(): Promise<boolean> {
    const modal = this.page.getByRole('dialog');
    return modal.isVisible();
  }

  /**
   * Get task count from modal
   */
  async getTaskCountFromModal(): Promise<number> {
    const rows = this.page.locator('[data-testid="task-row"]');
    return rows.count();
  }

  /**
   * Get task table headers from modal
   */
  getTaskTableHeaders(): Locator {
    return this.page.locator('thead th');
  }

  /**
   * Close task list modal
   */
  async closeTaskListModal() {
    const closeButton = this.page.getByRole('button', { name: /close/i });
    await closeButton.click();
    await this.page.waitForTimeout(300); // Wait for modal animation
  }

  /**
   * Sort task table by column (click header)
   */
  async sortTaskTableByColumn(columnName: string) {
    const header = this.page.getByRole('columnheader', { name: columnName });
    await header.click();
    await this.page.waitForTimeout(200); // Wait for sort animation
  }

  /**
   * Get queue status badge text (available/unavailable)
   */
  async getQueueStatusBadge(queueName: string): Promise<string> {
    const badge = this.getQueueCard(queueName).locator('[data-testid="queue-status-badge"]');
    return (await badge.textContent()) || '';
  }
}
