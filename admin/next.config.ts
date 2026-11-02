import type { NextConfig } from 'next';
const config: NextConfig = { poweredByHeader: false, allowedDevOrigins: ['127.0.0.1'], distDir: process.env.NEXT_DIST_DIR || '.next' };
export default config;
