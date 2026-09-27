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

import { upstream } from "@/lib/api/upstream";
import { needsRefresh, refreshTokens } from "@/lib/auth/entra";
import {
  IMPERSONATION_HEADER,
  borrowedUserIdFrom,
  returnedCookie,
} from "@/lib/auth/impersonation";
import {
  clearedSessionCookies,
  currentSession,
  sealSession,
  sessionCookies,
  type Session,
} from "@/lib/auth/session";

const HOP_BY_HOP = new Set(["connection", "keep-alive", "transfer-encoding", "host"]);

/**
 * What the API says about the body, relayed as it said it.
 *
 * `Content-Type` decides how the browser reads the answer; the next one is
 * what turns a response into a file it offers to save, under the name the
 * register holds. Forcing `application/json` here, as this used to, made
 * every download a broken string.
 *
 * The last two are what the API says about *reading* the body safely, and
 * they are the reason this list is worth reading twice: a file is served to
 * the browser on this origin, not on the API's, so a protection the API sets
 * and this relay drops is a protection nobody ever receives.
 *
 * `Content-Length` is deliberately not among them, and that is the other half
 * of the same lesson: a header may describe bytes we no longer hold. Caddy
 * compresses what the API serves in production, `fetch` hands the body back
 * decompressed but the headers as they came, and that length then counts the
 * compressed bytes. Relayed as such, it cut the answer off mid-object. The
 * runtime counts the bytes it actually sends, which is the only count that can
 * be right here.
 */
const ABOUT_THE_BODY = [
  "content-type",
  "content-disposition",
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
  const target = upstream(`${suffix}${incoming.search}`);

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) headers.set(key, value);
  });
  // Taken away before anything is put back: the relay copies what the browser
  // sent, and this header says which account the API is to answer as. A page
  // that could set it would be a page naming its own reader. It is written
  // here alone, out of a sealed cookie no script on the page can reach.
  //
  // It would open nothing either way — the API reads it off the account the
  // token names, and refuses anybody who does not administrate the platform —
  // but a header the browser can steer is a header somebody will one day
  // trust.
  headers.delete(IMPERSONATION_HEADER);
  const readAs = await borrowedUserIdFrom((name) => request.cookies.get(name)?.value);
  if (readAs !== null) headers.set(IMPERSONATION_HEADER, String(readAs));

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
  // A session the API turns away is over, whatever the seal says. `proxy.ts`
  // catches a seal that no longer opens; this catches the other case, the one
  // it cannot see — a seal that opens perfectly onto a token the API will not
  // have. Left in place, the browser sends it again at every request for the
  // fortnight it was set to live, and the person walks from a screen to the
  // sign-in page and back without anything changing.
  //
  // 401 and nothing else: a 403 is the API saying the gesture is not theirs
  // to make, which says nothing about the session and must not sign anybody
  // out.
  // What the browser sends now, so what this session does not use is taken
  // away rather than left to be read back glued to it.
  const carried = request.cookies.getAll().map((cookie) => cookie.name);
  if (response.status === 401) {
    for (const cookie of clearedSessionCookies(carried)) relayed.cookies.set(cookie);
    // And the borrowing with it, for the reason signing out takes it: it was
    // opened under a session that is over.
    relayed.cookies.set(returnedCookie());
  } else if (renewed && session) {
    for (const cookie of sessionCookies(await sealSession(session), carried)) {
      relayed.cookies.set(cookie);
    }
  }
  return relayed;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
