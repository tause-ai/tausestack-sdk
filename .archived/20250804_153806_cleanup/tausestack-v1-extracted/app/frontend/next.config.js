/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Configuración mínima que funciona
  distDir: '.next',
  poweredByHeader: false,
  compress: true,
}

module.exports = nextConfig 