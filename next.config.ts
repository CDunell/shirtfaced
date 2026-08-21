import type { NextConfig } from "next";

// `output: "export"` was dropped 2026-08-21: it silently produces a static
// build with no server, which means /api/create-payment-intent,
// /api/stripe-webhook, /api/order-status and /api/apply-discount compile
// cleanly but are never actually reachable in production -- the whole
// checkout chain (see src/app/api/create-payment-intent/route.ts) was
// deployed but never live. Now runs as `next start` behind its own systemd
// service, same model as shirtfaced-admin.
const nextConfig: NextConfig = {
  images: { unoptimized: true },
};

export default nextConfig;
