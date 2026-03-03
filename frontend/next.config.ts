import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker 部署使用 standalone 输出
  output: "standalone",
  // API 代理到后端服务
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
  // 代理超时：图片 OCR + LLM 解题可能需要较长时间
  experimental: {
    proxyTimeout: 180_000, // 180 秒
  },
  // react-katex 使用 CommonJS，需要 transpile
  transpilePackages: ["react-katex"],
};

export default nextConfig;
