import { test as base, Page } from '@playwright/test';
import { LoginPage, DashboardPage, RegisterPage } from '../pages';
import path from 'path';

// Test user credentials (from environment or defaults)
export const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'test@example.com',
  password: process.env.TEST_USER_PASSWORD || 'testpassword123',
  name: process.env.TEST_USER_NAME || 'Test User',
};

// Auth state file path
export const AUTH_FILE = path.resolve(__dirname, '../.auth/user.json');

// Extend base test with page objects
type AuthFixtures = {
  loginPage: LoginPage;
  registerPage: RegisterPage;
  dashboardPage: DashboardPage;
  authenticatedPage: Page;
};

export const test = base.extend<AuthFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  registerPage: async ({ page }, use) => {
    await use(new RegisterPage(page));
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  // Pre-authenticated page using stored state
  authenticatedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: AUTH_FILE,
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect } from '@playwright/test';
