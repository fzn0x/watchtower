import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

/** @type {import('next').NextConfig} */
const config = {
  // Static HTML for GitHub Pages: no Node.js server at runtime.
  output: 'export',
  // The site is a project page served from https://fzn0x.github.io/watchtower/.
  basePath: '/watchtower',
  // Emit tools/index.html so /watchtower/tools/ keeps working.
  trailingSlash: true,
  // The image optimizer needs a server, so serve images as they are.
  images: { unoptimized: true },
  // Name the build after the commit in CI so the same commit builds the same files.
  // Locally (no GITHUB_SHA) Next.js falls back to a random id.
  generateBuildId: async () => process.env.GITHUB_SHA ?? null,
  reactStrictMode: true,
};

export default withMDX(config);
