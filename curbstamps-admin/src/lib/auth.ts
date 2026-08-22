import { cookies } from "next/headers";
import { SESSION_COOKIE, verifySessionToken } from "./session";

/** The logged-in admin's email, or null. Used by layout.tsx to decide
 * whether to show the sidebar/logout, and by proxy.ts to gate every route. */
export async function currentAdmin(): Promise<string | null> {
  const jar = await cookies();
  return verifySessionToken(jar.get(SESSION_COOKIE)?.value);
}
