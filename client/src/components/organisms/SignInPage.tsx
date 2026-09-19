"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { buttonVariants } from "@/components/ui/button";

/**
 * Why a sign-in did not go through, said plainly.
 *
 * Entra's own words name the tenant and the client: they are for us, in the
 * logs. What is shown here says what happened and what to do about it.
 */
const REASONS: Record<string, string> = {
  refus: "La connexion a été refusée. Vous pouvez réessayer.",
  incomplet: "Microsoft n'a pas renvoyé de quoi vous identifier. Réessayez.",
  expire: "La connexion a pris trop de temps. Il faut la reprendre.",
  etat: "Cette connexion ne vient pas de cet onglet. Reprenez depuis ici.",
  echange: "Microsoft n'a pas accepté la connexion. Réessayez dans un instant.",
  "sans-adresse": "Votre compte Microsoft n'expose pas d'adresse e-mail.",
  domaine: "Seules les adresses @waat.fr ont accès à Ganesh.",
  identifiants: "Identifiant ou mot de passe incorrect.",
  "hors-service": "Cette façon de se connecter n'est pas active ici.",
};

function SignIn({ entra }: { entra: boolean }) {
  const params = useSearchParams();
  const reason = params.get("erreur");
  const from = params.get("from");

  const href = from
    ? `/api/auth/login?from=${encodeURIComponent(from)}`
    : "/api/auth/login";

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Ganesh</h1>
        <p className="mt-1 text-sm text-slate-500">
          Le temps passé par projet, chez WAAT.
        </p>

        {reason && (
          <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800">
            {REASONS[reason] ?? "La connexion n'a pas abouti. Réessayez."}
          </p>
        )}

        {entra ? (
          /* A link, not a fetch: signing in leaves the site for Microsoft and
             comes back. Only a real navigation does that — which is also why
             this wears a button's clothes rather than being one. */
          <a href={href} className={`${buttonVariants()} mt-6 w-full cursor-pointer`}>
            Se connecter avec Microsoft
          </a>
        ) : (
          /* A plain form, posted to the BFF: no script needs to run for
             someone to sign in, and the password never touches the page's
             JavaScript. */
          <form action="/api/auth/local" method="post" className="mt-6 space-y-3">
            {from && <input type="hidden" name="from" value={from} />}
            <label className="block">
              <span className="text-sm text-slate-600">Identifiant</span>
              <input
                name="login"
                autoComplete="username"
                required
                autoFocus
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
              />
            </label>
            <label className="block">
              <span className="text-sm text-slate-600">Mot de passe</span>
              <input
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
              />
            </label>
            <button
              type="submit"
              className={`${buttonVariants()} w-full cursor-pointer`}
            >
              Se connecter
            </button>
          </form>
        )}
      </div>
    </main>
  );
}

/**
 * The screen that asks who you are.
 *
 * `useSearchParams` reads the address, which is only known in the browser:
 * without this boundary, the whole page would have to be rendered there.
 */
export function SignInPage({ entra }: { entra: boolean }) {
  return (
    <Suspense>
      <SignIn entra={entra} />
    </Suspense>
  );
}
