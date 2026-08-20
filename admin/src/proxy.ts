import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { SESSION_COOKIE, verifySessionToken } from "@/lib/session";

/**
 * Session enforcement.
 *
 * Was a no-op stub ("disabled for dev" -- convenient locally, since it means
 * no login step to touch a page while working) that never got a production
 * guard, so it shipped disabled everywhere: every admin page, including
 * customer records and orders, served real data to anyone who reached the
 * URL, no session required. Confirmed live against the production site
 * before this fix, not just suspected from reading the code.
 *
 * `auth.ts`'s own comment already claimed this file "guarantees a valid
 * session for every route this is called from" -- true now, was never
 * actually true before.
 */
export function proxy(request: NextRequest) {
  // Unchanged from before: dev stays login-free, exactly what "disabled for
  // dev" set out to do. Only production enforces a session.
  if (process.env.NODE_ENV !== "production") {
    return NextResponse.next();
  }

  const { pathname, search } = request.nextUrl;

  // /login itself must stay reachable without a session, or nobody could
  // ever sign in. Next's own internals and static assets never carry a
  // session either -- excluded via the matcher below, not here.
  if (pathname === "/login") {
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
  /* Everything except Next's own internals, static files and favicon --
     matches the conventional Next.js middleware matcher pattern. */
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
