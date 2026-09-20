/**
 * The door. Nobody reaches a screen without saying who they are.
 *
 * The check runs before anything is rendered, on every address that is not
 * expressly open: a screen added tomorrow is protected without anyone
 * thinking about it.
 *
 * Only the seal is examined here, never what Entra signed — the API verifies
 * that, on every call. This answers one question: is there a session worth
 * relaying.
 *
 * It is named `proxy` because Next 16 renamed the convention: `middleware.ts`
 * still runs, and warns that it is deprecated.
 */
import { NextRequest, NextResponse } from "next/server";

import { isAuthDisabled, isOpenPath } from "@/lib/auth/guard";
import { SESSION_COOKIE, openSession } from "@/lib/auth/session";

export async function proxy(request: NextRequest): Promise<NextResponse> {
  const { pathname } = request.nextUrl;

  if (isAuthDisabled() || isOpenPath(pathname)) return NextResponse.next();

  const sealed = request.cookies.get(SESSION_COOKIE)?.value;
  if (sealed && (await openSession(sealed))) return NextResponse.next();

  // The API answers, it does not redirect: a fetch that lands on an HTML
  // sign-in page reads as a parsing error, never as « sign in again ».
  const response = pathname.startsWith("/api/")
    ? NextResponse.json({ detail: "Session expirée." }, { status: 401 })
    : signInAt(request);

  // A seal that no longer opens is a session that is over. Cleared here, or
  // the browser would keep sending it at every request for the fortnight it
  // was set to live, and signing in afresh would be the only way out.
  if (sealed) response.cookies.set(SESSION_COOKIE, "", { path: "/", maxAge: 0 });
  return response;
}

function signInAt(request: NextRequest): NextResponse {
  const { pathname, search } = request.nextUrl;
  const signIn = new URL("/sign-in", request.nextUrl.origin);
  // Where they were headed, so signing in takes them there rather than home.
  signIn.searchParams.set("from", `${pathname}${search}`);
  return NextResponse.redirect(signIn);
}

export const config = {
  // Everything but the files Next serves itself: this has no business
  // slowing down an image.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icon.svg).*)"],
};
