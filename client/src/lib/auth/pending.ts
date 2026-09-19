/**
 * The three throwaway secrets a sign-in needs, and where they wait.
 *
 * They live in their own short-lived cookie, sealed like a session: the state
 * that ties the callback to the request, the nonce that ties the identity
 * token to this sign-in, and the PKCE verifier that proves at the exchange
 * that the code came home to whoever asked for it.
 *
 * They have their own shape rather than borrowing a session's: a session and
 * a sign-in in progress hold nothing alike, and squeezing one into the other
 * would only make both unreadable.
 */
import { seal, unseal } from "@/lib/auth/session";

export const PENDING_COOKIE = "timesheet_signin";

/** Five minutes: the time it takes to sign in, and not a minute more. */
export const PENDING_MAX_AGE = 300;

export interface PendingSignIn {
  state: string;
  nonce: string;
  verifier: string;
  /** Where to land once signed in. A path of ours, never a full address. */
  landing: string;
}

export async function sealPending(pending: PendingSignIn): Promise<string> {
  return seal({ ...pending });
}

export async function openPending(sealed: string): Promise<PendingSignIn | null> {
  const payload = (await unseal(sealed)) as unknown as PendingSignIn | null;
  if (!payload) return null;
  const { state, nonce, verifier, landing } = payload;
  if (!state || !nonce || !verifier || !landing) return null;
  return { state, nonce, verifier, landing };
}

/**
 * A landing spot we are willing to send someone to.
 *
 * Only a path of ours: a caller must not be able to hand us another site to
 * send the person to once signed in.
 *
 * Starting with a slash is not enough. The URL parser reads a backslash as a
 * slash, so « /\\elsewhere.example » resolves to elsewhere.example just as
 * surely as « //elsewhere.example » — and the sign-in page becomes a springboard
 * to whatever site a link names. The second character therefore has to be
 * neither, and the answer is checked against the origin rather than trusted.
 */
export function safeLanding(asked: string | null): string {
  if (!asked || !asked.startsWith("/")) return "/";
  if (asked[1] === "/" || asked[1] === "\\") return "/";
  return asked;
}

export function pendingCookie(sealed: string) {
  return {
    name: PENDING_COOKIE,
    value: sealed,
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: PENDING_MAX_AGE,
  };
}

/**
 * The address to land on, resolved and checked against our own origin.
 *
 * `safeLanding` already refuses what does not look like one of our paths.
 * This is the second lock, at the one place a redirection actually happens:
 * whatever the parser makes of the path, if it does not resolve to us, it is
 * not where anyone is sent.
 */
export function landingUrl(landing: string, origin: string): URL {
  const home = new URL("/", origin);
  try {
    const target = new URL(landing, origin);
    return target.origin === home.origin ? target : home;
  } catch {
    return home;
  }
}
