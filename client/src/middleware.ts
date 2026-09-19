/**
 * The door. Nobody reaches a screen without saying who they are.
 *
 * The check runs before anything is rendered, on every address that is not
 * expressly open: a screen added tomorrow is protected without anyone
 * thinking about it.
 *
 * Only the seal is examined here, never what Entra signed — the API verifies
 * that, on every call. The middleware answers one question: is there a
 * session worth relaying.
 */
import { NextRequest, NextResponse } from "next/server";

import { isAuthDisabled, isOpenPath } from "@/lib/auth/guard";
import { SESSION_COOKIE, openSession } from "@/lib/auth/session";

export async function middleware(request: NextRequest): Promise<NextResponse> {
  const { pathname, search } = request.nextUrl;

  if (isAuthDisabled() || isOpenPath(pathname)) return NextResponse.next();

  const sealed = request.cookies.get(SESSION_COOKIE)?.value;
  if (sealed && (await openSession(sealed))) return NextResponse.next();

  // The API answers, it does not redirect: a fetch that lands on an HTML
  // sign-in page reads as a parsing error, never as « sign in again ».
  if (pathname.startsWith("/api/")) {
    return NextResponse.json({ detail: "Session expirée." }, { status: 401 });
  }

  const signIn = new URL("/connexion", request.nextUrl.origin);
  // Where they were headed, so signing in takes them there rather than home.
  signIn.searchParams.set("from", `${pathname}${search}`);
  return NextResponse.redirect(signIn);
}

export const config = {
  // Everything but the files Next serves itself: the middleware has no
  // business slowing down an image.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icon.svg).*)"],
};
