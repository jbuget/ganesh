/**
 * BFF: the browser's only way into the API.
 *
 * The browser calls `/api/v1/...`, this handler relays to
 * `${API_URL}/api/v1/...`, injecting the Entra token fetched server-side. The
 * token never crosses the browser boundary.
 *
 * The paths are identical on both sides: one URL vocabulary.
 *
 * It carries bytes, not only text: a file goes up as the browser wrote it and
 * comes back as the API served it, with the headers a download needs. Reading
 * the body as a string, as this used to, mangled both directions.
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
 * What the API says about the body, relayed as it said it.
 *
 * `Content-Type` decides how the browser reads the answer; the next two are
 * what turns a response into a file it offers to save, under the name the
 * register holds. Forcing `application/json` here, as this used to, made
 * every download a broken string.
 *
 * The last two are what the API says about *reading* the body safely, and
 * they are the reason this list is worth reading twice: a file is served to
 * the browser on this origin, not on the API's, so a protection the API sets
 * and this relay drops is a protection nobody ever receives.
 */
const ABOUT_THE_BODY = [
  "content-type",
  "content-disposition",
  "content-length",
  "x-content-type-options",
  "content-security-policy",
];

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
    // `arrayBuffer` rather than `text`: a multipart body carries raw bytes,
    // and reading it as a string re-encodes them. Held whole in memory on
    // purpose — the domain caps a file at ten megabytes.
    body: hasBody ? await request.arrayBuffer() : undefined,
    cache: "no-store",
  });

  const relayedHeaders = new Headers();
  for (const name of ABOUT_THE_BODY) {
    const value = response.headers.get(name);
    if (value) relayedHeaders.set(name, value);
  }
  if (!relayedHeaders.has("content-type")) {
    relayedHeaders.set("content-type", "application/json");
  }

  // A 204 carries no body at all, and handing one a stream is a runtime
  // error rather than an empty answer.
  const empty = response.status === 204 || response.status === 304;
  const relayed = new NextResponse(empty ? null : await response.arrayBuffer(), {
    status: response.status,
    headers: relayedHeaders,
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
