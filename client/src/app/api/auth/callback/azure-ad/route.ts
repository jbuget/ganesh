/**
 * Where Entra sends the person back, code in hand.
 *
 * Everything that can be checked is checked here, because this is the one
 * place a stranger can reach with something that looks like a sign-in: the
 * state must match the one we set aside, the code must be spendable with our
 * PKCE secret, and the address must belong to the company. Anything short of
 * that lands back on the sign-in screen with a reason, never on a half-open
 * session.
 */
import { NextRequest, NextResponse } from "next/server";

import { emailFromIdToken, exchangeCode, isAllowedEmail } from "@/lib/auth/entra";
import { PENDING_COOKIE, openPending } from "@/lib/auth/pending";
import { sealSession, sessionCookie } from "@/lib/auth/session";

/** Back to the sign-in screen, saying what went wrong in a word. */
function refused(request: NextRequest, reason: string): NextResponse {
  const url = new URL("/connexion", request.nextUrl.origin);
  url.searchParams.set("erreur", reason);
  const response = NextResponse.redirect(url);
  response.cookies.delete(PENDING_COOKIE);
  return response;
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");

  // Entra says so itself when the person declined, or when the tenant refused.
  if (request.nextUrl.searchParams.get("error")) {
    return refused(request, "refus");
  }
  if (!code || !state) return refused(request, "incomplet");

  const sealed = request.cookies.get(PENDING_COOKIE)?.value;
  const pending = sealed ? await openPending(sealed) : null;
  // No pending sign-in: either this callback was not asked for by this
  // browser, or the person took longer than the five minutes it lives.
  if (!pending) return refused(request, "expire");
  if (pending.state !== state) return refused(request, "etat");

  const tokens = await exchangeCode(code, pending.verifier);
  if (!tokens) return refused(request, "echange");

  const email = emailFromIdToken(tokens.idToken);
  if (!email) return refused(request, "sans-adresse");
  if (!isAllowedEmail(email)) return refused(request, "domaine");

  const response = NextResponse.redirect(
    new URL(pending.landing, request.nextUrl.origin),
  );
  response.cookies.set(sessionCookie(await sealSession({ ...tokens, email })));
  response.cookies.delete(PENDING_COOKIE);
  return response;
}
