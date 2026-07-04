import type { NextConfig } from "next";

// The backend runs on a different origin (127.0.0.1:8000). Browsers treat
// "localhost" and "127.0.0.1" as different sites for cookie purposes, so a
// SameSite=Lax auth cookie set by the backend is never sent back on
// cross-site fetch() calls - only the page's own same-origin requests.
// Proxying /api/v1/* through the Next.js server keeps every browser request
// same-origin, so the auth cookie flows correctly regardless of whether the
// app is opened via localhost or 127.0.0.1.
const BACKEND_URL =
  process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${BACKEND_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
