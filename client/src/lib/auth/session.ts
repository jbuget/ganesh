/**
 * The session, sealed in a cookie the browser cannot read.
 *
 * What Entra hands over — the identity token, the one that renews it — stays
 * server-side. The cookie carries it encrypted (`httpOnly`, so no script on
 * the page can reach it either), and only this module holds the key. A cookie
 * stolen in transit says nothing; a cookie rewritten on the way is refused.
 *
 * The tokens ride in the cookie rather than in a store because the BFF has no
 * database of its own. It costs the 4 KB a cookie may weigh: nothing else is
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
  const sealed = store.get(SESSION_COOKIE)?.value;
  return sealed ? openSession(sealed) : null;
}

/** How a sealed session is written down, wherever a response sets it. */
export function sessionCookie(sealed: string) {
  return {
    name: SESSION_COOKIE,
    value: sealed,
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    // A fortnight: long enough not to sign in every morning, short enough that
    // a forgotten session on a shared machine does not outlive the month.
    maxAge: 60 * 60 * 24 * 14,
  };
}
