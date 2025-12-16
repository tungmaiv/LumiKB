import { Page } from '@playwright/test';
import { BasePage } from './base.page';
import { LoginPage } from './login.page';

/**
 * Page object for Admin Dashboard and Admin tools
 */
export class AdminPage extends BasePage {
  private loginPage: LoginPage;

  constructor(page: Page) {
    super(page);
    this.loginPage = new LoginPage(page);
  }

  /**
   * Login as admin user (superuser)
   */
  async loginAsAdmin() {
    await this.loginPage.goto();
    // Use environment variable or default admin credentials
    const adminEmail = process.env.ADMIN_EMAIL || 'admin@example.com';
    const adminPassword = process.env.ADMIN_PASSWORD || 'adminpassword';
    await this.loginPage.login(adminEmail, adminPassword);
  }

  /**
   * Login as regular (non-admin) user
   */
  async loginAsRegularUser() {
    await this.loginPage.goto();
    const userEmail = process.env.USER_EMAIL || 'user@example.com';
    const userPassword = process.env.USER_PASSWORD || 'userpassword';
    await this.loginPage.login(userEmail, userPassword);
  }

  /**
   * Navigate to admin dashboard
   */
  async gotoAdminDashboard() {
    await this.goto('/admin');
  }

  /**
   * Navigate to audit log viewer
   */
  async gotoAuditLogs() {
    await this.goto('/admin/audit');
  }

  /**
   * Navigate to system configuration page
   */
  async gotoSystemConfig() {
    await this.goto('/admin/config');
  }

  /**
   * Seed audit events (mock data for testing)
   * This is a placeholder - in real tests you'd hit backend API or use fixtures
   */
  async seedAuditEvents(events: Array<{ event_type: string; count: number }>) {
    // Placeholder for seeding test data
    // In real implementation, this would call backend API to create audit events
    console.warn('seedAuditEvents is a placeholder - implement with real backend calls');
  }

  // ============================================================
  // Story 5-22: Document Tags Management Methods
  // ============================================================

  /**
   * Navigate to a specific KB's dashboard to access document tags
   */
  async gotoKBDashboard(kbId: string) {
    await this.goto(`/dashboard?kb=${kbId}`);
  }

  /**
   * Open the document tags edit modal for a specific document
   */
  async openDocumentTagsModal(documentName: string) {
    const documentRow = this.page.getByRole('row').filter({ hasText: documentName });
    await documentRow.getByRole('button', { name: /edit tags/i }).click();
    await this.page.getByRole('dialog').waitFor({ state: 'visible' });
  }

  /**
   * Add a tag to the current document tags modal
   */
  async addDocumentTag(tagName: string) {
    const tagInput = this.page.getByPlaceholder(/add tag|enter tag/i);
    await tagInput.fill(tagName);
    await tagInput.press('Enter');
  }

  /**
   * Remove a tag from the current document tags modal
   */
  async removeDocumentTag(tagName: string) {
    const tagBadge = this.page.locator('[data-testid="tag-badge"]').filter({ hasText: tagName });
    await tagBadge.getByRole('button', { name: /remove|×/i }).click();
  }

  /**
   * Save document tags and close modal
   */
  async saveDocumentTags() {
    await this.page.getByRole('button', { name: /save/i }).click();
    await this.page.getByRole('dialog').waitFor({ state: 'hidden' });
  }

  /**
   * Get all visible document tags for a specific document row
   */
  async getDocumentTags(documentName: string): Promise<string[]> {
    const documentRow = this.page.getByRole('row').filter({ hasText: documentName });
    const tagBadges = documentRow.locator('[data-testid="document-tag"]');
    const count = await tagBadges.count();
    const tags: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await tagBadges.nth(i).textContent();
      if (text) tags.push(text.trim());
    }
    return tags;
  }

  /**
   * Check if document has "+N more" tags indicator
   */
  async hasMoreTagsIndicator(documentName: string): Promise<boolean> {
    const documentRow = this.page.getByRole('row').filter({ hasText: documentName });
    const moreIndicator = documentRow.locator('[data-testid="more-tags"]');
    return await moreIndicator.isVisible();
  }

  /**
   * Verify edit tags button visibility (should be hidden for READ-only users)
   */
  async isEditTagsButtonVisible(documentName: string): Promise<boolean> {
    const documentRow = this.page.getByRole('row').filter({ hasText: documentName });
    const editButton = documentRow.getByRole('button', { name: /edit tags/i });
    return await editButton.isVisible();
  }

  // ============================================================
  // Story 5-23: Document Processing Progress Methods
  // ============================================================

  /**
   * Navigate to the Processing tab for a specific KB
   */
  async gotoProcessingTab(kbId: string) {
    await this.goto(`/dashboard?kb=${kbId}&tab=processing`);
  }

  /**
   * Check if Processing tab is visible (requires ADMIN/WRITE permission)
   */
  async isProcessingTabVisible(): Promise<boolean> {
    const processingTab = this.page.getByRole('tab', { name: /processing/i });
    return await processingTab.isVisible();
  }

  /**
   * Click on the Processing tab
   */
  async clickProcessingTab() {
    await this.page.getByRole('tab', { name: /processing/i }).click();
  }

  /**
   * Get processing status for a specific document
   */
  async getDocumentProcessingStatus(documentName: string): Promise<{
    status: string;
    currentStep: string;
    chunkCount: string;
  }> {
    const row = this.page.getByRole('row').filter({ hasText: documentName });
    const status = await row.locator('[data-testid="processing-status"]').textContent();
    const currentStep = await row.locator('[data-testid="current-step"]').textContent();
    const chunkCount = await row.locator('[data-testid="chunk-count"]').textContent();
    return {
      status: status?.trim() || '',
      currentStep: currentStep?.trim() || '',
      chunkCount: chunkCount?.trim() || '',
    };
  }

  /**
   * Open processing details modal for a document
   */
  async openProcessingDetailsModal(documentName: string) {
    const row = this.page.getByRole('row').filter({ hasText: documentName });
    await row.getByRole('button', { name: /view details/i }).click();
    await this.page.getByRole('dialog').waitFor({ state: 'visible' });
  }

  /**
   * Get step statuses from the processing details modal
   */
  async getProcessingStepStatuses(): Promise<Array<{ step: string; status: string; duration: string }>> {
    const steps = this.page.locator('[data-testid="processing-step"]');
    const count = await steps.count();
    const statuses: Array<{ step: string; status: string; duration: string }> = [];

    for (let i = 0; i < count; i++) {
      const stepEl = steps.nth(i);
      const step = await stepEl.locator('[data-testid="step-name"]').textContent();
      const status = await stepEl.locator('[data-testid="step-status"]').textContent();
      const duration = await stepEl.locator('[data-testid="step-duration"]').textContent();
      statuses.push({
        step: step?.trim() || '',
        status: status?.trim() || '',
        duration: duration?.trim() || '',
      });
    }
    return statuses;
  }

  /**
   * Apply processing filter by status
   */
  async filterProcessingByStatus(status: 'pending' | 'processing' | 'ready' | 'failed' | 'all') {
    const statusDropdown = this.page.getByRole('combobox', { name: /status/i });
    await statusDropdown.click();
    await this.page.getByRole('option', { name: new RegExp(status, 'i') }).click();
  }

  /**
   * Apply processing filter by current step
   */
  async filterProcessingByStep(step: 'upload' | 'parse' | 'chunk' | 'embed' | 'index' | 'complete' | 'all') {
    const stepDropdown = this.page.getByRole('combobox', { name: /step/i });
    await stepDropdown.click();
    await this.page.getByRole('option', { name: new RegExp(step, 'i') }).click();
  }

  /**
   * Search processing documents by name
   */
  async searchProcessingDocuments(query: string) {
    const searchInput = this.page.getByPlaceholder(/search.*document/i);
    await searchInput.fill(query);
    // Wait for debounce
    await this.page.waitForTimeout(400);
  }

  /**
   * Get "Last updated" timestamp from processing screen
   */
  async getLastUpdatedTimestamp(): Promise<string> {
    const timestamp = this.page.locator('[data-testid="last-updated"]');
    return (await timestamp.textContent())?.trim() || '';
  }

  /**
   * Click "Refresh Now" button
   */
  async clickRefreshNow() {
    await this.page.getByRole('button', { name: /refresh now/i }).click();
  }

  /**
   * Get processing step error message from modal
   */
  async getProcessingError(step: string): Promise<string | null> {
    const stepEl = this.page.locator('[data-testid="processing-step"]').filter({ hasText: step });
    const errorEl = stepEl.locator('[data-testid="step-error"]');
    if (await errorEl.isVisible()) {
      return (await errorEl.textContent())?.trim() || null;
    }
    return null;
  }

  // ============================================================
  // Story 5-24: KB Dashboard Filtering & Pagination Methods
  // (These extend the DashboardPage but are included here for admin context)
  // ============================================================

  /**
   * Navigate to user management page
   */
  async gotoUserManagement() {
    await this.goto('/admin/users');
  }

  /**
   * Navigate to group management page
   */
  async gotoGroupManagement() {
    await this.goto('/admin/groups');
  }

  /**
   * Navigate to KB permissions page
   */
  async gotoKBPermissions() {
    await this.goto('/admin/kb-permissions');
  }

  /**
   * Navigate to KB stats page
   */
  async gotoKBStats() {
    await this.goto('/admin/kb-stats');
  }

  // ============================================================
  // Story 7-2: LLM Configuration Methods
  // ============================================================

  /**
   * Navigate to LLM configuration page
   */
  async gotoLLMConfig() {
    await this.goto('/admin/config/llm');
  }

  /**
   * Get current temperature value from the LLM config form
   */
  async getTemperatureValue(): Promise<string> {
    const temperatureDisplay = this.page.locator('text=Temperature').locator('..').locator('span').last();
    return (await temperatureDisplay.textContent())?.trim() || '';
  }

  /**
   * Get current max tokens value from the LLM config form
   */
  async getMaxTokensValue(): Promise<string> {
    const maxTokensInput = this.page.getByRole('spinbutton');
    return await maxTokensInput.inputValue();
  }

  /**
   * Set max tokens value in the LLM config form
   */
  async setMaxTokens(value: string) {
    const maxTokensInput = this.page.getByRole('spinbutton');
    await maxTokensInput.fill(value);
  }

  /**
   * Apply LLM configuration changes
   */
  async applyLLMConfigChanges() {
    await this.page.getByRole('button', { name: /apply changes/i }).click();
  }

  /**
   * Reset LLM configuration form
   */
  async resetLLMConfigForm() {
    await this.page.getByRole('button', { name: /reset/i }).click();
  }

  /**
   * Check if Apply Changes button is enabled
   */
  async isApplyChangesEnabled(): Promise<boolean> {
    const button = this.page.getByRole('button', { name: /apply changes/i });
    return !(await button.isDisabled());
  }

  /**
   * Check if dimension mismatch dialog is visible
   */
  async isDimensionMismatchDialogVisible(): Promise<boolean> {
    const dialog = this.page.getByRole('alertdialog').or(this.page.locator('[role="dialog"]'));
    const hasDimensionText = await dialog.getByText(/dimension.*mismatch/i).isVisible().catch(() => false);
    return hasDimensionText;
  }

  /**
   * Confirm dimension mismatch warning
   */
  async confirmDimensionMismatch() {
    const dialog = this.page.getByRole('alertdialog').or(this.page.locator('[role="dialog"]'));
    await dialog.getByRole('button', { name: /continue|understand/i }).click();
  }

  /**
   * Cancel dimension mismatch warning
   */
  async cancelDimensionMismatch() {
    const dialog = this.page.getByRole('alertdialog').or(this.page.locator('[role="dialog"]'));
    await dialog.getByRole('button', { name: /cancel/i }).click();
  }

  /**
   * Refresh LLM config from server
   */
  async refreshLLMConfig() {
    const updateText = this.page.getByText(/Updated.*ago|Updated Never/);
    const refreshButton = updateText.locator('..').locator('button').first();
    await refreshButton.click();
  }

  /**
   * Get current embedding model name
   */
  async getCurrentEmbeddingModel(): Promise<string> {
    const embeddingInfo = this.page.getByText(/Current:.*\(/).first();
    const text = await embeddingInfo.textContent();
    const match = text?.match(/Current:\s*([^(]+)/);
    return match ? match[1].trim() : '';
  }

  /**
   * Get current generation model name
   */
  async getCurrentGenerationModel(): Promise<string> {
    const generationInfo = this.page.getByText(/Current:.*\(/).last();
    const text = await generationInfo.textContent();
    const match = text?.match(/Current:\s*([^(]+)/);
    return match ? match[1].trim() : '';
  }
}
