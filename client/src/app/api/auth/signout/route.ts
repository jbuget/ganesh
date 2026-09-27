/**
 * End of session: the cookie carrying the Entra token is cleared.
 *
 * The token lives server-side, in an `httpOnly` cookie: only a handler like
 * this one can remove it. Redirecting is left to the caller, who knows where to
 * send the person.
 */
import { NextRequest, NextResponse } from "next/server";

import { returnedCookie } from "@/lib/auth/impersonation";
import { clearedSessionCookies } from "@/lib/auth/session";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const response = new NextResponse(null, { status: 204 });
  // Every cookie the session is written across, not only the first: one piece
  // left behind is a session that half exists.
  for (const cookie of clearedSessionCookies(
    request.cookies.getAll().map((held) => held.name),
  )) {
    response.cookies.set(cookie);
  }
  // A borrowing goes with the session that opened it. Left behind, it would
  // hand whoever signs in next on this browser somebody else's screens —
  // refused by the API, which reads it off the new token, but refused is a
  // blank page rather than a sign-in.
  response.cookies.set(returnedCookie());
  return response;
}
