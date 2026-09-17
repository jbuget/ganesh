"use client";

import { useSyncExternalStore } from "react";

const PARAMETRE = "mission";

/**
 * La mission ouverte dans le panneau lateral, tenue par l'URL.
 *
 * L'URL est la source : un panneau se partage par un lien, et le retour arriere
 * le referme. Elle se lit avec `useSyncExternalStore` plutot qu'avec
 * `useSearchParams`, qui imposerait une frontiere `Suspense` au-dessus d'une
 * page par ailleurs prerendue, et ferait passer chaque ouverture par le routeur
 * alors qu'il ne s'agit que de montrer un panneau.
 *
 * `history.pushState` ne declenche pas `popstate` : on previent donc les
 * abonnes nous-memes apres chaque navigation.
 */
const abonnes = new Set<() => void>();

function lire(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get(PARAMETRE);
}

function prevenir() {
  abonnes.forEach((callback) => callback());
}

function abonner(callback: () => void) {
  abonnes.add(callback);
  window.addEventListener("popstate", callback);

  // Le serveur rend toujours le panneau ferme. Si l'URL dit l'inverse, personne
  // ne previendrait React apres l'hydratation : on le fait au premier abonnement.
  if (lire()) queueMicrotask(callback);

  return () => {
    abonnes.delete(callback);
    window.removeEventListener("popstate", callback);
  };
}

/** Cote serveur, aucun panneau n'est ouvert : c'est l'etat par defaut. */
function surLeServeur(): string | null {
  return null;
}

export function useMissionOuverte() {
  const valeur = useSyncExternalStore(abonner, lire, surLeServeur);

  return {
    missionOuverte: Number(valeur) || null,

    ouvrir(projectId: number) {
      window.history.pushState(null, "", `?${PARAMETRE}=${projectId}`);
      prevenir();
    },

    fermer() {
      window.history.pushState(null, "", window.location.pathname);
      prevenir();
    },
  };
}
