/** @type {import('next').NextConfig} */
const path = require("path");

const apiBackend = process.env.API_BACKEND_URL || "http://localhost:8000";
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Корень для трассировки файлов (монорепо: один lockfile в services/web)
  outputFileTracingRoot: path.join(__dirname),
  async rewrites() {
    return [
      { source: "/api/proxy/:path*", destination: `${apiBackend}/:path*` },
      { source: "/api/auth/callback", destination: `${apiBackend}/api/auth/callback` },
    ];
  },
};

module.exports = nextConfig;
