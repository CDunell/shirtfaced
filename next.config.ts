import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs/config";

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

// Safe with no Sentry project configured at all: without SENTRY_ORG/
// SENTRY_PROJECT/SENTRY_AUTH_TOKEN this just skips source-map upload at
// build time, it doesn't fail the build. Runtime behaviour is controlled
// entirely by NEXT_PUBLIC_SENTRY_DSN (see src/instrumentation*.ts) — this
// wrapper is only about getting readable stack traces once a DSN exists.
export default withSentryConfig(nextConfig, {
  silent: true,
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  authToken: process.env.SENTRY_AUTH_TOKEN,
});
