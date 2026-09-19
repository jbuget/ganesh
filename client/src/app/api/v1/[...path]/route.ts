/**
 * BFF: the browser's only way into the API.
 *
 * The browser calls `/api/v1/...`, this handler relays to
 * `${API_URL}/api/v1/...`, injecting the Entra token fetched server-side. The
 * token never crosses the browser boundary.
 *
 * The paths are identical on both sides: one URL vocabulary.
 *
 * It is also where a session is renewed. An identity token lives an hour and
 * Entra will not make it live longer; rather than sign the person out on the
 * hour, the relay buys a fresh one just before the old one dies, on the way
 * past. Entra rotates the renewal token as it goes, so the session is written
 * back on the response — keeping the spent one would lock the person out at
 * the following renewal.
 */
import { NextRequest, NextResponse } from "next/server";

import { needsRefresh, refreshTokens } from "@/lib/auth/entra";
import {
  currentSession,
  sealSession,
  sessionCookie,
  type Session,
} from "@/lib/auth/session";

const API_URL = process.env.API_URL ?? "http://localhost:8000";
// `||` rather than `??`: an API_PREFIX left empty in the environment is a
// variable nobody filled in, not a deliberate empty prefix — and `??`
// would take it for one, relaying to an address without /api/v1.
const API_PREFIX = process.env.API_PREFIX || "/api/v1";

const HOP_BY_HOP = new Set(["connection", "keep-alive", "transfer-encoding", "host"]);

/**
 * The session to relay with, renewed if it was about to expire.
 *
 * Returns the session to use and, when it changed, the cookie to write back.
 */
async function freshSession(): Promise<{ session: Session | null; renewed: boolean }> {
  const session = await currentSession();
  if (!session || !needsRefresh(session)) return { session, renewed: false };

  // Nothing to renew with: the fallback door issues no renewal token, so an
  // expired session there is simply over. The API will say 401, and the
  // screen will ask to sign in again.
  if (!session.refreshToken) return { session: null, renewed: false };

  const tokens = await refreshTokens(session.refreshToken);
  // A renewal Entra refuses is a session that has run its course: we relay
  // without a token, the API answers 401, and the screen sends the person to
  // sign in again. Better than a request that hangs on a dead token.
  if (!tokens) return { session: null, renewed: false };

  return { session: { ...tokens, email: session.email }, renewed: true };
}

async function proxy(request: NextRequest): Promise<NextResponse> {
  const incoming = new URL(request.url);
  const suffix = incoming.pathname.replace(/^\/api\/v1/, "");
  const target = `${API_URL}${API_PREFIX}${suffix}${incoming.search}`;

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) headers.set(key, value);
  });

  const { session, renewed } = await freshSession();
  if (session) headers.set("Authorization", `Bearer ${session.idToken}`);

  const hasBody = !["GET", "HEAD"].includes(request.method);

  const response = await fetch(target, {
    method: request.method,
    headers,
    body: hasBody ? await request.text() : undefined,
    cache: "no-store",
  });

  const payload = await response.text();

  const relayed = new NextResponse(payload || null, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
    },
  });
  if (renewed && session) {
    relayed.cookies.set(sessionCookie(await sealSession(session)));
  }
  return relayed;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
