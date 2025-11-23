import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('Global teardown: Cleaning up test resources');
  // Add any cleanup logic here if needed
  // For example: delete test data, close connections, etc.
}

export default globalTeardown;
