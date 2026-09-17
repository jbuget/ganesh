/**
 * Fin de session : le cookie qui porte le jeton Entra est efface.
 *
 * Le jeton vit cote serveur, dans un cookie `httpOnly` : seul un handler comme
 * celui-ci peut le retirer. La redirection est laissee a l'appelant, qui sait
 * ou renvoyer la personne.
 */
import { NextResponse } from "next/server";

import { SESSION_COOKIE } from "@/lib/auth/session";

export async function POST(): Promise<NextResponse> {
  const response = new NextResponse(null, { status: 204 });
  response.cookies.set(SESSION_COOKIE, "", { path: "/", maxAge: 0 });
  return response;
}
