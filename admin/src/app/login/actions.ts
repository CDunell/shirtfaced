"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { verifyPassword } from "@/lib/password";
import {
  createSessionToken,
  SESSION_COOKIE,
  SESSION_MAX_AGE,
  sessionCookieDomain,
  sessionCookieOptions,
} from "@/lib/session";

/**
 * Where to send someone after signing in.
 *
 * A relative path is always fine. An absolute URL is allowed only when it is on
 * the domain the session cookie covers -- that is the set of sites this login
 * actually signs you into, and anything wider is an open redirect. Studio sends
 * people here with its own URL in `next`, which is the case this exists for.
 */
function safeNext(next: string): string {
  if (next.startsWith("/")) return next;

  const domain = sessionCookieDomain();
  if (!domain) return "/products";
  try {
    const url = new URL(next);
    const suffix = domain.startsWith(".") ? domain : `.${domain}`;
    if (url.protocol === "https:" && (url.hostname + ".").endsWith(suffix + ".")) {
      return next;
    }
  } catch {
    // Not a URL at all.
  }
  return "/products";
}

export async function loginAction(
  _prevState: { error: string | null },
  formData: FormData,
): Promise<{ error: string | null }> {
  const email = String(formData.get("email") ?? "").trim().toLowerCase();
  const password = String(formData.get("password") ?? "");
  const next = String(formData.get("next") ?? "/products");

  const adminEmail = process.env.ADMIN_EMAIL?.toLowerCase();
  const adminHash = process.env.ADMIN_PASSWORD_HASH;

  if (!adminEmail || !adminHash) {
    return { error: "Admin account is not configured." };
  }

  if (email !== adminEmail || !verifyPassword(password, adminHash)) {
    return { error: "Wrong email or password." };
  }

  const store = await cookies();
  store.set(SESSION_COOKIE, createSessionToken(email), {
    ...sessionCookieOptions(),
    maxAge: SESSION_MAX_AGE,
  });

  redirect(safeNext(next));
}
