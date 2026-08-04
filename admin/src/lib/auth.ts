import { cookies } from "next/headers";
import { SESSION_COOKIE, verifySessionToken } from "@/lib/session";

/** Reads the current admin's email from the session cookie. proxy.ts already
 * guarantees a valid session for every route this is called from. */
export async function currentAdmin(): Promise<string | null> {
  const store = await cookies();
  return verifySessionToken(store.get(SESSION_COOKIE)?.value);
}
