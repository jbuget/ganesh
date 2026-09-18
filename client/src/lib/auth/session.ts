/**
 * Access to the Entra token, server-side only.
 *
 * In development, `REQUIRE_AUTH=false` on the API side allows working without
 * a token: the BFF then forwards nothing and the API applies its development
 * identity. This mode must never be active in production.
 */
import { cookies } from "next/headers";

export const SESSION_COOKIE = "timesheet_token";

/** Returns the session's access token, if there is one. */
export async function getAccessToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(SESSION_COOKIE)?.value ?? null;
}
