/**
 * Starting and ending a borrowing: reading Ganesh as one of the team.
 *
 * A handler rather than a call to the API, for the reason the sign-out is
 * one: what it changes is a sealed cookie, and only a handler can write it.
 *
 * It asks the API first, and that is the whole of its caution. Sealing the
 * cookie on the strength of a click would hand back a session every request
 * of which the API refuses — a screen that draws nothing, with no band on it
 * to say why and no way out but the browser's own cookie jar. So the
 * borrowing is tried on `GET /users/me`, which is the one route that answers
 * for *whoever is reading*: it comes back 200 with the teammate, or it says
 * no and nothing is written down.
 *
 * The API stays the authority for everything after: each request carries the
 * header again, and is read again.
 */
import { NextRequest, NextResponse } from "next/server";

import { upstream } from "@/lib/api/upstream";
import {
  IMPERSONATION_HEADER,
  borrowingCookie,
  returnedCookie,
} from "@/lib/auth/impersonation";
import { currentSession } from "@/lib/auth/session";

function refusal(status: number, detail: string): NextResponse {
  return NextResponse.json({ detail }, { status });
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  const body = (await request.json().catch(() => null)) as {
    userId?: unknown;
  } | null;
  const userId = body?.userId;
  if (typeof userId !== "number" || !Number.isInteger(userId)) {
    return refusal(400, "Il faut nommer le collaborateur à lire.");
  }

  const session = await currentSession();
  const headers = new Headers({ [IMPERSONATION_HEADER]: String(userId) });
  if (session) headers.set("Authorization", `Bearer ${session.idToken}`);

  const tried = await fetch(upstream("/users/me"), { headers, cache: "no-store" });
  if (!tried.ok) {
    // Relayed as the API said it: the screen shows why rather than « une
    // erreur est survenue » over a refusal that names itself.
    return new NextResponse(await tried.text(), {
      status: tried.status,
      headers: { "content-type": "application/json" },
    });
  }

  const response = new NextResponse(await tried.text(), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
  // The seal needs the key the session is sealed with, and a laptop running
  // with the door open has never needed one. Said out loud rather than left
  // as a 500 with an empty body: the screen shows this sentence, and whoever
  // reads it knows which line of `.env.local` is missing.
  try {
    response.cookies.set(await borrowingCookie(userId));
  } catch {
    return refusal(
      500,
      "SESSION_SECRET est absent : l'emprunt ne peut pas être scellé.",
    );
  }
  return response;
}

/** Gives the account back, and the administrator their own screens. */
export async function DELETE(): Promise<NextResponse> {
  const response = new NextResponse(null, { status: 204 });
  response.cookies.set(returnedCookie());
  return response;
}
