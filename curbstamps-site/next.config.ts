import type { NextConfig } from "next";

// Runs as `next start` behind its own systemd service, same model as
// shirtfaced-site — `output: "export"` would silently drop the API routes
// that /api/create-payment-intent and /api/stripe-webhook need at runtime.
const nextConfig: NextConfig = {
  images: { unoptimized: true },
};

export default nextConfig;
