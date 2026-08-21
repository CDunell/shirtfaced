import { timingSafeEqual } from "node:crypto";

/**
 * Auth for server-to-server routes under /api/internal — the storefront's
 * own Next.js server calls these, never a browser, so there is no session
 * cookie to check. proxy.ts exempts this path from the cookie redirect on
 * exactly that basis; every route under it must call this itself, or the
 * exemption is a hole, not a boundary.
 */
export function verifyInternalRequest(request: Request): boolean {
  const expected = process.env.INTERNAL_API_KEY;
  const provided = request.headers.get("x-internal-api-key");
  if (!expected || !provided) return false;

  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  // timingSafeEqual throws on length mismatch rather than returning false —
  // an unequal length is already a "no" and never a bug to surface as one.
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}
