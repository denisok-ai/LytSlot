/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/proxy/:path*", destination: "http://localhost:8000/:path*" },
      { source: "/api/auth/callback", destination: "http://localhost:8000/api/auth/callback" },
    ];
  },
};

module.exports = nextConfig;
