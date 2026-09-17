"use client";

import { useSyncExternalStore } from "react";

/**
 * L'URL comme etat partage de l'ecran.
 *
 * Panneau ouvert, filtres poses : ce sont des choses qui se partagent par un
 * lien et survivent a un rechargement. Elles vivent donc dans l'adresse, et non
 * dans un etat React que le premier F5 emporte.
 *
 * `history.pushState` ne declenche pas `popstate` : on previent donc les
 * abonnes nous-memes apres chaque ecriture.
 */
const subscribers = new Set<() => void>();

function query(): string {
  return typeof window === "undefined" ? "" : window.location.search;
}

/** Cote serveur, l'adresse n'est pas connue : aucun parametre. */
function surLeServeur(): string {
  return "";
}

function subscribe(callback: () => void) {
  subscribers.add(callback);
  window.addEventListener("popstate", callback);

  // Le serveur rend toujours l'ecran nu. Si l'URL dit autre chose, personne ne
  // previendrait React apres l'hydratation : on le fait au premier abonnement.
  if (query()) queueMicrotask(callback);

  return () => {
    subscribers.delete(callback);
    window.removeEventListener("popstate", callback);
  };
}

/** Les parametres courants, tels que l'adresse les porte. */
export function useQueryString(): string {
  return useSyncExternalStore(subscribe, query, surLeServeur);
}

/**
 * Remanie les parametres de l'adresse.
 *
 * `pousser` ajoute une etape a l'historique : c'est ce qu'on veut d'une
 * navigation, dont le retour arriere doit defaire l'effet. `remplacer` n'en
 * ajoute aucune : un filtre se regle par touches successives, et chacune ne
 * doit pas devenir une etape a remonter.
 */
export function writeUrl(
  maj: (params: URLSearchParams) => void,
  mode: "pousser" | "remplacer" = "pousser",
): void {
  const params = new URLSearchParams(window.location.search);
  maj(params);

  const queryString = params.toString();
  const address = queryString ? `?${queryString}` : window.location.pathname;
  if (mode === "pousser") window.history.pushState(null, "", address);
  else window.history.replaceState(null, "", address);

  subscribers.forEach((callback) => callback());
}
