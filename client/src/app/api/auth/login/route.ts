/**
 * Where signing in starts.
 *
 * Three throwaway secrets are minted here and set aside in a short-lived
 * cookie: the state, the nonce and the PKCE verifier. None of them may be
 * guessed, and none outlives the round trip.
 */
import { NextRequest, NextResponse } from "next/server";

import { authorizationUrl, pkcePair, randomToken } from "@/lib/auth/entra";
import { pendingCookie, safeLanding, sealPending } from "@/lib/auth/pending";

export async function GET(request: NextRequest): Promise<NextResponse> {
  const state = randomToken();
  const nonce = randomToken();
  const { verifier, challenge } = await pkcePair();
  const landing = safeLanding(request.nextUrl.searchParams.get("from"));

  const response = NextResponse.redirect(
    await authorizationUrl({ state, nonce, challenge }),
  );
  response.cookies.set(
    pendingCookie(await sealPending({ state, nonce, verifier, landing })),
  );
  return response;
}
