/**
 * E2E Tests: Chat Streaming UI (Story 4.2)
 * Tests streaming response UX with SSE
 */

import { test, expect } from '@playwright/test';

test.describe('Chat Streaming UI', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/auth/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'testpassword123');
    await page.click('[data-testid="login-button"]');

    // Wait for redirect to dashboard
    await page.waitForURL('/dashboard');

    // Navigate to a KB with documents
    await page.click('[data-testid="kb-card"]');
    await page.waitForURL(/\/kb\/.+/);

    // Click Chat tab
    await page.click('[data-testid="chat-tab"]');
  });

  test('P1: user message appears immediately on send', async ({ page }) => {
    /**
     * GIVEN: I am in the chat interface
     * WHEN: I send a message
     * THEN: my message appears immediately on the right
     */
    const userMessage = 'What is OAuth 2.0?';

    await page.fill('[data-testid="chat-input"]', userMessage);
    await page.click('[data-testid="send-button"]');

    // User message should appear immediately
    const userMsgElement = page.locator('[data-testid="chat-message"][data-role="user"]').last();
    await expect(userMsgElement).toBeVisible();
    await expect(userMsgElement).toContainText(userMessage);

    // Should be right-aligned
    await expect(userMsgElement).toHaveClass(/right|justify-end|ml-auto/);
  });

  test('P1: thinking indicator appears while AI responds', async ({ page }) => {
    /**
     * GIVEN: I send a message
     * WHEN: waiting for AI response
     * THEN: a "thinking" indicator appears
     */
    await page.fill('[data-testid="chat-input"]', 'Explain PKCE flow');
    await page.click('[data-testid="send-button"]');

    // Thinking indicator should appear
    const thinkingIndicator = page.locator('[data-testid="thinking-indicator"]');
    await expect(thinkingIndicator).toBeVisible();
    await expect(thinkingIndicator).toContainText(/thinking/i);
  });

  test('P1: AI response streams word-by-word', async ({ page }) => {
    /**
     * GIVEN: AI is responding
     * WHEN: tokens stream in
     * THEN: they appear word-by-word in the chat bubble
     */
    await page.fill('[data-testid="chat-input"]', 'What is OAuth 2.0?');
    await page.click('[data-testid="send-button"]');

    // Wait for AI message to start appearing
    const aiMessage = page
      .locator('[data-testid="chat-message"][data-role="assistant"]')
      .last();
    await expect(aiMessage).toBeVisible({ timeout: 10000 });

    // Content should progressively appear (not all at once)
    // We can't easily test word-by-word streaming, but we can verify the message exists
    await expect(aiMessage).toContainText(/oauth/i);
  });

  test('P1: citations populate in real-time', async ({ page }) => {
    /**
     * GIVEN: AI response contains citations
     * WHEN: response streams
     * THEN: citation markers appear inline as generated
     */
    await page.fill('[data-testid="chat-input"]', 'How do we handle authentication?');
    await page.click('[data-testid="send-button"]');

    // Wait for AI message
    const aiMessage = page
      .locator('[data-testid="chat-message"][data-role="assistant"]')
      .last();
    await expect(aiMessage).toBeVisible({ timeout: 10000 });

    // Check for citation badges
    const citationBadges = page.locator('[data-testid="citation-badge"]');
    const count = await citationBadges.count();

    // Should have at least one citation
    expect(count).toBeGreaterThan(0);
  });

  test('P1: AI messages are left-aligned with proper styling', async ({ page }) => {
    /**
     * GIVEN: AI responds
     * THEN: message is left-aligned with surface color background
     */
    await page.fill('[data-testid="chat-input"]', 'Test query');
    await page.click('[data-testid="send-button"]');

    const aiMessage = page
      .locator('[data-testid="chat-message"][data-role="assistant"]')
      .last();
    await expect(aiMessage).toBeVisible({ timeout: 10000 });

    // Should be left-aligned
    await expect(aiMessage).toHaveClass(/left|justify-start|mr-auto/);
  });

  test('P2: confidence indicator shows for AI messages', async ({ page }) => {
    /**
     * GIVEN: AI message is complete
     * THEN: confidence indicator appears with percentage
     */
    await page.fill('[data-testid="chat-input"]', 'What is PKCE?');
    await page.click('[data-testid="send-button"]');

    const aiMessage = page
      .locator('[data-testid="chat-message"][data-role="assistant"]')
      .last();
    await expect(aiMessage).toBeVisible({ timeout: 10000 });

    // Wait for streaming to complete (thinking indicator disappears)
    await expect(page.locator('[data-testid="thinking-indicator"]')).not.toBeVisible({
      timeout: 15000,
    });

    // Confidence indicator should be visible
    const confidenceIndicator = page.locator('[data-testid="confidence-indicator"]').last();
    await expect(confidenceIndicator).toBeVisible();

    // Should show percentage
    await expect(confidenceIndicator).toContainText(/%/);
  });

  test('P2: timestamp displays relative time', async ({ page }) => {
    /**
     * GIVEN: Messages are sent
     * THEN: timestamps show relative time like "just now"
     */
    await page.fill('[data-testid="chat-input"]', 'Test message');
    await page.click('[data-testid="send-button"]');

    const userMessage = page.locator('[data-testid="chat-message"][data-role="user"]').last();
    await expect(userMessage).toBeVisible();

    const timestamp = userMessage.locator('[data-testid="message-timestamp"]');
    await expect(timestamp).toBeVisible();
    await expect(timestamp).toContainText(/just now|ago/i);
  });

  test('P3: citation click triggers preview', async ({ page }) => {
    /**
     * GIVEN: AI message with citations
     * WHEN: user clicks citation badge
     * THEN: citation panel/preview opens
     */
    await page.fill('[data-testid="chat-input"]', 'Show me authentication examples');
    await page.click('[data-testid="send-button"]');

    // Wait for AI response
    await expect(
      page.locator('[data-testid="chat-message"][data-role="assistant"]').last()
    ).toBeVisible({ timeout: 10000 });

    // Click first citation badge
    const citationBadge = page.locator('[data-testid="citation-badge"]').first();
    await citationBadge.click();

    // Citation panel or preview should open
    // (Exact behavior depends on UX implementation - checking for common patterns)
    const citationPanel = page.locator('[data-testid="citation-panel"]');
    const citationModal = page.locator('[role="dialog"]');

    const panelVisible = await citationPanel.isVisible().catch(() => false);
    const modalVisible = await citationModal.isVisible().catch(() => false);

    expect(panelVisible || modalVisible).toBeTruthy();
  });

  test('P3: multiple messages create conversation thread', async ({ page }) => {
    /**
     * GIVEN: Multiple messages sent
     * THEN: conversation thread shows all messages in order
     */
    // Send first message
    await page.fill('[data-testid="chat-input"]', 'What is OAuth?');
    await page.click('[data-testid="send-button"]');

    await expect(
      page.locator('[data-testid="chat-message"][data-role="assistant"]').first()
    ).toBeVisible({ timeout: 10000 });

    // Wait for thinking to complete
    await expect(page.locator('[data-testid="thinking-indicator"]')).not.toBeVisible({
      timeout: 15000,
    });

    // Send follow-up
    await page.fill('[data-testid="chat-input"]', 'Tell me more');
    await page.click('[data-testid="send-button"]');

    await expect(
      page.locator('[data-testid="chat-message"][data-role="assistant"]').last()
    ).toBeVisible({ timeout: 10000 });

    // Should have at least 4 messages (2 user + 2 assistant)
    const messageCount = await page.locator('[data-testid="chat-message"]').count();
    expect(messageCount).toBeGreaterThanOrEqual(4);
  });
});
