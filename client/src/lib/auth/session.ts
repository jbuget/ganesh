/**
 * Acces au jeton Entra, cote serveur uniquement.
 *
 * En developpement, `REQUIRE_AUTH=false` cote API permet de travailler sans
 * jeton : le BFF ne transmet alors rien et l'API applique son identite de
 * developpement. Ce mode ne doit jamais etre actif en production.
 */
import { cookies } from "next/headers";

export const SESSION_COOKIE = "timesheet_token";

/** Retourne le jeton d'acces de la session, s'il existe. */
export async function getAccessToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(SESSION_COOKIE)?.value ?? null;
}
