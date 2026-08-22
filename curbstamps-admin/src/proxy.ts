import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { SESSION_COOKIE, verifySessionToken } from "@/lib/session";

/** Session enforcement — same shape as shirtfaced-admin/src/proxy.ts.
 * Dev stays login-free; only production enforces a session. */
export function proxy(request: NextRequest) {
  if (process.env.NODE_ENV !== "production") {
    return NextResponse.next();
  }

  const { pathname, search } = request.nextUrl;

  if (pathname === "/login") {
    return NextResponse.next();
  }

  // Server-to-server routes: curbstamps-site's own server calls these, never
  // a browser. Each route under /api/internal and /api/pod checks its own
  // shared secret (verifyInternalRequest / verifyPodWebhook) and returns 401
  // without it — skipping the cookie check here only avoids redirecting a
  // machine caller to an HTML login page it can't use.
  if (pathname.startsWith("/api/internal/") || pathname.startsWith("/api/pod/")) {
    return NextResponse.next();
  }

  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (verifySessionToken(token)) {
    return NextResponse.next();
  }

  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("next", pathname + search);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
