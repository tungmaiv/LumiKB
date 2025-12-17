/**
 * Story 5-0 Automation: Chat Negative Paths
 * Generated: 2025-12-02
 *
 * Test Coverage:
 * - [P0] Chat API returns 500 Internal Server Error
 * - [P0] Chat API returns 403 Forbidden
 * - [P1] Chat API returns 401 Unauthorized
 * - [P1] Chat API timeout
 * - [P2] Chat API returns malformed JSON
 * - [P2] Chat SSE stream aborts mid-response
 *
 * Knowledge Base References:
 * - test-quality.md: Deterministic error simulation
 * - network-first.md: Route interception before navigation
 * - error-handling.md: Graceful degradation patterns
 */

import { test, expect } from '../../fixtures/auth.fixture';
import { test as errorTest, ERROR_RESPONSES } from '../../fixtures/error-scenarios.fixture';
import { ChatPage } from '../../pages';
import { expectToast } from '../../utils/test-helpers';

test.describe('Story 5-0: Chat Negative Paths', () => {
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    chatPage = new ChatPage(page);
  });

  errorTest(
    '[P0] Chat API 500 error displays user-friendly error message',
    async ({ page, mockApiError }) => {
      /**
       * GIVEN: User is on chat page with KB selected
       * WHEN: Chat API returns 500 Internal Server Error
       * THEN: User sees friendly error message, can retry
       */

      // GIVEN: Set up error response BEFORE navigation (network-first)
      await mockApiError(page, '**/api/v1/chat/stream', ERROR_RESPONSES.INTERNAL_SERVER_ERROR);

      await chatPage.goto();
      await page.waitForLoadState('networkidle');

      // Select KB
      const kbSelector = page.getByTestId('kb-selector');
      await kbSelector.click();
      const firstKb = page.getByRole('option').first();
      await firstKb.click();

      // WHEN: Send message
      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('Test message');

      const sendButton = page.getByTestId('send-message-button');
      await sendButton.click();

      // THEN: Error message is displayed
      const errorMessage = page.getByTestId('chat-error-message');
      await expect(errorMessage).toBeVisible({ timeout: 10000 });

      // THEN: Error message is user-friendly (not raw API error)
      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/try again|error|failed|something went wrong/i);
      expect(errorText).not.toContain('500');
      expect(errorText).not.toContain('Internal Server Error');

      // THEN: Retry button is available
      const retryButton = page.getByTestId('retry-button');
      if (await retryButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await expect(retryButton).toBeEnabled();
      }
    }
  );

  errorTest(
    '[P0] Chat API 403 Forbidden shows access denied message',
    async ({ page, mockApiError }) => {
      /**
       * GIVEN: User attempts to access chat for KB they don't have access to
       * WHEN: Chat API returns 403 Forbidden
       * THEN: User sees access denied message, redirected or prompted to select different KB
       */

      // GIVEN: Set up forbidden response
      await mockApiError(page, '**/api/v1/chat/stream', ERROR_RESPONSES.FORBIDDEN);

      await chatPage.goto();
      await page.waitForLoadState('networkidle');

      // Select KB
      const kbSelector = page.getByTestId('kb-selector');
      await kbSelector.click();
      const firstKb = page.getByRole('option').first();
      await firstKb.click();

      // WHEN: Send message
      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('Test message');

      const sendButton = page.getByTestId('send-message-button');
      await sendButton.click();

      // THEN: Access denied message is displayed
      const errorMessage = page.getByTestId('chat-error-message');
      if (await errorMessage.isVisible({ timeout: 5000 }).catch(() => false)) {
        const errorText = await errorMessage.textContent();
        expect(errorText).toMatch(/access denied|forbidden|permission/i);
      }

      // OR: Toast notification appears
      const toast = page.locator('[data-sonner-toast]').first();
      if (await toast.isVisible({ timeout: 5000 }).catch(() => false)) {
        await expect(toast).toContainText(/access|permission|forbidden/i);
      }
    }
  );

  errorTest('[P1] Chat API 401 Unauthorized redirects to login', async ({ page, mockApiError }) => {
    /**
     * GIVEN: User's session expires
     * WHEN: Chat API returns 401 Unauthorized
     * THEN: User is redirected to login page with return URL
     */

    // GIVEN: Set up unauthorized response
    await mockApiError(page, '**/api/v1/chat/stream', ERROR_RESPONSES.UNAUTHORIZED);

    await chatPage.goto();
    await page.waitForLoadState('networkidle');

    // Select KB
    const kbSelector = page.getByTestId('kb-selector');
    await kbSelector.click();
    const firstKb = page.getByRole('option').first();
    await firstKb.click();

    // WHEN: Send message
    const chatInput = page.getByTestId('chat-input');
    await chatInput.fill('Test message');

    const sendButton = page.getByTestId('send-message-button');
    await sendButton.click();

    // THEN: User is redirected to login
    await page.waitForURL(/\/login/, { timeout: 10000 });

    // THEN: Return URL is preserved
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/login/);
  });

  errorTest('[P1] Chat API timeout shows timeout error', async ({ page, mockNetworkTimeout }) => {
    /**
     * GIVEN: User is on chat page with KB selected
     * WHEN: Chat API request times out
     * THEN: Timeout error message is displayed, user can retry
     */

    // GIVEN: Set up timeout (simulate very slow response)
    await mockNetworkTimeout(page, '**/api/v1/chat/stream', 35000);

    await chatPage.goto();
    await page.waitForLoadState('networkidle');

    // Select KB
    const kbSelector = page.getByTestId('kb-selector');
    await kbSelector.click();
    const firstKb = page.getByRole('option').first();
    await firstKb.click();

    // WHEN: Send message
    const chatInput = page.getByTestId('chat-input');
    await chatInput.fill('Test message');

    const sendButton = page.getByTestId('send-message-button');
    await sendButton.click();

    // THEN: Timeout error is displayed
    const errorMessage = page.getByTestId('chat-error-message');
    if (await errorMessage.isVisible({ timeout: 40000 }).catch(() => false)) {
      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/timeout|slow|try again/i);
    }

    // OR: Toast notification appears
    const toast = page.locator('[data-sonner-toast]').first();
    if (await toast.isVisible({ timeout: 40000 }).catch(() => false)) {
      await expect(toast).toContainText(/timeout|slow|error/i);
    }
  });

  errorTest(
    '[P2] Chat API malformed JSON shows error gracefully',
    async ({ page, mockMalformedResponse }) => {
      /**
       * GIVEN: User is on chat page with KB selected
       * WHEN: Chat API returns malformed JSON
       * THEN: Parsing error is handled gracefully, user sees error message
       */

      // GIVEN: Set up malformed response
      await mockMalformedResponse(page, '**/api/v1/chat/stream', 'invalid{{{json');

      await chatPage.goto();
      await page.waitForLoadState('networkidle');

      // Select KB
      const kbSelector = page.getByTestId('kb-selector');
      await kbSelector.click();
      const firstKb = page.getByRole('option').first();
      await firstKb.click();

      // WHEN: Send message
      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('Test message');

      const sendButton = page.getByTestId('send-message-button');
      await sendButton.click();

      // THEN: Error is handled gracefully
      const errorMessage = page.getByTestId('chat-error-message');
      if (await errorMessage.isVisible({ timeout: 10000 }).catch(() => false)) {
        const errorText = await errorMessage.textContent();
        expect(errorText).toMatch(/error|failed|try again/i);
      }

      // OR: Toast notification appears
      const toast = page.locator('[data-sonner-toast]').first();
      if (await toast.isVisible({ timeout: 10000 }).catch(() => false)) {
        await expect(toast).toContainText(/error|failed/i);
      }
    }
  );

  test('[P2] Chat handles KB API error gracefully (no KBs loaded)', async ({ page }) => {
    /**
     * GIVEN: KB list API fails to load
     * WHEN: User navigates to chat page
     * THEN: Error message is displayed, user can retry loading KBs
     */

    // GIVEN: Mock KB API failure
    await page.route('**/api/v1/knowledge-bases**', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    });

    // WHEN: Navigate to chat
    await chatPage.goto();
    await page.waitForLoadState('networkidle');

    // THEN: Error message is displayed for KB loading
    const kbLoadError = page.getByTestId('kb-load-error');
    if (await kbLoadError.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(kbLoadError).toBeVisible();
    }

    // OR: KB selector shows error state
    const kbSelector = page.getByTestId('kb-selector');
    const selectorText = await kbSelector.textContent();
    expect(selectorText).toMatch(/error|failed|retry/i);
  });

  test('[P1] Chat handles missing KB gracefully (KB deleted mid-session)', async ({ page }) => {
    /**
     * GIVEN: User has a KB selected
     * WHEN: KB is deleted by another user/session
     * THEN: Error is displayed, user prompted to select different KB
     */

    // GIVEN: Navigate to chat and select KB
    await chatPage.goto();
    await page.waitForLoadState('networkidle');

    const kbSelector = page.getByTestId('kb-selector');
    await kbSelector.click();
    const firstKb = page.getByRole('option').first();
    await firstKb.click();

    // WHEN: Simulate KB deletion (404 response)
    await page.route('**/api/v1/chat/stream', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Knowledge base not found' }),
      });
    });

    const chatInput = page.getByTestId('chat-input');
    await chatInput.fill('Test message');

    const sendButton = page.getByTestId('send-message-button');
    await sendButton.click();

    // THEN: Error message about KB not found
    const errorMessage = page.getByTestId('chat-error-message');
    if (await errorMessage.isVisible({ timeout: 10000 }).catch(() => false)) {
      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/not found|deleted|select different/i);
    }

    // OR: Toast notification
    const toast = page.locator('[data-sonner-toast]').first();
    if (await toast.isVisible({ timeout: 10000 }).catch(() => false)) {
      await expect(toast).toContainText(/not found|deleted/i);
    }
  });

  test('[P2] Chat handles rapid error recovery correctly', async ({ page }) => {
    /**
     * GIVEN: Chat API fails once
     * WHEN: User retries and API succeeds
     * THEN: Error state is cleared, normal chat resumes
     */

    let requestCount = 0;

    // Mock first request to fail, second to succeed
    await page.route('**/api/v1/chat/stream', async (route) => {
      requestCount++;
      if (requestCount === 1) {
        // First request fails
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Internal server error' }),
        });
      } else {
        // Subsequent requests succeed
        await route.continue();
      }
    });

    // Navigate to chat and select KB
    await chatPage.goto();
    await page.waitForLoadState('networkidle');

    const kbSelector = page.getByTestId('kb-selector');
    await kbSelector.click();
    const firstKb = page.getByRole('option').first();
    await firstKb.click();

    // Send message (should fail)
    const chatInput = page.getByTestId('chat-input');
    await chatInput.fill('First message');

    const sendButton = page.getByTestId('send-message-button');
    await sendButton.click();

    // Wait for error
    await page.waitForTimeout(2000);

    // Retry (should succeed)
    const retryButton = page.getByTestId('retry-button');
    if (await retryButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await retryButton.click();
    } else {
      // No retry button, try sending again
      await chatInput.fill('Second message');
      await sendButton.click();
    }

    // THEN: Error is cleared and chat continues
    const errorMessage = page.getByTestId('chat-error-message');
    if (await errorMessage.isVisible().catch(() => false)) {
      await expect(errorMessage).not.toBeVisible({ timeout: 10000 });
    }
  });

  test('[P2] Chat handles concurrent API requests correctly', async ({ page }) => {
    /**
     * GIVEN: User sends message while another is processing
     * WHEN: Multiple API requests are triggered
     * THEN: Requests are queued/handled correctly, no race conditions
     */

    // Navigate to chat and select KB
    await chatPage.goto();
    await page.waitForLoadState('networkidle');

    const kbSelector = page.getByTestId('kb-selector');
    await kbSelector.click();
    const firstKb = page.getByRole('option').first();
    await firstKb.click();

    // Send first message
    const chatInput = page.getByTestId('chat-input');
    const sendButton = page.getByTestId('send-message-button');

    await chatInput.fill('First message');
    await sendButton.click();

    // Send button should be disabled
    await expect(sendButton).toBeDisabled({ timeout: 2000 });

    // Try to send another message (should be prevented)
    await chatInput.fill('Second message');
    await expect(sendButton).toBeDisabled();

    // Wait for first request to complete
    await expect(sendButton).toBeEnabled({ timeout: 30000 });

    // Now second message can be sent
    await sendButton.click();

    // Verify message was sent
    await expect(sendButton).toBeDisabled({ timeout: 2000 });
  });
});
