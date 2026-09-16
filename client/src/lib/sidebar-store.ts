"use client";

import { useSyncExternalStore } from "react";

const CLE = "timesheet.sidebar-repliee";

/**
 * Preference de repli de la barre laterale.
 *
 * Elle vit hors de React et se lit avec `useSyncExternalStore` : initialiser un
 * etat depuis `localStorage` au premier rendu ferait diverger le serveur et le
 * client, et le lire dans un effet imposerait un `setState` que React
 * deconseille.
 *
 * Aucune valeur n'est mise en cache : `localStorage` est la seule source, ce
 * qui laisse un autre onglet la modifier sans desynchroniser celui-ci.
 */
const abonnes = new Set<() => void>();

function lire(): boolean {
  return typeof window !== "undefined" && window.localStorage.getItem(CLE) === "1";
}

function prevenir() {
  abonnes.forEach((callback) => callback());
}

function abonner(callback: () => void) {
  abonnes.add(callback);
  window.addEventListener("storage", callback);

  // Le serveur rend toujours la barre depliee. Si la preference dit l'inverse,
  // personne ne previendrait React apres l'hydratation : on le fait ici, au
  // premier abonnement cote client.
  if (lire()) queueMicrotask(callback);

  return () => {
    abonnes.delete(callback);
    window.removeEventListener("storage", callback);
  };
}

/** Cote serveur, la barre est toujours depliee : c'est l'etat par defaut. */
function surLeServeur() {
  return false;
}

export function basculerBarreLaterale() {
  window.localStorage.setItem(CLE, lire() ? "0" : "1");
  prevenir();
}

export function useBarreLateraleRepliee(): boolean {
  return useSyncExternalStore(abonner, lire, surLeServeur);
}
