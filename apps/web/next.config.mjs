/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Next.js 通过相对路径访问后端（同源部署 / 反代）
  async rewrites() {
    const apiUrl = process.env.AIOS_API_URL || 'http://api:8080';
    return [
      { source: '/api/backend/:path*', destination: `${apiUrl}/api/v1/:path*` },
    ];
  },
  transpilePackages: ['antd', '@ant-design/pro-components', '@ant-design/icons', 'rc-util', 'rc-pagination', 'rc-picker'],
};

export default nextConfig;
