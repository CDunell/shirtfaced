import * as Sentry from "@sentry/nextjs";

/**
 * Browser-side half of error monitoring — see instrumentation.ts for the
 * server/edge half and why this is a single, non-secret DSN var.
 */
if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    tracesSampleRate: 0.1,
    // Session replay is off by default -- checkout pages handle card data
    // (via Stripe's own iframe, never our inputs) and cookie-consent hasn't
    // been scoped for this yet. Turn on deliberately, not as a default.
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0,
  });
}

export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
