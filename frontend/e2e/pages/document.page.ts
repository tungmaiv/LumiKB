import { Page, expect } from '@playwright/test';
import { BasePage } from './base.page';

/**
 * Page object for Document Chunk Viewer (Stories 5.25, 5.26)
 * Handles chunk viewing, content streaming, and citation verification
 */
export class DocumentPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // ============================================================
  // Navigation
  // ============================================================

  /**
   * Navigate to document chunk viewer
   */
  async gotoChunkViewer(kbId: string, documentId: string) {
    await this.goto(`/dashboard?kb=${kbId}&document=${documentId}&view=chunks`);
  }

  /**
   * Navigate to document detail view
   */
  async gotoDocumentDetail(kbId: string, documentId: string) {
    await this.goto(`/dashboard?kb=${kbId}&document=${documentId}`);
  }

  // ============================================================
  // Chunk Viewer - Split Pane Layout
  // ============================================================

  /**
   * Check if split pane layout is visible
   */
  async isSplitPaneVisible(): Promise<boolean> {
    const splitPane = this.page.locator('[data-testid="chunk-viewer-split-pane"]');
    return await splitPane.isVisible();
  }

  /**
   * Get left pane (chunk list) element
   */
  getChunkListPane() {
    return this.page.locator('[data-testid="chunk-list-pane"]');
  }

  /**
   * Get right pane (document content) element
   */
  getDocumentContentPane() {
    return this.page.locator('[data-testid="document-content-pane"]');
  }

  /**
   * Resize split pane by dragging divider
   */
  async resizeSplitPane(deltaX: number) {
    const divider = this.page.locator('[data-testid="split-pane-divider"]');
    await divider.dragTo(divider, { targetPosition: { x: deltaX, y: 0 } });
  }

  // ============================================================
  // Chunk List Operations
  // ============================================================

  /**
   * Get all visible chunks
   */
  async getChunks(): Promise<
    Array<{
      index: number;
      preview: string;
      pageNumber: number | null;
    }>
  > {
    const chunkItems = this.page.locator('[data-testid="chunk-item"]');
    const count = await chunkItems.count();
    const chunks: Array<{ index: number; preview: string; pageNumber: number | null }> = [];

    for (let i = 0; i < count; i++) {
      const item = chunkItems.nth(i);
      const indexText = await item.locator('[data-testid="chunk-index"]').textContent();
      const preview = await item.locator('[data-testid="chunk-preview"]').textContent();
      const pageText = await item.locator('[data-testid="chunk-page"]').textContent();

      chunks.push({
        index: indexText ? parseInt(indexText.replace('#', '')) : i,
        preview: preview?.trim() || '',
        pageNumber: pageText ? parseInt(pageText.replace('Page ', '')) : null,
      });
    }
    return chunks;
  }

  /**
   * Get total chunk count
   */
  async getTotalChunkCount(): Promise<number> {
    const countText = await this.page.locator('[data-testid="total-chunk-count"]').textContent();
    const match = countText?.match(/(\d+)/);
    return match ? parseInt(match[1]) : 0;
  }

  /**
   * Select a chunk by index
   */
  async selectChunk(chunkIndex: number) {
    const chunk = this.page.locator(`[data-testid="chunk-item"][data-chunk-index="${chunkIndex}"]`);
    await chunk.click();
  }

  /**
   * Check if chunk is selected
   */
  async isChunkSelected(chunkIndex: number): Promise<boolean> {
    const chunk = this.page.locator(`[data-testid="chunk-item"][data-chunk-index="${chunkIndex}"]`);
    return (await chunk.getAttribute('data-selected')) === 'true';
  }

  /**
   * Search chunks by text
   */
  async searchChunks(query: string) {
    const searchInput = this.page.getByPlaceholder(/search chunks/i);
    await searchInput.fill(query);
    // Wait for debounce
    await this.page.waitForTimeout(400);
  }

  /**
   * Clear chunk search
   */
  async clearChunkSearch() {
    const clearButton = this.page.getByRole('button', { name: /clear search/i });
    await clearButton.click();
  }

  /**
   * Get search result count
   */
  async getSearchResultCount(): Promise<number> {
    const resultText = await this.page
      .locator('[data-testid="chunk-search-results"]')
      .textContent();
    const match = resultText?.match(/(\d+)/);
    return match ? parseInt(match[1]) : 0;
  }

  // ============================================================
  // Chunk Pagination
  // ============================================================

  /**
   * Go to next chunk page
   */
  async goToNextChunkPage() {
    await this.page.getByRole('button', { name: /next.*chunks/i }).click();
  }

  /**
   * Go to previous chunk page
   */
  async goToPreviousChunkPage() {
    await this.page.getByRole('button', { name: /previous.*chunks/i }).click();
  }

  /**
   * Get chunk pagination info
   */
  async getChunkPaginationInfo(): Promise<{
    showing: number;
    total: number;
    page: number;
  }> {
    const infoText = await this.page.locator('[data-testid="chunk-pagination-info"]').textContent();
    const match = infoText?.match(/Showing (\d+).*of (\d+).*Page (\d+)/i);
    return {
      showing: match ? parseInt(match[1]) : 0,
      total: match ? parseInt(match[2]) : 0,
      page: match ? parseInt(match[3]) : 1,
    };
  }

  // ============================================================
  // Document Content Viewer
  // ============================================================

  /**
   * Check if document content is loading
   */
  async isContentLoading(): Promise<boolean> {
    const loading = this.page.locator('[data-testid="document-content-loading"]');
    return await loading.isVisible();
  }

  /**
   * Wait for document content to load
   */
  async waitForContentLoaded() {
    await this.page.locator('[data-testid="document-content"]').waitFor({ state: 'visible' });
  }

  /**
   * Get document content type indicator
   */
  async getContentType(): Promise<string> {
    const contentType = await this.page
      .locator('[data-testid="document-content-type"]')
      .textContent();
    return contentType?.trim() || '';
  }

  /**
   * Check if PDF viewer is displayed
   */
  async isPdfViewerVisible(): Promise<boolean> {
    const pdfViewer = this.page.locator('[data-testid="pdf-viewer"]');
    return await pdfViewer.isVisible();
  }

  /**
   * Check if HTML content viewer is displayed
   */
  async isHtmlViewerVisible(): Promise<boolean> {
    const htmlViewer = this.page.locator('[data-testid="html-content-viewer"]');
    return await htmlViewer.isVisible();
  }

  /**
   * Check if text content viewer is displayed
   */
  async isTextViewerVisible(): Promise<boolean> {
    const textViewer = this.page.locator('[data-testid="text-content-viewer"]');
    return await textViewer.isVisible();
  }

  // ============================================================
  // Chunk Highlighting
  // ============================================================

  /**
   * Check if chunk highlight is visible in document
   */
  async isChunkHighlightVisible(): Promise<boolean> {
    const highlight = this.page.locator('[data-testid="chunk-highlight"]');
    return await highlight.isVisible();
  }

  /**
   * Get highlighted text content
   */
  async getHighlightedText(): Promise<string> {
    const highlight = this.page.locator('[data-testid="chunk-highlight"]');
    return (await highlight.textContent())?.trim() || '';
  }

  /**
   * Scroll document to show highlighted chunk
   */
  async scrollToHighlight() {
    const highlight = this.page.locator('[data-testid="chunk-highlight"]');
    await highlight.scrollIntoViewIfNeeded();
  }

  /**
   * Get highlight position info
   */
  async getHighlightPosition(): Promise<{
    charStart: number;
    charEnd: number;
    pageNumber: number | null;
  }> {
    const highlight = this.page.locator('[data-testid="chunk-highlight"]');
    const charStart = await highlight.getAttribute('data-char-start');
    const charEnd = await highlight.getAttribute('data-char-end');
    const pageNumber = await highlight.getAttribute('data-page-number');

    return {
      charStart: charStart ? parseInt(charStart) : 0,
      charEnd: charEnd ? parseInt(charEnd) : 0,
      pageNumber: pageNumber ? parseInt(pageNumber) : null,
    };
  }

  // ============================================================
  // Chunk Detail Panel
  // ============================================================

  /**
   * Open chunk detail panel for selected chunk
   */
  async openChunkDetailPanel() {
    const detailButton = this.page.getByRole('button', { name: /view chunk details/i });
    await detailButton.click();
    await this.page.locator('[data-testid="chunk-detail-panel"]').waitFor({ state: 'visible' });
  }

  /**
   * Close chunk detail panel
   */
  async closeChunkDetailPanel() {
    await this.page.getByRole('button', { name: /close/i }).click();
    await this.page.locator('[data-testid="chunk-detail-panel"]').waitFor({ state: 'hidden' });
  }

  /**
   * Get chunk detail information
   */
  async getChunkDetails(): Promise<{
    chunkIndex: number;
    charStart: number;
    charEnd: number;
    pageNumber: number | null;
    paragraphIndex: number | null;
    fullText: string;
  }> {
    const panel = this.page.locator('[data-testid="chunk-detail-panel"]');

    const chunkIndex = await panel.locator('[data-testid="detail-chunk-index"]').textContent();
    const charStart = await panel.locator('[data-testid="detail-char-start"]').textContent();
    const charEnd = await panel.locator('[data-testid="detail-char-end"]').textContent();
    const pageNumber = await panel.locator('[data-testid="detail-page-number"]').textContent();
    const paragraphIndex = await panel
      .locator('[data-testid="detail-paragraph-index"]')
      .textContent();
    const fullText = await panel.locator('[data-testid="detail-full-text"]').textContent();

    return {
      chunkIndex: chunkIndex ? parseInt(chunkIndex) : 0,
      charStart: charStart ? parseInt(charStart) : 0,
      charEnd: charEnd ? parseInt(charEnd) : 0,
      pageNumber: pageNumber && pageNumber !== '-' ? parseInt(pageNumber) : null,
      paragraphIndex: paragraphIndex && paragraphIndex !== '-' ? parseInt(paragraphIndex) : null,
      fullText: fullText?.trim() || '',
    };
  }

  /**
   * Copy chunk text to clipboard
   */
  async copyChunkText() {
    await this.page.getByRole('button', { name: /copy text/i }).click();
    await this.waitForToast(/copied/i);
  }

  // ============================================================
  // Document Download
  // ============================================================

  /**
   * Download original document
   */
  async downloadOriginalDocument(): Promise<string> {
    const [download] = await Promise.all([
      this.page.waitForEvent('download'),
      this.page.getByRole('button', { name: /download original/i }).click(),
    ]);
    return download.suggestedFilename();
  }

  // ============================================================
  // Error Handling
  // ============================================================

  /**
   * Check if error state is displayed
   */
  async isErrorVisible(): Promise<boolean> {
    const error = this.page.locator('[data-testid="chunk-viewer-error"]');
    return await error.isVisible();
  }

  /**
   * Get error message
   */
  async getErrorMessage(): Promise<string> {
    const error = this.page.locator('[data-testid="chunk-viewer-error"]');
    return (await error.textContent())?.trim() || '';
  }

  /**
   * Retry loading after error
   */
  async retryLoading() {
    await this.page.getByRole('button', { name: /retry/i }).click();
  }

  // ============================================================
  // Assertions
  // ============================================================

  /**
   * Assert chunk viewer is fully loaded
   */
  async expectChunkViewerLoaded() {
    await expect(this.page.locator('[data-testid="chunk-viewer-split-pane"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="chunk-list-pane"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="document-content-pane"]')).toBeVisible();
  }

  /**
   * Assert specific chunk is highlighted
   */
  async expectChunkHighlighted(chunkIndex: number) {
    await expect(
      this.page.locator(
        `[data-testid="chunk-item"][data-chunk-index="${chunkIndex}"][data-selected="true"]`
      )
    ).toBeVisible();
    await expect(this.page.locator('[data-testid="chunk-highlight"]')).toBeVisible();
  }

  /**
   * Assert document content type matches
   */
  async expectContentType(type: 'pdf' | 'html' | 'text') {
    const viewers: Record<string, () => Promise<boolean>> = {
      pdf: () => this.isPdfViewerVisible(),
      html: () => this.isHtmlViewerVisible(),
      text: () => this.isTextViewerVisible(),
    };
    const isVisible = await viewers[type]();
    expect(isVisible).toBe(true);
  }
}
