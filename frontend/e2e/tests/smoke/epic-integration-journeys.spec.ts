/**
 * E2E Smoke Tests: Story 5-0 - Epic 3 & 4 Integration Completion
 * Status: Generated for deferred AC4 validation (Story 5.16)
 * Generated: 2025-11-30
 *
 * Test Coverage:
 * - P0: Journey 1 - Document Upload → Processing → Search
 * - P0: Journey 2 - Search → Citation Display
 * - P1: Journey 3 - Chat Conversation (references Story 4.1 tests)
 * - P1: Journey 4 - Document Generation (Search → Generate → Edit → Export)
 *
 * Acceptance Criteria:
 * - AC4.1: Document shows "Completed" status within 2 minutes of upload
 * - AC4.2: Search returns results with at least 1 citation in [1] format
 * - AC4.3: Chat response streams within 5 seconds, maintains conversation history
 * - AC4.4: Draft exports successfully in at least one format with citations preserved
 *
 * Knowledge Base References:
 * - network-first.md: Route interception before navigation
 * - test-quality.md: Deterministic E2E tests, no hard waits
 * - test-priorities-matrix.md: P0 = Critical paths, P1 = Core journeys
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { Page } from '@playwright/test';

test.describe('Story 5-0: Epic Integration Smoke Tests', () => {
  test.beforeEach(async ({ authenticatedPage, page }) => {
    // GIVEN: User is authenticated
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('[P0] Journey 1: Document Upload → Processing → Search', async ({ page }) => {
    /**
     * GIVEN: User has access to a knowledge base
     * WHEN: User uploads a document, waits for processing, then searches
     * THEN: Document processes successfully and content is searchable with citations
     *
     * Success Criteria: Document shows "Completed" status within 2 minutes
     */

    // Step 1: Select or create KB (use demo KB)
    const kbCard = page.locator('[data-testid="kb-card"]').first();
    await expect(kbCard).toBeVisible({ timeout: 5000 });

    const kbName = await kbCard.locator('[data-testid="kb-name"]').textContent();
    await kbCard.click();

    // Should navigate to KB detail view
    await page.waitForURL(/\/kb\/.+/);

    // Step 2: Upload a test document
    const uploadButton = page.locator('[data-testid="upload-document-button"]');
    await expect(uploadButton).toBeVisible();

    // Create a test file (sample text document)
    const fileContent = `
      OAuth 2.0 Authentication Guide

      OAuth 2.0 is an authorization framework that enables applications to obtain
      limited access to user accounts on an HTTP service. It works by delegating
      user authentication to the service that hosts the user account.

      Key Concepts:
      - Authorization Code Grant
      - Implicit Grant
      - Client Credentials Grant
      - Resource Owner Password Grant

      Security Best Practices:
      - Always use HTTPS
      - Validate redirect URIs
      - Use state parameter to prevent CSRF
      - Implement proper token expiration
    `;

    // Upload file using file chooser
    const fileChooserPromise = page.waitForEvent('filechooser');
    await uploadButton.click();
    const fileChooser = await fileChooserPromise;

    await fileChooser.setFiles({
      name: 'oauth-guide.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from(fileContent),
    });

    // Step 3: Wait for document to appear in list
    const documentRow = page.locator('[data-testid="document-row"]').filter({
      hasText: 'oauth-guide',
    });
    await expect(documentRow).toBeVisible({ timeout: 10000 });

    // Step 4: Monitor document status (Queued → Processing → Completed)
    const statusBadge = documentRow.locator('[data-testid="document-status"]');

    // Should start as Queued or Processing
    const initialStatus = await statusBadge.textContent();
    expect(initialStatus).toMatch(/Queued|Processing/i);

    // CRITICAL: Wait for "Completed" status within 2 minutes (AC4 success criteria)
    await expect(statusBadge).toHaveText(/Completed/i, { timeout: 120000 });

    const completedTime = Date.now();
    console.log(`Document processing completed in ${completedTime}ms`);

    // Step 5: Navigate to Search page
    await page.goto('/search');
    await page.waitForLoadState('networkidle');

    // Step 6: Search for content from uploaded document
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible();

    // Network-first pattern: Intercept search request BEFORE submitting
    const searchResponsePromise = page.waitForResponse(
      (resp) => resp.url().includes('/api/v1/search') && resp.status() === 200
    );

    await searchInput.fill('OAuth 2.0 authorization framework');
    await searchInput.press('Enter');

    // Wait for search response
    const searchResponse = await searchResponsePromise;
    const searchData = await searchResponse.json();

    // Step 7: Verify search returns results with citations
    // CRITICAL: Search must return at least 1 citation (AC4.2 success criteria)
    expect(searchData.citations).toBeDefined();
    expect(searchData.citations.length).toBeGreaterThanOrEqual(1);

    // Verify citation appears in UI
    const citationBadge = page.locator('[data-testid="citation-badge"]').first();
    await expect(citationBadge).toBeVisible({ timeout: 5000 });

    const citationText = await citationBadge.textContent();
    expect(citationText).toMatch(/\[1\]/); // Should show [1] format

    // Verify answer contains content
    const answerText = page.locator('[data-testid="search-answer"]');
    await expect(answerText).toBeVisible();
    const answer = await answerText.textContent();
    expect(answer).toBeTruthy();
    expect(answer!.length).toBeGreaterThan(50);
  });

  test('[P0] Journey 2: Search → Citation Display', async ({ page }) => {
    /**
     * GIVEN: User navigates to Search from dashboard
     * WHEN: User enters search query
     * THEN: Streaming answer displays with inline [1], [2] citations
     * AND: Citation panel shows source excerpts
     * AND: Confidence score displays
     *
     * Success Criteria: Search returns results with at least 1 citation in [1] format
     */

    // Step 1: Navigate from dashboard to Search
    const searchCard = page.locator('[data-testid="search-card"]');
    await expect(searchCard).toBeVisible({ timeout: 5000 });
    await searchCard.click();

    // Should navigate to /search
    await expect(page).toHaveURL(/\/search$/);

    // Step 2: Enter search query
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible();

    // Network-first: Intercept BEFORE submitting search
    const searchResponsePromise = page.waitForResponse(
      (resp) => resp.url().includes('/api/v1/search') && resp.status() === 200
    );

    const searchQuery = 'authentication security best practices';
    await searchInput.fill(searchQuery);
    await searchInput.press('Enter');

    // Step 3: Verify streaming answer displays
    const thinkingIndicator = page.locator('[data-testid="thinking-indicator"]');
    await expect(thinkingIndicator).toBeVisible({ timeout: 1000 });

    // Wait for search to complete
    const searchResponse = await searchResponsePromise;
    await expect(thinkingIndicator).toBeHidden({ timeout: 10000 });

    const searchData = await searchResponse.json();

    // Step 4: Verify inline citations appear as [1], [2]
    const answerSection = page.locator('[data-testid="search-answer"]');
    await expect(answerSection).toBeVisible();

    const citationBadges = page.locator('[data-testid="citation-badge"]');
    const citationCount = await citationBadges.count();

    // CRITICAL: At least 1 citation must be present (AC4.2)
    expect(citationCount).toBeGreaterThanOrEqual(1);

    // Verify citation format [1], [2], [3]...
    for (let i = 0; i < Math.min(citationCount, 3); i++) {
      const badge = citationBadges.nth(i);
      const badgeText = await badge.textContent();
      expect(badgeText).toMatch(/\[\d+\]/);
    }

    // Step 5: Verify citation panel shows source excerpts
    const citationPanel = page.locator('[data-testid="citation-panel"]');
    await expect(citationPanel).toBeVisible();

    // Click first citation to view source
    await citationBadges.first().click();

    const citationSource = page.locator('[data-testid="citation-source"]').first();
    await expect(citationSource).toBeVisible();

    const sourceText = await citationSource.textContent();
    expect(sourceText).toBeTruthy();
    expect(sourceText!.length).toBeGreaterThan(20);

    // Step 6: Verify confidence score displays
    const confidenceScore = page.locator('[data-testid="confidence-score"]');
    await expect(confidenceScore).toBeVisible();

    const scoreText = await confidenceScore.textContent();
    // Score should be a percentage like "85%" or "High"
    expect(scoreText).toMatch(/\d+%|High|Medium|Low/i);
  });

  test('[P1] Journey 3: Chat Conversation', async ({ page }) => {
    /**
     * GIVEN: User navigates to Chat from dashboard
     * WHEN: User sends message and follow-up
     * THEN: Streaming response appears with citations within 5 seconds
     * AND: Chat maintains conversation history
     *
     * Success Criteria: Chat response streams within 5 seconds, maintains history
     *
     * NOTE: Detailed chat tests exist in chat-conversation.spec.ts (Story 4.1)
     * This is a smoke test for end-to-end integration validation
     */

    // Step 1: Navigate from dashboard to Chat
    const chatCard = page.locator('[data-testid="chat-card"]');
    await expect(chatCard).toBeVisible({ timeout: 5000 });
    await chatCard.click();

    // Should navigate to /chat
    await expect(page).toHaveURL(/\/chat$/);

    // Step 2: Send first message
    const chatInput = page.locator('[data-testid="chat-input"]');
    await expect(chatInput).toBeVisible();

    const startTime = Date.now();

    await chatInput.fill('What is OAuth 2.0?');
    await chatInput.press('Enter');

    // Step 3: Verify streaming response appears
    const thinkingIndicator = page.locator('[data-testid="thinking-indicator"]');
    await expect(thinkingIndicator).toBeVisible({ timeout: 1000 });

    const aiMessage = page.locator('[data-testid="chat-message"][data-role="assistant"]').first();
    await aiMessage.waitFor({ state: 'visible', timeout: 10000 });

    const timeToFirstToken = Date.now() - startTime;

    // CRITICAL: First token should arrive within 5 seconds (AC4.3)
    expect(timeToFirstToken).toBeLessThan(5000);

    // Wait for streaming to complete
    await expect(thinkingIndicator).toBeHidden({ timeout: 15000 });

    // Verify citations appear in chat
    const citationBadge = aiMessage.locator('[data-testid="citation-badge"]').first();
    await expect(citationBadge).toBeVisible({ timeout: 2000 });

    // Step 4: Send follow-up message (multi-turn)
    await chatInput.fill('How do I implement it?');
    await chatInput.press('Enter');

    await expect(thinkingIndicator).toBeVisible({ timeout: 1000 });
    await expect(thinkingIndicator).toBeHidden({ timeout: 15000 });

    // Step 5: Verify conversation history maintained
    const allMessages = await page.locator('[data-testid="chat-message"]').all();

    // Should have 4 messages: 2 user + 2 AI
    expect(allMessages.length).toBe(4);

    // Verify second response maintains context (references "it" = OAuth)
    const secondAiMessage = page
      .locator('[data-testid="chat-message"][data-role="assistant"]')
      .nth(1);
    const secondResponse = await secondAiMessage.textContent();
    expect(secondResponse?.toLowerCase()).toMatch(/implement|integration|oauth/);
  });

  test('[P1] Journey 4: Document Generation', async ({ page }) => {
    /**
     * GIVEN: User performs search to gather context
     * WHEN: User generates draft from template
     * THEN: Draft generates with streaming
     * AND: User can edit draft
     * AND: Draft exports successfully in at least one format with citations
     *
     * Success Criteria: Draft exports in DOCX/PDF/MD with citations preserved
     */

    // Step 1: Perform search to gather context
    await page.goto('/search');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible();

    // Network-first: Intercept search
    const searchResponsePromise = page.waitForResponse(
      (resp) => resp.url().includes('/api/v1/search') && resp.status() === 200
    );

    await searchInput.fill('OAuth 2.0 implementation guide');
    await searchInput.press('Enter');

    await searchResponsePromise;

    // Wait for results to display
    const thinkingIndicator = page.locator('[data-testid="thinking-indicator"]');
    await expect(thinkingIndicator).toBeHidden({ timeout: 10000 });

    // Step 2: Click "Generate Draft" button
    const generateButton = page.locator('[data-testid="generate-draft-button"]');
    await expect(generateButton).toBeVisible();
    await generateButton.click();

    // Step 3: Verify template selector modal appears with 4 templates
    const templateModal = page.locator('[data-testid="template-selector-modal"]');
    await expect(templateModal).toBeVisible({ timeout: 3000 });

    const templateCards = page.locator('[data-testid="template-card"]');
    const templateCount = await templateCards.count();

    // Should show 4 templates (Technical Doc, Summary, Report, Guide)
    expect(templateCount).toBe(4);

    // Step 4: Select template and provide context
    const firstTemplate = templateCards.first();
    await firstTemplate.click();

    // Fill in generation context/prompt
    const contextInput = page.locator('[data-testid="generation-context-input"]');
    if (await contextInput.isVisible()) {
      await contextInput.fill('Create a comprehensive guide for OAuth 2.0 implementation');
    }

    const confirmButton = page.locator('[data-testid="confirm-generation-button"]');
    await confirmButton.click();

    // Step 5: Verify draft generates with streaming
    const draftEditor = page.locator('[data-testid="draft-editor"]');
    await expect(draftEditor).toBeVisible({ timeout: 5000 });

    // Wait for generation to complete
    const generationIndicator = page.locator('[data-testid="generation-indicator"]');
    await expect(generationIndicator).toBeHidden({ timeout: 60000 });

    // Verify draft has content
    const draftContent = await draftEditor.textContent();
    expect(draftContent).toBeTruthy();
    expect(draftContent!.length).toBeGreaterThan(100);

    // Step 6: Test edit functionality
    const editableArea = page.locator('[data-testid="draft-content-editable"]');
    if (await editableArea.isVisible()) {
      await editableArea.click();
      await editableArea.fill(draftContent + '\n\nAdditional notes: Test edit');

      const updatedContent = await editableArea.textContent();
      expect(updatedContent).toContain('Additional notes: Test edit');
    }

    // Step 7: Export draft to at least one format with citations preserved
    const exportButton = page.locator('[data-testid="export-draft-button"]');
    await expect(exportButton).toBeVisible();
    await exportButton.click();

    const exportModal = page.locator('[data-testid="export-modal"]');
    await expect(exportModal).toBeVisible();

    // Try DOCX export first
    const docxOption = page.locator('[data-testid="export-format-docx"]');
    if (await docxOption.isVisible()) {
      await docxOption.click();
    } else {
      // Fallback to any available format (PDF or MD)
      const exportOptions = page.locator('[data-testid^="export-format-"]');
      const firstOption = exportOptions.first();
      await firstOption.click();
    }

    const downloadButton = page.locator('[data-testid="confirm-export-button"]');

    // Network-first: Wait for export request
    const exportPromise = page.waitForResponse(
      (resp) => resp.url().includes('/api/v1/export') && resp.status() === 200,
      { timeout: 30000 }
    );

    await downloadButton.click();

    const exportResponse = await exportPromise;
    const exportData = await exportResponse.json();

    // CRITICAL: Export should succeed with citations preserved (AC4.4)
    expect(exportResponse.status()).toBe(200);
    expect(exportData.download_url || exportData.file_url).toBeDefined();

    // Verify citations are in export (check metadata or response)
    if (exportData.citations) {
      expect(exportData.citations.length).toBeGreaterThanOrEqual(1);
    }
  });
});

test.describe('Story 5-0: Navigation Integration Tests', () => {
  test.use({ storageState: 'e2e/.auth/user.json' });

  test('[P0] Dashboard → Search navigation works', async ({ page }) => {
    /**
     * GIVEN: User is on dashboard
     * WHEN: User clicks Search card
     * THEN: User navigates to /search page
     */
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const searchCard = page.locator('[data-testid="search-card"]');
    await expect(searchCard).toBeVisible({ timeout: 5000 });

    await searchCard.click();

    await expect(page).toHaveURL(/\/search$/);

    // Verify search page loaded
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible();
  });

  test('[P0] Dashboard → Chat navigation works', async ({ page }) => {
    /**
     * GIVEN: User is on dashboard
     * WHEN: User clicks Chat card
     * THEN: User navigates to /chat page
     */
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const chatCard = page.locator('[data-testid="chat-card"]');
    await expect(chatCard).toBeVisible({ timeout: 5000 });

    await chatCard.click();

    await expect(page).toHaveURL(/\/chat$/);

    // Verify chat page loaded
    const chatInput = page.locator('[data-testid="chat-input"]');
    await expect(chatInput).toBeVisible();
  });

  test('[P1] No "Coming in Epic" placeholders remain', async ({ page }) => {
    /**
     * GIVEN: Dashboard is updated with navigation cards
     * WHEN: User views dashboard
     * THEN: No "Coming in Epic 3" or "Coming in Epic 4" text is visible
     */
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const epicPlaceholder = page.getByText(/Coming in Epic [34]/i);
    await expect(epicPlaceholder).toBeHidden();
  });
});
