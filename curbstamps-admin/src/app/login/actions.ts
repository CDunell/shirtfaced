"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { verifyPassword } from "@/lib/password";
import { createSessionToken, SESSION_COOKIE, SESSION_MAX_AGE, sessionCookieOptions } from "@/lib/session";

function safeNext(next: string): string {
  return next.startsWith("/") ? next : "/orders";
}

export async function loginAction(
  _prevState: { error: string | null },
  formData: FormData,
): Promise<{ error: string | null }> {
  const email = String(formData.get("email") ?? "").trim().toLowerCase();
  const password = String(formData.get("password") ?? "");
  const next = String(formData.get("next") ?? "/orders");

  const adminEmail = process.env.ADMIN_EMAIL?.toLowerCase();
  const adminHash = process.env.ADMIN_PASSWORD_HASH;

  if (!adminEmail || !adminHash) {
    return { error: "Admin account is not configured." };
  }
  if (email !== adminEmail || !verifyPassword(password, adminHash)) {
    return { error: "Wrong email or password." };
  }

  const store = await cookies();
  store.set(SESSION_COOKIE, createSessionToken(email), { ...sessionCookieOptions(), maxAge: SESSION_MAX_AGE });
  redirect(safeNext(next));
}

export async function logoutAction() {
  const store = await cookies();
  store.delete(SESSION_COOKIE);
  redirect("/login");
}
