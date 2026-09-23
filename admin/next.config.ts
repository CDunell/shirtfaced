import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs/config";

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
