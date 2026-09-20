/**
 * Where Entra sends the person back, code in hand.
 *
 * Everything that can be checked is checked here, because this is the one
 * place a stranger can reach with something that looks like a sign-in: the
 * state must match the one we set aside, the code must be spendable with our
 * PKCE secret, the identity token must echo our nonce, and the address must
 * belong to the company. Anything short of
 * that lands back on the sign-in screen with a reason, never on a half-open
 * session.
 */
import { NextRequest, NextResponse } from "next/server";

import { claimsFromIdToken, exchangeCode, isAllowedEmail } from "@/lib/auth/entra";
import { PENDING_COOKIE, appOrigin, landingUrl, openPending } from "@/lib/auth/pending";
import { sealSession, sessionCookie } from "@/lib/auth/session";

/** Back to the sign-in screen, saying what went wrong in a word. */
function refused(request: NextRequest, reason: string): NextResponse {
  const url = new URL("/sign-in", appOrigin(request.nextUrl.origin));
  url.searchParams.set("reason", reason);
  const response = NextResponse.redirect(url);
  response.cookies.delete(PENDING_COOKIE);
  return response;
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");

  // Entra says so itself when the person declined, or when the tenant refused.
  if (request.nextUrl.searchParams.get("error")) {
    return refused(request, "denied");
  }
  if (!code || !state) return refused(request, "incomplete");

  const sealed = request.cookies.get(PENDING_COOKIE)?.value;
  const pending = sealed ? await openPending(sealed) : null;
  // No pending sign-in: either this callback was not asked for by this
  // browser, or the person took longer than the five minutes it lives.
  if (!pending) return refused(request, "expired");
  if (pending.state !== state) return refused(request, "state");

  const tokens = await exchangeCode(code, pending.verifier);
  if (!tokens) return refused(request, "exchange");

  const claims = claimsFromIdToken(tokens.idToken);
  if (!claims) return refused(request, "token");
  // The nonce came back from the token Entra signed for *this* sign-in. An
  // identity token captured elsewhere carries another one, and stops here.
  if (!claims.nonce || claims.nonce !== pending.nonce) {
    return refused(request, "nonce");
  }

  const email = claims.preferred_username ?? claims.email ?? claims.upn ?? null;
  if (!email) return refused(request, "no-email");
  if (!isAllowedEmail(email)) return refused(request, "domain");

  const response = NextResponse.redirect(
    landingUrl(pending.landing, appOrigin(request.nextUrl.origin)),
  );
  response.cookies.set(sessionCookie(await sealSession({ ...tokens, email })));
  response.cookies.delete(PENDING_COOKIE);
  return response;
}
