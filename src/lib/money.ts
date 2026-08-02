/**
 * Currency formatting.
 *
 * Deliberately NOT in cart-context.tsx: that module is "use client", and a
 * server component importing from it fails the build. Formatting has no
 * client-side state, so it lives here where either side can use it.
 */
export const money = (n: number) =>
  n.toLocaleString("en-AU", { style: "currency", currency: "AUD" });
