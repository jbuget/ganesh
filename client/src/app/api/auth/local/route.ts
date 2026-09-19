/**
 * The fallback door, seen from the BFF.
 *
 * The form is posted here; this handler asks the API to check the
 * credentials, and seals what comes back into the same session cookie an
 * Entra sign-in would have set. Nothing downstream — neither the relay nor
 * the screens — has to know which door was used.
 *
 * The BFF does not check the password itself: one place decides who may come
 * in, and it is the one that guards the data.
 */
import { NextRequest, NextResponse } from "next/server";

import { landingUrl, safeLanding } from "@/lib/auth/pending";
import { sealSession, sessionCookie } from "@/lib/auth/session";

const API_URL = process.env.API_URL ?? "http://localhost:8000";
// `||` rather than `??`: an API_PREFIX left empty in the environment is a
// variable nobody filled in, not a deliberate empty prefix — and `??`
// would take it for one, relaying to an address without /api/v1.
const API_PREFIX = process.env.API_PREFIX || "/api/v1";

/** A day, as the API's own token lasts. */
const SESSION_SECONDS = 60 * 60 * 24;

export async function POST(request: NextRequest): Promise<NextResponse> {
  const form = await request.formData();
  const login = String(form.get("login") ?? "");
  const password = String(form.get("password") ?? "");
  const landing = safeLanding(String(form.get("from") ?? ""));

  const answer = await fetch(`${API_URL}${API_PREFIX}/auth/local`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login, password }),
    cache: "no-store",
  });

  if (!answer.ok) {
    const url = new URL("/connexion", request.nextUrl.origin);
    url.searchParams.set(
      "erreur",
      answer.status === 404 ? "hors-service" : "identifiants",
    );
    if (landing !== "/") url.searchParams.set("from", landing);
    return NextResponse.redirect(url, { status: 303 });
  }

  const { access_token: accessToken } = (await answer.json()) as {
    access_token: string;
  };

  const response = NextResponse.redirect(
    landingUrl(landing, request.nextUrl.origin),
    // 303: what follows a form is a GET, not a second POST on the landing page.
    { status: 303 },
  );
  response.cookies.set(
    sessionCookie(
      await sealSession({
        idToken: accessToken,
        // This door issues no renewal token: the session lasts what the token
        // lasts, and signing in again is the way to extend it.
        refreshToken: "",
        expiresAt: Math.floor(Date.now() / 1000) + SESSION_SECONDS,
        email: login,
      }),
    ),
  );
  return response;
}
