/**
 * Test Helpers and Utilities
 * Story 5-0 Automation: Common utilities for E2E tests
 *
 * Knowledge Base References:
 * - network-first.md: Network interception patterns
 * - test-quality.md: Deterministic waits and assertions
 */

import { Page, expect, Response } from '@playwright/test';

/**
 * Wait for SSE (Server-Sent Events) streaming to complete
 * Used for chat and generation streaming endpoints
 *
 * @param page - Playwright page instance
 * @param endpoint - SSE endpoint URL pattern (e.g., '/api/v1/chat/stream')
 * @param timeout - Maximum wait time in ms (default: 30000)
 */
export async function waitForStreamingComplete(
  page: Page,
  endpoint: string | RegExp,
  timeout = 30000
): Promise<void> {
  // Wait for SSE connection to establish
  const responsePromise = page.waitForResponse(
    (resp) => {
      const url = resp.url();
      const matchesEndpoint = typeof endpoint === 'string'
        ? url.includes(endpoint)
        : endpoint.test(url);
      return matchesEndpoint && resp.status() === 200;
    },
    { timeout }
  );

  await responsePromise;

  // Wait additional time for streaming to complete
  // Look for UI indicators (e.g., send button re-enabled)
  await page.waitForTimeout(500); // Small buffer for UI update
}

/**
 * Mock API response with specific data
 * Network-first pattern: Set up route BEFORE navigation
 *
 * @param page - Playwright page instance
 * @param urlPattern - URL pattern to intercept
 * @param responseData - Response body (will be JSON stringified)
 * @param status - HTTP status code (default: 200)
 */
export async function mockApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  responseData: unknown,
  status = 200
): Promise<void> {
  await page.route(urlPattern, async (route) => {
    await route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(responseData),
    });
  });
}

/**
 * Wait for element to be visible with custom error message
 *
 * @param page - Playwright page instance
 * @param selector - Element selector
 * @param errorMessage - Custom error message if element not found
 * @param timeout - Maximum wait time in ms (default: 10000)
 */
export async function waitForElement(
  page: Page,
  selector: string,
  errorMessage: string,
  timeout = 10000
): Promise<void> {
  const element = page.locator(selector);
  try {
    await expect(element).toBeVisible({ timeout });
  } catch (error) {
    throw new Error(`${errorMessage} (selector: ${selector})`);
  }
}

/**
 * Clear local storage and cookies (reset state between tests)
 *
 * @param page - Playwright page instance
 */
export async function clearBrowserState(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.context().clearCookies();
}

/**
 * Get text content from multiple elements
 *
 * @param page - Playwright page instance
 * @param selector - Element selector
 * @returns Array of text content from matching elements
 */
export async function getTextFromElements(
  page: Page,
  selector: string
): Promise<string[]> {
  const elements = await page.locator(selector).all();
  const texts: string[] = [];

  for (const element of elements) {
    const text = await element.textContent();
    if (text) {
      texts.push(text.trim());
    }
  }

  return texts;
}

/**
 * Wait for network idle (all pending requests complete)
 * Useful after dynamic actions that trigger multiple requests
 *
 * @param page - Playwright page instance
 * @param timeout - Maximum wait time in ms (default: 10000)
 */
export async function waitForNetworkIdle(
  page: Page,
  timeout = 10000
): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Intercept and verify API request body
 * Returns the request body for assertions
 *
 * @param page - Playwright page instance
 * @param urlPattern - URL pattern to intercept
 * @returns Promise that resolves with request body
 */
export async function interceptAndGetRequestBody<T = unknown>(
  page: Page,
  urlPattern: string | RegExp
): Promise<T> {
  return new Promise((resolve) => {
    page.route(urlPattern, async (route) => {
      const request = route.request();
      const body = request.postDataJSON();
      resolve(body as T);
      await route.continue();
    });
  });
}

/**
 * Take screenshot with custom name for debugging
 *
 * @param page - Playwright page instance
 * @param name - Screenshot name (without extension)
 */
export async function takeDebugScreenshot(
  page: Page,
  name: string
): Promise<void> {
  await page.screenshot({
    path: `frontend/e2e/test-results/${name}-${Date.now()}.png`,
    fullPage: true,
  });
}

/**
 * Verify toast notification appears
 *
 * @param page - Playwright page instance
 * @param message - Expected toast message (partial match)
 * @param timeout - Maximum wait time in ms (default: 5000)
 */
export async function expectToast(
  page: Page,
  message: string | RegExp,
  timeout = 5000
): Promise<void> {
  const toast = page.locator('[data-sonner-toast]').first();
  await expect(toast).toBeVisible({ timeout });

  if (typeof message === 'string') {
    await expect(toast).toContainText(message);
  } else {
    const text = await toast.textContent();
    expect(text).toMatch(message);
  }
}

/**
 * Wait for URL to match pattern (navigation complete)
 *
 * @param page - Playwright page instance
 * @param urlPattern - Expected URL pattern
 * @param timeout - Maximum wait time in ms (default: 10000)
 */
export async function waitForNavigation(
  page: Page,
  urlPattern: string | RegExp,
  timeout = 10000
): Promise<void> {
  await page.waitForURL(urlPattern, { timeout });
}

/**
 * Retry action until success or max attempts
 * Useful for flaky operations like network requests
 *
 * @param action - Async action to retry
 * @param maxAttempts - Maximum retry attempts (default: 3)
 * @param delayMs - Delay between retries in ms (default: 1000)
 */
export async function retryUntilSuccess<T>(
  action: () => Promise<T>,
  maxAttempts = 3,
  delayMs = 1000
): Promise<T> {
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await action();
    } catch (error) {
      lastError = error as Error;
      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    }
  }

  throw new Error(
    `Action failed after ${maxAttempts} attempts. Last error: ${lastError?.message}`
  );
}

/**
 * Generate unique test data identifier
 * Prevents test data collisions in parallel execution
 *
 * @param prefix - Prefix for identifier (e.g., 'test-kb')
 * @returns Unique identifier string
 */
export function generateTestId(prefix: string): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  return `${prefix}-${timestamp}-${random}`;
}

/**
 * Verify element count matches expected
 *
 * @param page - Playwright page instance
 * @param selector - Element selector
 * @param expectedCount - Expected number of elements
 */
export async function expectElementCount(
  page: Page,
  selector: string,
  expectedCount: number
): Promise<void> {
  const elements = page.locator(selector);
  await expect(elements).toHaveCount(expectedCount);
}

/**
 * Wait for specific network response and return data
 *
 * @param page - Playwright page instance
 * @param urlPattern - URL pattern to wait for
 * @param timeout - Maximum wait time in ms (default: 10000)
 * @returns Response JSON data
 */
export async function waitForApiResponse<T = unknown>(
  page: Page,
  urlPattern: string | RegExp,
  timeout = 10000
): Promise<T> {
  const response = await page.waitForResponse(
    (resp) => {
      const url = resp.url();
      const matchesUrl = typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url);
      return matchesUrl && resp.status() === 200;
    },
    { timeout }
  );

  return response.json() as Promise<T>;
}
