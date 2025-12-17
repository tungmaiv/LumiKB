/**
 * Error Scenarios Fixture
 * Story 5-0 Automation: Negative path testing infrastructure
 *
 * Provides utilities for mocking API errors, network failures, and edge cases
 * Knowledge Base References:
 * - network-first.md: Route interception patterns
 * - test-quality.md: Deterministic error simulation
 */

import { test as base, Page, Route } from '@playwright/test';

/**
 * Common error responses for API testing
 */
export const ERROR_RESPONSES = {
  INTERNAL_SERVER_ERROR: {
    status: 500,
    body: { detail: 'Internal server error' },
  },
  UNAUTHORIZED: {
    status: 401,
    body: { detail: 'Unauthorized' },
  },
  FORBIDDEN: {
    status: 403,
    body: { detail: 'Forbidden' },
  },
  NOT_FOUND: {
    status: 404,
    body: { detail: 'Not found' },
  },
  BAD_REQUEST: {
    status: 400,
    body: { detail: 'Bad request' },
  },
  NETWORK_TIMEOUT: {
    status: 0,
    body: null,
  },
  MALFORMED_JSON: {
    status: 200,
    body: 'not valid json{{{',
  },
};

type ErrorScenarioFixtures = {
  /**
   * Mock API endpoint to return error response
   * @example
   * await mockApiError(page, '/api/v1/search', ERROR_RESPONSES.INTERNAL_SERVER_ERROR);
   */
  mockApiError: (
    page: Page,
    urlPattern: string | RegExp,
    errorResponse: (typeof ERROR_RESPONSES)[keyof typeof ERROR_RESPONSES]
  ) => Promise<void>;

  /**
   * Mock API endpoint to timeout
   * @example
   * await mockNetworkTimeout(page, '/api/v1/chat/stream');
   */
  mockNetworkTimeout: (
    page: Page,
    urlPattern: string | RegExp,
    timeoutMs?: number
  ) => Promise<void>;

  /**
   * Mock API endpoint to return malformed response
   * @example
   * await mockMalformedResponse(page, '/api/v1/search', 'invalid json');
   */
  mockMalformedResponse: (
    page: Page,
    urlPattern: string | RegExp,
    responseBody: string
  ) => Promise<void>;

  /**
   * Mock slow network (delay all requests)
   * @example
   * await mockSlowNetwork(page, 3000); // 3 second delay
   */
  mockSlowNetwork: (page: Page, delayMs: number) => Promise<void>;
};

export const test = base.extend<ErrorScenarioFixtures>({
  mockApiError: async ({}, use) => {
    await use(async (page: Page, urlPattern: string | RegExp, errorResponse) => {
      await page.route(urlPattern, async (route: Route) => {
        if (errorResponse.status === 0) {
          // Simulate network failure (no response)
          await route.abort('failed');
        } else {
          await route.fulfill({
            status: errorResponse.status,
            contentType: 'application/json',
            body:
              typeof errorResponse.body === 'string'
                ? errorResponse.body
                : JSON.stringify(errorResponse.body),
          });
        }
      });
    });
  },

  mockNetworkTimeout: async ({}, use) => {
    await use(async (page: Page, urlPattern: string | RegExp, timeoutMs = 30000) => {
      await page.route(urlPattern, async (route: Route) => {
        // Delay longer than Playwright's default timeout to simulate timeout
        await new Promise((resolve) => setTimeout(resolve, timeoutMs));
        await route.abort('timedout');
      });
    });
  },

  mockMalformedResponse: async ({}, use) => {
    await use(async (page: Page, urlPattern: string | RegExp, responseBody: string) => {
      await page.route(urlPattern, async (route: Route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: responseBody,
        });
      });
    });
  },

  mockSlowNetwork: async ({}, use) => {
    await use(async (page: Page, delayMs: number) => {
      await page.route('**/*', async (route: Route) => {
        await new Promise((resolve) => setTimeout(resolve, delayMs));
        await route.continue();
      });
    });
  },
});

export { expect } from '@playwright/test';
