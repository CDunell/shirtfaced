import * as Sentry from "@sentry/nextjs";

/**
 * Server/edge error monitoring — gated on NEXT_PUBLIC_SENTRY_DSN, same
 * "unset means quietly absent" convention as every other integration in
 * this app. The DSN isn't a secret (it ships in client-side JS anyway), so
 * one var covers both sides — see instrumentation-client.ts for the browser
 * half.
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
