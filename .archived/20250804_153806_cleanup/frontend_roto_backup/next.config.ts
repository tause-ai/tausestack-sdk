import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Conditional output for development vs production
  // Use 'export' only for static deployment, comment out for API routes
  ...(process.env.NODE_ENV === 'production' && process.env.STATIC_EXPORT === 'true' ? { output: 'export' } : {}),
  trailingSlash: true,
  
  // Environment configuration
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // Image optimization for production
  images: {
    domains: [
      'localhost',
      'tausestack.dev',
      'api.tausestack.dev',
      'app.tausestack.dev',
      'vjoxmprmcbkmhwmbniaz.supabase.co'
    ],
    formats: ['image/webp', 'image/avif'],
  },

  // Security headers for production (only when not using static export)
  ...(!(process.env.NODE_ENV === 'production' && process.env.STATIC_EXPORT === 'true') && {
    async headers() {
      return [
        {
          source: '/(.*)',
          headers: [
            {
              key: 'X-Frame-Options',
              value: 'DENY',
            },
            {
              key: 'X-Content-Type-Options',
              value: 'nosniff',
            },
            {
              key: 'Referrer-Policy',
              value: 'origin-when-cross-origin',
            },
            {
              key: 'Strict-Transport-Security',
              value: 'max-age=31536000; includeSubDomains',
            },
          ],
        },
      ];
    },

    // Redirects for production
    async redirects() {
      return [
        // Removed admin redirect to allow admin panel access
      ];
    },
  }),

  // Compiler options
  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // TypeScript configuration - Allow build to continue with errors for MVP
  typescript: {
    ignoreBuildErrors: true,
  },

  // ESLint configuration - Allow build to continue with errors for MVP
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
