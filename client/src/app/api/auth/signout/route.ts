/**
 * End of session: the cookie carrying the Entra token is cleared.
 *
 * The token lives server-side, in an `httpOnly` cookie: only a handler like
 * this one can remove it. Redirecting is left to the caller, who knows where to
 * send the person.
 */
import { NextRequest, NextResponse } from "next/server";

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
  return response;
}
