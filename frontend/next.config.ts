import path from 'node:path'
import type { NextConfig } from 'next'

const backendBaseUrl = process.env.FASTAPI_BASE_URL ?? 'http://127.0.0.1:8000'

const nextConfig: NextConfig = {
  allowedDevOrigins: ['127.0.0.1'],
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendBaseUrl}/api/:path*`,
      },
      {
        source: '/health',
        destination: `${backendBaseUrl}/health`,
      },
    ]
  },
  experimental: {
    serverComponentsHmrCache: false,
  },
  turbopack: {
    root: path.resolve(__dirname),
  },
}

export default nextConfig
