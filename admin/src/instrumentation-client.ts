import * as Sentry from "@sentry/nextjs";

/**
 * Browser-side half of error monitoring — see instrumentation.ts for the
 * server/edge half and why this is a single, non-secret DSN var. Session
 * replay stays off by default: this app is the admin surface, handling
 * customer PII on every order/customer page, and turning replay on needs a
 * deliberate decision about what it's allowed to record, not a default.
 */
if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0,
  });
}

export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
