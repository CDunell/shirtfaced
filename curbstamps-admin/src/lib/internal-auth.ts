import { timingSafeEqual } from "node:crypto";

/**
 * Auth for server-to-server routes under /api/internal — curbstamps-site's
 * own Next.js server calls these, never a browser, so there's no session
 * cookie to check. proxy.ts exempts this path from the login redirect on
 * exactly that basis; every route under it must call this itself.
 */
export function verifyInternalRequest(request: Request): boolean {
  const expected = process.env.INTERNAL_API_KEY;
  const provided = request.headers.get("x-internal-api-key");
  if (!expected || !provided) return false;

  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}
