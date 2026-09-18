/**
 * End of session: the cookie carrying the Entra token is cleared.
 *
 * The token lives server-side, in an `httpOnly` cookie: only a handler like
 * this one can remove it. Redirecting is left to the caller, who knows where to
 * send the person.
 */
import { NextResponse } from "next/server";

import { SESSION_COOKIE } from "@/lib/auth/session";

export async function POST(): Promise<NextResponse> {
  const response = new NextResponse(null, { status: 204 });
  response.cookies.set(SESSION_COOKIE, "", { path: "/", maxAge: 0 });
  return response;
}
