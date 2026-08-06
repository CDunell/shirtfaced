import { createHmac, timingSafeEqual } from "node:crypto";

export const SESSION_COOKIE = "sf_admin_session";
const MAX_AGE_SECONDS = 60 * 60 * 24 * 7; // 7 days

function secret(): string {
  const s = process.env.SESSION_SECRET;
  if (!s) throw new Error("SESSION_SECRET is not set");
  return s;
}

function sign(value: string): string {
  return createHmac("sha256", secret()).update(value).digest("base64url");
}

/** Stateless signed session token: base64url(email).expiryEpoch.signature */
export function createSessionToken(email: string): string {
  const expires = Math.floor(Date.now() / 1000) + MAX_AGE_SECONDS;
  const payload = `${Buffer.from(email).toString("base64url")}.${expires}`;
  return `${payload}.${sign(payload)}`;
}

export function verifySessionToken(token: string | undefined): string | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [emailB64, expiresStr, signature] = parts;
  const payload = `${emailB64}.${expiresStr}`;
  const expected = sign(payload);

  const a = Buffer.from(signature);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;

  const expires = Number(expiresStr);
  if (!Number.isFinite(expires) || expires < Date.now() / 1000) return null;

  try {
    return Buffer.from(emailB64, "base64url").toString("utf8");
  } catch {
    return null;
  }
}

export const SESSION_MAX_AGE = MAX_AGE_SECONDS;

/**
 * Where the session cookie is valid.
 *
 * Set to `.shirtfaced.wtf` in production so the cookie also reaches Studio on its
 * own subdomain: Studio has no login, it verifies this same token with the same
 * secret, and being signed into admin is being signed into Studio. Left unset for
 * localhost, where a domain attribute would stop the cookie being stored at all.
 */
export function sessionCookieDomain(): string | undefined {
  return process.env.SESSION_COOKIE_DOMAIN || undefined;
}

/** The options every place that writes or clears the cookie must agree on. A
 *  cookie cleared with different attributes than it was set with is not cleared. */
export function sessionCookieOptions() {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    domain: sessionCookieDomain(),
  };
}
