"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/session";

export async function logoutAction() {
  const store = await cookies();
  // Cleared with the attributes it was set with. A cookie deleted without its
  // domain leaves the domain-scoped one in place, and logging out of admin would
  // leave you signed into Studio.
  const { httpOnly, secure, sameSite, path, domain } = sessionCookieOptions();
  store.set(SESSION_COOKIE, "", {
    httpOnly,
    secure,
    sameSite,
    path,
    domain,
    maxAge: 0,
  });
  redirect("/login");
}
