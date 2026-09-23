import * as Sentry from "@sentry/nextjs";

/**
 * Server/edge error monitoring — gated on NEXT_PUBLIC_SENTRY_DSN like every
 * other integration in this app (Stripe, GA4, Meta/TikTok pixels): unset
 * means quietly absent, not a build/runtime failure. The DSN isn't a secret
 * (it's designed to ship in client-side JS), so one var covers both sides —
 * see instrumentation-client.ts for the browser half.
 */
export async function register() {
  if (!process.env.NEXT_PUBLIC_SENTRY_DSN) return;

  if (process.env.NEXT_RUNTIME === "nodejs") {
    Sentry.init({
      dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
      tracesSampleRate: 0.1,
    });
  }

  if (process.env.NEXT_RUNTIME === "edge") {
    Sentry.init({
      dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
      tracesSampleRate: 0.1,
    });
  }
}

export const onRequestError = Sentry.captureRequestError;
