import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  transpilePackages: [
    "@krishiai/auth",
    "@krishiai/shared-types",
    "@krishiai/shared-utils",
    "@krishiai/ui"
  ]
};

export default nextConfig;
