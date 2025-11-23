import { defineConfig, devices } from '@playwright/test';
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
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
