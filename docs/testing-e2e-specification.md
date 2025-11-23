# E2E Test Framework Specification

**Version:** 1.0
**Last Updated:** 2024-01-XX
**Status:** Active
**Applies To:** Full-stack end-to-end tests in `frontend/e2e/`

---

## 1. Overview

This document establishes the end-to-end (E2E) testing standards for LumiKB using Playwright. E2E tests validate complete user journeys through the actual running application, ensuring all system components work together correctly.

### 1.1 Core Principles

1. **User Journey Focus**: Test complete workflows, not individual components
2. **Real Environment**: Tests run against actual application (not mocks)
3. **Stability First**: Prefer slower, stable tests over fast, flaky ones
4. **Failure Evidence**: Capture screenshots, videos, traces on failure
5. **Cross-Browser**: Validate critical paths across multiple browsers

### 1.2 Tech Stack

| Tool | Purpose | Version |
|------|---------|---------|
| Playwright | E2E test framework | ^1.40.0 |
| @playwright/test | Test runner and assertions | ^1.40.0 |
| dotenv | Environment configuration | ^16.0.0 |

### 1.3 When to Use E2E Tests

| Use E2E For | Use Unit/Integration Instead |
|-------------|------------------------------|
| Authentication flows | Form validation logic |
| Multi-page workflows | Individual component behavior |
| Critical business paths | API contract testing |
| Cross-browser validation | Store/hook logic |
| Visual regression (optional) | Utility functions |

---

## 2. Directory Structure

```
frontend/
├── e2e/
│   ├── playwright.config.ts       # Main Playwright configuration
│   ├── config/
│   │   ├── base.config.ts         # Shared base configuration
│   │   ├── local.config.ts        # Local development config
│   │   └── staging.config.ts      # Staging environment config
│   ├── tests/
│   │   ├── auth/
│   │   │   ├── login.spec.ts
│   │   │   └── register.spec.ts
│   │   ├── documents/
│   │   │   ├── upload.spec.ts
│   │   │   └── search.spec.ts
│   │   └── settings/
│   │       └── profile.spec.ts
│   ├── pages/                     # Page Object Models
│   │   ├── base.page.ts
│   │   ├── login.page.ts
│   │   ├── dashboard.page.ts
│   │   └── documents.page.ts
│   ├── fixtures/
│   │   ├── auth.fixture.ts        # Authentication fixtures
│   │   └── test-data.fixture.ts   # Test data fixtures
│   ├── support/
│   │   ├── global-setup.ts        # Global setup (auth state)
│   │   └── global-teardown.ts     # Global cleanup
│   └── .auth/                     # Stored auth state (gitignored)
│       └── user.json
├── .env.example                   # Environment template
└── package.json
```

---

## 3. Installation

### 3.1 Install Dependencies

```bash
cd frontend
npm install -D @playwright/test dotenv
npx playwright install --with-deps
```

### 3.2 Package.json Scripts

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:report": "playwright show-report"
  }
}
```

---

## 4. Configuration

### 4.1 Main Configuration

**File**: `frontend/e2e/playwright.config.ts`

```typescript
import { config as dotenvConfig } from 'dotenv';
import path from 'path';

// Load environment variables
dotenvConfig({
  path: path.resolve(__dirname, '../.env'),
});

// Environment-based config loader
const envConfigMap = {
  local: require('./config/local.config').default,
  staging: require('./config/staging.config').default,
};

const environment = process.env.TEST_ENV || 'local';

// Fail fast if environment not supported
if (!Object.keys(envConfigMap).includes(environment)) {
  console.error(`No configuration found for environment: ${environment}`);
  console.error(`Available environments: ${Object.keys(envConfigMap).join(', ')}`);
  process.exit(1);
}

console.log(`Running E2E tests against: ${environment.toUpperCase()}`);

export default envConfigMap[environment as keyof typeof envConfigMap];
```

### 4.2 Base Configuration

**File**: `frontend/e2e/config/base.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';
import path from 'path';

export const baseConfig = defineConfig({
  testDir: path.resolve(__dirname, '../tests'),
  outputDir: path.resolve(__dirname, '../test-results'),

  // Execution settings
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // Timeouts (standardized)
  timeout: 60000,        // Test timeout: 60s
  expect: {
    timeout: 10000,      // Assertion timeout: 10s
  },

  use: {
    actionTimeout: 15000,      // Click, fill, etc.: 15s
    navigationTimeout: 30000,  // Page navigation: 30s

    // Artifacts
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  // Reporters
  reporter: [
    ['html', { outputFolder: '../playwright-report', open: 'never' }],
    ['junit', { outputFile: '../test-results/e2e-results.xml' }],
    ['list'],
  ],

  // Browser projects
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
});
```

### 4.3 Local Configuration

**File**: `frontend/e2e/config/local.config.ts`

```typescript
import { defineConfig } from '@playwright/test';
import { baseConfig } from './base.config';

export default defineConfig({
  ...baseConfig,
  use: {
    ...baseConfig.use,
    baseURL: 'http://localhost:3000',
    video: 'off', // No video locally for speed
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
  // Run only chromium locally for speed
  projects: [
    {
      name: 'chromium',
      use: { ...baseConfig.projects?.[0]?.use },
    },
  ],
});
```

### 4.4 Staging Configuration

**File**: `frontend/e2e/config/staging.config.ts`

```typescript
import { defineConfig } from '@playwright/test';
import { baseConfig } from './base.config';

export default defineConfig({
  ...baseConfig,
  use: {
    ...baseConfig.use,
    baseURL: process.env.STAGING_URL || 'https://staging.lumikb.example.com',
    ignoreHTTPSErrors: true,
  },
  // No webServer - staging is already running
});
```

---

## 5. Page Object Model

### 5.1 Base Page

**File**: `frontend/e2e/pages/base.page.ts`

```typescript
import { Page, Locator } from '@playwright/test';

export abstract class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  // Common navigation
  async goto(path: string = '/') {
    await this.page.goto(path);
  }

  // Common locators
  getByTestId(testId: string): Locator {
    return this.page.getByTestId(testId);
  }

  // Common actions
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  // Toast/notification helpers
  async getToastMessage(): Promise<string | null> {
    const toast = this.page.locator('[data-sonner-toast]').first();
    if (await toast.isVisible()) {
      return toast.textContent();
    }
    return null;
  }
}
```

### 5.2 Login Page

**File**: `frontend/e2e/pages/login.page.ts`

```typescript
import { Page, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class LoginPage extends BasePage {
  // Locators
  readonly emailInput = this.page.getByLabel(/email/i);
  readonly passwordInput = this.page.getByLabel(/password/i);
  readonly submitButton = this.page.getByRole('button', { name: /sign in/i });
  readonly registerLink = this.page.getByRole('link', { name: /create account/i });
  readonly errorMessage = this.page.getByRole('alert');

  constructor(page: Page) {
    super(page);
  }

  async goto() {
    await super.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message: string | RegExp) {
    await expect(this.errorMessage).toContainText(message);
  }

  async expectRedirectToDashboard() {
    await expect(this.page).toHaveURL(/.*dashboard/);
  }
}
```

### 5.3 Dashboard Page

**File**: `frontend/e2e/pages/dashboard.page.ts`

```typescript
import { Page, expect } from '@playwright/test';
import { BasePage } from './base.page';

export class DashboardPage extends BasePage {
  // Locators
  readonly welcomeMessage = this.page.getByRole('heading', { name: /welcome/i });
  readonly searchInput = this.page.getByPlaceholder(/search/i);
  readonly uploadButton = this.page.getByRole('button', { name: /upload/i });
  readonly userMenu = this.page.getByTestId('user-menu');

  constructor(page: Page) {
    super(page);
  }

  async goto() {
    await super.goto('/dashboard');
  }

  async search(query: string) {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
  }

  async openUserMenu() {
    await this.userMenu.click();
  }

  async logout() {
    await this.openUserMenu();
    await this.page.getByRole('menuitem', { name: /logout/i }).click();
  }

  async expectWelcomeVisible() {
    await expect(this.welcomeMessage).toBeVisible();
  }
}
```

---

## 6. Fixtures

### 6.1 Authentication Fixture

**File**: `frontend/e2e/fixtures/auth.fixture.ts`

```typescript
import { test as base, Page } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';
import path from 'path';

// Test user credentials (from environment)
const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'test@example.com',
  password: process.env.TEST_USER_PASSWORD || 'testpassword123',
};

// Extend base test with authenticated context
type AuthFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  authenticatedPage: Page;
};

export const test = base.extend<AuthFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  // Pre-authenticated page using stored state
  authenticatedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: path.resolve(__dirname, '../.auth/user.json'),
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect } from '@playwright/test';
export { TEST_USER };
```

### 6.2 Global Setup (Auth State)

**File**: `frontend/e2e/support/global-setup.ts`

```typescript
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

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Navigate to login
    await page.goto(`${baseURL}/login`);

    // Perform login
    await page.getByLabel(/email/i).fill(process.env.TEST_USER_EMAIL || 'test@example.com');
    await page.getByLabel(/password/i).fill(process.env.TEST_USER_PASSWORD || 'testpassword123');
    await page.getByRole('button', { name: /sign in/i }).click();

    // Wait for successful login
    await page.waitForURL('**/dashboard', { timeout: 30000 });

    // Save authentication state
    await page.context().storageState({ path: AUTH_FILE });

    console.log('Authentication state saved successfully');
  } catch (error) {
    console.error('Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
```

---

## 7. Test Patterns

### 7.1 Authentication Tests

**File**: `frontend/e2e/tests/auth/login.spec.ts`

```typescript
import { test, expect, TEST_USER } from '../../fixtures/auth.fixture';

test.describe('Login', () => {
  test.beforeEach(async ({ loginPage }) => {
    await loginPage.goto();
  });

  test('displays login form', async ({ loginPage }) => {
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.submitButton).toBeVisible();
  });

  test('shows error for invalid credentials', async ({ loginPage }) => {
    await loginPage.login('invalid@example.com', 'wrongpassword');
    await loginPage.expectError(/invalid credentials/i);
  });

  test('redirects to dashboard on successful login', async ({ loginPage }) => {
    await loginPage.login(TEST_USER.email, TEST_USER.password);
    await loginPage.expectRedirectToDashboard();
  });

  test('shows validation error for empty email', async ({ loginPage }) => {
    await loginPage.passwordInput.fill('password');
    await loginPage.submitButton.click();
    await expect(loginPage.page.getByText(/email is required/i)).toBeVisible();
  });
});
```

### 7.2 Authenticated User Tests

**File**: `frontend/e2e/tests/documents/search.spec.ts`

```typescript
import { test, expect } from '../../fixtures/auth.fixture';
import { DashboardPage } from '../../pages/dashboard.page';

test.describe('Document Search', () => {
  test.use({
    storageState: 'e2e/.auth/user.json', // Use authenticated state
  });

  test('can search documents from dashboard', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    await dashboard.search('meeting notes');

    // Verify search results appear
    await expect(page.getByTestId('search-results')).toBeVisible();
  });

  test('shows empty state for no results', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    await dashboard.search('xyznonexistent123');

    await expect(page.getByText(/no results found/i)).toBeVisible();
  });
});
```

### 7.3 Multi-Step Workflow Test

**File**: `frontend/e2e/tests/documents/upload.spec.ts`

```typescript
import { test, expect } from '../../fixtures/auth.fixture';
import path from 'path';

test.describe('Document Upload Workflow', () => {
  test.use({
    storageState: 'e2e/.auth/user.json',
  });

  test('complete document upload flow', async ({ page }) => {
    // Step 1: Navigate to upload
    await page.goto('/dashboard');
    await page.getByRole('button', { name: /upload/i }).click();

    // Step 2: Select file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(__dirname, '../fixtures/sample.pdf'));

    // Step 3: Fill metadata
    await page.getByLabel(/title/i).fill('Test Document');
    await page.getByLabel(/description/i).fill('Test description');

    // Step 4: Submit
    await page.getByRole('button', { name: /upload/i }).click();

    // Step 5: Verify success
    await expect(page.getByText(/upload successful/i)).toBeVisible();

    // Step 6: Verify document appears in list
    await page.goto('/dashboard');
    await expect(page.getByText('Test Document')).toBeVisible();
  });
});
```

---

## 8. Running Tests

### 8.1 Commands

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI mode (interactive)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run in debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test tests/auth/login.spec.ts

# Run specific project (browser)
npx playwright test --project=chromium

# Run against staging
TEST_ENV=staging npm run test:e2e

# View HTML report
npm run test:e2e:report
```

### 8.2 Makefile Integration

```makefile
test-e2e:
	cd frontend && npm run test:e2e

test-e2e-ui:
	cd frontend && npm run test:e2e:ui

test-e2e-headed:
	cd frontend && npm run test:e2e:headed
```

---

## 9. CI Integration

### 9.1 GitHub Actions Workflow

**File**: `.github/workflows/e2e.yml`

```yaml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  NODE_VERSION: "20"

jobs:
  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Install Playwright browsers
        run: cd frontend && npx playwright install --with-deps

      - name: Build application
        run: cd frontend && npm run build

      - name: Run E2E tests
        run: cd frontend && npm run test:e2e
        env:
          TEST_ENV: local
          TEST_USER_EMAIL: ${{ secrets.TEST_USER_EMAIL }}
          TEST_USER_PASSWORD: ${{ secrets.TEST_USER_PASSWORD }}

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-test-results
          path: frontend/test-results/
          retention-days: 30

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30
```

### 9.2 Sharded Execution (Large Test Suites)

```yaml
jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      # ... setup steps ...

      - name: Run E2E tests (shard ${{ matrix.shard }}/4)
        run: |
          cd frontend
          npx playwright test --shard=${{ matrix.shard }}/4

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: e2e-results-shard-${{ matrix.shard }}
          path: frontend/test-results/
```

---

## 10. Timeout Standards

| Timeout Type | Duration | Purpose |
|--------------|----------|---------|
| Test timeout | 60s | Maximum time for entire test |
| Action timeout | 15s | Click, fill, select operations |
| Navigation timeout | 30s | Page.goto, redirects |
| Expect timeout | 10s | Assertion waiting |

### 10.1 Overriding Timeouts

```typescript
// Per-test timeout
test('slow operation', async ({ page }) => {
  test.setTimeout(120000); // 2 minutes

  await page.goto('/heavy-page');
  // ... slow operations
});

// Per-assertion timeout
await expect(page.getByText('Processed')).toBeVisible({
  timeout: 30000, // 30s for slow API
});

// Per-action timeout
await page.click('[data-testid="submit"]', {
  timeout: 20000,
});
```

---

## 11. Best Practices

### 11.1 Do's

| Practice | Example |
|----------|---------|
| Use Page Objects | `await loginPage.login(email, password)` |
| Use data-testid for stability | `page.getByTestId('submit-btn')` |
| Wait for network idle | `await page.waitForLoadState('networkidle')` |
| Use meaningful test names | `test('user can upload PDF document')` |
| Isolate test data | Create unique data per test |
| Clean up after tests | Delete created resources |

### 11.2 Don'ts

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Hard waits | Flaky, slow | Use `waitFor`, `expect` |
| Shared mutable state | Test pollution | Isolate per test |
| CSS selectors | Brittle | Use `getByRole`, `getByTestId` |
| Testing implementation | Breaks on refactor | Test user behavior |
| Giant test files | Hard to maintain | Split by feature |
| Skipping retries in CI | Flaky failures | Use `retries: 2` |

### 11.3 Locator Priority

```typescript
// PREFERRED: Accessible queries
page.getByRole('button', { name: /submit/i });
page.getByLabel(/email address/i);
page.getByText(/welcome back/i);

// GOOD: Test IDs for complex elements
page.getByTestId('document-card-123');

// AVOID: CSS selectors (brittle)
page.locator('.btn-primary');
page.locator('#submit-form');
```

---

## 12. Debugging

### 12.1 Debug Mode

```bash
# Run single test in debug mode
npx playwright test tests/auth/login.spec.ts --debug

# Run with browser visible
npx playwright test --headed

# Run with slow motion
npx playwright test --headed --slow-mo=1000
```

### 12.2 Trace Viewer

```typescript
// Enable trace for specific test
test('debug this test', async ({ page }) => {
  await page.context().tracing.start({ screenshots: true, snapshots: true });

  // ... test steps ...

  await page.context().tracing.stop({ path: 'trace.zip' });
});
```

```bash
# View trace
npx playwright show-trace trace.zip
```

### 12.3 Screenshots in Test

```typescript
test('capture state', async ({ page }) => {
  await page.goto('/dashboard');

  // Capture screenshot
  await page.screenshot({ path: 'debug-screenshot.png', fullPage: true });

  // Continue test...
});
```

---

## 13. Visual Testing (Optional)

### 13.1 Screenshot Comparison

```typescript
test('visual regression', async ({ page }) => {
  await page.goto('/dashboard');

  // Compare against baseline
  await expect(page).toHaveScreenshot('dashboard.png', {
    maxDiffPixels: 100,
  });
});
```

### 13.2 Update Baselines

```bash
# Update all snapshots
npx playwright test --update-snapshots

# Update specific test snapshots
npx playwright test tests/visual.spec.ts --update-snapshots
```

---

## 14. Environment Variables

### 14.1 Required Variables

**File**: `frontend/.env.example`

```bash
# Test environment (local, staging)
TEST_ENV=local

# Test user credentials
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=testpassword123

# Staging URL (for staging tests)
STAGING_URL=https://staging.lumikb.example.com

# API URL (if different from app)
API_URL=http://localhost:8000
```

### 14.2 CI Secrets

Required GitHub secrets for CI:
- `TEST_USER_EMAIL`: Test user email
- `TEST_USER_PASSWORD`: Test user password

---

## 15. Checklist

### 15.1 Before Writing E2E Tests

- [ ] User story requires full journey validation
- [ ] Unit/integration tests cover individual components
- [ ] Test user credentials available
- [ ] Page Objects created for involved pages

### 15.2 Test Quality Checklist

- [ ] Test has descriptive name explaining user journey
- [ ] Uses Page Object Model (no raw selectors in tests)
- [ ] Uses accessible locators (role, label, text, testid)
- [ ] No hard waits (`waitForTimeout`)
- [ ] Handles loading states properly
- [ ] Cleans up created data (if applicable)
- [ ] Works in CI environment
- [ ] Timeout is appropriate (not too short/long)

---

## Appendix A: Quick Reference

### A.1 Common Locators

```typescript
// By role (most accessible)
page.getByRole('button', { name: /submit/i });
page.getByRole('link', { name: /home/i });
page.getByRole('textbox', { name: /email/i });
page.getByRole('checkbox', { name: /agree/i });

// By label
page.getByLabel(/email address/i);

// By placeholder
page.getByPlaceholder(/search/i);

// By text
page.getByText(/welcome/i);

// By test ID
page.getByTestId('submit-button');
```

### A.2 Common Assertions

```typescript
// Visibility
await expect(element).toBeVisible();
await expect(element).toBeHidden();

// Text content
await expect(element).toHaveText('Hello');
await expect(element).toContainText('Hello');

// Attributes
await expect(element).toHaveAttribute('disabled');
await expect(input).toHaveValue('test@example.com');

// URL
await expect(page).toHaveURL(/.*dashboard/);

// Count
await expect(page.getByTestId('item')).toHaveCount(5);
```

### A.3 Common Actions

```typescript
// Navigation
await page.goto('/dashboard');
await page.goBack();
await page.reload();

// Clicks
await element.click();
await element.dblclick();

// Input
await input.fill('text');
await input.clear();
await input.press('Enter');

// Select
await select.selectOption('value');
await select.selectOption({ label: 'Option' });

// File upload
await fileInput.setInputFiles('path/to/file.pdf');

// Keyboard
await page.keyboard.press('Escape');
await page.keyboard.type('Hello');
```

---

**Document End**
