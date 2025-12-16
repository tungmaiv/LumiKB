import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  /* config options here */
  // Enable standalone output for Docker deployment
  // This creates a self-contained build with all dependencies
  output: 'standalone',
};

export default nextConfig;
