/**
 * Reading Ganesh as somebody else, sealed in a cookie the browser cannot read.
 *
 * An administrator may borrow a teammate's account to see what it sees. What
 * they are borrowing is held here rather than in the address bar or in a
 * store: a page that could write it would be a page that could read any
 * screen as anybody, and the whole guarantee rests on the browser having no
 * say in the matter.
 *
 * It rides beside the session rather than inside it. The session is rewritten
 * every time Entra renews a token, and across as many cookies as it takes —
 * a borrowing that travelled in there would be lost on the hour, or would
 * survive a sign-out. Its own cookie starts, ends, and is cleared on its own.
 *
 * The API is the authority all the same: the header this cookie produces
 * opens exactly what the account behind the token already held, which is
 * nothing unless it administrates the platform.
 */
import { seal, unseal } from "@/lib/auth/session";

export const IMPERSONATION_COOKIE = "timesheet_read_as";

/** The header the API reads a borrowing off. */
export const IMPERSONATION_HEADER = "x-impersonate-user-id";

/**
 * As long as the session, and no longer.
 *
 * A borrowing outliving the session it was opened under would hand the next
 * person to sign in on that browser somebody else's screens.
 */
const MAX_AGE = 60 * 60 * 24 * 14;

interface CookieToWrite {
  name: string;
  value: string;
  httpOnly: boolean;
  sameSite: "lax";
  secure: boolean;
  path: string;
  maxAge: number;
}

function cookieFor(value: string, maxAge: number): CookieToWrite {
  return {
    name: IMPERSONATION_COOKIE,
    value,
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge,
  };
}

/** What a response hands the browser to start reading as `userId`. */
export async function borrowingCookie(userId: number): Promise<CookieToWrite> {
  return cookieFor(await seal({ userId }), MAX_AGE);
}

/** What a response hands the browser to give the account back. */
export function returnedCookie(): CookieToWrite {
  return cookieFor("", 0);
}

/**
 * Who the incoming request is reading as, if anybody.
 *
 * It is handed the cookies rather than reaching for them, as
 * `sealedSessionFrom` is: the relay already holds the request, and asking
 * `next/headers` from inside it would tie this to a request scope for
 * nothing.
 *
 * Anything that does not open under our key is nobody, the way an unsealed
 * session is « not signed in »: a cookie from before a key was replaced
 * should send somebody back to their own screens, not to an error.
 */
export async function borrowedUserIdFrom(
  read: (name: string) => string | undefined,
): Promise<number | null> {
  const sealed = read(IMPERSONATION_COOKIE);
  if (!sealed) return null;
  const payload = await unseal(sealed);
  const userId = payload?.userId;
  return typeof userId === "number" && Number.isInteger(userId) ? userId : null;
}
