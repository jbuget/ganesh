/**
 * The session, sealed in a cookie the browser cannot read.
 *
 * What Entra hands over — the identity token, the one that renews it — stays
 * server-side. The cookie carries it encrypted (`httpOnly`, so no script on
 * the page can reach it either), and only this module holds the key. A cookie
 * stolen in transit says nothing; a cookie rewritten on the way is refused.
 *
 * The tokens ride in the cookie rather than in a store because the BFF has no
 * database of its own. It costs the 4 KB a cookie may weigh — which is why a
 * session is written across as many cookies as it takes, and nothing else is
 * ever to be put in here.
 */
import { cookies } from "next/headers";
import { jwtDecrypt, EncryptJWT } from "jose";

export const SESSION_COOKIE = "timesheet_token";

/** What a signed-in session holds. */
export interface Session {
  /** What the API is shown: Entra signed it, the API verifies that signature. */
  idToken: string;
  /**
   * What buys a fresh identity token when this one runs out.
   *
   * Empty on a session opened by the fallback door: that one issues no
   * renewal token, so its session lasts what its token lasts.
   */
  refreshToken: string;
  /** When the identity token stops being accepted, in seconds since the epoch. */
  expiresAt: number;
  /** Who it belongs to, so the BFF can say it without opening the token. */
  email: string;
}

/**
 * The key, derived from the secret so that any passphrase length works.
 *
 * Read on each call rather than once: the environment is not settled when a
 * module is first loaded, and a test may hand over another key.
 */
async function key(): Promise<Uint8Array> {
  const secret = process.env.SESSION_SECRET;
  if (!secret) {
    throw new Error("SESSION_SECRET est absent : la session ne peut être scellée.");
  }
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(secret),
  );
  return new Uint8Array(digest);
}

/** Seals anything into the string a cookie carries. */
export async function seal(payload: Record<string, unknown>): Promise<string> {
  return new EncryptJWT(payload)
    .setProtectedHeader({ alg: "dir", enc: "A256GCM" })
    .setIssuedAt()
    .encrypt(await key());
}

/**
 * Opens what a cookie carried, or nothing at all.
 *
 * Anything that does not open under our key — forged, tampered with, sealed
 * under a key since replaced — comes back as nothing rather than as an error:
 * to the screens, it reads as « not signed in », which is what it is.
 */
export async function unseal(sealed: string): Promise<Record<string, unknown> | null> {
  if (!sealed) return null;
  try {
    const { payload } = await jwtDecrypt(sealed, await key());
    return payload as Record<string, unknown>;
  } catch {
    return null;
  }
}

/** Seals a session into the string a cookie carries. */
export async function sealSession(session: Session): Promise<string> {
  return seal({ ...session });
}

/** Opens a sealed session, or nothing if it does not hold together. */
export async function openSession(sealed: string): Promise<Session | null> {
  const payload = (await unseal(sealed)) as unknown as Session | null;
  if (!payload) return null;
  const { idToken, refreshToken, expiresAt, email } = payload;
  // The renewal token is the one thing a session may lack: the fallback door
  // hands none out.
  if (!idToken || !expiresAt || !email) return null;
  return { idToken, refreshToken: refreshToken ?? "", expiresAt, email };
}

/** The session the incoming request carries, if it carries one. */
export async function currentSession(): Promise<Session | null> {
  const store = await cookies();
  const sealed = sealedSessionFrom((name) => store.get(name)?.value);
  return sealed ? openSession(sealed) : null;
}

/**
 * How much of a sealed session one cookie carries.
 *
 * A browser drops a cookie over 4 096 bytes, name and attributes counted,
 * without a word: no error, no console, nothing but a session that was never
 * there on the next request. And a sealed session sits right on that line —
 * an identity token and the one that renews it, encrypted together, weigh
 * between three and eight kilobytes depending on whose claims they carry.
 *
 * It showed the day production moved to Entra: half the team signed in and
 * the other half came back to the sign-in page with nothing anywhere to say
 * why — not a log, not a refusal, not a `reason` in the address bar. A
 * session that worked measured 3 799 bytes.
 *
 * 3 500 leaves room for the name, the attributes, and the margin a browser is
 * entitled to take.
 */
const CHUNK = 3_500;

/** What a response hands the browser to write a cookie down. */
interface CookieToWrite {
  name: string;
  value: string;
  httpOnly: boolean;
  sameSite: "lax";
  secure: boolean;
  path: string;
  maxAge: number;
}

/** The name of one piece of a session, in the order it is read back. */
function pieceName(index: number): string {
  return `${SESSION_COOKIE}.${index}`;
}

function cookieFor(name: string, value: string, maxAge: number): CookieToWrite {
  return {
    name,
    value,
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge,
  };
}

/** A fortnight: long enough not to sign in every morning, short enough that a
 * forgotten session on a shared machine does not outlive the month. */
const SESSION_MAX_AGE = 60 * 60 * 24 * 14;

/** Every cookie name a session is written across, among those a browser sends. */
export function sessionCookieNames(present: readonly string[]): string[] {
  return present.filter(
    (name) => name === SESSION_COOKIE || name.startsWith(`${SESSION_COOKIE}.`),
  );
}

/**
 * How a sealed session is written down, wherever a response sets it.
 *
 * `present` is what the browser currently sends. Whatever the session before
 * was written across and this one does not use is taken away in the same
 * breath: a piece left behind is read back glued to the new session, and then
 * nothing opens at all. The single cookie sessions used to be written as is
 * one such leftover, which is how a session from before the cut is replaced
 * rather than doubled.
 */
export function sessionCookies(
  sealed: string,
  present: readonly string[] = [],
): CookieToWrite[] {
  const written: CookieToWrite[] = [];
  for (let at = 0; at < sealed.length; at += CHUNK) {
    written.push(
      cookieFor(
        pieceName(written.length),
        sealed.slice(at, at + CHUNK),
        SESSION_MAX_AGE,
      ),
    );
  }
  const stale = sessionCookieNames(present).filter(
    (name) => !written.some((cookie) => cookie.name === name),
  );
  return [...written, ...stale.map((name) => cookieFor(name, "", 0))];
}

/** What a response sends to take a session away, whole. */
export function clearedSessionCookies(present: readonly string[]): CookieToWrite[] {
  return sessionCookieNames(present).map((name) => cookieFor(name, "", 0));
}

/**
 * The sealed session a request carries, however many cookies it took.
 *
 * The single cookie comes first: sessions opened before the cut are still
 * live, and shipping this is no reason to sign everybody out.
 */
export function sealedSessionFrom(
  read: (name: string) => string | undefined,
): string | null {
  const whole = read(SESSION_COOKIE);
  if (whole) return whole;

  let sealed = "";
  for (let index = 0; ; index += 1) {
    const piece = read(pieceName(index));
    if (piece === undefined) break;
    sealed += piece;
  }
  return sealed || null;
}
