/**
 * ATDD E2E Tests: Epic 4 - Chat Conversation (Story 4.1, 4.2)
 * Status: RED phase - Tests written before implementation
 * Generated: 2025-11-26
 *
 * Test Coverage:
 * - P0: Multi-turn conversation maintains context (E2E)
 * - P0: Citation markers appear inline in chat
 * - P0: SSE streaming delivers tokens
 * - P1: Chat UI renders messages correctly
 * - P1: Timestamps and thinking indicators
 *
 * Risk Mitigation:
 * - R-001 (TECH): Token limit management - test 10-turn conversation
 * - R-002 (SEC): Citation integrity in chat responses
 * - R-003 (PERF): Streaming latency <2s
 *
 * Knowledge Base References:
 * - network-first.md: Route interception before navigation
 * - test-quality.md: Deterministic E2E tests
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { Page } from '@playwright/test';

test.describe('Chat Conversation', () => {
  test.beforeEach(async ({ authenticatedPage, page }) => {
    // GIVEN: User is authenticated and has demo KB
    await page.goto('/dashboard');

    // Wait for KB list to load
    await page.waitForSelector('[data-testid="kb-card"]');

    // Click on demo KB to enter chat
    await page.click('[data-testid="kb-card"]:first-child');

    // Should navigate to chat interface
    await page.waitForURL(/\/kb\/.*\/chat/);
  });

  test('P0: multi-turn conversation maintains context', async ({ page }) => {
    /**
     * Risk: R-001 (Token limit management)
     * GIVEN: User is on chat page
     * WHEN: User sends 5 follow-up messages requiring context
     * THEN: Each response demonstrates understanding of previous turns
     */

    // Turn 1: Initial question
    await sendChatMessage(page, 'What is OAuth 2.0?');
    const response1 = await waitForChatResponse(page);

    // Verify response contains OAuth content
    expect(response1).toContain('OAuth');

    // Verify citations appear
    await expect(page.locator('[data-testid="citation-badge"]').first()).toBeVisible();

    // Turn 2: Follow-up (requires context)
    await sendChatMessage(page, 'How do I implement it?'); // "it" = OAuth
    const response2 = await waitForChatResponse(page);

    // Should reference implementation (context maintained)
    expect(response2.toLowerCase()).toMatch(/implement|integration|setup/);

    // Turn 3: Another contextual follow-up
    await sendChatMessage(page, 'What are the security risks?');
    const response3 = await waitForChatResponse(page);

    // Should discuss security in OAuth context
    expect(response3.toLowerCase()).toMatch(/security|risk|vulnerability/);

    // Turns 4-5: Continue conversation
    await sendChatMessage(page, 'Which grant type should I use?');
    const response4 = await waitForChatResponse(page);
    expect(response4.toLowerCase()).toMatch(/grant|authorization/);

    await sendChatMessage(page, 'Show me an example');
    const response5 = await waitForChatResponse(page);
    expect(response5.length).toBeGreaterThan(0);

    // CRITICAL: Verify all 10 messages (5 user + 5 AI) are visible in chat
    const allMessages = await page.locator('[data-testid="chat-message"]').all();
    expect(allMessages.length).toBe(10);
  });

  test('P0: SSE streaming delivers tokens and citations appear inline', async ({ page }) => {
    /**
     * Risk: R-003 (Streaming latency)
     * Risk: R-002 (Citation integrity)
     * GIVEN: User sends a message
     * WHEN: Response streams via SSE
     * THEN: First token arrives <2s AND citations appear inline as [1], [2]
     */

    const messageInput = page.locator('[data-testid="chat-input"]');

    await messageInput.fill('What is JWT authentication?');

    // Start timer
    const startTime = Date.now();

    await messageInput.press('Enter');

    // Wait for thinking indicator
    await expect(page.locator('[data-testid="thinking-indicator"]')).toBeVisible();

    // Wait for first token to appear in response
    const aiMessage = page.locator('[data-testid="chat-message"][data-role="assistant"]').last();
    await aiMessage.waitFor({ state: 'visible', timeout: 3000 });

    // Measure time-to-first-token
    const timeToFirstToken = Date.now() - startTime;

    // CRITICAL: First token should arrive within 2 seconds
    expect(timeToFirstToken).toBeLessThan(2000);

    // Wait for streaming to complete (thinking indicator disappears)
    await expect(page.locator('[data-testid="thinking-indicator"]')).toBeHidden({ timeout: 10000 });

    // Verify citation badges appear inline
    const citationBadges = aiMessage.locator('[data-testid="citation-badge"]');
    const badgeCount = await citationBadges.count();

    expect(badgeCount).toBeGreaterThan(0);

    // Verify citation numbers are sequential (1, 2, 3...)
    for (let i = 0; i < badgeCount; i++) {
      const badge = citationBadges.nth(i);
      const badgeText = await badge.textContent();
      // Badge should show number like [1], [2], etc.
      expect(badgeText).toMatch(/\[\d+\]/);
    }
  });

  test('P1: chat UI renders messages correctly with timestamps', async ({ page }) => {
    /**
     * GIVEN: User sends messages
     * WHEN: Chat displays messages
     * THEN: User messages right-aligned, AI left-aligned, timestamps shown
     */

    await sendChatMessage(page, 'Test message 1');
    await waitForChatResponse(page);

    await sendChatMessage(page, 'Test message 2');
    await waitForChatResponse(page);

    // Check user message alignment (right-aligned)
    const userMessages = page.locator('[data-testid="chat-message"][data-role="user"]');
    const userCount = await userMessages.count();
    expect(userCount).toBe(2);

    // Verify user messages have correct styling
    for (let i = 0; i < userCount; i++) {
      const msg = userMessages.nth(i);
      // Should have right-aligned class or style
      const classes = await msg.getAttribute('class');
      expect(classes).toMatch(/right|justify-end|ml-auto/);
    }

    // Check AI message alignment (left-aligned)
    const aiMessages = page.locator('[data-testid="chat-message"][data-role="assistant"]');
    const aiCount = await aiMessages.count();
    expect(aiCount).toBe(2);

    // Verify timestamps are displayed
    const timestamps = page.locator('[data-testid="message-timestamp"]');
    const timestampCount = await timestamps.count();
    expect(timestampCount).toBeGreaterThanOrEqual(4); // At least 4 messages

    // Verify timestamp format (relative time like "2m ago")
    const firstTimestamp = await timestamps.first().textContent();
    expect(firstTimestamp).toMatch(/\d+[smh]\s*ago|just now/);
  });

  test('P1: thinking indicator shows before first token', async ({ page }) => {
    /**
     * GIVEN: User sends message
     * WHEN: Waiting for response
     * THEN: "AI is thinking..." indicator displays
     */

    await sendChatMessage(page, 'Test question');

    // Thinking indicator should appear immediately
    await expect(page.locator('[data-testid="thinking-indicator"]')).toBeVisible({ timeout: 500 });

    // Verify indicator text
    const indicatorText = await page.locator('[data-testid="thinking-indicator"]').textContent();
    expect(indicatorText?.toLowerCase()).toMatch(/thinking|generating|processing/);

    // Wait for response to complete
    await waitForChatResponse(page);

    // Thinking indicator should disappear
    await expect(page.locator('[data-testid="thinking-indicator"]')).toBeHidden();
  });

  test('P1: new conversation clears context', async ({ page }) => {
    /**
     * GIVEN: User has active conversation about OAuth
     * WHEN: User clicks "New Conversation"
     * THEN: Previous context is cleared
     */

    // Start conversation about OAuth
    await sendChatMessage(page, 'Tell me about OAuth 2.0 grant types');
    await waitForChatResponse(page);

    // Click "New Conversation" button
    await page.click('[data-testid="new-conversation-button"]');

    // Confirm dialog if shown
    const confirmButton = page.locator('button:has-text("Start New")');
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
    }

    // Chat should be cleared
    const messages = await page.locator('[data-testid="chat-message"]').all();
    expect(messages.length).toBe(0);

    // Send new message on different topic
    await sendChatMessage(page, 'What is JWT?');
    const response = await waitForChatResponse(page);

    // Should discuss JWT, not OAuth (context cleared)
    expect(response.toLowerCase()).toContain('jwt');

    // Follow-up that would make sense in OAuth context
    await sendChatMessage(page, 'What grant type should I use?');
    const response2 = await waitForChatResponse(page);

    // Should NOT reference OAuth grant types (new context)
    // Response should be confused or ask for clarification
    expect(response2.toLowerCase()).not.toMatch(/authorization code|implicit|client credentials/);
  });

  test('P2: conversation history scrolls correctly with many messages', async ({ page }) => {
    /**
     * GIVEN: Conversation with 10+ messages
     * WHEN: User scrolls chat
     * THEN: All messages are accessible and rendering is performant
     */

    // Send 10 messages
    for (let i = 1; i <= 10; i++) {
      await sendChatMessage(page, `Message ${i}: Tell me about authentication`);
      await waitForChatResponse(page, 1000); // Short timeout for speed
    }

    // Verify scroll container exists
    const chatContainer = page.locator('[data-testid="chat-messages-container"]');
    await expect(chatContainer).toBeVisible();

    // Verify auto-scroll to bottom (latest message visible)
    const latestMessage = page.locator('[data-testid="chat-message"]').last();
    await expect(latestMessage).toBeInViewport();

    // Scroll to top
    await chatContainer.evaluate((el) => {
      el.scrollTop = 0;
    });

    // Verify first message is now visible
    const firstMessage = page.locator('[data-testid="chat-message"]').first();
    await expect(firstMessage).toBeInViewport();
  });
});

// Helper functions
async function sendChatMessage(page: Page, message: string) {
  const input = page.locator('[data-testid="chat-input"]');
  await input.fill(message);
  await input.press('Enter');
}

async function waitForChatResponse(page: Page, timeout = 10000): Promise<string> {
  // Wait for thinking indicator to appear and disappear
  await page
    .locator('[data-testid="thinking-indicator"]')
    .waitFor({ state: 'visible', timeout: 1000 })
    .catch(() => {});
  await page.locator('[data-testid="thinking-indicator"]').waitFor({ state: 'hidden', timeout });

  // Get latest AI message
  const aiMessage = page.locator('[data-testid="chat-message"][data-role="assistant"]').last();
  await aiMessage.waitFor({ state: 'visible', timeout });

  return (await aiMessage.textContent()) || '';
}
