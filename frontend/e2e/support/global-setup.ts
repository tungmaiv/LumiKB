import { chromium, FullConfig } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const AUTH_FILE = path.resolve(__dirname, '../.auth/user.json');

async function globalSetup(config: FullConfig) {
  // Ensure .auth directory exists
  const authDir = path.dirname(AUTH_FILE);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  const baseURL = config.projects[0].use?.baseURL || 'http://localhost:3000';

  console.log(`Global setup: Authenticating against ${baseURL}`);

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Navigate to login
    await page.goto(`${baseURL}/login`);

    // Check if login page is available
    const emailInput = page.getByLabel(/email/i);
    const isLoginAvailable = await emailInput.isVisible({ timeout: 10000 }).catch(() => false);

    if (!isLoginAvailable) {
      console.log('Login page not available, skipping auth setup (app may not be running)');
      // Create empty auth state for tests that don't require auth
      await page.context().storageState({ path: AUTH_FILE });
      await browser.close();
      return;
    }

    // Perform login
    const testEmail = process.env.TEST_USER_EMAIL || 'test@example.com';
    const testPassword = process.env.TEST_USER_PASSWORD || 'testpassword123';

    await emailInput.fill(testEmail);
    await page.getByLabel(/password/i).fill(testPassword);
    await page.getByRole('button', { name: /sign in/i }).click();

    // Wait for successful login (redirect to dashboard)
    await page.waitForURL('**/dashboard', { timeout: 30000 });

    // Save authentication state
    await page.context().storageState({ path: AUTH_FILE });

    console.log('Authentication state saved successfully');
  } catch (error) {
    console.warn('Global setup auth failed (this is OK for unauthenticated tests):', error);
    // Create empty auth state so tests can still run
    await page.context().storageState({ path: AUTH_FILE });
  } finally {
    await browser.close();
  }
}

export default globalSetup;
