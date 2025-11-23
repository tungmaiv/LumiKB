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
