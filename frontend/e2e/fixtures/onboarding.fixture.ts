/**
 * Onboarding Test Fixtures
 *
 * Provides reusable fixtures for onboarding wizard E2E tests:
 * - newUser: User with onboarding_completed = false
 * - completedUser: User with onboarding_completed = true
 * - Mock API responses for user state
 *
 * Usage:
 *   import { test, expect } from '../fixtures/onboarding.fixture';
 *
 *   test('should show wizard for new user', async ({ page, newUser }) => {
 *     await page.goto('/dashboard');
 *     // Wizard automatically appears for newUser
 *   });
 */

import { test as base, Page } from '@playwright/test';

/**
 * User factory for onboarding tests
 * Creates user objects with configurable onboarding state
 */
export const createUser = (overrides: Partial<UserState> = {}): UserState => ({
  id: 1,
  email: 'testuser@example.com',
  is_active: true,
  onboarding_completed: false,
  last_active: null,
  created_at: new Date().toISOString(),
  ...overrides,
});

/**
 * User state interface matching backend UserRead schema
 */
interface UserState {
  id: number;
  email: string;
  is_active: boolean;
  onboarding_completed: boolean;
  last_active: string | null;
  created_at: string;
}

/**
 * Onboarding fixtures for E2E tests
 */
type OnboardingFixtures = {
  /**
   * New user (onboarding_completed = false)
   * Automatically mocks GET /api/v1/users/me to return new user state
   */
  newUser: UserState;

  /**
   * Completed user (onboarding_completed = true)
   * Automatically mocks GET /api/v1/users/me to return completed state
   */
  completedUser: UserState;

  /**
   * Mock onboarding completion API (PUT /api/v1/users/me/onboarding)
   * Returns updated user with onboarding_completed = true
   */
  mockOnboardingComplete: (page: Page) => Promise<void>;

  /**
   * Mock onboarding API failure (500 error)
   * Used for error scenario testing
   */
  mockOnboardingError: (page: Page) => Promise<void>;
};

/**
 * Extend Playwright test with onboarding fixtures
 */
export const test = base.extend<OnboardingFixtures>({
  /**
   * Fixture: newUser
   * Automatically mocks API to return new user (onboarding_completed = false)
   */
  newUser: async ({ page }, use) => {
    const user = createUser({ onboarding_completed: false });

    // Mock GET /api/v1/users/me to return new user
    await page.route('**/api/v1/users/me', async (route) => {
      // Only intercept GET requests
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(user),
        });
      } else {
        // Allow other methods (PUT) to pass through or be mocked separately
        await route.continue();
      }
    });

    await use(user);

    // Cleanup: Remove route intercept
    await page.unroute('**/api/v1/users/me');
  },

  /**
   * Fixture: completedUser
   * Automatically mocks API to return completed user (onboarding_completed = true)
   */
  completedUser: async ({ page }, use) => {
    const user = createUser({ onboarding_completed: true });

    // Mock GET /api/v1/users/me to return completed user
    await page.route('**/api/v1/users/me', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(user),
        });
      } else {
        await route.continue();
      }
    });

    await use(user);

    // Cleanup
    await page.unroute('**/api/v1/users/me');
  },

  /**
   * Fixture: mockOnboardingComplete
   * Helper to mock successful onboarding completion API call
   */
  mockOnboardingComplete: async ({ page }, use) => {
    const mockFn = async (page: Page) => {
      await page.route('**/api/v1/users/me/onboarding', async (route) => {
        if (route.request().method() === 'PUT') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 1,
              email: 'testuser@example.com',
              is_active: true,
              onboarding_completed: true, // Updated to true
              last_active: null,
              created_at: new Date().toISOString(),
            }),
          });
        } else {
          await route.continue();
        }
      });
    };

    await use(mockFn);

    // Cleanup: Remove route intercept
    await page.unroute('**/api/v1/users/me/onboarding');
  },

  /**
   * Fixture: mockOnboardingError
   * Helper to mock failed onboarding completion API call (500 error)
   */
  mockOnboardingError: async ({ page }, use) => {
    const mockFn = async (page: Page) => {
      await page.route('**/api/v1/users/me/onboarding', async (route) => {
        if (route.request().method() === 'PUT') {
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({
              detail: 'Internal server error',
            }),
          });
        } else {
          await route.continue();
        }
      });
    };

    await use(mockFn);

    // Cleanup
    await page.unroute('**/api/v1/users/me/onboarding');
  },
});

export { expect } from '@playwright/test';

/**
 * Wizard step content expectations
 * Reusable assertions for each wizard step
 */
export const wizardSteps = {
  step1: {
    title: 'Welcome to LumiKB!',
    subtitle: /AI-powered knowledge management/i,
    stepIndicator: 'Step 1 of 5',
  },
  step2: {
    title: 'Explore the Sample Knowledge Base',
    stepIndicator: 'Step 2 of 5',
  },
  step3: {
    title: 'Ask Your First Question',
    stepIndicator: 'Step 3 of 5',
  },
  step4: {
    title: 'Citations Build Trust',
    stepIndicator: 'Step 4 of 5',
  },
  step5: {
    title: "You're All Set!",
    stepIndicator: 'Step 5 of 5',
  },
};

/**
 * Helper function: Navigate to specific wizard step
 * Clicks "Next" button N times to reach target step
 */
export const navigateToStep = async (page: Page, targetStep: number) => {
  if (targetStep < 1 || targetStep > 5) {
    throw new Error(`Invalid step number: ${targetStep}. Must be between 1 and 5.`);
  }

  const clicksNeeded = targetStep - 1; // Step 1 = 0 clicks, Step 2 = 1 click, etc.

  for (let i = 0; i < clicksNeeded; i++) {
    await page.getByRole('button', { name: /next/i }).click();
    await page.waitForTimeout(150); // Allow for step transition animation
  }
};

/**
 * Helper function: Complete full wizard flow
 * Navigates through all 5 steps and clicks "Start Exploring"
 */
export const completeWizard = async (page: Page) => {
  // Navigate through Steps 1-4
  await navigateToStep(page, 5);

  // Click "Start Exploring" on Step 5
  await page.getByRole('button', { name: /start exploring/i }).click();
};

/**
 * Helper function: Skip wizard with confirmation
 * Clicks "Skip Tutorial" and confirms in dialog
 */
export const skipWizard = async (page: Page) => {
  // Click "Skip Tutorial" link
  await page.getByText('Skip Tutorial').click();

  // Wait for confirmation dialog
  await page.waitForSelector('text=Skip Tutorial?', { state: 'visible' });

  // Click "Skip" button in confirmation dialog
  const skipButtons = page.getByRole('button', { name: /skip/i });
  await skipButtons.last().click(); // Last button is confirmation "Skip"
};
