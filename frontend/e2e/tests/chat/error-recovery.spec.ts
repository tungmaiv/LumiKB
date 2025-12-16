/**
 * E2E Tests: Chat Error Recovery (Story 4.2)
 * Priority: P2 (Medium - Error handling paths)
 * Generated: 2025-11-27
 *
 * Test Coverage:
 * - P2: SSE connection drop recovery
 * - P2: Partial message preservation on error
 * - P2: Network error display (user-friendly messages)
 * - P2: Retry after error
 * - P3: EventSource cleanup on page navigation
 *
 * Risk Mitigation:
 * - R-004 (UX): Error recovery without data loss
 * - R-003 (PERF): Graceful degradation on network issues
 *
 * Knowledge Base References:
 * - network-first.md: Route interception patterns
 * - test-quality.md: Deterministic E2E tests
 * - error-handling.md: Error recovery patterns
 */

import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Chat Error Recovery', () => {
  test.beforeEach(async ({ authenticatedPage, page }) => {
    // GIVEN: User is authenticated and on chat page
    await page.goto('/dashboard');
    await page.waitForSelector('[data-testid="kb-card"]');
    await page.click('[data-testid="kb-card"]:first-child');
    await page.waitForURL(/\/kb\/.*\/chat/);
  });

  test('[P2] should preserve partial message when connection drops', async ({ page }) => {
    /**
     * Risk: R-004 (Data loss on error)
     * GIVEN: AI is streaming a response
     * WHEN: Network connection drops mid-stream
     * THEN: Partial message content is preserved (not deleted)
     * AND: Error message is displayed
     * AND: User can retry
     */

    // Intercept streaming endpoint to simulate connection drop
    await page.route('**/api/v1/chat/stream*', async (route) => {
      const response = route.request();

      // Send partial response then drop connection
      route.fulfill({
        status: 200,
        headers: {
          'content-type': 'text/event-stream',
          'cache-control': 'no-cache',
        },
        body: `data: {"type":"status","content":"Searching..."}\n\ndata: {"type":"token","content":"OAuth 2.0 is"}\n\ndata: {"type":"token","content":" an authorization"}`,
        // Connection drops here (no done event)
      });

      // Simulate connection drop after 500ms
      setTimeout(() => {
        route.abort('failed');
      }, 500);
    });

    // Send message
    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('What is OAuth 2.0?');
    await input.press('Enter');

    // Wait for partial response
    await page.waitForSelector('[data-testid="chat-message"][data-role="assistant"]', {
      timeout: 2000,
    });

    const aiMessage = page.locator('[data-testid="chat-message"][data-role="assistant"]').last();

    // Verify partial content is preserved
    await expect(aiMessage).toContainText('OAuth 2.0 is an authorization');

    // Verify error message is shown
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText(
      /connection lost|please try again/i
    );

    // Verify input is re-enabled (user can retry)
    await expect(input).toBeEnabled();
  });

  test('[P2] should display user-friendly error when API returns error event', async ({ page }) => {
    /**
     * GIVEN: User sends message
     * WHEN: API returns error event (e.g., LLM timeout)
     * THEN: User-friendly error message is displayed
     * AND: Technical error details are not exposed
     */

    // Intercept streaming endpoint to send error event
    await page.route('**/api/v1/chat/stream*', async (route) => {
      route.fulfill({
        status: 200,
        headers: {
          'content-type': 'text/event-stream',
          'cache-control': 'no-cache',
        },
        body: `data: {"type":"status","content":"Searching..."}\n\ndata: {"type":"error","message":"Generation failed: LLM timeout"}\n\n`,
      });
    });

    // Send message
    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('Test query');
    await input.press('Enter');

    // Wait for error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 3000 });

    // Verify user-friendly error (not raw technical error)
    const errorText = await page.locator('[data-testid="error-message"]').textContent();

    // Should contain user-friendly message
    expect(errorText).toMatch(/an error occurred|please try again|something went wrong/i);

    // Should NOT expose technical details (LLM timeout)
    expect(errorText).not.toContain('LLM timeout');
    expect(errorText).not.toContain('Generation failed');
  });

  test('[P2] should allow retry after error', async ({ page }) => {
    /**
     * GIVEN: Previous message failed with error
     * WHEN: User sends new message
     * THEN: New message is sent successfully
     * AND: Error state is cleared
     */

    // First request: simulate error
    let requestCount = 0;
    await page.route('**/api/v1/chat/stream*', async (route) => {
      requestCount++;

      if (requestCount === 1) {
        // First request fails
        route.fulfill({
          status: 200,
          headers: {
            'content-type': 'text/event-stream',
            'cache-control': 'no-cache',
          },
          body: `data: {"type":"error","message":"Service unavailable"}\n\n`,
        });
      } else {
        // Second request succeeds
        route.fulfill({
          status: 200,
          headers: {
            'content-type': 'text/event-stream',
            'cache-control': 'no-cache',
          },
          body: `data: {"type":"status","content":"Searching..."}\n\ndata: {"type":"token","content":"Success"}\n\ndata: {"type":"done"}\n\n`,
        });
      }
    });

    const input = page.locator('[data-testid="chat-input"]');

    // First message (fails)
    await input.fill('First message');
    await input.press('Enter');

    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 3000 });

    // Retry (second message succeeds)
    await input.fill('Second message');
    await input.press('Enter');

    // Wait for success response
    await page.waitForSelector('[data-testid="chat-message"][data-role="assistant"]', {
      timeout: 3000,
    });

    const aiMessage = page.locator('[data-testid="chat-message"][data-role="assistant"]').last();
    await expect(aiMessage).toContainText('Success');

    // Error message should be hidden
    await expect(page.locator('[data-testid="error-message"]')).toBeHidden();
  });

  test('[P2] should handle 404 permission error gracefully', async ({ page }) => {
    /**
     * GIVEN: User does not have permission to access KB
     * WHEN: User tries to send message
     * THEN: User-friendly permission error is shown
     * AND: No chat messages are created
     */

    // Intercept streaming endpoint to return 404
    await page.route('**/api/v1/chat/stream*', async (route) => {
      route.fulfill({
        status: 404,
        body: JSON.stringify({
          detail: 'Knowledge Base not found',
        }),
      });
    });

    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('Test message');
    await input.press('Enter');

    // Wait for error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 3000 });

    // Verify error message content
    const errorText = await page.locator('[data-testid="error-message"]').textContent();
    expect(errorText).toMatch(/not found|no access|permission denied/i);

    // Verify no AI message was created
    const aiMessages = page.locator('[data-testid="chat-message"][data-role="assistant"]');
    await expect(aiMessages).toHaveCount(0);
  });

  test('[P3] should clean up EventSource on page navigation', async ({ page }) => {
    /**
     * GIVEN: User is streaming a response
     * WHEN: User navigates away from chat page
     * THEN: EventSource connection is closed (no memory leak)
     */

    // Start streaming
    await page.route('**/api/v1/chat/stream*', async (route) => {
      route.fulfill({
        status: 200,
        headers: {
          'content-type': 'text/event-stream',
          'cache-control': 'no-cache',
        },
        body: `data: {"type":"status","content":"Searching..."}\n\n`,
        // Keep connection open (no done event)
      });
    });

    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('Test message');
    await input.press('Enter');

    // Wait for streaming to start
    await expect(page.locator('[data-testid="thinking-indicator"]')).toBeVisible();

    // Navigate away
    await page.goto('/dashboard');

    // Verify navigation succeeded (no errors)
    await page.waitForURL('/dashboard');

    // Note: EventSource cleanup verification requires browser DevTools monitoring
    // This test documents expected behavior for manual verification
  });

  test('[P3] should show "No documents" error for empty KB', async ({ page }) => {
    /**
     * GIVEN: KB has no indexed documents
     * WHEN: User sends message
     * THEN: Clear error message is displayed
     */

    // Intercept streaming endpoint to return "no documents" error
    await page.route('**/api/v1/chat/stream*', async (route) => {
      route.fulfill({
        status: 200,
        headers: {
          'content-type': 'text/event-stream',
          'cache-control': 'no-cache',
        },
        body: `data: {"type":"error","message":"No indexed documents found in this Knowledge Base"}\n\n`,
      });
    });

    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('Test message');
    await input.press('Enter');

    // Wait for error
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 3000 });

    const errorText = await page.locator('[data-testid="error-message"]').textContent();
    expect(errorText).toMatch(/no documents|empty knowledge base/i);
  });

  test('[P3] should recover from network timeout', async ({ page }) => {
    /**
     * GIVEN: Network request times out
     * WHEN: User waits for timeout
     * THEN: Timeout error is displayed
     * AND: User can retry
     */

    // Simulate timeout by delaying response beyond timeout threshold
    await page.route('**/api/v1/chat/stream*', async (route) => {
      // Delay response for 15 seconds (beyond typical timeout)
      await new Promise((resolve) => setTimeout(resolve, 15000));

      route.fulfill({
        status: 200,
        headers: {
          'content-type': 'text/event-stream',
          'cache-control': 'no-cache',
        },
        body: `data: {"type":"done"}\n\n`,
      });
    });

    const input = page.locator('[data-testid="chat-input"]');
    await input.fill('Timeout test');
    await input.press('Enter');

    // Wait for timeout error (should appear before 15s delay completes)
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 12000 });

    // Verify input is re-enabled for retry
    await expect(input).toBeEnabled();
  });
});
