/**
 * Which addresses may be reached without being signed in.
 *
 * Everything else asks who you are first. The list is short on purpose: what
 * is not named here is protected, so forgetting to add a screen closes it
 * rather than opens it.
 */
const OPEN_PATHS = ["/sign-in"];
const OPEN_PREFIXES = ["/api/auth/", "/_next/", "/favicon", "/icon"];

export function isOpenPath(pathname: string): boolean {
  if (OPEN_PATHS.includes(pathname)) return true;
  return OPEN_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

/**
 * Whether signing in may be skipped altogether.
 *
 * Development only, and it mirrors `REQUIRE_AUTH` on the API side: the two
 * must be set together, or the screens open on an API that turns them away.
 * Never in production — the check is written so that anything other than a
 * plain « true » leaves the door shut.
 */
export function isAuthDisabled(): boolean {
  return process.env.NODE_ENV !== "production" && process.env.AUTH_DISABLED === "true";
}
