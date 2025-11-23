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
  timeout: 60000, // Test timeout: 60s
  expect: {
    timeout: 10000, // Assertion timeout: 10s
  },

  use: {
    actionTimeout: 15000, // Click, fill, etc.: 15s
    navigationTimeout: 30000, // Page navigation: 30s

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
