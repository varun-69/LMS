/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Playwright must run in the Node.js runtime, never bundled for the browser.
  experimental: {
    serverComponentsExternalPackages: ["playwright", "playwright-core", "cheerio"],
  },
};

module.exports = nextConfig;
