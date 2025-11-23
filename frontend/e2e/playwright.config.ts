import { config as dotenvConfig } from 'dotenv';
import path from 'path';

// Load environment variables
dotenvConfig({
  path: path.resolve(__dirname, '../.env'),
});

// Environment-based config loader
const envConfigMap: Record<string, unknown> = {
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

export default envConfigMap[environment];
