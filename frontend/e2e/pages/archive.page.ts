import { Page, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Page object for Document Archive Management (Epic 6)
 * Handles archive, restore, purge, clear failed, duplicate detection, and replace operations
 */
export class ArchivePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // ============================================================
  // Navigation
  // ============================================================

  /**
   * Navigate to archive management page for a KB
   */
  async gotoArchiveManagement(kbId: string) {
    await this.goto(`/dashboard?kb=${kbId}&view=archive`);
  }

  /**
   * Navigate to document list with archived filter
   */
  async gotoArchivedDocuments(kbId: string) {
    await this.goto(`/dashboard?kb=${kbId}&status=archived`);
  }

  // ============================================================
  // Archive View Layout
  // ============================================================

  /**
   * Check if archive management view is visible
   */
  async isArchiveViewVisible(): Promise<boolean> {
    const archiveView = this.page.locator('[data-testid="archive-management-view"]');
    return await archiveView.isVisible();
  }

  /**
   * Get archive statistics
   */
  async getArchiveStats(): Promise<{
    totalArchived: number;
    totalActive: number;
    totalFailed: number;
  }> {
    const statsText = await this.page.locator('[data-testid="archive-stats"]').textContent();
    const archivedMatch = statsText?.match(/(\d+)\s*archived/i);
    const activeMatch = statsText?.match(/(\d+)\s*active/i);
    const failedMatch = statsText?.match(/(\d+)\s*failed/i);

    return {
      totalArchived: archivedMatch ? parseInt(archivedMatch[1]) : 0,
      totalActive: activeMatch ? parseInt(activeMatch[1]) : 0,
      totalFailed: failedMatch ? parseInt(failedMatch[1]) : 0,
    };
  }

  // ============================================================
  // Document List Operations
  // ============================================================

  /**
   * Get visible documents in archive view
   */
  async getDocumentList(): Promise<
    Array<{
      id: string;
      name: string;
      status: string;
      archivedAt: string | null;
    }>
  > {
    const rows = this.page.locator('[data-testid="archive-document-row"]');
    const count = await rows.count();
    const documents: Array<{
      id: string;
      name: string;
      status: string;
      archivedAt: string | null;
    }> = [];

    for (let i = 0; i < count; i++) {
      const row = rows.nth(i);
      const id = (await row.getAttribute('data-document-id')) || '';
      const name = (await row.locator('[data-testid="document-name"]').textContent())?.trim() || '';
      const status =
        (await row.locator('[data-testid="document-status"]').textContent())?.trim() || '';
      const archivedAt = await row.locator('[data-testid="archived-at"]').textContent();

      documents.push({
        id,
        name,
        status,
        archivedAt: archivedAt?.trim() || null,
      });
    }
    return documents;
  }

  /**
   * Select a document by name
   */
  async selectDocument(documentName: string) {
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    await row.locator('[data-testid="document-checkbox"]').click();
  }

  /**
   * Select multiple documents
   */
  async selectDocuments(documentNames: string[]) {
    for (const name of documentNames) {
      await this.selectDocument(name);
    }
  }

  /**
   * Select all visible documents
   */
  async selectAllDocuments() {
    await this.page.getByRole('checkbox', { name: /select all/i }).click();
  }

  /**
   * Get selected document count
   */
  async getSelectedCount(): Promise<number> {
    const countText = await this.page.locator('[data-testid="selected-count"]').textContent();
    const match = countText?.match(/(\d+)/);
    return match ? parseInt(match[1]) : 0;
  }

  // ============================================================
  // Archive Operations (Story 6.1)
  // ============================================================

  /**
   * Archive a single document
   */
  async archiveDocument(documentName: string) {
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    await row.getByRole('button', { name: /archive/i }).click();
    await this.confirmAction();
  }

  /**
   * Archive selected documents (bulk)
   */
  async archiveSelected() {
    await this.page.getByRole('button', { name: /archive selected/i }).click();
    await this.confirmAction();
  }

  /**
   * Check if document can be archived
   */
  async canArchiveDocument(documentName: string): Promise<boolean> {
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    const archiveButton = row.getByRole('button', { name: /archive/i });
    return await archiveButton.isEnabled();
  }

  // ============================================================
  // Restore Operations (Story 6.2)
  // ============================================================

  /**
   * Restore a single document
   */
  async restoreDocument(documentName: string) {
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    await row.getByRole('button', { name: /restore/i }).click();
    await this.confirmAction();
  }

  /**
   * Restore selected documents (bulk)
   */
  async restoreSelected() {
    await this.page.getByRole('button', { name: /restore selected/i }).click();
    await this.confirmAction();
  }

  /**
   * Check if name collision warning is displayed during restore
   */
  async isNameCollisionWarningVisible(): Promise<boolean> {
    const warning = this.page.locator('[data-testid="name-collision-warning"]');
    return await warning.isVisible();
  }

  /**
   * Get name collision details
   */
  async getNameCollisionDetails(): Promise<{
    archivedDocumentName: string;
    existingDocumentName: string;
  }> {
    const warning = this.page.locator('[data-testid="name-collision-warning"]');
    const archived =
      (await warning.locator('[data-testid="archived-name"]').textContent())?.trim() || '';
    const existing =
      (await warning.locator('[data-testid="existing-name"]').textContent())?.trim() || '';

    return {
      archivedDocumentName: archived,
      existingDocumentName: existing,
    };
  }

  // ============================================================
  // Purge Operations (Story 6.3)
  // ============================================================

  /**
   * Purge (permanently delete) a document
   */
  async purgeDocument(documentName: string) {
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    await row.getByRole('button', { name: /purge|delete permanently/i }).click();
    await this.confirmDangerousAction();
  }

  /**
   * Purge selected documents (bulk)
   */
  async purgeSelected() {
    await this.page.getByRole('button', { name: /purge selected/i }).click();
    await this.confirmDangerousAction();
  }

  /**
   * Confirm dangerous action (purge requires extra confirmation)
   */
  async confirmDangerousAction() {
    const dialog = this.page.getByRole('dialog');
    await dialog.waitFor({ state: 'visible' });

    // Type confirmation text if required
    const confirmInput = dialog.getByPlaceholder(/type.*confirm|delete/i);
    if (await confirmInput.isVisible()) {
      await confirmInput.fill('DELETE');
    }

    await dialog.getByRole('button', { name: /confirm|delete/i }).click();
    await dialog.waitFor({ state: 'hidden' });
  }

  // ============================================================
  // Clear Failed Operations (Story 6.4)
  // ============================================================

  /**
   * Clear a failed document
   */
  async clearFailedDocument(documentName: string) {
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    await row.getByRole('button', { name: /clear|remove/i }).click();
    await this.confirmAction();
  }

  /**
   * Clear all failed documents
   */
  async clearAllFailed() {
    await this.page.getByRole('button', { name: /clear all failed/i }).click();
    await this.confirmAction();
  }

  /**
   * Get failed document error message
   */
  async getFailedDocumentError(documentName: string): Promise<string> {
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    const error = await row.locator('[data-testid="failure-reason"]').textContent();
    return error?.trim() || '';
  }

  // ============================================================
  // Duplicate Detection (Story 6.5)
  // ============================================================

  /**
   * Check if duplicate warning is displayed
   */
  async isDuplicateWarningVisible(): Promise<boolean> {
    const warning = this.page.locator('[data-testid="duplicate-warning"]');
    return await warning.isVisible();
  }

  /**
   * Get duplicate detection details
   */
  async getDuplicateDetails(): Promise<{
    newFileName: string;
    existingFileName: string;
    existingDocumentId: string;
  }> {
    const warning = this.page.locator('[data-testid="duplicate-warning"]');
    const newFile =
      (await warning.locator('[data-testid="new-filename"]').textContent())?.trim() || '';
    const existingFile =
      (await warning.locator('[data-testid="existing-filename"]').textContent())?.trim() || '';
    const existingId = (await warning.getAttribute('data-existing-document-id')) || '';

    return {
      newFileName: newFile,
      existingFileName: existingFile,
      existingDocumentId: existingId,
    };
  }

  /**
   * Choose to replace existing document when duplicate detected
   */
  async chooseReplaceOnDuplicate() {
    await this.page.getByRole('button', { name: /replace existing/i }).click();
    await this.confirmAction();
  }

  /**
   * Choose to skip upload when duplicate detected
   */
  async chooseSkipOnDuplicate() {
    await this.page.getByRole('button', { name: /skip|cancel/i }).click();
  }

  /**
   * Choose to keep both (rename) when duplicate detected
   */
  async chooseKeepBothOnDuplicate() {
    await this.page.getByRole('button', { name: /keep both|rename/i }).click();
  }

  // ============================================================
  // Replace Document Operations (Story 6.6)
  // ============================================================

  /**
   * Open replace document dialog
   */
  async openReplaceDialog(documentName: string) {
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    await row.getByRole('button', { name: /replace/i }).click();
    await this.page.getByRole('dialog').waitFor({ state: 'visible' });
  }

  /**
   * Upload replacement file
   */
  async uploadReplacementFile(filePath: string) {
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
  }

  /**
   * Confirm document replacement
   */
  async confirmReplacement() {
    await this.page.getByRole('button', { name: /confirm replacement|replace/i }).click();
    await this.waitForToast(/replaced|updated/i);
  }

  /**
   * Cancel document replacement
   */
  async cancelReplacement() {
    await this.page.getByRole('button', { name: /cancel/i }).click();
    await this.page.getByRole('dialog').waitFor({ state: 'hidden' });
  }

  // ============================================================
  // Common Actions
  // ============================================================

  /**
   * Confirm standard action dialog
   */
  async confirmAction() {
    const dialog = this.page.getByRole('dialog');
    await dialog.waitFor({ state: 'visible' });
    await dialog.getByRole('button', { name: /confirm|yes|ok/i }).click();
    await dialog.waitFor({ state: 'hidden' });
  }

  /**
   * Cancel action dialog
   */
  async cancelAction() {
    const dialog = this.page.getByRole('dialog');
    await dialog.waitFor({ state: 'visible' });
    await dialog.getByRole('button', { name: /cancel|no/i }).click();
    await dialog.waitFor({ state: 'hidden' });
  }

  // ============================================================
  // Filtering
  // ============================================================

  /**
   * Filter by document status
   */
  async filterByStatus(status: 'all' | 'active' | 'archived' | 'failed') {
    const statusDropdown = this.page.getByRole('combobox', { name: /status/i });
    await statusDropdown.click();
    await this.page.getByRole('option', { name: new RegExp(status, 'i') }).click();
  }

  /**
   * Search documents by name
   */
  async searchDocuments(query: string) {
    const searchInput = this.page.getByPlaceholder(/search/i);
    await searchInput.fill(query);
    await this.page.waitForTimeout(400); // debounce
  }

  /**
   * Clear all filters
   */
  async clearFilters() {
    await this.page.getByRole('button', { name: /clear filters/i }).click();
  }

  // ============================================================
  // Assertions
  // ============================================================

  /**
   * Assert document has specific status
   */
  async expectDocumentStatus(
    documentName: string,
    status: 'active' | 'archived' | 'failed' | 'processing'
  ) {
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    const statusBadge = row.locator('[data-testid="document-status"]');
    await expect(statusBadge).toHaveText(new RegExp(status, 'i'));
  }

  /**
   * Assert document is archived
   */
  async expectDocumentArchived(documentName: string) {
    await this.expectDocumentStatus(documentName, 'archived');
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    await expect(row.locator('[data-testid="archived-at"]')).toBeVisible();
  }

  /**
   * Assert document is restored (active)
   */
  async expectDocumentRestored(documentName: string) {
    await this.expectDocumentStatus(documentName, 'active');
  }

  /**
   * Assert document no longer exists (purged)
   */
  async expectDocumentPurged(documentName: string) {
    const row = this.page
      .locator('[data-testid="archive-document-row"]')
      .filter({ hasText: documentName });
    await expect(row).not.toBeVisible();
  }

  /**
   * Assert success toast for operation
   */
  async expectOperationSuccess(
    operation: 'archived' | 'restored' | 'purged' | 'cleared' | 'replaced'
  ) {
    await this.waitForToast(new RegExp(operation, 'i'));
  }

  /**
   * Assert error toast for operation
   */
  async expectOperationError(errorPattern: RegExp | string) {
    await this.waitForToast(errorPattern);
  }
}
